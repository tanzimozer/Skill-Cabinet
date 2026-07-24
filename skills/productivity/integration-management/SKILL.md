---
name: integration-management
description: "Managing, auditing, and reconnecting third-party integrations — credential storage, connection testing, Software & API sheet maintenance."
version: 1.0.0
tags: [integrations, credentials, API, OAuth, audit]
related_skills: [google-workspace, canva-connect]
---

# Integration Management

Covers the full lifecycle of third-party integrations: audit what's connected, test live status, reconnect expired credentials, and maintain the Software & API tracking sheet.

## Credential storage locations

| Service | File | Format |
|---------|------|--------|
| Google Workspace | `~/.hermes/google_token.json` | OAuth2 token (auto-refresh) |
| Trello | `~/.hermes/.trello_credentials` | JSON: `api_key`, `token` |
| Wix | `~/.hermes/.wix_credentials.json` | JSON: `api_key`, `site_id`, `site_name` |
| Webflow | `~/.hermes/.webflow_credentials.json` | JSON: `api_token`, `email`, `org_id` |
| Canva | `~/.hermes/.canva_credentials` | JSON: OAuth tokens + client creds |

All credential files should be `chmod 600`.

## Integration audit procedure

When Tanzim asks "what are you connected to" or requests an integration overview:

1. **Check Google Workspace:** `python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check`
2. **Test Trello:** GET `https://api.trello.com/1/members/me?key={key}&token={token}` — look for `fullName`
3. **Test Wix:** POST `https://www.wixapis.com/site-list/v2/sites/query` with `{"query":{}}` — look for sites array
4. **Test Webflow:** GET `https://api.webflow.com/v2/token/authorized_by` with Bearer token — look for `email`
5. **Test Canva:** After refresh, GET `https://api.canva.com/rest/v1/users/me` — look for `profile.display_name`

Classify each as: ✅ LIVE / 🟡 NEEDS ATTENTION / ❌ DEAD

## Software & API Google Sheet

Tanzim maintains a tracking sheet for all integrations:
- **Sheet ID:** `18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4`
- **Columns:** Software Name | API Key | Expiry
- **Colour coding:** Green rows = active; Amber rows = expired/needs attention

When reconnecting integrations, update the sheet row for that service.

## Test-before-store rule

**Always test a credential before writing it to disk.** Pattern:
1. Receive token/key from user
2. Hit a lightweight read endpoint (e.g. `/me`, `/users/me`, `/members/me`)
3. Confirm 200 + expected fields in response
4. Only then write to credentials file + update sheet

If test fails: diagnose first (wrong endpoint? wrong token format? scopes missing?) before asking user to regenerate.

## Wix IST token notes

Wix API keys are IST (Identity Service Tokens) — they look like JWTs. The correct test endpoint is:
```
POST https://www.wixapis.com/site-list/v2/sites/query
Body: {"query": {}}
Header: Authorization: {token}
```
NOT `/site-properties/v4/properties` (returns 401 for app tokens) or `/account/v1/account`.

## Webflow token notes

Personal API tokens (v2): use `Authorization: Bearer {token}` header.
Test endpoint: `GET https://api.webflow.com/v2/token/authorized_by`

## Reconnect flow (general)

For each expired integration, the approach depends on auth type:
- **Simple API key/token (Trello, Webflow):** User regenerates from dashboard, pastes here, test + store
- **OAuth (Google, Canva):** Generate auth URL → user clicks + authorises → user pastes callback URL → exchange for token → store
- **Session cookie (Substack):** User opens browser DevTools → Application → Cookies → copy `connect.sid` value

See individual skills (canva-connect, google-workspace) for their specific flows.
