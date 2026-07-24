---
name: timbr-workout-dataset
category: timbr
description: Working on the TIMBR - WORKOUT DATASET Google Sheet — reading/writing tabs, computing exercise alternatives, maintaining naming conventions, and running logic validation passes.
triggers:
  - TIMBR workout dataset
  - WORKOUT PLAN DB
  - STRENGTH DB alt exercise
  - timbr google sheet
---

# TIMBR Workout Dataset — Google Sheets Operations

## Sheet ID
`1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`

## Credentials
Google OAuth token at `/home/hermes/.hermes/google_token.json` — authorized_user type. Use `google.oauth2.credentials.Credentials` with refresh token. Venv may be needed if pip is externally managed.

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)

creds = Credentials(
    token=t.get('token'), refresh_token=t.get('refresh_token'),
    token_uri=t.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=t.get('client_id'), client_secret=t.get('client_secret'),
    scopes=t.get('scopes')
)
svc = build('sheets', 'v4', credentials=creds)
```

## Sheet structure (July 2026)
Tabs: `WORKOUT PLAN DB`, `TRAINING SPLIT`, `SOURCE OF TRUTH`, `FX - 2`, `STRENGTH DB`, `CONDITIONING DB`, `HYBRID DB`, `MUSCLE PAIRING`, `S Level Progression`

### STRENGTH DB schema
`Computed Level | Exercise Name | Difficulty | Learning Curve | Risk of Injury | Muscle Size | Muscle Part | Muscle Group | Skill | Flexibility | Grip | Load | Cluster`

- **Computed Level**: S1/S2/S3 via FX-2: `max(Difficulty, LC, Risk)` → ≤3=S1, 4–6=S2, ≥7=S3
- **Cluster**: movement pattern (Horizontal Press, Vertical Pull, Leg Curl, Fly, Hip Thrust, etc.)

### WORKOUT PLAN DB schema
`Computed Level | Muscle Group | Primary Exercise | Alt Exercise 1 | Alt Exercise 2`

---

## Alt Exercise Logic (locked July 2026)

### Col D — Alt Exercise 1
- Same Computed Level + Same Muscle Group + Same Cluster as Primary
- **Different equipment type** from Primary
- Fallback: any different exercise at same level + muscle group (if no cross-equipment same-cluster option)

### Col E — Alt Exercise 2
- Same Computed Level + Same Muscle Group + **Different Cluster** from Primary
- Must not duplicate Col C or Col D — hard dedup, left-to-right
- Fallback: any different exercise at same level + muscle group not already used

### Equipment taxonomy (derive from name prefix)
Check multi-word prefixes FIRST before single-word ones to avoid mis-tagging:

| Prefix | Tag |
|--------|-----|
| Smith Machine | Smith Machine |
| Stability Ball | Stability Ball |
| Trap-Bar | Barbell family |
| T-Bar | Barbell family |
| EZ-Bar | EZ-Bar |
| Machine | Machine |
| Cable | Cable |
| Dumbbell | Dumbbell |
| Barbell | Barbell |
| Bodyweight / Hanging / Weighted / GHD | Bodyweight |
| TRX | TRX |

---

## Naming conventions (enforced)
- Every exercise name must start with its equipment type — the prefix IS the taxonomy
- Format: `[Equipment] [Movement] ([variant])` — brackets only when a modifier distinguishes variants
- Capitalise all meaningful words
- Five exercises renamed July 2026 (Bodyweight prefix added):
  - `Tricep Dip (bodyweight)` → `Bodyweight Tricep Dip`
  - `Kneeling Ab Rollout` → `Bodyweight Kneeling Ab Rollout`
  - `Nordic Curl` → `Bodyweight Nordic Curl`
  - `Dragon Flag` → `Bodyweight Dragon Flag`
  - `L-Sit (parallel bars)` → `Bodyweight L-Sit (parallel bars)`
- After any rename in STRENGTH DB, propagate to WORKOUT PLAN DB

---

## Workflow: testing logic changes
1. Duplicate the tab first — never touch the live tab with experimental logic
2. Name the test tab `[TAB NAME] - TEST`
3. Trim test tab to 10 rows only
4. Review row-by-row with Tanzim before applying to full tab
5. Run full scan after computing
6. Apply to full tab only on explicit green light

## Full scan checklist
- [ ] Zero blanks (or documented as pool gap, not logic error)
- [ ] Zero duplicates within any row
- [ ] Every alt matches Computed Level of its row
- [ ] Every alt matches Muscle Group of its row
- [ ] Equipment swap firing (Alt 1 uses different equipment from Primary where possible)

---

## Pitfalls
- **Alt 1 blanks** — legitimate when a cluster has only one exercise at that S-level. Pool gap, not a bug. Document rather than force a wrong alt.
- **Duplicate rows in WORKOUT PLAN DB** — inflated from prior sessions; 292 rows is too many. Check count after writing.
- **S-level classification** uses `max(Difficulty, LC, Risk)` — not Difficulty alone.
- **gspread `open_by_key` vs `open_by_id`** — use googleapiclient directly to avoid this confusion.
- **Multi-word prefix detection** — always check Smith Machine, EZ-Bar, Trap-Bar etc. before single-word prefixes.

---

## Deploy Opus for compute tasks
When Tanzim says "deploy Opus" — spawn a subagent:
```python
acp_args=["--model", "claude-opus-4-5"]
acp_command="cop"
toolsets=["terminal"]
```
Pass: full logic spec, credentials path, sheet ID, tab name, expected output. Subagent must report row-by-row.

## Support files
- `references/naming-audit-july2026.md` — full naming audit, 5 renames applied
