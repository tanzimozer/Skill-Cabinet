---
name: google-api-integration
category: integrations
description: OAuth 2.0 patterns for Gmail, Drive, Docs, Sheets, Chat. Use googleapiclient library (not raw HTTP) for Drive uploads.
---

# Google API Integration (Gmail, Drive, Docs, Sheets, Chat)

Durable patterns for Google API authentication and operations via OAuth 2.0.

## Critical Pattern: Drive File Upload

**BROKEN:** Direct multipart HTTP to `/files?uploadType=multipart` returns 400 Parse Error.

**WORKS:** Use `googleapiclient.http.MediaFileUpload`:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = Credentials(
    token=token_data['access_token'],
    refresh_token=token_data.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
)

drive_service = build('drive', 'v3', credentials=creds)

file_metadata = {'name': 'filename.pdf', 'mimeType': 'application/pdf'}
media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, webViewLink'
).execute()
```

## Common Operations

**Move file to folder:**
```python
drive_service.files().update(
    fileId=file_id,
    addParents=folder_id,
    fields='id, parents'
).execute()
```

**List files in folder:**
```python
files = drive_service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    spaces='drive',
    fields='files(id, name, webViewLink)'
).execute()
```

## Token Management

Credentials auto-refresh when expired. Manual refresh:
```python
refresh_data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'refresh_token': refresh_token,
    'grant_type': 'refresh_token',
}
response = requests.post('https://oauth2.googleapis.com/token', data=refresh_data)
```

## OAuth Scopes

- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/chat`

---

**Key lesson (Jun 8, 2026):** Multipart HTTP requests to Drive API fail with 400 Parse Error. Always use google-auth library + discovery build() for file operations.
