"""
LLM-backed job matcher.

Given an (anonymized) CV and a job description, produces a structured
MatchResult via a local or cloud LLM.
"""

from typing import Optional

from ollama import chat

from cv_pii.log import get_logger
from .base import JobMatcher
from .data import MatchResult

log = get_logger(__name__)


PROMPT_TEMPLATE = r"""Task: Match a candidate's CV against a job description.

You are given two documents:
1. The candidate's CV (may be anonymized — names and contact info
   replaced with placeholders like [CANDIDATE_NAME])
2. The job description (JD)

Your job is to assess how well the candidate fits the role, based
ONLY on the information present in the CV. Do not invent qualifications.

Process:
- Read the JD and extract the concrete requirements: skills, tools,
  years of experience, domain knowledge, responsibilities.
- For each requirement, check whether the CV provides evidence.
- Score the overall fit as a float between 0 and 1:
    0.0–0.3  poor fit — most requirements missing
    0.3–0.6  partial fit — some overlap, notable gaps
    0.6–0.8  good fit — most requirements covered
    0.8–1.0  excellent fit — strong evidence for nearly all requirements

Return JSON with:
- score: float 0–1
- summary: 2–3 sentences explaining the score
- matched_skills: list of requirements the CV covers. Each has:
    - skill: the requirement as stated in the JD
    - matched: true
    - evidence: a short quote or paraphrase from the CV
- missing_skills: list of requirements the CV does not cover. Each has:
    - skill: the requirement as stated in the JD
    - matched: false
    - evidence: null
- notes: any caveats about ambiguity in either document, or null

Example:

JD:
    Senior Backend Engineer. 5+ years Python. Experience with
    PostgreSQL and AWS required. Kubernetes a plus.

CV (excerpt):
    ## EXPERIENCE
    Senior Software Engineer, 2019–2024
    - Built REST APIs in Python serving 2M requests/day
    - Migrated legacy database to PostgreSQL (2019)
    - Deployed services on AWS ECS

Output:
    {{"score": 0.85,
     "summary": "Strong backend background with the required Python and \
PostgreSQL experience. AWS experience is present but via ECS rather \
than the broader AWS stack. No Kubernetes mentioned.",
     "matched_skills": [
       {{"skill": "5+ years Python", "matched": true,
         "evidence": "Built REST APIs in Python serving 2M requests/day"}},
       {{"skill": "PostgreSQL", "matched": true,
         "evidence": "Migrated legacy database to PostgreSQL"}},
       {{"skill": "AWS", "matched": true,
         "evidence": "Deployed services on AWS ECS"}}
     ],
     "missing_skills": [
       {{"skill": "Kubernetes", "matched": false, "evidence": null}}
     ],
     "notes": "5+ years of Python experience is inferred from the \
2019–2024 role duration; no earlier Python experience is shown."}}

Job Description:
{job_description}

CV:
{cv_text}
"""


class LLMJobMatcher(JobMatcher):
    """
    Job matching via an LLM. Defaults to a local Ollama model.

    The CV is expected to be anonymized already (the output of a PIIMasker).
    If you pass an unmasked CV, the LLM will see the candidate's PII.
    """

    DEFAULT_MODEL = "gemma3:4b"
    DEFAULT_TEMPERATURE = 0.0

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        num_predict: int = 4096,
        num_ctx: int = 16384,
    ):
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict
        self.num_ctx = num_ctx

    def match(self, cv_text: str, job_description: str) -> MatchResult:
        prompt = PROMPT_TEMPLATE.format(
            cv_text=cv_text,
            job_description=job_description,
        )

        log.debug("Matching CV (%d chars) against JD (%d chars) via %s",
                  len(cv_text), len(job_description), self.model)

        response = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=MatchResult.model_json_schema(),
            options={
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "num_ctx": self.num_ctx,
                "stop": ["<|im_end|>", "<|endoftext|>", "<|im_start|>"],
                "repeat_penalty": 1.2,
                "repeat_last_n": 128,
            },
        )

        log.debug("Matcher done_reason=%s eval_count=%s content_len=%d",
                  response.done_reason,
                  response.eval_count,
                  len(response.message.content or ""))

        raw = response.message.content
        if not raw or not raw.strip():
            log.warning("Empty matcher response; returning zero score")
            return MatchResult(
                score=0.0,
                summary="Matcher returned no output.",
                matched_skills=[],
                missing_skills=[],
                notes="LLM returned an empty response.",
            )

        return MatchResult.model_validate_json(raw)