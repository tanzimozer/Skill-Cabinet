# Cost Audit Diagnostic Checklist

Run this to establish baseline spending before applying cost-efficiency upgrades.

## Token Leak Sources

### 1. Cold Start Penalty
- **How to measure:** Log token count at session start (before any user query) vs. after system prompt injected
- **Baseline:** If > 150 tokens injected before first user query, you have cold-start bloat
- **Savings potential:** Compressed snapshots (Upgrade 1) can eliminate this

```
Expected baseline: ~50 tokens (system prompt + agent metadata)
Your baseline: ___ tokens
Gap (savings opportunity): ___ tokens
Monthly impact (3 sessions/day): ___ tokens/month
```

### 2. Skill Re-Loading
- **How to measure:** Enable logging in skill_view() calls; count tokens per call
- **Baseline:** Each skill definition costs ~50-80 tokens (definition + context)
- **Savings potential:** Skill index pre-binding (Upgrade 2) eliminates re-definition load

```
Skills used daily: ___
Skills used 3+ times/day: ___
Average tokens per skill load: ~70 tokens
Daily waste (skills × 3 invocations × 70 tokens): ___ tokens/day
Monthly impact: ___ tokens/month
```

### 3. Credential Access Overhead
- **How to measure:** Trace one Google OAuth lookup; count: disk_read + JSON_parse + token_validation + auto_refresh_check
- **Baseline:** Full credential lookup typically costs 100-150 tokens (disk I/O, parsing, validation)
- **Savings potential:** EDITH fast-path (Upgrade 4) cuts this to ~30-40 tokens

```
Credential lookups/day: ___
Tokens per lookup (before): ~130 tokens
Tokens per lookup (after EDITH): ~35 tokens
Daily savings: ___ × 95 tokens = ___ tokens/day
Monthly impact: ___ tokens/month
```

### 4. Browser Vision Repeats
- **How to measure:** Count browser_vision() calls on the same URL/page
- **Baseline:** Vision analysis costs ~150 tokens per call
- **Savings potential:** Browser cache (Upgrade 3) replaces with ~30-token snapshot on cache hit

```
Browser tasks/week: ___
Average repeats per page: 2-3
Vision calls avoided/week (est): ___ × 2 = ___ calls
Tokens per vision call avoided: ~120 tokens
Weekly savings: ___ × 120 = ___ tokens
Monthly impact (4 weeks): ___ tokens/month
```

### 5. Memory Retrieval Overhead
- **How to measure:** Time hindsight_recall() queries; they cost ~50-100 tokens per query
- **Baseline:** If querying hindsight 3+ times per session for the same thing, it's overhead
- **Savings potential:** Fast-path memory layer (Upgrade 1) moves frequent data back to fast memory

```
Hindsight queries/session: ___
Queries that could be in fast memory (operational, not narrative): ___
Tokens saved per query moved to memory: ~60 tokens
Queries/month: ___ × ~60 = ___ tokens/month
```

## Summary Template

```
COST AUDIT — Before Upgrades
Date: ___
System: ___ (agent name)
Baseline monthly tokens: ~___ (extrapolate from daily spend)
Baseline monthly cost: ~$___ (at $0.0006/1K tokens)

Leak source breakdown:
  • Cold start: ___ tokens/month
  • Skill re-loading: ___ tokens/month
  • Credential access: ___ tokens/month
  • Browser vision: ___ tokens/month
  • Memory overhead: ___ tokens/month
  ──────────────────────────────
  TOTAL WASTE: ___ tokens/month (~$___ cost)

Upgrades to apply (in order):
  [ ] EDITH fast-path (Upgrade 4) — estimated savings: ___ tokens/month
  [ ] Compressed snapshots (Upgrade 1) — estimated savings: ___ tokens/month
  [ ] Skill index (Upgrade 2) — estimated savings: ___ tokens/month
  [ ] Auto-binding (Upgrade 5) — estimated savings: ___ tokens/month
  [ ] Browser cache (Upgrade 3) — estimated savings: ___ tokens/month

Projected savings: ___ tokens/month (~___ % reduction, cost: $___/month)
```

## Validation Checklist (Post-Deployment)

Run this 2 weeks after deploying upgrades to confirm cost reduction:

- [ ] Measure actual monthly tokens (2 weeks × 2 = 1 month estimate)
- [ ] Compare to pre-upgrade baseline
- [ ] If savings < 60% of projected, debug which upgrade failed (check logs)
- [ ] If savings > 90%, validate cache hit rates aren't inflated (rerun on new data)
- [ ] Set up ongoing monthly tracking (spreadsheet or alert)
- [ ] Schedule quarterly review to re-baseline (services change, new skills added, etc.)
