---
name: whatsapp-bridge-ops
category: operations
description: Sending text and media via the Hermes WhatsApp bridge — direct HTTP patterns, auth, troubleshooting. Use when send_message fails or when sending images/files.
---

# WhatsApp Bridge Ops

Class-level skill for sending messages and media through the Hermes WhatsApp bridge directly, bypassing the `send_message` tool when it fails.

## When to use this instead of send_message
- `send_message` returns 401 Unauthorized
- Need to send an image, video, audio, or file (binary media)
- Need reliable delivery with explicit token auth

## Auth — always required
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
```
All curl calls need: `-H "Authorization: Bearer $BRIDGE_TOKEN"`

## Send text
```bash
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId": "160799431606497@lid", "message": "your text here"}'
```

## Send image / file — use /send-media, NOT /send
```bash
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId": "160799431606497@lid", "filePath": "/absolute/path/file.png", "mediaType": "image", "caption": "optional"}'
```

**Why not /send for images:** `/send` requires `chatId` + `message` (text only). Sending base64 or form-data to `/send` always returns `{"error":"chatId and message are required"}`. Use `/send-media` for ALL binary files.

### /send-media fields
| Field | Required | Notes |
|---|---|---|
| chatId | yes | LID format e.g. `160799431606497@lid` |
| filePath | yes | Absolute path on VM; must be readable by hermes user |
| mediaType | yes | "image" / "video" / "audio" / "document" |
| caption | no | String shown below the media |
| fileName | no | Override display name for documents |

## Bridge health check
```bash
curl -s http://localhost:3000/health
# {"status":"connected","queueLength":0,"uptime":...}
```
If not "connected" — bridge is reconnecting, wait 3–5s and retry.

## Key IDs
- Tanzim personal DM: `160799431606497@lid`

## Auth token location
Token is at `~/.hermes/.env` (NOT `~/.env` — that path doesn't exist). Correct pull:
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
```

## Common errors
| Error | Cause | Fix |
|---|---|---|
| 401 Unauthorized | Missing/wrong token | Pull token from `~/.hermes/.env` (not `~/.env`) and pass as Bearer header |
| "chatId and message are required" | Using /send for media | Switch to /send-media |
| Bridge not responding | Gateway restarting | Check `systemctl --user status hermes-gateway`, wait for reconnect |

## Restarting the gateway (model change, config update)
Restarting via `systemctl --user restart hermes-gateway` kills the current session mid-command — always times out from inside. This is expected. The restart still happens; you come back online on the next message. Do NOT attempt to confirm the restart from within the same session.

## Model config layer precedence
`~/.hermes/config.yaml` is read top-to-bottom — a later `model:` key at the bottom of the file overrides the one at the top. The base default at line 1 (`claude-sonnet-4-6`) can be silently overridden by an appended block further down. To check what model is actually running:
```bash
grep -n "^model:\|model: claude" ~/.hermes/config.yaml
```
The LAST matching entry wins. Check `tail -50` of config.yaml for any appended overrides before assuming the base default is active.
