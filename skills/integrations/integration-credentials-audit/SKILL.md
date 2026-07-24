---
name: integration-credentials-audit
description: "Procedure for auditing, testing, and restoring all active API integrations in one session. Pattern: check memory → test live → fix or skip → update registry sheet."
version: 1.0.0
tags: [integrations, credentials, audit, API, maintenance]
related_skills: [canva-connect, google-workspace, gmail-inbox-check]
---

# Integration Credentials Audit

Reusable procedure for reviewing the full stack of active integrations — checking what's live, what's expired, what's skipped, and updating the central registry.

## When to use
- After a period of inactivity (integrations expire silently)
- When setting up a new device or VM
- When cron jobs start returning auth errors
- When user asks "what are you connected to?"

## Registry sheet
**"Software and API"** — Google Sheet ID: `18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4`
Columns: Software Name | API Key / Status | Expiry / Notes
Colour coding: 🟢 green = active, 🔴/🟡 amber = needs attention, ⚪ grey = skipped

## Credential file locations
| Integration | Credential file |
|---|---|
| Google Workspace | `~/.hermes/google_token.json` |
| Canva | `~/.hermes/.canva_credentials` |
| Wix | `~/.hermes/.wix_credentials.json` |
| Webflow | `~/.hermes/.webflow_credentials.json` |
| Trello | `~/.hermes/.trello_credentials` |

## Audit procedure (per integration)

### Step 1 — Check memory first
Before asking the user for credentials, search memory and skill files for stored tokens. Most integrations from prior sessions are already on the VM — test them before declaring them dead.

### Step 2 — Test live
Run a lightweight authenticated request (e.g. `/users/me`, `/members/me`, list endpoint). Don't assume a token is expired — test it.

### Step 3 — Triage result
- **200 OK** → Live. Store confirmed credentials, move on.
- **401/403** → Token expired or revoked. Attempt refresh if refresh_token exists.
- **Refresh fails (`invalid_grant`)** → Full re-auth required.
- **No stored credentials** → Ask user to provide.

### Step 4 — Decision: fix or skip
Before walking user through re-auth, ask: **is this integration actually needed right now?** Many integrations (job scrapers, Substack, OpenRouter) are only useful for specific workflows. If the workflow isn't active, skip it and note it in the registry. Don't reconnect things just because they exist.

### Step 5 — Update registry sheet
After completing all integrations, update the Google Sheet with final statuses. Use colour coding.

## Integration-specific notes

### Wix (IST tokens)
- IST tokens from the Wix dashboard are app-scoped, not account-scoped
- The correct test endpoint is: `POST https://www.wixapis.com/site-list/v2/sites/query` with body `{"query": {}}`
- `GET https://www.wixapis.com/site-properties/v4/properties` returns 401 even with valid tokens — wrong endpoint
- `POST https://www.wixapis.com/account/v1/account` returns 403 — also wrong
- If site-list returns sites, the token is valid regardless of 403s on other endpoints

### Webflow
- Personal API tokens have no set expiry but should be tested monthly
- Test endpoint: `GET https://api.webflow.com/v2/token/authorized_by`
- Token from May 9 2026 still valid as of May 26 2026 ✅

### Trello
- API Key + Token combo — key never expires, token can be set to never expire
- Test: `GET https://api.trello.com/1/members/me?key=KEY&token=TOKEN`
- Credentials stored at `~/.hermes/.trello_credentials` (JSON)

### Canva
- OAuth 2.0 with PKCE. Access tokens expire in 4 hours — refresh_token is long-lived (~1 year)
- If refresh returns `invalid_grant: Token lineage has been revoked`, full re-auth required (takes ~2 min)
- Client ID `OC-AZ5TE93EPw0y` and client_secret already in `~/.hermes/.canva_credentials` — never ask Tanzim to re-register the app
- Re-auth flow: generate URL (save PKCE pending state) → user pastes callback URL → exchange code → verify with `/users/me`

### OpenRouter
- Not set up. Claude Max $200/month makes it unnecessary for Tanzim's current usage
- Only relevant for: context compression at scale, fallback model routing, accessing non-Anthropic models cheaply
- Revisit if context limits become a real problem

### RapidAPI / JSearch
- Only needed for TerraJob job scraper's secondary source — JobSpy handles the primary crawl without it
- Reconnect only if TerraJob is actively running and JSearch results are needed to supplement

### Substack
- Session cookie (`connect.sid`) integration — expires every few weeks
- No API: only viable via browser cookie extraction
- Low priority unless Substack auto-posting workflow is active

## Skipping decisions log (May 26 2026)
- **Substack** — skipped, no active posting workflow
- **OpenRouter** — skipped, Claude Max covers the need
- **RapidAPI/JSearch** — skipped, TerraJob runs fine on JobSpy alone
