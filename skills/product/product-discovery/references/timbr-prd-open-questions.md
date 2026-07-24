# Timbr PRD — Open Questions Tracker

Source doc: TIMBR-PRD-QUIP.pdf (v0.2, 2026-05-30). Owner: Sagar.

## Resolved

| Q# | Question | Answer |
|----|----------|--------|
| Q1 | Same email across Apple + Google — merge or error? | Doesn't matter |
| Q2 | Password reset — email link or OTP? | **Email link** |
| Q3 | Email verification before app access? | Yes |
| Q4 | Session expiry? | Standard (follow industry norm) |
| Q6 | Invite code validity? | One-time invite to download; shows pre-filled assessment + workout created by trainer |
| Q7 | One trainer per client or multiple? | Trainer has multiple clients; client has one trainer |
| Q8 | Invalid/expired code — what does client see? | "Request invite code from trainer" page |
| Q11 | Assessment mandatory before app access? | Done by trainer, not client |
| Q12 | Assessment editable after submission? | Trainer only |
| Q13 | Trainer notified when client completes assessment? | Not applicable |
| Q14 | No workout assigned today — what does client see? | Rest tips, nutrition plan, upcoming plan |
| Q15 | Can client see upcoming days? | Yes — full weekly plan visible |
| Q16 | Rest day — trainer marks or empty? | Shown as rest day on screen; client can configure in settings or mark home screen; session skips to next day |
| Q17 | No video for exercise — fallback? | Don't show the exercise |
| Q18 | Form cues — plain text or structured? | (See Q17 — no video = no show) |
| Q19 | Exercise library — shared or private per trainer? | Shared across all trainers |
| Q21 | Workout complete — auto or manual submit? | **Manual — End Workout button, not auto-complete** |
| Q24 | Fibre as tracked macro? | Yes |
| Q25 | How often can trainer update nutrition targets? | Whenever they want |
| Q30 | Voice/video in chat — MVP? | Text, photos, videos only. Basic 1:1 with trainer |
| Q32 | Message history retention? | 30 days |
| Q33 | Read receipts? | Not required |
| Q34 | Unified trainer inbox? | Yes |
| Q36 | Workout reminder — who sets time? | Client |
| Q37 | Client controls which notifications? | No |
| Q38 | Deep link on notification tap? | Yes |
| Q39 | Workout history retention? | Streaks on calendar only, not detailed |
| Q40 | Filterable/searchable history? | No — calendar streaks only |
| Q41 | Export functionality? | No |
| Q42 | Stripe Connect confirmed? | Yes |
| Q43 | Session "consumed" mechanic? | Removed — no longer applicable |
| Q44 | Client dispute mechanism? | Email support@timbr.com |
| Q45 | Bundle discount? | Trainer's discretion — one-time or recurring payment request |
| Q46 | Price change mid-bundle? | Not applicable — trainer decides |

## Still Open

| Q# | Question | Notes |
|----|----------|-------|
| Q5 | Client without trainer link — account state? | Falls under solo tier — TBD |
| Q9 | Client with inactive trainer — what do they see? | Falls under solo tier — direction noted (existing plan, no new updates) but not locked |
| Q20 | Skipped exercise — mark as skipped or unchecked? | Open |
| Q22 | Retroactive logging of missed workout? | Open |
| Q23 | Trainer notified on workout completion? | Open |
| Q26–29 | Food logger — in MVP or cut entirely? | Decision pending |
| Q31 | Chat infrastructure — Stream, Sendbird, Twilio? | Not decided |
| Q35 | Push service — Firebase + APNs? | Not decided |
| Q47 | Online session setup and pricing | TBC |

## Design decisions made outside Q&A

- **Wearable-only sessions are valid.** Don't block End Workout if cards aren't completed. Record untouched exercises as SKIPPED. Confirmation modal shows "X of N done" as soft nudge only.
- **Swipe cards are always required** for prescription compliance. Wearable covers session biometrics only.
- **Smart pre-fill** from last session's values is the recommended proxy for weight/reps/sets.
