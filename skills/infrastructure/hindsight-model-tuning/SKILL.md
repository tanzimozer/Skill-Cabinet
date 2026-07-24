---
name: hindsight-model-tuning
category: infrastructure
description: |
  Tune which LLM the Hindsight memory subsystem uses, globally or per-operation
  (RETAIN / CONSOLIDATION / REFLECT). Covers the env-var mechanism, the
  hindsight-embed launcher's non-override rule, safe edit + restart + verify
  workflow. Separate from the chat model — Hindsight reasons over memory on its
  own background daemon.
triggers:
  - Pair model X to Hindsight, put Haiku on memory, or change Hindsight's model
  - Cost-tuning the memory subsystem (cheaper extraction, keep synthesis sharp)
  - Hindsight memory ops feel slow or expensive, or reflections feel shallow
  - Need to confirm what model Hindsight is actually running vs the chat model
---

# Hindsight Model Tuning

## Why Hindsight needs its own LLM (the user's mental model)
Hindsight is not just storage — it **reasons over memory** on a background daemon,
often when no chat session is active, so it can't borrow the chat model. Three jobs:
- **RETAIN** — fact extraction from raw conversation. High-volume, runs constantly.
- **CONSOLIDATION** — dedup / merge / resolve contradictions. High-volume.
- **REFLECT** — synthesis across many memories when answering. Low-volume, quality-sensitive.

Embeddings are a **separate** local concern (Postgres pgvector) — model tuning here
only touches the *reasoning* LLM, never the embeddings.

**One-liner for Tanzim:** "the chat model is your voice; Hindsight's model is your
memory's librarian — different jobs, different brains."

## The mechanism (verified Jun 2026)
The live daemon (`hindsight-api --daemon --port 9177`) reads env vars. The
`hindsight-embed` launcher translates `config.yaml` + `.env` into `HINDSIGHT_API_*`
vars at spawn time. Global + per-operation overrides:

```
# Global (covers all three ops unless overridden)
HINDSIGHT_API_LLM_PROVIDER=anthropic
HINDSIGHT_API_LLM_MODEL=claude-haiku-4-5
HINDSIGHT_API_LLM_BASE_URL=https://api.anthropic.com
HINDSIGHT_API_LLM_API_KEY=<key>

# Per-operation override (same prefix, swap LLM for RETAIN_LLM / CONSOLIDATION_LLM / REFLECT_LLM)
HINDSIGHT_API_REFLECT_LLM_PROVIDER=anthropic
HINDSIGHT_API_REFLECT_LLM_MODEL=claude-opus-4-8
HINDSIGHT_API_REFLECT_LLM_BASE_URL=https://api.anthropic.com
# api_key/base_url inherit from the global HINDSIGHT_API_LLM_* if omitted
```

Per-op env names live in
`~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hindsight_api/config.py`
(ENV_RETAIN_LLM_MODEL, ENV_REFLECT_LLM_MODEL, ENV_CONSOLIDATION_LLM_MODEL, etc.).

## CRITICAL launcher rule
`hindsight_embed/cli.py` does `if key not in os.environ: os.environ[key] = value`
— **it will NOT override anything already set in the environment.** So an override
placed in `~/.hermes/.env` *wins* over the launcher's defaults. Put overrides in
`.env`; they survive restart.

## Where to set it
- `.env` keys live in `~/.hermes/.env` (loaded via the service's `EnvironmentFile`).
- The systemd unit is `hindsight.service` (user scope); `EnvironmentFile=/home/hermes/.hermes/.env`.
- The global Haiku default may already be injected by the launcher from `config.yaml`
  (`model:` / memory block) even when not visible in `.env` — verify on the live
  daemon, not just by reading `.env`.

## Safe edit + restart + verify workflow
1. **Back up first:** `cp ~/.hermes/.env ~/.hermes/.env.bak-$(date +%Y%m%d-%H%M%S)`
2. Append/remove the `HINDSIGHT_API_*_LLM_*` lines (write_file/patch, not raw echo into a dotfile — the dotfile-overwrite guard will flag a careless `>`).
3. **Restart:** `systemctl --user restart hindsight.service` (fallback:
   `~/.hermes/hermes-agent/venv/bin/hindsight-embed -p hermes daemon restart`).
4. **Health:** `curl -s http://127.0.0.1:9177/health` → expect `{"status":"healthy","database":"connected"}`.
5. **VERIFY ON THE LIVE DAEMON** (don't trust `.env` alone — read the actual process env):
   ```bash
   for p in $(pgrep -f 'hindsight-api --daemon'); do
     tr '\0' '\n' < /proc/$p/environ | grep -iE "HINDSIGHT_API_(LLM|RETAIN|CONSOLIDATION|REFLECT)_(MODEL|PROVIDER)"
   done
   ```
   Pick the PID that's actually serving (newest); after restart there can be a
   brief moment where an old PID lingers — grep all and confirm the live one.

## Recommended configurations
- **Cost split (default recommendation):** Haiku global (→ RETAIN + CONSOLIDATION),
  Opus override on REFLECT. ~90% cheaper on the high-volume work, synthesis stays deep.
- **All-Haiku ("dedicate Hindsight to Haiku"):** drop the REFLECT override so all three
  ops inherit the Haiku global. Faster/cheaper everywhere; reflections a touch shallower
  on hard multi-thread questions. This is what Tanzim chose Jun 18 2026.
- Always flag the REFLECT trade-off in one line before going all-Haiku — it's the only
  op where the cheaper model is a real (if small) quality hit.

## Confirming chat model vs Hindsight model (they are different)
Do NOT guess the chat model from config or memory — config *default* and *live route*
diverge (fallback providers exist). Read the authoritative live log:
```bash
grep -hiE "model=.*provider=" ~/.hermes/logs/agent.log | tail -5
# e.g. model=claude-opus-4-8 provider=anthropic  ← the live chat model this turn
```
Hindsight model = the daemon env grep above. State both separately and only from
verified sources.

## Pitfalls
- Editing `.env` but not restarting → daemon keeps old model. Always restart + verify.
- Reading `.env` and assuming that's live → the launcher injects extra vars from
  config.yaml; the process env is the truth.
- Grepping only one PID after restart → may catch a dying old process. Grep all
  `hindsight-api --daemon` PIDs.
- Confusing embeddings with the reasoning LLM — tuning here never touches embeddings.
- Logging the change: Tanzim keeps a running "Friday X.0 Changes" Google Sheet ledger
  (dated). Append every infra change there as a row (Date, Component, Change, Detail, Status).
