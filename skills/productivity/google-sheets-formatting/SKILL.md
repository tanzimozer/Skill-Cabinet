---
name: google-sheets-formatting
description: "Format Google Sheets programmatically — column widths, row heights, colours, borders, checkboxes, frozen rows, alignment. Covers full batchUpdate workflow."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [google-sheets, formatting, spreadsheet, batchUpdate, styling]
    related_skills: []
---

# Google Sheets Formatting

## When to use
Any time you're writing data to a Google Sheet and need it to look clean and readable — not just raw data dumps.

## Auth pattern
**Live token: `~/.hermes/google_token.json`** (scopes incl. spreadsheets + drive; refresh works). Do NOT use `~/friday_backup/google_token.json` — it's dead (`deleted_client: The OAuth client was deleted`), and the EDITH vault's stored google_oauth entry references the same deleted client, so it's stale too. Default to `~/.hermes/google_token.json` for all Sheets/Drive work.

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    td = json.load(f)

creds = Credentials(
    token=td['token'], refresh_token=td['refresh_token'],
    token_uri=td['token_uri'], client_id=td['client_id'],
    client_secret=td['client_secret']
)
sheets = build('sheets', 'v4', credentials=creds)
```

## Token expired / invalid_grant
If you get `invalid_grant`, the token needs a full re-auth — it cannot be refreshed automatically.
Re-auth flow:
1. Get client_id from `~/.hermes/google_client_secret.json` → `installed.client_id`
2. Build auth URL and send directly to user as a clickable link — do NOT route through terminal
3. User opens URL in browser, approves, copies the full redirect URL (localhost:8080 will show an error — that's fine, they just copy the URL)
4. Extract `code=` param from URL, POST to token endpoint:

```python
import requests as req
with open('/home/hermes/.hermes/google_client_secret.json') as f:
    sec = json.load(f).get('web', json.load(open('/home/hermes/.hermes/google_client_secret.json')).get('installed', {}))
resp = req.post('https://oauth2.googleapis.com/token', data={
    'code': CODE,
    'client_id': sec['client_id'],
    'client_secret': sec['client_secret'],
    'redirect_uri': 'http://localhost:8080',
    'grant_type': 'authorization_code'
})
data = resp.json()
with open('/home/hermes/.hermes/google_token.json') as f:
    existing = json.load(f)
existing['token'] = data['access_token']
existing['refresh_token'] = data['refresh_token']
with open('/home/hermes/.hermes/google_token.json', 'w') as f:
    json.dump(existing, f)
```

Auth URL template (send this to user):
```
https://accounts.google.com/o/oauth2/auth?client_id=313611152308-9is3h086p9n4f8d7qabjk8pfkjp80qdq.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8080&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&access_type=offline&prompt=consent
```

**Client ID:** `313611152308-9is3h086p9n4f8d7qabjk8pfkjp80qdq.apps.googleusercontent.com`
**Do NOT send user through terminal `hermes auth google` — that command doesn't exist.**
**Do NOT run `setup.py` without args — it hangs waiting for input.**
**DO give user the direct browser URL — fastest path.**

## Core batchUpdate pattern
All visual formatting goes through `spreadsheets().batchUpdate()`. Build a list of request dicts, fire once.

```python
requests = []
# ... build requests list ...
sheets.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={'requests': requests}
).execute()
```

## Common request types

### repeatCell — apply format to a range
```python
requests.append({'repeatCell': {
    'range': {
        'sheetId': sheet_id,
        'startRowIndex': 0, 'endRowIndex': 1,      # row 1 only (0-indexed)
        'startColumnIndex': 0, 'endColumnIndex': 5  # cols A-E
    },
    'cell': {'userEnteredFormat': {
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.96},
        'textFormat': {'bold': True, 'fontSize': 11},
        'horizontalAlignment': 'LEFT',   # LEFT / CENTER / RIGHT
        'verticalAlignment': 'MIDDLE',
        'wrapStrategy': 'WRAP',
        'padding': {'top': 8, 'bottom': 8, 'left': 10, 'right': 10}
    }},
    'fields': 'userEnteredFormat'
}})
```

### updateDimensionProperties — column widths / row heights
```python
# Column width
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 80},
    'fields': 'pixelSize'
}})
# Row height
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': sheet_id, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 44},
    'fields': 'pixelSize'
}})
```

### updateBorders — cell borders
```python
BORDER = {'style': 'SOLID', 'color': {'red': 0.88, 'green': 0.88, 'blue': 0.89}}
requests.append({'updateBorders': {
    'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 20,
              'startColumnIndex': 0, 'endColumnIndex': 5},
    'top': BORDER, 'bottom': BORDER, 'left': BORDER, 'right': BORDER,
    'innerHorizontal': BORDER, 'innerVertical': BORDER
}})
```

### Freeze header row
```python
requests.append({'updateSheetProperties': {
    'properties': {'sheetId': sheet_id, 'gridProperties': {'frozenRowCount': 1}},
    'fields': 'gridProperties.frozenRowCount'
}})
```

### Checkboxes (boolean validation)
```python
requests.append({'repeatCell': {
    'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'endRowIndex': 51,
              'startColumnIndex': 1, 'endColumnIndex': 2},
    'cell': {'dataValidation': {'condition': {'type': 'BOOLEAN'}}},
    'fields': 'dataValidation'
}})
```
Write `FALSE` (string) as the cell value — it becomes a proper checkbox.

### Add / delete / rename sheets
```python
# Add
{'addSheet': {'properties': {'title': 'New Tab'}}}
# Delete
{'deleteSheet': {'sheetId': sheet_id_int}}
# Rename
{'updateSheetProperties': {'properties': {'sheetId': id, 'title': 'New Name'}, 'fields': 'title'}}
```
**Always re-fetch tab IDs after structural changes** — `sheets.spreadsheets().get()` → iterate `meta['sheets']`.

## Tanzim's preferred sheet style
- Header row: bg `#F2F2F7` (light grey), bold, 44px height, frozen
- Data rows: 40-42px height, wrap text, left-aligned
- Alternating row colours: white / `#F8F8FA`
- Highlight rows: light accent colour (e.g. `#E8F1FB` for blue)
- Borders: `#E2E2E7` solid on all cells — clean grid, never garish
- Column widths: sized to content — don't leave defaults (too narrow or too wide)
- Center-align: numbers, checkboxes, short status fields only
- Left-align: all text content

