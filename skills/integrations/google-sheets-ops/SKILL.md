---
name: google-sheets-ops
description: Working with Google Sheets API — reading, writing, tab management, batch operations. Covers auth, range notation quirks, and known pitfalls for Tanzim's sheets.
category: integrations
tags: [google, sheets, api, oauth, spreadsheets]
---

# Google Sheets Operations

## Auth
Token at `~/.hermes/google_token.json`. Refresh before any call:
```python
import json, requests
with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)
r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': t['client_id'], 'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'], 'grant_type': 'refresh_token'
})
token = r.json()['access_token']
t['token'] = token
with open('/home/hermes/.hermes/google_token.json', 'w') as f:
    json.dump(t, f)
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
```

## Tab names with slashes (MM/DD format — TerraJob pattern)
**Critical:** Tab names like `05/27` require different handling for reads vs writes.

| Operation | Method | Range format |
|-----------|--------|--------------|
| Read (GET) | `spreadsheets/{id}/values/05%2F27!A1:M500` | URL-encode slash |
| Write (PUT) | ❌ FAILS with 404 | — |
| Write (batchUpdate) | ✅ POST to `spreadsheets/{id}/values:batchUpdate` | `'05/27'!A1` in JSON body only |

**Only reliable write method for slash-named tabs:**
```python
r = requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate',
    headers=headers,
    json={
        'valueInputOption': 'USER_ENTERED',
        'data': [{'range': "'05/27'!A1", 'majorDimension': 'ROWS', 'values': rows}]
    }
)
```

## Creating a new tab
```python
requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate',
    headers=headers,
    json={'requests': [{'addSheet': {'properties': {
        'title': '05/27',
        'gridProperties': {'rowCount': 250, 'columnCount': 13}
    }}}]}
)
```

## Getting sheet metadata (list all tabs + IDs)
```python
r = requests.get(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}',
    headers=headers,
    params={'fields': 'sheets.properties'}
)
for s in r.json()['sheets']:
    print(s['properties']['sheetId'], s['properties']['title'])
```

## Deleting a tab
```python
requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate',
    headers=headers,
    json={'requests': [{'deleteSheet': {'sheetId': sheet_id}}]}
)
```

## Updating individual cells (batchUpdate)
```python
data = [{'range': f"'05/27'!L{row_num}", 'majorDimension': 'ROWS', 'values': [[url]]}
        for row_num, url in fixes.items()]
requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate',
    headers=headers,
    json={'valueInputOption': 'USER_ENTERED', 'data': data}
)
```

## AI Foundations Week Tab — Column Map

**Tab name:** `AI Foundations Week` (no slashes — standard read/write, no URL-encoding needed)  
**Sheet ID:** `19v5x4oScpEPXkjHBWvt97UHtWChki5UGniJvop258bc` (Tahmeed profile sheet)

| Col | Letter | Field |
|-----|--------|-------|
| 1 | A | Status (✅ / ⏳ / ☐) — tick/checkbox column |
| 2 | B | Date |
| 3 | C | Day |
| 4 | D | Section # |
| 5 | E | Topic |
| 6 | F | Duration (min) |
| 7 | G | Key Concepts Covered |
| 8 | H | YouTube Resource |
| 9 | I | Hands-On Task |
| 10 | J | Gate Test Score (/5) |
| 11 | K | Quiz Questions (logged) |
| 12 | L | Blockers / Notes |

**⚠️ Status is col A, NOT col L.** Earlier skill doc had Status listed as col L (index 11) — that was wrong. Confirmed from live sheet read Jun 2 2026: col A holds the status symbol (✅/⏳/☐).

**Row layout:** Row 1 = headers. Row 2 = title banner. Row 3 = blank. Day 1 = rows 4–8. Day 2 = rows 10–14. Day 3 = rows 16–21. Day 4 = rows 23–29. Day 5 = rows 31–38. Blank separator rows between days. Row 40 = weekly score summary.

**Status values:** `✅` (done), `⏳` (gate test pending / awaiting response), `☐` (not yet started)

