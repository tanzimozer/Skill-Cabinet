---
name: gmail-automation
description: "Automating Gmail via the Gmail REST API — search, batch delete/trash, label management. Uses Google OAuth token stored at ~/.hermes/google_token.json."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [gmail, google, email, automation, oauth, cleanup]
    related_skills: [google-auth-refresh]
---

# Gmail Automation

## Account
- Primary job account: `tanzim.seattle@gmail.com`
- Personal: `tanzim.ozer@gmail.com` (separate — do NOT mix)
- **Current active token location:** `~/.hermes/google_token.json` (full access, all 8 scopes, verified Jun 2026)
- **Fallback location:** `~/.hermes/google_oauth_full.json` (if primary unavailable)

## Permanent Credential Setup

**Tanzim's requirement (Jun 8, 2026):** Credentials must be stored everywhere, have **all 8 scopes upfront** (Gmail + Sheets + Calendar + Drive + Docs), and never require re-authentication. **Delivery: speed-first.** Strip all preamble and explanation; lead with the action. When OAuth is complete, move to next task immediately — no "should I now..." or option menus. Ultra-condensed numbered steps, one line each.

**See `references/oauth-full-setup-jun8-2026.md` for the complete step-by-step OAuth flow** (credentials download → auth link generation → code exchange → token storage → verification). This reference includes:
- How to request all 8 scopes upfront (avoids the scope-mismatch pitfall)
- Token file structure and merge logic
- Multi-location storage (filesystem, memory, env vars)
- Verification test and refresh pattern

**See `references/oauth-headless-exchange-jun8-2026.md` for the pure-urllib headless OAuth exchange pattern** — user clicks link, pastes code, agent handles token exchange on VM with zero external dependencies. No browser automation, no gcloud, zero terminal commands sent to user.

**Legacy reference:** `references/oauth-full-setup.md` (older, less detailed)

**Current status:** `~/.hermes/google_oauth_full.json` provisioned with all 8 scopes (Gmail modify/readonly/send/labels, Calendar, Drive, Documents, Sheets). Stored in long-term memory and hindsight.

## Execution Style (Tanzim Preference)

**For destructive actions (trash/delete):**
1. Always ask for confirmation first — state what you're about to delete (count + examples).
2. **Once Tanzim says "proceed" or "yes", execute immediately.** No restating the command, no option menus, no "should I also...". Move straight to the deletion code.
3. Report after completion only — summary of deleted count + any errors.
4. Do not volunteer next steps or ask "what's next" — Tanzim will direct.

**For non-destructive actions (search/scan):** No confirmation needed — report the results and wait for direction.

## Auth — always refresh manually first
The google-auth library's auto-refresh fails with `invalid_scope` if the token file was written with a different scope set. **Always refresh manually via requests before building the service:**

```python
import requests, json, subprocess

result = subprocess.run(['cat', '/home/hermes/.hermes/google_token.json'], capture_output=True, text=True)
t = json.loads(result.stdout)

r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token',
})
access_token = r.json()['access_token']
headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
```

Verify with profile call:
```python
r = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/profile', headers=headers)
print(r.json())  # should show emailAddress, messagesTotal
```

## Searching messages

Use Gmail search syntax — same as the web UI search box:

```python
def search_messages(query, max_results=500):
    all_ids = set()
    res = requests.get(
        'https://gmail.googleapis.com/gmail/v1/users/me/messages',
        params={'q': query, 'maxResults': max_results},
        headers=headers
    ).json()
    for m in res.get('messages', []):
        all_ids.add(m['id'])
    return all_ids
```

**Useful query patterns:**
| Intent | Query |
|--------|-------|
| Rejection emails | `subject:"we regret" OR subject:"not moving forward" OR subject:"other candidates"` |
| Application confirmations | `subject:"thank you for applying" OR subject:"thank you for your application" OR subject:"application received"` |
| All job-related noise | combine both above |
| Unread only | append `is:unread` |
| From specific sender | `from:noreply@greenhouse.io` |
| Older than 30 days | `older_than:30d` |

**Run multiple queries and union the IDs** — each query only catches one pattern. De-duplicate with a set.

## Trashing messages (soft delete — goes to Trash, recoverable 30 days)

```python
deleted = 0
for msg_id in all_ids:
    r = requests.post(
        f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/trash',
        headers=headers
    )
    if r.status_code == 200:
        deleted += 1
print(f"Trashed: {deleted}/{len(all_ids)}")
```

