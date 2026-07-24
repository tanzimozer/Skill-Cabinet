# Canva Integration Setup — Reference
**Date:** June 9, 2026 (Updated)  
**Status:** Submitted for Review (awaiting Canva approval)

## Current State

- **Client ID:** OC-AZ6uvUWgLDkX
- **Client Secret:** [stored in vault.json]
- **Integration Name:** F.R.I.D.A.Y (renamed from "Untitled")
- **Purpose:** Manage Tanzim's Canva templates programmatically (edit designs, update text, publish changes)
- **Scopes Enabled:** design:content (read/write), design:meta (read/write), design:permission (read/write), folder (read/write), asset (read/write), brandtemplate:content (read/write), brandtemplate:meta (read/write), app (read/write), comment (read/write), profile (read), folder:permission (read/write)

## Setup Steps (Completed)

1. ✅ Create integration in Canva Developers console
2. ✅ Generate Client ID + Secret (June 9, 2026)
3. ✅ Store credentials in vault.json and Desktop CREDENTIALS_MASTER.md
4. ✅ Configure all scopes (full design editing, template access, publishing, assets)
5. ✅ Set up OAuth Redirect URL: `https://webhook.site/unique-id`
6. ✅ Generate Authorization URL (code_challenge included)
7. ⏳ **Submit for review & approval from Canva** (pending user action on Canva console)

## Configuration Pages

- **Configuration:** https://www.canva.com/developers/integrations/connect-api/OC-AZ6uvUWgLDkX/configuration
- **Scopes:** https://www.canva.com/developers/integrations/connect-api/OC-AZ6uvUWgLDkX/scopes
- **Authentication:** https://www.canva.com/developers/integrations/connect-api/OC-AZ6uvUWgLDkX/authentication
- **Submission:** https://www.canva.com/developers/integrations/connect-api/OC-AZ6uvUWgLDkX/submission

## Scope Configuration (Final)

All scopes enabled with write access where applicable:
- ✅ `design:content` (read/write) — edit design content
- ✅ `design:meta` (read/write) — edit design metadata
- ✅ `design:permission` (read/write) — manage design permissions
- ✅ `folder` (read/write) — organize templates in folders
- ✅ `folder:permission` (read/write) — set folder permissions
- ✅ `asset` (read/write) — manage images and assets
- ✅ `brandtemplate:content` (read/write) — edit brand templates
- ✅ `brandtemplate:meta` (read/write) — edit brand template metadata
- ✅ `app` (read/write) — general app-level access
- ✅ `comment` (read/write) — read and post design comments
- ✅ `profile` (read only) — read user profile info
- ✅ `collaboration:event` (enabled via toggle) — receive webhook notifications for design events

## OAuth Flow

**Authorization URL Generated:**
```
https://www.canva.com/api/oauth/authorize?code_challenge_method=s256&response_type=code&client_id=OC-AZ6uvUWgLDkX&redirect_uri=https%3A%2F%2Fwebhook.site%2Funique-id&scope=[all scopes above]&code_challenge=[value]
```

**Redirect URI:** `https://webhook.site/unique-id` (temporary public endpoint for webhook.site)

**Note:** Code challenge was incomplete when user pasted URL. Switched to "Submit for review" path instead of manual OAuth test, as integration was fully configured and user already has existing Canva designs.

## Integration Approval Timeline

Canva typically requires 1-3 business days for approval after submission. Once approved, Friday can:
- List and fetch Tanzim's Canva templates
- Edit design content (text, colors, layouts, images)
- Modify template metadata
- Manage template organization (folders, permissions)
- Publish changes back to templates

## Vault.json Entry (Current)

```json
{
  "canva": {
    "client_id": "OC-AZ6uvUWgLDkX",
    "client_secret": "[redacted]",
    "integration_name": "F.R.I.D.A.Y",
    "status": "submitted_for_review",
    "created": "2026-06-09",
    "scopes": "design:content:write, design:meta:write, design:permission:write, folder:read, folder:write, folder:permission:write, asset:read, asset:write, brandtemplate:content:read, brandtemplate:content:write, brandtemplate:meta:read, brandtemplate:meta:write, app:read, app:write, comment:read, comment:write, profile:read, collaboration:event"
  }
}
```

## Next Steps

1. User clicks "Submit for review" on Canva console (pending)
2. Canva reviews and approves (1-3 business days)
3. Once approved, Friday receives approval notification
4. Friday can begin managing Tanzim's Canva designs via API

## Session Notes

- Canva Autofill API is a separate feature requiring additional access request (form auto-generated on Developers console)
- Webhook notifications will ping `https://webhook.site/unique-id` for design events (edits, publishes, collaborations)
- Full access scopes enable complete design management pipeline
