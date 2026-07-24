# Timbr MVP Scope — Coached Tier Only (2026-05-31)

## Decisions made this session
- Solo tier: **ruled out** for MVP
- Timbr Scoring (Harmony / XP / levels / streaks): **ruled out** for MVP
- Wearable integration: **ruled out** for MVP
- AI program generation: **ruled out** — trainer builds manually in MVP
- Food logging: **TBD** — not decided whether in or out

## MVP Feature List

### Client Mobile App (iOS + Android)
- Sign up / login (email + Apple + Google)
- Trainer linking via invite code (one-time, pre-filled assessment + workout on accept)
- Initial assessment (trainer-filled: experience, injuries, body type; client-filled: lifestyle, nutrition, sleep)
- Daily workout view — exercises, sets, reps, prescribed weight
- Exercise detail — video demo, form cues (no video = exercise not shown)
- Workout logging — guided checkoff, confirm/adjust weight per exercise
- Nutrition plan view — macro targets (protein, carbs, fat, calories, fibre) + meal timing
- 1:1 trainer chat — text + photos + video (basic)
- Push notifications — workout reminders (client-set), trainer messages, program changes
- Workout history — calendar streak view only, no detailed log, no export
- Subscription + payment management (Stripe)

### Trainer App (Web + iOS/Android)
- Sign up / login + profile setup
- Client list with status (active / inactive)
- Invite client via code or email
- Client detail view — assessment, workout history, compliance
- Program builder — create/edit workout plans, assign to client
- Nutrition target setting per client
- Approve / reject client progression requests
- 1:1 client chat (unified inbox)
- Session booking + calendar availability
- Payment dashboard — sessions consumed, escrow, payouts

### Admin Panel (Web)
- Trainer management
- Basic platform health monitoring

### Infrastructure
- Stripe Connect — subscriptions + session escrow + trainer payouts (USD only)
- Push notifications (service TBD — Firebase/APNs likely)
- Exercise library with video hosting/CDN
- Auth (Apple + Google social login)
- Real-time messaging infrastructure (service TBD — Stream/Sendbird/Twilio)

## Deferred to V2+
- Solo tier
- Timbr Score / Harmony / XP / levels / streaks
- Wearable integration (HealthKit, Health Connect, Whoop, Oura, Garmin)
- AI program generation
- Barcode scanning (food)
- Progress photos
- Achievement badges
- Broadcast messaging
- Cohort analytics
- Recovery recommendations
- White-labelling
- Trainer marketplace / discovery
- Chat-based plan modification (free-text)
- Online session video infrastructure

## 47-Question Checklist — Status

### Sign Up / Login
1. Same email across Apple + Google → doesn't matter (merge or error, no preference)
2. Password reset → email link or OTP (both acceptable, to be decided)
3. Email verification before access → yes
4. Session expiry → standard (follow industry norm, e.g. 30 days)
5. Client without trainer link → TBD (show inactive state or limited access)

### Trainer Linking
6. Invite code validity → one-time use, pre-populates assessment + workout on client accept
7. One trainer per client or multiple → one trainer per client; trainer can have multiple clients
8. Invalid/expired code → show "request invite from trainer" page
9. Client with no trainer → TBD (show existing plan, no new updates; or inactive state)
10. Unlink → both can unlink; client cancels payment; trainer marks client inactive

### Initial Assessment
11. Mandatory before app access → yes, done by trainer
12. Editable after submission → trainer only
13. Trainer notified on completion → not applicable (trainer fills it)

### Daily Workout View
14. No workout assigned → show rest tips + nutrition plan + upcoming plan
15. Can client see upcoming days → yes, full week plan visible
16. Rest day → client can mark rest day on home screen or configure in settings; skips to next session

### Exercise Detail
17. No video uploaded → exercise not shown to client
18. Form cues format → not specified (plain text assumed)
19. Exercise library → shared across all trainers

### Workout Logging
20. Skipped exercise → ❓ OPEN
21. Workout complete → ❓ OPEN (auto-complete vs manual submit)
22. Retroactive logging → ❓ OPEN
23. Trainer notified on completion → ❓ OPEN

### Nutrition Plan View
24. Fibre tracked → yes
25. How often trainer can update → anytime

### Food Logger (entire section TBD — may be cut from MVP)
26. Food database API → TBD
27. Custom food entries → TBD
28. Trainer sees food logs → TBD
29. Edit/delete logged entry → TBD

### Trainer Chat
30. Media types → text + photos + video (basic 1:1)
31. Messaging infrastructure → TBD (Stream/Sendbird/Twilio)
32. Message history → 30 days
33. Read receipts → not required
34. Unified trainer inbox → yes

### Push Notifications
35. Push service → TBD (Firebase + APNs likely)
36. Workout reminder timing → client-set
37. Client controls which notifications → no
38. Deep link on tap → yes

### Workout History
39. Retention → calendar streak view only (not detailed)
40. Filterable/searchable → no (calendar view only)
41. Export → no

### Payments
42. Stripe Connect → confirmed
43. Session "consumed" mark → removed from MVP (no consume flow)
44. Client disputes → email support@timbr.com
45. Bundle discount → trainer decides (trainer creates and sends payment request)
46. Price change mid-bundle → not applicable
47. Online vs in-person pricing → TBD (online session setup not yet decided)

## Still open after session
Q20, Q21, Q22, Q23 (workout logging behaviour)
Q26–29 (food logging — whole section TBD)
Q31 (messaging infrastructure)
Q35 (push service)
Q47 (online session setup)
Q5, Q9 (client without trainer account state)
Q2 (email link vs OTP for password reset)
