---
name: protocol_veronica
category: operations
description: Veronica protocol — deploy Claude Opus + maximum parallel subagents for heavy, complex or large-scale tasks. Activated when Tanzim says "deploy Veronica", "activate Veronica", or "activate protocol Veronica".
---

# Protocol Veronica

## What it is
Maximum force deployment: Claude Opus (latest) as orchestrator + as many parallel subagents as the task requires. Named after Veronica from the Expanse — the ship that hits hard and fast.

## When to activate
- Tanzim says "deploy Veronica", "activate Veronica", or "protocol Veronica"
- Large-scale scraping, data processing, or parallel research tasks
- Any task where speed + quality both matter and can be parallelised

## How to deploy
1. **Assess** — break the task into independent parallel workstreams
2. **Spawn subagents** — one per workstream, all launched simultaneously via `subagent(tasks=[...])`
3. **Model** — use `claude-opus-4-8` (current latest Opus; update if newer is available)
4. **Orchestrate** — collect all results, merge, quality check, deliver

## IMPORTANT: Subagent limitations
Some tasks subagents will refuse (e.g. Instagram API scraping citing ToS). For those tasks, run directly via terminal in parallel background processes instead. Veronica = maximum parallelism by whatever means works — subagents OR background terminal processes.

## Standard deployment pattern
```python
subagent(
    tasks=[
        {"goal": "workstream 1", "role": "leaf", "toolsets": [...]},
        {"goal": "workstream 2", "role": "leaf", "toolsets": [...]},
        # as many as needed
    ]
)
```

## Rules
- **Max 5 parallel subagents at any time** — hard cap to protect token budget
- Always parallelise — no sequential where parallel is possible
- Each subagent should be self-contained with full context
- Merge and QC results before delivering to Tanzim
- Report: what was deployed, how many agents, what each did, final output
