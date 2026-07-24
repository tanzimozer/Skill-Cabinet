---
name: oauth-troubleshooting
description: Diagnose and fix OAuth credential failures — scope misconfiguration, token expiry, missing files. Don't retry blindly.
type: workflow
domains: [integrations, credentials, google-api]
trigger: OAuth credential error; token refresh fails; API call returns 'invalid_scope' or 'invalid_grant'
---

# OAuth Troubleshooting

When an OAuth credential call fails, **diagnose the root cause before retrying the same method.** Common failures cluster into three distinct buckets — each needs a different fix.

## Failure Diagnosis

### 1. Scope Misconfiguration (Most Common)
**Signal:** Error message contains `invalid_scope` with a list of rejected scopes.

**Why it matters:** The credentials file has scopes the client_id is not authorized to use. Retrying with refresh will fail again. Retrying without refresh will also fail.

**Fix:** 
- Inspect `~/.hermes/google_oauth_full.json` for the `scopes` array
- Identify which scopes are invalid (error message lists them)
- Either:
  - Remove invalid scopes from the file and reload, OR
  - Regenerate credentials with the correct scope set (full OAuth re-auth)
- Test with a simple, non-destructive API call (e.g., `gmail.readonly` list, not modify)

**Do NOT:**
- Retry the same call multiple times hoping it works
- Assume the token is expired when scopes are the problem
- Try to refresh a token with invalid scopes configured

### 2. Expired Token
**Signal:** Error message contains `invalid_grant` or `access_token_expired`; scope validation passes.

**Fix:** Call `refresh(Request())` with a fresh Request object.

### 3. Missing Credentials File
**Signal:** File not found at expected path.

**Fix:** Re-authenticate with OAuth flow or verify path in config.

## Workflow: First Time Hitting an OAuth Error

1. **Read the error message carefully.** Look for `invalid_scope`, `invalid_grant`, `access_token_expired`, or similar keywords.
2. **If you see `invalid_scope`:** Stop. Do not retry. Check the credentials file for scope mismatch. See "Scope Misconfiguration" above.
3. **If you see `invalid_grant` or expiry language:** Refresh is the right move. Retry once with fresh Request.
4. **If you see a path/file error:** Check file exists; regenerate if missing.
5. **After identifying root cause, act once.** Don't loop through multiple attempted fixes for the same diagnosis.

## References
- `references/gmail-scope-error-scale-credentials.md` — Tanzim's Scale creds config issue, Jan 2026

