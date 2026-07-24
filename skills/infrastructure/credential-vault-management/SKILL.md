---
name: credential-vault-management
category: infrastructure
description: Secure credential storage, OAuth token exchange, and EDITH vault patterns for multi-service authentication
---

## Overview

Tanzim's credential strategy uses **EDITH** — an obfuscated, semantically-misdirected credential vault stored at `~/.hermes/.edith/` with file-level access controls (600 permissions, owner read/write only). This skill captures the patterns for:

1. **OAuth token exchange** (converting auth codes to access/refresh token pairs)
2. **EDITH vault storage** (encrypted, obfuscated naming, verification-gated access)
3. **Multi-service credential consolidation** (Google OAuth for Gmail, Drive, Docs, Sheets, Chat; GitHub PAT; etc.)
4. **Verification protocol** (3-question identity checks before vault access)

## EDITH Vault Architecture

### Naming & Obfuscation Strategy

**EDITH** stands for "Encrypted Distributed Identity Token Handler" but is designed to:
- Sound like a legitimate system config or username
- Defeat keyword-based filesystem enumeration attacks ("secret", "vault", "credential", "key" won't find it)
- Distribute challenge factors across multiple filesystem paths (no single "vault" file)

**File structure:**
```
~/.hermes/.edith/
├── google_oauth_vault          # Google OAuth tokens (Gmail, Drive, Docs, Sheets, Chat)
├── github_pat_vault            # GitHub Personal Access Token
├── [other_service]_vault       # Per-service token files
└── verification_index          # Hashed verification answers (NOT plaintext)
```

### Access Control & Encryption

**Permissions:**
- 600 (owner read/write only) on all vault files
- Never world-readable, never group-accessible

**Storage format (current):**
```json
{
  "service": "google_oauth",
  "scopes": ["gmail", "drive", "docs", "sheets", "chat"],
  "access_token": "ya29.a0AT3oNZ...",
  "refresh_token": "1//06guIN_rSub6ACgYI...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Future enhancement:** Wrap in AES-256-GCM encryption as per EDITH architecture spec (`/home/hermes/EDITH_VAULT_ARCHITECTURE.md`).

### Verification Protocol

**Three unconventional questions** (user-provided, hashed separately, never stored plaintext):
1. Favourite football team?
2. Favourite character?
3. Favourite person?

**Verification flow:**
1. User answers the three questions
2. Responses are hashed (SHA-256 or similar)
3. Hashes stored in `~/.hermes/.edith/verification_index`
4. On vault access, hash user's answers and compare
5. All three must match; failure denies access completely

**Implementation note:** Verification answers are stored separately from the vault itself, never in the same plaintext file. Use constant-time comparison to prevent timing attacks.

## OAuth Token Exchange Pattern

### Google OAuth (Multi-Scopes)

**Scopes for Friday's integrated services:**
```
https://www.googleapis.com/auth/gmail.modify       # Gmail (read, send, modify)
https://www.googleapis.com/auth/drive              # Google Drive (full access)
https://www.googleapis.com/auth/documents          # Google Docs
https://www.googleapis.com/auth/spreadsheets       # Google Sheets
https://www.googleapis.com/auth/chat               # Google Chat
```

**Exchange workflow:**

1. **Build OAuth URL** (no JSON dependency, fresh each time):
   ```python
   client_id = "313611152308-epldc78dvcp55q0n4tfg7lt6tsanalhb.apps.googleusercontent.com"
   redirect_uri = "http://localhost:8080"
   scope_str = "+".join(scopes)
   oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope_str}&access_type=offline&prompt=consent"
   ```

2. **User authorizes** and returns redirect URL with auth code:
   ```
   http://localhost:8080/?code=4/0AdkVLPxRBUGPEeJmEFX8yf3nTRUg12LX...&scope=...
   ```

3. **Exchange code for tokens:**
   ```python
   import requests
   
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
   ```

4. **Store in EDITH vault:**
   ```python
   edith_dir = os.path.expanduser('~/.hermes/.edith')
   os.makedirs(edith_dir, exist_ok=True)
   
   vault_file = os.path.join(edith_dir, 'google_oauth_vault')
   with open(vault_file, 'w') as f:
       json.dump(tokens, f)
   os.chmod(vault_file, 0o600)
   ```

**Key point:** Once stored, never ask the user for OAuth credentials again. Refresh token handles re-authentication automatically (see `google-oauth-refresh` skill).

## GitHub PAT Storage & Retrieval

**Pattern:** Store GitHub PAT in EDITH the same way as Google OAuth tokens.

**Pitfall (encountered June 8, 2026):** 
- Obtained GitHub PAT from user
- Attempted to push to non-existent repo
- Push failed with "Repository not found"

**Lesson:** Before pushing code to a GitHub repo, verify the repo exists first. Can't push to a repo that hasn't been created yet. Either:
1. User creates the repo manually on GitHub first, then push succeeds
2. Use GitHub API (authenticated with PAT) to create the repo programmatically, then push

## Credential Routing & Silent Usage

**Design principle:** Store once, never ask again.

**Resourcefulness principle:** Before asking the user for clarification on which sheet/service/credential to use, exhaust diagnostic tooling:
- Scan local credential files (EDITH, vault.json, env vars, Drive API token cache)
- Run token validation (refresh, check expiry, verify scopes)
- Use discovery APIs (Drive search, Gmail labels, etc.) to find the resource by keyword
- Only ask for input after diagnostics are complete and ambiguity remains

This keeps the interaction tight and surfaces working paths the user might not have articulated yet.

**Workflow:**
1. User provides credential (OAuth code, PAT, API key) once
2. Agent exchanges / stores in EDITH
3. On future tasks requiring that service, agent:
   - Checks EDITH vault silently
   - Uses token if present and valid
   - Only asks if token is missing or expired (should be rare with refresh tokens)

**Never expose vault internals in group chats or user-facing messages.** The vault and its paths are operational detail; users see only results.

## Implementation Checklist

- [ ] EDITH vault directory exists (`~/.hermes/.edith`)
- [ ] Verification protocol implemented (3-question hash check)
- [ ] Google OAuth scopes match all 5 services (Gmail, Drive, Docs, Sheets, Chat)
- [ ] OAuth exchange tested end-to-end (auth URL → code → token → storage)
- [ ] Vault file permissions set to 600 (owner read/write only)
- [ ] Refresh token strategy documented and tested
- [ ] GitHub PAT stored in EDITH (when available)
- [ ] Credential access is silent (no permission asks after initial storage)
- [ ] Vault paths never exposed in logs or group messages

## Fallback & Recovery Patterns

**See:** 
- `references/edith-vault-access-fallback.md` — Practical fallback pattern when EDITH vault is inaccessible (token encryption, plaintext vault fallback, user prompt chain). Tested June 11, 2026 during GitHub push workflow.
- `references/google-oauth-sheets-discovery-jun12-2026.md` — Google Sheets discovery via Drive API + gspread access pattern, including diagnostic checklist and permission troubleshooting. Discovered June 12, 2026.

## Related Skills

- `google-oauth-refresh` — handling token refresh when access token expires
- `github-connect` — GitHub API operations using stored PAT
- `gmail-automation` — sending/reading email using stored Gmail token
- `integrate-new-service` — pattern for adding a new service to EDITH
