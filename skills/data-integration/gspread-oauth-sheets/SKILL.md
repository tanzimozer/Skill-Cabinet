---
name: gspread-oauth-sheets
type: integration
summary: Google Sheets API operations via gspread (OAuth, keyless credentials). Tab management, data sync, batch append.
description: >-
  gspread + Google OAuth provides keyless, user-authenticated access to Google Sheets.
  No paid API key, no service account — the user's Google login is cached as an OAuth token after first-run sign-in.
  Handles tab creation, data read/write, batch append, and dedup patterns for Job Hammer crawl outputs.
---

## Installation
```bash
pip install gspread google-auth google-auth-oauthlib
```

## One-Time OAuth Setup
1. Go to console.cloud.google.com → create/select project.
2. **APIs & Services → Library** → enable **Google Sheets API** + **Google Drive API**.
3. **OAuth consent screen** → External → app name + test user email (e.g., tanzim.seattle@gmail.com).
4. **Credentials → Create OAuth client ID** → Desktop app → Download JSON.
5. Save to `~/.config/gspread/credentials.json` (create folder if needed).
6. First run: `gspread.oauth()` opens browser, user signs in, token cached to `~/.config/gspread/authorized_user.json`.

After first run, all subsequent calls are silent — no prompt.

## Code Patterns

### Load credentials (after first-time setup)

**Option A: Standard setup (first-run interactive OAuth)**
```python
from google.oauth2.credentials import Credentials
import gspread
import json
from pathlib import Path

creds_path = Path.home() / ".config" / "gspread" / "authorized_user.json"

if creds_path.exists():
    with open(creds_path) as f:
        cred_data = json.load(f)
    creds = Credentials.from_authorized_user_info(cred_data)
    gc = gspread.authorize(creds)
else:
    # First run: browser sign-in
    gc = gspread.oauth()
```

**Option B: Direct credentials dict (e.g., stored in ~/.hermes/google_oauth_full.json)**
When OAuth token is stored as a dict with keys `access_token`, `refresh_token`, `client_id`, `client_secret`, and `scopes`:
```python
from google.oauth2.credentials import Credentials
import gspread
import json

with open('/home/hermes/.hermes/google_oauth_full.json', 'r') as f:
    creds_data = json.load(f)

creds = Credentials(
    token=creds_data['access_token'],
    refresh_token=creds_data['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id=creds_data['client_id'],
    client_secret=creds_data['client_secret'],
    scopes=creds_data['scopes'].split() if isinstance(creds_data['scopes'], str) else creds_data['scopes']
)

gc = gspread.authorize(creds)
```

Both methods work; Option B is useful when token is already persisted elsewhere or managed externally.

### Open sheet + list tabs
```python
sheet_id = "12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0"
sh = gc.open_by_key(sheet_id)

tabs = {ws.title: ws for ws in sh.worksheets()}
for title in sorted(tabs.keys()):
    print(f"  - {title}")
```

### Create a tab
```python
if "master_tab" not in tabs:
    master_ws = sh.add_worksheet("master_tab", rows=2000, cols=20)
else:
    master_ws = tabs["master_tab"]
```

### Read all data from a tab
```python
data = master_ws.get_all_values()  # Returns list of lists
print(f"{len(data)} rows, {len(data[0]) if data else 0} cols")
```

### Scanning & Search (Multi-Sheet or Single Sheet)
**Find a company / keyword across all worksheets or within a tab with full-text search:**
```python
# Scan all worksheets for target company
SHEET_ID = "abc123"
TARGETS = ['Company A', 'Company B']

sheet = gc.open_by_key(SHEET_ID)
worksheets = sheet.worksheets()

results = {t: None for t in TARGETS}

for ws in worksheets:
    try:
        values = ws.get_all_values()
        if not values:
            continue
        
        for row_idx, row in enumerate(values, start=1):
            row_text = ' '.join(str(c) for c in row).lower()
            
            for target in TARGETS:
                if target.lower() in row_text and results[target] is None:
                    results[target] = {
                        'sheet': ws.title,
                        'row': row_idx,
                        'data': row
                    }
                    print(f"Found '{target}' in {ws.title}!{row_idx}")
    except:
        continue

# Extract columnar data from matched rows
for target, match in results.items():
    if match:
        row = match['data']
        print(f"{target}: {row[1]} | {row[2]} | {row[3]}")  # cols 2-4
```

→ See `references/sheet-scanning-pattern-jun2026.md` for full multi-sheet scan with refinement phases.

### Clear + append rows
```python
master_ws.clear()
master_ws.append_rows(data)  # data = list of lists
```

## Job Hammer Sheet Architecture (Jun 2026)
**Sheet ID:** `12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`

**Tab structure:**
- **master_tab** — unified archive of all jobs ever crawled (all sources, all time)
- **Dated tabs** (e.g., `Jun 03`) — jobs from each crawl run; dedup applied before append to master

