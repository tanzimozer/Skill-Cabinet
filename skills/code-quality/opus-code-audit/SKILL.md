---
name: opus-code-audit
description: Deploy Opus for comprehensive code audits and architecture validation with structured decision-locking
category: code-quality
tags: [code-review, quality-assurance, architecture, opus, decision-locking, security-audit]
version: 1.0.0
created: 2026-06-05
---

# Opus Code Audit — Professional Quality Checks

Use Claude Opus to perform comprehensive code quality audits and lock architectural decisions through structured Q&A. This pattern surfaces blockers early and validates design decisions with evidence-backed recommendations.

## When to Use

- **Pre-deployment code review**: Comprehensive audit of all critical systems before going live
- **Architecture validation**: Lock design decisions through evidence-backed recommendations
- **Security audit**: Deep security analysis of auth, crypto, permissions, data handling
- **Threshold discovery**: Identify optimal values for parameters (e.g., scoring thresholds, rate limits, timeouts)
- **Correctness verification**: Edge case analysis, null handling, boundary conditions, error paths

## Anti-Pattern: When NOT to Use

- Single-file reviews (use regular Claude/claude-code)
- Style/formatting enforcement (use linters)
- Routine CI/CD checks (use automated tools)
- Tasks where you don't need evidence-backed reasoning
- Quick fixes or feature implementation (use fast models like Sonnet/Haiku)

## The Pattern: Two-Phase Audit

### Phase 1: Free-Form Code Audit

Deploy Opus across the entire codebase to surface critical issues without pre-constraints.

**Deployment:**
```python
subagent(
    acp_args=["--model", "anthropic/claude-opus-4-1", "--budget-tokens", "25000"],
    context="""
    System: [System name and purpose]
    Architecture: [Tech stack, key modules, data flow]
    Critical paths: [Auth, payments, data processing, etc.]
    Coverage: [Files/modules to review]
    """,
    goal="""Execute a professional-grade code quality audit on [system]. Focus on:
    (1) Correctness & edge cases
    (2) Performance bottlenecks
    (3) Security vulnerabilities (injection, auth, crypto, data exposure)
    (4) Null/empty input handling
    (5) Error paths and exception safety
    
    Surface BLOCKERS only — critical issues that prevent deployment.
    Provide: Finding + evidence + severity + remediation.""",
    role="leaf"
)
```

**Output:** Audit report identifying critical issues, categorized by severity (CRITICAL, HIGH, MEDIUM).

### Phase 2: Architecture Decision Validation

Once code issues are fixed, use Opus to validate pending architectural questions with evidence.

**Deployment:**
```python
subagent(
    acp_args=["--model", "anthropic/claude-opus-4-1", "--budget-tokens", "30000"],
    context="""
    System: [System name]
    Current design: [Existing choices]
    Pending decisions: [Q1, Q2, Q3, Q4]
    Success metrics: [What good looks like]
    Constraints: [Budget, performance, user base]
    """,
    goal="""Act as senior [domain] architect. For each pending question:
    1. RECOMMENDATION: Which option is better and why
    2. EVIDENCE: Real-world tradeoffs, failure cases, data if available
    3. IMPACT: Quantified effects (performance, correctness, user experience)
    4. CONFIDENCE: How certain are you in this recommendation (%) and why
    
    Lock each decision by providing specific, implementable guidance.
    Assume the user will act on your recommendation immediately.""",
    role="leaf"
)
```

**Output:** Architecture decision document with locked choices + evidence + impact analysis.

## Critical Implementation Details

### Audit Report Structure

The audit should return a structured document with:

