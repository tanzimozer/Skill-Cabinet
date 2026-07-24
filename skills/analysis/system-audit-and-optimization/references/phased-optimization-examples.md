# Phased Optimization Examples

## Pattern: Friday 2.0 Memory Routing (Real Session)

**Context**: Three-layer memory system (Vault/Memory/Hindsight) had efficiency problems.

### Phase 1: Quick Wins (2-3 hours, +30-40%)

**OPT-2: Extend Credential Cache TTL**
- **Change**: 5 minutes → 30 minutes
- **Why**: Vault time-gating too aggressive; users re-authenticate frequently
- **Code effort**: ~50 lines, one config file
- **Risk**: LOW (cache expiry is still enforced, just longer)
- **Rollback**: Revert config, restart service
- **Metric**: Auth prompts/session drops 80%

**OPT-3: Add Routing Hints to Messages**
- **Change**: Add `routing_target` field to message schema
- **Why**: Router spends 5-20ms per message guessing where to send data
- **Code effort**: ~80 lines (schema + classifier)
- **Risk**: LOW (schema addition is backwards compatible)
- **Rollback**: Ignore field in old code, no data loss
- **Metric**: Routing decision latency 5x faster

**Deployment**: Both can ship together day 1, measure over 48 hours.

---

### Phase 2: Medium Improvements (4-5 hours, +50-60%)

**OPT-1: Session Archival**
- **Change**: Move sessions >90 days old to archive DB
- **Why**: sessions.db grew to 150 MB, searches slow down
- **Code effort**: ~150 lines (new methods), 1 hour testing
- **Risk**: LOW (archival is non-destructive, dual-DB search works)
- **Rollback**: Keep archive.db, revert main DB from backup
- **Metric**: sessions.db 80% smaller, FTS searches 10x faster

**OPT-6: Lazy-load Hindsight**
- **Change**: Stop auto-fetching Hindsight on session init; only fetch on explicit recall
- **Why**: Many sessions never ask for long-term context; we were burning API calls
- **Code effort**: ~60 lines (remove auto-fetch, add explicit recall with cache)
- **Risk**: LOW (sessions still work, context just comes on-demand)
- **Rollback**: Add auto-fetch back, clear cache
- **Metric**: Hindsight API calls -60%, session startup faster

**Deployment**: Run OPT-1 with backup, then OPT-6. Measure over 1 week.

---

### Phase 3: Strategic (6-8 hours, 3-4x total)

**OPT-4: Session Context Prefetch**
- **Change**: Async prefetch Hindsight contexts at end of session; inject on next session start
- **Why**: Cross-chat startup was 1000+ ms because loading context is sequential
- **Code effort**: ~130 lines (lifecycle hooks, async fetch, TTL cache)
- **Risk**: MEDIUM (async patterns, need error handling if prefetch fails)
- **Rollback**: Remove async hooks, context loads on-demand again (original behavior)
- **Metric**: Cross-chat startup 10x faster (1000ms → 100ms)

**OPT-5: Unified Credential Provider**
- **Change**: Credential access through single interface (decorator pattern: Vault → Cache → ErrorHandler)
- **Why**: Credential access scattered, duplication high, hard to add caching tier
- **Code effort**: ~200 lines (abstraction + 3 layers), refactor all credential uses (3-4 hours)
- **Risk**: MEDIUM (refactoring touches many callsites)
- **Rollback**: Revert to direct vault calls, no data loss
- **Metric**: Cleaner code, enables caching, fewer auth prompts

**Deployment**: OPT-4 first (lower risk), then OPT-5. Extensive testing in staging. 1 week total.

---

## Pattern: When to Break Phases

**If optimizations depend on each other** → they can be same phase (e.g., OPT-4 and OPT-5 both touch session/credential flows).

**If a phase grows >8 hours** → split it. Original Phase 3 was 6-8 hours; if it hit 12+ hours, move OPT-5 to its own Phase 3b.

**If risk multiplies** → separate. Two MEDIUM-risk changes in one phase can amplify unknowns; sequence them.

---

## Metrics to Track Per Phase

| Phase | Baseline | Target | How to Measure |
|-------|----------|--------|----------------|
| Phase 1 | Auth prompts: 20/session | 18/session | Logs (drop should be visible) |
| Phase 1 | Router latency: 5-20ms | 1-2ms | Instrumentation at router entry/exit |
| Phase 2 | sessions.db: 150 MB | 30 MB | Disk usage after archival job |
| Phase 2 | Hindsight API calls: 200/day | 80/day | API logs, request counts |
| Phase 3 | Cross-chat startup: 1000ms | 100ms | Wall-clock measure in test |
| Phase 3 | Cache hit rate: 10% | 80% | Counter in credential provider |

---

## Risk Tiers Explained

**LOW**: Change is additive (new field, new config), easily undone, no existing data touched.
- Rollback: Config change, code revert, restart.
- Testing: Basic happy path + rollback test.

**MEDIUM**: Change touches existing data paths or async behavior, but is non-destructive.
- Rollback: Data restore from backup (if store changed), code revert.
- Testing: Full test suite, staging validation, 24h monitoring post-deploy.

**HIGH**: Change requires data migration, touches critical paths, or is hard to undo.
- Rollback: May require restore + replay of missed writes; users affected.
- Testing: Extensive staging, A/B test if possible, on-call ready.
- Recommendation: Phase HIGH changes after LOW/MEDIUM succeed.

Friday 2.0 audit avoided HIGH-risk changes entirely; all recommendations are LOW or MEDIUM.
