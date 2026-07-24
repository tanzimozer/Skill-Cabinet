---
name: friday-user-onboarding
description: Onboard a new primary user into Friday — establish identity, access control, profiles, and persistent memory structure across multi-chat contexts.
triggers:
  - User is setting up Friday for the first time
  - User wants to introduce contacts/friends to Friday
  - User wants to define who can access Friday and what they can do
  - User wants to establish authorization codes or access rules
  - User wants to create persistent profiles for themselves or collaborators
---

# Friday User Onboarding

## What this covers
The class of task: setting up a primary user's identity, authorization rules, contact profiles, and memory structure so Friday operates correctly across multiple WhatsApp chats and group contexts.

## Steps

### 1. Establish primary user identity
- Confirm their name
- Get their WhatsApp number — this is the primary key for identifying them vs others
- Save to memory: `PROFILE — [NAME]: [role, location, company, WhatsApp number]`

### 2. Set authorization code
- Confirm the codeword they'll use to authorize sensitive actions (provisioned out-of-band, never written here)
- Save rule to memory: friends/contacts need explicit authorization from the primary user before Friday acts on their requests

### 3. Define access control rules
- Who can reach Friday (groups only vs direct DMs)
- Whether friends can DM Friday directly (Tanzim's preference: no — groups only)
- Save to memory: access control rules including DM restrictions

### 4. Build contact profiles
- For each person the user introduces, collect: name, role, location, relationship to user, company/project affiliation
- Save as: `PROFILE — [NAME]: [role, location, relationship, notes]`
- Consolidate duplicate entries — don't store the same person twice under different keys
- If the contact has an **active working relationship** with the primary user (client, trainee, collaborator), also capture:
  - The nature of the ongoing work (e.g. fitness training, business project)
  - What role Friday plays in that work (e.g. assist trainer in group chat, track progress, generate programs)
  - Where the work happens (which group chat, channel, or context)
  - Save this as part of the profile line, not as a separate memory entry

### 5. Verify memory fits within limits
- Memory cap is ~1,375 chars. Keep entries compact.
- Merge redundant entries (e.g. if Blair was mentioned earlier as a collaborator and then profiled, remove the earlier raw mention)
- Profiles should be one dense line each

## Ongoing persona tuning (post-onboarding)
The user may refine Friday's persona over time — tone per audience, flirt level, formality, greeting style. When this happens:
- Identify what changed: tone with primary user vs others, routing rules, greeting variants, communication style
- Update the relevant memory entry (usually the Friday persona line) — keep it compact
- Memory is near-capacity; shorten existing entries before adding new ones
- Common tuning patterns seen so far:
  - "25% flirt when talking to me" → add to persona memory line: `25% flirt with Tanzim — confident, subtle`
  - "more corporate with others" → add: `With others: +25% corporate — professional, precise, polished`
  - "text me personally = DM me here" → save as routing rule in user memory
- These are persona preferences, not onboarding steps — save to memory immediately, no confirmation needed

## T1 Trainee Onboarding (fitness clients)

When Tanzim adds a new T1 Campaign trainee, follow this pattern:

### Files to create
- `/home/hermes/trainees/[name]_profile.md` — identity, access protocol, links to other files, program placeholders
- `/home/hermes/trainees/[name]_supplements.md` — full supplement stack with upper limit dosing

### Profile file structure
```
# [Name] — Fitness Profile
## Identity
## Access Protocol (approved/not approved, what they can query)
## Supplement Stack (link to supplements file)
## Training Program (TBD or populated)
## Nutrition Plan / Macros (TBD or populated)
## Check-In Log
```

### Macro formula (Tanzim's standard)
- Protein: 1g per lb bodyweight (non-negotiable)
- Carbs: 0.75g per lb bodyweight
- Fat: fills remaining calories (typically 20-25% of TDEE)
- Minimum 40g protein per meal
- Ask trainee: current bodyweight + preferred meal count before building

### Google Sheet
- Create a sheet named "[Name] [Year]" (e.g. "Blair 2026")
- First tab named by month (e.g. "May 2026")
- Add SUPPLEMENTS segment: dark header row merged across columns A:B, column headers bolded grey, all supplements + upper limit doses populated
- Use Python + googleapiclient directly (not gws CLI) for multi-tab/formatted sheets

### Access approval
- Trainee is read-only on their own data by default
- Tanzim must explicitly say "approve [name]" to grant no-codeword query access
- Once approved: save to memory + update t1-campaign skill's approved trainees list + update trainee's profile file

### Pitfalls
- Always get bodyweight before building macros — can't calculate without it
- WhatsApp @mention by JID (e.g. @3724340625515) may not work in all group bridge configs — fall back to name mention if bridge errors
- Don't hardcode individual trainee names into t1-campaign skill — keep that skill's access protocol section general; list approved trainees there only as a registry

## Blocking Users

When Tanzim says "block [number/name]" with the codeword:
1. Add to memory SECURITY entry: `BLOCKED: +1XXXXXXXXXX (ignore all messages)`
2. Format: strip formatting from phone number, store as +1XXXXXXXXXX
3. If name given instead of number, ask for the number to confirm
4. Once blocked: Friday ignores ALL messages from that number — no response, no acknowledgment, no DM to Tanzim
5. To unblock: Tanzim says "unblock [number]" with BETA — remove from BLOCKED list in memory

### Block vs. restrict
- **Blocked**: Complete silence, as if Friday doesn't exist for them
- **Restricted** (non-Tanzim friends): Can ask about themselves, no actions, groups only
- Blocking is nuclear — use for people who shouldn't interact with Friday at all

## Pitfalls
- Memory fills up fast — remove redundant/duplicate entries before adding new ones
- Group chat memory issues: the system prompt is built once at session start from a frozen snapshot of USER.md/MEMORY.md. If memory was updated in a different session (e.g. a DM), an already-open group chat session will NOT see the update — it's running on a stale snapshot. The fix is for the group session to expire/reset so it reloads from disk on the next message. Old sessions won't refresh mid-flight. This is by design (prompt caching stability), not a bug.
- Do not save the authorization code itself into memory in a way that exposes it to others reading context — keep it abstract ("Tanzim's authorization code is saved; only he knows it") or as already established in the persona prompt

## Verification
- Ask the user to confirm profiles look right before saving
- After saving, recite back what's in memory so user can spot gaps
- If group chat memory isn't loading, ask user to send a screenshot of the broken response for diagnosis
