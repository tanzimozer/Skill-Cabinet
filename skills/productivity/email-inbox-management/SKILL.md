---
name: email-inbox-management
description: Email triage, cleanup, and action detection across Gmail and iCloud
trigger: email cleanup, inbox management, delete noise, find actionable emails, email triage
---

# Email Inbox Management

Patterns for managing Tanzim's email across Gmail and iCloud.

## CRITICAL USER PREFERENCES

1. **NEVER mix Gmail and iCloud in the same report.** When Tanzim asks about email, clarify which one OR keep results strictly separated. iCloud = personal. Gmail (tanzim.ozer@gmail.com) = also personal. A separate Timbr work Gmail coming later.

2. **Priority order = oldest first.** When listing actionable emails, the older the email, the higher the priority. Sort ascending by date.

3. **Delete noise proactively when asked.** Don't hedge — when he says "delete them," execute immediately.

4. **Career context (June 2026):** Tanzim is currently unemployed — declined JPMC offer (informed Maureen June 2). Job search is active via FLUXJOB/TerraJob automation. Jobot recruiter (Jeni) + COWI (Mehul Jain) are top-priority actionable threads in Gmail.

5. **Gmail accounts:** `tanzim.seattle@gmail.com` is primary for job applications and the morning brief. `tanzim.ozer@gmail.com` is also used for job search. Keep them separate — don't conflate results.

6. **Rippling ATS (`mail@ats.rippling.com`):** This is an ATS relay used by companies like TrueCar. It sends both auto-acks and rejection decisions. Always check the snippet — if it contains "move forward with other candidates" or similar rejection language, it's a real signal (include as FYI). If it's just an acknowledgement, skip.

5. **Key correspondent: Maureen Searle** (alex4sea1@gmail.com) — 94+ email threads on iCloud. Topics: fitness, AI in healthcare, GLP-1, longevity, Timbr business model. Always check Maureen Searle folder + INBOX when scanning iCloud. She writes frequently — flag unanswered threads. Last active threads: "Health Obsession" (Jun 1), "Exciting Times & The Dark Side" (May 21-28, about JPMC offer Tanzim ultimately declined).

## Credentials

- **Gmail**: OAuth via `~/.hermes/google_token.json` (use google-oauth-refresh skill)
- **iCloud**: IMAP via `~/.hermes/icloud_creds.json` (imap.mail.me.com:993)

See [references/icloud-mail-setup.md](references/icloud-mail-setup.md) for iCloud connection details.
See [references/icloud-mail-patterns.md](references/icloud-mail-patterns.md) for full folder map, Maureen Searle context, scanning strategy, and timeout workarounds.

## Noise Detection Patterns

### Subject patterns (delete on sight)
```
"thank you for applying"
"application received"
"we received your application"
"Thank You For Applying"
"application update"
"your application has been received"
```

### From patterns (noise)
```
noreply, no-reply, donotreply
@myworkday.com
@greenhouse-mail.io
notifications@, alert@
indeedapply@indeed.com  (application confirmation, not recruiter contact)
@applytojob.com
@talent.icims.com (auto-ack only)
@adp.com (ADP HR system auto-acks)
@hire.lever.co (Lever ATS auto-acks)
@candidates.workablemail.com (Workable ATS auto-acks)
opportunities@careeralerts.usbank.com (U.S. Bank feedback/marketing blasts — noise)
opportunities@careeralerts.tranetechnologies.com (Trane recruiter blasts — noise)
monster@notifications.monster.com (Monster job alerts — noise)
news@mg.monster.com (Monster marketing — noise)
no-reply@governmentjobs.com subject "Incomplete Job Application Alert" (action item — NOT noise, has a deadline)
```

### ATS message relay — @ashbyhq.com is NOT always noise
`no-reply@ashbyhq.com` sends both noise and real signals. Always check subject + snippet:
- "Reminder: Your Upcoming Interview" = real action item (interview is happening, confirm date/time)
- "Your application" / rejection language = informational, not noise
- Generic acknowledgement = noise
Never batch-discard ashbyhq.com on sender alone.

### BrightHire (hello@brighthire.ai) — real signal, not noise
BrightHire is an interview recording platform used by employers (e.g. Commvault). When they send "You have an interview with [Company]", that is a **real interview confirmation** — the company arranged the BrightHire link. Do not discard as marketing.

### noreply@fortive.com / Workday-relayed rejections
Fortive sends rejections via `noreply@fortive.com` with subject "Tanzim, following up from Fortive". This looks like a recruiter follow-up but is a rejection. Read the snippet — "won't be moving forward" = rejection, not action item.

### Monster / job board inbox notifications — NOT noise
`no-reply@messages.monster.com` with subject "You have new messages in your Monster inbox" means an actual recruiter has messaged. This is NOT an auto-ack — flag it as actionable. Same logic for LinkedIn InMail notifications, Indeed message alerts.

### "Complete your profile" emails — action items, not noise
Emails from ATS systems asking to complete an applicant profile (e.g. UPMC Talent Acquisition "Complete your UPMC Applicant Profile") are action items — without completing the profile, future applications at that employer are blocked. Flag these prominently.

