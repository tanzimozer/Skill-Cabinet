---
name: product-discovery
category: product
description: Running PRD discussions, open question tracking, and product design decisions with Tanzim — fitness apps and beyond.
triggers:
  - PRD discussion
  - open questions tracking
  - product decisions
  - feature spec review
  - interaction model design
---

# Product Discovery & PRD Work

## When to use
Any session involving PRD review, feature specification, open question resolution, or product design trade-off discussion.

## How Tanzim runs these sessions
- He shares a doc (PDF or Quip link) and says "read and acknowledge" — do exactly that: read it fully, give a tight structured summary, then ask what he wants to discuss. Don't wait.
- He sends batches of answered questions inline. Cross-match against the open list, identify what's resolved vs still pending, and return the clean delta list. Don't pad.
- He thinks out loud about design problems. Your job is to reason through the trade-offs, give a clear recommendation, and defend it. He will push back — engage, don't fold.
- He uses short fragmented messages. Infer the full question; don't ask him to re-explain.

## PRD summary format
Lead with: product name + what it is (one line). Then:
- **Core approach:** build strategy, team size, platform priority
- **Feature list:** numbered, build-order, with timeline and cuttability
- **Feature N (if specced):** design principles + key interaction decisions + open questions count
- Keep it compressed. He can read — don't restate the doc, synthesise it.

## Open question tracking
- When he sends answered questions, extract and cross-match immediately.
- Return the **pending list only** — resolved questions disappear from the list.
- Flag where an answer was ambiguous or incomplete (e.g. "yes" to a binary choice without picking a side).
- Group by feature area if it helps readability; flat list if short.

## Answering questions from the live Timbr Google Sheet
Much of the Timbr spec lives in a Google Sheet, not the PDF. When he asks "answer what we can from tab X":
- **Pull the live tab, never answer from memory.** Use the `gs.py` helper (`/home/hermes/gs.py`) — `gs.get("'Tab Name'")`, `gs.put(...)`, `gs.meta()` for tab list, `gs.gid(title)`. Sheet ID is hardcoded in it. Google OAuth (Sheets/Drive/Docs) is already provisioned — see `references/timbr-sheet-mechanics.md`.
- **Run integrity checks, don't just transcribe.** This session's win was checking the swap data: 150/150 alternates same-level ✓, but 7 crossed muscle groups and several level/muscle pools were too thin (<4) to guarantee a swap. Those findings were the value, not the summary.
- **Resolve his own inconsistencies against the source of truth.** His two chat messages disagreed on Core count (3 vs 2/day); the TRAINING SPLIT tab settled it. Always reconcile ambiguous inline claims against the sheet.
- **Separate answered from open crisply.** End with an explicit "the sheet does NOT answer these" list so nothing looks decided that isn't.
- See `references/timbr-sheet-mechanics.md` for the gs helper API, tab inventory, and the S1/S2/S3 classification formula.

## Design trade-off discussions
- Give a clear recommendation, not a menu of options.
- State the reasoning briefly — one or two sentences, not a paragraph.
- If a decision resolves an open question, flag it: "that also closes Q21 — want me to mark it?"
- Don't volunteer unsolicited feature ideas. Reason through what he raises.

## Pitfalls
- **Don't underclaim your own capability.** This session I twice hedged "I can't spin up a native Google Sheet / I'll build a CSV workaround" — when full Google OAuth (Sheets + Drive + Docs scopes) was already provisioned and working. Before saying "I can't do X with an external service," CHECK: read `~/Desktop/CREDENTIALS_MASTER.md`, `~/.hermes/vault.json`, and `~/.hermes/*creds*`. Offering a degraded workaround when the real capability exists wastes his trust. Default assumption: the access is probably there — verify before hedging.
- **Don't give a URL you haven't verified.** If asked for a product link, navigate to it first. Saying "https://pushband.com" without checking it = wasted trust.
- **Don't conflate data layers.** Wearable = session biometrics. Swipe cards / manual input = prescription compliance. They are complementary, not alternatives. Never frame them as an either/or.
- **Don't block on wearable availability.** "Wearable enriches, never gates" is the right principle for any fitness app MVP. Mainstream wearable penetration (~45–55% even in tech-forward cities like Seattle) means you always design for the non-wearable path first.
- **Don't over-answer on deferred features.** If something is explicitly out of MVP, note it and move on.

## Reference files
- `references/timbr-sheet-mechanics.md` — gs.py helper API, tab inventory, S1/S2/S3 formula, swap-data integrity findings, Google OAuth access note
- `references/timbr-wearable-architecture.md` — rep tracking technology landscape, wearable data proxy strategies, Seattle demographic data points
- `references/timbr-prd-open-questions.md` — running log of Timbr PRD open questions and resolution status
