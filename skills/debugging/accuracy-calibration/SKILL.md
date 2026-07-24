---
name: accuracy-calibration
category: debugging
description: Systematic approach to fixing classification/detection systems with high false negatives via semantic pattern library and weighted scoring calibration
type: technique
triggers:
  - "system scoring low accuracy (< 50%)"
  - "classification or detection system not recognizing valid patterns"
  - "false negatives outweighing true positives"
  - "need to recalibrate weighted scoring logic"
---

# Accuracy Calibration: Pattern Library + Weighted Scoring

When a detection/classification system underperforms (especially with high false negatives), use this systematic approach to diagnose and fix.

## Root Cause Pattern

High false negatives typically indicate:
- **Keywords-only detection is too narrow** — real examples don't match simple keyword lists
- **Scoring thresholds are too strict** — valid signals are penalized or discounted
- **Weights are inverted or imbalanced** — important signals get fewer points than noise

## The Fix: Four-Phase Calibration

### Phase 1: Build a Semantic Pattern Library

Instead of keyword lists, create a structured pattern library that captures *implicit* patterns.

**Shape:**
```json
{
  "trait_or_category": [
    {
      "pattern": "regex or natural language descriptor",
      "example": "concrete sample from real use",
      "explanation": "why this signals the trait",
      "confidence": 0.8
    }
  ]
}
```

**Key principle:** Patterns describe *what valid examples look like*, not just keywords. Include:
- Linguistic patterns (tone, negation, irony)
- Structural patterns (sentence length, punctuation absence)
- Contextual patterns (presence of other signals)
- Anti-patterns (what *shouldn't* co-occur with valid examples)

**Example:** For "deadpan wit", patterns should capture:
- Statements without exclamation marks or emojis
- Subtle humour (layering of meaning, understatement)
- Formal register (British phrasing, precise vocabulary)
- NOT defensive hedging, NOT enthusiasm, NOT apology spirals

### Phase 2: Enhance Detection Logic

Replace simple keyword matching with **pattern confidence scoring**:

```python
def pattern_confidence(patterns: List[dict], text: str) -> float:
    """
    Match text against patterns. Return 0.0–1.0 confidence.
    - Regex patterns: binary match + weight by confidence field
    - Natural language patterns: semantic heuristics (word count, punctuation, register)
    """
    confidence = 0.0
    for p in patterns:
        if pattern_matches(p['pattern'], text):
            confidence = max(confidence, p.get('confidence', 0.5))
    return confidence

def detect_trait(response: str) -> List[str]:
    detected = []
    
    # Pattern-based detection (primary)
    for trait, patterns in pattern_library.items():
        conf = pattern_confidence(patterns, response)
        if conf > threshold:  # threshold typically 0.2–0.3
            detected.append((trait, conf))
    
    # Keyword fallback (secondary, lower weight)
    if not detected:
        for trait, keywords in keyword_fallbacks.items():
            if any(kw in response.lower() for kw in keywords):
                detected.append((trait, 0.5))  # Lower confidence
    
    return detected
```

**Critical:** Use fallback keywords for *breadth*, not precision. Keyword matches are secondary signals.

### Phase 3: Recalibrate Scoring Weights

Once detection is working, fix the scoring function:

**Bad approach:**
- Equal points for all traits
- Simple sum (score = traits × 10)
- No penalty structure

**Good approach:**
- **Tier traits by importance:** Core (25pts), Secondary (18pts), Support (12pts)
- **Assign violation penalties:** Strong negative signal (-40pts per violation)
- **Add density bonuses:** If 2+ core traits present, system confidence is high — add bonus (+5–25pts)
- **Clamp to range:** Max 100, min 0

**Example from JARVIS fix:**
```python
def calculate_score(detected_traits, violations):
    core = 25 * count(trait in core_set for trait in detected_traits)
    secondary = 18 * count(trait in secondary_set)
    support = 12 * count(trait in support_set)
    
    penalties = -40 * len(violations)
    
    core_count = count(trait in core_set)
    if core_count >= 2:
        density_bonus = 5  # High confidence in the classification
    
    return clamp(core + secondary + support + penalties + density_bonus, 0, 100)
```

### Phase 4: Test + Iterate

**Test set:** Use 5–10 iconic, unambiguous examples. If accuracy on *these* is < 70%, the system is broken.

**Iteration loop:**
1. Run test suite, capture failing cases
2. Diagnose: Is it detection (pattern not matching) or scoring (right traits, wrong weight)?
3. For detection failures: Add pattern + confidence to library, or broaden keyword fallback
4. For scoring failures: Adjust tier weights or thresholds
5. Re-test. Repeat until average >= 70%

**Red flags:**
- If one trait dominates scoring, the weights are imbalanced
- If all responses score equally, detection isn't working
- If valid examples fail but invalid ones pass, violation detection is backwards

## Common Pitfalls

**Pitfall 1: Patterns too specific**
Don't hardcode the exact wording of test examples into patterns. Patterns should match the *class* of valid response, not memorize test cases.

**Pitfall 2: Keyword fallback as primary**
If keyword-only detection is your main path, you'll always have high false negatives for implicit patterns. Use fallback only when pattern confidence is low.

**Pitfall 3: Ignoring context**
Some traits are only valid given context (e.g., "unflappable under pressure" needs to know pressure exists). Pattern library should note context requirements.

**Pitfall 4: Thresholds too strict**
If pattern_confidence > 0.8, you'll miss valid examples. Typical working threshold is 0.2–0.3. You'll catch more false positives — handle that via violation detection and scoring penalties, not by raising the detection bar.

**Pitfall 5: Over-weighting core traits**
If core traits are worth 25pts each and support traits are 5pts, a response with 1 core + 5 support might score higher than one with 3 support + context match. Re-weight if this causes issues.

## Checklist

- [ ] Built pattern library with 5+ patterns per trait/category
- [ ] Pattern library includes examples + confidence weights
- [ ] Detection logic uses pattern confidence (0.0–1.0) as primary signal
- [ ] Keyword fallback in place (secondary, lower weight)
- [ ] Scoring function has 2–3 tiers (core/secondary/support)
- [ ] Violations carry strong negative penalty (-30 to -50pts)
- [ ] Density bonus for high-confidence cases (2+ core traits)
- [ ] Test suite: 5–10 iconic unambiguous examples
- [ ] Average accuracy on test set >= 70%
- [ ] Edge cases documented (context-dependent, ambiguous cases)

## Support Files

- `references/jarvis-calibration.md` — Real example: JARVIS personality checker fix (14.2 → 71.4/100), detailed walkthrough with test results and learnings
- `templates/pattern-library-template.json` — Starter template for building semantic pattern libraries
