# Muscle Pairing Reference (TIMBR System)

## Approved Pairings (34 total)

Extracted from TIMBR Fitness Google Sheet — Pairings tab.

### Upper Body Antagonist & Sequential

| Muscles | Why | CNS Cost | Recovery |
|---------|-----|----------|----------|
| Chest + Back | Antagonist push/pull; superset-friendly | Moderate | High (opposing) |
| Chest + Shoulders | Shared anterior delts; front delta assist in pressing | Moderate | High |
| Chest + Triceps | Triceps assist every chest press (secondary) | Moderate | Moderate (shared muscle) |
| Back + Biceps | Biceps assist every back pull (secondary) | Moderate | Moderate (shared muscle) |
| Back + Forearms | Forearms assist grip in every back pull | Low | Moderate |
| Back + Traps | Same pull pattern; rows, shrugs, deadlifts recruit both | Moderate | Moderate |
| Shoulders + Triceps | Triceps assist overhead pressing; OHP co-recruits both | Moderate | Moderate |
| Shoulders + Traps | Share upright pull/shrug pattern | Moderate | Moderate |
| Biceps + Triceps | Antagonist arm pair; minimal compound overlap | Low | High (opposing) |
| Biceps + Forearms | Forearms assist every bicep curl (grip) | Low | Low (finisher) |
| Biceps + Traps | Both pull muscles; strong synergy in deadlift/rows | Moderate | Moderate |
| Triceps + Forearms | Both elbow/grip work; low system fatigue | Low | Low (finisher) |

### Lower Body Antagonist & Sequential

| Muscles | Why | CNS Cost | Recovery |
|---------|-----|----------|----------|
| Quads + Hamstrings | Leg antagonist pair; proven programming | Moderate | High (opposing) |
| Quads + Glutes | Squats + hinges train both; works if glutes lead | Moderate | Moderate |
| Hamstrings + Glutes | Hip extension links; posterior chain synergy | Moderate | Moderate |
| Quads + Calves | Same lower body region; easy sequencing | Low | Low |
| Hamstrings + Calves | Same lower body region; easy sequencing | Low | Low |
| Glutes + Calves | Same lower body; easy sequencing | Low | Low |

### Core / Stabilizer Pairings (Low Cost, Always Safe)

| Muscles | Why | CNS Cost | Recovery |
|---------|-----|----------|----------|
| Chest + Core | Core stabilizes pressing; low independent fatigue | Low | Low |
| Back + Core | Core braces all pulling; low independent fatigue | Low | Low |
| Shoulders + Core | Core stabilizes overhead work; low independent fatigue | Low | Low |
| Quads + Core | Core braces squats; low independent fatigue | Low | Low |
| Hamstrings + Core | Core braces hinge patterns; low independent fatigue | Low | Low |
| Glutes + Core | Both low-cost finishers; minimal central fatigue | Low | Low |
| Biceps + Core | Both low-cost finishers; zero interference | Low | Low |
| Triceps + Core | Both low-cost finishers; zero interference | Low | Low |
| Forearms + Core | Both low-cost finishers; zero interference | Low | Low |
| Calves + Core | Two low-cost finishers; minimal systemic load | Low | Low |
| Abs/Core + Traps | Both low-cost; core doesn't fatigue traps | Low | Low |

**Pattern:** Pairing ANY muscle with Core is always safe. Core stabilizes everything and doesn't fatigue from stabilization alone.

---

## Forbidden Pairings (6 total)

These are **absolute no-go** combinations due to regional overload and overlapping recovery demands.

| Pair | Why | CNS Hit | Recovery Window | Example Fail |
|------|-----|---------|-----------------|--------------|
| Chest + Quads | Two large unrelated regions; huge systemic fatigue | EXTREME | 72+ hours | Upper press + leg crush = depleted for 3+ days |
| Chest + Hamstrings | Large unrelated regions; bloated session | HIGH | 72 hours | Bench pressing + heavy deadlift hamstring work = shot |
| Chest + Glutes | Upper push + large lower; no synergy, high cost | HIGH | 72 hours | Chest focus + glute focus = split recovery |
| Back + Quads | Two large unrelated; massive fatigue multiplier | EXTREME | 72+ hours | Heavy rows + heavy squats = complete depletion |
| Back + Hamstrings | Deadlifts hammer both; overlapping recovery conflict | EXTREME | 72+ hours | Back workout hits hams hard; dedicated hamstring session conflicts |
| Shoulders + Quads | Upper push + big lower; high fatigue, no synergy | HIGH | 72 hours | OHP + squat = extreme CNS demand |

**Core principle:** If pairing two muscles means two *large* muscle groups from *unrelated regions* (upper + lower, or upper + upper in unrelated patterns), recovery demand explodes exponentially. CNS can only recover so fast; client will miss next session or perform poorly.

---

## Implementation Notes

### Validation Logic

```python
approved = [
    ('Chest', 'Back'),
    ('Chest', 'Shoulders'),
    ('Chest', 'Triceps'),
    ('Chest', 'Core'),
    # ... (34 total)
]

forbidden = [
    ('Chest', 'Quads'),
    ('Chest', 'Hamstrings'),
    ('Chest', 'Glutes'),
    ('Back', 'Quads'),
    ('Back', 'Hamstrings'),
    ('Shoulders', 'Quads'),
]

def is_valid_pairing(muscle_a, muscle_b):
    pair = tuple(sorted([muscle_a, muscle_b]))
    if pair in forbidden:
        return False, "Forbidden pairing: overlapping recovery demand"
    if pair in approved:
        return True, "Approved pairing"
    return False, "Pairing not validated"
```

### Gray Zone (Not in Either List)

If a pairing is not in the approved list, **conservatively reject it**. This prevents accidental overtraining. The 34 approved + 6 forbidden covers 95%+ of practical programming. Unlisted pairs are either:
- Untested (don't risk it)
- Implicitly forbidden (regional overload)
- Very niche (ask Tanzim)

### Practical Example: Day Structure

**Valid day (Approved Pairing):**
- Chest (primary) + Triceps (secondary) ✓
- Back (primary) + Biceps (secondary) ✓
- Quads (primary) + Core (stabilizer finisher) ✓

**Invalid day (Forbidden Pairing):**
- Chest (primary) + Quads (primary) ✗ — Two large, unrelated regions
- Back (primary) + Hamstrings (primary) ✗ — Overlapping recovery (deadlifts hit both)

**Gray zone (not validated; conservatively reject):**
- Triceps + Glutes — Not in list; unclear. Don't assign.
- Shoulders + Hamstrings — Not in list; likely OK but untested. Don't assign.
