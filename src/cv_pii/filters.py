""" filters.py: Tools for filtering entity types """

from typing import List, Optional

from cv_pii.identifier import PIIIdentifier
from cv_pii.data import PIIEntity

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