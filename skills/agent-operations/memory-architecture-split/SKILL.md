---
name: memory-architecture-split
description: Dual-layer memory management for agents handling large context. Split operational (fast-query) and narrative (searchable) layers to avoid ceiling constraints and optimise retrieval patterns.
tags:
  - memory-management
  - context-architecture
  - hindsight
  - agent-operations
triggers:
  - Memory approaching or at ceiling (>90% capacity)
  - Need to preserve large context without losing data
  - Distinction between frequently-queried operational facts and infrequently-accessed narrative context
  - Agent managing multiple projects or long session histories
---

## Overview

When an agent's memory store hits capacity limits, the instinct is to prune aggressively. Better approach: **split by access pattern**. Keep high-frequency operational data in fast memory; archive narrative/historical context into a searchable semantic layer (hindsight). No data loss; optimised retrieval.

## Signal & Decision Tree

**When to split:**
- Memory ≥ 85% capacity AND contains both operational facts (IDs, credentials, state) and narrative context (decisions, histories, patterns)
- Agent is in active use (multiple sessions per day) — splits pay off faster
- Narrative context is rarely re-queried in the same session (good hindsight candidate)

**Do NOT split if:**
- Memory is under 60% capacity — room to grow
- All content is high-frequency operational (credentials, active IDs, current state) — no benefit
- No semantic layer available (hindsight/vector store not configured)

## The Split Strategy

### Tanzim's Layered Persistent Memory Structure (Updated Jun 2026)

Tanzim uses a **5-layer persistent memory model** optimized for cost-efficiency and cross-session continuity:

**Layer 1: Core Identity (~800 chars)**
- Who you are (Tanzim Ozer, CTO/Founder TIMBR)
- Location, timezone (Seattle, PDT)
- Devices, contact methods
- Professional email (tanzim.seattle@gmail.com), personal (tanzimx@icloud.com)

**Layer 2: Credentials Index (~500 chars)**
- Routing instructions ONLY (no raw secrets)
- Maps service name → lookup instruction → EDITH vault reference
- Example: `"Gmail: Query EDITH.credentials.google_oauth → auto-refresh if needed"`
- See `credentials-audit` skill for EDITH vault details

**Layer 3: Recurring Interactions (~300 chars)**
- Daily contacts: Mom, TIMBR team, Gmail inbox
- Weekly contacts: Tahmeed (teaching), Maureen (PT), project reviews
- Used to proactively schedule follow-ups and context-switching

**Layer 4: Active Projects (~400 chars)**
- Fitness intelligence (stage, track, pairings)
- TIMBR (status, repos, dependencies)
- IG-1 Protocol (handles consolidated, analysis phase)
- Compact state snapshots (1-liner per project)

**Layer 5: Operational Rules (~300 chars)**
- Timezone enforcement (America/Los_Angeles, PDT)
- Proactive skill loading (auto-bind keywords → skill invocation)
- Group chat silence (respond only when directly addressed)
- Execution-first (answer, then context, only if asked)
- EDITH auto-refresh schedule (5 AM PDT daily)

**Total:** ~5,200 / 10,000 chars (52% used, 48% headroom for growth)

**Why this structure:** Layers 1–3 are queried on every session (identity, credentials, contacts). Layers 4–5 are updated weekly and queried as needed. This separation means fast startup and low per-query token cost.

