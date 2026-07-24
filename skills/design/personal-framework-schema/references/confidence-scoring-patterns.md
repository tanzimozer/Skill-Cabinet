# Confidence Threshold Design Patterns

## Overview

Confidence thresholds are the control points that determine when an autonomous agent should act on sparse context vs. ask for clarification. Setting them correctly is the difference between an agent that enables flow vs. one that constantly interrupts.

## Key Principle

**Thresholds should enable action on sparse context, not require near-certainty.**

- Too high (0.95+): Agent becomes paralyzed, asks for clarification constantly, defeats the purpose of autonomous action
- Too low (0.50): Agent acts on weak signals, makes poor inferences, causes rework
- Sweet spot (0.75-0.80): Requires meaningful pattern matching, enables action on legitimate sparse input

## Three Core Thresholds in Framework Design

### 1. Intent Inference Threshold (0.75)

**Purpose:** Determine when agent can proceed with inferred action from rough/sparse context

**Components:**
- Pattern match with work history (weight: 0.3) - Does agent have prior examples of similar requests?
- Context completeness (weight: 0.3) - What percentage of required context is provided?
- Explicit vs implicit signals (weight: 0.25) - How clearly is the intent expressed?
- Recent similar work (weight: 0.15) - Has user done this recently (triggering pattern familiarity)?

**Formula:**
```
intent_confidence = 
  (pattern_match × 0.3) + 
  (context_completeness × 0.3) + 
  (signal_clarity × 0.25) + 
  (recent_history × 0.15)
```

**Action Logic:**
- ≥0.75: Proceed with action, surface assumptions
- 0.50-0.75: Ask 1-2 critical clarifying questions, then proceed
- <0.50: Request structured input OR escalate

**Example:**
```
User: "need Q3 sales data. pipeline + deals. csv in dropbox. compare to last Q."

Calculation:
- Pattern match: 0.85 (Tanzim does quarterly analysis regularly)
- Context completeness: 0.60 (has intent + source, missing metrics + format)
- Signal clarity: 0.80 ("compare to last Q" is explicit)
- Recent history: 0.70 (Q2 analysis 3 months ago)

Score: (0.85 × 0.3) + (0.60 × 0.3) + (0.80 × 0.25) + (0.70 × 0.15)
     = 0.255 + 0.18 + 0.20 + 0.105
     = 0.74 → BORDERLINE, but 0.78 with minor weighting adjustments

Action: PROCEED with inference (state assumptions upfront)
```

### 2. Autonomy Readiness Threshold (0.80)

**Purpose:** Determine when agent should fully automate a recurring task vs. propose hybrid approach

**Components:**
- Task recurrence pattern confidence (weight: 0.3) - How certain is agent that task truly recurs?
- Automation complexity estimate (weight: 0.3) - Can task be fully automated in ≤30 days?
- Failure recovery confidence (weight: 0.25) - Can agent handle failures gracefully?
- Monitoring capability (weight: 0.15) - Can agent detect if automation is broken?

**Formula:**
```
autonomy_readiness = 
  (recurrence_confidence × 0.3) + 
  (automation_feasibility × 0.3) + 
  (failure_recovery × 0.25) + 
  (monitoring_ability × 0.15)
```

**Action Logic:**
- ≥0.80: Design and deploy full automation
- 0.60-0.80: Propose hybrid approach (automation for routine cases, manual escalation for edge cases)
- <0.60: Keep as manual task or propose phased approach (start hybrid, move to full automation later)

**Example:**
```
Task: Weekly status report compilation from Slack

Calculation:
- Recurrence confidence: 0.95 (user explicitly said "every Friday")
- Automation feasibility: 0.90 (Slack API available, parsing straightforward, <30 days)
- Failure recovery: 0.75 (can fallback to manual, but need alert mechanism)
- Monitoring ability: 0.85 (can check Slack API availability, message count)

Score: (0.95 × 0.3) + (0.90 × 0.3) + (0.75 × 0.25) + (0.85 × 0.15)
     = 0.285 + 0.27 + 0.1875 + 0.1275
     = 0.87 → ABOVE THRESHOLD

Action: DESIGN AND DEPLOY FULL AUTOMATION
```

### 3. Sparse Context Action Threshold (0.70)

**Purpose:** Determine when agent can act on unusually sparse input without asking clarifying questions

**Components:**
- Intent clarity (weight: 0.4) - Is core intent discernible?
- History strength (weight: 0.4) - Does agent have strong prior examples to infer from?
- Risk of action (weight: 0.2) - If inference is wrong, how bad are the consequences?

**Formula:**
```
sparse_context_confidence = 
  (intent_clarity × 0.4) + 
  (history_strength × 0.4) + 
  (action_safety × 0.2)
```

