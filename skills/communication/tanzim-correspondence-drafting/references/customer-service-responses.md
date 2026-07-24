# Customer-Service Email Responses (grounded in verified policy)

A distinct sub-class of correspondence: replying to a customer/member complaint or
inquiry **as a staff member of an organisation**, where answers must be factually
correct per the org's published policy — not invented. Emerged from the YMCA of
Greater Seattle "Lead Membership Support Specialist" second-interview task (July 2026:
answer four customer emails using seattleymca.org).

## Golden rule: verify before you draft

Never invent policy, pricing, hours, or program details. Pull the real facts from the
org's website first, then write. For the YMCA task the authoritative pages were:
- Membership rates + terms: `/membership`
- Policies (cancellation/refund/hold): `/support/policies/cancellation-refund-hold-temporary-facility-closure-policy`
- Support webforms: `/support/webform-membership-hold-cancellation`
- Program detail pages under `/programs/...` (e.g. `/programs/youth-family/birthday-parties`)

Fetch technique that worked cleanly (no browser needed): plain `urllib` GET with a
`Mozilla/5.0` User-Agent, strip `<script>/<style>`, drop tags, unescape HTML entities,
then filter to lines >25–40 chars and dedupe. FAQ/policy pages render their full text
server-side, so this pulls everything. Guessing page URLs 404s — instead fetch the
hub/support page and regex `href="([^"]*(?:hold|cancel|birthday|party)[^"]*)"` to find
the real slug.

## The de-escalation / policy-hold play (when policy does NOT favour the customer)

Scenario shape: customer disputes a charge or asks for an exception the policy doesn't
grant (e.g. "I was out of town, remove my $91 membership dues"). Tanzim's framing,
which is the durable pattern:

1. **Find the policy first.** If it favours the customer, great — grant it.
2. **If it doesn't**, convey the terms *empathetically* — never quote the rule at them.
   - Explain the *why* warmly ("membership reserves your access whether or not you
     visit"), never the naked clause ("dues are not prorated — tough luck").
   - Don't admit fault or offer a refund the policy doesn't support.
3. **Route all goodwill into zero-cost offers** that retain the customer:
   - A hold/freeze option for the future (costs the org nothing).
   - Existing perks they're under-using (e.g. nationwide access to 2,600+ Ys).
   - Offer to set it up or walk them through it.
4. **Close on service, not on the dispute.**

Goal: customer feels helped and stays, the org concedes nothing it shouldn't.

## Format: keep it tight — bullets, not prose

Tanzim's standing length preference applies here too. First drafts that answer a
multi-part inquiry in full paragraphs draw a "too long" correction. Second pass:
compress to **labelled bullets** (one per question asked), keep a warm one-line opener
and a single next-step close. Every question the customer asked gets its own bullet so
nothing is dropped, but each answer is one line. This reads far better than paragraphs
for a multi-question reply.

## Signature

He signs these `Tanzim Ozer` / role line (e.g. "Membership Support — YMCA of Greater
Seattle") for the formal customer-facing version, or just `Tanzim` when tightened.
