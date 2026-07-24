# Google OAuth Scope Troubleshooting

## The Problem: invalid_scope Error

When making a Google API call, you get:
```
google.auth.exceptions.RefreshError: ('invalid_scope: Bad Request', {'error': 'invalid_scope', 'error_description': 'Bad Request'})
```

**Root cause:** The credentials file contains scope requests that the OAuth client_id was NOT provisioned for. Refreshing the token does NOT fix this — scope validation happens at token refresh time, not at API call time.

## Diagnosis

### Step 1: Locate all token files
```bash
ls -la ~/.hermes/google_token.json
ls -la ~/.hermes/google_oauth_full.json
cat ~/.hermes/vault.json | grep -A5 '"google"'
```

### Step 2: Check which scopes are declared
Look at the `scopes` array in each file:

**Good (google_token.json):**
```json
{
  "scopes": [
    "https://www.googleapis.com/auth/gmail.modify"
  ]
}
```

**Bad (google_oauth_full.json or vault.json):**
```json
{
  "scopes": [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",  // ← not authorized on client_id
    "https://www.googleapis.com/auth/drive"          // ← not authorized on client_id
  ]
}
```

### Step 3: Check what the client_id actually supports

Go to Google Cloud Console:
1. Project: job-scraping-494906
2. APIs & Services → Credentials
3. Click the OAuth 2.0 Client ID
4. Note the creation date and any recent changes
5. Check the **configured scopes** in the client settings (not the token file — the actual client configuration)

## The Fix

### Option A: Use the correct token file
If you have a working token file (e.g., `google_token.json` with `gmail.modify` only), use THAT file and load it as the credential source:

```python
from google.oauth2.credentials import Credentials
import json

with open('/home/hermes/.hermes/google_token.json') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data.get('access_token'),
    refresh_token=token_data.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
    scopes=token_data.get('scopes'),  # This must match client_id authorization
)
```

**Do NOT override the scopes — use what's in the file.**

### Option B: Re-authenticate with the correct scope set
If you need broader scopes (Sheets, Drive, Docs, Calendar), you must:

1. **Delete the poisoned token file:**
   ```bash
   rm ~/.hermes/google_oauth_full.json
   ```

2. **Configure the OAuth client with ALL needed scopes** in Google Cloud Console (if not already done)

3. **Run fresh OAuth flow** with correct scopes:
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow
   
   SCOPES = [
       'https://www.googleapis.com/auth/gmail.modify',
       'https://www.googleapis.com/auth/spreadsheets',
       'https://www.googleapis.com/auth/drive',
       'https://www.googleapis.com/auth/documents',
       'https://www.googleapis.com/auth/calendar',
   ]
   
   flow = InstalledAppFlow.from_client_secrets_file(
       'client_secret.json', SCOPES)
   creds = flow.run_local_server(port=8080)
   
   # Save to file
   import json
   with open('google_token.json', 'w') as f:
       json.dump({
           'access_token': creds.token,
           'refresh_token': creds.refresh_token,
           'token_uri': creds.token_uri,
           'client_id': creds.client_id,
           'client_secret': creds.client_secret,
           'scopes': SCOPES,
       }, f)
   ```

4. **Ensure the OAuth client's redirect URI includes `http://localhost:8080/`** (Google Cloud Console → Credentials → OAuth 2.0 Client ID → Authorized redirect URIs)

## Token File Precedence (Tanzim's system)

When multiple token files exist, use this precedence:
1. `~/.hermes/google_token.json` — primary, trusted source (used in this session)
2. `~/.hermes/google_oauth_full.json` — legacy/poisoned (avoid unless verified)
3. `~/.hermes/vault.json` → `google.token_file` — points to #1
4. `~/.hermes/.edith/edith_vault.json` — encrypted backup (requires EDITH passphrase)

## Prevention

- **Always check scopes before API calls:** Print `creds.scopes` and verify they match the client_id
- **One token file per client_id:** Don't mix credentials from different OAuth clients
- **Re-auth when adding services:** If you need a new scope, delete the old token and start fresh — don't try to patch the scopes array
- **Keep vault.json scopes in sync:** If vault.json lists broader scopes, ensure the actual token file supports them

## Historical Pattern (Tanzim's system)

This has happened before (Jan 2026 with Scale credentials). The pattern:
1. OAuth client created with limited scopes (gmail.readonly)
2. Credentials file updated to request broader scopes (spreadsheets, gmail.modify)
3. Mismatch discovered during API call
4. Retrying doesn't help — scope validation pre-auth

**Lesson:** Scope decisions should be made BEFORE you create the token, not after.
