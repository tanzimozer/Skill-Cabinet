---
name: hindsight-maintenance
description: Manage, audit, wipe, and rebuild the Hindsight long-term memory database. Covers backup procedures, schema navigation, codeword-leak scrubbing, and clean rebuild patterns.
triggers:
  - "clean up memory"
  - "wipe hindsight"
  - "memory organisation"
  - "hindsight backup"
  - "rebuild memory"
  - "memory bloat"
  - "duplicate entries"
  - "codeword leak"
---

# Hindsight DB Maintenance

## Dedup Run History
| Date | Before | After | Removed | Method |
|------|--------|-------|---------|--------|
| Jun 2, 2026 | 5,315 | 3,639 | 1,676 | Two-pass SQL on LEFT(text,120) + LEFT(text,60)+date |
| Jun 4, 2026 | 6,075 | 5,902 | 173 | Exact dedup on LEFT(text,200) + targeted noise deletion |

**Root causes seen:** repeated session-end writes for same event; nightly gardener appending rather than merging; process completion logs stored as facts.

**Backup location (Jun 4):** `~/.hermes/backups/hindsight_backup_20260604_004023.sql` (84MB)

## Noise Deletion Patterns (June 2026)

These SQL patterns safely removed low-value ephemeral entries. Run after the dedup passes:

```sql
-- Process completion logs (never useful long-term)
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE 'Background process proc_%completed%exit code 0%';
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%proc_%completed successfully%';

-- Resolved one-time infrastructure events
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%disk space constraint%35GB%40GB%';
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE '%zip%unzip%upload to Google Drive%delete%';

-- Identity map near-dupes (keep richest, remove repeated confirmations)
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE 'Identity map confirmed%Tanzim%Blair%Tahmeed%';
DELETE FROM memory_units WHERE bank_id='hermes' AND text ILIKE 'Hermes Agent fixed identity mapping%diagnosing sender IDs%';

-- Instagram cookie sharing events (transient — session state only)
DELETE FROM memory_units WHERE bank_id='hermes'
  AND text ILIKE '%Instagram%authentication cookies%session data%'
  AND LENGTH(text) < 400;

-- Taylor Crow stale entries (keep the rich one with HITTlab/Equinox)
DELETE FROM memory_units WHERE bank_id='hermes'
  AND text ILIKE '%Taylor Crow%Seattle%trainer%early collaborator%'
  AND text NOT ILIKE '%HITTlab%Equinox%';
```

## Zero-Downtime Dedup Process

**Safe to run on live DB — no restart, no API downtime.**

### Step 1: Full SQL backup first
```bash
PGPASSWORD=hindsight /home/hermes/.pg0/installation/18.1.0/bin/pg_dump \
  -h localhost -p 5432 -U hindsight hindsight \
  > ~/.hermes/backups/hindsight_backup_$(date +%Y%m%d_%H%M%S).sql
```

-- Step 2: Dedup pass 1 — exact near-dupes (same first 120 chars)
DELETE FROM memory_units
WHERE id IN (
  SELECT id FROM (
    SELECT id,
           ROW_NUMBER() OVER (
             PARTITION BY LEFT(text, 120)
             ORDER BY proof_count DESC, created_at ASC
           ) AS rn
    FROM memory_units
  ) ranked WHERE rn > 1
);

-- Step 3: Dedup pass 2 — same first 60 chars + same event_date
DELETE FROM memory_units
WHERE id IN (
  SELECT id FROM (
    SELECT id,
           ROW_NUMBER() OVER (
             PARTITION BY LEFT(text, 60), DATE(event_date)
             ORDER BY proof_count DESC, LENGTH(text) DESC, created_at ASC
           ) AS rn
    FROM memory_units
    WHERE event_date IS NOT NULL
  ) ranked WHERE rn > 1
);

