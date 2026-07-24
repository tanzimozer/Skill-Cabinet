---
name: gsheets-formatting-standard
description: Tanzim's mandatory formatting standard for every Google Sheet created or edited. Wrap + middle + center everywhere; auto-resize rows always. Includes header/section banding, column widths, tab migration pattern, post-format verification, and the rule to never mix unrelated projects into the same spreadsheet.
---

# Google Sheets — Formatting Standard (Tanzim)

**Rule (locked 2026-06-21):** Every sheet I create or populate must be formatted, not raw. Apply as the final step after writing data. Non-negotiable, no need to ask.

## Alignment — by content type (CORRECTED 2026-06-21)

Blanket center on the whole grid is WRONG and Tanzim rejected it — centering long sentences makes them unreadable. Do this instead:

- **Vertical = MIDDLE** everywhere. Always.
- **Wrap = WRAP** everywhere. Always.
- **Horizontal = depends on content:**
  - **Long text / prose / descriptions / sentences → LEFT.** (paragraphs, bullet items, "why it matters" cells)
  - **Short data → CENTER.** (IDs, codes, F-levels, numbers, status flags, dependencies, single-word tags)
  - **Headers / titles → CENTER, bold, white-on-dark.**

The test: if a cell holds a sentence, left-align it. If it holds a token, center it.

## Structure Tanzim expects (reconsider rows & headers)

He flagged "reconsider rows and headers" — a flat wrapped grid isn't enough. A good tab has:
- **Title banner** — merged across all columns, dark background, white bold ~15pt, centered.
- **Italic subtitle** — merged, left-aligned, the one-line "what this is".
- **Section bands** — merged, light-grey background, bold ~11pt, separating logical blocks.
- **Real table headers** — dark background, white bold, centered, on the header row only.
- **Body rows** — aligned by content type (above); zebra banding optional for long tables.
- **Column widths set explicitly** — prose column wide (~500px), data columns narrow (~150-170px).
- **Gridlines hidden** for a clean look (`gridProperties.hideGridlines: true`).
- Spacer (blank) rows between blocks for breathing room.

A reusable block-based renderer that does all this is in `scripts/build_formatted_tab.py` — copy and feed it block tuples (title/sub/section/p/bul/kv/tbl).

## Tab migration between sheets — copyTo + rename + delete

When Tanzim asks to move tabs out of one spreadsheet into a new one:

```python
# 1. Create destination sheet
new_sheet = sheets_svc.spreadsheets().create(body={
    "properties": {"title": "New Sheet Name"},
    "sheets": [{"properties": {"title": "Index"}}]
}).execute()
NEW_ID = new_sheet['spreadsheetId']

# 2. Share it (writer for owner, reader/writer for collaborators)
drive_svc.permissions().create(
    fileId=NEW_ID,
    body={"type": "user", "role": "writer", "emailAddress": "email@gmail.com"},
    sendNotificationEmail=False
).execute()

# 3. Copy each tab (arrives as "Copy of X" — rename immediately)
result = sheets_svc.spreadsheets().sheets().copyTo(
    spreadsheetId=OLD_ID,
    sheetId=old_tab_id,
    body={"destinationSpreadsheetId": NEW_ID}
).execute()
new_tab_id = result['sheetId']

# 4. Rename to original name
sheets_svc.spreadsheets().batchUpdate(spreadsheetId=NEW_ID, body={"requests": [
    {"updateSheetProperties": {
        "properties": {"sheetId": new_tab_id, "title": "Original Tab Name"},
        "fields": "title"
    }}
]}).execute()

# 5. Delete from old sheet
sheets_svc.spreadsheets().batchUpdate(spreadsheetId=OLD_ID, body={"requests": [
    {"deleteSheet": {"sheetId": old_tab_id}}
]}).execute()
```

Batch all renames + reorders into one `batchUpdate` call on the new sheet, then all deletes into one call on the old sheet — minimises quota usage.

