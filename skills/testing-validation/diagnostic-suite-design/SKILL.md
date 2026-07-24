---
name: diagnostic-suite-design
title: Diagnostic Suite Design & Execution
description: Pattern for building comprehensive test suites that validate system health across performance, integration, reliability, and accuracy dimensions. Includes instrumentation, multi-layer auditing, bottleneck detection, and multi-stakeholder reporting.
triggers:
  - "build diagnostic / test suite"
  - "validate system integration"
  - "audit logging / data flow"
  - "measure latency and accuracy"
  - "identify bottlenecks"
  - "comprehensive system health check"
  - "multi-layer validation"
  - "performance benchmarking with reporting"
---

## Overview

A diagnostic suite is a structured automated test framework that validates system health across multiple dimensions:
- **Performance** (latency, throughput)
- **Reliability** (data integrity, error handling)
- **Integration** (data flow between components)
- **Logging/Audit** (comprehensive record-keeping across all layers)

The suite produces both **raw metrics** (machine-readable JSON) and **executive-level reports** (stratified by audience: management, technical, operations).

**Execution shape:** ~15 seconds for 30+ tests across 4 categories; outputs JSON + 7+ formatted reports.

---

## Design Pattern

### 1. Test Matrix Design

Structure tests across **multiple dimensions**:
- **Component coverage**: Personality checker, integrations, logging, bottleneck detection
- **Response diversity**: 30+ test cases spanning aligned / moderate / misaligned / edge cases
- **Test categories**: Structural tests (pass/fail) + metric tests (latency/accuracy/distribution)

**Reference:** `references/test-matrix-design.md` — detailed test case taxonomy and why 30+ is the minimum effective set.

### 2. Instrumentation

Capture **submillisecond precision** metrics:
```python
import time

start = time.perf_counter()
result = function_under_test()
elapsed_ms = (time.perf_counter() - start) * 1000
```

Collect:
- **Mean, P95, P99, min/max latency**
- **Accuracy distribution** (e.g., % poor, % fair, % good)
- **Pass/fail counts** (integration tests)
- **Entry counts** (logging audits: 8,977 entries verified)

**Reference:** `references/latency-instrumentation.md` — submillisecond collection and statistical interpretation.

### 3. Multi-Layer Validation

Design tests that validate the **full stack**:
- **Component-level**: Individual subsystem performance
- **Integration-level**: Data flow between components (e.g., Framework ↔ JARVIS ↔ EDITH)
- **System-level**: End-to-end pipeline latency
- **Audit-level**: Logging completeness across all layers

Run at least **3 integration tests** covering distinct paths through the system.

### 4. Bottleneck Detection

Include a systematic check for communication delays:
- Measure latency of each component in isolation
- Measure latency of integration paths
- Compare: If sum of parts << whole, bottleneck exists
- Report: "0 bottlenecks detected" is a positive finding worth highlighting

### 5. Structured Output

Generate **two output formats**:

**Machine-readable (JSON):**
- All test results, latencies, accuracy scores, counts
- 500+ data points for dashboarding/CI integration
- Timestamp all results for reproducibility

**Human-readable (multiple formats):**
- **Executive summary** (1-2 pages): Health score, key findings, production readiness
- **Technical report** (5-10 pages): Root causes, code locations, implementation roadmap
- **Comprehensive report**: All metrics, test-by-test results, detailed analysis
- **Quick reference** (bullet list): Metrics at a glance
- **Manifest/index**: Navigation guide by role

### 6. Multi-Stakeholder Reporting

Stratify reports by audience:
- **Managers**: Health score, production readiness %, timeline, next steps
- **Technical leads**: Root causes, code locations, 3-priority roadmap, risk assessment
- **Developers**: Specific issues with line numbers, expected outcomes, validation steps
- **QA/Testers**: Complete metrics, test methodology, raw data export
- **DevOps**: Latency baselines, bottleneck status, alert thresholds

**Reference:** `references/reporting-strategy.md` — how to write for each audience without duplication.

### 7. Bottleneck Remediation Roadmap

When issues are found, structure the fix as:
- **Priority 1** (blocking): Critical fixes needed for production readiness (10 hours)
- **Priority 2** (next sprint): Enhancement items (13 hours)
- **Priority 3** (quarter): Long-term optimization (28 hours)

