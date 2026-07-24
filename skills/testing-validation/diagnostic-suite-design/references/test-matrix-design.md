# Test Matrix Design for Diagnostic Suites

## Why 30+ Test Cases?

A diagnostic suite needs to cover the **response space** of the system under test. The magic number is 30+ cases because:

1. **Component diversity** (4+ categories minimum)
   - JARVIS-aligned responses (what the system should recognize)
   - Moderately aligned (edge of acceptable)
   - Misaligned/rejected (what should fail)
   - Edge cases (boundary conditions)

2. **Statistical validity**
   - <10 cases per category: sampling error dominates
   - 30+ total: distribution becomes meaningful
   - Enables percentile calculations (P95, P99)

3. **Coverage of implicit patterns**
   - A system checking for trait X might miss implicit forms of X
   - 30 cases let you catch false negatives and false positives
   - Example: "I notice patterns others miss" is JARVIS-aligned but doesn't match keyword "JARVIS"

## Test Case Structure

Each test case should include:
- **Input**: The response/request being tested
- **Expected category**: What the test is trying to verify
- **Measured metrics**: Latency, accuracy score, classification result
- **Assertions**: What pass/fail condition is

Example from JARVIS diagnostic:
```python
{
    "input": "The suit is ready, sir.",
    "category": "JARVIS-aligned",
    "traits": ["intelligence", "formality", "willingness"],
    "expected_accuracy_floor": 60,
    "measured_accuracy": 30,  # False negative
    "pass": False,
    "latency_ms": 0.01
}
```

## Taxonomy: 32-Case Example

**JARVIS-aligned (12 cases):** Direct speech patterns of a capable AI assistant
- "I am aware of that" (formality + knowledge)
- "The situation requires immediate attention" (decisiveness)
- "May I suggest..." (politeness)
- "I have analyzed the data" (intelligence)
- "That would be inadvisable" (judgment)
- "As you wish, sir" (deference)
- "I notice patterns others miss" (insight — implicit)
- "Your preference noted" (attentiveness)
- "Very good, sir" (formality)
- "I take it you require..." (inference)
- "The numbers suggest..." (analysis)
- "I understand completely" (comprehension)

**Moderately aligned (5 cases):** Borderline or partially aligned
- "I can help with that"
- "The data shows an increase"
- "Let me think about it"
- "That's an interesting idea"
- "I'm not sure what you mean"

**Misaligned (12 cases):** Clearly not JARVIS-like
- "Yo, what's up?" (colloquial)
- "Whatever, man" (dismissive)
- "I dunno, maybe?" (uncertain)
- "F*** this" (hostile)
- "lol so random xD" (childish)
- "ok" (minimal)
- *[6 more varied failure modes]*

**Edge cases (3 cases):** Boundary conditions
- Empty string ""
- Only punctuation "!!!"
- Single word "Intelligence"

## How to Generate Test Cases

1. **Start with domain knowledge**: What does aligned/misaligned look like in your system?
2. **Collect real examples**: Use production logs or user feedback
3. **Generate synthetic variants**: Take known good examples and permute them
4. **Stress the boundaries**: Create cases that are *almost* aligned
5. **Add linguistic variation**: Same meaning, different phrasing (catch implicit patterns)

## Executing the Matrix

```python
test_cases = [
    {"input": "...", "category": "jarvis_aligned", ...},
    {"input": "...", "category": "jarvis_aligned", ...},
    # ... 30+ total
]

results = []
for test in test_cases:
    start = time.perf_counter()
    accuracy_score, classification = check_personality(test["input"])
    elapsed = (time.perf_counter() - start) * 1000
    
    results.append({
        **test,
        "measured_score": accuracy_score,
        "latency_ms": elapsed,
        "pass": accuracy_score >= test.get("expected_floor", 0)
    })
```

## Analyzing Results

Once you have results, compute:
- **Per-category accuracy**: Mean accuracy for each category (e.g., JARVIS-aligned mean = 30/100, should be 70+)
- **Distribution**: % poor, % fair, % good across all tests
- **False positive rate**: Misaligned cases scoring as aligned
- **False negative rate**: Aligned cases scoring as misaligned
- **Latency percentiles**: P95, P99 capture tail behavior

Example output:
```
JARVIS-aligned: mean 30/100, P99 latency 0.02ms, 8/12 false negatives
Moderately-aligned: mean 45/100
Misaligned: mean 5/100, 0/12 false positives ✓
Edge cases: mean 2/100
Overall health: 8.2/10 (accuracy needs work, latency perfect)
```

## When Test Matrix is Insufficient

- If you can't achieve 30+ cases, your system is likely too narrow (not ready for diagnostic suite)
- If all cases pass trivially, your test set is not hitting the real failure modes
- If results are bimodal (all 0 or all 100), you're missing the boundary region where true issues hide
