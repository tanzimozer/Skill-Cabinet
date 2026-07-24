---
name: whatsapp-group-file-drop
description: "Drop any file (HTML, DOCX, PDF, MD, TXT, etc.) into WhatsApp group chats"
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [whatsapp, file, group, document, html, pdf, drop]
    related_skills: [whatsapp-send-document, private-message]
---

# WhatsApp Group File Drop

Drop any file type into any WhatsApp group chat via the bridge `/send-media` endpoint.

## Quick Command

```bash
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $WHATSAPP_BRIDGE_TOKEN" \
  -d '{
    "chatId": "<GROUP_ID>",
    "filePath": "/absolute/path/to/file",
    "mediaType": "document",
    "fileName": "display_name.ext"
  }'
```

## Known Group IDs

| Group Name | Chat ID |
|------------|---------|
| TIMBR APP - PRD | `120363427118724513@g.us` |
| TIMBR-3 | `120363427031872209@g.us` |
| Blair's Fitness Profile | `120363427373827049@g.us` |
| Blair's Magazine | `120363429573679291@g.us` |

## Supported File Types

| Extension | mediaType | Notes |
|-----------|-----------|-------|
| `.html` | `document` | Downloads as file, open in browser |
| `.pdf` | `document` | Native PDF viewer |
| `.docx` | `document` | Downloads for Word/Docs |
| `.md` | `document` | Raw markdown file |
| `.txt` | `document` | Plain text |
| `.png/.jpg` | `image` | Displays inline |
| `.mp4` | `video` | Plays inline |

## Python Function

```python
import requests

BRIDGE_TOKEN = "<WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>"
BRIDGE_URL = "http://127.0.0.1:3000"

def drop_file_to_group(file_path: str, group_id: str, display_name: str = None, caption: str = None):
    """
    Drop any file into a WhatsApp group.
    
    Args:
        file_path: Absolute path to the file
        group_id: WhatsApp group ID (e.g., '120363427118724513@g.us')
        display_name: Optional filename shown in chat (defaults to basename)
        caption: Optional caption text
    
    Returns:
        dict with success status and messageId
    """
    import os
    
    if not display_name:
        display_name = os.path.basename(file_path)
    
    payload = {
        "chatId": group_id,
        "filePath": file_path,
        "mediaType": "document",
        "fileName": display_name
    }
    
    if caption:
        payload["caption"] = caption
    
    resp = requests.post(
        f"{BRIDGE_URL}/send-media",
        headers={
            "Authorization": f"Bearer {BRIDGE_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )
    
    return resp.json()
```

## Examples

### Drop HTML to TIMBR PRD group
```bash
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>" \
  -d '{
    "chatId": "120363427118724513@g.us",
    "filePath": "/tmp/mockup.html",
    "mediaType": "document",
    "fileName": "Timbr-Mockup-v3.html"
  }'
```

### Drop PDF to Blair's Magazine group
```bash
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>" \
  -d '{
    "chatId": "120363429573679291@g.us",
    "filePath": "/tmp/magazine.pdf",
    "mediaType": "document",
    "fileName": "Blair-Magazine-June.pdf"
  }'
```

## Finding New Group IDs

When user mentions a new group name:

```python
import requests

BRIDGE_TOKEN = "<WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>"

resp = requests.get(
    "http://127.0.0.1:3000/groups-all",
    headers={"Authorization": f"Bearer {BRIDGE_TOKEN}"}
)

for g in resp.json():
    print(f"{g.get('subject', 'Unknown')} → {g['id']}")
```

## Auth Token Location

The bridge token is in `~/.hermes/.env` as `WHATSAPP_BRIDGE_TOKEN`.

Current token: `<WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>`

## Response Format

Success:
```json
{"success": true, "messageId": "3EB0A09D2AB35E65C50CAC"}
```

Failure:
```json
{"error": "Unauthorized"}
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 401 Unauthorized | Check token matches `~/.hermes/.env` |
| File not found | Use **absolute** path, not relative |
| 413 Payload too large | Bridge limit is 50MB; file may exceed |
| Connection refused | Bridge not running; check `ps aux | grep bridge` |

## When to Use This Skill

User says any of:
- "drop the file in [group]"
- "send this to [group]"
- "share in the group"
- "put this in [group name]"
- "drop it here" (when in a group chat context)

**Skip `send_message` tool** — go straight to `/send-media` endpoint.

## CRITICAL PITFALL — Confirmation Message ≠ File Drop

**Sending a "Done — file dropped ✅" message to the user's DM is NOT the same as dropping the file to the group.**

The failure pattern:
1. Agent calls `/send-media` correctly → file lands in group ✅
2. Agent then *also* sends a follow-up text message via `send_message` tool → lands in user DM
3. User sees the DM confirmation but no file in the group, thinks the file wasn't sent

OR worse:
1. Agent accidentally sends the file itself to user DM (wrong chatId)
2. Then sends confirmation to user DM
3. Group gets nothing

**Rule**: After a successful `/send-media` to a group, report back inline in the same chat (DM) with a brief confirmation — but NEVER use `send_message` to the user's DM as a *substitute* for the actual group drop. The file must go to the group; the confirmation can come back here.

**When user says "you sent it to me directly / you didn't send it to the group"**: immediately resend to the correct group using `/send-media` with the correct `chatId`. Don't re-explain what happened.

## CRITICAL: /send-media vs /send

| Endpoint | Use Case | Payload |
|----------|----------|---------|
| `/send-media` | **Files on disk** — HTML, PDF, images | `filePath` (absolute path) |
| `/send` | Text messages, or base64 inline media | `media` (base64 data URI) |

**Always prefer `/send-media` for files.** It's simpler, avoids base64 encoding, and handles large files better. The `/send` endpoint with base64 hits "Argument list too long" errors on large files and requires a workaround via Python requests.
**Skip `send_message` tool** — go straight to `/send-media` endpoint.

## CRITICAL: Don't Confuse "Here" With User's DM

When user says "drop the file **here**" or "send it **here**" while discussing a group project:
- "Here" means **the project's group chat**, not the user's DM
- Check context for which group is active (e.g., TIMBR discussion → TIMBR APP - PRD group)
- If user corrects you ("you sent it to me directly"), immediately resend to the correct group

**Never send project files to user's DM when a project group exists.**

## CRITICAL PITFALL — Do NOT Work Around With Drive Links

**"Drop the file" means the ACTUAL FILE appears in chat as a native WhatsApp attachment.**

❌ **WRONG:** Upload to Drive → share the Drive URL → send link as text message
✅ **RIGHT:** Use `/send-media` endpoint → file attachment appears directly in chat

Tanzim explicitly hates the Drive link workaround. When the bridge works, use it. If the bridge is truly down (401/connection refused), say so honestly rather than defaulting to Drive links.

This mistake persists because the agent pattern-matches "file delivery" to "upload and share link" — break that pattern. The user wants the native WhatsApp document attachment experience.
