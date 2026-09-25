""" extractor package: TextAbstractor interface """

from abc import ABC, abstractmethod


class TextExtractor(ABC):
    """
    Extract plain text (typically Markdown) from a document.

    Implementations should return a string suitable for feeding into
    a PIIIdentifier. The exact markup format (Markdown, plain text, HTML)
    is implementation-defined, but should be consistent across calls.
    """

    @abstractmethod
    def extract(self, path: str) -> str:
        """Return the extracted text."""
        ...