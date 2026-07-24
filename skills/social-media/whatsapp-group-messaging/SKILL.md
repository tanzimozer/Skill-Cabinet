---
name: whatsapp-group-messaging
description: "Send messages to WhatsApp groups via the Hermes bridge using curl (workaround for mcp_send_message bug)."
tags: [whatsapp, groups, messaging, bridge, hermes]
triggers:
  - Need to send a message to a WhatsApp group
  - mcp_send_message fails with jidDecode error for groups
  - User asks to ping someone in a WhatsApp group
  - User asks to notify a group chat
---

# WhatsApp Group Messaging

## The Problem

`mcp_send_message` with target `whatsapp:{group_id}` fails for groups with:
```
Error: Cannot destructure property 'user' of 'jidDecode(...)' as it is undefined
```

The bridge's mcp_send_message handler doesn't properly append `@g.us` suffix for group chats.

## The Workaround

**Option 1: Use `send_message` with `@g.us` suffix** (simplest):

```python
send_message(
    target="whatsapp:120363411696218942@g.us",
    message="Your message here"
)
```

**Option 2: Use `curl`/HTTP directly** (fallback if Option 1 fails):

```bash
TOK=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send \
  -H "Authorization: Bearer $TOK" \
  -H 'Content-Type: application/json' \
  -d '{
    "chatId": "GROUP_ID@g.us",
    "message": "Your message here"
  }'
```

Both require the `@g.us` suffix. Without it, you get the jidDecode error.

⚠️ **Bearer token now REQUIRED on all bridge calls (added Jun 2026).** The bridge added
token middleware — every endpoint (`/send`, `/groups-all`, etc.) returns
`{"error":"Unauthorized"}` (HTTP 401) without it. Token lives at
`WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`. Header: `Authorization: Bearer <token>`.
The field is **`chatId`, not `to`** — wrong field name returns HTTP 400 Bad Request.

## ID Formats

| Type | Format | Example |
|------|--------|---------|
| Group | `{numeric_id}@g.us` | `120363411696218942@g.us` |
| DM | `{phone}@s.whatsapp.net` | `14255203988@s.whatsapp.net` |

## Known Group IDs

| Group Name | ID |
|------------|-----|
| Towsif's Desk | `120363411696218942@g.us` |
| Learn AI (Tahmeed) | `120363425196031209@g.us` |
| Blair's Fitness Profile | `120363427373827049@g.us` |

*(Add more as discovered — save to memory)*

## Step-by-Step: Send to a Group

1. **Get the group ID** — check memory or use `mcp_send_message(action='list')` to see available groups
2. **Append `@g.us`** to the numeric ID
3. **Send via curl:**

```bash
curl -s -X POST http://localhost:3000/send \
  -H 'Content-Type: application/json' \
  -d '{
    "chatId": "120363411696218942@g.us",
    "message": "Hey team! 👋\n\nYour message here."
  }'
```

4. **Check response:**
   - Success: `{"success":true,"messageId":"3EB0..."}`
   - Failure: `{"error":"item-not-found"}` (group not joined or invalid ID)

## Discovering Unknown Group IDs

The `send_message(action='list')` output shows groups as numeric IDs **with no names** — so
you can't pick a named group ("Towsif's Desk") from that list alone. Resolve name → ID directly
via the bridge's `/groups-all` endpoint (returns every group's `subject` + `id`):

```python
import subprocess, os, json, urllib.request
tok = subprocess.run(['grep','WHATSAPP_BRIDGE_TOKEN',os.path.expanduser('~/.hermes/.env')],
                     capture_output=True, text=True).stdout.strip().split('=',1)[1]
req = urllib.request.Request("http://localhost:3000/groups-all",
                             headers={"Authorization": f"Bearer {tok}"})
data = json.load(urllib.request.urlopen(req, timeout=30))
groups = data if isinstance(data, list) else data.get("groups", data)
for g in groups:
    print(g.get("subject"), g.get("id"))   # name -> id, grep for the one you want
```

