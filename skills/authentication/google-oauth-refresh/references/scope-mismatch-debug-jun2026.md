# Google OAuth Scope Mismatch — Debug Pattern (Jun 2026)

## Symptom

When attempting to use Google Sheets, Gmail, or Drive APIs via `google-oauth-full.json`, the google-auth library throws:

```
RefreshError: ('invalid_scope: Some requested scopes were invalid. {invalid=[spreadsheets, gmail.modify]}', 
{'error': 'invalid_scope', ...})
```

Or when attempting to create a Google Sheet:

```python
sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
# → RefreshError: invalid_scope
```

## Root Cause

The token file at `~/.hermes/google_oauth_full.json` was created with a `scopes` field listing scopes that were **never actually granted by the OAuth Consent Screen**. When the google-auth library tries to refresh the token, it validates the stored scopes against the actual grant scope set — if there's a mismatch, refresh fails immediately.

**Example:**
- Token file has `"scopes": ["spreadsheets", "gmail.modify"]` in the JSON
- But the OAuth Consent Screen in Google Cloud only configured `gmail.readonly`
- When google-auth library tries to refresh, it sees a mismatch and rejects the token

## Immediate Workaround (for current session)

**Do NOT use google-auth library for refresh.** Use `requests.post()` raw HTTP instead:

```python
import requests
import json

with open('/home/hermes/.hermes/google_oauth_full.json', 'r') as f:
    t = json.load(f)

# Raw HTTP refresh — bypasses scope validation
r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token',
})

if r.status_code == 200:
    new_token = r.json()['access_token']
    print(f"✓ Access token refreshed. Valid for 3600s.")
else:
    print(f"✗ Refresh failed: {r.status_code} {r.text}")
    # If this fails with 400, the refresh token itself is revoked → full re-auth needed
```

**Why this works:** Raw HTTP refresh doesn't validate scopes; it just exchanges the refresh token for a new access token. As long as the refresh token is valid, this succeeds.

## Long-Term Fix

### Option 1: Correct the Consent Screen (Recommended)

1. Go to Google Cloud Console: https://console.cloud.google.com/apis/consent
2. Select the GCP project (e.g., `job-scraping-494906`)
3. Click **Edit App** on the OAuth Consent Screen
4. Under **Scopes**, add all required scopes with exact URLs:
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.labels`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/documents` (NOT `docs`)
   - `https://www.googleapis.com/auth/spreadsheets`
5. Under **Test users**, add `tanzimozer@gmail.com` (or the authorization email)
6. Save all changes
7. **Delete the old token file:** `rm ~/.hermes/google_oauth_full.json`
8. **Full re-auth:** Generate new OAuth link with all 8 scopes, have Tanzim authorize fresh, capture new token
9. Store new token at `~/.hermes/google_oauth_full.json`

### Option 2: Edit Token File Scopes Field (Quick hack)

If the refresh token is still valid and you just want to unblock immediate tasks:

```python
import json

with open('/home/hermes/.hermes/google_oauth_full.json', 'r') as f:
    t = json.load(f)

# Set scopes field to match what was actually granted
t['scopes'] = ['https://www.googleapis.com/auth/gmail.readonly']  # or whatever was actually granted

with open('/home/hermes/.hermes/google_oauth_full.json', 'w') as f:
    json.dump(t, f, indent=2)
```

Then retry the google-auth refresh. **This is temporary** — you'll still be stuck with limited scopes. Long-term you need the Consent Screen fix + full re-auth.

## Prevention

When creating OAuth credentials for Tanzim:
1. **Request ALL 8 scopes upfront** in the authorization URL (don't add scopes incrementally)
2. **Configure all 8 scopes on the OAuth Consent Screen** before generating the auth link
3. **Write the token file with the exact scopes that were actually granted** (not hypothetical future scopes)
4. **Test with raw HTTP refresh BEFORE using google-auth library**

## Session History

- **Jun 8, 2026:** Created `hermes-full-access` GCP project and Desktop client `Hermes CLI`
- **Jun 8, 17:01:** Generated auth link but scopes did not match Consent Screen config
- **Jun 8, 17:02:42:** Corrected scope URL typo (`docs` → `documents`)
- **Jun 8, 17:03:06:** Still failed because `tanzimozer@gmail.com` not added as test user
- **Jun 8, ~17:10:** Tanzim completed OAuth and credentials stored at `~/.hermes/google_oauth_full.json`
- **Jun 9, later session:** Attempted to create Google Sheet using google-auth library → hit `invalid_scope` RefreshError
- **Root cause identified:** Token file was written with scopes that Consent Screen never granted

