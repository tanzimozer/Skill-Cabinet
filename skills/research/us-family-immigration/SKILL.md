---
name: us-family-immigration
description: "Analyse US family-based immigration sequencing — who can petition whom, which category applies, wait times, and age/marriage traps. Use when a user asks whether a relative can immigrate, how to bring family to the US, or how long a green-card path takes."
metadata:
  hermes:
    tags: [immigration, uscis, visa-bulletin, family, research, legal]
---

# US Family-Based Immigration

Reason about who can sponsor whom, which visa category applies, realistic wait times, and the traps that age people out. This is a sequencing problem: each person needs their OWN petition, and the order/timing of filings is everything.

**Always verify live before committing to numbers.** Categories and rules below are stable law; priority-date wait times change monthly via the Visa Bulletin. Pull the current bulletin (see references file) rather than quoting from memory.

**Disposition:** give the honest structural read, flag the hard conditions (unmarried / under-21 traps), and recommend a real immigration attorney for the filing sequence and CSPA timing — these mistakes age people out permanently.

## The two-tier structure (the core mental model)

| Tier | Who | Cap? | Wait |
|------|-----|------|------|
| **Immediate Relatives (IR)** | Spouse, unmarried child under 21, or parent of a US **citizen** | No annual cap | Only processing time, no backlog |
| **Family Preference (F1–F4)** | Everyone else (LPR's relatives; citizen's adult/married kids; siblings) | Annual + per-country caps | Backlog governed by Visa Bulletin |

## The single biggest trap: Immediate Relatives carry NO derivatives

When a US citizen petitions a **parent** (category **IR-5**), that petition CANNOT carry the parent's other children along. IR categories have **zero derivative beneficiaries**. The parent's other kids (the petitioner's siblings) cannot "ride along." **Each person needs a separate I-130.**

This kills the common assumption "I'm bringing my mom, so my younger sibling comes too." They do not.

## Category cheat-sheet

| Petitioner | Beneficiary | Category |
|-----------|-------------|----------|
| US citizen | spouse / parent / unmarried child <21 | Immediate Relative (no wait) |
| US citizen | unmarried child 21+ | F1 |
| US citizen | married child (any age) | F3 |
| US citizen | sibling | **F4 (12–15 yr backlog — usually useless)** |
| **LPR (green-card holder)** | **spouse / unmarried child <21** | **F2A (fastest preference, often near-current)** |
| LPR | unmarried child 21+ | F2B |

**The clean path to bring a green-card-holder's young child:** LPR parent files I-130 → **F2A**. Marriage destroys F2A/IR eligibility entirely (drops to F3). Staying unmarried and under 21 is non-negotiable.

## The naturalisation upgrade (the good news)

When an LPR petitioner **naturalises** (becomes a citizen, typically ~5 yrs as LPR), an existing **F2A petition for an unmarried child under 21 automatically converts to Immediate Relative (IR-2)** — unlimited visas, NO backlog. No new petition needed (8 CFR §204.2(i)). CSPA freezes the child's age as of the **naturalisation date** (INA §201(f)(2)).

So: file F2A the day the parent gets their green card; if they naturalise while the child is still unmarried and under 21, the case jumps the queue.

## CSPA — preventing "aging out"

A "child" = unmarried AND under 21. Without CSPA, turning 21 while waiting drops F2A → F2B (much longer). CSPA freezes a calculated age:

**CSPA age = (age when visa becomes available) − (days the I-130 was pending)**

Locked in only if the beneficiary **"sought to acquire" LPR status within 1 year** of visa availability (filed I-485 or DS-260). On the petitioner's naturalisation, the simpler **naturalisation-date freeze** applies instead.

## Workflow for answering these questions

1. Identify the petitioner's status (citizen vs LPR) and the exact relationship.
2. Map to the category table. Watch for the IR-no-derivatives trap.
3. Pull the **current Visa Bulletin** for the live priority dates (see `references/visa-bulletin-lookup.md`).
4. State the realistic total timeline (USCIS I-130 processing ~12–24mo + priority-date wait).
5. Flag the unmarried/under-21 conditions and any CSPA timing risk.
6. Recommend an attorney for the filing sequence — getting the priority date filed early and protecting CSPA age is what matters.

See `references/visa-bulletin-lookup.md` for the live-data fetch recipe and how to read the F2A row.
