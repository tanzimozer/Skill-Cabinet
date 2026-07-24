---
name: framework-testing-and-diagnostics
description: "Comprehensive diagnostic testing of decision frameworks: validate all rules, measure performance, detect logic gaps and edge cases, root-cause issues systematically."
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [testing, diagnostics, framework-validation, performance-benchmarking, edge-cases, root-cause-analysis, decision-systems]
related_skills: [systematic-debugging, decision-framework-design, code-audit-with-risk-model]
---

# Framework Testing & Diagnostics

When you have an **implemented decision framework** (rules, state machines, logging, orchestrator) and need to **comprehensively validate it**, this skill provides the pattern: build a diagnostic test suite that exercises all rules, measures latency, validates thresholds, detects logic gaps, and identifies edge cases.

Use this when:
- Framework implementation is complete and you need to verify correctness
- You need to audit all decision rules before production deployment
- You want to measure performance per rule (latency, throughput)
- You need to identify and root-cause edge case failures
- You want to validate logging format and completeness
- You need to ensure thresholds are strictly enforced
- You want to document findings for stakeholders and fix prioritization

Do NOT use this for:
- Building a new framework (use `decision-framework-design` instead)
- Unit testing individual functions in isolation (use standard unittest/pytest)
- Load testing under production traffic (use dedicated load testing tools)

---

## The Diagnostic Pattern

A comprehensive framework diagnostic has **6 phases**:

### Phase 1: Test Suite Architecture

**Structure:**
- One test class per decision rule
- One test class for cross-cutting concerns (logging, performance)
- Separate test class for edge cases (boundaries, precision, state machines)
- MetricsCollector class to track latency and decision counts

**Template:**

```python
import unittest
from unittest.mock import patch, MagicMock
import time
import json
from datetime import datetime, timedelta

class MetricsCollector:
    """Track test execution metrics: latency, pass/fail rates, log validation."""
    
    def __init__(self):
        self.decision_times = []      # (principle, latency_ms)
        self.decisions = []           # (principle, passed)
        self.log_entries = []         # (principle, decision, metrics)
    
    def record_latency(self, principle: str, latency_ms: float):
        self.decision_times.append((principle, latency_ms))
    
    def record_decision(self, principle: str, passed: bool):
        self.decisions.append((principle, passed))
    
    def record_log_entry(self, principle: str, decision: str, metrics: dict):
        self.log_entries.append((principle, decision, metrics))
    
    def latency_stats(self, principle: str) -> dict:
        """Return min, max, mean latency for a principle."""
        times = [t for p, t in self.decision_times if p == principle]
        return {
            "count": len(times),
            "min_ms": min(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "mean_ms": sum(times) / len(times) if times else 0,
        }
    
    def pass_rate(self, principle: str) -> float:
        """Return percentage of decisions that passed."""
        decisions = [(p, passed) for p, passed in self.decisions if p == principle]
        if not decisions:
            return 0.0
        passed = sum(1 for _, p in decisions if p)
        return (passed / len(decisions)) * 100

# Global metrics collector
metrics = MetricsCollector()

class TestRule1_30DayRecurringTasks(unittest.TestCase):
    """Validate 30-day recurring task interval enforcement."""
    
    def setUp(self):
        self.framework = framework.RecurringTaskManager()
    
    def test_task_creation(self):
        """New tasks should have next_due set to now + 30 days."""
        task = self.framework.create_task("Daily standup", interval_days=30)
        self.assertIsNotNone(task.next_due)
        # ...
    
    # Additional tests for recurrence, completion, edge cases
```

### Phase 2: Test All Rules Independently

For each decision rule in the framework:

**What to test:**
1. **Core logic**: Rule correctly identifies pass vs. fail cases
2. **Thresholds**: Boundary conditions (e.g., 0.74, 0.75, 0.76 for 0.75 threshold)
3. **State transitions**: If the rule involves state (ACTIVE → IDLE → SILENT), test transitions
4. **Data aggregation**: If the rule aggregates (mean confidence, oldest task), verify calculation
5. **Edge cases**: Empty inputs, None values, extreme values, duplicate data

**Template:**