**Confirmed working write pattern (batchUpdate):**
```python
updates = [
    # Mark content section done (col A)
    {'range': "'AI Foundations Week'!A16", 'majorDimension': 'ROWS', 'values': [['✅']]},
    # Gate test row: pending status + quiz Qs in K + blockers in L
    {'range': "'AI Foundations Week'!A21", 'majorDimension': 'ROWS', 'values': [['⏳']]},
    {'range': "'AI Foundations Week'!K21", 'majorDimension': 'ROWS', 'values': [['Q1: ... | Q2: ... | Q3: ...']]},
    {'range': "'AI Foundations Week'!L21", 'majorDimension': 'ROWS', 'values': [['Blocker notes here']]},
    # Gate test score (when available) in col J
    {'range': "'AI Foundations Week'!J21", 'majorDimension': 'ROWS', 'values': [['4/5']]},
]
r = requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate',
    headers=headers,
    json={'valueInputOption': 'USER_ENTERED', 'data': updates}
)
```
**Sheet ID:** `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI`
**Columns:** `pdf_resume, score, company, position, location, remote, salary_min, salary_max, posted_date, alert, first_seen, url, source`
**Tab naming:** MM/DD (e.g. `05/27`). One tab per job search session.
**Source values:** `manual` (hand-logged), `jobspy_linkedin` (scraped)
**URL format:** `https://www.linkedin.com/jobs/view/{job_id}` (no trailing slash)

### Seattle metro — keep vs. drop
Tanzim's "Seattle jobs" filter = **Seattle proper + the Eastside**. Keep anything in:
- Seattle, WA
- Bellevue, WA
- Kirkland, WA
- Redmond, WA
- Remote (remote=TRUE, any location string)

Drop: Renton, Auburn, Kent, Tacoma, Bothell, Monroe, Marysville, Woodinville, Federal Way, SeaTac, Tukwila, Mountlake Terrace, Edmonds, Puyallup, Issaquah, Covington, Arlington VA, and anything clearly out-of-state.

**Rule of thumb:** if it's on the Eastside across Lake Washington (Bellevue/Kirkland/Redmond corridor), keep it. If it's south of Renton or north of Bothell, drop it.

## LinkedIn job URL lookup pattern
Search LinkedIn with title + company in keywords, scrape `jobPosting:(\d+)` from HTML, verify each ID by checking `og:title` of `linkedin.com/jobs/view/{id}/`. Company name must appear in og:title — if not, re-search with broader/different terms.

## Dual-tab output pattern (Master + Dated snapshot) — Crawl/Append Workflows

**Pattern:** Large scrapes or repeated data collection jobs that need both cumulative history + daily snapshots.

**Architecture:**
- **Results tab** (or equivalent master): Cumulative list of all results across all runs. Append only; never clear. Row ID / Run ID column distinguishes runs within the tab.
- **Dated tab** (e.g., "Jun 05", "Jun 06"): One tab per calendar date. Created fresh if doesn't exist; cleared if it does (overwrites previous run same day). Receives same data as Results.

**Implementation pattern:**

```python
from datetime import datetime

run_id = datetime.now().strftime('%Y%m%d-%H%M%S')  # Unique per run
date_tab = datetime.now().strftime('%b %d').lstrip('0')  # 'Jun 05' format

# Get master Results tab
results_ws = sheet.worksheet('Results')

# Create or clear dated tab
try:
    dated_ws = sheet.add_worksheet(title=date_tab, rows=500, cols=11)
except:  # Tab exists
    dated_ws = sheet.worksheet(date_tab)
    dated_ws.clear()

# Add headers to dated tab (Results tab should already have headers)
headers = ['col1', 'col2', 'col3', ..., 'Crawled At', 'Run ID']
dated_ws.append_row(headers)

# Append to both tabs simultaneously
for result in results:
    row = [result['field1'], ..., datetime.now().isoformat(), run_id]
    results_ws.append_row(row)  # Master cumulative
    dated_ws.append_row(row)    # Daily snapshot
```

**Benefits:**
- **Results tab** enables analysis across all historical runs (filter by Run ID for per-run subset)
- **Dated tab** provides daily rollup without needing to filter master tab
- **Run ID** column allows distinguishing multiple runs within the same date
- Follows Job Tracker pattern (master + daily tabs)

**Date tab naming conventions:**
- Format: `Mon DD` (space-padded, e.g., "Jun 05", "Dec 25")
- Use `.lstrip('0')` on `strftime('%b %d')` to remove leading zero from single-digit days
- One tab per calendar day (not per run; one day can have multiple runs appended to the same dated tab)

**Pitfall:** If you want to "restart" a dated tab mid-day (overwrite previous runs), call `dated_ws.clear()` after getting the worksheet — do NOT delete and recreate, or row 1 loses headers.

