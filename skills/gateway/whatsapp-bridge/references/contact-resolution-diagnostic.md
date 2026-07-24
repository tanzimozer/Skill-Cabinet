# Contact & Group Resolution — Diagnostic Report

**Date:** 2026-07 session
**Investigator:** Opus subagent (27 tool calls, read-only)

## Files Examined
- `hermes-agent/scripts/whatsapp-bridge/bridge.js` — message payload structure
- `hermes-agent/gateway/platforms/whatsapp.py` — Python adapter
- `hermes-agent/gateway/whatsapp_identity.py` — JID normalisation
- `hermes-agent/gateway/channel_directory.py` — channel/group discovery
- `hermes-agent/gateway/session_context.py` — session variable layer
- `hermes-agent/gateway/platforms/base.py` — MessageEvent schema
- `channel_directory.json` — live channel map (all groups unnamed)
- `memories/MEMORY.md` and `USER.md` — person data (name-only, no JIDs)
- `config.yaml` — free_response_chats, owner_chat_id
- `SOUL.md` — persona and memory rules

## What Data IS Available
- `senderId` (JID) — reliable
- `pushName` / `senderName` — sender's self-reported display name (semi-reliable for DMs)
- `mentionedIds[]` — JIDs of @mentioned people — present but unresolved
- `quotedParticipant` — reply threading info
- `isGroup` flag
- `chatId` — group or DM JID
- `chatName` — pushName for DMs; raw numeric JID prefix for groups (broken)
- `free_response_chats` — 4 JIDs hardcoded in config.yaml
- Person profiles in memory: Blair, Tahmeed, Tanzim — name-only, no JID linkage
- LID↔phone mapping files — exist for Tanzim's own device aliases only

## What Is MISSING
- WhatsApp contacts list (name → JID/phone)
- Group name resolution (JID → human group name)
- `mentionedId` → display name decoder
- Structured people registry with name+JID pairs
- Blair's JID or phone linked to "Blair" anywhere on system
- Group participant lists with names (available via `/chat/:id` but never loaded)

## Key Bridge Code Reference

### bridge.js — chatName bug (line ~428)
```js
// BUG: For groups, chatName becomes the raw JID prefix, not the group subject
chatName: isGroup ? (chatId.split('@')[0]) : (msg.pushName || senderNumber)
```

### bridge.js — /groups-all endpoint (EXISTS, never called on startup)
```js
app.get('/groups-all', async (req, res) => {
  // Returns all groups with real subjects — just needs to be called
})
```

### @mention wire format
When someone @mentions Blair in WhatsApp:
- `body` contains `"@14255203988"` (phone number, NOT the name "Blair")
- `mentionedIds` contains `["14255203988@s.whatsapp.net"]`
- Display name "Blair" is rendered client-side only — never transmitted

### MessageEvent schema (base.py)
The AI receives:
- `text` — message body (with `@phonenumber` tokens, not names)
- `source.chat_id` — raw JID
- `source.chat_name` — broken for groups (see above)
- `source.user_name` — pushName of sender
- `raw_message` — full data dict including `mentionedIds` — **not structured into AI context**

## Fix Implementation Notes

### Fix 1 — Group name resolution
Call `/groups-all` at gateway startup, write to `~/.hermes/wa_groups.json`:
```json
{"120363424680620369": "Blair's Training Group", ...}
```
Then in `whatsapp.py`, replace `chatId.split('@')[0]` lookup with `wa_groups.json` lookup.

### Fix 2 — Contacts registry
File: `~/.hermes/wa_contacts.json`
```json
{
  "Blair": {"phone": "+1XXXXXXXXXX", "jid": "1XXXXXXXXXX@s.whatsapp.net", "role": "fitness client"},
  "Tahmeed": {"phone": "+8801789840112", "jid": "8801789840112@s.whatsapp.net"},
  "Waseem": {"phone": "+16507989994", "jid": "16507989994@s.whatsapp.net"},
  "Towsif": {"phone": "+8801616299548", "jid": "8801616299548@s.whatsapp.net"},
  "Imran Khan": {"phone": "+8801858121999", "jid": "8801858121999@s.whatsapp.net"}
}
```
**Blair's number not confirmed** — needs Tanzim to supply.

### Fix 3 — mentionedIds decoder
In `_build_message_event()` in `whatsapp.py`, add a pre-processing step:
```python
# For each JID in mentionedIds, look up wa_contacts.json
# Inject resolved names: "Mentioned: Blair (14255203988@s.whatsapp.net)"
# Append to message context before passing to AI
```
