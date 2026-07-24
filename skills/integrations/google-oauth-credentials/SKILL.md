---
name: google-oauth-credentials
category: integrations
description: |
  Manage Google OAuth token lifecycle, credential storage, scope management, and re-authorization workflows. Handles both EDITH Vault (authoritative, full-scope) and plain-JSON credential files.
triggers:
  - Need to authenticate with Google APIs (Gmail, Drive, Sheets, Docs)
  - OAuth token expired or missing required scopes
  - Need to upload to Drive, create Docs, or access Gmail
  - Credential files need to be refreshed or scopes expanded
---

## Overview

Google OAuth credentials are stored in multiple places. **See `references/credential-paths-tanzim-environment.md` for the current live paths in this environment.**

**In Tanzim's environment specifically:**
- **Primary:** `~/.hermes/google_token.json` — unencrypted, immediately usable, full scopes (gmail, drive, docs, sheets, calendar)
- **Secondary:** EDITH Vault (`~/.hermes/.edith/`) — encrypted with vault.enc, requires decryption middleware (not directly readable as plain JSON)

**Golden rule in this environment:** **Always start with the token file.** It is unencrypted, directly readable, and has all required scopes. Only attempt vault access if token file is missing or corrupted.

The vault exists but is encrypted (`vault.enc`, `services.map.enc`) and not suitable for direct file-based credential loading in stateless agent contexts.

## Workflow: Check Credentials First

### Step 1: Determine what scopes you need
- Gmail operations → `gmail.modify` scope
- Drive upload/delete/share → `drive` scope
- Sheets read/write → `spreadsheets` scope
- Docs create → `docs` scope

### Step 2: Load Credentials (Token File Primary Path)

**PRIMARY: Plain Token File (unencrypted, immediately accessible)**
```python
import json
import os

token_file = os.path.expanduser('~/.hermes/google_token.json')
with open(token_file, 'r') as f:
    token_data = json.load(f)

# Token file structure (verified in Tanzim's environment):
oauth = {
    'access_token': token_data['token'],
    'refresh_token': token_data['refresh_token'],
    'token_uri': token_data['token_uri'],
    'client_id': token_data['client_id'],
    'client_secret': token_data['client_secret'],
    'scopes': token_data['scopes']  # Array of scope URLs
}
```

This file is the immediate, reliable source for credential access. Do not attempt EDITH vault (`~/.hermes/.edith/edith_vault.json`) unless this file is missing — the vault is encrypted and requires decryption infrastructure outside the scope of agent-initiated auth.

### Step 3: Create credentials and refresh
```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

creds = Credentials(
    token=oauth['access_token'],
    refresh_token=oauth['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id='313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com',
    client_secret='<GOOGLE_OAUTH_CLIENT_SECRET — see ~/.hermes/google_token.json>'
)

creds.refresh(Request())  # Refresh before use
```

## Workflow: Re-Authorization (when vault is expired)

If EDITH Vault token refresh fails with `unauthorized_client` error:

### Step 1: Generate authorization URL
```python
CLIENT_ID = "313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/docs"
]

scope_str = " ".join(SCOPES)
auth_url = (
    f"https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri=http://localhost:8080/&"
    f"response_type=code&"
    f"scope={scope_str}&"
    f"access_type=offline&"
    f"prompt=consent"
)
```

### Step 2: User authorizes, gets redirect URL with code
User clicks link, authorizes, receives URL like:
`http://localhost:8080/?code=4/0AdkVLPxc0TrYy6HXZwrkrMhX-oR3BBFoVrEeDSGPk8aNCmXF6NLzUpZcwrvIdFxkaFDl0Q`

