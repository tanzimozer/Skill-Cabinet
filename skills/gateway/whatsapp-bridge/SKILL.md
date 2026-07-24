---
name: whatsapp-bridge
description: Troubleshooting and operational patterns for the WhatsApp bridge (Baileys-based)
category: gateway
tags: [whatsapp, messaging, gateway, bridge, troubleshooting]
---

# WhatsApp Bridge

> **WA-BRIDGE-SKILL-SAFE-RESTART-V1.** Sections 3 and 7 were rewritten 2026-05-31 to remove
> the harmful `pkill bridge && node bridge.js &` pattern that caused recurring
> WA outages. The bridge is a managed child of `hermes-gateway`; only ever
> restart via `systemctl --user stop/start hermes-gateway`. See CLAUDE.md
> gotcha #3 (no `gateway restart` — soft reload crashes WA bridge).

Operational knowledge and troubleshooting patterns for Hermes's WhatsApp gateway bridge.

## Architecture
- **Bridge**: Node.js service (`~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`)
- **Port**: `localhost:3000` (default)
- **Session**: Stored in `~/.hermes/whatsapp/session/`
- **Logs**: `~/.hermes/whatsapp/bridge.log`

## When to use this skill
- `send_message` tool fails with WhatsApp-specific errors
- Bridge connectivity issues
- Message delivery failures to groups or DMs

## Common issues

### 0. Direct bridge calls require Bearer token auth

All state-changing bridge endpoints (`/send`, `/send-media`, `/edit`, etc.) require:
```
Authorization: Bearer <WHATSAPP_BRIDGE_TOKEN>
```
Retrieve it with: `echo $WHATSAPP_BRIDGE_TOKEN` (already exported in gateway sessions), or fallback: `grep 'WHATSAPP_BRIDGE_TOKEN' ~/.hermes/.env | cut -d= -f2`

Without it you get `{"error":"Unauthorized"}` (HTTP 401). `/health` is always open.

> **Do not confuse** `X-Bridge-Secret` (the gateway webhook secret on port 8644) with the bridge Bearer token (port 3000). They are different — using `X-Bridge-Secret` against the bridge gives a 401.

See `references/send-message-workaround.md` for full curl examples with auth.

> ⚠️ **Wrong endpoint pitfall**: The correct send endpoint is `/send` (with `chatId` field).
> `/send-message` does **not** exist and returns a 404 HTML error page — not a JSON 401.
> If you see `Cannot POST /send-message` in an HTML response body, you're hitting the wrong path.
> Always use: `POST /send` with `{ "chatId": "<jid>", "message": "<text>" }`.

### 1. send_message fails with JID decode error
**Symptom**: `WhatsApp bridge error (500): {"error":"Cannot destructure property 'user' of 'jidDecode(...)' as it is undefined."}`

**Cause**: Bridge cannot parse the target JID (group ID or contact number).

**Solutions**:
1. **Retry once** — Transient bridge state can resolve on second attempt
2. **Use direct bridge API** — See `references/send-message-workaround.md`
3. **Manual fallback** — Provide user with message text to send manually

**Do not** capture this as "WhatsApp messaging is broken" — it's a transient bridge parsing issue, not a permanent failure.

### 2. Person-specific messaging protocols

**When user says "always text [Person] in [Group]"**, store this in **hindsight memory**, not just session memory:

```python
hindsight_retain(
    content="[Person] communication protocol: Always message [Person] in '[Group Name]' group chat (ID: [group_id]), never send direct messages. This is the only [Person]-related group.",
    context="[Person] messaging preference"
)
```

**Why hindsight, not skill**: Person-specific routing rules are operational state, not workflow patterns. They belong in durable memory so every future session knows the rule.

**When to surface the protocol**: Any time the user says "text [Person]" or "[Person]" appears in a task requiring messaging.

### 3. Bridge not running

**NEVER `pkill` the bridge directly.** The bridge is a managed child process of
`hermes-gateway`. Killing it manually leaves the gateway-adapter in a confused
state, race-conditions the respawn, and can drift env vars between gateway and
the new bridge (root cause of the 2026-05-31 401 loop).

