# Stage Progression Graph & Branching Logic

## Visual Progression Map

```
START: Client Assessment
       (Strength level, Goal, Frequency, Gender)
         ↓
    ┌─→ STAGE 1 — FOUNDATION 0 ←────────────┐
    │   (8-12 weeks minimum)                 │
    │                                         │
    │   • 3x/week (Upper/Lower/Rest pattern)  │
    │   • 4x/week (Upper/Lower/Upper/Lower)   │
    │   • 5x/week (Full upper/lower split)    │
    │                                         │
    │   Gender variants: Male (upper-priority) │
    │                    Female (lower-priority)│
    │                                         │
    │   Progression: If strength gains 10%+   │
    │                or 8 weeks completed     │
    │                                         │
    └───→ STAGE 2 — FOUNDATION 1 ←──────────┐
        (4-6 weeks minimum)                 │
                                           │
        BRANCH POINT ↙══════════════════╋══╖
        "What is your primary goal?"    │  │
           ├─ Fat Loss (FL)             │  └─→ Muscle Building (MB)
           │                            │
           ↓                            ↓
        STAGE 4                      STAGE 5
        Foundation 2                 Strength 2 / Performance 2
        (6 weeks)                    (6 weeks)
           ↓                            ↓
        STAGE 7                      STAGE 8
        Foundation 3                 Strength 3 / Performance 3
        (6 weeks)                    (6 weeks)
           ↓                            ↓
        STAGE 9 (FL)               STAGE 9 (MB)
        PERFORMANCE 3 (FL)         PERFORMANCE 3 (MB)
        [END PROGRESSION]           [END PROGRESSION]
            OR                          OR
        [Cycle back for               [Cycle back for
         maintenance/deload]          strength peak]
```

## Stage Details

### Stage 1 — Foundation 0 (Entry Level)

**Duration:** 8-12 weeks

**Frequency Options:**
- **3x/week:** 2 upper + 1 lower per week
- **4x/week:** 2 upper + 2 lower per week
- **5x/week:** Upper/Lower/Upper/Lower/Rest

**Muscle pairing focus:** Basic antagonist (Chest/Back, Quads/Hams). Introduces core work.

**Gender splits:**
- **Male:** Upper day first in week (males recover upper faster)
- **Female:** Lower day first in week (females have better lower body leverages + hormonal response)

**Progression criteria:**
- Main compound lifts up 10%+ in weight
- All reps at target range (no "short sets")
- 8 weeks minimum completed
- No major injury / form breakdown

**Exit:** → **Stage 2**

---

### Stage 2 — Foundation 1 (Intermediate Entry)

**Duration:** 4-6 weeks

**Focus:** Increase training frequency / moderate intensity. Begin fatigue management.

**Frequency Options:** Same 3/4/5x/week structure as Stage 1, but higher volume per session.

**Progression criteria:**
- Successfully completed Stage 1
- Ready to specialize (goal-dependent)

**BRANCHING POINT:** Choose Fat Loss OR Muscle Building

---

### Stage 4 — Foundation 2 (Fat Loss Path)

**Duration:** 6 weeks

**Focus:** Metabolic conditioning + moderate strength retention. Higher rep ranges (8-12) to maximize time under tension and glycogen depletion.

**Frequency Options:** 3/4/5x/week (same structure as Stage 1-2, but adjusted intensity)

**Pairing rules remain:** No Chest + Quads, etc.

**Exit:** → **Stage 7**

---

### Stage 5 — Strength 2 / Performance 2 (Muscle Building Path)

**Duration:** 6 weeks

**Focus:** Hypertrophy emphasis. Progressive overload on main lifts. Higher intensity (6-10 reps) with strict form.

**Frequency Options:** Same 3/4/5x/week structure.

**Pairing rules remain:** Muscle Building clients still respect forbidden pairs.

**Exit:** → **Stage 8**

---

### Stage 7 — Foundation 3 (FL Terminal)

**Duration:** 6 weeks

**Focus:** Fat loss consolidation + metabolic finisher. Can be performed multiple times before advancing to Stage 9.

**This is the "maintenance" stage for FL path** — can cycle here indefinitely or progress to Stage 9 Performance.

**Exit:** → **Stage 9 (FL)** OR repeat Stage 7

---

### Stage 8 — Strength 3 / Performance 3 (MB Terminal)

**Duration:** 6 weeks

**Focus:** Peak strength performance. Lower rep ranges (3-8), longer rest, higher weight.

**This is the "maintenance" stage for MB path** — can cycle here indefinitely or progress to Stage 9 Performance.

**Exit:** → **Stage 9 (MB)** OR repeat Stage 8

---

### Stage 9 (FL) — Performance 3 (Fat Loss)

**Duration:** 4 weeks

**Focus:** Sport-specific or body composition finisher. Advanced metabolic work.

**Exit:** [END] or cycle back to Stage 7

---

### Stage 9 (MB) — Performance 3 (Muscle Building)

**Duration:** 4 weeks

**Focus:** Absolute strength peak or advanced hypertrophy block. Competition-prep if applicable.

**Exit:** [END] or cycle back to Stage 8

---

## Progression Logic (Code Pattern)

