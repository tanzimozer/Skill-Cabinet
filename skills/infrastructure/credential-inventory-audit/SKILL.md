---
name: credential-inventory-audit
category: infrastructure
description: Comprehensive audit of all credentials, API keys, tokens, and service integrations across the system. Maps what exists, what's missing, what's stale, and what's blocked.
---

# Credential Inventory Audit

## When to Run This

**Triggers (any one warrants a full audit):**
- User asks "what credentials do I have?" or "find everything"
- New service integration planned (need to audit existing before adding)
- Credential access failures (invalid_scope, 401 unauthorized, token expired)
- Credential setup/refresh session starting
- Quarterly/annual credential rotation cycle

**Do NOT run on every small task.** Reserve for setup, troubleshooting, or explicit user request.

## Audit Phases

### Phase 1: Discover All Credential Locations
Scan these locations in order:

| Location | Type | Encryption | Scan Method |
|----------|------|------------|-------------|
| `~/.hermes/vault.json` | Plaintext vault | chmod 600 only | `read_file` + JSON parse |
| `~/.hermes/google_token.json` | Google token | chmod 600 only | `read_file` + JSON parse |
| `~/.hermes/.edith/edith_vault.json` | Encrypted vault | AES-256-GCM (3FA) | `stat` only — don't try to decrypt |
| `~/.hermes/.edith/github_pat_vault` | Encrypted | AES-256-GCM (EDITH) | `stat` only |
| `~/.hermes/.edith/google_oauth_vault` | Encrypted | AES-256-GCM (EDITH) | `stat` only |
| `~/.bashrc`, `~/.zshrc` | Shell config | None | Grep for API_KEY, TOKEN, SECRET patterns |
| `~/.aws/credentials`, `~/.aws/config` | AWS config | None | Check if files exist |
| `~/.ssh/config` | SSH keys | None | Check if files exist |
| Environment vars | In-process | None | Check `os.environ` for credential keywords |

**Key pattern:** Plaintext files are readable. Encrypted EDITH files show only size/date — don't attempt read.

### Phase 2: Map Credential Inventory
For each plaintext credential found, record:
- Service name (Google, GitHub, iCloud, etc.)
- Account/email
- Token location
- Scopes (if OAuth)
- Creation date (if available)
- Status (Active, Stale, Encrypted, Missing)
- Last verified (timestamp or "In vault")

### Phase 3: Identify Gaps
Cross-reference discovered credentials against expected services. Create a "missing" list.

**Canonical service list for Tanzim (as of June 2026):**
1. Google (Gmail, Sheets, Drive, Docs, Calendar) — ✅ Often present
2. iCloud (IMAP access) — ✅ Often present
3. Webflow (site API) — ✅ Often present
4. Wix (TIMBR site) — ✅ Often present
5. Instagram (cookies + session) — ✅ Often present
6. GitHub (PAT for tanzimozer) — ✅ Often encrypted in EDITH
7. WhatsApp (bridge token) — ✅ Often present
8. Anthropic (Claude API) — ✅ Often in env vars
9. Hindsight (memory backend) — ✅ Often in env vars
10. Slack (bot token) — ❌ Rarely present
11. AWS (access keys) — ❌ Rarely present

### Phase 4: Health Check
For each credential:

| Check | Action |
|-------|--------|
| **Expiry** | Is token >1 year old? (GitHub PAT) Approaching 30-day refresh? (Webflow) |
| **Scope mismatch** | Does token have all required scopes? (Google OAuth often poisoned) |
| **Stale** | Last updated >5 days ago? (Instagram cookies expire in 7–14 days) |
| **Encryption** | Is sensitive data in plaintext when it should be encrypted? |
| **Dual storage** | Is same credential in multiple places (vault.json + EDITH)? |

### Phase 5: Output Format
Generate two files:
1. **CREDENTIAL_AUDIT_COMPLETE.md** — Full table, status, actions, timeline
2. **CREDENTIALS_MASTER.md** — Running log of fresh credentials as provided/verified

**Both files live on user's Desktop for easy reference.**

## Common Patterns & Pitfalls

### Pattern: Google OAuth Poisoning
**Symptom:** Token file exists but API calls fail with `invalid_scope: Bad Request`  
**Cause:** Token scopes don't match what client_id was provisioned for  
**Fix:** Create new OAuth client with full scope set; don't try to patch existing token  
**Prevention:** Provision client with full scopes upfront

### Pattern: Stale Instagram Cookies
**Symptom:** Enrich endpoint returns HTML even on status 200 (not JSON)  
**Cause:** Device fingerprint (datr cookie) flagged as spam/rate-limited  
**Fix:** Get fresh cookies from different browser (Firefox, Edge, different Chrome profile)  
**Timeline:** Check every 5–7 days; rotate when blocked

### Pattern: GitHub PAT Age Unknown
**Symptom:** PAT stored in EDITH vault, creation date unclear  
**Cause:** PAT created >1 year ago needs rotation (GitHub best practice)  
**Fix:** Decrypt vault, check GitHub settings, regenerate and update vault if old  
**Timeline:** Verify every 3 months; mandatory refresh at 1-year mark

