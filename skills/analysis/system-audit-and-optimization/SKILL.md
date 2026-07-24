---
name: system-audit-and-optimization
type: procedure
description: >
  Comprehensive system auditing and optimization delivery, from problem identification
  through phased implementation. Produces multi-layered documentation suitable for
  decision-makers, architects, and developers. Includes executable tooling for
  ongoing monitoring.
trigger: |
  - "audit [system/architecture/performance]"
  - "identify bottlenecks/inefficiencies in [system]"
  - "optimize [component/layer/service]"
  - "what are the issues in [system]"
  - User requests comprehensive system analysis with recommendations and implementation path
prerequisites:
  - System/codebase access (read config, code, runtime state)
  - Understanding of system layers/architecture
  - Ability to trace data flows and dependencies
---

## Core Pattern: Four-Document Deliverable

A system audit produces FOUR primary documents serving different audiences:

1. **Executive Brief** (5-10 min read)
   - Decision-maker audience (project manager, leadership)
   - Key findings per layer/component
   - Quantified issues (bottlenecks, redundancies)
   - Phased optimization roadmap with timelines
   - Performance projections (before/after)
   - High-level risk/effort assessment
   - Clear recommendation (proceed/redesign/hold)

2. **Technical Deep-Dive** (30-45 min read)
   - Architect/senior engineer audience
   - Layer-by-layer audit results with data flow diagrams
   - Detailed bottleneck analysis (4-5 scenarios each)
   - Redundancy breakdown with examples
   - Complete optimization recommendations
   - Cross-component impact analysis
   - Phase-by-phase timeline with success criteria

3. **Implementation Guide** (copy-paste ready code)
   - Developer audience
   - Complete Python/language-specific code examples
   - Before/after comparisons
   - Testing checklist for each optimization
   - Risk assessment per change
   - Integration points and dependencies
   - Monitoring/metrics setup
   - Rollout sequence

4. **Machine-Readable Raw Data** (JSON/structured)
   - Programmatic access to audit results
   - Metrics, findings, recommendations
   - For dashboard integration, automated tracking
   - Baseline for comparing future audits

PLUS: **Executable Audit Tool**
   - Python/shell script that generates all data
   - Re-runnable for ongoing monitoring
   - Tracks progress through optimization phases

## Phased Optimization Structure

When audit identifies multiple improvements, organize as PHASES:

- **Phase 1** (QUICK WINS): 2-3 hours effort, 30-40% improvement
  - Low risk (config changes, schema additions)
  - Immediate impact on user experience
  - Reversible in minutes
  - Deploy within 1 week

- **Phase 2** (MEDIUM IMPROVEMENTS): 4-5 hours, 50-60% improvement
  - Low-to-medium risk (new data stores, non-destructive changes)
  - Significant storage/API optimization
  - Requires backup before deploy
  - Deploy week 2

- **Phase 3** (STRATEGIC): 6-8 hours, 3-4x total improvement
  - Medium risk (refactoring, new architectural patterns)
  - End-to-end performance transformations
  - Requires extensive testing
  - Deploy week 3

- **Phase 4** (ONGOING): Maintenance, 1-2 hours
  - Deduplication, cleanup, monitoring
  - Low risk continuous improvements

Each phase must include:
- Specific effort estimate (hours)
- Performance improvement % or multiplier
- Risk level (LOW/MEDIUM/HIGH)
- Deployment timeline
- Rollback procedure
- Success metrics

## Code Example Standards

For each optimization, provide:

```
### Code: OPT-N - [Name]

**File: [path]**

BEFORE (current):
```python
# Current implementation showing the inefficiency
```

AFTER (optimized):
```python
# Optimized version with inline comments
# Highlight key changes in behavior, not just syntax
```

**Config/Integration:**
```yaml
# Any config changes, env vars, setup needed
```

**Testing Checklist:**
- [ ] Specific assertion/test (do NOT use vague "it works")
- [ ] Rollback procedure works
- [ ] No performance regression in other areas
- [ ] Metrics improve as projected

**Risk: [LOW/MEDIUM/HIGH]**
**Rollback: [procedure in 1-2 sentences]**
```

## Data Flow Analysis Pattern

For system audits:

1. **Identify the three types of data movement**:
   - Request path (user input → processing → response)
   - Persistence path (state → storage → retrieval)
   - Cross-layer routing (when data moves between layers)

2. **For each path, measure**:
   - Latency (wall-clock time)
   - Cache hit rate (if caching present)
   - Redundant copies / duplication
   - Serialization overhead
   - Authentication/gating overhead

3. **Bottlenecks emerge from**:
   - Sequential operations that could parallelize
   - Fetches that could be cached or prefetched
   - Round-trips that could batch
   - Redundant work done multiple times
   - Gates (auth, validation) that repeat unnecessarily

4. **Redundancies emerge from**:
   - Same data stored in multiple places
   - Same computation done at different layers
   - Duplicate extraction/parsing of source data
   - Preferences/config scattered across stores

## Metric Tracking

Create a matrix showing:

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Latency (ms) | 1000 | 100 | Wall-clock measure |
| Cache hit rate | 10% | 80% | Instrumentation |
| Storage (MB) | 150 | 30 | Disk usage |
| API calls/day | 200 | 80 | Log analysis |

Include in both Executive Brief and Implementation Guide.
Success measurement at end of each phase by re-running metrics.

## Rollout Strategy

Standard three-track approach:

**Decision Path** (Days 1-2):
- Stakeholders review Executive Brief
- Approve Phase 1 (always low-risk, proceed unless blocked)
- Conditional approval for Phase 2-3 based on Phase 1 results

**Implementation Path** (Weeks 1-3):
- Week 1: Phase 1 (quick wins, fast feedback)
- Week 2: Phase 2 (monitor metrics, gather feedback)
- Week 3: Phase 3 (largest effort, highest reward)
- Ongoing: Phase 4 maintenance

**Validation Path** (After each phase):
- Run testing checklist from Implementation Guide
- Re-execute audit tool to confirm metrics
- Compare before/after in machine-readable report
- Gather user/team feedback

## Red Flags to Avoid

- ❌ Recommending "redesign everything" without phased path
- ❌ Mixing architectural issues with optimization issues
- ❌ Providing recommendations without effort/cost estimates
- ❌ Code examples that require multiple files to understand
- ❌ Testing checklists that are vague ("test it", "validate")
- ❌ Performance claims without baseline measurement
- ❌ Ignoring security implications of optimizations

## When to Recommend HOLD (Not Proceed)

Recommend holding optimization if:
1. System is already performing well (no clear bottlenecks)
2. Proposed optimizations introduce significant risk for marginal gain (<20%)
3. Architectural redesign is needed (recommend that separately)
4. Org is in flux (staff changes, migration planned)
5. System is being replaced soon

When recommending HOLD, provide:
- Clear metrics showing current state is acceptable
- What conditions would trigger re-evaluation
- What to monitor in the meantime

---

## Templates

See `templates/audit-deliverable-structure.md` for document outline boilerplate.
See `references/phased-optimization-examples.md` for real-world phase breakdowns.
See `references/safe-cleanup-and-dedup-execution.md` for the Phase-4 cleanup/teardown workflow: archive-not-delete, redundant-repo proof, service-store consolidation via API (Hindsight), and core-memory pruning — all under the "don't break configs/rules, don't lose history" constraint.
See `scripts/audit-template.py` for executable audit scaffold.
