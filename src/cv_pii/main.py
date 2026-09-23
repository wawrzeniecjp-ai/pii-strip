#!/usr/bin/env python3
"""
PDF PII Extractor
Extracts text from a PDF using cocoapdf, then identifies and masks PII
using a pluggable abstraction layer.

Usage:
    python pdf_pii.py <input.pdf>
"""

import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Callable
from dataclasses import dataclass
from ollama import chat
from pydantic import BaseModel
import re
import warnings

from cocoapdf import ConvertOptions, convert_file
from transformers import pipeline

ner_model_name =   "LH-Tech-AI/Shield-82M" #"exdsgift/NerGuard-0.3B" #
ner_model_threshold = 0.5

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PIIEntity:
    """A single detected PII entity within the extracted text."""
    entity_type: str          # e.g. "PERSON", "EMAIL_ADDRESS"
    start: int                # character offset (inclusive)
    end: int                  # character offset (exclusive)
    text: str                 # the exact substring that was detected
    score: float = 1.0        # confidence score from the identifier


# ---------------------------------------------------------------------------
# Pluggable identifier abstraction
# ---------------------------------------------------------------------------

class PIIIdentifier(ABC):
    """
    Abstract base class for PII identification strategies.

    Any concrete identifier (NER model, LLM, ensemble, regex-only, etc.)
    implements this single method, allowing the extraction pipeline to
    remain agnostic about *how* PII is found.
    """

    @abstractmethod
    def identify(self, text: str) -> List[PIIEntity]:
        """
        Return a list of PIIEntity objects found in `text`.

        Implementations must ensure:
        - Offsets are 0-based character indices into the original text.
        - `text` field matches text[start:end] exactly.
        - Overlapping entities are de-duplicated (caller may also dedupe).
        """
        ...

# ---------------------------------------------------------------------------
# Masker interface
# ---------------------------------------------------------------------------

class PIIMasker(ABC):
    @abstractmethod
    def mask(self, text: str, entities: List[PIIEntity]) -> str: ...


class OffsetMasker(PIIMasker):
    """Use entity.start / entity.end. Fast, precise, requires accurate offsets."""
    def mask(self, text: str, entities: List[PIIEntity]) -> str:
        # NER mask_pii logic
        return mask_pii(text, entities)


class TextSearchMasker(PIIMasker):
    def __init__(self, replace_all: bool = True):
        self.replace_all = replace_all

    def mask(self, text: str, entities: List[PIIEntity]) -> str:
        # Sort longest-first so "Danielle Johnson" doesn't get partially
        # masked by an earlier "Danielle" replacement.
        ordered = sorted(entities, key=lambda e: len(e.text), reverse=True)

        result = text
        for e in ordered:
            placeholder = f"[{e.entity_type}]"
            if self.replace_all:
                result = result.replace(e.text, placeholder)
            else:
                result = result.replace(e.text, placeholder, 1)
        return result


def make_masker(kind: str) -> PIIMasker:
    if kind == "text":
        return TextSearchMasker()
    elif kind == "offset":
        return OffsetMasker()
    else:
        raise ValueError("Unknown masker kind: " + kind)


# ---------------------------------------------------------------------------
# Label normalization
# ---------------------------------------------------------------------------
# Different models use different names for the same concept. Normalizing
# to a canonical label set lets downstream code (filters, masking, analytics)
# stay model-agnostic.
LABEL_ALIASES = {
    "USER_AGENT": "USERAGENT",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "TELEPHONENUM": "PHONEN",
    "SOCIALNUM": "SSN",
    "SOCIAL_SECURITY_NUMBER": "SSN",
    "GIVENNAME": "FIRSTNAME",
    "SURNAME": "LASTNAME",
    "COMPANYNAME": "ORG",
    "ORGANIZATION": "ORG",
}


def _normalize_label(label: str) -> str:
    """Map a model-specific label to a canonical form."""
    upper = label.upper().lstrip("BI-")  # strip BIO prefix if present
    return LABEL_ALIASES.get(upper, upper)


# ---------------------------------------------------------------------------
# NerGuard identifier
# ---------------------------------------------------------------------------

