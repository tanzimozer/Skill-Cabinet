---
name: application-tracker
description: Maintain Tanzim's job-application tracker Sheet — add/update rows, statuses, follow-up dates. Use after any application sent or status change.
---

# Application tracker (Google Sheet)

Use whenever an application is sent or a status changes.

Columns: Company | Role | Date Applied | Source | Status | Next Action | Next Action Date | Notes | Link.

Steps:
1. On submit: append a row, Status=Applied, Next Action=Follow up, Next Action Date=+7 days.
2. On reply/interview/reject: update Status + Next Action + date.
3. Surface (only if asked, or as a single heads-up): rows whose Next Action Date ≤ today.

Deadlines context: US Bank ends May 22; Chase June 1 backup; priority = land remote tech job before Chase.

Pitfalls: one row per application; never duplicate; keep the Sheet in HERMES Drive folder.
Verify: row count == applications sent; no past-due Next Actions silently sitting.
