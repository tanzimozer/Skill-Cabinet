---
name: google-oauth-setup-tanzim
description: "Complete workflow for setting up and authorizing Google OAuth 2.0 credentials for Tanzim's projects. Covers Google Cloud Console setup, scope configuration, client creation, and authorization code exchange."
keywords: ["google", "oauth", "credentials", "authorization", "gmail", "drive", "sheets"]
triggers:
  - "User needs Gmail/Drive/Sheets API access"
  - "OAuth token has expired or been revoked"
  - "Need to authorize a new project with Google APIs"
context: |
  Google OAuth setup for Tanzim's personal projects (e.g., Friday) requires careful scope selection and client configuration. The process has several failure modes (invalid scopes, unverified app, redirect URI issues) that can be avoided by following the correct sequence.
---

## Google OAuth Setup Workflow for Tanzim

### Overview
Setting up Google OAuth to access Gmail, Google Drive, Google Sheets, and Google Calendar. The process involves:
1. Create a Google Cloud project
2. Enable required APIs
3. Configure OAuth consent screen + add test users
4. Create OAuth 2.0 Desktop Client credentials
5. Authorize and exchange code for refresh token

### Step 1: Create Google Cloud Project
- Go to https://console.cloud.google.com/projectcreate
- Name it (e.g., "Friday")
- Wait for creation to complete

### Step 2: Enable APIs
In the project, go to **APIs & Services → Library** and enable:
- Gmail API
- Google Drive API
- Google Sheets API
- Google Calendar API
- (Optional) Google Docs API

Each takes ~10 seconds. No additional config needed at this step.

### Step 3: Configure OAuth Consent Screen
Go to **APIs & Services → OAuth consent screen**:
1. Select **External** user type (if internal, Google may block certain operations)
2. Fill in:
   - **App name**: Project name (e.g., "Friday")
   - **User support email**: User's email (tanzim.seattle@gmail.com)
   - **Developer contact info**: Same email
3. Click **Save and Continue**
4. **Add scopes** — use ONLY these; others will fail:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive.readonly` (or drive for full access)
   - `https://www.googleapis.com/auth/calendar`
   - ⚠️ **DO NOT use**: `gmail.modify`, `documents`, or other non-standard URIs
5. Click **Save and Continue**
6. **Add test user**: Add tanzim.seattle@gmail.com as a test user (required for unverified apps)
7. Click **Save and Continue**

### Step 4: Create OAuth 2.0 Client ID
Go to **APIs & Services → Credentials**:
1. Click **+ Create Credentials → OAuth 2.0 Client ID**
2. Select **Desktop application** (not Web, not Android)
3. Name it (e.g., "Friday")
4. Click **Create**
5. **Download the JSON file** — this contains client_id, client_secret, and redirect_uris

Key fields from the downloaded JSON:
```json
{
  "installed": {
    "client_id": "XXXXX.apps.googleusercontent.com",
    "client_secret": "GOCSPX-XXXXX",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost"]
  }
}
```

Save this to `~/.hermes/google_oauth_client.json`.

### Step 5: Generate Authorization Link
Use the client_id and client_secret from the JSON file to build an auth URL:

```python
import urllib.parse

client_id = "YOUR_CLIENT_ID_HERE"
redirect_uri = "http://localhost"  # Match what's in the JSON
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
print(auth_url)
```

Send the URL to the user. They click it, approve all scopes, and Google redirects to `http://localhost?code=AUTHORIZATION_CODE&...`.

### Step 6: Exchange Authorization Code for Tokens
Once the user approves and Google gives you the authorization code:

```python
import requests
import json

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
auth_code = "THE_CODE_FROM_REDIRECT"
redirect_uri = "http://localhost"

token_payload = {
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}

response = requests.post(
    'https://oauth2.googleapis.com/token',
    json=token_payload
)

tokens = response.json()
# tokens now contains 'access_token', 'refresh_token', 'expires_in', etc.

# Save refresh_token to ~/.hermes/google_token.json for future use
with open(os.path.expanduser('~/.hermes/google_token.json'), 'w') as f:
    json.dump(tokens, f)
```

### Step 7: Use the Access Token
Initialize Google API clients:

