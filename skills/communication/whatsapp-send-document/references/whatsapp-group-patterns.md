# WhatsApp Group Authorization & Reply Patterns

## Problem: Group message routing
The `send_message` tool routes to Tanzim DM even when `target` is a group ID. Always use direct bridge calls for groups:

```python
import requests
TOKEN = "<WHATSAPP_BRIDGE_TOKEN — see ~/.hermes/.env>"

requests.post("http://localhost:3000/send",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"chatId": "120363427118724513@g.us", "message": "Your message"})
```

## Authorizing a new collaborator
1. Tanzim says "[person], DELTA" in a session (or grants access explicitly)
2. Get group participant list: `GET /chat/120363427118724513@g.us`
3. Cross-reference against known IDs to identify the new person's `@lid`
4. Update memory identity map with exact `@lid`, authorization scope, and date
5. Confirm their `@lid` from a message they've sent in the group (visible in bridge `/messages` if available, or from `GET /chat/:id` participants list)
6. Update `private-message` skill authorized collaborators table

**Sagar pattern (session 2026-06-01):** Tanzim added Sagar in two stages:
- Stage 1: "whitelist Sagar, DELTA" → reply to his messages in TIMBR APP - PRD group
- Stage 2: "Allow access to Sagar to give you directions, instructions, and actions on TIMBR APP project. DELTA" → full project authority on Timbr

Lesson: initial whitelisting = respond in group. Full authority grant = accept task direction from that person. These are separate permissions, both need DELTA.

## Group message history
The bridge `/messages` endpoint returns `[]` for groups in practice. Cannot pull what someone said — ask user to paste or screenshot it. Don't burn tokens trying multiple message history endpoints.

## Known group IDs
| Group | ID |
|---|---|
| TIMBR APP - PRD | `120363427118724513@g.us` |
| TIMBR-3 | `120363427031872209@g.us` |
| Blair's Fitness Profile | `120363427373827049@g.us` |
| Blair's Magazine | `120363429573679291@g.us` |

## Group message history
The bridge has no persistent message history endpoint that returns past messages reliably. `/messages` endpoint returns `[]` for groups in practice. Cannot pull what Sagar said without him resending. Don't promise to look up group history — ask the user to paste/forward it.

## Bridge health check
```bash
curl -s http://localhost:3000/health
# {"status":"connected","queueLength":0,"uptime":...}
```
If 401: bridge token mismatch. Get token from `WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`.
If empty/timeout: bridge process is down. Restart:
```bash
# Kill existing
kill $(ps aux | grep "node.*bridge" | grep -v grep | awk '{print $2}')
# Restart in background
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge && node bridge.js &
# Wait 4s then health check
```