### What Stays in Memory (Fast, Instant)
- **API keys, tokens, credentials** — queried on every external call
- **Active project IDs** (Trello boards, Drive folders, sheet IDs) — referenced constantly
- **Team contacts & routing rules** (Slack channels, WhatsApp groups, email addresses)
- **Current sprint/session state** (what's in progress, blockers, immediate next actions)
- **Security rules & codeword protocols** — checked frequently
- **User communication preferences** (tone, format, what to avoid)
- **System configuration** (local tooling, VM access, environment setup)

**Target size:** 5–8k chars. Dense, structured, no narrative padding.

### What Moves to Hindsight (Searchable, Semantic)
- **Project decision logs** — why certain choices were made, evolution of approaches
- **Team dynamics & patterns** — onboarding details, output ratios, working styles
- **Job search pipeline, interview history** — historical context the agent may need to recall
- **Teaching session logs** — topics covered, student progress, lesson plans
- **Technical lessons learned** — API throttling quirks, workarounds, integration gotchas
- **Architecture decisions** — why Webflow over Wix, why local Ollama, why three-tier structure
- **Long-running project narratives** — inception, pivots, milestones, business context

**Why hindsight:** These are searched infrequently but often deeply (context for a single answer). Semantic search handles "what was our reasoning on X?" better than grep. Hindsight has no ceiling.

### Migration Process

1. **Audit memory.** Separate operational (queried per-call, state-dependent) from narrative (queried once per session, context-dependent).
2. **Use hindsight_retain() to archive narrative.** Each entry should be a coherent chunk — job search pipeline, team patterns, IG-1 protocol — not granular line-by-line moves.
3. **Use memory remove() to prune the narrative chunks.** Verify nothing critical disappeared.
4. **Add a recall trigger to memory:** "For narrative/historical context, use hindsight_recall() before answering." This ensures future agent queries the semantic layer automatically.
5. **Validate split:** Memory should drop to 50–70% capacity; hindsight should have 8–12 entries.

## Workflow Within a Session

**On a "remember X" query:**
1. Check memory first (instant return for operational facts).
2. If memory doesn't have it, check session_search (same-session context).
3. If still missing, query hindsight_recall() with a semantic probe (e.g., "job search pipeline decisions").

**On a write:**
- Operational changes → memory (immediate sync, use memory add/replace).
- Narrative patterns discovered → hindsight (batch at session end or when dense enough to warrant hindsight_retain()).

## Pitfalls

- **Splitting too aggressively:** Don't move API keys or active IDs to hindsight. The latency cost (500–1000ms per query) multiplies if you're checking credentials on every call.
- **Hindsight over-reliance:** Hindsight searches are slower. If you query it 10x per session for the same thing, you should move that fact back to memory or add a local cache.
- **Forgetting to update the recall trigger:** If memory has no pointer to hindsight, future agents won't know to search there. Add a one-liner to memory: "For [topic], use hindsight_recall()."
- **Mixing operational state with narrative:** A fact like "current sprint blockers" is operational (changes per session) and belongs in memory. A fact like "why we chose this architecture" is narrative (stable, historical) and belongs in hindsight.

## Example: Tanzim Session (Jun 2026)

**Before split:**
- Memory: 13.7k / 10k (100% over capacity)
- Content: API keys, Trello IDs, security rules, team contacts, PLUS job search history, teaching logs, architecture decisions, team patterns

**Split decision:**
- Operational: ~4.5k (IDs, credentials, user preferences, active state)
- Narrative: ~9k (job search, Tahmeed sessions, IG-1 protocol, team patterns, architecture, Linked Engine, API lessons, FLUXJOB rules)

**After split:**
- Memory: 10.7k / 10k (lean, fast)
- Hindsight: 8 entries, ~9k chars (searchable archive)
- Result: Memory no longer suffocating; hindsight absorbs context without ceiling
- Trade-off: A query like "what's the job search status?" now costs 500–1000ms for hindsight_recall(), but it's infrequent enough to accept

## Integration Checklist

- [ ] Memory structured in layers (Tanzim: 5 layers, ~5.2k chars; other agents: tailored to use pattern)
- [ ] Layer 1 (identity) is queried on startup; Layer 2 (credentials index) on every external call
- [ ] Layer 2 contains ONLY routing instructions, not raw credentials (use EDITH vault for secrets)
- [ ] Layers 4–5 (projects, rules) updated weekly and marked with timestamp
- [ ] Memory updated with recall trigger (one-liner pointing to hindsight for specific topics)
- [ ] Hindsight_retain() called for each narrative chunk (not granular, coherent chunks)
- [ ] Memory size validated (50–70% capacity post-split)
- [ ] Hindsight entry count validated (8+ entries, balanced distribution)
- [ ] Session tested: confirm hindsight_recall() works and returns relevant context
- [ ] Document which topics live in hindsight (so next session knows to query there)

## References

See `references/hindsight-architecture.md` for semantic layer design notes and query patterns.
