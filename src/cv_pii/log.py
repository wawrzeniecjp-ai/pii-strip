"""
Central logging configuration for the cv_pii package.

Usage:
    from cv_pii.log import get_logger

    log = get_logger(__name__)
    log.debug("something happened: %s", value)
    log.warning("unexpected: %s", thing)
"""

import logging as _logging
import sys
from typing import Optional


_CONFIGURED = False


def configure(level: str = "WARNING") -> None:
    """
    Configure the root cv_pii logger. Safe to call multiple times.

    level: one of "DEBUG", "INFO", "WARNING", "ERROR"
    """
    global _CONFIGURED

    root = _logging.getLogger("cv_pii")

    if not _CONFIGURED:
        handler = _logging.StreamHandler(sys.stderr)
        handler.setFormatter(_logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))
        root.addHandler(handler)
        _CONFIGURED = True

    root.setLevel(getattr(_logging, level.upper()))


def get_logger(name: Optional[str] = None) -> _logging.Logger:
    """Get a logger under the cv_pii namespace."""
    if name:
        # Ensure all our loggers share the cv_pii prefix so configure()
        # can control them with a single call.
        if not name.startswith("cv_pii."):
            name = f"cv_pii.{name}"
    else:
        name = "cv_pii"
    return _logging.getLogger(name)