---
name: hermes-infrastructure
# See references/hindsight-api-dedup-jun2026.md for Hindsight API shape and dedup approach
description: Diagnosing and fixing Hermes system components — gateway, Hindsight, bridge, systemd services
category: operations
---

# Hermes Infrastructure — Ops & Fixes

## WhatsApp Bridge 401 — Outbound Sends Failing

### Symptom
`send_message` returns `WhatsApp bridge error (401)` on all outbound sends. Direct curl with token works. Bridge `/health` returns connected.

### Root Cause
`WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env` not loaded into gateway process — no `EnvironmentFile` in the systemd service unit.

### Fix
Add to `~/.config/systemd/user/hermes-gateway.service` under `[Service]`:
```
EnvironmentFile=/home/hermes/.hermes/.env
```
Then reload: `systemctl --user daemon-reload && systemctl --user restart hermes-gateway.service`

### Diagnostic path
1. Direct curl test: `curl -s -X POST http://localhost:3000/send -H "Authorization: Bearer $TOKEN" -d '{"chatId":"ID","message":"test"}'`
2. Works → gateway env issue. Fix: EnvironmentFile
3. Returns `item-not-found` → dead group ID, not auth
4. Returns 401 on direct curl → bridge token wrong/expired

---

## Hindsight API Down (port 9177) While Postgres Running

### Symptom
`hindsight_recall` fails with connection refused on 9177. `systemctl --user status hindsight.service` shows active but only postgres PIDs visible.

### Root Cause
systemd service restarts Postgres fine but doesn't relaunch the API layer on top.

### Fix
```bash
~/.hermes/hermes-agent/venv/bin/hindsight-embed -p hermes daemon start
```
The service file uses `Type=forking` — daemon start is idempotent if already running.

---

## Hindsight Deduplication — SQL Direct

### Connect
```python
import json, subprocess, os
inst = json.load(open('/home/hermes/.pg0/instances/hindsight-embed-hermes/instance.json'))
pw, user, db, port = inst['password'], inst['username'], inst['database'], inst['port']
env = {**os.environ, 'PGPASSWORD': pw}
pg = '/home/hermes/.pg0/installation/18.1.0/bin/psql'
```

### Dedup exact duplicates (keep highest access_count, then oldest)
```sql
DELETE FROM memory_units WHERE bank_id='hermes' AND id NOT IN (
  SELECT DISTINCT ON (LEFT(text, 200)) id FROM memory_units WHERE bank_id='hermes'
  ORDER BY LEFT(text, 200), access_count DESC, mentioned_at ASC NULLS LAST
);
```

### Delete noise patterns
```sql
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%Background process proc_%completed%';
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%proc_%completed successfully%';
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%User confirmed Friday availability%';
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%gateway interruption%';
```

### Backup before any bulk delete
```bash
~/.pg0/installation/18.1.0/bin/pg_dump -h localhost -p 5432 -U hindsight hindsight -f ~/.hermes/backups/hindsight_backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## Memory Architecture

| Layer | File | Speed | Limit | Purpose |
|-------|------|-------|-------|---------|
| USER.md | `~/.hermes/USER.md` | Instant | 12k | Stable facts about Tanzim — never changes |
| MEMORY.md | `~/.hermes/MEMORY.md` | Instant | 15k | Protocols, operational rules |
| Hindsight | Postgres via API | Query | ~unlimited | Time-bound events and decisions only |

**Rule:** Stable facts (team, identity, preferences) belong in USER.md. If it's already in USER.md, DO NOT re-add to Hindsight.

Config: `~/.hermes/config.yaml` → `memory.user_char_limit` (currently 12000)