## Trashing messages (soft delete — goes to Trash, recoverable 30 days)

```python
requests.delete(
    f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}',
    headers=headers
)
```

⚠️ **Always use trash first. Only permanently delete on explicit instruction.**

## Batch delete (more efficient for large volumes)

```python
# Batch trash up to 1000 at a time
ids_list = list(all_ids)
for chunk in [ids_list[i:i+1000] for i in range(0, len(ids_list), 1000)]:
    requests.post(
        'https://gmail.googleapis.com/gmail/v1/users/me/messages/batchDelete',
        headers=headers,
        json={'ids': chunk}
    )
```

## Email Cleanup at Scale

**Recommended: Actionability-Filter Method (Jun 2026)** — See `references/actionability-filter-cleanup-jun2026.md` for the new single-scan pattern that filters 100–200+ emails by presence of action keywords. **98% accuracy, zero false positives on interviews/offers.** This replaces the four-pass strategy for large-scale cleanups.

**Legacy: Four-Pass Strategy** — See `references/email-triage-multipass-cleanup.md` for the original four-pass pattern that clears 150–200 junk emails in one session (still works for smaller batches):
1. **Pass 1:** Courtesy / ATS auto-thanks (95 emails)
2. **Pass 2:** Promotional & job board marketing (68 emails)  
3. **Pass 3:** Auto-notifications & security codes (16 emails)
4. **Pass 4:** Manual sweep for edge cases (15 emails)

This pattern achieves ~95% junk removal with zero false positives on active interviews/offers.

## "Bin the noise, keep live threads" pattern (verified Jun 27 2026)

When Tanzim asks to find what's binnable, **always split the result into two buckets and report them separately:**
1. **Pure dead noise — safe to bin:** ATS auto-acks, Indeed/job-board confirmations, marketing/promo, survey requests, instant-interview bot nags, rejections.
2. **Hold — touches a live or optional thread, his call:** selection-process reminders from a recruiter who's an active thread, "complete next steps" nags for assessments he may still want (Coldwell/Protingent/Criteria-type), calendar reminders.

Never bin bucket 2 without explicit say-so — a "reminder"/"next steps" subject can belong to a live recruiter. Report counts + a few examples per bucket, then wait for the word. He'll typically say "bin the ~N dead ones, leave the reminders."

Confirmed category queries (in:inbox scoped) that cleanly catch bucket 1:
- ATS auto-acks: `subject:"thank you for applying" OR subject:"thank you for your application" OR subject:"application received" OR subject:"we received your application"`
- Indeed confirms: `from:indeed.com (subject:"applied" OR subject:"application")`
- Marketing/promo: `from:dice.com OR from:apollo.io OR from:technologyadvice OR category:promotions`
- Surveys/nags: `subject:survey OR subject:reminder OR subject:"complete your"` ← **this one bleeds into bucket 2; review hits individually before binning.**

Pull `From`+`Subject` metadata for every hit before binning so the report shows the actual senders, not just a count.

### Don't be over-conservative — receipts ARE noise (correction, Jun 28 2026)
Two-bucket only — **never invent a third "unsure" bucket and leave it in the inbox.** In a session Tanzim asked to bin the binnable; I held back the auto-acks AND parked ~24 receipts in an "unsure" pile. He pushed back: *"did you read all the emails? There are some thank you/application receipt emails"* — i.e. those receipts are dead noise, bin them. Lesson:

- **Scan the WHOLE inbox, not just unread.** He'll call it out if you only read the unread slice.
- **These ARE bucket 1 (bin), not "hold":** `thank you for applying`, `application received/update/status/submitted`, `we received your application`, `Indeed Application: <role>` (submission receipts), `your application for <role>` (ATS receipt), `a job application has been created`, `welcome to <X> careers/talent community`, ATS auto-acks from myworkday/icims/greenhouse/ashby/eightfold/adp. A subject naming a role + "application" with a no-reply/ATS sender = receipt = bin.
- **Bucket 2 (hold) is genuinely narrow:** a real human name in `From`, an interview invite/confirmation, a calendar invite, an active recruiter's "next steps"/reminder, an offer/onboarding/background-check/assessment-to-complete. When in doubt the discriminator is *is there a person or a live action attached* — not the word "application" or "reminder" alone.
- **KEEP regex must be tight.** `application update`, `your application for X`, `update on your X application` are receipts — do NOT let them match KEEP. Match KEEP on: interview, offer, onboard, background check, next step(s), schedule, reference, assessment, interview invite, appointment booked, request a chat, opportunity, internship, and human-sender threads.

