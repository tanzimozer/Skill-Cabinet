---
name: google-drive-bulk-operations
description: "Bulk file operations on Google Drive — download, unzip, upload, delete, scan. Patterns for large-scale Drive migrations and processing jobs."
category: productivity
tags: [google-drive, bulk, migration, upload, download, ocr, pipeline]
version: 1.0.0
created: 2026-05-31
---

# Google Drive Bulk Operations

Patterns for large-scale Drive file operations — migrations, scans, transforms.

## When to use
- Moving/copying many files between Drive folders
- Downloading → processing → re-uploading (e.g. unzip, OCR, face-detect)
- Listing and counting files in Drive folders
- Deleting files from Drive programmatically

---

## Core API pattern (always use this, not google_api.py for bulk ops)

```python
import json, sys
sys.path.insert(0, '/home/hermes/.hermes/hermes-agent/venv/lib/python3.11/site-packages')
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_drive():
    with open('/home/hermes/.hermes/google_token.json') as f:
        t = json.load(f)
    creds = Credentials(
        token=t.get('token'), refresh_token=t.get('refresh_token'),
        token_uri=t.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=t.get('client_id'), client_secret=t.get('client_secret'),
        scopes=t.get('scopes')
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)
```

## List all files in a folder (handles pagination)

```python
def list_folder(drive, folder_id):
    files = []
    page_token = None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageToken=page_token
        ).execute()
        files.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return files
```

## Download a file

```python
from googleapiclient.http import MediaIoBaseDownload
import io

def download_file(drive, file_id, dest_path, chunksize=100*1024*1024):
    request = drive.files().get_media(fileId=file_id)
    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=chunksize)
        done = False
        while not done:
            status, done = downloader.next_chunk()
```

## Upload a file

```python
from googleapiclient.http import MediaFileUpload

def upload_file(drive, local_path, parent_folder_id, mime='application/octet-stream'):
    fname = os.path.basename(local_path)
    meta = {'name': fname, 'parents': [parent_folder_id]}
    media = MediaFileUpload(local_path, mimetype=mime, resumable=True, chunksize=5*1024*1024)
    req = drive.files().create(body=meta, media_body=media, fields='id')
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp['id']
```

## Parallel uploads (8 threads)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def upload_batch(files_list, folder_id, workers=8):
    # files_list: list of (local_path, filename)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(upload_file, get_drive(), p, folder_id): n for p, n in files_list}
        for future in as_completed(futures):
            result = future.result()
```

## Create a folder

```python
def create_folder(drive, name, parent_id):
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    f = drive.files().create(body=meta, fields='id,webViewLink').execute()
    return f['id'], f['webViewLink']
```

## Delete a file

```python
drive.files().delete(fileId=file_id).execute()
```

## Share a file / grant permissions

```python
drive.permissions().create(
    fileId=FILE_ID,
    body={"type": "user", "role": "reader", "emailAddress": "user@example.com"},
    sendNotificationEmail=True,
    emailMessage="Optional message here."
).execute()
# role options: "reader", "commenter", "writer", "owner"
```

## Revoke a specific user's access (by email)

Don't guess the permission ID — list all permissions, match by email, then delete:

```python
perms = drive.permissions().list(
    fileId=FILE_ID,
    fields="permissions(id,emailAddress)"
).execute()
for p in perms.get('permissions', []):
    if p.get('emailAddress', '').lower() == target_email.lower():
        drive.permissions().delete(fileId=FILE_ID, permissionId=p['id']).execute()
        print(f"Removed {target_email}")
        break
```

## Copy a Sheets tab to another spreadsheet + rename + reorder + delete from source

Pattern for migrating tabs between spreadsheets cleanly:

```python
sheets_svc = build('sheets', 'v4', credentials=creds)

# 1. Copy tab — arrives in destination as "Copy of <name>"
result = sheets_svc.spreadsheets().sheets().copyTo(
    spreadsheetId=SOURCE_ID,
    sheetId=SOURCE_TAB_ID,
    body={"destinationSpreadsheetId": DEST_ID}
).execute()
new_tab_id = result['sheetId']

# 2. Rename + reorder in destination (batch these together)
sheets_svc.spreadsheets().batchUpdate(
    spreadsheetId=DEST_ID,
    body={"requests": [
        {"updateSheetProperties": {
            "properties": {"sheetId": new_tab_id, "title": "Correct Name", "index": 1},
            "fields": "title,index"
        }}
    ]}
).execute()

# 3. Delete from source
sheets_svc.spreadsheets().batchUpdate(
    spreadsheetId=SOURCE_ID,
    body={"requests": [{"deleteSheet": {"sheetId": SOURCE_TAB_ID}}]}
).execute()
```

**Note:** When migrating multiple tabs, batch all renames/reorders into a single `batchUpdate` call, then batch all source deletes into a second call. Don't interleave — deleting from source while copying can cause race conditions.

---

## iCloud → GDrive migration pattern (May 31 2026)

**Scenario:** Large zip files on Drive → download → unzip → upload files → delete zip → repeat.

**Disk constraint:** VM has limited disk. Must process one zip at a time.
- Check free space before each zip: `shutil.disk_usage('/home/hermes').free`
- Need ~2.5x zip size free (zip + extracted)
- Delete zip immediately after extraction to reclaim space
- Delete local extracted files after upload completes

**Key pitfalls:**
- `google_api.py drive search` does NOT support `'folder_id' in parents` syntax — use the API directly
- `zipfile.ZipFile` can fail with `[Errno 28] No space left` mid-extract if disk fills — the script continues with partial extraction; `system unzip` is fallback but may not be installed
- Always refresh creds every ~100 uploads in long-running jobs (`creds.expired` check)
- Run in background with `terminal(background=True, notify_on_complete=True)` — don't block

**Resume logic:** Check already-uploaded files via `list_folder()`, skip those in the upload loop. Enables safe restarts.

**Results from May 31 migration:**
- 4 zips (7GB, 5.8GB, 18.8GB, 12.1GB) → 3,487 files (2,578 photos, 909 videos)
- Parallel uploads (8 threads) ~5x faster than sequential
- Drive folders: iCloud to Google -1/2/3/4 under parent `18-3ya4x6q_sB2rqg0fdbdZdOcKgL96dW`

---

## OCR scan for personal info

Install in the hermes venv:
```bash
sudo apt-get install -y tesseract-ocr
/home/hermes/.hermes/hermes-agent/venv/bin/pip3 install pytesseract
```

Pattern — download image bytes directly, OCR in memory (no temp files needed):
```python
import io
from PIL import Image
import pytesseract

def ocr_drive_image(drive, file_id):
    request = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request, chunksize=5*1024*1024)
    done = False
    while not done: _, done = downloader.next_chunk()
    img = Image.open(io.BytesIO(buf.getvalue())).convert('RGB')
    return pytesseract.image_to_string(img, timeout=30)
```

**Note:** Install pytesseract in the hermes venv specifically — `pip install --break-system-packages` installs to system Python, not the venv the scripts run in. Always use `/home/hermes/.hermes/hermes-agent/venv/bin/pip3`.

---

## Lima VM disk resize (Mac Mini)

If more VM disk is needed:
```bash
# On Mac terminal:
limactl stop hermes
qemu-img resize ~/.lima/hermes/datadisk 120G
limactl start hermes
# After restart, expand partition inside VM:
limactl shell hermes sudo growpart /dev/vda 1
limactl shell hermes sudo resize2fs /dev/vda1
```
Tanzim's Mac Mini: 228GB disk, ~88GB free. VM safely up to ~160GB max. Current: 120GB.
