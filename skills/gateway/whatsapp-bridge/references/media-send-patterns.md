# Media Send Patterns — WhatsApp Bridge

## `/send-media` endpoint

**Required fields:**
```json
{ "chatId": "<jid>", "filePath": "/absolute/path/to/file.png", "caption": "optional" }
```

**NOT supported:** `base64`, `url` fields — bridge will return 400 `chatId and filePath are required`.

## Body size limit

Default Express limit is ~100KB — too small for any image.

**Fix**: patch `bridge.js`:
```js
// line ~461
app.use(express.json({ limit: '50mb' }));
```
Restart bridge after patching.

## Splitting large screenshots

Use PIL to split a wide mockup screenshot into rows before sending:
```python
from PIL import Image
img = Image.open("/path/to/screenshot.png")
w, h = img.size
row1 = img.crop((0, 0, w, h//2 + 60))
row2 = img.crop((0, h//2 - 60, w, h))
row1.save("/tmp/row1.png")
row2.save("/tmp/row2.png")
```

## Full send pattern (Python)
```python
import requests

token = "..." # WHATSAPP_BRIDGE_TOKEN from .env
chat  = "160799431606497@lid"

for path, caption in [("/tmp/row1.png", "Row 1 caption"), ("/tmp/row2.png", "Row 2 caption")]:
    resp = requests.post(
        "http://localhost:3000/send-media",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"chatId": chat, "filePath": path, "caption": caption},
        timeout=30
    )
    print(resp.status_code, resp.text[:120])
```
