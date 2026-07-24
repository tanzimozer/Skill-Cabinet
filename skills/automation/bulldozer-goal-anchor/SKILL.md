---
name: bulldozer-goal-anchor
description: The north-star goal and anti-drift guard for the Bulldozer Instagram crawler. Load this whenever working on Bulldozer to stay locked on the ONE goal and catch deviation early. Use at the start of any Bulldozer work session and whenever the conversation starts adding features before the core loop is closed.
---

# Bulldozer — Goal Anchor (anti-drift)

## THE ONE GOAL (everything else is secondary)
**Tanzim types "crawl @handle" in this WhatsApp group chat → the crawler fires on
his Mac → results come back to the chat.** Friday can trigger it the same way on
his say-so. That is the deliverable. Nothing counts as "done" until this loop is
closed and tested live.

## DONE / NOT DONE (check every session)
- [x] crawler.py — scrolls followers, scrapes handles, dedupes, CSV. WORKS (tested: 1,633 handles from a public seed).
- [x] Cookies live, venv + Playwright installed on Mac (~/Desktop/Bulldozer).
- [x] Sheets upload works (OAuth authorised).
- [x] **Trigger loop built via listener_sheet.py** — polls a 'Commands' tab on the
  Bulldozer sheet, fires crawler, writes status back. Reuses existing Google OAuth,
  NO WhatsApp bridge token needed. This was the unlock: the Sheet IS the bridge.
- [ ] Live trigger test: Friday writes a `pending` row → Mac fires → dated tab appears → Friday reports.

## THE TRIGGER MECHANISM (resolved — the Sheet is the bridge)
The original plan needed a WhatsApp bridge URL+token that was never available. The
working design instead: **Friday writes a command row to a 'Commands' tab on the
Bulldozer Google Sheet; the Mac (already OAuth-authorised) polls it and executes.**
No new credentials. Commands tab columns: id | command | target | depth | status |
result | requested_at | done_at. status: pending→running→done|error.

## I/O SPEC (locked by Tanzim)
- **Input:** Tanzim sends a screenshot of an IG handle → Friday reads the handle off it.
- **Output:** ALWAYS the same spreadsheet ('Bulldozer — Handles'). EVERY crawl
  creates a NEW tab named the crawl date in `%b %d` format → "Jul 03". Same-day
  repeat → "Jul 03 (2)", never overwrites. Header row bold, centred, frozen.
- Crawler takes `--run-out <csv>` to emit this run's catch (pre global-dedup) so
  the dated tab shows the full haul even when handles already exist in the master.

## ANTI-DRIFT RULES
1. **Before adding ANY feature, ask: does this close the trigger loop?** If no, park it.
2. Enrich pass, fitness scoring, Seattle flag, 24-column schema, account pool,
   dispatcher, CI/CD — all real, all LATER (Phase 2+). Do NOT build them before the
   trigger loop works end-to-end. THIS SESSION drifted into Phase 2 enrich-building
   and Tanzim caught it with "why are we doing this?" — do not repeat.
3. When Tanzim asks "why are we doing this?" — that's the drift alarm. Stop, return
   to THE ONE GOAL, report done/not-done honestly. He is a reliable drift detector;
   trust it.
4. Seeds must be PUBLIC accounts (tanzim_ozer is private — its followers won't open).

## OUTPUT DISCIPLINE (Tanzim corrected this HARD this session)
Repeated complaints: "too much information to consume at once", "don't crowd it",
"write as less as possible but don't miss context", "let's [cut] noise", "you don't
have to add anything for me or explain me". Rules that follow:
1. **When he'll copy-paste to Claude, write ONLY the exact block Claude needs.** No
   preamble, no explanation to Tanzim, no "then we'll…". Just the code/command.
2. **Never dump a multi-section wall.** One idea, condensed, in bullets. If it needs
   a chart he asked for, give the chart and nothing else around it.
3. **Verify before texting.** He said: "Organize the data, condense it, check that
   you have no error, and then text it." Compile/validate first, deliver the clean
   result — don't think out loud in the message.
4. **Don't re-teach him his own system.** He designed it; he doesn't need it
   re-explained back. State status/next-command and stop.
5. When condensing a settled decision, write it into the skill ("hard put it into
   your soul") rather than re-deriving it in chat next time.

## PHASE MAP (do not jump ahead)
- **Phase 1 (NOW):** WhatsApp trigger loop. crawl @handle from chat → fires → replies.
- **Phase 2:** Enrich → Providers/Rejected tabs, fitness score, Seattle flag, band 150–3,500.
- **Phase 3:** Account pool (10 crawl + 1 follow) + hub-and-spoke dispatcher, cold rotation.
- **Phase 4:** CI/CD self-updating watcher (deploy from phone).

## REPO
github.com/tanzimozer/Bulldozer (private, renamed from instagrammer-lite).
On Mac: ~/Desktop/Bulldozer. Full detail + Phase 2–4 specs live in the
`instagram-follower-crawler` skill.