## Pitfall — never mix unrelated projects into the same spreadsheet (2026-07-23)

Tanzim flagged this directly. When building tabs for a NEW project or person, **always create a fresh spreadsheet** — do not append tabs to an existing sheet that belongs to a different project. The TIMBR/IG sheet is for TIMBR ops; Tahmeed's study plan belongs in its own file. When in doubt, create new. Ask if uncertain which sheet a tab belongs to.

## Migrating tabs between spreadsheets (copy-then-delete pattern)

When Tanzim asks to move tabs from one sheet to another:
1. Create the destination sheet first (`spreadsheets().create`)
2. Share it with relevant users immediately (`drive.permissions().create`)
3. Use `spreadsheets().sheets().copyTo(spreadsheetId=SRC, sheetId=TAB_ID, body={"destinationSpreadsheetId": DEST})` — one call per tab
4. Tabs arrive as "Copy of X" — rename them all in a single `batchUpdate` with `updateSheetProperties` requests
5. Reorder tabs in the same `batchUpdate` using `index` field
6. Delete the originals from the source sheet in a second `batchUpdate` with `deleteSheet` requests
7. Update permissions: remove user from old sheet, confirm they have access to new sheet

```python
# Copy tab
result = svc.spreadsheets().sheets().copyTo(
    spreadsheetId=OLD_ID, sheetId=old_tab_id,
    body={"destinationSpreadsheetId": NEW_ID}
).execute()
new_tab_id = result['sheetId']

# Rename (tabs arrive as "Copy of X")
svc.spreadsheets().batchUpdate(spreadsheetId=NEW_ID, body={"requests": [
    {"updateSheetProperties": {
        "properties": {"sheetId": new_tab_id, "title": "Original Name"},
        "fields": "title"
    }}
]}).execute()

# Delete from source
svc.spreadsheets().batchUpdate(spreadsheetId=OLD_ID, body={"requests": [
    {"deleteSheet": {"sheetId": old_tab_id}}
]}).execute()
```

## Pitfall — ALWAYS verify formatting after applying (2026-07-23)

Writing `=== EXAM OVERVIEW ===` directly into a cell makes Sheets parse it as a formula (starts with `=`). Results in `#ERROR!` in every such cell.

**Fix:** Use plain title text (`"EXAM OVERVIEW"`) and style it via a colour-banded `repeatCell` in `batchUpdate`. Never use `===` as a visual separator in cell values.

```python
# BAD — causes #ERROR!
rows.append(["=== EXAM OVERVIEW ===", "", ""])

# GOOD — plain title, colour-banded via batchUpdate
rows.append(["EXAM OVERVIEW", "", ""])
```

## Pitfall — ALWAYS verify formatting after applying (2026-07-23)

Applying `repeatCell` does not guarantee the format landed correctly — API silently accepts malformed requests or earlier formatting can override it. After any format pass, **read back a sample and assert**:

```python
# Verify wrap + middle + center landed on first 3 rows x 3 cols
meta = svc.spreadsheets().get(
    spreadsheetId=SID,
    ranges=["'TAB NAME'"],
    includeGridData=True
).execute()
for sheet in meta['sheets']:
    if sheet['properties']['sheetId'] == TARGET_SHEET_ID:
        rows = sheet['data'][0].get('rowData', [])
        errors = []
        for ri, row in enumerate(rows[:5]):
            for ci, cell in enumerate(row.get('values', [])[:5]):
                fmt = cell.get('effectiveFormat', {})
                if fmt.get('verticalAlignment') != 'MIDDLE' or fmt.get('wrapStrategy') != 'WRAP':
                    errors.append(f"R{ri}C{ci}: {fmt.get('verticalAlignment')} / {fmt.get('wrapStrategy')}")
        print("Errors:", errors or "None — clean.")
```

