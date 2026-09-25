""" identifier/llm.py: LLMIdentifier implementation """

import re
from pydantic import BaseModel
from typing import List, Optional
from .base import PIIIdentifier
from cv_pii.data import PIIEntity, _normalize_label
from ollama import chat

from cv_pii.log import get_logger
log = get_logger(__name__)

# JSON output schema for the LLM - no character offsets 
# as LLMs are not useful for that
class PIIEntitySchema(BaseModel):
    entity_type: str
    text: str
    score: float


class PIIResponse(BaseModel):
    entities: List[PIIEntitySchema]


ORG_MARKERS = re.compile(
    r"\b(University|College|Institute|School|Academy|"
    r"Inc\.?|LLC|Corp\.?|Ltd\.?|Group|Partners|Studios|"
    r"Solutions|Systems|Services|Technologies|Labs|"
    r"Consulting|Analytics|Software|Financial|Insurance|"
    r"Manufacturing|Logistics|Biotech|Pharmaceuticals)\b",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?"          # optional country code
    r"(?:\(?\d{2,4}\)?[-.\s]?)"        # area code, with or without parens
    r"\d{2,4}[-.\s]?\d{2,4}"           # subscriber digits
    r"(?:\s*(?:x|ext\.?)\s*\d+)?"      # optional extension
)

def _looks_like_org(text: str) -> bool:
    return bool(ORG_MARKERS.search(text))

_prompt_template = """Task: Extract ALL personally identifying information from a CV, including
information about people OTHER than the candidate.

Entities:
- CANDIDATE_NAME: the CV owner's name (first, last, or full)
- CANDIDATE_EMAIL: the CV owner's email
- CANDIDATE_PHONE: the CV owner's phone
- CANDIDATE_ADDRESS: the CV owner's address
- CANDIDATE_DOB: the CV owner's date of birth
- CANDIDATE_URL: the CV owner's LinkedIn, GitHub, personal site
- CANDIDATE_GOV_ID: the CV owner's SSN, passport, driver's license

- THIRD_PARTY_NAME: an identifiable individual mentioned by name
  (co-author, referee, supervisor, collaborator). Must be a proper
  noun naming a specific person.
  NOT: counts of people ("12 junior engineers"), roles ("the hiring manager"),
  or generic descriptions ("my team").
- THIRD_PARTY_EMAIL: any other person's email
- THIRD_PARTY_PHONE: any other person's phone

How to tell candidate from third party:
- The candidate's name appears in the header, in the contact line, or as a
  publication author alongside the CV content.
- The candidate is the subject of the CV's narrative (summary, experience).
- Everyone else is THIRD_PARTY.

DO NOT extract (preserve these in the text):
- Company names (employers): e.g., "Atlantic Software", "Redwood Financial"
- Company locations: cities and countries in the EXPERIENCE section
  that describe where the employer is based (e.g., "London, UK" next to
  a company name). These are NOT the candidate's address.
- University / school names: e.g., "Pennsylvania State University", "MIT"
- Job titles: e.g., "Senior Software Engineer", "Data Scientist"
- Skills, technologies, languages: e.g., "Python", "AWS", "English"
- Years and date ranges: e.g., "2019 - 2023"
- Publication venues: e.g., "Nature Methods", "NIPS"
- Counts or descriptions of unnamed people: "12 junior engineers",
  "a team of 5", "the recruiter", "3 direct reports"

ADDRESS detection:
- Any line containing a city/country pair like "City, Country"
- Any line in the contact block with a location-like fragment
- "City, State" or "City, Country" patterns, even if the city name
  is unusual or unfamiliar
- The candidate's location is often on the same line as email and phone

Publications:
- Extract ALL named authors, including those separated by commas and "and"
- Format example: "Alice Smith, Bob Jones and Carol Lee" contains three
  person names to extract
- Even if only one author is the candidate, extract the others as
  THIRD_PARTY_NAME

Note: The same person's name may appear in different forms:
- Full name in the header ("Robert Down")
- With middle initials in publications ("Robert J. Down")
- Initials only ("R. Down")
- Informal variants ("Bob Down")

Extract each occurrence with its own entity_type label. Do not try to
merge them — the masking layer will handle them as separate entities.

Return JSON with an "entities" array. Each entity has:
- entity_type: string
- text: string (exact substring from the input)
- score: float 0–1

Example:
Input:
    # Robert Down
    robert.down@gmail.com | 555-1234-154 | New Crestview, Portugal

    ## EXPERIENCE
    - Jun 2018 - Mar 2025 | Principal Scientist
    Scheider Electric Corp. | London, UK
      - Mentored 12 junior engineers and ran code reviews

    - Sep 2011 - May 2018 | Junior Data Scientist
    Auchamps S.A. | Toulouse, France
      - Collaborated with Doug Bessent on the migration project

    ## PUBLICATIONS
    Two dimensional manifold in Fourier spaces. Robert J. Down, Kim Jung and Denis J.E. Lambert. Nature Methods, 2023.

    ## REFERENCES
    Dr. Luc Dupont — ldupont@uniparis.edu

Output:
    {{"entities": [
      {{"entity_type": "CANDIDATE_NAME", "text": "Robert Down", "score": 0.95}},
      {{"entity_type": "CANDIDATE_EMAIL", "text": "robert.down@gmail.com", "score": 0.95}},
      {{"entity_type": "CANDIDATE_PHONE", "text": "555-1234-154", "score": 0.9}},
      {{"entity_type": "CANDIDATE_ADDRESS", "text": "New Crestview, Portugal", "score": 0.85}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Doug Bessent", "score": 0.9}},
      {{"entity_type": "CANDIDATE_NAME", "text": "Robert J. Down", "score": 0.9}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Kim Jung", "score": 0.9}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Denis J.E. Lambert", "score": 0.9}},
      {{"entity_type": "THIRD_PARTY_NAME", "text": "Luc Dupont", "score": 0.85}},
      {{"entity_type": "THIRD_PARTY_EMAIL", "text": "ldupont@uniparis.edu", "score": 0.9}}
    ]}}

CV content:
```markdown
{}
```
"""

