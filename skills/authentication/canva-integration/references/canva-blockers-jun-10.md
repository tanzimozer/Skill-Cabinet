# Canva Integration Blockers — Jun 10 Session

## Status Overview (Jun 10, 2026)

**TIMBR Canva Integration:**
- ✅ Credentials created (Client ID + Secret)
- ✅ OAuth scopes negotiated (design:content:write, folder:write, etc. — all permissions enabled)
- ✅ Authorization flow complete (user approved all scopes from tan.biz@icloud.com)
- ✅ Access token obtained and stored in vault
- ❌ **Submission to Canva blocked** (see below)

---

## Blocker #1: Localhost Redirect URI (HIGH SEVERITY)

### Problem
Canva requires **non-localhost public URL** for Production/Submission status. Our current redirect:
```
http://127.0.0.1:8080/callback
```

Canva blocks submission with:
> "Redirect URI must be a publicly accessible URL (non-localhost)"

### Why Localhost Was Used
Initial setup was Dev/Test only. Localhost is correct for local OAuth flows (user's machine accepts the redirect). But Canva classifies it as "development only" — submission requires public URL.

### Solution Options

**Option A: Public Webhook URL (Recommended)**
- Use webhook.site or similar free service for redirect capture
- Canva redirects to: `https://webhook.site/unique-id/callback`
- We capture auth code from webhook logs
- Trade-off: Extra hop, but zero infrastructure

**Option B: Public Server (Future)**
- Deploy small Express/Node server with `/callback` endpoint
- Canva redirects there; we capture auth code
- Return user to success page
- Trade-off: Requires server infrastructure, but cleaner UX

**Option C: Defer Submission**
- Keep current setup for development (localhost works fine for token refresh)
- Submit when public URL available
- Trade-off: Can't use Production features until submitted (if Canva enforces)

### Current State (Jun 10)
**CHOSEN:** Option C (defer). TIMBR integration is authorized and functional for development (no submission deadline pressure). Public URL can be added later when:
- Canva submission timeline is clear
- Infrastructure is finalized (webhook.site or own server)
- Tanzim approves redirect URL strategy

### Next Steps (When Needed)
1. Decide on public redirect URL (webhook.site ID or server)
2. Update `redirect_uri` in Canva Developers console
3. Canva may invalidate current auth code — full re-auth required
4. Resubmit for Production status

---

## Blocker #2: Multiple OAuth Clients (MEDIUM)

### Problem
As of Jun 10, two Canva clients were created/attempted:
1. **TIMBR Client** (OC-AZ5TE93EPw0y) — Preferred, all scopes enabled, access token stored
2. **Untitled Client** (OC-AZ6uvUWgLDkX) — Also created, may be orphaned

### Why This Matters
- Different credentials → different access tokens
- Risk of storing/using wrong credentials
- Desktop CREDENTIALS_MASTER.md and vault.json may diverge

### Solution
- Designate TIMBR Client as canonical (primary in Tanzim_Frameworks)
- Delete or archive Untitled Client (confirm with Tanzim)
- Track all active clients in desktop CREDENTIALS_MASTER.md with status (active/archived/pending-submission)
- One entry per client:
  ```markdown
  ## CANVA — TIMBR
  - Client ID: OC-AZ5TE93EPw0y
  - Status: Authorized (Development, localhost redirect)
  - Scopes: design:content:write, folder:write, design:permission:write, app:write
  - Access Token: [REDACTED in file, stored in vault]
  - Redirect URI: http://127.0.0.1:8080/callback
  - Created: June 9, 2026
  - Notes: Awaiting public redirect URL for production submission
  ```

---

## Testing Access (All Integrations)

After any re-auth or scope change, test access immediately:

```python
import urllib.request, json

access_token = vault['canva']['access_token']

# Test 1: Fetch user profile
req = urllib.request.Request(
    'https://api.canva.com/rest/v1/users/me',
    headers={'Authorization': f'Bearer {access_token}'}
)
result = json.loads(urllib.request.urlopen(req).read())
print(f"✅ Canva Access: {result['user']['display_name']}")
```

Expected: Returns user object for `tan.biz@icloud.com`.

---

## Reference: Canva Submission Path (When Ready)

1. **Create/update integration in Canva Developers**
   - Change redirect URI to public URL
   - Verify all required scopes enabled
   - Request Production status

2. **Canva review (1–3 business days)**
   - Canva may ask for app preview/demo
   - May require terms of service acceptance
   - Status email sent to registered owner

3. **On approval**
   - Canva marks integration as "Production"
   - All API endpoints fully available (may lift rate limits)
   - Use Production access token (different token if required)

4. **In practice** (Jun 10)
   - This is deferred; no timeline set
   - Current localhost setup works for all API calls (Canva doesn't enforce Production status in API response)
   - Can test full design export, team creation, etc. without submission
