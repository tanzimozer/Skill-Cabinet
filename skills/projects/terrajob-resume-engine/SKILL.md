---
name: terrajob-resume-engine
description: TerraJob resume generation with strict spec compliance and validation gates
trigger: TerraJob resume generation, resume tailoring, job application automation
---

# TerraJob Resume Engine

Resume generation system with strict spec compliance. Lives in `TERRAjob.V2-personal` repo.

## Critical Rule

**READ THE SPEC DOCS FIRST** before any implementation. The repo contains authoritative spec files — don't build from scratch.

## Spec Documents (Stage_2_Resume_Tailoring/)

| File | Purpose |
|------|---------|
| `tanzim_resume_instructions_1of8.md` | Pipeline overview, trigger logic |
| `tanzim_resume_purpose_2of8.md` | Mission, test contracts T-1 to T-20, error codes |
| `tanzim_resume_layout_5of8.md` | Visual spec: geometry, typography, colors, spacing |
| `tanzim_resume_deedy_layout_6of8.md` | Two-column LaTeX format spec |
| `tanzim_resume_soul_7of8.md` | P1-P12 summary protocols, bullet selection, no-wrap rewrite |
| `tanzim_resume_profile_4of8.json` | User profile data (source of truth) |

## Test Contracts (must pass)

| ID | Constraint |
|----|------------|
| T-1 | Page count == 1 |
| T-2 | Every bullet 121-123 chars (target 122) |
| T-3 | No bullet wraps in rendered PDF |
| T-9 | Summary ≤220 chars |
| T-15 | Font === Calibri (no substitution) |

## Hard Limits

- **Bullets**: Target 122 chars, but **117 is the wrap-safe ceiling** (spec section 8.3: "bullets ≤117 chars are wrap-safe regardless of character mix"). Anything 118+ risks wrapping.
- **Max fill principle**: Fill bullets as close to 117 as possible — no white space, no wrap. Target 115-117 chars.
- **Summary**: ≤220 chars total
- **Skills**: 6 core (locked) + ≤15 swappable = 21 max (reduce swappable first when overflowing)
- **Bullets per role**: 5 default (4 scored + 1 closer), reduce to 4 under overflow
- **Roles**: 4 max
- **Page**: 1 STRICT — apply overflow ladder, never relax geometry

## Page Overflow Ladder (apply in order until 1-page fit)

| Step | Action |
|------|--------|
| 1 | Trim swappable skills 15 → 12 |
| 2 | Trim swappable skills 12 → 10 |
| 3 | Trim swappable skills 10 → 8 |
| 4 | Trim swappable skills 8 → 6 → 4 |
| 5 | Drop closer bullet from oldest role |
| 6 | Reduce bullets per role 5 → 4 |
| 7 | Trim certifications |
| 8 | Trim projects |

**Never**: shrink fonts, reduce margins, add italics. Trim content only.

## Spec Cross-Match Validation

Before shipping ANY resume, cross-match these constants against the spec (Section 15):

```python
SPEC = {
    'BULLET_TARGET': 122,       # Density target
    'BULLET_WRAP_SAFE': 117,    # Actual max (use this!)
    'SUMMARY_MAX': 220,
    'SKILLS_MAX': 21,
    'CORE_SKILLS': 6,
    'ROLES': 4,
    'BULLETS_PER_ROLE': 5,
    # Spacing (twips)
    'SP_NAME': (0, 60),
    'SP_CONTACT': (0, 60),
    'SP_SECTION': (100, 20),
    'SP_ROLE': (80, 20),
    'SP_BULLET': (10, 10),
}

## No-Wrap Rewrite Protocol (bullet compression)

Apply in order until bullet fits:
1. Drop filler adverbs (all, various, successfully, consistently)
2. Replace verbose prepositions (through → via, across all → across)
3. Compress verb phrases (ensuring coordination → coordinating)
4. Compress noun phrases (multi-site operations → multi-site ops)
5. Drop lowest-value descriptor
6. Drop lowest-value clause entirely

## Typography (from layout spec)

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Name | Calibri | 38pt | Bold, ALL CAPS, centered |
| Contact | Calibri | 10.5pt | Regular, pipe-delimited |
| Section header | Calibri | 12.5pt | Bold, ALL CAPS, bottom border |
| Body/bullets | Calibri | 10.5pt | Regular, justified |

## Pipe Colors

- `#666666` (dark): contact line, role headers
- `#999999` (light): skills, certs, projects, education

