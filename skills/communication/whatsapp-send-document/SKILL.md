---
name: whatsapp-send-document
description: "Send PDF/document files directly to WhatsApp chats via the bridge API"
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [whatsapp, document, pdf, file, attachment, media]
    related_skills: [private-message]
---

# WhatsApp Document Sending

## Problem
The `send_message` tool doesn't route `MEDIA:` tags to WhatsApp — only Telegram, Discord, Matrix, Weixin, Signal, Yuanbao, and Feishu get native media delivery.

However, the WhatsApp bridge **does** support document sending via its `/send-media` endpoint.

## Solution
Call the bridge directly via curl:

```bash
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "<CHAT_ID>",
    "filePath": "/absolute/path/to/file.pdf",
    "mediaType": "document",
    "fileName": "display_name.pdf"
  }'
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `chatId` | WhatsApp chat ID (e.g., `160799431606497@lid` for DM, `120363...@g.us` for group) |
| `filePath` | **Absolute** path to the file on disk |
| `mediaType` | `document` for PDFs/files, `image` for images, `video` for videos, `audio` for audio |
| `fileName` | Display name shown in WhatsApp (optional but recommended) |
| `caption` | Optional caption text |

## Finding the Bridge Port
```bash
ps aux | grep whatsapp-bridge | grep -v grep
# Look for --port flag, typically 3000
```

## Supported Media Types
- `document` — PDFs, ZIPs, DOCXs, etc. (downloads as file)
- `image` — JPG, PNG, GIF, WEBP (displays inline)
- `video` — MP4, MOV (plays inline)
- `audio` — OGG, MP3, M4A (plays as audio message)

## Example: Send PDF to Owner
```bash
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "160799431606497@lid",
    "filePath": "/home/hermes/report.pdf",
    "mediaType": "document",
    "fileName": "report.pdf"
  }'
```

## Response
```json
{"success": true, "messageId": "3EB02063C76384408D6DF3"}
```

## Why This Works
The WhatsApp adapter in `gateway/platforms/whatsapp.py` has `send_document()` which calls `_send_media_to_bridge()`. The bridge exposes `/send-media` endpoint. The gap is only that `send_message` tool doesn't auto-route `MEDIA:` tags for WhatsApp yet.

## Sending Text Messages to Groups (Workaround)
The `send_message` tool with `whatsapp:groupid` format can fail with bridge errors. Direct curl to `/send` works:

```bash
curl -s http://127.0.0.1:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <BRIDGE_TOKEN>" \
  -d '{
    "chatId": "120363429573679291@g.us",
    "message": "Your message here"
  }'
```

**Key:** Use `@g.us` suffix for groups, `@lid` for DMs. The parameter is `message`, not `text`.

## Auth Header Required
The bridge requires `Authorization: Bearer <token>` on all endpoints. The token is `WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`. The `send_message` tool may omit this, causing 401. Always use direct curl with the token when the tool fails.

```python
# Python equivalent (preferred for large files / complex payloads)
import requests
TOKEN = "<WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>"
requests.post("http://localhost:3000/send-media",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"chatId": CHAT_ID, "filePath": "/abs/path/to/file", "caption": "..."},
    timeout=30)
```

## Body Size Limit
Default express.json() limit is ~100KB — too small for images/HTML. **Already patched** to `express.json({ limit: '50mb' })` in bridge.js ~line 461. If a future session hits 413 PayloadTooLarge again, re-apply this patch and restart the bridge.

## Finding Groups by Name
When user says "drop it in [group name]" — look up the chat ID first:
```python
resp = requests.get("http://localhost:3000/groups-all",
    headers={"Authorization": f"Bearer {TOKEN}"})
groups = resp.json()
for g in groups:
    if "timbr" in g.get("subject","").lower():
        print(g["id"], g["subject"])
```
No `/chats` endpoint exists — only `/groups-all` for groups, `/chat/:id` for a specific chat.

**Known group IDs (Tanzim):**
- `120363427118724513@g.us` — TIMBR APP - PRD
- `120363427031872209@g.us` — TIMBR-3
- `120363427373827049@g.us` — Blair's Fitness Profile
- `120363429573679291@g.us` — Blair's Magazine

## Generating Presentation Images
See `references/image-generation-for-whatsapp.md` for the full HTML→Playwright→PNG pipeline and Tanzim's Apple-style design system.

## Screenshots of HTML Mockups
When user says "drop screenshots in the group":
1. Render HTML with `chromium-browser --headless --screenshot=/path/out.png --window-size=WxH --no-sandbox "http://localhost:PORT/file.html"`
2. Crop into sections if >150KB using PIL (`img.crop((x,y,w,h)).save(...)`)
3. Send each section via `/send-media` with `filePath` (NOT base64 — too large for JSON body)
4. `filePath` must be absolute path readable by the bridge process

## The Failure Pattern (confirmed June 2, 2026 — happened twice in same session)

**Tanzim explicitly stated: "I want the actual file dropped in chat. Not a Drive link. Not a URL."**

The repeating failure sequence:
1. Try `send_message` with `file:///path` → delivers plain text string ❌
2. Upload to Drive → send share link → Tanzim rejects it, asks again ❌
3. Use `/send-media` endpoint → delivers native file attachment ✅

**There is no scenario where a Google Drive link is acceptable as a substitute for a file attachment in WhatsApp.** Skip straight to step 3 every single time.

This applies to: HTML, PDF, DOCX, MD, TXT — any file type.
When user asks to "drop the PDF here" or "send the file" via WhatsApp, **use this skill immediately** — don't attempt `send_message` with `file://` paths first. The `send_message` tool will appear to succeed (returns a message ID) but delivers nothing — the `file://` URI is sent as a literal text string.

**Also confirmed wrong:** Google Drive links. Tanzim explicitly rejected Drive links as a fallback — he wants the actual file in chat, not a URL. No Google Drive workarounds.

**The failure pattern to avoid:**
1. Try `send_message` with `file:///path` → appears to succeed, delivers plain text ❌
2. Try Google Drive upload + share link → Tanzim rejects, asks again ❌  
3. Use `/send-media` endpoint → delivers native attachment ✅

Skip straight to step 3. Every time.

**This mistake has happened multiple times in the same session.** If you find yourself about to upload to Drive and send a link — stop. That is never the answer for WhatsApp file delivery. See also: `whatsapp-group-file-drop` skill for the group-specific version of this.
