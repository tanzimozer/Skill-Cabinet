# Timbr — Wearable Data Architecture & Rep Tracking Landscape

## Core principle (agreed in session)
Wearable enriches, never gates. Two separate data layers:
- **Wearable** → session biometrics: HR, calories, duration, effort intensity
- **Swipe cards (manual)** → prescription compliance: which exercise, what weight, reps, sets

These are complementary. Wearable-only sessions are valid — skipped exercises recorded as SKIPPED (not null), not blocked.

## Rep counting technology landscape (as of 2024)

### Best in class — niche
- **PUSH Band 2.0** — velocity-based training, clip-on barbell/dumbbell sensor. Gold standard for S&C coaches, NFL/NBA teams. ~$200, separate device, near-zero mainstream adoption. Website intermittently offline.
- **Gymaware** — commercial/pro sports grade. Not consumer.
- **Atlas Wristband** — most ambitious consumer attempt (100+ exercise auto-recognition + rep counting). Effectively dead.

### Best at scale — mainstream
- **Apple Watch (watchOS 9+)** — rep counting via accelerometer + gyroscope for ~10 exercise types. Accurate on simple bilateral movements (bicep curls, push-ups); degrades on compound/asymmetric lifts. On 30M+ US wrists.
- **Garmin (Fenix/Forerunner)** — has strength tracking, lags Apple on accuracy and exercise variety.
- **Whoop / Oura** — no rep counting. Recovery-focused only.

### Gap nobody has closed
Automatic exercise *identification* + accurate rep counting together, on a mainstream wrist device, across a varied strength library. Apple requires the user to declare the exercise; PUSH counts reps but still needs exercise selection. Nobody has "I put on a watch and it knows I did 3 sets of Romanian deadlifts at X velocity" — reliably, at scale.

## Proxy strategies for weight/reps/sets without explicit input

1. **Historical defaults** (strongest proxy) — pre-fill cards with last session's values. High hit rate; people are creatures of habit. Lowest friction.
2. **Velocity-based inference** — bar speed correlates with % of 1RM. Requires PUSH-class hardware. Not mainstream yet.
3. **Time under tension + motion signature** — duration + wrist motion ≈ rough rep count for simple exercises. Apple Watch does this for ~10 movements. Imprecise on compound lifts.
4. **RPE triangulation** — RPE + HR + known exercise type = plausible load range. Directional, not exact.

**Practical Timbr recommendation:** Option 1 (smart pre-fill from last session + progression algorithm). Cards arrive pre-loaded with best guess; user confirms or tweaks. Wearable validates effort, doesn't replace input.

## Seattle demographic data points
- US adult smartwatch/fitness tracker ownership: ~30–35% (Statista 2023–24)
- Seattle estimated (tech-forward, high income, health-conscious): ~45–55% ownership
- Active gym-goers specifically: ~60–65% ownership
- Actual active use *during strength sessions*: ~40–50% (battery, forgetting, discomfort)
- **Implication:** Even in best-case city, designing for split house. "Never gates" principle holds in the data.

## Apple Watch companion app note
watchOS has rep counting APIs for a subset of exercises — viable as a v2 feature (already deferred in Timbr PRD). Not MVP.
