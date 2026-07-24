---
name: personal-framework-schema
type: design_methodology
domain: agent-systems, autonomous-workflows
triggers:
  - User wants to define how an autonomous agent should behave
  - Building a personal operating system for an AI agent
  - Translating work principles into agent decision rules
  - Designing principle-driven workflow automation
  - Creating confidence thresholds and decision logic for agent autonomy
  - Documenting how minimal input maps to autonomous action

description: |
  Design a complete personal framework schema that translates a user's 
  work principles, decision rules, and communication preferences into an 
  autonomous agent's operating system. Output includes:
  - Core principle registry (mapped to agent behavior)
  - Framework translation layers (decision rules, workflow logic, communication)
  - Confidence scoring and action thresholds
  - Principle → behavior example mappings
  - Implementation guides, decision trees, validation checklists

outputs:
  - YAML schema (principles + framework layers + confidence scoring)
  - Markdown examples (3+ principle → behavior real-world mappings)
  - Quick reference implementation guide (decision trees, templates)
  - Visual guides (flow diagrams, principle matrices, walkthroughs)
  - Executive summary and navigation index

process:
  step_1_principle_gathering:
    description: |
      Identify and document the 3-5 core principles that govern the user's work.
      Principles should cover:
        • How they make decisions (decision rules)
        • How they prefer to communicate (communication style)
        • When/how they want the agent to act (workflow logic)
        • How tasks recur and should be automated (work cadence)
        • What execution approach they value (execution philosophy)
      For each principle: name, definition, priority level, category
      
  step_2_framework_translation:
    description: |
      Map each principle to specific agent behaviors and triggers.
      Create the translation layer with four main sections:
        • Decision Rules Layer: Autonomy thresholds, context assessment, inference rules
        • Workflow Logic: Autonomous action patterns, execution approach
        • Communication Layer: Message structure, context depth, assumption surfacing
        • Work Cadence: Scheduling rules, silence protocols, async reporting
      For each mapping: trigger condition → decision logic → Friday's behavior
      
  step_3_confidence_scoring:
    description: |
      Define confidence thresholds for agent action. Minimum three thresholds:
        1. Intent inference (when to act on sparse context)
        2. Autonomy readiness (when to fully automate vs. propose hybrid)
        3. Action readiness (when confidence is sufficient to proceed)
      For each threshold: scoring factors, weights, minimum score to act,
      action taken if below threshold
      
  step_4_behavior_templates:
    description: |
      Create 4-6 behavior templates showing how principles manifest in actual actions.
      Each template includes:
        • Principle ID and trigger condition
        • Step-by-step implementation sequence
        • Decision points and branching logic
        • Example successful outcome
      Templates should be copy-able patterns for future agent sessions
      
  step_5_example_mappings:
    description: |
      Provide 3+ detailed real-world examples showing principle → behavior in action.
      Each example should include:
        • Principle being demonstrated
        • Concrete user input or scenario
        • Agent's decision process step-by-step
        • Behaviors applied (from templates)
        • What the agent WON'T do (anti-patterns)
        • Result and cascade benefits
      Examples should be tangible and executable, not abstract
      
  step_6_implementation_guide:
    description: |
      Create a quick-reference guide for implementing the framework:
        • 5-step decision tree for request processing
        • Principle → action lookup table
        • 3-5 ready-to-use communication templates
        • Confidence thresholds with action branching
        • 5-7 anti-patterns (what not to do) with corrections
        • Workflow diagram (request → execution)
        • Mastery progression (levels of framework integration)
      Format: YAML or markdown for easy scanning
      
  step_7_validation:
    description: |
      Create validation artifacts:
        • Success metrics (how to tell if framework is working)
        • Checklist (did the agent follow the principles?)
        • Anti-patterns (signs of framework drift)
        • Framework refinement signals (when to iterate)

schema_structure:
  metadata:
    - owner (user/organization)
    - agent_name
    - created_date
    - purpose
    - principles_count
  
  principles_registry:
    - principle_id
    - name
    - definition (one sentence)
    - description (paragraph)
    - category (decision_rules, communication_style, workflow_logic, work_cadence, execution_design)
    - priority (critical, high, medium)
  
  framework_translation:
    - decision_rules
    - workflow_logic
    - communication_style
    - work_cadence
  
  behavior_templates:
    - template_id
    - principle
    - trigger
    - implementation
    - decision_points
    - success_outcome
  
  confidence_scoring:
    - threshold_name
    - factors
    - weights
    - threshold_value
    - action_if_above
    - action_if_below

