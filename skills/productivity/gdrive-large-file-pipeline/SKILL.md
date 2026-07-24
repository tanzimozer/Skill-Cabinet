---
name: gdrive-large-file-pipeline
description: "Download large files/zips from Google Drive to VM, process them (unzip, transform, categorise), re-upload results, and clean up. Handles multi-GB batch jobs sequentially to stay within disk limits."
version: 1.0.0
tags: [Google Drive, large files, batch, upload, download, iCloud, pipeline]
related_skills: [gmail-inbox-check]
---

# Google Drive Large-File Pipeline

Use when Tanzim needs to process large files stored on Drive — unzip, categorise, re-upload, transform — where the VM disk is the constraint.

## When to use
- Batch processing of multi-GB zip/archive files on Drive
- Unzip → scan → re-upload → delete cycles
- Any pipeline where total file size exceeds ~30GB and must be processed sequentially

## Disk budget rule
Always check disk space first:
```bash
df -h /home/hermes
```
- Free space must be ≥ `zip_size × 2.5` before processing that zip (zip + unzipped content + upload buffer)
- Process one zip at a time; delete local copy before downloading the next
- If a single zip + unzipped exceeds available space, alert Tanzim — don't proceed

## Authentication — use native Drive API, NOT google_api.py

`google_api.py` only supports freetext search. For folder listing, download, and upload, use the native client directly:

```python
import json, sys
sys.path.insert(0, '/home/hermes/.hermes/hermes-agent/venv/lib/python3.11/site-packages')

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

def get_creds():
    with open('/home/hermes/.hermes/google_token.json') as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes')
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds
```

## Folder listing by parent ID

```python
drive = build('drive', 'v3', credentials=get_creds())
results = drive.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=200,
    fields="files(id, name, mimeType, modifiedTime, webViewLink, size)"
).execute()
files = results.get('files', [])
```

**Pitfall:** Do NOT pass `"'folder_id' in parents"` to `google_api.py drive search` — it wraps it in `fullText contains` and returns HTTP 400.

## Downloading large files (chunked)

```python
def download_file(drive, file_id, dest_path, log_fn=print):
    request = drive.files().get_media(fileId=file_id)
    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=50*1024*1024)
        done = False
        last_pct = 0
        while not done:
            status, done = downloader.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                if pct >= last_pct + 10:
                    log_fn(f"Download: {pct}%")
                    last_pct = pct
```

## Uploading files (resumable)

```python
def upload_file(drive, local_path, parent_folder_id):
    fname = os.path.basename(local_path)
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else ''
    mime_map = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'heic': 'image/heic', 'heif': 'image/heif',
        'mp4': 'video/mp4', 'mov': 'video/quicktime',
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    meta = {'name': fname, 'parents': [parent_folder_id]}
    media = MediaFileUpload(local_path, mimetype=mime, resumable=True, chunksize=10*1024*1024)
    req = drive.files().create(body=meta, media_body=media, fields='id')
    response = None
    while response is None:
        _, response = req.next_chunk()
    return response['id']
```

## Creating a Drive folder

```python
def create_drive_folder(drive, name, parent_id):
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    folder = drive.files().create(body=meta, fields='id,webViewLink').execute()
    return folder['id'], folder['webViewLink']
```

## Full pipeline loop pattern

```python
for zip_info in ZIPS:
    # 1. Check disk
    # 2. Download zip → /home/hermes/work/<name>/
    # 3. Unzip to extracted/ subdir
    # 4. Delete local zip immediately (free space)
    # 5. Create Drive folder
    # 6. Upload all files (skip .DS_Store, ._* macOS artifacts)
    # 7. Refresh creds every ~100 uploads (long jobs expire tokens)
    # 8. shutil.rmtree() local work dir
    # 9. Log summary (categories, count, Drive URL)
```

## Categorisation pattern for iCloud exports

| Extension | Category |
|-----------|----------|
| jpg/jpeg/png/heic/heif/gif | Photos |
| mp4/mov/avi/m4v/3gp | Videos |
| aae | iOS Metadata — skip upload |
| json | Metadata JSON |
| other | Other (log extension) |

Skip macOS artifacts: files starting with `._` or named `.DS_Store`.

## Background execution

Run as background process so Tanzim can continue chatting:
```python
terminal(background=True, command="python /home/hermes/icloud_pipeline.py", notify_on_complete=True)
```
- Log to a file (e.g. `/home/hermes/icloud_pipeline.log`) for polling
- Alert Tanzim with folder URL + category summary when each zip completes

## Token refresh during long jobs

For jobs uploading thousands of files, refresh creds every ~100 uploads:
```python
if uploaded % 100 == 0 and uploaded > 0:
    creds = get_creds()
    drive = build('drive', 'v3', credentials=creds)
```

## Pitfalls
- `zipfile` may fail on some macOS-generated zips with comments or non-standard encoding — fallback to `os.system('unzip -q ...')` if it raises
- Resumable uploads can stall silently; add a timeout or retry wrapper for production use
- Always delete the zip **before** unzipping if disk is tight — the zip and unzipped content together can be 2–3× the zip size

## Reference files
- `references/icloud-pipeline-2026-05-31.md` — first run context: 4 zips (~40GB), iCloud to Google folder, pipeline script location
