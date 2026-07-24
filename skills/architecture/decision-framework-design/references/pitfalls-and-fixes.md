# Decision Framework — Pitfalls & Fixes

Common mistakes when building decision frameworks, and how to avoid them.

## Pitfall 1: Magic Numbers in Decision Logic

**Bad:**
```python
def evaluate_ready(completion: float) -> bool:
    return completion >= 0.8  # Where does 0.8 come from?
```

**Good:**
```python
class MVPShippingPrinciple:
    MIN_COMPLETION = 0.80  # Explicitly hardcoded
    
    def evaluate_ready(self, completion: float) -> tuple[bool, dict]:
        """Decision: MVP ready when completion >= 80%."""
        ready = completion >= self.MIN_COMPLETION
        metrics = {
            "completion": completion,
            "min_required": self.MIN_COMPLETION,
            "ready": ready,
        }
        return ready, metrics
```

**Why:** Named constants make thresholds visible, auditable, and changeable without hunting through code.

---

## Pitfall 2: Metrics Omitted or Incomplete

**Bad:**
```python
def infer_intent(pattern_id: str) -> bool:
    count = self.occurrences.get(pattern_id, 0)
    return count >= 3  # No metrics! Can't debug threshold misses.
```

**Good:**
```python
def infer_intent(pattern_id: str) -> tuple[bool, dict]:
    """Decision: Infer intent if 3+ occurrences within 30 days."""
    occurrences = self.get_recent_occurrences(pattern_id, days=30)
    count = len(occurrences)
    inferred = count >= 3
    
    metrics = {
        "pattern_id": pattern_id,
        "occurrence_count": count,
        "min_required": 3,
        "confidence": min(count / 30, 1.0),
        "inferred": inferred,
        "lookback_days": 30,
    }
    return inferred, metrics
```

**Why:** Metrics let you:
- Debug why a decision went the wrong way ("off by 1 occurrence")
- Tune thresholds ("confidence was 0.09, needed 0.1")
- Build audit trails ("show me all decisions near the threshold")

---

## Pitfall 3: State Hidden in Closures or Globals

**Bad:**
```python
# Global state, hard to test
_last_activity = None

def check_idle():
    global _last_activity
    idle_min = (now - _last_activity).total_seconds() / 60
    return idle_min >= 60
```

**Good:**
```python
# State in class, testable
class SilenceProtocol:
    def __init__(self):
        self.last_activity: Optional[datetime] = None
    
    def record_activity(self):
        self.last_activity = datetime.now()
    
    def check_idle(self) -> tuple[str, dict]:
        if self.last_activity is None:
            idle_min = 0.0
        else:
            idle_min = (datetime.now() - self.last_activity).total_seconds() / 60
        
        state = "SILENT" if idle_min >= 60 else "ACTIVE"
        return state, {"idle_minutes": idle_min}
```

**Why:** Class state is testable (inject mock times), loggable (snapshot the state), and auditable (see when it changed).

---

## Pitfall 4: Logging Outside Decision Logic

**Bad:**
```python
passes, metrics = decide_something(value)
if passes:
    logger.info("Decision passed")  # Logging scattered everywhere
else:
    logger.warning("Decision failed")
```

**Good:**
```python
class Manager:
    def process(self, value):
        passes, metrics = decide_something(value)
        
        # Log once, in one place
        self.logger.log_decision(
            principle="My Principle",
            decision="Passed" if passes else "Failed",
            metrics=metrics
        )
        return passes
```

**Why:** Centralized logging ensures:
- Consistent format (JSON metrics always present)
- No forgotten logs (every decision is captured)
- Easy to change output format once (e.g., switch to structured logging backend)

---

## Pitfall 5: Confidence Scoring With No Cap

**Bad:**
```python
confidence = occurrence_count / lookback_days  # Can exceed 1.0 if count > days
# If 40 occurrences in 30 days: confidence = 1.33 (nonsense)
```

**Good:**
```python
confidence = min(occurrence_count / lookback_days, 1.0)  # Always 0.0-1.0
# 40 occurrences in 30 days: confidence = 1.0 (at max)
```

**Why:** Confidence must stay in [0.0, 1.0] to be comparable across decisions. Uncapped values break aggregation and thresholds.

---

## Pitfall 6: Tie-Breaking Ambiguity

**Bad:**
```python
def passes_threshold(value, threshold):
    return value > threshold  # Is the threshold inclusive or exclusive?
    # Caller doesn't know: does 0.75 pass against 0.75 threshold?
```

**Good:**
```python
def passes_threshold(value: float, threshold: float = 0.75) -> tuple[bool, dict]:
    """
    Decision: Accept signals with confidence >= threshold (inclusive).
    
    Examples:
    - 0.75 passes against 0.75 threshold: YES
    - 0.7499 passes against 0.75 threshold: NO
    """
    passes = value >= threshold  # Explicit: >= is inclusive
    metrics = {
        "value": value,
        "threshold": threshold,
        "passes": passes,
        "comparison": ">=",  # Made explicit
    }
    return passes, metrics
```

**Why:** Edge cases at thresholds are where bugs hide. Document the boundary explicitly.

---

## Pitfall 7: Metrics Dict with Nested Prose

