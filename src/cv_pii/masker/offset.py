""" masker/offset.py: OffsetMasker implementation
    
    This masker uses character offsets to find entities
    in the original text.
"""

from typing import List
from .base import PIIMasker
from cv_pii.data import PIIEntity

from cv_pii.log import get_logger
log = get_logger(__name__)

class OffsetMasker(PIIMasker):
    """Use entity.start / entity.end. Fast, precise, requires accurate offsets."""
    def mask(self, text: str, entities: List[PIIEntity]) -> str:
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
