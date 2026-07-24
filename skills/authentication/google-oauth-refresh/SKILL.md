---
name: google-oauth-refresh
description: Refresh expired Google OAuth tokens for Sheets/Drive/Gmail access
category: authentication
---

## Credential Storage (June 2026 Update — Plaintext Vault Model)

**As of June 9, 2026:** Tanzim uses plaintext credential storage (no encrypted vaults). Credentials are stored in **two places for transparency + backup:**

1. **Primary (Code-accessible):** `~/.hermes/vault.json` — plaintext JSON with all credentials (Google OAuth, GitHub PAT, iCloud, Webflow, Wix, Instagram, Canva, Anthropic, Hindsight). Load this in Python scripts.
2. **Human-visible backup:** `~/Desktop/CREDENTIALS_MASTER.md` — running log on desktop with full credential values, expiry dates, status, and next steps. Updated after every credential generation or rotation.

**Never reference EDITH vault** — it was deleted June 9, 2026. If you encounter references to encrypted 3-factor vaults in older skills, ignore them.

**Load priority (new):** `~/.hermes/vault.json` → check for `google` key → load both `client_id`, `client_secret`, `refresh_token` from there.

**Structure in vault.json (current):**
```json
{
  "google": {
    "client_id": "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com",
    "client_secret": "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>",
    "refresh_token": "<REDACTED_OAUTH_TOKEN>",
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": ["gmail.modify", "gmail.readonly", "gmail.send", "calendar", "drive", "spreadsheets", "documents"],
    "created": "2026-06-09"
  }
}
```

**Separate file:** `~/.hermes/google_token.json` stores the *current* access token (refreshable token). Refresh it whenever it expires. Don't worry about keeping desktop file in sync — the code-accessible vault is authoritative.

---

**You run on the VM. The user is on their Mac. Don't send commands to the user's Mac.**

When a Google token expires:
1. **Refresh it yourself on the VM** (you have the refresh token)
2. **Don't walk the user through terminal commands** — they're on a different machine
3. **Don't overcomplicate** — if you have a refresh token, use it. Full re-auth is rare.

## Account Identity — Tanzim

**Primary Gmail account:** `tanzim.seattle@gmail.com` (professional/job search). Use this account for all Gmail API calls unless explicitly directed otherwise. Do not guess or ask — this is the canonical account.

## Loading Credentials from Plaintext Vault

**When you need Google OAuth credentials (any scope), load from plaintext vault:**

```python
import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load plaintext vault
vault_path = os.path.expanduser('~/.hermes/vault.json')
with open(vault_path, 'r') as f:
    vault_data = json.load(f)

oauth_config = vault_data['google']

# Build credentials object
creds = Credentials(
    token=oauth_config.get('access_token'),  # may not exist; refresh first
    refresh_token=oauth_config['refresh_token'],
    token_uri=oauth_config['token_uri'],
    client_id=oauth_config['client_id'],
    client_secret=oauth_config['client_secret'],
    scopes=oauth_config.get('scopes', [])
)

# If token is expired or missing, refresh it first
from google.auth.transport.requests import Request
try:
    if not creds.valid:
        creds.refresh(Request())
except Exception as e:
    if 'unauthorized_client' in str(e).lower():
        print("❌ Refresh token revoked. Need full re-auth.")
    else:
        print(f"⚠️ Refresh failed: {e}")

# Now use for Sheets, Drive, Gmail, etc.
service = build('sheets', 'v4', credentials=creds)
result = service.spreadsheets().get(spreadsheetId='...').execute()
```

**Key insight:** Plaintext vault has full refresh token; access token in `~/.hermes/google_token.json` gets rotated hourly. Always refresh before API calls if unsure about token age.

---

## Steps (General Token Management)

**CRITICAL: Token file is always at `~/.hermes/google_token.json` — check there first.**

