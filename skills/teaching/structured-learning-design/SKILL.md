---
name: structured-learning-design
description: "Designing structured learning curricula for Tanzim's people — waterfall sequencing, gate tests, cron delivery, sheet logging"
category: teaching
tags: [teaching, curriculum, learning-design, waterfall, cron, google-sheets, assessment]
version: 1.0.0
created: 2026-05-29
---

# Structured Learning Design

Patterns for designing and running structured learning programmes for Tanzim's people (Tahmeed, trainees, team members). Covers curriculum architecture, delivery via WhatsApp crons, assessment, and progress logging to Google Sheets.

**Active programmes:** Tahmeed AI curriculum (`tahmeed-ai-curriculum` skill)

---

## Curriculum Architecture

### Waterfall Sequencing
Use waterfall when: topics are genuinely dependent (understanding X is required to make sense of Y). Each block is a gate — learner must demonstrate basic competency before the next block unlocks.

**Gate test design:**
- 5 MCQs + 1 practical task per session
- MCQs test recall of key concepts from the session
- Practical task tests application (explain in own words, hand-draw a diagram, run a live comparison)
- Pass = attempted gate test. Fail = 15-min recap at start of next session, NOT a full redo
- Score logged to sheet at session close

**Sequencing logic to document per curriculum:**
- For each block: what does this assume the learner already knows?
- State the dependency explicitly as a "Waterfall gate" note
- This forces you to check whether skipping or reordering is safe

### Session Structure (2-hour window)
1. Video first (~15–25 min) — anchors the concept visually before teaching
2. Teaching sections (3–4 blocks, ~20 min each) — build on the video
3. Gate test at end (~15–20 min) — consolidates the day
4. Total: ~100 min of content + 20 min gate = 2 hours

**Pitfall — don't front-load theory.** Video → concept → test, in that order. If you explain everything before the video, the video becomes redundant and boring.

---

## Delivery via WhatsApp Crons

Two crons per programme:

| Cron | UTC schedule (Dhaka = UTC+6) | Purpose |
|------|------------------------------|---------|
| Kick-off | 2 AM UTC = 8 AM Dhaka | Deliver day's topic, video link, first instruction |
| Wrap-up | 4 AM UTC = 10 AM Dhaka | Gate questions, score, sheet log, DM summary to Tanzim |

**Kick-off message design:**
- 6–8 lines max. No walls of text.
- Good morning + what today is about (1 sentence)
- Video link with a one-line hook ("watch this first — 15 mins, worth it")
- Instruction: "reply when you're done watching and we'll go from there"
- Warm, punchy. NOT formal. Learner's age/register matters — adapt tone.

**Wrap-up cron tasks:**
1. Send gate test questions to group (conversational, not intimidating — 3 Qs verbally)
2. Log to sheet: status, score, concepts covered, quiz Qs, blockers
3. DM Tanzim 3-line summary: what covered / score / any flags

**Live teaching between crons:**
The crons are bookends. The actual teaching happens live when the learner messages during the session window. Be present, responsive, and adjust to where they are — not where the plan says they should be.

---

## Google Sheets Logging Pattern

**Tab structure for a learning programme:**
- Columns: Date | Day | Section # | Topic | Duration | Key Concepts Covered | YouTube Resources | Hands-On Task | Gate Score | Quiz Questions | Blockers/Notes | Status
- One row per section (not per day)
- Status values: ⏳ Pending → ✅ Done → ❌ Skipped
- Weekly score summary row at bottom

**Sheet write at wrap-up:**
- Find today's rows by date and section number
- Update Status to ✅ Done for completed sections
- Log Key Concepts Covered based on what the learner actually engaged with
- Log gate score and the 3 questions verbatim
- Log any confusion points or things to revisit in Blockers/Notes

**Pitfall — write to correct tab.** Always verify sheetId before writing. Tahmeed's sheet has 3 tabs now; wrong sheetId writes to wrong tab silently.

---

## Learner Profile Considerations

Before designing curriculum, understand:
- **Learning style:** hands-on vs. reading vs. watching. Shapes how much video vs. text vs. doing.
- **Frustration tolerance:** low tolerance → smaller steps, more wins, never make it feel like a chore
- **Background:** zero background → more analogies, more "why this matters", less assumed vocabulary
- **Motivation:** what does the learner want from this? Anchor every concept to that goal.
- **Age / register:** adapt tone. 14-year-old ≠ same register as a 25-year-old trainee.

**Tahmeed specifics:** 14, hands-on learner, hates rote memorisation, wants to build software/AI tools, football fan. Teach like a cool older sibling. Never condescending.

---

## Curriculum Sequencing Heuristics

1. **Conceptual before tooling.** Teach what AI is before teaching how to use it. Teach how it works before benchmarks.
2. **Familiar before abstract.** Start with something they already use (autocomplete, spam filter) then generalise.
3. **OSI / networking / CS fundamentals:** introduce as needed, not as a standalone block. Don't frontload abstract layer models without the experiential hook.
4. **Week 1 should produce confidence, not exhaustion.** One achievable win per session. End each session with something they can explain to someone else.

---

## Assessment Bank Pattern

After each session, log the gate test questions to the sheet. By end of week, you have a 25–30 question bank drawn directly from what was taught. Weekly test: pull 10 questions from the bank. Send to learner on the Sunday before the next week starts (test before new content unlocks).

This means: **never write quiz questions in advance.** Write them after the session, based on what the learner actually engaged with — not what the plan said they should have learned.
