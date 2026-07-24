# Credential Management Architecture — Decision Log

**Date:** June 11, 2026  
**Context:** Friday 2.0 credential management system design  
**Status:** Production (live in friday-master repo)

---

## The Pattern: Dual-Store System

**Problem:** Secrets need to be both machine-readable (for code/automation) and human-auditable (to answer "what credentials do we have?"). Single-store approaches fail:
- Vault-only: encrypted files are opaque without decryption
- Plaintext-only: secrets exposed on disk, poor access control

**Solution:** Two complementary stores, each with its own job.

### Store 1: Vault (Code-Accessible, Encrypted)

**Location:** `~/.hermes/vault.json`  
**Permissions:** 600 (owner read/write only)  
**Format:** JSON (optionally encrypted via EDITH 2.0)

**Access:**
```python
import json
vault = json.load(open(os.path.expanduser('~/.hermes/vault.json')))
google_token = vault['google']['token']
```

**Contains:**
- Google OAuth tokens (access + refresh)
- GitHub PAT
- AWS/Azure credentials
- iCloud app passwords
- API keys for all services

**Lifecycle:**
- Tokens are refreshed automatically (daily at 06:00 UTC)
- Access tokens expire hourly; refresh token is indefinite (until user revokes)
- PATs rotate monthly (first Saturday)

### Store 2: Desktop Master (Human-Readable, Plaintext)

**Location:** `~/Desktop/CREDENTIALS_MASTER.md`  
**Permissions:** Owner readable, optionally synced to iCloud  
**Format:** Markdown with running log

**Purpose:** Single source of truth for "what credentials exist and when do they expire?"

**Contains:**
- Service name, account, scopes
- Creation date, expiry date
- Status (active, expired, pending enablement)
- Test results
- Notes and context

**Example entry:**
```markdown
## GOOGLE OAUTH
- **Service:** Gmail, Drive, Sheets, Docs, Calendar
- **Status:** Active
- **Created:** 2026-06-09
- **Expires:** Never (refresh token indefinite)
- **Last Tested:** 2026-06-11 06:00 UTC
- **Test Result:** ✓ All products connected (Calendar API pending project enablement)
- **Notes:** Refreshed daily. Access token expires hourly, auto-renewed.
```

---

## Memory vs. Hindsight vs. Vault: The Three-Layer Rule

**Rule:** Where information lives depends on what it answers.

### Vault (Secure Credential Store)
- **Answers:** "What's the actual API key / token / PAT?"
- **Storage:** Local encrypted file, never in Git, never in memory systems
- **Accessed by:** Code, scripts, background jobs
- **Lifecycle:** Auto-refreshed, rotated on schedule

### Memory (Fast Operational Store, ~4–5k tokens)
- **Answers:** "What's active right now? What's the immediate blocker?"
- **Storage:** In-context, session-scoped, high-velocity
- **Examples:** "Interview scheduled for Jun 11 at 10:30 AM PST"; "Calendar API needs enabling"
- **Rule:** Store *operational status*, never secrets
- **Update:** Frequent, mutable, session-driven

### Hindsight (Long-Term Semantic Memory)
- **Answers:** "What did we decide? Why did we choose this pattern? What happened last time?"
- **Storage:** Searchable, narrative-focused, durable across sessions
- **Examples:** "Dual-store credential architecture chosen June 11 because vault-only is opaque and plaintext-only is insecure"
- **Rule:** Store *decision rationale* and *pattern definitions*, never secrets
- **Update:** At end of session, captures learning

---

## Daily Credential Check Workflow

**Schedule:** 06:00 UTC every day  
**Owner:** Friday (automated, no user intervention)  
**Output:** `~/Desktop/CREDENTIAL_CHECK_LOG.md`

