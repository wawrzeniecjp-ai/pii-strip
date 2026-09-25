""" identifier/shield.py: ShieldIdentifier implementation """

from typing import List, Optional
from transformers import pipeline
from .base import PIIIdentifier
from cv_pii.data import PIIEntity

from cv_pii.log import get_logger
log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shield identifier
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
