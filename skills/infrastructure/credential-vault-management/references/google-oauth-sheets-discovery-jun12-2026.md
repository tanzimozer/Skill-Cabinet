# Google Sheets Discovery & Access Pattern
**Session:** June 12, 2026 (Credential scanning, Sheets access via Drive API)

## Problem

User asked agent to "check the feed" for player questions without specifying which sheet. Agent needed to:
1. Discover available sheets from Google Drive
2. Identify sheets matching keyword filters (names containing "blair", "tweets", "questions", "player")
3. Access sheet content via Google Sheets API

Initial gspread authorization worked, but sheet access failed with 404 errors despite successful Drive API file discovery (permissions or sheet IDs mismatched).

## Solution Pattern

**Discovery & Access Workflow:**

### Step 1: Load & Validate OAuth Token
```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

token_path = os.path.expanduser('~/.hermes/google_token.json')
with open(token_path, 'r') as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)
if creds.expired:
    creds.refresh(Request())
    # Re-save refreshed token
    with open(token_path, 'w') as f:
        json.dump(json.loads(creds.to_json()), f)
```

### Step 2: Search Drive for Sheets by Name Pattern
```python
from googleapiclient.discovery import build

drive_service = build('drive', 'v3', credentials=creds)

search_terms = ["blair", "tweets", "player", "questions"]
for term in search_terms:
    query = f"name contains '{term}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
    results = drive_service.files().list(
        q=query, 
        spaces='drive', 
        pageSize=10, 
        fields='files(id, name)'
    ).execute()
    files = results.get('files', [])
    # Process results...
```

### Step 3: Try gspread Authorization (Primary Path)
```python
import gspread

gc = gspread.authorize(creds)
sh = gc.open_by_key(sheet_id)
data = sh.worksheet(tab_name).get_all_values()
```

### Step 4: Fallback — Direct Sheets API (If gspread Fails)
If gspread encounters 404 or permission issues:
```python
sheets_service = build('sheets', 'v4', credentials=creds)
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range='Sheet1!A:Z'
).execute()
values = result.get('values', [])
```

## Diagnostics Checklist

When sheets are discoverable but inaccessible:

- ✓ OAuth token valid & refreshed (check `creds.token` is not None)
- ✓ Scopes include `https://www.googleapis.com/auth/spreadsheets` (check `creds.scopes`)
- ✓ Sheet ID is correct (copy-paste from Drive search results)
- ✓ User has read permission on sheet (share settings in Google Drive UI)
- ✓ Sheet not in trash (filter: `trashed = false`)
- ✓ Worksheet tab name is exact (case-sensitive)

If still 404 after these checks: **Ask user for direct sheet URL or share permissions link**, because either:
- User doesn't have permission (Drive search is lenient; access is strict)
- Sheet has been moved or deleted since search
- Sheet is owned by another account user has temporary access to

## Implementation Notes

**Token refresh is critical:** Google OAuth tokens expire. Always check `creds.expired` and refresh before using, even if you just loaded the token. This prevents "invalid_grant" errors mid-session.

**Drive search is fast but permissive:** Search will find sheets you have *some* access to, but open/read will fail if permissions don't grant the specific scope (read vs write, etc.). Trust gspread/Sheets API errors over Drive search results for access status.

**Keyword search is fuzzy:** Searching for `name contains 'blair'` finds "Blair 2026", "blair_log", "BLAIR_MAGAZINE_CONTENT", but not sheets where "blair" is only in a tab name or cell content. If sheet not found by name search, ask user.

## When This Pattern Applies

- Agent needs to find a sheet by partial name or keyword
- User said "check [thing]" without providing a direct link
- Multiple sheets with similar names exist (need discovery, not assumption)
- User has shared sheets from multiple Google accounts
- First access after credential refresh

## Related Skills

- `credential-vault-management` — OAuth token storage & refresh
- `gmail-automation` — similar OAuth patterns for Gmail
- `google-workspace` — broader Google API integration

## Pitfalls to Avoid

- ❌ Assume sheet exists without search first (user may misremember name)
- ❌ Use gspread alone without Drive API fallback (gspread errors are less informative)
- ❌ Skip token refresh (expired tokens fail silently mid-operation)
- ❌ Trust Drive search = access (permission ≠ discoverability)
- ❌ Hard-code sheet IDs across sessions (users delete/reorganize)

## Status

✓ Discovered June 12, 2026
✓ Search pattern working (found 3 Blair sheets)
✓ Access issue remains (permission or moved sheets) — awaiting user clarification
