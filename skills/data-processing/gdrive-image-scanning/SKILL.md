---
name: gdrive-image-scanning
description: Scan Google Drive image folders for specific visual content using OCR + Claude Vision. Includes PII detection, spreadsheet identification, and bulk filtering with copy/delete operations.
tags: [google-drive, images, ocr, vision, pii, filtering, tesseract]
category: data-processing
---

# Google Drive Image Scanning

Bulk-scan Drive image folders to identify, filter, or copy images based on visual content. Uses a two-stage pipeline: fast OCR gate → Claude Vision confirm.

## Core pipeline (hybrid OCR + Vision)

This is the proven architecture. Use it for any Drive image classification task.

```python
import json, urllib.request, urllib.parse, os, re, subprocess, tempfile, base64, time

TOKEN_PATH = os.path.expanduser('~/.hermes/google_token.json')
CLIENT_SECRET_PATH = os.path.expanduser('~/.hermes/google_client_secret.json')

def refresh_gdrive():
    with open(TOKEN_PATH) as f: tok = json.load(f)
    with open(CLIENT_SECRET_PATH) as f: sec = json.load(f)
    web = sec.get('web') or sec.get('installed', {})
    data = urllib.parse.urlencode({
        'client_id': tok.get('client_id') or web['client_id'],
        'client_secret': tok.get('client_secret') or web['client_secret'],
        'refresh_token': tok['refresh_token'], 'grant_type': 'refresh_token'
    }).encode()
    resp = json.loads(urllib.request.urlopen(
        urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
    ).read())
    tok['token'] = resp['access_token']
    with open(TOKEN_PATH, 'w') as f: json.dump(tok, f)
    return resp['access_token']

def get_anthropic_key():
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('CLAUDE_CODE_OAUTH_TOKEN='):
                return line.split('=',1)[1].strip().strip('"').strip("'")

def list_all_images(folder_id, token):
    images, page_token = [], None
    while True:
        q = urllib.parse.quote(f"'{folder_id}' in parents and trashed = false")
        url = f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name,mimeType)&pageSize=200'
        if page_token: url += f'&pageToken={page_token}'
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        result = json.loads(urllib.request.urlopen(req).read())
        images.extend([f for f in result.get('files',[]) if f.get('mimeType','').startswith('image/')])
        page_token = result.get('nextPageToken')
        if not page_token: break
    return images

def download_image(file_id, token, max_bytes=4*1024*1024):
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media',
        headers={'Authorization': f'Bearer {token}'}
    )
    return urllib.request.urlopen(req, timeout=30).read(max_bytes)

def ocr_text(image_bytes):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(image_bytes); tmp = f.name
    try:
        r = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'],
                           capture_output=True, text=True, timeout=20)
        return r.stdout
    except: return ""
    finally: os.unlink(tmp)

def vision_check(image_bytes, filename, api_key, prompt):
    ext = filename.lower().split('.')[-1]
    mt = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','gif':'image/gif','webp':'image/webp'}.get(ext,'image/jpeg')
    b64 = base64.standard_b64encode(image_bytes).decode()
    payload = json.dumps({
        "model": "claude-haiku-4-5", "max_tokens": 10,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
            {"type": "text", "text": prompt}
        ]}]
    }).encode()
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages', data=payload,
        headers={'Authorization': f'Bearer {api_key}', 'anthropic-version': '2023-06-01',
                 'content-type': 'application/json'}
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return resp['content'][0]['text'].strip()
    except Exception as e:
        return f"ERROR:{e}"

def trash_file(file_id, token):
    data = json.dumps({'trashed': True}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}',
        data=data, method='PATCH',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try: urllib.request.urlopen(req); return True
    except: return False

def restore_file(file_id, token):
    data = json.dumps({'trashed': False}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}',
        data=data, method='PATCH',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try: urllib.request.urlopen(req); return True
    except: return False

def copy_to_folder(file_id, dest_folder_id, token):
    data = json.dumps({'parents': [dest_folder_id]}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}/copy?fields=id,name',
        data=data,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try:
        result = json.loads(urllib.request.urlopen(req).read())
        return True, result.get('name','')
    except Exception as e:
        return False, str(e)
```

