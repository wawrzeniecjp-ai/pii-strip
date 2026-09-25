"""
Data models for job matching.

These are the shapes returned by JobMatcher implementations. They are
intentionally structured (not just a score) so downstream consumers can
reason about *why* a match was made.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    """A single skill mentioned in the JD, and whether the CV covers it."""

    skill: str = Field(description="The skill or requirement as stated in the JD")
    matched: bool = Field(description="True if the CV demonstrably covers it")
    evidence: Optional[str] = Field(
        default=None,
        description="A short quote or paraphrase from the CV supporting the match. "
                    "None when matched is False.",
    )


class MatchResult(BaseModel):
    """Structured output of a CV-to-job match."""

    score: float = Field(
        ge=0.0, le=1.0,
        description="Overall fit score, 0 (poor) to 1 (excellent)",
    )
    summary: str = Field(
        description="Two or three sentences explaining the score",
    )
    matched_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="JD requirements the CV covers",
    )
    missing_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="JD requirements the CV does not cover",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any caveats, e.g. ambiguity in the JD or the CV",
    )