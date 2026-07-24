---
name: student-profile-building
category: teaching
description: Building a learner profile through structured questioning — one question at a time, directional toward engineering/AI/tech.
triggers:
  - "build his/her user profile"
  - "ask questions to understand"
  - "profile the student"
  - "extract brain power"
  - "assess learner"
---

# Student Profile Building

## Purpose
Build a complete picture of a student's mind before designing a learning path. Goal: understand natural aptitude, curiosity style, problem-solving instincts, peak interests, and weaknesses.

## Rules
- **One question at a time.** Always. No batching unless explicitly asked (e.g. "2 at a time").
- **Fire the next question immediately** when the previous answer lands — don't wait to be prompted.
- **10 questions** is the standard profile depth unless told otherwise. For a deep profile (Tanzim's directive for Adiyan), expand to the full 22-question framework below.
- Steer questions toward the intended domain (engineering, AI, science, business) — not generic personality questions.
- **Currency formatting for Bangladesh:** use ৳1,00,000 (South Asian lakh format), not $1,000.

## Question framework for engineering/AI track — Standard 10

Target: reveal wiring, not just interests.

1. **Curiosity instinct** — "When you see something, do you wonder how it works inside?"
2. **Fix-it drive** — "When something breaks, do you want to fix it or leave it?"
3. **Build ambition** — "If you could build anything, no limits — what would it be?"
4. **Persistence** — "When something's hard, do you keep going or move on?"
5. **Science depth** — "What's your favourite thing you've learned in science?"
6. **Learning style** — "Do you learn better by reading, watching, or doing/building?"
7. **Frustration pattern** — "What kind of thing makes you want to give up?"
8. **Role models** — "Is there anyone — inventor, entrepreneur, scientist — you look up to?"
9. **Ambition scale** — "Do you want to build something big someday, or do you just want to understand how things work?"
10. **Self-awareness** — "What do you think you're not good at yet?"

## Extended question bank — Full 22 (deep profile)

Used for Adiyan (Tahmeed). Fire in batches of 2 or 5 when Tanzim directs, or one at a time via cron nudge.

1. When you look at something — a machine, a building, a phone — do you ever wonder how it actually works inside?
2. When something breaks around the house, do you want to fix it yourself, or leave it for someone else?
3. If you could build anything in the world — no limits — what would you build?
4. When something is hard, do you keep going until you crack it, or move on?
5. Have you ever watched something about rockets, robots, or computers and felt like you needed to know more?
6. Would you rather invent something new, or take something existing and make it better?
7. What's something broken or unfair in the world that you think someone should fix?
8. Do you work better alone or talking it through with someone?
9. How do you learn best — watching, reading, or jumping in and trying?
10. Who do you look up to and want to be like?
11. What's something you tried that felt really hard — where you thought "I can't do this"?
12. If someone gave you ৳1,00,000 to learn or build something — what would you spend it on?
13. When you see a rocket launch or a new iPhone — excited, or do you think "I could do better"?
14. What's the last thing you got genuinely obsessed with?
15. If school disappeared and you could learn anything — what first?
16. Do you get frustrated when people around you don't think as fast as you?
17. Honest answer — do you think you're smart? And do you think where you grew up affects how far you can go?
18. Could you explain how a car engine works to a 10-year-old? Would you try?
19. Do you read anything outside school? What was the last thing?
20. What does your life look like at 25?
21. Have you ever thought "why doesn't this exist yet?" — what was it?
22. What's the biggest problem Bangladesh has right now — could technology solve it?

## Context: Tahmeed (Adiyan) — May 2026
- 14 years old, in school in Bangladesh
- Loves science; no coding/computer experience yet
- Interests: engineering, business (Elon archetype per Tanzim)
- Mission: close the gap between Bangladesh education environment and Silicon Valley-level thinking
- Tanzim's directive: treat him as if he has the world's best mentors

## Cron nudge workflow (for ongoing follow-up)

When Tanzim schedules cron check-ins to nudge Adiyan:
- The cron job delivers output to the group chat directly — produce the message as the **final response text**. Do NOT call `send_message` yourself; the cron delivery system handles it.
- Before nudging, always check recent session history (`session_search`) to establish which questions have been fired and which (if any) Adiyan has answered. Don't re-ask a question that was already answered.
- Pick ONE unanswered question per run — the most natural next one in sequence or the most engaging if he's been silent.
- Keep the nudge warm, short, no pressure. Don't dump multiple questions in a cron run.
- If Adiyan hasn't responded at all across multiple runs, vary the framing slightly — don't send the exact same phrasing twice.
- Context-gather order: (1) check memory for any recorded answers, (2) `session_search` for group chat history, (3) default to the next question in the numbered list above.

## Pitfalls
- Don't ask generic "what do you like" questions — steer toward engineering/science framing from the start.
- Don't pivot to the learning plan before the profile is complete.
- If Tanzim says "extract more info" mid-session, continue from the last answered question — don't restart.
- If questions are paused by Tanzim mid-session, resume from where you left off when directed.
- **Don't call send_message from within a cron nudge run** — cron delivery is automatic from the final response. Calling send_message inside would double-send.
- **State tracking gap:** Adiyan's answers may not route back through sessions — Tanzim may need to relay them, or they arrive via separate WhatsApp sessions that don't surface in session_search. If search yields nothing, default to the next unanswered question in the list, starting from Q3 (the most engaging anchor if truly cold).

## References
- `references/adiyan-question-log.md` — delivery history and answer tracking for Tahmeed (Adiyan)
