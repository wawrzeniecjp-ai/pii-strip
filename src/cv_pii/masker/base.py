""" masker/base.py: PIIMasker Interface"""

from typing import List

from abc import ABC, abstractmethod
from cv_pii.data import PIIEntity

# ---------------------------------------------------------------------------
# Masker interface
# ---------------------------------------------------------------------------
class PIIMasker(ABC):
    @abstractmethod
    def mask(self, text: str, entities: List[PIIEntity]) -> str: ...


