# TIMBR — WORKOUT PLAN DB Pattern (Jul 2026)

## Context
Sagar Giri (Timbr collaborator) outlined a requirement via Google Chat:
- Trainer selects a client's strength level (S1/S2/S3)
- System generates a workout plan per day
- Each day has a fixed muscle group prescription (e.g. Day 1: Chest 3 exercises, Back 3 exercises, Core 2 exercises)
- DB must have ≥6 exercises per muscle group per level so alternates are available
- Client can swap any primary exercise to an alternate of the SAME level + SAME muscle group (e.g. if equipment unavailable)

## Schema (WORKOUT PLAN DB tab)

| Column | Field | Notes |
|--------|-------|-------|
| A | S_Level | S1 / S2 / S3 |
| B | Day | Day 1 / Day 2 / etc. |
| C | Muscle_Group | Chest / Back / Core / etc. |
| D | Slot | Primary 1/2/3 or Alt 1/2/3/4 |
| E | Exercise_Name | Exact name matching STRENGTH DB |
| F | Alt_Pool | Tag e.g. `Chest_S1_D1` — what the swap logic filters on |
| G | Equipment_Needed | Machine / Cable / Dumbbell / Bodyweight / etc. |
| H | Notes | Coaching notes |

## Alt_Pool tag convention
`{MuscleGroup}_{Level}_{Day}` — e.g. `Chest_S1_D1`

This is the filter key the app/logic uses: "give me any exercise where Alt_Pool = Chest_S1_D1 AND Slot starts with Alt". Each primary has 3–4 alternates tagged the same way.

## Minimum pool depth per group per level
- Each muscle group × level × day needs ≥6 rows in the pool (3 primary + 3+ alt)
- This ensures a client always has substitutes regardless of equipment

## Day 1 muscle prescription (S1 example from Sagar's spec)
- Chest: 3 exercises
- Back: 3 exercises
- Core: 2 exercises (with 4 alts available)

## Sheet ID
`1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo` — tab: `WORKOUT PLAN DB`

## Relationship to STRENGTH DB
Exercise names in WORKOUT PLAN DB should match exactly to STRENGTH DB rows so the app can do a JOIN on `Exercise_Name` to pull scores, difficulty, equipment, etc. Don't use variant names.

## What's built (Jul 13 2026)
- S1/S2/S3 × Day 1 × Chest/Back/Core — fully populated
- Day 2+ = skeleton (muscle pairings not yet defined by Tanzim/Sagar)
