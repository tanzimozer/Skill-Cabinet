---
name: hindsight-db-management
description: Backup, wipe, rebuild, and audit the Hindsight long-term memory database (PostgreSQL via pg0 embedded)
category: memory
tags: [hindsight, memory, postgres, backup, rebuild, security]
---

# Hindsight DB Management

Procedures for backing up, wiping, and rebuilding the Hindsight long-term memory store.

## Architecture

- Hindsight runs as `hindsight-api` on port **9177**
- Backed by **pg0 embedded PostgreSQL** instance `hindsight-embed-hermes` on port **5433**
- A second instance `hindsight` runs on port **5432** — this is empty/unused; don't confuse them
- Key tables: `documents` (681 source texts), `memory_units` (25k+ extracted facts), `entities`, `memory_links`, `chunks`

## Connection

```bash
PGPASSWORD=hindsight /home/hermes/.pg0/installation/18.1.0/bin/psql \
  -h 127.0.0.1 -p 5433 -U hindsight -d hindsight
```

## Backup (before any wipe)

```bash
# Export documents (source texts)
PGPASSWORD=hindsight /home/hermes/.pg0/installation/18.1.0/bin/psql \
  -h 127.0.0.1 -p 5433 -U hindsight -d hindsight \
  -c "\COPY (SELECT id, bank_id, original_text, tags, created_at FROM documents ORDER BY created_at) \
  TO '/home/hermes/.hermes/backups/hindsight_docs_backup_YYYYMMDD.csv' WITH CSV HEADER;"

# Export memory units (extracted facts)
PGPASSWORD=hindsight /home/hermes/.pg0/installation/18.1.0/bin/psql \
  -h 127.0.0.1 -p 5433 -U hindsight -d hindsight \
  -c "\COPY (SELECT id, bank_id, text, context, fact_type, tags, created_at FROM memory_units ORDER BY created_at) \
  TO '/home/hermes/.hermes/backups/hindsight_units_backup_YYYYMMDD.csv' WITH CSV HEADER;"
```

**Then upload both CSVs to Google Drive HERMES folder before wiping.**

Note: `hindsight-admin backup` CLI tool exists but errored in May 2026 (`relation "public.banks" does not exist`) — use direct psql COPY instead.

## Wipe (CASCADE order — respect foreign keys)

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

-- Verify
SELECT 'memory_units' as tbl, COUNT(*) FROM memory_units
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'entities', COUNT(*) FROM entities;
```

## Rebuild — what to re-seed

After a wipe, re-seed via `hindsight_retain` calls covering these core topics:
1. Tanzim owner profile (IDs, location, role, company)
2. Identity map (all known WhatsApp sender IDs + tiers)
3. TIMBR products and state
4. Blair Grimes profile (including injury log)
5. Tahmeed profile
6. All active integrations (paths, account IDs)
7. Job search state and active interviews
8. Infrastructure and WhatsApp routing
9. Website known issues
10. TerraJob and Linked Engine specs
11. Editorial Bible / magazine production standards
12. Active cron jobs
13. Backup system
14. WhatsApp bridge notes
15. Trello boards and credentials
16. Security / SOUL changes
17. Webflow state
18. Collaborators (Towsif, etc.)
19. MAGPROD Drive structure
20. Any pending injury/health notes for trainees

## Cross-match after rebuild

```python
import csv
csv.field_size_limit(10 * 1024 * 1024)

topics_found = set()
with open('/home/hermes/.hermes/backups/hindsight_docs_backup_YYYYMMDD.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        text = (row.get('original_text', '') or '').lower()
        for kw in ['webflow', 'towsif', 'blackwire', 'irissa', 'substack', ...]:
            if kw in text:
                topics_found.add(kw)
```

Compare against rebuild list — anything in backup not in rebuild = missed topic.

## Security note — codeword leaks

Hindsight is **append-only** via the API — old entries with leaked codewords cannot be deleted individually. The only remedy is a full wipe + rebuild. After a codeword rotation, always check if the old codeword appears in Hindsight and wipe if so.

## Pitfalls

- **Wrong instance**: port 5432 is empty; always use port 5433 for the live instance
- **CSV field size limit**: Python's default csv reader limit is 131072 bytes — set `csv.field_size_limit(10 * 1024 * 1024)` before reading backup files
- **hindsight-admin backup**: broken as of May 2026 (`asyncio.run() cannot be called from a running event loop`) — use direct psql COPY
- **Rebuild order matters**: retain the identity map and owner profile first — these gate everything else
