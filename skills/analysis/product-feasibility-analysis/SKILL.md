---
name: product-feasibility-analysis
description: "Run a feasibility / go-no-go analysis on a product or venture idea for Tanzim (e.g. 'is building a tool for fitness trainers worth it?'). Covers the four-gate demand→sizing→product→verdict math, the one-question-at-a-time intake that builds toward a stakeholder report, and how to handle an unvalidated wedge."
version: 1.0.0
tags: [analysis, feasibility, market-validation, product, business, tanzim]
related_skills: [deep-questioning-facilitation, decision-framework-design]
---

# Product / Venture Feasibility Analysis

Tanzim brings idea-validation questions: *"How do we work out if building X is worth it? We need to know if there's real demand, how big it is, what it looks like, and whether it's worth pursuing — a feasibility test."* This is recurring (Timbr / trainer-tool was the first). The deliverable is usually a **report to present to stakeholders** (e.g. Sagar, Maureen), built up through a structured intake, not a one-shot essay.

This is NOT `deep-questioning-facilitation` — that maps his psyche. This maps a *market*. It IS one-question-at-a-time like that skill, but the questions are about user/pain/price/competition, and the output is a feasibility verdict.

## The four-gate framework (the actual math)

Pass each gate before spending real money on the next. Present it as gates, not a flat checklist — the point is *kill early, kill cheap*.

**Gate 1 — Does demand exist? (existence)**
- Count the market: how many of the target user in the target geography. (e.g. ~340k personal trainers in the US.)
- Look for proof people already pay to solve this: existing competitors charging money = demand confirmed. Zero competitors = either no market or you're early (risky), not "open field."
- **Talk to 10–15 real target users.** If they can't name the pain unprompted, there's no demand. This gate kills most ideas for free — do it before any spreadsheet.

**Gate 2 — How big is it? (sizing — TAM/SAM/SOM)**
- **TAM** = total users × annual price (e.g. 340k × $300/yr ≈ $100M).
- **SAM** = the slice you can actually serve (niche/region/segment).
- **SOM** = realistic 1–3 yr capture, usually **1–5% of SAM**. That's the real revenue ceiling.

**Gate 3 — What does it look like? (the product)**
- Name the *one* job it does better than incumbents. No sharp wedge → don't build.
- MVP scope = smallest thing a user would pay for. Sketch the 3 core screens.

**Gate 4 — Is it worth it? (the verdict)**
- **Cost** = build + 12-mo run, *including his own time at a real hourly rate*.
- **Revenue** = SOM customers × price × retention.
- **Rules of thumb:** payback under ~18 months; **LTV:CAC ≥ 3:1** (lifetime value of a customer ≥ 3× cost to acquire one). Below either → it's a hobby, not a business.

## Intake style: one question at a time, building to a report

When he says "ask me one question at a time, then we'll create a report" — run it like a structured interview:
- **One question per turn, labelled "Question N of ~10."** Same hard rule as deep-questioning: never batch, never preview.
- **Log each answer back in one tight line** before the next question, so the report writes itself.
- Question order that works: (1) primary user — be specific, (2) the single biggest pain, (3) wedge/pain-ranking, (4) price intuition, (5) current tools/competitors, (6) willingness to switch, (7) acquisition channel, (8) build cost/time, (9) success metric, (10) deal-breakers.
- Plan to assemble the logged answers into a report for the named stakeholders at the end — tell him that's where it's heading.

## Back claims with real numbers, flag what you can't verify

When he gives a figure (e.g. "5 hrs/week unpaid admin"), don't just accept it — *back it with industry data* and say plainly which numbers you'd verify before the report ships. Cite ranges (trainer admin = 40–60% of hours; program design 3–8 hrs/wk pre-AI; median pay $25–40/hr → quantify the loss as $/wk and $/yr). Concise, not a literature review. If the browser/search is down, give the established figures and explicitly mark them "verify before report."

### BLS excludes self-employed — the market-sizing trap that bites this venture