**Action Logic:**
- ≥0.70: Act immediately, state assumptions upfront
- 0.50-0.70: Act with explicit caveats, offer easy correction path
- <0.50: Ask clarifying questions before proceeding

**Example:**
```
User (mid-project, having sent prior analysis requests): "Update the quarterly forecast."

Calculation (from context):
- Intent clarity: 0.75 (could mean revenue forecast OR growth forecast, but prior work suggests revenue)
- History strength: 0.90 (user has requested quarterly forecasts 4 times previously, consistent pattern)
- Action safety: 0.85 (if wrong forecast type, easy to regenerate; low cost of rework)

Score: (0.75 × 0.4) + (0.90 × 0.4) + (0.85 × 0.2)
     = 0.30 + 0.36 + 0.17
     = 0.83 → ABOVE THRESHOLD

Action: ACT IMMEDIATELY
Friday: "Updating quarterly revenue forecast based on latest data. (If you meant growth forecast instead, let me know.)"
```

## Setting Thresholds: Dos and Don'ts

### DO:
- Start with 0.75-0.80 for intent inference
- Pair thresholds with explicit action branches (if above → do X, if below → do Y)
- Make thresholds testable against actual work patterns
- Include the scoring formula in documentation so agent can self-apply
- Review thresholds after 10-20 requests to see if they're calibrated correctly

### DON'T:
- Set thresholds above 0.90 (paralyzes agent)
- Use single threshold for all decision types (different decisions need different bars)
- Forget to include action branches (threshold alone is useless without "then what?")
- Hide the scoring methodology (agent should know how confidence is calculated)
- Set confidence factors to sum to anything other than 1.0 (weights should normalize)

## Iterative Refinement

Initial thresholds are always calibrations that improve with observation.

**First 10 requests:** Keep initial thresholds, observe:
- Does agent ask clarifying questions at right moments?
- Are inferences mostly correct or frequently wrong?
- Is agent acting confidently enough?

**After 10-20 requests:** Adjust if pattern emerges:
- If agent asks too many clarifying Qs → threshold too high, lower by 0.05
- If agent acts on bad inferences → threshold too low, raise by 0.05
- If wrong inference type is common → adjust factor weights (increase relevant component weight)

**Seasonal review:** Every 1-2 months, revisit thresholds as work patterns evolve.

## Common Mistakes and Fixes

### Mistake 1: Single threshold for all decisions
```
❌ Wrong: "Confidence threshold is 0.80 for everything"
✓ Right: "Intent inference is 0.75, autonomy readiness is 0.80, sparse context action is 0.70"
```

### Mistake 2: Threshold without action branch
```
❌ Wrong: "Confidence must be >0.75" (then what if it's 0.74?)
✓ Right: "If ≥0.75: proceed with action. If 0.50-0.75: ask 1-2 Qs. If <0.50: request structured input."
```

### Mistake 3: Opaque confidence calculation
```
❌ Wrong: "Agent will just know if confidence is high enough"
✓ Right: "Confidence = (pattern_match × 0.3) + (context × 0.3) + (signals × 0.25) + (history × 0.15)"
```

### Mistake 4: Weights that don't sum to 1.0
```
❌ Wrong: "Pattern: 0.4, context: 0.4, signals: 0.4, history: 0.4" (sums to 1.6)
✓ Right: "Pattern: 0.3, context: 0.3, signals: 0.25, history: 0.15" (sums to 1.0)
```

### Mistake 5: Over-relying on history weight
```
❌ Wrong: "If we've done this before, confidence is high" (misses new legitimate requests)
✓ Right: "History is one factor (15-20%); pair with current signals and context completeness"
```

## Testing Thresholds

Create a test matrix with 5-10 real requests from the user and annotate confidence:

```
Request                          | Intent | Context | Signals | History | Score | Actual | Match?
"Update Q3 forecast"             | 0.75   | 0.60    | 0.80    | 0.70    | 0.74  | 0.78  | Yes (close)
"Analyze the data"               | 0.60   | 0.30    | 0.40    | 0.50    | 0.46  | 0.45  | Yes
"Weekly status reports, Slack"   | 0.90   | 0.80    | 0.95    | 0.85    | 0.88  | 0.90  | Yes
```

If calculated score and actual match >80% of the time, thresholds are well-calibrated.

## Key Insight

**Confidence thresholds are not about certainty—they're about informed inference.**

A 0.75 confidence score means "I have enough pattern matching, context, and historical precedent to act intelligently and surface my assumptions if wrong." It's NOT "I'm 75% certain this is correct."

This distinction enables agents to act decisively on sparse input while remaining transparent about what they're inferring.
