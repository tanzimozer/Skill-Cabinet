# Google OAuth Token Refresh & Diagnostics

## Token Refresh Pattern (User Credentials)

When a Google OAuth user credential token expires (access_token missing or stale), use this pattern:

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path

token_file = Path("/home/hermes/.hermes/google_token.json")

# Load credentials from file
creds = Credentials.from_authorized_user_file(str(token_file))

# Check and refresh if expired
if creds.expired:
    request = Request()
    creds.refresh(request)
    
    # Write refreshed token back to file
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'id_token': getattr(creds, 'id_token', None),
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
        'type': 'authorized_user'
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=2)
```

**Key points:**
- `Request()` from `google.auth.transport.requests` handles the refresh transparently
- Always write the refreshed token back to disk (refresh_token and new access_token)
- If `creds.refresh_token` is missing, the token cannot be refreshed — regenerate via OAuth flow

---

## Google Products Connection Test

Once token is refreshed, verify connectivity to all Google products:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

creds = Credentials.from_authorized_user_file(str(token_file))

# Gmail
try:
    gmail = build('gmail', 'v1', credentials=creds)
    gmail.users().messages().list(userId='me', maxResults=1).execute()
    print("✓ Gmail connected")
except HttpError as e:
    print(f"✗ Gmail: {e.resp.status}")

# Google Drive
try:
    drive = build('drive', 'v3', credentials=creds)
    drive.files().list(pageSize=1, spaces='drive').execute()
    print("✓ Drive connected")
except HttpError as e:
    print(f"✗ Drive: {e.resp.status}")

# Google Sheets (scope test only — no list API)
try:
    sheets = build('sheets', 'v4', credentials=creds)
    print("✓ Sheets scope enabled")
except HttpError as e:
    print(f"✗ Sheets: {e.resp.status}")

# Google Docs
try:
    docs = build('docs', 'v1', credentials=creds)
    print("✓ Docs scope enabled")
except HttpError as e:
    print(f"✗ Docs: {e.resp.status}")

# Google Calendar
try:
    calendar = build('calendar', 'v3', credentials=creds)
    calendar.calendarList().list().execute()
    print("✓ Calendar connected")
except HttpError as e:
    # 403 with "accessNotConfigured" = API disabled in Cloud project
    print(f"✗ Calendar: {e.resp.status} — {e.error_details}")
```

**Common errors:**
- **403 accessNotConfigured:** API disabled in Google Cloud project. Enable via Cloud Console.
- **401 Unauthorized:** Token invalid or refresh failed. Regenerate OAuth credentials.
- **scope issues:** Token lacks required scope. Re-authorize with full scope set.

---

## Diagnostic Checklist

When credentials exist but tests fail:

1. **Token file exists?** → `/home/hermes/.hermes/google_token.json`
2. **Client secret exists?** → `/home/hermes/.hermes/google_client_secret.json`
3. **Token has refresh_token?** → Can be refreshed if expired
4. **Token has scopes?** → Check `token_data['scopes']` for required APIs
5. **Scopes include target API?** → e.g., `https://www.googleapis.com/auth/calendar` for Calendar
6. **API enabled in project?** → Visit Google Cloud Console, search API name, enable it
7. **After enabling API, wait 2–5 minutes** for propagation before retesting

---

## Session Reference
- Google OAuth token refresh & Calendar API fix (June 11, 2026): Credentials were stale; refresh succeeded. Calendar API was disabled in project 313611152308 — requires manual Cloud Console enable.