The default failure here is timidity, not recklessness — he asked to clean, so clean. Soft-trash (recoverable 30d) means erring toward binning receipts costs nothing.

## Confirmed working patterns (Jun 2026)

### Rejection / job application cleanup
Queries that caught emails in tanzim.seattle@gmail.com:
- `subject:"thank you for applying"` → 23 results
- `subject:"thank you for your application"` → 6 results
- `subject:"application received"` → 5 results
- `subject:"we regret"`, `subject:"unfortunately" application`, `subject:"not moving forward"` → 0 results (not present)

Total: 32 unique emails trashed in one run. Zero failures.

## Credential Recovery (Tanzim's Environment)

**CRITICAL — check the vault before claiming you can't act (verified Jun 26 2026):** The most embarrassing recurring failure is asserting an \"OAuth wall\" / \"no Gmail access\" and offering to make Tanzim do the work by hand — while a fully-valid token sits in `~/.hermes/google_token.json` and the active client in `~/.hermes/GOOGLE_OAUTH_ACTIVE.json`. Tanzim has had to correct this directly: *\"You do, check vault.\"* **Rule: before EVER telling Tanzim you can't touch Gmail, run the auth check** — confirm `google_token.json` + `GOOGLE_OAUTH_ACTIVE.json` exist, then do a refresh + profile call to verify. Assume access exists and prove otherwise; never pre-emptively declare a wall.

**CRITICAL:** Tanzim has explicitly stated frustration with repeated credential failures: *"I'm tired of this every next day you keep forgetting google connections."* **DO NOT ask for re-auth without exhausting all local recovery paths first.** Assume the credentials exist somewhere in the environment and your job is to find them, not assume they're lost.

**`deleted_client` error — refresh token valid, client_id is dead (verified working fix Jun 17 2026):**
The single most common failure in Tanzim's environment. Token refresh returns `{"error": "deleted_client", "error_description": "The OAuth client was deleted."}` even though `google_token.json` looks healthy. The refresh_token is FINE — the `client_id`/`client_secret` stapled to it point to a Google Cloud OAuth client that was deleted.
- **The working client lives in `~/.hermes/GOOGLE_OAUTH_ACTIVE.json`** (client_id `990922176945-...`, project `friday-mark-2-499708`). That file is marked "ACTIVE AND WORKING. DO NOT REPLACE."
- **Fix:** load `GOOGLE_OAUTH_ACTIVE.json`, swap its `client_id` + `client_secret` into the existing token (keep the existing `refresh_token`), rewrite `google_token.json`, retry refresh. Works immediately.
- **Note:** the refresh_token in `~/.hermes/google_token.json` pairs with the ACTIVE client; the one in `~/.hermes/friday_backup/google_token.json` gives `invalid_grant` against it — use the primary, not the backup.

**Current credential locations (verified Jun 2026):**
- **ACTIVE OAuth client:** `~/.hermes/GOOGLE_OAUTH_ACTIVE.json` — the source of truth for client_id/secret. Try this first when refresh fails.
- **Primary token:** `~/.hermes/google_token.json` (access_token + refresh_token, sometimes missing or carrying a stale/dead client_id/secret)
- **FRIDAY OAuth clients:** Multiple versions exist in document cache (`/home/hermes/.hermes/document_cache/`) as `client_secret_*.json` files
  - `client_secret_2_990922176945-n9132okninl4isc7l7kd3n9345epaiqg...json` (friday-mark-2-499708) — verified working Jun 2026
  - Older versions in `/home/hermes/friday_backup/google_client_secret.json` and `/home/hermes/hermes-friday-client-secret.json`
- **Credentials master:** `~/Desktop/CREDENTIALS_MASTER.md` (tracks active credentials, last updated Jun 9, 2026)

**Multi-source recovery pattern (DO THIS FIRST):**
See `references/credential-recovery-multi-source-jun2026.md` for the complete workflow. Short version:
1. If token refresh fails with `invalid_client` / `unauthorized_client`:
2. Check document cache for the newest `client_secret_*.json` file (by modification time)
3. Extract client_id + client_secret from that file
4. Merge with existing refresh_token and retry refresh
5. Only ask for re-auth if all fallback sources are exhausted

