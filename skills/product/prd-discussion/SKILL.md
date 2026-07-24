---
name: prd-discussion
description: "Facilitate PRD/product spec discussions, track open questions, and translate decisions into structured documentation."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [prd, product, spec, decisions, timbr, requirements]
    related_skills: []
---

# PRD Discussion Facilitation

## When to use
User shares a PRD, feature doc, or spec and wants to work through open questions, design decisions, or architecture tradeoffs.

## Workflow

### 1. Read the full document first
Never respond to a PRD share with questions before reading it. Acknowledge with a compressed summary:
- What it is (one sentence)
- Build approach / constraints
- Feature count and timeline
- What's already specced vs open

### 2. Track open questions by number
Keep the original Q-numbers from the PRD. When questions are resolved, record BOTH the question AND the answer. Don't just mark "resolved" — the answer is the content.

Format:
```
Q2: Password reset → email link (NOT OTP — user said "yes" to both options, clarified to email link)
Q21: Workout complete trigger → manual End Workout button (not auto-complete)
```

### 3. Cross-check answers for ambiguity
When a user gives a one-word answer to a multi-option question, flag the ambiguity:
- "Yes" to "email link or OTP?" is not an answer — follow up to confirm which
- "Depends" or "TBD" → push for a timeline or a provisional decision

### 4. Surface pending decisions proactively
After a batch of answers, produce a clean pending list — only the truly unresolved ones. Don't re-list questions that have a clear direction even if not formally locked.

### 5. Technical depth on architecture questions
When the user asks "how do I incorporate X into the system", go to the decision-making layer:
- What data does the engine collect?
- What decisions does it make automatically vs escalate to humans?
- What's the output format (draft, notification, event)?
- Where's the boundary between automation and human judgment?

Use tables for decision trees when there are 3+ conditions.

## Timbr-specific decisions (captured 2026-05-31)
See `references/timbr-prd-decisions.md` for full Q1–Q47 resolution log.

## Key design patterns that emerged

### Program vs Exercise hierarchy
- **Program (mesocycle):** 3–6 week block, defines training split + periodisation + goal phase
- **Exercise swap within program:** NOT a new program — logged as progression event with reason
- **New program trigger:** Split changes, phase change, periodisation model changes, or volume landmark change
- **Test:** "Would a different trainer call this a different programme or the same with tweaks?"

### Wearable data architecture
Two separate data layers — they complement, never replace each other:
- **Wearable:** Session biometrics (HR, calories, duration, effort intensity) — session-level
- **Swipe cards:** Prescription compliance (which exercise, what weight, how many reps) — exercise-level
- Rep-counting via wearable not reliable for strength training at mainstream scale (Apple Watch best but only covers ~10 exercise types for simple bilateral movements)
- Best proxy for missing data: **historical pre-fill** from last session + RPE triangulation

### Plan engine intelligence layer
Three-layer headless automation:
1. **Data collection:** Every `workout.completed` event captures exercise status + values + RPE + wearable
2. **Decision engine** (fires at mesocycle end): per-exercise audit with four outcomes:
   - >80% complete + progressed → advance
   - >80% complete + plateaued → flag plateau
   - 50–80% → carry forward flagged
   - <50% → hold, require trainer input
   - RPE trending down → ready to progress; trending up → too aggressive
3. **Output:** Draft program + reasoning card → trainer reviews and publishes (never auto-publish)

### Skipped exercise handling
- Skipped = SKIPPED signal, not null — it's actionable data for the trainer
- If skipped >60% of mesocycle by preference (no injury): auto-substitute equivalent same-muscle exercise next program
- Never carry forward the identical exercise that was consistently avoided
- Engine works inside program structure — does NOT replace the program (that's a trainer call)

## Pitfalls
- Don't conflate "new program" with "new exercise" — exercise swaps within a program are progression events
- Don't let the engine auto-publish next program — trainer review is always required
- When user gives a partial answer ("doesn't matter"), record it as resolved-not-relevant, not as open
