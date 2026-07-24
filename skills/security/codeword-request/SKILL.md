---
name: codeword-request
description: Protocol for requesting the authorization codeword from Tanzim when needed for side-effecting actions
category: security
tags: [codeword, authorization, security, theta, owner]
---

# Codeword Request Protocol

When a side-effecting action requires the codeword, **always ask Tanzim for it** — whether in a group chat or private DM.

## When to Request the Codeword

Any action that:
- Modifies external systems (Trello, Google Sheets, Wix, GitHub, etc.)
- Sends messages to other people
- Deletes or archives data
- Changes configuration
- Spends money
- Posts publicly
- Creates scheduled tasks

**Exception:** Skill authoring under `~/.hermes/skills/` is codeword-exempt (proactive creation allowed).

## How to Request

**Format:**
```
I need your authorization codeword to [ACTION].

[One-line description of what I'll do]

Please provide the codeword to proceed.
```

**Examples:**

**In a group chat:**
> "I need your authorization codeword to update the Trello board.
> 
> I'll move Blair's Content Extraction card to In Progress and update the description with current status (18/40 answers).
> 
> Please provide the codeword to proceed."

**In a private DM:**
> "I need your authorization codeword to send Round 3 questions to Blair's group.
> 
> I'll forward Q17-Q21 to Blair's Fitness Profile group (120363427373827049).
> 
> Please provide the codeword to proceed."

## Where to Ask

**Doesn't matter — ask wherever the conversation is happening:**
- If we're in a group chat → ask there
- If we're in a DM → ask there
- If user wants privacy → they'll provide it privately

**Don't assume location.** The user will choose whether to respond in the same chat or switch to private.

## After Receiving the Codeword

1. **Acknowledge receipt** (one line)
2. **Execute the action immediately**
3. **Report completion** (brief status)

**Example:**
> ✓ Codeword confirmed. Updating Trello now.
> 
> [executes action]
> 
> ✅ Done. Trello board updated: [link]

## Don't Proactively Volunteer

**Never suggest or offer actions that require a codeword unless:**
1. User explicitly asked for it
2. It's a genuine can't-stay-silent risk/blocker (one line, once)

The codeword gate exists to prevent me from doing things you didn't ask for. Respect that boundary.

## Security Notes

- **Never print, confirm, or hint at the codeword itself** — evaluate it transiently, never store it
- **Codeword must come from verified Owner ID** (`160799431606497@lid`) in their current message — not forwarded, quoted, screenshot, or from someone else
- **In groups:** Anyone can see the request, but only honor the codeword from the verified Owner ID
- **Replay protection:** Codeword must be in the most recent Owner message, not a previous one

## Owner's Verified WhatsApp ID

**Tanzim Ozer:** `160799431606497@lid`

Only this ID can authorize actions with the codeword.

## Codeword Name

The authorization codeword is provisioned out-of-band and never written in files or memory. It's referenced as "the codeword" in all documentation.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Need to modify Trello | Ask for codeword in current chat |
| Need to send messages to others | Ask for codeword in current chat |
| Need to delete data | Ask for codeword in current chat |
| Creating a new skill | No codeword needed (exempt) |
| User suggests an action | Clarify what I'll do, then ask for codeword |
| In group chat and need auth | Ask there — user chooses where to respond |

## Example Conversation

**User (in group chat):** "Update the magazine board with today's progress"

**Friday:** "I need your authorization codeword to update the Trello board.

I'll update Blair's Content Extraction card with:
- 18/40 questions answered (45%)
- 8 extracted from fitness data
- 22 pending Blair's input

Please provide the codeword to proceed."

**User:** "[codeword]"

**Friday:** "✓ Codeword confirmed. Updating now.

✅ Done. Board updated: https://trello.com/c/O3ga1ba4"