1. **Check if refresh token exists:**
```bash
cat ~/.hermes/google_token.json | grep refresh_token
```

2. **If refresh token exists, refresh it yourself — use Option B (raw HTTP) for speed and clarity:**

**Option B: Raw HTTP (no google-auth needed — works in cron jobs, most reliable)**
```python
import requests
import json
from datetime import datetime, timedelta

with open('/home/hermes/.hermes/google_token.json', 'r') as f:
    token_data = json.load(f)

resp = requests.post(
    token_data['token_uri'],
    data={
        "client_id": token_data["client_id"],
        "client_secret": token_data["client_secret"],
        "refresh_token": token_data["refresh_token"],
        "grant_type": "refresh_token"
    }
)

if resp.status_code == 200:
    new_data = resp.json()
    # Merge new access token into existing token file (keep scopes, refresh_token, etc)
    token_data['token'] = new_data['access_token']
    token_data['expiry'] = (datetime.utcnow() + timedelta(seconds=new_data.get('expires_in', 3600))).isoformat() + 'Z'
    
    with open('/home/hermes/.hermes/google_token.json', 'w') as f:
        json.dump(token_data, f, indent=2)
    print("✅ Token refreshed.")
else:
    print(f"❌ Refresh failed: {resp.status_code} — {resp.text}")
```

**Option A: Using google-auth library (if installed — slower, adds dependency)**
```bash
cd ~/.hermes && python3 << 'EOF'
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

with open('google_token.json', 'r') as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)
creds.refresh(Request())

token_data['token'] = creds.token
token_data['expiry'] = creds.expiry.isoformat() + 'Z'

with open('google_token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print("✅ Token refreshed.")
EOF
```

**Prefer Option B in production** — simpler, fewer dependencies, works in cron and background jobs without google-auth library installed.

3. **If no refresh token, need full re-auth:**
Only then ask user to run OAuth flow. Use `google_client_secret.json` (not `credentials.json`):
```bash
cd ~/.hermes && python3 << 'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
import json

flow = InstalledAppFlow.from_client_secrets_file(
    'google_client_secret.json',
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive',
     'https://www.googleapis.com/auth/gmail.modify'])

creds = flow.run_local_server(port=0)

token_data = {
    'token': creds.token,
    'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri,
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'scopes': creds.scopes,
    'expiry': creds.expiry.isoformat() + 'Z'
}

with open('google_token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print("✅ New token saved.")
EOF
```

## Handling Token File Errors — See references/

**See `references/token-refresh-malformed-scope-jun14-2026.md`** for the fix when token file is missing `access_token` or google-auth library refuses to refresh with `invalid_scope` errors. Includes raw HTTP refresh pattern that works even when the library fails.

## Use `~/.hermes/google_token.json` ONLY — ignore the backup token

There are several `*_token.json` files scattered on the VM. **`~/.hermes/google_token.json` is the live one** (scopes: calendar, documents, gmail.*, spreadsheets, contacts.readonly, drive — refreshes clean). Go straight to it.

**Do NOT use `~/friday_backup/google_token.json`** — its OAuth client was deleted; refreshing it throws `RefreshError: ('deleted_client: The OAuth client was deleted.')`. It looks valid (has a refresh_token, sensible scopes) but is dead. Same goes for any stray `google_oauth_full.json` / `friday_backup/google_client_secret.json` — don't reach for backups, they cost a wasted round-trip.

If a refresh ever throws `deleted_client`, that's a wrong/dead token FILE (not a revoked token) — switch files to `~/.hermes/google_token.json`, don't kick off a re-auth flow.

## When the refresh token itself is stale (400 on refresh)

If the refresh request returns HTTP 400, the refresh token has been revoked (e.g. user re-authed elsewhere, scope changed, or Google revoked it). Full re-auth is required. Use the OOB flow — it doesn't need a local server on the VM and works even when you can't open a browser:

