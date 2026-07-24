# Google OAuth Token Refresh — Manual Flow

## When it fails
`google.auth.exceptions.RefreshError: invalid_grant: Token has been expired or revoked`

This means the refresh token itself is invalidated — not just the access token expired. A simple `creds.refresh(Request())` won't fix it. Full re-auth required.

## The right approach — try refresh first
```python
from google.auth.transport.requests import Request
creds.refresh(Request())
```
If this raises `RefreshError: invalid_grant` → full re-auth needed.

## Full re-auth flow (no browser on VM — user does it)

### Step 1 — Get client credentials
```bash
cat /home/hermes/.hermes/google_client_secret.json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); w=d.get('web',d.get('installed',{})); print(w['client_id'])"
```

### Step 2 — Build auth URL and send to user
```
https://accounts.google.com/o/oauth2/auth?client_id=CLIENT_ID&redirect_uri=http%3A%2F%2Flocalhost%3A8080&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&access_type=offline&prompt=consent
```

User opens link → approves → browser redirects to localhost (shows error) → user copies full URL from address bar.

### Step 3 — Extract code and exchange
URL looks like: `http://localhost:8080/?code=4/0AeoWuM-...&scope=...`
Extract the `code` parameter.

```python
import json, requests

with open('/home/hermes/.hermes/google_client_secret.json') as f:
    d = json.load(f)
w = d.get('web', d.get('installed', {}))

resp = requests.post('https://oauth2.googleapis.com/token', data={
    'code': '<CODE_FROM_URL>',
    'client_id': w['client_id'],
    'client_secret': w['client_secret'],
    'redirect_uri': 'http://localhost:8080',
    'grant_type': 'authorization_code'
})
data = resp.json()

# Merge into existing token file
with open('/home/hermes/.hermes/google_token.json') as f:
    existing = json.load(f)
existing['token'] = data['access_token']
if 'refresh_token' in data:
    existing['refresh_token'] = data['refresh_token']
with open('/home/hermes/.hermes/google_token.json', 'w') as f:
    json.dump(existing, f, indent=2)
```

### Step 4 — Verify
```python
from googleapiclient.discovery import build
sheets = build('sheets', 'v4', credentials=creds)
sheets.spreadsheets().values().get(spreadsheetId='<any_sheet_id>', range='A1').execute()
# If no exception — auth is live
```

## Client ID (Tanzim)
`313611152308-9is3h086p9n4f8d7qabjk8pfkjp80qdq.apps.googleusercontent.com`

## Scopes used
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/calendar`

## Pitfalls
- `hermes auth google` does not exist — that command is invalid
- `setup.py` (the auth script) does work but requires `--auth-url` flag — running it bare does nothing visible
- The redirect goes to localhost:8080 — user's browser shows a connection error but the URL bar has the code. That's expected.
- Always use `prompt=consent` in the URL to force a fresh refresh_token to be issued