```python
class TestRule2_075ConfidenceThreshold(unittest.TestCase):
    """Validate 0.75 confidence threshold enforcement."""
    
    def test_accept_high_confidence(self):
        """Signals >= 0.75 should be accepted."""
        signal = {"confidence": 0.92, "signal_type": "intent"}
        result = self.framework.evaluate_signal(signal)
        self.assertTrue(result.accepted)
        metrics.record_decision("confidence_threshold", True)
    
    def test_reject_low_confidence(self):
        """Signals < 0.75 should be rejected."""
        signal = {"confidence": 0.65, "signal_type": "intent"}
        result = self.framework.evaluate_signal(signal)
        self.assertFalse(result.accepted)
        metrics.record_decision("confidence_threshold", False)
    
    def test_boundary_0_74(self):
        """Boundary case: 0.74 should be rejected (< 0.75)."""
        signal = {"confidence": 0.74, "signal_type": "intent"}
        result = self.framework.evaluate_signal(signal)
        self.assertFalse(result.accepted)
    
    def test_boundary_0_75(self):
        """Boundary case: 0.75 should be accepted (== 0.75)."""
        signal = {"confidence": 0.75, "signal_type": "intent"}
        result = self.framework.evaluate_signal(signal)
        self.assertTrue(result.accepted)
    
    def test_boundary_0_76(self):
        """Boundary case: 0.76 should be accepted (> 0.75)."""
        signal = {"confidence": 0.76, "signal_type": "intent"}
        result = self.framework.evaluate_signal(signal)
        self.assertTrue(result.accepted)
    
    def test_aggregate_confidence(self):
        """Multiple signals should be aggregated by mean."""
        signals = [
            {"confidence": 0.70, "signal_type": "intent"},
            {"confidence": 0.80, "signal_type": "intent"},
        ]
        mean = (0.70 + 0.80) / 2  # 0.75
        result = self.framework.evaluate_aggregate(signals)
        self.assertTrue(result.accepted)  # Mean >= 0.75
        self.assertAlmostEqual(result.metrics["mean_confidence"], 0.75, places=2)
```

### Phase 3: Measure Decision Latency

**For each rule, measure:**
- Time taken to evaluate the decision
- Latency should be consistent (no sudden spikes)
- Identify which rules are slowest

**Template:**

```python
class TestPerformance(unittest.TestCase):
    """Measure decision latency per rule."""
    
    def test_latency_recurring_tasks(self):
        """30-day task evaluation should be fast (< 10ms)."""
        framework = RecurringTaskManager()
        
        start = time.perf_counter()
        result = framework.check_due_tasks()
        latency_ms = (time.perf_counter() - start) * 1000
        
        metrics.record_latency("30_day_tasks", latency_ms)
        self.assertLess(latency_ms, 10.0, "Latency exceeds 10ms")
    
    def test_latency_confidence_threshold(self):
        """Confidence evaluation should be fast (< 5ms)."""
        framework = MinimalContextProcessor()
        signal = {"confidence": 0.85, "signal_type": "intent"}
        
        start = time.perf_counter()
        result = framework.evaluate_signal(signal)
        latency_ms = (time.perf_counter() - start) * 1000
        
        metrics.record_latency("confidence_threshold", latency_ms)
        self.assertLess(latency_ms, 5.0)
```

### Phase 4: Validate Logging and Metrics

**Test that:**
- All decisions are logged
- Log format is valid (JSON, timestamps, etc.)
- All required metrics are present
- Metrics are human-readable (rounded, not floating-point artifacts)

**Template:**

