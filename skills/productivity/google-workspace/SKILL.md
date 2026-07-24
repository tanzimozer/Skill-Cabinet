---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Email + Calendar** → Continue with this skill, but use
  `--services email,calendar` during auth so the consent screen only asks for
  the scopes they actually need.

- **Calendar/Drive/Sheets/Docs only** → Continue with this skill and use a
  narrower `--services` set like `calendar,drive,sheets,docs`.

- **Full Workspace access** → Continue with this skill and use the default
  `all` service set.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
>    Enable: Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API
> 3. Set up the OAuth consent screen (Google now calls this "Google Auth Platform"):
>    https://console.cloud.google.com/auth/overview
>    Click "Get started" → fill App name + support email → Next → select External → Next → add contact email → Next → Create
> 4. **IMPORTANT — Add yourself as a test user BEFORE visiting the auth URL:**
>    https://console.cloud.google.com/auth/audience
>    Test users → Add users → add your Gmail. **Do this before step 5, not after.** Skip this and you'll get `access_denied` even after clicking Allow. If user already got `access_denied`, have them add the test user now and generate a fresh auth URL — old codes are invalid.
> 5. Create the OAuth client:
>    https://console.cloud.google.com/auth/clients
>    Create client → Desktop app → name it "Friday" → Create
> 6. Copy the Client ID and Client Secret shown in the dialog. **CRITICAL: The full Client Secret is only shown once at creation time.** After that, the Clients list only shows the last 4 characters (e.g. `****-o_2`). If you need to retrieve it later, you cannot — you must click "+ Add secret" to generate a new one.

Once they provide the client ID and secret, write the JSON file yourself and run:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

The JSON format for a Desktop app client secret file:
```json
{
  "installed": {
    "client_id": "CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "GOCSPX-...",
    "redirect_uris": ["http://localhost:1", "urn:ietf:wg:oauth:2.0:oob"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
  }
}
```

Save it to `~/hermes-friday-client-secret.json` (avoid paths with `/Downloads/` that may not exist).

### Step 3: Get authorization URL

```bash
$GSETUP --auth-url
```

This prints the auth URL directly to stdout. Note: `--services` and `--format` flags are NOT supported in the current setup.py — use the bare command only.

Agent rules for this step:
- Send the URL to the user as a single line.
- Tell the user that the browser will likely fail on `http://localhost:1` after approval, and that this is expected.
- Tell them to copy the ENTIRE redirected URL from the browser address bar.
- If the user gets `Error 403: access_denied` or `access_denied`, send them directly to `https://console.cloud.google.com/auth/audience` to add themselves as a test user under Test users → Add users. **They MUST do this BEFORE clicking the auth URL**, not after.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

If `--auth-code` fails because the code expired, was already used, or came from
an older browser tab, it now returns a fresh `fresh_auth_url`. In that case,
immediately send the new URL to the user and have them retry with the newest
browser redirect only.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` points it at the same `~/.hermes/google_token.json` credentials file. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`

## Usage

All commands go through the API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Wix API — Correct Endpoint (May 2026)

Wix IST tokens (format: `IST.eyJ...`) work with the **site-list** endpoint, NOT site-properties:

```python
# WORKS
requests.post("https://www.wixapis.com/site-list/v2/sites/query",
    json={"query": {}}, headers={"Authorization": token})

# FAILS (403)
requests.get("https://www.wixapis.com/site-properties/v4/properties", ...)
```

Store credentials at `~/.hermes/.wix_credentials.json`:
```json
{"api_key": "IST...", "site_id": "ab465896-...", "site_name": "TIMBR"}
```

## GAPI Path — Use $HOME not ~

When calling `google_api.py` from scripts or cron, `~` does NOT expand properly in all contexts. Use explicit path:
```bash
python /home/hermes/.hermes/skills/productivity/google-workspace/scripts/google_api.py
```

## Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD

# Trash / Delete (google_api.py does NOT support trash — use direct Python)
# Trash one or more messages:
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
gmail = build('gmail', 'v1', credentials=creds)

for mid in ['MESSAGE_ID_1', 'MESSAGE_ID_2']:
    gmail.users().messages().trash(userId='me', id=mid).execute()
    print(f"Trashed: {mid}")
