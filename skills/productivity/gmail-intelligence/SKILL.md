---
name: gmail-intelligence
description: Search, read, and extract actionable intelligence from Tanzim's Gmail using Google API. Covers interview detection, junk flagging, recruiter tracking, and nightly/morning summary patterns.
triggers:
  - "find my emails"
  - "check gmail"
  - "what interviews do I have"
  - "any emails about"
  - "search my email"
  - "nightly inbox sweep"
  - "morning job brief"
---

# Gmail Intelligence

## Auth pattern
```python
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

## Searching emails
```python
results = service.users().messages().list(
    userId='me', q=query, maxResults=20
).execute()
```

Key query patterns:
- Interviews today: `(interview OR "phone screen" OR "hiring manager") after:{unix_timestamp}`
- Interview confirmations (7-14 days): `(interview scheduled OR "interview confirmation" OR "we would like to interview") newer_than:14d`
- Junk sweep: run nightly, categories below

## Extracting body text
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

## Deep read (full format)
```python
m = service.users().messages().get(
    userId='me', id=msg['id'], format='full'
).execute()
headers = {h['name']: h['value'] for h in m['payload']['headers']}
body = get_body(m['payload'])
```

## Gmail link construction
```python
f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
```

## Interview detection
- Check for: confirmation emails, Zoom/Meet links, time slots
- Sources: myworkday.com, ashbyhq.com, greenhouse, roosterinc.com, itccorp.com, alex.com
- Key fields: Subject (REMINDER pattern), From (recruiter domain), body (time + Zoom link)
- Always convert to PT for Tanzim (Seattle-based)

## Junk sweep categories
- 🗑️ Job rejections / automated HR (myworkday.com, ashbyhq.com automated)
- 📢 Marketing / newsletters
- 🤖 App notifications / automated alerts
- 🧾 Receipts / confirmations (no action needed)
- ❓ Other low-value

## Pitfalls
- `google_token.json` requires permissions `600` — file was found at `664` (world-readable), fix: `chmod 600 ~/.hermes/google_token.json`
- Google Calendar API is disabled in GCP project 313611152308 — do not attempt calendar queries, use Gmail only
- Never invent interview details — only surface what is verifiably in Gmail
- myworkday.com emails are almost always automated rejections or ATS noise — low signal

## References
- See `references/interview-email-patterns.md` for known sender patterns
