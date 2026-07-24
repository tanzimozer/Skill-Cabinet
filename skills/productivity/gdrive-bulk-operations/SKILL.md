---
name: gdrive-bulk-operations
description: "Patterns for bulk Google Drive operations — large file downloads, parallel uploads, folder scanning, batch deletes."
category: productivity
tags: [google-drive, bulk, upload, download, parallel, icloud, migration]
version: 1.0.0
created: 2026-05-31
---

# Google Drive Bulk Operations

Reusable patterns for large-scale Drive work: migrations, bulk uploads, folder scans, batch deletes.

## When to use
- Moving large files (zips, media) to/from Drive
- Scanning folder contents and categorizing files
- Parallel upload pipelines
- Batch deleting files

## Auth pattern (always use this)

```python
import json, sys
sys.path.insert(0, '/home/hermes/.hermes/hermes-agent/venv/lib/python3.11/site-packages')

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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

drive = build('drive', 'v3', credentials=creds)
```

## List files in a folder

```python
files = []
page_token = None
while True:
    resp = drive.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
        pageToken=page_token
    ).execute()
    files.extend(resp.get('files', []))
    page_token = resp.get('nextPageToken')
    if not page_token:
        break
```

**PITFALL:** The `google_api.py` CLI script uses a `fullText contains` query prefix — passing `'folder_id' in parents` as the search string will fail with 400. Use the Python API directly for folder listing.

## Parallel upload (8 threads)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.http import MediaFileUpload

def upload_single(args):
    fpath, fname, folder_id = args
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else ''
    mime_map = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'heic': 'image/heic', 'mp4': 'video/mp4', 'mov': 'video/quicktime',
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    try:
        drive = build('drive', 'v3', credentials=get_creds())  # fresh per thread
        meta = {'name': fname, 'parents': [folder_id]}
        media = MediaFileUpload(fpath, mimetype=mime, resumable=True, chunksize=5*1024*1024)
        req = drive.files().create(body=meta, media_body=media, fields='id')
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        return ('ok', fname)
    except Exception as e:
        return ('err', fname, str(e))

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(upload_single, args): args[1] for args in to_upload}
    for future in as_completed(futures):
        result = future.result()
```

**Key:** Get a fresh `drive` client per thread — the googleapiclient is not thread-safe.

## Resume support — skip already-uploaded files

```python
def get_already_uploaded(drive, folder_id):
    uploaded = set()
    page_token = None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=1000, fields="nextPageToken, files(name)",
            pageToken=page_token
        ).execute()
        for f in resp.get('files', []):
            uploaded.add(f['name'])
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return uploaded
```

## Disk space check before large downloads

```python
import shutil
stat = shutil.disk_usage('/home/hermes')
free_gb = stat.free / 1e9
# Need: zip_size * 2.5 (zip + extracted + buffer)
# But google_api.py script's 2.5x multiplier is conservative — 
# actual need is zip_size + extracted_size + ~20% buffer
# For 18.8GB zip: 18.8 (download) + ~20GB (extracted) + buffer = ~40GB needed
```

**PITFALL (May 31 session):** 2.5x multiplier caused zip 3 (18.8GB) to be skipped even though 35GB was free. After zips 1+2 cleaned up, 35GB was actually enough. Consider a more realistic check: `free_gb > zip_size * 2.2`.

## Sequential zip pipeline with cleanup

The proven pattern for large migrations:
1. Download zip → VM (100MB chunks for speed)
2. Unzip to `extracted/` dir
3. Delete zip immediately to free space
4. Create Drive folder
5. Upload all files in parallel (8 threads), skipping iOS metadata (`.aae`)
6. Delete local extracted dir
7. Repeat for next zip

This fits within 35GB free for zips up to ~15GB. For 18.8GB+ zips, need 35GB+ free.

## File categorization

```python
def categorize(fname):
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else 'unknown'
    if ext in ('jpg','jpeg','png','gif','heic','heif','bmp','tiff','webp','raw'): return 'Photos'
    if ext in ('mp4','mov','avi','mkv','m4v','3gp','m4p'): return 'Videos'
    if ext == 'aae': return 'iOS Metadata'  # skip these — iPhone edit sidecar files
    if ext == 'json': return 'Metadata JSON'
    return f'Other ({ext})'
```

## Batch delete

```python
for file_id in file_ids_to_delete:
    drive.files().delete(fileId=file_id).execute()
```

**Always requires codeword before executing destructive deletes.**

## iCloud migration result (May 31 2026)
- Parent folder: `18-3ya4x6q_sB2rqg0fdbdZdOcKgL96dW`
- 4 subfolders created, 3,487 files (2,578 photos, 909 videos)
- Original 4 zips (~40GB) deleted after migration confirmed
- Reference: `references/icloud-migration-2026-05-31.md`
