from abc import ABC, abstractmethod

from .data import MatchResult


class JobMatcher(ABC):
    """Abstract base class for CV-to-job matching strategies."""

    @abstractmethod
    def match(self, cv_text: str, job_description: str) -> MatchResult:
        """
        Match a (typically anonymized) CV against a job description.

        cv_text: the CV content, usually the output of a masker
        job_description: the JD text

        Returns a MatchResult. Implementations should not raise on
        "no match" — return a low score instead.
        """
        ...