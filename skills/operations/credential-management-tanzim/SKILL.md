---
name: credential-management-tanzim
description: Tanzim's preferred workflow for generating, storing, and testing credentials (OAuth, PAT, API keys). Emphasizes plaintext storage on desktop for transparency.
type: operational
scope: |
  OAuth token generation, PAT creation, credential audit, vault management.
  Covers: Google OAuth, GitHub PAT, email/iCloud credentials, credential testing.
triggers:
  - User requests OAuth/PAT access to a service
  - Credential audit needed
  - Token refresh or rotation required
  - "Give me access to X"
---

# Credential Management — Tanzim's Approach

## Core Principle\n**Transparency as SSOT.** ~/Desktop/CREDENTIALS_MASTER.md is the single source of truth for active credentials — not vault, not scattered files. Plaintext, human-readable, directly editable. ~.hermes/vault.json is for Python/code access only; desktop file is the authority when there's conflict.

## Workflow

### Step 1: Audit First — Full Credential Lookup Cascade
When asked for access to a service:
- Scan `~/.hermes/vault.json` for existing credentials
- Check EDITH vault via `from edith import EDITHVault; vault = EDITHVault(require_verification=False); vault.get_credential(service)` — may have working credentials even if stale test data shows
- Search disk for backup files: `~/.hermes/*.json`, `~/Desktop/credentials.json`, `~/.hermes/google_oauth_client.json`, or other OAuth client configs
- Check CREDENTIALS_MASTER.md on Desktop for historic client IDs and token status
- Report what exists, what's missing, what's stale
- Do NOT assume encrypted vaults can be decrypted
- **Only after exhausting all local lookups:** ask user for fresh credential generation

### Step 2: Fresh Credential Generation
If credentials are missing or poisoned:
- **ALWAYS try EDITH vault first** via `from edith import EDITHVault; vault = EDITHVault(require_verification=False)` and `vault.get_credential(service)`
- If EDITH returns stale/test data or KeyError, then proceed to OAuth flow
- Generate new OAuth token or PAT via official service UI (Google Cloud, GitHub, etc.)
- For Google OAuth: use **out-of-band redirect** (`urn:ietf:wg:oauth:2.0:oob`) instead of localhost redirect to avoid "invalid_request" / "app doesn't comply with OAuth policy" errors
- Get the full credential string from user (via paste/image/text or authorization code from Google consent screen)
- Do NOT prompt for passwords/passphrases — Tanzim doesn't use them for local vaults

### Step 3: Storage (Two Places)
1. **Code-accessible:** `~/.hermes/vault.json` (JSON format, for Python/CLI access)
2. **Human-visible:** `~/Desktop/CREDENTIALS_MASTER.md` (Markdown, running log)

Store full credential values in both. Mark secrets as `[REDACTED]` only in shared sheets or public reports.

### Step 4: Test Before Confirming
After storing a credential, test it immediately:
- Google OAuth: Create or list a Sheet
- GitHub PAT: Clone a repo or delete a repo
- Gmail: Send a test email
- Report pass/fail clearly

If it fails, troubleshoot before asking user to re-generate.

### Step 5: Document Expiry
Temporary credentials (admin PATs) get annotated:
- Add `_note: "Expires in X days / manually deleted after use"` in vault.json
- Update Desktop log with expiry date
- Do NOT use after expiry without re-confirmation

## Service-Specific Patterns

### Google OAuth
- **Generation:** User creates client in Google Cloud Console → copy Client ID + Secret
- **Scope negotiation:** Always clarify scope set (gmail, spreadsheets, drive, docs, calendar, etc.)
- **Authorization flow:** Generate auth link → user clicks → approves → pastes redirect URL
- **Token exchange:** Exchange auth code for access + refresh tokens
- **Storage:** Under `google.oauth` in vault.json
- **Test:** Immediate Sheets/Drive/Gmail API call after exchange

### GitHub PAT
- **Generation:** User goes to https://github.com/settings/tokens/new → names token → selects scopes
- **Scope clarity:** Confirm which scopes needed (repo, gist, user for standard; delete:repo for cleanup)
- **Storage:** Full PAT string under `github.pat` in vault.json
- **Test:** Attempt git clone, API call, or repo deletion immediately
- **Expiry:** Document in Desktop file (scopes and expiry date)