```python
class TestLoggingValidation(unittest.TestCase):
    """Validate decision logging format and completeness."""
    
    def test_log_format_valid_json(self):
        """Logged metrics must be valid JSON."""
        framework = PersonalFramework()
        
        # Trigger a decision
        framework.check_idle_state()
        
        # Read log file and parse
        with open("framework_decisions.log", "r") as f:
            for line in f:
                if "Silence Protocol" in line:
                    # Extract JSON from log line
                    json_start = line.index("{")
                    json_str = line[json_start:]
                    parsed = json.loads(json_str)  # Should not raise
                    self.assertIn("idle_minutes", parsed)
                    self.assertIn("protocol_engaged", parsed)
    
    def test_metrics_include_threshold(self):
        """Every logged decision must include the threshold."""
        # Trigger decision
        signal = {"confidence": 0.85}
        result = framework.evaluate_signal(signal)
        
        # Verify logged metrics
        self.assertIn("threshold", result.metrics)
        self.assertEqual(result.metrics["threshold"], 0.75)
    
    def test_no_floating_point_artifacts(self):
        """Metrics should be rounded to human-readable precision."""
        # Evaluate with 0.895 mean (from (0.79 + 1.0) / 2)
        signal1 = {"confidence": 0.79}
        signal2 = {"confidence": 1.0}
        result = framework.aggregate_confidence([signal1, signal2])
        
        # Should be rounded to 0.90 or similar, not 0.8949999...
        mean = result.metrics["mean_confidence"]
        self.assertEqual(len(str(mean).split(".")[-1]), 2, "Mean should be 2 decimal places")
```

### Phase 5: Edge Cases and Boundary Conditions

**Test special cases that often break:**
- **Floating-point precision** (0.79 + 1.0 / 2 should equal 0.895)
- **State machine transitions** (ACTIVE → IDLE → SILENT with correct thresholds)
- **Empty collections** (zero tasks, zero signals, zero patterns)
- **Duplicate data** (same pattern recorded twice, same signal twice)
- **Extreme values** (very large or very small inputs)
- **Time boundaries** (task due at exact midnight, idle for exactly 60 minutes)

**Template:**

```python
class TestEdgeCases_MVPThreshold(unittest.TestCase):
    """Test edge cases for 80% MVP completion threshold."""
    
    def test_floating_point_boundary_079_100(self):
        """Mean of 0.79 and 1.0 should be 0.895 (> 0.80, ready to ship)."""
        feature1 = Feature(completion=0.79, is_core=True)
        feature2 = Feature(completion=1.0, is_core=True)
        
        mvp = ExecutionFirstMVPShipper()
        mvp.add_feature(feature1)
        mvp.add_feature(feature2)
        
        is_ready = mvp.is_ready_to_ship()
        mean_completion = (0.79 + 1.0) / 2
        
        self.assertGreaterEqual(mean_completion, 0.80)  # Mathematically true
        self.assertTrue(is_ready, "MVP with 89.5% mean should be ready")
    
    def test_state_transition_idle_to_silent(self):
        """State should transition IDLE → SILENT at exactly 60 minutes."""
        silence = SilenceProtocol()
        
        # Simulate 59:59 idle
        state, m = silence.check_idle_state(idle_seconds=59*60 + 59)
        self.assertEqual(state, IdleState.IDLE)
        
        # Simulate 60:00 idle
        state, m = silence.check_idle_state(idle_seconds=60*60)
        self.assertEqual(state, IdleState.SILENT)
        
        # Simulate 60:01 idle
        state, m = silence.check_idle_state(idle_seconds=60*60 + 1)
        self.assertEqual(state, IdleState.SILENT)
    
    def test_empty_task_list(self):
        """Framework should handle zero tasks gracefully."""
        manager = RecurringTaskManager()
        due_tasks = manager.check_due_tasks()
        self.assertEqual(due_tasks, [])
    
    def test_intent_inference_at_minimum_threshold(self):
        """Inference should trigger at exactly 3 occurrences (minimum)."""
        engine = IntentInferenceEngine(min_occurrences=3)
        
        # 2 occurrences: should NOT infer
        engine.record_context("schedule_meeting")
        engine.record_context("schedule_meeting")
        inferred, m = engine.infer_intent()
        self.assertFalse(inferred, "Should not infer with 2 < 3 occurrences")
        
        # 3 occurrences: should infer
        engine.record_context("schedule_meeting")
        inferred, m = engine.infer_intent()
        self.assertTrue(inferred, "Should infer with 3 >= 3 occurrences")
```

### Phase 6: Root-Cause Analysis of Failures

**When a test fails:**

1. **Do NOT immediately fix the code.** Follow `systematic-debugging` skill.
2. **Investigate the failure:**
   - Is this a logic error in the framework?
   - Is this a floating-point precision issue?
   - Is this a boundary condition the framework doesn't handle?
   - Is this a missing metric in logging?

