# Google OAuth Client Blocking — Pitfall & Recovery

**Session:** June 16, 2026  
**Context:** User attempted OAuth auth with FRIDAY client (`313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com`). All redirect URIs (localhost, OOB) returned HTTP 400 `invalid_request` with message "app doesn't comply with OAuth policy."

## Problem

Google blocks OAuth clients that:
- Accumulate repeated failed auth attempts
- Have exposed secrets (leaked in logs, GitHub, or Slack)
- Use mismatched redirect URIs
- Created in deprecated/old projects
- Age: old clients created before Google OAuth 2.0 policy updates

When blocked, **all redirect URIs fail** — even if the credential config is technically correct.

## Symptoms

```
HTTP 400 Bad Request
{
  "error": "invalid_request",
  "error_description": "..."
}

Page: "Authorization Error — You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy..."
```

Appears even with:
- Valid client ID/secret
- Correct scopes
- Both localhost and OOB redirect URIs
- Multiple attempts at approval

## Solution — Credential Fallback Cascade

**DO NOT** immediately ask user to create a new project. **FIRST** exhaust credential lookups:

### Step 1: Lookup Existing OAuth Clients
Before suggesting fresh generation, search disk for alternative OAuth clients already configured:

```bash
find ~ -name "*oauth*client*" -o -name "*credentials*.json" 2>/dev/null
# Typical locations:
# ~/.hermes/google_oauth_client.json
# ~/Desktop/credentials.json
# ~/Desktop/CREDENTIALS_MASTER.md (reference file listing all clients)
```

### Step 2: Try Alternative Client
If multiple clients exist on disk, try the next one:
- Update client_id and client_secret in auth request
- Use **out-of-band redirect** (`urn:ietf:wg:oauth:2.0:oob`) — avoids localhost issues
- Attempt auth flow again

Example:
```python
# Try second client from disk
alt_client_id = "313611152308-epldc78dvcp55q0n4tfg7lt6tsanalhb.apps.googleusercontent.com"
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # Out-of-band, not localhost

auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={alt_client_id}&redirect_uri={redirect_uri}&..."
```

### Step 3: Fresh Project (Last Resort)
Only if:
- All disk-stored clients are blocked
- User confirms OK to create new project

Steps:
1. User creates new Google Cloud project at https://console.cloud.google.com/projectcreate
2. Enable Gmail, Drive, Sheets, Calendar, Docs APIs
3. Create OAuth 2.0 Client ID (Desktop application)
4. Download JSON and extract client_id/secret
5. User pastes credentials back
6. Test immediately with single API call before adding full scope set

## Prevention

- **Store multiple OAuth clients** in `~/Desktop/CREDENTIALS_MASTER.md` so if one gets blocked, fallback is available
- **Keep backup OAuth client** in `~/.hermes/google_oauth_client.json` for fallback scenarios
- **Never commit OAuth credentials** to GitHub or public repos
- **Use OOB redirect** for all new OAuth clients to avoid "invalid_request" policy issues
- **Test token refresh immediately** after generation to catch revoked tokens early

## Key Insight

Google OAuth blocking is **irreversible for a given client** — you cannot "unblock" a blocked client. The only remedy is:
1. Try a different valid client (if available)
2. Create a new one in a new project

Blocking typically occurs after 3-5 consecutive failed auth attempts or secret exposure. **Defensive approach:** keep 2-3 valid OAuth clients on disk at all times.
