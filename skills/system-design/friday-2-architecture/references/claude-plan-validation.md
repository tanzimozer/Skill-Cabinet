# Claude Plan Validation Checklist

## Problem

Proposed cost-reduction strategies to a Claude Max plan user. Max plan has flat monthly fee, unlimited usage — cost optimization is irrelevant. Forced rebuild of entire Friday 2.0 design.

## Quick-Check Logic

Before proposing cost optimization, cost-reduction paths, or model-selection strategies:

1. **Confirm billing model:**
   - API plan (pay-per-token): Cost optimization is valid pillar
   - Claude Max / subscription: Cost optimization irrelevant; focus on capability & trustworthiness
   - Unknown: Ask first

2. **If Max plan detected:**
   - Remove all cost-reduction language
   - Reframe pillars as: Security, Capability, Trustworthiness, Framework
   - Focus on autonomy, safety, explainability

3. **If cost pillar is proposed but user is on Max:**
   - Expect rejection + rebuild request
   - The rebuild will cost session tokens
   - Better to verify upfront

## Implementation

Add this check to any design brief involving:
- Model selection / optimization
- Token-efficiency improvements
- Cost baseline calculations
- Pricing tier analysis
- Cost-reduction "pillars" or "strategies"

## Template

```
Before proposing cost optimizations:
- Confirm: "You're on [API/Max/Unknown]?"
- If Max: "Cost is fixed, so focus shifts to [security/capability/autonomy]."
- If API: Proceed with cost optimization as valid pillar
```
