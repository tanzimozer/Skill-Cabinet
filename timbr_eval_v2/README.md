# TIMBR Eval Harness v2

A two-tier eval: fast deterministic gates for anything mechanical, a rubric-driven judge for
anything that's actually a judgment call. Sits alongside `../timbr_eval/` (v1) rather than
deleting it — v1's ProhibLint hard gates were sound and are absorbed here; only its VoiceLint
scorer is replaced.

## Why v2 exists

Running v1 against the "Inside Taylor Crow Studio" article (shipped live to TIMBR | Fitness
Magazine) surfaced a real bug: `voicelint.score_people()` and `score_fitt()` both start every
section at a baseline of **100** before counting anything, and their positive-match patterns
(`\b(?:who|whose|her|his|she|he)\s+[a-z]+`, sentence-start capitalization, paragraphs over 40
words) fire on ordinary prose almost unconditionally. The result: any section that names a
person or writes in normal paragraph lengths scores ~100 on "people" and ~60-100 on "fitt"
regardless of what it actually says, which triggers automatic cross-contamination penalties
against whatever voice the section actually required (`CROSS_CONTAMINATION_THRESHOLD = 5`,
i.e. any score over 50 counts as contamination). The Training section above scored 80/100 only
because two of these were basically guaranteed to fire — it would have scored the same on a
noticeably worse draft, and there was no way to tell from the number alone.

The deeper issue: **voice, editorial value, and factual accuracy are judgment calls.** No
amount of regex tuning turns a keyword counter into a reader. TIMBR already has a working
answer to this — Maya, the Editor-in-Chief persona in `skills/timbr/timbr_magazine_eic`, who
reasons over a 12-point checklist and a double AI-detection gate for the print magazine. v2 is
that same idea, operationalized into a runnable, auditable, schema-validated contract instead
of a persona doc with no code behind it, and extended to cover Wix blog posts (which Maya's
checklist doesn't address — it's magazine-issue-specific).

## What changed from v1

| | v1 | v2 |
|---|---|---|
| Hard gates (em-dash, banned words, word count) | ✅ kept, `hardgate.py` | ✅ same logic, extended banned-vocab list (merged with Maya's) |
| Voice scoring | Regex keyword-fingerprint, baseline 100, near-unavoidable cross-contamination | Rubric-based judge, evidence required for any score < 100 |
| Factual/venue accuracy | Not checked at all | New Tier-2 dimension, operationalizes [[timbr_venue_preflight]]'s certainty rule as a hard fail on hedge language |
| Seattle specificity | Not checked at all | New Tier-2 dimension, from Maya's checklist item 6 |
| AI-pattern detection | Not checked at all | New Tier-2 dimension (rule-of-three overuse, generic transitions, listicle cadence) — a lightweight stand-in for Maya's GPTZero gate, since this harness has no external API budget |
| Content types supported | 7 fixed magazine sections only | Magazine sections + Wix blog categories (Guide/Training/Culture) + product/venue card copy |
| Output | Single blended score per section | Per-dimension score + verdict + quoted evidence, never blended |
| Calibration | None | `calibration/` — one known-good, one deliberately-bad passage, checked into the repo with expected output |

## How to run it

**Step 1 — Tier 1 (instant, free, run this first on every draft):**

```bash
python3 orchestrator.py --text draft.md --content-type blog_training
```

Content types: `blog_the_guide`, `blog_training`, `blog_culture`, `magazine_nutrition_spot`,
`magazine_fitness_spot`, `magazine_location_spot`, `product_venue_card`, `unspecified`.

If Tier 1 fails, fix it before spending any judge effort — a piece with banned words or the
wrong word count doesn't need a rubric read to know it's not ready.

**Step 2 — Tier 2 (requires an LLM judge in the loop):**

Brief a Claude instance with `RUBRIC.md` and `judge_schema.render_judge_prompt(text,
research_trail)`. The judge's job is to produce a JSON object matching the schema in
`judge_schema.py` — six dimensions, each scored 0-100 with a verdict and, for anything under
100, at least one quoted excerpt as evidence. This is not optional theater: `validate_judge_output()`
rejects output that's missing evidence or has a score/verdict mismatch.

```python
from judge_schema import render_judge_prompt
prompt = render_judge_prompt(text, research_trail="verified via WebFetch of taylorcrowstudio.com, ...")
# hand `prompt` to a Claude judge, save its JSON response to judge_output.json
```

```bash
python3 orchestrator.py --text draft.md --content-type blog_training \
    --judge judge_output.json --out scorecard.json
```

**CI mode:** `--ci` prints only the overall verdict and sets the exit code (0 = PASS, 1 = anything
else), for use in an agent pipeline gate.

## Files

- `RUBRIC.md` — the spec. Read this before touching any code here.
- `hardgate.py` — Tier 1, deterministic, no LLM needed.
- `judge_schema.py` — Tier 2 output contract + validator + the prompt template used to brief a judge.
- `orchestrator.py` — combines both tiers into one scorecard, CLI entry point.
- `calibration/` — proof the harness discriminates; see `calibration_report.md`.

## Non-goals

This does not call GPTZero or any paid third-party API — Maya's real Gate 1 stays a manual step
for print issues. `ai_pattern_detection` is a structural heuristic stand-in, not a replacement
for an actual AI-detection service, and should be treated as advisory rather than as strong as
the deterministic Tier-1 gates.
