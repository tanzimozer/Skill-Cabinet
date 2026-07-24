# Timbr PRD — Resolved Decisions Register
Session: 2026-05-31 | Source PRD: timbr-product-requirements.md v1.4

## Resolved (from bulk Q&A + discussion)

| # | Question | Decision |
|---|---|---|
| Q2 | Password reset method | Email link (not OTP) |
| Q4 | Session expiry | Industry standard (follow other apps) |
| Q6 | Invite code validity | One-time invite to download app; shows pre-filled assessment + workout created by trainer |
| Q7 | Trainer:client ratio | One trainer per client; trainer has multiple clients |
| Q10 | Unlink mechanism | Both can unlink. Client = cancel trainer payment. Trainer = mark client inactive (stops progress updates) |
| Q11 | Assessment — mandatory? | Done by trainer, not client |
| Q12 | Assessment — editable by? | Trainer only |
| Q13 | Trainer notified on assessment? | Not applicable |
| Q14 | No workout today | Show rest tips + nutrition plan + upcoming plan |
| Q15 | Upcoming days visible? | Yes — full week workout plan visible |
| Q16 | Rest day | Client-configurable in settings or can mark on home screen; workout session skipped to next day |
| Q17/18 | No video for exercise | Exercise not shown (hidden entirely) |
| Q19 | Exercise library | Shared across all trainers |
| Q21 | Workout complete trigger | Manual End Workout button (not auto-complete) — confirmed in discussion |
| Q24 | Fibre tracked? | Yes |
| Q25 | Nutrition target update freq | Trainer can update anytime |
| Q30 | Chat media types | Text, photos, videos (basic 1:1 with trainer) |
| Q32 | Message history | 30 days |
| Q33 | Read receipts | Not required |
| Q34 | Unified trainer inbox | Yes |
| Q36 | Workout reminder time | Client-set |
| Q37 | Client notification control | No — all notifications on, no client control |
| Q38 | Deep link on tap | Yes |
| Q39–41 | Workout history | Calendar streaks only (like Duolingo streaks), no detail view, no export |
| Q42 | Stripe Connect | Confirmed |
| Q43 | Session consumption | Removed — no longer applicable |
| Q44 | Dispute resolution | Client emails support@timbr.com |
| Q45 | Payment model | Trainer creates and sends one-time OR recurring payment notification |

## Still open (as of end of session)

| # | Question | Status |
|---|---|---|
| Q5 | Client without trainer: account state | Falls under Solo tier — TBD |
| Q9 | Client with inactive trainer: UX | Falls under Solo tier — TBD |
| Q20 | Skipped exercise: mark as skipped or unchecked? | Open |
| Q22 | Retroactive logging | Open |
| Q23 | Trainer notified on workout completion | Open |
| Q26–29 | Food logger | In MVP or out — not decided |
| Q31 | Chat infrastructure | Stream / Sendbird / Twilio — not picked |
| Q35 | Push service | Firebase + APNs — not confirmed |
| Q47 | Online session setup | TBC |

## Key design decisions from discussion (not in formal Q list)

- Wearable enriches, never gates — confirmed as core principle
- Skipped exercises recorded as SKIPPED (not null) — signal for trainer
- End Workout = manual submit; modal shows "X of N done" as soft nudge only (not a gate)
- Wearable-only sessions valid; swipe cards ALWAYS required for prescription compliance
- Wearable data = session biometrics; swipe cards = exercise compliance — two separate data layers
- Per-exercise tracking IS the core value prop — without it, plan engine has nothing to adapt from
- Rep-counting wearable tech not reliable enough at scale; Apple Watch best at consumer scale but still falls short for compound lifts
- Seattle wearable ownership: ~45–55% general, ~60–65% gym-goers; active use during strength ~40–50%

## Program/mesocycle decisions (from discussion)

- "New program" = mesocycle (3–6 week block with specific milestone) — NOT exercise-level changes
- Exercise swap within program = progression event, not new program
- Plan engine: exercise-by-exercise audit at block end; generates draft + reasoning card for trainer
- Skipped exercises (preference): carry intent forward with equivalent substitution, not same exercise
- Trainer reviews and approves before publishing to client
