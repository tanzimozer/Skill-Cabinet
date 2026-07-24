# Google OAuth Authorization Flow — Session June 9, 2026

## Quick Reference
1. Create OAuth client in Google Cloud Console
2. Generate authorization link with scopes
3. User clicks link, approves, gets redirected
4. Extract auth code from redirect URL
5. Exchange code for tokens (access + refresh)
6. Store tokens in vault.json
7. Test with Sheets/Drive/Gmail API immediately

## Step-by-Step (Session Example)

### Create Client
- Project: job-scraping-494906
- Client type: Desktop application
- Name: FRIDAY (descriptive, not generic)
- Save Client ID + Client Secret

### Generate Auth Link
```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com&
  redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&
  response_type=code&
  scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.modify+
        https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly+
        https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send+
        https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar+
        https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive+
        https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets+
        https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdocuments&
  access_type=offline&
  prompt=consent
```

### User Authorization
- User clicks link
- Signs in with account (tanzim.seattle@gmail.com)
- Approves all permissions
- Browser redirects to: `http://localhost:8080/?code=AUTH_CODE&state=...`

### Extract Code
From redirect URL, copy the `code=` parameter:
```
code=4/0AdkVLPyM47S7LSZqOyQHhudkSFoCdJWQOe0YR7PHacOAnpveFQy33s3VfvrkrrVzlD65jA
```

### Exchange for Tokens
```python
import requests

code = "4/0AdkVLPyM47S7LSZqOyQHhudkSFoCdJWQOe0YR7PHacOAnpveFQy33s3VfvrkrrVzlD65jA"
client_id = "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>"
redirect_uri = "http://localhost:8080/"

payload = {
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code",
}

response = requests.post("https://oauth2.googleapis.com/token", data=payload)
tokens = response.json()

# tokens now has: access_token, refresh_token, expires_in, token_type
```

### Store in vault.json
```json
{
  "google": {
    "oauth": {
      "access_token": "ya29.a0AT3oNZ_UZ-UWasHOUd1jNX1kMfe1Aqb6...",
      "refresh_token": "<REDACTED_OAUTH_TOKEN>",
      "token_uri": "https://oauth2.googleapis.com/token",
      "client_id": "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com",
      "client_secret": "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>",
      "scopes": [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/documents"
      ],
      "type": "authorized_user"
    }
  }
}
```

### Test Immediately
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials(
    token=tokens['access_token'],
    refresh_token=tokens['refresh_token'],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret,
    scopes=[...]
)

# Test Sheets API
sheets = build('sheets', 'v4', credentials=creds)
spreadsheet = sheets.spreadsheets().create(body={'properties': {'title': 'Test Sheet'}}).execute()
print(f"✓ Sheet created: {spreadsheet.get('spreadsheetId')}")
```

## Key Points
- **Redirect URI:** Must be registered in Google Cloud Console AND match the authorization link
- **Scopes:** Declare all scopes upfront; can't add more without re-authorization
- **Refresh token:** Lasts indefinitely (unlike access token which expires in ~1 hour)
- **Test:** Always test token exchange immediately with a real API call
- **Common error:** `invalid_scope` means the client_id wasn't provisioned for those scopes → delete and recreate the client
