# OAuth Setup Session — June 17, 2026

## Credentials Created

**Project:** Friday (friday-499707)  
**Client Type:** Desktop Application  
**Client ID:** `768192326455-77dgh26ibi6eraoh5jafen8ukkae1os1.apps.googleusercontent.com`  
**Client Secret:** `<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>`  
**Redirect URI:** `http://localhost`  
**Status:** Active, test user added, ready for authorization

Saved to: `~/.hermes/google_oauth_client.json`

## Error Sequence & Resolutions

### Error 1: Invalid Client (blocked "job-scraping-494906" client)
**URL:** `accounts.google.com/signin/oauth/error?authError=Cg9pbnZhbGlkX3JlcXVlc3Q...`  
**Message:** "You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy for keeping apps secure."

**Root Cause:** Old client ID from an earlier project was blocked by Google's validation system.

**Resolution:** Created new client ID from scratch in a fresh OAuth project ("Friday" instead of "job-scraping").

---

### Error 2: Invalid Scope (Error 400: invalid_scope)
**Message:** "Some requested scopes were invalid."  
**URL:** `accounts.google.com/signin/oauth/error?authError=...invalid_scope...`

**Attempted Scopes (WRONG):**
- `https://www.googleapis.com/auth/gmail.modify` ❌ (used instead of `.readonly`)
- `https://www.googleapis.com/auth/documents` ❌ (not a real scope)

**Root Cause:** Typos and non-existent scope URIs. The Google OAuth server rejected the entire request because one scope was invalid.

**Resolution:** Use ONLY validated scopes:
- `https://www.googleapis.com/auth/gmail.readonly` ✓
- `https://www.googleapis.com/auth/spreadsheets` ✓
- `https://www.googleapis.com/auth/drive.readonly` ✓
- `https://www.googleapis.com/auth/calendar` ✓

---

### Error 3: App Not Verified (Error 403: access_denied)
**Message:** "Access blocked: Authorization Error"  
**Details:** "Friday has not completed the Google verification process. The app is currently being tested, and can only be accessed by developer-approved testers."

**Root Cause:** OAuth app was in "testing" mode. User (tanzim.seattle@gmail.com) was not listed as a test user, so Google blocked access.

**Resolution:** 
1. Go to **OAuth consent screen** in Google Cloud Console
2. Scroll to **Test users** section
3. Add `tanzim.seattle@gmail.com`
4. Wait ~1 minute for propagation
5. Retry authorization

---

## Key Learnings

1. **Always create new client credentials from a fresh project.** Old clients accumulate Google's trust issues. If you get a blanket rejection ("doesn't comply with policy"), start fresh.

2. **Scope validation is strict.** A single invalid scope URI causes the entire request to fail. No partial successes. Verify every scope name against the official Google OAuth documentation.

3. **Test user addition is mandatory for unverified apps.** Even with correct scopes and client setup, Google won't grant access to an unverified app unless the user is explicitly added as a test user.

4. **Redirect URI must match exactly.** For desktop apps, use `http://localhost` (not `https`, not with a path). This is what Google expects for the localhost flow.

5. **Include `access_type=offline` and `prompt=consent` in the auth URL.** These ensure:
   - `access_type=offline` → Returns refresh_token (needed for token refresh)
   - `prompt=consent` → Forces re-consent (sometimes needed to recover refresh_token if it was previously lost)

---

## Timeline

| Time | Action | Result |
|------|--------|--------|
| T+0 | Created new Google Cloud project "Friday" | ✓ |
| T+5m | Enabled Gmail, Drive, Sheets, Calendar APIs | ✓ |
| T+8m | Configured OAuth consent screen (External, app name, emails) | ✓ |
| T+10m | Attempted first auth with old client ID | ✗ Error: invalid_request (blocked client) |
| T+12m | Attempted auth with invalid scopes | ✗ Error: invalid_scope |
| T+15m | Attempted auth with unverified app | ✗ Error: access_denied (app not verified) |
| T+18m | Added test user to consent screen | ✓ |
| T+20m | Created fresh desktop client (Friday project) | ✓ |
| T+22m | Generated auth URL with correct scopes & localhost redirect | ✓ |
| T+25m | User approved, received authorization code | ✓ |

---

## Next Steps (for next session)

- Exchange authorization code for tokens using Step 6 in SKILL.md
- Save refresh token to `~/.hermes/google_token.json`
- Test Gmail API with a simple query (list unread emails)
- Scan inbox for "thank you for applying" emails (original task)