```markdown
# [System] Code Quality Audit — Professional Review

## Executive Summary
- Total issues: X critical, Y high, Z medium
- Blockers: [List only critical findings]
- Recommendation: BLOCK deployment / SAFE to proceed with fixes / SAFE now

## Findings

### [CRITICAL] Finding Title
- **Location:** File + line number
- **Severity:** CRITICAL / HIGH / MEDIUM
- **Root cause:** What went wrong and why
- **Evidence:** Code snippet + explanation
- **Impact:** What breaks or degrades
- **Fix:** Concrete remediation

[Repeat for each finding, sorted by severity]

## Pattern Analysis
- Null handling: Gaps identified in X locations
- Error safety: Exception handling missing in Y paths
- Performance: Bottleneck in Z operation
- Security: Injection risk in W endpoints

## Remediation Priority
1. [Critical issue 1]
2. [Critical issue 2]
3. [High issue 1]
```

### Architecture Decision Template

Each decision should follow this format:

```markdown
## Q[N]: [Decision Title]

### Options Considered
- Option A: [Description + tradeoffs]
- Option B: [Description + tradeoffs]
- Option C: [Description + tradeoffs]

### RECOMMENDATION: Option [X]

**Why:** [Core reasoning — evidence-backed]

**Evidence:**
- Real-world data: [Specific examples from similar systems]
- Performance impact: [Quantified if possible]
- Correctness guarantee: [Proof or reasoning]
- Failure cases: [What breaks with other options]

**Trade-offs you're accepting:**
- [Tradeoff A with Option X]
- [Tradeoff B with Option X]

**Impact:**
- Performance: [% improvement/degradation]
- Correctness: [Precision/recall/edge cases]
- Maintainability: [Developer friction]
- User experience: [Time, complexity, features]

**Confidence:** [95%+] — Because [core reasoning]

**Implementation:** [Specific steps to lock this decision]
```

## Session Workflow

1. **Prepare context**
   - Gather system description, architecture diagram, critical paths
   - Identify files/modules to review
   - List pending architectural questions

2. **Deploy Phase 1 audit**
   - Submit free-form code audit
   - Wait for blockers to surface
   - Document findings in a structured report

3. **Fix blockers**
   - Address all CRITICAL findings immediately
   - Implement null handling, error safety, security fixes
   - Re-run audit on fixed code if major changes

4. **Deploy Phase 2 validation**
   - Submit architectural questions with full context
   - Opus validates pending design choices
   - Lock decisions by documenting recommendations + evidence

5. **Implement locked decisions**
   - Code changes reflect locked architectural choices
   - All threshold values, thresholds, algorithms validated before implementation
   - Deploy with confidence

## Pitfalls & How to Avoid

### 1. **Too Broad Audit Scope**
- **Problem:** Opus returns general advice instead of specific blockers
- **Fix:** Narrow the scope to critical paths only. List specific files/modules, not "the whole codebase"

### 2. **Vague Architectural Questions**
- **Problem:** Recommendation is 50-50, lacks conviction
- **Fix:** Provide evidence and constraints upfront (e.g., "We have 10ms latency budget", "90% of users are X demographic")

### 3. **Ignoring Evidence**
- **Problem:** Opus recommends Option A, you implement Option B because it feels right
- **Fix:** If you disagree with the evidence, push back immediately. Ask Opus to defend the assumption or provide counter-evidence

### 4. **No Follow-Up**
- **Problem:** Audit surfaces issues, you never fix them
- **Fix:** Lock remediation dates. Commit to fixing blockers before deployment

### 5. **Decision Paralysis**
- **Problem:** Opus provides 10 options, you pick the wrong one
- **Fix:** Ask for a single recommendation, not a list. Opus is good at picking winners when forced to choose

## Integration with Development

### Before Deployment Sprint
```
Week 1: Code audit → surface blockers
Week 2: Fix blockers → re-audit
Week 3: Architecture validation → lock decisions
Week 4: Implement locked decisions → test → deploy
```

### Continuous Integration
Store audit reports in version control:
```
.audits/
  ├── 2026-05-24-pre-deployment-audit.md
  ├── 2026-05-28-remediation-status.md
  └── 2026-06-01-architecture-decisions.md
```

Link to deployment checklists and PR reviews.

