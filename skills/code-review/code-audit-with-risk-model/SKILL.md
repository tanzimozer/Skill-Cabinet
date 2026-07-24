---
name: code-audit-with-risk-model
author: claude-code
description: >
  Comprehensive code quality audits with quantified risk assessment and 
  phased remediation roadmaps. Particularly effective for security-sensitive 
  code (scrapers, bots, detection-evasion systems). Delivers multi-format 
  documentation for different audiences and decision-making contexts.
usage: >
  Use when performing a thorough code audit that requires:
  - Identification of multiple issue categories (syntax, logic, performance, security)
  - Quantified risk or ban probability assessment
  - Multi-phase remediation roadmap with effort estimates
  - Documentation for both technical and non-technical audiences
  - Reference implementations addressing top issues
tags: [audit, security, risk-assessment, code-review, documentation]
---

## Pattern Overview

This skill delivers **structured, multi-audience code audits** that go beyond bug-finding to provide:
1. **Prioritized issue identification** across 5+ categories
2. **Quantified risk modeling** (probability, confidence, timeline)
3. **Phased remediation roadmap** (effort vs. risk reduction)
4. **Multiple documentation formats** (executives, developers, implementers, reviewers)
5. **Reference implementations** showing top fixes
6. **Decision matrices** for stakeholders to choose investment level

## Core Workflow

### Phase 1: Code Analysis (2-3 hours)
- Read source files completely
- Categorize issues by type (syntax, logic, security, performance, detection)
- Assign severity (critical, high, medium) AND impact category
- Document root cause for each issue
- Estimate fix difficulty (hours or effort level)

### Phase 2: Risk Modeling (1 hour)
- Identify detection/failure triggers specific to domain
- Build probabilistic model for ban/failure outcome
- Calculate compound probability (multiple triggers firing together)
- Establish confidence intervals (conservative vs. optimistic)
- Create timeline to failure/detection

### Phase 3: Remediation Planning (1 hour)
- Group fixes into phases (critical only → critical+high → all)
- Calculate ban probability reduction per phase
- Estimate effort for each phase
- Identify quick wins vs. long-term improvements
- Create implementation checklists per phase

### Phase 4: Documentation (2-3 hours)
- Executive summary (managers, 15-20 min read)
- Technical deep-dive (developers, 45+ min read)
- Decision documents (risk matrices, phase comparison)
- Quick reference (checklists, fast lookups)
- Reference implementation (code showing Phase 1 fixes)
- Navigation guides for different roles

### Phase 5: Delivery (30 min)
- Create index file with reading paths by role
- Verify all documents created and cross-linked
- Provide quick-start guide
- Summarize verdict and next steps

## Document Structure Template

Create these files (adjust names to specific project):

```
00_START_HERE.md (5 min)
├─ 30-sec summary
├─ Top N problems
├─ Risk timeline
└─ Decision matrix

AUDIT_SUMMARY.md (15 min)
├─ Findings by priority category
├─ Impact & difficulty for each
└─ Key recommendations

QUICK_SUMMARY.txt (10 min)
├─ All issues at a glance
├─ Code examples of problems
└─ Fast reference

[PROJECT]_Code_Audit_Report.md (45 min)
├─ Issue 1-N with detail
├─ Root cause analysis
├─ Code examples
└─ Step-by-step remediation

Risk_or_Detection_Analysis.md (20 min)
├─ Probability model
├─ Timeline to failure
├─ Detection triggers
└─ Confidence assessment

Remediation_Guides.md (30 min)
├─ How to fix category 1
├─ How to fix category 2
└─ Testing strategies

[PROJECT]_Fixed_[VERSION].py (reference)
└─ Code with top N fixes applied + comments

AUDIT_CHECKLIST.md (reference)
└─ All issues as checkbox list

README_AUDIT.md (10 min)
└─ Navigation + reading paths by role

INDEX.txt (5 min)
└─ File manifest + quick-start guide
```

## Key Techniques

### Risk Modeling for Bots/Scrapers
- Identify all detection triggers (timing patterns, headers, fingerprints, behavior)
- Calculate detection probability per trigger independently
- Combine using: P(detect) = 1 - ∏(1 - P_i)
- Add correlation adjustment (triggers often co-fire)
- Use conservative estimate: P_combined × 0.8 (for unknowns)
- Confidence: 95% if model covers 80%+ of likely triggers

### XPath/Selector Brittleness
- Test each selector against Instagram's actual DOM
- Note which class names/IDs are stable vs. dynamic
- Provide fallback chains (CSS → XPath → JavaScript inspection)
- Measure failure rate empirically or estimate from pattern
- Flag DOM-dependent data (follower count often not in HTML)

### Rate Limiting Assessment
- Calculate request rate (requests per unit time)
- Compare against published or inferred API limits
- Note when limit will be hit (typically after N requests)
- Check if code handles 429/rate-limit errors
- Identify fixed delays (bot signature) vs. jittered (human-like)

### Multi-Audience Documentation
- **Managers:** Verdict + decision matrix + phase ROI (15 min)
- **Developers:** Issues + root causes + code examples (90 min)
- **Implementers:** Checklist + reference code + phase roadmap (ongoing)
- **Reviewers:** Technical deep-dive + risk model + verification (120+ min)

## Common Pitfalls

1. **Single-audience document:** Trying to write one doc for all roles fails. Create multiple formats upfront.

2. **Missing confidence:** Stating risk as fact without confidence intervals. Always say "75-95% (confidence: 95%)" not "will be detected."

3. **No phased approach:** Fixing everything at once overwhelms implementers. Group by impact & effort.

4. **Forgetting reference code:** Pointing out problems without showing solutions frustrates developers. Provide fixed version of top issues.

5. **Incomplete root cause:** Saying "XPath fails" is useless. Say "XPath fails because Instagram changed class name from 'user-bio' to 'bio-text' in v2.4."

6. **Ignoring cascading fixes:** Some fixes are blockers for others (exception handling before retry logic). Sequence them.

7. **No testing strategy:** Saying "test it" is vague. Specify: "Test on test account, monitor for 24-48h, check logs for ERROR/FAIL patterns."

## Output Quality Checklist

- [ ] Issue count by severity (N critical, M high, P medium)
- [ ] Confidence level stated (85-95%)
- [ ] Ban/failure probability quantified and justified
- [ ] Each issue has root cause explanation
- [ ] Each issue has estimated fix difficulty
- [ ] Phased roadmap with effort and risk reduction
- [ ] Multiple documentation formats (quick + deep + reference)
- [ ] Decision matrix (what happens at each phase)
- [ ] Reference implementation with Phase 1 fixes
- [ ] Navigation guide for different roles
- [ ] Quick-start guide (30-60 min to understand verdict)
- [ ] All documents cross-linked

## Success Indicators

✓ Stakeholders can decide to invest (Phase 1? 1+2? Full fix?) based on doc
✓ Developers can start implementing Phase 1 from reference code + checklist
✓ Security team can validate risk model independently
✓ Managers understand ROI (effort vs. risk reduction per phase)
✓ No follow-up questions about "why is this broken" (docs explain)

---

## Support Files

- **`references/instagram-scraper-detection-triggers.md`** — Detection patterns and compound probability model specific to bot/scraper detection. Useful for security-sensitive audits.
- **`references/multi-audience-audit-structure.md`** — Document types, audience segments, naming conventions, and delivery checklist for comprehensive multi-audience audits.
- **`references/probabilistic-risk-modeling.md`** — Framework for quantifying ban/failure probability when multiple detection mechanisms exist. Includes model calibration and scenario analysis.

---

See also: code-review-best-practices (for general audit structure)
