---
name: vault_access
category: infrastructure
description: Read credentials from the Hermes vault. Use this as the first step in any integration that needs API keys, tokens, or passwords. Never ask Tanzim for credentials if the vault has them.
---

# Vault Access

## Vault location
`~/.hermes/vault.json` — permissions 600, owner: hermes

## How to read a credential

```python
import json

def get_vault():
    with open('/home/hermes/.hermes/vault.json') as f:
        return json.load(f)

def get_cred(service, key=None):
    vault = get_vault()
    svc = vault.get(service, {})
    if key:
        return svc.get(key)
    return svc
```

**IMPORTANT: EDITH Vault (`~/.hermes/.edith/edith_vault.json`) is AES-256-GCM encrypted.** Do NOT try to load it as JSON directly. It requires three-factor authentication: (1) hardware UUID at `~/.hermes/.edith/hardware_uuid`, (2) bcrypt-10 hashed passphrase at `~/.hermes/.edith/passphrase_hash`, (3) time-window gating (±5 min from last auth, auto-purge 5 min idle). If you need EDITH credentials and can't decrypt the vault at runtime, fall back to `~/.hermes/google_oauth_full.json` for Google scopes or check `vault_access` references for decryption patterns (future — known gap as of Jun 2026).

## Services in vault
| Service | Keys available |
|---|---|
| `google` | token_file, client_secret_file, account, scopes |
| `icloud` | email, app_password, imap_server, imap_port |
| `webflow` | api_token, email, org_id |
| `wix` | api_key, site_id, site_name |
| `instagram` | session_id, csrf_token, datr, mid, ig_did, ds_user_id, last_updated |
| `env` | WHATSAPP_BRIDGE_TOKEN, HINDSIGHT_LLM_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, etc. |

## Instagram cookie notes
- `datr` = device fingerprint. Same datr = same browser fingerprint. If session is rate-limited, new cookies from the SAME browser will still be blocked on write endpoints.
- Always get fresh cookies from a DIFFERENT browser (Firefox, Edge, incognito) when recovering from a checkpoint.
- Update `last_updated` field whenever cookies are refreshed.

## Google OAuth (special case)
Google token lives in its own file — read it directly:
**Current active client (as of 2026-07-22):**
- Project: `job-scraping-494906`
- Client ID: `313611152308-r2g23uql9vg6hlahgvabrdk8klsoa0jk.apps.googleusercontent.com`
- Client secret file: `~/.hermes/google_client_secret.json`
- Previous project (`friday-mark-2-499708`, client `990922176945-...`) was deleted — do not use.


```python
with open('/home/hermes/.hermes/google_token.json') as f:
    token_data = json.load(f)
from google.oauth2.credentials import Credentials
creds = Credentials(
    token=token_data.get('token'),         # NOTE: key is 'token' (not 'access_token') — flow.fetch_token saves as 'token'
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
    scopes=token_data.get('scopes'),
)
```

### Google OAuth poisoning pattern (common blocker)
**Symptom:** `invalid_scope: Bad Request` when calling Sheets/Drive/Docs APIs, even with valid refresh token.

**Root cause:** Credentials file contains scopes the OAuth client_id was NOT provisioned for. This happens when:
1. New integration demands broader scopes (e.g., add spreadsheets scope)
2. Credentials file updated with new scope list
3. Client_id in Google Cloud Console never re-authorized for those scopes
4. Token refresh attempt triggers scope validation → fails before making request

**Why refresh doesn't fix it:** Scope mismatch is pre-authorization. Retrying same token won't help.

**Fix path:**
- Delete/backup the poisoned token file
- Generate NEW OAuth client in Google Cloud Console with correct name (e.g., "FRIDAY")
- Use fresh OAuth 2.0 authorization flow with full scope set in single auth step
- Test with simple API call (e.g., `sheets.spreadsheets().get()`) before batch operations
- Store new token in `~/.hermes/google_token.json` with all scopes in metadata

**Prevention:** Always provision OAuth client with FULL scope set upfront. Never add scopes mid-flight to an existing client_id — create a new client instead.

## Writing new or updated credentials
```python
def update_vault(service, updates: dict):
    vault = get_vault()
    if service not in vault:
        vault[service] = {}
    vault[service].update(updates)
    import os, stat
    path = '/home/hermes/.hermes/vault.json'
    with open(path, 'w') as f:
        json.dump(vault, f, indent=2)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
```

