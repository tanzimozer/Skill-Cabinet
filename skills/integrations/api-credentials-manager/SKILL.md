---
name: api-credentials-manager
description: "Pull, verify, and update API credentials from the Software and API Google Sheet. Single source of truth for all integration keys and statuses."
version: 1.0.0
tags: [api, credentials, integrations, google-sheets, trello, wix, webflow, canva]
related_skills: [google-workspace]
---

# API Credentials Manager

Single source of truth for all of Tanzim's software integrations. The Google Sheet is the canonical record — credential files on disk are the live copies.

## Sheet Reference
- **Sheet Name:** Software and API
- **Sheet ID:** `18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4`
- **URL:** https://docs.google.com/spreadsheets/d/18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4/edit
- **Columns:** A = Software Name | B = API Key/Status | C = Expiry / Status

See `references/integration-reconnect-patterns.md` for service-specific test patterns, credential file locations, and what was skipped in the May 2026 audit.

## Credential File Locations (on VM)
| Integration | File |
|---|---|
| Google Workspace | `~/.hermes/google_token.json` |
| Trello | `~/.hermes/.trello_credentials` |
| Wix | `~/.hermes/.wix_credentials.json` |
| Webflow | `~/.hermes/.webflow_credentials.json` |
| Canva | `~/.hermes/.canva_credentials` |
| Anthropic | `~/.hermes/.env` (CLAUDE_CODE_OAUTH_TOKEN) |

## How to Pull Credentials from Sheet

```bash
GAPI="python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI sheets get 18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4 "Sheet1!A1:C20"
```

Parse the result — column A is the service name, B is the key/token, C is expiry status.

## How to Update Sheet Status

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

SHEET_ID = "18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4"

# Update a specific row's status (e.g. row 8 = Webflow)
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range="Sheet1!C8",
    valueInputOption='RAW',
    body={'values': [["Token refreshed — May 26 2026 ✅"]]}
).execute()
```

## Current Integration Status (as of May 26, 2026)

| Software | Status | Notes |
|---|---|---|
| Google Workspace | ✅ Live | OAuth auto-refresh |
| Anthropic / Claude | ✅ Live | Claude Max $200/mo |
| WhatsApp Bridge | ✅ Live | Session-persisted |
| Hindsight | ✅ Live | Internal |
| Trello | ✅ Live | Key: ~/.hermes/.trello_credentials |
| Wix (TIMBR) | ✅ Live | IST token, site: ab465896 |
| Webflow | ✅ Live | Bearer token, tan.biz@icloud.com |
| Canva | ✅ Live | OAuth, 4hr access token (auto-refresh) |
| Substack | ⏭️ Skipped | connect.sid cookie, re-auth when needed |
| OpenRouter | ⏭️ Skipped | Claude Max covers the need |
| RapidAPI/JSearch | ⏭️ Skipped | TerraJob uses JobSpy, no key needed |

## Canva Token Lifecycle — Critical Pitfall

Canva OAuth tokens have a **4-hour access token expiry** and the refresh token lineage gets invalidated server-side when:
- User logs out of Canva in browser
- Password change
- Canva security policy rotation

**Symptom:** `invalid_grant: Token lineage has been revoked` on refresh attempt.
**Fix:** Full re-auth flow — generate new auth URL, exchange code. Cannot recover without user action.

This happened 3 times in a single session (May 26, 2026). Do NOT assume the stored refresh token is valid. Always test before use. If it fails, go straight to re-auth — don't retry refresh.

**Canva API limitations discovered:**
- `PATCH /v1/designs/{id}` — does NOT exist. Cannot rename designs via API.
- `PUT /v1/designs/{id}` — does NOT exist.
- Cannot edit text content of existing design elements via API.
- CAN: list designs, export to PDF, read page thumbnails, create exports.
- Design renaming and text editing must be done in Canva UI or via Canva MCP.

## Verification — Test All Active Connections

```python
import json, requests, urllib.request

results = {}

# Trello
try:
    creds = json.load(open('/home/hermes/.hermes/.trello_credentials'))
    r = urllib.request.urlopen(f"https://api.trello.com/1/members/me?key={creds['api_key']}&token={creds['token']}", timeout=8)
    results['Trello'] = '✅ ' + json.loads(r.read()).get('fullName','connected')
except Exception as e:
    results['Trello'] = f'❌ {e}'

# Wix
try:
    creds = json.load(open('/home/hermes/.hermes/.wix_credentials.json'))
    r = requests.post("https://www.wixapis.com/site-list/v2/sites/query",
        json={"query": {}}, headers={"Authorization": creds['api_key']}, timeout=8)
    results['Wix'] = '✅ ' + str(len(r.json().get('sites',[]))) + ' site(s)'
except Exception as e:
    results['Wix'] = f'❌ {e}'

# Webflow
try:
    creds = json.load(open('/home/hermes/.hermes/.webflow_credentials.json'))
    r = requests.get("https://api.webflow.com/v2/token/authorized_by",
        headers={"Authorization": f"Bearer {creds['api_token']}"}, timeout=8)
    results['Webflow'] = '✅ ' + r.json().get('email','connected')
except Exception as e:
    results['Webflow'] = f'❌ {e}'

# Canva
try:
    creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))
    # Refresh first
    r = requests.post('https://api.canva.com/rest/v1/oauth/token',
        data={'grant_type':'refresh_token','refresh_token':creds['refresh_token'],
              'client_id':creds['client_id'],'client_secret':creds['client_secret']}, timeout=8)
    if r.status_code == 200:
        creds['access_token'] = r.json()['access_token']
        json.dump(creds, open('/home/hermes/.hermes/.canva_credentials','w'), indent=2)
        results['Canva'] = '✅ Token refreshed'
    else:
        results['Canva'] = f'❌ Refresh failed: {r.text[:80]}'