```python
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Load saved tokens
with open(os.path.expanduser('~/.hermes/google_token.json'), 'r') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['access_token'],
    refresh_token=token_data['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET'
)

# Refresh if needed (access tokens expire after ~1 hour)
if creds.expired:
    creds.refresh(Request())

# Build clients
gmail = build('gmail', 'v1', credentials=creds)
sheets = build('sheets', 'v4', credentials=creds)
drive = build('drive', 'v3', credentials=creds)
```

---

## Common Pitfalls & Fixes

### Pitfall 1: Invalid Scope Error (Error 400: invalid_scope)
**Symptom:** "Some requested scopes were invalid."

**Cause:** Typo or non-existent scope URI (e.g., `gmail.modify` instead of `https://www.googleapis.com/auth/gmail.modify`, or `documents` instead of a real Google Docs scope).

**Fix:** Use ONLY the scopes listed in Step 3. Do not improvise scope names. If you need a scope not listed, verify it exists in the official Google OAuth docs.

### Pitfall 2: Error 403: access_denied / "App has not completed verification"
**Symptom:** Google blocks the login with "Friday has not completed the Google verification process."

**Cause:** The OAuth app is in "testing" mode (unverified). User is not listed as a test user, or the consent screen is not fully configured.

**Fix:**
1. Go to **APIs & Services → OAuth consent screen**
2. Ensure **External** user type is selected (not Internal)
3. Scroll to **Test users** section
4. Add the user's email (tanzim.seattle@gmail.com) as a test user
5. Save and wait ~1 minute for propagation
6. Retry the auth link

### Pitfall 3: Redirect URI Mismatch
**Symptom:** "redirect_uri_mismatch" error.

**Cause:** The redirect_uri in the auth URL doesn't match what's configured in the OAuth client credentials.

**Fix:** In the downloaded JSON, check the `redirect_uris` array. Use the exact same value in your auth URL. For desktop apps, this is typically `http://localhost` or `urn:ietf:wg:oauth:2.0:oob` (out-of-band, for copy/paste flow).

### Pitfall 4: Refresh Token Expired or Missing
**Symptom:** Can initialize credentials but cannot refresh when access_token expires.

**Cause:** No refresh_token was returned during authorization, or it was revoked (can happen if user revokes app access or changes password).

**Fix:**
1. Include `access_type=offline` in the authorization URL (ensures refresh_token is returned)
2. Include `prompt=consent` to force a full re-consent (sometimes needed to get refresh_token back)
3. If refresh_token is still missing, user must re-authorize from scratch

### Pitfall 5: Token File Not Persisting
**Symptom:** Credentials work in the session but fail the next time.

**Cause:** Token file not saved to disk, or saved to wrong path.

**Fix:** Always save to `~/.hermes/google_token.json` and verify the file exists before trying to load it.

---

## Implementation Checklist

- [ ] Google Cloud project created
- [ ] Gmail, Drive, Sheets, Calendar APIs enabled
- [ ] OAuth consent screen configured (External, app name, emails filled in)
- [ ] Test user (tanzim.seattle@gmail.com) added to consent screen
- [ ] OAuth 2.0 Desktop Client created and JSON downloaded
- [ ] Client JSON saved to `~/.hermes/google_oauth_client.json`
- [ ] Authorization URL generated and sent to user
- [ ] User approved scopes and received auth code
- [ ] Auth code exchanged for tokens
- [ ] Refresh token saved to `~/.hermes/google_token.json`
- [ ] API clients initialized and tested with a simple query

---

## Scopes Reference

**Valid Google OAuth scopes for this workflow:**

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/gmail.readonly` | Read Gmail messages (not write/send) |
| `https://www.googleapis.com/auth/gmail.modify` | Read and manage Gmail (send, delete, label) |
| `https://www.googleapis.com/auth/spreadsheets` | Read and write Google Sheets |
| `https://www.googleapis.com/auth/drive.readonly` | Read-only Google Drive access |
| `https://www.googleapis.com/auth/drive` | Full Google Drive access (read, write, delete) |
| `https://www.googleapis.com/auth/calendar` | Read and manage Google Calendar |

Do NOT invent scope names. Always verify against [Google OAuth Scopes documentation](https://developers.google.com/identity/protocols/oauth2/scopes).

---

## See Also
- `references/oauth-june-2026-session.md` — Session-specific credentials and error transcripts from June 17, 2026
- `credential-management-tanzim` — EDITH vault operations and local credential storage
