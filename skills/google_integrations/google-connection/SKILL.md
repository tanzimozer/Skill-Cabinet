---
name: google-connection
description: Authenticate and manage persistent Google OAuth connections for Gmail, Sheets, Drive, Docs, and Calendar APIs
tags:
  - google
  - oauth
  - gmail
  - sheets
  - drive
  - credentials
  - automation
---

# Google Connection — OAuth Authentication & Token Management

## Overview
Persistent Google OAuth 2.0 authentication for Tanzim's Gmail, Sheets, Drive, Docs, and Calendar access. Eliminates repeated re-authentication by managing token lifecycle (request → exchange → refresh → store).

## Current Active Credentials (June 17, 2026)

**Project:** friday-499707
**Client Type:** Desktop Application
**Client ID:** 990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com
**Client Secret:** <GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>
**Redirect URI:** http://localhost
**Email Account:** tanzim.seattle@gmail.com

**Scopes (Active — MUST use exact URLs):**
- `https://www.googleapis.com/auth/gmail.readonly` — Read Gmail only
- `https://www.googleapis.com/auth/gmail.modify` — Read, modify, delete Gmail messages (required for deletes)
- `https://www.googleapis.com/auth/spreadsheets` — Read/write Google Sheets
- `https://www.googleapis.com/auth/drive.readonly` — Read Google Drive
- `https://www.googleapis.com/auth/calendar` — Read/write Calendar

**CRITICAL:** Scope names must be exact full URLs. Google OAuth does not recognize shortcuts or abbreviated forms. See `references/oauth-scope-reference.md` for full list and validation rules.

**Token Location:** `~/.hermes/google_token.json`
**Status:** ✓ Live (June 17, 2026, 07:28 UTC)

---

## OAuth Flow (5 Steps)

### 1. Generate Auth Link
```python
import urllib.parse

client_id = "990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com"
redirect_uri = "http://localhost"
scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar'
]

params = {
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'response_type': 'code',
    'scope': ' '.join(scopes),
    'access_type': 'offline',
    'prompt': 'consent'
}

auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
```

### 2. User Approves
User clicks auth link, signs in with tanzim.seattle@gmail.com, approves scopes.

### 3. Copy Authorization Code
Google redirects to `http://localhost/?code=AUTHORIZATION_CODE`. User copies the code parameter.

### 4. Exchange Code for Token
```python
import requests
import json
import os

client_id = "990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>"
code = "USER_AUTHORIZATION_CODE"
redirect_uri = "http://localhost"

token_url = "https://oauth2.googleapis.com/token"
payload = {
    'code': code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}

response = requests.post(token_url, data=payload)
token_data = response.json()

# Save token
token_file = os.path.expanduser('~/.hermes/google_token.json')
with open(token_file, 'w') as f:
    json.dump(token_data, f, indent=2)
```

### 5. Use Token
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os

token_file = os.path.expanduser('~/.hermes/google_token.json')
with open(token_file, 'r') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['access_token'],
    refresh_token=token_data.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id='990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com',
    client_secret='<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>'
)

gmail_service = build('gmail', 'v1', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)
calendar_service = build('calendar', 'v3', credentials=creds)
```

---

## Common Operations

### Scan Gmail for Unread Emails
```python
service = build('gmail', 'v1', credentials=creds)
query = 'is:unread "thank you for applying"'
results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
messages = results.get('messages', [])
```

### Read Google Sheets
```python
sheets_service = build('sheets', 'v4', credentials=creds)
spreadsheet_id = "YOUR_SHEET_ID"
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range="Sheet1!A1:Z100"
).execute()
values = result.get('values', [])
```

### List Google Drive Files
```python
drive_service = build('drive', 'v3', credentials=creds)
results = drive_service.files().list(pageSize=10, fields='files(id, name)').execute()
files = results.get('files', [])
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Error 403: insufficient scopes` on delete | You requested `gmail.readonly` but need `gmail.modify`. Must re-authenticate with new scopes. See `references/oauth-troubleshooting.md`. |
| `Error 400: invalid_scope` during auth | Scope URL is malformed or not recognized. Check exact URL spelling against Google docs. Never use abbreviations like `gmail` or `drive`. |
| `invalid_grant` when exchanging code | Authorization code was already used or has expired (30 min max). Each code is single-use. Get a fresh code and retry immediately. |
| Token file has `error` key instead of `access_token` | Token exchange failed. File contains error response, not a valid token. Delete file and re-authenticate. |
| Stale token being used after re-auth | Python client may cache the old token object. **Delete the token file**, save the new one, **force a fresh file read** in your script. |
| Unverified app warning at login | App is in testing mode. Add user email to Google Cloud Console → OAuth consent screen → Test users. User must be added as a tester. |
| `deleted_client` error on token refresh | The token file has a **stale/dead `client_id`+`client_secret`** stapled to a **still-valid `refresh_token`**. Do NOT re-auth. Fix: copy the working client_id/client_secret from `~/.hermes/GOOGLE_OAUTH_ACTIVE.json` (the `990922176945...` client) into `~/.hermes/google_token.json`, then refresh. The refresh token survives a client swap as long as it was issued by the new client. Verified June 17 2026. |
| Token refresh fails with 401 | Refresh token was revoked or is invalid. Re-authenticate from scratch (OAuth flow step 1). |
| Rate limiting (429) | Gmail API: 300 req/min. Add exponential backoff; see `references/rate-limiting.md`. |
| Redirect URI mismatch | Must match exactly what's registered in Google Cloud Console credentials. Default: `http://localhost`. |

See `references/oauth-troubleshooting.md` for detailed error transcripts and recovery steps.
See `references/oauth-auth-flow-pitfalls.md` for common gotchas (invalid_grant, access_denied, scope mismatch) encountered during OAuth setup.

---

## When to Re-authenticate

- Token file corrupted or deleted
- **Scopes need expansion** (e.g., from `gmail.readonly` to `gmail.modify`) — always requires fresh auth
- User revokes authorization
- Token refresh fails 3+ times
- Authorization code was already used or has expired

**Important:** Each authorization code is single-use and expires in ~30 minutes. If you get `invalid_grant`, the code has been consumed or timed out — generate a new one.

---

## Security

- Client secret stored only in skill/hindsight, never in git
- Token file (`~/.hermes/google_token.json`) is sensitive; keep secure
- Minimal scopes: read-only for Gmail/Drive, read-write for Sheets/Calendar
- Account: tanzim.seattle@gmail.com (production, not sandbox)