```
# Save to /tmp/gmail_trash.py and run with python3 — avoids shell quoting issues.
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search only — google_api.py does NOT support folder creation or file upload
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5
```

#### Drive — Folder creation and file upload (direct Python required)

`google_api.py` only exposes `drive search`. For creating folders or uploading files, write a script and run it:

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
drive = build('drive', 'v3', credentials=creds)

# Create a folder
folder = drive.files().create(
    body={'name': 'MY_FOLDER', 'mimeType': 'application/vnd.google-apps.folder'},
    fields='id, name, webViewLink'
).execute()
folder_id = folder['id']

# Upload a file into the folder
media = MediaFileUpload('/path/to/file.md', mimetype='text/markdown', resumable=False)
f = drive.files().create(
    body={'name': 'file.md', 'parents': [folder_id]},
    media_body=media,
    fields='id, name, webViewLink'
).execute()
print(f['webViewLink'])
```

Save to `/tmp/drive_upload.py` and run with `python3 /tmp/drive_upload.py` — avoids shell quoting issues with `-c`.

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

#### Direct Python (when gws/google_api.py unavailable)

Use `googleapiclient` directly for multi-tab spreadsheets or when the CLI isn't installed:

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

# List all tabs
meta = sheets.get(spreadsheetId=SHEET_ID).execute()
tab_names = [s['properties']['title'] for s in meta['sheets']]

# Read a tab (quote tab names with spaces using single quotes in the range string)
result = sheets.values().get(spreadsheetId=SHEET_ID, range="'Tab Name'!A1:K100").execute()
rows = result.get('values', [])

# Search across all tabs
for tab in tab_names:
    result = sheets.values().get(spreadsheetId=SHEET_ID, range=f"'{tab}'!A1:K200").execute()
    for i, row in enumerate(result.get('values', [])):
        if 'keyword' in ' '.join(row).lower():
            print(f"Tab: {tab} | Row {i+1}: {row}")

# Update a single cell
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range="'Tab Name'!E2",
    valueInputOption='RAW',
    body={'values': [['New Value']]}
).execute()
```

#### Adding a new tab via batchUpdate

`google_api.py` does not support adding sheets. Use direct Python:

```python
r = requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate',
    headers=headers,
    json={'requests': [{'addSheet': {'properties': {'title': 'NewTab'}}}]}
)
new_sheet_id = r.json()['replies'][0]['addSheet']['properties']['sheetId']
```

#### Writing to tabs with `/` in their name (e.g. "05/27")

- **Reading**: `05%2F27!A1:Z100` in the URL path works fine.
- **Writing via PUT**: URL path encoding and body range must match exactly — both must use the same notation or you get `400: Request range does not match value's range`. Avoid the mismatch entirely by using `values:batchUpdate` (POST) instead of `values/{range}` (PUT):

```python
# ✅ WORKS — batchUpdate POST, single quotes in body range only
r = requests.post(
    f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate',
    headers=headers,
    json={
        'valueInputOption': 'USER_ENTERED',
        'data': [{'range': "'05/27'!A1", 'majorDimension': 'ROWS', 'values': rows}]
    }
)

# ❌ FAILS — PUT with URL-encoded path but quoted body range → 400 mismatch
# ❌ FAILS — PUT with single-quoted path → 404
```

Use `values:batchUpdate` as the default write method for any tab whose name contains `/`, spaces, or other special characters.

**Pitfalls:**
- Tab names with spaces must be wrapped in single quotes in the range string: `"'Sheet Name'!A1:Z100"`
- Updating beyond the sheet's column/row limit raises `HttpError 400: Range exceeds grid limits` — check how many columns the sheet actually has before writing
- Column E being TRUE/FALSE (applied checkbox) may be the last column — adding a 6th column requires the sheet to have that column or it will fail
- **Auto-resize can hide data:** When writing tabular data (e.g. exercise tables with narrow columns like RPE, TEMPO), `autoResizeDimensions` may collapse columns with short values to near-zero width. Data appears missing but is actually there. Fix: set explicit column widths with `updateDimensionProperties` instead of relying on auto-resize:

