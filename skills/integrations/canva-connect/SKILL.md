---
name: canva-connect
description: Canva OAuth authentication and API integration for magazine design automation
tags: [canva, oauth, api, design, integration]
---

# Canva Connect

Manage Canva API OAuth authentication and token lifecycle for automated magazine design workflows.

## Credentials Location

All Canva credentials stored at: `~/.hermes/.canva_credentials`

Contains:
- `client_id`: OAuth client identifier
- `client_secret`: OAuth client secret (never expose in output)
- `redirect_uri`: OAuth callback URL (http://127.0.0.1:8080/callback)
- `access_token`: Current API access token (4-hour lifespan)
- `refresh_token`: Long-lived refresh token (1+ year)
- `code_verifier`: PKCE verifier (temporary, only during OAuth flow)

## OAuth Flow

### Initial Setup (One-time)

1. **Generate authorization URL with PKCE:**
```python
import json, base64, hashlib, secrets, urllib.parse

# Load credentials
with open('~/.hermes/.canva_credentials', 'r') as f:
    creds = json.load(f)

# Generate PKCE challenge
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8').rstrip('=')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).decode('utf-8').rstrip('=')

# Save verifier for token exchange
creds['code_verifier'] = code_verifier
with open('~/.hermes/.canva_credentials', 'w') as f:
    json.dump(creds, f, indent=2)

# Build authorization URL
params = {
    "client_id": creds['client_id'],
    "redirect_uri": creds['redirect_uri'],
    "response_type": "code",
    "scope": "design:content:read design:content:write asset:read asset:write",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256"
}

auth_url = f"https://www.canva.com/api/oauth/authorize?{urllib.parse.urlencode(params)}"
print(auth_url)
```

2. **User clicks auth URL, authorizes, gets redirected to callback URL**

3. **Exchange authorization code for tokens:**
```bash
python3 /tmp/canva_token_exchange.py "<callback_url>"
```

Script extracts code, exchanges for access + refresh tokens, saves to credentials file, tests connection.

### Token Refresh (Automatic)

## Token Lifecycle — Hard-Won Lessons (May 2026)

Access tokens expire in **4 hours**. Refresh tokens get **revoked server-side** (not just expired) when the user logs out or Canva rotates credentials. `invalid_grant: Token lineage has been revoked` = full re-auth required, refresh cannot recover it.

**In a single session this can happen multiple times.** Always refresh-then-test before any API call. If refresh returns `invalid_grant`, go straight to `--auth-url` — do not retry.

**API Capabilities (confirmed May 2026):**
- ✅ List all designs: `GET /v1/designs?limit=50`
- ✅ Get design details: `GET /v1/designs/{id}`
- ✅ List pages: `GET /v1/designs/{id}/pages`
- ✅ Export to PDF: `POST /v1/exports` with `{"design_id": id, "format": {"type": "pdf", "export_quality": "regular"}}`
- ✅ Poll export: `GET /v1/exports/{job_id}`
- ❌ Rename design: `PATCH /v1/designs/{id}` — endpoint does not exist (404)
- ❌ Edit text elements — not possible via API; requires Canva UI or Canva MCP
- ❌ Update design content directly — read/export only for existing designs

**PDF Export flow (working):**
1. POST to `/v1/exports` — get `job_id`
2. Poll `GET /v1/exports/{job_id}` every 3s until `status == "success"`
3. Download from `job.urls[0]`
4. Extract text: `pdftotext /path/to/file.pdf -`

Access tokens expire in 4 hours. Use `/tmp/canva_refresh.py` to auto-refresh:

```python
from canva_refresh import get_valid_token

# Returns valid access token, refreshing if needed
token = get_valid_token()
```

Refresh flow:
- Checks last refresh timestamp + expiry
- If within 5 min of expiry, auto-refreshes using refresh_token
- Updates credentials file with new access_token
- Returns valid token

## API Usage

### Make authenticated requests

```python
import json, requests

# Get valid token
with open('~/.hermes/.canva_credentials', 'r') as f:
    token = json.load(f)['access_token']

headers = {"Authorization": f"Bearer {token}"}

# Example: Get user info
response = requests.get("https://api.canva.com/rest/v1/users/me", headers=headers)
print(response.json())
```

### Scope Requirements

Different operations require different OAuth scopes. Current working set:
- `design:content:read` — read design content
- `design:content:write` — write/modify design content, use autofill
- `asset:read` — read uploaded assets
- `asset:write` — upload new assets

**Additional scopes needed for full access:**
- `design:meta:read` — list designs, get design metadata (needed for GET /designs/{id})
- `brandtemplate:meta:read` — list brand templates
- `brandtemplate:content:read` — read brand template content/dataset
- `brandtemplate:content:write` — use autofill to populate brand templates

**Recommended scope string for magazine automation:**
```
design:meta:read design:content:read design:content:write asset:read asset:write brandtemplate:meta:read brandtemplate:content:read brandtemplate:content:write
```

### Verified Working Endpoints

Tested and confirmed working with basic scopes:

| Endpoint | Method | Scope | Notes |
|----------|--------|-------|-------|
| `/users/me` | GET | (any) | ✅ Always works |
| `/exports` | POST | design:content:read | ✅ Export any design to PDF |
| `/exports/{id}` | GET | design:content:read | ✅ Check export job status |
| `/asset-uploads` | POST | asset:write | ✅ Upload images |
| `/autofills` | POST | design:content:write | ✅ But requires Brand Template |

**Blocked without additional scopes:**
- `GET /designs` — needs `design:meta:read`
- `GET /designs/{id}` — needs `design:meta:read`
- `GET /brand-templates` — needs `brandtemplate:meta:read`

### Export a Design to PDF

```python
import requests, json, time

with open('/tmp/canva_tokens.json', 'r') as f:
    tokens = json.load(f)

headers = {"Authorization": f"Bearer {tokens['access_token']}", "Content-Type": "application/json"}
design_id = "DAG9awLrJbg"  # From Canva URL

# Start export job
response = requests.post(
    "https://api.canva.com/rest/v1/exports",
    headers=headers,
    json={"design_id": design_id, "format": {"type": "pdf"}}
)
job_id = response.json()['job']['id']

# Poll for completion
while True:
    response = requests.get(f"https://api.canva.com/rest/v1/exports/{job_id}", headers=headers)
    job = response.json()['job']
    if job['status'] == 'success':
        pdf_url = job['urls'][0]  # Download URL (expires in ~21 hours)
        break
    time.sleep(2)
```

### Autofill (Requires Brand Template + Data Fields)

**Critical limitation:** Canva Connect API cannot directly edit text elements in designs. You cannot read individual text boxes, modify their content, or programmatically place text. The only content manipulation path is autofill, which has strict requirements:

**Autofill prerequisites (ALL required):**
1. Design must be saved as a **Brand Template** (File → Save as Brand Template)
2. Text elements must be tagged as **data fields** via Canva's "Connect data" feature
3. API must have `brandtemplate:content:write` scope

**How to tag data fields in Canva:**
1. Open brand template → Edit
2. Click text element
3. Look for "Connect data" icon in floating toolbar, OR open Bulk Create (left sidebar → Apps → Bulk Create)
4. Name each field (e.g., `intro`, `morning_ritual`, `macros`)
5. Publish the brand template

**Check if data fields exist:**
```python
# Get autofill dataset (empty = no data fields defined)
response = requests.get(
    f"https://api.canva.com/rest/v1/brand-templates/{template_id}/dataset",
    headers=headers
)
# Returns {} if no fields tagged
```

**Autofill API call:**
```python
response = requests.post(
    "https://api.canva.com/rest/v1/autofills",
    headers=headers,
    json={
        "brand_template_id": "BRAND_TEMPLATE_ID",
        "data": {
            "field_name": "content value"  # field names must match tagged elements
        }
    }
)
```

Full API reference: https://www.canva.dev/docs/connect/

## Design Renaming — Not Supported via API

`PATCH /v1/designs/{id}` → 404 `endpoint_not_found`. `PUT` also 404. Design renaming is UI-only.
**Workaround:** Direct the user to click the design title in Canva to rename. Provide the `edit_url` from the design search result. Takes 5 seconds.

## Known API Limitations
See `references/timbr-workout-series-structure.md` for TIMBR Workout Series design IDs, the 8-page template structure, shared vs unique content per issue, and the PDF extraction method used for magazine production.

See `references/canva-api-limits.md` for confirmed limitations including:
- Design renaming not supported via API (UI only)
- Text content not readable via API — use PDF export method
- Token lineage revocation pattern and re-auth flow

### Workaround: Structured Copy-Paste Doc

When autofill isn't viable (user can't/won't tag data fields), create a Google Doc that maps content to template pages:

1. Download template page thumbnails via API
2. Analyze page structure (cover, intro, sections, closing)
3. Generate doc with content organized by page number
4. User opens doc + Canva side-by-side, copies section-by-section

This is faster than teaching the user to set up data fields for a one-time task.

## Magazine Automation Workflow

**With Brand Template (Full Automation):**
1. Convert Canva design to Brand Template (manual, one-time)
2. Use `/autofills` to populate content fields
3. Export to PDF via `/exports`
4. Download and distribute

**Without Brand Template (Semi-Automated):**
1. User/collaborator manually populates template in Canva
2. Use `/exports` to generate PDF via API
3. Download and distribute

**Current constraint:** Regular designs can be exported but not modified via API. Converting to Brand Template unlocks autofill.

See `references/magazine-content-mapping.md` for:
- Two-product strategy (Magazine vs Workout Pack)
- Standard editorial TOC structure
- Content mapping table (profile data → template sections)
- Design analysis checklist for comparing options

## Token Security

- Access tokens expire in 4 hours
- Refresh tokens last 1+ year (or until revoked)
- Never log or expose `client_secret`, `access_token`, or `refresh_token` in output
- Credentials file is chmod 600 (owner read/write only)
- Auto-refresh ensures continuous connection without re-authorization

## Canva Token Revocation — Happens Frequently

⚠️ **Canva kills the entire token lineage multiple times per session.** In a single working session (May 26, 2026), the token lineage was revoked 3 times within hours of re-auth. This is NOT a one-off — Canva appears to revoke tokens aggressively on any of:
- Browser logout on any device
- Password change
- Security policy enforcement
- Possibly: opening Canva in a new browser tab while a token is active

**Do not assume the token is live just because you re-authed earlier in the same session.** Always attempt a refresh first before blaming the user. If refresh returns `invalid_grant`, accept it and re-auth immediately — do not waste time investigating.

**Fastest re-auth path (no explanation needed after the first time):**
1. Generate URL → send to user
2. User pastes callback URL back
3. Exchange code → test immediately with `/users/me`

**The `scripts/refresh_token.py` script is unreliable** — it may report success but not actually save the new token back to the credentials file. Always verify with a direct API call after refresh.

## Re-auth Flow (Token Lineage Revoked)

If `refresh_token` is revoked (e.g. user logged out of Canva, or Canva killed the session), `requests.post` to `/oauth/token` returns:
```json
{"error": "invalid_grant", "error_description": "Token lineage has been revoked"}
```
The entire token chain is dead — the refresh token cannot be used again. Full re-auth required.

**Correct PKCE generation for re-auth:**
```python
import secrets, hashlib, base64, json, urllib.parse

client_id = "OC-AZ5TE93EPw0y"
redirect_uri = "http://127.0.0.1:8080/callback"

code_verifier = secrets.token_urlsafe(64)  # Use token_urlsafe, NOT base64(token_bytes)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()
state = secrets.token_urlsafe(16)

scopes = "design:meta:read design:content:read design:content:write asset:read asset:write brandtemplate:meta:read brandtemplate:content:read brandtemplate:content:write"

params = {
    "client_id": client_id, "response_type": "code",
    "redirect_uri": redirect_uri, "scope": scopes,
    "state": state, "code_challenge": code_challenge, "code_challenge_method": "S256"
}
auth_url = "https://www.canva.com/api/oauth/authorize?" + urllib.parse.urlencode(params)

# Save pending state
import json
with open('/home/hermes/.hermes/.canva_oauth_pending.json', 'w') as f:
    json.dump({"state": state, "code_verifier": code_verifier, "redirect_uri": redirect_uri}, f)

print(auth_url)
```

User opens URL → logs into Canva → clicks Allow → browser redirects to `http://127.0.0.1:8080/callback?code=...` (shows error page — expected). User copies full URL from address bar and pastes back.

**Token exchange after user pastes callback URL:**
```python
import json, requests, urllib.parse

callback_url = "http://127.0.0.1:8080/callback?code=THE_CODE&state=..."
code = urllib.parse.parse_qs(urllib.parse.urlparse(callback_url).query)['code'][0]

pending = json.load(open('/home/hermes/.hermes/.canva_oauth_pending.json'))
creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))

r = requests.post("https://api.canva.com/rest/v1/oauth/token", data={
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": pending["redirect_uri"],
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "code_verifier": pending["code_verifier"]
})
tokens = r.json()
creds["access_token"] = tokens["access_token"]
creds["refresh_token"] = tokens["refresh_token"]
with open('/home/hermes/.hermes/.canva_credentials', 'w') as f:
    json.dump(creds, f, indent=2)
print("Authenticated")
```

## Canva API Read Limitations

**Cannot read text content from designs.** The Canva Connect API exposes design metadata (title, page count, dimensions, thumbnails) and pages list — but does NOT return text element content. There is no endpoint to extract copy/text from a design.

**To read what's on a design:**
1. Export as PDF via `/exports` endpoint, then extract text with `pdftotext`
2. Or retrieve thumbnail URLs from `/designs/{id}/pages` and use vision analysis
3. Or direct the user to open the design directly via `edit_url`

**To search designs by name:**
```python
r = requests.get('https://api.canva.com/rest/v1/designs?query=IG+carousel', headers=headers)
# Returns items[] with id, title, thumbnail, urls.edit_url, page_count
```

**Design ID from search result** → use for `/designs/{id}` or `/exports`.

## Troubleshooting

**"Why can't you edit text like Claude Desktop does?"**
Claude Desktop uses Canva MCP (Model Context Protocol), which wraps the same Connect API. MCP doesn't unlock new capabilities — it's still subject to the same limitation: autofill requires data fields. If the user expects direct text editing, explain this and offer the structured doc workaround.

**No access token in credentials file:** OAuth flow incomplete. Credentials file exists with client_id/secret but missing `access_token` and `refresh_token`. Run full OAuth flow (steps 1-3 above) to complete authorization.

**400 on auth URL:** Missing or invalid PKCE parameters. Regenerate with fresh code_challenge.

**401 on API call:** Token expired. Run refresh script or call `get_valid_token()`.

**Redirect URL mismatch:** Must use exact URL registered in Canva Developer Portal (http://127.0.0.1:8080/callback, not localhost).

**Token refresh fails / `invalid_grant: Token lineage has been revoked`:** Refresh token is permanently dead — Canva kills the whole chain on logout or manual revocation. Re-run full OAuth re-auth flow (see Re-auth Flow section above). Client ID/secret are already on VM at `~/.hermes/.canva_credentials` — no need to re-register the app.

**`refresh_token.py` returns stale token / 401 on API call after refresh:** The script in `scripts/refresh_token.py` uses `requests` library. If token refresh returns 200 but the access_token field comes back nested differently, check the full response before assuming success — always verify with `/users/me` after refresh.

**`refresh_token.py` runs but `/users/me` still returns 401:** The script may print a token but NOT save it back to `~/.hermes/.canva_credentials`. Verify the script writes the new `access_token` to the credentials file after refresh. If not, do the refresh manually:
```python
import json, requests
creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))
r = requests.post('https://api.canva.com/rest/v1/oauth/token', data={
    'grant_type': 'refresh_token',
    'refresh_token': creds['refresh_token'],
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret']
})
print(r.status_code, r.json())  # Check for access_token key before saving
```
If status is 400 with `invalid_grant: Token lineage has been revoked` — the whole chain is dead. Skip refresh entirely and run the full re-auth flow.
