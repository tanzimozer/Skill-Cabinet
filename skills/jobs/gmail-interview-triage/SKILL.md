---
name: gmail-interview-triage
description: Search Gmail for today's interviews, confirmed schedules, and job-related actions needed — then surface them cleanly
category: jobs
tags: [gmail, interviews, jobs, triage, google]
---

# Gmail Interview Triage

Reusable pattern for finding confirmed interviews and job actions from Gmail.

## Credentials

Google OAuth token: `~/.hermes/google_token.json` (chmod 600)
Scopes needed: `gmail.readonly` or `gmail.modify`

## Step 1 — Find today's interview emails

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json, datetime, base64, re

with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)
creds = Credentials(token=t['token'], refresh_token=t['refresh_token'],
    token_uri=t['token_uri'], client_id=t['client_id'],
    client_secret=t['client_secret'], scopes=t['scopes'])
service = build('gmail', 'v1', credentials=creds)

today = datetime.date.today()
after = int(datetime.datetime(today.year, today.month, today.day, 0, 0, 0).timestamp())

# Broad search — catch all job/interview emails today
query = f'(interview OR "phone screen" OR "hiring") after:{after}'
results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
```

## Step 2 — Find confirmed interview schedules (last 14 days)

```python
query = '(interview scheduled OR "interview confirmation" OR "schedule an interview" OR "we would like to interview") newer_than:14d'
results = service.users().messages().list(userId='me', q=query, maxResults=15).execute()
```

## Step 2b — Find recruiter phone/call scheduling (a distinct thread type)

Recruiter screen **calls** are scheduled in plain back-and-forth email, not formal
"interview confirmation" templates — they often won't match the Step 2 query. Search
them separately:

```python
query = '(call OR "phone screen" OR "phone interview" OR "give you a call" OR "speak with you" OR recruiter OR "connect with you") newer_than:10d'
results = service.users().messages().list(userId='me', q=query, maxResults=30).execute()
```

When a "do I have a call/interview today?" question comes in, run BOTH the interview
queries AND this call query — the answer is frequently a recruiter call thread, not a
formal interview. Identify the live thread by recency + back-and-forth (multiple
messages same subject in the last day or two).

## Step 2c — Catch Bookings / Outlook-Bookings meeting invites (title has NO keyword)

The biggest miss risk: some scheduled meetings arrive as calendar/Bookings invites
whose subject is just **"<Name> - Book Time W/<Recruiter>"** or **"Confirmed:
Interview"** — carrying *neither* "interview" nor "call", so Steps 1/2/2b all miss them.
They come from `*.onmicrosoft.com`, `bookings`, or a recruiter's direct address, often
with an `invite.ics` attachment.

```python
# Catch booking-page / calendar invites regardless of keyword
query = '("book time" OR "booking is confirmed" OR "scheduled from the bookings page" OR "Confirmed: Interview" OR filename:ics OR "reschedule or cancel") newer_than:14d'
results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
```

For a "what do I have today / do I have a call today?" question, run Steps 1, 2, 2b AND
2c. The live event is frequently one of these low-keyword Bookings invites, not a formal
template. Also do a plain date-scoped sweep: `after:{today_unix}` with no keyword filter,
then eyeball anything from a person/recruiter domain.

## Recruiter name ≠ company name

The sender/organizer is usually the **recruiter**, not the employer. The company is in
the **email domain** (`MariaSantaAna@columbiabank.com` → Columbia Bank) or the invite body
("Book time with Maria Santa Ana" from "Columbia Bank Talent Acquisition"). Resolve the
company from the domain/body *before* searching the job sheet — searching the recruiter's
name will return nothing.

## Step 3 — Extract body text

```python
def get_body(payload):
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    for part in payload.get('parts', []):
        if part['mimeType'] == 'text/plain':
            if part.get('body', {}).get('data'):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        result = get_body(part)
        if result:
            return result
    return ''