-- Step 4: Vacuum
VACUUM ANALYZE memory_units;
```

**Column name is `text`, NOT `content`** — early attempts failed with `column "content" does not exist`.

**CASCADE on memory_links:** FK constraints use `ON DELETE CASCADE` — deleting from `memory_units` auto-cleans `memory_links`. No manual cleanup needed.

**When to run:** When Tanzim says "organise memory", "memory is bloated", "you're forgetting things", or the hindsight recall tool returns 30+ near-identical entries on a topic.

## Hindsight API down (port 9177 not responding)

Symptom: `hindsight_recall` returns `Cannot connect to host 127.0.0.1:9177`.

**Root cause pattern (confirmed June 2026):** `systemctl --user restart hindsight.service` keeps Postgres alive but does NOT restart the API layer on top. `daemon status` reports "Daemon is not running" even though postgres process is healthy.

**Fix:**
```bash
~/.hermes/hermes-agent/venv/bin/hindsight-embed -p hermes daemon start
```

Verify after:
```bash
curl -s http://127.0.0.1:9177/health
# expect: {"status":"healthy","database":"connected"}
```

Do NOT attempt to restart the WhatsApp bridge or gateway as part of Hindsight recovery — they are unrelated.

## Architecture
- Hindsight API on port **9177**
- Backed by embedded PostgreSQL (`pg0`) — **instance `hindsight-embed-hermes`**
- DB connection: host=localhost, port=**5432**, user=`hindsight`, password=`hindsight`, db=`hindsight`
- **⚠️ Port confusion**: two pg0 instances exist — `hindsight` (5432) AND `hindsight-embed-hermes` (5432). They share port 5432 but only one runs at a time. Verify with `ps aux | grep postgres` — look for the `hindsight-embed-hermes` data dir path to confirm the live one.
- Password confirmed via `~/.pg0/instances/hindsight-embed-hermes/instance.json` → `password` field

## Database connection
```bash
# Read password from instance.json (authoritative source)
PW=$(python3 -c "import json; print(json.load(open('/home/hermes/.pg0/instances/hindsight-embed-hermes/instance.json'))['password'])")
PGPASSWORD=$PW /home/hermes/.pg0/installation/18.1.0/bin/psql \
  -h localhost -p 5432 -U hindsight -d hindsight
```

## Memory Architecture — Three Layers

Understanding this shapes what belongs where:

| Layer | File | Speed | Limit | What belongs here |
|-------|------|-------|-------|-------------------|
| USER.md | Injected at startup | Instant | 12,000 chars | Stable personal facts: who Tanzim is, team, cap table, health, devices, preferences |
| MEMORY.md | Injected at startup | Instant | 15,000 chars | Operational protocols: codewords, group chat rules, credential map, platform behaviour |
| Hindsight | Live query required | ~1s | Unlimited | Time-bound events, decisions, context — one entry per fact, deduped |

**Key principle:** stable facts belong in USER.md/MEMORY.md, NOT Hindsight. When Hindsight has 10 copies of "Tanzim is CEO of TIMBR", that fact should be in USER.md and pruned from Hindsight entirely. Hindsight is for *events and decisions*, not *identity*.

**Config:** `~/.hermes/config.yaml` → `memory.user_char_limit` (currently 12000) and `memory.memory_char_limit` (currently 15000). Adjustable.
| Table | Purpose |
|---|---|
| `documents` | Original retained text (hindsight_retain calls) |
| `memory_units` | Extracted/processed fact units (embeddings etc) |
| `entities` | Named entities extracted |
| `chunks` | Text chunks linked to documents |
| `memory_links` | Relationships between memory units |

## Export before any wipe
```bash
PGPASSWORD=hindsight psql -h 127.0.0.1 -p 5433 -U hindsight -d hindsight \
  -c "\COPY (SELECT id, bank_id, original_text, tags, created_at FROM documents ORDER BY created_at) \
  TO '/home/hermes/.hermes/backups/hindsight_docs_backup_YYYYMMDD.csv' WITH CSV HEADER;"

PGPASSWORD=hindsight psql -h 127.0.0.1 -p 5433 -U hindsight -d hindsight \
  -c "\COPY (SELECT id, bank_id, text, context, fact_type, tags, created_at FROM memory_units ORDER BY created_at) \
  TO '/home/hermes/.hermes/backups/hindsight_units_backup_YYYYMMDD.csv' WITH CSV HEADER;"
