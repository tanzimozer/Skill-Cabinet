---
name: owner-identity-check
category: security
description: Canonical method for verifying Owner identity from incoming messages
tags: [security, whatsapp, identity, grants]
triggers:
  - any request requiring Owner-tier auth
  - codeword validation
  - side-effecting actions
related_skills:
  - hermes-agent
---

# Owner Identity Verification

## The Problem
WhatsApp sends different ID formats depending on message source:
- **Linked devices** → `160799431606497@lid`
- **Primary number** → `14255203988@s.whatsapp.net`

Both are Tanzim. Both must be treated as Owner.

## Verification Steps

1. Read `~/.hermes/grants.json` **fresh** every request
2. Check `owner.ids[]` array — if sender matches **any** entry, they are Owner
3. Never match on a single `whatsapp_id` field; always iterate the array

## grants.json Structure (canonical)

```json
"owner": {
  "ids": [
    "160799431606497@lid",
    "14255203988@s.whatsapp.net"
  ],
  "scopes": ["*"]
}
```

## Common Mistakes (never do these)

- ❌ Checking only `owner.whatsapp_id` (old format)
- ❌ Assuming @lid and @s.whatsapp.net are different people
- ❌ Requiring both IDs to match
- ❌ Caching owner ID across requests

## If a New ID Format Appears

If Tanzim messages from an unrecognised format but can provide the codeword and context matches (memory, conversation history), add the new ID to the `owner.ids[]` array immediately — no out-of-band verification needed if codeword + context are solid.

## Lesson Learned (May 2026)

grants.json was initially set with only `@s.whatsapp.net` format, but WhatsApp linked devices use `@lid` format. Both are the same person. Fixed by changing `owner.whatsapp_id` (single string) to `owner.ids[]` (array) so either format matches Owner.