Common failure mode seen 2026-07-23: `vAlign=BOTTOM` persisted throughout a freshly-built tab after a `repeatCell` pass that specified MIDDLE — because the section-header `repeatCell` calls that came AFTER the global pass also specified `backgroundColor` + `textFormat` but omitted `verticalAlignment`, which reset it to the default (BOTTOM). **Any per-row formatting call that doesn't include `verticalAlignment` in its `fields` will silently reset it.** Always include `verticalAlignment` in every `repeatCell.fields` that touches a row.

## Pitfall — Sheets write quota (RATE_LIMIT_EXCEEDED)

Sheets API caps **60 write requests per minute per user**. Building many tabs with per-tab `values.update` + `batchUpdate` blows through this fast (each tab = 2+ writes). Symptom: `HttpError 429 ... WriteRequestsPerMinutePerUser`.

Mitigations:
- Batch aggressively — one `batchUpdate` with many requests counts as fewer calls than many small ones.
- If building 8+ tabs in a loop, expect to hit the cap mid-run. Sleep ~60s and resume from the tab that failed (the writes are idempotent — re-running a tab is safe).
- Don't retry the identical failing call immediately; wait out the 60s window first.

## Default cell formatting — LOCKED STANDARD (added 2026-07-23)

Every sheet/tab must apply all three on the whole grid, no exceptions:
- **wrapStrategy = WRAP**
- **verticalAlignment = MIDDLE**
- **horizontalAlignment = CENTER**

After writing data, always auto-resize ALL rows to reduce row height to content — do NOT leave rows bloated at a fixed pixel size. Use `autoResizeDimensions` on ROWS. This keeps the sheet tight and readable.

```python
# Standard 3-in-1 format + row auto-resize (apply to every tab, always)
def apply_standard_format(svc, SID, sheet_id):
    svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [
        # 1. Wrap + middle + center on entire grid
        {"repeatCell": {
            "range": {"sheetId": sheet_id},
            "cell": {"userEnteredFormat": {
                "wrapStrategy": "WRAP",
                "verticalAlignment": "MIDDLE",
                "horizontalAlignment": "CENTER"
            }},
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment)"
        }},
        # 2. Auto-resize rows to reduce height (fits content tightly)
        {"autoResizeDimensions": {
            "dimensions": {"sheetId": sheet_id, "dimension": "ROWS"}
        }}
    ]}).execute()
```

**Note on horizontalAlignment:** The content-type rule (prose LEFT, data CENTER) is the design standard for bespoke builds. But Tanzim's locked default is CENTER everywhere — honour it unless he specifies otherwise. Row auto-resize is always included; never leave rows at a fixed oversized height after wrap is applied.

## Minimal whole-grid format (when a quick uniform pass is genuinely fine)

```python
def apply_format(svc, SID, sheet_id):
    """Wrap + middle + center on whole grid + auto-resize rows."""
    req={'repeatCell':{
        'range':{'sheetId':sheet_id},
        'cell':{'userEnteredFormat':{'wrapStrategy':'WRAP','verticalAlignment':'MIDDLE','horizontalAlignment':'CENTER'}},
        'fields':'userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment)'}}
    svc.spreadsheets().batchUpdate(spreadsheetId=SID,body={'requests':[req]}).execute()
```

## Bulk-format ALL tabs in one shot

When Tanzim says "text wrap everything, middle align and centre" across the whole file — he means every tab, and he means it literally. Pull all sheet IDs from metadata, build one `repeatCell` + one `autoResizeDimensions` (ROWS) request per tab, fire them all in a single `batchUpdate`. One round-trip, done.

```python
meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
sheet_ids = [s['properties']['sheetId'] for s in meta['sheets']]

requests = []
for sid in sheet_ids:
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid},
            "cell": {
                "userEnteredFormat": {
                    "wrapStrategy": "WRAP",
                    "verticalAlignment": "MIDDLE",
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment)"
        }
    })
    requests.append({
        "autoResizeDimensions": {
            "dimensions": {"sheetId": sid, "dimension": "ROWS"}
        }
    })

svc.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={"requests": requests}
).execute()
```