except Exception as e:
    results['Canva'] = f'❌ {e}'

for k, v in results.items():
    print(f"{k}: {v}")
```

## Integration-Specific Notes

### Wix
- Token format: `IST.eyJ...` (account-level API key from manage.wix.com → Account Settings → API Keys)
- Do NOT confuse with app tokens — both look similar but app tokens scope to a specific Wix app and return 403 on account-level endpoints
- Correct test endpoint: `POST https://www.wixapis.com/site-list/v2/sites/query` with `{"query":{}}` body
- Wrong test endpoints that return 403/401 even with valid tokens: `/site-properties/v4/properties`, `/members/v1/members/my`

### Canva
- Access token expires every 4 hours — always refresh before use via `/rest/v1/oauth/token` with `grant_type=refresh_token`
- If refresh returns `{"error":"invalid_grant","error_description":"Token lineage has been revoked"}` → full re-auth needed (client secret already on VM at `~/.hermes/.canva_credentials`)
- Cannot read text content from designs — API only returns metadata and thumbnails. Export as PDF to extract text.
- To search designs: `GET https://api.canva.com/rest/v1/designs?query=<name>`

### Trello
- Check memory/existing credential files BEFORE asking user for new keys — credentials from May 2026 still valid

### Google Workspace
- `REFRESH_FAILED: invalid_scope` = stale token, needs fresh OAuth flow (2 min, client secret already on VM)
- Partial auth (`AUTHENTICATED (partial)`) is fine for Gmail — missing `documents.readonly` doesn't affect most operations

## Rules
## Canva — Token Revocation Pattern
Canva kills the **entire token lineage** (access + refresh) when the user logs out or changes password. `invalid_grant: Token lineage has been revoked` = full re-auth needed, not just a refresh.

Re-auth flow (2 steps):
1. Generate PKCE auth URL using client_id from `~/.hermes/.canva_credentials`, save state+verifier to `~/.hermes/.canva_oauth_pending.json`
2. User opens URL, clicks Allow, pastes the `http://127.0.0.1:8080/callback?code=...` redirect back
3. Exchange: POST to `https://api.canva.com/rest/v1/oauth/token` with `grant_type=authorization_code`, code, client_id, client_secret, redirect_uri, code_verifier
4. Save new access_token + refresh_token to `~/.hermes/.canva_credentials`

**Canva API limitations (confirmed):**
- Design renaming via API is NOT supported (`PATCH /v1/designs/{id}` returns 404 — endpoint does not exist)
- Text content of designs is NOT readable via API — must export as PDF and extract text
- PDF export: `POST /v1/exports` with `{"design_id": "...", "format": {"type": "pdf", "export_quality": "regular"}}`, then poll `GET /v1/exports/{job_id}` until status = "success", then download the URL

## Wix — IST Token Format
Wix account-level API keys are IST tokens (format: `IST.eyJ...`). Test with `POST https://www.wixapis.com/site-list/v2/sites/query` with body `{"query": {}}` — returns site list. The `/site-properties/v4/properties` endpoint returns 401 for IST tokens.

## Trello — Credentials Location
`~/.hermes/.trello_credentials` (JSON: `api_key`, `token`). May 21 credentials still valid as of May 26. Test: `GET https://api.trello.com/1/members/me?key={key}&token={token}`

## Webflow — Credentials Location
`~/.hermes/.webflow_credentials.json` (JSON: `api_token`, `email`, `org_id`). Test: `GET https://api.webflow.com/v2/token/authorized_by` with `Authorization: Bearer {token}`

## RapidAPI / JSearch
Not needed while TerraJob uses JobSpy (scrapes Indeed/LinkedIn directly, no API key). Reconnect only when active job scraping resumes.

## Canva Token Revocation — Frequent Pattern (May 2026)
Canva revoked the token lineage **3 times in a single session** (May 26, 2026). Each re-auth generates a new refresh token and invalidates the old one. Token lineage is invalidated by:
- User logging out of Canva in browser
- Password change
- Canva's own security rotation policy

**Detection:** `{"error":"invalid_grant","error_description":"Token lineage has been revoked"}`
**Resolution:** Full re-auth every time. Cannot recover without user clicking a new auth URL.
**Do NOT:** Retry refresh, check the token manually, or tell user "the token should still be valid" — if `invalid_grant` came back, it's dead. Go straight to re-auth.

Re-auth is 2 steps — user clicks URL, pastes redirect back. ~60 seconds. State and verifier saved to `~/.hermes/.canva_oauth_pending.json` during URL generation.

## Check Existing Credentials Before Asking

**Always search memory and disk before asking Tanzim for credentials.** In this session, Trello (May 21), Webflow (May 9), and Canva credentials were all already stored and valid — no need to ask. Check:
1. Memory/hindsight for prior credential setup notes
2. `~/.hermes/.{service}_credentials*` and `~/.hermes/.{service}_credentials.json`
3. Friday backup at `~/friday_backup/` (e.g. `google_token.json`, `google_client_secret.json`)

Only ask Tanzim for new credentials after confirming nothing is stored.

## Rules
- Never print full API keys/tokens in responses — confirm connection by account name or site name only
- Always test connection after pulling credentials before using them
- Canva access tokens expire every 4 hours — always refresh before use; if refresh fails with `invalid_grant`, do full re-auth
- If any credential fails, alert Tanzim with which service and what action is needed
- Update the sheet status column whenever a token is refreshed or re-authed
- OpenRouter: skipped — Claude Max $200/mo covers context compression needs. Revisit only if hitting limits.