→ See `references/sheets-dual-tab-crawl-pattern-jun2026.md` for full case study (IG-1 Protocol v2.1 implementation).

## No-auth read of a PUBLIC sheet — gviz CSV endpoint (skip OAuth entirely)
When a sheet is link-shareable and you only need to READ, don't bother with the token or the browser. Pull tabs directly as CSV:
```python
import urllib.request, csv, io
base = "https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&gid={GID}"
rows = list(csv.reader(io.StringIO(urllib.request.urlopen(base.format(SID=sid, GID=gid)).read().decode())))
```
- The `/export?format=csv&gid=` endpoint works too, but `gviz/tq?tqx=out:csv` quotes fields cleanly.
- **PITFALL — `&sheet=<TabName>` lookup is unreliable:** requesting a tab by NAME (`...out:csv&sheet=Conditioning`) silently FALLS BACK to the default/first tab on a near-miss instead of erroring. This session it returned the Strength tab's data under three different tab-name queries, producing bogus "all rows are Strength" counts. **Always address tabs by numeric `gid`, never by name.**
- The browser tools hung on this Google Sheets URL (snapshot/vision timing out); the curl/urllib CSV path worked first try. For pure reads, reach for the CSV endpoint before the browser.

### Getting the tab→gid map without auth
The edit-page HTML is obfuscated and won't yield names. Use the **htmlview** export instead — it carries a clean `{name:"…", … gid:"N"}` menu:
```bash
curl -sL "https://docs.google.com/spreadsheets/d/{SID}/htmlview" -o /tmp/hv.html
```
```python
import re
h = open('/tmp/hv.html', encoding='utf-8', errors='ignore').read()
for m in re.finditer(r'\{name:\s*"([^"]+)",[^}]*?gid:\s*"?(\d+)', h):
    print(m.group(2), '=>', m.group(1))   # gid => Tab Name
```

## Structural-drift QC across "parallel" tabs — compare COLUMN SETS, not just rows
Before trusting a multi-tab DB, diff each tab's HEADER against the canonical one. Tabs that should be parallel often aren't: one was half-built.
- This session: Conditioning DB and Hybrid DB each carried the full scoring block (Skill/Coordination, Stability, Flexibility, Grip, Learn, **Level Score, Unified Level, Risk Gate**); **Strength DB had only the 9 base columns** — no computed level, no risk gate. So it can't be scored until the block is extended to it. `[x for x in canonical_header if x not in tab_header]` surfaces exactly the gap.
- Bundle the standard cross-tab integrity sweep: (a) header/column-set diff per tab, (b) cross-tab duplicate exercise names (`set(tabs_seen)>1`), (c) blank Level Score / Risk Gate cells, (d) Level vs Unified Level prefix mismatch, (e) per-tab distribution of Risk Gate + Unified Level (Counter) as a sanity read. A clean sweep = "no strays, no dupes, no blanks" stated plainly; the one real finding leads.

## Reverse-engineer the LIVE formula from the data — trust cells over docs
When a user asks "is this the right formula / find out the truth," **do not quote the documentation tab.** Docs drift; the data is ground truth. Recover the formula by brute-forcing candidates against the actual values:
- Write 3–5 plausible formulas as lambdas over the input columns, run each across every row, count exact matches vs the computed-result column. The one that matches **N/N** is the live formula. This session a single candidate hit 97/97 — `Difficulty = (Skill/Coordination × 2) + Flexibility + Grip − 3` — and proved the SCORING LOGIC + FX tabs were quoting a STALE formula (Strength×2, even an older −4 variant).
- **Check which input COLUMNS actually exist first.** The doc named a "Strength" input that wasn't a column at all — the real inputs were Skill/Coordination, Stability, Flexibility, Grip, Learn. A formula referencing a non-existent column is your first clue the doc is stale.
- Once recovered, the deliverable is usually **fix the docs to match reality**, not change the data. Leave the historical/v1 formula block intact as record; correct only the "active/v2" cards and flip any "coach-blocked / not-yet-applied" warning to "applied" once the data proves it's live.
- Report it as a finding, not a theory: "the live data obeys exactly one formula, N/N rows match" — then name the consequence (docs are stale / fix was already applied).

