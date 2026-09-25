#!/usr/bin/env python3
"""
PDF PII Extractor and Job Matcher.

Usage:
    cv_pii anon  <pdf>              Anonymize a CV (cached alongside the PDF)
    cv_pii match <pdf> <jd>         Match an already-anonymized CV to a JD
    cv_pii all   <pdf> <jd>         Anonymize then match
"""

import argparse
import sys
from pathlib import Path

from cv_pii import cache
from cv_pii.extractor import available_extractors, make_extractor
from cv_pii.identifier import available_identifiers, make_identifier
from cv_pii.masker import available_maskers, make_masker
from cv_pii.matcher import available_matchers, make_matcher
from cv_pii.log import configure as configure_logging, get_logger
from cv_pii.commands import run_anon, run_match, print_result

log = get_logger(__name__)


# --- Shared argument groups ------------------------------------------------

def add_anonymization_args(p):
    p.add_argument("--extractor", choices=available_extractors(),
                   default="cocoapdf",
                   help="Text extractor (default: cocoapdf)")
    p.add_argument("--model", choices=available_identifiers(),
                   default="shield",
                   help="PII identifier (default: shield)")
    p.add_argument("--checkpoint", default=None,
                   help="HF model name / checkpoint override")
    p.add_argument("--masker", choices=available_maskers(),
                   default=None,
                   help="Masking strategy (default: auto)")


def add_matching_args(p):
    p.add_argument("--matcher", choices=available_matchers(),
                   default="llm",
                   help="Matcher implementation (default: llm)")
    p.add_argument("--matcher-model", default=None,
                   help="Model name for the matcher")


def add_logging_args(p):
    p.add_argument("--log-level", default="WARNING",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                   help="Logging verbosity (default: WARNING)")


# --- Subcommand handlers ---------------------------------------------------

def cmd_anon(args):
    pdf_paths = expand_pdf_args(args.pdf)

    if not pdf_paths:
        log.error("No PDFs found in the given paths: %s", args.pdf)
        sys.exit(1)

    log.info("Anonymizing %d PDF(s)", len(pdf_paths))

    # Load models once
    extractor = make_extractor(args.extractor)
    identifier = make_identifier(
        kind=args.model,
        model_name=args.checkpoint,
        exclude_types=DEFAULT_EXCLUDE_TYPES,
    )
    masker_kind = args.masker or ("text" if args.model == "llm" else "offset")
    masker = make_masker(masker_kind, model=args.checkpoint)

    for i, pdf in enumerate(pdf_paths, 1):
        log.info("[%d/%d] %s", i, len(pdf_paths), pdf.name)
        out = run_anon(
            str(pdf), extractor, identifier, masker,
            identifier_kind=args.model,
            identifier_model=args.checkpoint,
            masker_kind=masker_kind,
            force=args.force,
        )
        # Print the cache path for each input
        print(out)


def cmd_match(args):
    matcher = make_matcher(args.matcher, model=args.matcher_model)

    paths = cache.cache_paths_for(args.pdf)
    if not paths.anonymized_txt.exists():
        log.error("No anonymized file for %s.", args.pdf)
        log.error("Run `cv_pii anon %s` first, or use `cv_pii all`.", args.pdf)
        sys.exit(1)

    result = run_match(paths.anonymized_txt, args.jd, matcher)
    print_result(result)


def cmd_all(args):
    extractor = make_extractor(args.extractor)
    identifier = make_identifier(
        kind=args.model,
        model_name=args.checkpoint,
        exclude_types={"USERAGENT", "ORG", "JOBTITLE", "COMPANYNAME",
                       "JOBAREA", "JOBTYPE"},
    )
    masker_kind = args.masker or ("text" if args.model == "llm" else "offset")
    masker = make_masker(masker_kind)

    anonymized_path = run_anon(
        args.pdf, extractor, identifier, masker,
        identifier_kind=args.model,
        identifier_model=args.checkpoint,
        masker_kind=masker_kind,
        force=args.force,
    )

    matcher = make_matcher(args.matcher, model=args.matcher_model)
    result = run_match(anonymized_path, args.jd, matcher)
    print_result(result)


# --- Entry point -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="cv_pii",
        description="Anonymize CVs and match them against job descriptions.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # anon
    p_anon = sub.add_parser("anon", help="Anonymize one or more CVs")
    p_anon.add_argument(
        "pdf", nargs="+",
        help="One or more PDF files, or directories containing PDFs",
    )
    p_anon.add_argument("--force", action="store_true",
                        help="Regenerate the cache even if valid")
    add_anonymization_args(p_anon)
    add_logging_args(p_anon)
    p_anon.set_defaults(func=cmd_anon)

    # match
    p_match = sub.add_parser("match", help="Match an anonymized CV to a JD")
    p_match.add_argument("pdf", help="Path to the source PDF (cache must exist)")
    p_match.add_argument("jd", help="Path to the job description file")
    add_matching_args(p_match)
    add_logging_args(p_match)
    p_match.set_defaults(func=cmd_match)

    # all
    p_all = sub.add_parser("all", help="Anonymize then match")
    p_all.add_argument("pdf", help="Path to the input PDF")
    p_all.add_argument("jd", help="Path to the job description file")
    p_all.add_argument("--force", action="store_true",
                       help="Regenerate the cache even if valid")
    add_anonymization_args(p_all)
    add_matching_args(p_all)
    add_logging_args(p_all)
    p_all.set_defaults(func=cmd_all)

    args = parser.parse_args()
    configure_logging(args.log_level)

    args.func(args)


if __name__ == "__main__":
    main()