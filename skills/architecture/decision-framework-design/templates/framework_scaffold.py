#!/usr/bin/env python3
"""
Scaffold for a new decision framework.

Usage:
  1. Copy this file and rename to your_framework.py
  2. Replace PRINCIPLE_NAME, THRESHOLD, decide_* functions
  3. Add your decision logic
  4. Test with: python your_framework.py
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import logging
import json

# ============================================================================
# LOGGING SETUP
# ============================================================================

class FrameworkLogger:
    """Centralized logger for decisions."""
    
    def __init__(self, log_file: str = "decisions.log"):
        self.logger = logging.getLogger("DecisionFramework")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        self.logger.addHandler(ch)
    
    def log_decision(self, principle: str, decision: str, metrics: Dict[str, Any]):
        """Log a decision with metrics."""
        msg = f"[{principle}] {decision} | {json.dumps(metrics)}"
        self.logger.info(msg)

# ============================================================================
# DATA MODELS
# ============================================================================

class ExampleState(Enum):
    """Example state machine. Replace with your states."""
    STATE_A = "state_a"
    STATE_B = "state_b"
    STATE_C = "state_c"

@dataclass
class ExampleEntity:
    """Example entity. Replace with your data."""
    entity_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# DECISION LOGIC (PURE FUNCTIONS)
# ============================================================================

def decide_example(input_value: float, threshold: float = 0.75) -> tuple[bool, dict]:
    """
    Example decision rule.
    
    Rule: Passes if input >= threshold
    
    Returns: (passes, metrics_dict)
    """
    passes = input_value >= threshold
    metrics = {
        "input_value": input_value,
        "threshold": threshold,
        "passes": passes,
        "gap": input_value - threshold,
    }
    return passes, metrics

# ============================================================================
# MANAGER CLASS
# ============================================================================

class ExampleManager:
    """Manager for principle-specific decisions."""
    
    # Hardcoded threshold for this principle
    THRESHOLD = 0.75
    
    def __init__(self):
        self.entities: Dict[str, ExampleEntity] = {}
        self.logger = FrameworkLogger("decisions.log")
    
    def process(self, entity_id: str, value: float) -> tuple[bool, dict]:
        """
        Process a decision.
        
        Returns: (result, metrics_dict)
        """
        # Call decision logic
        passes, metrics = decide_example(value, threshold=self.THRESHOLD)
        
        # Store entity
        self.entities[entity_id] = ExampleEntity(
            entity_id=entity_id,
            metadata={"value": value, "passes": passes}
        )
        
        # Log decision
        decision_msg = "ACCEPTED" if passes else "REJECTED"
        self.logger.log_decision(
            principle="Example Principle",
            decision=f"Entity {entity_id}: {decision_msg}",
            metrics=metrics
        )
        
        return passes, metrics

# ============================================================================
# UNIFIED ORCHESTRATOR (if multiple managers)
# ============================================================================

class MyFramework:
    """Unified orchestrator for all principles."""
    
    def __init__(self):
        self.logger = FrameworkLogger("decisions.log")
        self.example_manager = ExampleManager()
    
    def get_health(self) -> dict:
        """Return metrics for all principles."""
        return {
            "example_manager": {
                "entities_count": len(self.example_manager.entities),
            }
        }

# ============================================================================
# TESTING & DEMONSTRATION
# ============================================================================

def main():
    """Demonstrate the framework."""
    print("=" * 70)
    print("DECISION FRAMEWORK SCAFFOLD")
    print("=" * 70)
    
    fw = MyFramework()
    
    # Example 1: Pass
    passes, m = fw.example_manager.process("ex_001", value=0.92)
    print(f"\nExample 1: {passes}, metrics: {m}")
    
    # Example 2: Fail
    passes, m = fw.example_manager.process("ex_002", value=0.65)
    print(f"Example 2: {passes}, metrics: {m}")
    
    # Health check
    health = fw.get_health()
    print(f"\nFramework Health: {health}")

if __name__ == "__main__":
    main()
