#!/usr/bin/env python3
"""
PDF PII Extractor
Extracts text from a PDF, then identifies and masks PII
using a pluggable abstraction layer.

Usage:
    python pdf_pii.py <input.pdf>
"""


import argparse

from cv_pii.extractor import available_extractors, make_extractor
from cv_pii.identifier import available_identifiers, make_identifier
from cv_pii.masker import available_maskers, make_masker
from cv_pii.log import configure as configure_logging, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def process_document(path, extractor, identifier, masker):
    """
    Full pipeline: extract text, identify PII, mask it.

    Returns (original_text, entities, masked_text).
    """
    text = extractor.extract(path)
    entities = identifier.identify(text)
    masked = masker.mask(text, entities)
    return text, entities, masked


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract text from a PDF and mask PII.")
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "--extractor",
        choices=available_extractors(),
        default="cocoapdf",
        help="Which text extractor to use (default: cocoapdf)",
    )
    parser.add_argument(
        "--model",
        choices=available_identifiers(),
        default="shield",
        help="Which PII identifier to use (default: shield)",
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Optional HF model name / checkpoint override",
    )
    parser.add_argument(
        "--masker",
        choices=available_maskers(),
        default=None,
        help="Masking strategy (default: auto-select based on --model)",
    )
    parser.add_argument(
        "--log-level", "--loglevel" ,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "TRACE"],
        help="Logging verbosity (default: WARNING)"
    )

    args = parser.parse_args()

    configure_logging(args.log_level)

    log.info("Starting pipeline on %s", args.pdf)
    log.debug("Model=%s masker=%s extractor=%s",
              args.model, args.masker, args.extractor)

    # Select and instantiate the pluggable components
    extractor = make_extractor(args.extractor)

    identifier = make_identifier(
        kind=args.model,
        model_name=args.checkpoint,
        exclude_types={"USERAGENT", "ORG", "JOBTITLE", "COMPANYNAME", "JOBAREA", "JOBTYPE"},
    )

    masker_kind = args.masker or ("text" if args.model == "llm" else "offset")
    masker = make_masker(masker_kind)

    original, entities, masked = process_document(
        args.pdf, extractor, identifier, masker,
    )

    # --- Output --------------------------------------------------------
    print("=" * 60)
    print("ORIGINAL TEXT")
    print("=" * 60)
    print(original[:2000])
    print()

    print("=" * 60)
    print(f"DETECTED PII ({len(entities)} entities)")
    print("=" * 60)
    for e in entities:
        print(f"  [{e.entity_type}] {e.text!r} (score={e.score:.2f})")
    print()

    print("=" * 60)
    print("MASKED TEXT")
    print("=" * 60)
    print(masked[:2000])


if __name__ == "__main__":
    main()
    