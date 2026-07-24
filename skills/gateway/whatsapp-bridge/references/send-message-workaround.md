# WhatsApp Bridge: send_message Failures — Direct API Workaround

## Problem
`send_message(target="whatsapp:120363...", message="...")` fails with:
```
WhatsApp bridge error (500): {"error":"Cannot destructure property 'user' of 'jidDecode(...)' as it is undefined."}
```

Typically happens with **group messages** when the abstraction layer mishandles JID parsing.

## Root cause
The `send_message` tool passes through a messaging gateway layer that may not correctly format group JIDs for the underlying bridge API.

## Workaround: Direct bridge HTTP call

Bypass `send_message` and call the bridge's `/send` endpoint directly via `curl`.

## ⚠️ Bearer Token Auth — Required

The bridge enforces Bearer token auth on all state-changing endpoints (including `/send`).  
Without it you get `{"error":"Unauthorized"}` (HTTP 401).

> **Common wrong-header pitfall**: `X-Bridge-Secret` is the *gateway webhook* secret (port 8644, not 3000). Sending it to the bridge gives a 401. The bridge only accepts `Authorization: Bearer <token>`. Confirmed failure mode: 2026-06-01 cron job.

```bash
# Retrieve token from env
BRIDGE_TOKEN=$(grep 'WHATSAPP_BRIDGE_TOKEN' ~/.hermes/.env | cut -d= -f2)
```

Then pass `-H "Authorization: Bearer $BRIDGE_TOKEN"` on every curl call.  
`/health` is the only endpoint that is always unauthenticated.

> The token is set via `WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`. If the var is absent or empty, the bridge fails open (dev mode) — but on the production VM it is always set.

---

### Simple messages (no special characters)
```bash
BRIDGE_TOKEN=$(grep 'WHATSAPP_BRIDGE_TOKEN' ~/.hermes/.env | cut -d= -f2)
curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId":"120363427373827049@g.us","message":"Your message text here"}'
```

### Messages with apostrophes, quotes, emoji, or newlines — USE THIS

> ⚠️ Inline `-d '{"message": "What's up?"}'` causes shell quoting failures (`unexpected EOF`) when the message contains `'`, `"`, emoji, or `\n`. **Always use a temp file for anything non-trivial.**

```bash
BRIDGE_TOKEN=$(grep 'WHATSAPP_BRIDGE_TOKEN' ~/.hermes/.env | cut -d= -f2)
cat > /tmp/msg.json << 'ENDJSON'
{
  "chatId": "120363427373827049@g.us",
  "message": "Hey there 👋\n\nWhat's your thought on this?"
}
ENDJSON
curl -s -X POST http://localhost:3000/send \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d @/tmp/msg.json
```

**Success response**:
```json
{"success":true,"messageId":"3EB0EA5901B1003952CD20","messageIds":["3EB0EA5901B1003952CD20"]}
```

### Key details
- **Endpoint**: `/send` (not `/message`)
- **Payload**: `chatId` (not `jid` or `target`) + `message`
- **Group format**: `<numeric-id>@g.us`
- **DM format**: `<phone>@s.whatsapp.net` or `<id>@lid` for linked devices

## When to use
- `send_message` returns 500 with JID decode errors
- Sending to WhatsApp groups specifically
- Bridge is confirmed running (`pgrep -f whatsapp-bridge` shows PIDs)
- Any cron job that sends messages (can't interactively recover from a tool failure)

## Verification
After sending, check bridge logs for success:
```bash
tail -5 ~/.hermes/whatsapp/bridge.log
```

## Related endpoints
- `/send-media` — Send images/files
- `/edit` — Edit previously sent messages
- `/typing` — Send typing indicator

## Reading group message history
**`sqlite3` is not installed** on this VM. `better-sqlite3` Node module is also not accessible via direct `node -e` eval.

Reliable options to check what was sent/received in a group:
1. **`session_search`** — search past cron/session records by chat ID or keyword. Best for "did I already send Q10?" type checks.
2. **Bridge log** — `tail ~/.hermes/whatsapp/bridge.log` shows recent outbound `msgId` entries.

## Related
- Bridge listens on `localhost:3000` (default)
- Logs: `~/.hermes/whatsapp/bridge.log`
- Restart: **never `pkill` the bridge directly** — restart the parent gateway: `systemctl --user stop hermes-gateway && sleep 5 && systemctl --user start hermes-gateway`
