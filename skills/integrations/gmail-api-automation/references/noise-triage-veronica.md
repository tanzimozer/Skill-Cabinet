# Noise triage ("Veronica") — heuristics & regexes

Tanzim's inbox-noise clearing protocol. Priority is **100% accuracy → KEEP when in doubt.**
Run from `execute_code` after the standard manual-token-refresh auth (see SKILL.md).

## Classification regexes (Jun 2026, validated on tanzim.seattle@gmail.com)

```python
import re

# PROTECT — never flag as noise. Job search is the live priority.
PROTECT = re.compile(r'(interview|recruit|hiring|application|applied|candidate|offer|'
    r'schedul|assessment|next step|opportunity|position|role|talent|onboard|'
    r'housingwire|wells fargo|allen institute|fluxx|amazon|foundation ai|webmd|'
    r'go2marine|jamie|sarah roncoroni)', re.I)

# NOISE senders — bulk/automated
NOISE_SENDER = re.compile(r'(noreply|no-reply|newsletter|notifications?@|updates?@|'
    r'marketing@|info@|hello@|team@|news@|digest|mailer|campaign|promo)', re.I)

# NOISE subjects — promo language
NOISE_SUBJ = re.compile(r'(sale|% off|deal|webinar|newsletter|unsubscribe|new arrival|'
    r'discount|coupon|flash|limited time|expires|don.t miss|trending|weekly digest|'
    r'daily digest|recommended for you|you might|tips|guide)', re.I)
```

## Bucketing logic
- PROTECT match → **keep**, full stop (check first, short-circuits everything).
- `List-Unsubscribe` present AND (promo label OR noise sender OR noise subject) → **high-confidence noise**.
- promo label (`CATEGORY_PROMOTIONS`/`CATEGORY_SOCIAL`) AND (noise sender OR noise subject) → **noise**.
- Everything else → **needs-review** (surface to Tanzim, never auto-act).

## Items that LOOK like job mail but ARE noise
- Indeed "send a quick message to <company>" nudges — marketing.
- "Welcome to <service>" account-marketing for unrelated signups (e.g. Free2move).
- Generic careers-marketing blasts ("Join a future-forward organization", ICF Careers).
- Workday "Thank You For Your Recent Submission" that is a marketing footer, not a real application reply — inspect snippet.

## Items inside the ambiguous pile that are ACTION-REQUIRED (never noise)
- "Additional Information Needed - <company>"
- "Follow up questions from <company>" (named human sender)
- "New Message from <recruiter name> - <role>"

## What Tanzim KEEPS during noise triage
- Plain "thank you for applying" / "application received" auto-acks — he reads these himself.
  (Contrast: the rejection-sweep DOES bin auto-acks. Noise triage does not.)
- Every recruiter, every real human, anything in his named pipeline.

## Quality pass (mandatory before delete)
Re-fetch each final candidate's metadata, re-run PROTECT against `From + Subject + snippet`,
print a per-item `NOISE-OK` / `HOLD-PROTECT` verdict line. Only `NOISE-OK` IDs get trashed.
Then `trash` (soft, 30-day recoverable), confirm trashed N/N + unread remaining.

## Run history
- Jun 2026: 121 unread → 6 dead-certain + 4 stragglers = 10 trashed, all cleared quality gate, zero job threads touched.
- Jun 2026 (hub-and-spoke body-verified): 84-candidate pool → 48 noise trashed, 36 protected. 121→54 unread.

## Body-level classifier (hub-and-spoke sweep — REQUIRED for rejection/receipt cleanup)
Subjects are unreliable; classify on the email BODY. Fetch `format=full`, strip `<...>`, collapse whitespace, lowercase, then:

```python
ACTION    = ['additional information needed','please complete','action required',
             'schedule your interview','schedule a time','please provide',
             'complete the assessment','next steps in your','book a time',
             'select a time','availability for']
INTERVIEW = ['interview','phone screen','congratulations','pleased to inform',
             'move forward with you','we would like to','excited to invite','offer']
RECEIPT   = ['received your application','thank you for applying','application confirmation',
             'thank you for your interest','received your resume','we have received',
             'application has been received','thanks for applying','will be reviewed',
             'reviewed by our']
REJECT    = ['do not meet','does not meet','not meet the minimum','not selected',
             'other candidates','will not be moving','not be moving forward',
             'pursuing other opportunit','position has been filled',
             'decided to move forward with other','no longer under consideration',
             'not be progressing','regret to inform','unfortunately']

# verdict: ACTION or (INTERVIEW and not REJECT) -> PROTECT
#          REJECT or RECEIPT -> NOISE
#          else -> PROTECT (default-safe)
```

## Subject-line traps (same subject, opposite meaning — body-verify!)
- "Thank you for your interest in <X>" → PG&E was a rejection; Stallion/WWT/Enhabit were receipts.
- "An update on your application from <X>" → rejection. BUT "Indeed Application: <role>" → apply-receipt, not a rejection.
- WWT appeared as BOTH a neutral receipt AND an "Additional Information Needed" (action-required) — never collapse a company to one verdict.

## batchDelete is unusable here
`messages/batchDelete` → HTTP 403 (token lacks full mail scope) and permanently deletes anyway. Loop per-message `/trash` instead.
