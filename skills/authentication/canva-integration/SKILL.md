---
name: canva-integration
description: Canva OAuth integration — authentication, token management, design export, and re-auth flow for Tanzim's Canva account.
tags: [canva, oauth, design, ebook, token-refresh]
category: authentication
---

# Canva Integration

## Credentials location

**Primary storage:** `~/.hermes/vault.json` under `canva` key (kept in sync with desktop CREDENTIALS_MASTER.md)

**Format:** JSON with `client_id`, `client_secret`, `access_token`, `refresh_token`

**Multiple integrations tracked — CLIENT ID HAS CHANGED OVER TIME. Always confirm the current one before building an auth URL:**
1. **TIMBR Client — CURRENT (as of Jun 2026):** `OC-AZ8U1xMKLhDC`. This is the live client ID. Use this unless Tanzim says otherwise.
2. **TIMBR Client — OLD (deprecated):** `OC-AZ5TE93EPw0y` — Redirect: `http://127.0.0.1:8080/callback`. Stored tokens/secret for this ID are dead; do not reuse.
3. **Standalone/Additional Clients** — May be created per project; track in desktop CREDENTIALS_MASTER.md under separate "CANVA — [PROJECT]" section

**CRITICAL — secret is bound to a specific client ID.** A client secret only works with the exact client ID it was generated under. If the client ID changes, the old secret AND the old refresh token are both dead — a refresh attempt returns `client secret is invalid for <client_id>`. Don't burn time trying old secrets against a new ID; ask Tanzim for the current secret of the current client and do a full re-auth.

**Getting the secret from Tanzim — give him the direct click:** `https://www.canva.com/developers/integrations/connect-api` → top nav **Your integrations** → click the integration → Authentication → Client secret → Generate/Reveal → copy immediately (Canva shows it once). Tanzim's standing instruction: ALWAYS give him the click and the numbered steps — never make him hunt. He gets frustrated fast if a step makes him search; lead every hand-off with the exact link + numbered clicks.

**Integration NAME may differ from "TIMBR".** As of Jun 29 2026 the active integration is named **"FRIDAY 2.0"** (client `OC-AZ8U1xMKLhDC`). Don't hard-tell him to click "TIMBR" — say "click your integration" or name the current one. Confirm the name if unsure; the client ID is the source of truth, not the label.

**Navigation trap — docs page ≠ settings page.** Tanzim repeatedly lands on `canva.dev/docs/connect/authentication` (the developer DOCS) instead of his integration's settings. The docs page has an "Authorization URL generator" and a TEMPLATE url with `code_challenge=<CODE_CHALLENGE>` literally unfilled — that template is useless, don't accept it. The real settings live under **Your integrations → [name] → Authentication** on `canva.com/developers/integrations/...`. If he pastes a URL with `<CODE_CHALLENGE>` or `s256` (lowercase) or trailing invisible chars (`%E2%80%AF%E2%81%A0`), he copied the docs template — redirect him to use YOUR generated link instead.

**Registered account:** `tan.biz@icloud.com` (primary)

## Token lifecycle — critical facts

Canva OAuth access tokens **expire every 4 hours**. They auto-refresh via the refresh token. However:

- **Canva revokes refresh tokens** if the OAuth app is re-authorized elsewhere, if the user revokes app access from Canva settings, or after long periods of inactivity
- A revoked refresh token returns `{"error":"invalid_grant","error_description":"Token lineage has been revoked"}`
- This is **not fixable by refreshing** — full re-auth is required

## Refresh flow (normal, token expired)

```python
import json, urllib.request, urllib.parse, os

with open(os.path.expanduser('~/.hermes/.canva_credentials')) as f:
    creds = json.load(f)

data = urllib.parse.urlencode({
    'grant_type': 'refresh_token',
    'refresh_token': creds['refresh_token'],
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret']
}).encode()
req = urllib.request.Request('https://api.canva.com/rest/v1/oauth/token', data=data, method='POST')
resp = json.loads(urllib.request.urlopen(req).read())
creds['access_token'] = resp['access_token']
creds['refresh_token'] = resp.get('refresh_token', creds['refresh_token'])
with open(os.path.expanduser('~/.hermes/.canva_credentials'), 'w') as f:
    json.dump(creds, f)
access_token = resp['access_token']
```

