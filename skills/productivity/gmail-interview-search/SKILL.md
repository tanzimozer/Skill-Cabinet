---
name: gmail-interview-search
description: "Find confirmed interviews in Gmail — distinguishes booked slots from scheduling invitations. Multi-query pattern with .ics attachment check as primary signal."
version: 1.0.0
tags: [gmail, interview, job-search, google-api]
related_skills: [google-oauth-refresh]
---

# Gmail Interview Search

Reliably surface confirmed upcoming interviews from Gmail. The core challenge is distinguishing **booked** interviews from **invitations to schedule** — the latter are not actionable as upcoming events.

## Primary Signal: .ics Attachment

The most reliable indicator of a *confirmed, booked* interview is a `.ics` calendar attachment:

```python
results = service.users().messages().list(
    userId='me',
    q='filename:ics after:2026/05/01',
    maxResults=15
).execute()
```

An `.ics` file means the time is fixed. An email asking you to "pick a time using the calendar link" is NOT a confirmed interview.

## Secondary Signals (in order of reliability)

1. Subject contains "confirmation" + has date/time in body
2. Zoom/Teams/Meet link in body with a specific date + time
3. Recruiter email with "your interview is scheduled for..."

## Full Search Sequence

Run these queries in order. Stop when you find a confirmed booked slot with a future date:

```python
queries = [
    # 1. .ics attachments — booked slots
    'filename:ics after:YYYY/MM/DD',
    # 2. Explicit confirmation language
    'subject:(interview OR "interview details" OR "interview confirmation") after:YYYY/MM/DD',
    # 3. Broad recent + interview keyword
    'subject:(interview OR schedule OR invite OR confirm OR meeting) after:YYYY/MM/DD',
    # 4. Specific day reference
    'Wednesday interview',
    '"May 28" interview',
    # 5. Company-specific if you have leads
    'Foundation AI OR Ferguson OR CBRE',
    # 6. Sent mail — did Tanzim confirm something himself?
    'in:sent interview OR schedule after:YYYY/MM/DD',
]
```

## Parsing a Result

For each matching message, fetch full body (not just metadata) to extract:
- Date and time
- Company name / role
- Interviewer name
- Meeting link (Zoom/Teams/Meet) + password
- Format: phone / video / in-person

```python
def get_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            result = get_body(part)
            if result:
                return result
    # Try text/plain first
    if payload.get('mimeType') == 'text/plain':
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return ''
```

If text/plain returns empty, fall back to text/html and strip tags:
```python
import re
clean = re.sub('<[^>]+>', ' ', html_text)
clean = re.sub(r'\s+', ' ', clean).strip()
```

## Finding Today's Interviews (Daily Briefing Pattern)

When Tanzim asks "what interviews do I have today", use a broader multi-query approach — not just `.ics` files. Confirmed interviews often arrive as Zoom/calendar reminder emails, not `.ics` attachments.

```python
# Query 1: anything interview-related received today
today_unix = int(datetime.datetime(today.year, today.month, today.day, 0, 0, 0).timestamp())
q = f'(interview OR "phone screen" OR "hiring") after:{today_unix}'

# Query 2: recent scheduling confirmations (last 14 days) that reference today's date
q = '(interview scheduled OR "interview confirmation" OR "interview invitation" OR "we would like to interview" OR "next steps" OR "technical interview" OR "hiring manager") newer_than:14d'
```

Key: use Unix timestamp in `after:` for same-day filtering. Always search **14 days back** for scheduling confirmations — the confirmation email was likely sent days before the interview.

**Distinguish email types in results:**
- Reminder email ("REMINDER: Interview Scheduled on Fri, May 29") → confirmed, extract time from body
- "Event Confirmation" from booking tool (Rooster, Calendly, HireVue) → confirmed, extract time
- "We invite you to schedule" → NOT confirmed, skip
- "Thank you for applying" → ignore
- "Feedback on your application" / rejection → ignore, but note it

**Escalation when user says "there's another one":** Run a second broader pass — the first pass may have missed something. Use:
```python
queries = [
    f'(interview OR "phone screen" OR "video interview" OR "hiring manager") newer_than:30d',
    f'("4:00 PM" OR "4 PM" OR "16:00") newer_than:14d',
    f'(interview OR recruiter) newer_than:30d -from:myworkday.com -from:ashbyhq.com',
]
```
Deduplicate by message ID across all queries before fetching bodies.

## Single-Query Sweep (validated Jun 2026, first-try clean)

When you just need "the latest interviews I scheduled" — not today-only — one combined query catches the full picture without the multi-pass dance:

```python
q = ('interview (schedule OR scheduled OR invitation OR confirmed OR '
     '"calendar" OR "phone screen" OR "video call" OR zoom OR teams OR meet) '
     'newer_than:21d')
```

Fetch `format="full"` per hit, sort by parsed date, report soonest-first. `newer_than:21d` is the sweet spot — wide enough to catch confirmations sent ~2 weeks before the slot, narrow enough to drop stale traffic. This returned 12 clean hits (2 upcoming, rest recently-passed) with zero noise.

## Confirmed-but-Unaccepted State (the third bucket)

Beyond "booked" vs "invitation to schedule," there's a third state worth flagging explicitly: a recruiter sends a real **calendar invite** (fixed date/time) but Google marks it *"Invitation from an unknown sender"* and it is **not yet on Tanzim's calendar**. The slot is real; the acceptance is pending.

- Subject pattern: `Invitation from an unknown sender: ... @ [date/time]`
- This IS a scheduled interview — surface it — but flag that it's **unaccepted** and offer to accept it. Don't treat "not on calendar yet" as "not confirmed."

## Booking-Tool Subject Prefixes = Confirmed

Microsoft Bookings / similar tools send a `Confirmed: Interview` subject with a body block: `Service Name / When [date range] / Interview With [name]`. Treat the literal `Confirmed:` prefix as a hard confirmed signal — extract the When line directly.

## Pitfalls

- **"Invitation to schedule" ≠ confirmed interview.** Foundation AI's email was "please use the calendar link to select a time" — NOT a booked slot. Never surface this as an upcoming interview.
- **Subject-only search misses a lot.** Interview confirmations often come with generic subjects like "Virtual Interview Details" or "Your upcoming meeting". Always fetch body.
- **Calendar API may not be enabled** — even with valid OAuth, Google Calendar v3 calls throw 403 if the Calendar API isn't enabled in the GCP project. Don't rely on Calendar as fallback; Gmail `.ics` search is more reliable anyway.
- **Google Calendar API is v3** — `build('calendar', 'v3', ...)`. v4 does not exist.
- **Check sent mail** — Tanzim sometimes confirms interviews via email reply without receiving a new inbound confirmation. If inbound search is dry, check sent.
- **Multiple email accounts** — if a result set looks thin, ask whether another email account was used for the application.

## Output Format

When reporting a confirmed interview:

```
Company: [Name]
Role: [Title]
Date: [Day, Month DD, Time + timezone]
Interviewer: [Name, Title]
Format: [Zoom/Phone/In-person]
Link: [URL]
Password: [if applicable]
```

Keep it short. One block per confirmed interview. Don't pad with maybes.