3. **Document the issue:**
   - What is the symptom?
   - What is the root cause?
   - What part of the framework is affected?
   - What is the severity (critical, high, medium, low)?
   - What are the fix options?

4. **Create fix options:**
   - Option A: Minimal fix (add 1 line)
   - Option B: Proper fix (refactor to be clearer)
   - Option C: Nuclear fix (redesign the principle)
   - Recommend one based on risk/benefit

**Template for issue documentation:**

```markdown
## Issue: [Title]

**Severity:** [CRITICAL | HIGH | MEDIUM | LOW]
**Affected Rule:** [Rule name and number]
**Test Case:** [test_name]

### Symptom
[What the test sees]

Example:
  AssertionError: False is not true
  Test: test_threshold_enforcement_strict
  Input: Feature(completion=0.79) + Feature(completion=1.0)
  Expected: ready_to_ship == True (mean 0.895 >= 0.80)
  Actual: ready_to_ship == False

### Root Cause Analysis

Hypothesis: Floating-point precision issue
  (0.79 + 1.0) / 2 might not exactly equal 0.895 in binary representation

Evidence:
  - Boundary case 0.79-0.80 fails
  - Boundary case 0.80-0.81 passes
  - Mean is mathematically > 0.80 but comparison returns False

### Options

**Option 1 (Minimal):** Add floating-point tolerance
  Code change: 2 lines
  Risk: VERY LOW
  Time: 5 minutes

**Option 2 (Proper):** Round to precision before comparison
  Code change: 3 lines
  Risk: LOW
  Time: 5 minutes

**Option 3 (Nuclear):** Use Decimal for exact arithmetic
  Code change: 10 lines
  Risk: LOW but overkill
  Time: 10 minutes

### Recommendation
Option 1 (floating-point tolerance) because:
- Standard pattern in scientific computing
- Minimal code change
- Well-understood semantics
```

---

## Building the Test Suite: Step by Step

### Step 1: Create Test Structure

```bash
/home/hermes/
├── framework.py                      # The framework to test
├── test_framework_diagnostics.py     # Your test suite (created here)
└── framework_decisions.log           # Log file created by framework
```

### Step 2: Define the MetricsCollector

Copy the template from Phase 1 above.

### Step 3: Create Test Class for Each Rule

For each rule in your framework:
- Copy the test class template
- Adapt rule name, thresholds, inputs
- Add at least 5 tests:
  1. Normal pass case
  2. Normal fail case
  3. Boundary case (at threshold)
  4. Boundary case (just below threshold)
  5. Boundary case (just above threshold)

### Step 4: Add Performance Tests

Measure latency for each rule using the `test_latency_*` template.

### Step 5: Add Logging Validation Tests

Verify all logs are well-formed using the `test_log_format_*` template.

### Step 6: Add Edge Case Tests

For each rule, add 3-5 edge case tests covering:
- Floating-point precision
- State transitions
- Empty collections
- Extreme values

### Step 7: Run the Suite

```bash
python test_framework_diagnostics.py -v
```

Expected output:
```
test_accept_high_confidence ... ok
test_reject_low_confidence ... ok
test_boundary_0_74 ... ok
test_boundary_0_75 ... ok
test_boundary_0_76 ... ok
...
Ran 44 tests in 0.036s
OK (42 passed, 2 failures/errors)
```

### Step 8: Root-Cause Analysis

For each failure/error:
1. Read the error carefully
2. Understand what the test expected vs. what the framework returned
3. Investigate the framework code
4. Document the issue with root cause and fix options

### Step 9: Create Comprehensive Report

Document:
- Overall pass rate (e.g., 95.5% = 42/44)
- Per-rule status (6/6 passed, 5/5 passed, etc.)
- Performance metrics (average latency per rule)
- Issues found (2 identified: LOW severity + MEDIUM severity)
- Fix recommendations with risk assessment

---

## Deliverables from a Diagnostic Session

Organize findings into **5 documents:**

