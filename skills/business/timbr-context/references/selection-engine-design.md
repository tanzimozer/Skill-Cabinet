# TIMBR Plan-Generation Engine — Module Design

The working selection engine built this session. Input `(goal, sex, days/week, stage)` → full weekly plan with real exercises picked from the correct tier DB, difficulty-gated, pairing-safe, with conditioning finishers. Reusable scaffold below — rebuild/extend from this, don't reinvent.

## Pipeline
1. **Load DBs fresh** from the three tabs (Foundation / Strength / Performance DB) — re-read every run; the sheet is edited concurrently.
2. **STAGE_MAP**: `stage → {goal: (tier, difficulty_cap)}`.
3. **WEEK_SPLITS**: `(stage, sex, days) → [Day1..Day7 labels]` lifted verbatim from the STAGES tab.
4. For each day label → resolve to muscle groups → pick exercises → assemble.

## STAGE_MAP (journey → tier + cap)
```
1: MB/FL = Foundation, cap 4        # F0
2: MB/FL = Foundation, cap 5        # F1
3: MB=Strength/6,  FL=Performance/6 # S1 / P1
4: MB/FL = Foundation, cap 6        # F2 free-weight intro (capped)
5: MB=Strength/8,  FL=Performance/8 # S2 / P2
6: MB=Performance/8, FL=Strength/8  # CROSSED L2
7: MB/FL = Foundation, cap 7        # F3 deload
8: MB=Strength/10, FL=Performance/10# S3 / P3 matched
9: MB=Performance/10, FL=Strength/10# CROSSED L3
```

## Day-label → muscle resolver (extend as STAGES adds labels)
```
Upper            -> Chest, Back, Shoulder, Tricep, Bicep, Core
Lower / Legs     -> Glute, Quad, Hamstring, Calf
Full Body        -> Chest, Back, Quad, Shoulder, Core
Chest+Back       -> Chest, Back
Shoulder+Bi+Tri  -> Shoulder, Bicep, Tricep
Chest+Tri        -> Chest, Tricep
Back+Bi          -> Back, Bicep
Shoulders+Traps  -> Shoulder, Traps
Glutes+Hams      -> Glute, Hamstring
Quads+Calves     -> Quad, Calf
Arms             -> Bicep, Tricep
Aerobic          -> Performance-Aerobic pool
```
Tolerate `+ Cardio` / `+ Core` suffixes by splitting on `+` and resolving the base, or appending the tagged finisher.

## Pick rule (the answer to the long-open question)
```python
pool = [e for e in DB[tier]
        if e.muscle == slot and e.difficulty <= cap]
pool.sort(key=lambda e: -e.difficulty)   # hardest allowed first = progression feel
n = 2 if muscle_is_big(slot) else 1       # big muscle 2 exercises, small 1
chosen = pool[:n]
# fallback: if pool empty under cap, drop the cap rather than return nothing
```
- **Conditioning finisher**: if `tier == Performance` or `goal == FL`, append the hardest Aerobic movement under cap from the Performance DB, name suffixed `(finisher)`.
- **Guardrail (inviolable)**: a day's muscle set must NOT contain both a big-upper {Chest, Back} and a big-lower {Glute, Hamstring, Quad}. Flag `⚠ PAIRING VIOLATION` or reject.

## Output rendering
Per `(goal, sex, days, stage)` print: header (goal · sex · days · stage, tier, cap), then Day 1–7 with focus label and bulleted exercises `name (Muscle/Part) Dn`. A `PLAN GENERATOR (demo)` sheet tab mirrors this for visual review — Tanzim wants visuals in the sheet, not just console.

## Known limitations to flag
- Difficulty/Learning/Risk ratings are unvalidated against the scoring formulas — selection quality is bounded by them.
- No reps/sets/load in the DB yet → execution-level distinctions (F2 cap, crossed stages 6/9) currently differ by tier/cap only, not rep-scheme. That's the next data layer.
- WEEK_SPLITS only fully defined for stages 1/3/5; other stages fall back to nearest defined split for the same sex/days. Fill from the STAGES tab as needed.
