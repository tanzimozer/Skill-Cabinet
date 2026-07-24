# Security Audit — May 30 2026

Full vulnerability list from first structured audit of Tanzim's Hermes VM.

## 🔴 CRITICAL (fixed)
1. **Webhook secret = `INSECURE_NO_AUTH`** — `~/.hermes/config.yaml` `platforms.webhook.extra.secret`. Replaced with 64-char random hex token.
2. **Port 8645 on 0.0.0.0** — `voice_server.py` (PID 192544). Changed `uvicorn.run(host="0.0.0.0")` → `host="127.0.0.1"`, restarted.
3. **SSH (port 22) on 0.0.0.0** — by design; noted, not changed.

## 🟠 HIGH (fixed)
4. **WhatsApp bridge `/send` etc — zero auth** — Express bridge.js had no token middleware. Added Bearer token middleware after DNS-rebinding check. Token stored as `WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`. Python gateway (`gateway/platforms/whatsapp.py`) updated to inject `Authorization: Bearer <token>` header on all bridge calls.
5. **Hindsight API (9177) — zero auth** — `hindsight-api` binary has no auth flag. Localhost-only so contained. **Unfixed — known gap.**
6. **Session files world-readable (`664`)** — `~/.hermes/sessions/*.jsonl` and `*.json`. Fixed: `chmod 600`.
7. **`redact_secrets: false`** — `~/.hermes/config.yaml` `security.redact_secrets`. Set to `true`.

## 🟡 MEDIUM (noted)
8. **Prompt injection via WhatsApp** — architectural; mitigated by grants.json identity tiers.
9. **Hindsight append-only, no expiry** — backup CSVs in Google Drive contain historical data. Accepted risk.
10. **Cron jobs run with full agent perms** — no per-job sandboxing. Accepted risk.
11. **`CLAUDE_CODE_OAUTH_TOKEN` in `.env`** — plaintext but file is `600`. Accepted.

## 🔵 LOW (noted)
12. Ollama on localhost:11434 — localhost-only, low risk.
13. Hindsight CSV backups in Drive — accepted.
14. Chrome debug process running.
15. No rate limiting on internal APIs.

## Fixed permissions
- `~/.hermes/hindsight/` → `700` (was `775`)
- `~/.hermes/hindsight/config.json` → `600` (was `664`)
- `~/.hermes/sessions/*.json` / `*.jsonl` → `600` (was `664`)
- `voice_server.py` → localhost only (was `0.0.0.0`)
- `config.yaml` webhook secret → rotated from `INSECURE_NO_AUTH`
