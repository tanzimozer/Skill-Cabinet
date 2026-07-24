# Hindsight Architecture & Query Patterns

## Semantic Layer Design

Hindsight is a searchable, unlimited narrative context store. Unlike memory (fast, finite), hindsight can absorb large historical context without ceiling constraints. Cost: queries are ~500–1000ms slower due to semantic search.

## Entry Structure

Each hindsight_retain() call should be:
- **Coherent & standalone:** One entry = one topic (job search pipeline, team patterns, architecture decision, etc.)
- **Rich with context:** Include *why*, not just *what*. An entry like "JPMC offer rescinded May 29. Now targeting AI implementation roles" is better than "job search active".
- **Tagged:** Include 3–5 tags for semantic cross-linking (e.g., `["job-search", "employment", "pipeline"]`).
- **Contextual:** Mention the date, the decision point, or the reason for the change.

Example from Jun 2026 session:
```
hindsight_retain(
  content="Job search pipeline (Jun 2026): JPMC declined — offer rescinded May 29. Currently targeting AI implementation, PM, org-efficiency roles. Active: Foundation AI (Customer Success/Solutions Manager, Serbhi.b@foundationai.com, rescheduled Jun 3), Fluxx Labs (Technical Software Implementation Specialist, Jun 8 11:00am PT, Christina.Muhammad@fluxxlabs.com, Zoom), Salesforce TSE blocked (US citizen req + Apex/LWC depth). Gmail label "JPMC" created, 23 emails moved to label (not hard-deleted per Tanzim's preference).",
  context="job search history",
  tags=["job-search", "employment", "pipeline"]
)
```

## Query Patterns for Future Sessions

When a user asks a recall question, the agent should:

1. **Check memory first** (instant).
2. **Check session_search** (same-session context, faster than hindsight).
3. **Query hindsight_recall()** with a semantic probe if neither returns the answer.

Example semantic probes for Tanzim's hindsight archive:
- "job search pipeline decisions" → returns job search entry
- "team dynamics and work patterns" → returns team entry
- "Instagram crawler strategy" → returns IG-1 protocol entry
- "TIMBR site architecture decisions" → returns Webflow/Wix entry
- "API throttling lessons" → returns API lessons entry

## Cost-Benefit

**Hindsight is worth it if:**
- Query frequency < 1x per session (rare)
- Context size > 500 chars (dense)
- Semantic search is better than grep (narrative, contextual, "why" questions)

**Keep in memory if:**
- Query frequency ≥ 3x per session (frequent)
- Context size < 200 chars (tiny facts)
- Exact match is sufficient (IDs, credentials, names)

## Latency Profile

- Memory query: ~0ms (injected at startup)
- Session_search: ~100–300ms (grep-like, full-text indexed)
- Hindsight_recall(): ~500–1000ms (semantic embedding + vector search)

For a user walking through Pike Place asking tactical questions, hindsight adds noticeable lag. For an off-hours review of architecture decisions, hindsight is imperceptible.

## Integration with User Protocols

Friday's recall protocol for Tanzim:
- Memory holds IDs, credentials, team contacts, security rules, current project state
- Session_search is the first fallback for "did you/remember/we discussed"
- Hindsight_recall() is the second fallback for deeper narrative context ("why did we", "what was the reasoning")

This matches Tanzim's direct, fast-paced communication style — memory answers first, hindsight answers second, only if needed.
