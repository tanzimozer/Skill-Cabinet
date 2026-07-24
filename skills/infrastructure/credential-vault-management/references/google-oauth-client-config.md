# Google OAuth Client Configuration

**Project:** job-scraping-494906  
**Client ID:** 313611152308-epldc78dvcp55q0n4tfg7lt6tsanalhb.apps.googleusercontent.com  
**Client Secret:** <GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>  
**Redirect URI:** http://localhost:8080

## OAuth Endpoint

**Base URL:** https://accounts.google.com/o/oauth2/v2/auth

## Scopes Configured

```
https://www.googleapis.com/auth/gmail.modify         # Gmail (read, send, reply)
https://www.googleapis.com/auth/drive                # Google Drive (full access)
https://www.googleapis.com/auth/documents            # Google Docs
https://www.googleapis.com/auth/spreadsheets         # Google Sheets
https://www.googleapis.com/auth/chat                 # Google Chat
```

## Obtaining Fresh Access/Refresh Tokens

### Step 1: Build Authorization URL

```python
client_id = "313611152308-epldc78dvcp55q0n4tfg7lt6tsanalhb.apps.googleusercontent.com"
redirect_uri = "http://localhost:8080"
scopes = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/chat',
]
scope_str = "+".join(scopes)

oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope_str}&access_type=offline&prompt=consent"
```

### Step 2: User Authorizes

Open `oauth_url` in browser. User clicks "Allow" on Google's consent screen. Browser redirects to:
```
http://localhost:8080/?code=4/0AdkVLPxRBUGPEeJmEFX8yf3nTRUg12LX...&scope=...
```

Copy the full URL (particularly the `code=` parameter).

### Step 3: Exchange Code for Tokens

```python
import requests

auth_code = "4/0AdkVLPxRBUGPEeJmEFX8yf3nTRUg12LX..."  # From redirect URL
client_id = "313611152308-epldc78dvcp55q0n4tfg7lt6tsanalhb.apps.googleusercontent.com"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>"
redirect_uri = "http://localhost:8080"

token_url = "https://oauth2.googleapis.com/token"
payload = {
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}

response = requests.post(token_url, data=payload)
tokens = response.json()

# tokens now contains:
# {
#   "access_token": "ya29.a0AT3oNZ9FpKSYWUizDHNay2gtOudOGJU8A2P3SCmW...",
#   "expires_in": 3599,
#   "refresh_token": "1//06guIN_rSub6ACgYIARAAGAYSNwF-L9IrUcAT9ZBmCAfPU5...",
#   "scope": "https://www.googleapis.com/auth/chat https://www.googleapis.com/auth/spreadsheets ...",
#   "token_type": "Bearer"
# }
```

### Step 4: Store in EDITH Vault

```python
import os, json

edith_dir = os.path.expanduser('~/.hermes/.edith')
os.makedirs(edith_dir, exist_ok=True)

vault_file = os.path.join(edith_dir, 'google_oauth_vault')
with open(vault_file, 'w') as f:
    json.dump(tokens, f)

os.chmod(vault_file, 0o600)  # Owner read/write only
```

## Refresh Token Behavior

**Access tokens expire in 3600 seconds (1 hour).** Refresh token is valid for ~6 months (or until revoked by user).

When access token expires, use refresh token to get a new one:

```python
import requests

refresh_token = "1//06guIN_rSub6ACgYIARAAGAYSNwF-L9IrUcAT9ZBmCAfPU5..."
client_id = "313611152308-epldc78dvcp55q0n4tfg7lt6tsanalhb.apps.googleusercontent.com"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>"

token_url = "https://oauth2.googleapis.com/token"
payload = {
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
    'client_id': client_id,
    'client_secret': client_secret,
}

response = requests.post(token_url, data=payload)
new_tokens = response.json()  # Contains new access_token, expires_in, etc.
```

See `google-oauth-refresh` skill for automation details.

## Session History

**Established:** June 8, 2026, 01:35 UTC  
**Status:** Live (all 5 scopes authorized and stored in EDITH vault)  
**Last refresh:** N/A (fresh tokens)