**Note on horizontal alignment override:** The content-type rule (prose LEFT, data CENTER) is the design standard. But when Tanzim explicitly says "centre everything", honour it — that's a user-directed blanket pass, not a design error. Apply CENTER uniformly. Don't second-guess it or apply a nuanced split he didn't ask for.

## Pitfall — browser can't render the live Sheets app (use the API, not screenshots)

When Tanzim asks for a "screenshot" of a sheet issue, do NOT try to drive a browser to the live `docs.google.com/spreadsheets/.../edit` URL — the Sheets web app is too heavy and the browser tools reliably time out (navigate + snapshot + vision all hang). Don't loop on it.

Instead, **render the proof image yourself from the API data**:
1. Pull the exact cells with `values.get` (you already have the token + scopes).
2. Confirm the claim programmatically (e.g. search all DB rows for the orphan term → prove 0 matches) so the image states a verified fact, not a guess.
3. Draw a clean table with Pillow (`pip install pillow`; DejaVuSans fonts at `/usr/share/fonts/truetype/dejavu/`) — title, the relevant rows, red-highlight the problem cells, a one-line caption of the issue.
4. Deliver it via the WhatsApp bridge `/send-media` endpoint (`filePath`, `chatId`, `mediaType:image`, `caption`) — see the `whatsapp-media-attachments` skill.

This is faster, more legible, and more reliable than a screenshot — and it forces you to verify the issue against the data before claiming it.

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
d=json.load(open('/home/hermes/.hermes/google_token.json'))
creds=Credentials(token=d['token'],refresh_token=d['refresh_token'],token_uri=d['token_uri'],
    client_id=d['client_id'],client_secret=d['client_secret'],scopes=d['scopes'])
if not creds.valid: creds.refresh(Request())
svc=build('sheets','v4',credentials=creds)
```

## Checkbox columns

Tanzim often wants a boolean status column with real tick-boxes. Add via data validation:

```python
{"setDataValidation":{"range":{"sheetId":TID,"startRowIndex":1,"endRowIndex":n_rows,
    "startColumnIndex":col,"endColumnIndex":col+1},
    "rule":{"condition":{"type":"BOOLEAN"},"strict":True}}}
```
Center the checkbox cells (horizontal+vertical) and keep the width narrow (~110px). Cells then read `TRUE`/`FALSE` in `values.get`.

## Soft-lock a tab ("read and lock" / "acknowledge and lock")

When Tanzim says he tweaked the format himself and wants it locked, he means: protect the LAYOUT but keep it editable for data entry. Use a **warning-only** protected range (soft lock) — editors still get a confirm prompt but can type passwords/values:

```python
{"addProtectedRange":{"protectedRange":{
    "range":{"sheetId":TID},
    "description":"<tab> layout locked — <current column order> (wrap/middle/center)",
    "warningOnly":True}}}