### Marketing/spam
```
newsletter, promo, sale
@themomproject.com
@globalsuccesssolution.co (Hellen Lebone spam)
@nl.technologyadvice.com
@rapidapi.com
```

## Action Detection Keywords

Emails likely needing response contain:
```
schedule, call, interview, available
respond, reply, let me know, get back
follow up, next steps, when can
phone screen, meeting, connect, chat
action required, action needed, your response, waiting
```

## Workflow: Clean Job Application Noise

```python
# Query patterns for batch deletion
noise_queries = [
    'subject:("thank you for applying")',
    'subject:("application received")',
    'from:myworkday.com',
    'from:greenhouse-mail.io',
    # ... etc
]

# For each query:
# 1. Search: GET /gmail/v1/users/me/messages?q=...
# 2. Trash each: POST /gmail/v1/users/me/messages/{id}/trash
```

## Workflow: Find Actionable Emails

1. Get all unread: `is:unread in:inbox`
2. For each, check headers + snippet
3. Filter out automated (noreply patterns)
4. Detect action keywords in subject/snippet
5. Sort by timestamp (oldest first = highest priority)
6. Present as prioritized list

## Morning Brief — Gmail Triage (Cron Context)

When scanning Gmail for a morning brief (not a cleanup task), the goal is signal extraction, not deletion. Different workflow:

1. Fetch unread inbox (`in:inbox is:unread`, maxResults=20, metadata only)
2. For each message, pull Subject + From + snippet
3. Classify into: **Action required** / **Informational** / **Noise** (skip noise entirely)
4. Action required = any human-sent reschedule, interview reminder, recruiter reply, scheduling request, incomplete application with a deadline
5. Report one line per item — no tables, no headers within the section, no emoji
6. If nothing real: "Nothing actionable overnight."

**Noise to skip entirely in brief context (don't even mention):**
- Auto-acks ("thank you for applying", "application received")
- Job board suggestion emails (Indeed, Monster, LinkedIn alerts)
- Recruiter mass blasts with no personalisation
- Feedback request emails (U.S. Bank, employer surveys)
- API/developer notifications (RapidAPI, JSearch API)
- `news@mg.monster.com` — Monster marketing (multiple per day, always noise)
- `noreply@indeed.com` with generic rejection = noise (mention only if notable company)
- Career alert blasts (Trane Technologies `opportunities@careeralerts.tra...`, Fidelity career webinar = optional, skippable)
- Motivational spam (`@globalsuccesssolution.co`)

**Ashby interview reminders are real — don't skip.** Subject "Reminder: Your Upcoming Interview with [Company]" via no-reply@ashbyhq.com = confirm date/time action.

**BrightHire `hello@brighthire.ai` = real signal.** "You have an interview with [Company]" = confirmed interview, link incoming. Top priority.

When presenting email lists to Tanzim:

**🗑️ USELESS (can delete):**
| # | Subject | From |
|---|---------|------|

**📬 ACTIONABLE:**
| # | Subject | From | Action Needed |
|---|---------|------|---------------|

**Always ask before deleting** — present the list first, wait for "delete them" confirmation.

## iCloud IMAP Notes

```python
import imaplib

mail = imaplib.IMAP4_SSL('imap.mail.me.com', 993)
mail.login(email, app_password)
mail.select('INBOX')

# Search unread
status, messages = mail.search(None, 'UNSEEN')

# Fetch headers only (faster)
mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
```

## ⚠️ iCloud Scan Pitfall: Full-Folder Scan Times Out

Scanning ALL folders sequentially (ALL messages) times out at 300s.

**Correct approach — targeted scan only:**
1. Scan `INBOX` + named folders (idctan, TAN-BIZ, Maureen Searle) for `UNSEEN` only
2. For body reads, fetch individual messages with `BODY.PEEK[]` — never bulk-fetch all
3. For date-bounded queries use IMAP `SINCE` flag: `mail.search(None, 'FROM', '"Name"', 'SINCE', '1-May-2026')`
4. Per-folder limit: max 50 msg IDs at a time

## iCloud Folder Structure (Tanzim)

| Folder | Purpose |
|--------|---------|
| INBOX | Primary personal inbox |
| idctan | Shopping, newsletters, marketing (mostly noise) |
| Maureen Searle | Archived threads from Maureen Searle (alex4sea1@gmail.com) |
| TAN-BIZ | Timbr/business related |
| USCIS | Immigration documents |
| Documents | Personal documents |
| Appointments | Calendar/appointment confirmations |
| Robinhood | Brokerage notifications |
| Junk | Spam (skip unless asked) |

## Maureen Searle — Important Context

Maureen Searle (alex4sea1@gmail.com) is Tanzim's long-term mentor/advisor. 94+ threads across INBOX + Maureen Searle folder. Topics: fitness, AI in healthcare, GLP-1/longevity, Timbr business model, geopolitics. Always check **both** folders when scanning for her emails. She writes frequently and Tanzim often owes her a reply — flag it.

## Rejection vs Confirmation

Watch for these rejection patterns (FYI, no action needed):
- "unfortunately"
- "not moving forward"
- "other candidates"
- "position has been filled"
- "decided to pursue"

These are informational — categorize separately from noise.
