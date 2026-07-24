---
name: drop-pdf
description: "Build a PDF from any content (markdown, research, reports) and drop it directly into the active chat via WhatsApp bridge — no Drive links, no workarounds."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [pdf, whatsapp, file-drop, document, report]
    related_skills: [whatsapp-group-file-drop, send-file-to-chat]
---

# Drop PDF

Generate a PDF from content and deliver it as a native WhatsApp attachment to the active conversation. One skill, end to end.

## Trigger Phrases

User says any of:
- "convert and drop as PDF"
- "make a PDF and send it here"
- "build a PDF and drop it"
- "drop the PDF here"
- "send it as PDF"

## Pipeline

```
Content (markdown/text) → PDF (pandoc + weasyprint) → /send-media → WhatsApp attachment
```

## Step 1 — Generate the PDF

```bash
pandoc /tmp/<filename>.md \
  -o /tmp/<filename>.pdf \
  --pdf-engine=weasyprint \
  --metadata title="<Document Title>"
```

Supported input: markdown, plain text, HTML.  
Output: `/tmp/<filename>.pdf`

## Step 2 — Send via Bridge

```python
import requests
import os

def drop_pdf(file_path: str, chat_id: str, display_name: str = None, caption: str = None):
    """
    Send a PDF to any WhatsApp chat via the bridge /send-media endpoint.
    
    Args:
        file_path:    Absolute path to the PDF
        chat_id:      WhatsApp chatId (DM or group)
        display_name: Filename shown in chat (defaults to basename)
        caption:      Optional caption text
    """
    bridge_url = "http://127.0.0.1:3000"
    token = os.environ.get("WHATSAPP_BRIDGE_TOKEN") or open(os.path.expanduser("~/.hermes/.env")).read().split("WHATSAPP_BRIDGE_TOKEN=")[-1].split()[0]

    payload = {
        "chatId": chat_id,
        "filePath": os.path.abspath(file_path),
        "mediaType": "document",
        "fileName": display_name or os.path.basename(file_path)
    }

    if caption:
        payload["caption"] = caption

    resp = requests.post(
        f"{bridge_url}/send-media",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    return resp.json()
```

## Chat ID Reference

| Context | Chat ID |
|---------|---------|
| Tanzim DM (default) | `160799431606497@lid` |
| TIMBR APP - PRD | `120363427118724513@g.us` |
| TIMBR-3 | `120363427031872209@g.us` |
| Blair's Fitness Profile | `120363427373827049@g.us` |
| Blair's Magazine | `120363429573679291@g.us` |

**Default**: always send to the chat where the request came from. Tanzim's DM = `160799431606497@lid`.

## Full Bash One-Liner (DM drop)

```bash
CHAT_ID="160799431606497@lid"
FILE="/tmp/report.pdf"
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)

pandoc /tmp/report.md -o $FILE --pdf-engine=weasyprint --metadata title="Report" && \
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"chatId\":\"$CHAT_ID\",\"filePath\":\"$FILE\",\"mediaType\":\"document\",\"fileName\":\"report.pdf\"}"
```

## Error Handling

| Error | Fix |
|-------|-----|
| `pandoc: command not found` | `apt install pandoc` |
| `weasyprint not found` | `pip install weasyprint` |
| `401 Unauthorized` | Check `~/.hermes/.env` for `WHATSAPP_BRIDGE_TOKEN` |
| `Connection refused` | Bridge not running — check `ps aux | grep bridge` |
| File not found on send | Always use **absolute** path |

## Rules

- **Never** use Drive links as a substitute. The file must land as a native WhatsApp document attachment.
- **Never** send to the wrong chat. Default = wherever Tanzim triggered the request.
- If bridge is genuinely down (401/refused), say so plainly. Don't silently fall back to Drive.
- After successful drop, confirm inline in the same chat: one line, no drama.