```python
# Set explicit column widths (in pixels)
requests = []
column_widths = [200, 200, 100, 60, 60, 150]  # A through F
for i, width in enumerate(column_widths):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': i, 'endIndex': i + 1},
            'properties': {'pixelSize': width},
            'fields': 'pixelSize'
        }
    })
sheets.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': requests}).execute()
```

### Docs

```bash
$GAPI docs get DOC_ID
```

#### Docs — create + build structured documents (direct Python)

`google_api.py` only reads. To create a doc and fill it with headings/bullets/bold, use the Docs API directly. Scopes needed: `documents` + `drive` (both present in Tanzim's token).

**Pattern that works — create, then batch-insert with range tracking:**

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

t = json.load(open('/home/hermes/.hermes/google_token.json'))
creds = Credentials(token=t['token'], refresh_token=t['refresh_token'],
    token_uri=t['token_uri'], client_id=t['client_id'],
    client_secret=t['client_secret'], scopes=t['scopes'])
if not creds.valid: creds.refresh(Request())
docs = build('docs', 'v1', credentials=creds)

doc = docs.documents().create(body={'title': 'My Doc'}).execute()
doc_id = doc['documentId']   # URL: https://docs.google.com/document/d/{doc_id}/edit
```

**Building content — the reliable method:** assemble the full text as one string,
tracking each paragraph's start/end index as you go, then issue ONE `insertText`
followed by style ops. Docs indices start at **1**, and each line adds `len(text)+1`
(the trailing `\n`).

```python
# content = list of (kind, text): 'H'=title, 'S'=HEADING_2, 'T'=HEADING_3, 'B'=bullet, 'Q'=bold, 'P'=plain
full, ops = "", []
for kind, txt in content:
    start = len(full) + 1          # +1 because doc body starts at index 1
    full += txt + "\n"
    end = start + len(txt)
    if kind == 'H': ops.append((start, end, 'TITLE'))
    elif kind == 'S': ops.append((start, end, 'HEADING_2'))
    elif kind == 'T': ops.append((start, end, 'HEADING_3'))
    elif kind == 'B': ops.append((start, end, 'BULLET'))
    elif kind == 'Q': ops.append((start, end, 'BOLD'))

requests = [{'insertText': {'location': {'index': 1}, 'text': full}}]
for start, end, style in ops:
    if style in ('TITLE','HEADING_2','HEADING_3'):
        requests.append({'updateParagraphStyle': {
            'range': {'startIndex': start, 'endIndex': end+1},   # +1 to catch the newline
            'paragraphStyle': {'namedStyleType': style}, 'fields': 'namedStyleType'}})
    elif style == 'BULLET':
        requests.append({'createParagraphBullets': {
            'range': {'startIndex': start, 'endIndex': end},
            'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'}})
    elif style == 'BOLD':
        requests.append({'updateTextStyle': {
            'range': {'startIndex': start, 'endIndex': end},
            'textStyle': {'bold': True}, 'fields': 'bold'}})

docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

**Appending a new section to an existing doc — anchor-and-insert.** Don't try to
compute the end index blind. Fetch the doc, find the paragraph you want to insert
*before* (e.g. a closing line), grab its `startIndex`, and insert there. All new
ranges are then computed as `insert_index + len(full_so_far)`:

```python
d = docs.documents().get(documentId=doc_id).execute()
insert_index = None
for el in d['body']['content']:
    p = el.get('paragraph')
    if not p: continue
    txt = ''.join(r.get('textRun',{}).get('content','') for r in p.get('elements',[]))
    if txt.startswith('— Draft prepared'):   # your anchor line
        insert_index = el['startIndex']; break
if insert_index is None:
    insert_index = d['body']['content'][-1]['endIndex'] - 1
# then build `full` and ops with start = insert_index + len(full)  (NOT +1),
# insert at {'index': insert_index}
```

**Pitfalls:**
- Body index starts at 1, not 0. First `insertText` goes to `index: 1`.
- For paragraph styles (headings, bullets) extend `endIndex` by +1 to include the newline, or the style may not apply to the whole line.
- Insert bottom-up OR build-one-string-then-insert. Do NOT fire multiple separate `insertText` calls top-down — every insert shifts all later indices and the math breaks.
- Flag modelled/unverified numbers in the doc text itself (Tanzim wants "modelled, not verified" stated inline for any figure that isn't sourced) — see the research-legibility habit in the browser/research skill.

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search/upload**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`

## Useful Patterns

### Gmail web link for a message
To give the user a clickable link to open a specific Gmail message in their browser:
```
https://mail.google.com/mail/u/0/#inbox/{message_id}
```
The message ID comes from the `id` field in any Gmail search result.

### Finding interview/calendar confirmations in Gmail
Effective search query for scheduled interviews:
```python
# Today's scheduled interviews
query = '(interview scheduled OR "interview confirmation" OR "interview invitation" OR "schedule an interview" OR "we would like to interview" OR "next steps" OR "technical interview" OR "hiring manager") newer_than:14d'

# Find a specific time (e.g. 4 PM interviews)
query = '("4:00 PM" OR "4 PM" OR "16:00") newer_than:14d'
```
Run multiple queries and deduplicate by message ID — different query angles catch different confirmation formats (Zoom link emails, reminder emails, calendar invite emails are often separate messages).

### Extracting body text from Gmail messages
`format='metadata'` only returns headers. To get body content, use `format='full'` and recurse through `payload.parts`:
```python
def get_body(payload):
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    for part in payload.get('parts', []):
        if part['mimeType'] == 'text/plain':
            if part.get('body', {}).get('data'):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        result = get_body(part)  # recurse for nested parts
        if result:
            return result
    return ''
```
Prefer `text/plain` over `text/html` — cleaner to parse and strip.

## Rules

1. **Never send email or create/delete events without confirming with the user first.** Show the draft content and ask for approval.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Upgrading Scopes (e.g. drive.readonly → drive write)

The token stores the scopes it was granted at auth time. If a new operation needs a broader scope (e.g. Drive write when token only has `drive.readonly`), you get `HttpError 403: Insufficient Permission`.

Fix:
1. Edit `setup.py` SCOPES list — replace the narrow scope with the broader one (e.g. `drive.readonly` → `drive`)
2. Run `--auth-url` to generate a new consent URL
3. User approves → paste redirect URL back → run `--auth-code`
4. Token is now re-issued with the new scopes

**Pitfall:** The token file is overwritten on re-auth — all previously granted scopes must still be in the SCOPES list or they'll be dropped from the new token. Don't just add the new scope; keep the full list intact.

**Known scope that's too narrow by default:** `drive.readonly` — the setup.py shipped with this. It was patched to `drive` (full read/write) after a Drive folder creation failed with 403. The current SCOPES list in setup.py already has `drive` (full).

## Tanzim-specific notes

- **Client secret already on VM** at `~/friday_backup/google_client_secret.json` — never ask Tanzim to recreate it. For any re-auth, skip Steps 1–2 and go straight to `--auth-url`.
- **Token path:** `~/.hermes/google_token.json` — partial auth (`AUTHENTICATED (partial): missing documents.readonly`) is acceptable; Gmail, Drive, Sheets, Calendar all work fine without it.
- **Sheets created:**
  - "Software and API" — `18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4` — integration registry (columns: Software Name, API Key, Expiry/Status)
  - "Magazine Production" — `1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew` — TIMBR Workout Series content map (5 tabs, 8 rows each, 9 columns A–I)
  - "Tahmeed profile" — `19v5x4oScpEPXkjHBWvt97UHtWChki5UGniJvop258bc` — 2 tabs: User Profile (20 Qs) + AI Learnings (25-topic curriculum). Checkboxes in col B of AI Learnings tab.
  - "TIMBR Exercise DB — Stage Classified" — `1tyu3bKIaPAOjKh1-_ptgpzb0WhF7oPWTb60iq8S_i9s` — 119 exercises, 9 cols. Source DB (read-only, link-shared): `1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo`. "Type of Exercise" reclassified into TIMBR stage taxonomy: **Strength** (load/hypertrophy resistance) vs **Performance** (conditioning/cardio/explosive/work-capacity). Rule: default Strength; Performance = carries, grip-endurance, explosive/metabolic (Mountain Climber, Farmer's Carry, Snatch-Grip High Pull, Dead Hang, Wrist Roller, Plate Pinch).
  - "TIMBR Workout Engine DB" — `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo` — the live foundation for the workout-generation app. 9 tabs: FOUNDATION DB (gid 1007006981), STRENGTH DB (653476118), PERFORMANCE DB (1615007886), TRAINING SPLIT (1046226275), MUSCLE PAIRING (2001), MUSCLE BUNDLES (1363876170), RULES (1235482689), SCORING LOGIC (65557771), PROGRESSION LOGIC (314741848). Scoring model: each exercise rated Difficulty / Learning Curve / Risk (each 1–10, built from 1–3 sub-inputs), rolled up via `Level Score = Risk×0.40 + Difficulty×0.35 + Learning Curve×0.25` into F0–F3 bands. Sagar (collaborator) reviews it. **Muscle:Fat Ratio** (0–1, 1=pure muscle/0=pure fat-loss) is the agreed replacement for the old binary "Classification" column: `Muscle:Fat Ratio = Load×0.5 + Rest×0.3 + Continuity×0.2`, each input 0–1. Added as section ⑤ of the SCORING LOGIC tab. Open issues flagged but not yet fixed: S1–S3 vs F1–F3 tier naming is inconsistent; Risk inputs under-scored across the DB (often a lazy floor of 2 despite carrying the heaviest 0.40 weight); per-tab F/P/S band definitions not all defined.
- **GAPI variable pitfall:** `GAPI="python ~/.hermes/..."` fails in cron prompts and double-quoted strings because `~` doesn't expand. Always use `$HOME` or the full absolute path `/home/hermes/.hermes/...` when referencing the script.

## Sheets — fast whole-sheet read via gviz CSV (no API call)

For a quick dump of a single-tab sheet (or the first tab) when it's shared with link access, the gviz CSV export is faster than the Sheets API and needs no auth:

```bash
curl -sL "https://docs.google.com/spreadsheets/d/SHEET_ID/gviz/tq?tqx=out:csv" -o /tmp/out.csv
```

Returns proper quoted CSV with the header row. Ideal for "read this whole DB, classify it, write a new copy" workflows. For private sheets or specific tabs, fall back to the authenticated API below.

**Workflow rule — don't fight the browser for Sheets/Docs.** The live Google Sheets/Docs web app frequently times out under browser automation (snapshot/vision/navigate all hang). Do NOT retry the browser. Go straight to: (a) gviz/`export?format=csv&gid=...` for a quick read of a shared sheet, or (b) the authenticated Sheets API for private sheets, specific tabs by gid, or any write. The CSV `export?format=csv&gid=GID` endpoint reads a specific tab by gid without auth when the sheet is link-shared.

## Sheets — gspread shortcut for create + bulk write + share

`gspread` is available and is the cleanest path for "read a sheet, transform, write a fresh copy" tasks. It wraps create/update/share in a few lines:

```python
import json, gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

tok = json.load(open('/home/hermes/.hermes/google_token.json'))
creds = Credentials(token=tok['token'], refresh_token=tok['refresh_token'],
    token_uri=tok['token_uri'], client_id=tok['client_id'],
    client_secret=tok['client_secret'], scopes=tok['scopes'])
if not creds.valid:
    creds.refresh(Request())

gc = gspread.authorize(creds)
sh = gc.create("New Sheet Title")           # lands in Drive root
sh.sheet1.update(values=rows, range_name='A1')  # rows = list of lists incl. header
sh.share(None, perm_type='anyone', role='reader')  # link-accessible
print(sh.url, sh.id)
```

**Workflow rule for data transforms:** when reclassifying/editing an existing live sheet that others are working off, write to a NEW sheet by default — never mutate the live source in place unless explicitly told to. State the row counts and any judgement-call rows back to Tanzim for eyeball before he relies on it.

## Sheets — creating a new sheet with formatted headers (direct Python)

`google_api.py` does not support sheet creation. Use direct Python:

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

sheet = sheets.create(body={'properties': {'title': 'My Sheet'}}).execute()
print(sheet['spreadsheetId'], sheet['spreadsheetUrl'])
```

Then `sheets.values().update()` for header data and `sheets.batchUpdate()` for formatting in one follow-up call. Always set explicit `pixelSize` column widths — never rely on auto-resize.

## Sheets — Tanzim's formatting expectations
When building sheets for Tanzim, apply these standards or he will ask for a redo:
- **Text wrapping:** `wrapStrategy: WRAP` on all cells
- **Alignment:** `horizontalAlignment: LEFT`, `verticalAlignment: MIDDLE` (center-align only for short data like checkboxes, numbers)
- **Row height:** Minimum 40px for data rows, 44px for header; never let Google auto-squish rows
- **Column widths:** Always set explicitly — never auto-resize. Short cols (checkboxes, numbers): 50–90px. Text cols: 280–420px. URL cols: 260px.
- **Header row:** Grey background (`#F2F2F7` or similar), bold, frozen
- **Borders:** Apply `innerHorizontal` + `innerVertical` + outer border — clean grid lines throughout
- **Alternating rows:** Light grey alternating (`#F8F8FA`) for readability on long lists
- **Checkboxes:** Use `dataValidation: {condition: {type: BOOLEAN}}` — real clickable checkboxes, not text TRUE/FALSE
- **Tab structure:** Keep tabs minimal — ask Tanzim what 2–3 tabs are needed before creating 5+

Apply all formatting in a single `batchUpdate` call after writing data — not in separate calls.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `invalid_client` / "The provided client secret is invalid" | The secret stored on the server doesn't match Google's record. Google only shows the full secret once at creation — after that it's masked (shows as `****-o_2`). Fix: Cloud Console → Credentials → click the client → Client secrets → "+ Add secret" → copy the new secret → edit `~/.hermes/google_client_secret.json` directly and update the `client_secret` field. Then run `--auth-url` to generate a fresh URL and redo the auth flow. Do NOT reuse old auth codes — they are bound to the previous PKCE session and will always fail. |
| `invalid_grant: Token has been expired or revoked` | Refresh token itself is invalidated — `creds.refresh(Request())` won't help. Need full re-auth. See `references/google-oauth-reauth.md` for the complete manual flow without running setup.py. Key: build auth URL with client_id from `google_client_secret.json`, user opens it, copies redirect URL from address bar, you extract the `code` param and POST to `oauth2.googleapis.com/token`. |
| Token in `google_token.json` is expired and `Credentials.refresh()` fails silently / returns 401 | Use raw `requests.post` to refresh manually — more reliable than the SDK wrapper:<br>`r = requests.post('https://oauth2.googleapis.com/token', data={'client_id': t['client_id'], 'client_secret': t['client_secret'], 'refresh_token': t['refresh_token'], 'grant_type': 'refresh_token'})`<br>Then write `r.json()['access_token']` back to `google_token.json['token']` and use it directly in `Authorization: Bearer` headers. |
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED: invalid_scope: Bad Request` | Token was issued with a scope set that no longer matches. Client secret already on VM at `~/friday_backup/google_client_secret.json` — skip Steps 1-2, go straight to Step 3 (`--auth-url`) and redo Steps 3-5. Takes ~2 min. |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| Drive create/upload returns `insufficientPermissions` | Token was authorized with `drive.readonly` scope. Edit `setup.py` SCOPES list: replace `drive.readonly` with `drive`. Then `$GSETUP --revoke` and redo Steps 3-5. |
| Drive operations fail when using `google_api.py drive create-folder` | `google_api.py` only supports `drive search`. Use direct Python with `googleapiclient` for folder creation and file uploads — see Drive section above. |
| `HttpError 403: Access Not Configured` for Calendar | Google Calendar API must be enabled separately at https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview — even when Gmail/Drive/Sheets all work fine, Calendar is a separate enablement. The token scopes can include `calendar` but if the API isn't enabled in the Cloud project, every Calendar call returns 403. Fix: enable at the link above, wait ~2 min, retry. |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```