## Anthropic API auth — critical

The key in `~/.hermes/.env` (`CLAUDE_CODE_OAUTH_TOKEN=`) is an **OAuth token**, not a raw API key. Use it as a **Bearer token**, not `x-api-key`:

```python
headers={
    'Authorization': f'Bearer {api_key}',   # ✅ correct
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json'
}
# NOT: 'x-api-key': api_key   ← returns 401
```

## PII detection (contact spreadsheets)

**Task:** find screenshots of Excel/Sheets with 3+ rows each containing name + phone + email.

### OCR gate
```python
emails = len(re.findall(r'\b\S+@\S+\.\S+\b', text))
phones = len(re.findall(r'\d{3}[-.\s]\d{3}[-.\s]\d{4}', text))
if emails < 2 and phones < 2:
    pass  # fast reject — no vision call
```

### Vision prompt (exact wording that works)
```
"Is this a spreadsheet with 3+ rows each containing a person name, phone number, and email address? YES or NO only."
```

### Filter logic — AND not OR
Images must have **all three** (name AND phone AND email) to qualify. Previous attempts with OR logic produced ~98% noise.

## PII NEW folder filtering (Tanzim's use case)

For the `PII NEW` folder specifically:
- **Delete** images that do NOT have all three: name + phone number + email
- **Keep** only images where all three are visible
- Always trash (not hard-delete) — use PATCH `trashed: true`
- If vision returns ERROR: **keep the file** (fail safe, never delete on error)
- Restore from trash: list with `trashed = true` in query, then PATCH `trashed: false`

## Folder operations

### Find folder by name
```python
q = urllib.parse.quote(f"name = 'FOLDER_NAME' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
req = urllib.request.Request(
    f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)',
    headers={'Authorization': f'Bearer {token}'}
)
result = json.loads(urllib.request.urlopen(req).read())
folder_id = result['files'][0]['id']
```

### Create folder
```python
data = json.dumps({'name': 'NEW FOLDER', 'mimeType': 'application/vnd.google-apps.folder'}).encode()
req = urllib.request.Request(
    'https://www.googleapis.com/drive/v3/files?fields=id,name', data=data,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
result = json.loads(urllib.request.urlopen(req).read())
folder_id = result['id']
```

### List trashed files in folder
```python
q = urllib.parse.quote(f"'{folder_id}' in parents and trashed = true")
# Same list pattern as above
```

## Parallel scanning across multiple folders

For 4 folders (~3,500 images total), run one background process per folder:

```bash
python3 final_scan.py FOLDER_ID_1 "iCloud-1" &
python3 final_scan.py FOLDER_ID_2 "iCloud-2" &
python3 final_scan.py FOLDER_ID_3 "iCloud-3" &
python3 final_scan.py FOLDER_ID_4 "iCloud-4" &
```

Each writes its own log to `/tmp/final_scan_<name>.txt`. Check progress with `tail -5 /tmp/final_scan_*.txt`.

See `scripts/final_scan.py` for the full reusable scanning script.

## Full workflow: scan → filter → extract → populate sheet

1. **Scan** all source folders in parallel (4 background processes)
2. **Copy matches** to a destination folder (e.g., "final iCloud")
3. **Extract data** from matched images using vision with JSON extraction prompt
4. **Create Google Sheet** with headers (Serial, Name, Phone, Email)
5. **Write extracted rows** to the sheet

This produces a clean sheet of structured contact data from scattered spreadsheet screenshots.

## Tanzim's Drive folder IDs (as of June 2026)

