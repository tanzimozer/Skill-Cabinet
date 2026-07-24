---
name: google-sheets
category: productivity
description: Creating, populating, and formatting Google Sheets programmatically via the Sheets API v4 using stored OAuth credentials.
---

# Google Sheets via API

## Auth pattern
Credentials live at `~/.hermes/google_token.json`. Load with `google.oauth2.credentials.Credentials`, refresh if expired, build service with `googleapiclient.discovery.build('sheets', 'v4', credentials=creds)`.

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data.get('token') or token_data.get('access_token'),
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
    scopes=token_data.get('scopes')
)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

service = build('sheets', 'v4', credentials=creds)
```

## Primary spreadsheet
Tanzim's master sheet ID: `1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0`
Existing tabs as of 2026-07: Commands, Jul 03, Jul 04 (x5) — add new tabs, don't overwrite.

## Creating a new tab
```python
result = service.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={"requests": [{"addSheet": {"properties": {"title": "Tab Name", "index": 0}}}]}
).execute()
new_sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
```

## Writing data
```python
service.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range="'Tab Name'!A1",
    valueInputOption='USER_ENTERED',
    body={"values": rows}  # list of lists
).execute()
```

## Formatting (batchUpdate requests)
All formatting goes in a single `batchUpdate` call after data is written. Common patterns:

### Freeze header row
```python
{"updateSheetProperties": {
    "properties": {"sheetId": SID, "gridProperties": {"frozenRowCount": 1}},
    "fields": "gridProperties.frozenRowCount"
}}
```

### Colour a range
```python
{"repeatCell": {
    "range": {"sheetId": SID, "startRowIndex": 0, "endRowIndex": 1},
    "cell": {"userEnteredFormat": {
        "backgroundColor": {"red": 0.13, "green": 0.13, "blue": 0.13},
        "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}
    }},
    "fields": "userEnteredFormat(backgroundColor,textFormat)"
}}
```

### Set column widths
```python
{"updateDimensionProperties": {
    "range": {"sheetId": SID, "dimension": "COLUMNS", "startIndex": i, "endIndex": i+1},
    "properties": {"pixelSize": px},
    "fields": "pixelSize"
}}
```

### Wrap text
```python
{"repeatCell": {
    "range": {"sheetId": SID},
    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
    "fields": "userEnteredFormat.wrapStrategy"
}}
```

### Auto-resize columns
```python
{"autoResizeDimensions": {
    "dimensions": {"sheetId": SID, "dimension": "COLUMNS", "startIndex": 0, "endIndex": N}
}}
```

## Colour palette (house style for section headers)
Use distinct colours per section type — dark backgrounds, white text. Example from English O'Levels sheet:
- Dark blue `(0.18, 0.38, 0.62)` — overview/meta
- Dark green `(0.13, 0.54, 0.33)` — reading/paper 1
- Dark amber `(0.55, 0.27, 0.07)` — writing/paper 2
- Dark purple `(0.33, 0.18, 0.55)` — objectives
- Teal `(0.10, 0.45, 0.55)` — reference/guides
- Dark red `(0.45, 0.10, 0.20)` — glossary/commands
- Slate `(0.20, 0.30, 0.45)` — planning/timelines

## Pitfalls
- Tab names with apostrophes (e.g. `English O'Levels`) must be wrapped in single quotes in range strings: `"'English O\\'Levels'!A1"` — or use the sheet ID in range references to avoid it.
- `new_sheet_id` is NOT the same as the spreadsheet ID. Always capture it from `addSheet` reply for subsequent formatting calls.
- Write data first, format second. You can't format a range that doesn't exist yet.
- `autoResizeDimensions` and explicit `pixelSize` conflict — pick one per column or run auto first then override.

## Support files
- `references/english-olevel-syllabus-breakdown.md` — full syllabus breakdown for Cambridge O Level English Language 1123 (used to build the study sheet)