## Output Files (per JD)

1. `{LastName}_{FirstName}_{Company}.docx` — ATS submission
2. `{LastName}_{FirstName}_{Company}.pdf` — PDF version
3. `{LastName}_{FirstName}_{Company}_CoverLetter.docx` — Cover letter
4. `{LastName}_{FirstName}_{Company}_Deedy.pdf` — Visual companion (LaTeX)

## References

- `references/profile-json-mapping.md` — Field name mapping between spec docs and actual JSON
- `references/1page-engine-pattern.md` — Working 1-page engine pattern with overflow-safe constants

- `references/fluxjob-architecture.md` — FLUXJOB fork architecture, content/render split, QC gate rules
- `references/fluxjob-efficiency-patterns.md` — Token reduction, retry, batch sheet write, compiled context pattern

## CRITICAL: Tanzim's Process Expectation

Tanzim is **extremely strict** about spec compliance. When he says "read the spec again":
1. Stop and re-read ALL spec docs end-to-end (1of8 through 7of8)
2. Cross-match EVERY constant against actual values in spec Section 15
3. Validate output against EVERY test contract before shipping
4. If it doesn't pass validation, iterate — don't ship broken output

The **iterate-until-pass** loop is expected. Never ship on first attempt if validation fails.

## FLUXJOB — Optimised Fork

`FLUXJOB` is a fork of `TERRAjob.V2-personal` at `github.com/tanzimozer/FLUXJOB` with:
- `FLUXJOB_CONTEXT_COMPILED.md` — 288-line compiled context (vs 1,413 lines across 8 files)
- `fluxjob_run.py` — orchestrator with parallel workers, content/render separation, QC gate
- `FLUXJOB_CLAUDE_WORKER_PROMPT.md` — Claude content-worker brief
- All original files untouched

Use FLUXJOB for new runs. Use TERRAjob.V2-personal as source-of-truth for spec.

## DO NOT Touch the Repo

Tanzim's explicit rule: **never modify TERRAjob.V2-personal files**. All changes go in FLUXJOB.
When asked to "optimise the engine" — build alongside, not inside.

## FLUXJOB Pipeline Efficiency (critical lessons from June 2026)

When optimising the engine, these patterns produced the most gains — none change output:

| Fix | Before | After | Impact |
|-----|--------|-------|--------|
| Claude call method | `subprocess` string hack | Direct `anthropic` SDK | Reliability |
| Spec context load | 1,413 lines × N workers | 288-line compiled once | ~75% token reduction |
| OAuth token | Refreshed per upload | Cached, TTL-gated | No mid-batch 401s |
| Drive folder lookup | N API calls | Cached after first | N-1 fewer calls |
| Sheet write | 1 write per job | Batch all in one call | Scales to 50+ jobs |
| QC disk reads | Re-read JSON from disk | Pass dict in memory | Speed + correctness |
| Content/render split | Claude does both | Claude = JSON only, Python = files | Deterministic output |

**Compile context pattern:** Pre-process all 8 spec files into one `COMPILED_CONTEXT.md` (strip rationale, keep rules). Workers load this once. Never make workers load all 8 docs.

**Retry wrapper (always include):**
```python
def _retry(fn, attempts=3, delay=2.0):
    last: Exception = Exception("no attempts")
    for i in range(attempts):
        try: return fn()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503): last = e; time.sleep(delay*(i+1))
            else: raise
        except Exception as e: last = e; time.sleep(delay*(i+1))
    raise last
```

## Pitfalls

- **Don't build output files from scratch** — Claude outputs `resume_data.json`, Python renders. Never reverse this.
- **Profile JSON structure differs from spec naming** — check actual keys (e.g., `default_title` not `title`, `core_skills` not `skills.core`)
- **Validation must gate output** — if T-2 fails, iterate/compress; never ship broken resume
- **LibreOffice may not be installed** — have fallback for PDF conversion
- **122 vs 117 confusion** — Spec says "target 122" but also "≤117 is wrap-safe". USE 117 AS THE CEILING. Bullets at 118+ WILL wrap depending on character mix.
- **Spacing drift causes overflow** — When reducing spacing to fit 1 page, you break the spec. Instead, reduce CONTENT via overflow ladder while keeping EXACT spacing values.
- **Read spec end-to-end before each rebuild** — Don't assume you remember the values; cross-match every constant against Section 15.