**Check**: `pgrep -f bridge.js`
**Restart the right way** (gateway-managed, env stays consistent):
```bash
systemctl --user stop hermes-gateway && sleep 5 && systemctl --user start hermes-gateway
```
This stops the gateway (which stops its bridge child), waits long enough for
sockets to close, then systemd respawns the gateway, which spawns a fresh bridge
with proper env inheritance from `~/.hermes/.env`. No drift, no race.

### 4. Session expired
**Symptom**: QR code prompt or "Not connected" errors  
**Fix**: Re-scan QR code via bridge startup output

### 5. `send_message` tool sends to wrong field
**Symptom**: Tool returns 401 Unauthorized or 400 error  
**Cause**: `send_message` tool passes `to` field; bridge requires `chatId`. Also the tool may not attach the Bearer token correctly.  
**Fix**: Bypass the tool and call bridge directly:
```python
import requests
token = open('/home/hermes/.hermes/.env').read()  # parse WHATSAPP_BRIDGE_TOKEN
requests.post('http://localhost:3000/send',
  headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
  json={'chatId': '<jid>', 'message': '<text>'})
```

### 6. Sending images/media via `/send-media`
**Correct payload**: `{"chatId": "...", "filePath": "/absolute/path/to/file.png", "caption": "..."}`  
**Wrong**: passing `base64` or `url` fields — these are NOT supported; bridge will 400.  
**Size limit**: Default Express body limit is ~100KB. For images, patch `bridge.js` line with `express.json()` → `express.json({ limit: '50mb' })` then restart bridge.  
**Large images**: Crop/split before sending. Use PIL: `img.crop((0,0,w,h//2)).save(...)`. Keep each file under ~200KB for reliable delivery.

### 7. Bridge restart sequence (correct order)

```bash
# Restart the parent gateway — its bridge child is restarted with it.
systemctl --user stop hermes-gateway && sleep 5 && systemctl --user start hermes-gateway
# Health check after ~10s of warmup
sleep 10 && curl -s http://127.0.0.1:3000/health
```

This is the ONLY supported way to restart the bridge. Do NOT use `pkill`, `kill`,
`fuser -k 3000/tcp`, or any direct-spawn `node bridge.js &` — those bypass the
gateway's managed-process tracking and were the root cause of the 2026-05-31
recurring 401 outage. The bridge file is `bridge.js` (not `.mjs`).

### 8. Typing indicator stuck — "always typing" in chat (fixed 2026-07-13)

**Symptom**: WhatsApp shows Friday "typing..." permanently in the chat even when idle.

**Root cause**: `bridge.js` had a `/typing` endpoint that sends `composing` presence but NO endpoint to clear it. Once set, `composing` never expires on the recipient's client — it shows indefinitely.

**Fix applied**: Added `/stop-typing` endpoint to `bridge.js` that sends `available` presence, AND added `stop_typing()` method to `whatsapp.py` adapter that calls it.

`bridge.js` — add after the `/typing` block:
```js
app.post('/stop-typing', async (req, res) => {
  const { chatId } = req.body;
  if (!chatId) return res.status(400).json({ error: 'chatId required' });
  try {
    await sock.sendPresenceUpdate('available', chatId);
    res.json({ success: true });
  } catch (err) {
    res.json({ success: false });
  }
});
```

`whatsapp.py` — add `stop_typing()` method alongside `send_typing()`:
```python
async def stop_typing(self, chat_id: str, metadata=None) -> None:
    """Clear typing indicator via bridge (sends 'available' presence)."""
    ...
    async with self._http_session.post(
        f"http://127.0.0.1:{self._bridge_port}/stop-typing",
        json={"chatId": chat_id},
        ...
    ):
        pass
```

To **manually clear** a stuck typing indicator immediately (useful when bridge was just restarted and indicator is stale):
```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://127.0.0.1:3000/stop-typing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chatId":"160799431606497@lid"}'
```

**After bridge restart**: the new `bridge.js` must be running (not the old one). The bridge is a managed child of `hermes-gateway` — see section 7 for correct restart sequence. Direct bridge spawn with `node bridge.js &` works to pick up `bridge.js` changes, but only after killing the old process and confirming the new port is live.

