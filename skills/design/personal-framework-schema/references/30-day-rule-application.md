# 30-Day Automation Rule: Application Patterns

## The Principle

**"If a recurring task can run autonomously in 30 days, design it out completely."**

This is the highest-impact principle in a personal framework because it eliminates recurring manual work entirely. It's non-negotiable.

## Key Insight

The 30-day window is not arbitrary—it's the sweet spot between:
- **Too short (<15 days):** Creates perfectionism, over-engineering
- **Too long (>60 days):** Keeps user stuck in manual execution, recurring pain point
- **Just right (20-30 days):** Achievable design effort that justifies elimination of recurring task

## Decision Tree

```
[User mentions recurring task]
        ↓
[Is this truly recurring?]
   YES           NO
    ↓             ↓
[Can estimate complexity?]  [Treat as one-time task]
   YES    NO
    ↓      ↓
[<30 days?] [Ask for clarification]
 YES   NO
  ↓     ↓
[DEPLOY] [Propose phased approach]
 FULL     OR hybrid model
 AUTO
```

## The Three Automation Pathways

### Pathway 1: Full Automation (≤30 Days)
**Condition:** Recurring task can be fully automated in ≤30 days

**Example:** Weekly status report compilation from Slack
- Complexity: 20 days (API integration, parsing, email trigger)
- Decision: FULL AUTOMATION
- Action:
  1. Design workflow (Slack API → parse → generate summary → email)
  2. Build and deploy immediately
  3. Set monitoring/alerts
  4. Document manual fallback
  5. Monitor for first month, then hands-off

**Result:** Zero future manual touches. Task disappears from user's recurring checklist.

### Pathway 2: Phased Automation (30-60 Days)
**Condition:** Recurring task requires >30 days of automation work