### Step 3: Exchange code for tokens
```python
import requests

code = "4/0AdkVLPxc0TrYy6HXZwrkrMhX-oR3BBFoVrEeDSGPk8aNCmXF6NLzUpZcwrvIdFxkaFDl0Q"
CLIENT_SECRET = "<GOOGLE_OAUTH_CLIENT_SECRET — see ~/.hermes/google_token.json>"

token_url = "https://oauth2.googleapis.com/token"
payload = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "grant_type": "authorization_code",
    "redirect_uri": "http://localhost:8080/"
}

response = requests.post(token_url, data=payload)
token_data = response.json()

# token_data now has 'access_token' and 'refresh_token'
```

### Step 4: Update EDITH Vault with new tokens
```python
edith_vault_path = os.path.expanduser('~/.hermes/.edith/edith_vault.json')

with open(edith_vault_path, 'r') as f:
    vault = json.load(f)

vault['google_oauth'] = {
    'service': 'google_oauth',
    'scopes': ['gmail', 'drive', 'docs', 'sheets', 'chat'],
    'access_token': token_data['access_token'],
    'refresh_token': token_data['refresh_token'],
    'expires_in': token_data['expires_in'],
    'token_type': 'Bearer'
}

with open(edith_vault_path, 'w') as f:
    json.dump(vault, f)
```

## Common Pitfalls

0. **`friday_backup/` credentials are dead** — `~/friday_backup/google_token.json` is tied to a deleted OAuth client and will throw `deleted_client` on any refresh. Ignore it entirely. Only use `~/.hermes/google_token.json`.

1. **Using plain JSON instead of vault** — The `~/.hermes/google_oauth_full.json` file may have fewer scopes or be stale. Always load from the primary token file first.

1b. **googleapiclient masks deleted-client failures** — `Credentials(...)` will report `expired=False, valid=True` even for a dead OAuth client. The error only surfaces on the first API call. **Always validate with a raw urllib refresh before building any googleapiclient service.** If urllib refresh throws `deleted_client`, the OAuth app is gone and re-auth is needed — don't waste time debugging token expiry.

2. **Not refreshing before API calls** — Call `creds.refresh(Request())` before building service clients. Stale tokens cause 401 errors partway through operations.

3. **Assuming 401 means "need to re-auth"** — Often it means the token is just stale. Try refresh first. Only re-auth if refresh fails with `unauthorized_client`.

4. **Not updating vault after re-auth** — After getting new tokens, write them back to EDITH Vault so future sessions have the fresh tokens.

5. **Forgetting to set `access_type=offline`** — Without this, Google won't give you a refresh token, and the next session will need to re-auth again.

## Checking What Scopes Are Currently Authorized

Read the Credentials sheet in Google Sheets (`https://docs.google.com/spreadsheets/d/1QtHeLtYqd21fGWY0FwRqxGgodYgj-rXnM7mXT9MzzLw/`) — the **Authentication** tab lists all active scopes and their status.

## Files & References

- Token file location: `~/.hermes/google_token.json` (primary, unencrypted)
- EDITH Vault location: `~/.hermes/.edith/edith_vault.json` (encrypted, avoid in agent code)
- Credentials tracking sheet: `https://docs.google.com/spreadsheets/d/1QtHeLtYqd21fGWY0FwRqxGgodYgj-rXnM7mXT9MzzLw/`
- OAuth app credentials: Client ID `313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com` (stored in code, not secret)
- **See `references/tanzim-drive-search-patterns.md` for job sheet IDs, credential file structure, and multi-sheet search patterns**
- **See `references/web-access-timeouts-fallback-patterns.md` for curl-based fallback when browser tools time out**
- **See `references/raw-rest-gmail-sheets-patterns.md` for stdlib-only (urllib) Gmail search/read + Sheets values patterns, the urlencode gotcha, and the email↔sheet interview cross-match workflow (inbox is source of truth, not CALLBACK column)**
- **See `references/docs-create-and-style-patterns.md` for creating a formatted Google Doc from scratch (title/headings/bullets), the 1-indexed range-tracking gotcha, and named-style + bullet-preset batchUpdate recipe**