### Pattern: Multiple Vault Locations
**Symptom:** Same credential in vault.json AND EDITH vault (or plaintext + encrypted)  
**Cause:** Migration incomplete or dual-storage for redundancy  
**Action:** Clarify intent — consolidate if accidental, document if intentional  
**Prevention:** Single source of truth per service

## Workflow: Running an Audit

```python
# Phase 1: Discover
vault_files = [
    '~/.hermes/vault.json',
    '~/.hermes/google_token.json',
    '~/.hermes/.edith/edith_vault.json',
    '~/.hermes/.edith/github_pat_vault',
]
# stat and read_file each

# Phase 2: Map
for cred in discovered:
    record {service, account, location, scopes, status, verified_date}

# Phase 3: Gap Analysis
expected_services = [Google, iCloud, Webflow, Wix, Instagram, GitHub, WhatsApp, Anthropic, Hindsight]
missing = expected_services - discovered

# Phase 4: Health Check
for cred in discovered:
    check expiry, scopes, staleness, encryption, dual_storage

# Phase 5: Output
write CREDENTIAL_AUDIT_COMPLETE.md
write CREDENTIALS_MASTER.md (template for fresh creds)
```

## Verification Pattern: Testing Credential Access

When auditing, go beyond discovery — **test that credentials actually work**. This is the difference between "credential exists" and "credential is usable."

### Testing Strategy

For each discovered credential, run a minimal read or write test:

| Service | Test | Command |
|---------|------|---------|
| **Google OAuth** | List a Sheets or create a Drive file | Use Google Sheets API (list_spreadsheets) |
| **GitHub PAT** | Attempt git clone or user info lookup | `git clone --depth 1 https://github.com/<org>/<repo>` or GitHub API `/user` |
| **iCloud** | IMAP connection test | `python3 -c "import imaplib; imaplib.IMAP4_SSL(...).login(...)"` |
| **Instagram cookies** | Fetch a user profile | Instagram graph endpoint with session cookies |
| **Webflow API** | List sites or fetch site data | Webflow API `/sites` |
| **Wix API** | Get site status | Wix API `/sites` |
| **Canva OAuth** | Verify token type (JWT vs. access_token) | Check token payload structure |

**Output format for testing:**
```
Service: google
Status: ✓ ACCESSIBLE
Test: Sheets API list_spreadsheets()
Result: 5 sheets found
Last verified: 2026-06-11 12:00
```

### Indexing & Access Patterns

When documenting credentials, note **how they are accessed**:

1. **Top-level indexed** (O(1) direct lookup)
   - Example: `vault['google_token_file']` → file path
   - Benefit: Fast, no hierarchy traversal
   - Document: "Accessible via vault[field]"

2. **Nested hierarchical** (O(1) double lookup)
   - Example: `vault['github']['pat']` → credential value
   - Benefit: Organized by service, grouped with metadata
   - Document: "Accessible via vault['service']['field']"

3. **External reference** (pointer + file)
   - Example: `vault['google_token_file']` points to `/path/to/token.json`
   - Benefit: Separates small metadata from large payloads
   - Document: "Accessible via vault[field] → file"

4. **Environment variable** (in-process)
   - Example: `vault['env']['WHATSAPP_BRIDGE_TOKEN']`
   - Benefit: Available to subprocess calls
   - Document: "Accessible via env var $WHATSAPP_BRIDGE_TOKEN"

### Generating Verification Reports

Structure the output as a multi-section report (not a flat list):

1. **Top-level indexed credentials** (table: field name, value, status)
2. **Service accessibility** (all discovered services with credential counts)
3. **Access patterns** (how each credential is retrieved)
4. **File security** (permissions, encryption, locations)
5. **Health summary** (count accessible, missing, stale, encrypted)

**Example report:**
```
## SERVICE ACCESSIBILITY SUMMARY
✓ Accessible: 7/7 services
  ✓ google (5 fields)
  ✓ github (5 fields, dual indexed + nested)
  ✓ icloud (4 fields)
  ...

## ACCESS PATTERN TESTS
✓ Indexed lookup (google_token_file): O(1) direct access
✓ Nested lookup (github.pat): O(1) double lookup
✓ External reference (google_token.json): File exists, permissions 600
```

## Execution Notes

**Timing:** Full audit takes ~5 minutes (scanning, parsing, writing files)

**Safety:** Reading plaintext vaults is safe (they're local, encrypted by OS). Never attempt to decrypt EDITH files — stat only.

**Output:** Both markdown files on Desktop; [REDACTED] placeholders for sensitive values.

**User handoff:** "Full audit on your desktop: ~/Desktop/CREDENTIAL_AUDIT_COMPLETE.md — have 9/11 services, missing Slack + AWS, critical issues on Google OAuth scopes (poisoned token)."

## Session Notes

- **June 11, 2026:** Added verification patterns and multi-section report structure (references/vault-verification-patterns-june-2026.md). Covers testing credential access, external file validation, and report layout. Full vault verification executed successfully with 7/7 services accessible.

## Related

- vault_access SKILL.md — how to read and use credentials
- references/google_oauth_setup.md — fixing Google OAuth poisoning
- references/edith_vault_access.md — EDITH architecture and passphrase requirement
- references/vault-verification-patterns-june-2026.md — testing access patterns, multi-section reporting, pitfall recovery