## Tahmeed Learning Sheet — Confirmed Layout (2026-06-02)
Sheet ID: `19v5x4oScpEPXkjHBWvt97UHtWChki5UGniJvop258bc`

**Tab: AI Learnings** — 5 columns only. Tanzim's explicit requirement: "easy on the eye, not too much information — what are we doing, two links, done or not, how long."
| Col | Label | Width | Align |
|-----|-------|-------|-------|
| A | Est. Time | 90px | Centre |
| B | Done ✅ | 70px | Centre (checkbox) |
| C | Subject | 320px | Left |
| D | Video 1 | 260px | Left |
| E | Video 2 | 260px | Left |
Claude/session rows highlighted `#E8F1FB` (light blue accent).

**Tab: User Profile** — 3 columns:
| Col | Label | Width |
|-----|-------|-------|
| A | # | 50px |
| B | Question | 380px |
| C | Answer | 420px |

## Large-text columns (cookies, tokens, JSON blobs) — CLIP not WRAP
When a column holds long strings (4000+ char cookie exports, session tokens, JSON), **WRAP explodes row height** — one 4k-char cell makes a row hundreds of px tall and wrecks the layout. Use **CLIP** instead: the full value stays in the cell (visible in the formula bar on click), but renders as a single clipped line.

```python
# Cookies/token column -> CLIP, left-aligned, narrow, fixed row height
{'repeatCell': {'range': {'sheetId': tid, 'startRowIndex': 1, 'endRowIndex': 1000,
    'startColumnIndex': col, 'endColumnIndex': col+1},
    'cell': {'userEnteredFormat': {'wrapStrategy': 'CLIP', 'verticalAlignment': 'MIDDLE',
        'horizontalAlignment': 'LEFT'}},
    'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment)'}}
# Pin row heights so a stray WRAP/paste can't balloon them
{'updateDimensionProperties': {'range': {'sheetId': tid, 'dimension': 'ROWS',
    'startIndex': 1, 'endIndex': 1000}, 'properties': {'pixelSize': 24}, 'fields': 'pixelSize'}}
```

**Pre-apply column-wide (rows 2–1000), not just current rows** — so cells a user pastes into LATER inherit the CLIP format. Caveat to tell the user: a full **Ctrl+V** paste carries the clipboard's own formatting and can override CLIP; **Ctrl+Shift+V (paste values-only)** keeps the column's format. If they use plain paste, just re-apply CLIP after each batch.

## Soft-lock (warningOnly protection) — lock layout, still allow typing
When the user says "lock this tab" but people still need to enter data, use a `warningOnly` protected range: editors get a confirm prompt on edits, not a hard block.
```python
{'addProtectedRange': {'protectedRange': {
    'range': {'sheetId': tid},
    'description': 'Layout locked — <column order / format standard>',
    'warningOnly': True}}}
```
To unlock: read `sheet['protectedRanges']`, then `{'deleteProtectedRange': {'protectedRangeId': pid}}` for each. To "re-lock after user changed the format": read current state first, then update the existing protection's `description` rather than stacking a second one.

## Doc-style / visual tabs (section bands, snapshot-friendly)
When a tab is prose/plan content (a wall of bullets in column A) and the user wants it "more visual / easy to snapshot," rebuild it with merged colour-banded section headers, tag chips, white content cards, and gridlines off. Full reusable builder + colour palette: see **references/doc-style-visual-tab.md**.

## Pitfalls
- **Get sheet IDs before formatting** — you need integer `sheetId`, not tab name
- **Grid column/row caps** — a new tab created with `gridProperties.columnCount: 4` will throw `Range exceeds grid limits. Max columns: 4` the moment you write to column E. **Expand the grid first**: `{'updateSheetProperties': {'properties': {'sheetId': tid, 'gridProperties': {'columnCount': N}}, 'fields': 'gridProperties.columnCount'}}`. Same for `rowCount`. Always check `meta['sheets'][i]['properties']['gridProperties']` before appending columns.
- **Clear before rewriting** — `values().clear()` first avoids stale data mixing. For a full visual rebuild, also `unmergeCells` over the range before re-merging.
- **`fields` param is mandatory** — omitting it silently does nothing
- **Colors are 0.0–1.0 floats**, not 0–255 ints
- **Don't batch too many requests** — Google has a request size limit; split into 50-100 at a time for large sheets
- **`FALSE` for checkboxes must be written as a string**, not Python `False`
- **Hide gridlines for doc-style tabs** — `{'updateSheetProperties': {'properties': {'sheetId': tid, 'gridProperties': {'hideGridlines': True}}, 'fields': 'gridProperties.hideGridlines'}}`