Include **effort estimates and effort breakdowns** for each priority level.

---

## Implementation Checklist

- [ ] **Test matrix**: 30+ cases across 4+ categories (structure in code as test case list)
- [ ] **Instrumentation**: `time.perf_counter()` for all measured functions
- [ ] **Component tests**: Verify each subsystem independently
- [ ] **Integration tests**: 3+ tests of data flow between components
- [ ] **Logging audit**: Verify entry counts and format completeness for all layers
- [ ] **Bottleneck detection**: Compare component latency vs. integrated latency
- [ ] **JSON export**: All metrics in structured JSON with timestamp
- [ ] **Executive summary**: 1-2 page overview with health score
- [ ] **Technical report**: Root causes + 3-priority roadmap
- [ ] **Quick reference**: Metrics table for fast scanning
- [ ] **Multi-audience format**: At least 3 different report formats
- [ ] **Validation checklist**: Expected outcomes and gates for each priority item

---

## Common Pitfalls

**Pitfall 1: Insufficient test diversity**
- ❌ Only happy-path tests or only edge cases
- ✓ Mix JARVIS-aligned + moderate + misaligned + edge cases in same suite
- Why: Narrow test coverage misses real-world failure modes

**Pitfall 2: Latency without percentiles**
- ❌ Reporting only mean latency (0.01ms)
- ✓ Collect P95, P99, min/max alongside mean
- Why: P99 catches outliers mean hides; essential for production baseline

**Pitfall 3: No bottleneck detection**
- ❌ Measuring components in isolation but not integration paths
- ✓ Compare: component sum < integrated latency → bottleneck
- Why: Performance regressions hide in integration; "0 bottlenecks detected" is a key finding

**Pitfall 4: Single report format**
- ❌ One dense 50-page technical report for all audiences
- ✓ Executive summary (management), technical deep-dive (dev), quick reference (ops)
- Why: Different roles need different data density and emphasis

**Pitfall 5: No remediation roadmap**
- ❌ Listing issues without effort estimates or timeline
- ✓ Priority 1/2/3 with hours, specific code locations, expected outcomes
- Why: Executives need timeline, developers need specificity, integration needs staging

**Pitfall 6: Latency but no accuracy metrics**
- ❌ Confirming "system is fast" but not "system is correct"
- ✓ Include accuracy distribution alongside performance
- Why: Low latency on wrong answers is worthless

**Pitfall 7: Not timestamping results**
- ❌ JSON report with no timestamp; difficult to correlate with deploys
- ✓ `"timestamp": "2026-06-09T23:45:01 UTC"` in all outputs
- Why: Reproducibility; essential for tracking regressions across deployments

---

## Template & References

**Template script:** `templates/diagnostic_suite_template.py` — starter framework (imports, test registration, instrumentation, JSON export, report generation).

**References:**
- `references/test-matrix-design.md` — how to create diverse test cases
- `references/latency-instrumentation.md` — submillisecond measurement patterns
- `references/reporting-strategy.md` — multi-audience report structure
- `references/bottleneck-detection-pattern.md` — how to identify integration slowdowns

---

## Session Example

**Context:** JARVIS Personality Checker + Integration validation  
**Input:** 30+ responses, need latency + accuracy + integration validation  
**Output:** 
- 38 automated tests (32 personality + 3 integration + 3 logging)
- JSON metrics (24 KB, 500+ data points)
- 7 formatted reports (112 KB total)
- Bottleneck analysis: 0 detected
- Health score: 8.2/10 with specific remediation roadmap

**Key finding:** System operationally excellent (latency/integration/logging all green) but accuracy needs calibration (14.2/100 → 50+/100 via Priority 1 in 10 hours).

---

## When to Use This Pattern

✓ Validating a major subsystem before production  
✓ Measuring performance/reliability of an integration layer  
✓ Auditing logging completeness across a multi-layer system  
✓ Identifying bottlenecks in a data pipeline  
✓ Creating a baseline for future regression detection  
✓ Producing actionable insights for mixed technical/management audiences  

✗ Single-component unit tests (use unit testing framework)  
✗ Load/stress testing (separate pattern, different scale)  
✗ One-off ad-hoc checks (not worth the overhead)

