# PII NEW Folder Scan — June 1, 2026

## Task
Filter Google Drive folder "PII NEW" (ID: 1fxUEK3wh214SbwRVueE2Gl35HfJSbsSz).
Keep images containing Name, Email, or Phone number. Delete the rest.

## Approach 1 — OCR + Regex (pii_filter.py)
- Tesseract OCR on each image → regex for email, phone, name labels
- Problem: too many false positives (phone regexes match random digit strings)
- Result: 44 kept, 56 deleted — but many of the 44 were likely wrong

## Approach 2 — Claude Vision (pii_vision_filter.py)
- Prompt: "Does this image contain a person's full name, email, or phone number? YES/NO"
- Model: claude-haiku-4-5 via Bearer token
- Problem on first run: used `x-api-key` header → 401 on every call → deleted 100 files on error
- Fix: restored all 100 from trash, switched to `Authorization: Bearer <token>`
- Second run: working correctly as of Jun 1 2026 (still in progress at session end)

## Key lessons
1. `CLAUDE_CODE_OAUTH_TOKEN` must be used as Bearer, not x-api-key
2. Drive trash endpoint: PATCH `trashed: true` — NOT POST `/trash` (returns 404)
3. Fail-safe: on classifier error, default KEEP not DELETE
4. Restore path: list with `trashed=true` in parents query, PATCH `trashed: false`

## Scripts on VM
- `/home/hermes/pii_filter.py` — OCR+regex version (deprecated)
- `/home/hermes/pii_vision_filter.py` — Vision API version (current)
- `/home/hermes/pii_restore.py` — Restore all trashed files in a folder
- `/home/hermes/pii_delete.py` — Batch delete by filename list
