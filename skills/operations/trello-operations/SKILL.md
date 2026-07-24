---
name: trello-operations
description: Full Trello API operations via Python urllib — board management, list manipulation, card creation/movement, and board audit patterns for TIMBR production boards.
triggers:
  - "trello board"
  - "update trello"
  - "create trello card"
  - "move card"
  - "trello list"
  - "production board"
---

# Trello Operations

## Credentials
```python
KEY = "<TRELLO_KEY — see ~/.hermes/.trello_credentials>"
TOKEN = "<TRELLO_TOKEN — see ~/.hermes/.trello_credentials>"
# Stored at: ~/.hermes/.trello_credentials
BASE = "https://api.trello.com/1"
```

## Core helpers (urllib — no extra libraries)
```python
import urllib.request, urllib.parse, json

def trello_get(path, params={}):
    params['key'] = KEY
    params['token'] = TOKEN
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{BASE}{path}?{qs}", timeout=15) as r:
        return json.loads(r.read())

def trello_post(path, data={}):
    data['key'] = KEY
    data['token'] = TOKEN
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=encoded, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def trello_put(path, data={}):
    data['key'] = KEY
    data['token'] = TOKEN
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=encoded, method='PUT')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())
```

## Common operations

### Get all boards
```python
boards = trello_get("/members/me/boards")
```

### Get lists on a board
```python
lists = trello_get(f"/boards/{BOARD_ID}/lists")
```

### Get all cards on a board
```python
cards = trello_get(f"/boards/{BOARD_ID}/cards")
card_map = {c['name']: c['id'] for c in cards}
```

### Create a card
```python
trello_post("/cards", {
    'name': 'Card name',
    'desc': 'Description text',
    'idList': LIST_ID,
})
```

### Move/rename a card
```python
trello_put(f"/cards/{card_id}", {
    'idList': NEW_LIST_ID,
    'name': 'New name',
})
```

### Archive a card
```python
trello_put(f"/cards/{card_id}", {'closed': 'true'})
```

### Rename a list
```python
trello_put(f"/lists/{list_id}", {'name': 'New list name'})
```

## Key TIMBR boards
| Board | ID | URL |
|---|---|---|
| 7-Day Magazine Sprint | `6a0e81483e169b28504ba8c1` | https://trello.com/b/U7StsSvp |
| TIMBR Go-Live Checklist | `69f8218432c9e44a9ae1abb7` | — |
| Magazine/Ebook Production | `68f54f1e83384f8868a3ed8a` | — |
| TIMBR TO-DO | `69c5df3b602c38c64889bf09` | — |
| Founders Kanban | `6990ed968580db07dd48f4d8` | — |
| Blackwire | `69feb2296fdd6aa6a734101c` | — |

## Magazine Sprint board list IDs
| List | ID |
|---|---|
| 📋 TO DO | `6a0e81499eade99efbbaa28c` |
| 🔄 IN PROGRESS | `6a0e814993006a98af881696` |
| 👁️ IN REVIEW | `6a0e8149409a6f9a8e3bf7ff` |
| 🚀 LAUNCH PREP | `6a0e81496392d9a63c836ce4` |
| ✅ DONE | `6a0e814aa49ecbff5b43677f` |

## Pitfalls
- **No `&` in card names or descriptions** — use 'and' instead, ampersand breaks urllib encoding
- **Token lacks board admin permissions** — cannot add members via API; use manual Trello web invite
- **Write to a file first** for complex multi-operation scripts — avoid inline `&` backgrounding in terminal()
- Account: `tanzimozer1`
