---
name: send-file-to-chat
summary: Send a file (CSV, JSON, etc.) to chat via messaging platform
description: |
  Detects available messaging platforms (WhatsApp, Telegram, etc.) and sends a file to the specified target.
  Falls back to plaintext file content in chat if binary transfer unavailable.
  Handles file path resolution, format detection, and message composition.
---

## Overview
Sends a file to chat via the most appropriate messaging platform. Primary use: exporting data (CSV, JSON, TXT) to the user immediately.

## How to Use

```
User: "send the CSV to chat"
Friday: Deploy send-file-to-chat skill with file path and target.
```

### Parameters
- **file_path** (required): Full path to file (e.g., `/home/hermes/n8n_learning_tracker.csv`)
- **target** (optional): Specific platform+recipient. If omitted, defaults to primary DM (Tanzim Ozer)
- **format** (optional): File format hint ('csv', 'json', 'txt', etc.). Auto-detected if omitted.
- **include_content** (optional): If true, also paste full file content as plaintext fallback

### Workflow
1. **Resolve file path** — expand relative paths, verify file exists
2. **Detect platform** — call `send_message(action='list')` to see available targets
3. **Choose target** — use provided target or default to `whatsapp:Tanzim Ozer (dm)`
4. **Attempt send** — call `send_message(message=content, target=target)`
5. **Fallback** — if platform auth fails, read file and send as plaintext message (with note: "Couldn't transfer binary; here's the content:")

### Implementation Notes
- Always include a one-line header describing the file (e.g., "n8n learning tracker CSV for Towsif")
- For CSV/JSON, include the full content in the message itself (most platforms support this)
- For binary files (images, PDFs), note limitation and offer alternative (Google Drive link, file path)
- Don't announce the skill use; just send the file and confirm once

### Error Handling
- **Platform unavailable**: Try next platform in order (WhatsApp → Telegram → fallback plaintext)
- **File not found**: Report the file path and suggest alternative
- **Auth failure**: Log the failure plainly, attempt plaintext fallback once

## Example Session
```
User: send me the csv
Friday: [sends file via WhatsApp or pastes content if auth down]
Result: "Done. CSV sent to your DM."
```
