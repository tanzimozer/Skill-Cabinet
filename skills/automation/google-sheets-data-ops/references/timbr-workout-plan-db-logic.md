# TIMBR — WORKOUT PLAN DB Logic

Session: July 2026. Sheet ID: `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`

## Tab: STRENGTH DB - EXTENDED

Schema (as of late July 2026):
```
A=Computed Level | B=Exercise Name | C=Alternative Exercise 1 |
D=Alternative Exercise 2 | E=Difficulty | F=Learning Curve |
G=Risk of Injury | H=Muscle Size | I=Muscle Part | J=Muscle Group |
K=Skill | L=Flexibility | M=Grip | N=Load | O=Cluster
```

Total rows: 426 (after extensions). S1=141, S2=140, S3=140 (approx).

## FX-2 Scoring Formula

```
Difficulty = min(9, max(2, (Skill×2) + Flex + Grip + Load - 3))
Computed Level:
  max(Difficulty, LC, Risk) ≤ 3 → S1
  max(Difficulty, LC, Risk) 4-6 → S2
  max(Difficulty, LC, Risk) ≥ 7 → S3
```

## Alternative Exercise Column Rules

### Col C — Alternative Exercise 1
- Same Computed Level (col A)
- Same Muscle Group (col J)
- Same Cluster (col O) — STRICT, no wrong-cluster fallback
- Different equipment type from col B
- Different exercise name from col B
- Globally unique across all rows in col C
- Fallback: same Level + Muscle Group, any different exercise (if no same-cluster cross-equipment option)
- If nothing available: blank (not X, not wrong-cluster)

### Col D — Alternative Exercise 2 (relaxed rule)
- Same Computed Level
- Same Muscle Group
- Different Cluster from col B (preferred)
- Different equipment from both col B and col C (preferred)
- Must not equal col B or col C
- Globally unique across all rows in col D (independent used set — do NOT seed from col C)
- Fallback: any same Level + Muscle Group, unique, ≠B, ≠C
- Use bipartite matching (not greedy) to maximise fill

## Equipment Taxonomy (derive from name prefix — check longer first)

```python
EQUIP_PREFIXES = [
    'smith machine', 'stability ball', 'resistance band',
    'trap-bar', 't-bar', 'ez-bar',
    'machine', 'cable', 'dumbbell', 'barbell',
    'bodyweight', 'trx', 'weighted', 'ghd',
    'hanging', 'kettlebell'
]
def get_equip(name):
    n = name.lower()
    for p in EQUIP_PREFIXES:
        if n.startswith(p): return p
    return 'other'
```

## Colour Convention (col A only)

- S1 → light green  `{'red': 0.82, 'green': 0.94, 'blue': 0.82}`
- S2 → medium green `{'red': 0.56, 'green': 0.81, 'blue': 0.56}`
- S3 → dark green   `{'red': 0.20, 'green': 0.55, 'blue': 0.20}`
- All other cols → white background, black text
- Header → dark navy, white bold text
- Apply colour to col A ONLY — row-wide colour "messes up the whole tab"

## Muscle Size Classification

**Big:** Chest, Back, Shoulders, Quads, Hamstrings, Glutes, Calves, Full Body
**Small:** Biceps, Triceps, Core, Traps

Binary by muscle group only — never varies within a group.

## Naming Convention

Every exercise name must start with equipment prefix. Five common NO_PREFIX
exercises to watch for — prefix with 'Bodyweight':
- Tricep Dip → Bodyweight Tricep Dip
- Kneeling Ab Rollout → Bodyweight Kneeling Ab Rollout
- Nordic Curl → Bodyweight Nordic Curl
- Dragon Flag → Bodyweight Dragon Flag
- L-Sit → Bodyweight L-Sit (parallel bars)

## Standard QA Checklist (hub-and-spoke, 5 spokes)

1. Formula validation: Difficulty + Computed Level vs FX-2 → expect 0 mismatches
2. Naming convention: every B and C starts with valid prefix → expect 0 violations
3. Duplicate detection: col B unique, col C unique, no row where B==C
4. Alt exercise validation: col C matches Level + Muscle Group + Cluster of col B (look up in pool, don't self-check)
5. Completeness: 100 per level (or target count), 0 blanks in A-O, all 12 muscle groups covered

## WORKOUT PLAN DB

Separate tab. Schema:
```
Computed Level | Muscle Group | Primary Exercise | Alt Exercise 1 | Alt Exercise 2
```

Alt 1 rule: same Level + Muscle Group + Cluster + different equipment from Primary.
Alt 2 rule: same Level + Muscle Group + different from both Primary and Alt 1 (no duplicates).
Hard dedup: global used set — each exercise appears once across entire tab.

Pool exhaustion here = not enough exercises per cluster in STRENGTH DB. Fix = extend STRENGTH DB, then rerun.

## Stress Test Pattern for Alt Columns

For each row, look up the alt exercise name in col B of the dataset:
1. Does it exist in the dataset?
2. Is it different from col B?
3. Does it match Computed Level?
4. Does it match Muscle Group?
5. Does it match Cluster?

Failures → fix with same-cluster/different-equipment replacement, or blank if none.
DO NOT validate alt's cluster against the alt's own stored row — that's circular.
Cross-reference against the PRIMARY's cluster.
