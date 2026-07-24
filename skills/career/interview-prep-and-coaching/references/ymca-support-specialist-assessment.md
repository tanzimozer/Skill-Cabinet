# YMCA Lead Membership Support Specialist — 2nd-round written assessment

Recruiter: **Dani (Danielle) Hastings** <dhastings@seattleymca.org>, Program
Executive: Membership Operations, YMCA of Greater Seattle. Sent July 2 2026,
due **Monday July 6, 12:00pm**. Attachment:
`Second Round Interview- Membership Support Specialist.docx` — four mock customer
emails, respond as YMCA staff. Graded on website navigation + customer-service
approach.

## Pull the attachment from Gmail (script)

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
creds = Credentials.from_authorized_user_file("/home/hermes/.hermes/google_token.json")
# refresh if expired -> creds.refresh(Request()); rewrite token
svc = build("gmail","v1",credentials=creds)
res = svc.users().messages().list(userId="me",
        q='from:dhastings subject:"Second Interview"', maxResults=5).execute()
mid = res["messages"][0]["id"]
full = svc.users().messages().get(userId="me", id=mid, format="full").execute()
# recurse payload parts; part["filename"] set + part["body"]["attachmentId"] present
att = svc.users().messages().attachments().get(
        userId="me", messageId=mid, id=aid).execute()
open("out.docx","wb").write(base64.urlsafe_b64decode(att["data"]))
```
Parse: `from docx import Document; [p.text for p in Document("out.docx").paragraphs]`

## The four scenarios
1. **John Doe — "UNFAIR CHARGES!!!"** — disputing $91 adult membership, was out of
   town, threatens BBB + small claims. De-escalation + hold-policy scenario.
2. **Jane Doe — Birthday Parties** — Big Splash vs Jump Around, guest count,
   duration/extra time, price, cancellation, decorations.
3. **Amy Adams — Swim Lessons** — Stage 3→4 transfer/cancellation policy, outdoor
   pool name + hours, lessons/rec swim there, member day-pass Q, solo swim test.
4. **Jamie Jones — Schedule Help (Kent YMCA)** — member cost for water aerobics/
   yoga/Pilates, days/times, beginner class recommendations.

## Source-of-truth URLs (verified this session)
- Membership rates: `https://www.seattleymca.org/membership`
  — Individual $91/mo, Household $154/mo, join fee $79. (John's $91 = legit
  Individual dues.)
- **Cancellation/Refund/Hold policy** (cite this to John):
  `https://www.seattleymca.org/support/policies/cancellation-refund-hold-temporary-facility-closure-policy`
  Key rules: dues NOT prorated for holds/cancels; hold/cancel needs written
  webform notice 14 days before the 1st; <14 days notice drafts one more time;
  memberships don't auto-cancel for inactivity; 30-day satisfaction guarantee for
  NEW members; dispute window 60 days only if Y failed to process a hold/cancel.
- Hold/cancel webform: `/support/webform-membership-hold-cancellation`
- Birthday parties (full FAQ): `https://www.seattleymca.org/programs/youth-family/birthday-parties`
  — up to 15 kids ($15/extra), 90min (45 activity + 45 room), Big Splash +30min
  pool transition, add 30min for $50, from $275 members, $100 non-refundable
  deposit, 14-day/48-hr cancel tiers, code **Birthday50** = $50 off (July booking,
  events through Oct). NOT offered at Downtown or University Family YMCA.