**Steps:**
1. Load vault (local, encrypted)
2. Refresh Google OAuth token (if expired)
3. Test live API connections (Gmail, Drive, Sheets, Docs, Calendar, GitHub)
4. Log results with timestamp
5. Alert on failures (flag, don't interrupt)
6. Push results to repo (optional, for audit trail)

**Sample log entry:**
```markdown
## 2026-06-11 06:00:00 UTC
- ✓ Google OAuth token refreshed
- ✓ Gmail API responding
- ✓ Google Drive API responding
- ✓ GitHub PAT valid, rate limit healthy
- ✗ Google Calendar API failed: 403 Forbidden (API not enabled in project)
```

**Failure handling:**
- OAuth refresh fails → flag and try again at next check
- API test fails → flag the specific service, include error
- PAT nearing expiry → flag 30 days before expiry date
- No interrupt — user sees clean summary when they check

---

## Monthly PAT Rotation

**Schedule:** First Saturday of each month  
**Trigger:** Cron job or manual request  
**Owner:** Friday (with user confirmation for sensitive ops)

**Steps:**
1. Check current PAT expiry date
2. If expiring within 60 days:
   a. Generate new PAT in GitHub UI (user action)
   b. Paste new PAT to Friday
   c. Store in vault
   d. Test with GitHub API
   e. Revoke old PAT in GitHub UI (user action)
   f. Update Desktop master with new expiry
   g. Document rotation in Hindsight

---

## Quarterly Full Audit

**Schedule:** First day of each quarter (Jan 1, Apr 1, Jul 1, Oct 1)  
**Owner:** Friday  
**Output:** Audit report to Hindsight

**Checks:**
- All credentials in vault are in use
- No stale or orphaned tokens
- Expiry dates are correct
- Desktop master is up to date
- EDITH encryption is functional
- Vault permissions are secure (600)

---

## Why Not: Single-Store Anti-Patterns

### Anti-Pattern 1: Vault-Only
**Problem:** How do you audit without decrypting?
- User asks "which credentials exist?" — requires Python + decryption
- Easy to forget about stale tokens
- No quick "expiry soon?" check

### Anti-Pattern 2: Plaintext-Only
**Problem:** Secrets exposed on disk with weak access control
- If someone gains user access, all credentials are visible
- No encryption means no hardware binding or verification protocol
- Hard to rotate without breaking active sessions

### Anti-Pattern 3: Cloud Vault (1Password, AWS Secrets Manager)
**Problem:** Introduces external dependency, latency, cost
- Offline work becomes impossible
- API rate limits apply
- Sync issues if offline
- Overkill for personal use

**The dual-store wins:**
- Vault stays encrypted, fast, local
- Desktop master stays readable, auditable, shareable (with redactions)
- Hindsight captures the pattern and reasoning (not secrets)
- Memory tracks immediate status (not secrets)

---

## Session Context (June 11, 2026)

**What happened:**
- User asked to set up credentials management framework for Friday 2.0
- Credential diagnostics revealed Google OAuth token was stale (access_token expired)
- Token refresh cycle was tested and working
- Calendar API discovered to be disabled in Google Cloud project (manual fix needed)
- GitHub PAT verified operational
- Dual-store architecture documented and pushed to friday-master repo

**Decision made:**
- Vault as encrypted code-accessible store (already in place, EDITH 2.0 ready)
- Desktop master as human-readable audit log (created, now in use)
- Daily cron job at 06:00 UTC (scheduled for later setup)
- Monthly PAT rotation on first Saturday (documented pattern, manual trigger for now)
- Quarterly full audit (documented pattern, first check Jan 1, 2027)

**Hindsight capture:**
Dual-store credential architecture (vault + Desktop master) chosen June 11, 2026. Pattern: encrypted vault for code/automation access, plaintext Desktop master for human audit trail. Solves opacity (vault-only) and exposure (plaintext-only) problems. Daily refresh at 06:00 UTC, monthly PAT rotation first Saturday, quarterly audit first day of Q. All decisions documented in CREDENTIAL_MANAGEMENT_LOGIC.md (friday-master repo).

---

## Related Skills

- **credential-management-tanzim** (this umbrella) — operational workflow
- **github-connect** — GitHub API operations and PAT management
- **google-oauth-credentials** — Google OAuth flow and refresh
- **google-oauth-refresh** — Token refresh patterns
- **secure-credential-vault** — EDITH 2.0 encryption setup

---

**Status:** Production  
**Last Updated:** June 11, 2026 at 20:30 UTC
