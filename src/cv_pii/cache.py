"""
Cache management for anonymized CVs.

The cache is a pair of files stored alongside the source PDF:

    foo.pdf
    foo.anonymized.txt          <- masked text
    foo.anonymized.meta.json    <- metadata for validity checks

The metadata records the source mtime plus the identifier/masker
configuration, so we can detect stale caches without re-running the
expensive anonymization step.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from cv_pii.log import get_logger

log = get_logger(__name__)


@dataclass
class CacheMeta:
    """Metadata stored alongside an anonymized CV."""
    source_pdf: str
    source_mtime: float
    identifier_kind: str
    identifier_model: Optional[str]
    masker_kind: str
    created_at: str


@dataclass
class CachePaths:
    """Resolved paths for a cache entry."""
    anonymized_txt: Path
    meta_json: Path
    source_pdf: Path


def cache_paths_for(pdf_path: str | Path) -> CachePaths:
    """Return the cache paths associated with a source PDF."""
    pdf = Path(pdf_path).resolve()
    # with_suffix replaces only the last suffix (.pdf), preserving stem
    anonymized = pdf.with_suffix(".anonymized.txt")
    # Path.with_suffix only handles a single suffix, so build meta manually
    meta = pdf.parent / f"{pdf.stem}.anonymized.meta.json"
    return CachePaths(
        anonymized_txt=anonymized,
        meta_json=meta,
        source_pdf=pdf,
    )


def is_valid(
    paths: CachePaths,
    *,
    identifier_kind: str,
    identifier_model: Optional[str],
    masker_kind: str,
) -> bool:
    """
    Return True if the cache exists and matches the current configuration.
    """
    if not paths.anonymized_txt.exists() or not paths.meta_json.exists():
        return False

    try:
        meta = CacheMeta(**json.loads(paths.meta_json.read_text()))
    except (json.JSONDecodeError, TypeError) as e:
        log.warning("Corrupt cache metadata %s: %s", paths.meta_json, e)
        return False

    # Source PDF must not have changed since the cache was written
    current_mtime = paths.source_pdf.stat().st_mtime
    if abs(meta.source_mtime - current_mtime) > 0.001:
        log.info("Cache stale: source PDF mtime changed")
        return False

    # Configuration must match
    if meta.identifier_kind != identifier_kind:
        log.info("Cache stale: identifier kind changed (%s -> %s)",
                 meta.identifier_kind, identifier_kind)
        return False
    if meta.identifier_model != identifier_model:
        log.info("Cache stale: identifier model changed (%s -> %s)",
                 meta.identifier_model, identifier_model)
        return False
    if meta.masker_kind != masker_kind:
        log.info("Cache stale: masker kind changed (%s -> %s)",
                 meta.masker_kind, masker_kind)
        return False

    return True


def read_anonymized(paths: CachePaths) -> str:
    """Read the anonymized text from the cache."""
    return paths.anonymized_txt.read_text(encoding="utf-8")


def write(
    paths: CachePaths,
    anonymized_text: str,
    *,
    identifier_kind: str,
    identifier_model: Optional[str],
    masker_kind: str,
) -> None:
    """Write the anonymized text and metadata to the cache."""
    from datetime import datetime, timezone

    paths.anonymized_txt.write_text(anonymized_text, encoding="utf-8")

    meta = CacheMeta(
        source_pdf=str(paths.source_pdf),
        source_mtime=paths.source_pdf.stat().st_mtime,
        identifier_kind=identifier_kind,
        identifier_model=identifier_model,
        masker_kind=masker_kind,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    paths.meta_json.write_text(
        json.dumps(asdict(meta), indent=2),
        encoding="utf-8",
    )
    log.info("Wrote cache: %s", paths.anonymized_txt)