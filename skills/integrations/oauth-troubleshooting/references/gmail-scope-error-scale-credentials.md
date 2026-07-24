# Gmail Scope Error — Scale Credentials Config (Jan 2026)

## Error Pattern
```
google.auth.exceptions.RefreshError: ('invalid_scope: Some requested scopes were 
invalid. {invalid=[spreadsheets, gmail.modify]}', 
{'error': 'invalid_scope', 'error_description': 'Some requested scopes were invalid...'
```

## Context
- File: `~/.hermes/google_oauth_full.json` (Tanzim's Scale credentials)
- Trigger: Attempted `gmail.users().messages().list()` call
- User assertion: "They are not expired" — correctly signalled the issue was NOT token expiry

## What Happened
1. First attempt: tried to refresh token, hit `invalid_scope` error
2. Second attempt: tried without refresh, hit the same error (scope validation happens before API call)
3. Root cause: credentials file has `scopes: ['spreadsheets', 'gmail.modify']` but the OAuth client_id was not authorized for those scopes

## Lesson
**Do not assume token expiry.** When you see `invalid_scope` in the error, the scope array in the credentials file does not match what the OAuth client_id was provisioned for. Refreshing won't fix it; you need to either:
- Regenerate the credentials with the correct scopes, OR
- Strip invalid scopes from the stored file and reload

This is distinct from `invalid_grant` (which IS token expiry).

## For Future Sessions
If accessing Tanzim's Gmail via Scale credentials, verify the scopes are minimally `['https://www.googleapis.com/auth/gmail.readonly']` or equivalent read-only set. Do NOT attempt refresh on `invalid_scope` errors.

