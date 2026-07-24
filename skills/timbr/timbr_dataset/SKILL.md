---
name: timbr_dataset
category: timbr
description: Build, update, and query the TIMBR workout dataset spreadsheet — STRENGTH DB, WORKOUT PLAN DB, TRAINING SPLIT, and related tabs.
---

# TIMBR Dataset Skill

## Spreadsheet
- **Sheet ID:** `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`
- **URL:** https://docs.google.com/spreadsheets/d/1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo/edit
- **Creds:** `~/.hermes/google_token.json` + `~/.hermes/google_client_secret.json`
- **Access method:** Direct Python + `googleapiclient`. NEVER use the `google_sheets` subagent toolset — it hits a demo account.

## Tab Inventory
| Tab | Purpose |
|-----|---------|
| STRENGTH DB | Master exercise pool — 149 exercises (as of Jul 2026), S1/S2/S3 classified |
| CONDITIONING DB | Conditioning exercises (C1/C2/C3) |
| HYBRID DB | Hybrid exercises (H1/H2/H3) |
| TRAINING SPLIT | Full 10-stage split definitions (F0–F3, S1–S3, P1–P3), male + female variants |
| WORKOUT PLAN DB | Denormalised plan table — one row per exercise per day/level/muscle combo |
| FX - 2 | Friday-built S1/S2/S3 reference table (source for STRENGTH DB restores) |
| SOURCE OF TRUTH | Scoring rubric and classification logic |
| S Level Progression | Progression notes |
| MUSCLE PAIRING | Muscle group pairing reference |

## STRENGTH DB Schema
`Computed Level | Exercise Name | Difficulty | Learning Curve | Risk of Injury | Muscle Size | Muscle Part | Muscle Group | Skill | Flexibility | Grip | Load | Cluster`

### Classification Formula
```python
def diff(sk, fl, gr, lo):
    return min(9, max(2, (sk*2) + fl + gr + lo - 3))

def level(sk, fl, gr, lo, lc, risk):
    d = diff(sk, fl, gr, lo)
    m = max(d, lc, risk)
    if m <= 3: return 'S1'
    if m <= 6: return 'S2'
    return 'S3'
```
- **S1:** max(Difficulty, LC, Risk) ≤ 3
- **S2:** 4–6
- **S3:** ≥ 7
- Always validate computed level matches expected before appending to DB.

## WORKOUT PLAN DB Schema
`Computed Level | Muscle Group | Primary Exercise | Alt Exercise 1 | Alt Exercise 2`

*(No Day column in current schema — as of July 2026 rebuild.)*

### Alt Exercise Logic (locked July 2026)
The alt columns are **not** a simple pool dump. Each column follows a distinct rule:

**Col D — Alt Exercise 1:**
- Same `Computed Level` as Col A
- Same `Muscle Group` as Col B
- Same `Cluster` (movement pattern) as Primary — i.e. the closest functional swap
- Must be a different exercise from Col C
- Falls back to any same-level/muscle exercise if no same-cluster option exists

**Col E — Alt Exercise 2:**
- Same `Computed Level` as Col A
- Same `Muscle Group` as Col B
- Different `Cluster` from Primary — broadens the option
- Must be different from **both** Col C (Primary) and Col D (Alt 1) — hard deduplication
- Falls back to any same-level/muscle exercise not already used if no different-cluster option exists

**Deduplication rule:** Each alt column must be unique against everything to its left. No exercise can repeat within a row.

### Equipment Taxonomy (derived from exercise names)
Equipment type is inferred from the exercise name prefix — there is no explicit equipment column:
- `Machine` → guided, fixed path
- `Cable` → cable-anchored, free path
- `Dumbbell` → free weight, bilateral or unilateral
- `Barbell` / `T-Bar` / `Trap-Bar` → barbell (S3 dominant)
- `EZ-Bar` → EZ-bar (S2/S3)
- `Smith Machine` → semi-guided barbell
- `Bodyweight` / `Weighted` / `Hanging` / `Nordic` / `TRX` / `L-Sit` / `Dragon Flag` → bodyweight
- `Stability Ball` → instability tool
- `GHD` → specialist rig

