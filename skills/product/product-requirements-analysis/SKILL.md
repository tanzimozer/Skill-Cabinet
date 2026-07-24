---
name: product-requirements-analysis
description: "Analyse a PRD or product spec to extract MVP scope, value propositions, vendor-handoff checklists, and open questions. Used when Tanzim shares a product doc and wants structured thinking or handoff prep."
version: 1.0.0
tags: [product, prd, scope, mvp, vendor-handoff, timbr]
related_skills: [trainee-task-spec]
---

# Product Requirements Analysis

Use when Tanzim shares a PRD, spec doc, or product brief and wants:
- Scope extracted (in vs out)
- Value proposition articulated
- Vendor-handoff checklist built
- Open questions surfaced

## When to trigger

- User shares a product/feature spec and asks for scope, value prop, or handoff prep
- User asks "what does this solve for X?" (a persona or stakeholder)
- User asks for questions to ask before building

---

## Step 1: Understand the primary customer

Before extracting features, identify WHO the product is built for and WHAT economic problem it solves. The PRD may serve multiple personas — find the one who pays or whose pain drives adoption.

> Timbr: Primary customer = trainer. The one-liner: *"The trainer designs the system. The AI runs it. The client just shows up."* The true value problem is **trainer income is capped by their time** — Timbr removes that cap.

---

## Step 2: Extract MVP scope

Group into:
- **In scope (V1)** — confirmed P0/P1 features
- **Deferred (V2+)** — explicitly parked items
- **Ruled out by owner** — items cut mid-session (these override the doc)

**Always check for owner corrections during the session.** If Tanzim says "we're ruling out X", that supersedes the PRD — note it in the scope output and update the checklist.

> Timbr session corrections:
> - Solo tier → **ruled out for MVP**
> - Timbr Scoring (Harmony/XP/levels/streaks) → **ruled out for MVP**
> - Result: Coached tier only, no gamification, no wearable scoring

---

## Step 3: Score the AI/automation layer against the use case

When the product uses AI as a functional layer (not just a feature), score it honestly per role:

| Role | In Coached tier | Notes |
|---|---|---|
| Program drafting | AI drafts, trainer approves | High value |
| Nutrition planning | AI generates, trainer sets | High value |
| Admin & payments | Fully handled | Solved |
| Communication gaps | Trainer covers via chat | Human fills AI gap |
| Wearable-free data | Trainer judgement fills | Human fills AI gap |

Key insight: **Coached tier scores ~8.5/10** because the human trainer patches every gap the AI has. Solo tier scores lower (~6/10) because AI has no feedback loop beyond structured forms — no real-time adaptation.

---

## Step 4: Build the vendor-handoff checklist

Structure: feature-by-feature questions grouped by module. For each question:
1. **First answer from the PRD** — exhaust the doc before escalating
2. **Flag unanswered questions** — owner's call only

### Question generation heuristics

Per feature, always ask:
- Who initiates this action?
- What are the exact inputs/outputs?
- What does the system show if the action fails or data is missing?
- Who gets notified and how?
- Can it be edited/reversed after submission?
- What are the edge cases (expired codes, missing data, mid-action state changes)?

### Checklist format

Use a table per module: Question | PRD Answer (✅ if answered, ❓ if pending). Separate final output into two lists:
1. PRD-answered (with source)
2. Pending — owner's call

> Timbr session produced ~70 questions, ~35 answered from PRD, ~47 needing Tanzim's input. See `references/timbr-mvp-checklist.md`.

---

## Step 5: Identify structural gaps not in the doc

Look for gaps between what the product *promises* and what the spec *actually covers*. Flag as decision entries.

> Timbr gap example: **Wearable-free admin problem** — without a wearable, trainer dashboard is only as good as what client manually logs. The PRD's Tier 3/4 fallbacks are client-facing (reduce client friction) but don't solve trainer admin. What's needed:
> - Structured biweekly/monthly check-in forms
> - AI-generated client summary per trainer (regardless of wearable status)
> - At-risk flags based on app behaviour (logins, logging frequency) not just biometrics

---

## Pitfalls

- **Don't score the AI layer against the wrong tier.** Solo AI vs Coached AI are completely different systems. Coached AI is a drafting + admin tool; Solo AI is a full replacement for human coaching — much harder bar.
- **Owner corrections override the PRD.** If Tanzim rules something out mid-session, update scope immediately and carry it through all subsequent outputs.
- **Don't answer PRD questions from memory.** Always read the doc. Answers that seem obvious often have specific constraints in the spec.
- **Value prop differs by persona.** Trainer VP ≠ Client VP. When asked "what's the value prop?", confirm which persona first.

---

## Support files

- `references/timbr-mvp-checklist.md` — full 47-question checklist from the May 2026 vendor-handoff session, split by PRD-answered vs owner-pending
