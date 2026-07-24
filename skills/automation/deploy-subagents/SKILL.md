---
name: deploy-subagents
description: Auto-deploy parallel subagents when triggered (max 5 concurrent per Protocol Veronica)
category: automation
tags: [subagent, parallel, orchestration, batch]
version: 1.0.0
created: 2026-05-24
---

# Deploy Subagents

Auto-deploy parallel subagents for high-throughput work.

**Token budget cap (locked Jul 2026):** Max 5 parallel agents at any time — Tanzim's explicit hard cap to protect token budget. This is enforced in Protocol Veronica and applies here too. Never spawn more than 5 at once.

## Trigger Phrases

When Tanzim says:
- "deploy subagents"
- "launch subagents"
- "spin up subagents"

## Execution

Deploy parallel subagents using the `subagent` tool with `tasks` parameter. Max 5 concurrent agents at any time per Protocol Veronica hard cap.

### Template

```python
subagent(tasks=[
    {"goal": "Task 1 description", "context": "Background for task 1"},
    {"goal": "Task 2 description", "context": "Background for task 2"},
    # ... up to 5 tasks (hard cap per Protocol Veronica)
])
```

## Task Distribution Strategies

### 1. Content Writing (up to 5 sections per batch)
Split content into up to 5 parallel sections per batch — each agent writes one part:
- Magazine sections (intro + up to 4 chapters per batch)
- Blog posts (up to 5 different topics per batch)
- Product descriptions (up to 5 items per batch)

### 2. Research (up to 5 topics per batch)
Each agent researches a different topic (up to 5 per batch):
- Competitor analysis (up to 5 companies per batch)
- Market research (up to 5 segments per batch)
- Content research (up to 5 sources per batch)

### 3. Data Extraction (up to 5 sources per batch)
Each agent extracts from different source (up to 5 per batch):
- Up to 5 spreadsheet tabs per batch
- Up to 5 websites per batch
- Up to 5 documents per batch

### 4. Outreach (up to 5 people per batch)
Each agent handles one person (up to 5 per batch):
- Message drafting
- Follow-up sequences
- Personalized content

### 5. Mixed Workflow
Combine different task types (total max 5):
- 2 agents research
- 2 agents write
- 1 agent extracts data

## Concurrency limit

Current `max_concurrent_children` is **5** in `~/.hermes/config.yaml` per Protocol Veronica. This is the hard cap — never exceed 5 concurrent agents.

If you need more than 5 total tasks, split into sequential `subagent()` calls:
- Call 1: first 5 tasks
- Call 2: next 5 tasks
- etc.

## Configuration

**Default toolsets:** All standard tools unless specified
**Role:** `leaf` (execution agents, not orchestrators)
**Context:** Share common background in `context` parameter
**Goal:** Each task gets specific, actionable goal

## Example: Magazine Sprint

```python
subagent(tasks=[
    {"goal": "Write Blair's origin story (pages 1-10)", "context": "Blair fitness magazine, narrative-driven, 60% women 20-38"},
    {"goal": "Write transformation journey (pages 11-20)", "context": "Same magazine context"},
    {"goal": "Write current training system (pages 21-30)", "context": "Same magazine context"},
    {"goal": "Write nutrition philosophy (pages 31-40)", "context": "Same magazine context"},
    {"goal": "Write Seattle lifestyle section (pages 41-50)", "context": "Same magazine context"},
    {"goal": "Write workout 1-pager", "context": "Same magazine context"},
    {"goal": "Write nutrition 1-pager", "context": "Same magazine context"},
    {"goal": "Write Seattle spots 1-pager", "context": "Same magazine context"},
    {"goal": "Research Shumon's persona", "context": "Second magazine subject, apply Blair question framework"},
    {"goal": "Research Taylor's persona", "context": "Third magazine subject, apply Blair question framework"},
    {"goal": "Source Blair's photos", "context": "Magazine imagery needs"},
    {"goal": "Source Seattle gym/cafe images", "context": "Magazine imagery needs"}
])
```

## Best Practices

1. **Clear goals:** Each task should be self-contained and specific
2. **Shared context:** Put common background once in context field
3. **Balanced load:** Distribute work evenly across agents (max 5 per batch)
4. **Independent tasks:** No dependencies between agents (they run in parallel)
5. **Collect results:** All results return together when complete

## Output Handling

All agents return results simultaneously. Review all outputs and synthesize:
- Combine written sections into single document
- Merge research findings
- Aggregate extracted data
- Compile outreach drafts

## When NOT to Use

- Tasks with dependencies (use sequential subagents instead)
- Single large task (no parallelization benefit)
- < 3 tasks (overhead not worth it)
- Tasks requiring human input mid-execution
- **I/O-bound scripted work** — for image scanning, API calls, or file processing where the work is a Python script, use background terminal processes instead (see below)

## Alternative: Background process parallelism

For scripted tasks (not LLM reasoning), background processes are lighter weight than subagents:

