# Building a Selection/Compute Engine on a Scored Exercise DB (TIMBR) — Jun 2026

Context: Tanzim's TIMBR WORKOUT DATASET (sheet id `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`).
Tabs: STRENGTH DB, CONDITIONING DB, HYBRID DB, plus scored twins (S-123/F-0123/P-123),
SCORING LOGIC, FX, DIFFICULTY, MUSCLE BUNDLES, and the new S123 LOGIC.
Goal arc: consistent schema → audit scoring → cluster/order → name consistency → level
definitions → full selection engine. This file captures the patterns from the engine-build phase.

## Clusters = MOVEMENT PATTERN, not muscle part
When Tanzim asks to "create clusters" inside a muscle group, the grain he means is the
**movement pattern** (Horizontal Press / Incline Press / Vertical Pull / Squat / Hip Hinge /
Lunge / Curl / Pressdown …), ~3–4 per muscle. NOT the finer muscle-part split (upper vs mid chest).
Confirm grain once, then tag every row with a `Cluster` column. Result: ~30 clusters across 12 muscle groups for 97 strength rows.

## Multi-key sort hierarchy for a progression ladder
The order Tanzim wants for a selection ladder, in priority order:
1. **Muscle Group** — preserve first-appearance order (build an `mg_order` dict, don't alphabetise).
2. **Cluster** — order clusters *within* a muscle group by their **easiest entry** (min S-level, then min Difficulty in that cluster). So a cluster that only contains S2 lifts (e.g. Decline Press) falls to the BACK of its muscle group; the muscle group must LEAD with an S1 cluster.
3. **Level (S1→S2→S3)** — inside a cluster, climb by competence tier first.
4. **Difficulty** — tiebreak inside a level (easiest → hardest).

Pitfall caught this session: sorting by Level+Difficulty alone left the *clusters themselves*
unordered (Chest opened with Decline Press S2 before Horizontal Press S1). The fix is the
per-cluster `cl_min = min((level, difficulty))` key. Verify by printing the full ladder and
reading the top of each muscle group — it must start at S1.

```python
def lvl(r):  # 'S2' -> 2, junk -> 99
    s=g(r,iL).strip().upper()
    return int(s[1:]) if s.startswith('S') and s[1:].isdigit() else 99
mg_order={}; cl_min={}
for r in rows:
    m=g(r,iM)
    if m not in mg_order: mg_order[m]=len(mg_order)
    key=(m,g(r,iC)); k=(lvl(r),diff(r))
    if key not in cl_min or k<cl_min[key]: cl_min[key]=k
rows.sort(key=lambda r:(mg_order[g(r,iM)], cl_min[(g(r,iM),g(r,iC))], g(r,iC), lvl(r), diff(r)))
```

## Naming convention — lead with the distinguishing word
Tanzim hates inconsistent variant placement ("Incline Chest Press Machine" then "Smith Machine
Incline Press" — the eye can't scan the variant). His locked convention:
**`[Variant] [Equipment] [Movement]`** → e.g. `Incline Machine Chest Press`, `Flat Barbell Chest Press`, `Decline Barbell Chest Press`.
- The cluster/variant word LEADS so a column scan groups instantly.
- Within a cluster where there's no real variant word, the equipment word leads.
- Apply as an explicit `old->new` dict (only touch the offenders; leave already-consistent names alone), then `put` the whole tab back.
- **Flag the downstream risk before/after:** these exact name strings are likely keys in other tabs (the scored twins, splits) and the app. Renaming silently breaks any exact-string join. Offer to propagate the rename across sibling tabs.

## Defining S1/S2/S3 — derive the rule from the data, then express as a DECISION TREE
S1/S2/S3 = Strength Level 1/2/3. They are **skill/access tiers, not strength capacity**.
- S1 = anyone can do it safely unguided (machine/cable/Smith — fixed path, self-spotting).
- S2 = free-weight compounds you can train hard solo (real load + balance, self-manageable).
- S3 = technical lift that must be COACHED (loaded spine / overhead / hip-hinge under a bar).

Method: don't invent thresholds — read the live `Difficulty / Learning Curve / Risk` ranges per
existing level first (groupby + min/max). The clean separator that fell out: **Difficulty gates
S1→S2** (can a beginner do it unguided?), **Learning Curve gates S2→S3** (does it need coaching?).
But the *deliverable Tanzim wanted was not a numeric formula* — it was a **decision tree** of
yes/no GATES, asked top-to-bottom, first-YES-wins:
- Gate 1: Is the path fixed for you? (machine/cable/Smith) → YES = S1
- Gate 2: Does it need a coach to do safely/correctly? → YES = S3
- Gate 3: Everything else → S2

Tanzim prefers "a question the exercise passes or fails" over a score he can't introspect.
Offer the tree first; show which rows shift; let him hand-move before locking.

### CORRECTION (locked) — classify on INTRINSIC axes only; equipment is a USER FILTER, never a classifier
The decision tree above leaned on equipment (machine/cable/Smith → S1). **Tanzim reversed this:**
classifying by equipment would *invalidate a user who doesn't have that equipment* — a barbell row
is intrinsically a barbell-row regardless of which gym you're in. Classification must live in the
exercise's own demands, not the tool. So:
- **Equipment / Role / Unilateral columns belong to the SELECTION engine (the filter/rank stack), NOT the classifier.** When he says "take those columns out, compute S123 from the current columns," delete the derived name-based columns and classify only on the intrinsic scored axes (Difficulty, Learning Curve, Risk, Skill/Coordination, Stability, Load).
- Equipment's role is Tier-1 hard-filter #2 ("does their gym have the tool"), full stop.

### Final locked classifier: fit a numeric formula AGAINST the existing labels, pick highest match
Once told to compute from intrinsic columns, the method is: propose 2–3 candidate formulas, run each
across all rows, count exact matches vs the existing hand-labels, and pick the highest. Don't theorise —
**measure.** This session:
- **Formula 1 (WINNER, locked): `IF Difficulty<=5 -> S1; ELSE IF Learning Curve<=7 -> S2; ELSE S3`** → 96/97 match.
  Difficulty answers Gate 1 (can a beginner just do it), Learning Curve answers Gate 2 (needs coaching).
  Both intrinsic to the exercise. The single disagreement (Flat Barbell Chest Press: label S2, formula S3
  on LC=8) is a genuine edge case to flag for his eye, not a formula flaw — report it, don't auto-resolve.
- Formula 2 (composite `2*Skill + LearningCurve`, bands): only 90/97 — over-promotes heavy lat pulldowns
  (high LC, not free weights). Single-number is cleaner but lost accuracy; offer it as the runner-up.
- Write the winner as a LIVE formula column (`Computed Level`, e.g. col T) so every row self-classifies and
  the mismatch is visible: `=IF(F2<=5,"S1",IF(G2<=7,"S2","S3"))`. Widen the grid first (appendDimension) —
  a 19-col tab rejects a write to col T until grown.
- Then UPDATE the S123 LOGIC tab: rewrite the WHAT-THEY-MEAN defs to intrinsic language (strip equipment
  words), add a "CLASSIFICATION FORMULA (locked)" block with the rule + a "why these axes" line
  (intrinsic = property of the exercise, not gym/user), and keep the decision tree as the plain-English mirror.

### Pitfall — rewriting a section longer than the original CLOBBERS rows below it
When `put`-ing a replacement block over an existing tab section, a longer block overruns into the next
section (collided with the mapping header + ate one exercise row this session). Also: formula-looking
TEXT written via USER_ENTERED gets parsed as a live formula and errors (`#ERROR!`). Fix for both: don't
patch in place — **rebuild the whole tab in one pass** (values().clear() the tab, then write the full
row set once), and write the formula as plain prose ("IF Difficulty <= 5 -> S1 ...") not a `=`-prefixed
string. Recompute the section row offsets from the rebuilt layout before re-applying formatting.

## The S123 LOGIC explainer tab — structure + formatting (reused template)
Tanzim wanted the level logic on its own tab, readable in one pass by him + Sagar. Layout:
1. Title bar (navy fill, frozen row 1).
2. **WHAT THEY MEAN** — one row per level, S1 green / S2 amber / S3 red, definition left-aligned.
3. **DECISION TREE** — grey panel, Gate IDs + outcome (`YES -> S1`) bold.
4. **EXERCISE MAPPING** — navy header, all rows grouped S1→S2→S3, each row colour-coded by level, exercise name left-aligned, everything else centred.
Format pass via one `batchUpdate`: wrap + MIDDLE + CENTER on the used range, then per-section
overrides (left-align long text), `mergeCells` for section headers, level colour fills, column
widths `[A 90, B 300, C 140, D 200]`, freeze row 1, light grey borders per block.
"Organize it how I like it" = wrap, centre/middle align, filled+bold section headers, colour-coded
bands, frozen title, tidy widths. This is his house style for any reference/explainer tab.

## Selection engine = three-tier GATE STACK (filter → target → rank)
When Tanzim says "make it a fully detailed compute engine for selection," he means more than the
competence level — a real engine runs a stack. The structure to propose:

**TIER 1 · HARD FILTERS (in/out):**
1. Level — client tier ≥ exercise tier (built).
2. Equipment — does their gym have the tool? (derivable from name).
3. Safety — Risk Gate: drop Spotter lifts if no spotter, Coaching lifts if no coach.
4. Contraindication — injury/mobility block (spine-loaded / overhead / deep-knee / shoulder). *Needs a NEW tag; can't be pulled from data — heuristic first-pass, user+Sagar verify.*

**TIER 2 · TARGETING (match the prescription):**
5. Muscle — Group + Part hits the day's target.
6. Role — Compound (primary slot) vs Isolation (accessory). Derivable from cluster.

**TIER 3 · RANK within surviving pool:**
7. Fatigue/Load — heavy compounds first; use **Load + Compound flag as the proxy**, do NOT build a separate fatigue score (avoids another column to maintain).
8. Unilateral — preferred for balance/rehab/asymmetry. Derivable from name.
9. Progression — within Cluster pick the rung at/just under client mastery (the cluster ladder, built).

## Deriving engine tag columns from the exercise NAME (data-driven, no manual scoring)
Three columns fall straight out of the name/cluster — add them non-destructively (append to header,
pad rows, `put`). Backup first.
- **Equipment:** keyword match on lowercased name. Order matters — check EZ-Bar / Trap-Bar / Smith
  / Cable BEFORE the generic Machine/Barbell fallback (else "Smith Machine" mis-tags as Machine).
  Machine also catches leg press/extension/curl/hack squat + non-cable pulldowns. Default = Barbell.
- **Role:** Compound vs Isolation by **cluster membership** (maintain an `ISO_CLUSTERS` set:
  Lateral/Front Raise, Rear Delt, Curl, Preacher Curl, Pressdown, Overhead Extension, Crunch,
  Anti-Rotation, Anti-Extension, Leg Extension, Leg Curl, calf clusters, Shrug). Everything else = Compound.
- **Unilateral:** Y if name contains single-arm/single-leg/split/reverse lunge/walking lunge/lunge.

Strength DB distribution this session (sanity anchors): Equipment {Machine 26, Cable 21, Smith 11,
Barbell 31, EZ-Bar 4, Trap-Bar 2, Bodyweight+ 2}; Role {Compound 56, Isolation 41}; Unilateral {N 89, Y 8}.

## "Is it accurate?" → validate the INPUTS, not the formula's fit to its own labels
When Tanzim asks "in your verdict, is it accurate?" of a fitted classifier, the honest answer is the
**circularity caveat**: an N/N match against his own hand-set labels proves the rule is *consistent*,
not that the underlying data is *right*. The formula only inherits the trust of its weakest input.
- Name the load-bearing input and its provenance. Here the whole S2/S3 split rests on **Learning
  Curve**, which was a heuristic first-pass never validated by Tanzim/Sagar. Lock the *logic*, flag
  the *inputs*.
- "What is the question for us/Sagar?" → the deliverable is a crisp validation question, not a status
  report: *"Are the Learning Curve scores right? — that's the one input the S2/S3 split rests on."*
- When he asks "what are the scores?", DON'T hand him the whole column — pull only the rows at the
  **decision boundary** (the LC 5–9 band that actually decides S2 vs S3) and read them sorted. The
  outlier jumps out: Flat Barbell Bench sat at LC 8 while its own incline/decline twins were LC 5 — a
  flat bench learning *harder* than an incline is nonsensical, so the value (not the formula) was wrong.

## Twin-consistency check for sibling rows — same cluster/family should share input scores
A heuristic-scored input is most easily audited by **comparing siblings within a cluster**. Flat /
Incline / Decline barbell bench are the same skill family; their Learning Curve should match. When one
diverges (Flat LC 8 vs Incline/Decline LC 5), the odd one out is almost certainly the error. Tanzim's
call: "flat is the same" → set Flat to 5, which took the classifier from 96/97 to **97/97**. Fixing the
single bad input, not touching the formula, is the correct resolution.

## Refuse a blind value edit that breaks a LOCKED definition — surface the redefinition instead
When Tanzim says a value "should be much higher" (e.g. machine chest press Difficulty "should be 8 not
2"), do NOT just type the number. A machine press is correctly the FLOOR of "hard to execute" (fixed
rails, no balance) — he confirmed that exact logic when signing off Smith Incline at 3. Overwriting it
to 8 collapses the meaning of every score beneath it. The right move:
- Name the conflict plainly: two different things are fighting on one axis — "hard to execute" (locked,
  machine = 2) vs "hard/taxing to train" (machine could be 8). One column can't carry both.
- If he genuinely wants the second meaning, that's a **redefinition** requiring a re-score of all rows
  AND a reshuffle of S123 (the formula feeds off Difficulty) — and the better design is a SEPARATE
  Intensity/Load column, not overwriting Difficulty (keep both signals).
- This is a "challenge directly" moment: hold the locked definition, explain the downstream blast
  radius, offer the clean alternative. He self-corrected ("sorry my mistake, chill") — the pushback was
  right. Don't be a yes-machine on data that breaks an agreed rule.

## Heuristic-input review queue — Load too-blunt on barbell ISOLATION
The Load 1–3 tag (feeds Difficulty) was auto-scored "barbell = Load 3," which over-rates barbell
ISOLATION moves (Barbell Curl, Front Raise, Shrug, Skullcrusher, Rollout, barbell Calf Raises) — you're
moving light weight through one joint, arguably Load 2 not 3. This is a Sagar-review item, NOT an
auto-fix: Tanzim's first instinct was "drop to 2," then reversed to "stay 3" — so RESTORE-FROM-BACKUP
was needed (the pre-change `~/backups/STRENGTH_DB_preLoadFix_<ts>.json`). Lesson: on a flagged-but-not-
locked input, confirm the direction before writing, and always have the immediate-prior backup ready to
revert a reversed call cleanly.

## "Alternative exercise" column — closest match within the SAME tier (constrained substitution)
Tanzim's rule when building an Alternative/Substitute column: the alt must be (1) the **same S-level**
(an S1 can only sub another S1 — never offer S2/S3 for an S1), and (2) the **closest by training benefit**,
where "closest" means same movement pattern + same muscle PART = same benefit ("a flat bench is a press
hitting specific parts a specific way; the alt must fulfil the same benefit").
- **Ranking key (weight muscle PART heaviest):** among same-level candidates, score each by
  `same Cluster/movement → same Muscle Part → same Muscle Group`, part weighted above group. Pick the top.
  The bench example validates the logic: Flat Barbell Bench → Barbell Floor Press (same press, same mid-chest).
- **Match-quality tiers to report honestly:** exact (same movement AND same part) / strong (same part, sibling
  movement) / nearest-in-group (no same-part twin in tier) / **orphan** (only member of its cluster+part at that
  level — no true same-benefit sibling exists). Don't dress an orphan up as a good match — name the 4-ish orphans
  in a table with the compromise made, and offer two fixes: add a sibling each, or accept "best available."
- **Don't strictly enforce same-part where it breaks sense:** a rear-delt fly with no same-part sibling should
  fall to a lateral raise (adjacent delt work), not to an overhead press that merely shares the group. Hand-tune
  the handful of orphans to the most sensible nearest before writing.

## Downstream lookup columns that MIRROR + independently RECOMPUTE — the built-in QC
When adding columns describing the *alternative* (its own Level, Difficulty, Learning Curve, Risk, and a
re-derived tier), build them as **live formulas that both mirror the source AND recompute independently**, so
the column stack self-checks:
- **Alt Level** = `INDEX/MATCH` the alt name into STRENGTH DB's level col. Because the alt was chosen same-level,
  this MUST equal the row's own level — so the column doubles as a rule-violation detector (any Alt Level != own
  Level means the matcher leaked). This session: 0 leaks across 150.
- **Alt Difficulty / LC / Risk** = three `INDEX(...,MATCH($F,DB!$B:$B,0))` pulls of the alt's own scored axes.
- **Verified Alt Level** = recompute the tier from those three pulled axes via the LOCKED rule
  `=IF(MAX(H,I,J)>=7,"S3",IF(MAX(H,I,J)>=4,"S2","S1"))`. It's computed *independently* of Alt Level, then the QC
  asserts `K == G` — proving the alt genuinely recomputes to the same tier from first principles, not just by
  name lookup. All 150 agreed this session.
- Everything stays **live** (INDEX/MATCH, not pasted values) so edits to STRENGTH DB propagate. Verify with the
  FORMULA render view that every cell starts with `=` — a pasted value would silently drift.

## Row-by-row fact-check of a derived tab — N checks per row, computed against source, "0 errors" as proof
When Tanzim says "fact check the tab, compute and test each row one by one, look for error with precision,"
re-derive EVERYTHING from the source tab in code and diff, don't eyeball. The per-row check battery this session
(8 gates × 150 rows, all clean):
1. Own Level == STRENGTH DB level for that exercise. 2. Muscle Group + Part == source. 3. Alt name exists in
source (no phantom names). 4. Alt Level == alt's real source level. 5. same-level rule (own == alt). 6. Alt
Difficulty/LC/Risk == alt's source axes. 7. Verified level recomputes correctly from those axes AND == Alt Level.
8. No self-referencing alt (alt != itself).
Plus integrity sweep: **0 blank cells** across all cols × rows, and **every lookup cell confirmed a live `=`
formula** (FORMULA render view) — not one pasted value. Report as "150 rows, 8 checks each, 0 errors" with the
proof (mismatch list length 0), and separately re-flag known compromises (the orphans) as compromises, not errors.

## Working style for this engine build
- "Do as much as you can with data-driven decisions" → derive everything derivable NOW, build it,
  and surface ONLY the genuinely non-derivable calls (contraindication tag, fatigue proxy) as a
  short either/or with a recommendation. Don't stall the whole build waiting on the judgment calls.
- Every destructive/structural write gets a `~/backups/<TAB>_<purpose>_<ts>.json` first.
- `cp /tmp/foo.py ~/foo.py` then run from `~` — running a script from `/tmp` shadowed the home
  `gs.py` helper (`AttributeError: module 'gs' has no attribute 'get'`). Keep gs-using scripts in `~`.
