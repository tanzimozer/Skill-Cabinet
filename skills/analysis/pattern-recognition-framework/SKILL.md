---
name: pattern-recognition-framework
type: analysis
description: Build and maintain metric-driven pattern recognition systems for audience/user segmentation. Design metrics with clear strategic objectives, identify high-performing patterns, measure outcomes. Used for Instagram audience analysis, conversion prediction, targeting optimization.
tags: [pattern-recognition, metrics-design, audience-analysis, conversion-optimization, segmentation]
---

# Pattern Recognition Framework

Build metric-driven systems to identify which user/audience characteristics correlate with desired outcomes (follow-back, conversion, engagement). Design around clear strategic objectives, not just data collection.

## Framework Structure

Every pattern recognition system has three layers:

### Layer 1: Metric Definitions

Define **7–9 core metrics** (not 50). Each metric must answer:
- **What does it measure?** (one sentence)
- **Why does this matter strategically?** (objective: "find X" or "avoid Y")
- **What range/values?** (categorical or 0-10 scale)
- **How do high/low values show up?** (signal: "high = X, low = Y")
- **Priority rating** (★★★★★ = core predictor; ★★☆☆☆ = supporting info)

**Anti-pattern:** Collecting metrics because data is available. Only include metrics that directly support decision-making.

**Example:** Instagram audience analysis

| Metric | Purpose | Values | High Signal | Priority |
|--------|---------|--------|------------|----------|
| `Followers_Estimate` | Identify optimal audience size for follow-back receptivity | micro/mid/macro | micro = receptive | ★★★★★ |
| `Follower_Velocity` | Find actively growing vs. stagnant accounts | fast/moderate/slow | fast = high engagement | ★★★★☆ |
| `Account_Age_Estimate` | Balance credibility with open-mindedness | new/active/mature/established | mature (1-3yr) = sweet spot | ★★★★☆ |
| `Bio_Signal_Strength` | Find authentic personal branding | 0-9 scale | 7-9 = invested profile | ★★★☆☆ |
| `Business_Likelihood` | Filter business vs. personal; apply conditional logic | 0-10 scale | 0-2 or 3.5-6 = target | ★★★★★ |
| `Female_Score_Predicted` | Primary demographic targeting metric | 0-10 scale | ≥3.0 = 96%+ precision | ★★★★★ |
| `Conversion_Rate_Observed` | Actual ROI of pattern combinations | 0-100% | >60% = gold pattern | ★★★★★ |

### Layer 2: Expected High-Performing Patterns

Identify 5–8 **pattern combinations** (not individual metrics). Each pattern combines 3–5 metrics and includes:
- **Description** (what the pattern looks like)
- **Expected outcome** (conversion rate, engagement, or other target metric)
- **Target audience** (who this pattern reaches)
- **Action** (PRIORITY / HIGH / MEDIUM / SKIP)
- **Notes** (caveats, conditional logic, exceptions)

**Example:** Instagram patterns

| Pattern | Metrics | Expected Rate | Target | Action |
|---------|---------|----------------|--------|--------|
| GOLD | micro + fast_growth + female≥3 + bio≥5 | 65-75% | Young women (18-35) | PRIORITY |
| Q4 Unlock | micro + female_business (3.5-6) + female≥3 | 50-65% | Female entrepreneurs | PRIORITY |
| Rising Creators | micro + moderate + active + female≥3 + bio≥6 | 55-70% | Micro influencers | HIGH |
| Avoid | micro + fast_growth + female<2.5 + bio≥5 | <15% | Male/ambiguous | SKIP |
| Gatekeepers | macro + any_metrics + female≥3 | 5-20% | Celebrities (50k+) | SKIP |

**Key principle:** Patterns emerge from **actual data**, not theory. Design expected patterns from domain knowledge, then validate against real outcomes.

### Layer 3: Outcome Tracking

Track what **actually converts** vs. what you predicted:

```
Status | Handles Analyzed | Top Pattern Identified | Conversion Rate Achieved | Vs. Expected | Action
-------|------------------|----------------------|--------------------------|-------------|--------
Phase 1| 500/1975         | Pattern 1 + Q4 combo  | 62% (GOLD expected 65%)  | -3% (OK)    | Expand
Phase 1| 500/1975         | Pattern 5 (avoid)     | 8% (expected <15%)       | -7% (Good)  | Skip
```

Once you have real data, update expected patterns based on actual conversion rates.

## Design Process

