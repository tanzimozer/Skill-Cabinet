# Gmail Automation — API Patterns & Pitfalls

## Auth
Google OAuth token at `~/.hermes/google_token.json`. Scopes: gmail.modify, drive, calendar, spreadsheets.
See vault_access skill for how to build `Credentials` object.

```python
from googleapiclient.discovery import build
service = build('gmail', 'v1', credentials=creds)
```

## Scope limitations
| Action | Scope needed | Available? |
|---|---|---|
| Read, search, list | gmail.readonly | ✅ |
| Label, trash, move | gmail.modify | ✅ |
| Hard-delete (batchDelete) | mail.google.com | ❌ not granted |
| Send | gmail.send | ✅ |

**Workaround for delete:** use `trash()` — auto-purges after 30 days. Tanzim explicitly wants this as a safety measure.

## Search queries that work well
```python
# Job application noise
'subject:("thank you for applying" OR "thanks for applying" OR "application received")'
'subject:("application status" OR "not moving forward" OR "other candidates")'
'subject:("keep track of your application")'  # Amazon tracker emails

# Sender-based
'from:jpmorgan OR from:jpmchase OR from:jpmorganchase'
'from:noreply@mail.amazon.jobs'
'from:indeedapply@indeed.com'

# Label management
'in:sent to:surbhi'  # sent emails to specific person
'in:inbox'           # inbox only
```

## Pagination pattern
```python
all_msgs = []
resp = service.users().messages().list(userId='me', q=query, maxResults=500).execute()
all_msgs.extend(resp.get('messages', []))
while 'nextPageToken' in resp:
    resp = service.users().messages().list(userId='me', q=query, maxResults=500, pageToken=resp['nextPageToken']).execute()
    all_msgs.extend(resp.get('messages', []))
```

## Get message metadata (fast — avoids fetching full body)
```python
detail = service.users().messages().get(
    userId='me', id=msg_id, format='metadata',
    metadataHeaders=['Subject','From','To','Date']
).execute()
headers = {h['name'].lower(): h['value'] for h in detail['payload']['headers']}
labels = detail.get('labelIds', [])  # ['INBOX', 'UNREAD', etc.]
snippet = detail.get('snippet', '')  # first ~100 chars of body
```

## Move to trash
```python
service.users().messages().trash(userId='me', id=msg_id).execute()
```

## Create label and move messages to it
```python
# Create label — handle already-exists gracefully
try:
    label = service.users().labels().create(userId='me', body={'name': 'JPMC'}).execute()
    label_id = label['id']
except Exception as e:
    if 'already exists' in str(e).lower():
        labels = service.users().labels().list(userId='me').execute()
        label_id = next(l['id'] for l in labels['labels'] if l['name'] == 'JPMC')
    else:
        raise

# Move message: add label, remove from INBOX
service.users().messages().modify(userId='me', id=msg_id, body={
    'addLabelIds': [label_id],
    'removeLabelIds': ['INBOX']
}).execute()
```

## Pitfalls
- **Don't use keyword guessing for important decisions.** Scanning all 563 emails and showing Tanzim the raw list by sender/subject is safer than auto-classifying and trashing. He'll flag what's actually junk.
- `noreply` sender pattern catches legit emails (interview reminders, calendar invites). Never auto-trash on sender alone.
- "Automated notifications" bucket is dangerous — interview reminders often come from noreply addresses
- Always show a preview list and get confirmation before trashing anything in bulk
- Check `r.text.strip().startswith('{')` is NOT needed for Gmail API — it uses proper HTTP status codes
- Total message count from `getProfile()` includes sent/drafts/all-mail, not just inbox. Filter by `labelIds` containing `INBOX`
