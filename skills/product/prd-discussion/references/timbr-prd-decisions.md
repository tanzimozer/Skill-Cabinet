# Timbr PRD — Q1–Q47 Resolution Log (2026-05-31)

## Resolved

| Q# | Question | Answer |
|---|---|---|
| Q2 | Password reset method | Email link (NOT OTP — original "yes" was ambiguous) |
| Q11 | Assessment mandatory before app access? | Done by trainer only |
| Q12 | Assessment editable after submission? | Trainer only |
| Q13 | Trainer notified when client completes assessment? | Not applicable |
| Q14 | No workout assigned today — what does client see? | Rest tips + nutrition plan + upcoming plan |
| Q15 | Can client see upcoming days? | Yes — full week plan visible |
| Q16 | Rest day — who marks it? | Client configures in settings or marks on home screen; workout session skipped to next day |
| Q17 | No video for exercise — fallback? | Exercise not shown at all |
| Q18 | Form cues format? | Same as Q17 — no video = exercise hidden |
| Q19 | Exercise library — shared or private? | Shared across all trainers |
| Q21 | Workout complete — auto or manual? | Manual End Workout button (confirmed in wearable design discussion) |
| Q24 | Fibre tracked as macro? | Yes |
| Q25 | How often can trainer update nutrition targets? | Anytime |
| Q30 | Chat — voice notes or text+photos? | Text, photos, videos only (basic 1:1 with trainer) |
| Q32 | Message history retention? | 30 days |
| Q33 | Read receipts? | Not required |
| Q34 | Unified trainer inbox? | Yes |
| Q36 | Workout reminder time — who sets it? | Client sets it |
| Q37 | Can client control which notifications? | No |
| Q38 | Deep link on notification tap? | Yes |
| Q39 | Workout history retention? | Calendar/streak view only (like streaks on calendar) |
| Q40 | Filterable/searchable? | No (streak calendar only) |
| Q41 | Export? | No |
| Q42 | Stripe Connect for trainer payouts? | Confirmed |
| Q43 | Session "consumed" marking? | Removed — not in product anymore |
| Q44 | Client dispute "consumed" mark? | Email support@timbr.com |
| Q45 | Bundle discount? | Trainer decides — creates one-time or recurring payment request |
| Q46 | Price change mid-bundle? | Not applicable |

## Still Open (as of 2026-05-31)

| Q# | Question | Status |
|---|---|---|
| Q1 | Same email across Apple + Google — merge or error? | Resolved as "doesn't matter" |
| Q5 | Client without trainer link — account state? | TBD — falls under Solo tier decision |
| Q9 | Client with inactive trainer — partial access? | TBD — direction given (show existing, no new) but not locked |
| Q20 | Skipped exercise — mark as skipped or unchecked? | Open |
| Q22 | Can client retroactively log missed workout? | Open |
| Q23 | Trainer notified on workout completion? | Open |
| Q26–29 | Food logger — in MVP or out? | Decision deferred |
| Q31 | Messaging infrastructure — Stream/Sendbird/Twilio? | Not picked |
| Q35 | Push service — Firebase + APNs? | Not confirmed |
| Q47 | Online session setup and pricing? | TBC |

## Design Decisions from Extended Discussion

**Wearable architecture:**
- Wearable = session biometrics layer (HR, calories, duration)
- Swipe cards = prescription compliance layer (exercise, weight, reps)
- Neither replaces the other — both required
- Wearable-only sessions valid; skipped exercises = SKIPPED not null
- End Workout is always manual; modal shows "X of N done" as soft nudge only

**Rep-counting landscape (as of May 2026):**
- PUSH Band 2.0 — best accuracy, $200, barbell clip-on, niche/pro sports only
- Apple Watch — best at scale, watchOS 9+ counts reps for ~10 simple bilateral exercises
- Garmin — has it, lags Apple on accuracy and exercise variety
- Whoop/Oura — no rep counting at all
- Nobody has cracked auto exercise ID + rep counting for compound lifts reliably at scale
- Seattle gym-goer wearable ownership: ~60–65%; active use during strength sessions: ~40–50%

**Best proxy for missing exercise data:** Historical pre-fill from last session (plan engine outputs prescriptions, sliders pre-loaded from last session values, user confirms or adjusts)

**Program vs progression:**
- Program = mesocycle (3–6 week block, defined by split + phase + periodisation model)
- Exercise swap within program = progression event (NOT a new program)
- New program = structural intent changes (split, phase, or periodisation model)
- Skipped exercises by preference → auto-sub equivalent next program; never repeat the avoided exercise