class NerGuardIdentifier(PIIIdentifier):
    """
    PII identification backed by the NerGuard-0.3B model.

    NerGuard outputs AI4Privacy labels (e.g. GIVENNAME, SOCIALNUM). The
    normalization step maps these to a canonical label set so that filters
    and downstream code don't need to know which model produced an entity.
    """

    DEFAULT_MODEL = "exdsgift/NerGuard-0.3B"
    DEFAULT_THRESHOLD = 0.5

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        exclude_types: Optional[set] = None,
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.exclude_types = {t.upper() for t in (exclude_types or set())}

        self.nlp = pipeline(
            "token-classification",
            model=model_name,
            aggregation_strategy="simple",
        )

    def identify(self, text: str) -> List[PIIEntity]:
        raw = self.nlp(text)
        entities: List[PIIEntity] = []

        for r in raw:
            if r["score"] < self.threshold:
                continue

            label = _normalize_label(r["entity_group"])
            if label in self.exclude_types:
                continue

            entities.append(
                PIIEntity(
                    entity_type=label,
                    start=r["start"],
                    end=r["end"],
                    text=r["word"],
                    score=r["score"],
                )
            )

        return entities

# ---------------------------------------------------------------------------
# Concrete stub: Shield-82
# ---------------------------------------------------------------------------

class ShieldIdentifier(PIIIdentifier):
    DEFAULT_MODEL = "LH-Tech-AI/Shield-82M"
    DEFAULT_THRESHOLD = 0.5
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        exclude_types: Optional[set] = None,
    ):
        self.nlp = pipeline(
            "token-classification",
            model=model_name,
            aggregation_strategy="simple",
        )
        self.threshold = threshold
        self.exclude_types = exclude_types or set()

    def identify(self, text: str) -> List[PIIEntity]:
        raw = self.nlp(text)
        return [
            PIIEntity(
                entity_type=r["entity_group"],
                start=r["start"],
                end=r["end"],
                text=r["word"],
                score=r["score"],
            )
            for r in raw
            if r["score"] >= self.threshold
            and r["entity_group"] not in self.exclude_types
        ]


# ---------------------------------------------------------------------------
# Concrete stub: LLM-based identifier
# ---------------------------------------------------------------------------

# Define the schema matching your PIIEntity shape
class PIIEntitySchema(BaseModel):
    entity_type: str
    text: str
    score: float

class PIIResponse(BaseModel):
    entities: List[PIIEntitySchema]

class EntityFilter(PIIIdentifier):
    """
    Wrap another identifier and drop excluded entity types.

    Useful for backends that don't natively support exclusion (like the
    LLM identifier), or for applying a uniform policy across mixed backends.
    """

    def __init__(self, inner: PIIIdentifier, exclude_types: Optional[set] = None):
        self.inner = inner
        self.exclude_types = {t.upper() for t in (exclude_types or set())}

    def identify(self, text: str) -> List[PIIEntity]:
        return [
            e for e in self.inner.identify(text)
            if e.entity_type.upper() not in self.exclude_types
        ]

ORG_MARKERS = re.compile(
    r"\b(University|College|Institute|School|Academy|"
    r"Inc\.?|LLC|Corp\.?|Ltd\.?|Group|Partners|Studios|"
    r"Solutions|Systems|Services|Technologies|Labs|"
    r"Consulting|Analytics|Software|Financial|Insurance|"
    r"Manufacturing|Logistics|Biotech|Pharmaceuticals)\b",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?"          # optional country code
    r"(?:\(?\d{2,4}\)?[-.\s]?)"        # area code, with or without parens
    r"\d{2,4}[-.\s]?\d{2,4}"           # subscriber digits
    r"(?:\s*(?:x|ext\.?)\s*\d+)?"      # optional extension
)

def _looks_like_org(text: str) -> bool:
    return bool(ORG_MARKERS.search(text))