## Instagram cookie lifecycle
- Cookies expire periodically — symptom: enrich endpoint (`/api/v1/users/{uid}/info/`) returns HTML (200 status but `<!DOCTYPE html>`) instead of JSON
- Tag fetch (`/api/v1/tags/{tag}/sections/`) continues working even when enrich is dead — don't confuse the two
- Enrich also fails with `{"message":"feedback_required","is_spam":true}` after heavy use — this is rate limiting, not cookie expiry; wait 30–60 mins
- After receiving new cookies, ALWAYS test enrich on a known UID before launching full scrape
- **Same browser = same fingerprint = stays blocked.** If enrich is rate-limited/flagged, a new sessionid from the SAME browser (even incognito of same browser) won't fix it — the `datr` cookie is the device fingerprint. Need a genuinely different browser (Firefox, Edge, or different Chrome profile with different device ID)
- Cookie-Editor export must come from cgagnier extension (blue icon): https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
- The hotcleaner.com "Cookie Manager" exports encrypted JSON (`{"data":"base64..."}`) — unparseable, reject and ask again
- After writing cookies to vault, confirm with: `requests.get('https://www.instagram.com/api/v1/users/{uid}/info/', ...)` and check `r.text.strip().startswith('{')`

## Gmail scope limitations
- Current scope: `gmail.modify` — can read, label, trash, move
- `batchDelete` (permanent delete) requires `mail.google.com` scope — NOT currently granted
- Workaround: use `trash()` instead — emails auto-purge from Trash after 30 days
- Tanzim is fine with trash-not-delete; it's a safety measure he wants kept

## Rules
- **Always check vault FIRST** — Tanzim explicitly flagged being asked for credentials he's already provided as a failure mode ("every morning I have to connect you")
- Silent credential use — never narrate that you're reading the vault
- If a credential is missing or None, ask once, write immediately, never ask again
- Never log or print raw credential values
- Never store credentials in Hindsight, memory.md, or skills body
- Instagram cookies: update vault immediately after receiving fresh cookies, include `last_updated` date
- **Instagram cookie failure modes — two distinct issues with different fixes:**
  - *Enrich blocked* (HTML on 200): device fingerprinted via `datr` cookie — need cookies from a DIFFERENT browser/device. Same `datr` = same device = still blocked. Wait ~2–3h or use Firefox/Edge.
  - *Write actions blocked* (follow/like failing): hourly rate limit (~60 follows, ~150 likes/hr). Fix: pace at 25–35s between likes, 8–10 min between accounts. A 200 on follow does NOT guarantee it went through — verify with friendship_status.
- Test before any scraping run: `r.status_code == 200 and r.text.strip().startswith('{')` — HTML response means blocked even if status is 200

## Credential Audit & Troubleshooting
When credentials fail or need inventory: use the credential audit workflow documented in `references/google-oauth-scope-troubleshooting.md` and `references/credential-inventory.md`. These include:
- How to discover all token files on the system
- Google OAuth scope mismatch diagnosis and repair
- Multi-token-file strategy (main vault vs. EDITH vs. google_token.json)
- Credential status matrix and refresh tracking

## See also
- `references/google_oauth_setup.md` — Fresh OAuth 2.0 flow for new client creation, token exchange, poisoned-token recovery
- `references/edith_vault_access.md` — EDITH 3FA vault architecture, passphrase requirement, decryption gap, workaround pattern
- `references/instagram_scraping.md` — Instagram API endpoints, scraping patterns, rate limits, personal account benchmark, follower-graph scraping, follow/like action pacing
- `references/gmail_automation.md` — Gmail API patterns, label management, search queries
- `references/gmail_bulk_operations.md` — Bulk inbox scanning, quality-check workflow, trash/label patterns, tested search queries
- `references/google-oauth-scope-troubleshooting.md` — OAuth scope mismatch diagnosis, token file precedence, re-auth workflow
- `references/credential-inventory.md` — service-by-service credential audit, status matrix, refresh schedule

## Gmail lessons (June 2026 session)
- `batchDelete` requires `mail.google.com` scope — current OAuth only has `gmail.modify`, use `trash()` instead
- `trash()` works fine — emails auto-purge after 30 days, Tanzim explicitly wants this as a safety measure
- To create a label and move emails: `labels().create()` then `messages().modify()` with `addLabelIds` + `removeLabelIds: ['INBOX']`
- Keyword search for job emails: search `from:jpmorgan OR from:jpmchase OR subject:jpmorgan` — catches most JPMC variants
- Gmail `messages().list()` maxResults caps at 500; paginate with nextPageToken for full inbox scans
