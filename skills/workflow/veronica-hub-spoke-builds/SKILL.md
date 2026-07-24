---
name: veronica-hub-spoke-builds
description: How to run a hub-and-spoke subagent deployment — parallel teams (currently Fable) design/produce OR run QA audits in isolation, and Friday (the hub) consolidates. Covers "deploy Veronica", the concurrency cap, task-splitting by axis, the QA-audit variant, the mechanical pre-check, embedding data into spoke briefs, and pluggable-architecture builds.
category: workflow
---

# Veronica — Hub-and-Spoke Builds

**"Deploy Veronica"** is Tanzim's codeword for maximum-capability execution: run Friday on the strongest model with **parallel subagents** and quality checks, then revert. In practice it means a **hub-and-spoke** build — spawn spoke teams to design/produce in isolation, then Friday (the hub) consolidates the output into the deliverable.

## Current Model Config

- **Current Opus model:** claude-opus-4-8
- **Concurrency cap:** 5 parallel agents max (enforced via `delegation.max_concurrent_children`)
- **Opus must be specified** via `delegation.model` in config OR as the `model` parameter in subagent calls — it is not the default and will not activate automatically.

## The pattern that works

1. **Hub plans, spokes produce.** Give each spoke a self-contained slice with full context (the spokes don't share Friday's context). Spell out the exact section structure you want back so the pieces slot together.
2. **Spokes return CONTENT, hub writes the artifact.** Tell subagents explicitly: *do NOT write to the sheet/repo — return structured text/files; the hub consolidates.* This keeps formatting consistent and avoids races. They wrote spec `.md` files; the hub read them and built the tabs.
3. **Hub consolidates + applies house standards** (e.g. the gsheets formatting standard) in one controlled pass.

## Variant — QA / audit hub-and-spoke (not just builds)

The same pattern runs for **quality-assurance passes**, not only design/build. Tanzim's phrasing: *"run a hub-and-spoke, deploy 2 teams for QA."* Structure that worked on the TIMBR STRENGTH DB scoring audit:

1. **Do the mechanical pre-check YOURSELF first, before spawning anything.** If the data has computed columns (a formula + inputs), recompute every row locally and diff against the stated values. This partitions the problem: *formula/logic errors* vs *input-judgement errors*. On STRENGTH DB the recompute was clean (0 mismatches) — which proved the errors could only live in the human-scored inputs, and told the spokes exactly where to look. Never hand a QA team a haystack you could have narrowed in 20 lines of code.
2. **Split spokes by axis-of-error, not by row range.** Spoke 1 audited the *computed-input* axes (the scores feeding the formula); Spoke 2 audited the *directly-judged* axes (scored 1–9 by hand). Each team gets a coherent, non-overlapping slice and a clear mental model.
3. **Embed the rubric/anchors in each brief.** For scoring audits, paste the authoritative rubric (score meanings + "typical movements" anchor lists) into the goal. Ask for: row number, item name, axis, current→proposed, one-line rationale *citing the anchor*, and the knock-on effect (does it flip the computed class/band). Tell them to group findings by systemic theme, not just list rows.
4. **Findings are STAGED, never written.** These datasets have a human sign-off gate (Sagar for TIMBR). Spokes return findings only; hub consolidates and holds for approval. State plainly in the report: "nothing written, N flags staged."
5. **Verify spoke output against the LIVE source before reporting.** Spokes may work off a stale copy (see pitfall below). Re-map every flagged item to the live sheet by NAME and confirm the values match before you put row numbers in front of Tanzim — spoke row numbers can be off if their snapshot differs.

## Pitfall — subagents don't inherit your data; embed it or they'll improvise

Spokes have **their own isolated context and filesystem view** — they do NOT see the data you pulled into the hub. On the STRENGTH DB audit the DB got truncated out of the task brief, so both spokes silently fell back to a stale local backup snapshot (`~/backups/STRENGTH_DB_*.json`) and audited that instead. The findings still translated (same dataset), but only by luck.

**Fix:** paste the full working data **inline in the task goal** and confirm it's actually there (check the byte count / print the tail before spawning). Don't rely on "there's a file at /tmp/..." — a subagent may not find it, or may grab a wrong-but-plausible file. If the data is too big to inline, give an explicit exact path AND tell them to fail loudly if it's empty rather than substitute another source. Always re-verify their row references against the live source afterward (step 5 above).

## Pitfall — Opus not wired by default

Opus (`claude-opus-4-8`) is NOT the default model — `claude-sonnet-4-6` is. Veronica requires Opus but config does not auto-switch. At deploy time, explicitly set `delegation.model: claude-opus-4-8` in config.yaml before spawning, then revert after. No inline per-task model override exists — config is the only lever.

## Pitfall — the concurrent-task cap

`subagent` batch mode caps at **5 concurrent children** (`delegation.max_concurrent_children: 5` — updated 2026-07-24). Exceeding the cap fails outright.

**Fix:** collapse work into ≤5 spokes. If you genuinely need more, split into sequential `subagent` calls. Don't reflexively make one spoke per item — fewer, richer spokes beat many thin ones.

## Pitfall — don't over-split

A natural N-part deliverable does not mean N spokes. Group by cohesion and the concurrency cap. Fewer, richer spokes beat many thin ones — each spoke carries more context and returns a more coherent slice.

## Infrastructure-first / pluggable builds (Tanzim's standing preference)

When Tanzim says "build the system/infrastructure ahead, we'll add filters/persona/specifics later":
- Architect everything **config-driven** — persona, filters, geo, pacing, thresholds are DATA in one config file, never hardcoded. Same binaries serve any campaign.
- Produce a **Questions tab/list** where every open decision maps 1:1 to a config key. The principle to state back: *"answering the Questions list = configuring the engine."* He answers later; the build doesn't wait on him.
- Each question carries: why-it-matters, an example, the config key it fills, and a blank ANSWER column.

## Reflect-the-build expectation

For build projects Tanzim wants the work made **legible in a Google Sheet** — what was created, how it works, how it helps — in plain English he can read without touching code. One tab per stage/component, plus Overview (plan + WBS) and Config. Use the `gsheets-formatting-standard` skill for the formatting.

## Naming note

"Veronica" has been redefined more than once (Opus deployment → Fable → etc.). Don't hardcode which model it maps to — read the current definition from memory/USER.md at deploy time. The *workflow* (hub-and-spoke, parallel, QA, revert) is the stable part.