```

## Step 4 — Get direct Gmail link for an email

```python
# Email deep link format:
f"https://mail.google.com/mail/u/0/#inbox/{message_id}"
```

## What to surface

For each confirmed interview, extract and report:
- **Company + Role**
- **Date + Time (with timezone)**
- **Format** (Zoom/Google Meet/Phone/In-person)
- **Join link + password**
- **Interviewer name**
- **Gmail link** to the confirmation email

## Cross-reference with Job Tracker

After finding interviews via Gmail, cross-reference against:
- `Job_Tracker` sheet (ID: `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`) — Interviews tab (GID: `1499246630`)
- `TERRAjob` sheet (ID: `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI`) — date tabs
- `JOB_HAMMER` sheet (ID: `12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`) — has `MASTER_TAB`, `RESEARCH`, `Manual Entry`, plus one tab per application date (`Jun 24`, `Jun 25`, ...). Row shape: `[resume_pdf, score, company, role, pay, location, remote?, full_description, ..., applied_bool]`.

Search sheets for the **company name** (resolved from the email domain, not the recruiter)
to find which tab, row, and resume PDF was used.

### Locating a listing across dated tabs (JOB_HAMMER pattern)

```python
meta = sheets.spreadsheets().get(spreadsheetId=SID).execute()
tabs = [(s['properties']['title'], s['properties']['sheetId']) for s in meta['sheets']]
for tab, gid in tabs:
    vals = sheets.spreadsheets().values().get(spreadsheetId=SID, range=f"'{tab}'").execute().get('values', [])
    for i, row in enumerate(vals, start=1):
        if 'columbia' in " | ".join(row).lower():   # company term, lowercased
            print(f"[{tab}] gid={gid} ROW {i}")
```

- The **most recent dated tab** with the company is the canonical entry (pay range often
  filled in later than the original). Report tab name, gid, and row number.
- Deep link to the exact tab: `https://docs.google.com/spreadsheets/d/{SID}/edit#gid={GID}`
  (there is no per-row anchor via API — give the tab link + row number).

## Sheet tab URL format

```
https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={TAB_GID}
```

## Extracting someone's message VERBATIM (not a summary)

When the user asks for "what X said," "his exact words," "extract the message," or
"rewrite what he wrote in plain text" — he wants the **verbatim transcription**, not a
paraphrase or your synthesis. He will correct you sharply if you summarise ("not
summarize — his exact words"). Rules:

- Reproduce the message word-for-word, only cleaning up formatting/line breaks to plain
  text. Do not condense, reorder, or editorialise.
- If the source is a **screenshot** (image the user pasted), the auto-generated image
  description is a paraphrase — do NOT transcribe from it. Open the actual cached image
  and read it directly: `browser_navigate` to `file:///home/hermes/.hermes/image_cache/<file>.jpg`,
  then `browser_vision` asking for a verbatim transcription of the specific bubble.
- Confirm you're reading the RIGHT image before transcribing — multiple screenshots in a
  session are easy to mix up (verify the content matches what was asked).
- When he's working through items "one by one" / "segment by segment," give exactly one
  segment and stop; don't pre-summarise the rest into a block.

## Pitfalls

- Gmail `after:` filter takes **Unix timestamp**, not a date string
- `text/plain` body parts are more reliable than `text/html` for content parsing — prefer plain text
- Some confirmation emails are HTML-only with CSS noise — strip tags with `re.sub(r'<[^>]+>', ' ', body)`
- Google Calendar API (scope `calendar`) may be **disabled** in the GCP project — don't rely on it; use Gmail search instead
- Reminder emails and original confirmation emails for the same interview will both appear — de-dupe by company+role
- **Reschedule supersedes:** a later email in the same thread can move the time (e.g. "9:30am EST Wed" → "1:00pm" next day). Always take the time from the **most recent** message in the thread, not the first match, and read the whole thread before reporting.
- **Date discipline — confirm "today" vs "tomorrow" before answering.** Recruiters write relative dates ("tomorrow (07/01)", "Wednesday"). Resolve them against the actual current date, and don't report a past event as upcoming (e.g. an interview dated June 25 is done if today is June 30). State the absolute date you landed on.
- **Timezone — convert to the user's local zone.** Recruiter times are usually in the recruiter's zone (EST common). The user is in Seattle (PT). Always note the source zone AND give the user's local time, since whether it's "today" can flip across the date line of business hours. Use `TZ="America/Los_Angeles" date` to anchor "now".
