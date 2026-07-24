# Timbr — Product Decisions & Design Reasoning
*Condensed from PRD discussion sessions, May–June 2026*

## App Overview
Timbr is a two-sided fitness platform: trainer assigns programs, client logs workouts. iOS-first. Coached tier before Solo tier. MVP strips gamification entirely (Timbr Score, XP, streaks, Harmony — all deferred post-retention).

**Build order (Feature 1–12):**
1. Workout Logging (3–4w) — core retention surface
2. Plan Generation Engine + Exercise DB (4–5w)
3. Initial Assessment & Tier Mapping (1.5w)
4. Trainer Coached Approval Flow (2w)
5. P1 Refresh / P2 Ready-for-Harder (1.5w)
6. Coach ↔ Client Chat (1w)
7. Trainer Client Inbox (1w)
8. Stripe Connect Billing (2w)
9. Push Notifications (0.5w)
10. Workout History (1w) — only cuttable feature
11. Auth / Clerk (0.5w)
12. Video Hosting / S3+CloudFront (0.5w)

---

## Answered PRD Questions (resolved)

| Q# | Question | Decision |
|---|---|---|
| Q2 | Password reset method | Email link (not OTP) |
| Q12 | Assessment editable by whom | Trainer only |
| Q17 | No video for exercise | Don't show the exercise at all |
| Q18 | Exercise library scope | Shared across all trainers |
| Q21 | Workout complete — auto or manual | Manual End Workout button (not auto-complete) |
| Q24 | Track fibre as macro | Yes |
| Q25 | Trainer nutrition update frequency | Whenever they want |
| Q30 | Chat media types | Text, photos, videos only — no voice notes |
| Q32 | Message history retention | 30 days |
| Q33 | Read receipts | Not required |
| Q34 | Unified trainer inbox | Yes |
| Q36 | Workout reminder — who sets | Client sets it |
| Q38 | Deep link on notification tap | Yes |
| Q39–41 | Workout history format | Calendar streak view only (no detailed history, no export) |
| Q42 | Stripe Connect | Confirmed |
| Q44 | Payment disputes | Client emails support@timbr.com |
| Q45 | Billing model | Trainer creates and sends one-time or recurring payment request |

**Still open (updated May 31 2026):**

| Q# | Topic | Status |
|---|---|---|
| Q5 | Client without trainer link — account state | Falls under Solo tier — to be finalised |
| Q9 | Client with inactive trainer — partial access | Falls under Solo tier — to be finalised |
| Q20 | Skipped exercise — mark as skipped or leave unchecked | Open |
| Q22 | Retroactive logging — can client log missed workout | Open |
| Q23 | Trainer notified on workout completion | Open |
| Q26–29 | Food logging — in MVP or out | Not decided |
| Q31 | Chat infrastructure — Stream/Sendbird/Twilio | Not decided |
| Q35 | Push service — Firebase + APNs | Not decided |
| Q47 | Online session setup and pricing | TBC |

**Q21 resolved this session:** Manual End Workout button — not auto-complete when all done.

---

## Wearable Data Architecture

**Core principle:** Wearable enriches, never gates. Two independent data layers:
- **Wearable** → session-level biometrics: HR, calories, duration, effort intensity. Cannot reliably identify which exercise or at what weight.
- **Swipe cards** → prescription compliance: which exercise, what load, how many reps/sets.

**They don't replace each other.** Without per-exercise data:
- Trainer can't adjust progression
- Plan engine has nothing to adapt from
- "45 min at avg HR 142" tells a trainer almost nothing useful

**If user has wearable but skips card interactions:** Don't block. Record all un-swiped exercises as SKIPPED — that's signal, not null. End Workout modal shows "X of N done" as a soft nudge, not a gate. Wearable-only sessions are valid.

**Seattle demographic:** ~45–55% wearable ownership in target demographic (tech-forward, health-conscious). Active use during strength sessions lower (~40–50%). Always design for split house.

**Rep-counting tech landscape:**
- PUSH Band 2.0 — gold standard accuracy, but it's a clip-on barbell attachment (not a wearable), ~$200, pro sports use only. Not a consumer assumption.
- Apple Watch — best at scale. watchOS 9+ counts reps natively for ~10 exercise types. Degrades on compound/asymmetric lifts.
- Garmin — has it, lags Apple on accuracy and variety.
- Whoop/Oura — no rep counting. Recovery-focused.
- Atlas Wristband — was most ambitious (100+ exercise auto-recognition), now defunct.
- **Gap nobody's closed:** automatic exercise identification + rep counting together, reliably, on mainstream wrist hardware.

