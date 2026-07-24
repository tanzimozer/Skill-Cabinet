# Execution-First Pattern (Tanzim Preference)

## Signal & Correction

User: "Why is it taking weeks? Why don't you build it now?"

This rejects the **phased-design** approach in favor of **immediate execution**.

## Correct Pattern

### ❌ Anti-Pattern (What I was doing)
```
Proposed approach:
- Phase 1: Design EDITH (1 week)
- Phase 2: Integrate framework (1 week)
- Phase 3: Clean up skills (1 week)
- Phase 4: Test (1 week)
Result: Four PDFs with timelines, pending approval
User reaction: "Why weeks? Build now."
```

### ✓ Correct Pattern
```
User: "Build Friday 2.0"
Agent:
1. Validate assumptions (30 sec)
2. Code EDITH vault (5 min) → test → live
3. Codify framework rules (5 min) → test → live
4. Set up credentials backup (5 min) → live
5. Report: "Live. Here's what was deployed."
User: Sees working system, can iterate
```

## Key Principle

**Execution beats planning.** Even if the design is incomplete, a working system with known limitations beats a perfect design that doesn't exist yet.

- Don't ask for permission to proceed through phases
- Don't wait for design sign-off
- Build incrementally, not speculatively
- Report results, not timelines

## Implementation Notes

- When user says "build X," assume execution-first
- No multi-week timelines unless explicitly requested
- Deploy immediately if technically possible
- Iterate on live work, not on design docs