```python
import json, urllib.request, urllib.parse

with open("/home/hermes/.hermes/google_client_secret.json") as f:
    client_data = json.load(f)
creds = client_data.get("installed", client_data.get("web", {}))

params = {
    "client_id": creds["client_id"],
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "response_type": "code",
    "scope": "https://mail.google.com/",  # adjust scope as needed
    "access_type": "offline",
    "prompt": "consent"
}
url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
print(url)
```

Send this URL to the user. They open it in their browser, sign in, copy the code shown on screen, and paste it back. Then exchange it:

```python
auth_code = "<paste from user>"
data = urllib.parse.urlencode({
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "code": auth_code,
    "grant_type": "authorization_code",
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    token = json.loads(r.read())
# token["access_token"] and token["refresh_token"] are both fresh — save them
```

This avoids asking the user to run anything in their terminal, which is cleaner and always works.

## Google Sheets API — Writing to Tabs with `/` in Name

**See `references/sheets-create-and-format-tab.md`** for the full recipe: create a tab (addSheet), write rows, format a header (bold/fill/freeze), widen columns, and apply wrap + vertical-middle + horizontal-center across the WHOLE tab via `repeatCell` with a bare `{"sheetId": id}` range. Also covers renaming the file vs. a tab, and sharing with a user.

Tab names like `05/27` require special handling:

**Reading** works with `05%2F27!A1:M300` in the URL path — URL-encode the slash.

**Writing** — `PUT /values/{range}` returns 404 for these tab names regardless of encoding. Use `POST /values:batchUpdate` instead:

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

Note: the `range` in the JSON body uses single quotes around the sheet name (`'05/27'!A1`), not URL encoding. The URL path is just `.../values:batchUpdate` — no range in the URL.

**Creating a new tab** with `addSheet` batchUpdate works fine regardless of tab name — the slash causes no issues there.

**Merging tabs**: read both with GET, combine Python-side (header from tab1 + data rows from both), write combined to tab1 with batchUpdate, then delete tab2 with `deleteSheet` batchUpdate. Get the numeric `sheetId` from `spreadsheets.get` first.

## Pitfalls

**See `references/scope-mismatch-debug-jun2026.md` for the full debug pattern when google-auth library throws `invalid_scope` errors on refresh. Includes immediate workaround (raw HTTP refresh) and long-term fix (Consent Screen correction + full re-auth).**

- **Never delete on API error in bulk operations.** If a vision or OCR call fails, treat it as "keep" — not "delete". One silent 401 loop deleted 100 files in a session; they had to be restored from trash. Pattern: `has_pii = answer.upper().startswith('YES') if not answer.startswith('ERROR') else True`.
- **Plaintext vault is now the source of truth.** Do not reference EDITH (encrypted) vault — it was deleted June 9, 2026. Older skills mentioning EDITH are outdated. All credentials are in `~/.hermes/vault.json` as plaintext.
- **Refresh token revocation (400 error)** — If the refresh request returns HTTP 400, the refresh token has been revoked (e.g., user re-authed elsewhere, scope changed, or Google revoked it). Full re-auth is required. Use the OOB flow (see "When the refresh token itself is stale" section below).
- **Load plaintext vault FIRST** — `~/.hermes/vault.json` has the current full credentials and refresh token. Desktop file (`~/Desktop/CREDENTIALS_MASTER.md`) is backup/reference only.
- **Google Calendar API version** — use `v3`, NOT `v4`. `v4` does not exist and will throw `UnknownApiNameOrVersion`. Correct: `build('calendar', 'v3', credentials=creds)`.
- **Google Calendar API may not be enabled in the GCP project** — even with valid credentials, Calendar calls return HTTP 403 `accessNotConfigured` if the Calendar API hasn't been enabled in the GCP project. Fix: visit `https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview?project=<project_id>` and enable it. Project ID is in the 403 error message.
- **VM vs user's Mac confusion is the #1 failure mode** — You're on the VM; they're on their Mac. Never send them VM paths or commands meant for your environment. If re-auth is needed, generate the URL from the VM and have them just click it and paste back a code.
- **Refresh first, re-auth only if needed** — HTTP 400 on refresh = stale refresh token = full OOB flow below.
- **File is `google_client_secret.json`, not `credentials.json`** — wrong filename = FileNotFoundError.
- **Token format is JSON, not pickle** — legacy code may reference `.pickle`, ignore it.
- **`google_client_secret.json` lives on the VM, not the user's Mac** — don't tell them to `cd ~/.hermes` on their machine; the file isn't there.

