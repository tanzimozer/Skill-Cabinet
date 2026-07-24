---
name: gmail_cleanup
category: productivity
description: Scan and trash useless emails from Tanzim's Gmail (tanzim.seattle@gmail.com) using the Gmail API. Covers job application noise, newsletters, automated notifications, OTPs. Always use trash (not hard delete) — Tanzim prefers the 30-day safety net.
---

# Gmail Cleanup

## Auth pattern
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)
creds = Credentials(
    token=t['token'], refresh_token=t['refresh_token'],
    token_uri=t['token_uri'], client_id=t['client_id'],
    client_secret=t['client_secret'], scopes=t['scopes']
)
service = build('gmail', 'v1', credentials=creds)
```

Scope is `gmail.modify` — can trash but NOT hard-delete (batchDelete needs `mail.google.com` scope).

## Scan approach — fetch ALL, then classify
Don't rely on search queries alone — they miss things. Fetch all 500+ messages with metadata, then classify in Python.

```python
# Fetch all message IDs
all_msgs = []
resp = service.users().messages().list(userId='me', maxResults=500).execute()
all_msgs.extend(resp.get('messages', []))
while 'nextPageToken' in resp:
    resp = service.users().messages().list(userId='me', maxResults=500,
        pageToken=resp['nextPageToken']).execute()
    all_msgs.extend(resp.get('messages', []))

# Enrich with headers
for m in all_msgs:
    detail = service.users().messages().get(userId='me', id=m['id'],
        format='metadata',
        metadataHeaders=['Subject','From','To','Date']).execute()
    # headers, labelIds, snippet all available here
```

## Trash (not delete)
```python
service.users().messages().trash(userId='me', id=mid).execute()
```
Tanzim explicitly prefers trash — it's a safety measure. Never hard-delete.

## Classification rules for Tanzim's inbox

### Always trash
- Job application thank-yous / received confirmations (Workday, Greenhouse, ATS systems)
- Amazon "keep track of your application" (noreply@mail.amazon.jobs)
- Generic application updates with no real content
- Newsletter/marketing with unsubscribe headers
- OTP codes older than 24h
- Duplicate interview reminders (keep the most recent only)
- Promotional emails (Spotify, Google One upsells, Yelp, Glassdoor digests)
- Indeed job match suggestions

### Always keep
- Active recruiter threads (real human names, back-and-forth)
- Interview confirmations and calendar invites
- Offer letters, rescind notices, onboarding emails
- Background check / Fieldprint / fingerprint emails
- Pre-adverse action notices (JPMorgan Global Workforce Screening etc.)
- Emails from/to Tanzim himself (sent items)
- Google Workspace shares (Sheets, Docs)
- Financial emails (receipts for real purchases, bank correspondence)
- TIMBR-related emails

### Ambiguous — surface to Tanzim before trashing
- "Application status update" — could be rejection OR next step. Check snippet.
- "Action required" from ATS — could be assessment invite (potentially useful) or just a login link
- Recruiter outreach (Jobot, CyberCoders etc.) — check if it's a match for active roles

## Reporting format
When reporting before trashing, group by category:

```
📁 Job application thank-yous: 54
📁 Automated/ATS noise: 30  
📁 Newsletters/marketing: 15
...
Total deletable: 99 | Keeping: 227
```

Then confirm with Tanzim before trashing — show a sample of each category, especially anything ambiguous.

## INBOX-only scan
When Tanzim says "scan my inbox" — filter to `INBOX` label only, not all mail. The full mailbox includes OTHER/SENT which inflates numbers.

```python
inbox = [e for e in emails if 'INBOX' in e.get('labels', [])]
```

## Tanzim's inbox profile (June 2026 baseline)
- Heavy job search activity — hundreds of ATS/Workday emails
- Active recruiter threads: FoundationAI, ITC, Essex, Fluxx, Salesforce
- Google/TIMBR operational emails
- Some old DoorDash order history, YouTube Music promos
- ~560 total messages; after cleanup ~460 useful

## Notes
- `gmail.modify` scope is sufficient for all operations except hard-delete
- Browser-based Gmail is unreliable from the agent — always use API directly
- Google OAuth token at `~/.hermes/google_token.json` — already has correct scopes
