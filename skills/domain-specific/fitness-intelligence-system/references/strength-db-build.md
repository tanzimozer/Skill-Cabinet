# STRENGTH DB — Build Conventions & Classifier

The STRENGTH DB is a data-driven exercise selection/compute engine feeding workout
generation. Distinct from the Pairings/Stages sheet — this one is the *exercise library*
the parent system says "lives elsewhere."

**Sheet:** `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`
**Access helper:** `~/gs.py` (home dir — NOT /tmp; running from /tmp causes path-shadowing
import failures). Functions: `get(rng)`, `put(rng, values)`, `meta()`, `gid(title)`.
Uses Google OAuth token at `~/.hermes/google_token.json`, auto-refreshes.

## Schema (STRENGTH DB tab — 13 columns, 97 exercise rows)

Final column order (Stability and Risk Gate were CUT — both derivable/orphan, not intrinsic):
`Computed Level (A, live formula)`, Exercise Name, Muscle Group, Muscle Size,
Muscle Part, Difficulty, Learning Curve, Risk of Injury, Skill, Flexibility, Grip,
Load, Cluster.

(Header "Skill/Coordination" renamed to **Skill**. Earlier 15-col version with Stability +
Risk Gate is retired.)

- Reading values with `valueRenderOption="FORMULA"` shows live formulas vs flattened text —
  use this to verify a computed column wasn't accidentally pasted as static text.

## The S123 Classifier (LOCKED)

```
Computed Level = IF(Difficulty<=5, "S1", IF(LearningCurve<=7, "S2", "S3"))
```

- **Difficulty gates entry** (S1→S2): can a beginner do it unguided?
- **Learning Curve gates mastery** (S2→S3): does it need coaching?
- Two intrinsic numbers only, no equipment. Reads 97/97 against user's labels
  (S1=66, S2=21, S3=10).
- Logic is sound and locked, BUT accuracy is *to the user's labels* and partly circular —
  see the Learning Curve caveat below.
- Tab **S123 LOGIC** holds the definitions, decision tree, locked formula block, and mapping.
- This S123 logic is the template to later port to the Conditioning and Hybrid DBs.

**Difficulty formula:** `(Skill*2) + Flex + Grip + Load - 3`, capped 2–9.
- Barbell isolation Load = **3** (user reversed an earlier drop-to-2; stays 3).
- Machine press Difficulty = 2 is correct — do not inflate to make "taxing" exercises score high.

## The Learning-Curve-as-equipment-proxy insight (IMPORTANT)

We deliberately removed Equipment from classification. But Learning Curve values track
equipment almost perfectly (Machine~2, Cable~3, Barbell isolation~5-6, Barbell compound~6-9),
so equipment smuggled itself back in via LC. The 97/97 looks clean partly because LC is a
proxy we said shouldn't classify. **The fix:** define LC objectively with a per-score rubric
(e.g. "reps before unsupervised competence") and re-score against the definition — otherwise
the number means whatever the last person felt. Flag LC for Sagar's coach-eye validation
either way; it's the only remaining heuristic input.

## Locked design rules

- **Difficulty means "hard to execute,"** NOT "taxing/heavy to train." Confirmed twice.
  If user wants a "taxing" signal, offer a separate Intensity column — don't overload Difficulty.
- **Equipment must NEVER classify.** It's a user *filter* (gym may lack the tool), not an
  intrinsic property. Classification lives in the exercise's own demands. (Equipment/Role/
  Unilateral columns were added then removed for this reason.)
- **Naming convention: `[Variant] [Equipment] [Movement]`** — e.g. "Incline Machine Chest Press".
- **Clusters** (col Cluster) grain = **movement pattern**, not muscle part. ~30 clusters across
  12 muscle groups. Applied to STRENGTH DB only.
- **Sort order:** Muscle Group → easiest cluster first (lead with S1) → within cluster S1→S2→S3
  with difficulty as tiebreak.
- **Muscle Part (col E) style:** plain, no parentheticals. "Outer biceps" not "Biceps (outer)";
  "Gastroc calves" not "Calves (gastroc)". Quads part = "Front thigh" (user's chosen term).
  Single-Arm Cable Row and Yates Row are "Mid back," not "Lats."

## House colour bands (the three palette RGBs)

Scoring cells are colour-graded green→yellow→red by value. The exact house RGBs (read from
the live sheet):
- **Green** `(0.847, 0.918, 0.776)` · **Yellow** `(0.976, 0.929, 0.847)` · **Red** `(0.969, 0.847, 0.847)`
- Wide 1–9 axes: 1–3 green, 4–6 yellow, 7–9 red. Narrow 1–3 axes: 1 green, 2 yellow, 3 red.
- **Apply as static cell backgrounds driven by value** (not a gradient conditional rule —
  user's other tabs use static fills, and a clean value-driven paint is the goal).
- **WARNING — STRENGTH DB's own bands are hand-painted and INCONSISTENT:** the same score
  shows all three colours across different rows (Difficulty 8 yellow in one row, red in
  another; LC 8 green). Do NOT replicate Strength's banding by copying its cells — it's broken.
  Paint fresh from the value. Strength itself is a candidate for the same clean re-paint.

## Pitfalls

- **Always back up before destructive writes** — user values reversibility. Pattern:
  `json.dump(gs.get("STRENGTH DB!A1:O98"), open("~/backups/STRENGTH_DB_pre<Action>_<stamp>.json","w"))`.
- **Never write heuristic/invented data silently** — flag it for Sagar review; show on screen,
  don't commit. A heuristic shortlist was printed-only then reverted on request.
- Keep a SINGLE live computed Level column — don't carry manual + computed duals (sync drift).
- Don't trust an LC/Difficulty "97/97 accuracy" as ground truth; the inputs are still heuristic.
