---
name: fitness-intelligence-system
description: Fitness intelligence engine for personalized progressive training programs, muscle pairing validation, and stage progression routing
version: 1.0.0
---

# TIMBR Fitness Intelligence System

## Overview

This is a structured fitness domain system built around:
1. **Muscle pairing rules** — validated combinations (34 approved) and forbidden pairings (6 to avoid)
2. **9-stage progression framework** — from Foundation (0-3) through Strength (1-3) and Performance variants
3. **User segmentation** — by frequency (3/4/5 days/week) and gender (applies different upper/lower emphasis)
4. **Goal branching** — Foundation path splits at Stage 2 into Muscle Building (MB) vs Fat Loss (FL) tracks

## Data Source

**Google Sheet:** `1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo`
- **Tab 1: Pairings** — Complete rules for muscle group training combinations
- **Tabs 2-10: Stage 1–9** — Progressive workout structures with day-by-day programming

## Core Concepts

### Muscle Pairing Rules

**Approved pairings (34 total)** follow these patterns:

| Type | Example | Why |
|------|---------|-----|
| Antagonist | Chest + Back | Opposing push/pull; one rests while other works |
| Sequential pull | Back + Biceps | Biceps naturally assist back pulls |
| Sequential push | Chest + Triceps | Triceps naturally assist chest presses |
| Lower synergy | Quads + Hamstrings | Leg antagonist pair; balanced recovery |
| Posterior chain | Hamstrings + Glutes | Hip extension links them naturally |
| Stabilizer | Chest + Core | Core stabilizes pressing movements |
| Finisher pairs | Biceps + Forearms | Both low-fatigue finishers; minimal CNS cost |

**Forbidden pairings (6 total) — AVOID:**

| Pair | Why |
|------|-----|
| Chest + Quads | Two large unrelated regions; massive systemic fatigue |
| Chest + Hamstrings | Upper push + big lower; bloated recovery demand |
| Chest + Glutes | Upper/lower mismatch; no synergy, high cost |
| Back + Quads | Two large unrelated; huge fatigue multiplier |
| Back + Hamstrings | Deadlifts hammer both; overlapping recovery window |
| Shoulders + Quads | Upper push + big lower; high fatigue |

**Key insight:** The rule is **regional coherence** — either anatomically synergistic (pull + assisting muscle) or antagonistic (different regions). Never pair two large muscle groups from unrelated regions.

### 9-Stage Progression Framework

```
Stage 1 — Foundation 0
  ↓ (8 weeks / client readiness)
Stage 2 — Foundation 1
  ↓ BRANCH POINT ↙════╋════╖
  └─ Stage 4 (FL)     │    └─ Stage 5 (MB)
      ↓                ↓
  Stage 7 (FL)    Stage 8 (MB)
      ↓                ↓
  Stage 9 (FL)    Stage 9 (MB)
```

**Path selection:**
- **Fat Loss (FL):** Client goal is weight loss, body composition, metabolic rate
- **Muscle Building (MB):** Client goal is hypertrophy, strength, athletic performance

Each stage comes in multiple **frequency variants:**
- 3 days/week (compact, high intensity per session)
- 4 days/week (balanced)
- 5 days/week (high volume, longer recovery between similar muscle groups)

### User Segmentation: Gender-Based Frequency

**Foundation Stage 0 (Universal):**

| Frequency | Male | Female |
|-----------|------|--------|
| 3x/week | Upper, Rest, Lower, Rest, Upper, Rest, Rest | Lower, Rest, Upper, Rest, Lower, Rest, Rest |
| 4x/week | Upper, Lower, Rest, Upper, Lower, Rest, Rest | Lower, Upper, Rest, Lower, Upper, Rest, Rest |
| 5x/week | Upper, Lower, Upper, Rest, Lower, Upper, Rest | Lower, Upper, Lower, Rest, Upper, Lower, Rest |

**Pattern:** Males default to upper-priority splits (2:1 upper:lower in 3x/week). Females default to lower-priority (posterior chain + leg emphasis). Both are evidence-based for body composition and hormonal response.

## Implementation: Class-Level Structure

### 1. PairingValidator

**Responsibility:** Check if a proposed muscle group combination is valid.

```python
class PairingValidator:
    def __init__(self, approved_pairs, forbidden_pairs):
        self.approved = approved_pairs  # List of (A, B) tuples
        self.forbidden = forbidden_pairs  # List of (A, B) tuples
    
    def validate(self, muscle_a, muscle_b):
        """Check if pairing is safe."""
        pair = tuple(sorted([muscle_a, muscle_b]))
        
        if pair in self.forbidden:
            return {'valid': False, 'reason': 'forbidden pairing'}
        
        if pair in self.approved:
            return {'valid': True, 'reason': 'approved'}
        
        # If not in either list, conservatively reject
        return {'valid': False, 'reason': 'not validated'}
```

### 2. StageRouter

**Responsibility:** Determine client's current stage and next progression path.