# ---------------------------------------------------------------------------
# LLM identifier
# ---------------------------------------------------------------------------
class LLMIdentifier(PIIIdentifier):
    def __init__(
        self,
        model: str = "gemma3:4b",
        threshold: float = 0.5,
        exclude_types: Optional[set] = None,
    ):
        self.model = model
        self.threshold = threshold
        self.exclude_types = {t.upper() for t in (exclude_types or set())}

    def identify(self, text: str) -> List[PIIEntity]:
        prompt = _prompt_template.format(text)
        response = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=PIIResponse.model_json_schema(),
            options={
                "temperature": 0,
                "num_predict": 8192,
                "num_ctx": 16384,
                "stop": ["<|im_end|>", "<|endoftext|>", "<|im_start|>"],
                "repeat_penalty": 1.2,      # 1.1 by default
                "repeat_last_n": 128,       # look back further
            }
        )
        log.debug("done_reason: %s, eval_count: %d", response.done_reason, response.eval_count)
        log.debug("---------------------- LLM OUTPOUT -----------------------")
        log.debug("%s", response.message.content)
        log.debug("----------------------------------------------------------")
        parsed = PIIResponse.model_validate_json(response.message.content)

        entities: List[PIIEntity] = []
        seen_spans: set[tuple[int, int]] = set()

        def _add(label: str, start: int, end: int, text: str, score: float):
            key = (start, end)
            if key in seen_spans:
                return
            seen_spans.add(key)
            entities.append(PIIEntity(
                entity_type=label,
                start=start,
                end=end,
                text=text,
                score=score,
            ))

        # --- 1. LLM entities -------------------------------------------
        for e in parsed.entities:
            if e.score < self.threshold:
                continue
            label = _normalize_label(e.entity_type)
            if label in self.exclude_types:
                log.debug("Ignoring excluded entity: {}".format(label))
                continue

            # Filter: a *_NAME label that looks like an org is a false positive
            if label.endswith("_NAME") and _looks_like_org(e.text):
                log.debug("Ignoring org-like entity: {}".format(e.text))
                continue

            pattern = re.compile(
                r"\b" + re.escape(e.text) + r"\b",
                flags=re.IGNORECASE,
            )
            for match in pattern.finditer(text):
                _add(label, match.start(), match.end(),
                     match.group(), e.score)

        # --- 2. Phone regex safety net ---------------------------------
        # Only add if no CANDIDATE_PHONE / THIRD_PARTY_PHONE entity
        # already covers the same span (the seen_spans check handles this).
        for match in PHONE_PATTERN.finditer(text):
            candidate = match.group().strip()
            # Skip very short matches (likely false positives from dates)
            if len(re.sub(r"\D", "", candidate)) < 7:
                continue
            _add("CANDIDATE_PHONE", match.start(), match.end(),
                 candidate, 1.0)

        return entities
    
