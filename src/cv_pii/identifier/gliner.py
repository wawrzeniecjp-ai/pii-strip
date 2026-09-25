""" identifier/gliner.py: GlinerIdentifier implementation """

from typing import List, Optional
from gliner import GLiNER

from cv_pii.data import PIIEntity, _normalize_label
from .base import PIIIdentifier

from cv_pii.log import get_logger
log = get_logger(__name__)

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