| Folder | ID |
|---|---|
| iCloud to Google - 1 | `1kFwgMx-eTOCXgzCq15iOOFJWe2F5130-` |
| iCloud to Google - 2 | `1dDipZ7Wk9YF_1fydVg17PiKQJyuYTReo` |
| iCloud to Google - 3 | `1iwgJ3iChBeg7WxnmZBTD5iVd8_4mnyG7` |
| iCloud to Google - 4 | `1VIu-Cx7ae_SzcYlDBD5P9UZIIe3cKmJK` |
| PII NEW | `1fxUEK3wh214SbwRVueE2Gl35HfJSbsSz` |
| PIIX | `1m_INknYNY0pwk-YIviYIbiWflBoC0ZOn` |
| final iCloud | `1503-a0AzgqHSeG1Xa1wMu1a_jQHoZcrs` |
| HERMES | `1yGZuAcD4jzf8257cXMTjZeGsfMcK0Ba-` |
| MAGPROD | `1OcieuCvhSiEjEzYcdepd2IJxlEagKUKt` |

## Extracting data from matched images to Google Sheets

After finding matches, extract structured data and populate a Sheet:

### Create a Google Sheet
```python
sheet_data = json.dumps({
    "properties": {"title": "PIIX collection"},
    "sheets": [{"properties": {"title": "Contacts"}}]
}).encode()
req = urllib.request.Request(
    'https://sheets.googleapis.com/v4/spreadsheets',
    data=sheet_data,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
result = json.loads(urllib.request.urlopen(req).read())
sheet_id = result['spreadsheetId']
```

### Extract contacts using vision (with higher max_tokens for extraction)
```python
payload = json.dumps({
    "model": "claude-haiku-4-5",  # Haiku works; Sonnet may 404 with OAuth token
    "max_tokens": 4000,  # Higher for extraction vs classification
    "messages": [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
        {"type": "text", "text": """Extract ALL contact records from this spreadsheet image.
For each row, extract: full name, phone number (exactly as shown), email address.
Return ONLY a JSON array: [{"name": "...", "phone": "...", "email": "..."}, ...]"""}
    ]}]
}).encode()
```

### Write rows to Sheet
```python
rows = [[i, c['name'], c['phone'], c['email']] for i, c in enumerate(contacts, 1)]
write_data = json.dumps({"values": rows}).encode()
req = urllib.request.Request(
    f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Sheet!A2:D{len(rows)+1}?valueInputOption=RAW',
    data=write_data, method='PUT',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
urllib.request.urlopen(req)
```

## Pitfalls

- **Model availability varies by auth method.** The OAuth token (`CLAUDE_CODE_OAUTH_TOKEN`) reliably works with `claude-haiku-4-5`. Sonnet models (`claude-sonnet-4-5-20250514`, `claude-3-5-sonnet-20241022`) may return 404 — fallback to Haiku for image tasks.
- **Never delete on error.** If vision call fails/errors, keep the file. Deleting on error nuked 100 files in one run (June 2026).
- **Trash, don't hard-delete.** Always use `trashed: true` PATCH — files stay recoverable for 30 days. Hard-delete is permanent.
- **Drive delete endpoint (POST /trash) returns 404.** Use PATCH with `{trashed: true}` instead — that's the correct method.
- **OCR + Vision = best combo.** OCR alone produces false positives. Vision alone is slow and expensive. Gate with OCR first, confirm with vision.
- **AND not OR for PII.** Filtering for images with name OR email OR phone = ~98% noise. Must be AND (all three).
- **Tesseract psm 6** works best for tabular/spreadsheet content. psm 3 is better for mixed documents.
- **4MB download cap.** Very large images can time out or hit memory issues. Cap reads at 4MB.
- **Rate limit.** Sleep 0.3s between images to avoid Drive API throttling.

## Support files

- `scripts/final_scan.py` — full reusable script for scanning one folder and copying matches to a destination
- `references/pii-scanning-history.md` — session history of what worked and what didn't for PII image detection
