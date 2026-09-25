from .base import PIIIdentifier
from .shield import ShieldIdentifier
from .nerguard import NerGuardIdentifier
from .gliner import GlinerIdentifier
from .llm import LLMIdentifier
from typing import Callable, Optional

# Registry of identifier classes
# Each entry maps a kind string to a builder that takes (model_name, **kwargs)
_IDENTIFIER_REGISTRY: dict[str, Callable[..., PIIIdentifier]] = {
    "shield": lambda model_name, **kw: ShieldIdentifier(
        model_name=model_name or ShieldIdentifier.DEFAULT_MODEL, **kw
    ),
    "nerguard": lambda model_name, **kw: NerGuardIdentifier(
        model_name=model_name or NerGuardIdentifier.DEFAULT_MODEL, **kw
    ),
    "llm": lambda model_name, **kw: LLMIdentifier(
        model=model_name or "gemma3:4b", **kw
    ),
    "gliner": lambda model_name, **kw: GlinerIdentifier(
        model_name=model_name or GlinerIdentifier.DEFAULT_MODEL, **kw
    ),
}

# ---------------------------------------------------------------------------
# Factory function for identifiers
# ---------------------------------------------------------------------------
def make_identifier(kind: str, model_name: Optional[str] = None, **kwargs) -> PIIIdentifier:
    if kind not in _IDENTIFIER_REGISTRY:
        raise ValueError(
            f"Unknown identifier kind: {kind!r}. "
            f"Known: {sorted(_IDENTIFIER_REGISTRY)}"
        )
    return _IDENTIFIER_REGISTRY[kind](model_name, **kwargs)


def available_identifiers() -> list[str]:
    return sorted(_IDENTIFIER_REGISTRY)