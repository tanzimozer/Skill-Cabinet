---
name: google-workspace-integration
category: integrations
description: Reading Gmail, Drive, and Sheets via the Google API on Tanzim's account. Token auth, common search patterns, spreadsheet navigation.
triggers:
  - "search my gmail"
  - "find email"
  - "check my calendar"
  - "give me the sheet"
  - "find the spreadsheet"
  - "download the PDF from Drive"
  - "job tracker sheet"
---

# Google Workspace Integration

## Auth setup
- Token file: `/home/hermes/.hermes/google_token.json` — NOT `/root/` (agent runs as `hermes` user)
- Load with `google.oauth2.credentials.Credentials` from token dict keys: `token`, `refresh_token`, `token_uri`, `client_id`, `client_secret`, `scopes`
- Build clients: `build('gmail', 'v1', credentials=creds)`, `build('drive', 'v3', ...)`, `build('sheets', 'v4', ...)`

## Gmail search
- Use Unix timestamp `after:` for date filtering (not human-readable strings)
- Prefer `text/plain` body parts — HTML needs tag-stripping and is noisier
- Direct link to email: `https://mail.google.com/mail/u/0/#inbox/{message_id}`
- See `references/gmail-search-patterns.md` for confirmed working queries

## Google Sheets — tab navigation
- Get GID: `meta['sheets'][n]['properties']['sheetId']`
- Direct tab link: `https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={gid}`
- Tab names with slashes (e.g. `5/8`) must be quoted in range strings: `"'5/8'"`

## Google Drive — download file
```python
request = drive.files().get_media(fileId=file_id)
with open('/tmp/filename.pdf', 'wb') as f:
    f.write(request.execute())
```
Then parse PDFs with `pdfplumber`.

## Google Docs — create, edit, build tables, share (verified Jun 2026)
Build clients: `build('docs', 'v1', creds)` + `build('drive', 'v3', creds)`. Requires the `documents` + `drive` scopes (present in Tanzim's token).

Core pattern for a shareable report doc:
1. `docs.documents().create(body={"info":{"title":...}})` → `documentId`
2. Insert body text at the top: `batchUpdate(requests=[{"insertText":{"location":{"index":1},"text":body}}])`
3. Make it shareable to anyone with the link: `drive.permissions().create(fileId=doc_id, body={"type":"anyone","role":"reader"})`
4. Link: `https://docs.google.com/document/d/{doc_id}/edit`

**Real tables (not ASCII art) — the gotcha that matters:** Tanzim rejects monospace/ASCII tables in Docs ("don't keep empty spaces when there's an overlap of a row… one point in one row"). Use a real `insertTable` and populate cells. Cell population MUST insert from the LAST cell to the FIRST so earlier insertions don't shift later cell start-indices. See `references/google-docs-api-patterns.md` for the full working code (insertTable, cell-walk, reverse-order population, replaceAllText for surgical edits, full doc rebuild via deleteContentRange).

**Surgical edits without rebuilding:** `replaceAllText` with `{"containsText":{"text":...,"matchCase":False},"replaceText":...}` — ideal for updating a single figure (e.g. 500 → 5,000) without touching the rest.

**Doc formatting/legibility preferences (Tanzim):** neutral by default — no recipient names baked into a doc he may forward to anyone. One point per line, no wrapping clutter. Real tables for any numeric matrix.

## Known disabled APIs
- **Google Calendar API** — NOT enabled on project 313611152308. Returns 403. Do not attempt `build('calendar', 'v3', ...)`. Workaround: search Gmail for calendar invite emails instead.
- **Google Forms API** — may be disabled on the active project (friday-mark-2). `forms().create()` returns 403 "Forms API has not been used in project … or it is disabled." Fix is owner-side: enable at `console.developers.google.com/apis/api/forms.googleapis.com/overview?project=<id>`, AND the token needs the `forms.body` scope added (a re-auth). Don't claim it's impossible — it's a one-click enable + re-auth.

## Tanzim's key sheets
- **Job_Tracker** — `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q` — daily job application logs by date tab + Interviews tab
- **TERRAjob** — `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI` — automated job pipeline sheet, Master tab + date tabs

## References
- `references/gmail-search-patterns.md` — confirmed query strings, body extraction code, direct link format
