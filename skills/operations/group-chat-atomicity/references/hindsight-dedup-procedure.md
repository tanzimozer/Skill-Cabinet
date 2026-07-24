# Hindsight Dedup Procedure
_June 2, 2026 — ran successfully, removed 1,676 dupes (5,315 → 3,639)_

## When to run

- Hindsight recall returns 10+ near-identical results for the same event
- Memory is sluggish or returning stale results
- Quarterly hygiene

## Safety first — backup

```bash
PGPASSWORD=hindsight /home/hermes/.pg0/installation/18.1.0/bin/pg_dump \
  -h 127.0.0.1 -p 5432 -U hindsight hindsight \
  > ~/.hermes/hindsight_backup_$(date +%Y%m%d_%H%M%S).sql
```

Backup is ~82MB. Verify it wrote before proceeding.

## Connect

```bash
PGPASSWORD=hindsight /home/hermes/.pg0/installation/18.1.0/bin/psql \
  -h 127.0.0.1 -p 5432 -U hindsight -d hindsight
```

Port is **5432** (not 5433 — common mistake). Password: `hindsight`.

## Schema

Key column is `text` (not `content`). Key tables:
- `memory_units` — 5,000+ rows (facts)
- `memory_links` — 300,000+ rows (relationships, cascade-deletes safely)

## Dedup queries (run in order)

```sql
-- Round 1: exact near-dupes (same first 120 chars)
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

-- Round 2: same first 60 chars + same event_date
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

-- Count after
SELECT COUNT(*) FROM memory_units;
```

## Verify key facts survived

```sql
SELECT LEFT(text, 90) AS sample FROM memory_units
WHERE text ILIKE '%Tanzim%sender%lid%'
   OR text ILIKE '%Sagar%TIMBR%authorized%'
   OR text ILIKE '%iCloud%tanzimx%'
   OR text ILIKE '%require_mention%'
   OR text ILIKE '%send-media%'
LIMIT 10;
```

## Vacuum after

```sql
VACUUM ANALYZE memory_units;
```

## Notes

- `memory_links` FK constraints use `ON DELETE CASCADE` — safe to delete from `memory_units`
- The `content` column does NOT exist — it's `text`
- Port 5432 (hindsight API runs on 9177, DB on 5432)
- No service restart needed — changes are live immediately
