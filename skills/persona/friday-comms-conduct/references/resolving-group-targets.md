# Resolving a named group ("Tahmeed's Desk") to a WhatsApp group target

`send_message action=list` returns group **IDs only** (e.g. `whatsapp:120363408371537142`), no human names. To send to a group the user named in plain English, you must map name → ID first. Don't guess — sending to the wrong group is an outward-facing mistake.

## Known identity anchors (in `~/.hermes/grants.json`)
`grants.json → assistant_managers[]` carries per-person labels + WhatsApp IDs. As of Jun 2026:
- **Tanzim (owner):** sender id `160799431606497@lid`.
- **Tahmeed (Adiyan)** — Tanzim's youngest brother / AI student: `whatsapp_id 90345106862172@lid`, alt `8801789840112@s.whatsapp.net`.

So a message from `90345106862172@lid` IS Tahmeed — useful both for address-term selection and for identifying which session/group is his.

## Resolving the group ID
The bare ID isn't in `grants.json`. Two reliable, read-only paths:
1. **Session-content match (preferred, no external calls):** find the recent session whose transcript IS that conversation, then read its group/chat key. Search session files under `~/.hermes/sessions/` for a distinctive recent line from that chat (e.g. the topic discussed), or for the person's WhatsApp number. The matching `.jsonl`'s inbound `user` messages carry `[sender:<id>]` and the file/session metadata ties to the chat.
2. **grants/state cross-ref:** `grep -rl "<person_number>" sessions/` narrows to sessions involving that person; intersect the `120363…` group IDs that recur with that person to find their dedicated "Desk" group.

## Pitfalls
- Don't dump the whole directory of `120363…` IDs and pick one — many session files embed the FULL target list (every group), so "group IDs present in the file" ≠ "this file's chat". Key on the session's own chat_id / the inbound `[sender:]`, not on every ID mentioned.
- The WhatsApp bridge HTTP endpoint (`localhost:3000/...`) may be blocked/denied — don't rely on it. Prefer the on-disk session + grants approach.
- Confirm the resolved group before sending. If you can't resolve it with confidence, ask the user to confirm the target rather than firing into the wrong room.
