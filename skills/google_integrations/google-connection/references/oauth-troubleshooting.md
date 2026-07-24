# Google OAuth Troubleshooting — Error Reference & Recovery

## Error: `Error 403: insufficient scopes` (Gmail Delete Operations)

**Scenario:** User tries to delete Gmail messages but receives 403 insufficient permissions.

**Root Cause:** Token was issued with `gmail.readonly` only. The delete operation requires `gmail.modify` scope, which was not requested during initial authentication.

**Fix:**
1. Delete the old token file: `rm ~/.hermes/google_token.json`
2. Regenerate the OAuth auth link with `gmail.modify` scope included
3. User re-authenticates and approves the new scopes
4. Exchange the new authorization code for a fresh token
5. The Python client will now have modify/delete permissions

**Code Pattern:**
```python
# Ensure scopes include gmail.modify
scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',  # <-- REQUIRED for deletes
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar'
]
```

---

## Error: `Error 400: invalid_scope` (OAuth Authorization)

**Scenario:** User is sent an OAuth auth link but gets `Error 400: invalid_scope` from Google.

**Root Cause:** One or more scope URLs are malformed, misspelled, or not recognized by Google. Common mistakes:
- Using short names: `gmail`, `drive` instead of full URLs
- Typos in scope URL
- URL encoding issues (spaces not converted to `+`)

**Fix:**
1. Verify all scopes are exact full URLs matching Google's documentation
2. Ensure spaces between scopes are either literal spaces (gets URL-encoded to `+`) or are already encoded as `%20`
3. Do NOT use abbreviations or custom scope names

**Valid Scope Format:**
```
https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify
```

**URL-Encoded Format** (in query params):
```
https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify
```

---

## Error: `invalid_grant` (Token Exchange)

**Scenario:** User copies the authorization code and sends it back, but token exchange fails with `{"error": "invalid_grant", "error_description": "Bad Request"}`.

**Root Cause:** The authorization code has already been used, or it has expired (30-minute timeout).

**Fix:**
1. User must **immediately** copy the authorization code after approval (before the 30-min window closes)
2. Each code is **single-use** — once exchanged for a token, it cannot be reused
3. If exchange fails, user must click the auth link **again** to get a new code
4. Do not attempt to reuse or retry with the same code

**Code Validation:**
```python
response = requests.post(token_url, data=payload)
token_data = response.json()

if 'error' in token_data:
    # This code was already used or has expired
    print(f"Code unusable: {token_data['error']}")
    # User must get a fresh code
else:
    # Success — save token
    with open(token_file, 'w') as f:
        json.dump(token_data, f)
```

---

## Error: Stale Token After Re-authentication

**Scenario:** After re-authenticating with new scopes and saving a fresh token, the Python client still uses the old token with old scopes.

**Root Cause:** The `google-auth` Python library caches the Credentials object in memory. Reading the file again doesn't reset the cache.

**Fix:**
1. **Delete the old token file** before saving the new one
2. **Force a fresh file read** in your script (read after save, or start a new process)
3. Recreate the `Credentials` object from scratch

**Code Pattern:**
```python
import os
import json

# Step 1: Delete old token
token_file = os.path.expanduser('~/.hermes/google_token.json')
if os.path.exists(token_file):
    os.remove(token_file)

# Step 2: Exchange new code and save
# ... (exchange code for token) ...
with open(token_file, 'w') as f:
    json.dump(new_token_data, f, indent=2)

# Step 3: Fresh load
with open(token_file, 'r') as f:
    token_data = json.load(f)

# Step 4: Create new Credentials object
creds = Credentials(...)
service = build('gmail', 'v1', credentials=creds)
```

---

## Error: Unverified App Warning

**Scenario:** During OAuth login, user sees: "Access blocked: Friday has not completed the Google verification process. The app is currently being tested, and can only be accessed by developer-approved testers."

**Root Cause:** Google Cloud project OAuth app is in testing mode and user is not listed as an approved tester.

**Fix:**
1. Go to **Google Cloud Console** → **APIs & Services** → **OAuth consent screen**
2. Scroll to **Test users**
3. Click **Add user**
4. Enter the test user email (e.g., `tanzim.seattle@gmail.com`)
5. Click **Save**
6. User tries the auth link again — it should now proceed

**Note:** This is a Google policy for unverified apps. Once the app is published/verified, this restriction is lifted.

---

## Error: `KeyError: 'access_token'` When Loading Token

**Scenario:** Script crashes when trying to access `token_data['access_token']` — the key doesn't exist.

**Root Cause:** The token file contains an error response from Google (e.g., `{"error": "invalid_grant"}`) instead of a valid token.

**Fix:**
1. Check the token file: `cat ~/.hermes/google_token.json`
2. If it contains `"error"` key, the token exchange failed
3. Delete the file and re-authenticate from scratch
4. Check token exchange response for errors before saving

**Safe Loading Code:**
```python
with open(token_file, 'r') as f:
    token_data = json.load(f)

if 'error' in token_data:
    print(f"Invalid token: {token_data['error']}")
    # Delete and re-auth
    exit(1)

# Safe to use now
access_token = token_data['access_token']
```

---

## Reference: Valid Google OAuth Scopes

For Gmail, Drive, Sheets, Calendar operations:

| Operation | Scope |
|-----------|-------|
| Read emails | `https://www.googleapis.com/auth/gmail.readonly` |
| Read + modify/delete emails | `https://www.googleapis.com/auth/gmail.modify` |
| Read/write Sheets | `https://www.googleapis.com/auth/spreadsheets` |
| Read Drive files | `https://www.googleapis.com/auth/drive.readonly` |
| Read/write Drive | `https://www.googleapis.com/auth/drive` |
| Read/write Calendar | `https://www.googleapis.com/auth/calendar` |
| Read Docs | `https://www.googleapis.com/auth/documents.readonly` |

Always use the full URL form. Never abbreviate.

---

## Session Reference: June 17, 2026

This reference was created after troubleshooting Tanzim's Google OAuth flow for gmail-connection skill. Key issues encountered:

1. Scope validation error (400) — resolved by using exact scope URLs
2. Insufficient scopes (403) on delete — user was added to test users, then re-authed with `gmail.modify`
3. Code reuse error (invalid_grant) — explained that codes are single-use
4. Stale token caching — fixed by deleting old token file before saving new one
5. Unverified app warning (403) — resolved by adding user to OAuth consent screen test users

See skill `google-connection` for recovery steps and code patterns.
