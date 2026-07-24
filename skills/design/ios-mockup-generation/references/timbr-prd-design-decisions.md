# Timbr PRD Design Decisions (Feature 1, v0.4.1)
_Session: May 31 2026 — Tanzim + Friday PRD discussion_

## Core UX Philosophy
- **Wearable enriches, never gates.** App works fully without a wearable; wearable adds HR/cal/duration to session summary.
- **Swipe cards are always required.** Wearable-only logging is not a valid path — per-exercise data (weight/reps/sets) is the core value prop. Session-level biometrics alone can't drive progressive overload.
- **Skipped = SKIPPED, not null.** Exercises not swiped-done are recorded as SKIPPED on End Workout. This is signal, not absence of data.
- **End Workout is manual + modal nudge.** Never auto-complete. Show "X of N done — end anyway?" to prompt without blocking.

## Data Model
```
Program (mesocycle) → Week → Day → Exercise
```
- **Program** = mesocycle, 3–6 week block with specific milestone goal (structural intent)
- **New program** = structural intent change (split, periodisation, phase, volume landmarks) OR outcome intent change (fat loss → muscle building)
- **Exercise swap within a program** = versioned progression event, NOT a new program
  - e.g. RDL → Leg Curl = same hamstring intent, different stimulus = progression event with reason tag

## Plan Generation Engine (Headless Automation)
Fires at mesocycle end (day 28 or trainer-defined). Per-exercise audit:

| Signal | Decision |
|---|---|
| >80% completion + load progressed | ✅ Advance — increase load or progress to next variation |
| >80% completion + no progression | ⚠️ Plateau — flag for trainer |
| 50–80% completion | ⚠️ Inconsistent — carry forward, flag reason |
| <50% completion | 🚫 Skipped pattern — hold, require trainer input |
| RPE trending down over block | Signal: client adapting → ready to progress |
| RPE trending up over block | Signal: program too aggressive → regress or deload |

Output: **draft program + reasoning card → trainer reviews → one tap to publish.**
Engine never auto-publishes.

**Preference-skipped exercises** (no injury, just avoidance): auto-substitute equivalent exercise from shared library (same muscle group, same movement pattern, different exercise). Do NOT repeat the same avoided exercise.

**Trainer-absent scenario**: apply same logic. Skip >60% on one exercise → auto-sub equivalent on next program build. Carry structural intent, not the specific exercise.

## Wearable Landscape (Seattle context)
- US adult smartwatch ownership: ~30–35% (Statista 2023–24)
- Seattle skew (tech-forward, higher income): estimated 45–55% ownership
- Active gym-goers: ~60–65% ownership
- Active use during strength sessions: ~40–50% even in Seattle
- **Design implication**: split house — always design wearable-optional

## Rep Counting Technology (as of May 2026)
- **PUSH Band 2.0** — best accuracy, velocity-based, clip-on attachment (NOT a wearable), ~$200, pro sports only, direct website unreliable
- **Apple Watch** — best consumer scale, watchOS 9+ counts reps for ~10 exercise types, degrades on compound lifts
- **Garmin** — has rep counting, lags Apple on accuracy and variety
- **Whoop / Oura** — no rep counting, recovery-focused
- **Gap nobody's closed**: automatic exercise ID + rep counting together, reliably, on mainstream wrist device

## Proxy Strategies for Weight/Reps/Sets (no wearable input)
1. **Historical pre-fill** (strongest) — pre-load sliders with last session's values; user confirms or tweaks
2. **Velocity-based inference** — bar speed + known 1RM → back-calculate load (not consumer-grade yet)
3. **Time under tension + motion** — duration + wrist pattern = rough rep count (Apple Watch, 10 movements)
4. **RPE triangulation** — RPE + HR + exercise type = plausible load range (directional only)

**Recommendation for Timbr MVP**: Option 1 (historical pre-fill). Smart defaults, low friction.

## Open PRD Questions (as of May 31 2026)
- Q5/Q9: Solo tier state — to be finalised
- Q22: Retroactive logging — no decision
- Q23: Trainer notified on workout completion — no decision
- Q26–29: Food logger — in/out of MVP not decided
- Q31: Chat infrastructure — Stream/Sendbird/Twilio not chosen
- Q35: Push notification service — Firebase + APNs not confirmed
- Q47: Online session pricing/setup — outstanding
