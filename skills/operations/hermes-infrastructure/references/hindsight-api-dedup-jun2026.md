# Hindsight API — Dedup Notes (June 2026)

## Correct port
Hindsight API runs on **:9177**, not :5001 or :8888.
Health check: `curl http://localhost:9177/health` → `{"status":"healthy","database":"connected"}`

## API shape (discovered via /openapi.json)
- List memories: `GET /v1/default/banks/hermes/memories/list?limit=200&offset=0`
  - Response key is `items`, not `memories`
  - Each item has `id`, `text`, `date`, `fact_type`, `entities`, `tags`
- Bulk delete: `DELETE /v1/default/banks/hermes/memories` (deletes ALL — destructive)
- Individual memory: `GET /v1/default/banks/hermes/memories/{memory_id}` — GET only, no DELETE on individual IDs (405 Method Not Allowed)
- Recall/search: `POST /v1/default/banks/hermes/memories/recall` with `{"query":"...","top_k":100}`
- Consolidate: `POST /v1/default/banks/hermes/consolidate`

## Dedup approach
Individual memory deletion via API is not supported (405). Dedup must go through:
1. The nightly gardener cron jobs (`7f2b039ebc7e` 11:30pm, `7a02da23ceba` 3am) — preferred
2. Direct Postgres access if urgent
3. Bulk delete endpoint filters by `type` (world/experience/opinion) — not by content

## Duplicate volume found June 2026
~340 near-duplicate entries (226 duplicate groups), primarily Pepper Potts style preference fragments written across multiple sessions. Gardener jobs updated to aggressively merge these.
