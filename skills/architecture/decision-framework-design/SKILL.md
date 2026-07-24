---
name: decision-framework-design
description: "Build explicit decision-making frameworks with quantified rules, state machines, and comprehensive metrics logging. Useful for policy codification, principle-driven systems, and decision audit trails."
version: 1.0.0
author: Friday (Tanzim's AI)
license: MIT
tags: [architecture, design-patterns, quantified-logic, decision-systems, state-machines, logging, metrics]
related_skills: [python-project-structure, logging-and-observability]
---

# Decision-Framework Design

When you need to **codify decision-making principles as explicit rules** — whether it's recurring task intervals, confidence thresholds, intent inference, idle protocols, or MVP shipping readiness — the pattern in this skill provides a reusable scaffold: clear state machines, quantified thresholds, and metrics logging for auditability.

Use this when:
- You're building a system that must make repeatable decisions based on explicit, measurable criteria
- You need an audit trail (who decided what, why, with what confidence)
- The decision logic involves thresholds, state transitions, or pattern recognition
- Multiple principles coexist and need unified orchestration
- Non-technical stakeholders need to verify the logic is correct ("Show me the threshold.")

Do NOT use this for:
- One-off heuristics or quick scripts
- Decisions that are inherently fuzzy or rely on LLM judgment alone
- Systems where the rules change frequently

---

## Core Pattern

A decision framework has **five layers**:

### 1. Data Models (dataclasses + enums)

Define the entities your decisions operate on. Use `@dataclass` for immutable state snapshots, and enums for finite state spaces.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

class IdleState(Enum):
    ACTIVE = "active"      # < 30 min idle
    IDLE = "idle"          # 30-60 min idle
    SILENT = "silent"      # >= 60 min idle

@dataclass
class ActivityLog:
    activity_id: str
    activity_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    
@dataclass
class RecurringTask:
    task_id: str
    name: str
    description: str
    interval_days: int = 30        # Hardcoded principle
    created_at: datetime = field(default_factory=datetime.now)
    completion_count: int = 0
    last_executed: Optional[datetime] = None
    next_due: Optional[datetime] = None
```

**Principles for data models:**
- Timestamps for everything you might want to audit later
- Use enums for state, not strings (type-safe, finite)
- Hardcode thresholds as class defaults, not magic numbers scattered in methods
- Make dataclasses immutable (`frozen=True`) for decision snapshots
- Use `Optional[T]` sparingly — prefer defaults over None

### 2. Decision Logic (explicit, quantified rules)

Write the decision rule as a pure function or method that returns:
- A boolean (pass/fail)
- A metrics dict (for logging)

**Never return just a boolean.** Always include the metrics — they make auditing, debugging, and threshold tuning possible.

```python
def evaluate_idle_state(idle_minutes: float) -> tuple[IdleState, dict]:
    """
    Determine idle state based on elapsed time.
    
    Rules:
    - ACTIVE:  < 30 min
    - IDLE:    30 <= min < 60
    - SILENT:  >= 60 min (protocol engaged)
    """
    ACTIVE_THRESHOLD = 30
    IDLE_THRESHOLD = 60
    
    state = (
        IdleState.ACTIVE if idle_minutes < ACTIVE_THRESHOLD else
        IdleState.IDLE if idle_minutes < IDLE_THRESHOLD else
        IdleState.SILENT
    )
    
    metrics = {
        "idle_minutes": idle_minutes,
        "active_threshold": ACTIVE_THRESHOLD,
        "idle_threshold": IDLE_THRESHOLD,
        "current_state": state.value,
        "protocol_engaged": state == IdleState.SILENT,
    }
    
    return state, metrics

def evaluate_confidence_threshold(signal_confidence: float, threshold: float = 0.75) -> tuple[bool, dict]:
    """
    Accept signals only above confidence threshold.
    
    Rule: passes = (confidence >= threshold)
    """
    passes = signal_confidence >= threshold
    metrics = {
        "confidence": signal_confidence,
        "threshold": threshold,
        "passes": passes,
        "confidence_gap": signal_confidence - threshold,
    }
    return passes, metrics

def evaluate_recurring_task(task: RecurringTask) -> tuple[bool, dict]:
    """
    Determine if a recurring task is due.
    
    Rule: is_due = (now >= next_due) where next_due = last_executed + interval_days
    """
    now = datetime.now()
    is_due = task.next_due is not None and now >= task.next_due
    metrics = {
        "task_id": task.task_id,
        "interval_days": task.interval_days,
        "completion_count": task.completion_count,
        "last_executed": task.last_executed.isoformat() if task.last_executed else None,
        "next_due": task.next_due.isoformat() if task.next_due else None,
        "is_due": is_due,
    }
    return is_due, metrics
```

**Principles for decision logic:**
- Name functions after the decision, not the implementation (`evaluate_*`, not `calculate_`).
- Hardcode thresholds as named constants in the function, with comments explaining the rule.
- Return a tuple: (result, metrics_dict). Never omit metrics.
- Make metrics human-readable: `0.75`, not `75` or `0.7500000001`.
- Include the threshold in the metrics, not just the result.
- Be explicit about tie-breaking: `>=` vs `>`, inclusive vs exclusive ranges.

### 3. Orchestrator / Manager Class

Create a single class per principle (or a unified orchestrator if principles are tightly coupled). The orchestrator:
- Holds mutable state (dicts of entities, collections, counters)
- Exposes methods that call decision logic + log metrics
- Never holds state *in the decision functions* — only in the manager

```python
class SilenceProtocol:
    """Manage idle state and silence protocol engagement."""
    
    def __init__(self):
        self.activities: dict[str, ActivityLog] = {}
        self.last_activity_time: Optional[datetime] = None
    
    def record_activity(self, activity_id: str, activity_type: str, description: str = "") -> dict:
        """Record an activity and return metrics."""
        activity = ActivityLog(
            activity_id=activity_id,
            activity_type=activity_type,
            description=description,
        )
        self.activities[activity_id] = activity
        self.last_activity_time = activity.timestamp
        
        # Trigger logging (see layer 4)
        metrics = {
            "activity_id": activity_id,
            "activity_type": activity_type,
            "timestamp": activity.timestamp.isoformat(),
        }
        return metrics
    
    def check_idle_state(self) -> tuple[IdleState, dict]:
        """
        Evaluate current idle state.
        
        Returns: (state, metrics_dict)
        """
        if self.last_activity_time is None:
            # No activity recorded yet — treat as just-activated
            idle_minutes = 0.0
        else:
            idle_minutes = (datetime.now() - self.last_activity_time).total_seconds() / 60
        
        state, metrics = evaluate_idle_state(idle_minutes)
        return state, metrics
```

**Principles for orchestrators:**
- One manager per principle (cohesion)
- Mutable state lives in the manager; decision logic is pure
- Methods return the same shape as decision functions: (result, metrics)
- Keep the manager thin — it dispatches to decision logic, doesn't reimplement rules

### 4. Centralized Logging

Create a single logger that:
- Logs to both console and file
- Uses JSON format for metrics (parseable, queryable)
- Includes the principle name and human-readable decision message
- Works as a cross-cutting concern across all managers

```python
import logging
import json

class FrameworkLogger:
    def __init__(self, log_file: str = "decisions.log"):
        self.logger = logging.getLogger("DecisionFramework")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler (JSON)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        self.logger.addHandler(console_handler)
    
    def log_decision(self, principle: str, decision: str, metrics: dict):
        """Log a decision with metrics in JSON format."""
        log_entry = {
            "principle": principle,
            "decision": decision,
            "metrics": metrics,
        }
        self.logger.info(f"[{principle}] {decision} | {json.dumps(metrics)}")

# Usage:
logger = FrameworkLogger("framework_decisions.log")
logger.log_decision(
    principle="Silence Protocol (60 min Idle)",
    decision="State: SILENT (protocol engaged)",
    metrics={"idle_minutes": 65.5, "state": "silent", "protocol_engaged": True},
)
```

**Principles for logging:**
- One logger instance per process (singleton)
- JSON metrics for parsing (no prose in the metrics dict)
- Include principle name + human-readable decision message + structured metrics
- Log at INFO for major decisions, DEBUG for intermediate steps
- Rotate logs if they grow large

### 5. Unified Orchestrator (optional, for multi-principle systems)

If you have multiple principles, create a single orchestrator that ties them together:

```python
class PersonalFramework:
    """Orchestrate all decision principles."""
    
    def __init__(self):
        self.logger = FrameworkLogger("framework_decisions.log")
        self.recurring_tasks = RecurringTaskManager()
        self.minimal_context = MinimalContextProcessor()
        self.intent_inference = IntentInferenceEngine()
        self.silence_protocol = SilenceProtocol()
        self.mvp_shipping = ExecutionFirstMVPShipper()
    
    def get_framework_health(self) -> dict:
        """Return metrics for all 5 principles."""
        return {
            "recurring_tasks": self.recurring_tasks.stats(),
            "minimal_context": self.minimal_context.stats(),
            "intent_inference": self.intent_inference.stats(),
            "silence_protocol": self.silence_protocol.stats(),
            "mvp_shipping": self.mvp_shipping.stats(),
        }
```

---

## Thresholds: Hardcoding vs. Configuration

**Hardcode** the threshold if:
- It's a core principle (e.g., "MVP ships at 80% completion")
- Changing it requires code review
- It's a business rule, not a knob

**Make configurable** if:
- It's tuning (idle timeout, retry counts, backoff multipliers)
- You expect to adjust it without code changes
- It's environment-specific

Example (hybrid):
```python
class IntentInferenceEngine:
    MIN_OCCURRENCES = 3              # Hardcoded principle
    LOOKBACK_DAYS = 30               # Hardcoded principle
    
    def __init__(self, min_occurrences: int = MIN_OCCURRENCES):
        self.min_occurrences = min_occurrences  # Configurable
        # ...
```

---

## Common Patterns

### Pattern: Aggregating Multiple Signals

When multiple signals feed into one decision:

```python
def aggregate_confidence(signals: list[float], threshold: float = 0.75) -> tuple[bool, dict]:
    """
    Decision: pass if mean(signals) >= threshold.
    """
    if not signals:
        return False, {"confidence": None, "threshold": threshold, "signal_count": 0, "passes": False}
    
    mean_confidence = sum(signals) / len(signals)
    passes = mean_confidence >= threshold
    
    metrics = {
        "signal_count": len(signals),
        "confidence_values": signals,
        "mean_confidence": round(mean_confidence, 3),
        "threshold": threshold,
        "passes": passes,
    }
    return passes, metrics
```

### Pattern: State Machine Transitions

When decisions change state, track the transition:

```python
@dataclass
class StateTransition:
    from_state: IdleState
    to_state: IdleState
    at_time: datetime
    reason: str

class StateTracker:
    def __init__(self):
        self.current_state = IdleState.ACTIVE
        self.transitions: list[StateTransition] = []
    
    def check_and_transition(self, idle_minutes: float) -> tuple[IdleState, dict]:
        """Evaluate idle state and record transition if state changed."""
        new_state, metrics = evaluate_idle_state(idle_minutes)
        
        if new_state != self.current_state:
            transition = StateTransition(
                from_state=self.current_state,
                to_state=new_state,
                at_time=datetime.now(),
                reason=f"idle_minutes={idle_minutes}",
            )
            self.transitions.append(transition)
            self.current_state = new_state
            metrics["transition"] = {
                "from": self.current_state.value,
                "to": new_state.value,
                "at": transition.at_time.isoformat(),
            }
        
        return new_state, metrics
```

### Pattern: Confidence Scoring

When inferring intent from patterns, score confidence based on recency and frequency:

```python
def infer_confidence(occurrence_count: int, lookback_days: int, min_occurrences: int = 3) -> float:
    """
    Confidence increases with occurrence count, capped at 1.0.
    Formula: min(occurrence_count / lookback_days, 1.0)
    """
    return min(occurrence_count / lookback_days, 1.0)

# Usage:
confidence = infer_confidence(occurrence_count=5, lookback_days=30)
# confidence ≈ 0.1667
```

---

## Testing Decision Logic

Unit-test the decision functions independently:

```python
def test_evaluate_idle_state():
    """Test idle state transitions."""
    state, m = evaluate_idle_state(10.0)
    assert state == IdleState.ACTIVE
    assert m["protocol_engaged"] is False
    
    state, m = evaluate_idle_state(45.0)
    assert state == IdleState.IDLE
    
    state, m = evaluate_idle_state(75.0)
    assert state == IdleState.SILENT
    assert m["protocol_engaged"] is True

def test_evaluate_confidence_threshold():
    """Test threshold acceptance."""
    passes, m = evaluate_confidence_threshold(0.92, threshold=0.75)
    assert passes is True
    assert m["confidence_gap"] == 0.17
    
    passes, m = evaluate_confidence_threshold(0.65, threshold=0.75)
    assert passes is False
```

---

## Red Flags

These patterns indicate a weak decision framework:

- **Magic numbers scattered through code.** Extract to named constants at the top of the function.
- **Metrics omitted or incomplete.** If you can't answer "how close was this to the threshold?", metrics are missing.
- **Logging happens outside decision logic.** Logging should be baked into the manager/orchestrator, not the caller.
- **State hidden in function closures or globals.** Keep all mutable state in managers/classes, never in nested scopes.
- **Threshold "tuning" via code changes.** If you find yourself changing `0.75` to `0.8` frequently, make it configurable.
- **No audit trail.** If you can't reproduce a decision 6 months later, logging is insufficient.
- **Decisions vary by context.** If the same rule applies differently in different branches, that's a sign you need more principles, not less.

---

## Support Files in This Skill

- **`references/personal-framework-session.md`** — Full implementation walkthrough of a 5-principle framework (production reference)
- **`references/pitfalls-and-fixes.md`** — 11 common mistakes in decision framework design and how to avoid them
- **`references/validating-a-classifier-framework.md`** — How to stress-test a framework AFTER building it: fitted-vs-validated match rates, the collinearity trap (axes that are secretly one, AND collinearity that lives in the data not the formula), the remediation hierarchy (fix the primitive — never bolt on a threshold floor/override, which repeats the original error), rescaling thresholds after a primitive redesign, dry-running rule blast radius before writing, red/blue adversarial validation, the unstated-invariant finding (a formula that's 97/97-correct yet latently broken because it silently depends on an unenforced correlation — "unguarded, not wrong"), pulling the spec before verdict to avoid a confident-but-wrong blind critique, and honest verdict discipline (Nimbus Engine session)
- **`templates/framework_scaffold.py`** — Starter template for building a new framework (copy and customize)

## External References

- **Pattern: Dataclass Models** — Python docs: https://docs.python.org/3/library/dataclasses.html
- **Pattern: Enums** — Python docs: https://docs.python.org/3/library/enum.html
- **Pattern: Structured Logging** — ELK stack, JSON parsing: https://www.elastic.co/what-is/structured-logging

---

## Checklist for a New Framework

- [ ] All decision rules written explicitly (not implicit in code)
- [ ] Each rule has a hardcoded threshold or formula
- [ ] Thresholds documented in code comments
- [ ] Dataclass models for all entities
- [ ] Enum for finite state spaces (never string states)
- [ ] Decision logic returns (result, metrics_dict)
- [ ] Metrics include the threshold, gap, and context
- [ ] Centralized logger with JSON format
- [ ] Orchestrator/manager classes for mutable state
- [ ] Unit tests for each decision function
- [ ] Audit trail (logs show who decided what)