**Auth token**: `WHATSAPP_BRIDGE_TOKEN` from `~/.hermes/.env` (NOT the gateway webhook secret `48912f...` from `config.yaml` — that's a different credential on a different port). Confusing the two gives 401.

### 9. Contact & Group Resolution — Structural Gaps (diagnosed 2026-07-xx)

**Symptom**: Friday cannot recognise contacts by name, cannot identify WhatsApp groups by human name, and confuses plain-text name mentions ("Blair") with WhatsApp @mentions ("@Blair").

**Root causes — all five confirmed via source inspection:**

**RC1 — Group names never resolved.**
`bridge.js` sets `chatName` to the raw numeric JID prefix for groups (e.g. `120363424680620369`), not the WhatsApp group subject. The `/groups-all` endpoint already exists in `bridge.js` but is never called on startup. `channel_directory.json` shows all 30+ groups unnamed.

**RC2 — No contacts registry.**
No file on the system maps phone numbers or JIDs to human names. `channel_directory.json` has only 3 named contacts; the rest are raw JIDs. `memories/USER.md` has person profiles (Blair, Tahmeed) but no JID or phone number fields.

**RC3 — @mention and plain-text name are structurally different and neither is decodable.**
- Plain text `"Blair"` → body contains the word, `mentionedIds` is empty. Friday matches it loosely against memory.
- WhatsApp @mention `"@Blair"` → body contains `"@14255203988"` (the phone number), `mentionedIds` contains the JID. The display name "Blair" is rendered client-side only — it never hits the wire. Friday has no lookup table to resolve `14255203988` → "Blair".

**RC4 — `mentionedIds` passed through but never decoded.**
The `MessageEvent` object contains `raw_message` (which includes `mentionedIds`) but this is not structured into the AI's context. No pre-processing step resolves JIDs in `mentionedIds` to names.

**RC5 — pushName matching unreliable.**
When a contact sends a message, `senderName` comes from their self-reported `pushName`. If Blair's WhatsApp display name is "B" or "Blair M", it won't match "Blair" in memory.

**Fix plan (in build order):**

| # | Fix | Effort | Unlocks |
|---|-----|--------|---------|
| 1 | Call `/groups-all` on gateway startup → write `~/.hermes/wa_groups.json` → use for `chatName` resolution | Low — endpoint exists | Group name recognition |
| 2 | Build `~/.hermes/wa_contacts.json` — `{"Blair": {"jid": "...", "phone": "..."}}` — populated by Tanzim supplying numbers | Low build, needs input | Name ↔ JID mapping |
| 3 | Pre-process `mentionedIds` in `_build_message_event()` → decode JIDs via contacts file → inject resolved names into message context | Low once #2 exists | @mention decoding |

**Data Tanzim needs to supply for Fix 2:**
Key contacts — Blair, Tahmeed, Waseem, Towsif, Imran Khan — phone numbers confirmed from WhatsApp contact screenshots. File format:
```json
{
  "Blair": {"phone": "+1XXXXXXXXXX", "jid": "1XXXXXXXXXX@s.whatsapp.net", "role": "fitness client"},
  "Tahmeed": {"phone": "+880 1789-840112", "jid": "8801789840112@s.whatsapp.net", "role": "friend"},
  "Waseem": {"phone": "+1 (650) 798-9994", "jid": "16507989994@s.whatsapp.net", "role": "friend"},
  "Towsif": {"phone": "+880 1616-299548", "jid": "8801616299548@s.whatsapp.net", "role": "friend"},
  "Imran Khan": {"phone": "+880 1858-121999", "jid": "8801858121999@s.whatsapp.net", "role": "contact"}
}
```
Blair's number was not confirmed in session — needs Tanzim to supply before Fix 2 can be completed.

## Reference files
- `references/send-message-workaround.md` — Direct HTTP API fallback when tool fails
- `references/media-send-patterns.md` — Image splitting, size limits, filePath vs base64
- `references/contact-resolution-diagnostic.md` — Full diagnostic report: root causes, file paths examined, fix plan