```bash
# Launch 4 parallel scans
python3 scan.py FOLDER_1 "batch-1" 2>&1 | tee /tmp/log1.txt &
python3 scan.py FOLDER_2 "batch-2" 2>&1 | tee /tmp/log2.txt &
python3 scan.py FOLDER_3 "batch-3" 2>&1 | tee /tmp/log3.txt &
python3 scan.py FOLDER_4 "batch-4" 2>&1 | tee /tmp/log4.txt &
```

Use `terminal(background=true, notify_on_complete=true)` for each. Check progress with `tail -5 /tmp/log*.txt`.

Best for: Google Drive scanning, web scraping, data processing, API-heavy work.
Subagents are better for: LLM reasoning tasks, content writing, research synthesis.

## Pattern: Hub-n-spoke QA with pre-vetted delivery

When Tanzim says "deploy hub and spoke" for a quality-check task (not adversarial
review), the pattern is:
1. **1 hub (you) + max 5 spokes** — Tanzim's explicit cap this session ("no more
   than five agents working at a time").
2. **Each spoke gets exactly ONE task** — not a multi-part brief.
3. **Hub does its own QC pass on combined results** before the summary reaches
   Tanzim. He should not be the first QC gate.
4. Deliver a single clean verdict: Pass/Fail per check, issues with row numbers,
   overall verdict.

Standard 5-spoke QA set for exercise databases:
1. Formula validation
2. Naming convention
3. Duplicate detection
4. Alternative exercise validation
5. Completeness check

**Briefing spokes — pass schema by COLUMN NAME, not index.** If the sheet has
had columns inserted mid-session, hard-coded indexes will be wrong. Instruct
every spoke to read the header row first and find columns by name dynamically.

## Pattern: Hub-n-spoke adversarial review ("challenge the methodology / red-team this")

Distinct from throughput splitting. Here every spoke attacks the **same artifact** from a different critical lens; the hub (you) synthesises where they converge vs split. Use when Tanzim says "run hub n spoke", "challenge X", "stress-test the methodology", "see if you'd change anything".

Recipe:
1. **Pick 3–4 orthogonal adversarial roles**, not generic reviewers. For a scoring/methodology artifact the proven set was: domain skeptic (e.g. sports-science), measurement/psychometrics auditor, pragmatic shipping engineer (the "is this over-engineered for v1" voice), and a red-team adversary tasked to BREAK it with concrete failing examples. The pragmatist + red-teamer are what make the output actionable — pure critics over-rotate on rigor.
2. **Give every spoke the full artifact inline** (all formulas, weights, bands) in its `context`/`goal` — they have no shared memory. Demand the SAME output shape from each: a ranked list, each item one line + reasoning, "output only the critique, no preamble".
3. **Mind the concurrency cap (5).** Up to 5 roles per `subagent(tasks=[...])` call. For more, use sequential calls.
4. **Hub synthesis = lead with CONVERGENCE** (what all spokes independently agreed on — that's the high-confidence signal), then name the SPLIT and make your own call on it, then translate into a concrete artifact (a v2 spec / WBS) so Tanzim reacts to something concrete, not prose.

## Subagent timeout — split multi-step tasks

**Visual generation tasks hit the 600s timeout** — confirmed in a session where a Veronica orchestrator was tasked with: write script → run → QC → fix → QC → send. That's 6+ sequential phases and reliably times out.

For image generation + QA + send: do the generation and QC yourself (directly), only use Veronica if the task is genuinely parallelisable (e.g. multiple independent images). A single sequential visual pipeline is NOT a good Veronica target.

A subagent with 5+ sequential steps (read → generate → compute → write → sort → rerun) will time out at 600s. This session: a single Opus agent tasked with "identify gaps, generate 61 exercises, append, sort, rerun col C" hit the wall.

**Rule:** if a task has more than 3 meaningful sequential phases, split into two separate subagent calls. Common split point:
- Call 1: Read + generate + append + sort
- Call 2: Rerun dependent columns using the expanded pool

Pass intermediate state via a local JSON file (`/tmp/gaps.json`, `/tmp/new_rows.json`) — the second call reads what the first wrote.

The pre-work scan (read the sheet, identify gaps) done directly in your own terminal before launching the subagent also reduces subagent scope significantly and avoids timeout.

## Pattern: Verify-before-write (always, for foundational data)

When the output feeds something downstream (a scoring model, a config, generated content), VERIFY the new logic against known-answer cases BEFORE committing it to the live sheet/file. This session: ran the proposed v2 formula against 9 known lifts in `execute_code`, confirmed the previously-wrong case (Reverse Lunge → F3) now landed right AND surfaced one residual failure (machines still over-tier) — all before writing a character. Tanzim's standing bar is "accuracy is my priority". Never write an untested formula to the foundation tab. Also: keep proposals as APPENDED new sections, not overwrites, until he signs off (see gsheets-formatting-standard).



- Subagents inherit codeword requirements for side-effecting actions
- Each agent operates in isolated context
- Results merge back to main session
