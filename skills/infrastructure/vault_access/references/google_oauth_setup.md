# Google OAuth Setup & Token Exchange

## Quick Reference: Fresh OAuth Flow

Use this when the current token is poisoned, the OAuth client was deleted, or credentials are missing.

---

## ⚠️ Critical: `oob` redirect is DEAD (deprecated by Google)

Do NOT use `redirect_uri='urn:ietf:wg:oauth:2.0:oob'` — Google returns `Error 400: invalid_request`.
Do NOT use `InstalledAppFlow.run_local_server()` — it tries to open a browser on the server.

**The correct pattern is localhost-redirect + manual code paste.** See Step 3 below.

---

## Step 1: Obtain a Client Secret JSON

Ask Tanzim to:
1. Go to [console.cloud.google.com](https://console.cloud.google.com) → project `job-scraping-494906` (or `friday-mark-2-499708`)
2. **APIs & Services → Credentials → + CREATE CREDENTIALS → OAuth 2.0 Client ID**
3. Type: **Desktop app**
4. Download the JSON and send it here

Save the received file to `~/.hermes/google_client_secret.json`.

Also ensure Tanzim's email (`tanzim.seattle@gmail.com`) is listed under **OAuth consent screen → Test users** if the app is in Testing mode.

---

## Step 2: Generate Authorization URL

```python
import urllib.parse

params = {
    'client_id': 'YOUR_CLIENT_ID',
    'redirect_uri': 'http://localhost',
    'response_type': 'code',
    'scope': ' '.join([
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets',
    ]),
    'access_type': 'offline',
    'prompt': 'consent',
}

url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
print(url)
```

OR using `InstalledAppFlow` (also works, skip the redirect_uri kwarg to avoid conflict):

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]

flow = InstalledAppFlow.from_client_secrets_file(
    '/home/hermes/.hermes/google_client_secret.json',
    scopes=SCOPES,
)

# Do NOT pass redirect_uri here — the JSON already has http://localhost
auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
print(auth_url)
```

Send the URL to Tanzim.

---

## Step 3: User Authorises — Paste Back the Redirect URL

Instruct Tanzim:
1. Open the link and sign in as `tanzim.seattle@gmail.com`
2. Approve all scopes
3. The browser will land on a **broken localhost page** — that's expected
4. Copy the full URL from the address bar and send it back

Example of what to expect:
```
http://localhost/?iss=https://accounts.google.com&code=4/0AXEQx...&scope=...
```

---

## Step 4: Exchange Code for Token

```python
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [...]  # same list as above

flow = InstalledAppFlow.from_client_secrets_file(
    '/home/hermes/.hermes/google_client_secret.json',
    scopes=SCOPES,
    redirect_uri='http://localhost'  # must match what was used in Step 2
)

# Extract code from the pasted URL (parse it or take it directly)
code = '4/0AXEQx...'  # the `code` param from the redirect URL

flow.fetch_token(code=code)
creds = flow.credentials

# Save token
token_data = {
    'token': creds.token,                  # NOTE: key is 'token', not 'access_token'
    'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri,
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'scopes': list(creds.scopes),
}

with open('/home/hermes/.hermes/google_token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print(f"Refresh token present: {bool(creds.refresh_token)}")
```

---

## Step 5: Load & Test

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)

creds = Credentials(
    token=t['token'],                   # key is 'token' (not 'access_token')
    refresh_token=t['refresh_token'],
    token_uri=t['token_uri'],
    client_id=t['client_id'],
    client_secret=t['client_secret'],
    scopes=t['scopes'],
)

service = build('gmail', 'v1', credentials=creds)
profile = service.users().getProfile(userId='me').execute()
print(f"Connected as: {profile['emailAddress']}")
```

---

## Also update vault.json after re-auth

```python
# Update the client_id and project_id fields in vault.json to reflect the new OAuth client
vault['google']['client_id'] = creds.client_id
vault['google']['project_id'] = 'job-scraping-494906'  # or whichever project was used
vault['google']['note'] = f'Re-authed {date.today()}; prior client deleted.'
```

---

## Troubleshooting

### `Error 400: invalid_request` / "Access blocked: Friday's request is invalid"
- You used `oob` as redirect URI — **deprecated, dead**. Use `http://localhost` instead.

### `deleted_client: The OAuth client was deleted`
- The OAuth client in Google Cloud Console was deleted (or the project changed).
- Fix: create a new Desktop app OAuth client, download JSON, re-run this flow.

### `redirect_uri_mismatch`
- The `redirect_uri` in Step 4 must exactly match what was registered (and used in Step 2).
- Desktop app clients auto-register `http://localhost` — use that exactly.

### `TypeError: got multiple values for keyword argument 'redirect_uri'`
- Caused by passing `redirect_uri` both in `from_client_secrets_file` AND in `authorization_url`.
- Fix: only pass `redirect_uri` in `fetch_token` / `InstalledAppFlow` constructor, not in `authorization_url()`.

### Token expires immediately / no refresh_token
- Ensure `access_type='offline'` and `prompt='consent'` are in the auth URL.
- Without `prompt=consent`, Google won't re-issue a refresh token if one was previously granted.

### `invalid_scope`
- Scopes in the auth URL don't match what the client was provisioned for, or a new scope was added mid-flight.
- Fix: create a new OAuth client and re-auth with the full desired scope set from the start.

---

## Current active credentials (as of Jul 2026)
- **Project:** `job-scraping-494906`
- **Client ID:** `313611152308-r2g23uql9vg6hlahgvabrdk8klsoa0jk`
- **Account:** `tanzim.seattle@gmail.com`
- **Token file:** `~/.hermes/google_token.json`
- **Client secret file:** `~/.hermes/google_client_secret.json`
