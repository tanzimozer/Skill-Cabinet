---
name: prd-facilitation
description: "Facilitating PRD discussions, tracking open questions, synthesising decisions, and maintaining a living question register across sessions."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [prd, product, requirements, facilitation, decisions, questions, timbr]
    related_skills: [ui-mockup-production]
---

# PRD Facilitation

## When this applies
User shares a PRD or feature spec (PDF, Quip doc, Markdown) and wants to discuss, resolve open questions, or build on top of it.

## Workflow

### 1. Read the doc first
Always read the full PRD before responding. Extract:
- Feature list (with build times and cuttability)
- Open questions (numbered)
- Already-resolved decisions
- Design principles

### 2. Acknowledge and orient
Give a compressed summary (not a wall): what it is, the key build approach, and the feature count. End with a pointed question or transition — don't just dump and wait.

### 3. Cross-match when the user provides answers
When the user drops a bulk list of answers, cross-match against the open questions. Call out:
- Questions answered clearly ✅
- Answers that need clarification (e.g., "yes" to an "A or B?" question)
- Questions still genuinely open

### 4. Maintain a clean pending list
After cross-matching, produce a numbered list of what's still open. Keep it concise — one line per question. Revisit after each discussion block.

---

## Question register format (Timbr example)

```
**Still open — needs a call:**
1. Q2 — Password reset: email link or OTP?
2. Q5 — Client without trainer: account state?
...
```

When the user answers questions mid-discussion (not in a bulk list), update the pending list immediately in your next reply.

---

## Discussion facilitation

PRD discussions often drift into product design. That's fine — facilitate it:
- Ask clarifying questions to narrow ambiguity
- Surface dependencies ("this decision affects Q9 and Q22")
- Call out when a decision resolves multiple open questions at once
- Don't let "TBD" accumulate — push for a directional answer even if not final

### Decision capture
When the user makes a decision in discussion (not just in a Q&A list), capture it explicitly:
> "Right — so that resolves Q21: manual End Workout button, not auto-complete. Noted."

Don't just silently absorb it.

---

## Program / mesocycle concepts (Timbr-specific)

From the 2026-05-31 session — these definitions were worked out in discussion and should be used consistently:

| Term | Definition |
|---|---|
| Journey (macrocycle) | Client's overall goal (fat loss, muscle building) — rarely changes |
| Program (mesocycle) | 3–6 week block with a specific milestone — THIS is what "new program" means in Timbr |
| Exercise swap | Progression event WITHIN a program — not a new program |
| New program trigger | Split changes OR phase change OR periodisation model changes OR volume landmark changes |

**The test:** if you handed the program to a different trainer with no context, would they say "different programme" or "same with tweaks"?

### Plan generation engine logic (Timbr decision, 2026-05-31)
At mesocycle end, the engine fires per exercise:

| Signal | Decision |
|---|---|
| >80% completion + load progressed | ✅ Advance |
| >80% completion + no progression | ⚠️ Plateau — flag |
| 50–80% completion | ⚠️ Carry forward, flag |
| <50% completion | 🚫 Skip pattern — hold, require trainer input |
| RPE trending down | Signal: client adapting → ready to progress |
| RPE trending up | Signal: too aggressive → regress or deload |

Skipped-by-preference exercises: carry the **intent** forward (same muscle group, different exercise from library), not the same exercise. Skip >60% of mesocycle = auto-substitute equivalent.

**Engine produces draft program + reasoning card for trainer review — never auto-publishes.**

---

## References
- `references/timbr-prd-decisions.md` — full resolved Q register from 2026-05-31 session