- Nationwide membership (the "2,600+ Ys" claim source, verified verbatim:
  "more than 2,600 Ys across the United States (including Puerto Rico) at no
  additional cost"): `https://www.seattleymca.org/membership/benefits/nationwide-benefits`
  Internal caveat (do NOT need to put in John's reply): nationwide access requires
  50%+ of monthly visits at the home Y.
- **Swim lessons** (Amy scenario): `https://www.seattleymca.org/programs/swim/lessons`
  — 8 stages, group/semi-private/private. Transfers follow the SAME timing as
  the program cancellation policy: 14+ days before first meeting = full refund/free
  transfer; 14 days–48 hrs = account credit valid 90 days; <48 hrs = nothing.
- **Cottage Lake Pool** (the outdoor pool, Amy scenario):
  `https://www.seattleymca.org/programs/swim/outdoor-pools/cottage-lake-pool`
  — 18831 NE Woodinville Duvall Rd, Woodinville; operated by Northshore YMCA; one
  of the only outdoor pools in King County; 3 lanes, water slide, 84°F. Hours
  8am–8pm daily. **Open-date CONFLICT on the page:** banner says July 4, FAQ says
  June 20 — both agree close is Aug 30. Lap swim / water walking / rec swim =
  included for members, $8 for community members, reservations required (open 48
  hrs ahead). **Swim test** (13 & under, to swim without an adult in arm's reach):
  deep-water plunge (head fully under) + swim 25 yds without stopping + 30-sec
  tread/float.
- **Group fitness / classes** (Jamie scenario, Kent YMCA):
  `https://www.seattleymca.org/programs/health-fitness/group-exercise` — water
  aerobics, yoga, mat Pilates all INCLUDED in membership, unlimited, no extra
  fee ("only members have unlimited, exclusive access"). Exception: reformer
  Pilates is a separate specialty class with a fee.
  Live Kent schedule: `https://www.seattleymca.org/schedules/kent-ymca` (filter by
  Group Fitness / Yoga; real category names are "Water Fitness" + "Mind Body").
  Schedule is day-by-day/live and returns 0 results for forward weekday dates — do
  NOT quote fixed weekly times; point the customer to the filtered URL. Beginner
  recs to surface: water aerobics (low-impact/buoyancy), gentle/beginner yoga,
  cycling (low-impact cardio). **AOA classes are 55+ ONLY** ("ideal for ages 55+")
  — do NOT recommend to a general returning exerciser; swap for cycling.
- **Personalized Wellness Plan** (free member benefit, Jamie's retention hook):
  `https://www.seattleymca.org/membership/benefits/personalized-wellness-plan`
  — free annual 30-min session with a Y wellness coach; individualised plan +
  class/equipment recommendations. Perfect for a returning member.
- **Personal & specialty training** (the PAID upsell, Jamie): 
  `https://www.seattleymca.org/programs/health-fitness/personal-training-programs`
  — member rates $73/60min, $43/30min; partner $102/60min; small group (3–8);
  reformer Pilates is a specialty option here. Referral path = **Healthy Living
  team / Healthy Living Director** at the local Y.

## Fetch pattern for the site
`urllib.request` with `User-Agent: Mozilla/5.0`; catch `HTTPError` and still read
`e.read()` (the 404 fallback page carries useful JS-rendered blocks like the
nationwide claim, AND its footer/nav dumps the canonical link map — hit a
deliberate bad URL to enumerate real page paths when a guessed URL 404s). Strip
`<script>/<style>` (DOTALL), regex `<[^>]+>` -> space, `html.unescape`. Some
pages redirect; live schedule data is JS-only (browser snapshot + tick the
category checkboxes to read it).

## Upsell / value-add mapping (Jamie — the technique that worked)
When a scenario is a warm lead (returning member wanting guidance), map what the
employer offers in TWO tiers before drafting:
- **Free retention hook FIRST** (lead with this — pure customer care, keeps them
  sticky): here the Personalized Wellness Plan.
- **Paid upsells SECOND** (genuine value, also revenue): reformer Pilates,
  personal training, small-group training.
This is the exact instinct a membership-support role is tested for: helpful AND
revenue-aware.

### CRITICAL correction — stay in your lane (membership support ≠ seller)
Tanzim's explicit note: "I don't want to be the trainer, I'm membership support —
I want to CONNECT the member to the department who can best help." Reframe EVERY
upsell as a warm handoff, not a self-pitch. "I'll point you to the right trainer"
→ "I can connect you with the **Healthy Living team** at Kent." The role routes;
another department closes. Apply this to any support-desk persona: recommend the
benefit, then offer to connect them to the owning team.

## Finalised drafts
John: empathy → explain access-not-usage → policy URL → offer membership hold →
nationwide access → close on service. Signed "Tanzim Ozer, Membership Support".
Jane: warm 2-sentence intro → prose describe Big Splash/Jump Around → bulleted
`Guests / Length & extra time / Cost / Cancellation / Decorations` → booking link.
(This hybrid warm-intro-then-bullets format is his confirmed preference.)
Amy: warm intro → prose transfer-timing explanation with 3 tiers as FULL-SENTENCE
bullets → prose on Cottage Lake pool (write "open through August 30", flag the
date conflict to Tanzim not the customer) → member-cost prose → swim test as
3-part bulleted list. Bullets written as complete explanatory sentences, not
fragments (his final refinement — "bullets but in a clearly explained sentence").
Jamie (iterated to final this session): cost-included prose (flag reformer
Pilates exception) → live Kent schedule URL, DON'T fabricate weekly times → free
PWP as retention hook → beginner recs (water aerobics, beginner yoga, cycling —
NOT AOA) → offer to connect to Healthy Living team for structured training.
Same warm-intro + Amy-style tone.

## Final QA pass on a compiled submission (he sends back a PDF)
He compiled all four replies into `YMCA_-_Email_Replies__Tanzim_Ozer_.pdf` and
asked to fact-check + attach source links. Workflow:
1. Parse the PDF back with `pdfplumber` (`pdf.pages` → `extract_text()`), don't
   trust that it matches the drafts — read what he actually shipped.
2. Re-verify EVERY factual claim against its source page (don't assume; this
   session the nationwide "2,600+" line was only confirmed verbatim on the final
   pass). Produce a per-email audit with ✓/correction.
3. **Attach a verified source-of-truth URL to EVERY email** — he explicitly wants
   each reply to carry its links. Place them as a labelled block before the
   sign-off (e.g. "Membership policy: <url>\nNationwide access: <url>").
4. Flag polish nits: PDF text-extraction wraps long URLs across line breaks
   (confirm the hyperlink is live, not broken text); proper-noun casing drift
   ("pilates" → "Pilates"); semicolon-vs-colon in his "Following are the details;".

## Tone loop to SKIP next time (hard-won, ~6 iterations on Jane)
Fluffy/warm-padded → REJECTED ("too much fluff"). All-tight-bullets → REJECTED
("too tight", "hated this"). Cold bullet-blast → REJECTED. Endpoint = warm human
prose intro + bulleted sections where each bullet is a FULL SENTENCE + warm close
+ source URL. Start there, don't rebuild the loop. He also routinely asks "give me
the source of truth" per paragraph — keep the URL list live as you draft.
