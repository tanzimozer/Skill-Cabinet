---
name: interview-prep
description: Research a company and role to produce a structured pre-call brief for Tanzim before a job interview.
tags: [jobs, interview, research, career]
triggers:
  - Tanzim has an interview or phone screen coming up
  - User asks to prep for a call with a company
  - A job invitation email is received and Tanzim wants to prepare
---

# Interview Prep

## Goal
Produce a concise, actionable brief Tanzim can read in under 5 minutes before a call.

## Inputs needed
- Company name
- Role title
- Job listing URL (direct company URL preferred over job board)
- Interview time + interviewer name if known
- Resume number (from job tracker) if Tanzim wants to review

## Research steps (delegate via delegate_task with web toolset)

Search for:
1. What the company does — product, market, customer segment, company size
2. Funding, ownership, notable investors (e.g. PE-backed = metrics-driven culture)
3. Recent news — product launches, acquisitions, expansions, layoffs
4. The role's core responsibilities and success metrics (pull from job listing)
5. Likely interview focus areas for the role type

## Output format

```
COMPANY — INTERVIEW PREP

What they do
[2-3 bullets: product, market, customers]

Company
[Size, founded, HQ, backed by, notable facts]

Recent intel
[1-3 bullets of recent news worth knowing]

The role — [Title]
[What the manager/team owns, key metrics, cross-functional partners]

What to lead with
[3-5 bullet talking points: past impact, numbers, relevant experience]

Smart questions to ask
1. [Process/team question]
2. [Success metrics question]
3. [Roadmap/growth question]
4. [Day-to-day/culture question]
```

## Tanzim's résumé anchor stories (May 2026 CV)
Always pull from his actual résumé — download `69.pdf` or relevant file from Drive and parse with pdfplumber. Key stories:
- **US Bank (Jan 2025–present)**: 9–17 team coordination, 100% on-time milestone rate, contractual SLA compliance, top 10 district producer in 9 months
- **TIMBR LLC (Nov 2022–Jan 2025)**: Jira/Confluence/Salesforce PM, MVP 45 days early + 6% under budget, risk logs, executive stakeholder reporting
- **24 Hour Fitness (Mar 2020–Nov 2022)**: 12+ staff trained, 95% SOP adoption in 30 days, location ranked 255→87 nationwide
- **Guckenheimer (Jan 2018–Nov 2019)**: 4-site simultaneous rollout, 35% reduction in unplanned downtime, MS Project planning

## Terminology/abbreviations — Tanzim asks for these
When he asks "what does X mean", keep it to 3-4 sentences max:
1. Full form
2. Plain English one-liner
3. How it shows up in his CV or this specific role
No padding, no lists of 10 terms at once — answer what was asked.

Common ones he's asked about: SLA (Service Level Agreement), PMO (Project Management Office), RAID log (Risks/Assumptions/Issues/Dependencies), Jira, Confluence, SDLC, Agile, Scrum, Kanban, W2.

## Job tracker lookup
- **Job_Tracker** sheet ID: `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`
- **TERRAjob** sheet ID: `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI`
- Tab naming: daily date tabs (`5/8`, `05/14`, `05/27` etc.) + `Master Tracker` + **`Interviews`** (canonical pipeline view)
- **Interviews tab** (GID `1499246630`) is the best first stop — it has company, role, resume filename, status, and interview link in one row
- Resume PDF filename = the number in the row (e.g. entry `69.pdf` — search Drive by filename)
- To build a direct tab link: get GID via `meta['sheets'][n]['properties']['sheetId']` then `https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={gid}`
- Resume row number ≠ PDF number always — check the actual cell value, don't assume offset
- **See `references/job-tracker-lookup-pattern.md` for full workflow + pitfalls**

## Email scan
- Search Gmail for latest email from the company: `from:[company domain] interview OR invitation`
- Pull interviewer name, exact time, any prep instructions

