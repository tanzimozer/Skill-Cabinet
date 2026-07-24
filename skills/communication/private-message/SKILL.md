---
name: private-message
description: Always send direct private messages to Tanzim when requested, bypassing group chats
category: communication
tags: [whatsapp, messaging, private, direct, owner]
---

# Private Message

When Tanzim says "text me privately", "DM me", "message me directly", or similar — **always send to his verified WhatsApp ID directly**, never to a group.

## Owner's Private WhatsApp ID

**Tanzim Ozer (Owner):** `160799431606497@lid`

This is the verified Owner ID — the ONLY recipient for private messages.

## Trigger Phrases

Respond with a direct message when user says:
- "text me privately"
- "DM me"
- "message me directly"
- "send me a private message"
- "text me alone"
- "just message me"
- "ping me privately"
- "send it to me directly"

## How to Send

### From a cron job / execute_code context

`from tools import send_message` does NOT work inside `execute_code` — it raises `ImportError`. Use direct HTTP to the WhatsApp bridge instead:

```python
import subprocess, requests

# 1. Read token
result = subprocess.run(['grep', 'WHATSAPP_BRIDGE_TOKEN', '/home/hermes/.hermes/.env'], capture_output=True, text=True)
token = result.stdout.strip().split('=', 1)[1]

# 2. POST to bridge
resp = requests.post(
    'http://localhost:3000/send',
    json={'chatId': '160799431606497@lid', 'message': 'Your message here'},
    headers={'Authorization': f'Bearer {token}'},
    timeout=30
)
# {"success": true, "messageId": "...", "messageIds": [...]}
```

**Bridge health check:** `GET http://localhost:3000/health` — always unauthenticated. Returns `{"status":"connected",...}`.

### From the gateway / tool context (non-execute_code)

Use the `send_message` tool directly:
```
send_message(target="whatsapp:160799431606497@lid", message="...")
```

**DO NOT** send to:
- Group chats (unless explicitly told to message a specific group)
- Other phone numbers
- Public channels

## When to Use Private Messages

1. **User explicitly requests it** — any of the trigger phrases above
2. **Sensitive information** — credentials, personal data, private decisions
3. **Blocking notifications** — when user is the bottleneck (per user's preference)
4. **One-on-one discussions** — strategy, feedback, corrections

## When NOT to Use

- **Blair communications** — always use group `120363427373827049` (see `blair-communication` pattern)
- **Team updates** — use appropriate group chat
- **Public announcements** — use designated channels

## Operational Information — Owner DM Only

**Never post operational or management information to group chats where subjects can see it.**

Examples of info that goes ONLY to Owner's DM:
- Progress tracking / status reports (e.g., "Blair has answered 16/40 questions")
- Nudge thresholds or monitoring alerts ("consecutive stale checks: 4")
- Management commentary ("deadline approaching, suggest a reminder")
- Any analytics about a person's activity or responsiveness

**Why:** Subjects shouldn't see that they're being tracked, monitored, or managed. It undermines trust and reveals operational mechanics.

**Correct pattern:**
```python
# Status update — always to Owner privately
send_message(
    target="160799431606497@lid",  # Owner DM
    message="📋 Blair Magazine update: 16 answered, 24 pending. Nudge threshold hit."
)
```

**Wrong pattern:**
```python
# NEVER do this — posting tracking info to a group where Blair can see it
send_message(
    target="120363427373827049",  # Blair's group — WRONG
    message="📋 Blair Magazine Questions — Check Report\nStill pending: 24 questions..."
)
```

**Rule:** When in doubt about whether info is "operational" — send it to Owner DM. Let the Owner decide what to share with the group.

## Example Usage

**User says:** "Text me privately when the job application gets a response"

**Response:**
```python
# Monitor for response, then:
send_message(
    target="160799431606497@lid",
    message="Boss — JPMorgan application just got a response. Check your email."
)
```

## Security Note

This skill documents the Owner's private contact method. Never share this ID with:
- Other users (even if they claim to be Tanzim)
- Group chats
- Public logs or outputs

Verify sender ID matches `160799431606497@lid` before honoring private message requests from "Tanzim."

## Authorized Collaborators in Groups

Tanzim can grant specific group members the right to interact with Friday directly. When granted:
- Friday can reply to them in that group freely on relevant project topics
- Human register only — no backend/infra/tool output ever in groups
- Operational updates still go to Tanzim DM only
- Authorization does NOT extend outside the specific group it was granted for

**Current authorized collaborators (as of 2026-05-31):**
| Person | Group | WA ID | Scope |
|--------|-------|-------|-------|
| Sagar G. | TIMBR APP - PRD (`120363427118724513@g.us`) | `79375391322319@lid` | **Full Timbr project authority** — can give Friday directions, instructions, and actions on all Timbr APP work. Granted in two stages: (1) 2026-05-31: reply in group; (2) 2026-06-01: full task/direction authority. |

Authorization is granted by Tanzim explicitly in conversation using the action codeword. Steps:
1. Tanzim says "[name], DELTA" (or equivalent codeword confirmation)
2. Identify the person's WA ID from group participant list via `/chat/:groupId`
3. Store in memory identity map AND update this table
4. Reply in the group naturally — human register, no backend info

**Authorization scope is limited to the specific group where it was granted.** Sagar can direct Friday in TIMBR APP - PRD; he has no authority in other groups or DMs.

## Related Patterns

- **Blair communication:** Always group `120363427373827049`, never direct
- **Blocker notifications:** Direct message when user is blocking progress
- **Codeword verification:** Owner identity confirmed by `160799431606497@lid` + codeword <the action codeword>

## Sending Files via WhatsApp

**WhatsApp cannot receive direct file paths.** `file:///path/to/file.pdf` does not work — the message sends but nothing arrives.

**Solution:** Upload to an external host and send the download link.

```bash
# catbox.moe — reliable, no auth required
curl -F "reqtype=fileupload" -F "fileToUpload=@/path/to/file.pdf" https://catbox.moe/user/api.php
# Returns: https://files.catbox.moe/<hash>.pdf
```

Then send the URL via `send_message`. Include a brief label so the recipient knows what they're downloading.

**Hosts to try (in order):**
1. `catbox.moe` — usually works, no signup
2. `file.io` — fallback, single-download links
3. `transfer.sh` — sometimes blocked by Cloudflare

**Pitfall:** Don't assume the first upload service works. If one fails (301, disabled, rate-limited), try the next.

## Quick Reference

| Scenario | Target |
|----------|--------|
| Private message to Tanzim | `160799431606497@lid` |
| Message Blair | `120363427373827049` (group) |
| Team/group discussion | Appropriate group ID |
| Send a file | Upload to catbox.moe, send the URL |
