---
name: email-scan-status
description: Scan Tanzim's Gmail inbox and sent folder, cross-match to get interview status, flag upcoming deadlines. Returns 2-5 actionable bullet points.
category: gmail
---

## Purpose
When Tanzim asks "scan my email" or similar, this skill:
1. Loads credentials from `google-oauth-refresh` skill
2. Connects to **tanzim.seattle@gmail.com** 
3. Pulls inbox and sent emails
4. Cross-matches to determine: already interviewed? pending response? deadline approaching?
5. Checks calendar for upcoming events (next 2 days)
6. Returns **2-5 concise bullet points only** — no long text

## Process

### 1. Load Credentials
Use existing `google_token.json` at `~/.hermes/google_token.json`:
```python
import json
import os

token_path = os.path.expanduser('~/.hermes/google_token.json')
with open(token_path, 'r') as f:
    token_data = json.load(f)
access_token = token_data['token']
```

If token expired (check `expiry` field), refresh using the `refresh_token`:
```python
import requests
from datetime import datetime, timedelta

resp = requests.post(
    token_data['token_uri'],
    data={
        'client_id': token_data['client_id'],
        'client_secret': token_data['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token'
    }
)
if resp.status_code == 200:
    new_data = resp.json()
    token_data['token'] = new_data['access_token']
    token_data['expiry'] = (datetime.utcnow() + timedelta(seconds=new_data.get('expires_in', 3600))).isoformat()
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)
    access_token = new_data['access_token']
```

### 2. Scan Inbox (all messages, last 50)
```python
import requests

headers = {'Authorization': f'Bearer {access_token}'}

# Get all messages
resp = requests.get(
    'https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=50',
    headers=headers
)
inbox_messages = resp.json().get('messages', [])
```

For each message, extract:
- **From** (sender name)
- **Subject** (look for keywords: interview, offer, rejection, confirmation, screening, etc.)
- **Date** (parse to check if recent — last 7 days = active)

Parse the full message body to detect:
- Interview scheduling language ("confirm your availability", "when are you available", "schedule", "interview time")
- Interview completion ("thanks for interviewing", "following our conversation", "next steps", "moving forward")
- Rejection ("decided not to move forward", "other candidates")
- Offer language ("congratulations", "offer", "position")

### 3. Scan Sent Folder (cross-match)
```python
# Get sent messages
resp = requests.get(
    'https://www.googleapis.com/gmail/v1/users/me/messages?q=in:sent&maxResults=30',
    headers=headers
)
sent_messages = resp.json().get('messages', [])
```

For each inbox email, look for a matching sent email (same subject/sender thread) dated **after** the inbox email. If found:
- **Status: Already responded** (you sent a reply)
- If no sent reply: **Status: Pending your response**

Extract the sent email's body to see what you said (acceptance, confirmation, availability, etc.)

### 4. Flag Interview Status
Build a map:

```
{
  "sender": "Company Name / Recruiter",
  "subject": "Interview Confirmation",
  "date": "Mon, 15 Jun 2026",
  "status": "INTERVIEW CONFIRMED" | "INTERVIEW PENDING" | "OFFER RECEIVED" | "REJECTED" | "DRAFT/INCOMPLETE",
  "action": "Nothing" | "Confirm attendance" | "Submit assessment" | "Respond by [DATE]",
  "days_old": 0
}
```

**Status rules:**
- **INTERVIEW CONFIRMED**: inbox has "confirmed" / "scheduled" language AND (sent email exists confirming OR calendar event exists)
- **INTERVIEW PENDING**: inbox has interview invite language BUT no sent reply yet
- **OFFER RECEIVED**: inbox has "congratulations", "offer", "formal offer" language
- **REJECTED**: inbox has "decided not to move forward" or similar
- **DRAFT/INCOMPLETE**: inbox has assessment link or "complete your application" language

### 5. Check Calendar (next 48 hours)
```python
# Get calendar events for next 2 days
now = datetime.utcnow().isoformat() + 'Z'
two_days_later = (datetime.utcnow() + timedelta(days=2)).isoformat() + 'Z'

resp = requests.get(
    f'https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now}&timeMax={two_days_later}',
    headers=headers
)
events = resp.json().get('items', [])
```

Extract event title, start time, link (if Zoom/Meet).

### 6. Return Format
**Return ONLY 2–5 bullet points**, no preamble, no explanation:

```
• Status: [Company] — [Interview Confirmed | Offer | Pending Response | Rejected]
• Action: [Confirm attendance by Friday | Submit assessment | Nothing]
• Upcoming: [Company interview tomorrow at 2pm] (if calendar event exists)
• Next steps: [One item only if actionable]
```

**Examples:**

✅ Good:
```
• Fluxx — Interview Confirmed (Jun 15, 5:45pm UTC)
• JPMorgan Chase — Offer Received (May 12) — status TBD
• Allen Institute — Screening call prep (Jun 12, 10:08pm UTC)
• SPS Global — Pending your response (interview invite sent Jun 9)
```

❌ Bad (too long, too much detail):
```
Hello Tanzim, I've scanned your email inbox and found several active interview processes...
```

## Notes
- **Ignore** marketing emails, job alerts, newsletters, system messages (Google security, confirmation codes, etc.)
- **Focus** on: recruiter emails, company correspondence, interview scheduling, offers, rejections
- **Cross-match** using: same subject thread, date proximity (inbox email → sent reply within 48 hours)
- **Timeframe**: Recent = last 7 days. Older items only if they're unresolved (pending action).
- **Failures**: If Gmail API returns 401, token is revoked — full re-auth required (see `google-oauth-refresh` skill). If 403, check Calendar API is enabled in GCP Console.