## Urgent-mode prep (< 20 minutes to interview)

**When Tanzim says "X mins til interview":**
- **Execution-only delivery**. No elaboration, no options, no suggestions. Facts only: company, role, interviewer name, time, format (video/phone/Zoom), Zoom link if applicable, resume filename
- If time < 15 mins: add **2 tactical talking points max** (key strength for the role, one STAR story if applicable)
- No background research, no "you might want to", no multi-option menus
- Brevity = respect for his time. Verbosity = frustration. Trust he knows what to do; just give him the facts

## Pitfalls
- Job listing URLs on job boards (BuiltInSeattle, Indeed, LinkedIn) may differ from the actual company listing — always find the direct company careers URL
- `delegate_task` with web toolset can time out on complex multi-URL scrapes — keep the prompt focused on search queries, not page extraction
- Vista Equity / PE-backed companies are heavily metrics-driven — always flag this and prompt Tanzim to bring numbers
- 20-minute phone screens = tight. Advise: keep answers sharp, ask 2 questions max, save depth for follow-up rounds
- **AI recruiter interviews (e.g. Avery at ITC)**: structured behavioural questions, on-camera, video link in confirmation email. Prep should focus on tight STAR-format answers, not company culture questions.
  - **Calendar API works** (used successfully Jun 2026 via the Google token at `/home/hermes/.hermes/google_token.json`, `calendar.events().list`). Use it to confirm what's genuinely on his calendar — but treat Gmail as the source of truth for scheduling intent: an interview can be confirmed by email yet sit unaccepted on the calendar (Google flags "unknown sender" invites and does NOT auto-add them). Cross-check both. Don't assume "in the inbox" = "on the calendar."
  - **Always include the live sheet LINK, not just tab + row.** Tanzim's standing instruction (Jun 2026): "make it as easy as possible for me." Give him the full clickable URL plus tab name and row number every time — never make him navigate from a bare cell reference. Canonical format: company → role → time → format/interviewer → JOB_HAMMER link → tab + row → score → résumé filename → company website. JOB_HAMMER sheet (current master, Jun 2026): `12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`, primary tab `MASTER_TAB`, with dated crawl-origin tabs (`Jun 08` etc.) holding the original row. The older TERRAjob sheet (`1vhK1ys...`) was migrated into JOB_HAMMER on 2026-06-16 — don't read from it.
- When Tanzim sends a screenshot of the JD and says "prep me for this", he wants: (1) role brief, (2) what they're really screening for, (3) Q&A anchored to his actual CV. Pull the résumé first before generating answers.
- **Sheet tab verification**: Always verify GID and tab name are correct before sending him a link. Check which tab the data actually landed in via sheet metadata, not assumption. Tab name ≠ GID.

## PST Time Tracking & Current Interview Status

**Always check current PST time when running prep.** Procedure:

```python
from datetime import datetime
import pytz

pst = pytz.timezone('America/Los_Angeles')
now_pst = datetime.now(pst)

# LFS Interview: June 17, 2:00 PM PST
interview_time = pst.localize(datetime(2026, 6, 17, 14, 0))
interview_end = pst.localize(datetime(2026, 6, 17, 14, 30))

if now_pst < interview_time:
    time_remaining = (interview_time - now_pst).total_seconds() / 3600
    status = f"UPCOMING in {time_remaining:.1f} hours"
elif now_pst <= interview_end:
    status = "IN PROGRESS (30-min duration)"
else:
    status = "COMPLETED"

print(f"Current PST Time: {now_pst.strftime('%A, %B %d, %I:%M %p %Z')}")
print(f"LFS Interview Status: {status}")
```

## Active Interview: LFS Inc. (Go2marine) — eCommerce Operations Specialist

