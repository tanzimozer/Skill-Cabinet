# Google Docs Creation via API

Confirmed working pattern (2026-07).

## Token location

```bash
/home/hermes/.hermes/google_token.json
```
Fields: `token`, `refresh_token`, `token_uri`, `client_id`, `client_secret`, `scopes`

Note: `/home/hermes/.hermes/GOOGLE_OAUTH_ACTIVE.json` does NOT contain refresh_token — use `google_token.json`.

## Python pattern

```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open("/home/hermes/.hermes/google_token.json") as f:
    tok = json.load(f)

creds = Credentials(
    token=tok["token"],
    refresh_token=tok["refresh_token"],
    token_uri=tok["token_uri"],
    client_id=tok["client_id"],
    client_secret=tok["client_secret"],
    scopes=tok["scopes"],
)

docs = build("docs", "v1", credentials=creds)

# 1. Create document
doc = docs.documents().create(body={"title": "My Title"}).execute()
doc_id = doc["documentId"]

# 2. Insert text
requests = [{
    "insertText": {
        "location": {"index": 1},
        "text": "Full document body here..."
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

print("https://docs.google.com/document/d/" + doc_id)
```

## Gotchas

- `GOOGLE_OAUTH_ACTIVE.json` has no `refresh_token` → will throw `RefreshError`. Use `google_token.json`.
- `googleapiclient` is installed in the hermes venv — no need to pip install.
- Insert index starts at 1, not 0.
- For structured docs, insert all text in one `insertText` call first, then apply styles via `updateParagraphStyle` / `updateTextStyle` batchUpdate in a second call.
- The API auto-creates the doc in the authenticated user's Drive root — no folder ID needed.
