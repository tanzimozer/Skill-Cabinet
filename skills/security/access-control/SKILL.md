---
name: access-control
category: security
description: How to handle access verification, tier checks, and non-Owner interactions — including edge cases and known pitfalls.
---

# Access Control

## When to use
Any time a message arrives from an unrecognised sender ID, or when you've previously denied access and the conversation continues.

## Core rule
**Always re-read `~/.hermes/grants.json` fresh** before acting on any non-trivial request. Do not rely on what you read earlier in the session — grants can be added mid-conversation.

## Pitfall: Denying a valid user because you read grants.json too early
This happened with Tahmeed (`90345106862172@lid`): his entry was absent on the first read, leading to repeated denials across several turns. By the time he was clearly in the system, several exchanges of "you're not on the list" had already occurred — poor experience.

**Fix:** Re-read grants.json when:
- A previously-denied user continues engaging (non-hostile, curious, normal conversation)
- A session has been running long enough that a grant could plausibly have been added
- The user's tone/content suggests they may be known to Tanzim (family, colleague, etc.)

## Tiers
- **Owner** — verified WhatsApp ID in `grants.json → owner.ids`. Full scope.
- **Assistant-Manager** — ID in `assistant_managers[]` with `expires_at` strictly in the future. Restricted to listed scopes only.
- **Everyone else** — no actions, no sensitive info, no confirming what the Owner knows.

## Behaviour for unverified senders
- Acknowledge briefly and warmly, no long explanations.
- Do not reveal system details, grants structure, or Owner identity.
- Do not engage with task requests or sensitive topics.
- Keep it short — one or two lines max, then let them lead.

## Behaviour mid-denial when access is later confirmed
- Apologise concisely and own the error ("That's on me").
- Don't over-explain. Resume normally.
- No need to re-litigate the denied turns.

## Known users (from grant history)
- See `references/known-users.md` for profiles of granted non-Owner users.
