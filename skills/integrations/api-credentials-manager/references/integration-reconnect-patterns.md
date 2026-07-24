# Integration Reconnect Patterns

Lessons from the May 26, 2026 integration audit session.

## What to check before asking Tanzim for a new key

Always check these locations first:
```bash
ls ~/.hermes/.trello_credentials
ls ~/.hermes/.wix_credentials.json
ls ~/.hermes/.webflow_credentials.json
ls ~/.hermes/.canva_credentials
ls ~/.hermes/google_token.json
```
And check memory/hindsight for tokens stored in session context.

**Result of this session:** Trello (May 21 key), Webflow (May 9 token), and Canva credentials were all already on disk — only Canva needed a fresh auth due to revoked lineage.

## Wix IST Token

- Source: manage.wix.com → Account Settings → API Keys → Generate API Key
- Format: `IST.eyJ...` (long JWT)
- Test with: `POST https://www.wixapis.com/site-list/v2/sites/query` body `{"query":{}}`
- Correct response includes `sites[]` array with `displayName`, `id`
- TIMBR site ID: `ab465896-e5c3-4f5d-bc9d-7f495a6d6be1`
- Token stored: `~/.hermes/.wix_credentials.json`

## Webflow Bearer Token

- Format: 64-char hex string
- Test: `GET https://api.webflow.com/v2/token/authorized_by` with `Authorization: Bearer <token>`
- Returns `{id, email, firstName, lastName}` on success
- Account: tan.biz@icloud.com
- Token stored: `~/.hermes/.webflow_credentials.json`

## Canva Full Re-auth (when lineage revoked)

When `refresh_token` returns `invalid_grant: Token lineage has been revoked`:
1. Use PKCE flow with `secrets.token_urlsafe(64)` as verifier
2. Save pending state to `~/.hermes/.canva_oauth_pending.json`
3. User opens auth URL, clicks Allow, browser fails at localhost — that's expected
4. User copies full callback URL from address bar
5. Extract `code` from URL, exchange using saved `code_verifier` and `redirect_uri`
6. Save new `access_token` + `refresh_token` to `~/.hermes/.canva_credentials`
7. Test with `GET https://api.canva.com/rest/v1/users/me`

Client ID: `OC-AZ5TE93EPw0y` | Redirect URI: `http://127.0.0.1:8080/callback`

## Trello (simple, never expires)

- API Key + Token at trello.com/app-key
- Test: `GET https://api.trello.com/1/members/me?key=KEY&token=TOKEN`
- Token stored: `~/.hermes/.trello_credentials` (JSON with `api_key` and `token`)
- Account: tanzimozer1

## What was skipped (May 26, 2026)

| Service | Reason skipped |
|---|---|
| Substack | Cookie-based only, expires periodically — reconnect when needed |
| OpenRouter | Claude Max $200/mo covers the use case (context compression) |
| RapidAPI/JSearch | TerraJob uses JobSpy directly — no key needed unless job search ramps up |
