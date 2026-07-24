# Google OAuth 2.0 Auth Flow — Pitfalls & Fixes

## Context
This documents the actual OAuth flow for connecting to Gmail API (and other Google services) as implemented for Tanzim's interview/job search automation.

## Gotchas & Fixes

### 1. Invalid Scope Error (400 bad_request)
**Symptom:** OAuth consent screen returns `Error 400: invalid_scope`
**Cause:** Some requested scopes are not valid or not properly formatted.
**Fix:**
- Use only validated scopes: `gmail.readonly`, `gmail.modify`, `spreadsheets`, `drive.readonly`, `calendar`
- Avoid custom/made-up scopes
- Do NOT request scopes the app hasn't enabled in Google Cloud Console APIs & Services

### 2. Access Blocked — App Not Verified (403 access_denied)
**Symptom:** `Error 403: access_denied — Access blocked: Friday has not completed the Google verification process`
**Cause:** OAuth app is in "testing mode" but no test users added, or attempting to auth with a non-test user.
**Fix:**
- In Google Cloud Console → APIs & Services → OAuth Consent Screen
- Add test user emails under "Test users"
- Authenticate with that exact email (e.g., tanzim.seattle@gmail.com)

### 3. Authorization Code Single-Use Only
**Symptom:** `invalid_grant` error when exchanging code for token, even though code is fresh
**Cause:** Authorization code was already used in a prior token exchange attempt
**Fix:**
- Authorization codes are one-time use only
- If token exchange fails, request a NEW authorization code (re-run the OAuth consent flow)
- Do not retry the same code

### 4. Token Expiry & Refresh
**Symptom:** Gmail API calls fail with 401 Unauthorized after ~1 hour
**Cause:** Access token has expired; refresh token must be used
**Fix:**
- Store refresh_token in token file (comes back with initial code exchange)
- Before any API call, check token expiry and refresh if needed
- Use `google.auth.transport.requests.Request` to handle refresh automatically

```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

### 5. Scope Mismatch on Subsequent Auth
**Symptom:** Adding a new scope (e.g., `gmail.modify`) fails with 400 bad_request
**Cause:** Attempting to add scope to existing authorization; Google expects a fresh auth flow
**Fix:**
- If new scopes are needed, trigger a full new authorization
- Old authorization code cannot be re-used
- Request fresh code from https://accounts.google.com/o/oauth2/auth with updated scopes

## Session-Specific Context (June 2026)
- Project: `friday-499707` (Friday)
- Client ID: `990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com`
- Token file: `~/.hermes/google_token.json`
- Active scopes: `gmail.readonly`, `gmail.modify`, `spreadsheets`, `drive.readonly`, `calendar`
- Refresh token: stored and active

## Testing Quick Reference
```bash
# Check token validity
cat ~/.hermes/google_token.json | jq '.expires_in'

# Verify scopes in current token
cat ~/.hermes/google_token.json | jq '.scope'
```
