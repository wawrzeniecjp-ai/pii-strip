from cocoapdf import ConvertOptions, convert_file
from .base import TextExtractor

from cv_pii.log import get_logger
log = get_logger(__name__)

class CocoapdfExtractor(TextExtractor):
    def __init__(self, options: ConvertOptions | None = None):
        self.options = options or ConvertOptions()

    def extract(self, path: str) -> str:
        result = convert_file(path, self.options)
        log.debug("Extracted text:")
        log.debug("%s", result.markdown)
        return result.markdown