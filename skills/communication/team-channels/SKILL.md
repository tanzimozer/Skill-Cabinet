---
name: team-channels
description: "WhatsApp group structure and team member roles"
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [whatsapp, groups, team, communication]
---

# Team Communication Channels

## Group Structure

### TIMBR APP - PRD
- **ID:** *(pending — Tanzim to ping from group so JID can be logged)*
- **Members:** Friday, Sagar G., Tanzim
- **Purpose:** TIMBR app product dev — Sagar leads MVP build, Tanzim and Friday in the loop
- **Use for:** App UI drops, build updates, screenshot sharing, PRD coordination
- **Note:** Friday is in this group but does NOT act on Sagar's directions without Tanzim's sign-off

### Towsif's Desk
- **ID:** 120363411696218942@g.us
- **Purpose:** Towsif's private room — direct communication with Towsif Mustafa
- **Use for:** Private coordination, technical requests, OAuth setup, 1:1 tasks

### Blair's Fitness Profile
- **ID:** 120363427373827049@g.us
- **Purpose:** Blair's fitness tracking and coaching
- **Use for:** Fitness updates, nutrition, training content for Blair

### Learn AI (Tahmeed's tutoring group)
- **ID:** 120363425196031209@g.us
- **Members:** Friday, Tahmeed (Adiyan) `90345106862172@lid` / `8801789840112@s.whatsapp.net`, Tanzim
- **Purpose:** Friday teaches Tahmeed AI — basics through to application and implementation
- **Mode:** Socratic; one question at a time; build student profile first, then curriculum
- **Cron nudge:** 2-hour interval cron fires questions one at a time until all 22 profiling questions answered or Tanzim calls it off
- **Note:** Backend system alerts (file-mutation verifier, curator) must NOT surface here — config suppressed via `file_mutation_verifier: false` and `curator.enabled: false`

### Blair's Magazine
- **ID:** 120363429573679291@g.us
- **Purpose:** Magazine production for Blair's TIMBR issue
- **Members:** Towsif (Assistant Manager), others
- **Use for:** Magazine content, design coordination, deadline updates

## Team Roles

### Towsif Mustafa
- **DM ID:** 199015949950994@lid
- **Private room:** Towsif's Desk (for direct/private comms)
- **Role in Blair's Magazine:** Assistant Manager
- **Remit:** Canva template setup, content population, design coordination, Wix/PDF exports
- **Contact email:** timbr.mustafa@gmail.com

## Resolving unknown group JIDs

The `send_message(action="list")` output shows group IDs as bare numbers (e.g. `120363424680620369`) with no names. To identify which group is which:

**Method:** Ask Tanzim to send a message *from* the target group. The `[sender:...]` prefix on that message contains the group's JID. Log it immediately.

**Do not:** Guess, try all groups, or make Tanzim list them — just ask for a ping from the group.

Once identified, update this skill with the JID.

## Communication Pattern

- **Private tasks for Towsif** → Towsif's Desk
- **Magazine production updates** → Blair's Magazine group
- **Blair fitness/nutrition** → Blair's Fitness Profile

## Sending Messages

```bash
# To Towsif's Desk (private)
curl -s http://127.0.0.1:3000/send \
  -H "Content-Type: application/json" \
  -d '{"chatId": "120363411696218942@g.us", "message": "..."}'

# To Blair's Magazine (project)
curl -s http://127.0.0.1:3000/send \
  -H "Content-Type: application/json" \
  -d '{"chatId": "120363429573679291@g.us", "message": "..."}'

# To Blair's Fitness Profile
curl -s http://127.0.0.1:3000/send \
  -H "Content-Type: application/json" \
  -d '{"chatId": "120363427373827049@g.us", "message": "..."}'

# To Learn AI (Tahmeed's tutoring group)
# send_message target: "120363425196031209@g.us"
```