Always save the new refresh token — Canva rotates it on each refresh.

## Error triage — read the error string, don't guess

- `{"error":"invalid_grant","error_description":"Token lineage has been revoked"}` → refresh token revoked. Full re-auth required.
- `{"error":"invalid_grant","error_description":"Invalid refresh token"}` → refresh token doesn't belong to this client ID (e.g. client ID changed). Full re-auth.
- `{"code":"invalid_access_token","message":"Client secret is invalid for OC-..."}` → **secret/client-ID mismatch**, NOT a token problem. The secret you have isn't the one generated under that client ID. Get the correct current secret from Tanzim. Do not keep retrying.
- `{"code":"invalid_access_token","message":"Access token is invalid"}` on an API call → normal expiry, just refresh.
- **In-browser error: "FRIDAY 2.0 has not configured its redirect URL"** (shown on the Canva consent page instead of the Allow button) → the integration has NO redirect URL registered. Fix BEFORE auth can proceed: Your integrations → [name] → Authentication → **Authorized redirects** → Add redirect URL → paste exactly `http://127.0.0.1:8080/callback` → Save (it becomes the default). Then reopen the auth link. This is a one-time setup per integration; confirmed Jun 29 2026 on FRIDAY 2.0.
- **Canva 400 / generic "We couldn't load this page" (Ray ID shown)** → Canva-side transient, NOT a config error. Have him reload (Cmd+R) or reopen the link fresh. Don't go re-checking credentials over this.

## Re-auth flow (PKCE / S256 — current method)

Canva Connect uses PKCE. Generate a fresh verifier+challenge, persist the pending state, build the URL:

```python
import json, secrets, hashlib, base64, urllib.parse, os
cid = 'OC-AZ8U1xMKLhDC'  # confirm current client ID first
redirect = 'http://127.0.0.1:8080/callback'
verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).rstrip(b'=').decode()
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
state = base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b'=').decode()
scopes = 'asset:read asset:write design:content:read design:content:write design:meta:read folder:read folder:write comment:read comment:write profile:read'
params = {'code_challenge_method':'S256','response_type':'code','client_id':cid,
          'redirect_uri':redirect,'scope':scopes,'code_challenge':challenge,'state':state}
url = 'https://www.canva.com/api/oauth/authorize?' + urllib.parse.urlencode(params)
json.dump({'state':state,'code_verifier':verifier,'redirect_uri':redirect},
          open(os.path.expanduser('~/.hermes/.canva_oauth_pending.json'),'w'))
print(url)
```

Send Tanzim that URL with numbered steps. He clicks Allow, lands on a "can't reach this page"/404 screen (expected — nothing listens at 127.0.0.1:8080), then **copies the ENTIRE address-bar URL** back. The full-URL paste is what fixed last time's truncation problem — tell him to paste the whole thing, you extract the `code` yourself.

Then exchange with the verifier (PKCE requires `code_verifier`, not the secret-only flow):

```python
pend = json.load(open(os.path.expanduser('~/.hermes/.canva_oauth_pending.json')))
import urllib.parse as up
code = up.parse_qs(up.urlparse(pasted_url).query)['code'][0]
data = up.urlencode({'grant_type':'authorization_code','code':code,
    'client_id':creds['client_id'],'client_secret':creds['client_secret'],
    'redirect_uri':pend['redirect_uri'],'code_verifier':pend['code_verifier']}).encode()
```

## Re-auth flow (legacy, no PKCE)

When the refresh fails with `invalid_grant`, generate this URL and send it to Tanzim:

```
https://www.canva.com/api/oauth/authorize?client_id=OC-AZ5TE93EPw0y&response_type=code&scope=design%3Acontent%3Aread%20design%3Acontent%3Awrite%20design%3Ameta%3Aread&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2Fcallback
```

He opens it in a browser while logged into Canva as `tan.biz@icloud.com`. The redirect goes to `127.0.0.1:8080` on **his device**, not the VM — so it will 404. That's expected. The auth code is in the URL bar despite the 404:

```
http://127.0.0.1:8080/callback?code=XXXXXXXXXXXX
```

