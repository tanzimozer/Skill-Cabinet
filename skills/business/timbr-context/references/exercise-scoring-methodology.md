# TIMBR Exercise Scoring — Methodology, Flaws & v2 Direction

The exercise-DB scoring model is the FOUNDATION of plan generation. Wrong scores → wrong
auto-generated workouts for real beginners. Sagar treats it as load-bearing; review it as such.

## v1 model (as found, 2026-06)

Three 1–10 ratings, each derived from subjective 1–3 coach inputs, then rolled into a band.

- **Difficulty** = Stability + (Strength×2) + Flexibility + Grip − 4 (cap 10)
- **Learning Curve** = (Learn×3) + Stability − 2
- **Risk of Injury** = Likelihood × Severity (worst failure mode); benign 2–3, tissue 4–6,
  catastrophic 8–9 (−3 with spotter)
- **Level Score** = Risk×0.40 + Difficulty×0.35 + LearningCurve×0.25 → F0(1–2.5)/F1(2.6–4.5)/F2(4.6–7.0)/F3(7.1–10)
- Per-tab floor: Strength/Performance can't read below F1.

The arithmetic IS internally consistent — every Level Score reproduces from the formula. The
problem was never the math; it's the inputs and the formula *structure*.

## Structural flaws (4-spoke hub-n-spoke review — sports-sci, psychometrics, product-eng, red-team all converged)

These are FORMULA bugs, not input errors. Re-scoring alone does NOT fix them.

1. **Risk mis-drives Level (weight 0.40).** Level should answer "can the user *execute* it?"
   (skill/mobility/coordination) — not "is it dangerous?". Loading Risk heaviest pushes safe
   staples (deadlift, bench) into advanced tiers and lets skill-heavy low-risk moves slip into
   beginner plans. → Risk should be a separate GATE/flag, never a level weight.
2. **Spotter −3 is dangerous.** It drops a SOLO beginner's near-max bench F3→F2 — in an
   auto-generated plan where no spotter exists. → spotter reduces *likelihood* and ONLY when one
   is actually present; ignore it for solo auto-plans.
3. **Stability double-counts** — it's in BOTH Difficulty and Learning Curve, silently over-tiering
   every free-weight/overhead move. → keep it in ONE formula only (chose Learning Curve).
4. **Strength×2 is backwards.** Strength is the EASIEST axis to regress (just lower the load), so
   doubling it over-tiers safe heavy machines (Leg Press, Chest Press → F2). → double-weight
   **Skill/Coordination** instead — the thing you can't scale down.
5. **Scales don't align** — Difficulty spans 1–11, Risk 1–9 — so the 40/35/25 weights are
   decorative. → normalise every input to 0–1 *before* weighting.
6. **False precision** — Risk=L×S can never equal 5/7/8 (holes in the scale); a "6.7" implies
   accuracy 1–3 gut calls don't have. → report BANDS, not decimals.

## v2 direction (verified against 9 known lifts before writing)

- Difficulty = (Strength×2)+Flex+Grip−3 (Stability removed), range 1–9
- Learning Curve unchanged (sole home of Stability), range 2–10
- Level = Difficulty_norm×0.60 + LC_norm×0.40 (0–1); F0≤0.20 / F1≤0.45 / F2≤0.70 / F3>0.70
- Risk = separate GATE column: ≤3 OK / 4–6 CAUTION / >6 NEEDS SPOTTER/COACHING — never demotes level
- Validation set (must pass eyeball): Pec Deck→F0, Goblet→F1, Reverse Lunge→F3 (Sagar's catch, now
  correct), Deadlift/Back Squat/Snatch→F3. Residual: Leg Press/Chest Press still F2 until Strength×2→Skill×2.

## CRITICAL data-modeling pitfall — store raw inputs, not just computed values

The DBs store ONLY the computed Difficulty/LC/Risk — **the raw sub-inputs (Stability, Strength,
Flexibility, Grip) were discarded** after computing Difficulty once. Consequence: you CANNOT
retrofit a formula change (e.g. swap Strength×2 → Skill×2) because there's nothing to recompute
from. The sub-inputs survive only as worked examples on the SCORING LOGIC tab.

**Lesson for any scored data model:** persist the raw component inputs alongside the rollup, or
every future formula revision becomes a full re-scoring of the whole catalog. Flag this to Tanzim
before promising a formula retrofit — it determines whether the fix is "10 minutes" or "re-score 375 rows".

## "Is this scientific?" — the honest answer

No — it's an expert-heuristic model: defensible and internally coherent, NOT empirically validated.
"Correct" here means consistent + passes coach gut-check, not peer-reviewed. To make it scientific
needs: published injury/EMG/ACSM-NSCA data per exercise, ≥2 coaches scoring blind with an inter-rater
agreement check (ICC/kappa), and band cutoffs calibrated to a real outcome. Pragmatist call (shared
by the product-eng spoke): ship the heuristic for v1 with the Risk gate + a hand-checked sanity set
+ a 2nd-coach Risk pass; DEFER literature review / formal reliability stats / weight optimisation to
a later version that has real user data.

## Workflow notes for this project
- **Non-destructive by default.** Add NEW tabs/sections; leave Foundation/Strength/Performance number
  columns untouched until Tanzim clears a re-score. "Proposal, not a change" until he says go.
- **3-stage QC, read live from the sheet** (not from memory): (1) header parity vs reference DB,
  (2) math integrity — every score+band reproduces from the formula, (3) business rules — classification,
  value ranges, level prefix, no duplicates.
- **He wants it TERSE.** "YOU ARE DUMPING TOO MUCH INFORMATION ON ME" / "address one thing at a time."
  On this project especially: answer the ONE point asked, stop. No multi-flaw essays unless he asks for the full picture.
- DB tabs seen this session: F-0123 / S-123 / P-123 (renamed live from FOUNDATION/STRENGTH/PERFORMANCE),
  plus CONDITIONING DB + HYBRID DB (new — conditioning is the homeless HIIT pool; hybrid = grey-zone
  carries/sleds that serve both strength & conditioning). Muscle:Fat ratio = 0–1 (1=pure muscle, 0=pure
  fat-loss), formula (Load×0.5)+(Rest×0.3)+(Continuity×0.2); replaces the dead binary "Classification" column.