**Token merge pattern (when client credentials are stale but refresh token is valid):**
1. Load current `~/.hermes/google_token.json` (extract access_token + refresh_token)
2. Load newest `client_secret_*.json` from document cache
3. Merge: use old tokens, new client credentials
4. Rewrite to `~/.hermes/google_token.json` (see \\\\\\\"Auth\\\\\\\" section for correct JSON structure)
5. Attempt refresh via `requests.post` to `https://oauth2.googleapis.com/token`

**If all recovery attempts fail:**
- Check `~/Desktop/CREDENTIALS_MASTER.md` — is the FRIDAY client listed as active?
- Did Tanzim recently send a new OAuth client secret file? (check hindsight or memory)
- Only THEN ask Tanzim for re-auth or new credentials

## Pitfalls\n\n### OAuth token structure mismatch — most common failure in fresh sessions\n**Problem:** Token file written in old format (e.g. `token`, `expiry` fields from google-auth library) or missing `client_id`/`client_secret`. Refresh fails with 403 or KeyError.\n\n**Fix (always run this first):**\n1. Load the token file from disk (it may have any format)\n2. Extract `client_id`, `client_secret`, `refresh_token` (required; may come from oauth_client.json if separate)\n3. Refresh manually via `requests.post` to get a fresh `access_token`\n4. **Rewrite the token file in correct format** (see \"Auth\" section above for structure)\n5. Test with profile call before proceeding\n\n**Correct token structure (always):**\n```json\n{\n  \"access_token\": \"ya29.a0AT...\",\n  \"expires_in\": 3600,\n  \"refresh_token\": \"1//0g...\",\n  \"client_id\": \"...-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com\",\n  \"client_secret\": \"GOCSPX-...\",\n  \"token_uri\": \"https://oauth2.googleapis.com/token\",\n  \"type\": \"authorized_user\",\n  \"scopes\": [\"https://www.googleapis.com/auth/gmail.modify\"]\n}\n```\n\n**Why this happens:** google-auth library writes tokens with different field names depending on the flow. If credentials were provisioned by hand, in a different system, or loaded from an oauth_client.json without merging, the fields can be split across files. Always check and merge before using.\n\n### Invalid scopes during OAuth authorization (Error 400: invalid_scope)
**Problem:** User clicks authorization link, gets "Some requested scopes were invalid" error. One or more scopes in the request were not configured on the OAuth Consent Screen in Google Cloud.

**Fix:**
1. Go to Google Cloud Console: https://console.cloud.google.com/apis/consent
2. Select the project (e.g., `job-scraping-494906`)
3. Click **Edit App** on the OAuth Consent Screen
4. Under **Scopes**, verify ALL of these are added with exact URLs:
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.labels`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/documents` (NOT `docs` — this trips up the typo)
   - `https://www.googleapis.com/auth/spreadsheets`
5. Under **Test users**, add the email being authorized (e.g., `tanzimozer@gmail.com`)
6. Save all changes, then retry the authorization link

**Why it happens:** New OAuth apps are in "Testing" mode and require both (a) scopes to be explicitly configured on the consent screen, and (b) the user to be added as a test user. Missing either causes invalid_scope. See `references/oauth-full-setup.md` for the complete step-by-step setup workflow.

**Common mistake:** Using `docs` instead of `documents` as the scope — Google rejects it silently with invalid_scope.

### google-auth library `invalid_scope` on refresh
The library tries to validate the scope string and fails if the token was issued under a different scope set. **Bypass entirely — use `requests.post` to refresh the token directly.** It always works.

### Wrong account
`tanzim.seattle@gmail.com` = job/professional. `tanzim.ozer@gmail.com` = personal. Never mix. The token currently points to `tanzim.seattle`. If Tanzim asks to clean "Gmail" without specifying, confirm which account first.

### Search returns 0 but emails exist
Gmail search is exact on subject strings — check capitalisation and spacing. Run multiple subject variants rather than one catch-all query.

## Identifying & Extracting Interview Details (Tanzim Preference)

When asked to find upcoming interviews, especially for a specific day:
1.  **Prioritise Calendar API (`calendar.events().list`) as the source of truth.** It's less noisy and provides structured data.
2.  **Cross-reference with Gmail API (`gmail.users().messages().list`) for details.** Search for keywords like `interview`, `schedule`, `meeting`, `video call`, `zoom`, `google meet`, `teams`, `onsite`, `phone screen`, or specific times (`1 PM`, `13:00`) within a relevant time window (e.g., `newer_than:21d`).
3.  **Extract specific details from email bodies:**
    - Company name
    - Company link
    - Position name
    - Interviewer Name
    - Interview Room Link (Microsoft Bookings, Zoom, Google Meet, Teams, or specify "Phone call" if no link)
4.  **Always verify the date and time against the calendar.** If an email suggests a date/time not on the calendar, check the broader calendar range (e.g., next 7 days) to confirm.
5.  **Formatting preference (Hard default):** Return findings in the following structure:
    ```
    Interview 1 - Company name
    Company link -
    Position name -
    Interviewer Name -
    Job Hammer - Tab / Row (locate via `sheets.spreadsheets().values().batchGet`)
    Interview Room - Link
    Time - [HH:MM AM/PM PDT, Day DD Month YYYY]

    Interview 2 - Company name
    Company link -
    Position name -
    Interviewer Name -
    Job Hammer - Tab / Row
    Interview Room - Link
    Time - [HH:MM AM/PM PDT, Day DD Month YYYY]
    ```
    - Ensure time includes timezone and full date.
    - If a Job Hammer entry is not found, state "Not found".
### Authorization with insufficient scopes (delete fails with 403 after auth succeeds)
**Problem:** Authorized with `gmail.readonly` only, then later try to delete/trash/label messages. API returns 403 `Insufficient Permission: Request had insufficient authentication scopes` even though the bearer token is valid and expires far in the future.

**Root cause:** Each authorization pass grants only the scopes requested in that session's auth link. If you authorized with `gmail.readonly` (e.g., for scanning), you cannot later delete without re-authorizing with `gmail.modify`. The token itself is stuck with read-only scopes; a fresh token is the only path forward.

**Fix:**
1. **Identify the scope mismatch:** Check the error message — it will name the missing scope (usually `gmail.modify`)
2. **Regenerate the OAuth authorization link** with the required scopes (see \\\"Authorization Link Generation\\\" below)
3. **Force re-authorization:** Use `prompt=consent` in the link to force the user to re-approve (even if they've already granted other scopes to your app)
4. **Complete the new auth flow:** Get new code → exchange for new access_token (and refresh_token if offline)
5. **Update the token file:** Write the new token to `~/.hermes/google_oauth_full.json`
6. **Retry the operation:** The new token will have the broader scopes

**Authorization Link Generation (correct form):**
```python
import urllib.parse

client_id = \"YOUR_CLIENT_ID\"  # from credentials file
redirect_uri = \"http://localhost\"

# List all scopes you'll ever need (not just what you need today)
scopes = [
    \"https://www.googleapis.com/auth/gmail.modify\",  # includes delete, trash, label
    \"https://www.googleapis.com/auth/gmail.readonly\",
    \"https://www.googleapis.com/auth/gmail.send\",
    \"https://www.googleapis.com/auth/gmail.labels\",
    \"https://www.googleapis.com/auth/calendar\",
    \"https://www.googleapis.com/auth/drive\",
    \"https://www.googleapis.com/auth/documents\",
    \"https://www.googleapis.com/auth/spreadsheets\",
]

auth_link = f\"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={urllib.parse.quote(' '.join(scopes))}&access_type=offline&prompt=consent\"
print(auth_link)
```

**Key insight:** Always request `gmail.modify` at minimum if you'll be doing anything beyond read-only. Tanzim's permanent setup should request all 8 scopes upfront to avoid re-auth cycles.

## Required scopes
- `gmail.modify` — for trash/label operations
- `gmail.readonly` — for search/list
- Both should be in `~/.hermes/google_token.json` already

## References

- **Multi-source credential recovery (Jun 2026):** See `references/credential-recovery-multi-source-jun2026.md` for the workflow when refresh fails with `invalid_client` / `unauthorized_client`. Covers document cache lookup, token merge, and fallback patterns. **Use this BEFORE asking for re-auth.**
- **Credential recovery when token file is incomplete (Jun 2026):** See `references/credential-recovery-oauth-Jun2026.md` for the merge workflow when `~/.hermes/google_token.json` is missing `client_id`/`client_secret`. Common failure mode in Tanzim's environment.
- **Gmail + Sheets combined workflow (Jun 8, 2026):** See `references/gmail-sheets-combined-workflow-jun8-2026.md` for the full pattern when you need to clean Gmail AND pull data from Google Sheets in the same session. Includes auth with all 8 scopes, subagent deployment for exhaustive sheet scanning, and headless token exchange pattern.
- **Permanent credential setup (Jun 8, 2026):** See `references/oauth-full-setup-jun8-2026.md` for the complete step-by-step OAuth flow (credentials download → auth link generation → code exchange → token storage → verification).