## Calendar API Enablement

See `references/calendar-api-enablement.md` for the pattern: OAuth scopes and GCP API enablement are independent. If Calendar calls return 403 `accessNotConfigured`, the GCP project has the API disabled — flip it on in the Console, then refresh the token.

## Pitfalls

See `references/drive-image-vision-scan.md` for the full pattern on scanning Drive folders for specific image types using AI vision.

See `references/drive-image-categorization.md` for sorting images into category folders by content type using vision AI.

Key points:

**Progressive refinement workflow (when user says "I know there are more"):**
1. **OCR gating** — fast, cheap, misses ~50% of real matches
2. **Full vision scan** — catches most, ~2-3s per image
3. **Deep reasoning** — inclusive matching, catches edge cases but also false positives
4. **Pattern scan** — sample images for categorization, find stragglers missed by all above

**Key insight:** When user insists there are more matches, they're usually right. No single pass catches everything; progressive refinement beats any single approach.

**False positive watch:** Deep reasoning with "be inclusive" will flag Zoom calls, phone call logs, and social media profiles as "contact lists" because they have "names in a grid." Verify matches before bulk operations.

- Deploy 4 parallel agents for 4 folders simultaneously
- Cross-match verification: re-extract from images and compare against destination

## PII Contact Image Filtering

See `references/pii-filter-criteria.md` for the standard filter rule: images must have **Name + Email + Phone** for all contacts to qualify. Phone call logs, Zoom screenshots, and social profiles don't qualify — they're missing at least one field.

## Gmail Search Patterns

See `references/gmail-interview-search-patterns.md` for a full sequence to hunt confirmed interviews/appointments across inbox, trash, spam, and calendar invites — including the key finding that calendar booking links often produce no inbound confirmation email.

See `references/gmail-inbox-triage.md` for the comprehensive inbox analysis pattern that prioritizes emails by action urgency (HIGH PRIORITY → NEEDS ACTION → SPAM RESCUE → LOW PRIORITY → EXPIRED).

## Anthropic API — OAuth token auth
## Google Drive — Upload file and share publicly

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

with open("/home/hermes/.hermes/google_token.json") as f:
    t = json.load(f)
creds = Credentials(token=t["token"], refresh_token=t["refresh_token"],
    token_uri=t["token_uri"], client_id=t["client_id"],
    client_secret=t["client_secret"], scopes=t["scopes"])

service = build("drive", "v3", credentials=creds)
meta = {"name": "filename.html", "mimeType": "text/html"}
media = MediaFileUpload("/local/path/file.html", mimetype="text/html", resumable=False)
file = service.files().create(body=meta, media_body=media, fields="id").execute()
fid = file["id"]
service.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"}).execute()
print(f"https://drive.google.com/file/d/{fid}/view?usp=sharing")
```

**mimetype matters** — use correct MIME for the file type or Drive will mis-identify it.

**For PDF upload + share specifically:**
```python
# After obtaining creds and service (see above)
pdf_path = os.path.expanduser('~/path/to/file.pdf')
file_metadata = {'name': 'file_name.pdf', 'mimeType': 'application/pdf'}
media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)

file = service.files().create(
    body=file_metadata, 
    media_body=media, 
    fields='id, webViewLink'
).execute()

