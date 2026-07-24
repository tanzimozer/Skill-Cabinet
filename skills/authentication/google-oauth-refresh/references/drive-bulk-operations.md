# Google Drive — Bulk File Operations Reference

## Pattern: Vision-based image scanning + bulk delete/copy

Used to filter or categorise a Drive folder by image content using Claude vision.
More accurate than OCR+regex — reads actual image semantics.

### Full pipeline

1. **Refresh token** (raw HTTP, no google-auth dependency)
2. **Find/create folder** by name via Drive API search
3. **List all images** in folder (paginate with `nextPageToken`)
4. **Download each image** (`?alt=media`, cap at 4MB)
5. **Check with Claude vision** (see below)
6. **Trash non-matching** or **copy matching** files

### Anthropic API auth — CRITICAL

The `CLAUDE_CODE_OAUTH_TOKEN` in `~/.hermes/.env` is an OAuth token, not a direct API key.
It must be sent as `Authorization: Bearer <token>`, NOT as `x-api-key`.

```python
# CORRECT
headers = {
    'Authorization': f'Bearer {oauth_token}',
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json'
}

# WRONG — returns 401
headers = {
    'x-api-key': oauth_token,
    ...
}
```

Read the token directly from the `.env` file (not from env vars — it's masked):
```python
def load_oauth_token():
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('CLAUDE_CODE_OAUTH_TOKEN='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return None
```

### FAIL-SAFE RULE — never delete on API error

Always treat API errors as "keep". If the vision call fails, skip deletion:

```python
answer = check_image_with_vision(img_bytes, img['name'], anthropic_key)
# Fail safe — keep on error, never delete blindly
has_pii = answer.upper().startswith('YES') if not answer.startswith('ERROR') else True
```

Deleting everything on error wiped 100 images in this session — required full restore from trash.

### Vision prompt patterns

**Filter: keep images with ALL of name + email + phone (AND logic)**
```python
"Does this image contain ALL THREE of the following: (1) a person's full name, "
"(2) an email address, AND (3) a phone number? Answer with only YES or NO, "
"then on the same line list which ones are present (e.g. YES: name, email, phone) "
"or NO: missing email, phone."
```

**Match by sample image (visual similarity scan)**
```python
# Send TWO images in the same message — sample first, candidate second
payload = {
    "model": "claude-haiku-4-5",
    "max_tokens": 80,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Here is a sample image showing the type of content I'm looking for:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": sample_b64}},
            {"type": "text", "text": "Now look at this second image. Does it show a similar type of content "
             "— a spreadsheet, table, list, or screenshot containing personal contact information "
             "(names, phone numbers, and/or email addresses)? Answer YES or NO only, followed by a brief reason."},
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}}
        ]
    }]
}
```

Use `claude-haiku-4-5` for speed/cost on large batches. Cap image downloads at 4MB.

### Copy a file to another folder (without moving)

```python
def copy_file_to_folder(file_id, dest_folder_id, access_token):
    data = json.dumps({'parents': [dest_folder_id]}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}/copy?fields=id,name',
        data=data,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )
    return json.loads(urllib.request.urlopen(req).read())
```

### Restore trashed files

To restore a batch from trash (e.g. after a bad bulk delete):

```python
# List trashed files from a specific parent folder
q = urllib.parse.quote(f"'{FOLDER_ID}' in parents and trashed = true")
url = f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=100'

# Restore each
def restore_file(file_id, access_token):
    data = json.dumps({'trashed': False}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}',
        data=data,
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        method='PATCH'
    )
    urllib.request.urlopen(req)
```

### Key pitfalls

- **Wrong delete endpoint.** `POST .../files/{id}/trash` → 404. Correct: `PATCH .../files/{id}` with `{"trashed": true}`.
- **Never delete on vision/API error** — treat errors as keep (fail-safe). One bad run deleted 100 files.
- **Bearer not x-api-key** for OAuth tokens. 401 = wrong auth header, not a bad token.
- **Folder ID from search, not hardcoded.** Use Drive search API: `name = 'FOLDER NAME' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`.
- **Pagination.** Drive API returns max 100 files per page. Always loop on `nextPageToken`.
- **Tesseract available** at `/usr/bin/tesseract` (v5.3.4) — but OCR+regex is far less accurate than vision for PII detection. Vision is the preferred approach.
- **Rate limits.** Add `time.sleep(0.3–0.5)` between vision API calls. `time.sleep(0.2)` between pure Drive API calls.
- **OR vs AND logic matters.** User said filter out images missing name+email+phone — that's AND (all three). First pass used OR logic and kept too many.

### PII NEW folder info (June 2026)
- Folder ID: `1fxUEK3wh214SbwRVueE2Gl35HfJSbsSz`
- After full vision filter (AND logic): 11 kept, 89 deleted
- PIIX folder (sample-matched contacts spreadsheets): `1m_INknYNY0pwk-YIviYIbiWflBoC0ZOn` — 21 images from 3,488 scanned
- Final iCloud folder (strict spreadsheet matches): `1503-a0AzgqHSeG1Xa1wMu1a_jQHoZcrs`

### OCR gate vs full vision scan — quality tradeoff

**OCR gate (fast, cheap, misses matches):**
- Requires 2+ emails AND 2+ phones detected by tesseract before vision call
- PROBLEM: OCR can't read rotated text, stylized fonts, or low-contrast screenshots
- Result in June 2026 session: found only 3 of ~5 actual contact spreadsheets across 557 images

**Full vision scan (slower, higher cost, accurate):**
- Every image goes through Claude vision — no pre-filtering
- Use when user says "quality over speed" or "make sure you don't miss any"
- Result: found additional matches OCR missed

**When to use which:**
- Default to OCR gate for initial bulk filtering (speed/cost)
- Switch to full vision scan when user pushes back on missed results
- User's exact words that signal full vision: "you missed a lot", "scan correctly", "not worried about time, worried about quality"

### Contact data extraction to Google Sheets

After identifying contact spreadsheet images, extract the data:

```python
# 1. Create the sheet
sheet_data = json.dumps({
    "properties": {"title": "PIIX collection"},
    "sheets": [{"properties": {"title": "Contacts"}}]
}).encode()
req = urllib.request.Request(
    'https://sheets.googleapis.com/v4/spreadsheets',
    data=sheet_data,
    headers={'Authorization': f'Bearer {gdrive_token}', 'Content-Type': 'application/json'}
)
sheet_result = json.loads(urllib.request.urlopen(req).read())
sheet_id = sheet_result['spreadsheetId']

# 2. Add headers
headers = [["Serial", "Name", "Phone", "Email"]]
header_data = json.dumps({"values": headers}).encode()
req = urllib.request.Request(
    f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Contacts!A1:D1?valueInputOption=RAW',
    data=header_data, method='PUT',
    headers={'Authorization': f'Bearer {gdrive_token}', 'Content-Type': 'application/json'}
)

# 3. Use vision to extract contacts from each image
extraction_prompt = """Extract ALL contact records from this spreadsheet image. 
For each row of data, extract the full name, phone number (exactly as shown), and email address.

Return ONLY a JSON array like this, no other text:
[{"name": "John Smith", "phone": "206-555-1234", "email": "john@email.com"}, ...]

Extract every visible row of contact data."""

# 4. Write extracted data to sheet
rows = [[i, c.get('name',''), c.get('phone',''), c.get('email','')] for i,c in enumerate(contacts, 1)]
write_data = json.dumps({"values": rows}).encode()
req = urllib.request.Request(
    f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Contacts!A2:D{len(rows)+1}?valueInputOption=RAW',
    data=write_data, method='PUT',
    headers={'Authorization': f'Bearer {gdrive_token}', 'Content-Type': 'application/json'}
)
```

### Parallel background scanning

For large folders (500+ images), deploy 4 parallel background processes:

```bash
# Launch all 4 simultaneously
python3 /home/hermes/full_scan.py $FOLDER_ID_1 "iCloud-1" 2>&1 &
python3 /home/hermes/full_scan.py $FOLDER_ID_2 "iCloud-2" 2>&1 &
python3 /home/hermes/full_scan.py $FOLDER_ID_3 "iCloud-3" 2>&1 &
python3 /home/hermes/full_scan.py $FOLDER_ID_4 "iCloud-4" 2>&1 &
```

Each writes to its own log file: `/tmp/full_scan_iCloud-{N}.txt`. Monitor with:
```bash
for i in 1 2 3 4; do echo "=== iCloud-$i ==="; tail -3 /tmp/full_scan_iCloud-$i.txt; done
```

iCloud to Google folder IDs (Tanzim's Drive):
- iCloud-1: `1kFwgMx-eTOCXgzCq15iOOFJWe2F5130-`
- iCloud-2: `1dDipZ7Wk9YF_1fydVg17PiKQJyuYTReo`
- iCloud-3: `1iwgJ3iChBeg7WxnmZBTD5iVd8_4mnyG7`
- iCloud-4: `1VIu-Cx7ae_SzcYlDBD5P9UZIIe3cKmJK`

### Deep research prompting (Opus-level analysis)

When user says "research layer", "detailed analysis", or "make sure each image is scanned correctly", use step-by-step reasoning prompts:

```python
deep_prompt = """You are an expert image analyst. Analyze this image with deep reasoning.

TASK: Determine if this is a screenshot of a CONTACT LIST or SPREADSHEET containing personal contact information.

THINK STEP BY STEP:
1. What type of image is this? (photo, screenshot, document, etc.)
2. If it's a screenshot, what application is shown? (Excel, Google Sheets, Numbers, Contacts app, etc.)
3. Is there a grid/table/list structure visible?
4. Are there multiple rows of data (2 or more people)?
5. For each row, can you identify: a person's NAME, a PHONE NUMBER, and an EMAIL ADDRESS?

A MATCH must have:
- Tabular/list structure (grid, rows, columns)
- Multiple contact records (2+ people)
- Each record contains at minimum: a name AND (phone OR email)
- Looks like data exported from or displayed in a spreadsheet/contacts app

NOT a match:
- Single contact cards or profiles
- Chat/messaging conversations
- Social media screenshots
- App settings or menus
- Photos of people
- Documents without contact data
- Business cards (single person)

IMPORTANT: Be INCLUSIVE if uncertain. If it MIGHT be a contact list, say YES.

Provide your reasoning, then on the FINAL LINE write only: MATCH or NO_MATCH"""
```

Use `ANTHROPIC_API_KEY` (not OAuth token) with `x-api-key` header for Sonnet/Opus models. The OAuth token only works with Haiku.

### Cross-match verification before deleting source images

After extracting contacts to a sheet, verify all data is captured before deleting source images:

```python
# 1. Get all emails from sheet
sheet_emails = set()
for row in sheet_data.get('values', []):
    if row and row[0]:
        for email in row[0].lower().split('/'):
            if '@' in email:
                sheet_emails.add(email.strip())

# 2. Re-extract emails from each source image
image_emails = set()
for img in images:
    # ... download and vision extract emails ...
    image_emails.update(extracted_emails)

# 3. Check for missing (allow for OCR variation)
for email in image_emails:
    prefix = email.split('@')[0]
    # Fuzzy match — 70% character match catches OCR variations
    found = any(
        sum(1 for a,b in zip(prefix, existing) if a==b) >= len(min(prefix, existing)) * 0.7
        for existing in [e.split('@')[0] for e in sheet_emails]
    )
    if not found:
        print(f"⚠️ Possibly missing: {email}")
```

Only delete source images after cross-match shows all contacts captured (or variations are OCR noise).

### Quality check for extracted contact data

After writing to sheet, validate with regex patterns:

```python
import re

email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
phone_pattern = re.compile(r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$')

errors = []
for i, row in enumerate(rows[1:], 2):  # Skip header
    name, phone, email = row[1], row[2], row[3]
    issues = []
    if not name or len(name) < 3:
        issues.append("bad name")
    if not phone_pattern.match(phone.replace(" ", "")):
        issues.append("bad phone")
    if not email_pattern.match(email.split('/')[0].strip()):
        issues.append("bad email")
    if issues:
        errors.append((i, issues))

# Mark bad data as UNCLEAR rather than guessing
for row_num, issues in errors:
    if "bad phone" in issues:
        # Update cell to UNCLEAR
        ...
```

### Deduplication when adding new contacts

Dedupe by email prefix before appending new rows:

```python
existing_emails = set()
for row in existing_sheet_data:
    for email in row[3].lower().split('/'):
        existing_emails.add(email.strip())

new_contacts = []
for contact in extracted_contacts:
    email = contact.get('email', '').lower().split('/')[0].strip()
    if email and email not in existing_emails:
        new_contacts.append(contact)
        existing_emails.add(email)  # Prevent duplicates within batch too
```

### OCR+regex PII detection (fallback only)

Only use if vision is unavailable. Less accurate — generates false positives on non-PII content.

```python
import re

def contains_pii(text):
    if not text or len(text.strip()) < 3:
        return False, []
    found = []
    if re.search(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', text):
        found.append('email')
    for p in re.findall(r'(\+?[\d\s\-().]{7,}\d)', text):
        if len(re.sub(r'\D', '', p)) >= 7:
            found.append('phone')
            break
    if re.search(r'(?i)(name\s*[:]\s*\S|full\s*name\s*[:]\s*\S|first\s*name|last\s*name|surname)', text):
        found.append('name')
    return len(found) > 0, found
```