```
Before re-locking, READ the tab first (he says "read and lock" because he moved columns) — capture the new column order into the description. Update the existing protectedRange via `updateProtectedRange` instead of stacking duplicates; check `sheet["protectedRanges"]` first.

## Pitfall — dead OAuth client ("deleted_client")

`~/friday_backup/google_token.json` can be stale — refresh throws `RefreshError: deleted_client: The OAuth client was deleted`. The LIVE token is `~/.hermes/google_token.json` (calendar+docs+drive+gmail+spreadsheets scopes, refreshes clean). Always prefer `~/.hermes/google_token.json`. If a token fails to refresh, probe candidates rather than assuming the tool is broken.

## Clone an existing tab's exact formatting ("make it match tab X")

When Tanzim says a new tab must match an existing one (colours, spacing, widths, heat-map) — don't eyeball it, READ the reference and mirror it cell-for-cell:

1. Pull the reference tab with `includeGridData=True` and inspect `effectiveFormat` per cell: `backgroundColor`, `textFormat(bold,fontSize,fontFamily,foregroundColor)`, `horizontalAlignment`, `verticalAlignment`, `wrapStrategy`. Also grab `columnMetadata[].pixelSize` (widths), `rowMetadata[].pixelSize` (heights), and `gridProperties.frozenRowCount/frozenColumnCount`.
2. If the tab uses a **value-driven heat-map** (e.g. green 1–3 / tan 4–6 / red 7–10 on numeric cols, a score-band tint on rollup cols), there will be **no `conditionalFormats`** — the colours are static per-cell, hand-applied. Derive the value→colour mapping by scanning every row and collecting `{value: set(rgb)}`. Originals are often slightly inconsistent (hand-done); apply a *clean consistent* version of the same scheme rather than copying the noise.
3. Build the new tab with `updateCells` carrying both `userEnteredValue` and `userEnteredFormat` per cell, then set row heights + column widths via `updateDimensionProperties`. Verify by reading both tabs back and diffing format tuples — rounding differences (0.843 vs 0.847) are the same swatch, fine.

Reference scheme seen on the TIMBR exercise DBs: header navy `(0.118,0.157,0.22)` white sz12 centered; data sz10; Level col light-blue `(0.929,0.957,0.988)`; Name white/LEFT; Difficulty/Learning/Risk heat-mapped green/tan/red; rollup cols (Class/Score/Level/Ratio) tinted by score band; row heights 21 (header) / 38 (data).

## Pitfall — `includeGridData=True` rejects qualified A1 sub-ranges

`spreadsheets().get(ranges=["TAB NAME!A1:M3"], includeGridData=True)` throws `400 Unable to parse range` — even with quotes `'TAB NAME'!A1:M3`. With grid data, pass the **bare tab name only**: `ranges=["TAB NAME"]` (no cell sub-range), then slice `rowData[:n]` / `columnMetadata[:n]` in Python. Or fetch the whole spreadsheet with `includeGridData=True` and filter `sheets` by `properties.title`. (Plain `values.get` accepts the qualified range fine — this only bites the grid-data path.)

## Pitfall — apostrophe in tab name breaks values.clear (and values.update range strings)

Tab names containing apostrophes (e.g. `English O'Levels`) cannot be used in range strings passed to `values.clear()` or `values.update()` — the API throws `400 Unable to parse range`. Two fixes:

1. **For clearing:** Use `updateCells` via `batchUpdate` instead — it targets by `sheetId`, no range string needed:
```python
svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [
    {"updateCells": {"range": {"sheetId": gid}, "fields": "userEnteredValue"}}
]}).execute()
```
2. **For writing:** Escape the apostrophe by doubling it in the range string: `'English O''Levels'!A1` (two single quotes inside the outer quotes).

## Sheet content authoring — layman standard (locked 2026-07-23)

