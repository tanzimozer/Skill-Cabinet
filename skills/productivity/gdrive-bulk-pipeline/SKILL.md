---
name: gdrive-bulk-pipeline
description: "Download → unzip → upload → cleanup pipeline for large file batches on Google Drive. Sequential by necessity (disk constraint), parallel uploads (8 threads). Handles resume, skips already-uploaded files."
version: 1.0.0
tags: [gdrive, google-drive, bulk-upload, pipeline, photos, files]
category: productivity
created: 2026-06-01
related_skills: []
---

# Google Drive Bulk File Pipeline

Used when Tanzim has large zipped archives on Drive that need to be expanded into folders. Canonical use case: iCloud photo export zips → unpacked Drive folders.

## When to use
- Large zips on Drive that need expanding into browsable folders
- Bulk file migration between cloud storage services
- Any "download → process → re-upload → cleanup" pattern at multi-GB scale

## Disk constraint — the non-negotiable
The VM has ~58GB total, ~35GB free under normal conditions. Zips **must be processed sequentially** — never download 2+ large zips simultaneously. Rule of thumb: need at least `zip_size × 2.2` free before starting (zip + unzipped contents + headroom).

Check before every zip:
```python
import shutil
stat = shutil.disk_usage('/home/hermes')
free_gb = stat.free / 1e9
print(f"Free: {free_gb:.1f} GB")
```

## Upload parallelism — 8 threads
Sequential upload is the bottleneck. Use `ThreadPoolExecutor(max_workers=8)` for uploads — each thread gets its own Drive client via `get_drive()` (which refreshes creds). Verified working at 8 threads with no auth conflicts.

## Resume support — always check what's already uploaded
Before uploading, query the target Drive folder and build a set of already-uploaded filenames. Skip those. This makes the pipeline idempotent — safe to restart mid-run without duplicating files.

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

## Zip extraction — zipfile vs system unzip
`zipfile.ZipFile` works for most archives but fails with `[Errno 28] No space left on device` if the disk fills mid-extraction (happened on zip 3, 18.8GB). Fallback: `os.system('unzip -q ...')` — but `unzip` may not be installed. Always delete the zip first before uploading to recover space.

Order of operations per zip:
1. Download zip → VM
2. Unzip to `extracted/` subdirectory
3. **Delete the zip immediately** (free the space before uploading)
4. Create Drive folder
5. Upload in parallel (skip already-uploaded)
6. Delete local extracted dir

## File categorization
```python
def categorize(fname):
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else 'unknown'
    if ext in ('jpg','jpeg','png','gif','heic','heif','bmp','tiff','webp','raw'): return 'Photos'
    if ext in ('mp4','mov','avi','mkv','m4v','3gp','m4p'): return 'Videos'
    if ext == 'aae': return 'iOS Metadata'  # skip these — Apple edit sidecar files
    if ext == 'json': return 'Metadata JSON'
    return f'Other ({ext})'
```
iOS `.aae` files are Apple sidecar edit metadata — not photos, skip uploading them.

## Drive folder query — correct syntax
The `google_api.py` script's `drive search` command wraps the query in `fullText contains` — this breaks parent-folder queries. Use the API directly:

```python
# CORRECT — direct API call
results = drive.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=200,
    fields="files(id, name, mimeType, modifiedTime, webViewLink, size)"
).execute()

# WRONG — google_api.py drive search wraps in fullText contains
# python google_api.py drive search "'folder_id' in parents"  ← 400 Invalid Value
```

## Deleting files from Drive
```python
drive.files().delete(fileId=file_id).execute()
# Permanent — no trash. Confirm with Tanzim + codeword before bulk deletes.
```

## Background execution pattern
Run as background process with `notify_on_complete=True`. Log to a file and tail it for status. On completion, parse the log for summary stats and report to Tanzim.

## Session results (iCloud migration, Jun 1 2026)
- 4 zips processed: 7.0 GB, 5.8 GB, 18.8 GB, 12.1 GB
- Total: 3,488 files — 0 errors
- Zip 1: 872 photos, 132 videos
- Zip 2: 1,008 files
- Zip 3: 690 photos, 450 videos (largest — disk was tight)
- Zip 4: 196 photos, 140 videos
- Originals deleted from Drive after confirmation + codeword

## References
- `references/pipeline-script.md` — full v2 script with parallel uploads and resume logic