## Stress-test a derived formula for FACE-validity, not just math-validity
A formula can be mathematically perfect (every row computes, range correct) and still be **wrong** because the outputs fail the eyeball test. Always run both gates:
- **Math gate:** theoretical min/max from input ranges, actual value distribution (`Counter`), input-variance per column.
- **Face gate:** sort by the output and read the extremes + a handful of known anchors. This session exposed the real flaw — Back Squat & Bench scored **5**, *below* a farmer's carry, because Skill barely varies (65/97 rows = "1") so Difficulty was being driven by the weakest signals (Grip/Flexibility), and the load axis had been dropped entirely. The math was flawless; the ranking was not.
- **Diagnose the cause, don't just flag the symptom.** Low variance in a heavily-weighted input collapses the signal; a removed axis (here Strength/load) silently changes what the metric even *measures* ("how awkward to hold/move" ≠ "how hard"). State the trade-off plainly: the fix that solved one end (machines no longer over-tier) can over-correct the other (heavy compounds now under-tier). Surface it before it propagates downstream (into plan generation), then offer options.

## TIMBR selection-engine build (clusters, naming, S1/S2/S3, gate stack)
For the TIMBR WORKOUT DATASET work — defining movement-pattern clusters, the multi-key progression
sort, Tanzim's `[Variant] [Equipment] [Movement]` naming convention, deriving S1/S2/S3 as a
yes/no DECISION TREE (not a formula), the S123 LOGIC explainer-tab template, and the three-tier
selection GATE STACK (filter → target → rank) with data-driven Equipment/Role/Unilateral columns,
and the **locked classifier correction** (classify on INTRINSIC axes only — equipment is a user
filter never a classifier — plus the fit-formula-against-existing-labels method), the
**constrained "alternative exercise" column** (closest match within the same tier, ranked by
movement→muscle-part→group, orphan-flagging), the **mirror+recompute live-lookup QC columns**
(Alt Level / Difficulty / LC / Risk / Verified Alt Level that self-check `K==G`), and the
**8-checks-per-row fact-check battery** (recompute every column from source, "0 errors" as proof):
→ See `references/timbr-selection-engine-patterns.md`.

For the WORKOUT PLAN DB schema (Sagar's trainer-selects-level + client-swaps-alternates pattern,
Alt_Pool tag convention, minimum pool depth per group per level):
→ See `references/timbr-workout-plan-db-pattern.md`.

## Deriving a classifier formula — fit candidates against existing hand-labels
When asked to turn an existing categorical column (tiers, bands, grades) into a reproducible formula
over other columns, **don't theorise the thresholds — measure them.** Write 2–3 candidate formulas as
lambdas, run each across every row, count exact matches vs the hand-labels, pick the highest match-rate.
Report it as "N/M match" and name the disagreeing rows for the user's eye — a single mismatch on a
borderline row is usually a genuine edge case, not a formula flaw, so flag it rather than auto-resolving.
Prefer a 2-gate cascade (`IF a<=X -> L1; ELSE IF b<=Y -> L2; ELSE L3`) over a single weighted composite
when the cascade scores higher — composites are cleaner as one number but often lose accuracy by letting
one high-variance axis over-promote rows. Write the winner as a LIVE formula column so every row
self-classifies and mismatches stay visible (widen the grid via appendDimension first if the target
column is past the current width).

## Standalone "explainer" tab for non-technical stakeholders
When the user wants a tab that they + a named collaborator can "easily read and understand — no jargon, no extra wording": build a dedicated tab (not a row buried in the logic sheet). Structure: title → THE FORMULA (front and centre) → a small table of each element + a one-line plain-English reason → why-X-was-excluded → the alternative that was rejected and why → known limitation (stated honestly). Use `addSheet`, write rows, then format with `batchUpdate`: set column widths, `wrapStrategy: WRAP` + `verticalAlignment: TOP` on the body, bold + a light background colour on section-header rows. Keep it to ~20 rows; respect "no extra wording" literally.

## Destructive ops — safe sequence
**Never clear+rewrite a sheet tab that contains manually-entered data without a local backup first.**
- `values().clear()` followed by `values().update()` is not atomic — if the write fails mid-way, data is gone.
- Drive revision history exists but `revisions().get(alt=media)` returns 404 for native Sheets files — you cannot restore from revision via API.
- **Safe sequence for bulk edits:**
  1. Read all rows into memory first
  2. Compute new row set locally
  3. If any row was manually entered (source=`manual`), write the filtered set back — do NOT clear first; use `values().clear()` only after confirming write succeeded, or use batchUpdate which overwrites in-place.
  4. Log dropped rows to terminal output before writing so they can be restored if intent was wrong.

