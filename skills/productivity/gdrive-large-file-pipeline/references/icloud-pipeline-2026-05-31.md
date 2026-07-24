# iCloud Pipeline Run — 2026-05-31

## Context
Tanzim transferred iCloud photos to GDrive a couple days prior. Folder: "iCloud to Google" (ID: `18-3ya4x6q_sB2rqg0fdbdZdOcKgL96dW`).

## Files
| Name | Drive ID | Size |
|------|----------|------|
| iCloud to Google - 1.zip | 1Czz2gx6ifACMq591p-nvmMvuUvRLKfxk | 7.0 GB |
| iCloud to Google - 2.zip | 1mk1QWTw8hNPuiq_ZgktgzTdbqkXSmrvF | 5.8 GB |
| iCloud to Google - 3.zip | 1jAX-6N_E913FqXAEEi89hJBWiYvm9ukf | 18.8 GB |
| iCloud to Google - 4.zip | 1U7pmLIzM6656ihnT96jXOFucvM53vlLz | 12.1 GB |

Total: ~43.7 GB across 4 zips.

## Pipeline script
`/home/hermes/icloud_pipeline.py` — runs sequentially, logs to `/home/hermes/icloud_pipeline.log`.

## VM disk at start
58GB total, 35GB free. Processed one zip at a time to stay within limits.

## Discovery path
- `google_api.py drive search` returned HTTP 400 when attempting `'folder_id' in parents` query
- Switched to native Drive API (`drive.files().list(q=...)`) — worked correctly
- Folder contents were 4 zip files, not loose images — had to propose download→unzip→reupload pipeline
