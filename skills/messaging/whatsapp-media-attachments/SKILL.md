---
name: whatsapp-media-attachments
description: "Sending files and media via WhatsApp — capabilities, limitations, and workarounds"
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [whatsapp, media, attachments, pdf, files, documents]
    related_skills: []
---

# WhatsApp Media & File Attachments

## The Problem

WhatsApp bridge has `send_document`, `send_image`, `send_video`, `send_voice` methods (see `gateway/platforms/whatsapp.py` lines 1011-1071), BUT the `send_message` tool doesn't route `MEDIA:` tags to these methods for WhatsApp.

**Platforms with native MEDIA: tag support:** Telegram, Discord, Matrix, Weixin, Signal, Yuanbao, Feishu
**Platforms WITHOUT native MEDIA: tag support:** WhatsApp (as of May 2026)

## What Happens

```
send_message with "MEDIA:/path/to/file.pdf" to WhatsApp
→ Returns success BUT with warning:
   "MEDIA attachments were omitted for whatsapp; native send_message 
    media delivery is currently only supported for telegram, discord, 
    matrix, weixin, signal, yuanbao and feishu"
```

The text arrives, the file does not.

## Workarounds (in preference order)

### 0. BEST — POST directly to the bridge `/send-media` endpoint (CONFIRMED 2026-06-21)

The `send_message` tool won't route media to WhatsApp, but the **bridge endpoint it would have called works directly** and delivers the file natively (real image/document bubble, no external link). Skip the file-host dance entirely — call `/send-media` yourself with a local `filePath`:

```python
import subprocess, os, json, urllib.request
tok = subprocess.run(['grep','WHATSAPP_BRIDGE_TOKEN', os.path.expanduser('~/.hermes/.env')],
                     capture_output=True, text=True).stdout.strip().split('=',1)[1]
payload = {"chatId": "120363411696218942@g.us",   # group; for a DM use the lid: "160799431606497@lid"
           "filePath": "/tmp/proof.png",
           "mediaType": "image",                   # image | video | audio | document
           "caption": "..."}
req = urllib.request.Request("http://localhost:3000/send-media",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        method="POST")
print(urllib.request.urlopen(req, timeout=60).read().decode())   # {"success":true,...}
```

Required body fields: `chatId`, `filePath` (must exist on the bridge host). Optional: `mediaType` (inferred from extension if omitted), `caption`, `fileName`. Audio auto-converts to ogg/opus for a native voice bubble. This is the first thing to try — only fall back to the link-based workarounds below if the bridge is unreachable.

### 1. Upload to file host, send link
```bash
# Catbox (anonymous, no expiry)
curl -F "reqtype=fileupload" -F "fileToUpload=@/path/to/file.pdf" https://catbox.moe/user/api.php
# Returns: https://files.catbox.moe/<hash>.pdf

# Then send the URL via send_message
```

### 2. Google Drive upload + share link
Upload to user's Drive, set sharing, send link.

### 3. Email the file
If Gmail is configured and token is valid, attach and send.

## File Hosting Services Status (as of May 2026)

| Service | Status | Notes |
|---------|--------|-------|
| catbox.moe | ✅ Working | Anonymous, no expiry, 200MB limit |
| transfer.sh | ❌ Redirects | Returns 301 |
| 0x0.st | ❌ Disabled | "AI botnet spam" block |
| file.io | ⚠️ Unreliable | Sometimes works |

## Technical Details

The capability exists in the codebase:
- `whatsapp.py:_send_media_to_bridge()` — sends to bridge `/send-media` endpoint
- `whatsapp.py:send_document()` — wraps `_send_media_to_bridge` with `mediaType: "document"`
- Bridge accepts: `chatId`, `filePath`, `mediaType`, `caption`, `fileName`

The gap is in `send_message_tool.py` — the `media_files` extraction and dispatch only covers certain platforms.

## Future Fix

When WhatsApp support is added to `send_message` media routing, this workaround becomes unnecessary. Check the warning message — if it no longer mentions WhatsApp in the unsupported list, try `MEDIA:` tags directly.
