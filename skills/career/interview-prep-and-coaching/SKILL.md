---
name: interview-prep-and-coaching
description: Find Tanzim's upcoming interview, cross-check the job listing against his resume, build a focused prep sheet, and stress-test him one question at a time using STAR. Also covers candid career/strategy coaching when he invites the hard read.
category: career
---

# Interview Prep & Coaching

Class-level skill for the recurring flow when Tanzim has an interview coming up,
plus the candid career-coaching register he asks for around it. Distinct from
`terrajob-crawler` (which is the crawl/track/resume-generate machinery) — this is
the human-facing prep + drilling + strategy work.

## 1. Find the interview (calendar is often EMPTY — go to Gmail)

Tanzim's interviews frequently aren't on his Google Calendar. When he says "find
my interview today," check BOTH and trust email over calendar:

- **Calendar:** `primary` calendar, today's window. Often returns nothing.
- **Gmail (the real source):** search recruiter/confirmation mail. Useful queries:
  `interview newer_than:Nd`, `zoom interview`, `from:<recruiter> <role>`,
  `"Jun 25" interview`, `"June 25" interview`. Read the full body of the
  confirmation to extract: date/time + timezone, interviewer name + title,
  platform + join link + Meeting ID + passcode.

Access pattern: build Google services directly in `execute_code` from
`~/.hermes/google_token.json` (token has calendar + gmail + drive + sheets +
docs scopes). Don't reach for the browser — Google properties hang headless.
If refresh fails, see `gmail-automation` credential-recovery references.

