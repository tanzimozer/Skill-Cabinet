---
name: google-auth-refresh
description: Refreshing an expired or revoked Google OAuth token for Hermes. Manual code-exchange flow when the refresh_token itself has been invalidated.
triggers:
  - google token expired
  - invalid_grant
  - google auth refresh
  - re-authenticate google
  - google token revoked
---

# Google OAuth Token Refresh

## When you need this
- API calls return `invalid_grant: Token has been expired or revoked`
- `google.auth.exceptions.RefreshError` from any Google API call
- Normal `creds.refresh(Request())` fails — the refresh_token itself is dead
- `invalid_scope: Bad Request` from the SDK even though scopes look correct (see bypass below)

## SDK `invalid_scope` bypass — use raw requests instead
The google-auth SDK sometimes throws `invalid_scope: Bad Request` on refresh even when the token file has correct scopes. **Bypass the SDK entirely and refresh manually:**

```python
import requests, json

t = json.load(open('/home/hermes/.hermes/google_token.json'))
r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token',
})
access_token = r.json()['access_token']
headers = {'Authorization': f'Bearer {access_token}'}
# Now use `requests` directly against any Google REST API — no SDK needed
```

**Test Gmail access:**
```python
r = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/profile', headers=headers)
print(r.json())  # should show emailAddress, messagesTotal
```

This pattern works reliably when the refresh_token is still valid but the SDK is misbehaving. If `r.status_code != 200`, the refresh_token itself is revoked — proceed to the full re-auth flow below.

## Step 1 — Try auto-refresh first
```python
from google.auth.transport.requests import Request
creds.refresh(Request())
```
If this throws `RefreshError: invalid_grant`, the refresh token is fully revoked. Proceed to Step 2.

## Step 2 — Get client credentials
```bash
cat /home/hermes/.hermes/google_client_secret.json | python3 -c "
import sys,json; d=json.load(sys.stdin)
w = d.get('web', d.get('installed', {}))
print('client_id:', w['client_id'])
"
```

## Step 3 — Build auth URL and send to Tanzim
```
https://accounts.google.com/o/oauth2/auth?client_id=<CLIENT_ID>&redirect_uri=http%3A%2F%2Flocalhost%3A8080&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&access_type=offline&prompt=consent
```

Tell Tanzim: open the URL, approve Google access, browser will redirect to localhost (will show error — that's fine), copy the **full URL from the address bar** and paste it back.

## Step 4 — Exchange code for token
```python
import requests, json

code = "4/0Aeo..."  # extracted from the ?code= param in the URL Tanzim pastes

with open('/home/hermes/.hermes/google_client_secret.json') as f:
    d = json.load(f)
w = d.get('web', d.get('installed', {}))

resp = requests.post('https://oauth2.googleapis.com/token', data={
    'code': code,
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

## Step 5 — Verify
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    td = json.load(f)
creds = Credentials(token=td['token'], refresh_token=td['refresh_token'],
    token_uri=td['token_uri'], client_id=td['client_id'], client_secret=td['client_secret'])
sheets = build('sheets', 'v4', credentials=creds)
# Test any known sheet ID
```

## Pitfalls
- `hermes auth google` — does NOT exist as a command. Don't suggest it.
- `setup.py` alone opens nothing — it's non-interactive by design. Use `--auth-url` flag.
- The redirect goes to localhost:8080 — browser shows an error, that's expected. Tanzim copies the URL with `?code=...` from the address bar.
- The `code` in the URL is URL-encoded — extract just the `code=` param value, don't include `&scope=...` etc.
- `access_type=offline&prompt=consent` are both required to get a new refresh_token

## Scope list (full set)
```
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/contacts.readonly
https://www.googleapis.com/auth/documents.readonly
```

## Gmail REST API — common operations (no SDK needed)

```python
# Search messages
res = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/messages',
    params={'q': 'subject:"thank you for applying"', 'maxResults': 500},
    headers=headers).json()
msg_ids = [m['id'] for m in res.get('messages', [])]

# Trash a message (recoverable — goes to Trash, not permanent delete)
requests.post(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/trash',
    headers=headers)

# Permanently delete (irreversible)
requests.delete(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}',
    headers=headers)
```

**Rejection/application email queries that work (Jun 2026, tanzim.seattle@gmail.com):**
```python
queries = [
    'subject:"thank you for applying"',       # 23 results
    'subject:"thank you for your application"', # 6 results
    'subject:"application received"',           # 5 results
    'subject:"we regret"',
    'subject:"unfortunately" application',
    'subject:"not moving forward"',
    'subject:"other candidates"',
]
# Pattern: collect all IDs into a set first, then trash/delete in a loop
```

**Confirmed working Jun 2026:** 32/32 rejection emails trashed in one pass from tanzim.seattle@gmail.com.

## Check before asking Tanzim
Always try the raw requests refresh first (`grant_type: refresh_token`). Only escalate to Tanzim if that returns a non-200 status — meaning the refresh_token itself is revoked. Don't ask him to re-auth when a simple token refresh would work.