### Build Logic
- One row per exercise in STRENGTH DB for `(level, muscle_group)`.
- Alt 1 and Alt 2 computed per the Cluster-based logic above.
- Empty alt cells = genuine DB gap (pool too small) — leave blank, never invent.
- Column naming must match STRENGTH DB exactly.

### Safe Testing Workflow
Before applying new alt logic to the live tab:
1. Duplicate `WORKOUT PLAN DB` as `WORKOUT PLAN DB - TEST` via `duplicateSheet` batchUpdate request.
2. Apply logic to first 10 S1 rows only in the TEST tab.
3. Get Tanzim sign-off on the sample output.
4. Only then apply to the full tab and delete the TEST tab.

### Day/Split Structure (from TRAINING SPLIT tab)
*(Used when Day column is present — currently absent from WORKOUT PLAN DB as of Jul 2026.)*
- **S1** — Day 1 (M): Chest/Back/Core · Day 2 (M): Shoulders/Biceps/Triceps · Day 3 (M): Quads/Hamstrings/Glutes/Calves
- **S1** — Day 1 (F): Quads/Glutes/Core · Day 2 (F): Hamstrings/Glutes/Core · Day 3 (F): Chest/Back/Shoulders/Biceps/Triceps
- **S2/S3** — Day 1 (M): Chest/Triceps/Core · Day 2 (M): Back/Biceps · Day 3 (M): Shoulders/Glutes/Hamstrings/Quads/Calves
- **S2/S3** — Day 1 (F): Quads/Glutes/Calves · Day 2 (F): Chest/Back/Shoulders/Biceps/Triceps · Day 3 (F): Glutes/Hamstrings/Core
- S3 uses the same split as S2 — harder exercises only, not a different split structure.

## Pitfalls
- **Never overwrite STRENGTH DB without reading it first.** Use `append` to add rows, not `clear` + rewrite, unless explicitly restoring.
- **FX - 2 is the restore source for STRENGTH DB.** If STRENGTH DB gets wiped, pull from FX - 2 (columns: S-Level | Exercise Name | Difficulty | LC | Risk | Muscle Size | Muscle Part | Muscle Group | Skill | Flex | Grip | Load | Cluster).
- **Tab names are ALL CAPS** — `STRENGTH DB`, `WORKOUT PLAN DB`, `TRAINING SPLIT`, etc. Case matters for range references.
- **`gs.py` must run from `/home/hermes/`** — running from `/tmp/` causes shadowing issues.
- **Sheets API 500s** — retry once; they're transient.
- **MUSCLE PAIRING tab sheetId = 2001** (atypically low — not a typo).
- When Tanzim says "reorg" or changes the column schema, read current data first, transform in memory, then rewrite — don't lose rows.
- Always `clear` the target range before `update` when rewriting a whole tab.

## Workflow: Adding New Exercises to STRENGTH DB
1. Define: `[name, lc, risk, size, part, muscle_group, skill, flex, grip, load, cluster]`
2. Compute `diff()` and `level()` — validate level matches intent before appending.
3. `append` to STRENGTH DB (INSERT_ROWS, not overwrite).
4. Reload full pool from STRENGTH DB.
5. Rebuild WORKOUT PLAN DB from scratch using the new full pool.

## Workflow: Rebuilding WORKOUT PLAN DB
1. Read STRENGTH DB → build `pool = defaultdict(list)` keyed on `(Computed Level, Muscle Group)`.
2. Iterate split structure (all level × day × muscle combos).
3. For each exercise in pool: primary = that exercise, alts = rest of pool for same key, padded to 6.
4. `clear` WORKOUT PLAN DB, then `update` with header + all rows.
5. Apply formatting: dark navy header (`rgb(0.08, 0.08, 0.25)`), freeze row 1, auto-resize columns.

## References
- `references/timbr-sheet-restore.md` — FX-2 restore procedure and column mapping
- `scripts/compute_alt_exercises.py` — Cluster-based Alt 1 / Alt 2 computation for WORKOUT PLAN DB; includes safe test mode (duplicate tab + S1 only + row_limit)
