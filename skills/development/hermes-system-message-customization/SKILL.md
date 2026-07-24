---
name: hermes-system-message-customization
description: "Rephrase or restyle Hermes' own hardwired system/UI strings (busy-queue acks, status lines, slash-command responses, onboarding hints) to match Tanzim's voice. Covers finding every variant across gateway/ACP/CLI/platform code, patching them consistently, updating the tests that assert the old wording, and the no-emoji/terse house style."
version: 1.0.0
tags: [hermes, codebase, system-messages, ux-copy, tanzim, development]
related_skills: [tanzim-communication-style, hermes-agent]
---

# Hermes System-Message Customization

Tanzim periodically wants Hermes' own machine-generated strings — the ones the framework emits, not Friday's replies — rephrased into his voice. Example (Jun 28 2026): the busy-session ack

> "⏳ Queued for the next turn (iteration 1/60, running: execute_code). I'll respond once the current task finishes."

He wanted it replaced with a clean, terse **"One moment please."** — no emoji, no iteration spam, no internal mechanics leaked to the user. Then: *"update everywhere and then wait for my signal for gateway action."*

This is a recurring **class**: the system speaks to him in many places, and he wants it to sound like Friday — composed, minimal, no emojis, no jargon. The work is mechanical but spread across several files plus tests.

## House style for these strings (Tanzim's defaults)
- **No emojis.** Strip the ⏳/⚡/💡 etc.
- **Terse and human.** "One moment please." beats "Queued for the next turn (iteration N/M, running: X)."
- **Don't leak internals.** Iteration counts, tool names, queue depth, "running: execute_code" — all noise to him. Cut them from user-facing copy.
- **Match the persona, not the framework's default tone.** Calm, plausibly-Friday.

## The locations — system strings hide in MANY files
A single user-facing string usually has 4–6 sibling copies. Grep the whole repo for the exact phrase before editing, then patch every hit. Known homes for busy/queue/status acks (`~/.hermes/hermes-agent/`):

- `gateway/run.py` — the main busy-session ack (steer/queue/interrupt branches) AND the `/queue` slash-command return value. **Two+ spots.**
- `acp_adapter/server.py` — the ACP (VS Code/Zed/JetBrains) queue update + the `_cmd_*` return strings. **Two+ spots.**
- `gateway/platforms/discord.py` — per-platform slash-command ack strings.
- `cli.py` — `_cprint(...)` console prints for queued/steered input. **Two+ spots.**
- `agent/onboarding.py` — one-time "first-time tip" hints (separate purpose: they teach the `/busy` knob). **Usually leave these** unless he asks — they're educational, not the recurring ack. Call out that you left them and why.

## Workflow
1. **Grep the exact phrase repo-wide** (`search_files` for e.g. "Queued for the next turn" and the second sentence "respond once the current task finishes"). Get the full count before touching anything.
2. **Patch each user-facing emission** to the new string. Keep surrounding logic (depth calc, mode branches) intact — just swap the message text.
3. **Update the tests that assert the old wording.** There WILL be tests (e.g. `tests/gateway/test_busy_session_ack.py`, `tests/gateway/test_slack.py`) asserting `"Queued for the next turn" in content`. Change them to the new phrase or CI breaks. Note: a self-contained round-trip test (sends a literal string, asserts the same string) needs no change — only assertions tied to the *generated* copy do.
4. **py_compile everything touched** to catch syntax errors: `python3 -m py_compile gateway/run.py acp_adapter/server.py ...`. The LSP/Pyright errors elsewhere in a 18k-line file are pre-existing noise — don't chase them; confirm only that YOUR edit compiles.
5. **Report what changed + what you deliberately left** (onboarding hints), and that it needs a restart to take effect.

## Critical: this needs a gateway restart, and Tanzim controls when
Edits to gateway/ACP/CLI code do NOT apply to the running process. The live session keeps using the old string until restart. **Tanzim explicitly said "wait for my signal for gateway action"** — make the edits, confirm them, then STOP and stand by. Do not restart the gateway yourself unless told. Always state plainly: "needs a gateway restart to take effect; standing by for your signal."

## Pitfalls
| Pitfall | Fix |
|---------|-----|
| Patching only the gateway copy | Same string lives in ACP, CLI, Discord too — grep repo-wide first |
| Forgetting the tests | Tests assert the old wording; update them or CI fails |
| Editing the onboarding hints by reflex | Those teach the /busy knob — different purpose; leave unless asked, and say so |
| Chasing unrelated Pyright errors | Big files have pre-existing LSP noise; only confirm your edit compiles |
| Restarting the gateway unprompted | He controls gateway actions — edit, confirm, wait for his signal |
| Leaving an emoji or iteration count in | His house style is no-emoji, no-internals, terse |

## See also
- `tanzim-communication-style` — his voice/format preferences (the target tone for these strings)
- `hermes-agent` — the codebase map (gateway/, acp_adapter/, cli.py, tests/) if bundled/available
