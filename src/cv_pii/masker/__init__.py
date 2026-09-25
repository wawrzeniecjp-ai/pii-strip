from typing import Callable, Optional

from .base import PIIMasker
from .offset import OffsetMasker
from .text_search import TextSearchMasker


_REGISTRY: dict[str, Callable[..., PIIMasker]] = {
    "offset": OffsetMasker,
    "text": TextSearchMasker,
}


def make_masker(
    kind: str = "offset",
    model: Optional[str] = None,
    **kwargs,
) -> PIIMasker:
    """
    Construct a masker.

    `model` is accepted for uniformity with the other factories and
    is forwarded to the constructor. Maskers that don't use a model
    accept and ignore it.
    """
    if kind not in _REGISTRY:
        raise ValueError(
            f"Unknown masker kind: {kind!r}. "
            f"Known: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[kind](model=model, **kwargs)


def available_maskers() -> list[str]:
    return sorted(_REGISTRY)