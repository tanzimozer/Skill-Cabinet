# Morning Brief — Gmail Scan Patterns

## Auth — use google_token.json exclusively (confirmed July 2026)

`GOOGLE_OAUTH_ACTIVE.json` has a stale/mismatched client pair and returns `{"error": "unauthorized_client"}` on token refresh. **Always read `client_id`, `client_secret`, and `token_uri` from `google_token.json`** — it is fully self-contained.

```python
with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)
resp = requests.post(t['token_uri'], data={
    'client_id': t['client_id'],
    'client_secret': t['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token'
})
access_token = resp.json()['access_token']
```

## format=metadata vs format=full (clarified July 2026)

Both work via raw `requests`. `format=metadata` with `metadataHeaders=["Subject","From","Date"]` returns headers correctly — the earlier claim that it returns empty fields was wrong.

- Use `format=metadata` when you only need headers (faster, lighter payload).
- Use `format=full` when you also need the snippet or body.

```python
# metadata only — Subject, From, Date
detail = requests.get(
    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
    headers=auth_headers,
    params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]}
).json()
hdrs = detail.get("payload", {}).get("headers", [])
subject = next((h["value"] for h in hdrs if h["name"] == "Subject"), "")

# full — when you also need snippet/body
full = requests.get(
    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
    headers=auth_headers,
    params={"format": "full"}
).json()
snippet = full.get("snippet", "")
```

## Inbox scan — signal vs. noise for Tanzim's job search

**Signal (surfaces in brief):**
- Real interview invites — human sender, "interview", "schedule", "availability", "zoom/teams link"
- Scheduling requests or calendar invites
- Offer/onboarding/background check triggers
- Recruiter replies with content (not ATS auto-ack)
- *Incomplete application alerts with deadlines* — governmentjobs.com, AppliTrack, etc. These are **action items**, not noise; flag them separately from rejections

**Noise (skip in brief, don't report):**
- "Thank you for applying" ATS auto-acknowledgements (Workday, Greenhouse, Ashby, etc.)
- Rejections from companies Tanzim hasn't flagged as priority — still worth a one-line summary but not individual mention unless it's a notable company
- Monster/Indeed/Glassdoor job alerts and digest emails
- Job board promotional emails

**Incomplete application pattern (July 2026 learning):**
governmentjobs.com sends "Incomplete Job Application Alert" emails with a deadline.
AppliTrack sends expiry warnings (~25-day idle threshold).
These are *time-sensitive action items* and must be called out explicitly in the brief, not lumped with rejections.

## Batch metadata fetch efficiency

For 15-20 messages, fetch sequentially in a loop with `format=full`. For 50+ messages, consider fetching in parallel with `concurrent.futures.ThreadPoolExecutor` to stay within cron time budgets.
