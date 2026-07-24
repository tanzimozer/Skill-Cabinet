# CONDITIONING DB — Build Conventions & Classifier

> Companion to `references/strength-db-build.md`. Built by porting the S123 model into a
> C123 analog. Read both together when working any of the three DBs (Strength/Conditioning/Hybrid).

The CONDITIONING DB mirrors the STRENGTH DB exactly in shape, formatting, and the
classify-by-two-intrinsic-gates principle. Built by **porting the S123 model** into a
C123 analog. Same sheet as STRENGTH DB (`1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`),
tab **CONDITIONING DB**, accessed via `~/gs.py`.

## Why the Strength classifier does NOT port directly

STRENGTH's `Difficulty = (Skill*2)+Flex+Grip+Load-3` is a **load model**. Grip / Flex / Load
are near-meaningless for a sprint or a burpee. Conditioning's intrinsic demand is
**metabolic intensity + coordination**, not load. So the entry gate had to be re-axised.
User agreed the new axis: **Intensity + Learning Curve** (Intensity replaces Difficulty).

## Schema (12 columns, same shape as STRENGTH DB's 13 minus the load-only axes)

`Computed Level (A, live)`, Exercise Name, Muscle Group, Muscle Size, Muscle Part,
Intensity, Learning Curve, Risk of Injury, Output, Coordination, Impact, Cluster.

- Three intrinsic axes, **all 1–3** (same narrow-scale discipline as Strength's Skill):
  - **Output** — metabolic ceiling: 1 steady-state, 2 hard intervals, 3 all-out. *Doubled in the formula* (the dominant driver, same role Skill plays in Strength).
  - **Coordination** — how much you manage at once: 1 fixed pattern, 2 repeating pattern you control, 3 whole-body timing under fatigue.
  - **Impact** — joint loading from ground contact/decel: 1 zero/low (ergs, sled), 2 moderate (running/skipping), 3 high (jumps, landings, sprints).
- No Flex/Grip/Load — dropped as meaningless for cardio, replaced by what actually gates conditioning.

## The C123 Classifier (analog of S123)

```
Intensity     = MAX(2, MIN(9, (Output*2) + Coordination + Impact - 2))   # live
Computed Level = IF(Intensity<=5, "C1", IF(LearningCurve<=7, "C2", "C3")) # live
```

- **Intensity gates entry** (C1→C2): can anyone do it unguided?
- **Learning Curve gates mastery** (C2→C3): months to own + high skill under fatigue?
- Identical two-gate structure to S123; only the axes and labels change.

## Cluster grain for conditioning = **modality**, not movement pattern

Erg/Machine · Jump/Plyo · Bodyweight Cardio · Locomotion · Implement.
(Strength clusters by movement pattern; conditioning by equipment-class modality.)

## Known characteristic: C3 tends to come up empty

C3 needs LC ≥ 8. Conditioning is rarely "months to own" — double-unders top at ~7,
sprints ~6. An empty C3 is the **honest** result, not a bug. If a populated C3 is wanted,
the only real candidates are skill-heavy (double-unders, Oly-style complexes, pistol/plyo
combos) or you nudge the gate to LC ≥ 7. Surface this as the decision question, don't decide it.

## Quality cross-match (run after any re-score)

Check internal coherence between axes — these are *soft* checks, a flag is a prompt not an error:
- Impact 3 should usually carry Risk ≥ 3 (high-impact = injury exposure).
- Coordination 3 should usually carry LC ≥ 5 (complex = slower to learn).
- Output 3 should carry Intensity ≥ 6.
- **True-positive example:** Kettlebell Swings = Impact 1 / Risk 4 — correct divergence
  (low ground-impact, real lumbar risk from the loaded hinge). The check *should* flag it;
  keep the value. Cross-match catches genuine mismatches AND confirms legitimate exceptions.

## Rubric

Conditioning axes documented in the shared **Rubric** tab as a "CONDITIONING SCORING RUBRIC"
section appended below the strength block (Output / Coordination / Impact bands + Intensity
formula + C1/C2/C3 gates). Navy section title, bold subsection headers — house style.

## Extending the list (appending exercises)

When growing the DB (e.g. 28 → 50), keep every new row LIVE — never paste computed values:

1. **Back up first** with `valueRenderOption='FORMULA'` so the backup captures formulas, not
   their evaluated results.
2. **Dedupe twice** — against all existing live names (case-folded) AND internally within the
   new batch. Print both checks before writing.
3. **Write row-relative formulas** for the two computed columns, e.g. for sheet row `r`:
   - `A{r}: =IF(F{r}<=5,"C1",IF(G{r}<=7,"C2","C3"))`
   - `F{r}: =MAX(2,MIN(9,(I{r}*2)+J{r}+K{r}-2))`
   Read an existing row's formula first to copy the exact pattern.
4. **Re-run BOTH gates in Python across the whole set** (not just new rows) and assert 0 fails.
5. New score rows are heuristic too → same Sagar-validation flag as the rest.

Adding skill-heavy movements (e.g. Depth Jumps, LC 8) is how C3 finally populates — expect the
distribution to shift, and surface the new C3 as honest, not a bug.

## Band-colour thresholds are HAND-TUNED, not an even split — verify before extending

The green→yellow→red bands on Intensity/LC/Risk do NOT follow a naive low/mid/high tertile.
The real cutoffs (read back from the live sheet) are per-column and uneven:

| Column    | Green   | Yellow  | Red   |
|-----------|---------|---------|-------|
| Intensity | (none)  | ≤ 6     | ≥ 7   |
| Learning Curve | ≤ 3 | 4–6     | ≥ 7   |
| Risk      | ≤ 3     | ≥ 4     | (none)|

Intensity has no green band at all; Risk has no red. **Do not guess thresholds when colouring
appended rows** — it silently desyncs the gradient from the existing rows. Instead, before
recolouring: read the existing rows' `effectiveFormat.backgroundColor` per value via
`spreadsheets.get(includeGridData=True)`, derive the true value→colour map, then apply that.
Verify after with a rounding tolerance (the API returns ~0.973 for a stored 0.976 — round to
3 dp and compare, don't string-match).

House palette (exact): Green `(0.847,0.918,0.776)` · Yellow `(0.976,0.929,0.847)` · Red `(0.969,0.847,0.847)`.

## Same locked rules carry over from STRENGTH DB

- Equipment NEVER classifies (user filter, not intrinsic).
- Back up before destructive writes: `~/backups/CONDITIONING_DB_pre<Action>_<stamp>.json`.
- Heuristic inputs (every Learning Curve and Risk value here is the agent's read) → flag for
  Sagar coach-validation, same as Strength.
- Single live computed Level column; never carry manual + computed duals.
- Always close the turn with the single open decision as a one-line question.
