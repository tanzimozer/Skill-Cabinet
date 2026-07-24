---
name: api-integrations
description: "Managing, auditing, testing, and reconnecting third-party API and OAuth integrations for Tanzim's stack."
version: 1.0.0
tags: [API, integrations, Trello, Wix, Webflow, Canva, Substack, credentials, audit]
related_skills: [google-workspace]
---

# API Integrations

Covers auditing what's connected, testing live credentials, reconnecting expired tokens, and tracking integrations in the Software and API sheet.

## Tanzim's integration inventory

Tracked in Google Sheet: **Software and API**
`https://docs.google.com/spreadsheets/d/18NuICPfLqXhGtIDDejvSznEWHZ9eRcowQ6OKdfoeLl4/edit`

| Service | Auth type | Status (as of May 2026) | Credentials location |
|---------|-----------|------------------------|----------------------|
| Google Workspace | OAuth 2.0 | ✅ Live | `~/.hermes/google_token.json` |
| Anthropic / Claude | API key | ✅ Live | `.env` |
| WhatsApp Bridge | Session | ✅ Live | `~/.hermes/whatsapp/session/` |
| Hindsight | Internal | ✅ Live | N/A |
| Trello | API Key + Token | ✅ Live (tested May 26) | `~/.hermes/.trello_credentials` |
| Wix (TIMBR Site) | Account API key | ⚠️ Needs reconnect | IST token format — use account-level key from manage.wix.com |
| Webflow | Bearer token | ❓ Unknown | Not stored on VM |
| Canva | OAuth | ❓ Unknown | Not stored on VM |
| Substack | connect.sid cookie | ❓ Unknown | Expires periodically |
| OpenRouter | API key | ❌ Not set up | Need key from openrouter.ai |
| RapidAPI / JSearch | API key | ❓ Unknown | Not stored on VM |

## Testing a credential before storing it

Always test first, store after. Patterns:

### Trello
```python
import urllib.request, json
creds = json.load(open('/home/hermes/.hermes/.trello_credentials'))
key, token = creds['api_key'], creds['token']
url = f'https://api.trello.com/1/members/me?key={key}&token={token}'
r = urllib.request.urlopen(url, timeout=10)
print(json.loads(r.read()).get('fullName'))
```

### Wix
⚠️ **IST tokens (app-scoped) return 403 on account-level endpoints.** They look valid but aren't usable for general API access. Tanzim needs the **account API key** from:
`manage.wix.com → Account Settings → API Keys → Generate API Key`
This is distinct from the IST token generated per-app.

Test with:
```python
import urllib.request, json
key = "YOUR_ACCOUNT_API_KEY"
req = urllib.request.Request(
    "https://www.wixapis.com/site-list/v2/sites/query",
    data=json.dumps({"query": {}}).encode(),
    headers={"Authorization": key, "Content-Type": "application/json"},
    method="POST"
)
r = urllib.request.urlopen(req, timeout=10)
print(json.loads(r.read()))
```

## Reconnection sequence (when doing 1-by-1 audit)

1. Test existing stored credential first — don't ask for a new one until you confirm the old one is dead
2. If dead, give Tanzim the exact URL and steps to get the new key (specific dashboard page, not general "go to settings")
3. Test the new credential before confirming it's live
4. Update the Software and API sheet after confirmation
5. Move to the next integration

## WhatsApp cron job delivery 401 — debugging sequence

When cron jobs deliver to WhatsApp groups via `whatsapp:{group_id}@g.us` and return 401 errors:

**Step 1 — Check if bridge itself is healthy:**
```bash
curl -s http://localhost:3000/health
# expect: {"status":"connected","queueLength":0,"uptime":...}
```
If unhealthy → bridge issue. If healthy → group ID issue.

**Step 2 — Test the specific group ID with auth:**
```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chatId":"GROUP_ID@g.us","message":"test"}'
```

| Response | Meaning |
|---|---|
| `{"success":true,...}` | Group ID valid and reachable |
| `{"error":"item-not-found"}` | Group ID is dead — account left/removed or group deleted |
| `{"error":"Unauthorized"}` | Bridge token wrong or not passed |

**Step 3 — Find the working group ID:**
- `send_message(action="list")` returns all connected groups as numeric IDs
- Cross-reference with a known working job's `deliver` field
- Send a test message to candidate IDs with the auth header above

**Step 4 — Update the failing jobs:**
```python
schedule_task(action="update", job_id="...", deliver="whatsapp:CORRECT_ID@g.us")
```

**Note:** The bridge itself requires `Authorization: Bearer {WHATSAPP_BRIDGE_TOKEN}` on every request — plain `curl localhost:3000/send` without the header always 401s regardless of group validity. Don't mistake this for a group issue.

## Cron jobs referencing integrations

When an integration credential changes, check for active cron jobs that use it and update their prompts or stored config. Key jobs that use external APIs:
- `bee2a703c25b` — Blair Sunday Check-in (Google Sheets)
- `fa9e4d48a414` — Blair magazine answers check (Google Sheets)
- `f45d1682b7e9` — Sunday Weekly Planning (Trello, Google Sheets)
- `d9c63d29837f` — MAGPROD Daily Backup

## Pitfalls

- **IST tokens ≠ account API keys on Wix.** IST tokens are app-instance scoped and will 403 on account-level APIs even if the format looks valid.
- **Trello tokens set to "never expire" at generation time** — if it was set to 30-day expiry during initial setup it will die silently. Check `trello.com/app-key` to regenerate with no-expiry.
- **Voice transcription garbles codewords** — if Tanzim gives codeword by voice and it sounds close but wrong (e.g. "TETA" instead of "THETA"), flag it and ask for text confirmation before refusing.
