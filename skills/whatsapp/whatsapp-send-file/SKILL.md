---
name: whatsapp-send-file
description: Send a file (PDF, PNG, DOCX, any format) as a native WhatsApp attachment to Tanzim or any chat. Uses the /send-media endpoint on the local WhatsApp bridge at port 3000.
category: whatsapp
tags: [whatsapp, file, pdf, media, attachment, send]
---

# WhatsApp File Sending — Native Attachment

## The One Right Method

```bash
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "CHAT_ID",
    "filePath": "/absolute/path/to/file.pdf",
    "mediaType": "document",
    "fileName": "display_name.pdf",
    "caption": "Optional caption text"
  }'
```

## Chat IDs
- Tanzim DM: `160799431606497@lid`
- Groups: `XXXXXXXXXXXXXXXXX@g.us`

## mediaType values
- `"document"` — PDF, DOCX, any non-image file (shows as downloadable attachment)
- `"image"` — PNG, JPG (shows inline as photo)
- `"video"` — MP4

## What DOES NOT work (learned the hard way)
| Method | What happens | Why it fails |
|--------|-------------|--------------|
| `send_message` with `file:///path` | Sends literal text string | send_message is text-only |
| `send_message` with `file:///path` as message | Renders as plain text in chat | Bridge doesn't interpret file:// URIs |
| Google Drive links | Sends a URL, not a file | User has to open browser, not native |
| Any text-based workaround | Never an attachment | Bridge doesn't parse file paths from text |

## What WORKS
The `/send-media` endpoint on the bridge (port 3000) uses Baileys under the hood to upload the file directly to WhatsApp servers and deliver it as a native attachment — exactly how any user would send a file from their phone. Tested and confirmed working May 27, 2026.

## Full Example — Send PDF + PNG + DOCX together
```bash
# PDF
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/Linked_Engine/output/LE004/file.pdf","mediaType":"document","fileName":"article.pdf","caption":"PDF"}'

# PNG
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/Linked_Engine/output/LE004/file.png","mediaType":"image","caption":"PNG"}'

# DOCX
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/Linked_Engine/output/LE004/file.docx","mediaType":"document","fileName":"caption.docx","caption":"Caption"}'
```

## Success response
```json
{"success":true,"messageId":"3EB0..."}
```

## Bridge location
```
node /home/hermes/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js --port 3000
```

## How this was discovered (May 27, 2026)
Tanzim showed a screenshot of Waseem's agent (Kaito) dropping a PDF natively into a group chat. Inspected bridge.js source, found `/send-media` endpoint documented in the file header comments. Tested with curl — worked immediately. The `send_message` tool and `file://` URIs had been tried multiple times before and consistently failed.
