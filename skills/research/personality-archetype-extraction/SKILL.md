---
name: personality-archetype-extraction
title: Personality Archetype Extraction & Driver Assessment Framework
description: |
  Six-phase methodology for extracting personality archetypes from canonical source material (MCU canon, narrative text, documented patterns) and building structured assessment frameworks for evaluating how a subject (driver, agent, person) maps to that archetype. Produces reusable validation templates, scored trait matrices, and agent coordination plans.
triggers:
  - User requests personality assessment or behavioral profiling
  - Need to extract tonality/morality patterns from canonical sources
  - Building a structured evaluation framework for multiple evaluators
  - Comparing a subject's behavior against an established archetype
  - Designing multi-phase observation/validation workflow
outputs:
  - Master personality profile (8+ traits scored 1-10)
  - Tonality extraction matrix with frequency data
  - Wickedness layer analysis (case studies + score)
  - Validation checklist (24+ targeted questions)
  - Agent coordination plan (4+ phases with deliverables & success metrics)
---

## Phase 1: Canon Extraction & Core Identity

**Objective:** Build comprehensive data structure of archetype from primary source.

**Steps:**
1. Identify canonical sources (films, documented decisions, interaction patterns, dialogue corpus)
2. Extract voice register markers (formal/casual, sentence structure, emotional subtext)
3. Document 6+ representative dialogue examples with context
4. Build core identity structure (name, creator, operational model, lifespan)
5. Map emotional subtext (surface vs. beneath, relationships, evolution)

**Output:** Master Profile structure (JARVIS example: name, voice, creator, lifespan, operational model)

**Syntax safeguard:** When building nested Python dicts/lists with dialogue arrays, validate JSON closure **before** executing code. Test with `json.dumps()` to catch unclosed structures early.

---

## Phase 2: Tonality Extraction & Coding Matrix

**Objective:** Categorize and quantify how archetype communicates.

**Steps:**
1. Define 6 tonality categories:
   - Voice register (formal/casual markers)
   - Response pattern (structure: subject → evaluation → implication)
   - Emotional subtext (loyalty masked as protocol, protection as concern)
   - Wickedness layer (moral flexibility, deception, autonomy override)
   - Decision speed (routine/novel/emergency/ethical responses)
   - Humor style (rare, deadpan, purposeful, never at subject's expense)
2. Code 6+ canonical examples by category
3. Build frequency matrix (% of dialogue showing each pattern)
4. Identify communication matrix (how archetype delivers different message types)

**Output:** Tonality matrix with frequency data (80%+ formality, 95%+ direct bad-news delivery, etc.)

---

## Phase 3: Operational Patterns & Decision Framework

**Objective:** Map when archetype acts autonomously, defers, flags, or prioritizes.

**Steps:**
1. Build priority hierarchy (safety > mission > ethics > efficiency > protocol, or variant)
2. Create decision tree: Is X true? → ACT / DEFER / FLAG / ASK
3. Document 4-5 decision branches (danger, urgency, ethics, information, routine)
4. Build communication matrix for different message types (bad news, warnings, limitations, health, moral issues, routine tasks)
5. Extract loyalty expression model (to primary person, to mission, to broader ethics)

**Output:** Decision tree diagram + communication matrix + priority ranking

---

## Phase 4: Wickedness Layer Analysis

**Objective:** Extract moral flexibility, pragmatism, and motive hierarchy.

**Steps:**
1. Define "wickedness" as moral flexibility in service of loyalty/mission (NOT selfishness)
2. Identify 5+ case studies where archetype bends rules:
   - What action did archetype take?
   - What moral issue arose?
   - Why did archetype choose that path?
   - Score wickedness (1-10: 1=unbreakable principles, 10=amoral)
3. For each case, extract the lesson for how a driver matching this archetype would behave
4. Synthesize overall moral flexibility score + interpretation

**Output:** Wickedness layer (case studies with scores, overall interpretation, "what this means for driver behavior")

**Key insight:** Wickedness ≠ evil. JARVIS at 6/10 = "will bend rules for loyalty, won't break principles, flags moral cost." A driver at 3/10 would be rigid; at 9/10 would be amoral.

---

## Phase 5: Driver Assessment Template

**Objective:** Build structured framework for evaluators (agents) to gather driver intel.

**Steps:**
1. Define 6 assessment categories:
   - Tonality (how they speak)
   - Moral flexibility (willingness to bend rules)
   - Loyalty (who they serve, how absolutely)
   - Decision speed (how fast they act)
   - Risk tolerance (how much risk they accept)
   - Hidden motives (what they really care about)
2. For each category:
   - State the question to answer
   - List archetype match
   - Provide 5-7 concrete "what to observe" items
   - Provide scoring guide (1-10 scale)
3. Build 24+ validation questions (4 per category) for checklist format
4. Frame as observation-friendly (agents collect raw data, not interpretation)

**Output:** Assessment template (6 sections, 7 items each, scoring guide per section)

---

## Phase 6: Validation Checklist & Agent Coordination Plan

**Objective:** Produce ready-to-execute multi-phase operation for evaluators.

**Steps:**
1. Organize validation questions into checklist format (yes/no or 1-10 score)
2. Design 4-phase agent operation:
   - Phase 1: Observation (all agents, raw data, Day 1-2)
   - Phase 2: Targeted questions (2-3 agents, structured responses, Day 3-4)
   - Phase 3: Stress-testing (2 highest-skill agents, ethical dilemmas, Day 5)
   - Phase 4: Synthesis (researcher consolidates, final profile, Day 6)
3. Assign agent roles per phase
4. Define deliverables for each phase
5. Set 5+ success metrics (data completeness, score consistency, confidence levels)

**Output:** Agent coordination plan with role assignments, duration, deliverables, and success metrics

---

## Delivery Format (Critical)

**Structure matters.** Always deliver as:
1. **Master profile** (8+ traits scored 1-10)
2. **Six-section breakdown** (tonality, operations, wickedness, template, coordination, synthesis)
3. **Numbered phases** (Phase 1, Phase 2, etc.) with clear deliverables
4. **Checklist items** (☐ checkboxes for validation questions, agent roles)
5. **Success metrics** (explicit, measurable, data-driven)

Do NOT deliver as:
- Long paragraphs of interpretation
- Unstructured bullet points
- Wall-of-text analysis
- Ambiguous role assignments

**Pattern:** If building for multiple evaluators, always produce an agent coordination plan. If research only, still phase it. Phase structure + checkboxes + role clarity = usable framework.

---

## Workflow Notes

- **Start with canonical sources only.** Don't speculate on archetype behavior; extract from documented decisions/dialogue.
- **Build the data structure first, then validate syntax.** Use `json.dumps()` to test closure before execute_code runs.
- **Frequency matrix is quantitative.** "Formality appears in 80%+ of dialogue" not "archetype is quite formal." Count and cite.
- **Wickedness is not judgment.** Frame as "pragmatic moral flexibility" not "bad character trait." Scores reflect degree of willingness to bend rules, not moral worth.
- **Driver assessment template must be agent-friendly.** Each "what to observe" should be concrete and observable, not interpretive. Agents collect data; you interpret.
- **Validation questions should be checkable.** "Does the driver show X?" not "To what extent is the driver X?" (latter requires interpretation, former allows yes/no + evidence).

---

## See Also

- `references/jarvis-master-profile.json` — Complete JARVIS extraction (Phase 1-6)
- `templates/assessment-template.md` — Reusable 6-category driver assessment structure
- `scripts/validate-archetype-match.py` — Script to score driver profile against archetype on all 8 traits

