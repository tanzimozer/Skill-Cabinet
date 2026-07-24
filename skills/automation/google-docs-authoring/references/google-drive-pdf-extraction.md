# Google Drive — PDF Download & Text Extraction (July 2026)

## Setup
Credentials are in `~/.hermes/vault.json` under `google`. Token file path is at `vault['google']['token_file']`.

## Pattern: Download a file from Drive

```python
import json, io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

with open('/home/hermes/.hermes/vault.json') as f:
    vault = json.load(f)

token_file = vault['google']['token_file'].replace('~', '/home/hermes')
with open(token_file) as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['token'],
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
)

drive = build('drive', 'v3', credentials=creds)

# Download binary file (PDF, DOCX, etc.)
file_id = '<FILE_ID>'
request = drive.files().get_media(fileId=file_id)
buf = io.BytesIO()
downloader = MediaIoBaseDownload(buf, request)
done = False
while not done:
    _, done = downloader.next_chunk()

with open('/tmp/output.pdf', 'wb') as f:
    f.write(buf.getvalue())
```

## PITFALL: export vs get_media
- `files().export_media()` — only works for **Google Docs/Sheets/Slides** (native Google formats)
- `files().get_media()` — use for **PDF, DOCX, and all binary uploads**
- Mixing them throws `403 "Export only supports Docs Editors files."`

## Pattern: Extract text from PDF
Use `pdfplumber` — already installed in the Hermes venv.

```python
# Always use the Hermes venv python
import subprocess
result = subprocess.run(
    ['/home/hermes/.hermes/hermes-agent/venv/bin/python3', '-c', '''
import pdfplumber
with pdfplumber.open("/tmp/output.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            print(text)
'''], capture_output=True, text=True)
print(result.stdout)
```

Or directly from execute_code (which uses the Hermes venv):
```python
import pdfplumber
with pdfplumber.open('/tmp/output.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            print(text)
```

## Search for files
```python
results = drive.files().list(
    q="name contains 'resume' and trashed=false",
    fields="files(id, name, mimeType, modifiedTime)",
    orderBy="modifiedTime desc",
    pageSize=20
).execute()
files = results.get('files', [])
```

## Tanzim's resume file IDs (as of July 2026)
- Main engineering CV PDF: `1uAq50DzGc8kyfN09jrVgFb3JXQfZq58L`
- Brex resume PDF: `1dnEiM8-xWAOXA7vQFJ3VhDDwcJMev_Xv`
- Engineering CV DOCX: `1_4kXTlRLXAR-rCpc7KmaUTvBPxDtf0HO`
