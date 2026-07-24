# Personal Framework Session — Reference Implementation

**Session Date:** June 9, 2026  
**Deliverable:** Full 5-principle decision framework module  
**Location:** `/home/hermes/framework.py` (33 KB)

## Overview

A complete, production-ready implementation of the decision-framework-design pattern. Codifies 5 core personal principles:

1. **30-day Recurring Task Design** — Execute recurring tasks every 30 days
2. **Minimal Context with 0.75 Confidence Threshold** — Accept only high-confidence signals
3. **Intent Inference from Patterns** — Infer intent from 3+ occurrences within 30 days
4. **Silence Protocol at 60 Min Idle** — Enter silence mode when idle for 60+ minutes
5. **Execution-First MVP Shipping** — Ship MVP when 80% core completion + 1 complete feature

## Architecture

### Core Classes

- **FrameworkLogger** — Centralized logging with dual handlers (console + file), JSON metrics
- **RecurringTask / RecurringTaskManager** — Principle 1 (30-day intervals)
- **ContextSignal / MinimalContextProcessor** — Principle 2 (0.75 threshold)
- **PatternOccurrence / IntentInferenceEngine** — Principle 3 (pattern-based inference)
- **IdleState / ActivityLog / SilenceProtocol** — Principle 4 (60-min idle state machine)
- **Feature / MVPRelease / ExecutionFirstMVPShipper** — Principle 5 (MVP readiness)
- **PersonalFramework** — Unified orchestrator for all 5 principles

### Key Patterns Used

1. **Dataclass Models** — Immutable snapshots for entities (RecurringTask, ContextSignal, etc.)
2. **Enum State Machines** — IdleState enum (ACTIVE, IDLE, SILENT) with explicit transitions
3. **Decision Logic (pure functions)** — Each decision rule returns (result, metrics_dict)
4. **Metrics Logging** — JSON-formatted metrics captured for every decision
5. **Centralized Logger** — Single FrameworkLogger instance with both console and file output

## Quantified Logic Reference

| Principle | Hardcoded Threshold | Formula / Rule |
|-----------|-------------------|-----------------|
| Recurring Tasks | 30 days | `next_due = last_executed + timedelta(days=30)` |
| Minimal Context | 0.75 | `passes = (confidence >= 0.75)` |
| Intent Inference | 3 occurrences | `confidence = min(count / 30, 1.0)` if count >= 3 and within 30 days |
| Silence Protocol | 60 minutes | SILENT state if `idle_minutes >= 60` |
| MVP Shipping | 80% core completion | `ready = (core_completion >= 0.80) AND (exists feature at 1.0)` |

## Code Structure

```
framework.py (800+ lines):
├── FrameworkLogger
├── Principle 1: RecurringTask, RecurringTaskManager
├── Principle 2: ContextSignal, MinimalContextProcessor
├── Principle 3: PatternOccurrence, IntentInferenceEngine
├── Principle 4: IdleState enum, ActivityLog, SilenceProtocol
├── Principle 5: Feature, MVPRelease, ReleaseStatus, ExecutionFirstMVPShipper
├── PersonalFramework (unified orchestrator)
└── main() — demonstration
```

## Logging Output Example

```json
{
  "principle": "Minimal Context (0.75 Confidence Threshold)",
  "decision": "Signal s1 ACCEPTED",
  "metrics": {
    "signal_id": "s1",
    "confidence": 0.92,
    "threshold": 0.75,
    "passes": true,
    "confidence_gap": 0.17,
    "source": "src"
  }
}
```

All decisions are logged to `/home/hermes/framework_decisions.log` with this JSON structure.

## Testing & Validation

All 5 principles verified functional:

```
✓ Principle 1 (30-day): Task interval = 30 days
✓ Principle 2 (0.75 Confidence): Signal passed = True, conf=0.92
✓ Principle 3 (Intent): Pattern inferred = True, occurrences=3
✓ Principle 4 (60 min Idle): State = active, idle=0.0 min
✓ Principle 5 (MVP Ship): Ready = True, core_completion=1.0
```

## Design Decisions

1. **Unified Orchestrator Pattern** — All 5 principles under one PersonalFramework class for cohesion, not separate modules.
2. **Hardcoded Thresholds** — Core principles live in code constants (0.75, 30, 60, 80), not config files. Changing them requires code review.
3. **Metrics Always** — Every decision returns (result, metrics_dict). Metrics include threshold, gap, and context for debugging and tuning.
4. **No Silent Failures** — Logging is baked into orchestrators; decision logic is pure and testable.
5. **Type Safety** — Full type hints, enums for state, dataclasses for immutability.

## Lessons

1. **Dataclass factories** — Using `field(default_factory=datetime.now)` for timestamps ensures each instance gets a fresh timestamp, not a shared reference.
2. **State machines over strings** — IdleState enum prevents typos and makes transitions explicit.
3. **Metrics as first-class** — If you can't measure a decision, you can't audit it. Always return metrics.
4. **Aggregation patterns** — When multiple signals feed into one decision, compute mean/max explicitly and log all values.
5. **Logging placement** — Put logging in the manager/orchestrator, not the caller. Decisions logic stays pure.

## Related Skills

- **python-project-structure** — For module organization
- **logging-and-observability** — For logger setup and rotation
- This skill: **decision-framework-design** — The pattern itself

---

**To use this pattern in a new project:**

1. Define your principles (explicit, measurable rules)
2. Create dataclass models for entities
3. Write pure decision functions returning (result, metrics_dict)
4. Build manager classes for mutable state
5. Centralize logging with JSON metrics
6. Test decision logic independently
7. Wrap in a unified orchestrator if multiple principles coexist