## Multi-sheet workflow pitfalls
**Before creating or moving tabs across sheets, verify destination intent with context clues:**
- Do NOT assume which sheet a guide/tab should live in — ask the user or read their earlier statements about structure.
- **Blind execution → rework**: Creating a tab in one sheet, then moving it because the user meant a different sheet, wastes cycles.
- **Safe sequence:**
  1. List current tabs in all sheets involved (what exists now)
  2. Read user's earlier statements about which sheet owns what (e.g., "Master Master File has Job Hammer and IG-1 Protocol")
  3. If ambiguous, ask: "Add Team User Guide to IG-1 Protocol sheet or Master Master File?" — don't guess.
  4. Execute once with full context, not in phases.

**When user says "undo the last step":**
- Reverse in reverse order (if you created tab A then deleted tab B, restore tab B then delete tab A)
- Verify final state matches what existed before your last action
- Confirm restoration with user

## Appending a NEW column (non-destructive tag/classification column)

**Use case:** Add a classification/tag column (e.g. "Actual Classification" = Cardio/Strength) to the right of existing data without touching any existing cells, formats, formulas, or frozen panes.

**Pitfall — grid limits:** Writing to a column index beyond the sheet's `columnCount` fails with:
`400 Range (...) exceeds grid limits. Max rows: N, max columns: M`
A standard 8-col tab will reject a write to col I until you GROW THE GRID first.

**Correct two-step sequence:**
```python
# 1. Grow the grid by one column (non-destructive — only adds empty space to the right)
svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': [
    {'appendDimension': {'sheetId': GID, 'dimension': 'COLUMNS', 'length': 1}}
]}).execute()

# 2. Now write header + values into the new column
body = {'values': [['Actual Classification']] + [[tag] for tag in tags]}
svc.spreadsheets().values().update(
    spreadsheetId=SID, range='PERFORMANCE DB!I1:I101',
    valueInputOption='RAW', body=body).execute()
```
- `appendDimension` needs the numeric `sheetId` (gid), not the tab name. Get it from metadata first.
- This append touches NO existing data, banding, conditional formatting, or frozen panes — safe to tell the user "nothing breaks."
- **Always read the live tab to get the REAL row count + correct gid before writing.** Compacted/summary notes drift — verify gid and column existence against the live sheet, never trust a remembered claim that "column X already exists." This session a summary claimed a classification column existed; it did not.

## Picking layman labels for tag columns
When adding a categorical column for an end-user-facing product, prefer everyday gym/domain language over technically-correct jargon. Tanzim's call this session: rejected "Aerobic/Anaerobic" (correct but jargon) in favour of **"Cardio/Strength"** (how people actually talk). Lead with the plain-language pairing; offer the precise term only if asked.

## Cross-tab comparison trap — verify label schemes match before diffing
When computing a value (e.g. a rollup) and reconciling it against an existing manual column across multiple tabs, **read the distinct values of that manual column per tab first.** Tabs that look parallel may use different label schemes.
- This session: TIMBR DBs use **Foundation = F0–F3, Strength = S1–S3, Performance = P1–P3.** Comparing a computed F-band against the S/P labels produced a meaningless "100% mismatch" on two tabs. Only Foundation was a valid F-vs-F diff (47/149 real mismatches).
- Rule: before reporting a mismatch rate, sanity-check it. ~100% disagreement almost always means you're comparing two different scales, not that the data is wrong. Pull `set(col_values)` per tab and confirm they share a vocabulary.
- When the user wants schemes unified, write the unified value into a NEW column and leave the original per-tab labels intact (he asked: "unified into 1 but the detailed version stays").

## Weighted rollup gotcha — a low-weighted-but-dominant axis can collapse the distribution
When banding a weighted composite (e.g. `Risk×0.40 + Difficulty×0.35 + LearningCurve×0.25` → F0–F3), check the resulting distribution before calling it done. If one heavily-weighted axis clusters low across most rows (e.g. Risk sits at 2–3 for nearly all lifts), it drags genuinely-advanced items into the beginner band. Flag the skew and offer either a weight nudge or a per-tab floor — don't ship a formula that tags strength lifts as "absolute novice."