class LLMIdentifier(PIIIdentifier):
    def __init__(
        self,
        model: str = "gemma3:4b",
        threshold: float = 0.5,
        exclude_types: Optional[set] = None,
    ):
        self.model = model
        self.threshold = threshold
        self.exclude_types = {t.upper() for t in (exclude_types or set())}

    def identify(self, text: str) -> List[PIIEntity]:
        prompt = fr"""Task: Extract ALL personally identifying information from a CV, including
information about people OTHER than the candidate.

Entities:
- CANDIDATE_NAME: the CV owner's name (first, last, or full)
- CANDIDATE_EMAIL: the CV owner's email
- CANDIDATE_PHONE: the CV owner's phone
- CANDIDATE_ADDRESS: the CV owner's address
- CANDIDATE_DOB: the CV owner's date of birth
- CANDIDATE_URL: the CV owner's LinkedIn, GitHub, personal site
- CANDIDATE_GOV_ID: the CV owner's SSN, passport, driver's license

- THIRD_PARTY_NAME: an identifiable individual mentioned by name
  (co-author, referee, supervisor, collaborator). Must be a proper
  noun naming a specific person.
  NOT: counts of people ("12 junior engineers"), roles ("the hiring manager"),
  or generic descriptions ("my team").
- THIRD_PARTY_EMAIL: any other person's email
- THIRD_PARTY_PHONE: any other person's phone

How to tell candidate from third party:
- The candidate's name appears in the header, in the contact line, or as a
  publication author alongside the CV content.
- The candidate is the subject of the CV's narrative (summary, experience).
- Everyone else is THIRD_PARTY.

DO NOT extract (preserve these in the text):
- Company names (employers): e.g., "Atlantic Software", "Redwood Financial"
- Company locations: cities and countries in the EXPERIENCE section
  that describe where the employer is based (e.g., "London, UK" next to
  a company name). These are NOT the candidate's address.
- University / school names: e.g., "Pennsylvania State University", "MIT"
- Job titles: e.g., "Senior Software Engineer", "Data Scientist"
- Skills, technologies, languages: e.g., "Python", "AWS", "English"
- Years and date ranges: e.g., "2019 - 2023"
- Publication venues: e.g., "Nature Methods", "NIPS"
- Counts or descriptions of unnamed people: "12 junior engineers",
  "a team of 5", "the recruiter", "3 direct reports"

ADDRESS detection:
- Any line containing a city/country pair like "City, Country"
- Any line in the contact block with a location-like fragment
- "City, State" or "City, Country" patterns, even if the city name
  is unusual or unfamiliar
- The candidate's location is often on the same line as email and phone

Publications:
- Extract ALL named authors, including those separated by commas and "and"
- Format example: "Alice Smith, Bob Jones and Carol Lee" contains three
  person names to extract
- Even if only one author is the candidate, extract the others as
  THIRD_PARTY_NAME

Note: The same person's name may appear in different forms:
- Full name in the header ("Robert Down")
- With middle initials in publications ("Robert J. Down")
- Initials only ("R. Down")
- Informal variants ("Bob Down")

Extract each occurrence with its own entity_type label. Do not try to
merge them — the masking layer will handle them as separate entities.

Return JSON with an "entities" array. Each entity has:
- entity_type: string
- text: string (exact substring from the input)
- score: float 0–1

Example:
Input:
    # Robert Down
    robert.down@gmail.com | 555-1234-154 | New Crestview, Portugal

    ## EXPERIENCE
    - Jun 2018 - Mar 2025 | Principal Scientist
    Scheider Electric Corp. | London, UK
      - Mentored 12 junior engineers and ran code reviews

    - Sep 2011 - May 2018 | Junior Data Scientist
    Auchamps S.A. | Toulouse, France
      - Collaborated with Doug Bessent on the migration project

    ## PUBLICATIONS
    Two dimensional manifold in Fourier spaces. Robert J. Down, Kim Jung and Denis J.E. Lambert. Nature Methods, 2023.

    ## REFERENCES
    Dr. Luc Dupont — ldupont@uniparis.edu

Output:
    {{"entities": [
      {{"entity_type": "CANDIDATE_NAME", "text": "Robert Down", "score": 0.95}},
      {{"entity_type": "CANDIDATE_EMAIL", "text": "robert.down@gmail.com", "score": 0.95}},
      {{"entity_type": "CANDIDATE_PHONE", "text": "555-1234-154", "score": 0.9}},
      {{"entity_type": "CANDIDATE_ADDRESS", "text": "New Crestview, Portugal", "score": 0.85}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Doug Bessent", "score": 0.9}},
      {{"entity_type": "CANDIDATE_NAME", "text": "Robert J. Down", "score": 0.9}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Kim Jung", "score": 0.9}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Denis J.E. Lambert", "score": 0.9}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Luc Dupont", "score": 0.85}},
      {{"entity_type": "THIRD_PARTY_EMAIL", "text": "ldupont@uniparis.edu", "score": 0.9}}
    ]}}

CV content:
```markdown
{text}
```
"""
        response = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=PIIResponse.model_json_schema(),
            options={
                "temperature": 0,
                "num_predict": 4096,   # Allow longer JSON output
                "num_ctx": 8192,       # Match context to your longest CVs
            },
        )
        parsed = PIIResponse.model_validate_json(response.message.content)

        entities: List[PIIEntity] = []
        seen_spans: set[tuple[int, int]] = set()

        def _add(label: str, start: int, end: int, text: str, score: float):
            key = (start, end)
            if key in seen_spans:
                return
            seen_spans.add(key)
            entities.append(PIIEntity(
                entity_type=label,
                start=start,
                end=end,
                text=text,
                score=score,
            ))

        # --- 1. LLM entities -------------------------------------------
        for e in parsed.entities:
            if e.score < self.threshold:
                continue
            label = _normalize_label(e.entity_type)
            if label in self.exclude_types:
                warnings.warn("Ignoring excluded entity: {}".format(label))
                continue

            # Filter: a *_NAME label that looks like an org is a false positive
            if label.endswith("_NAME") and _looks_like_org(e.text):
                warnings.warn("Ignoring org-like entity: {}".format(e.text))
                continue

            pattern = re.compile(
                r"\b" + re.escape(e.text) + r"\b",
                flags=re.IGNORECASE,
            )
            for match in pattern.finditer(text):
                _add(label, match.start(), match.end(),
                     match.group(), e.score)

        # --- 2. Phone regex safety net ---------------------------------
        # Only add if no CANDIDATE_PHONE / THIRD_PARTY_PHONE entity
        # already covers the same span (the seen_spans check handles this).
        for match in PHONE_PATTERN.finditer(text):
            candidate = match.group().strip()
            # Skip very short matches (likely false positives from dates)
            if len(re.sub(r"\D", "", candidate)) < 7:
                continue
            _add("CANDIDATE_PHONE", match.start(), match.end(),
                 candidate, 1.0)

        return entities
    