**Bad:**
```python
metrics = {
    "decision": "Signal from source X passed confidence check because...",  # Prose!
    "details": "The signal had a confidence score and compared it...",
}
```

**Good:**
```python
metrics = {
    "signal_source": "source_x",
    "confidence": 0.92,
    "threshold": 0.75,
    "passes": True,
    "confidence_gap": 0.17,
}
```

**Why:** JSON metrics must be parseable and queryable. Keep them data, not prose. The principle name + decision message carries the prose.

---

## Pitfall 8: No Audit Trail

**Bad:**
```python
# Decision made, but no record of how or why
def ship_mvp(completion):
    if completion >= 0.8:
        return True  # Silent decision, no log
```

**Good:**
```python
def ship_mvp(self, release_id: str) -> tuple[bool, dict]:
    """Evaluate and log MVP readiness."""
    completion = self.releases[release_id].core_completion
    has_complete_feature = any(f.completion == 1.0 for f in self.releases[release_id].core_features)
    
    ready = (completion >= 0.80) and has_complete_feature
    
    # Log with full context
    metrics = {
        "release_id": release_id,
        "core_completion": completion,
        "has_complete_feature": has_complete_feature,
        "ready": ready,
        "timestamp": datetime.now().isoformat(),
    }
    
    self.logger.log_decision(
        principle="MVP Shipping",
        decision="READY" if ready else "NOT READY",
        metrics=metrics
    )
    
    return ready
```

**Why:** 6 months later, you need to answer "why did we ship v1.2.1?" Log it now so you can audit it then.

---

## Pitfall 9: Threshold Tuning via Code Changes

**Bad:**
```python
# Every time you want to tweak the threshold, you edit code:
class Decision:
    THRESHOLD = 0.75  # Changed to 0.80? Code review needed, redeploy needed
```

**Good for Hardcoded Principles:**
```python
# This is OK if the threshold is a core principle (code review intended)
class MVPShipper:
    MIN_COMPLETION = 0.80  # Hardcoded. Change = philosophy change. Intentional.
```

**Good for Tuning Knobs:**
```python
# This is OK if the threshold is tuning, not principle
class IdleDetector:
    DEFAULT_IDLE_MINUTES = 60
    
    def __init__(self, idle_threshold: int = DEFAULT_IDLE_MINUTES):
        self.idle_threshold = idle_threshold  # Configurable
        # This can be passed from config, no code change needed
```

**Why:** Know which is which. Principles should require code review. Knobs should be configurable.

---

## Pitfall 10: State Transitions Without Recording

**Bad:**
```python
def check_idle(self):
    idle_min = (now - self.last_activity).total_seconds() / 60
    
    if idle_min >= 60:
        self.state = IdleState.SILENT  # State changed, but no record
    
    return self.state
```

**Good:**
```python
@dataclass
class Transition:
    from_state: IdleState
    to_state: IdleState
    at: datetime
    reason: str

class SilenceProtocol:
    def check_idle(self) -> tuple[IdleState, dict]:
        idle_min = (now - self.last_activity).total_seconds() / 60
        new_state = IdleState.SILENT if idle_min >= 60 else IdleState.ACTIVE
        
        # Record transition
        if new_state != self.state:
            self.transitions.append(Transition(
                from_state=self.state,
                to_state=new_state,
                at=datetime.now(),
                reason=f"idle_minutes={idle_min}"
            ))
            self.state = new_state
        
        metrics = {
            "idle_minutes": idle_min,
            "current_state": self.state.value,
            "transition": new_state != self.state,
        }
        
        return self.state, metrics
```

**Why:** Transitions are decisions too. Log them. Audit trails need to show state changes, not just the final state.

---

## Pitfall 11: Aggregating Signals Without Checking Count

**Bad:**
```python
def aggregate_confidence(signals: list[float]) -> float:
    return sum(signals) / len(signals)  # What if signals is empty?
```

**Good:**
```python
def aggregate_confidence(signals: list[float], threshold: float = 0.75) -> tuple[bool, dict]:
    """
    Decision: Aggregate multiple confidence signals.
    
    Rule: Accept if mean(signals) >= threshold
    Edge case: No signals → REJECT
    """
    if not signals:
        return False, {
            "signal_count": 0,
            "confidence": None,
            "threshold": threshold,
            "passes": False,
            "reason": "no_signals",
        }
    
    mean_conf = sum(signals) / len(signals)
    passes = mean_conf >= threshold
    
    return passes, {
        "signal_count": len(signals),
        "confidence_values": signals,
        "mean_confidence": round(mean_conf, 3),
        "threshold": threshold,
        "passes": passes,
    }
```

**Why:** Empty edge cases hide in aggregation. Check the count, and return explicit metrics for the no-signal case.

---

## Checklist Before Shipping a Framework

- [ ] All thresholds named constants (no magic numbers)
- [ ] All decisions return (result, metrics_dict)
- [ ] Metrics include threshold and gap
- [ ] Logging is centralized and JSON-formatted
- [ ] State lives in classes, not closures
- [ ] Tie-breaking rules documented (>= vs >)
- [ ] Edge cases handled (empty lists, None values, boundary conditions)
- [ ] Transitions recorded (if state machine)
- [ ] Audit trail complete (can replay decision 6 months later)
- [ ] Unit tests for each decision function
- [ ] Integration test of full orchestrator
