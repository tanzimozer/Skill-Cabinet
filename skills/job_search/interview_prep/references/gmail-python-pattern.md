# Gmail Search — Working Python Pattern

**NEVER use the `gmail` subagent toolset.** It hits a demo account (alex@example.com) and returns entirely fake emails. Always script directly.

## Working boilerplate

```python
import json, base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)

creds = Credentials(
    token=t.get('token'),
    refresh_token=t.get('refresh_token'),
    token_uri=t.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=t.get('client_id'),
    client_secret=t.get('client_secret'),
    scopes=t.get('scopes')
)

svc = build('gmail', 'v1', credentials=creds)

# Search
results = svc.users().messages().list(
    userId='me',
    q='interview after:2026/07/01',  # adjust query
    maxResults=20
).execute()

messages = results.get('messages', [])
for m in messages:
    msg = svc.users().messages().get(userId='me', id=m['id'], format='full').execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    subject = headers.get('Subject', '')
    sender  = headers.get('From', '')
    date    = headers.get('Date', '')
    
    # Decode body
    body = ''
    payload = msg['payload']
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                body = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
                break
    elif payload['body'].get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data'] + '==').decode('utf-8', errors='ignore')
    
    print(f"FROM: {sender}\nSUBJECT: {subject}\nDATE: {date}\nBODY:\n{body}\n{'—'*40}")
```

## Useful query strings
- `interview` — all interview emails
- `interview after:2026/07/13` — today onwards
- `from:Complete Fence` — specific sender domain
- `subject:interview` — subject-line only
- `Commercial Project Coordinator` — role name search

## Account confirmed
- Real account: tanzim.seattle@gmail.com
- Token path: `/home/hermes/.hermes/google_token.json`