from gliner import GLiNER

class GlinerIdentifier(PIIIdentifier):
    """
    PII identification backed by GLiNER.

    Key difference from NerGuard/Shield: entity labels are supplied at
    inference time, not fixed at training time. This makes the label space
    fully dynamic.
    """

    DEFAULT_MODEL = "knowledgator/gliner-pii-large-v1.0" #"knowledgator/gliner-pii-base-v1.0"
    DEFAULT_THRESHOLD = 0.35
    DEFAULT_LABELS = [
        # Direct identifiers
        "person", "first name", "last name",
        "email", "phone number",
        "address", "street address",
        "ssn", "social security number",
        "passport number", "driver license number",
        "credit card number", "bank account number",
        "username", "ip address",
        "linkedin profile",
        # DOB only — not general dates
        "date of birth",
    ]

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        labels: Optional[List[str]] = None,
        exclude_types: Optional[set] = None,
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.labels = labels or self.DEFAULT_LABELS
        self.exclude_types = {t.upper() for t in (exclude_types or set())}

        self.model = GLiNER.from_pretrained(model_name)

    def identify(self, text: str) -> List[PIIEntity]:
        raw = self.model.predict_entities(
            text,
            self.labels,
            threshold=self.threshold,
        )
        entities = []
        for r in raw:
            label = _normalize_label(r["label"])
            if label in self.exclude_types:
                continue
            entities.append(
                PIIEntity(
                    entity_type=label,
                    start=r["start"],
                    end=r["end"],
                    text=r["text"],
                    score=r["score"],
                )
            )
        return entities

# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