BLS occupation **39-9031 (Exercise Trainers & Group Fitness Instructors)** is the anchor for US/metro trainer counts, BUT **OEWS employment figures cover wage-and-salary jobs only — self-employed / 1099 contractors are excluded.** For the TIMBR thesis that is fatal to a naïve read: independent trainers are *precisely* the target, and they're the ones NOT in the count. So:
- The BLS metro number (Seattle-Tacoma-Bellevue ≈ 4,000–5,000 for 39-9031) frames the *employed* market, not the independent pool.
- Any "independent trainer count" derived by taking a % of the BLS number **understates** the real independent population.
- National 39-9031 ≈ 340k–360k (employed); US PT *industry revenue* ≈ $12–14B/yr (IBISWorld/IHRSA order).
- **The move:** frame BLS as the market-size anchor, but treat Tanzim's own trainer outreach (the 17-trainer list) as the ground-truth for the independent count — his primary data beats the national dataset for exactly the segment BLS misses. State this caveat inline in the report.

### When web sources are bot-walled — the fallback ladder

Live market-data lookups get blocked constantly (Google search, BLS.gov, DuckDuckGo HTML, jina reader, direct `curl` with UA — all returned 403/captcha in the Jul-2026 run). Don't burn ten calls hammering a walled source. Escalate in this order:
1. **Bing** (`curl` to `bing.com/search`) — usually returns HTTP 200, but snippets are JS-rendered so text extraction is thin.
2. **Marginalia** (`marginalia-search.com/search?query=`) — non-JS, renders real result text and links in the snapshot; good for finding the authoritative PDF/source URL.
3. **BLS public data API** (`api.bls.gov/publicAPI/v2/timeseries/data/`, POST JSON with `seriesid`) — returns JSON, no captcha, but **metro OEWS series return empty rows without a registered API key**; national series are more reliable.
4. **State labor dept** (e.g. WA ESD) — regional occupational wage estimates, often as downloadable PDFs surfaced via Marginalia.
5. If all walled: give BLS-anchored ranges from established knowledge, mark them "modelled / verify before report," and move on. Do not present a blocked lookup as a dead end — deliver the ranged estimate with the caveat.

## The most important pattern: "I don't know" = the wedge, and it comes from customers

When he can't answer the core wedge question ("which pain is biggest?") — **that "I don't know" is the finding, not a failure.** Do NOT invent the wedge from your chair, and don't let him invent it either. The ranking must come from the target users themselves.

- Name it directly: guessing the wedge is how products get built that nobody wants.
- Offer two paths: (a) **best** — gather it via the user interviews/survey he was already on the hook for; (b) **shortcut for the report now** — log the wedge as "unvalidated; top candidates are X/Y/Z" and flag it as the #1 open risk for stakeholders.
- Watch for the **AI-commoditised pain trap**: if GPT/tooling already solves part of the pain (e.g. program-writing), that slice is no longer a wedge. The durable wedge is the admin GPT *doesn't* touch (payment chasing, retention/check-ins, progress tracking, cross-gym scheduling). Steer him off the commoditised slice.

## Survey-as-data-collection (Google Forms)

When the wedge needs validation, the move is a Google Form survey — email-required, open to anyone with the link — to collect the customer answers that resolve Gate 1/3.
- **Forms API gotcha:** the Forms API is often *disabled* in the project AND the OAuth token usually lacks the `forms.body` scope (Drive/Sheets access does NOT cover writing form questions). Both need the user in the Google console — see `google-oauth-refresh` / `gmail-automation` credential skills. Don't promise a form you can't yet write; check `forms().create()` actually succeeds first.
- Faster fallbacks if console access is blocked: build a Sheets-backed form with existing Sheets scope, or draft the full question set for him to paste into a blank Form in 5 minutes.
- Draft the question set while waiting on access so it's ready to publish the second auth clears.

## The model can pivot mid-intake — rewrite the math live

Don't assume the revenue model is fixed once stated. In the Timbr run Tanzim flipped it mid-questioning: trainer-pays-$50 → **client pays $25, Timbr keeps the full cut**. That makes it **B2B2C — the trainer is the distribution channel, not the payer**: one trainer brings their whole roster (15–30 seats), so a trainer signup is worth 15–30 paying clients, not one. When the model changes: recompute unit economics immediately, say so plainly, and note that the **key risk moves too** (from "will the user pay" to "will the channel adopt + will the end-customer pay"). Watch for the wedge to surface here — in Timbr the marketplace/discovery angle (fitness-only Uber/Yelp map, zero marketing cost) turned out to BE the answer to the earlier "I don't know" wedge.

