# Timbr MVP Checklist — Vendor Handoff
**Session:** May 2026 | **Scope:** Coached Tier Only (Solo + Timbr Scoring ruled out)

---

## Scope Corrections (override PRD)
- Solo tier → **RULED OUT** for MVP
- Timbr Scoring (Harmony, Fuel, Effort, Recharge sub-scores) → **RULED OUT** for MVP
- Gamification (XP, levels, streaks) → **RULED OUT** for MVP
- Wearable integration → **RULED OUT** for MVP
- AI program generation → **RULED OUT** for MVP (trainer builds manually)

---

## PRD-Answered Questions

### 1. Sign Up / Login
- Auth: Email + Apple + Google ✅
### 2. Trainer Linking
- Auto-link on code entry (creates TrainerClientRelationship) ✅
### 3. Initial Assessment
- Who fills it: Experience + Injuries = Client + Trainer; Body Type = Trainer; Lifestyle + Nutrition + Sleep = Client ✅
- Fields: Experience (1–9 scale), Body Type, Lifestyle (4 levels), Injuries (type + impact), Nutrition (calorie intake), Sleep (weekly score) ✅
- Trainer can trigger reassessment ✅
### 4. Daily Workout View
- Data structure: sets, reps, prescribed weight, rest periods ✅
### 5. Exercise Detail
- Video hosting: CDN/video host = P0 third-party integration ✅
### 6. Workout Logging
- Confirm/adjust prescribed weight per exercise ✅
- Private notes per exercise (Category D — AI never reads) ✅
### 7. Nutrition Plan View
- Macros tracked: protein, carbs, fat, calories ✅ (fibre not mentioned)
- Meal timing suggestions included ✅
- Client notified on nutrition plan change via push ✅
### 8. Food Logger
- Quick-add = recent meals + favourites (history-based) ✅
- Natural language input ("chicken and rice") ✅
- Running macro totals vs targets, real-time ✅
### 9. Trainer Chat
- Text + photos only ✅
- Real-time messaging (third-party infra, P1) ✅
- Push notification on new message ✅
- Broadcast messaging = V2+ only ✅
### 10. Push Notifications
- Triggers: workout reminders, trainer messages, program changes ✅
### 11. Workout History
- Data: past workouts, completion %, volume trends ✅
- Trainer sees client workout history ✅
### 12. Payments
- Client pays subscription ✅
- Bundle (8 sessions) + one-off both in MVP ✅
- 60-day session expiry ✅
- Timbr manages disputes ✅
- Payout options: instant / weekly / bi-weekly (trainer chooses) ✅
- Refund rules: trainer cancel = window extends; trainer no-show = session preserved; expiry = Timbr keeps money ✅
- USD only ✅

---

## Pending — Owner's Call (47 questions)

### Sign Up / Login
1. Same email across Apple + Google — merge or error?
2. Password reset — email link or OTP?
3. Email verification required before app access?
4. Session expiry — how long before re-login?
5. Client account without trainer link — allowed state? (Solo ruled out)

### Trainer Linking
6. Invite code validity period?
7. One trainer per client or multiple allowed?
8. Invalid/expired code — what does client see?
9. No trainer linked — locked app or partial access?
10. Can client unlink themselves, or trainer-only?

### Initial Assessment
11. Mandatory before accessing the app?
12. Editable after submission — by client, trainer, or both?
13. Trainer notified when client completes assessment?

### Daily Workout View
14. No workout assigned for today — what does client see?
15. Can client see upcoming days or today only?
16. Rest day — trainer marks it, or just empty day?

### Exercise Detail
17. No video uploaded for an exercise — fallback behaviour?
18. Form cues — plain text or structured?
19. Exercise library — shared across all trainers or private per trainer?

### Workout Logging
20. Skipped exercise — mark as skipped or just leave unchecked?
21. Workout complete — all checked = auto-complete, or manual submit?
22. Can client retroactively log a missed workout?
23. Trainer notified when client completes a workout?

### Nutrition Plan View
24. Fibre as a tracked macro — yes or no?
25. How often can trainer update nutrition targets?

### Food Logger
26. Which food database API — Nutritionix, FatSecret, USDA, or OpenFoodFacts?
27. Can client create custom food entries?
28. Can trainer see what client logged, or client-only?
29. Can client edit or delete a logged meal entry?

### Trainer Chat
30. Voice notes or video in MVP — or text + photos only confirmed?
31. Which messaging infrastructure — Stream, Sendbird, Twilio, or custom?
32. Message history retention — how far back?
33. Read receipts — yes or no?
34. Unified trainer inbox across all clients?

### Push Notifications
35. Push service — Firebase + APNs confirmed?
36. Workout reminder timing — trainer-set, client-set, or platform default?
37. Can client control which notifications they receive?
38. Deep link on tap — opens relevant screen?

### Workout History
39. Retention — indefinite or rolling window?
40. Filterable/searchable by client?
41. Export functionality?

### Payments
42. Stripe Connect for trainer payouts — confirmed?
43. Trainer never marks session "consumed" — auto-consume after 48hrs, client can mark, or support escalation only?
44. Can client dispute a "consumed" mark?
45. Bundle discount — cheaper per-session than one-off?
46. Price change mid-bundle — old price honoured or new?
47. Online vs in-person sessions — separate pricing allowed?

---

## Structural Gaps (not in PRD — flagged for decision entry)

**Wearable-free trainer admin gap:** PRD's Tier 3/4 fallbacks (emoji prompts, RPE sliders, history auto-fill) reduce *client* friction but don't solve *trainer* admin. Without biometric data, trainer has nothing unless client logs manually. What's needed but not specced:
- Structured biweekly/monthly client check-in forms (trainer-scheduled)
- AI-generated per-client summary brief (aggregates available signals: completion rate, nutrition adherence, RPE trends, self-reports)
- At-risk flags based on app behaviour (login frequency, logging gaps) — not biometrics-dependent