Then POST to `/send` with that `chatId`. **No need to ask the user for an invite link or to
tag you in-thread** — `/groups-all` resolves any named group you're a member of. (Curl
equivalent: `curl -s -H "Authorization: Bearer $TOK" http://localhost:3000/groups-all`.)

Fallback only if `/groups-all` is unavailable: ask the user to share the group's invite link.
Once discovered, save the ID to the table below / memory.

## Checking Bridge Health

```bash
curl -s http://localhost:3000/health
```

Returns: `{"status":"connected","queueLength":0,"uptime":...}`

## Pitfalls

- **Always include `@g.us` suffix** — bare numeric ID triggers jidDecode error
- **Try `send_message` first** (with @g.us), fallback to curl if it fails
- **`item-not-found` error** means the group doesn't exist or the bridge account isn't a member
- **Newlines in messages** — use `\\n` in the JSON string
- **Emojis** — work fine in curl JSON
- **Long messages** — no known limit, but keep reasonable
- **@number tags render as raw numbers** — never use @phoneNumber or @whatsappID as a mention in group messages. It shows the raw digits to the recipient, not their name. Just use their plain name.
- **Backend confirmations must never go to the group** — "Sent.", "Done.", "Message delivered." belong in the DM reply to Tanzim or stay silent. Only Tahmeed-directed content goes to the Learn AI group.
- **Drive to completion** — when Tanzim assigns a task in a group (teach Tahmeed, test him, etc.), own it end-to-end. Anticipate the next step and execute it without waiting to be told. Don't park after sending one message. Send → watch → respond → gate → next task. Stop only when the job is done or Tanzim redirects.

## When mcp_send_message DOES Work

- DMs to saved contacts work fine: `mcp_send_message(target='whatsapp:ContactName', message='...')`
- Sending to the default/home chat works

## Backend Hygiene — CRITICAL

- **Never send backend confirmations ("Sent.", "Done.", "Message delivered.") to the group** — those go to Tanzim's DM or stay silent. Only Tahmeed-directed content goes to the Learn AI group.

## Memory Hygiene for Group Participants

When managing ongoing sessions with a named participant (e.g. Tahmeed):
- **Use Hindsight, not memory** — the memory tool is capped at 6,000 chars. Per-person profiles, curriculum state, and session progress belong in Hindsight (`hindsight_retain`), not memory entries.
- **Consolidate, don't duplicate** — before storing new facts about a person, check what's already in Hindsight. Update the master entry rather than adding a new one. Duplicate entries cause recall noise.
- **One master profile entry per person** — keyed clearly (e.g. "Tahmeed — Master Profile"). Tag it so it surfaces cleanly.

## Teaching Sessions via Group (Tahmeed / Learn AI)

For structured learning sessions delivered over WhatsApp group, see:
`references/tahmeed-learn-ai-session-protocol.md`

Key pattern: one task at a time → gate on confirmation → test knowledge → next task. Drive end-to-end without waiting for Tanzim to prompt each step.

## What the Bridge CANNOT Do

The WhatsApp bridge is **send-only** for groups. You CANNOT:
- Fetch historical messages from a group
- Search past conversations
- Read the message backlog

The `/messages` endpoint only returns NEW incoming messages (real-time polling queue).
The `/chat/:id` endpoint returns basic info (name, isGroup) but participants array is empty.

**Workarounds if you need info from a group:**
- Ask the user to forward specific messages
- Ask user to screenshot (you can analyze with vision)
- Ask the user directly what info they need

## Example: Notify Towsif in Group

```bash
curl -s -X POST http://localhost:3000/send \
  -H 'Content-Type: application/json' \
  -d '{
    "chatId": "120363411696218942@g.us",
    "message": "Hey Towsif 👋\n\nNew task assigned to you:\nhttps://trello.com/b/xxx\n\nCheck the board when you get a chance."
  }'
```
