# OAuth Headless Code Exchange (No Browser, No gcloud)

**Context:** User on Mac, agent on VM. Generate auth link, user clicks it and pastes code back, agent exchanges code for tokens on the VM. Zero terminal commands sent to user, zero gcloud dependency.

## Generate Authorization Link (urllib only, runs on VM)

```python
import urllib.parse

client_id = "313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com"
redirect_uri = "http://localhost"

# Request all scopes upfront to avoid re-auth later
scopes = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

auth_link = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={client_id}&"
    f"redirect_uri={redirect_uri}&"
    "response_type=code&"
    f"scope={urllib.parse.quote(' '.join(scopes))}&"
    "access_type=offline&"
    "prompt=consent"
)

print("Click this link:")
print(auth_link)
```

**Output:** A URL the user pastes into their browser. They sign in, Google shows an authorization page, they click "Allow", and the browser redirects to:

```
http://localhost/?iss=https://accounts.google.com&code=4/0AdkVLPwahsOq7AJWvaxWueWnHW45T4asAsT4fZjQaSAAvsfXR08FxiCC90T66ej6sOIkyQ&scope=https://www.googleapis.com/auth/gmail.modify ...
```

**Extract the code:** Everything after `code=` and before the next `&`. User copies it back and pastes it into your prompt.

## Exchange Code for Tokens (urllib only, runs on VM)

```python
import urllib.request, urllib.parse, json

auth_code = "4/0AdkVLPwahsOq7AJWvaxWueWnHW45T4asAsT4fZjQaSAAvsfXR08FxiCC90T66ej6sOIkyQ"

client_id = "313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET — see ~/.hermes/google_token.json>"
redirect_uri = "http://localhost"

token_url = "https://oauth2.googleapis.com/token"
data = urllib.parse.urlencode({
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}).encode('utf-8')

req = urllib.request.Request(token_url, data=data)
with urllib.request.urlopen(req) as resp:
    tokens = json.loads(resp.read())

# Save to ~/.hermes/google_oauth_full.json
config = {
    'client_id': client_id,
    'client_secret': client_secret,
    'access_token': tokens['access_token'],
    'refresh_token': tokens['refresh_token'],
    'expires_in': tokens['expires_in'],
    'scopes': 'gmail.modify gmail.readonly gmail.send gmail.labels calendar drive documents spreadsheets'
}

import os
config_path = os.path.expanduser('~/.hermes/google_oauth_full.json')
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Tokens stored")
```

## Key Differences from Browser Flow

| Aspect | Headless | Browser Flow |
|--------|----------|--------------|
| User opens browser | Manual (click link we generate) | Auto-launched by `InstalledAppFlow.run_local_server()` |
| Redirect URI | http://localhost (but no server listening) | http://localhost:xxxx (local server catches it) |
| Code extraction | User copies from URL bar manually | Automatically extracted from redirect |
| Dependencies | urllib only (zero external libs) | google-auth-oauthlib, google-auth |
| VM/user separation | Clean — user clicks URL, pastes code | Blurs the line (if running on user's Mac works, but not on VM for a headless user) |

## When to Use This Pattern

✅ Agent is on VM, user is on different machine (normal Hermes case)
✅ Need to avoid any terminal commands sent to user
✅ Credentials need to be stored on agent's machine (not user's)
✅ One-time OAuth setup that survives account migrations

❌ User has local server running and can intercept redirects themselves (use browser flow instead)
❌ Testing OAuth client library behavior locally

## Session Record (Jun 8, 2026)

- **User:** Tanzim (tanzimozer@gmail.com)
- **Project:** job-scraping-494906
- **Initial error:** `invalid_scope` on authorization (scope "documents" was typo'd as "docs")
- **Scopes on consent screen:** Added all 8 upfront to avoid re-auth
- **Test user:** Added tanzimozer@gmail.com to consent screen
- **Result:** Full permanent Gmail access with refresh token, multi-location storage
- **Follow-up:** Used this token for 179-email cleanup in same session (no re-auth needed)
