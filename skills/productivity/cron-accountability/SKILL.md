---
name: cron-accountability
description: "Design rules and pitfall patterns for Tanzim's scheduled accountability and reminder cron jobs."
version: 1.0.0
tags: [cron, accountability, reminders, check-in, scheduled]
related_skills: [gmail-inbox-check]
---

# Cron Accountability Jobs

Covers the daily check-in, reminder design, and lessons learned from bad prompts.

## Active recurring jobs (as of May 2026)

| Job ID | Name | Schedule | Notes |
|--------|------|----------|-------|
| `30660ee62c1d` | Daily Accountability Check-in | 7 AM weekdays | Format-only, no data source |
| `7fde95af25e4` | Gmail Check — Morning | 6 AM daily | Full inbox scan |
| `e1b36b5e1a09` | Gmail Check — Midday | 12 PM daily | Full inbox scan |
| `7347dc7f2f8a` | Gmail Check — Evening | 5 PM daily | Full inbox scan |
| `cae21a89a272` | Substack reminder | Monday 8 PM | Static message |
| `f45d1682b7e9` | Sunday Weekly Planning | Sunday 9 PM | Trello + Sheets |

## ⚠️ Critical rule: never fabricate specifics in cron prompts

The May 26, 2026 Daily Accountability check-in hallucinated a "Housecall Pro interview at 12:30 PM with Precious Barton" — a completely invented specific that Tanzim received as a real reminder. This happened because:
- The prompt had static context ("job search is a priority") but no live data source
- The model filled gaps with plausible-sounding specifics from older memory

**Rule:** Any cron prompt that mentions specific tasks, meetings, names, or deadlines MUST either:
1. Have a verified live data source (Gmail, Sheets, calendar) the job can actually query, OR
2. Be explicitly instructed: *"Do NOT invent or assume specific tasks. If you have no verified specifics, keep priorities general."*

Never ship a cron prompt with static "context hints" that could be mistaken for current state.

## Reminder design pattern

One-shot reminders for same-day tasks:
```
schedule: "2026-MM-DDThh:mm:ss-07:00"  # always include Seattle TZ offset
repeat: once
```

Recurring reminders: use cron expression `"0 H * * *"` for daily, `"0 H * * 1-5"` for weekdays.

## Cleaning up stale reminders

When interview/task reminders go stale (the tasks are done or expired), **delete them** — don't pause. Paused jobs accumulate and confuse future audits. The 3 interview task reminders (0ff7a3d00edf, d2afbb448c20, 359043ea5b93) were deleted May 26 after running for 9 days on an expired task list.

## Voice codeword handling

Tanzim sometimes gives the codeword by voice. Voice transcription can mangle it (e.g. "TETA" instead of "THETA"). If the word is close but wrong:
- Flag it: *"That came through as X — did you mean Y?"*
- Do NOT refuse and make him repeat from scratch
- Do NOT act on a garbled codeword that doesn't match
