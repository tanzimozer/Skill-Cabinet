# Multi-Audience Audit Documentation Patterns

Reference from IG-Hunter audit session (2026-06-07). Demonstrates how to structure comprehensive audit output for different stakeholder groups.

## Audience Segments & Time Budgets

| Role | Time Budget | Goal | Content Focus |
|------|------------|------|----------------|
| Manager | 20-30 min | Approve investment? | Verdict + ROI per phase |
| Developer | 90 min | Implement Phase 1? | Issues + code examples + reference code |
| Implementer | 4-24h | Execute fixes | Checklist + reference code + detailed guides |
| Security Reviewer | 2+ hours | Validate risk model | Root causes + detection analysis + probability math |

## Document Types & Purposes

### Type 1: Entry Point (5-10 min)
**Purpose:** Quick verdict + decision trigger  
**Audience:** Everyone (first touchpoint)  
**Include:**
- 30-second summary of findings
- Top N problems (typically 3-5 most critical)
- Single decision matrix (yes/no on deployment)
- File navigation guide
- Time budget for deeper reading

**Example structure:**
```
TL;DR (30 sec)
Problem #1: [Issue] → [Impact] → [Risk]
Problem #2: [Issue] → [Impact] → [Risk]
Decision Matrix (Do I deploy?)
Next steps (read this if yes)
```

### Type 2: Executive Summary (15-20 min)
**Purpose:** Detailed findings without code-level depth  
**Audience:** Managers, non-technical stakeholders  
**Include:**
- 5 priority categories with 2-3 sentences each
- Severity breakdown (N critical, M high, P medium)
- Ban/failure probability with confidence
- Phased approach with effort + risk reduction
- Verdict and clear recommendation
- ROI calculation per phase

**Example structure:**
```
Category 1: [Name] (40% of failures)
├─ What: [Problem explanation]
├─ Impact: [User-facing consequence]
├─ Effort: 4 hours
└─ Risk reduction: 85% → 60%

Category 2: [Name] (25% of failures)
├─ What: [Problem explanation]
├─ Impact: [User-facing consequence]
├─ Effort: 8 hours
└─ Risk reduction: 60% → 30%

VERDICT: [Do/Don't deploy] because [1-2 sentences]
RECOMMENDATION: [Invest in Phase 1?] Yes/No
```

### Type 3: Quick Reference (10 min)
**Purpose:** Fast lookup for specific issues  
**Audience:** Developers, implementers  
**Include:**
- All issues at a glance (one-liner each)
- Code examples of what breaks
- Failure rate or probability for each
- Link to detailed section
- Priority ranking

**Format:** Markdown table or checklist  
**Example:**
```
Issue ID | Problem | Failure Rate | Priority | Details
---------|---------|--------------|----------|--------
[1] | XPath selector too generic | 30% | CRITICAL | See section 3.1
[2] | No retry on 429 error | 100% | CRITICAL | See section 3.2
```

### Type 4: Technical Deep-Dive (45-60 min)
**Purpose:** Root cause analysis + step-by-step remediation  
**Audience:** Developers, architects  
**Include:**
- Issue statement (what is broken)
- Root cause analysis (why is it broken)
- Code example showing the problem
- Impact assessment (what fails as a result)
- Step-by-step fix with code example
- Testing strategy for this specific issue
- Known variations/edge cases

**Structure per issue:**
```
## Issue [N]: [Title]

**Problem:** [What user sees]
**Root Cause:** [Why technically]
**Code Example — BEFORE:**
```python
# Broken code here
```
**Code Example — AFTER:**
```python
# Fixed code here
```
**Impact:** [What breaks if not fixed]
**Test Strategy:** [How to verify fix works]
**Difficulty:** X hours
**Priority:** CRITICAL | HIGH | MEDIUM
```

### Type 5: Risk Analysis (20 min)
**Purpose:** Validate that detection probability is justified  
**Audience:** Security reviewers, risk-conscious stakeholders  
**Include:**
- Detection triggers (all mechanisms Instagram uses)
- Probability calculation per trigger
- Combined probability model (with correlation adjustment)
- Confidence intervals
- Timeline to detection/failure
- Residual risk after each phase

**Math to show:**
```
P(timing detected) = 0.85 (fixed delays → obvious after 10-20 requests)
P(rate limit hit | no backoff) = 1.0 (hard limit at ~45 requests)
P(fingerprint weak | incomplete headers) = 0.70

P(at least one triggers) = 1 - ∏(1 - P_i)
                         = 1 - (0.15 × 0 × 0.30)
                         = 1.0 (100% certain to trigger something)

Conservative estimate (unknowns): 75-95%
Confidence: 95%
```

