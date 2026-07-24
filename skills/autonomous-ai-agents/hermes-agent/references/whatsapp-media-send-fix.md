# WhatsApp Bridge — Media Send Fix (July 2026)

## Problem
`send_message` tool throws `401 Unauthorized` when sending images/media.

## Root Cause
The `send_message` tool does not pass the bridge auth token. The bridge itself is healthy — `GET /health` returns `{"status":"connected"}`.

## Fix — Send media directly via curl
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)

# Send image
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d "{\"chatId\": \"<CHAT_ID>\", \"filePath\": \"<ABSOLUTE_PATH_TO_FILE>\", \"mediaType\": \"image\", \"caption\": \"<CAPTION>\"}"

# Send text
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d "{\"chatId\": \"<CHAT_ID>\", \"message\": \"<TEXT>\"}"
```

## Tanzim's chat ID
`160799431606497@lid`

## Key endpoint notes
- `/send` requires `chatId` + `message` fields (NOT `text`)
- `/send-media` requires `chatId` + `filePath` + `mediaType` + optional `caption`
- Auth header: `Authorization: Bearer <token>` — must be present on every request
- Bridge token is in `~/.hermes/.env` as `WHATSAPP_BRIDGE_TOKEN`

## Diagnosis commands
```bash
# Check bridge health
curl -s http://localhost:3000/health

# Check bridge logs
cat ~/.hermes/whatsapp/bridge.log | tail -30
```
