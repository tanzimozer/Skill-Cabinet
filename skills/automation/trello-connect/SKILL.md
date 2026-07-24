---
name: trello-connect
description: Connect to Trello API with stored credentials and perform common board/card operations
category: automation
tags: [trello, api, automation, boards, cards]
---

# Trello Connect

Reusable skill for Trello API operations using securely stored credentials.

## Credentials

Stored at: `~/.hermes/.trello_credentials` (JSON format, chmod 600)

```json
{
  "api_key": "...",
  "token": "..."
}
```

## Load Credentials

```python
import json
import os

creds_path = os.path.expanduser('~/.hermes/.trello_credentials')
with open(creds_path, 'r') as f:
    creds = json.load(f)
    
api_key = creds['api_key']
token = creds['token']
```

## Helper Functions (urllib — no external deps, confirmed working May 2026)

**IMPORTANT:** Use `urllib.request` not `requests` on this VM. The shell `&` character in Trello URLs causes issues when running via `terminal()`. Write scripts to `/tmp/` and run them:

```python
import urllib.request, urllib.parse, json

KEY = "..."   # from ~/.hermes/.trello_credentials
TOKEN = "..."
BASE = "https://api.trello.com/1"

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

**Always write multi-step Trello scripts to `/tmp/trello_<task>.py` and run with `python3 /tmp/trello_<task>.py`** — avoids the shell `&` backgrounding conflict that occurs when using inline `-c` with `urllib`.

**Pitfall:** Trello POST/PUT needs **form-encoded** data (`urllib.parse.urlencode(data).encode()`), not JSON body. Sending `json=data` (requests-style) silently fails — credentials aren't recognised and you get 401.

## Common Operations

### Get all boards
```python
boards = trello_request('GET', '/members/me/boards?fields=name,shortUrl,id')
for board in boards:
    print(f"{board['name']}: {board['shortUrl']}")
```

### Get lists on a board
```python
board_id = 'N1PbdP9e'  # from URL
lists = trello_request('GET', f'/boards/{board_id}/lists')
```

### Get cards in a list
```python
list_id = '...'
cards = trello_request('GET', f'/lists/{list_id}/cards?fields=name,id,desc,shortUrl')
```

### Create a card
```python
new_card = trello_request('POST', '/cards', {
    'name': 'Card Title',
    'desc': 'Card description with details',
    'idList': list_id
})
```

### Update a card
```python
trello_request('PUT', f'/cards/{card_id}', {
    'desc': 'Updated description',
    'idList': new_list_id  # move to different list
})
```

### Move card to different list
```python
trello_request('PUT', f'/cards/{card_id}', {'idList': target_list_id})
```

### Add comment to card
```python
trello_request('POST', f'/cards/{card_id}/actions/comments', {
    'text': 'Comment text here'
})
```

### Archive a card
```python
trello_request('PUT', f'/cards/{card_id}', {'closed': True})
```

### Create a board
```python
board = trello_request('POST', '/boards/', {
    'name': 'New Board Name',
    'defaultLists': False,  # Don't auto-create To Do/Doing/Done
    'prefs_background': 'blue',
    'prefs_permissionLevel': 'private'
})
board_id = board['id']
board_url = board['shortUrl']
```

### Create a list
```python
new_list = trello_request('POST', '/lists', {
    'name': 'List Name',
    'idBoard': board_id,
    'pos': 'bottom'  # or 'top' or numeric position
})
```

## Bulk Operations Pattern

When doing multi-step Trello work (board restructure, bulk card moves, mass create), **always write to `/tmp/trello_<task>.py` and run as a script** — never inline with terminal `-c`. The `&` character in urllib URLs triggers shell backgrounding when used inline.

```python
# /tmp/trello_setup.py — write this file, then: python3 /tmp/trello_setup.py
import urllib.request, urllib.parse, json

KEY = "..."
TOKEN = "..."
BASE = "https://api.trello.com/1"