**Best proxy approach for Timbr (no special hardware):**
1. Historical pre-fill — plan engine pre-fills cards with last session's weight/reps/sets. High hit rate, lowest friction.
2. Velocity inference — bar speed correlates with % 1RM (PUSH Band approach), not viable mainstream.
3. Time under tension + motion signature — Apple Watch does this for simple movements.
4. RPE triangulation — RPE + HR + known exercise = plausible load range for trainer conversation.
**Decision: Use option 1 (smart pre-fill). Cards arrive pre-loaded with best guess. User confirms or tweaks.**

---

## Program & Periodisation Data Model

**Hierarchy:**
```
Journey (macrocycle) → fat loss, muscle building — rarely changes
Program (mesocycle)  → 3–6 week block with specific milestone → this is "a new program"
Week → Day → Exercise → lives inside the program
```

**What defines a new program (mesocycle boundary):**
1. Split changes (push/pull/legs → upper/lower)
2. Phase change (hypertrophy → strength)
3. Periodisation model changes (linear → undulating)
4. Volume landmarks change (4 days/week → 5 days/week, deliberate)

**What does NOT make a new program:**
- Exercise swap within same muscle group and intent (RDL → leg curl = progression event)
- Load/rep adjustments week to week (progression)
- Substitution due to equipment or injury (adaptation)
- Adding an exercise to an existing day

**Test:** If you handed the new program to a different trainer with no context, would they say "different programme" or "same programme with tweaks"?

**Exercise swap tracking:** Must be a versioned event with reason attached (not a silent overwrite). Trainer selects reason: "progression", "equipment", "injury", etc. Audit trail preserves training lineage.

---

## Plan Generation Engine — Decision Layer (Feature 2)

Fires automatically at mesocycle end (day 28 or trainer-defined block end). Runs per exercise:

| Signal | Engine Decision |
|---|---|
| >80% completion + load progressed | Advance — increase load or next variation |
| >80% completion + no progression | Flag plateau to trainer |
| 50–80% completion | Carry forward, flag as inconsistent |
| <50% completion | Hold — require trainer input before next program |
| RPE trending down over block | Client adapting — ready to progress |
| RPE trending up over block | Too aggressive — regress or deload |

**Output:** Draft program + reasoning card surfaced to trainer. Not auto-published.
- "Block 1 complete. Hamstring curl: skipped 7/12 sessions — excluded from draft. Squat: consistent, RPE trending down — progressed to 4×6 @ +10%. 3 exercises flagged for review."
- Trainer reviews, edits, approves in one tap → publishes to client.

**Headless (no trainer) rule for preference-skipped exercises:**
- Skip >60% of mesocycle + preference-flagged (not injury) → auto-substitute equivalent exercise (same muscle group, same movement pattern, different exercise from shared library). Carry the *intent*, not the exercise.
- Full plan never auto-replaced — only exercise-level substitutions. Structural program change (new mesocycle) is always a trainer-initiated event.

**What the engine cannot automate (trainer decision required):**
- Why an exercise was skipped (injury? equipment? dislike?)
- Whether plateau means regress, substitute, or push through
- Whether client is ready for a full structural program change

---

## Workout Logging UX — Key Decisions (Feature 1, v0.4.1)

- **Swipe-right** = mark exercise DONE, advance to next NOT_DONE (Reels-style)
- **Swipe-up/down** = navigate NOT_DONE only (DONE cards skip in main flow)
- **Left rail** = tappable circles, only way to reach DONE cards mid-workout
- **Undo** = transient 4s popup post-swipe (dating-app pattern), not a header button
- **Refresh icon** = cycles original ↔ alt1 ↔ original ↔ alt2 (wraps when exhausted). Disabled on DONE cards.
- **End Workout flow = 3 paths:**
  - Path A (all done): "Good job" popup → RPE
  - Path B (some skipped): Journal sheet → toggle each exercise → RPE
  - Path C (zero done): Streak-only popup → Save streak or Discard → no RPE
- **Video:** MP4 H.264, S3+CloudFront, CSS edge-fade (radial-gradient mask-image), autoplay always

**Q21 resolved:** Manual End Workout (not auto-complete when all done).
