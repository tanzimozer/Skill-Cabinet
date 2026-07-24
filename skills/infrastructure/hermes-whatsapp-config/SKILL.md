---
name: hermes-whatsapp-config
description: "Diagnosing and fixing WhatsApp gateway config — require_mention, free_response_chats, group behaviour, progress message leaks."
category: infrastructure
tags: [whatsapp, gateway, config, groups, require_mention, friday]
version: 1.0.0
created: 2026-05-31
---

# Hermes WhatsApp Config

Patterns for configuring and debugging the WhatsApp gateway — group response behaviour, mention requirements, progress leaks.

## Key config block (`~/.hermes/config.yaml`)

```yaml
whatsapp:
  require_mention: false          # false = respond to anyone in any chat
  free_response_chats: "160799431606497@lid,14255203988@s.whatsapp.net"  # Tanzim's IDs
  keyword_trigger: friday         # saying "friday" in a group triggers a session
  keyword_session_minutes: 480
  owner_chat_id: 160799431606497@lid
  home_channel:
    chat_id: 160799431606497@lid
    name: Tanzim Ozer
```

**PITFALL:** `free_response_chats` takes **group JIDs** (e.g. `120363425196031209@g.us`), not sender IDs. Tanzim's personal IDs in this list only affect DM routing — they do NOT make him exempt from mention requirements in groups. To allow free response in a specific group, add the group's JID.

**PITFALL:** `require_mention: false` makes me respond to EVERYONE in all groups — including Tahmeed, Sagar, etc. This caused the Tahmeed "For you, Boss?" incident (May 31). The persona fix is behavioural, not config — I just respond differently to non-Tanzim users. Don't set `require_mention: true` to solve persona problems; it locks out Tanzim too.

## Group response logic (from whatsapp.py)

For group messages, the check order is:
1. Is `chat_id` in `free_response_chats`? → respond
2. Is `require_mention: false`? → respond to all
3. Does message start with `/`? → respond
4. Is it a reply to the bot? → respond
5. Does it @mention the bot? → respond

So with `require_mention: false`, everyone in every group gets responses. The Tanzim-only behaviour must be enforced in the SOUL/persona layer, not config.

## Progress message leak fix

"Still working..." / "⏳ Queued" messages firing into group chats:

```yaml
agent:
  gateway_notify_interval: 0   # kills all in-flight progress pings (was 180s)

display:
  platforms:
    whatsapp:
      tool_progress: false
      interim_assistant_messages: false
```

Set `gateway_notify_interval: 0` — this is the main fix. The `interim_assistant_messages: false` handles the "[Group chat — internal reasoning]" leak separately.

## Config changes require gateway restart

Config is loaded at startup — changes to config.yaml don't hot-reload.

```bash
systemctl --user restart hermes-gateway
```

**Note:** `systemctl --user restart` will briefly kill the current session (this is expected). The command will appear to time out from inside the session — that's normal. The gateway comes back up in ~10s.

## Verifying active config

```bash
python3 -c "
import yaml
wa = yaml.safe_load(open('/home/hermes/.hermes/config.yaml'))['whatsapp']
print('require_mention:', wa.get('require_mention'))
print('free_response_chats:', wa.get('free_response_chats'))
print('gateway_notify_interval:', yaml.safe_load(open('/home/hermes/.hermes/config.yaml'))['agent'].get('gateway_notify_interval'))
"
```

## Known group JIDs (Tanzim's groups)
- Learn AI: `120363425196031209@g.us` (Tahmeed's teaching group)
- TIMBR APP PRD: JID not yet confirmed — ask Tanzim to ping from group to capture it

## What NOT to do
- Don't set `require_mention: true` to fix persona issues — it silences Tanzim in groups
- Don't add Tanzim's personal LID to `free_response_chats` expecting group bypass — it only affects DM policy
- Don't use `require_mention_groups: true` — not a valid config key (tried May 31, had no effect)
