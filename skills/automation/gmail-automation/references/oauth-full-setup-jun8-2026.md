# Gmail OAuth Full Setup — Jun 8, 2026

**Goal:** One-time permanent Gmail OAuth setup with full scopes (8 total) so Tanzim never re-authenticates. Credentials stored in multiple locations (filesystem, memory, env vars).

**Status:** Completed Jun 8, 2026. Token stored in `~/.hermes/google_oauth_full.json` with refresh_token (permanent access).

---

## Prerequisites

- Google Cloud project with OAuth app (Desktop type, not Web)
- Client credentials JSON downloaded from GCP Console (contains `client_id`, `client_secret`, `project_id`)
- Localhost redirect URI: `http://localhost`

---

## Step 1: Download Credentials File

In Google Cloud Console for the project (e.g., `job-scraping-494906`):
1. Go to **Credentials**
2. Select the **OAuth 2.0 Client ID** (should be type "Desktop application")
3. Click **Download JSON**
4. Save as `Friday_Gmail_OAuth.json` (or similar)

**File structure:**
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
  }
}
```

---

## Step 2: Extract Credentials and Store Locally

```python
import json

# Read credentials file
with open('Friday_Gmail_OAuth.json') as f:
    creds_raw = json.load(f)

creds = creds_raw['installed']  # extract the 'installed' block

# Store permanently
with open(os.path.expanduser('~/.hermes/google_oauth_full.json'), 'w') as f:
    json.dump(creds, f, indent=2)

print(f"Stored credentials to ~/.hermes/google_oauth_full.json")
print(f"  client_id: {creds['client_id']}")
print(f"  project_id: {creds['project_id']}")
```

---

## Step 3: Generate Authorization Link with Full Scopes

**Critical:** Request all 8 scopes upfront (don't do read-only first, then delete later — you'll have to re-auth).

```python
import urllib.parse

client_id = "313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com"
redirect_uri = "http://localhost"

scopes = [
    "https://www.googleapis.com/auth/gmail.modify",      # includes delete, trash, label
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",         # NOT "docs" — this is the correct name
    "https://www.googleapis.com/auth/spreadsheets",
]

scope_str = urllib.parse.quote(' '.join(scopes))

auth_link = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope_str}&access_type=offline&prompt=consent"

print("Open this link in a browser and authorize:\n")
print(auth_link)
```

**User does this:**
1. Copy the link
2. Paste into browser
3. Sign in to Google account (e.g., tanzim.seattle@gmail.com)
4. Click "Allow" to grant all scopes
5. Browser redirects to `http://localhost?code=XXXXX&scope=...&iss=...`
6. Copy the `code=` value and send back to agent

---

## Step 4: Exchange Authorization Code for Access Token

User sends back: `http://localhost/?iss=https://accounts.google.com&code=4/0AdkVLPwVdkwdJz7RY46UE9_geehdfQci7Q4IETOxWIpOMpkQ5nhZSWkmtv1h8n7rQgoMCg&scope=...`

Extract the code (everything after `code=` up to the next `&`):

```python
import urllib.request
import urllib.parse
import json
import os

auth_code = "4/0AdkVLPwVdkwdJz7RY46UE9_geehdfQci7Q4IETOxWIpOMpkQ5nhZSWkmtv1h8n7rQgoMCg"

# Load the credentials file
with open(os.path.expanduser('~/.hermes/google_oauth_full.json')) as f:
    creds = json.load(f)

# Exchange code for token
data = urllib.parse.urlencode({
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'code': auth_code,
    'grant_type': 'authorization_code',
    'redirect_uri': creds['redirect_uris'][0],  # "http://localhost"
}).encode()

req = urllib.request.Request(
    creds['token_uri'],
    data=data,
    method='POST'
)

response = urllib.request.urlopen(req)
token_data = json.loads(response.read())

print(f"✓ Got access_token (expires in {token_data['expires_in']}s)")
print(f"✓ Got refresh_token (permanent)")
```

**Response structure:**
```json
{
  "access_token": "ya29.a0ATrz8AkXxxx...",
  "expires_in": 3600,
  "refresh_token": "1//0gxxxxxxxxxxxxxxxxxxxxxx",
  "scope": "https://www.googleapis.com/auth/spreadsheets ... (all 8)",
  "token_type": "Bearer"
}
```

---

## Step 5: Merge and Store the Token

The response contains the access & refresh tokens. Merge with the credentials file and save:

```python
# Merge token data with credentials
merged = {
    **creds,  # client_id, client_secret, etc.
    **token_data,  # access_token, refresh_token, expires_in
}

# Store back to ~/.hermes/google_oauth_full.json
with open(os.path.expanduser('~/.hermes/google_oauth_full.json'), 'w') as f:
    json.dump(merged, f, indent=2)

print("✓ Token saved to ~/.hermes/google_oauth_full.json")
print(f"  Scopes: {merged.get('scope', '').split()}")
```

