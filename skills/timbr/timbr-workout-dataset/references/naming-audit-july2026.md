# Naming Audit — STRENGTH DB (July 2026)

## Summary
148 exercises scanned. One structural issue found: 5 exercises lacked an equipment prefix, breaking the taxonomy used for alt exercise computation.

## Renames applied
| Old name | New name |
|----------|----------|
| Tricep Dip (bodyweight) | Bodyweight Tricep Dip |
| Kneeling Ab Rollout | Bodyweight Kneeling Ab Rollout |
| Nordic Curl | Bodyweight Nordic Curl |
| Dragon Flag | Bodyweight Dragon Flag |
| L-Sit (parallel bars) | Bodyweight L-Sit (parallel bars) |

## Other findings
- **Bracket consistency**: 48 exercises use variant brackets, 100 do not. This is intentional — brackets appear only when a modifier distinguishes variants (e.g. flat/incline/decline, seated/lying). Not an issue.
- **Capitalisation**: Clean — no issues found.
- **Equipment prefix groups** (counts at time of audit):
  - Barbell: 45
  - Cable: 28
  - Machine: 29
  - Dumbbell: 21
  - EZ-Bar: 4
  - Smith Machine: 5
  - Bodyweight: 7 (after renames)
  - Weighted: 2
  - T-Bar: 1
  - Trap-Bar: 1
  - GHD: 1
  - Hanging: 2
  - Stability Ball: 1
  - TRX: 1

## Action required after renames
Propagate updated exercise names from STRENGTH DB into WORKOUT PLAN DB (Primary Exercise and Alt columns).
