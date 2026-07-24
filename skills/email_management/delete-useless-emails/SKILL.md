---
name: delete-useless-emails
description: Identify and delete low-value emails from Gmail inbox — application confirmations, auto-reply thank yous, Indeed/job platform notifications, and similar transactional messages that clutter the inbox
tags:
  - gmail
  - email-management
  - inbox-cleanup
  - automation
---

## Purpose
Clean up Gmail inbox by automatically identifying and moving to trash emails that are confirmational/transactional in nature and provide no actionable value — such as "Indeed Application: [Job Title]" confirmations, auto-reply "Thank You for Applying" messages from job platforms, and similar noise.

## Email Types to Delete

### High-Priority (Always Delete)
- **Indeed Application confirmations** — "Indeed Application: [Job Title]" from indeedapply@indeed.com
- **Job platform auto-thanks** — "Thanks for applying to [Company]" from Workable, Greenhouse, CPG Beyond, etc.
- **Application receipt confirmations** — "Application Received", "Profile Submitted", "Profile submitted to [Company]" from HR systems and ATS platforms (HireBridge, ADP, etc.)
- **Auto-reply thank yous** — Confirmation that application was received (not personalized) — e.g., "Thanks for Applying to [Company]!" from Human Resources Departments
- **Generic hiring acknowledgments** — "Thank you for submitting your resume", "We have received your application" automated responses from company HR systems
- **ADP HR system notifications** — "Application Received — [Job Title]" from ADP services (LeadingReach.hr@adp.com, etc.) with yellow disclaimer banner
- **Workday system confirmations** — "[Company] - Application" from Workday (smithnephew@myworkday.com, etc.) with "Thank you for considering us" boilerplate
- **Applicant tracking system confirmations** — Generic "Thank you for your interest" responses from recruiting platforms (Applicant-track systems, etc.)

### Secondary (Delete on Request)
- **Job platform alerts** — "New jobs matching your profile" from Indeed, LinkedIn, etc.
- **Generic recruiter follow-ups** — Template-based "let's schedule a call" messages from platforms
- **Security alerts from Google** — "Security alert — You allowed [App] access" confirmations

## Important: DO NOT DELETE

- **Any email requesting action from the user:** scheduling calls/interviews, filling forms, confirming attendance, clicking links, booking appointments, providing information. Even if it looks like a courtesy/template, if it mentions scheduling or asks for user input — PRESERVE IT.
- **Personalized recruiter outreach:** even if template-like, if from a specific recruiter (not auto-system)
- **Interviews scheduled or pending:** any email with interview confirmation, date/time, Zoom/Teams link, or scheduling link
- **Emails with attachments** that might be JDs, offer documents, or background materials
- **Starred emails** — always preserve user-flagged messages

## Critical Safety Check Before Deletion

Before deleting any email, scan the body for these action-request keywords:
- schedule, book, confirm, RSVP, register, sign up, click, join
- fill out, submit, reply with, provide, send, attend
- "please", "kindly", "next steps", "action required"

If ANY of these appear in context of the user performing an action → DO NOT DELETE.

**`search_query`** (required, string)
- Gmail search query to identify emails to delete
- Examples:
  - `from:indeedapply@indeed.com "Indeed Application"`
  - `is:unread subject:"Thanks for applying"`
  - `from:workable.com subject:"Thanks for applying"`

**`dry_run`** (optional, boolean, default: true)
- If true, return list of matching emails without deleting
- If false, move matched emails to trash
- Always use dry_run=true on first pass

**`label_instead`** (optional, boolean, default: false)
- If true, apply custom label instead of moving to trash
- Useful for archiving without deletion

## Usage

```python
# Dry run — see what would be deleted
delete_useless_emails(
  search_query='from:indeedapply@indeed.com "Indeed Application"',
  dry_run=True
)

# Actually delete
delete_useless_emails(
  search_query='is:unread subject:"Thanks for applying"',
  dry_run=False
)
```

## Implementation Notes

- Uses Gmail API with `gmail.modify` scope to move emails to TRASH label
- Always requires `dry_run=True` confirmation before permanent deletion
- Logs number of emails matched and action taken
- Does NOT permanently delete (can be recovered from Trash for 30 days)
- Skips emails with stars or specific labels to prevent accidental loss

## Related Skills
- `google-connection` — OAuth setup and token management for Gmail API access
