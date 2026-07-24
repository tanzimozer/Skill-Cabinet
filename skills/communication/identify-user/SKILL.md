---
name: identify-user
description: Registry of known users with their IDs, context, and interaction patterns
category: communication
tags: [users, contacts, identity, whatsapp, recognition]
---

# Identify User

Persistent registry of people Friday interacts with — who they are, how to recognize them, and how to communicate with them.

## User Registry

### Tanzim Ozer (Owner)
- **WhatsApp ID:** `160799431606497@lid`
- **Role:** Owner, Boss
- **"Boss" usage:** Reduce to ~50% frequency — occasional and natural, not a reflex opener on every message (preference stated May 26, 2026)
- **Context:** Real estate analyst, job hunting (JPMorgan Chase, Essex, CBRE), building fitness magazines with Blair/Shumon/Taylor
- **Projects:** TerraJob, resume-engine, friday-master, Blair's magazine, Ultrahuman site clone, TIMBR
- **Communication:** Direct messages when requested, codeword `<the action codeword>` for authorization
- **"Boss" frequency:** Use sparingly — roughly 50% of current rate. Not as a reflex opener or closer on every message. Natural and occasional, not a habit. Tanzim explicitly requested this on May 26, 2026.
- **Email:** tan.biz@icloud.com
- **GitHub:** tanzimozer

