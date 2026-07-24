---
name: client-fitness-programming
category: health-fitness
description: Designing and iterating training programmes for Tanzim's clients — split structure, exercise selection, tempo, cardio protocol, and progressive overload. Each client has a profile in references/.
triggers:
  - client asks about their training split
  - client asks what programme they should be on
  - request to write or update a workout programme
  - client mentions goals (tone, slim, build, recomp, strength)
  - client flags an injury or recovery update
---

# Client Fitness Programming

## Workflow

1. **Pull client profile first.** Check `references/<client>.md` before responding. Existing injuries, goals, equipment, training age, and preferences must inform every answer.
2. **Clarify before writing.** If the profile is missing training age, available equipment, or exercise exclusions — ask before building the programme. A generic programme is a wasted iteration.
3. **Write for their level.** Experienced clients need tempo, rest periods, drop sets, progressive overload logic. Beginners need clarity and simplicity. Don't default to basic.
4. **Update the profile after sessions.** Any correction, preference, or status change (injury recovered, goal shift, exercise removed) gets written back to the reference file immediately.

---

## Programme Design Principles

### Recomp Goals (tone + slim + build simultaneously)
- Frequency: each muscle group **2× per week** minimum
- Upper/Lower split (4–5 days) is the default recommendation
- Lagree / reformer Pilates counts as a training day — don't stack heavy gym sessions on top
- No HIIT for recomp — steady-state cardio protects recovery and muscle
- No fasted cardio when protein is high
- Cardio always **post-weights**, never before
- Carbs highest on heaviest lower body days

### Feminine Physique Goals
- **Lateral delts are the priority** on push days — create the shoulder-to-waist ratio
- **Rear delts hit twice per week** — posture, roundness, back width
- Glutes: hip thrust is the primary builder — pause at the top
- RDL stops at knee height — full glute/hamstring load, lumbar protected
- Avoid excessive chest volume — shape over bulk
- Calves: minimal. One exercise, one day, 3 sets maximum unless client explicitly wants calf development

### Back Protection
- No axial loading (no barbell back squat unless client is cleared and requests it)
- RDL: neutral spine, stops at knee
- Core braced before every rep — cue this in the programme notes
- Cable and machine work preferred over heavy free-weight spinal loading

### Push Up / Pull Up Progressions (bodyweight not yet achievable)
- **Push ups:** Start incline (hands on bench). Drop bench height weekly. Floor push up is the target. Programme as `3×max` with tempo.
- **Pull ups:** Assisted pull-up machine (reduce assistance 2.5–5kg every 1–2 weeks) + negatives (jump to top, lower slow, 5-0-0-0 tempo). **Cap at 5 total sets across both variations** — do not stack 7–8 sets of the same pulling pattern.
- Negatives build eccentric strength fastest — always pair with assisted work, not as a standalone.

---

## Pitfalls

- **Don't over-prescribe calves.** Clients training for a feminine physique rarely want calf hypertrophy. One exercise max unless asked.
- **Don't over-prescribe chest.** One compound + one isolation is sufficient on push days when shoulders are the priority.
- **Don't stack pull-up variations to 7+ sets.** Assisted + negatives = 5 sets total. Lat pulldown covers remaining volume.
- **Basic programmes get called out.** Experienced clients will say "this seems fairly basic." Always ask training age and equipment before writing — or check the profile.
- **Daily leg sessions cause recovery failure.** If a client is hitting legs every day, flag it and restructure. Recovery window = growth window.
- **Lagree is a training day.** Don't treat it as filler or ignore it in the split. Programme it as the conditioning/core day — no additional cardio needed on that day.

---

## Tempo Format

`Eccentric – Pause – Concentric – Reset` (e.g. `3-1-2-0`)

Always include tempo and rest periods for experienced clients. Rest ranges:
- Compound movements: 90s
- Secondary compounds: 75s
- Isolation: 45–60s

---

## Cardio Protocol Defaults (Recomp)

| Day Type | Cardio | Duration | Intensity |
|---|---|---|---|
| Heavy lower | Incline treadmill walk | 20 min | Grade 10, conversational |
| Upper push | Steady-state bike | 15 min | 70–75% max HR |
| Upper pull | Easy walk or rest | 20 min | Active recovery |
| Lagree day | None | — | — |

---

## Client Profiles

- `references/blair.md` — Blair's full profile, goals, injuries, programme history
