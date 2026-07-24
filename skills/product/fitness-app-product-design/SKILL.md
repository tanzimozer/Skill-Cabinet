---
name: fitness-app-product-design
description: "Product design principles, data model decisions, and intelligence layer architecture for fitness tracking apps — specifically Timbr."
version: 1.0.0
platforms: [any]
metadata:
  hermes:
    tags: [product, prd, fitness, timbr, data-model, plan-generation, wearable]
    related_skills: [ios-mockup-html]
---

# Fitness App Product Design

## Core Architecture Principle

Wearable data and card-based logging are **two separate data layers**, not alternatives:

| Layer | Source | Captures |
|-------|--------|---------|
| Session biometrics | Wearable (Apple Watch, Garmin) | HR, calories, duration, effort |
| Prescription compliance | Swipe cards | Which exercise, what weight, how many reps/sets |

Wearable-only sessions are valid (record biometrics) but cards are always required for progression data. "Wearable enriches, never gates."

## Workout Logging UX Principles (Timbr v0.4.1)

- **Explicit start/end** — user taps Start and End; no auto-detection
- **One card per exercise** — granularity is exercise level, not set level
- **SKIPPED ≠ null** — unswipped exercises on End = SKIPPED signal, not missing data
- **End Workout = manual submit** — modal shows "X of N done" as soft nudge, not a blocker
- **Undo = 4s transient toast** — dating-app pattern; no persistent undo button

## Program / Mesocycle Model

**Definition hierarchy:**
```
Journey (macrocycle)  — fat loss, muscle building — rarely changes
  └── Program (mesocycle) — 3–6 week block with specific milestone — THIS is "a program"
        └── Week → Day → Exercise
```

**What defines a new program:**
1. Split changes (push/pull/legs → upper/lower)
2. Phase change (hypertrophy → strength)
3. Periodisation model changes (linear → undulating)
4. Volume landmark changes (4 days/week → 5 days/week structurally)

**What does NOT define a new program:**
- Exercise swap within same muscle group / intent (RDL → leg curl)
- Load/rep week-to-week adjustments (progression)
- Substitution due to equipment or injury

**The test:** would a different trainer looking at the program say "this is different" or "same with tweaks"?

## Exercise Progression / Substitution Logic

When an exercise is swapped within a program with intent (e.g. RDL → leg curl for more knee flexion):
- This is a **progression event within the same program**, not a new program
- The swap should be a **versioned event with a reason** in the audit trail
- Data model: `exercise_substitution` record with `reason: progression`

## Headless Plan Generation Intelligence Layer

Three layers:

**1. Data collection** — every session fires `workout.completed` with: exercise status (done/skipped), weight/reps/sets, RPE, wearable biometrics.

**2. Decision engine** (fires at mesocycle end per exercise):

| Signal | Decision |
|--------|---------|
| >80% completion + load progressed | Advance — increase load/variation |
| >80% completion + plateau | Flag to trainer |
| 50–80% completion | Carry forward + flag |
| <50% completion | Hold — require trainer input |
| RPE trending down | Client adapting → ready to progress |
| RPE trending up | Too aggressive → regress or deload |
| Skipped >60% by preference (no injury) | Auto-substitute equivalent in next block |

**3. Output** — draft program + reasoning card surfaced to trainer for review/approval. Never auto-publishes without trainer sign-off (unless trainer-less).

**Trainerless mode:** same logic, substitution rule applies. Skip >60% by preference → carry the *intent* forward (same muscle group, same movement pattern) with a different exercise pulled from shared library. Never repeat the skipped exercise verbatim.

**Engine boundary:** pattern recognition + draft generation. Trainer handles: why exercise was skipped (injury vs preference), whether plateau means regress/substitute/push through, structural program change decisions.

## Wearable Rep-Counting Landscape

| Device | Rep counting | Consumer scale | Notes |
|--------|-------------|----------------|-------|
| PUSH Band 2.0 | ✅ Best in class | ❌ Niche, ~$200 clip-on | Pro sports use; not wrist wearable |
| Apple Watch | ✅ watchOS 9+, ~10 exercises | ✅ 30M+ US wrists | Degrades on compound/asymmetric |
| Garmin | ✅ Limited | ✅ Good | Lags Apple on accuracy |
| Whoop / Oura | ❌ None | ✅ Good | Recovery-focused only |

Nobody has cracked: auto exercise ID + rep counting together, reliably, on a mainstream wrist device. Until then, swipe cards are the only reliable cross-device compliance capture.

**Seattle demographic estimate:** ~45–55% wearable ownership in target user base; ~60–65% among active gym-goers; ~40–50% actually wearing it during strength sessions.

## Smart Pre-fill Strategy (Proxy for Wearable Data Gap)

Best proxy for weight/reps/sets when wearable can't capture them:
1. **Historical defaults** — pre-fill from last session's values (highest hit-rate; people are creatures of habit)
2. **RPE triangulation** — RPE 8 + HR + known exercise = plausible load range
3. **Velocity inference** (future) — PUSH Band / Apple Watch velocity → back-calculate % 1RM

For MVP: option 1. Cards arrive pre-loaded with last session's values. User confirms or tweaks — not data entry from scratch.

## References
- `references/timbr-prd-decisions.md` — full list of resolved and open PRD questions
