from typing import Callable

from .base import PIIMasker
from .offset import OffsetMasker
from .text_search import TextSearchMasker


_REGISTRY: dict[str, Callable[..., PIIMasker]] = {
    "offset": OffsetMasker,
    "text": TextSearchMasker,
}


def make_masker(kind: str = "offset", **kwargs) -> PIIMasker:
    if kind not in _REGISTRY:
        raise ValueError(
            f"Unknown masker kind: {kind!r}. "
            f"Known: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[kind](**kwargs)


def available_maskers() -> list[str]:
    return sorted(_REGISTRY)