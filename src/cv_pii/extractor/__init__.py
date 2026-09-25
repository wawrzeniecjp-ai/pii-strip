from .base import TextExtractor
from .cocoapdf import CocoapdfExtractor

_REGISTRY = {
    "cocoapdf": CocoapdfExtractor,
}


def make_extractor(kind: str = "cocoapdf", **kwargs) -> TextExtractor:
    if kind not in _REGISTRY:
        raise ValueError(f"Unknown extractor: {kind!r}. Known: {sorted(_REGISTRY)}")
    return _REGISTRY[kind](**kwargs)


def available_extractors() -> list[str]:
    return sorted(_REGISTRY)