def trello_get(path, params={}):
    params['key'] = KEY
    params['token'] = TOKEN
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{BASE}{path}?{qs}", timeout=15) as r:
        return json.loads(r.read())

def trello_put(path, data={}):
    data['key'] = KEY
    data['token'] = TOKEN
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=encoded, method='PUT')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# Get all cards, build name→id map, then batch-update
cards = trello_get(f"/boards/{BOARD_ID}/cards")
card_map = {c['name']: c['id'] for c in cards}

for old_name, (list_id, new_name) in moves.items():
    if old_name in card_map:
        trello_put(f"/cards/{card_map[old_name]}", {'idList': list_id, 'name': new_name})
        print(f"Moved: {old_name} -> {new_name}")
```

## Board ID from URL

Trello URL format: `https://trello.com/b/BOARD_ID/board-name`

Example: `https://trello.com/b/N1PbdP9e/7-day-magazine-sprint-blair-shumon-taylor`
- Board ID: `N1PbdP9e`

## Error Handling

```python
try:
    result = trello_request('GET', '/boards/invalid_id')
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("Board not found")
    elif e.response.status_code == 401:
        print("Invalid credentials")
    else:
        print(f"Error: {e}")
```

## Permissions

- Token does **NOT** have board-admin permissions — member adds require manual web invite
- Credentials file must stay at `chmod 600`

## Board Restructuring Pattern (learned May 30, 2026)

When restructuring an existing board (rename lists, archive stale cards, move cards, create new cards in batch):

1. **Fetch card map first** — `{card['name']: card['id'] for card in cards}` — then iterate moves dict against it
2. **Archive before moving** — archive placeholder/old cards first so name conflicts don't confuse the map
3. **Rename lists with PUT** before creating new cards — list IDs stay stable across renames
4. **Write the whole operation to `/tmp/trello_setup.py`** — multi-step restructures always go to a script file, never inline
5. **Confirm with a final GET** after — fetch board lists+cards and print to verify state

## Known Trello Boards (verified May 2026)

| Board Name | URL | Board ID |
|---|---|---|
| 7-Day Magazine Sprint (Blair, Shumon, Taylor) | https://trello.com/b/U7StsSvp | `6a0e81483e169b28504ba8c1` |
| Magazine / Ebook Production | — | `68f54f1e83384f8868a3ed8a` |
| MAGPROD | — | `69fec363f83059e96e53e10f` |
| Admin & AI | — | `69b9d4f1a7a097483a4121c7` |
| Founders Kanban | — | `6990ed968580db07dd48f4d8` |
| TIMBR Go-Live Checklist | — | `69f8218432c9e44a9ae1abb7` |
| TIMBR SITE 3 | — | `6a07779cce2a64e87881908e` |
| TIMBR TO-DO | — | `69c5df3b602c38c64889bf09` |
| Webflow Build - Ultrahuman Clone | — | `6a0f54b9f10b76bfd99ea7a5` |

### Magazine Sprint board list IDs (as of May 29, 2026)
After restructuring this session, the lists are:
- `📋 TO DO` — `6a0e81499eade99efbbaa28c`
- `🔄 IN PROGRESS` — `6a0e814993006a98af881696`
- `👁️ IN REVIEW` — `6a0e8149409a6f9a8e3bf7ff`
- `🚀 LAUNCH PREP` — `6a0e81496392d9a63c836ce4`
- `✅ DONE` — `6a0e814aa49ecbff5b43677f`

## Tips

1. **Always use `defaultLists: False`** when creating boards to avoid auto-generated lists
2. **Load credentials once** at the start of a script, not per-request
3. **Use `shortUrl`** field for human-readable board/card links
4. **Card descriptions support Markdown** — use for formatting
5. **Position cards/lists** with `pos: 'top'`, `'bottom'`, or numeric value
6. **Bulk operations** — fetch all items first, then iterate to avoid rate limits

## Security Note

Never commit `~/.hermes/.trello_credentials` to version control. File permissions are set to 600 (owner read/write only).
