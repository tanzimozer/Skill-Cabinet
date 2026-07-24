---
name: oauth-flow-setup
description: Complete OAuth 2.0 authorization code + PKCE flows end-to-end for third-party API integrations. Handles credential storage, PKCE challenge generation, token exchange, refresh logic, and connection verification.
triggers:
  - User asks to connect to an API via OAuth
  - Setting up Canva API, Google API, Notion API, or similar OAuth-protected service
  - Get API access for a service requiring user authorization
  - Token refresh or connection expired scenarios
---

## Overview

OAuth flows require **upfront preparation** and **minimal user interaction**. The user should click one link and paste one callback URL — everything else (PKCE generation, token exchange, refresh setup, verification) happens automatically.

## Anti-pattern (what NOT to do)

❌ **Incremental back-and-forth asking for parameters one at a time**  
❌ Explaining OAuth theory before acting  
❌ Asking "do you want me to..." when you can just prep the work  
❌ Making the user navigate multiple manual steps

## Correct workflow

### 1. Gather credentials upfront (one ask, or read from context)
- Client ID
- Client Secret  
- Redirect URI (use `http://localhost:8080/callback` as default for local flows)

Save immediately to `~/.hermes/.<service>_credentials` with 600 permissions.

### 2. Generate PKCE challenge automatically
```python
import secrets, base64, hashlib

code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8').rstrip('=')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).decode('utf-8').rstrip('=')
```

Save `code_verifier` to credentials file (needed for token exchange).

### 3. Build and send authorization URL (one message)
Include:
- `client_id`
- `redirect_uri`
- `response_type=code`
- `scope` (space-separated, read from API docs or user request)
- `code_challenge` + `code_challenge_method=S256`
- `state` (optional but recommended for CSRF protection)

**Format the URL cleanly** — no preamble, just the clickable link with one-line instruction:

> Click this, authorize, then paste the callback URL here: [URL]

### 4. Prep token exchange script while waiting
Write `/tmp/<service>_token_exchange.py` that:
- Takes callback URL as arg
- Extracts `code` from query params
- POSTs to token endpoint with `grant_type=authorization_code`, the code, `code_verifier`, client credentials
- Saves `access_token`, `refresh_token`, `expires_in` back to credentials file
- Tests connection with a simple API call (e.g. `/users/me`)
- Prints success/failure clearly

**Deploy a subagent** (if <the action codeword> given) to monitor for the callback URL and run the script automatically when received.

### 5. Implement refresh logic
Write `/tmp/<service>_refresh.py` with:
- `refresh_access_token()` — uses refresh token to get new access token
- `get_valid_token()` — checks expiry, auto-refreshes if needed (5min buffer), returns valid token

Make this importable so future scripts can just call `get_valid_token()` without thinking about expiry.

### 6. Verify end-to-end
After token exchange:
- Make a test API call
- Confirm refresh works
- Report connection status in **one line**: ✅ Connected to [Service] API — access valid for 4h, auto-refresh configured.

## User preferences (Tanzim-specific)

- **Simplify, don't complicate.** If OAuth needs 6 steps, do 5 silently and ask for 1.
- **Deploy subagents for async waiting.** Don't sit idle waiting for user input when a subagent can monitor and act.
- **Prep executable scripts upfront.** Write the token exchange and refresh scripts *before* asking for the callback URL, not after.
- **No verbose explanations of OAuth theory** unless explicitly asked "how does this work?"
- **Fresh flows over provided files:** When credentials are offered (JSON files, PAT tokens, etc.), **always verify whether the user wants a fresh OAuth flow independent of those files.** Signal: user says "use a fresh link, nothing to do with the json i gave you". If so, ignore the provided file entirely and initiate a new authorization from scratch. This is a deliberate workflow choice — respect it without assuming.
- **SPEED-FIRST DELIVERY (Jun 8, 2026).** User explicitly rejects multi-paragraph walkthroughs mid-OAuth flow. When setting up OAuth: (1) generate the auth link with minimal preamble, (2) give numbered steps ULTRA-CONDENSED (numbers only, one line per step, no explanation), (3) when code arrives, exchange it silently and report result in one line. Never ask "should I do X" when you can do it and report. Example bad: "Here's the link. To authorize, you click it, then you'll see a page, then you paste the code...". Example good: "**STEP 1:** Click link. **STEP 2:** Authorize. **STEP 3:** Copy code, paste here." The preamble is death.

## Common pitfalls

- **Missing PKCE** → 400 Bad Request. Always include `code_challenge` and `code_challenge_method=S256` for modern OAuth flows.
- **Scope errors** → Verify scopes are enabled in the app settings (Developer Portal / API Console). You can't request scopes not pre-approved.
- **CORS errors on token exchange** → Token requests MUST come from backend (terminal/script), never from browser JS.
- **Forgetting to save code_verifier** → You need it for the token exchange. Save it immediately after generation.
- **Not implementing refresh** → Access tokens expire (often 1-4 hours). Refresh token can last 6-12 months. Implement auto-refresh or the connection dies after 4 hours.

## References

- **Google Cloud Console setup from scratch:** See `references/google-cloud-console-oauth-setup.md` for step-by-step GCP project creation, API enablement, consent screen configuration, and OAuth client credential generation.
- PKCE spec: https://datatracker.ietf.org/doc/html/rfc7636
- OAuth 2.0 spec: https://datatracker.ietf.org/doc/html/rfc6749
