# Google OAuth Error Handling & Fixes

## Error: "invalid_request" / "App doesn't comply with OAuth 2.0 policy"

**Root cause:** Redirect URI `http://localhost:8080/` triggers Google's native app validation on some client IDs.

**Fix:** Use out-of-band redirect instead:
```
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
```

This tells Google to display the authorization code on-screen instead of redirecting, avoiding the localhost validation error.

### Code Pattern (Out-of-Band Flow)

```python
import urllib.parse

client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # KEY CHANGE
scopes = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
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

**User flow:**
1. Click auth URL
2. Google shows authorization code on screen (e.g., `4/0AY0e-...`)
3. User copies and pastes the code back
4. Agent exchanges code for access/refresh tokens

## Error: "Token has been expired or revoked"

**Root cause:** Refresh token is stale (> 6 months since last use) or was explicitly revoked.

**Fix:**
1. Check EDITH vault for any existing valid tokens
2. If vault is empty or has test data, generate fresh OAuth credentials via out-of-band flow above
3. Store new tokens in both EDITH vault and `~/.hermes/google_token.json`

## Token Exchange (After Getting Code)

Once user provides authorization code:

```python
import json
import urllib.request
import urllib.parse

client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
auth_code = "4/0AY0e-..."  # User-provided code from above
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

token_url = "https://oauth2.googleapis.com/token"
payload = {
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}

data = urllib.parse.urlencode(payload).encode('utf-8')
req = urllib.request.Request(token_url, data=data, method='POST')

with urllib.request.urlopen(req) as response:
    token_response = json.loads(response.read().decode())

print(f"Access Token: {token_response['access_token'][:20]}...")
print(f"Refresh Token: {token_response['refresh_token'][:20]}...")
print(f"Expires in: {token_response['expires_in']} seconds")

# Store in ~/.hermes/google_token.json
with open(os.path.expanduser('~/.hermes/google_token.json'), 'w') as f:
    json.dump(token_response, f, indent=2)
```

## Reference

- Google OAuth 2.0 Out-of-Band Flow: https://developers.google.com/identity/protocols/oauth2/native-app
- Troubleshoot OAuth errors: https://developers.google.com/identity/protocols/oauth2/troubleshooting
