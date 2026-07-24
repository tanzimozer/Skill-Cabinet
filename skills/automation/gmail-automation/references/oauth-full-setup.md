# Google OAuth Full Setup Workflow (Permanent Credentials)

**Context:** Jun 8, 2026. Tanzim required permanent, full-access Google credentials that persist across sessions and never need re-authentication. This document captures the corrected workflow after multiple scope configuration failures.

## Credentials (Current)

**File:** `~/.hermes/google_oauth_full.json`

```json
{
  "installed": {
    "client_id": "313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com",
    "project_id": "job-scraping-494906",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "<GOOGLE_OAUTH_CLIENT_SECRET — see ~/.hermes/google_token.json>",
    "redirect_uris": ["http://localhost"]
  },
  "access_token": null,
  "refresh_token": null,
  "scopes": [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets"
  ]
}
```

## Setup Steps (Complete Workflow)

### 1. Create Google Cloud Project & OAuth App

1. Go to: https://console.cloud.google.com
2. Create new project (name: `hermes-full-access` or similar)
3. Wait ~30 seconds for initialization

### 2. Enable Required APIs

Go to **APIs & Services** → **Library** and enable each:
- Gmail API
- Google Calendar API
- Google Drive API
- Google Docs API
- Google Sheets API

### 3. Configure OAuth Consent Screen (CRITICAL)

Go to **APIs & Services** → **Credentials** → **OAuth consent screen**

1. Choose **"External"** (unless you have Google Workspace)
2. Click **CREATE**
3. Fill app info:
   - App name: `Hermes`
   - User support email: `tanzimozer@gmail.com`
   - Developer contact: `tanzimozer@gmail.com`
4. Click **SAVE AND CONTINUE**

**On Scopes page:**
1. Click **ADD OR REMOVE SCOPES**
2. **Carefully add each scope with exact URL spelling:**
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.labels`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/documents` ← **NOT `docs`**
   - `https://www.googleapis.com/auth/spreadsheets`
3. Click **UPDATE** → **SAVE AND CONTINUE**

**On Test Users page:**
1. Click **ADD USERS**
2. Add: `tanzimozer@gmail.com` (or the email being authorized)
3. Click **SAVE AND CONTINUE**
4. Review and click **BACK TO DASHBOARD**

### 4. Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Desktop application**
4. Name: `Hermes CLI`
5. Click **CREATE**
6. Download the JSON or copy client_id + client_secret

### 5. Generate Refresh Token (Desktop Flow)

Use this authorization URL (replace `CLIENT_ID`):

```
https://accounts.google.com/o/oauth2/v2/auth?
client_id=CLIENT_ID&
redirect_uri=http://localhost&
response_type=code&
scope=https://www.googleapis.com/auth/gmail.modify%20https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/gmail.labels%20https://www.googleapis.com/auth/calendar%20https://www.googleapis.com/auth/drive%20https://www.googleapis.com/auth/documents%20https://www.googleapis.com/auth/spreadsheets&
access_type=offline&
prompt=consent
```

**Steps:**
1. Open the URL in browser
2. Click "Allow" to authorize all scopes
3. Browser redirects to: `http://localhost?code=AUTHORIZATION_CODE&...`
4. Copy the `code` value (long string between `code=` and `&` or end of URL)

### 6. Exchange Authorization Code for Refresh Token

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=http://localhost"
```

Response will include `refresh_token` (long string starting with `1//`). Save this.

### 7. Store Credentials Permanently

**Primary location:** `~/.hermes/google_oauth_full.json`

```json
{
  "installed": { /* OAuth app info */ },
  "access_token": "ya29.a0AT...",
  "refresh_token": "1//0...",
  "expires_in": 3600,
  "scopes": [ /* all 8 scopes */ ]
}
```

**Backup locations:**
- Google Sheets "Credentials" sheet (if shared workspace exists)
- Long-term hindsight memory (via hindsight_retain)
- System environment variable `$GOOGLE_OAUTH_FULL` (optional)
- USER.md profile (optional)

## Common Failures & Fixes

### Error: "Some requested scopes were invalid"
**Root cause:** One or more scopes not added to the OAuth Consent Screen, OR scopes added with typos (e.g., `docs` instead of `documents`).

**Fix:** Re-check step 3. Verify exact spelling. Test with one scope first (`gmail.readonly`) to isolate which one fails.

### Error: "Unauthorized" (401) when accessing Gmail
**Root cause:** Access token expired. Refresh token is valid but access token needs refresh.

**Fix:** Use refresh token to get new access token:
```python
import requests
r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': client_id,
    'client_secret': client_secret,
    'refresh_token': refresh_token,
    'grant_type': 'refresh_token'
})
new_access_token = r.json()['access_token']
```

### Error: "localhost refused to connect" on redirect
**Root cause:** Browser tried to navigate to `http://localhost` but no local server is running.

**Fix (workaround):** This is expected. The redirect will fail, but the URL bar will show the code. Copy it from there. Desktop apps don't need a real server.

## Verification (Test Immediately After Setup)

```python
import requests

headers = {'Authorization': f'Bearer {access_token}'}
r = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/profile', headers=headers)
print(r.json())
# Should print: { "emailAddress": "tanzimozer@gmail.com", "messagesTotal": ..., ... }
```

If this works, full Gmail access is confirmed.

## Scope Meanings

| Scope | Purpose |
|-------|---------|
| `gmail.modify` | Read, trash, label emails (non-destructive) |
| `gmail.readonly` | Read emails only (no modifications) |
| `gmail.send` | Send emails on behalf of user |
| `gmail.labels` | Create, update, delete custom labels |
| `calendar` | Read/write calendar events |
| `drive` | Read/write Google Drive files |
| `documents` | Read/write Google Docs |
| `spreadsheets` | Read/write Google Sheets |