file_id = file.get('id')
web_link = file.get('webViewLink')

# Make publicly shareable
service.permissions().create(
    fileId=file_id,
    body={'role': 'reader', 'type': 'anyone'},
    fields='id'
).execute()

print(f"✓ Shared: {web_link}")
```

**Troubleshooting:** If upload fails with token error, check EDITH Vault first (see "Loading Credentials from EDITH Vault" above). Fallback token in `google_oauth_full.json` may lack Drive scope.

## Google Drive — Trash / Delete a file

To move a file to Drive trash, use **PATCH** with `trashed: true` in the body. Do NOT use `POST .../trash` — that endpoint returns 404.

```python
import json, urllib.request

def trash_file(file_id, access_token):
    data = json.dumps({'trashed': True}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}',
        data=data,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        method='PATCH'
    )
    urllib.request.urlopen(req)  # raises on error
```

To look up a file's ID by name within a folder before trashing:

```python
def get_file_id(name, folder_id, access_token):
    q = urllib.parse.quote(f"name = '{name}' and '{folder_id}' in parents and trashed = false")
    url = f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=5'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    result = json.loads(urllib.request.urlopen(req).read())
    files = result.get('files', [])
    return files[0]['id'] if files else None
```

Add a `time.sleep(0.2)` between batch deletes to avoid rate-limiting. See `references/drive-bulk-operations.md` for a full pattern including PII folder filtering.

## Google Drive — Upload file and share publicly

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

with open("/home/hermes/.hermes/google_token.json") as f:
    t = json.load(f)
creds = Credentials(token=t["token"], refresh_token=t["refresh_token"],
    token_uri=t["token_uri"], client_id=t["client_id"],
    client_secret=t["client_secret"], scopes=t["scopes"])

service = build("drive", "v3", credentials=creds)
meta = {"name": "filename.html", "mimeType": "text/html"}
media = MediaFileUpload("/local/path/file.html", mimetype="text/html", resumable=False)
file = service.files().create(body=meta, media_body=media, fields="id").execute()
fid = file["id"]
service.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"}).execute()
print(f"https://drive.google.com/file/d/{fid}/view?usp=sharing")
```

**mimetype matters** — use correct MIME for the file type or Drive will mis-identify it.

## Google Sheets — Finding credentials/tokens

When Tanzim says "check the Google Sheet for X token":
1. List all sheets: `service.files().list(q="mimeType='application/vnd.google-apps.spreadsheet'", fields="files(id,name)").execute()`
2. Most likely candidates for credentials: **"Software and API"** sheet and **"Friday — SOS Recovery Sheet"** (has an "API Credentials" tab).
3. **Credentials sheet** (full name: "Credentials"): `1QtHeLtYqd21fGWY0FwRqxGgodYgj-rXnM7mXT9MzzLw` — Tanzim's central credential tracking. Check this first for status and current locations.
4. **SOS Recovery Sheet** ID: `1Zjp7OyHISLXr-uYMJBBc6SRPFqud9BShDGTIe-d9ZOw` — tabs include: Overview, Hermes Server, API Credentials, Google OAuth, WhatsApp Session, Active Projects, Key Contacts, Cron Jobs.
5. GitHub token for `tanzimozer` account is NOT stored in any sheet as of May 2026 — memory records it as active ("Friday-Hermes" token) but it was never persisted to disk. Ask Tanzim to paste it fresh.
6. **Canva credentials** are in `~/.hermes/.canva_credentials` (JSON), NOT in the SOS sheet. If the Canva refresh token is revoked (`invalid_grant`), see the `canva-integration` skill for the full re-auth flow. After any Canva re-auth, update both the Software & API sheet AND the SOS Recovery Sheet — Canva was missing from the SOS sheet as of June 2026.

## Success criteria

- `google_token.json` has fresh `expiry` timestamp (future date)
- Google API calls return 200, not 401/403
