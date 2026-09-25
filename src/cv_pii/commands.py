"""Orchestration for the anon / match / all commands."""

from pathlib import Path

from cv_pii import cache
from cv_pii.extractor import TextExtractor
from cv_pii.identifier import PIIIdentifier
from cv_pii.masker import PIIMasker
from cv_pii.matcher import JobMatcher
from cv_pii.matcher.data import MatchResult
from cv_pii.log import get_logger
from pathlib import Path
from typing import Iterable

log = get_logger(__name__)

def expand_pdf_args(paths: Iterable[str]) -> list[Path]:
    """
    Expand a mix of files and directories into a sorted list of PDF paths.

    - Directories are scanned for *.pdf (non-recursive).
    - Files are passed through as-is.
    - Duplicates are removed while preserving order.
    """
    result: list[Path] = []
    seen: set[Path] = set()

    for p in paths:
        path = Path(p)
        if path.is_dir():
            candidates = sorted(path.glob("*.pdf"))
        else:
            candidates = [path]

        for c in candidates:
            resolved = c.resolve()
            if resolved not in seen:
                seen.add(resolved)
                result.append(resolved)

    return result


def run_anon(
    pdf_path: str,
    extractor: TextExtractor,
    identifier: PIIIdentifier,
    masker: PIIMasker,
    *,
    identifier_kind: str,
    identifier_model: str | None,
    masker_kind: str,
    force: bool = False,
) -> Path:
    """Extract, identify, mask, and cache. Returns the anonymized .txt path."""
    paths = cache.cache_paths_for(pdf_path)

    if not force and cache.is_valid(
        paths,
        identifier_kind=identifier_kind,
        identifier_model=identifier_model,
        masker_kind=masker_kind,
    ):
        log.info("Cache hit: %s", paths.anonymized_txt)
        return paths.anonymized_txt

    if force:
        log.info("--force set; regenerating cache for %s", pdf_path)

    log.info("Extracting text from %s", pdf_path)
    text = extractor.extract(pdf_path)

    log.info("Identifying PII (%d chars)", len(text))
    entities = identifier.identify(text)

    log.info("Masking %d entities", len(entities))
    masked = masker.mask(text, entities)

    cache.write(
        paths, masked,
        identifier_kind=identifier_kind,
        identifier_model=identifier_model,
        masker_kind=masker_kind,
    )
    return paths.anonymized_txt


def run_match(
    anonymized_path: Path,
    job_description_path: str,
    matcher: JobMatcher,
) -> MatchResult:
    """Match an anonymized CV against a job description."""
    cv_text = anonymized_path.read_text(encoding="utf-8")
    jd_text = Path(job_description_path).read_text(encoding="utf-8")

    log.info("Matching %s against %s", anonymized_path.name, job_description_path)
    return matcher.match(cv_text, jd_text)


def print_result(result: MatchResult) -> None:
    """Print a MatchResult to stdout."""
    print("=" * 60)
    print(f"MATCH SCORE: {result.score:.2f}")
    print("=" * 60)
    print(result.summary)
    print()

    if result.matched_skills:
        print("MATCHED:")
        for s in result.matched_skills:
            print(f"  ✓ {s.skill}")
            if s.evidence:
                print(f"      {s.evidence}")
        print()

    if result.missing_skills:
        print("MISSING:")
        for s in result.missing_skills:
            print(f"  ✗ {s.skill}")
        print()

    if result.notes:
        print(f"NOTES: {result.notes}")