---
name: operational-protocols
description: Store, retrieve, distinguish, and execute deployment protocols with precision. Prevent cross-contamination between distinct protocols.
type: class
trigger: User says "deploy [protocol-name]", references an existing protocol, or defines a new one.
---

# Operational Protocols

## Overview
Operational protocols are standardized deployment templates for recurring, complex, or high-stakes tasks. They live in **hindsight** (semantic search, persistent, tagged for distinction) and must be:
- **Clearly named** at the protocol level (not feature names or task codes)
- **Tagged distinctly** to prevent bleed-through in search/recall
- **Executed immediately** when invoked, without confirmation menu or preamble
- **Distinct from similar-named concepts** (e.g., Protocol Veronica ≠ IG-1 Protocol — one is a deployment standard, the other is a scraper)

## Storage Pattern

Each protocol lives in hindsight with:
1. **Distinct context tag**: e.g., `"context": "operational protocol - CRITICAL DISTINCTION"`
2. **Explicit NOT tags**: e.g., `"tags": ["protocol-veronica-ONLY", "not-ig1", "distinct-protocol"]`
3. **Clear purpose statement**: What triggers it, when to use it, what it deploys

Example:
```
Protocol Veronica — DISTINCT FROM IG-1 Protocol

Deployment standard for complex/high-stakes tasks:
1. Deploy latest Claude Opus model for primary task execution
2. Deploy 2–3 subagents in parallel if needed to scale work or isolate concerns
3. Two-level quality check at task end by default (review layer 1, then review layer 2)

Use case: task complexity warrants model upgrade, work parallelization, or high confidence threshold needed.

Execution: When user says "deploy veronica", execute immediately without preamble, confirmation menu, or options. Full protocol runs as stated above.

DO NOT CONFUSE with IG-1 Protocol (Instagram crawler) — they are separate operational protocols.
```

## Retrieval & Verification

**CRITICAL RULE:** Never claim to know a protocol without verifying it in hindsight first.

When user references a protocol:
1. **Search hindsight** immediately: `hindsight_recall(query="Protocol [name]")`
2. **Verify the result** against what you claim to know
3. **If unsure or conflicted**, say so explicitly: *"Let me pull that from memory to be sure"* — then search
4. **Never guess** on protocol details, even if the name is familiar

Pitfall from Jun 6, 2026: User asked "Did you understand Protocol Veronica?" and I said yes without searching. I was wrong — I'd conflated Veronica (Opus + subagent deployment standard) with IG-1 (Instagram scraper). Searching hindsight would have caught it immediately. **Always verify before claiming understanding.**

## Execution Pattern

When invoked with "deploy [protocol-name]":
1. **No preamble.** No "Understood", no "Got it", no setup questions.
2. **State the action in one line** if not already clear: `"Spinning up Opus + 2 subagents, two-level QC at the end."`
3. **Execute immediately.** Run the protocol as stated.
4. **Report after.** One line: what happened, what's done, what's next (if applicable).

Example:
```
User: "deploy veronica"
You: "Running Protocol Veronica — Opus primary task, 2 subagents, two-level QC."
[execute immediately]
You: "Opus task complete. Layer 1 QC done. Layer 2 review: [brief result]. Ready?"
```

## Distinction Rules

If two protocols share similar names or overlapping purposes:
- **Tag both explicitly** with "NOT-[othername]" to prevent hindsight bleed
- **State the difference in the body** (one sentence, crystal clear)
- **Use different context tags** (e.g., "operational protocol - Opus deployment" vs. "operational protocol - Instagram crawler")

## References
- See `references/protocol-veronica.md` for Protocol Veronica deployment details
- See `references/ig1-protocol.md` for IG-1 Protocol distinction notes
