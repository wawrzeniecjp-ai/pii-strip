""" identifier/nerguard.py: NerGuardIdentifier implementation """

from typing import List, Optional
from transformers import pipeline
from .base import PIIIdentifier
from cv_pii.data import PIIEntity, _normalize_label

from cv_pii.log import get_logger
log = get_logger(__name__)

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
