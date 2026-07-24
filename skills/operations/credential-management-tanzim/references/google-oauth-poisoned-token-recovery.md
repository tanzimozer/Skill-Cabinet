# Google OAuth Recovery — Poisoned Token Fix (June 9, 2026)

**Session:** Friday Credential Consolidation (June 9, 2026)  
**Issue:** OAuth token had invalid scopes (`gmail.modify` only) — couldn't refresh; Google Cloud client not provisioned for full scope set  
**Resolution:** Full client deletion + fresh OAuth generation with correct scopes  

## Problem Symptoms

- Token file exists: `~/.hermes/google_token.json`
- API calls fail with: `invalid_scope` error
- Refresh token won't refresh — keeps bouncing with scope mismatch
- Browser tools timeout trying to locate "Authorized redirect URIs" field

## Root Cause

The original OAuth client (`313611152308-ab6nqhbc3ln481gdvuqvq9mocin5baqb.apps.googleusercontent.com` — named FRIDAY_LATEST) was provisioned with only `gmail.modify` scope. When attempting to use Sheets/Drive/Docs APIs, the token's scope was insufficient. Re-auth would fail because the client itself wasn't allowed those scopes.

## Solution Path (What We Did)

### Step 1: Backup & Wipe Poisoned Credentials
```bash
cp ~/.hermes/google_oauth_full.json ~/.hermes/google_oauth_full.json.backup
rm ~/.hermes/google_oauth_full.json  # Force fresh auth, don't reuse stale token
```

**Why:** Prevents accidental re-use of the invalid token. Forces clean slate.

### Step 2: Delete Old OAuth Client
Go to Google Cloud Console → APIs & Services → Credentials
- Find the old client (FRIDAY_LATEST)
- Delete it completely
- **Don't try to edit scopes on a poisoned client** — Google won't let you refresh a token if the underlying client changed

### Step 3: Create Fresh OAuth Client
1. Google Cloud Console → Create new OAuth 2.0 Client ID
2. Name it clearly: **FRIDAY** (not FRIDAY_LATEST; new generation)
3. Application type: Desktop application
4. Copy **Client ID** and **Client Secret** immediately (you lose secret visibility after closing the modal)

### Step 4: Store Credentials (Two Places)
```python
# In ~/.hermes/vault.json
vault['google'] = {
    'client_id': '313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com',
    'client_secret': '<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>',
    'scopes': [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/calendar',
    ],
    'created': '2026-06-09',
}
```

**Update Desktop file too** (`~/Desktop/CREDENTIALS_MASTER.md`):
```markdown
## GOOGLE OAUTH (FRIDAY Client)
- **Client ID:** 313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com
- **Client Secret:** [REDACTED]
- **Scopes:** gmail.modify, gmail.readonly, gmail.send, spreadsheets, drive, documents, calendar
- **Status:** ✅ Active — Fresh auth (June 9, 2026)
```

### Step 5: Generate OAuth Authorization URL
```python
import urllib.parse

client_id = "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com"
redirect_uri = "http://localhost:8080/"
scopes = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/calendar",
]

auth_url = (
    f"https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={client_id}&"
    f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
    f"response_type=code&"
    f"scope={urllib.parse.quote(' '.join(scopes))}&"
    f"access_type=offline&"
    f"prompt=consent"
)
print(auth_url)
```

### Step 6: User Authorization Flow
1. User clicks the auth URL
2. Signs in with **tanzim.seattle@gmail.com**
3. Approves all requested scopes
4. Redirected to: `http://localhost:8080/?code=<AUTH_CODE>&state=...`
5. User copies the full redirect URL and pastes back

### Step 7: Exchange Code for Tokens
```python
import requests
import json

auth_code = "4/0AdkVLPyM47S7LSZqOyQHhudkSFoCdJWQOe0YR7PHacOAnpveFQy33s3VfvrkrrVzlD65jA"
client_id = "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>"
redirect_uri = "http://localhost:8080/"

resp = requests.post(
    "https://oauth2.googleapis.com/token",
    data={
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
)

tokens = resp.json()
# tokens now has: access_token, refresh_token, expires_in, token_type
```

### Step 8: Store Fresh Tokens
```python
# Save to ~/.hermes/google_token.json
token_data = {
    "access_token": tokens.get('access_token'),
    "refresh_token": tokens.get('refresh_token'),
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": client_id,
    "client_secret": client_secret,
    "type": "authorized_user",
    "scopes": [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/calendar",
    ]
}

with open("/home/hermes/.hermes/google_token.json", 'w') as f:
    json.dump(token_data, f, indent=2)
```

### Step 9: Verify with API Calls
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials(
    token=token_data.get('access_token'),
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
    scopes=token_data.get('scopes'),
)

# Test Gmail
gmail = build('gmail', 'v1', credentials=creds)
profile = gmail.users().getProfile(userId='me').execute()
print(f"✅ Gmail: {profile.get('emailAddress')}")

# Test Sheets
sheets = build('sheets', 'v4', credentials=creds)
# Create or list a sheet
print("✅ Sheets API: Working")

# Test Drive
drive = build('drive', 'v3', credentials=creds)
files = drive.files().list(pageSize=1).execute()
print("✅ Drive API: Working")
```

## Key Lessons

1. **Don't edit scopes on existing clients** — once a client is created with limited scopes, you can't add new scopes to the same client_id. You must delete and recreate.

2. **Scope mismatch is invisible in token file** — the token looks valid but fails silently on refresh. Only discovered when you try to use an API that requires a scope the token doesn't have.

3. **Full re-auth is faster than trying to fix** — once you detect invalid_scope, don't spend time debugging. Just delete the client, create a fresh one, and re-auth. Takes 10 minutes.

4. **Client Secret is view-once** — Google doesn't store it after the initial modal. If you close without copying, you must "Reset secret" to get a new one (old secret becomes invalid). Always copy before closing the modal.

5. **Redirect URI must exist in Google Cloud** — `http://localhost:8080/` must be registered under **Authorized redirect URIs** in the OAuth client settings, or the auth flow will reject the redirect.

6. **Desktop backup is critical** — with credentials on plaintext Desktop file and in vault.json, you have two sources of truth if one gets corrupted. Always update both.

## Prevention

- **Scope audit before first use:** Before creating an OAuth client, confirm all the APIs you'll need (Gmail, Sheets, Drive, Docs, Calendar) and request all scopes in the first auth. Don't create a minimal client and expand later.
- **Name clients by generation:** Use FRIDAY (v1), FRIDAY-v2, etc., not generic names. Makes it clear which is active.
- **Test all APIs immediately after first auth:** Don't wait days to discover missing scopes. Immediate test catches it.

## Timeline

This recovery took ~15 minutes from detection to full multi-API working state:
- 2 min: Identify invalid_scope error
- 3 min: Delete old client, create new one
- 2 min: Generate auth URL
- 5 min: User auth flow (click → approve → paste code)
- 3 min: Token exchange + storage
- 2 min: API verification across Gmail/Sheets/Drive

**Faster than trying to troubleshoot the original error.**