```python
class StageProgressor:
    FOUNDATION_STAGES = ['Stage 1 — Foundation 0', 'Stage 2 — Foundation 1']
    FL_PATH = ['Stage 4 — Foundation 2', 'Stage 7 — Foundation 3', 'Stage 9 (FL) — Performance 3']
    MB_PATH = ['Stage 5 — Strength 2 / Performance 2', 'Stage 8 — Strength 3 / Performance 3', 'Stage 9 (MB) — Performance 3']
    
    def __init__(self):
        self.client_stages = {}  # client_id → current_stage
        self.client_goals = {}   # client_id → 'FL' or 'MB'
    
    def advance_client(self, client_id, reason='strength_gain'):
        """Advance client to next stage."""
        current = self.client_stages.get(client_id)
        
        if not current:
            # New client starts at Stage 1
            return 'Stage 1 — Foundation 0'
        
        # Check if client is in branching stages
        if current == 'Stage 2 — Foundation 1':
            # Must choose goal before advancing
            goal = self.client_goals.get(client_id)
            if goal == 'FL':
                return 'Stage 4 — Foundation 2'
            elif goal == 'MB':
                return 'Stage 5 — Strength 2 / Performance 2'
            else:
                return None  # Awaiting goal selection
        
        # Linear progression for foundation
        if current in self.FOUNDATION_STAGES:
            idx = self.FOUNDATION_STAGES.index(current)
            return self.FOUNDATION_STAGES[idx + 1] if idx + 1 < len(self.FOUNDATION_STAGES) else None
        
        # Path progression (FL or MB)
        if current in self.FL_PATH:
            idx = self.FL_PATH.index(current)
            return self.FL_PATH[idx + 1] if idx + 1 < len(self.FL_PATH) else None
        
        if current in self.MB_PATH:
            idx = self.MB_PATH.index(current)
            return self.MB_PATH[idx + 1] if idx + 1 < len(self.MB_PATH) else None
        
        # Terminal stages can cycle or end
        if current in ['Stage 9 (FL) — Performance 3', 'Stage 9 (MB) — Performance 3']:
            # Option to cycle back or end
            return None  # Awaiting client decision
    
    def set_goal(self, client_id, goal):
        """Lock in Fat Loss or Muscle Building path."""
        if goal not in ['FL', 'MB']:
            raise ValueError("Goal must be 'FL' or 'MB'")
        self.client_goals[client_id] = goal
        
        # If client is in Stage 2, auto-advance to next stage in chosen path
        if self.client_stages.get(client_id) == 'Stage 2 — Foundation 1':
            next_stage = self.advance_client(client_id)
            self.client_stages[client_id] = next_stage
            return next_stage
        
        return None
```

## Timing & Recovery

| Stage | Duration | Rest Between Progression |
|-------|----------|--------------------------|
| 1 | 8-12 weeks | 1 week deload |
| 2 | 4-6 weeks | 3-5 days |
| 4 (FL) | 6 weeks | 4-7 days |
| 5 (MB) | 6 weeks | 4-7 days |
| 7 (FL) | 6 weeks | Can repeat immediately |
| 8 (MB) | 6 weeks | Can repeat immediately |
| 9 (FL) | 4 weeks | End or cycle to 7 |
| 9 (MB) | 4 weeks | End or cycle to 8 |

---

## Pitfalls

- **Don't skip Stage 1-2** — Foundation is mandatory. No one starts at Stage 4 or 5.
- **Stage 2 → Goal choice is irreversible** — Once FL or MB is set, switching is a full reset. Changing paths means starting that path at Stage 4/5.
- **Stage 7 / 8 can be cycled, but not forever** — After 3 cycles, client should advance to Stage 9 or reassess goals.
- **Gender doesn't change day ordering** — Male and Female variants are preset in each stage tab. Don't mix them mid-stage.
- **If client stalls (no strength gain 4+ weeks)** — Don't advance. Offer: (a) repeat stage, (b) increase frequency, (c) re-assess form/nutrition.

---

## Selection Flowchart (Client Intake)

```
New Client Assessment
│
├─ "How many days/week can you train?"
│  ├─ 3 days → 3x/week programming
│  ├─ 4 days → 4x/week programming
│  └─ 5 days → 5x/week programming
│
├─ "Male or Female?"
│  ├─ Male → Male split variant
│  └─ Female → Female split variant
│
├─ "What's your primary goal?"
│  ├─ Weight loss / body comp → Note for Stage 2 branching
│  └─ Strength / muscle gain → Note for Stage 2 branching
│
├─ "Current strength level?" (approximate 1RM on main lifts)
│  ├─ Beginner (no consistent training) → START Stage 1
│  ├─ Intermediate (1+ year training) → ASSESS if Stage 1 or Stage 2
│  └─ Advanced (3+ years training) → Rare; may skip Stage 1-2 with assessment
│
└─ → Assign to Stage 1 — Foundation 0, frequency + gender variant
   → Reassess at week 8 or 10% strength gain
   → Auto-advance to Stage 2
   → At Stage 2 week 4, lock in goal (FL or MB)
   → Auto-advance to Stage 4 (FL) or Stage 5 (MB)
```
