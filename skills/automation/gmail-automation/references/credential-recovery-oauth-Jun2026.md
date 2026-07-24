# OAuth Credential Recovery (Tanzim, Jun 2026)

## Problem
Token refresh fails with `invalid_client` or `401 Unauthorized` because:
- Stored `~/.hermes/google_token.json` is missing `client_id` and `client_secret` fields
- Client credentials are split across multiple backup files

## Solution: Merge Credentials from Backups

### Step 1: Identify available files
```bash
cat ~/.hermes/google_token.json          # Has access_token, refresh_token, scope, token_type
cat /home/hermes/friday_backup/google_client_secret.json  # Has client_id, client_secret
```

### Step 2: Load and merge (Python)
```python
import json, subprocess

# Read stored token (may be incomplete)
result = subprocess.run(['cat', '/home/hermes/.hermes/google_token.json'], capture_output=True, text=True)
current_token = json.loads(result.stdout)

# Read client credentials from backup
result = subprocess.run(['cat', '/home/hermes/friday_backup/google_client_secret.json'], capture_output=True, text=True)
client_data = json.loads(result.stdout)
client_info = client_data.get('installed') or client_data.get('web') or client_data

# Merge: token fields + client fields
merged = {
    'access_token': current_token['access_token'],
    'refresh_token': current_token['refresh_token'],
    'expires_in': current_token['expires_in'],
    'token_type': current_token['token_type'],
    'scope': current_token['scope'],
    'client_id': client_info['client_id'],
    'client_secret': client_info['client_secret'],
    'token_uri': client_info['token_uri'],
    'type': 'authorized_user'
}

# Write merged token back
with open('/home/hermes/.hermes/google_token.json', 'w') as f:
    json.dump(merged, f, indent=2)

print("Token file rebuilt with client credentials.")
```

### Step 3: Test refresh
```python
import requests, json, subprocess

result = subprocess.run(['cat', '/home/hermes/.hermes/google_token.json'], capture_output=True, text=True)
t = json.loads(result.stdout)

r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token',
})

if r.status_code == 200:
    print("Success. New access token:", r.json()['access_token'][:20])
else:
    print(f"Refresh failed: {r.status_code} - {r.json()}")
```

## When to use this workflow
- Token refresh returns `401` or `invalid_client`
- Credential files exist but are scattered across the filesystem
- You have `access_token` and `refresh_token` but no `client_id`/`client_secret` in the same file

## Files involved (Tanzim's environment, Jun 2026)
| File | Contains | Status |
|------|----------|--------|
| `~/.hermes/google_token.json` | access_token, refresh_token, scope | Primary (often incomplete) |
| `/home/hermes/friday_backup/google_client_secret.json` | client_id, client_secret, token_uri | Backup (complete) |
| `~/Desktop/CREDENTIALS_MASTER.md` | Metadata on active credentials | Reference |

## If refresh STILL fails after merge
- Check `~/Desktop/CREDENTIALS_MASTER.md` for the current active FRIDAY OAuth client ID
- If the client_id in the backup does not match the master file, the OAuth app may have been deleted/regenerated in Google Cloud
- Tanzim needs to create fresh OAuth credentials in Google Cloud Console (see parent skill references for OAuth setup)
- Do not assume the credentials are permanently broken — ask Tanzim for the current client_id from Google Cloud Console first
