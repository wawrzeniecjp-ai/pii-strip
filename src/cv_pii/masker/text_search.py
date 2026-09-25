""" masker/text_search.py: TextSearchMasker implementation

    This masker works without character offsets, and instead
    searches the original text to find entities to be masked.
"""

from typing import Optional

from typing import List
from .base import PIIMasker
from cv_pii.data import PIIEntity

from cv_pii.log import get_logger
log = get_logger(__name__)

class TextSearchMasker(PIIMasker):
    def __init__(self, model: Optional[str] = None, replace_all: bool = True):
        self.model = model  # unused
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
