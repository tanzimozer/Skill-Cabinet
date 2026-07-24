# Timbr Google Sheet — Mechanics & Data Map

The Timbr spec's data model lives in a Google Sheet, separate from the PRD PDF.
Answer questions from the **live sheet**, not memory.

## Access
- Google OAuth (FRIDAY client) is provisioned and active: Sheets, Drive, Docs scopes all live.
- Token: `~/.hermes/google_token.json` · client secret: `~/.hermes/google_client_secret.json`.
- Auto-refreshes (access token hourly; refresh token indefinite).
- Credential inventory: `~/Desktop/CREDENTIALS_MASTER.md`, `~/.hermes/vault.json`.
- **This means native Google Docs/Sheets creation is available — no CSV workaround needed.**

## The `gs.py` helper (`/home/hermes/gs.py`)
```python
import sys; sys.path.insert(0,'/home/hermes'); import gs
gs.get("'Tab Name'")        # -> list[list], row 0 = header. Quote tab names with spaces.
gs.put("'Tab'!A1", values)  # USER_ENTERED, writes formulas live
gs.meta()                   # spreadsheet metadata (all tabs)
gs.gid("Tab Name")          # numeric sheetId for a tab
gs.svc                      # raw sheets v4 service for clear() etc.
```
Sheet ID is hardcoded in `gs.py` (`SHEET=...`).

## Tab inventory (as of Jul 2026)
SOURCE OF TRUTH · TRAINING SPLIT · FX - 2 · STRENGTH DB · CONDITIONING DB ·
HYBRID DB · MUSCLE PAIRING · S Level Progression · (S123 LOGIC built by rebuild script)

## S1/S2/S3 classification (locked formula)
`IF Difficulty <= 5 -> S1 | else IF Learning Curve <= 7 -> S2 | else -> S3`
- Computed live in STRENGTH DB col T ("Computed Level"). 96/97 match.
- Difficulty = intrinsic execution demand. Learning Curve = time-to-master (coaching need).
- Equipment is a selection filter, NEVER a classifier.

## Swap / alternate feature (Sagar's requirement, 10 Jul)
`S Level Progression` tab = 150 exercises (50 S1 / 50 S2 / 50 S3). Columns:
Computed Level · Exercise Name · Vector Plane · Muscle Group · Muscle Part ·
Alternative Exercise · Alt Level · Difficulty · Learning Curve · Risk of Injury · Verified Alt Level.

Integrity findings from the audit (the actual value delivered):
- 150/150 rows have an alternate; 150/150 alternates are same computed level. ✓
- **7 alternates cross muscle groups** — breaks the "same muscle" swap rule. Fix or reword rule.
- **Only 1 alternate per exercise** — PRD asked for primary + 3 alternates. Gap.
- **Thin pools** (< 4, can't guarantee a swap): S1 Hamstrings 2, Traps 3;
  S2 Triceps 2 / Hamstrings 1 / Full Body 1 / Calves 3 / Glutes 3; S3 Biceps 1, Core 1.

## Per-day exercise counts come from TRAINING SPLIT, not chat
- S1 day rule: 2 big muscles (nothing else) OR 1 big + up to 3 small. Core independent.
- S2 = synergist split (Chest+Triceps push / Back+Biceps pull; Shoulders+Glutes; Ham+Quads).
- S3 = identical split to S2; progression is harder movements + heavier load in the DB, not a new split.
- DB-depth multiplier should key off the split's per-day count, not a flat "double."

## Output convention
Write the answer doc to `/home/hermes/timbr/` (e.g. `S_Level_Progression_Answers.md`),
or offer to push as a native Google Doc / new sheet tab so it drops straight into the chat thread.