## execute_code state does NOT persist — build a reusable helper module
Each `execute_code` run is a fresh interpreter: variables, `svc`, imported creds — all gone next call. Re-importing/re-authing inline every run is wasteful and error-prone.
**Fix:** write a small persistent helper file ONCE, then `import` it each run.
```python
# /home/hermes/gs.py  — written once via write_file, reused all session
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
SHEET="<id>"; TOK="/home/hermes/.hermes/google_token.json"; CS="/home/hermes/.hermes/google_client_secret.json"
def _svc():
    ti=json.load(open(TOK)); cs=json.load(open(CS)); inner=cs.get('installed') or cs.get('web') or {}
    creds=Credentials(token=ti.get('token') or ti.get('access_token'), refresh_token=ti.get('refresh_token'),
        token_uri=ti.get('token_uri') or inner.get('token_uri','https://oauth2.googleapis.com/token'),
        client_id=ti.get('client_id') or inner.get('client_id'),
        client_secret=ti.get('client_secret') or inner.get('client_secret'),
        scopes=ti.get('scopes') or ['https://www.googleapis.com/auth/spreadsheets'])
    if not creds.valid: creds.refresh(Request()); json.dump({**ti,'token':creds.token},open(TOK,'w'))
    return build('sheets','v4',credentials=creds,cache_discovery=False)
svc=_svc()
def get(rng): return svc.spreadsheets().values().get(spreadsheetId=SHEET,range=rng).execute().get('values',[])
def put(rng,v): return svc.spreadsheets().values().update(spreadsheetId=SHEET,range=rng,valueInputOption='USER_ENTERED',body={'values':v}).execute()
def meta(): return svc.spreadsheets().get(spreadsheetId=SHEET).execute()
```
Then every later run starts: `import sys; sys.path.insert(0,'/home/hermes'); from gs import *`.
- The `google-api-python-client` + `Credentials`/`Request` refresh path is the discovery-client equivalent of the raw-`requests` auth block above; both read the SAME token file. Use whichever, but don't mix mid-session.
- The discovery client (`build('sheets','v4',...)`) gives you `appendDimension`, `copyPaste`, `updateDimensionProperties` batchUpdate requests cleanly — preferred for grid/format ops.

## Gate vs. weight — decouple a "danger/quality" axis from the tier score
When an axis (Risk, Spotter-needed, etc.) shouldn't *drive* the tier but still needs to be surfaced, make it a **separate flag column**, not a weighted term in the score. This session: Risk-of-Injury was pulled out of Level entirely and mapped to a `Risk Gate` column (`Clear` / `Coaching` / `Spotter`), so a Back Squat correctly sits at the top skill tier (F3) AND carries a `Spotter` flag — high risk without being mislabelled "advanced". Map raw value → band with a simple threshold function (e.g. 2–3→Clear, 4–6→Coaching, 8–9→Spotter); read the live value distribution FIRST so thresholds land on real holes, not guesses.

## Verify by RECOMPUTE-PARITY, not by eyeballing written cells
The strongest 3-gate QC for a derived column: re-derive the value independently from raw inputs in code, then diff against what's written in the sheet. Report "N OK, M mismatch" with the mismatching rows named. This session: 375/375 gate-recompute parity, plus header parity (every tab's new col header == expected string), plus confirming the upstream Level Score cells were untouched. A mismatch list of length 0 is the proof — not "looks right."
- When formatting a newly-added column to match the tab, `copyPaste` with `pasteType: PASTE_FORMAT` from an existing header cell (row 1) → new header cell, and from a data cell (row 2) → the new data range. Clones bold/navy header + non-bold body in two requests, no manual style spec.

