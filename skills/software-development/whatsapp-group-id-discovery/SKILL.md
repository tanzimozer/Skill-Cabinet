---
name: whatsapp-group-id-discovery
description: Identify the correct numeric WhatsApp group ID when the bridge only exposes bare IDs with no name lookup.
tags: [whatsapp, groups, bridge, hermes]
triggers:
  - Need to send a message to a specific WhatsApp group but only have numeric IDs
  - User asks Friday to message a group whose ID is not yet in memory
  - Bridge returns a list of group IDs with no names attached
---

# WhatsApp Group ID Discovery

## The Problem
The Hermes WhatsApp bridge (`send_message` list) returns groups as bare numeric IDs only — e.g. `whatsapp:120363411696218942 (group)`. The `send_message` tool itself has no name lookup — BUT the bridge's HTTP API does (see below).

## What Works BEST — the `/groups-all` endpoint (CONFIRMED 2026-06-21)

The bridge exposes `GET http://localhost:3000/groups-all` which returns **every joined group with its name (`subject`) AND id** in one call. This is the fast, reliable answer — no manual phone/invite-link dance needed. It just requires the Bearer token (the bridge now has auth middleware).

```python
import subprocess, os, json, urllib.request
tok = subprocess.run(['grep','WHATSAPP_BRIDGE_TOKEN', os.path.expanduser('~/.hermes/.env')],
                     capture_output=True, text=True).stdout.strip().split('=',1)[1]
req = urllib.request.Request("http://localhost:3000/groups-all",
                             headers={"Authorization": f"Bearer {tok}"})
data = json.load(urllib.request.urlopen(req, timeout=30))
groups = data if isinstance(data, list) else data.get("groups", data)
for g in groups:
    name = g.get("subject") or g.get("name") or ""
    gid  = g.get("id") or g.get("jid") or ""
    print(f"{name!r:45} {gid}")
```

Match the group name to its `@g.us` id, save it to memory, then send. This supersedes the manual options below — only fall back to them if `/groups-all` is unavailable.

## What Does NOT Work
- `curl http://localhost:3000/chats` — 404
- `curl http://localhost:3000/groupMetadata/{id}@g.us` — 404
- `curl http://localhost:3000/groupInviteInfo` — 404
- Sending test pings via `mcp_send_message` to each ID — bridge rejects with jidDecode error if the ID isn't a joined group in the correct format
- Resolving a WhatsApp invite link (e.g. `chat.whatsapp.com/xxx`) to an ID — bridge has no endpoint for this

## What Works

### Option 1 — WhatsApp Web URL (fastest)
1. Open WhatsApp Web (web.whatsapp.com) in browser — already logged in
2. Click the target group in the left sidebar
3. Click the group name at the top to open group info
4. The URL in the browser address bar will NOT change on web.whatsapp.com
5. Instead: right-click the group in the sidebar → "Copy link" or check group info panel for the invite link
6. **Better:** Ask Tanzim to open the group on his phone → tap group name → scroll down → "Invite to Group via Link" → copy and share that link
7. Cross-reference the invite link code against known groups by trial

### Option 2 — Check Memory First
Known group IDs are saved in memory. Check there before attempting discovery:
- Towsif's Desk: `120363411696218942@g.us`
- Blair's Fitness Profile: unknown as of 2026-05-04 — update when discovered

### Option 3 — Ask Tanzim to Check Phone
Simplest: ask Tanzim to open the group on WhatsApp → group info → invite link → paste here. The invite link contains a code that can be matched once the bridge supports it.

## Once Discovered
- Save the group ID immediately to memory under the group name
- Format: `GroupName group: {ID}@g.us`
- Send via curl: `curl -s -X POST http://localhost:3000/send -H 'Content-Type: application/json' -d '{"chatId": "{ID}@g.us", "message": "..."}'`

## Pitfalls
- `mcp_send_message` target format is `whatsapp:{ID}` (no @g.us) — bridge adds it internally
- curl send format requires `{ID}@g.us` explicitly
- WhatsApp Web URL does not update when switching groups — cannot read group ID from browser URL bar
