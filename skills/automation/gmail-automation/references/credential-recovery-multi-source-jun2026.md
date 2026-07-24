# Credential Recovery: Multi-Source Lookup (Jun 2026)

## Context
Tanzim has fragmented OAuth credentials across multiple locations and OAuth clients in Google Cloud Console. When Gmail operations fail with `invalid_client`, `unauthorized_client`, or `deleted_client`, the token file itself may be correct but pointing to a stale or revoked OAuth app.

**Session fact (Jun 2026):** Multiple OAuth clients exist:
- `friday-499707` (June 17, created but later unauthorized)
- `friday-mark-2-499708` (June 17, working)
- `job-scraping-494906` (older, may have legacy tokens)

## Recovery Workflow

### Step 1: Identify the Current Credential State
Check in this order:

1. **~/.hermes/google_token.json** (primary token file)
   - Contains: `access_token`, `refresh_token`, sometimes `client_id`/`client_secret`
   - If `client_id`/`client_secret` are missing → go to Step 2

2. **~/Desktop/CREDENTIALS_MASTER.md** (Tanzim's master list)
   - Last updated: Jun 9, 2026
   - Lists: active Google OAuth (FRIDAY), GitHub PAT, Canva, etc.
   - If outdated, check document cache

3. **Document cache / Recently received files**
   - Tanzim sends OAuth client_secret files directly when setting up new clients
   - Check `/home/hermes/.hermes/document_cache/` for recent `client_secret_*.json` files
   - Pattern: `client_secret_<N>_<CLIENT_ID>.apps.googleusercontent.com.json`
   - **Last known working:** `client_secret_2_990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com.json` (friday-mark-2-499708 project)

4. **~/friday_backup/google_client_secret.json** (fallback backup)
   - Older FRIDAY client from June 9, 2026
   - May be stale but useful for fallback reference

### Step 2: When Refresh Fails with `invalid_client` / `unauthorized_client`

**The stale token problem:**
- The `refresh_token` in `~/.hermes/google_token.json` was issued under a previous OAuth app ID
- That OAuth app has been deleted or revoked in Google Cloud Console
- Google rejects the refresh because the client_id/secret pair is no longer valid

**Recovery steps:**
1. Extract the `refresh_token` from `~/.hermes/google_token.json`
2. Find the **newest** OAuth client credentials from the document cache (by file modification time)
3. Extract `client_id`, `client_secret` from that file
4. Attempt token refresh with the new credentials and the old refresh_token
5. If refresh succeeds → write the merged token file with the new client credentials (see "Token File Merge" below)
6. If refresh fails → the refresh_token itself is stale; Tanzim needs to re-authorize (see "Full Re-auth")

### Step 3: Token File Merge (When Recovery Succeeds)

When you have a valid refresh_token but missing/stale client credentials:

```python
import json
import subprocess

# Load current token file
result = subprocess.run(['cat', '/home/hermes/.hermes/google_token.json'], capture_output=True, text=True)
current_token = json.loads(result.stdout)

# Load new client credentials (from document cache or backup)
# Example: client_secret_2_990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com.json
with open('/path/to/client_secret_2.json') as f:
    client_data = json.load(f)
    client_info = client_data.get('installed') or client_data.get('web') or client_data

# Merge: preserve existing tokens, add new client credentials
merged = {
    'access_token': current_token['access_token'],
    'refresh_token': current_token['refresh_token'],
    'expires_in': current_token.get('expires_in', 3600),
    'token_type': current_token.get('token_type', 'Bearer'),
    'scope': current_token.get('scope', ''),
    'client_id': client_info['client_id'],
    'client_secret': client_info['client_secret'],
    'token_uri': client_info['token_uri'],
    'type': 'authorized_user'
}

# Write back
with open('/home/hermes/.hermes/google_token.json', 'w') as f:
    json.dump(merged, f, indent=2)

print("Token file merged with new client credentials")
```

### Step 4: Full Re-auth (When Refresh Token is Stale)

If the refresh_token itself is no longer valid (Google returns `invalid_grant` or similar after Step 2 attempt), the token was revoked or expired. Tanzim must re-authorize from scratch:

1. Identify the latest OAuth client in Google Cloud Console (or ask Tanzim to create one)
2. Generate authorization link with all required scopes (gmail.modify, gmail.readonly, gmail.send, gmail.labels, calendar, drive, documents, spreadsheets)
3. Tanzim clicks, approves, provides authorization code
4. Exchange code for new access_token + refresh_token
5. Store in `~/.hermes/google_token.json` with all fields populated

See `references/oauth-full-setup-jun8-2026.md` for the full auth flow.

## Session Example: Jun 2026

**Failure sequence:**
1. User requests: "scan my gmail trash for interview calls"
2. Token refresh attempt with `client_id: 768192326455-77dgh26ibi6eraoh5jafen8ukkae1os1` (from stored token) → 401 `unauthorized_client`
3. Agent tries alternate client ID from June 9 backup → 401 `invalid_client`
4. Agent checks document cache → finds `client_secret_2_990922176945-n9132okninl4isc7l7kd3n9345epaiqg...json`
5. Agent merges new client credentials with old refresh_token
6. Token refresh succeeds with **Friday Mark 2** project client
7. Scan executes: 53 interview emails found in trash

**Lesson:** Always check document cache for the most recent OAuth client file before asking user for re-auth. The newest file in that directory is usually the active one.

## Prevention

1. **Credential master file discipline:** Tzanim should update `~/Desktop/CREDENTIALS_MASTER.md` every time a new OAuth client is created. Include:
   - Client ID
   - Project name
   - Date created
   - Status (active/deprecated/revoked)

2. **Single source of truth:** Consolidate onto one working OAuth app in Google Cloud Console. Delete old apps once new ones are verified.

3. **Don't ask first:** If refresh fails, agent should:
   - Check document cache for newer client_secret files
   - Try merge + refresh with newest credentials first
   - Only ask for re-auth if all fallback attempts fail
