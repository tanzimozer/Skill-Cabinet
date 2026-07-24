---
name: whatsapp-media-delivery
category: messaging
description: Sending images and media files to WhatsApp via the Hermes Baileys bridge
triggers:
  - send image to whatsapp
  - send png to whatsapp
  - send file via whatsapp bridge
  - whatsapp media delivery
  - image not sending to whatsapp
---

# WhatsApp Media Delivery

## Critical: Use `/send-media`, NOT `/send`

The bridge exposes two endpoints:
- `/send` — text only (`chatId` + `message` required). Images will fail with "chatId and message are required".
- `/send-media` — images, video, audio. Use this for any file.

## Auth

Token lives in `/home/hermes/.hermes/.env` as `WHATSAPP_BRIDGE_TOKEN`.
Bridge runs on **port 3000** (not 3822 — that's a dead port).
Always include `Authorization: Bearer <token>` header.

## Working curl pattern

```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"chatId\": \"<JID>\",
    \"filePath\": \"/absolute/path/to/file.png\",
    \"mediaType\": \"image\",
    \"caption\": \"\"
  }"
```

Success response: `{"success":true,"messageId":"..."}`.

## Owner JID

Tanzim's WhatsApp JID: `160799431606497@lid`  
Config also at `whatsapp.owner_chat_id` in `~/.hermes/config.yaml`.

## send_message tool

The `send_message` tool with `image::/path/to/file.png` returns **401 Unauthorized** for WhatsApp — the tool routes image paths through `/send` with no auth header that the bridge accepts. Do NOT retry it; it will always fail. For WhatsApp images, always use the direct bridge curl call above.

Note: the error `{"error":"Unauthorized"}` here means **wrong endpoint**, not expired session. The bridge session itself is usually fine — the `/send` route simply rejects non-text payloads.

## Bridge health check

```bash
curl -s http://localhost:3000/health
# Expected: {"status":"connected","queueLength":0,"uptime":...}
```

## Pitfalls

- Using `/send` with an image path → always fails ("chatId and message are required")
- Using port 3822 or **port 19080** → connection refused (wrong port; bridge is on 3000)
- Missing `Authorization` header → 401 Unauthorized
- **Multipart form (`-F` flags) does NOT work** — bridge `/send-media` expects JSON body, not `multipart/form-data`. Using `-F "session_id=..." -F "media=@file"` will 404 or fail silently. Always use `-H "Content-Type: application/json"` with `-d '{...}'`.
- **`session_id` is not a valid field** — correct field name is `chatId` (WhatsApp JID). Wrong field name returns 400.
- Subagent with `messaging` toolset cannot send WA images — it will try `send_message` and fail. Do it directly in the parent agent via terminal curl.

## Fastest debug path when delivery fails

1. Check port: `ss -tlnp | grep node` → should show 3000
2. Health check: `curl -s http://localhost:3000/health`
3. Confirm token: `grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env`
4. Confirm file exists: `ls -lh /path/to/file.png`
5. Run the working curl pattern above verbatim — don't adapt it until it works once.
