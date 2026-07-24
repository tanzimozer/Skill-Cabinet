---
name: hindsight-model-configuration
domain: infrastructure
category: infrastructure
description: |
  Configure which LLM(s) the Hindsight memory engine uses for its background reasoning
  operations (extraction, consolidation, reflection) — independently of the chat model.
  Covers the per-operation model split, env-var mechanism, daemon restart, and live verification.
tags:
  - hindsight
  - memory
  - model-routing
  - configuration
  - daemon
---

# Hindsight Model Configuration

## Why Hindsight has its own LLM (the mental model)
Hindsight is the memory engine. It doesn't just store — it *reasons over memory* on a
**background daemon**, often when no chat session is active. So it cannot borrow the chat
model; it needs its own model wiring. Three distinct jobs, each separately tunable:

- **RETAIN** — extraction: reads raw conversation, pulls structured facts to save. High-volume, cheap.
- **CONSOLIDATION** — dedup/merge: cleans the bank, resolves contradictions. High-volume, cheap.
- **REFLECT** — synthesis: reasons across many memories to answer a considered question. Low-volume, quality-sensitive.

**Embeddings stay local** (Postgres vector store, pg0). You only ever swap the *reasoning* LLM.

Plain framing for the user: "the chat model is your voice; Hindsight's model is your memory's librarian."

## The mechanism: env vars read at daemon launch
The live daemon is `hindsight-api --daemon ... --port 9177` (a child of `hindsight-embed`).
It is started by systemd: `systemctl --user cat hindsight.service` shows
`EnvironmentFile=/home/hermes/.hermes/.env` and `ExecStart=.../hindsight-embed -p hermes daemon start`.

`hindsight-embed` translates config + env into `HINDSIGHT_API_*` vars and **does not override
anything already in the environment** (cli.py: `if key not in os.environ`). So setting a var in
`~/.hermes/.env` wins over the inherited default — that's how per-op overrides work.

Global LLM (covers RETAIN + CONSOLIDATION + REFLECT unless overridden):
```
HINDSIGHT_API_LLM_PROVIDER=anthropic
HINDSIGHT_API_LLM_MODEL=claude-haiku-4-5
HINDSIGHT_API_LLM_API_KEY=<key>        # per-op configs inherit this if omitted
HINDSIGHT_API_LLM_BASE_URL=https://api.anthropic.com
```

Per-operation override prefixes (same suffixes): `RETAIN_LLM`, `CONSOLIDATION_LLM`, `REFLECT_LLM`.
Example — global Haiku, but keep synthesis on Opus:
```
HINDSIGHT_API_REFLECT_LLM_PROVIDER=anthropic
HINDSIGHT_API_REFLECT_LLM_MODEL=claude-opus-4-8
HINDSIGHT_API_REFLECT_LLM_BASE_URL=https://api.anthropic.com
# api_key omitted → inherits HINDSIGHT_API_LLM_API_KEY automatically
```

## The recommended split (cost vs quality)
- Haiku on RETAIN + CONSOLIDATION — that's where the volume and the savings are (~90% cheaper).
- Opus (or stronger) on REFLECT — synthesis depth on the hard multi-thread questions.
- "All Haiku for Hindsight" is a valid user choice (cost + simplicity); it only costs a little
  REFLECT depth. To do it, simply set the global to Haiku and remove any REFLECT override.

## Apply procedure (always do all four steps)
1. **Back up first:** `cp ~/.hermes/.env ~/.hermes/.env.bak-$(date +%Y%m%d-%H%M%S)`
2. **Edit `~/.hermes/.env`** — add/remove the `HINDSIGHT_API_*` lines. (Editing a dotfile via
   shell redirect triggers a security-approval prompt — expected.)
3. **Restart the daemon:** `systemctl --user restart hindsight.service`
   (fallback: `~/.hermes/hermes-agent/venv/bin/hindsight-embed -p hermes daemon restart`)
4. **Verify on the LIVE daemon, not the config** (see below).

## Verification (read it off the running process)
```bash
curl -s http://127.0.0.1:9177/health        # {"status":"healthy","database":"connected"}
for p in $(pgrep -f 'hindsight-api --daemon'); do
  echo "--- PID $p (up since $(ps -o lstart= -p $p)) ---"
  tr '\0' '\n' < /proc/$p/environ 2>/dev/null \
    | grep -iE "HINDSIGHT_API_(LLM|RETAIN|CONSOLIDATION|REFLECT)_(MODEL|PROVIDER)" \
    | sed -E 's/(KEY|TOKEN|SECRET)=.*/\1=***/' | sort
done
```
Config files are the *intent*; `/proc/<pid>/environ` is the *truth*. Always confirm against the
freshly-spawned PID after restart — the old daemon PID lingers briefly.

## Pitfalls
- **Don't confuse the chat model with the Hindsight model.** They're independent. "Friday on Opus,
  Hindsight on Haiku" is a normal, intended state.
- **`/config` endpoint returns 404** on this daemon — there is no live config readout API. Use
  `/proc/<pid>/environ` instead.
- **Verify the NEW pid.** After restart, `pgrep` may show two PIDs momentarily; read the one whose
  `lstart` is the restart time.
- **Per-op api_key inheritance is real** — omit `*_LLM_API_KEY` on an override and it falls back to
  the global key. Don't duplicate secrets.

## Related
- Authoritative chat-model identity comes from the runtime block / `~/.hermes/logs/agent.log`
  (`model=... provider=...` lines), never from guessing. See note in `gspread-oauth-sheets` for log location.
- Persona/model preferences for Tanzim live in memory, not here.
