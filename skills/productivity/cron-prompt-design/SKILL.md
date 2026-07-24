---
name: cron-prompt-design
description: "How to write reliable cron job prompts — data sourcing, hallucination prevention, classification logic, and delivery rules."
version: 1.0.0
tags: [cron, scheduling, prompts, accountability, reliability]
related_skills: [gmail-inbox-check, google-workspace]
---

# Cron Prompt Design

Rules and patterns for writing cron prompts that stay accurate across runs without inventing information.

## The cardinal rule: no live data source = no specific claims

If a cron prompt has no tool access to verify facts (no `web`, `file`, `terminal` toolset), it MUST NOT mention specific names, deadlines, appointments, or tasks. It can only use:
- General standing priorities (e.g. "TIMBR and job search")
- Format scaffolding
- Instructions to stay general if nothing is verifiable

**What goes wrong:** A prompt with only `file` toolset access and static context like "TIMBR and job search are priorities" will hallucinate specifics — invented interview names, fake meeting times, fabricated deadlines — because the model fills the template with plausible-sounding detail. This erodes trust fast.

**The fix:** Add explicit instruction: `"Do NOT invent or assume specific tasks, interviews, or appointments. Only surface items you can verify. If nothing specific is known, keep priorities general."`

## Toolset pairing rules

| Job type | Minimum toolsets needed |
|---|---|
| Gmail scan / inbox check | `terminal`, `file` |
| Job search accountability | `terminal`, `file` (to read Gmail/sheets) OR keep general |
| Weekly planning with Trello/Sheets | `web`, `file`, `terminal` |
| Pure message delivery (static text) | none — hardcode the message in the prompt |
| Memory-based accountability | none — but only reference things memory reliably holds |

## Static delivery pattern
When the output is fully known at creation time, hardcode it:
```
Output this message exactly, with zero additions: "[message text]"
```
This is the most reliable pattern. Zero hallucination risk.

## [SILENT] suppression
Every intelligence-gathering cron (inbox check, planning review) MUST include:
```
If there is genuinely nothing new/actionable, output exactly [SILENT] and nothing else.
```
Without this, jobs produce noise every run even when empty.

## Reminder jobs for on-demand scan results
When Tanzim asks for a reminder based on a live scan (e.g. "remind me at 7:30 to complete these"), create a one-shot static delivery job with the specific items hardcoded from the scan. Do NOT create a job that re-scans — the scan already happened, the reminder just needs to echo the findings.

## Codeword via voice transcription
Voice messages occasionally garble the codeword (e.g. "TETA" instead of "THETA"). Pattern:
- If the transcribed word is close but not exact, flag it plainly: "That came through as [X] — did you mean [THETA]?"
- Do not guess or accept partial matches — confirm before acting.
- Once confirmed in text, proceed normally.

## Pitfalls
- **Never use `~` in double-quoted shell variable assignments** in cron prompts — `~` doesn't expand inside double quotes. Use `$HOME` or the full path.
- **Expired task lists in cron prompts** go stale silently. Any cron that hardcodes a task list (interview tasks, assessments, etc.) will keep firing that stale list indefinitely. Either: (a) pull tasks live from a data source, or (b) delete the job when the tasks are done.
- **Duplicate reminder jobs:** Before creating a new reminder, check if an existing job covers the same ground.
