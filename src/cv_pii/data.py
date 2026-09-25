""" data.py: Data & Data procesing abstractions """

from dataclasses import dataclass

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


# Ignored entities
DEFAULT_EXCLUDE_TYPES = {"USERAGENT", "ORG", "JOBTITLE", "COMPANYNAME", "JOBAREA", "JOBTYPE"}