# Each entry maps a kind string to a builder that takes (model_name, **kwargs)
_IDENTIFIER_REGISTRY: dict[str, Callable[..., PIIIdentifier]] = {
    "shield": lambda model_name, **kw: ShieldIdentifier(
        model_name=model_name or ShieldIdentifier.DEFAULT_MODEL, **kw
    ),
    "nerguard": lambda model_name, **kw: NerGuardIdentifier(
        model_name=model_name or NerGuardIdentifier.DEFAULT_MODEL, **kw
    ),
    "llm": lambda model_name, **kw: LLMIdentifier(
        model=model_name or "gemma3:4b", **kw
    ),
    "gliner": lambda model_name, **kw: GlinerIdentifier(
        model_name=model_name or GlinerIdentifier.DEFAULT_MODEL, **kw
    ),
}


def make_identifier(kind: str, model_name: Optional[str] = None, **kwargs) -> PIIIdentifier:
    if kind not in _IDENTIFIER_REGISTRY:
        raise ValueError(
            f"Unknown identifier kind: {kind!r}. "
            f"Known: {sorted(_IDENTIFIER_REGISTRY)}"
        )
    return _IDENTIFIER_REGISTRY[kind](model_name, **kwargs)


def available_identifiers() -> list[str]:
    return sorted(_IDENTIFIER_REGISTRY)

# ---------------------------------------------------------------------------
# Masking layer
# ---------------------------------------------------------------------------
def mask_pii(text: str, entities: List[PIIEntity]) -> str:
    """
    Replace each detected PII entity with a class-aware placeholder.

    Entities are processed in reverse offset order so earlier replacements
    do not shift the positions of later entities.
    """
    # Normalize entity offsets: strip leading/trailing whitespace from the
    # span and re-align start/end so the span exactly matches the original.
    normalized = []
    for e in entities:
        span = text[e.start:e.end]
        # If the raw span doesn't match, try trimming whitespace from the
        # entity's text and shrinking the offsets to compensate.
        if span != e.text:
            stripped = e.text.strip()
            if stripped and stripped in span:
                offset = span.index(stripped)
                normalized.append(
                    PIIEntity(
                        entity_type=e.entity_type,
                        start=e.start + offset,
                        end=e.start + offset + len(stripped),
                        text=stripped,
                        score=e.score,
                    )
                )
                continue
            # Fall back to the raw entity if we can't reconcile it
            normalized.append(e)
        else:
            normalized.append(e)

    # Drop entities we couldn't validate against the source text
    valid = [e for e in normalized if text[e.start:e.end] == e.text]

    # Sort descending by start offset so earlier splices don't shift later ones
    valid.sort(key=lambda e: e.start, reverse=True)

    result = text
    for e in valid:
        placeholder = f"[{e.entity_type}]"
        result = result[: e.start] + placeholder + result[e.end :]

    return result


# ---------------------------------------------------------------------------
# Extraction + PII pipeline
# ---------------------------------------------------------------------------

def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF using cocoapdf and return it as a string."""
    result = convert_file(pdf_path, ConvertOptions())
    return result.markdown


def process_pdf(pdf_path: str, identifier: PIIIdentifier, masker: PIIMasker) -> tuple[str, list[PIIEntity], str]:
    """
    Full pipeline: extract text, identify PII, mask it.

    Returns (original_text, entities, masked_text).
    """
    text = extract_text(pdf_path)
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
    parser.add_argument("--masker", choices=["offset", "text"], default=None,
                    help="Masking strategy (default: auto-select based on --model)")
    args = parser.parse_args()

    # Select and instantiate the pluggable identifier
    identifier = make_identifier(
        kind=args.model,
        model_name=args.checkpoint,
        exclude_types={"USERAGENT", "ORG", "JOBTITLE", "COMPANYNAME", "JOBAREA", "JOBTYPE"},
    )
    masker_kind = args.masker or ("text" if args.model == "llm" else "offset")
    masker = make_masker(masker_kind)

    original, entities, masked = process_pdf(args.pdf, identifier, masker)

    print("=" * 60)
    print("ORIGINAL TEXT")
    print("=" * 60)
    print(original[:2000])  # preview only
    print()
    if entities is None:
        return
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
