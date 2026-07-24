---
name: product-prd-scoping
description: "Analyse a PRD, extract MVP scope, generate vendor-ready LLD question checklist, and structure feature specs for handoff"
version: 1.0.0
tags: [prd, product, scoping, mvp, vendor-handoff, lld]
---

# Product PRD Scoping & Vendor Handoff

## When to use
- User shares a PRD (PDF, doc, or paste) and asks for scope, analysis, or handoff prep
- Building MVP feature list for a vendor or dev team
- Generating open questions before LLD / low-level design work begins

## Step sequence

### 1. Extract scope from PRD
Read the full document. Summarise:
- **In scope (MVP)** — bulleted, grouped by surface (client app / trainer app / admin / infra)
- **Explicitly deferred** — what's V2+
- **Ruled out for MVP** — decisions that narrow scope further (e.g. "no Timbr Scoring", "Solo tier removed")

### 2. Value proposition analysis
Before feature listing, establish WHY the product exists for its primary user (often the B2B side, not the consumer). Ask:
- What is the core pain? (time, scale, admin burden, revenue cap)
- What does the platform replace? (spreadsheets, WhatsApp groups, manual invoicing)
- What is the one-liner value prop?

### 3. AI/automation scoring
If product uses AI, score it per function:
- ✅ Strong — AI does this well autonomously
- 🟡 Partial — works with caveats (data dependency, wearable, etc.)
- ⚠️ Gap — not solved in current spec
- ❌ Missing — not addressed at all

Be honest about gaps. Don't overclaim.

### 4. Generate MVP feature list
Group by platform surface. For each feature: name + one-line description. Mark P0/P1 where known.

### 5. Generate LLD question checklist
For each feature cluster, generate specific, answerable questions a vendor needs before building. Group by feature area. Format:

```
**Feature Area**
Q#. Question — [PRD answer if known] OR ❓ Needs your call
```

Then split the list into:
- **PRD-answered** — include the answer inline
- **Pending on you** — numbered list, clean, one question per line

### 6. Close the checklist
As user answers open questions, log answers inline. Track what's still open. When all answered → LLD is ready to draft.

## Format rules (Tanzim-specific)
- Lead with the answer, not the analysis
- Tables for structured comparisons (scope, scores, question status)
- Bullet points for feature lists — no walls of prose
- Keep section headers short
- Flag genuine gaps directly — don't soften them

## Pitfalls
- **Don't conflate B2B and B2C value props.** If the trainer is the primary customer, frame everything through trainer ROI first.
- **Ruling out features mid-session changes scope significantly** — when a tier or scoring system is removed, re-derive the MVP feature list from scratch rather than patching the old one.
- **Food logging, AI chat, wearable scoring** are common "sounds simple, actually complex" features — flag as decision points before including in MVP.
- **"AI does everything in Solo tier" is a high bar** — be honest that AI as a replacement trainer scores ~6/10 in V1; AI as a trainer's assistant scores ~8.5/10.

## Reference: Timbr MVP (Coached Tier Only, No Timbr Scoring)
See `references/timbr-mvp-scope.md` for the full scoped feature list and 47-question checklist with answers from the 2026-05-31 session.