When building sheets for non-technical users (students, clients, anyone who isn't Tanzim):
- **Plain English only.** No jargon, no codes (no "R1", "W3", "AO2" — spell it out in plain words).
- **3 columns max** for reference/info tabs: Topic | What it means | Tip or note.
- **No walls of text** in any single cell — one clear sentence per point.
- **Section headers** as colour-banded rows — no nested sub-headers, no indented hierarchy.
- **Less is more** — if a row can be cut without losing meaning, cut it. Tanzim will flag if too sparse; he won't flag if too dense.

## Pitfall — apostrophe in tab name breaks range strings in values.clear / values.update

When a tab name contains an apostrophe (e.g. `English O'Levels`), passing it as a range string like `"'English O'Levels'!A1:Z200"` throws `Unable to parse range`. The single-quote escaping breaks both `values.clear` and `values.update`.

**Fix options:**
1. Use `batchUpdate` with `updateCells` + `fields: "userEnteredValue"` to clear — it takes a sheetId, not a range string, so apostrophes don't matter.
2. For `values.update`, escape the apostrophe by doubling it: `"'English O''Levels'!A1"` — one apostrophe becomes two inside the surrounding single-quote pair.
3. Rename the tab to avoid apostrophes if you control the name.

```python
# Clear via batchUpdate (safe for any tab name)
svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": [
    {"updateCells": {"range": {"sheetId": gid}, "fields": "userEnteredValue"}}
]}).execute()

# Write via values.update with doubled apostrophe
svc.spreadsheets().values().update(
    spreadsheetId=SID,
    range="'English O''Levels'!A1",  # note doubled apostrophe
    valueInputOption='USER_ENTERED',
    body={"values": rows}
).execute()
```

## Layman / plain-English sheet design (Tanzim preference — locked 2026-07-23)

When Tanzim says "layman" or "easy to understand" or "condense":
- **3 columns max** for reference/info tabs. Typical pattern: `What | Detail | Status` or `Topic | What You Need to Know | Tips`.
- **No jargon, no codes, no AO references** in visible cells. Spell out what things mean in plain English.
- **No section rows with `=== X ===`** — use colour-banded section header rows instead. The `===` pattern causes `#ERROR!` in Sheets when not wrapped in a text-safe formula.
- **No walls of bullet points in a single cell.** One clear sentence per cell beats a paragraph.
- **Prose stays left-aligned** when it's a sentence. Data tokens center. Don't blindly center all cells when content is prose.
- Strip all "sources" / "links" / admin clutter into a separate tab or remove entirely — the main tab should only contain what Tahmeed (or the user) needs to act on.

## Pitfall — `=== SECTION HEADER ===` syntax causes #ERROR! in Sheets

When you `values.update` a wide block (e.g. a 13-col grid) and the **API response says it wrote all the columns** (`updatedColumns: 13`) but a **readback returns only the first 2–3 columns** — the cause is **leftover merged cells from the tab's previous layout**. A `values.update` reports success but the data folds into the top-left cell of each merge; D+ come back empty. `clear()` does NOT remove merges. Diagnose + fix:

```python
# 1. Detect merges on the tab
m = svc.spreadsheets().get(spreadsheetId=SID).execute()
for s in m["sheets"]:
    if s["properties"]["sheetId"] == gid:
        print("merges:", len(s.get("merges", [])))   # e.g. 75 leftover C:M merges

# 2. Unmerge the whole region BEFORE rewriting
svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests":[
    {"unmergeCells":{"range":{"sheetId":gid,"startRowIndex":0,"endRowIndex":N,
        "startColumnIndex":0,"endColumnIndex":COLS}}}]}).execute()
# 3. Re-put the block — now lands full-width.
```
When recreating a tab on a NEW schema (different column layout from the old one), **unmerge the full grid as the first build step**, before any `values.update`. Don't trust `updatedColumns` — always read the far cells (`get("TAB!M22")`) back to confirm width landed.

## Pitfall — ragged bulk `put` can drop a single cell mid-block

A large `gs.put` of formula rows occasionally lands a row missing its B/C content (only the leading col survives) — readback total comes up one short (e.g. 272 of 273). Verify counts after a bulk write (`Counter` by size/category against the expected enumeration), locate the gap (`valueRenderOption="FORMULA"` shows the empty cell), and patch just that cell. Don't assume a clean `put` wrote every cell.

## Live edits mid-session — watch for tab renames

The team edits the file concurrently. Tab names/structure can shift under you (e.g. "STRENGTH DB" → "STRENGTH"). Re-list `sheets` before assuming a title or sheetId; flag to Tanzim if the naming convention changed so new tabs match the current set.

## Active project sheets (reference files)
- `references/tahmeed-english-olevel-sheet.md` — Tahmeed's English O Level spreadsheet: tab IDs, exam dates, access, structure notes.

## Notes
- **`execute_code` sandbox resets between calls** — `svc`/`creds` defined in one call are GONE in the next (`NameError: name 'svc' is not defined`). Don't re-auth inline every call. Write a tiny helper module once (e.g. `/tmp/gs.py` exporting `svc()` + `SID`), then each subsequent call does `import sys; sys.path.insert(0,"/tmp"); from gs import svc,SID; s=svc()`. Clean and reuses the refresh logic.
- **Global bold/non-bold pass — guard section headers.** When asked "make all rows non-bold except headers", a blanket `repeatCell` over `startRowIndex=frozenRowCount..rowCount` also strips bold from **in-body section titles** on doc-style tabs (SCORING LOGIC, RULES, FX). Apply it, then flag that those mid-body headers went non-bold too and offer to restore — don't silently flatten them.
- Token path: `~/.hermes/google_token.json` (full scopes incl. spreadsheets). NOT the friday_backup copy.
- **Tahmeed's English O Levels sheet** (created 2026-07-23): IDs, tab GIDs, exam facts, prep context — see `references/tahmeed-english-olevel-sheet.md`.
- **Canonical sheet ID for TIMBR ops: `1NVaI-jXqfS1z6aMLvNlwJCZoSzVMzP-17to24kKMcDA`** — confirmed in `/home/hermes/.hermes/instagrammer/mac/mac_agent.py` and `instagrammer/engine/enrich_queue.py`. Don't search for it each session.
- To append a column to a tab whose grid is at max columns, grow the grid first: either `appendDimension` (COLUMNS, length N) or bump `gridProperties.columnCount` via `updateSheetProperties`, THEN write — otherwise `Range exceeds grid limits`. **Same trap on ROWS**: appending a long block to a freshly-created small tab (e.g. `rowCount:40`) throws `Range (TAB!A43) exceeds grid limits. Max rows: 41`. Bump `gridProperties.rowCount` to `start+len(block)+slack` via `updateSheetProperties` BEFORE the `values.update`. When appending iteratively across a session, read current `len(values.get(...!A:A))+2` as the start row each time rather than tracking it in your head.
- **Doc-style tabs (SCORING LOGIC / FX / RULES): append new versions, never overwrite.** When Tanzim says \"don't erase anything\" / \"write X below Y\", append the new section under the existing content with a clear banner row (e.g. `═══ v2 (ACTIVE) — v1 above preserved ═══`) and band section headers grey, but use an **amber** background `(0.988,0.91,0.78)` for any block that is BLOCKED / needs-input / a warning, so the distinction is visible at a glance. Detect section-header rows for banding by prefix match (e.g. `t.startswith(\"v2-\")` or a `\"N.0 \"` numbered-phase pattern) rather than hardcoding row indices.
- Visual redesign of doc-style tabs (walls of bullets in col A): rebuild as title banner + italic subtitle + colour-coded section bands + IN/OUT tag chips + white body cards, gridlines off. Don't alter the content — only presentation. Build ONE tab as a prototype, show him the link, get sign-off before rolling across the rest.
- Formatting is idempotent; safe to re-run.

## 3-stage QC after building DB-style tabs ("check everything 3 stages for accuracy")

When Tanzim asks for a thorough/multi-stage accuracy check on populated tabs, run three gates that
**read the data back live from the sheet** (never validate from the in-memory copy you just wrote —
that can't catch a write that didn't land):

1. **Header parity** — pulled header == the reference DB header, exact list compare.
2. **Math integrity** — every computed cell reproduces from its formula (e.g. Level Score = the
   weighted sum; band == the score's bucket). Recompute in Python and diff.
3. **Business rules** — classification value correct, numeric ranges in-bounds (e.g. ratio 0–1),
   level prefix matches the tab (C*/H*/S*), no duplicate exercise names.

Report "NONE — all 3 stages clean" or the exact failing rows. For a larger build, a hub-n-spoke pass
(parallel subagents each attacking from one angle, then synthesise) surfaces structural flaws a single
linear check misses — but cap at `max_concurrent_children` (3) per `subagent` call; split into batches if more.