## Decompose a big target — the Map and the Mountain

When the success metric is a large number (e.g. 5,000 clients), don't just state it — break it down two ways:
- **The Map** — a real table of the key lever. For channel-driven models: trainers × clients-per-trainer → total → monthly → annual, 2–3 rows so the lever is visible. Push the ratio (15→20 clients/trainer) and show revenue jump with the same headcount.
- **The Mountain** — brutally honest reality of hitting it. Convert the end-target into the *recruitment* target (5,000 ÷ ~20 ≈ 250 trainers), size it against the real market (Seattle ≈ 3–4k trainers → 250 = ~7% of the whole pool), and state plainly where the actual risk sits (recruitment execution, not capital). List the 3–4 things that must be true.

## Reframe the model around a single North Star metric — work backwards

Tanzim will often pivot the whole model to anchor on **one headline number** (in the Timbr run: *"compute everything on $100K ARR, work backwards, everything aligned to that metric"*). When he does this, restructure the doc so the North Star leads and every section serves it:
- **Put the North Star first** — a top "Section 0" that states the goal, the per-unit basis, and the arithmetic to the target. Everything below references it.
- **Work backwards, not forwards.** Don't lead with "how many trainers do we need" — lead with the revenue target and derive the client/trainer count from it. $100K ARR ÷ ($20/client/mo × 12 = $240/yr) = **417 clients**.
- **Add a buffer and round to a working target.** He asked for 417 → **450 clients** (safety margin). Use the buffered number as the operative target everywhere; note the raw number too.
- **Translate to the lever last.** 450 clients ÷ 20 clients/trainer ≈ **23 trainers**. The trainer count is an *output* of the North Star now, not the input.
- **Recompute margin basis, not gross price.** If TIMBR nets $20 of a $25 sub (the rest is a trainer incentive / buffer), ALL ARR math runs on the **$20 net**, never the $25 gross. Sweep any prior $25-based figures and mark them superseded.

## Churn-adjusted onboarding — the "defended position" math

A revenue target is not a finish line; churn erodes it every month. When a churn rate is given (Timbr modelled **4%/month**), always compute the maintenance load:
- **Monthly loss** = base × churn rate. 450 × 4% = **18 clients lost/month**.
- **Replacement to stand still** = onboard that many every month, indefinitely, just to hold the number.
- **Annualised attrition** = 1 − (1 − monthly)^12. 4%/mo compounds to **~39%/yr** — nearly half the book rebuilt yearly.
- **Gross-adds formula:** required monthly onboarding = net-growth-target + (churn% × current base). The drag grows with the base, so the engine must accelerate, not coast. To climb to 450 in year one *and* cover churn, target ~30–35 adds/mo during ramp; ~18/mo at steady state just to hold.
- **The highest-leverage lever is lowering churn, not raising onboarding.** Cutting 4%→2%/mo halves the maintenance load (18→9/mo). State this — it reframes where effort should go.
- **The framing line that lands:** "$100K ARR is a defended position, not a finish line — the onboarding machine must out-run churn permanently." This points straight back at the switching-cost moat as the real weapon.

## Fee-bearer & switching-cost design (B2B2C plumbing)

Two design conversations recur once the model is B2B2C-with-client-paying:
- **Who bears the transaction fee?** Charging the *trainer* any cost blocks early adoption — trainers won't take on cost to join an unproven tool. Cleanest resolution: **client bears the processor fee** (~2.9% Square / ~2% Visa-MC) as a visible service-fee line *on top of* the subscription (e.g. $25 → ~$25.73). Trainer bears nothing, TIMBR bears nothing, price integrity of the headline number preserved. Flag the open items: client willingness to pay a visible surcharge, and state-level credit-card surcharging legality (WA).
- **Switching cost — carrot, not punishment.** When Tanzim proposes a lock-in lever (he floated *data-loss on exit* vs a *$5–9 re-onboarding fee*), steer him off punishment mechanisms:
  - **Data-loss on exit is a trap** — it punishes churn instead of preventing it, breeds distrust, and (critically) **kills win-backs**, which at high churn are half of growth. Never destroy client history.
  - **A small re-onboarding fee ($5–9) is fine as friction**, but reframe it as a *carrot*: "stay and your history stays live; lapse and coming back costs $X to re-set up." Same lever, framed as continuity-retained rather than data-destroyed.
  - **Don't overlap both** — fee + data-loss punishes twice and still kills the win-back.
  - **The real moat isn't the fee** — it's continuity: the client's data + the trainer relationship living on the platform. The fee is a nudge; continuity is the lock-in. This is the same "switching-cost moat" the churn math keeps pointing at.