```python
class StageRouter:
    def __init__(self, stage_sequence):
        # stage_sequence = ['Stage 1', 'Stage 2', 'Stage 4 (FL)', 'Stage 7 (FL)', ...]
        self.sequence = stage_sequence
    
    def current_stage(self, client_id):
        """Lookup client's current stage from database."""
        # Fetch from persistent store
        pass
    
    def next_stage(self, client_id):
        """Recommend next stage based on goal and history."""
        current = self.current_stage(client_id)
        if current == 'Stage 2':
            # Check client goal (FL vs MB)
            goal = self.get_goal(client_id)
            return 'Stage 4 (FL)' if goal == 'FL' else 'Stage 5 (MB)'
        
        # Linear progression otherwise
        idx = self.sequence.index(current)
        return self.sequence[idx + 1] if idx + 1 < len(self.sequence) else None
```

### 3. FrequencyAdapter

**Responsibility:** Map user profile (gender, frequency) to the right split template.

```python
class FrequencyAdapter:
    def __init__(self, stage_data):
        # stage_data = {'Stage 1': {...daily schedule...}}
        self.stages = stage_data
    
    def get_split(self, stage, frequency, gender):
        """Return the 7-day schedule for this profile."""
        # Lookup in stage data
        stage_info = self.stages[stage]
        
        key = f"{frequency} days/week — {'Male' if gender == 'M' else 'Female'}"
        return stage_info.get(key, None)
```

### 4. ExerciseAssigner

**Responsibility:** Given a stage and muscle group, recommend exercises that respect pairing rules.

```python
class ExerciseAssigner:
    def assign_exercises(self, stage, muscle_groups_for_day, client_profile):
        """
        stage: 'Stage 1'
        muscle_groups_for_day: ['Chest', 'Triceps']  # from the daily split
        client_profile: {...strength level, equipment access...}
        
        Returns: list of exercises with rep ranges, progressions
        """
        # Validate pairing first
        if len(muscle_groups_for_day) == 2:
            pair = tuple(sorted(muscle_groups_for_day))
            if not self.pairing_validator.validate(*pair):
                raise ValueError(f"Invalid pairing: {pair}")
        
        # Assign exercises per muscle
        exercises = []
        for muscle in muscle_groups_for_day:
            stage_exercises = self.exercise_library[stage].get(muscle, [])
            selected = self.pick_best_for_profile(stage_exercises, client_profile)
            exercises.extend(selected)
        
        return exercises
```

## Data Loading: From Google Sheets

See `references/sheet-api-access.md` for the full pattern to:
1. Load `Pairings` tab into `approved_pairs` and `forbidden_pairs` lists
2. Iterate stages 1-9 and extract day-by-day split templates
3. Build the stage progression graph

## Reference Files

- `references/muscle-pairings.md` — Full 34-approved + 6-forbidden list with biomechanical justification
- `references/stage-progression-graph.md` — Visual map of 9 stages, branch points, FL vs MB logic
- `references/sheet-api-access.md` — Code pattern to fetch stage data from Google Sheets API (requires Google OAuth)
- `references/strength-db-build.md` — STRENGTH DB schema, the locked S123 classifier, naming/cluster/sort conventions, the Learning-Curve-as-equipment-proxy caveat, and `~/gs.py` access. This is the *exercise library* the parent system references as "living elsewhere."

## Working with Tanzim on the DB build (standing instructions)

- **Always close with the final decision question** — same as you would hand to Sagar. When
  building/iterating on these DBs, end each turn by surfacing the single open decision as a
  one-line question for Tanzim to call (e.g. "apply all three now, or eyeball it first?").
  He drives the calls; you tee them up. Standing instruction, do not drop it.
- **Short, human responses** — no jargon, no padding. Reference tabs must read one-pass for
  Tanzim + Sagar, each value in its own editable cell.

## Pitfalls

- **Forbidden pairs are absolute** — Never assign Chest + Quads even if client insists. Recovery conflict is real; safety rule.
- **Stage 2 → Stage 4/5 branching is irreversible** — Once a client commits to FL path, don't slide them to MB without explicit re-goal-setting. Progression is different.
- **Frequency affects fatigue tolerance** — A 3x/week split can be higher intensity per session than 5x/week. Account for daily tonnage, not just exercises.
- **Gender differences in the Foundation stage are backed by research** — Don't treat as outdated. Males have faster upper body recovery; females' lower body has higher natural leverage. The splits respect this.
- **Exercise library is NOT in this system** — You have the *structure* for pairing and routing. The actual exercise selection (variations, progressions, reps) lives elsewhere. This system just validates pairing combinations and stage flow.

## Next Steps

1. **Build the data layer** — Load Google Sheets (Pairings + Stages 1-9) into the classes above
2. **Add client persistence** — Track which stage each client is in, goal, frequency, gender
3. **Build the API layer** — `/get_daily_workout` (given stage + day + frequency) → returns validated exercise list
4. **Implement progression logic** — When to advance stage (based on strength gains, adherence, or time)