**Pin the DATE before answering — he often has several interviews queued.** He
may have 3-5 upcoming interviews at once (Partners 1st, YMCA, Aquila, etc.). When
he says "find my interview today" and you answer, and he replies "that's not the
correct interview" — he means a DIFFERENT day. Don't re-explain the same one;
ask or search for the specific date he names ("check all my emails for July 2nd
interview"). Gmail query that works: search broad terms — `interview July 2`,
`YMCA interview`, `<interviewer name>`, `Danielle Hastings`, `interview confirmed`
— then read the MS Bookings / calendar-invite confirmation for the exact
`When: <date> <time> (UTC-08:00) Pacific Time`. MS Bookings confirmations from
`*.onmicrosoft.com` carry the clean date/time/interviewer block; strip the
`<style>` HTML noise first (regex `<style.*?</style>` with DOTALL) or you get CSS.

**Disambiguate same-name employers.** "Allen Institute" (biosciences,
Admin Coordinator role) vs "Ai2 / Allen Institute for AI" (OlmoEarth) are
DIFFERENT employers — and "Booz Allen Hamilton" is a third. When cross-checking
the sheet, a substring match on "Allen" pulls all three; report them separately
and name which one is the actual interview. Same trap with short company names.

## 2. Cross-check the listing vs the resume

The job listing lives in the JOB_HAMMER sheet (id
`12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`, tab `MASTER_TAB`, columns
`RESUME_PDF, SCORE, COMPANY, TITLE, SALARY, LOCATION, REMOTE, JD, NOTES,
APPLIED, CALLBACK`). The resume PDF is in Drive (search by the RESUME_PDF
filename). Read both, then produce a SHORT match analysis:

**Resume access — the per-job PDF is a real PDF; fall back to the master Doc.**
Each job has its own tailored resume in Drive named `Tanzim_<Company>.pdf` (and a
`_Deedy.pdf` variant + `_CoverLetter.docx`). Those are true PDFs, so
`files().export()` fails on them — download bytes and parse, or when you just need
the career facts fast, export the master Google-Doc resume
`Tanzim_Ozer_Resume` (Drive id `1ACxA2mz9PThr3QvJUpKBf0qBLJO4hHkXgMp-sQYbjUI`)
via `files().export(mimeType='text/plain')`. It carries the hard numbers to build
answers from: US Bank CRC (current, $350K+ deposits, 100% SATE/CRI), TIMBR TPM
(MVP early + 6% under $80K budget, 600 users), 24 Hour Fitness Sales/Ops Analyst
(led 17-person team, 1,500 members, 255→87 national rank), Guckenheimer PM.

- **Edges:** where the resume maps cleanly to the JD (mirror the JD's own words).
- **Gaps/landmines:** named tools/systems in the JD that are absent from the
  resume (e.g. ServiceNow named 5×, resume only has JIRA/Asana). Flag every one
  — these are what the interviewer probes.
- **Over/under-qualification:** if it's a tier below his background (HS-diploma,
  1-yr role, lower band), flag it and prep a clean "why this role" answer.

**Backfill empty JD cells while you're in there.** If the listing's JD column is
blank, pull the description (from the LinkedIn posting / email) and write it to
`MASTER_TAB!H{row}`. Confirm the write and report the new length.

## 3. Build the prep sheet (short, scannable)

Structure: the role in one line → 3 strongest bridges (with hard numbers from
his resume) → 3 landmines → their stated values to mirror → 2 questions HE asks
THEM (pull from the recruiter's own email if they listed suggestions). Plus 2-3
real facts about the employer (founding year, founder, mission) — recruiters
often explicitly say "research us," so have facts ready, not platitudes.

## 4. Stress-test — ONE question at a time

This is the format Tanzim explicitly asked for. Do NOT dump a question bank.

- Pose ONE likely question (lead with the hardest landmine).
- Let him answer; he'll often ask "how should I answer that?" first — give a
  model answer, THEN make him say it back in his own words.
- **Grade honestly and push back** before moving on. Name what's vague, what
  number he dropped, what he should lead with. He values the candor.
- Use **STAR** (Situation, Task, Action, Result) — recruiters tell him they
  score on it. Keep each beat to 1-2 sentences; don't let Situation balloon.
- Only advance to the next question when the current answer holds.

### Answer-craft rules that landed well
- **Name a gap once, don't dwell, land on a proof point.** ("Not ServiceNow
  directly — but ticket-and-dispatch was daily in JIRA/Asana... at US Bank I
  picked up banking cold and was top-10 in nine months. I'd be productive in a
  week.") Never say "I'm a fast learner" — show it with a cold-start story.
- **Don't repeat a loaded phrase the interviewer might fear.** Tanzim caught
  this: answering a flight-risk question, do NOT say "on the flight risk—" and
  re-plant the doubt. Fold the loyalty proof in as commitment ("when I commit to
  a place, I dig in and build" + retention numbers). Only address it head-on if
  THEY name it first.
- **Reframe a step-down as focus, not desperation.** "The titles look senior but
  the through-line is operations/coordination — this role is exactly that,
  somewhere the mission matters."
- Lead every answer with the hard number from his history (255→87, 14→5 days,
  35% downtime cut, retained across all 3 phases).
- Speech-to-text mangles acronyms (his "SLA" came through as "Ella"); when
  drilling verbally, flag to enunciate acronyms on the day.

## 5. Deliver the interview link cleanly when asked

When he asks for "the link," give platform + join URL + Meeting ID + passcode +
interviewer + time, then a one-line "test your connection early." Nothing more.

**Job Hammer row deep-link (jumps straight to the row).** When he asks for the
Job Hammer link to a specific listing, hand him a gid+range anchor, not the bare
sheet URL:
`https://docs.google.com/spreadsheets/d/12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0/edit#gid=<TAB_GID>&range=A<ROW>`
Get `<TAB_GID>` from `spreadsheets().get()` sheet properties (the dated tab, e.g.
`Jun 25` = gid `988765811`), and `<ROW>` is the 1-indexed row on THAT tab (the
canonical dated-tab row, not the MASTER_TAB row — cite both, link the dated one).

**The public posting is often GONE once he's interviewing.** When he says "find
the posting on Indeed/Google, I couldn't find it," expect to come up empty:
either it was pulled once he entered the pipeline, or it only ever lived on the
employer's internal ATS. All the public boards (Google, Bing, DuckDuckGo, Indeed,
LinkedIn) captcha/bot-wall the headless browser — LinkedIn returns generic
region-wide junk, not the exact role. Don't burn ten navigations chasing it.
Give the honest read fast: the role is real (he has the full JD from Job Hammer +
a confirmed interview + the recruiter's email), the missing public listing
changes nothing, and offer ONE more targeted try (the employer's ATS) or stop.
If he sends the ZipRecruiter/aggregator link himself, it's the live posting even
when the headless browser hits Cloudflare — it opens fine for him.

**Aggregator salary is INFLATED — trust the real posting, not ZipRecruiter.**
Aggregators (ZipRecruiter especially) slap an algorithmic pay estimate on the
listing that can be wildly high — this session Zip showed "$35–40/hr" while the
actual employer posting AND the JOB_HAMMER `SALARY` column both said $24–28/hr.
Anchor him to the REAL number for salary-expectation questions. Two traps caught
here: (a) don't propagate the aggregator's inflated figure as if it were the
offer band; (b) sidebar "related jobs" on the same page carry their OWN pay (the
$35–40 was actually a TEKsystems sidebar row, not the YMCA role) — read which
listing a number belongs to before flagging it. Verify against the scrolled
screenshot showing the employer's own "Hiring range:" line.

## 5b. Take-home / written assessment stage (respond-to-scenarios)

Some interviews (YMCA Lead Membership Support Specialist did this) send a
**second-round written assessment**: a .docx with 3-5 mock customer emails,
"respond as if you were a staff member." Distinct from live drilling — you're
GHOST-WRITING polished replies on his behalf, not quizzing him.

**Workflow that worked:**
1. **Pull the attachment from Gmail** — the scenarios are a .docx attachment on
   the recruiter's mail. Find the message (`from:<recruiter> subject:"Second
   Interview"`), walk `payload` parts for the attachment, save bytes, parse with
   `python-docx` (`from docx import Document`). See
   `references/ymca-support-specialist-assessment.md` for the exact scripts.
2. **VERIFY every fact on the employer's own site — never invent.** The
   assessment explicitly grades "how you navigate our website." Pricing, policy,
   pool names, schedules, class costs all come from the live site. Fetch pages
   with `urllib` + a real User-Agent; strip `<script>/<style>`, regex out tags.
   Some content is JS-injected and only shows via the browser or on the 404
   fallback page — if `urllib` returns empty, the browser snapshot has it.
3. **Cite the source-of-truth URL in the reply**, especially when the customer
   threatens escalation (BBB, small claims). A policy link = paper trail and
   reads as competence, not defensiveness. Place it right after the explanation,
   not as a defensive footer.
4. **Discuss the strategy BEFORE writing** when he says "let me lead, you
   observe." He'll frame the business goal himself (e.g. "hold the charge but
   retain the customer, offer something that costs the Y nothing"). Confirm the
   policy read, name the zero-cost goodwill levers, THEN draft.
5. **Map upsells / value-adds in TWO tiers for warm leads** (returning member
   wanting guidance): free retention hook FIRST (leads the reply, pure care),
   paid upsells SECOND. This is the exact helpful-AND-revenue-aware instinct a
   membership/support role is graded on.
6. **STAY IN YOUR LANE — support routes, it doesn't sell.** Hard correction he
   gave: "I'm membership support, I want to CONNECT the member to the department
   who can best help — I don't want to be the seller." Reframe every upsell as a
   warm handoff ("I can connect you with the Healthy Living team") not a
   self-pitch ("I'll set you up with a trainer"). Applies to any support-desk
   persona.
7. **Final QA when he compiles a submission PDF.** He'll send back a combined
   PDF and ask to fact-check + attach sources. Parse it back (`pdfplumber`),
   re-verify EVERY claim against its live source page (don't assume it matches
   the drafts), attach a verified source-of-truth URL to EVERY email as a
   labelled block before the sign-off, and flag polish nits (URL line-wrap
   breaking the hyperlink, proper-noun casing drift).

### Customer-service reply craft — the tone he landed on (HARD-WON)
He iterated the birthday-party reply ~6 times. The endpoint, and what to START
with next time so you skip the loop:

- **NOT fluffy.** He rejected the warm-padded version ("I did not like the
  fluffiness"). Cut throat-clearing, over-apology, and adjectives on vibes.
- **NOT a cold bullet-blast.** He also hated the all-bullets tight version ("too
  tight", "I hated this one"). Pure bullets read robotic.
- **THE WINNER = warm prose intro (2-3 sentences, human) THEN digestible
  bulleted sections with bold headers.** One short personal opener, describe the
  options in prose, then `**Guests** / **Duration** / **Cost** / **Cancellation**
  / **Decorations**` as scannable bullet groups, then a warm one-line close with
  the booking link. This hybrid is his format. Lead with it.
- **Bullets = FULL EXPLANATORY SENTENCES, not terse fragments.** The final
  refinement (Amy swim-lessons reply): he asked for "bullets but in a clearly
  explained sentence." A bullet like `14+ days → free` reads cold; write it as
  "If you transfer 14 or more days before the start date, it's completely free —
  no additional cost to move him into Stage 4." Each bullet is a complete,
  human sentence. Mix is fine: prose paragraph for continuous explanation, then
  a short bulleted list where the content is genuinely a set of tiers/parts (the
  three swim-test steps, the three cancellation tiers). Don't bullet-ise a
  narrative; don't narrate a genuine list.
- **He'll ask for "the source of truth" on any factual claim.** After a draft he
  frequently says "give me the source of truth / source URL" for a specific
  paragraph. Have the exact page URL ready for every fact you asserted — this is
  the website-navigation skill Dani grades. Keep a running URL list as you draft.
- **De-dupe confusing bullets.** When the same number appears three times doing
  different jobs (three "30 minutes": pool changeover vs paid add-on), he calls
  it "confusing." Fix: give each its own unambiguous line, and hoist a shared
  caveat to a header note (e.g. "the $100 deposit is never refundable — only the
  balance moves") instead of repeating "minus deposit" four times.
- **Flag shared-vs-unique explicitly.** If one set of terms covers two options,
  say "the details below apply to whichever you choose" so he isn't left
  wondering why there's one price for two parties.
- For the angry-billing scenario: empathy first, hold the charge WITHOUT quoting
  policy AT the customer ("explain why warmly, don't recite the rule"), route all
  goodwill into zero-cost levers (membership hold, nationwide access), close on
  service not the dispute, cite the policy URL for the paper trail.
- **When the site fact is conflicting or unverifiable, FLAG it — never invent.**
  Two live cases: (a) Cottage Lake Pool's page gave two different open dates (a
  banner said July 4, the FAQ said June 20) — write around it with the consistent
  fact ("open through August 30") and flag the conflict to Tanzim, don't pick one
  silently. (b) Kent's class schedule renders live/day-by-day — quoting fixed
  days/times risks being wrong by the time the customer reads it, so point the
  customer to the live filtered schedule URL and offer to pull current options,
  rather than fabricating a weekly timetable. Fabricated specifics fail the
  grading worse than an honest "here's the live source." Always surface the flag
  to Tanzim in your reply-after-draft note.

## 6. Candid career / strategy coaching (when invited)

Around interviews he often shifts to big-picture: "where am I wrong," "top 3
weaknesses," "what should I study," "who should I follow." He wants the REAL
read, not validation. Deliver decisively — pick ONE answer, don't hand him a
menu of options. Standing context that recurs (verify against current memory,
don't treat as frozen):

- **His core pattern: breadth as avoidance.** Starts many things (projects,
  applications), stalls at depth/finishing because finishing invites judgment.
  Procrastination here is risk-avoidance, not laziness. The fix is mechanical,
  not motivational: one project, one hard deadline, shipped ugly.
- **His leverage: closing fast under pressure.** He arrives sharp in live, human,
  high-stakes rooms. Point him at conversations that convert, not funnel volume.
- **His direction:** wants out of employment, ~$5k cashflow from
  digital/product (NOT sales — he hates sales), two deep SMEs + generalist
  breadth, and to be CEO of TIMBR (fitness-AI; "Apple of fitness"). The
  decisive call given to him: deep on (1) Applied AI / agentic systems and
  (2) consumer subscription economics; product is the master, AI is the weapon;
  PMP is a loop to CLOSE and a job-market hedge, NOT a thing to centre; trading
  stays "study," not an SME (it's his seductive rabbit hole). Don't let PM
  become the safe identity he hides in.
- **Reward/accountability mechanism that worked:** he set a Saturday EOD ship
  deadline for the magazine+website; Friday created a one-shot cron to check him
  on it and gated a "reward" (a Titan distillation) behind shipping. Use
  deadline-check crons + earned rewards to fight the stall. Don't soften the
  check-in.
- **Don't feed the procrastination.** When he asks "should I read X now?" and
  there's an overdue ship, say no — reading is comfortable fake-progress.
  Make the book/study the reward AFTER shipping.

### Coaching register
Short, decisive, warm-but-honest. He asked for "describe me truly" / "in 2
sentences" / "officially" — match the framing he requests (résumé version vs the
real human read) and don't pad. When he wants depth he'll say so.
