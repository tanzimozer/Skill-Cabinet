# Gmail Bulk Operations Workflow

## Overview
Pattern for safely scanning and bulk-actioning emails (trash, label, archive) without destructive mistakes.

## Workflow: Scan → Quality Check → Act

### 1. Initial Scan (Discovery)
Use `messages().list()` with search query and `resultSizeEstimate` to assess scale:

```python
results = service.users().messages().list(
    userId='me',
    q='from:indeed',
    maxResults=100,
    fields='messages(id),resultSizeEstimate'
).execute()
count = results.get('resultSizeEstimate', 0)
```

**Key patterns that work reliably:**
- `from:domain.com` — exact sender domain
- `from:(noreply@ OR no-reply@)` — multiple senders (OR syntax)
- `subject:(word1 OR word2)` — keyword alternatives
- `label:LABELNAME` — Gmail label search

**Avoid:** wildcard patterns like `from:*.notifications.com` don't work in Gmail API search.

### 2. Quality Check (Before Any Destructive Action)
Always fetch a 2–3 sample from each category using `messages().get()` with `format='metadata'` and `metadataHeaders`:

```python
email = service.users().messages().get(
    userId='me',
    id=msg['id'],
    format='metadata',
    metadataHeaders=['From', 'Subject', 'Date']
).execute()
headers = {h['name']: h['value'] for h in email.get('payload', {}).get('headers', [])}
```

**Human review requirement:** Display From, Subject, Date and ask for confirmation before proceeding to trash/label/archive.

**Why:** Search patterns can be overly broad or misclassify emails. Indeed emails include recruiter direct messages (potentially important), not just digests.

### 3. Action: Trash or Label

**Trash (safe — 30-day recovery window):**
```python
service.users().messages().trash(userId='me', id=msg['id']).execute()
```
Emails remain in Trash for 30 days; Tanzim views this as a safety measure (not permanent delete).

**Label + Remove from Inbox:**
```python
service.users().messages().modify(
    userId='me',
    id=msg['id'],
    body={
        'addLabelIds': [label_id],
        'removeLabelIds': ['INBOX']
    }
).execute()
```

**Do NOT use `batchDelete`:** requires `mail.google.com` scope (not granted). `trash()` is the practical alternative.

## Search Pattern Reference (Session-Tested)

**Job application confirmation / thank-you emails:**
```
from:(noreply@ OR no-reply@ OR do-not-reply@) subject:(confirmation OR thank OR receipt)
subject:("Application Received" OR "Application Confirmation" OR "Thank you for applying")
```
Result: 30 emails successfully identified and trashed.

**Job board digests (Indeed, Glassdoor):**
```
from:indeed
from:glassdoor
```
Result: 106 emails (Indeed job alerts, "stand out" recruiter pitches, Glassdoor market reports).

**Important emails (inverse filter for finding signal):**
```
label:STARRED
subject:(important OR action required OR ASAP)
subject:(offer OR opportunity OR congratulations)
from:(recruiter OR hiring OR hr@)
subject:(urgent OR critical OR breaking OR alert)
```

## Pagination for Full Inbox Scan
`messages().list()` maxResults caps at 500. For full inbox scan use `nextPageToken`:

```python
page_token = None
while True:
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=500,
        pageToken=page_token,
        fields='messages(id),nextPageToken'
    ).execute()
    messages = results.get('messages', [])
    # ... process messages ...
    page_token = results.get('nextPageToken')
    if not page_token:
        break
```

## Label Management
Create a label (use `messageListVisibility: 'hide'` to auto-archive):
```python
new_label = service.users().labels().create(
    userId='me',
    body={
        'name': 'Useless/Category',
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'hide'
    }
).execute()
label_id = new_label['id']
```

Get existing label ID:
```python
labels = service.users().labels().list(userId='me').execute()
label_id = next((l['id'] for l in labels.get('labels', []) if l['name'] == 'Useless/Job Apps'), None)
```

## Common Gotchas
1. **Search result is empty on retry:** If you move emails to a label or trash and then search again, they may not appear in the original search if the pattern relied on INBOX membership. Always fetch full results in the first query pass.
2. **Label doesn't appear in UI immediately:** New labels take a few seconds to sync; search will find them but the sidebar may lag.
3. **resultSizeEstimate can be inexact:** Use it for discovery scale only; fetch actual messages to get precise count.
