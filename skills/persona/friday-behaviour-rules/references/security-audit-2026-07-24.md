# Security Audit — Hermes/Friday System (2026-07-24)

Senior pen-tester grade. Read-only pass + all fixes applied same session.

## Fixes Applied

| Sev | Finding | Fix |
|-----|---------|-----|
| C | Trello API key + token in world-readable state.db | Left intentionally (Tanzim: "keep it") |
| C | Google OAuth token in errors.log | chmod 600 all Google token files |
| C | google_token.json, google_client_secret.json world-readable | chmod 600 |
| C | Instagram session cookie world-readable | chmod 600 .ig_cookies.json |
| H | All log files world-readable, contain PII | chmod 640 logs/*.log |
| H | WhatsApp bridge fail-open (no BRIDGE_TOKEN = open) | Changed to fail-closed (throws on missing token) |
| H | wa_contacts.json / wa_groups.json world-readable PII | chmod 600 |
| H | kanban.db / hindsight.db world-readable | chmod 600 |
| H | Webhook DEFAULT_HOST = 0.0.0.0 | Changed to 127.0.0.1 |
| M | hermes-agent/skills/ group-writable | chmod -R o-w |
| M | CUPS — not installed, skipped | N/A |

## Open / Not Fixed

- **Trello key in state.db** — Tanzim elected to keep. Key: 70c5827... Token: ATTA74e8...
- **SSH on all interfaces** — standard for server, no action taken
- **Ollama on localhost:11434** — low risk, localhost only
- **hindsight-api on localhost:9177** — auth status unverified
- **Pre-commit secret scanning** — not installed (gitleaks/truffleHog)
- **auth.json partial key values** — low risk, file is 600

## Monitoring Built

- `/home/hermes/.hermes/scripts/health_check.sh` — every 5 min via cron
- `/home/hermes/.hermes/scripts/security_monitor.sh` — every 2 min via cron
- Alert method: `hermes send --to "whatsapp:Tanzim Ozer"`
- State dedup: `.health_state/` and `.security_state/` dirs (30-min and 15-min suppression)