### Step 1: Define Strategic Objectives
What decision do you want to make with this framework? Examples:
- "Prioritize which 500 of 1,975 handles to message" → metrics: audience size, growth, demographic fit
- "Identify which business accounts are worth targeting" → metrics: business signals, female ownership, category
- "Optimize follow-back conversion rate" → metrics: engagement, authenticity, demographic match

### Step 2: Design 7–9 Core Metrics
- Start with domain knowledge (what do experts care about?)
- Include one **outcome metric** (actual conversion, engagement, or return)
- Avoid metrics that are too correlated (e.g., followers + follower_velocity are related — decide which adds signal)
- Each metric should have a clear strategic use

### Step 3: Identify Expected High-Performing Patterns
- Brainstorm 5–8 combinations that should perform well (based on intuition + domain knowledge)
- Include 2–3 "avoid" patterns (what should you NOT target)
- Assign expected outcome metrics to each pattern
- Be specific: "micro + active" is too vague; "micro + moderate growth + 1-3 year old + female≥3" is testable

### Step 4: Measure Real Data
- Populate metrics for 100–1000 items (depending on data source)
- Calculate actual outcome (conversion, engagement, ROI)
- Compare actual vs. expected patterns
- Identify surprising patterns that emerge

### Step 5: Iterate & Optimize
- If actual > expected: double down on that pattern
- If actual < expected: investigate why (data quality? metric design? wrong target audience?)
- Look for new patterns that emerge in the data
- Feed back into targeting/prioritization logic

## Implementation Patterns

### Metric Scoring: Weighted Signals

When a metric combines multiple signals (e.g., `Female_Score_Predicted`), use explicit weights:

```python
female_score = 0

# Pronouns (highest weight — most specific)
if re.search(r'she/her', bio):
    female_score += 3
elif re.search(r'they/them', bio):
    female_score += 1

# Gender nouns (high weight)
female_nouns = len(re.findall(r'\b(she|her|woman|girl|female|queen|wife|sister|mom)\b', bio))
female_score += min(female_nouns * 0.5, 3)

# Lifestyle signals (lower weight)
if re.search(r'yoga|fitness|beauty|fashion|skincare', bio):
    female_score += 1

# Threshold
return 'female' if female_score >= 3.0 else 'unknown'
```

**Key principle:** Weighted hierarchy prevents weak signals from overwhelming strong ones.

### Pattern Matching: Decision Trees

Implement patterns as simple decision trees, not complex scoring:

```python
def match_pattern(account):
    if account['followers'] > 100000:
        return 'SKIP'  # Gatekeepers
    
    if account['female_score'] < 2.5:
        return 'SKIP'  # Demographic miss
    
    if account['followers'] < 10000 and account['growth_rate'] == 'fast' and account['bio_signal'] >= 5:
        return 'PRIORITY'  # GOLD pattern
    
    if account['followers'] < 10000 and account['business_likelihood'] >= 3.5 and account['female_score'] >= 3:
        return 'PRIORITY'  # Q4 pattern
    
    return 'MEDIUM'
```

### Batch Analysis with Checkpoints

For 1000+ items, implement resumable analysis:

```python
for i, item in enumerate(items):
    if already_analyzed(item):
        continue
    
    result = analyze(item)
    save_result(item, result)
    
    # Checkpoint every 50 items
    if (i + 1) % 50 == 0:
        print(f"Progress: {i+1}/{len(items)}")
        time.sleep(30)  # Rate limit
```

## Pitfalls & Fixes

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Too many metrics (20+) | Becomes analysis theater; hard to act on | Ruthlessly prune to 7–9 core metrics |
| Vague pattern descriptions | "Active + female-ish" is not testable | Be specific: "10–20k followers + female≥3.0 + post_frequency>3/week" |
| No outcome metric | Can't validate patterns | Always include ONE metric that measures actual success (conversion, engagement, ROI) |
| Expected patterns wrong | Theory doesn't match reality | Compare actual outcomes within first 100–200 items; update expectations early |
| Correlation vs. causation | "This metric is correlated with success; cause unknown" | That's fine — patterns are predictive, not causal. Use for prioritization. |
| Analysis paralysis | Keeps analyzing, never acts | Set a checkpoint: "After 100–200 items analyzed, start using patterns for targeting" |

## Related Skills

- `google-sheets-batch-operations` — Populating metrics across large datasets
- `instagram-data-extraction` — Fetching profile data for metric calculation
- `audience-segmentation-strategy` — Using patterns for targeting/prioritization

## References

- `references/metric-design-checklist.md` — Quick checklist for defining new metrics
- `references/conversion-pattern-examples.md` — Real patterns from past campaigns