### Type 6: Implementation Checklist (Reference)
**Purpose:** Trackable task list during implementation  
**Audience:** Implementers  
**Include:**
- Checkbox for each issue
- Phase assignment (1, 2, or 3)
- Effort estimate
- Dependencies (must do X before Y)
- Testing requirements
- Approval checkpoints (per phase)

**Format:**
```markdown
### Phase 1: Critical Fixes (4-6 hours)

- [ ] **Issue [N1]**: [Title] (2 hours)
  - Depends on: Issue [M]
  - Test: [Specific verification step]
  
- [ ] **Issue [N2]**: [Title] (1 hour)
  - Depends on: Issue [N1]
  - Test: [Specific verification step]

**Phase 1 Approval Gate:** [ ] All tests pass, [ ] Code reviewed

### Phase 2: High-Impact (8-12 hours)
...
```

### Type 7: Reference Implementation (Ongoing)
**Purpose:** Show top N fixes applied; copyable examples  
**Audience:** Implementers  
**Include:**
- Original code side-by-side with fixed version
- Detailed comments explaining each change
- TODO comments for Phase 2/3
- Imports/dependencies listed
- Known limitations documented

**Approach:**
```python
# Original (broken):
time.sleep(4)  # TODO: Add jitter

# Fixed (Phase 1):
import random
time.sleep(random.uniform(2.5, 5.5))  # Human-like variance

# TODO (Phase 2): Add rate-limit detection logic
# TODO (Phase 3): Add proxy rotation
```

### Type 8: Navigation Guide (10 min)
**Purpose:** Help readers find what they need  
**Audience:** Everyone (second touchpoint)  
**Include:**
- Complete file manifest with size/read time
- Reading paths by role (manager, developer, reviewer, implementer)
- Cross-references (issue X → see document Y)
- Quick-start sequences

**Format:**
```markdown
## For Managers (30 min)
1. START_HERE.md (5 min)
2. AUDIT_SUMMARY.md (15 min)
3. Decision: Approve Phase 1?

## For Developers (90 min)
1. QUICK_SUMMARY.txt (10 min)
2. CODE_AUDIT_REPORT.md sections 1-5 (45 min)
3. Reference code (20 min)
4. Ready to implement

## For Reviewers (2+ hours)
1. CODE_AUDIT_REPORT.md (45 min)
2. RISK_ANALYSIS.md (20 min)
3. Reference code validation (30 min)
```

## Format Guidelines

**Use markdown for:**
- Entry points, summaries, navigation
- Lists and tables (easier to skim)
- Code examples (syntax highlighting)

**Use plain text for:**
- Quick references and checklists
- Content that won't be reformatted
- Multi-document indices (INDEX.txt)

**Use Python/script comments for:**
- Reference implementations
- Configuration examples
- Inline explanations of complex fixes

## Naming Convention

```
00_START_HERE.md           ← Entry point
README_AUDIT.md            ← Navigation guide
QUICK_SUMMARY.txt          ← Fast reference
AUDIT_SUMMARY.md           ← Executive summary (15 min)
[PROJECT]_Code_Audit_Report.md  ← Technical deep-dive (45+ min)
[CATEGORY]_Remediation_Guide.md ← How to fix specific category
Ban_or_Risk_Analysis.md    ← Risk model and detection
AUDIT_CHECKLIST.md         ← Implementation tracking
[PROJECT]_Fixed_Scraper.py ← Reference implementation
INDEX.txt                  ← File manifest
```

## Delivery Checklist

- [ ] Entry point created (START_HERE.md)
- [ ] Executive summary (AUDIT_SUMMARY.md)
- [ ] Technical deep-dive (CODE_AUDIT_REPORT.md)
- [ ] Risk analysis (if applicable)
- [ ] Reference implementation (fixed code)
- [ ] Implementation checklist
- [ ] Navigation guide (README or INDEX)
- [ ] Quick reference (QUICK_SUMMARY.txt)
- [ ] All documents cross-linked
- [ ] Read time estimates included
- [ ] Reading paths by role documented
- [ ] Quick-start guide provided (30-60 min to verdict)

## Success Signals

✓ Manager can decide (Phase 1? 1+2? Full?) in 30 min  
✓ Developer can start coding in 90 min  
✓ Implementer has clear checklist + reference code  
✓ Reviewer can validate probability model  
✓ No follow-ups asking "why is this broken"  