## Rebuilding a stale tab from its already-scored TWIN — don't hand-rebuild what already exists
When a tab is found "half-built" (missing the scoring/computed block), look for a parallel tab that already carries the full schema for the SAME rows before reaching for manual recompute. This session: `STRENGTH DB` was the stale v1 copy (9 cols); `S-123` was its fully-scored v2 twin — same 97 exercises, same order, all 17 cols populated and already consistent with Conditioning/Hybrid. The fix was a rebuild-from-twin, not 97 hand-scores.
- **Confirm the twin really IS the same data before trusting it:** diff exercise-name sets (`set(a)==set(b)`), confirm same length, confirm same order (`names_a==names_b`). Only then treat it as the source of truth.
- **Expect the shared base columns to DIFFER, and decide consciously.** Here Difficulty/LearningCurve/Risk disagreed on 79/97 rows (v2 recompute vs old v1). To keep the rebuilt tab internally consistent (Level Score must reconcile with the visible inputs), overwrite those base columns from the twin too — a partial copy that keeps old inputs but new scores is silently broken. Flag this to the user before writing ("rebuild overwrites the old v1 Difficulty/LC/Risk on 79 rows") and get the go-ahead.
- **Align to a CANONICAL header before writing.** Pick the reference tab's header (here CONDITIONING DB), assert the twin's header equals it (`cond_hdr==src_hdr`), pad every row to the column count, write header+body in one `values().update` to `A1:Q{n}`.
- **Always back up the target to a local JSON file first** (`~/backups/<TAB>_backup_<ts>.json`) — Sheets revision API can't restore native files (see Destructive ops). Then write, then run recompute-parity QC + header-parity across all sibling tabs and report `blanks=0` plainly.
- **Watch for business-rule floors that the raw twin data violates.** STRENGTH DB has a "cannot read below F1" floor in SCORING LOGIC, but the v2 twin carried 31 rows at F0. After a rebuild, re-check documented per-tab floors against the new distribution and flag the conflict — don't silently ship data that breaks a stated rule, but don't auto-apply the floor either; surface it and let the user choose.

## Merging two spreadsheets into one canonical file — "latest wins" dedup

When a user asks to combine two overlapping sheets into a new master file:
- **Establish recency objectively, don't guess.** Pull `createdTime` + `modifiedTime` from the Drive API (`drive.files().get(fileId=..., fields='name,createdTime,modifiedTime')`) and let the newer file win every overlap. The user's instinct about "which is latest" is often wrong — show them the dates.
- **Dedup by KEEPING the richer/newer version of each overlapping tab; only fold in tabs the winner LACKS.** Don't blindly concatenate both files — that duplicates most of the content. Map a tab plan first (new tab name → source file → source tab), read all data into a dict, then build.
- **Create the new spreadsheet with all tabs at once:** `svc.spreadsheets().create(body={'properties':{'title':...},'sheets':[{'properties':{'title':t}} for t in tab_order]})`. Then `values().batchUpdate` with one `{'range':"'Tab'!A1",'values':v}` per tab.
- **Add a README/provenance tab** at the top: built date, merge rule ("latest wins"), source file IDs, one-line "how to read" tab guide. Future readers need to know what governed the merge.
- **Clean as you merge** when the user says "empty out invalid texts / old ones get deleted": strip fully-empty rows (`[r for r in rows if any(c.strip() for c in r)]`) and stitch broken cells.
- **Format pass after writing:** freeze row 1, bold + dark-bg header row, `wrapStrategy:WRAP` + `verticalAlignment:TOP` on the whole grid, widen col A (~230px) and body cols (~430px). One `batchUpdate` per sheetId.

## PITFALL — hyperlinks DIE when you copy cell VALUES between sheets
`values().get` / `values().batchUpdate` move only the displayed text, NOT the embedded hyperlink. A cell reading "Open in Canva" with a link behind it copies as dead plain text — the URL is silently lost.
- **Recover the real URLs** from the source via the grid API, checking BOTH `hyperlink` and `textFormatRuns[].format.link.uri` (link can live in either):
```python
res = svc.spreadsheets().get(spreadsheetId=SRC, ranges=["'Tab'!A1:B11"],
    fields='sheets.data.rowData.values(formattedValue,hyperlink,textFormatRuns)').execute()
for r in res['sheets'][0]['data'][0]['rowData']:
    for c in r.get('values',[]):
        link = c.get('hyperlink')
        if not link:
            for run in c.get('textFormatRuns',[]) or []:
                link = link or run.get('format',{}).get('link',{}).get('uri')
```
- **Restore by writing the bare URL** with `valueInputOption='USER_ENTERED'` (Sheets auto-relinks a raw URL), or a `=HYPERLINK(url,"label")` formula to keep the label. After any cross-sheet copy, audit link-bearing cells and re-inject — don't assume the copy carried them.

## Reading a many-tab sheet cover-to-cover for review
When the user wants you to "read through all of them one by one," batch several tabs per `execute_code` call, print with tab headers, and read before commenting. The discovery client + OAuth token path works first try; the browser HANGS on Google Sheets URLs — don't reach for browser tools to read a sheet.