**Interview Status:** SCHEDULED FOR TODAY (Wednesday, June 17, 2026)
- **Time:** 2:00 PM – 2:30 PM PST (30 minutes)
- **Interviewer:** Charlene Slayton <cslayton@go2marine.com> / LFSCharleneSlayton@hinc.com
- **Format:** Video call (Microsoft Bookings link in confirmation email)
- **Job Sheet:** JOB_HAMMER → MASTER_TAB → Row 294
- **Sheet Link:** https://docs.google.com/spreadsheets/d/12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0/edit#gid=0&range=A294:Z294

### Job Summary
**Position:** eCommerce Operations Specialist  
**Location:** Remote, Full-time  
**Pay:** $20–$22/hour  
**Company:** LFS Inc. (subsidiary of Trident Seafoods, est. 1967)

### Core Responsibilities (What You'll Do)
- Process orders, manage cancellations, returns, and customer issues
- Provide multi-channel customer service (phone, email, support cases)
- Support Shopify and call center order flow
- Coordinate with warehouse on fulfillment issues
- Manage customer follow-ups (returns, warranties, shipping claims, order resolution)
- Work across Amazon, Walmart, eBay, and Shopify platforms

### Key Skills & Requirements
**Must Have:**
- Excel expertise (data entry, troubleshooting, reporting)
- Detail-oriented, organized, multi-tasking capability
- Comfortable troubleshooting errors, stranded inventory, fulfillment issues
- 1–2 years eCommerce or digital operations experience
- High School diploma or GED minimum
- Clear communicator who can follow and improve processes

**Preferred:**
- Bachelor's degree in marketing, business, communications, or related field
- 3–5 years eCommerce/digital operations experience
- Warehouse coordination or third-party shipping experience

### What They're Looking For (Prep Talking Points)
1. **Multi-channel platform expertise** — Amazon/Walmart/eBay/Shopify experience; show SLA compliance and order accuracy metrics
2. **Problem-solving under pressure** — Examples of handling difficult customers, stranded inventory, shipping issues; focus on quick resolution
3. **Process improvement mindset** — Any examples of streamlining workflows, reducing errors, improving customer satisfaction
4. **Communication clarity** — Ability to document issues, escalate appropriately, coordinate cross-functionally with warehouse teams
5. **Remote work discipline** — Home office setup, self-directed time management, ability to meet deadlines without supervision

### Pre-Interview Checklist
- [ ] Review eCommerce operations fundamentals (order lifecycle, returns management, platform mechanics)
- [ ] Prepare 2–3 STAR examples:
  - Managing a difficult customer service situation (complaint resolution)
  - Handling fulfillment/inventory issue under time pressure
  - Improving a process or reducing errors in past role
- [ ] Confirm home workstation is ready (quiet, professional background, camera/mic tested)
- [ ] Have LFS job description open (Row 294 of Job Hammer sheet)
- [ ] Test Zoom/video link 5 minutes before interview
- [ ] Keep resume (69.pdf or relevant) and notes on eCommerce experience visible

### Smart Questions to Ask Charlene
1. **"What does a typical day look like in this role? How much time is spent on each channel (Amazon, Shopify, eBay, Walmart)?"** — Shows you're thinking operationally
2. **"What's the biggest challenge the current team faces with order processing or customer service?"** — Opens door for you to position your problem-solving
3. **"How does the warehouse coordination work day-to-day? Are there pain points I should be aware of?"** — Demonstrates partnership mindset
4. **"What metrics matter most for success in this role?"** — Shows you're metrics-driven (SLA, accuracy, response time, customer satisfaction)

### Post-Interview Follow-Up (Within 2 Hours)
- Send thank-you email to Charlene Slayton at cslayton@go2marine.com
- Mention specific discussion point (e.g., multi-channel coordination, a challenge she mentioned)
- Update Job_Tracker Interviews tab with outcome and next steps
- Note any callbacks, second round requests, or timeline information

## State file
Update `/home/hermes/context/daily_state.md` after prep is delivered — mark task as complete and note interview outcome when Tanzim reports back.