## Report polish — Tanzim's standing format rules

- **Neutral, no names.** Never address the report to specific stakeholders in the body — he sends it to whoever he wants. Audience-agnostic.
- **Real tables, not ASCII.** Use an actual Docs `insertTable`, one figure per cell — never a monospace pipe-table in body text (it overlaps/leaves gaps).
- **One point per line, no wrapping.** "Row character count, five as buffer" = keep each line short enough not to wrap.
- Ship as a shareable Google Doc (anyone-with-link reader) and hand the link.

**Full worked example + reproduction detail:** see `references/timbr-feasibility-run-jun28-2026.md`.

## Cadence template per turn

```
[1 line logging his last answer as a report-ready fact]

**Question N of ~10.**

[One question. Be specific. Offer named options if the answer space is fuzzy.]
```

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| Jumping to "build it" before Gate 1 | Talk to 10–15 users first; it kills most ideas free |
| Presenting framework as a flat checklist | Frame as gates — kill early, kill cheap |
| Inventing the wedge when he says "I don't know" | That's the finding; get the ranking from customers |
| Treating an AI-solved pain as a wedge | Commoditised slice ≠ wedge; find the admin GPT doesn't touch |
| Accepting his stat unbacked | Back with industry ranges; flag what to verify |
| Batching intake questions | One at a time, labelled N of ~10, log each answer |
| Promising a Google Form before checking access | Forms API often disabled + token lacks forms.body scope |
| "Open field, no competitors" read | Usually means no market or too early — not a green light |
| Assuming the revenue model is locked | It can pivot mid-intake (B2B2C flip) — recompute the math live |
| Stating a big target without decomposing | Build the Map (lever table) + the Mountain (recruitment reality) |
| Naming stakeholders in the report | Keep it neutral — he sends it to whoever he wants |
| ASCII pipe-tables in the doc body | Use a real Docs insertTable, one figure per cell |
| Deriving independent-trainer count from BLS % | BLS 39-9031 excludes self-employed — understates the target; use his own outreach as ground-truth |
| Hammering a bot-walled source (Google/BLS/DDG) | Escalate the ladder: Bing → Marginalia → BLS API → state labor dept → ranged estimate w/ "verify" flag |
| Leading the model with "how many trainers" | Work backwards from the North Star: revenue target ÷ per-unit ARR = clients → trainers is the output |
| Running ARR on gross price when net is lower | If TIMBR nets $20 of a $25 sub, all math runs on $20; sweep prior $25 figures as superseded |
| Treating the revenue target as a finish line | It's a defended position — compute churn maintenance (base × churn%/mo) and the gross-adds formula |
| Optimising onboarding while ignoring churn | Lowering churn 4%→2% halves maintenance load — higher leverage than more onboarding |
| Charging the trainer any fee | Blocks adoption; client bears the processor fee as a visible on-top surcharge instead |
| Proposing data-loss as a lock-in lever | Punishment kills win-backs + breeds distrust; use a small re-onboarding fee framed as continuity-retained; the real moat is data+relationship continuity |

## See also
- `deep-questioning-facilitation` — the one-at-a-time intake cadence (psyche-mapping cousin)
- `decision-framework-design` — if the verdict needs to be codified into a scored model
- `gmail-automation` / `google-oauth-refresh` — Google API auth, scopes, and the console-enable gotchas the survey step hits
- `timbr-company-brief` / `timbr-context` — the trainer-tool venture this framework was first run on