**Final token file structure:**
```json
{
  "client_id": "313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com",
  "client_secret": "<GOOGLE_OAUTH_CLIENT_SECRET — see ~/.hermes/google_token.json>",
  "project_id": "job-scraping-494906",
  "access_token": "ya29.a0ATrz8AkXxxx...",
  "expires_in": 3600,
  "refresh_token": "1//0gxxxxxxxxxxxxx",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "scope": "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.readonly ... (all 8)",
  "redirect_uris": ["http://localhost"]
}
```

---

## Step 6: Store in Multiple Locations (Tanzim's Requirement)

To ensure credentials survive system resets and are accessible from anywhere:

1. **Filesystem (primary):** `~/.hermes/google_oauth_full.json` ✓ (done above)
2. **Permanent Memory:** Add to `~/.hermes/MEMORY.md` or via `memory.action='add'` (Friday's system)
3. **Environment variable:** Export `GOOGLE_OAUTH_FULL` in `~/.hermes/.env`
4. **Backup sheet:** "Software & API" sheet in Google Sheets (reference only, not auto-sync)

**Memory entry example:**
```
GOOGLE OAUTH FULL ACCESS — Jun 8, 2026

Client ID: 313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com
Refresh Token: 1//0gxxxxxxxxxxxxx (permanent — use for eternal access)
Scopes: gmail.modify, gmail.readonly, gmail.send, gmail.labels, calendar, drive, documents, spreadsheets
Status: Active ✓
Primary storage: ~/.hermes/google_oauth_full.json
```

---

## Step 7: Verify Token Works

```python
import urllib.request
import json
import os

with open(os.path.expanduser('~/.hermes/google_oauth_full.json')) as f:
    token_data = json.load(f)

access_token = token_data['access_token']

# Test: Get Gmail profile
req = urllib.request.Request(
    'https://gmail.googleapis.com/gmail/v1/users/me/profile',
    headers={'Authorization': f'Bearer {access_token}'}
)

response = urllib.request.urlopen(req)
profile = json.loads(response.read())

print(f"✓ Gmail access confirmed")
print(f"  Email: {profile['emailAddress']}")
print(f"  Total messages: {profile.get('messagesTotal', '?')}")
```

Expected response:
```json
{
  "emailAddress": "tanzim.seattle@gmail.com",
  "messagesTotal": 12345,
  "threadsTotal": 5000,
  "historyId": "99999999"
}
```

---

## Future: Refresh the Token

When the access_token expires (3600 seconds), refresh it without asking the user:

```python
import urllib.request
import urllib.parse
import json
import os

with open(os.path.expanduser('~/.hermes/google_oauth_full.json')) as f:
    token_data = json.load(f)

# Use the refresh_token to get a new access_token
data = urllib.parse.urlencode({
    'client_id': token_data['client_id'],
    'client_secret': token_data['client_secret'],
    'refresh_token': token_data['refresh_token'],
    'grant_type': 'refresh_token',
}).encode()

req = urllib.request.Request(
    token_data['token_uri'],
    data=data,
    method='POST'
)

response = urllib.request.urlopen(req)
new_token = json.loads(response.read())

# Update the access_token in memory (don't re-save to disk unless you want to)
access_token = new_token['access_token']
# Now use access_token for API calls
```

**Key:** The refresh_token never expires; the access_token only lasts ~1 hour. Always refresh before a long batch job, or refresh on 401 errors.

---

## Common Pitfalls

**1. "invalid_scope" error at authorization time**
- Google Cloud Console OAuth Consent Screen is missing one or more scopes
- Solution: Add all 8 scopes explicitly in the consent screen config (see gmail-automation SKILL.md, section "Pitfalls > Invalid scopes during OAuth authorization")

**2. Authorizing with only `gmail.readonly`, then trying to delete**
- Token is locked to read-only; no amount of retrying will unlock it
- Solution: Re-authorize with `gmail.modify` (and all other scopes you'll need)
- This is why we request all 8 upfront in Step 3

**3. Using `docs` instead of `documents` as a scope**
- Google silently rejects it with invalid_scope (no error message naming the typo)
- Solution: Always use `documents` (the correct Google scope name)

**4. Confusing `http://localhost` redirect with `localhost:8000` or `127.0.0.1`**
- OAuth link must match the redirect_uris in credentials file exactly
- Solution: Use `http://localhost` (no port number)

**5. Not storing refresh_token; only storing access_token**
- access_token expires in ~1 hour; without refresh_token, you're stuck
- Solution: Always extract and store refresh_token; access_token can be discarded after each use