**Example:** Customer data synchronization across 3 systems
- Complexity: 45 days (API contracts, error handling, monitoring)
- Decision: PHASED APPROACH
- Action:
  1. Phase 1 (Days 1-15): Automate Tier 1 systems (80% of volume)
  2. Deploy Phase 1, gather learnings
  3. Phase 2 (Days 16-30): Add Tier 2 + edge cases
  4. Phase 3 (Days 31-45): Final Tier 3, full monitoring
  5. Move to hands-off after Phase 1 (don't wait for perfection)

**Result:** Automation ships in phases, recurring manual work reduced immediately by 80%, final polish later.

### Pathway 3: Hybrid Model (Requires Human Judgment)
**Condition:** Recurring task has decision points requiring human judgment

**Example:** Weekly prioritization of customer support tickets
- Complexity: Could automate 70% (auto-sort by urgency)
- Manual component: 30% (interpret ambiguous requests, business context)
- Decision: HYBRID
- Action:
  1. Automate what's deterministic (category, urgency scoring)
  2. Surface ambiguous cases for human decision
  3. Document decision rules for future refinement
  4. Plan transition to full automation if patterns emerge

**Result:** Manual effort reduced to 30%, scalable, with exit path to full automation.

## Execution Pattern: Full Automation Lifecycle

### Step 1: Scoping (2-3 hours)
- [ ] Understand the recurring task completely
- [ ] Map data flow (where does input come from? where does output go?)
- [ ] Identify edge cases (what can go wrong?)
- [ ] Estimate effort for each component
- [ ] Set target deployment date (before day 30)

**Red flags:**
- Scope keeps expanding during discussion (restate the scope, don't include nice-to-haves)
- Multiple stakeholders with conflicting requirements (nail down single source of truth)
- Unclear success criteria (define "what does success look like?")

### Step 2: Design (5-7 days)
- [ ] Create architecture diagram (input → processing → output)
- [ ] Specify data formats, APIs, integrations
- [ ] Document assumptions (what can we rely on?)
- [ ] Design error handling (what if API fails? what if data is missing?)
- [ ] Plan monitoring (how will we detect breakage?)

**Design quality checklist:**
- [ ] Can be implemented without further clarification
- [ ] Has explicit error handling
- [ ] Includes monitoring/alerts
- [ ] Has documented fallback (if automation fails, what's manual escape hatch?)
- [ ] Could be explained to another engineer

### Step 3: Implementation (10-15 days)
- [ ] Build core functionality
- [ ] Implement error handling and retries
- [ ] Add logging and monitoring
- [ ] Test with real data (not mock data)
- [ ] Document runbook (how to debug if something breaks?)

**Implementation checklist:**
- [ ] Works end-to-end without manual intervention
- [ ] Handles common failure modes gracefully
- [ ] Logs enough detail to debug issues
- [ ] Alerts trigger appropriately (not too noisy, not too silent)
- [ ] Runbook is clear and actionable

### Step 4: Deployment (1-2 days)
- [ ] Deploy to staging, validate against real environment
- [ ] Deploy to production with kill-switch readily available
- [ ] Monitor first 3 executions closely
- [ ] Verify output meets expectations

**Deployment checklist:**
- [ ] Staging validation complete
- [ ] Manual fallback tested and documented
- [ ] Alert channels configured
- [ ] Owner notified and trained
- [ ] Rollback plan documented

### Step 5: Monitoring (First 30 Days)
- [ ] Validate output quality after each run
- [ ] Track failure modes and fix them
- [ ] Refine alerts (reduce false positives)
- [ ] Document any manual overrides (did anyone need to intervene?)
- [ ] Adjust schedule if needed (is 5pm the right time?)

**Monitoring checklist:**
- [ ] Zero or near-zero manual intervention needed
- [ ] Failures detected and alerted on
- [ ] Output quality consistent
- [ ] Performance acceptable (runs in reasonable time)
- [ ] Owner confidence high

### Step 6: Handoff to Hands-Off (Day 30+)
- [ ] Reduce monitoring frequency (weekly checks → monthly)
- [ ] Owner can ignore the task completely (it just runs)
- [ ] Automation proven reliable over 4+ execution cycles
- [ ] Document and declare success

## Antipatterns: When to Reject the 30-Day Rule

The rule does NOT apply to:

### Antipattern 1: Task is not actually recurring
```
❌ "I need this report once a quarter"
✓ Reject: Not recurring often enough to justify automation. Revisit if pattern emerges.
```

### Antipattern 2: Task requires fundamental business process change
```
❌ "Automate our CRM data cleanup" (but CRM schema is fundamentally broken)
✓ Reject: Fix the root cause first. Automation will perpetuate the problem.
```

### Antipattern 3: Task has unclarified requirements
```
❌ User says: "I need a weekly report. I'll tell you what to include when you show me the first one."
✓ Reject: Design requires clarity. Get requirements locked before committing to automation.
```

### Antipattern 4: User hasn't confirmed they actually want automation
```
❌ Agent assumes: "This would be better automated"
✓ Reject: Ask first. Some tasks serve a purpose (e.g., forcing a weekly review), automation would eliminate the value.
```

## Cost-Benefit Analysis

Use this to decide whether automation is worth it.

```
Automation Value = (Time_saved_per_run × Runs_per_year × Cost_of_time) - Automation_design_cost

Example:
- Time per manual execution: 15 minutes
- Frequency: Every Friday (52 times/year)
- Cost of time: $150/hour
- Automation design cost: 25 days × 8 hours × $150/hour = $30,000

Manual cost per year: (15/60) × 52 × $150 = $1,950
Automation ROI breakeven: $30,000 / $1,950 = 15.4 years

For lower-cost labor or more frequent tasks:
- If frequency: Weekly (52x), time: 30 min, cost: $50/hr
  Annual cost: (30/60) × 52 × $50 = $1,300
  Breakeven: $30,000 / $1,300 = 23 years (unlikely)

- If frequency: Daily (260x), time: 5 min, cost: $150/hr  
  Annual cost: (5/60) × 260 × $150 = $3,250
  Breakeven: $30,000 / $3,250 = 9.2 years (possible)
```

**Rule of thumb:** If annual manual cost exceeds $2,000-3,000 OR frequency is >weekly, automation ROI is strong within 10 years.

## Examples of Well-Applied 30-Day Rule

### Example 1: Weekly Status Reports
- **Recurrence:** Every Friday 5pm
- **Effort:** 20 days (Slack API + parsing + email)
- **Result:** Full automation, zero manual touches
- **Success:** Runs reliably every week, no user attention needed

### Example 2: Monthly Reconciliation Report
- **Recurrence:** First day of each month
- **Effort:** 15 days (query 3 systems, compare, flag discrepancies)
- **Result:** Full automation with human review for >$5k discrepancies
- **Success:** 95% auto-resolved, 5% escalated for review

### Example 3: Daily Backup Validation
- **Recurrence:** Daily 2am
- **Effort:** 8 days (check backup completeness, send alerts)
- **Result:** Full automation with Slack alert on failure
- **Success:** Detects backup failures within 1 hour, team alerted automatically

## Testing the Rule

After deployment, ask:
1. **Did automation happen?** (Is the task no longer manual?)
2. **Is it reliable?** (Does it work >95% of the time?)
3. **Is maintenance minimal?** (Less than 30 min/month?)
4. **Did it save time?** (Has the user actually been freed from this task?)

If all four: Rule successfully applied. Celebrate and move on.
If not: Diagnose and fix the automation (don't revert to manual).

## Key Insight

**The 30-Day Rule is not about creating perfect automation—it's about eliminating recurring manual work.**

An 80/20 automation that runs every week and saves 15 minutes each time is a win. You don't need to build the perfect system; you need to build something that works reliably and removes the task from the user's mental queue.

The cost of rework on 10% of executions is almost always less than the cost of manual execution on 100% of tasks.
