---
name: hermes-hindsight-configuration
category: infrastructure
description: Configuring the Hermes runtime and the Hindsight memory daemon — model selection, per-operation model overrides, the config.yaml → env → daemon launch chain, and safe restart/verify procedure.
triggers:
  - "Pair / change the model used by Hindsight memory"
  - "What model is Hermes / the agent running?"
  - "Split memory operations across models (cost vs quality)"
  - "Edit ~/.hermes/config.yaml or ~/.hermes/.env model settings"
  - "Restart the Hindsight daemon / memory not updating"
---

# Hermes & Hindsight Configuration

How Tanzim's runtime picks its models, and how to safely change them. Two distinct layers: the **agent model** (Hermes) and the **memory daemon model** (Hindsight). They are configured separately.

## Authoritative model source — never guess

The model serving the agent is **NOT introspectable from inside**. Do not name a model from memory or past notes. The authoritative source is the runtime environment block. If asked "what model are we running" and the block isn't present, say you're not certain rather than naming one.

The **configured default** lives in `~/.hermes/config.yaml` line 1: `model: <name>`, with `providers.default.base_url` setting the endpoint and `fallback_providers:` listing the failover chain (e.g. gemini-2.5-flash). Note: the *configured* default can differ from what *actually ran* — a session can land on the fallback. Verify the live route if it matters for billing.

## The config → env → daemon launch chain (critical mental model)

The Hindsight daemon (`hindsight-api --daemon --port 9177`) does NOT read config.yaml directly. The chain:

1. `~/.hermes/config.yaml` — Hermes-level config. The `memory:` block sets `provider: hindsight`.
2. `hindsight-embed -p hermes daemon start` — the launcher. Reads config + translates into `HINDSIGHT_API_*` env vars, then spawns the daemon.
3. `~/.hermes/.env` — loaded as `EnvironmentFile` by the systemd unit `hindsight.service`. This is where raw `HINDSIGHT_API_*` overrides go.
4. The daemon process inherits the merged environment.

**Key launcher behaviour (lets overrides win):** `hindsight-embed`'s cli only sets a var `if key not in os.environ` (cli.py ~line 115). So **anything you put in `.env` is NOT clobbered** by the launcher's defaults. This is what makes per-operation overrides via `.env` reliable.

## Hindsight is THREE LLM jobs, not one

Hindsight splits memory work across separately-configurable operations. Each has its own env-var prefix; all fall back to the global `HINDSIGHT_API_LLM_*` (and inherit the global API key) if unset:

| Operation | Env prefix | Volume | Quality sensitivity | Recommended model |
|---|---|---|---|---|
| RETAIN (fact extraction) | `HINDSIGHT_API_RETAIN_LLM_*` | High, constant | Low | Cheap (Haiku) |
| CONSOLIDATION (dedup/merge) | `HINDSIGHT_API_CONSOLIDATION_LLM_*` | High | Low | Cheap (Haiku) |
| REFLECT (cross-memory synthesis) | `HINDSIGHT_API_REFLECT_LLM_*` | Low | **High** | Strong (Opus) |
| (global default) | `HINDSIGHT_API_LLM_*` | — | — | covers anything unset |

**Embeddings are separate and local** (Postgres vector store, `pg0://hindsight-embed-hermes`). Model swaps do NOT touch embeddings — only the reasoning LLM.

Each prefix has the suffix set: `_PROVIDER`, `_MODEL`, `_BASE_URL`, `_API_KEY` (optional — inherits global), plus tuning (`_MAX_CONCURRENT`, `_MAX_RETRIES`, `_TIMEOUT`, etc.). Full var list lives in the installed `hindsight_api/config.py`.

## The recommended split (Tanzim's chosen pattern, Jun 2026)

Set the global to cheap, override only REFLECT to strong. This is the cost-smart default:

```
# Global → covers RETAIN + CONSOLIDATION (high-volume, cheap)
HINDSIGHT_API_LLM_PROVIDER=anthropic
HINDSIGHT_API_LLM_MODEL=claude-haiku-4-5
# REFLECT → strong model for synthesis depth (api_key inherits from global)
HINDSIGHT_API_REFLECT_LLM_PROVIDER=anthropic
HINDSIGHT_API_REFLECT_LLM_MODEL=claude-opus-4-8
HINDSIGHT_API_REFLECT_LLM_BASE_URL=https://api.anthropic.com
```

If the global is *already* Haiku, RETAIN/CONSOLIDATION are covered by inheritance — the only edit needed is the REFLECT override. Always check the live daemon env before assuming what's set.

## Safe change procedure (always follow)

1. **Backup first:** `cp ~/.hermes/.env ~/.hermes/.env.bak-$(date +%Y%m%d-%H%M%S)`
2. **Inspect the LIVE daemon, not just the file** — the running config may already differ from the file. Read `/proc/<pid>/environ` of the `hindsight-api --daemon` process: `tr '\0' '\n' < /proc/<PID>/environ | grep HINDSIGHT_API` (redact keys before showing).
3. **Append overrides** to `.env` with a comment explaining why (redirecting into a dotfile triggers a security-approval prompt — expected).
4. **Restart:** `systemctl --user restart hindsight.service` (fallback: `hindsight-embed -p hermes daemon restart`).
5. **Verify two things:** `curl -s http://127.0.0.1:9177/health` returns `{"status":"healthy","database":"connected"}`, AND re-read the *new* PID's `/proc/<pid>/environ` to confirm the override landed. Don't trust health alone — confirm the actual model vars on the new process.

Note: `/config` endpoint returns 404 — there is no live config readout API. `/proc/<pid>/environ` is the ground truth.

## Agent model config — layering gotcha (Jul 2026)

`~/.hermes/config.yaml` uses YAML's last-key-wins rule. The primary model is declared at line 1 (`model: default: claude-sonnet-4-6`), but **appended profile/override blocks lower in the same file can shadow it**. When diagnosing "what model is actually running":

1. `grep -n "^model:\|model: claude" ~/.hermes/config.yaml` — look for multiple hits
2. The **lowest** matching entry in the file wins
3. To change the active model, find and patch the lowest-occurring declaration — not just line 1
4. The fallback chain (`fallback_providers:`) is separate; Opus in the fallback chain does NOT mean Opus is the primary
5. Auxiliary models (vision, session_search) are configured under `auxiliary:` — change them separately if you want full consistency

**Correct audit sequence when user says "change to X":**
```bash
grep -n "opus\|sonnet\|haiku\|claude" ~/.hermes/config.yaml   # find all occurrences
# patch the lowest-occurring primary override, not just line 2
# then verify: grep -n "^model:" ~/.hermes/config.yaml
```

**Gateway restart note:** restarting the gateway via terminal kills the session mid-command — always times out. That's expected. The restart still happens; confirmation comes when the agent comes back online.

## Pitfalls
- Don't edit config.yaml expecting the daemon to pick it up live — it's a launch-time translation, requires restart.
- Don't put the override in config.yaml's memory block; the per-op model vars are env-only.
- After restart there may be a brief transient second process (a snapshot shell); grep specifically for `hindsight-api --daemon` to find the real daemon PID.
- Never expose `HINDSIGHT_API_*` keys or daemon internals in a group chat.
- config.yaml line 1 is NOT always the effective model — check for appended override blocks lower in the file.

## Session Reference
- Haiku/Opus REFLECT split — full wiring, launcher inspection, verification (Jun 18 2026): see references/hindsight-model-split-jun2026.md
