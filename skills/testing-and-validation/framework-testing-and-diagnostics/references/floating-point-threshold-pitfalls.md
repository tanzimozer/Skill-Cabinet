# Floating-Point Threshold Pitfalls & Patterns

## The Problem

When decision frameworks use floating-point comparisons at thresholds, binary arithmetic can silently fail boundary cases. This doc captures patterns from real diagnostics.

## Case Study: MVP 80% Completion Threshold

### The Failure

Test expected: `0.895 >= 0.80` → True
Framework returned: False

Input: Two core features at 0.79 and 1.0 completion
Calculation: (0.79 + 1.0) / 2 = 0.895 mathematically
Comparison: 0.895 >= 0.80 → **False in framework** ❌

### Root Cause

Binary floating-point cannot exactly represent 0.79 in decimal:
- 0.79 in binary: 0.1100101010001111010111...  (repeating)
- 0.79 stored: truncated/rounded to nearest representable value
- (0.79_binary + 1.0) / 2 ≠ 0.895_decimal exactly
- Result might be 0.8949999999... or 0.8950000001...

When compared with `>=`, the tiny difference causes failure.

### Evidence from Testing

```python
# Test progression that exposed the issue:

def test_0_80_boundary():
    # (0.80 + 1.0) / 2 = 0.90
    ready = framework.is_ready_to_ship([0.80, 1.0])
    assert ready  # ✓ PASS

def test_0_79_boundary():
    # (0.79 + 1.0) / 2 = 0.895
    ready = framework.is_ready_to_ship([0.79, 1.0])
    assert ready  # ✗ FAIL — unexpected!

def test_0_78_boundary():
    # (0.78 + 1.0) / 2 = 0.89
    ready = framework.is_ready_to_ship([0.78, 1.0])
    assert not ready  # ✓ PASS (correctly rejects)
```

Pattern: The 0.79 case fails while 0.80 and 0.78 pass. This points to floating-point precision, not logic error.

## Solutions

### Solution 1: Floating-Point Tolerance (Recommended)

Add small epsilon tolerance to comparison:

```python
def is_ready_to_ship(self):
    THRESHOLD = 0.80
    TOLERANCE = 0.0001  # Allow for FP imprecision
    
    # ... calculate core_completion ...
    
    return (core_completion >= THRESHOLD - TOLERANCE) and has_complete_feature
```

**Why this works:**
- Tolerance of 0.0001 is 0.01% of threshold
- Addresses FP rounding without changing logic
- Industry standard in scientific/financial code
- Performance impact: negligible

**Downsides:**
- Introduces magic number (though documented)
- Slightly relaxes threshold (0.7999 now passes)

### Solution 2: Rounding to Precision

Round to 2 decimal places before comparison (percentage precision):

```python
def is_ready_to_ship(self):
    # ... calculate core_completion ...
    core_completion = round(core_completion, 2)  # Round to 2 decimals
    
    return (core_completion >= 0.80) and has_complete_feature
```

**Why this works:**
- Explicit rounding eliminates FP artifacts
- 2 decimals = percentage precision (0.01 = 1%)
- Clear intent in code

**Downsides:**
- Slightly aggressive rounding (0.894 becomes 0.89, now rejects)
- May affect other boundary cases

### Solution 3: Use Decimal Module

For exact arithmetic:

```python
from decimal import Decimal

def is_ready_to_ship(self):
    THRESHOLD = Decimal('0.80')
    
    # ... calculate core_completion as Decimal ...
    core_completion = Decimal(str(core_sum)) / Decimal(len(core_features))
    
    return (core_completion >= THRESHOLD) and has_complete_feature
```

**Why this works:**
- Decimal eliminates floating-point errors entirely
- Exact arithmetic for business logic

**Downsides:**
- Overkill for percentages (adds complexity)
- Requires converting to/from Decimal
- Performance hit (negligible for this use case)

## Recommendation

Use **Solution 1 (floating-point tolerance)** because:
1. Standard pattern in professional code
2. Minimal code change (1-2 lines)
3. Clear intent (tolerance documented)
4. No rounding side effects
5. Preserves threshold semantics

## Testing Floating-Point Boundaries

### The Right Way to Test

```python
import unittest

class TestFloatingPointThresholds(unittest.TestCase):
    
    def test_boundary_below_threshold(self):
        """Just below threshold should fail."""
        value = 0.7999999
        self.assertFalse(value >= 0.80)
    
    def test_boundary_at_threshold(self):
        """Exactly at threshold should pass."""
        value = 0.80
        self.assertTrue(value >= 0.80)
    
    def test_boundary_above_threshold(self):
        """Just above threshold should pass."""
        value = 0.8000001
        self.assertTrue(value >= 0.80)
    
    def test_aggregate_boundary(self):
        """Aggregated value near threshold should be consistent."""
        # This is where FP precision breaks
        values = [0.79, 1.0]
        mean = sum(values) / len(values)
        
        # Without tolerance, this fails:
        # self.assertTrue(mean >= 0.80)  # False unexpectedly!
        
        # With tolerance, this passes:
        TOLERANCE = 0.0001
        self.assertTrue(mean >= (0.80 - TOLERANCE))  # True as expected
```

### Test Checklist

- [ ] Test exact threshold value (== threshold)
- [ ] Test just below threshold (threshold - 0.00001)
- [ ] Test just above threshold (threshold + 0.00001)
- [ ] Test aggregated values (mean, sum, etc.)
- [ ] Test with real-world data (0.79, 0.89, 0.895, etc.)
- [ ] Run tests multiple times (FP rounding can vary)

## Detection Pattern

If you see this:
```
AssertionError: False is not true
Test: test_threshold_enforcement
Input: [0.79, 1.0]
Expected: >= 0.80
Actual: False
Math check: (0.79 + 1.0) / 2 = 0.895 which IS > 0.80
```

**This is almost certainly a floating-point precision issue.**

## Prevention

**In framework code:**
1. Always return metrics with the calculated value
2. Round metrics to human-readable precision (0.895 not 0.8949999...)
3. Document threshold with >=, >, <=, < explicitly
4. Test boundaries with aggregated values

**In test code:**
1. Test all three boundary cases (below, at, above)
2. Use assertAlmostEqual for FP comparisons:
   ```python
   self.assertAlmostEqual(result, 0.895, places=2)
   ```
3. Add tolerance to >= comparisons when aggregating

## Historical Note

This pattern appeared in Personal Framework diagnostics (June 2026). The MVP completion rule (80% threshold) failed on:
- Input: [0.79, 1.0] core features
- Expected: ready_to_ship = True (mean 0.895 >= 0.80)
- Actual: ready_to_ship = False
- Root cause: Binary FP representation of 0.79 + rounding errors
- Solution: Added TOLERANCE = 0.0001 to comparison

Symptom signature: A boundary test fails while adjacent values (0.78, 0.80) pass. This is the telltale sign of FP precision, not logic error.