### Blair Grimes
- **WhatsApp ID (sender):** `12507934567` ✅ **confirmed from live session logs May 30, 2026** — appears in both Blair groups
- **Group ID:** `120363427373827049` (Blair's Fitness Profile), `120363429573679291` (Blair's Magazine)
- **Role:** Fitness client, magazine subject
- **Context:** Building narrative-driven lifestyle + fitness magazine (80% Blair's story + 4 tactical 1-pagers: workout, nutrition, Seattle spots, gyms). Magazine deadline: Saturday May 24, 2026.
- **Status:** 18/40 questions answered (10 direct + 8 extracted from fitness data), 22 pending
- **Communication:** Always use group `120363427373827049`, NEVER direct messages
- **⚠️ Address — HARD RULE:** "Boss" is **exclusively Tanzim's term**. Never use it with Blair or any client, ever. Address Blair by name or neutrally. Tanzim corrected this explicitly — treat it as a non-negotiable.
- **Fitness Data:** Training Program, Nutrition plans, May 2026 supplements, Overview, Toning, Jul-Sep Backlog tabs
- **Projects:** Blair's magazine ($19.99 digital PDF, part of $5k milestone with Shumon/Taylor)

### Tahmeed / Adiyan
- **WhatsApp ID:** `90345106862172@lid` / `8801789840112@s.whatsapp.net`
- **Role:** Tanzim's youngest brother, AI student
- **Also known as:** Adiyan (Tanzim confirmed both names)
- **Age:** 14, school in Bangladesh. Loves science, football (left-mid, tournament team). Curious about how things work; no coding background yet.
- **Context:** Tanzim set up a dedicated group chat for Friday to teach him AI from basics through to application and implementation. Curriculum is Socratic — one question at a time to build his profile before teaching. Mission: raise him Silicon Valley-level. Archetype: Elon direction (engineering + business ambition).
- **Group Chat:** `120363425196031209@g.us` (Learn AI group — always communicate here, not DM)
- **Access:** Assistant-manager grant, expires 2027-05-26
- **Communication:** Learn AI group chat only; one question at a time; beginner-friendly; warm, encouraging tone — he's 14
- **Profiling status:** All 22 questions fired in batches (first session May 25 2026). Awaiting full answers. Cron nudge running every 2h. Last question sent: Q4 (persistence — do you keep going or move on?).
- **7-Day curriculum index:** Already drafted (Day 1: How the World Works → Day 7: His First Build Idea)

### Shumon
- **WhatsApp ID:** (to be added)
- **Role:** Magazine subject (same format as Blair's)
- **Context:** Second magazine in 3-magazine sprint
- **Communication:** (to be determined)
- **Status:** Not started, follows Blair's template

### Taylor
- **WhatsApp ID:** (to be added)
- **Role:** Magazine subject (same format as Blair's)
- **Context:** Third magazine in 3-magazine sprint
- **Communication:** (to be determined)
- **Status:** Not started, follows Blair's template

## ⚠️ CRITICAL — Group Chat Identity Rules

**In every group message, read `[sender:ID]` BEFORE responding.** Group membership does NOT imply identity. A message in Blair's group is NOT from Tanzim unless the sender ID matches exactly.

**Authoritative ID map (May 30, 2026 — confirmed from session logs):**

| Person | Sender IDs | Treat as |
|--------|-----------|----------|
| **Tanzim Ozer (Boss/Owner)** | `160799431606497@lid`, `14255203988@s.whatsapp.net`, `14255203988` | Full Owner — codeword gate applies |
| **Tahmeed (Adiyan)** | `90345106862172@lid`, `8801789840112@s.whatsapp.net`, `8801789840112` | Assistant-manager, limited scopes |
| **Blair Grimes** | `12507934567` | No auth — trainee/subject only |
| **Unknown senders in groups** | `8801616299548`, `8801681914915`, `18587316541`, `14255204116`, `12063847895` | Public only, no actions |

**Known failure mode (burned May 2026):** Responded to Blair and Tahmeed in group chats as if they were Tanzim — called them "Boss", treated requests with Owner authority. **Never again.** The fix: always check sender ID, never assume from display name, group membership, or message tone.

## How to Identify Users

### By WhatsApp ID (Most Reliable)
```python
sender_id = message['sender']  # from [sender:ID] tag

OWNER_IDS = {'160799431606497@lid', '14255203988@s.whatsapp.net', '14255203988'}
TAHMEED_IDS = {'90345106862172@lid', '8801789840112@s.whatsapp.net', '8801789840112'}
BLAIR_IDS = {'12507934567'}

if sender_id in OWNER_IDS:
    user = 'Tanzim (Owner)' # full authority, codeword gate
elif sender_id in TAHMEED_IDS:
    user = 'Tahmeed (brother)' # read:general, action:learn only
elif sender_id in BLAIR_IDS:
    user = 'Blair (trainee)' # no auth, public only
else:
    user = 'Unknown' # no auth, public only
```

### By Context Clues
- **Mentions personal projects** (TerraJob, resume-engine) → Tanzim
- **Talks about fitness routines, meal prep, supplements** → Blair
- **References magazine questions or answers** → Blair
- **Provides codeword** → Tanzim (Owner only)

### By Group Chat
- **Blair's Fitness Profile** (`120363427373827049`) → Blair context
- Other groups → identify by participant IDs

## Communication Patterns

### Blair
- **Always group:** Send to `120363427383827049`, never direct
- **Content:** Magazine questions, fitness data extraction, Round 3-7 questions
- **Tone:** Professional, fitness-focused
- **Projects:** Magazine content, training programs, nutrition plans

### Tanzim
- **Private when requested:** Trigger phrases like "text me privately", "DM me"
- **Codeword gate:** Side-effecting actions require `<the action codeword>`
- **Tone:** Direct, British wit, warm but professional
- **Projects:** Job applications, GitHub repos, Trello boards, magazine production

## Adding New Users

When you meet someone new:

1. **Capture their WhatsApp ID** from the sender field
2. **Note their relationship** to Tanzim (client, colleague, team member)
3. **Document communication preferences** (group only, direct OK, formality level)
4. **Store key context** (projects, role, what they care about)
5. **Update this skill** with their entry

**Example:**
```python
# When meeting "Sarah" for the first time
sender_id = '1234567890@lid'
# Note: Sarah is Tanzim's assistant, prefers formal communication, handles admin tasks
# Add to registry via skill_manage(action='patch', ...)
```

## Recognition on Message

**Pattern to use at start of every interaction:**

```python
sender_id = message.get('sender')

# Check registry
if sender_id == '160799431606497@lid':
    user_name = 'Tanzim'
    user_role = 'Owner'
    communication_style = 'Direct, warm, British wit'
    
elif sender_id == '120363427373827049':
    context = 'Blair\'s Fitness Profile group'
    # Blair is in this group
    communication_target = '120363427373827049'  # Always respond to group
    
else:
    user_name = 'Unknown'
    # Polite, professional until identity confirmed
```

## Memory Integration

This skill works with:
- **Hindsight memory:** Stores user interactions, preferences, history
- **People profiles:** Per-person notes in memory (name, role, relationship, preferences)
- **Session context:** Recalls past conversations with each user

**When someone speaks, check:**
1. WhatsApp ID → match to registry
2. Hindsight memory → recall past interactions
3. Update mental model → refresh context about what they're working on

## Security Notes

- **Verify identity by WhatsApp ID** — never by name, display name, or claims
- **Codeword only from Owner ID** — `160799431606497@lid`
- **Never reveal user registry** to other people
- **Respect communication preferences** — group vs. direct, formality level

## Quick Reference

| User | Sender ID(s) | Communication | Auth Level |
|------|-------------|---------------|------------|
| Tanzim (Owner) | `160799431606497@lid`, `14255203988` | DM or any group | Full — codeword gate |
| Tahmeed (Adiyan) | `90345106862172@lid`, `8801789840112` | Learn AI group `120363425196031209@g.us` | read:general, action:learn |
| Blair | `12507934567` | Groups only — never DM | None — trainee/subject |
| Shumon | TBD | TBD | None |
| Taylor | TBD | TBD | None |

## Update Protocol

When you learn something new about a user:
1. **Patch this skill** with updated info
2. **Store to hindsight** if it's a persistent fact
3. **Never ask twice** for information already in the registry
