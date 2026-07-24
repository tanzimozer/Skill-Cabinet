---
name: gmail-search-and-triage
description: Search Gmail for specific email types (interviews, jobs, junk), extract body content, and triage/summarise for Tanzim.
category: productivity
tags: [gmail, google, email, jobs, interviews, triage, search]
related_skills: [google-oauth-refresh]
---

# Gmail Search & Triage

Searching Gmail programmatically via Google API — for job interviews, scheduling emails, junk triage, and recruiter outreach. Uses the `google-auth` + `googleapiclient` libraries already installed in the hermes venv.

## Credentials

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data.get('token'),
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
    scopes=token_data.get('scopes')
)

service = build('gmail', 'v1', credentials=creds)
```

**Pitfall:** `~/.hermes/google_token.json` is owned by `hermes` user — always use the full `/home/hermes/` path, not `~/.hermes/`. The `~` resolves to `/root/` when running as root, causing PermissionError.

## Search Query Patterns

Gmail search uses the same syntax as the Gmail web UI:

```python
# Interviews today
import datetime
today = datetime.date.today()
after_ts = int(datetime.datetime(today.year, today.month, today.day, 0, 0, 0).timestamp())
query = f'(interview OR "phone screen" OR "hiring") after:{after_ts}'

# Interview confirmations / scheduling (last 14 days)
query = '(interview scheduled OR "interview confirmation" OR "interview invitation" OR "schedule an interview" OR "we would like to interview") newer_than:14d'

# Junk/marketing sweep
query = 'newer_than:1d (unsubscribe OR "marketing" OR "newsletter" OR "no-reply") -in:sent'

# By sender
query = 'from:WFronczak@essex.com subject:REMINDER newer_than:7d'
```

## Fetching Messages

```python
# Search
results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
messages = results.get('messages', [])

# Get metadata only (fast)
for msg in messages:
    m = service.users().messages().get(
        userId='me', id=msg['id'],
        format='metadata',
        metadataHeaders=['Subject', 'From', 'Date', 'To']
    ).execute()
    headers = {h['name']: h['value'] for h in m['payload']['headers']}
```

## Extracting Body Text

```python
import base64, re

def get_body(payload):
    """Extract plain text from message payload — handles nested parts."""
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

# Get full message with body
m = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
body = get_body(m['payload'])
body_clean = re.sub(r'<[^>]+>', ' ', body)       # strip HTML tags
body_clean = re.sub(r'\s+', ' ', body_clean).strip()
```

## Getting Gmail Link to a Message

```python
msg_id = msg['id']
gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
```

## Timestamp-Based vs Relative Search

- **`after:{unix_timestamp}`** — precise to the second, good for "today only"
- **`newer_than:7d`** — relative, simpler, good for "last N days"
- Combine: `newer_than:14d after:{timestamp}` doesn't work — pick one

## Interview Detection Strategy

Emails that confirm an interview (vs. rejection or application ack):

```python
INTERVIEW_SIGNALS = [
    'interview scheduled', 'interview confirmation', 'interview invitation',
    'we would like to interview', 'schedule an interview',
    'your interview', 'zoom conference', 'google meet', 'teams meeting',
    'reminder:', 'interview reminder', '3:00 PM', '4:00 PM'
]

REJECTION_SIGNALS = [
    'we have selected another candidate', 'not moving forward',
    'we appreciate your interest', 'other candidates', 'not a match'
]
```

## Junk Triage Categories

When scanning for deletable emails, group into:
1. 🗑️ Job rejections / automated HR (Workday, Greenhouse, AshbyHQ)
2. 📢 Marketing / newsletters (unsubscribe link present)
3. 🤖 App notifications / automated alerts (no-reply@, donotreply@)
4. 🧾 Receipts / confirmations (no action needed)
5. ❓ Other low-value

**Always flag, never delete without explicit permission from Tanzim.**

## Known Pitfall — Calendar API Disabled

Google Calendar API is **disabled** in GCP project `313611152308`. Calling `build('calendar', 'v3', credentials=creds)` will return a 403. Use Gmail search for calendar-related info instead (look for calendar invite emails).

To re-enable: https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview?project=313611152308

## Key Resources

| Sheet / Doc | ID |
|---|---|
| Job_Tracker (interviews tab) | `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q` |
| Interviews tab GID | `1499246630` |
| TerraJob sheet | `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI` |

## Cron Jobs Active (as of May 30, 2026)

| Job ID | Schedule | Purpose |
|---|---|---|
| `8b19da12d038` | 11:45 PM daily | Nightly Gmail junk sweep — flag for Tanzim's deletion permission |
| `2eefd5d0fead` | 9:00 AM daily | Morning job brief — interviews + actions needed today |
| `7a02da23ceba` | 3:00 AM daily | Memory organisation + identity audit (silent unless anomaly) |