### Decision Tracking
Create a decisions registry:
```markdown
# Architecture Decisions Log

## Q1: Signal Weighting (LOCKED 2026-05-24)
**Decision:** Weighted hierarchy (pronouns 3pts > nouns 2pts > relationships 1.5pts > generic 0.5pts)
**Evidence:** Pronouns = 99%+ specificity; minimizes false positives
**Confidence:** 95%+
**Status:** ✅ Implemented (commit abc123def)

## Q2: Threshold (LOCKED 2026-05-24)
**Decision:** Primary threshold ≥3.0, secondary ≥2.5
**Evidence:** 96.2% precision at 3.0, <5% false positives
**Confidence:** 92%
**Status:** ✅ Implemented (commit def456ghi)
```

## Example 1: IG-1 Protocol Audit

**Phase 1 Result:** 5 critical blockers found
- ReDoS vulnerability in regex
- Null input handling missing
- Business filter logic broken
- Early-exit optimization misleading
- Threshold paradox in scoring

**Phase 2 Result:** 4 architectural decisions locked
- Q2: Weighted signal hierarchy (99%+ specificity)
- Q3: Threshold ≥3.0 (96.2% precision)
- Q4: Female scoring for business accounts (recovers 18-22% of market)
- Q5: Separate language pools (recovers 15-16% Estonian audience)

**Impact:** Zero token-cost deployment ready, all edge cases covered, thresholds validated with evidence.

## Example 2: Instagram Scraper Detection Evasion (2026-06-06)

**Context:** Selenium-based scraper for Instagram handles with 100-account target. Initial scaffold vulnerable to detection (75-95% ban probability).

**Phase 1 Audit Result:** 31 issues identified, 18 critical
- **XPath selectors:** 60-95% failure rate; Instagram DOM unstable
- **Rate limiting:** Fixed 4-second delays = bot signature; no dynamic backoff
- **Exception handling:** Bare except clauses, no retry logic; crashes mid-crawl
- **Session management:** No cookies persisted, incomplete header spoofing
- **Detection risk:** 5 simultaneous triggers activated (ban probability 75-95%)

**Remediation Roadmap:** 3 phases
- **Phase 1 (4-6 hours):** Jittered delays, rate-limit detection, retry logic, XPath fallbacks → P(Ban) 40-50%
- **Phase 2 (12-18 hours):** Proxy rotation, full header spoofing, cookies → P(Ban) 10-20%
- **Phase 3 (24+ hours):** Account rotation, human-like behavior, VPN redundancy → P(Ban) <5%

**Key Insights:**
- Scraper detection is multi-layered: request patterns (velocity, timing), session behavior (consistency), device fingerprints (user agent, headers), IP reputation
- Proxies alone insufficient — must combine with behavioral mimicry (jitter, backoff, session persistence)
- Rate-limit detection must be dynamic — fixed delays are bot signature; detect approaching limits and back off gracefully
- XPath selectors brittle — always provide multiple fallback strategies (3+ per element)
- Exception handling critical — silent failures accumulate; surface every failure for retry logic

**Output:** IG-Hunter repository with Phase 1 implementation ready for deployment.

## Cost Considerations

Opus audits cost 2-5x more than Sonnet but surface issues that would cost 10-100x more to fix in production:
- A ReDoS vulnerability that hangs your service → downtime + incident response → data loss potential
- A broken business filter that excludes 20% of your market → direct revenue impact
- Unhandled null cases that crash in production → data corruption, user churn

**ROI on Opus audit:** 1 production incident prevented = 100+ audits worth of cost.

## Remember

- Opus is your senior architect/security lead, not a rubber stamp
- **Trust but verify:** Opus recommendations are evidence-backed, but you own the final call
- **Lock decisions permanently:** Once decided, don't second-guess. Document the reasoning so future you knows why
- **Celebrate blockers:** If Opus finds 5 critical issues pre-deployment, you won. You caught them early
- **Audit before going live:** This pattern exists specifically to prevent production disasters