**Important:** Tell Tanzim explicitly that the 404 is expected and the code is in the browser address bar — he will be confused by the error page otherwise (confirmed experience June 2026). The redirect server only exists conceptually; there's nothing listening at `127.0.0.1:8080` on either the VM or his Mac. The 404 is the signal that auth worked.

**Faster alternative:** If auth is blocking a time-sensitive task (like shipping an e-book), suggest he screenshots the Canva pages and send them via WhatsApp. You can analyze them with vision while auth is sorted separately. Don't let auth block the work.

He pastes the full URL (or just the code). Then exchange it:

```python
auth_code = "CODE_FROM_USER"

data = urllib.parse.urlencode({
    'grant_type': 'authorization_code',
    'code': auth_code,
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'redirect_uri': 'http://127.0.0.1:8080/callback'
}).encode()
req = urllib.request.Request('https://api.canva.com/rest/v1/oauth/token', data=data, method='POST')
resp = json.loads(urllib.request.urlopen(req).read())

creds['access_token'] = resp['access_token']
creds['refresh_token'] = resp['refresh_token']
with open(os.path.expanduser('~/.hermes/.canva_credentials'), 'w') as f:
    json.dump(creds, f)
```

Then update the **Software and API** Google Sheet (row for Canva) and the **SOS Recovery Sheet** (API Credentials tab) with the new status.

## Design API

### Get design info (page count, thumbnail)
```python
design_id = "DAHFfAiLO3E"  # from Canva URL

req = urllib.request.Request(
    f'https://api.canva.com/rest/v1/designs/{design_id}',
    headers={'Authorization': f'Bearer {access_token}'}
)
result = json.loads(urllib.request.urlopen(req).read())
# result['design']['page_count'], result['design']['title'], result['design']['thumbnail']
```

### Export design pages as images
```python
export_data = json.dumps({
    "design_id": design_id,
    "format": "png",
}).encode()

req = urllib.request.Request(
    'https://api.canva.com/rest/v1/exports',
    data=export_data,
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
)
result = json.loads(urllib.request.urlopen(req).read())
# Returns a job — poll until complete, then download page URLs
```

Export is async — poll `GET /rest/v1/exports/{export_id}` until `status == "success"`.

## Known designs

- **Seattle Workout Series (e-book):** `DAHFfAiLO3E` — 13 pages, "Workout Series Template"
  - Concept: workout plan + local Seattle gyms + nearby cafés for post-workout + nutrition guide
  - Target audience: 9-to-5 workers aged 22–35 in Seattle
  - Tanzim's background: 10+ years experience, led athlete to national championship in Bangladesh (~15 gold medals, 4 overall/Champion of Champions wins)
  - See `references/seattle-workout-series.md` for full content brief

## Pitfalls

- **Don't use the browser** to open Canva edit URLs — the browser tool times out on Canva reliably (60+ second timeouts confirmed June 2026). Even `browser_navigate` to the Canva homepage times out. Always use the API or ask Tanzim for screenshots.
- **Token expires every 4 hours** — always try a refresh before assuming the stored token is valid.
- **`invalid_grant` = revoked lineage** — cannot be fixed with another refresh. Needs full re-auth via Tanzim clicking the URL.
- **Export API is async** — don't assume the response contains URLs immediately. Poll for completion.
- **Save the rotated refresh token** — Canva rotates the refresh token on every use. If you discard it, you'll need full re-auth sooner.
- **Add Canva to SOS sheet** — the SOS Recovery Sheet (API Credentials tab) didn't have Canva credentials. After any re-auth, update both the Software & API sheet and the SOS sheet.
- **New client ID = skip refresh entirely, go straight to PKCE re-auth.** When Tanzim hands a NEW client ID + secret (the live one rotated again this session to `OC-AZ8U1xMKLhDC`), the old refresh token is bound to the prior client and is already dead. Don't waste cycles trying the new secret against the old refresh token, or old secrets against the new ID — both fail (`invalid_grant` / `client secret is invalid`). The moment the client ID differs from what minted the stored refresh token, save the new creds and build a fresh PKCE auth URL. Confirmed Jun 30 2026 — burned 2 attempts before going straight to re-auth.

## Support files

- `references/seattle-workout-series.md` — content brief and structure for the Seattle Workout Series e-book
