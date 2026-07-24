---
name: launch-countdown-cron
description: "Schedule a launch countdown with periodic check-in pings and a go-time notification via cron jobs. Reusable for any TIMBR or project launch."
version: 1.0.0
tags: [cron, launch, timbr, countdown, schedule, whatsapp]
related_skills: [deploy-subagents, wix-api-operations]
---

# Launch Countdown Cron

Schedule a set of timed check-in pings + a terminal "go time" notification for a project launch. Used for TIMBR launch countdowns delivered to Tanzim's WhatsApp.

## Pattern

When Tanzim says "set a timer and give me check-ins at [times]" for a launch:

1. Note current time + timezone (server is PDT, UTC-7)
2. Convert each requested local time to UTC cron expression
3. Set `repeat` to cover just the launch window (e.g. `2` for 2 days)
4. Create a separate one-shot "go time" job at the exact launch moment
5. Deliver all jobs to `160799431606497@lid`

## PDT → UTC Cron Conversion

PDT = UTC-7. Add 7 hours to the local time:

| PDT | UTC | Cron (UTC) |
|---|---|---|
| 11:00 AM | 6:00 PM | `0 18 * * *` |
| 3:00 PM | 10:00 PM | `0 22 * * *` |
| 7:00 PM | 2:00 AM+1 | `0 2 * * *` |
| 10:00 PM | 5:00 AM+1 | `0 5 * * *` |

Note: 7pm and 10pm PDT roll into the next UTC calendar day — be aware of this for single-day launch windows.

## Check-in Prompt Template

Each check-in job prompt should include:
- Who you are (Friday, Tanzim's assistant)
- Target: `160799431606497@lid`
- Launch time anchor (absolute date+time) for calculating hours remaining
- Instructions: state current time, hours to launch, ask for status update (done/left/blockers)
- Sign off as Friday

**Calculating time remaining at runtime:** Use `python3` with `pytz` to get exact hours/minutes:
```python
from datetime import datetime
import pytz
pdt = pytz.timezone('America/Los_Angeles')
now = datetime.now(pdt)
launch = pdt.localize(datetime(2026, 6, 1, 2, 48, 0))
delta = launch - now
mins = int(delta.total_seconds() / 60)
print(f"{mins // 60}h {mins % 60}m remaining")
```
Always run `date -u && TZ='America/Los_Angeles' date` first to confirm current wall time.

**Example check-in message (actual June 1 2:00 AM send):**
```
⏰ *TIMBR Launch Check-in* — 2:00 AM PDT, June 1

47 minutes to launch window (target: 2:48 AM PDT).

Boss — status report:
• What's shipped?
• What's still outstanding?
• Any blockers?

Clock's ticking. — Friday
```
Sharp, punchy, three bullets max. No preamble.

## Go-Time Prompt Template

One-shot job at the exact launch moment:
- Countdown hit zero
- TIMBR is live / launch has happened
- Energetic but sharp — not gushing
- Sign off as Friday

## Example Job Set (TIMBR Launch May 30 → June 1, 2026)

```
11am PDT:  schedule_task(schedule="0 18 * * *", repeat=2, deliver="160799431606497@lid")
3pm PDT:   schedule_task(schedule="0 22 * * *", repeat=2, deliver="160799431606497@lid")
7pm PDT:   schedule_task(schedule="0 2 * * *",  repeat=2, deliver="160799431606497@lid")
10pm PDT:  schedule_task(schedule="0 5 * * *",  repeat=2, deliver="160799431606497@lid")
Go-time:   schedule_task(schedule="48 9 1 6 *", repeat=1, deliver="160799431606497@lid")
```

Go-time cron for June 1 at 2:48 AM PDT = June 1 at 9:48 AM UTC = `48 9 1 6 *`

## Pitfalls

- **Don't use daily cron naively for a 48h window.** A `repeat=2` cap ensures the check-ins stop after 2 days; without it, they'd run indefinitely.
- **7pm and 10pm PDT cross midnight UTC.** `0 2 * * *` and `0 5 * * *` fire the next calendar day in UTC — works correctly in practice but easy to misread when debugging.
- **Go-time job needs a specific date cron, not `* * *`.** Use `MM HH DD MON *` format for the one-shot launch ping.
- **Check actual server time before calculating.** Run `date` to confirm current timezone is PDT (UTC-7) before building cron expressions — the server could be misconfigured.
- **`send_message` tool may fail 401 in cron context.** When running as a scheduled job, the `send_message` tool can hit auth issues. Fall back to direct curl against `localhost:3000/send` with Bearer token from `WHATSAPP_BRIDGE_TOKEN` in `~/.hermes/.env`. See `whatsapp-bridge` skill for full pattern.