**Columns (A→J):**
`URL | COMPANY | TITLE | SCORE | LOCATION | REMOTE | SALARY_MIN | SALARY_MAX | POSTED_DATE | SOURCE | JD`
(JD column added commit 806b523, Jun 3)

**Dedup logic:**
- Jobs already in MASTER (matched by URL) are dropped from today's tab
- New jobs append to MASTER only after dedup pass
- Each new job gets its own dated tab + sync copy to master_tab

## Raw REST approach (no gspread — token at ~/.hermes/google_token.json)

When gspread isn't installed or you want zero dependencies, hit the Google APIs directly with `urllib`. This is the approach that works reliably in execute_code. The active token lives at `~/.hermes/google_token.json` (keys: token, refresh_token, client_id, client_secret, scopes). Scopes already cover Sheets, Drive, Docs, Gmail.

```python
import json, urllib.request, urllib.parse, os
TOKEN_PATH=os.path.expanduser('~/.hermes/google_token.json')

def refresh():
    with open(TOKEN_PATH) as f: tok=json.load(f)
    data=urllib.parse.urlencode({'client_id':tok['client_id'],'client_secret':tok['client_secret'],
        'refresh_token':tok['refresh_token'],'grant_type':'refresh_token'}).encode()
    r=json.loads(urllib.request.urlopen(urllib.request.Request(
        'https://oauth2.googleapis.com/token',data=data,method='POST')).read())
    tok['token']=r['access_token']
    with open(TOKEN_PATH,'w') as f: json.dump(tok,f)
    return r['access_token']

T=refresh()
def api(url,method='GET',body=None):
    d=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(url,data=d,method=method,
        headers={'Authorization':f'Bearer {T}','Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req).read())
```

Common calls:
- List spreadsheets: `GET https://www.googleapis.com/drive/v3/files?<urlencoded params>`
- Read range: `GET https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/{quoted_range}`
- Write range: `PUT .../values/{quoted_range}?valueInputOption=RAW` body `{'values':[[...]]}`
- Append row: `POST .../values/{quoted_range}:append?valueInputOption=RAW` body `{'values':[[...]]}`
- Create sheet: `POST https://sheets.googleapis.com/v4/spreadsheets` body `{'properties':{'title':...}}`
- Format/freeze: `POST .../{sid}:batchUpdate` with repeatCell / updateSheetProperties requests
- Make a Drive file public (anyone-with-link reader): `POST https://www.googleapis.com/drive/v3/files/{id}/permissions` body `{'role':'reader','type':'anyone'}`
- Read a Doc as text: `GET https://docs.googleapis.com/v1/documents/{id}` then walk `body.content[].paragraph.elements[].textRun.content`

→ See `references/google-rest-api-jun2026.md` for full create-sheet-with-formatting and create-doc-with-headings recipes.

## Two quirks that WILL bite (encode these)

1. **URL-encode the WHOLE query, never hand-concatenate.** A literal space in a Drive `orderBy=modifiedTime desc` or an unescaped `q=` value raises `http.client.InvalidURL: URL can't contain control characters`. Always build params with `urllib.parse.urlencode({...})` and ranges with `urllib.parse.quote("Sheet1!A1:K10")`. This is the single most common failure.

2. **The access token expires mid-session (~1h).** A long multi-step task (read → process → write) will throw `HTTP Error 401: Unauthorized` partway through even though the first calls succeeded. Fix: call `refresh()` again and retry the failed call — do NOT assume the token is dead for the session. For any task spanning several minutes, refresh at the start of each distinct execute_code block rather than reusing a stale `T` from a prior block.

## Known Issues & Workarounds

### Credentials file not found (first run)
User must complete OAuth setup at console.cloud.google.com. gspread.oauth() prompts for sign-in.

### AttributeError: Credentials.from_authorized_user_file
Use `Credentials.from_authorized_user_info(dict, scopes=...)` instead. Load JSON first, pass as dict.

### Rate limiting on append_rows()
Batch into chunks of 500–1000 rows. gspread handles backoff.

### Eventual consistency after write
Wait 1–2s after clear() + append_rows() before reading. Google's consistency is delayed.

### gc.copy(..., copy_permissions=True) → 403 transferOwnership
Duplicating a sheet owned by someone else (e.g. a teammate's source-of-truth file) with `copy_permissions=True` throws `APIError [403]: The transferOwnership parameter must be enabled when the permission role is 'owner'` — gspread tries to copy the original owner's permission verbatim. Fix: call `gc.copy(SOURCE_ID, title=..., copy_permissions=False)`, then share explicitly with `sh.share(None, perm_type='anyone', role='writer')` (or 'reader'). Make your own working drafts rather than copying foreign ownership.

## Integration: Job Hammer Crawl → Sheet
1. Crawl produces CSV output (Stage_1_Crawl/output/jobs.csv).
2. sync_to_sheet.py reads CSV, dedupes against MASTER (URL match), appends net-new to dated tab.
3. Dated tab (e.g., Jun 03) + MASTER both updated atomically.
4. Stage 2 handoff: JD packets include metadata (top_wins, score) for resume tailoring.