```

## Upload backup to Drive before wiping
```python
from googleapiclient.http import MediaFileUpload
HERMES_FOLDER = '1yGZuAcD4jzf8257cXMTjZeGsfMcK0Ba-'
media = MediaFileUpload(path, mimetype='text/csv')
drive.files().create(body={'name': fname, 'parents': [HERMES_FOLDER]}, media_body=media, fields='id').execute()
```

## Wipe procedure (CASCADE order — respect FK constraints)
```sql
BEGIN;
TRUNCATE TABLE memory_links CASCADE;
TRUNCATE TABLE unit_entities CASCADE;
TRUNCATE TABLE chunks CASCADE;
TRUNCATE TABLE memory_units CASCADE;
TRUNCATE TABLE documents CASCADE;
TRUNCATE TABLE entities CASCADE;
TRUNCATE TABLE entity_cooccurrences CASCADE;
TRUNCATE TABLE mental_models CASCADE;
TRUNCATE TABLE audit_log CASCADE;
TRUNCATE TABLE async_operations CASCADE;
COMMIT;
```

## hindsight-admin backup (official tool)
```bash
/home/hermes/.hermes/hermes-agent/venv/bin/hindsight-admin backup /path/to/output.zip
```
⚠️ This fails with `relation "public.banks" does not exist` when called from inside a running event loop (asyncio conflict). Use direct psql export instead.

## Rebuild after wipe
Seed with `hindsight_retain` calls covering these class-level topics:
1. Owner/Tanzim profile
2. Identity map (all WhatsApp sender IDs)
3. TIMBR products and company state
4. Blair profile
5. Tahmeed profile
6. All active integrations + credentials
7. Job search state
8. Infrastructure (VM, WhatsApp routing)
9. Website known issues
10. TerraJob/automation system
11. Editorial/production state
12. Cron jobs
13. Backup system
14. Any person profiles (Towsif, Irissa, etc.)
15. Security/SOUL change log

## Cross-match after rebuild
```python
import csv
csv.field_size_limit(10 * 1024 * 1024)  # required — rows can exceed 131072 char default

topics_found = set()
with open('/path/to/backup.csv') as f:
    for row in csv.DictReader(f):
        text = (row.get('original_text', '') or '').lower()
        for kw in keyword_list:
            if kw in text:
                topics_found.add(kw)
```

## Hindsight REST API — key endpoints (discovered Jun 2026)

Full OpenAPI schema at: `http://localhost:9177/openapi.json`

**List memories (paginated):**
```python
r = requests.get('http://localhost:9177/v1/default/banks/hermes/memories/list',
                 params={'limit': 200, 'offset': 0})
data = r.json()
items = data['items']        # ← key is 'items', NOT 'memories'
total = data['total']
# Each item has: id, text, context, date, fact_type, entities, tags, chunk_id
```

**Recall (semantic search):**
```python
r = requests.post('http://localhost:9177/v1/default/banks/hermes/memories/recall',
                  json={'query': 'pepper potts style', 'top_k': 100})
# Returns: {'memories': [...]}  ← 'memories' key here (not 'items')
```

**Delete — BULK ONLY, no per-ID delete:**
```
DELETE /v1/default/banks/{bank_id}/memories?type={world|experience|opinion}
```
- `type` filter is optional — omit to delete all memories in the bank.
- There is NO `DELETE /memories/{id}` endpoint (returns 405). Per-ID deletion is not supported.
- To surgically remove duplicates, use direct PostgreSQL — see SQL dedup section above.

**Trigger consolidation (dedup + synthesis):**
```python
r = requests.post('http://localhost:9177/v1/default/banks/hermes/consolidate')
```

**Banks list:**
```python
r = requests.get('http://localhost:9177/v1/default/banks')
# Returns: {'banks': [{'bank_id': 'hermes', 'fact_count': N, ...}]}
```

**Get bank stats:**
```python
r = requests.get('http://localhost:9177/v1/default/banks/hermes/stats')
```

## Pitfalls
- **Port 5432 is the live instance** (hindsight-embed-hermes) — older skill notes saying 5433 are wrong. Always read password/user from `instance.json` rather than hardcoding.
- **instance.json is authoritative** — `/home/hermes/.pg0/instances/hindsight-embed-hermes/instance.json` contains live port, user, password, and db name. Read it programmatically rather than guessing.
- **Field size limit**: default CSV field limit is 131072 — set `csv.field_size_limit(10*1024*1024)` before reading backup
- **Hindsight is append-only via tool**: cannot delete via `hindsight_retain` — only wipe via direct DB
- **Always backup to Drive BEFORE wiping** — local backups survive but Drive is the safety net
- **Never persist codeword** in any hindsight entry — if spotted, add scrub entry + plan wipe
- **systemctl restart doesn't restart the API layer** — only Postgres comes back up. Always run `hindsight-embed -p hermes daemon start` after any restart, and verify with `curl http://127.0.0.1:9177/health`

## References
- `references/rebuild-checklist.md` — ordered list of topics for post-wipe rebuild
