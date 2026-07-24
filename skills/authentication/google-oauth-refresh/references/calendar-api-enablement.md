# Calendar API Enablement Pattern

## Context
Google Calendar API is frequently disabled in GCP projects even when OAuth credentials exist and other Google APIs (Gmail, Drive, Sheets, Docs) are active. Attempting Calendar API calls with a disabled API returns HTTP 403 `accessNotConfigured` — confusing because the OAuth token is valid.

## Quick Fix
1. Go to: `https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project=<PROJECT_ID>`
   - Replace `<PROJECT_ID>` with the value from `google_token.json` → `client_id` field (extract numeric part before the `.apps.googleusercontent.com` suffix)
   - Example: `313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com` → project `313611152308`
   - Or read from the `google_oauth_client.json` file's `project_id` field

2. Click **"Enable"** button on that page
3. Wait ~30 seconds for the API to become available
4. Refresh the OAuth token using `google-oauth-refresh` skill (raw HTTP option B)
5. Calendar API calls now work

## Why This Happens
- OAuth scopes in the token include `https://www.googleapis.com/auth/calendar` (the permission), but the GCP *project* still needs the *API* (the service) explicitly enabled
- These are two separate configurations: OAuth scope (user's permission) and GCP API (project's capability)
- Happens often because projects are set up with Drive/Sheets/Docs but Calendar is added later in the credential refresh process

## Verification
After enabling, verify with a simple Calendar API call:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

with open('/home/hermes/.hermes/google_token.json', 'r') as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)
service = build('calendar', 'v3', credentials=creds)  # Note: v3, NOT v4
calendars = service.calendarList().list().execute()
print(f"✅ Found {len(calendars.get('items', []))} calendars")
```

If this returns 200, Calendar API is live. If 403 with `accessNotConfigured`, the GCP project still has the API disabled.

## Notes
- Calendar API version is always `v3` — `v4` does not exist
- Some GCP projects ship with Calendar disabled by default; others disable it to save quota
- The vault file (vault.json) may show Calendar in scopes even if the API is disabled — scope and API are independent configurations
