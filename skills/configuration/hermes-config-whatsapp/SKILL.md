---
name: hermes-config-whatsapp
category: configuration
description: Suppressing system/backend alerts from leaking into WhatsApp group chats, and other WhatsApp-specific config tuning.
triggers:
  - "backend texts leaking into group"
  - "system alerts in WhatsApp"
  - "suppress file mutation verifier"
  - "hide internal messages from group"
---

# Hermes Config — WhatsApp

## ⚠️ Group mention fix — May 31 2026 lessons

**Problem:** Tanzim does NOT want to tag/mention Friday in group chats — plain text must trigger a response. He also does NOT want Friday responding to others (e.g. Tahmeed) with his personal register.

**Root cause of the incident:** Setting `require_mention: true` globally silenced Friday in ALL groups including Tanzim's. The fix was overcorrected from config rather than handled as a persona issue.

**Correct config:**
```yaml
whatsapp:
  require_mention: false          # Never set to true — breaks Tanzim's groups
  free_response_chats: "160799431606497@lid,14255203988@s.whatsapp.net"  # Tanzim's IDs
  keyword_trigger: friday
  keyword_session_minutes: 480
  owner_chat_id: 160799431606497@lid
```

**How it actually works (from source):**
- For group messages: checks `free_response_chats` (chat JID, not sender ID) first → if match, respond. Otherwise falls through to `require_mention`.
- `require_mention: false` means respond to everyone in all groups — use `free_response_chats` with group JIDs to whitelist specific groups if needed.
- The Tahmeed/register problem is a **persona rule**, not a config rule — don't touch config for it.

**Gateway restart required** after any config change to whatsapp section — use `systemctl --user restart hermes-gateway`. Config changes don't hot-reload.

**Progress/status messages:** Set `gateway_notify_interval: 0` to stop "still working…" messages firing into chats. Also set `interim_assistant_messages: false` and `tool_progress: false` under `platforms.whatsapp`.

-Specific Tuning

## Suppress backend/system alerts from group chats

Two sources of system noise that can leak into WhatsApp:

### 1. File-mutation verifier footer
Appended when a write/patch call failed during a turn. Suppressed via:

```yaml
# in ~/.hermes/config.yaml, under display:
display:
  file_mutation_verifier: false
```

### 2. Gateway "still working / queued" heartbeat messages
The agent sends ⏳ "Still working… (N min elapsed)" and "Queued for the next turn" progress pings into WhatsApp at a configurable interval. These leak into group chats during long-running tasks. Kill them with:

```yaml
# under agent: in ~/.hermes/config.yaml
agent:
  gateway_notify_interval: 0   # 0 = disabled; default 180 = fires every 3 min
```

Also ensure the platforms block suppresses interim messages at the WhatsApp layer:

```yaml
display:
  platforms:
    whatsapp:
      tool_progress: false
      interim_assistant_messages: false
```

### 3. Self-improvement / curator review messages
Background skill-review fork that sends summary messages. Suppressed via:

```yaml
# top-level in ~/.hermes/config.yaml
curator:
  enabled: false
```

## WhatsApp Bridge Direct API — Auth and Field Names

The bridge runs on `localhost:3000` and requires a Bearer token on every request.
Plain curl without auth returns `{"error":"Unauthorized"}` — misleading, not a group/WA issue.

```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chatId":"120363426592331480@g.us","message":"test"}'
```

**Field name is `chatId`, NOT `to`.** Using `to` returns `{"error":"chatId and message are required"}`.

**Group ID gone stale:** If a group returns `{"error":"item-not-found"}` with correct auth, the group JID is dead — the account was removed from that group, or the group was deleted. Fix: find the correct live group JID (bridge `/chats` endpoint or test each candidate), update cron job deliver targets.

**Health check (no auth needed):**
```bash
curl -s http://localhost:3000/health
# {"status":"connected","queueLength":0,"uptime":...}
```

**Cron job 401 ≠ bridge down.** If cron jobs show delivery 401 errors but `/health` returns `connected`, the issue is the job's target group JID, not the bridge itself.

## When to apply
Any time Tanzim says backend/system texts are leaking into a group chat. These are cosmetic suppressions — they don't affect agent function, only what gets sent to the chat.

## Checklist — full leak suppression
When any group chat leak is reported, run through all three:
- [ ] `display.file_mutation_verifier: false`
- [ ] `curator.enabled: false`
- [ ] `agent.gateway_notify_interval: 0`

## Notes
- Changes take effect after gateway restart.
- `file_mutation_verifier` lives under the `display:` block.
- `curator:` is a top-level key — add it if absent.
- The patch tool works fine for config.yaml — no need for Python json manipulation.
