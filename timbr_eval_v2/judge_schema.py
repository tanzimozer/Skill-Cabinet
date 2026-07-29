"""
judge_schema.py — the structured output contract for Tier-2 (RUBRIC.md judge
dimensions) and the prompt template used to brief a judge.

Tier 2 requires reasoning, not regex — voice, editorial value, and factual
integrity are judgment calls (see RUBRIC.md "Design principles" #1). This
module does not run a judge itself; it defines exactly what a judge's output
must look like so orchestrator.py can validate and combine it with Tier 1
deterministically. In practice the judge is an LLM (a Claude instance)
briefed with JUDGE_PROMPT_TEMPLATE, the same way Maya (skills/timbr/
timbr_magazine_eic) already reasons over the print magazine's 12-point
checklist — this just gives that reasoning a validated, auditable shape.
"""

DIMENSIONS = [
    "voice_brand_compliance",
    "structural_format_compliance",
    "editorial_value",
    "factual_venue_integrity",
    "seattle_local_specificity",
    "ai_pattern_detection",
]

VALID_VERDICTS = {"PASS", "NEEDS_REVISION", "FAIL", "UNSCORABLE"}


def score_to_verdict(score):
    if score is None:
        return "UNSCORABLE"
    if score >= 70:
        return "PASS"
    if score >= 40:
        return "NEEDS_REVISION"
    return "FAIL"


def validate_judge_output(obj):
    """
    Validates a judge output dict against the contract. Returns (ok, errors).
    Expected shape:
    {
      "dimensions": {
        "<dimension_name>": {
          "score": 0-100 or null (null only allowed for factual_venue_integrity when UNSCORABLE),
          "verdict": "PASS" | "NEEDS_REVISION" | "FAIL" | "UNSCORABLE",
          "evidence": ["quoted excerpt", ...],   # required if score < 100
          "rationale": "1-3 sentence explanation"
        },
        ...
      }
    }
    """
    errors = []
    if not isinstance(obj, dict) or "dimensions" not in obj:
        return False, ["Missing top-level 'dimensions' key."]

    dims = obj["dimensions"]
    for name in DIMENSIONS:
        if name not in dims:
            errors.append(f"Missing dimension: {name}")
            continue
        d = dims[name]
        score = d.get("score")
        verdict = d.get("verdict")
        evidence = d.get("evidence", [])
        rationale = d.get("rationale", "")

        if verdict not in VALID_VERDICTS:
            errors.append(f"{name}: invalid verdict '{verdict}'")

        if name == "factual_venue_integrity" and verdict == "UNSCORABLE":
            pass  # allowed: no research trail available
        elif score is None:
            errors.append(f"{name}: score is required (only factual_venue_integrity may be UNSCORABLE)")
        elif not (0 <= score <= 100):
            errors.append(f"{name}: score {score} out of range 0-100")
        else:
            expected_verdict = score_to_verdict(score)
            if verdict != expected_verdict:
                errors.append(
                    f"{name}: score {score} implies verdict {expected_verdict}, got {verdict}"
                )

        if score is not None and score < 100 and not evidence:
            errors.append(f"{name}: score {score} < 100 requires at least one evidence quote")

        if not rationale:
            errors.append(f"{name}: rationale is required")

    return (len(errors) == 0), errors


JUDGE_PROMPT_TEMPLATE = """\
You are grading TIMBR editorial copy against RUBRIC.md Tier 2 (six judge \
dimensions). Read the full rubric first — do not rely on memory of it.

TEXT TO GRADE:
---
{text}
---

RESEARCH TRAIL (for factual_venue_integrity — omit if none was captured this \
session; if omitted, that dimension must be scored UNSCORABLE, not guessed):
---
{research_trail}
---

For each of the six dimensions in RUBRIC.md Tier 2, output a JSON object \
matching this exact shape (see judge_schema.py validate_judge_output for the \
full contract):

{{
  "dimensions": {{
    "voice_brand_compliance": {{"score": <0-100>, "verdict": "<PASS|NEEDS_REVISION|FAIL>", "evidence": ["..."], "rationale": "..."}},
    "structural_format_compliance": {{...}},
    "editorial_value": {{...}},
    "factual_venue_integrity": {{...}},
    "seattle_local_specificity": {{...}},
    "ai_pattern_detection": {{...}}
  }}
}}

Rules:
- A score of 100 needs no evidence. Any score below 100 REQUIRES at least one \
  quoted excerpt from the text showing what cost points.
- verdict must match the score band exactly: 70-100=PASS, 40-69=NEEDS_REVISION, \
  0-39=FAIL. Except factual_venue_integrity may be UNSCORABLE with score=null \
  if no research trail was provided.
- Do not blend dimensions into one number. Score all six independently.
- Be the skeptic, not the cheerleader — this rubric exists because a lenient \
  automated grader let 56 posts ship at half the intended word count and let \
  a founder-biography voice trap through undetected. Err toward NEEDS_REVISION \
  over PASS when genuinely unsure.
"""


def render_judge_prompt(text, research_trail=""):
    return JUDGE_PROMPT_TEMPLATE.format(text=text, research_trail=research_trail or "(none provided)")
