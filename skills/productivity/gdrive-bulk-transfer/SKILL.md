---
name: gdrive-bulk-transfer
description: "Bulk download, transform, and re-upload files to Google Drive. Covers large zip extraction pipelines, parallel uploads, resume support, and disk-constrained sequencing."
version: 1.0.0
tags: [Google Drive, bulk upload, iCloud, zip, files, migration]
related_skills: [gmail-inbox-check, google-oauth-refresh]
---

# Google Drive Bulk Transfer Pipeline

For large file migrations: download from Drive, unzip, re-upload as unpacked files, clean up. Verified pattern for iCloud → GDrive and similar multi-GB transfers.

## When to use
- Tanzim asks to unzip and re-upload files stored in Drive
- Migrating photos/files from iCloud exports to organized Drive folders
- Any bulk "download → transform → re-upload → delete local" pipeline

## Core constraint: disk-sequential, upload-parallel

**Disk is the binding constraint.** The VM has ~58GB total, ~28–36GB free. You cannot download multiple large zips simultaneously. Always:
1. Process zips **sequentially** (one at a time)
2. Delete the zip immediately after extraction (before uploading)
3. Delete local extracted files immediately after upload completes
4. Upload files **in parallel** (8 threads is the sweet spot)

## Drive API — folder listing requires native Python, not GAPI script

The `google_api.py` script's `drive search` wraps queries in `fullText contains` — passing `"'folder_id' in parents"` returns HTTP 400. Use the native API directly:

```python
import json, sys
sys.path.insert(0, '/home/hermes/.hermes/hermes-agent/venv/lib/python3.11/site-packages')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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
drive = build('drive', 'v3', credentials=creds)

results = drive.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=200,
    fields="files(id, name, mimeType, modifiedTime, webViewLink, size)"
).execute()
files = results.get('files', [])
```

## Parallel upload pattern (verified, 8 threads)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.http import MediaFileUpload

UPLOAD_THREADS = 8

def upload_single(args):
    fpath, fname, folder_id = args
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else ''
    mime_map = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'heic': 'image/heic', 'heif': 'image/heif',
        'mp4': 'video/mp4', 'mov': 'video/quicktime', 'avi': 'video/avi',
        'm4v': 'video/mp4', '3gp': 'video/3gpp',
        'aae': 'application/octet-stream', 'json': 'application/json',
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    try:
        drive = get_drive()  # fresh creds per thread
        meta = {'name': fname, 'parents': [folder_id]}
        media = MediaFileUpload(fpath, mimetype=mime, resumable=True, chunksize=5*1024*1024)
        req = drive.files().create(body=meta, media_body=media, fields='id')
        response = None
        while response is None:
            _, response = req.next_chunk()
        return ('ok', fname)
    except Exception as e:
        return ('err', fname, str(e))

with ThreadPoolExecutor(max_workers=UPLOAD_THREADS) as executor:
    futures = {executor.submit(upload_single, args): args[1] for args in to_upload}
    for future in as_completed(futures):
        result = future.result()
```

**Important:** Each thread must call `get_drive()` independently — Drive clients are not thread-safe. Pass `get_creds()` inside the thread, not from outside.

## Resume support — check already-uploaded files

If a pipeline is killed mid-run, restart by querying what's already in the target folder:

```python
def get_already_uploaded(drive, folder_id):
    uploaded = set()
    page_token = None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=1000,
            fields="nextPageToken, files(name)",
            pageToken=page_token
        ).execute()
        for f in resp.get('files', []):
            uploaded.add(f['name'])
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return uploaded
```

Then filter `to_upload` to exclude already-uploaded filenames.

## Disk safety check before each zip

```python
def check_disk(zip_size_gb, multiplier=2.5):
    stat = shutil.disk_usage('/home/hermes')
    free_gb = stat.free / 1e9
    if free_gb < zip_size_gb * multiplier:
        log(f"ERROR: Only {free_gb:.1f} GB free, need {zip_size_gb * multiplier:.0f} GB. Skipping.")
        return False
    return True
```

**Multiplier of 2.5** = zip size + extracted size + headroom. The 18.8GB zip (iCloud batch 3) was skipped when only ~28GB was free after processing batches 1 and 2 — correct behaviour, but plan for it: process the largest zip first if possible, or free disk manually.

## File categorization for photo/video libraries

```python
def categorize(fname):
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else 'unknown'
    if ext in ('jpg', 'jpeg', 'png', 'gif', 'heic', 'heif', 'bmp', 'tiff', 'webp', 'raw'):
        return 'Photos'
    elif ext in ('mp4', 'mov', 'avi', 'mkv', 'm4v', '3gp', 'm4p'):
        return 'Videos'
    elif ext == 'aae':
        return 'iOS Metadata'   # skip these — Apple edit sidecar files, useless outside iOS
    elif ext == 'json':
        return 'Metadata JSON'
    else:
        return f'Other ({ext})'
```

Skip `.aae` files (iOS photo edit metadata) and `.DS_Store`. Also skip any file starting with `._` (macOS resource fork artifacts).

## iCloud export structure

iCloud photo exports via iCloud.com come as numbered zip batches:
- `iCloud to Google - 1.zip`, `- 2.zip`, etc.
- Each zip contains flat HEIC/JPG/MP4/MOV files + `.aae` sidecars
- No subfolder structure inside the zip
- Batch sizes vary widely (5–19 GB per zip)

## Pitfalls

- **Don't run all downloads in parallel** — disk will fill up. Sequential download, parallel upload only.
- **The largest zip should go first** if disk is tight — it needs the most headroom and clearing it frees the most space for subsequent batches.
- **`zipfile` module may fail on large iCloud zips** — fall back to system `unzip -q` command if it throws. Both were handled in the verified script at `references/icloud-pipeline-v2.py`.
- **Creds expire mid-run** on long jobs — call `get_creds()` fresh every 100 uploads or per-thread, not once at the start.
- **Double-logging bug:** If the pipeline script is accidentally started twice (or v1 and v2 overlap), log lines appear duplicated. Always kill the old process before starting a new one.

## Full verified pipeline script
See `references/icloud-pipeline-v2.py` for the complete working script from the 2026-05-31 session.
