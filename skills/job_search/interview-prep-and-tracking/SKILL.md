---
name: interview-prep-and-tracking
description: Scan Gmail for interviews, cross-reference job tracker sheets, extract details, and prepare briefing notes for upcoming calls
tags:
  - interview
  - job-search
  - gmail
  - sheets
  - preparation
---

# Interview Prep & Tracking

## Overview
End-to-end workflow for managing job interview pipeline: locate interview confirmations in Gmail, pull job descriptions from tracker sheets (JOB_HAMMER, terrajob, Job_Tracker), extract key details (time, interviewer, role, company), and prepare talking points.

## Workflow

### 1. Scan Gmail for Interview Emails
**Query patterns to use:**
```
subject:interview
subject:schedule
subject:confirmed
subject:booking
subject:"meeting confirmed"
```

**What to extract from each:**
- Sender (hiring manager / recruiter name)
- Subject line (role title often here)
- Date/time (look for ISO format or "Wednesday June 17")
- Zoom/Teams link (often in body or calendar attachment)
- Interview type (phone screen, technical, behavioral, final round)
- Key context clues (position name, company, location)

### 2. Cross-Reference Job Tracker Sheets
**Primary sheets:**
- `JOB_HAMMER` (MASTER_TAB) — single source of truth; columns: Resume PDF, ID, Company, Position, Status, Location, Application Date, JD (full)
- `terrajob` (multiple tabs by date) — alternate reference
- `Job_Tracker` (various tabs) — application history

**Lookup strategy:**
1. Extract company name from Gmail
2. Search JOB_HAMMER → MASTER_TAB for company match
3. Pull full row: resume used, job ID, position title, location, pay range, full JD
4. If not found, check dated tabs (Jun 16, Jun 15, etc.)

**Key fields to extract:**
- **Position:** exact job title
- **Company:** full legal name
- **Location:** remote/city (for context)
- **Pay range:** salary/hourly (if listed)
- **Core responsibilities:** top 3–5 from JD
- **Key skills required:** from "Minimum Requirements" and "Preferred"
- **Success metrics:** how performance is measured

### 3. Prepare Interview Brief
**One-page talking points format:**

| Field | Content |
|-------|---------|
| **Date/Time** | Wednesday, June 17, 2:00 PM PT (30 min) |
| **Interviewer** | Charlene Slayton (Hiring Manager) |
| **Role** | eCommerce Operations Specialist |
| **Company** | LFS Inc. (Go2marine.com) |
| **Key Duties** | Order processing, customer service, multi-channel (Amazon/eBay/Shopify), catalog updates |
| **Core Skills** | Excel, troubleshooting, detail-oriented, warehouse coordination |
| **Your Edge** | [Customer service under pressure / inventory management / multi-channel experience] |
| **2–3 STAR Stories** | [Prepared examples matching role] |
| **Questions for Them** | [Company culture / team size / remote setup / growth path] |

### 4. Detect Action-Required Emails (Safety Gate)
**Do NOT delete interview emails. Always check for:**
- Scheduling link or booking confirmation
- Time/date/Zoom link
- Mention of "confirm your availability" or similar
- Any request for user to take action (RSVP, fill form, etc.)

If present → flag for preservation. See `delete-useless-emails` for safe deletion rules.

---

## Quick Script — Scan & Extract Today's Interviews

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json, os

# Load credentials
token_file = os.path.expanduser('~/.hermes/google_token.json')
with open(token_file, 'r') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['access_token'],
    refresh_token=token_data.get('refresh_token'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id='990922176945-n9132okninl4isc7l7kd3n9345epaiqg.apps.googleusercontent.com',
    client_secret='<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>'
)

gmail_service = build('gmail', 'v1', credentials=creds)

# Search for interview emails
queries = ['subject:interview', 'subject:schedule', 'subject:confirmed']
all_interviews = []

for q in queries:
    results = gmail_service.users().messages().list(
        userId='me', q=q, maxResults=50
    ).execute()
    all_interviews.extend(results.get('messages', []))

# Deduplicate and display
seen = set()
unique = []
for msg in all_interviews:
    if msg['id'] not in seen:
        seen.add(msg['id'])
        unique.append(msg)

# Get full details
for msg in unique[:10]:
    full = gmail_service.users().messages().get(
        userId='me', id=msg['id'], format='full'
    ).execute()
    headers = {h['name']: h['value'] for h in full['payload']['headers']}
    print(f"• {headers.get('Subject', 'No subject')}")
    print(f"  From: {headers.get('From', 'Unknown')[:50]}")
    print(f"  Date: {headers.get('Date', 'Unknown')[:30]}\n")
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Interview email accidentally deleted | Check trash; do not delete emails with scheduling/confirmation details |
| Wrong job description pulled (similar company names) | Always verify company legal name and location match |
| Missing time zone in meeting link | Always convert to user's local TZ (Pacific PT / UTC-08) before briefing |
| Interviewer name misspelled in brief | Copy directly from email header or LinkedIn profile |
| No talking points for role | Pull core responsibilities and craft 2–3 STAR stories mapping to them |
| Forgot to pull full JD | Check JOB_HAMMER MASTER_TAB; full JD usually in column 8+ (wide text field) |

---

## Related Skills
- `google-connection` — OAuth setup for Gmail/Sheets access
- `delete-useless-emails` — safe deletion of non-action-required emails
- `credential-management-tanzim` — secure credential handling

---

## Session References
- **Session:** June 17, 2026 — LFS Inc. eCommerce Specialist interview, 2:00 PM, Charlene Slayton
- **Job Sheet:** JOB_HAMMER, MASTER_TAB, Row 294
- **Gmail Query Pattern:** Used `subject:interview`, `subject:schedule`, `subject:confirmed`
- **Cross-Reference Result:** Found via company name "LFS" + "Go2marine"; pulled full 8-column JD from sheet
