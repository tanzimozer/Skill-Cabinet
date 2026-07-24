---
name: credentials-audit
description: Track and audit all service credentials, scopes, and expiry dates
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [credentials, oauth, authentication, audit]
    related_skills: [google-oauth-refresh, gmail-automation]
---

# Credentials Audit & Status Tracking

## Overview

Central hub for tracking all active service credentials, scope status, expiry dates, and refresh cycles. Single source of truth alongside `~/.hermes/vault.json` (plaintext) and `~/Desktop/CREDENTIALS_MASTER.md` (human-readable backup).

## Services Tracked

| Service | Account | Status | Scopes | Last Verified | Next Check |
|---------|---------|--------|--------|----------------|------------|
| Google OAuth | tanzim.seattle@gmail.com | ✅ Active | Gmail (modify/read/send), Calendar, Drive, Sheets, Docs | 2026-06-14 | 2026-06-21 |
| GitHub PAT | tanzimozer | ✅ Active | repo, gist, user, delete:repo | 2026-06-09 | 2026-06-23 |
| iCloud | tanzimx@icloud.com | ✅ Active | IMAP (pop/imap/smtp) | 2026-06-09 | 2026-06-23 |
| Webflow | tan.biz@icloud.com | ✅ Active | API token (full org access) | 2026-06-09 | 2026-06-23 |
| Wix | TIMBR site | ✅ Active | API key (read/write collections) | 2026-06-09 | 2026-06-23 |
| Instagram | tanzim.seattle | ⚠️ Stale | Session cookies (5+ days old) | 2026-06-04 | On-demand re-paste |
| Canva | (authenticated) | ✅ Active | OAuth token | 2026-06-11 | 2026-06-25 |
| Anthropic | Claude API | ✅ Active | API key (full model access) | 2026-06-11 | 2026-06-25 |
| Hindsight | LLM API | ✅ Active | API key (memory + reflect) | 2026-06-11 | 2026-06-25 |

## Google OAuth Status — Full Detail

**Client ID:** 313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct  
**Project:** job-scraping-494906  
**Account:** tanzim.seattle@gmail.com  
**Created:** 2026-06-09 03:58 PM GMT-7  
**Last Authorized:** 2026-06-09 11:01:43 PM UTC  
**Token Location:** `~/.hermes/google_token.json`  
**Token Expiry:** 2026-06-14 09:52:09 UTC (refreshed 2026-06-14 01:52 UTC)  
**Next Auto-Refresh:** 2026-06-21 (weekly check)  

**Scopes Active (7/7):**
- ✅ `gmail.modify` — send, delete, trash, label emails
- ✅ `gmail.readonly` — search and read emails
- ✅ `gmail.send` — send emails directly
- ✅ `calendar` — create, read, modify calendar events
- ✅ `drive` — read, create, modify files and folders
- ✅ `spreadsheets` — create, edit, read Google Sheets
- ✅ `documents` — create, edit, read Google Docs

**Calendar API Status:**
- ✅ Enabled in Google Cloud Console (2026-06-14 01:52 UTC)
- ✅ Scope added to OAuth token
- ✅ Token refreshed with full scope set

**Known Blockers:** None. All scopes operational.

## EDITH Vault (Standard for Tanzim's Systems)

EDITH is the 3-factor credential vault, replacing generic vault.json. Location: `~/.hermes/edith/edith_vault.json`

**Structure:**
- **Version:** 2.0
- **Encryption:** AES-256-GCM
- **Access control:** Hardware UUID + passphrase + 3 security questions (all required)
- **Credentials stored:**
  - `google_oauth` — 5 services (Gmail, Calendar, Drive, Sheets, Docs)
  - `github_pat` — Repository PAT (repo, gist, user scopes)
  - `icloud` — IMAP credentials (app password)
  - `instagram` — Session token + backup credentials
  - (Extensible: add Webflow, Wix, Canva, Anthropic, Hindsight as needed)

**Access pattern:** Do NOT store full credentials in persistent memory. Instead, store **routing instructions** that point to EDITH:
```
Gmail: "Lookup EDITH.credentials.google_oauth → validate refresh token → auto-refresh if expiry < 14 days"
GitHub: "Lookup EDITH.credentials.github_pat → validate expiry → alert if < 14 days"
```

**Auto-refresh:** EDITH supports scheduled refresh via cron (default: 5 AM PDT daily, configurable per service).

## Refresh Cycles

**Manual refresh (on-demand):**
```bash
cd ~/.hermes && python3 -m google.oauth2.credentials --refresh ~/.hermes/google_token.json
```

Or use the `google-oauth-refresh` skill to refresh any expired token.

**Automated weekly check (cron):**
Set `schedule_task(action='create', schedule='every Sunday 00:00', ...)` to audit all credentials and refresh any expiring within 7 days. See `launch-countdown-cron` skill for the template.

## Audit Checklist

When running a full credential audit:

1. **Google OAuth**
   - [ ] Token exists at `~/.hermes/google_token.json`
   - [ ] Refresh token is present (never rotates)
   - [ ] Access token is fresh (check expiry field)
   - [ ] All 7 scopes are listed
   - [ ] Calendar API is enabled in Cloud Console

2. **GitHub**
   - [ ] PAT token is NOT expired (check GitHub settings)
   - [ ] Scopes include `repo` (required for private repos)

3. **iCloud**
   - [ ] App password is correct (main password != app password)
   - [ ] IMAP port 993 is reachable

4. **Instagram**
   - [ ] Session ID is fresh (< 7 days old)
   - [ ] Check if account is blocked or rate-limited

5. **Webflow / Wix / Canva / Anthropic / Hindsight**
   - [ ] API key is not revoked
   - [ ] Test API call succeeds

## Desktop Master File

**Location:** `~/Desktop/CREDENTIALS_MASTER.md`

Human-readable plaintext backup. Updated after every credential generation, refresh, or rotation. Includes:
- Service name
- Account / project ID
- Current status
- Scope list
- Expiry date
- Last verified timestamp
- Next action (refresh, re-auth, or on-demand)

**Authority rule:** If vault.json and CREDENTIALS_MASTER.md conflict, desktop file is authoritative (user may have manually updated it). Hermes updates the desktop file after every credential change.

## Pitfalls

- **Do NOT store raw credentials in persistent memory** — store routing instructions instead. Persistent memory is queryable across sessions and agents; raw tokens there are a vulnerability. EDITH vault is the single source of truth.
- **Google Calendar API not enabled in Cloud Console** — even with valid OAuth credentials and scopes, Calendar API calls return 403 `accessNotConfigured` if the API hasn't been enabled in the GCP project. Always check the Console.
- **Refresh token revocation (400 on refresh)** — if refresh request returns HTTP 400, the refresh token is stale (user re-authed elsewhere, or Google revoked it). Full re-auth is required.
- **Instagram session cookies expire silently** — no warning; API calls just start returning 401. Re-paste fresh cookies on-demand.
- **GitHub PAT tokens have fixed expiry** — set calendar reminder for 1 week before expiry to regenerate.
- **Mixing accounts** — `tanzim.seattle@gmail.com` (job/professional) ≠ `tanzim.ozer@gmail.com` (personal). Tokens are account-specific.
- **EDITH 3-factor auth failure** — if any one of the three factors (UUID, passphrase, security questions) fails, vault is inaccessible. Keep backup credentials in a secure secondary location (e.g., password manager with manual sync).

## References

- **google-oauth-refresh:** Full token refresh workflow (manual and automated)
- **gmail-automation:** Gmail API usage with current credentials
- **Desktop CREDENTIALS_MASTER.md:** Human-readable audit log (user authority)