tips_and_patterns:
  confidence_thresholds: |
    Set thresholds high enough (0.75+) to require meaningful pattern matching,
    low enough (not 0.95+) to enable action on sparse context. Standard range: 0.75-0.80.
  
  silence_activation: |
    Silence thresholds should be 60+ minutes (detect true inactivity) but short enough
    to maintain momentum. Pair with task queue check: only activate if queued work exists.
  
  thirty_day_rule: |
    The 30-day hard rule (any recurring task automatable in 30 days gets designed immediately)
    is the highest-impact principle. It eliminates recurring manual work entirely. Make it non-negotiable.
  
  behavior_templates: |
    Should be copy-able patterns. Future sessions should read a template and execute it
    without reinterpreting. Use explicit step sequences, not prose.
  
  example_mappings: |
    Most valuable artifact. Show principle in action with concrete input, decision process, outcome.
    Include what the agent WON'T do (anti-patterns) to clarify boundaries.
  
  anti_patterns: |
    Provide 5-7 "don't do this" rules paired with corrections. They clarify framework
    boundaries and prevent drift.
  
  validation: |
    Build-in validation upfront. Create a checklist and success metrics to enable iterative
    refinement and catch framework drift early.
  
  self_documentation: |
    Schema should be self-documenting so agents can load and apply it without re-explanation.
    Use clear naming, consistent structure, embedded commentary.

anti_patterns_to_avoid:
  abstract_principles: |
    Avoid "be helpful" or "think creatively". Principles must be testable:
    "If recurring AND <30 day effort THEN design full automation" is principle-shaped.
  
  missing_decision_trees: |
    Principles without explicit branching become vague guidelines. Map each to a decision point:
    "If X THEN Y, ELSE Z".
  
  overly_high_thresholds: |
    Thresholds above 0.95 require near-certainty. Agent will ask for clarification constantly.
    Default to 0.75-0.80 to enable action on sparse context.
  
  over_engineering: |
    Start with 3-5 principles covering critical behaviors. Add refinements if drift appears.
    Do not try to capture every nuance upfront.
  
  abstract_examples: |
    Real-world mappings need concrete input (actual sentence user said, not "user requests analysis"),
    specific inference steps, measurable outcomes.
  
  skipping_anti_patterns: |
    What the agent should NOT do is as important as what it should. Include 5-7 "don't do this"
    rules with corrections.
  
  no_validation: |
    Cannot iterate if you cannot measure. Always include checklist and success metrics.

references:
  - references/confidence-scoring-patterns.md
  - references/30-day-rule-application.md
  - references/silence-protocol-patterns.md
  - references/example-mapping-template.md
  - templates/framework-schema-scaffold.yaml
  - templates/principle-template.yaml
  - references/tanzim-framework-session.md

---

## FRAMEWORK SCHEMA DESIGN SKILL

Design personal operating systems for autonomous agents by translating work principles
into decision rules, communication patterns, and workflow logic.

### When to Use

- Building a personal framework for an autonomous agent
- Translating abstract work philosophy into testable agent behaviors
- Designing how minimal input maps to autonomous action
- Creating confidence thresholds and autonomy activation rules
- Documenting principle-driven workflow automation

### Expected Deliverables

Six production-ready artifacts (50-70 KB total):
1. YAML schema with principle registry and framework translation layers
2. Markdown examples with 3+ detailed principle → behavior mappings
3. Quick-reference implementation guide with decision trees
4. Visual guide with flow diagrams and principle matrices
5. Executive summary for architects and decision-makers
6. Navigation index for multi-role access

### Key Principles

- Thresholds drive autonomy: Set them at 0.75-0.80, not 0.95+
- Silence thresholds: 60+ minutes, paired with task queue validation
- 30-day rule: Any recurring task automatable in 30 days gets designed immediately—non-negotiable
- Templates must be copy-able patterns ready for agent execution
- Examples are the most valuable artifact; include anti-patterns alongside positive cases
- Validation is built-in: checklists and success metrics enable iteration
- Self-document the schema so agents can apply it without re-explanation
