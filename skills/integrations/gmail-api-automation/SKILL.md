---
name: gmail-api-automation
description: "Searching, trashing, and managing Gmail messages via the Gmail REST API using Tanzim's stored Google OAuth token."
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [gmail, google, email, api, oauth]
    related_skills: [google-auth-refresh]
---

# Gmail API Automation

## Account
`tanzim.seattle@gmail.com` — personal/job search inbox. 671 messages as of Jun 2026.
Separate from `tanzim.ozer@gmail.com` (not connected) and `tanzimx@icloud.com` (iCloud, different connector).

## Auth — use manual token refresh (not google-auth library)
The stored token at `~/.hermes/google_token.json` can have scope mismatch issues with the google-auth library's refresh path. Use direct HTTP refresh instead — it's reliable:

```python
import json, requests, subprocess

result = subprocess.run(['cat', '/home/hermes/.hermes/google_token.json'], capture_output=True, text=True)
t = json.loads(result.stdout)

r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token',
})
access_token = r.json()['access_token']
headers = {'Authorization': f'Bearer {access_token}'}
```

**Verify connection:**
```python
g = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/profile', headers=headers)
print(g.json())  # should show emailAddress, messagesTotal, threadsTotal
```

## Search messages
```python
res = requests.get(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages',
    params={'q': 'subject:"thank you for applying"', 'maxResults': 500},
    headers=headers
).json()
msg_ids = [m['id'] for m in res.get('messages', [])]
```

Gmail search syntax: same as Gmail UI. Key operators:
- `subject:"..."` — subject match
- `from:...` — sender
- `label:...` — label/folder
- `is:unread`, `is:read`
- `before:YYYY/MM/DD`, `after:YYYY/MM/DD`
- Combine with space (AND) or `OR`

## Trash messages (soft delete — goes to Trash, recoverable 30 days)
```python
for msg_id in msg_ids:
    requests.post(
        f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/trash',
        headers=headers
    )
```

## Permanently delete (unrecoverable — confirm with Tanzim first)
```python
requests.delete(
    f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}',
    headers=headers
)
```

## Batch delete (faster — up to 1000 IDs per call)
```python
requests.post(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages/batchDelete',
    headers={**headers, 'Content-Type': 'application/json'},
    json={'ids': list_of_ids}
)
```

## Standard rejection/application email queries
Confirmed working for `tanzim.seattle@gmail.com` (Jun 2026, 32 emails found):
```python
queries = [
    'subject:"thank you for applying"',
    'subject:"thank you for your application"',
    'subject:"we regret"',
    'subject:"unfortunately" application',
    'subject:"not moving forward"',
    'subject:"other candidates"',
    'subject:"application received"',
    'subject:"we will not"',
    'subject:"position has been filled"',
    'subject:"decided to move forward with other"',
]
```
Deduplicate across queries with a `set()` before actioning.

## Noise triage workflow ("deploy Veronica" — identify & clear noise unread)
Tanzim's standing protocol when he asks to clear inbox noise. **100% accuracy is the priority — when in doubt, KEEP.** False-positive (binning a real lead) is far worse than a missed bit of noise. Sequence he steered (Jun 2026):

1. **Pull all unread, classify by signal** — not by guessing. Fetch `format=metadata` headers (`From`, `Subject`, `List-Unsubscribe`) plus `labelIds` and `snippet`. Bulk-marketing signals: `List-Unsubscribe` header present, `CATEGORY_PROMOTIONS`/`CATEGORY_SOCIAL` label, noise senders (`noreply|newsletter|notifications@|marketing@|hello@|team@|digest|mailer`).
2. **PROTECT-FIRST gate.** Anything matching job-pipeline terms is untouchable: `interview|recruit|hiring|application|applied|candidate|offer|next step|assessment|schedule|onboard|position|role|talent|opportunity` + named pipeline companies. Job-search is his live priority — protect aggressively.
3. **Three buckets:** high-confidence NOISE / PROTECTED / NEEDS-REVIEW (ambiguous). Report the counts, don't auto-act on ambiguous.
4. **Surface ambiguous and ask ONE question at a time** — he wants to steer classification interactively, not get a wall. Flag action-required items inside the ambiguous pile separately ("Additional Information Needed", "Follow up questions", "New Message from <recruiter>") — those are never noise.
5. **He keeps plain "thank you for applying" auto-acks** — he reads those himself. Do NOT bin auto-acks during noise triage (different from the rejection-sweep, where they go).
6. **QUALITY PASS before delete** — he says "qualify pass first then del". Re-fetch every final candidate, re-run the protect regex against `From+Subject+snippet`, print a per-item `NOISE-OK`/`HOLD-PROTECT` verdict. Only IDs that clear the gate get trashed.
7. **Trash (soft delete), confirm count**, report: trashed N/N, unread remaining, "zero job threads touched."

Full heuristics + regexes: `references/noise-triage-veronica.md`.

## Subject lines LIE — body-verify before any rejection/receipt delete (critical)
The #1 accuracy trap (Jun 2026). Identical subjects hide opposite meanings:
- **"Thank you for your interest in <X>"** → was 1 genuine rejection (PG&E: "do not meet the minimum qualifications") vs 3 neutral receipts (Stallion, WWT, Enhabit). Same words, opposite action.
- **"An update on your application from <X>"** → rejection. But **"Indeed Application: <role>"** → just an apply-receipt, NOT a rejection. Easy to over-match.

Rule: for the rejection/cleanup sweep, **fetch `format=full`, strip HTML, lowercase, and classify on the BODY**, never the subject. Run `REJECT`/`RECEIPT`/`ACTION`/`INTERVIEW` keyword sets against body text; default-PROTECT anything that matches none. Body-verified sweep + keyword sets: `references/noise-triage-veronica.md`.

## Hub-and-spoke sweep (Tanzim's phrase for the full body-verified pass)
When he says "deploy Veronica and hub-and-spoke" / wants the whole noise category gone precisely:
1. **Spokes** = cast ~20 wide `subject:`/`from:` queries into one dedup'd candidate pool (`in:inbox` scoped).
2. **Hub** = one body-level classifier over the pool → NOISE (receipt+rejection) vs PROTECT (action/interview/unsure, default-safe).
3. Print the full PROTECT and NOISE lists for his eyes, then trash NOISE. Jun 2026: 84 candidates → 48 noise trashed, 36 protected (held: Wells Fargo interview reminder, 2 Coldwell invites, text-interview invite, live recruiter messages).

## Pitfalls
- **google-auth library refresh fails with `invalid_scope`** even when the token file has the right scopes. Use the direct HTTP refresh above instead — it works reliably.
- **`batchDelete` returns HTTP 403** with the current token (missing the mail.google.com full scope) AND it permanently deletes (no Trash). Do NOT use it for cleanup — loop per-message `POST .../{id}/trash` instead (soft, recoverable). 48 trashed individually in ~14s is fine.
- **`maxResults` caps at 500 per call** — paginate with `pageToken` if inbox could have more than 500 matches. For small targeted deletions (rejection emails) this isn't needed.
- **`tanzim.ozer@gmail.com` is a different account** — the stored token connects to `tanzim.seattle@gmail.com`. Don't conflate them.
- Always use `trash` not `delete` unless Tanzim explicitly says "permanently delete" — trash is recoverable for 30 days.
