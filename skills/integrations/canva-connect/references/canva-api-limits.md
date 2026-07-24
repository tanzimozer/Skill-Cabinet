# Canva Connect API — Known Limitations (confirmed May 26, 2026)

## What the API cannot do
- **Rename designs** — `PATCH /v1/designs/{id}` returns `404 endpoint_not_found`. No PUT or POST update equivalent exists. Renaming must be done manually in the Canva UI (click title at top of editor).
- **Read text content from designs** — The API exposes metadata, thumbnails, and page dimensions only. Text layers are not accessible via any v1 endpoint.

## Reading design content — PDF export method
1. `POST https://api.canva.com/rest/v1/exports` with body:
   ```json
   {"design_id": "DAH...", "format": {"type": "pdf", "export_quality": "regular"}}
   ```
   ⚠️ `format` must be an object with a `type` field — `"format": "pdf"` (string) returns `invalid_field: 'type' must not be null`
2. Poll `GET /v1/exports/{job_id}` until `status == "success"` (~3s typical)
3. Download `job.urls[0]` and run `pdftotext file.pdf -` or use `pypdf`

## Token lifespan
- Access token: ~4 hours
- Refresh token: long-lived BUT entire lineage is revoked on logout or password change
- Error: `400 invalid_grant: Token lineage has been revoked` → requires full re-auth
- Full re-auth: PKCE flow using client_id/secret from `~/.hermes/.canva_credentials`; save pending state to `~/.hermes/.canva_oauth_pending.json`

## Creds file location
`~/.hermes/.canva_credentials` — fields: `client_id`, `client_secret`, `redirect_uri`, `access_token`, `refresh_token`
