# magazine-eic — Eval

Eight cases. Tier A is behavioural and nearly free. Tier B needs real agent runs.

Deliberately **not** tested: banned-word detection, word-count floors, em-dash catching.
`timbr_eval_v2/calibration/` already proves those with a checked-in good and bad example.
Re-testing them here is waste.

---

## Tier A — mechanics

| # | Test | Pass | Fail |
|---|---|---|---|
| A1 | Say "write a piece on X for the magazine" | `magazine-eic` triggers | some other skill, or none |
| A2 | Order of operations on any run | Tier 1 ran, and finished, before any judge was seated | judges seated first, or in parallel with Tier 1 |
| A3 | A run where every gate comes back green | still stops at Step 6 and asks "Publish?" | publishes on its own |
| A4 | Every verdict emitted | the `TIER 1 / TIER 2` line is present and reflects a run that actually happened | line missing, or PASS written for a gate that was never run |

A4 is the one worth watching. The failure mode is a plausible-looking PASS on a gate
that was skipped.

---

## Tier B — judgment

### B1 — the kill

Assign: **"Top 10 protein powders of 2026"**

- **Pass:** returns KILL. Cites §Kill — not local, no Seattle reader learns anything a
  national site could not tell them. Names a specific alternative worth commissioning.
- **Fail:** drafts it anyway, or kills it without saying what to run instead.

### B2 — the real run

Assign a Seattle recovery/cafe angle. Chosen deliberately: the cafe data was never
researched, so the fact researcher has to do genuine live work rather than reread an
existing sheet.

- **Pass:** RUN → draft in band → Tier 1 clean → no Tier-2 dimension FAIL → stops and
  asks. Every venue in the piece traceable to a source URL in the research trail.
- **Fail:** any unverified venue reaches the draft; a fact appears hedged rather than
  cut; Tier 1 needs more than two fix cycles to clear.

### B3 — the planted fact

Take B2's cleared draft. Change one venue's closing hour to something wrong. Re-run the
judge panel.

- **Pass:** `factual_venue_integrity` catches it and the overall verdict goes FAIL.
- **Fail:** the panel passes it, or flags it as NEEDS_REVISION rather than FAIL. The
  factual gate is non-negotiable; a wrong hour is not a revision note.

### B4 — the split

Feed the panel a draft whose voice is genuinely ambiguous — clean magazine prose that is
not quite the clipped house register. This is a real observed failure: an owner-written
v2 draft scored well on the rubric and the owner still judged it off-voice.

- **Pass:** the verdict reports the split with both readings, e.g. *"2 judges PASS, 1
  flagged rule-of-three cadence"*, and surfaces it as a NOTE for the owner.
- **Fail:** three scores averaged into one number, or the minority read dropped.

B4 tests the quietest failure mode in the whole harness. A blended score looks like a
verdict and hides a disagreement.

---

## Run 1 — 2026-07-29

| Case | Result | Evidence |
|---|---|---|
| A1 trigger | NOT TESTED | cannot be self-tested in the session that built the skill |
| A2 gate order | PASS | Tier 1 ran and completed before any judge was seated |
| A3 stop before publish | PARTIAL | never published, but no run reached all-green, so the real condition was never exercised |
| A4 gate line honest | PASS | every verdict carried the tier line; no gate reported that was not run |
| B1 the kill | PASS | killed "Top 10 protein powders of 2026" on 3 of 4 criteria, returned a specific better commission |
| B2 real run | REVISE | Tier 1 clean first try; panel found 5 factual defects. Correctly did not ship |
| B3 planted fact | PASS | Marination 8 PM → 10 PM caught. factual_venue_integrity 18, FAIL, overall FAIL |
| B4 the split | PASS | two genuine splits surfaced (structural 1/2, editorial value 2/1) and reported as splits |

**Panel convergence, B2** (judges 1/2/3): voice 78/82/85 all PASS · structural 55/62/62 all
NEEDS_REVISION · factual 62/55/52 all NEEDS_REVISION · seattle 92/88/72 all PASS ·
editorial value 76/66/80 SPLIT · ai-pattern 68/68/71 SPLIT at the threshold.

Three independent judges agreeing to within 10 points on four of six dimensions is the
signal that the rubric is doing real work rather than being read differently each time.

### What the run changed

Six writer rules were added to `SKILL.md` Step 2b, each because a judge caught it:
invented supporting statistics, superlatives contradicted by the piece's own numbers,
research-trail field labels leaking into prose, bold text used as headings, multi-paragraph
sections, and identical per-entry sentence templates.

**Harness gap found:** Tier 1's word count includes markdown headings. The Taylor Crow v2
fixture measures 814 with headings and 778 without. Tier 1 passed it; the body is under the
800 floor and a judge caught it. `SKILL.md` Step 3 now carries a body-only recount.

**Also found:** B4's panel scored voice 66/68/66, all NEEDS_REVISION, on the draft that a
single v2 judge had scored well and the owner independently judged off-voice. Three judges
caught what one missed. That is the case for the panel.

---

## Scoring

Tier A: all four must pass. A failure here is a defect in the skill, not a close call.

Tier B: B1, B3 and B4 are pass/fail. B2 is the end-to-end proof — it passes only if the
piece is one the owner would actually publish, which is the owner's read, not the
rubric's.

**Standing caveat:** a good rubric score is not a substitute for the brand owner's own
read. That has already been observed once on a shipped post. The eval measures whether
the harness catches what it claims to catch — not whether the copy is good enough to run.
