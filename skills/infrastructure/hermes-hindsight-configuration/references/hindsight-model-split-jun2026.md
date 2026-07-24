# Hindsight Model Split — Haiku + Opus REFLECT (June 18, 2026)

## Goal
Pair Haiku to Hindsight's high-volume memory ops to cut cost, keep synthesis on Opus.

## What we found on inspection
- Daemon: `hindsight-api --daemon --idle-timeout 0 --port 9177` (originally PID 3563).
- Launched by systemd user unit `hindsight.service`:
  - `EnvironmentFile=/home/hermes/.hermes/.env`
  - `ExecStart=.../hindsight-embed -p hermes daemon start`
- Live daemon env (`tr '\0' '\n' < /proc/3563/environ`) already showed:
  - `HINDSIGHT_API_LLM_PROVIDER=anthropic`
  - `HINDSIGHT_API_LLM_MODEL=claude-haiku-4-5`
  - So global was ALREADY Haiku → RETAIN + CONSOLIDATION covered by inheritance.
- `.env` itself only had `HINDSIGHT_LLM_API_KEY`, `HINDSIGHT_TIMEOUT/IDLE_TIMEOUT/BUDGET` — the `HINDSIGHT_API_*` vars were injected by the launcher from config.yaml at start, not present in `.env`.
- config.yaml had no `retain`/`reflect`/`consolidation` keys — those are env-only overrides.

## Why the override is safe
`hindsight_embed/cli.py` ~line 115: `if key not in os.environ:` before setting defaults → launcher will NOT overwrite an env var we already set. So a REFLECT override in `.env` survives the launch translation.

`hindsight_api/config.py` confirmed the per-op env var names:
- `HINDSIGHT_API_RETAIN_LLM_{PROVIDER,API_KEY,MODEL,BASE_URL,MAX_CONCURRENT,MAX_RETRIES,...}`
- `HINDSIGHT_API_REFLECT_LLM_{...}`
- `HINDSIGHT_API_CONSOLIDATION_LLM_{...}`
- Global: `HINDSIGHT_API_LLM_{...}`
- Embeddings/reranker are separate (`HINDSIGHT_API_EMBEDDINGS_*`, local Postgres vector store) — untouched.

## What we applied
Backed up `.env`, then appended:
```
HINDSIGHT_API_REFLECT_LLM_PROVIDER=anthropic
HINDSIGHT_API_REFLECT_LLM_MODEL=claude-opus-4-8
HINDSIGHT_API_REFLECT_LLM_BASE_URL=https://api.anthropic.com
```
(REFLECT api_key intentionally omitted — inherits global `HINDSIGHT_API_LLM_API_KEY`.)

## Restart + verify
```
systemctl --user restart hindsight.service
sleep 6
curl -s http://127.0.0.1:9177/health        # -> {"status":"healthy","database":"connected"}
NEWPID=$(pgrep -f 'hindsight-api --daemon' | head -1)
tr '\0' '\n' < /proc/$NEWPID/environ | grep -iE 'HINDSIGHT_API_(LLM|REFLECT_LLM)_(MODEL|PROVIDER)'
```
New daemon (PID 65267) confirmed carrying:
- `HINDSIGHT_API_LLM_MODEL=claude-haiku-4-5` / provider anthropic
- `HINDSIGHT_API_REFLECT_LLM_MODEL=claude-opus-4-8` / provider anthropic / base_url api.anthropic.com

## Gotchas hit
- First verify grep returned empty because it matched the transient snapshot shell PID, not the daemon. Re-ran with `pgrep -f 'hindsight-api --daemon'` and iterated per-PID to get the real one.
- `/config` endpoint → 404. No live config API; `/proc/<pid>/environ` is ground truth.
- Appending to `.env` triggered a HIGH security-approval prompt (dotfile overwrite) — expected, approved.

## Result
- RETAIN + CONSOLIDATION → claude-haiku-4-5 (cheap, high-volume).
- REFLECT → claude-opus-4-8 (synthesis depth).
- Embeddings local, untouched. Backup at `~/.hermes/.env.bak-<timestamp>`.