1. **TASK_COMPLETION_REPORT.txt** (or .md)
   - What was accomplished
   - Test results: pass/fail counts
   - Overall framework health score
   - Time to fix issues
   - Production readiness assessment

2. **DIAGNOSTICS_SUMMARY.txt**
   - Executive summary (1-2 pages)
   - The 5 rules: status for each
   - Key findings (strengths + issues)
   - Recommendations

3. **DIAGNOSTICS_REPORT.md**
   - Detailed rule-by-rule analysis
   - Performance metrics (latency, throughput)
   - Logging validation results
   - Edge cases tested
   - Framework health assessment

4. **TECHNICAL_FINDINGS.md**
   - Implementation details per rule
   - Test result breakdown
   - Root cause analysis
   - Performance benchmarks

5. **FIX_IMPLEMENTATION_GUIDE.md**
   - Each identified issue
   - Root cause explanation
   - 2-3 solution options
   - Step-by-step implementation
   - Verification procedures
   - Risk/effort assessment

See `references/diagnostic-deliverable-structure.md` for template structure.

---

## When Issues Are Found

### Floating-Point Precision Issues

**Symptom:** Boundary conditions at thresholds fail (e.g., 0.895 should be >= 0.80 but returns False)

**Root Cause:** Binary floating-point representation doesn't exactly match decimal (0.79 + 1.0 / 2 might be 0.8949999... or 0.8950000...1)

**Solution:**
```python
# Add floating-point tolerance
THRESHOLD = 0.80
TOLERANCE = 0.0001

# Change comparison from:
return core_completion >= THRESHOLD

# To:
return core_completion >= (THRESHOLD - TOLERANCE)
```

### Missing Metrics in Logging

**Symptom:** Test expects metric key in logged output but it's missing, causing KeyError

**Root Cause:** Decision function returns metrics dict but doesn't include all expected fields

**Solution:** Add missing field to metrics dict before returning
```python
metrics = {
    # ... existing fields ...
    "missing_field": calculated_value,  # ADD THIS LINE
}
return decision, metrics
```

### State Machine Logic Gaps

**Symptom:** State transition doesn't happen at boundary (e.g., IDLE → SILENT should happen at 60 min but doesn't)

**Root Cause:** Comparison operator is `>` instead of `>=` or vice versa

**Solution:** Verify comparison logic matches specification
```python
# If rule says "SILENT after 60 minutes", use:
if idle_minutes >= 60:  # >= not >
    state = IdleState.SILENT
```

---

## Common Mistakes to Avoid

1. **Testing only happy path.** Always test boundaries and failure cases.
2. **Omitting latency measurement.** You won't know if performance regresses unless you measure.
3. **Not validating logging.** Log format might be broken in production and you won't know until you check.
4. **Assuming thresholds are correct.** Test them explicitly, especially >= vs >.
5. **Ignoring floating-point precision.** Binary arithmetic ≠ decimal math.
6. **Not documenting issues.** Create comprehensive issue docs so fixes are prioritized correctly.
7. **Fixing without understanding.** Always complete Phase 1 root-cause investigation before proposing fixes.

---

## Support Files

- **`references/diagnostic-deliverable-structure.md`** — Template structure for 5 diagnostic documents
- **`references/floating-point-testing-patterns.md`** — Patterns for testing boundary conditions with floating-point numbers
- **`templates/metrics_collector.py`** — Ready-to-use MetricsCollector class
- **`templates/test_suite_scaffold.py`** — Starter test class structure for 5 rules + logging + performance

---

## Checklist: Comprehensive Framework Diagnostic

- [ ] Test class created for each decision rule
- [ ] At least 3 tests per rule (pass, fail, boundary)
- [ ] Boundary tests for >=0, == threshold, and >threshold cases
- [ ] Performance latency measured for each rule
- [ ] Logging validation tests (JSON format, metrics present)
- [ ] Edge case tests (empty collections, extreme values, floating-point)
- [ ] Test suite runs to completion: python test_diagnostics.py
- [ ] All test results documented
- [ ] Issues identified and root-cause analyzed
- [ ] Fix options proposed with risk assessment
- [ ] Comprehensive report generated
- [ ] Framework health score calculated (pass rate %)
- [ ] Production readiness determined

