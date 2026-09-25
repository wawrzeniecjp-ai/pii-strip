"""
Job matcher registry.

Mirrors the pattern used by cv_pii.identifier and cv_pii.masker:
a dict of kind -> class, a factory function, and an availability list.
"""

from typing import Callable, Optional

from .base import JobMatcher
from .llm import LLMJobMatcher


_REGISTRY: dict[str, Callable[..., JobMatcher]] = {
    "llm": LLMJobMatcher,
}


def make_matcher(
    kind: str = "llm",
    model: Optional[str] = None,
    **kwargs,
) -> JobMatcher:
    """
    Construct a job matcher.

    `model` is accepted for uniformity with the other factories and is
    forwarded to the constructor. Matchers that don't use a model accept
    and ignore it.
    """
    if kind not in _REGISTRY:
        raise ValueError(
            f"Unknown matcher kind: {kind!r}. "
            f"Known: {sorted(_REGISTRY)}"
        )
    # Only forward `model` if it was explicitly provided, so each matcher's
    # default is respected when the caller doesn't override it.
    if model is not None:
        kwargs["model"] = model
    return _REGISTRY[kind](**kwargs)


def available_matchers() -> list[str]:
    return sorted(_REGISTRY)