## Compact credential/dense-data tabs — CLIP + fixed row height
When a tab has cells with large multi-line content (JSON blobs, cookie arrays, long bios) and the user wants rows compact WITHOUT losing the data:
- **DO NOT use WRAP** — that blows out row height to match content
- **Use CLIP + fixed pixel height:** content is preserved in the cell (click to see/copy), display is capped
```python
requests = [
    # Clip all cells (don't wrap, don't overflow — just clip display)
    {'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': 0, 'endRowIndex': 200},
        'cell': {'userEnteredFormat': {'wrapStrategy': 'CLIP', 'verticalAlignment': 'MIDDLE'}},
        'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'
    }},
    # Fix row height at 24px
    {'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': 1, 'endIndex': 200},
        'properties': {'pixelSize': 24}, 'fields': 'pixelSize'
    }},
]
svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': requests}).execute()
```
Column widths to pair with this (for a handle/password/cookie layout): Handle 180px, Password 140px, Cookie 420px.

## Centre+middle align ALL tabs in one call
```python
meta = svc.spreadsheets().get(spreadsheetId=SID).execute()
sheet_ids = [s['properties']['sheetId'] for s in meta['sheets']]
requests = [
    {'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': 0, 'endRowIndex': 200, 'startColumnIndex': 0, 'endColumnIndex': 26},
        'cell': {'userEnteredFormat': {'horizontalAlignment': 'CENTER', 'verticalAlignment': 'MIDDLE', 'wrapStrategy': 'CLIP'}},
        'fields': 'userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy)'
    }} for sid in sheet_ids
]
svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': requests}).execute()
```

## Deduplication audit before rewriting a tab
Before clearing+rewriting a credentials/data tab, scan it first:
```python
rows = svc.spreadsheets().values().get(spreadsheetId=SID, range='Tab!A1:C200').execute().get('values', [])
for i, r in enumerate(rows, 1):
    handle = r[0] if r else ''
    has_pw = bool(r[1]) if len(r) > 1 else False
    has_data = bool(r[2]) if len(r) > 2 else False
    print(f"{i:3} | {handle:<35} | pw:{has_pw} | data:{has_data}")
```
Keep only rows with pw OR data (or both). Rows where both are False and the handle is "account not found" / empty = dead weight, delete.

## CRITICAL — subagent toolsets hit a DEMO account, not Tanzim's real Google account
The `gmail` and `google_sheets` subagent toolsets are connected to a sandbox/demo account (emails addressed to "Alex" at alex@example.com; sheets containing fake food inventory data). Every result they return is fabricated. **Never use them for any real Google operation.**

Always use: `terminal` + `python3` + `googleapiclient` with creds at `~/.hermes/google_token.json`.

This applies equally to Gmail reads, Sheets reads, Sheets writes, and Drive searches.

## STRENGTH DB overwrite incident (Jul 2026) — lesson encoded
Cleared STRENGTH DB with `values().clear()` before understanding what the original data looked like. Had to restore from FX-2 (a parallel tab that happened to have the same data). The Sheets revision API (`revisions().get(alt=media)`) returns 404 for native Sheets files — you cannot restore via API. The only recovery was a parallel tab.

**Rule:** Before `clear()`-ing any tab, read and print a row count + first 3 rows first. If the tab contains manually entered or hard-to-reconstruct data, ask before clearing.

## Other pitfalls
- **Don't run a `gs.py`-importing script from `/tmp`.** Running `python3 /tmp/foo.py` shadowed the home `gs.py` helper and `import gs` resolved to a different module (`AttributeError: module 'gs' has no attribute 'get'`). Fix: `cp /tmp/foo.py ~/foo.py` and run from `~`, or `sys.path.insert(0,'/home/hermes')` before the import.
- **`&` in a heredoc/Python comment trips the foreground shell guard** ("uses '&' backgrounding"). When running Python via `python3 << 'EOF'`, avoid literal `&` in comments/strings (write "plus"/"and") or the terminal wrapper may reject the command. Rerun without the `&`.
- Tab name `&` in sheet names → avoid; use `+` or `and`
- `PUT /values/{range}` with quoted range in URL → 404. Use batchUpdate POST instead.
- `values:batchUpdate` URL must NOT contain the range — range goes in JSON body only
- After merging two tabs (read both, combine, write to tab1, delete tab2), verify row count
- **clear() then update() = data loss if intent was wrong.** Always log what you're dropping before writing. Confirm with user if the filter rule is ambiguous before executing.
