---
name: hermes-whatsapp-ops
category: infrastructure
description: Operational patterns for WhatsApp bridge — sending messages/media, auth, debugging, model config management.
---

# Hermes WhatsApp Operations

## Sending Text (direct bridge call)

The `send_message` tool can return 401 — use direct HTTP as reliable fallback.

**In `execute_code` context (cron jobs, subagents): `requests` works fine.** Use `subprocess.check_output` for env var reads — confirmed working July 2026. The pipe-to-interpreter security block only fires in `terminal` shell pipes, not in `execute_code`.

```python
# execute_code pattern (cron-safe):
import urllib.request, json

with open('/home/hermes/.hermes/.env') as f:
    env_content = f.read()
for line in env_content.splitlines():
    if line.startswith('WHATSAPP_BRIDGE_TOKEN='):
        bridge_token = line.split('=', 1)[1].strip()
        break

payload = json.dumps({"chatId": "160799431606497@lid", "message": "Text here"}).encode()
req = urllib.request.Request(
    'http://localhost:3000/send',
    data=payload,
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {bridge_token}'},
    method='POST'
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
```

If running from a `terminal` block (not `execute_code`), the curl pattern still works:
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId": "160799431606497@lid", "message": "Text here"}'
```

> **Pitfall:** Token truncation — always use `split('=', 1)[1].strip()` when reading from `.env`. A partial token causes 401 Unauthorized. Verified 2026-07-17.

Note: fields are `chatId` + `message` — NOT `to` + `text`.

## Sending Images / Media

`send_message` tool cannot send images. Use `/send-media` endpoint:

```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId": "160799431606497@lid", "filePath": "/path/to/image.png", "mediaType": "image", "caption": "Optional"}'
```

Supported `mediaType` values: `image`, `video`, `audio`, `document`.

## Health Check

```bash
curl http://localhost:3000/health
# → {"status":"connected","queueLength":0,"uptime":...}
```

## Bridge Logs

```bash
tail -30 ~/.hermes/whatsapp/bridge.log
```

503/428 disconnect codes are transient reconnections — normal. Bridge auto-reconnects.

## Key Reference
- Tanzim's LID: `160799431606497@lid`
- Token: `WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`
- Bridge script: `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`
- Session: `~/.hermes/whatsapp/session`
- **Finding owner LID from config:** `grep 'owner_chat_id' ~/.hermes/config.yaml` → `160799431606497@lid`

---

## Finding a WhatsApp Group Chat ID

When the user doesn't know a group's chat ID, derive it from bridge session files — no API endpoint needed.

**Step 1 — Find groups the target user is in:**
```bash
ls ~/.hermes/whatsapp/session/ | grep "<user_lid>.*@g.us"
# e.g. grep "90345106862172" → sender-key-120363426767339595@g.us--90345106862172_1--0.json
# The group ID is the @g.us part: 120363426767339595@g.us
```

**Step 2 — Confirm group name via bridge `/chat/:id`:**
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s "http://localhost:3000/chat/120363426767339595@g.us" \
  -H "Authorization: Bearer $BRIDGE_TOKEN"
# → {"name":"Tahmeed's Desk","isGroup":true,"participants":[...]}
```

Known group IDs:
- **Tahmeed's Desk**: `120363426767339595@g.us` (members: Tanzim, Tahmeed, Sagar)

---

## Per-Chat Model Override (Permanent)

### Architecture
`_session_model_overrides` in `gateway/run.py` is **in-memory only** — clears on every gateway restart. There is no per-chat model field in `config.yaml` for WhatsApp.

### Durable fix: gateway startup hook
The correct approach is a hook in `~/.hermes/hooks/` that fires on `gateway:startup` and pre-populates `_session_model_overrides` for the target session key.

**Session key format for WhatsApp groups:**
```
agent:main:whatsapp:group:<chat_id>
# e.g. agent:main:whatsapp:group:120363426767339595@g.us
```
(Note: `group_sessions_per_user: false` in config.yaml means no user suffix is appended)

**Hook structure:**
```
~/.hermes/hooks/tahmeed-desk-haiku/
  HOOK.yaml
  handler.py
```

`HOOK.yaml`:
```yaml
name: tahmeed-desk-haiku
events:
  - gateway:startup
```

`handler.py`:
```python
async def handle(event_type, context):
    runner = context.get("runner")
    if runner is None:
        return
    session_key = "agent:main:whatsapp:group:120363426767339595@g.us"
    runner._session_model_overrides[session_key] = {
        "model": "claude-haiku-4-5",
        "provider": "anthropic",
        "api_key": "",
        "base_url": "",
        "api_mode": "",
    }
```

After writing the hook files, restart the gateway. The override fires at startup and persists across turns for that group session.

### Pitfall
`/model haiku` typed in-chat only sets an ephemeral override for the current gateway process lifetime. It does not survive a restart.

---

## Model Config Management

### Config file: `~/.hermes/config.yaml`

Primary model is set at top of file:
```yaml
model:
  default: claude-sonnet-4-6
  provider: anthropic
```

Fallback chain follows under `fallback_providers:`. Check for Opus references scattered throughout — grep is your friend:
```bash
grep -n "opus\|model:" ~/.hermes/config.yaml | head -30
```

### Changing model across all references

Three places to update:
1. `model.default` (line ~2) — primary model
2. `fallback_providers` entry for anthropic (line ~12) — fallback
3. `auxiliary.vision.model` (line ~175) — vision tasks

Use `patch` tool for surgical replacement. Always grep first to confirm all references.

### Restart after model change

Gateway must restart to pick up config changes:
```bash
systemctl --user restart hermes-gateway
```

This kills the current session — Friday will come back on next message. The restart itself times out (kills own connection) — that's expected, not an error.

### Subagent model override

For Veronica deployments, pin Opus explicitly in the subagent call:
```python
subagent(tasks=[...], model={"model": "claude-opus-4-8", "provider": "anthropic"})
```

See `protocol_veronica` skill for full Veronica pattern.