### Email / iCloud
- **Storage:** App passwords, NOT main account password
- **Test:** SMTP connection or fetch test before marking active

### Canva API
- **Generation:** User creates integration in Canva Developers console → copy Client ID + Secret
- **Scope negotiation:** Clarify design permissions (read templates, edit, publish, assets?)
- **Storage:** Under `canva` in vault.json with status field (draft/active/approved)
- **Approval:** Requires Canva review before full activation (1-3 business days typical)
- **Progress tracking:** See references/canva-integration-setup.md for current session state

## Anti-patterns (Avoid These)
- ✗ Prompting for EDITH passphrase when user has none set
- ✗ Storing credentials in encrypted vaults user can't decrypt
- ✗ Asking "should I store this?" — just store it after receiving credential
- ✗ Storing partial or masked credentials — always store the full value
- ✗ Generic OAuth client names ("oauth_client_1") — name them after the service (FRIDAY, FRIDAY_LATEST, etc.)
- ✗ Leaving credentials unstored while testing — store first, then test

## Desktop Master File Format

```markdown
# CREDENTIALS MASTER — Running Log
**Created:** June 9, 2026
**Owner:** Tanzim Ozer
**Location:** ~/Desktop/CREDENTIALS_MASTER.md
**Last Updated:** [date/time]

---

## GOOGLE OAUTH
- **Service:** Gmail, Sheets, Drive, Docs, Calendar
- **Client ID:** [full string]
- **Client Secret:** [full string]
- **Refresh Token:** [full string]
- **Scopes:** gmail.modify, gmail.readonly, gmail.send, spreadsheets, drive, documents, calendar
- **Status:** Active
- **Created:** 2026-06-09
- **Expires:** Never (refresh token valid indefinitely)
- **Notes:** Generated for FRIDAY client; tested with Sheets API

## GITHUB PAT
- **Account:** tanzimozer
- **PAT:** [full token string]
- **Scopes:** repo, gist, user
- **Status:** Active
- **Created:** 2026-06-09
- **Expires:** 2027-06-09
- **Notes:** Used for repo CRUD operations
```

## EDITH 2.0 Vault Module

For programmatic credential access in Friday 2.0 core and background jobs, use the EDITH 2.0 Python module (`/home/hermes/edith.py`). This module provides:
- Hardware UUID binding (automatic decryption on correct machine, no passphrase)
- Fernet (AES-256-GCM) encryption per credential
- Obfuscated service names (prevents enumeration attacks)
- 3/3 verification protocol enforcement
- Complete audit logging

**Import:**
```python
from edith import EDITHVault
vault = EDITHVault(require_verification=False)  # for background jobs
creds = vault.get_credential('github')
```

See **references/edith-2.0-python-module.md** for full usage, architecture, and pitfalls.

## Session Reference
## Session Reference
- Credential lookup cascade & disk search workflow (June 16, 2026): see references/credential-lookup-cascade.md
- Google OAuth client blocking detection & recovery (June 16, 2026): see references/google-oauth-client-blocking.md
- Credential management architecture & decision log (June 11, 2026): see references/credential-management-architecture.md
- Daily credential check cron setup (June 11, 2026): see references/daily-credential-check-setup.md
- OAuth Google flow (June 9, 2026): see references/oauth-google-authorization-flow.md
- Google OAuth poisoned token recovery (June 9, 2026): see references/google-oauth-poisoned-token-recovery.md
- Canva integration setup (June 9, 2026): see references/canva-integration-setup.md
- GitHub repo cleanup (June 9, 2026): see references/github-admin-cleanup.md
- GitHub repo creation from loaded docs (June 2026): see references/github-repo-creation-from-docs.md
- Vault.json schema: see references/vault-json-structure.md
- EDITH 2.0 module implementation (June 9, 2026): see references/edith-2.0-python-module.md
- Cryptography patterns (PBKDF2HMAC, Fernet, hardware UUID binding): see references/cryptography-patterns.md
