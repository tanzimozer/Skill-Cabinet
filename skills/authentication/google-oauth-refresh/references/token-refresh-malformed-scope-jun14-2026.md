# Token Refresh — Malformed Scope / Missing Access Token (Jun 14, 2026)

## Problem
Google token file (`~/.hermes/google_token.json`) had:
- Valid `refresh_token` ✓
- Valid `client_id`, `client_secret` ✓
- Full scope list ✓
- **BUT:** Missing `access_token` (null/empty)
- **AND:** Token marked `expiry: 2026-06-14T09:52:09Z` (past)

**Error on refresh attempt:**
```
google.auth.exceptions.RefreshError: ('invalid_scope: Bad Request', {'error': 'invalid_scope', 'error_description': 'Bad Request'})
```

## Root Cause
Unclear, but likely causes:
1. Token file was partially written (access token field missing)
2. Scope list in token file doesn't match scopes requested in `Credentials.from_authorized_user_info()` call
3. Token was revoked server-side and needs full re-auth

## Solution: Use Raw HTTP Refresh (Most Reliable)

Avoid the google-auth library for refresh — it's stricter about scope validation. Instead, do raw HTTP:

```python
import requests
import json
from datetime import datetime, timedelta

token_path = os.path.expanduser('~/.hermes/google_token.json')
with open(token_path, 'r') as f:
    token_data = json.load(f)

# Make the refresh request directly
resp = requests.post(
    'https://oauth2.googleapis.com/token',
    data={
        'client_id': token_data['client_id'],
        'client_secret': token_data['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token'
    }
)

if resp.status_code == 200:
    new_data = resp.json()
    
    # Merge new access token back into the token file (keep everything else)
    token_data['token'] = new_data['access_token']
    token_data['expiry'] = (
        datetime.utcnow() + 
        timedelta(seconds=new_data.get('expires_in', 3600))
    ).isoformat() + 'Z'
    
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print('✓ Token refreshed and saved.')
    
elif resp.status_code == 400:
    error = resp.json().get('error', 'unknown')
    if error == 'invalid_grant':
        print('❌ Refresh token revoked. Need full re-auth.')
    else:
        print(f'❌ Refresh failed: {error} — {resp.json().get("error_description")}')
else:
    print(f'❌ Unexpected error: {resp.status_code} — {resp.text}')
```

**This works even if the google-auth library refuses to refresh.** It bypasses scope validation and just uses the refresh token to get a new access token.

## Pattern: Check Token First

Before attempting any Google API call, always check token freshness:

```python
import json
from datetime import datetime

token_path = os.path.expanduser('~/.hermes/google_token.json')
with open(token_path, 'r') as f:
    token_data = json.load(f)

# Check if token is missing or expired
token = token_data.get('token')
expiry = token_data.get('expiry')

is_expired = False
if not token:
    print('⚠️ No access token in file. Refreshing...')
    is_expired = True
elif expiry:
    try:
        exp_time = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        if datetime.utcnow() > exp_time:
            print('⚠️ Token expired. Refreshing...')
            is_expired = True
    except ValueError:
        print(f'⚠️ Could not parse expiry: {expiry}. Refreshing...')
        is_expired = True

if is_expired:
    # Do the raw HTTP refresh (see above)
    ...
```

## When to Use This

- Token file is missing `access_token`
- `google-auth` library refuses to refresh with `invalid_scope`
- Token is expired and you need Sheets/Drive/Gmail access quickly
- Running in a cron job or headless context where google-auth is not available

## Success Indicator

After refresh, `~/.hermes/google_token.json` should have:
- `token`: non-null 40+ character string
- `expiry`: future timestamp (e.g., `2026-06-14T10:52:09Z` if refreshed at 09:52)

Test with:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open(os.path.expanduser('~/.hermes/google_token.json')) as f:
    t = json.load(f)

creds = Credentials.from_authorized_user_info(t)
sheets = build('sheets', 'v4', credentials=creds)
sheets.spreadsheets().get(spreadsheetId='1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo').execute()
print('✓ Token is valid and Google API is accessible.')
```
