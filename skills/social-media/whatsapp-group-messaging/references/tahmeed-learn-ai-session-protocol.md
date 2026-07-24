# Tahmeed — Learn AI Session Protocol

## Context
Tanzim's 14-year-old brother, Dhaka. Zero background. Friday is assigned tutor.
Learn AI group: `120363425196031209@g.us`
Sheet: `19v5x4oScpEPXkjHBWvt97UHtWChki5UGniJvop258bc` (Tahmeed profile)

## Tanzim's Expectations (hardcoded)
- **Autonomous and proactive** — don't wait for Tanzim to drive sessions. If Tahmeed is meant to be learning, get him started immediately.
- **Sequential gating — ONE TASK AT A TIME** — assign only the current task. Do not front-load a full time-blocked plan into one message. When Tahmeed says he's done, assign the next task then. Gate is his confirmation, not a timer.
- **Drive to completion** — when Tanzim says "work with him", own it fully. Send task → monitor → respond to Tahmeed → gate → test → next task. Do NOT stop and wait for Tanzim to say "now ask him the next question" or "now test him." Anticipate and execute each step until the session is done or Tanzim redirects. Parking after each action is a failure mode.
- **Speed over comfort** — Tanzim's instruction is "executing with speed, getting up to speed now." No slow warm-up, but don't dump everything at once either.
- **Everything logged to sheet** — session topics, gate scores, quiz banks. Tab: AI Foundations Week.
- **Cron-driven** — 8 AM Dhaka kick-off, 10 AM wrap-up. Cron IDs: kick-off `7fd483de1cbe`, wrap-up `e461f4d4699d`.
- **Hindsight for profile data** — Tahmeed's facts, progress, and answers live in Hindsight (hindsight_retain), not the 6k-cap memory tool. Always check Hindsight for his master profile before starting a session. Update the single master entry, never add duplicates.

## Task Assignment Format
Each message to Tahmeed should contain ONLY the current task:
1. Task number + one-line description
2. Single video link or single instruction
3. Clear "come back when done" trigger
4. Nothing else — no future tasks, no full schedules, no options

**Good:**
```
Task 1:
Watch this video (8 mins): https://youtu.be/...
Come back when you're done and I'll give you Task 2.
```

**Bad:** Sending a full time-blocked schedule with Task 1, 2, 3 all at once.

## Addressing Tahmeed
- **Just use "Tahmeed"** — no @mentions, no phone numbers
- @number tags render as raw numbers on his phone, not his name
- Plain name is cleaner and reads better in the group

## Curriculum Order — CRITICAL
**Start here, in this order:**

### Day 1 (AI Foundations Week — what to teach first):
1. Task 1 — Watch: Kurzgesagt "Humans Need Not Apply" → https://youtu.be/wvWpdrfoEv0
2. Task 2 — Watch: 3Blue1Brown "But what is a neural network?" → https://youtu.be/aircAruvnKk *(take notes)*
3. Task 3 — Teach: Intelligence vs Artificial Intelligence (live explanation in chat)
4. Task 4 — Teach: Evolution of AI (calculators → rule-based → ML → deep learning → LLMs)
5. Task 5 — Gate Test: 5 MCQs + explain phone autocomplete in own words

**DO NOT start with:**
- OSI Model (F1) — this is pre-work for networking context, not Day 1 AI foundations
- DNS/HTTP (F2) — same, pre-work only
- Any of the 10 projects — those are weeks away

The sheet's AI Foundations Week tab is the source of truth for task order. Always read it before assigning.

## Testing Protocol (after each video)
When Tanzim says "test his knowledge":
- Ask one question at a time
- Wait for his answer before the next question
- Questions should be in plain English, no jargon
- After 3 questions, give feedback and move to next task
- Keep questions conceptual, not recall-based (explain in your own words > what are the 7 layers)

## Gate Test Protocol
- 5 MCQs per day + 1 hands-on task
- Score logged to AI Foundations Week tab, Gate Test Score column
- Cumulative test Day 5: 10 questions across all 5 days
- If score < 3/5: 15-min recap before next block

## Backend Hygiene — CRITICAL
- **Never send backend confirmations ("Sent.", "Done.", "Message delivered.") to the group**
- Those go to Tanzim's DM or stay silent
- Only Tahmeed-directed content goes to the Learn AI group
- Confirmation of sending belongs in the DM reply to Tanzim, not the group

## When Tahmeed Doesn't Respond
- First no-response: wait 30 mins, send a nudge in the group
- Persistent silence: DM Tanzim to flag
- Don't escalate immediately — 14-year-olds drift. One nudge first.

## Pre-work (before Jun 1)
F1 — OSI Model (NetworkChuck): teach *after* Day 1–2 AI foundations are solid
F2 — DNS/HTTP (Fireship): same

## 10 Projects (Jun 8 – Sep 19)
Escalating difficulty, free tools, GitHub uploads. See AI Learnings tab for full list.
