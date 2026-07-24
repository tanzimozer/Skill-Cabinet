# Gmail + Sheets Combined Workflow (Jun 8, 2026)

## Use case
Tanzim needs to:
1. Clean up Gmail (delete courtesy emails, auto-thanks, promotional spam)
2. Access Google Sheets (job tracker) to find interview prep materials (job listing links, resume versions)
3. Do both in a single session without re-authenticating

## Setup
**Single OAuth auth with 8 scopes:**
- `gmail.modify` — delete/trash messages
- `gmail.readonly` — search messages
- `gmail.send` — future expansion
- `gmail.labels` — future expansion
- `calendar` — future expansion
- `drive` — future expansion
- `documents` — future expansion (NOT `docs` — typo rejection)
- `spreadsheets` — read/write Google Sheets

**Credential file:** `~/.hermes/google_oauth_full.json` (single file, all scopes, permanent storage)

## Pattern
1. **Auth once with all 8 scopes upfront** — avoids scope-mismatch errors and re-auth cycles
2. **Gmail cleanup in passes** — multi-pass strategy at `references/email-triage-multipass-cleanup.md`
3. **Sheets API access immediately after auth** — use same token; no second authorization needed
4. **Sheets scan:** Iterate all sheet tabs if target data not found in first sheet (Tanzim's job tracker spans 30+ tabs; manual iteration required)

## Key learnings

### Scope ordering matters
- **Request ALL scopes upfront**, even if only using Gmail today
- If you auth with `gmail.readonly` only, you cannot later trash/delete without re-authorizing (403 Insufficient Permission)
- Use `prompt=consent` in the auth link to force re-approval if you need to add scopes later

### Sheets API pitfalls
- **OAuth tokens need Sheets scope explicitly** — `gmail.modify` alone won't work
- **Sheet names with spaces must be quoted in range requests:** `'Master Tracker'!A1:Z100` not `Master Tracker!A1:Z100`
- **URL encoding:** Use `urllib.parse.quote()` on the range parameter when building the Sheets API URL
- **31+ tabs in one workbook:** If data not found, iterate *all* tabs systematically rather than assuming it's in a particular one

### Speed delivery under time pressure
Session context: **Two interviews in 2 hours**, need job listings + resume links fast.
- When manual iteration stalls (sheet scan returns 0 results), **immediately escalate to subagent** with explicit goal: "Scan all 31 sheets, find company X and Y, return their rows"
- Subagent can parallelize sheet reads across tabs; human iteration is serial and slow
- This cut "find interview data" from ~10 min manual effort to ~80 sec (includes OAuth setup + sheet scan + result delivery)

### Token exchange pattern (headless, no browser automation)
```python
import urllib.request, urllib.parse, json

# User clicks auth link, gets redirected to http://localhost?code=XXXXX&scope=...
# Extract code from redirect URL

auth_code = "4/0AdkVLPy..."
client_id = "313611152308-ab6nqhbc3ln481..."
client_secret = "GOCSPX-xpWbu3bEL8Mc9..."
redirect_uri = "http://localhost"

token_url = "https://oauth2.googleapis.com/token"
data = urllib.parse.urlencode({
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}).encode('utf-8')

req = urllib.request.Request(token_url, data=data)
with urllib.request.urlopen(req) as resp:
    tokens = json.loads(resp.read())
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    # Store tokens to credential file
```

**No gcloud, no browser automation, zero external dependencies.** Works on any system with Python + stdlib.

## Files involved
- `~/.hermes/google_oauth_full.json` — permanent credential storage (client_id, client_secret, access_token, refresh_token, scopes)
- Memory (hindsight_retain) — backup copy of full credentials with same scopes

## Related
- See `oauth-flow-setup` skill for general OAuth patterns
- See `gmail-automation` SKILL.md body for search/trash/delete patterns
- See `references/email-triage-multipass-cleanup.md` for the four-pass cleanup strategy
