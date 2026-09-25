""" identifier/base.py: PIIIdentifier API"""

from cv_pii.data import PIIEntity
from abc import ABC, abstractmethod
from typing import List

from cv_pii.log import get_logger
log = get_logger(__name__)

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

