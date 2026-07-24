# Timbr Feasibility Run — Jun 28 2026 (worked example + new patterns)

The full Timbr trainer-tool run. Useful as a reproduction template and for the patterns that emerged beyond the base four-gate framework.

## The 10-question intake as it actually ran
1. **Primary user** → independent Seattle trainers, defined by profession not venue (split across 24 Hour Fitness, boutiques, apartment gyms, own space). Ownership irrelevant.
2. **Core pain** → ~5 hrs/week unpaid admin, every week, even post-GPT. Backed: trainers spend 40–60% of hours non-billable; ~$6.5–10k/yr unpaid labour; income ceiling at 20–30 clients.
3. **Wedge ranking** → "I don't know" → parked, to come from trainers via survey.
4. **Price intuition** → started $50/mo (from trainer).
5. **Competition/wedge** → not confident, found along the way.
6. **Demand sample** → founder + 1 other trainer, risk accepted deliberately (founder-as-user).
7. **Resources** → $15k from the CTO (active), Tanzim builds the database, production to a Bangladesh vendor (offshore-rated).
8. **Break-even** → reframed entirely by the model pivot (below).
9. **Revenue split** → Timbr keeps the FULL $25; trainer pays nothing, earns from sessions.
10. **Verdict line** → 5,000 paying clients at $25/mo.

## NEW PATTERN — the model can pivot mid-intake; rewrite the math live
Tanzim flipped the revenue model during questioning:
- **From** trainer pays $50/mo **to** client pays $25/mo, **Timbr keeps the full $25.**
- This makes it **B2B2C**: the trainer is NOT the payer — they're the **distribution channel**. One trainer brings their whole roster (15–30 clients), so one trainer signup = 15–30 paying seats, not one.
- Trainer's incentive becomes: free platform + all admin handled + **marketplace discovery** (a fitness-only Uber/Yelp map of verified trainers) that absorbs their marketing cost.
- **Action:** when the model changes, immediately recompute unit economics and say so plainly. The new key risk also moves — from "will the trainer pay" to "will the trainer push their clients onto it, and will clients pay $25."
- **The marketplace/discovery angle turned out to BE the answer to the earlier unvalidated wedge** (Q3/Q5). Discovery + zero marketing cost, not features. Note this back to him when it surfaces.

## NEW PATTERN — sensitivity table + "the mountain"
When the target is a big number (5,000 clients), don't just state it — decompose it:
- **The Map:** a real table of trainers × clients-per-trainer → total clients → monthly → annual. Show 2–3 rows so the lever is visible (e.g. 255×15 vs 255×20 vs 250×20). The clients-per-trainer ratio is usually the single biggest lever — push 15→20 and revenue jumps materially with the same headcount.
- **The Mountain:** a brutally honest recruitment-reality section. Convert the client target into the trainer-recruitment target (5,000 ÷ ~20 = ~250 trainers), then size it against the real market (Seattle ≈ 3–4k trainers → 255 = ~7% of the entire local pool). State plainly: capital is not the risk, recruitment execution is. List the 3–4 things that must be true (repeatable recruitment channel, trainer roster-adoption, client willingness-to-pay, marketplace carrot live early).
- Math worth keeping: 5,000 × $25 = $125k/mo = $1.5M/yr; payback on $15k is trivial → the $15k is seed, not the constraint.

## Report polish — Tanzim's standing corrections (apply by default)
- **Neutral, no names.** Don't address the report to specific people ("for Sagar, Maureen"). He sends it to whoever he wants. Make it audience-agnostic.
- **Real tables, not ASCII.** Use an actual Google Docs `insertTable` with one figure per cell — never a monospace pipe-table in body text. Watch for empty-cell/overlap artefacts.
- **One point per line.** No wrapping clutter; condensed, easy on the eye. He said: "do a row character count, put five as buffer." Translation: keep each line short enough not to wrap.
- Deliver as a shareable Google Doc (anyone-with-link reader) and hand the link.

## Forms-as-survey blocker hit this run
Forms API was disabled in project friday-mark-2 (`forms.googleapis.com` 403 "has not been used"), AND the token lacked `forms.body` scope. Both need Tanzim in the console. He took ~3 hrs to sort access; set a reminder and kept the intake moving rather than blocking. Draft the question set meanwhile.
