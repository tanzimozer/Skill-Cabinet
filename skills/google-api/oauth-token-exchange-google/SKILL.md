---
name: oauth-token-exchange-google
type: workflow
triggers:
  - User provides OAuth auth code
  - Need to exchange code for access/refresh tokens
  - Multi-scope OAuth setup (incrementally add scopes)
description: |
  Workflow for exchanging Google OAuth authorization codes for access tokens and refresh tokens.
  Handles scope expansion, token storage, and immediate API access. Optimized for time-constrained
  environments where immediate API calls follow token acquisition.
---

## Phase 1: Generate Authorization Link

**Input:** 
- client_id
- client_secret  
- redirect_uri (typically http://localhost for desktop app)
- scopes (as list: ['gmail.readonly', 'spreadsheets', ...])

**Action:** Build OAuth URL with scopes formatted as space-separated string.

```python
scopes_str = ' '.join(scopes)  # NOT comma-separated
auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes_str}&access_type=offline"
```

**Key pitfall:** 'documents' scope is NOT 'docs'. The correct scope string is 'https://www.googleapis.com/auth/documents' for Google Docs, or leave it out if target is Sheets only.

**Common scopes:**
- `https://www.googleapis.com/auth/gmail.readonly` — read Gmail only
- `https://www.googleapis.com/auth/gmail.modify` — full Gmail (read, write, delete)
- `https://www.googleapis.com/auth/spreadsheets` — Google Sheets API
- `https://www.googleapis.com/auth/drive` — Google Drive (broad; use cautiously)

## Phase 2: User Authorizes & Provides Code

**User action:** Opens the auth URL in browser, grants permissions, copies the returned authorization code from the redirect URL (or prompt).

**Your role:** Wait for the code. When received, do NOT delay.

## Phase 3: Exchange Code for Tokens

**Input:**
- auth_code (from user)
- client_id
- client_secret
- redirect_uri (must match the auth URL)

**Action:** POST to Google's token endpoint.

```python
import urllib.request
import urllib.parse
import json

token_url = "https://oauth2.googleapis.com/token"
data = urllib.parse.urlencode({
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}).encode('utf-8')

req = urllib.request.Request(token_url, data=data, method='POST')
response = urllib.request.urlopen(req)
tokens = json.loads(response.read())

access_token = tokens['access_token']
refresh_token = tokens.get('refresh_token')  # May be present on first exchange
expires_in = tokens.get('expires_in', 3600)
```

**Output:** access_token, refresh_token (if present), expires_in (seconds).

**Key detail:** refresh_token is only returned on the FIRST exchange for a given code. Subsequent authorization requests for the same scope won't return a new refresh_token — reuse the old one.

## Phase 4: Store Tokens Durably

**Location:** `~/.hermes/google_oauth_full.json` (or user-specified path).

**Format:**
```json
{
  "client_id": "...",
  "client_secret": "...",
  "redirect_uri": "http://localhost",
  "access_token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0...",
  "expires_at": 1234567890,
  "scopes": ["gmail.modify", "spreadsheets"]
}
```

**Why:** Allows future sessions to reuse tokens without re-authorizing. Store immediately after exchange.

## Phase 5: Immediate API Access

**After token storage:** Do NOT wait or re-confirm. Proceed directly to the API call using the fresh access_token.

**Pattern:**
```python
# Load stored tokens
with open(os.path.expanduser('~/.hermes/google_oauth_full.json')) as f:
    config = json.load(f)
access_token = config['access_token']

# Use it immediately
headers = {'Authorization': f'Bearer {access_token}'}
# ... make API request
```

## Scope Expansion (Incremental Authorization)

**Scenario:** User started with gmail.readonly, now needs spreadsheets too.

**Approach:** Generate a NEW auth URL with the **combined** scopes (all old + new), get user to re-authorize, exchange code for tokens.

**Key:** The new token will have both scopes. **Do NOT** try to merge tokens or make separate requests with different tokens — one token, all scopes.

**Process:**
1. Generate auth URL with scopes: ['gmail.modify', 'spreadsheets']
2. User authorizes (they'll see both permissions requested)
3. Exchange code for combined access_token + refresh_token
4. Store both tokens (refresh_token overwrites old one if provided)
5. Now token has access to both Gmail and Sheets

**Pitfall:** Trying to use two separate tokens for two different scopes. Google OAuth returns ONE token per authorization. If you need multiple scopes, request them all at once.

## Time-Constrained Scenario (Immediate API Call Needed)

**Signal:** User has a deadline (e.g., interview prep, urgent lookup).

**Approach:**
1. Generate auth URL (instant)
2. User authorizes (their time)
3. Exchange code → store tokens (instant, <1 sec)
4. Query API immediately (no preamble, no confirmation, just do it)
5. Report result inline with next action

**Pattern:** "Got the token. Querying Sheets now for Fluxx Labs row..." (already executing, not asking permission).

## Troubleshooting

**"Invalid auth code" or "code already used":**
- Auth codes are single-use and expire in ~10 minutes.
- User must provide a fresh code if the exchange fails.
- Re-do Phase 1 (generate fresh auth URL) and ask user to re-authorize.

**"Invalid scope":**
- Scope string is malformed or not URL-encoded.
- Verify scopes are space-separated and use full `https://...` URIs.
- Check Google API documentation for the exact scope string for the API you're calling.

**"redirect_uri_mismatch":**
- The redirect_uri in the token request must EXACTLY match the auth URL.
- Both must match the URI registered in Google Cloud Console.
- Typical value: `http://localhost` (not http://localhost:80, not http://localhost/)

**Token expired, but you have refresh_token:**
- Use refresh_token to get a new access_token without re-authorizing.
```python
data = urllib.parse.urlencode({
    'refresh_token': refresh_token,
    'client_id': client_id,
    'client_secret': client_secret,
    'grant_type': 'refresh_token'
}).encode('utf-8')
# POST to token_url, extract new access_token
```

## References
- See `references/google-scopes.md` for complete scope list.
- See `references/session-example.md` for a worked example from a time-constrained scenario.
