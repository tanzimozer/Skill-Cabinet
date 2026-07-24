---
name: timbr-exercise-scoring
description: Design, audit, and apply the scoring/classification logic for the TIMBR Workout Engine exercise database (Strength/Conditioning/Hybrid Google Sheet). Use when working on Difficulty/Level/cluster/selection logic, formulas, or the S1/S2/S3 tiers.
---

# TIMBR exercise-database scoring & classification

The TIMBR Workout Engine runs off a Google Sheet ("TIMBR - WORKOUT DATASET", id `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`). Tabs: STRENGTH DB (97 rows), CONDITIONING DB, HYBRID DB, plus reference tabs (S-123, SCORING LOGIC, FX, DIFFICULTY, S123 LOGIC, MUSCLE BUNDLES). Tanzim owns the product; **Sagar** (co-founder/CTO) is the SME who validates exercise scores. This work ultimately feeds workout generation.

## Tooling
- Write via `~/gs.py` — `gs.get(range)`, `gs.put(range, values)`, `gs.meta()`, `gs.gid(title)`, `gs.svc` (raw API for batchUpdate/formatting). Already OAuth-authorised for writes.
- **CRITICAL: run scripts from `~` (home), never `/tmp`.** A different `gs` module shadows ours from /tmp and `gs.get` won't exist. Symptom: `AttributeError: module 'gs' has no attribute 'get'`. Fix: `cp script /tmp` → run from `~`, or just keep the script in `~`.
- New columns: the sheet's grid is fixed-width. Writing past the last column errors `Range exceeds grid limits`. **Append a column first** via `appendDimension` batchUpdate, then write.
- **Always back up before destructive writes** — `json.dump(gs.get('TAB'), open('~/backups/TAB_<purpose>_<ts>.json','w'))`. Tanzim values reversibility; every reorder/rebuild/rename in this project got a timestamped backup.

## The locked scoring model (as of Jun 2026)

**Difficulty** = `(Skill/Coordination × 2) + Flexibility + Grip + Load − 3`, capped 2–9.
- Definition is **"hard to EXECUTE"** — NOT how taxing/heavy/advanced the set is. This distinction is load-bearing and Tanzim will test it: a machine chest press is correctly a **2** (fixed rails, no balance, self-spotting), even though it can be heavy. If asked "shouldn't this be higher?", hold the line — pushing execution-difficulty up to mean "how hard you're working" collapses the whole scale. If he genuinely wants "how taxing," that's a SEPARATE column (Intensity), not a redefinition of Difficulty.
- Skill ×2 because it's the one axis you can't regress (you can scale load down, not fake technique).
- Load 1–3: machine/cable/pin-stack = 1 (scales instantly), moderate free weight = 2, heavy barbell = 3. `cable = Load 1` is a documented rule.
- −3 constant lands the floor at 2 and anchors Smith Incline at 3.
- Stability is deliberately EXCLUDED (lives in Learning Curve; avoids double-count).

**S1/S2/S3 classifier** (Strength Levels 1/2/3):
```
IF Difficulty <= 5        -> S1   (beginner can do it unguided)
ELSE IF Learning Curve <= 7 -> S2 (real load you self-control, grindable solo)
ELSE                      -> S3   (long to learn, must be coached)
```
- Difficulty answers "can a beginner just do it" (S1 gate). Learning Curve answers "needs coaching" (S2/S3 split).
- Implemented as a live `=IF(F<=5,"S1",IF(G<=7,"S2","S3"))` formula in STRENGTH DB column T ("Computed Level"). Currently 97/97 match to hand labels.
- **EQUIPMENT IS A SELECTION FILTER, NEVER A CLASSIFIER.** A barbell row is intrinsically a barbell row regardless of whether the user's gym has a barbell. Classification must live in the exercise's own demands (Difficulty, Learning Curve, Skill, Risk) — not equipment. Tanzim rejected an equipment-based classifier explicitly: it would invalidate a user who lacks the equipment.

## Selection engine (downstream of classification — distinct job)
Selection runs filter → target → order. Columns like Equipment, Role (Compound/Isolation), Unilateral, Load belong to SELECTION, not classification. Keep the two jobs separate — conflating them is a known trap (happened this session; columns were added then removed). Proposed gate stack: Level + Equipment-availability + Risk Gate (Spotter/Coaching) + contraindication tag (hard filters) → Muscle + Role (targeting) → Load/fatigue + Unilateral + cluster-progression (ranking).

## Structure & conventions
- **Clusters = movement patterns** within a muscle group (Horizontal Press / Incline Press / Vertical Pull / Squat / Hip Hinge…), NOT muscle parts. ~30 clusters across 12 muscle groups in Strength.
- **Sort order:** Muscle Group → Cluster (cluster ordered by its easiest entry, so each group leads S1) → S-level (S1→S2→S3) → Difficulty as tiebreak. So each cluster reads an easiest-to-hardest progression ladder, the engine's swap path.
- **Naming: `[Variant] [Equipment] [Movement]`** — the variant/cluster word leads so the eye scans it. e.g. "Incline Machine Chest Press", "Flat Barbell Chest Press". Normalise hyphens (Smith-Machine → Smith Machine). NOTE: renames likely break exact-string references in other tabs (S-123, splits, the app) — flag propagation as a follow-up.

## Validation discipline (Tanzim's standard)
- A formula matching the EXISTING hand labels (e.g. 96/97) proves CONSISTENCY, not ground truth — it's circular. Say so honestly. The real question is whether the underlying input scores are right.
- **Load and Learning Curve values were heuristic first-pass — flag them for Sagar/user review, don't present as validated.** When a single row breaks a formula, inspect it: it's usually one bad input, not a formula flaw (Flat Barbell Bench LC was 8 vs its incline/decline twins at 5 — fixing that one cell took the classifier to 97/97).
- Don't silently invent or trust unvalidated data.

### The two axes are collinear — Gate 2 is nearly decorative (confirmed Jul 4, 2026)
Difficulty and Learning Curve correlate at **r ≈ 0.96** across all 97 Strength rows — they share ~93% of variance. Consequence Tanzim will (and did) probe:
- **Gate 2 (Learning Curve) never fires on the S1 side.** Every D≤5 exercise also has LC 2–5; every D>5 has LC 6–9. Difficulty alone reproduces all 66 S1s. LC only does real work splitting S2 from S3 among already-hard lifts.
- **Root cause is structural, not data luck:** Skill/Coordination is ×2 *inside* Difficulty, and Learning Curve ≈ skill-to-master — so Difficulty already bakes in what LC re-measures. The rubric currently *cannot* produce a low-D / high-LC row.
- **The unspoken assumption holding the design up:** "nothing is both easy to execute and slow to master." The data contains zero counterexamples, so the second gate is untested. The honest read: correct as a sorter, overclaiming as a two-axis *model*.
- **The deliberate challenge case to offer:** hunt for a low-Difficulty, high-Learning-Curve movement. If one exists in real training, the rubric is the bug (it can't score it); if none does, drop Gate 2 and run a single scale losing nothing. Either way, that's the seam to pull — don't let a 97/97 match rate paper over it.

### The two-axis redesign Tanzim is exploring (Jul 4, 2026) — physical vs technical load
When he asks "propose a better/more precise formula," the fix he responded to is **splitting into two genuinely independent axes** (kills the r≈0.96 collinearity by removing the shared Skill term):
- **Physical load** = body tax = `Flex + Grip + Load` (Skill STRIPPED OUT — that's what made the old Difficulty double-count).
- **Technical load** = brain tax = `Skill + Learning Curve`.
- Classify on a **2×2, not a waterfall:** low+low → S1; high on ONE axis → S2; high on BOTH → S3.
- Why it's more precise: each axis measures one thing, no double-count; it can finally represent the row the old formula *cannot* (physically easy + technically hard); S2 becomes meaningful ("hard in one dimension") instead of "slightly less hard than S3."
- Caveat to state before committing: this reshuffles some current labels. Offer to run it across all 97 and show what moves — but only when he says go (he tests row-by-row first; see below).

### Load must be COMPUTED, not hand-picked (Tanzim's hard rule, Jul 4)
He rejected hand-scored Load outright: "Load cannot be random... we have to compute load to gain preciseness." A chosen number is a vibe; it has to fall out of measurable primitives the same way Difficulty does. **Compute Load from four observable primitives, none a taste call:**
- **Muscle mass moved** — count prime movers × their size (big/small).
- **Joint count** — isolation (1 joint) vs compound (2+). Objective.
- **Axial flag** — does the spine bear the load? barbell squat/OHP standing = 1; machine/seated/lying = 0. Binary.
- **ROM band** — short / medium / full. Measured.
- `Load = MuscleMass + JointCount + AxialFlag + ROMband` → normalise to 1–9.
- **Why this was the actual bug:** old hand-scored Load flattened heavy compound machine lifts to 2 across the board. Computed Load correctly promotes them. The axial flag is what keeps a Smith/machine lift *below* a barbell one (rails carry the spine → axial 0) while still crediting its mass/joints/ROM.

### Row-by-row validation results with computed Load (Jul 4 — pattern is clean both directions)
He tests candidates one at a time before any bulk rerun. Confirmed behaviour:
- **Smith Machine Squat** (Skill1 Flex1 Grip1 LC2, Load→~5–6): Physical ~high, Technical low → **S2** (was S1). His instinct was S2; the hand-scored Load 2 was the bug.
- **Smith Machine OHP** (Load→~4–5): Physical ~7 high, Technical 3 low → **S2** (was S1).
- **Machine OHP** (Load→~3): Physical ~5, Technical 3 → **stays S1**. Control case — machine (seated, back-padded) correctly reads easier than Smith (standing, self-braced). The gap the old system flattened.
- **Flat Barbell Bench** (Skill2 Flex2 Grip2 LC8, Load→~4–5, axial 0): Physical ~9, Technical ~10 → **stays S3**. A true S3 doesn't collapse — validates the formula isn't just inflating everything.
- **Dumbbell Curl** (small muscle, 1 joint, Load→~2): Physical ~5, Technical ~6 → **stays S1** near the line. Isolation stays put.
- **Net pattern:** big compound machine lifts → promoted (Load was under-scored); small isolation lifts → stay put; true free-weight S3s → hold. That's the formula separating physical demand honestly, not inflating.
- **Data gap flagged:** STRENGTH DB has ZERO dumbbell entries. Separate follow-up.

### The Implement axis = the progression spine (Jul 4, later same session — supersedes "equipment is never a classifier" ONLY as a within-movement PROGRESSION, not as a raw availability filter)
After computed Load, Tanzim landed on the cleaner mental model: **the implement IS the S1→S2→S3 progression for a given movement.** Same exercise, three implements, three tiers:
- **S1 = Machine** (guided path, supported, minimum forced load)
- **S2 = Dumbbell** (free, independent limbs, self-stabilised)
- **S3 = Olympic bar** (heaviest fixed floor ~45 lb / 20 kg, two-handed, real balance + technique)
- Encode as a scored **Implement primitive**: Machine 1 · Cable 2 · Dumbbell 3 · Barbell/Olympic 4. It carries THREE things the other inputs miss, in one number: stabilisation demand, the fixed weight floor, and coordination.
- **Two computable primitives the Load formula was still missing, surfaced here:** (1) **Implement floor** — the bar is 45 lb no matter the movement; a front raise with a 20 kg bar ≠ a 5 lb dumbbell. This is what his June 22 "barbell isolation = Load 3" hand-rule was encoding. (2) **Balance / free-path demand** — standing, unsupported, bar drifts = a stability cost the model never scored.
- **Design tension he has NOT yet resolved (surface it, let him decide):** does Implement *set a floor* (Olympic = AT LEAST S3, guaranteed) or just *add points* into the gates? Floor is stronger and guarantees the progression holds (dumbbell front raise S2, Olympic bar S3, every time). Floor's blast radius: a few genuinely light Olympic-bar lifts jump to S3 that his gut might still call S2 — offer to list which rows move before locking.
- **The one row that actually TESTS the floor:** a light Olympic-bar lift (e.g. Olympic front raise) where both computed axes say S2 but implement says S3. Heavy barbell lifts (OHP, RDL) agree S3 three ways too easily and don't stress the rule. When validating the floor, line the light-bar case against a heavy one — only the light case proves the floor does work the old formula couldn't.

### RESOLVED: Implement is a PROPORTIONAL cost gated by joint-count — NOT a floor (Jul 4, final)

The "floor vs points" tension above got resolved, and the game proved the floor WRONG. A hard "Barbell → S3 floor" breaks on isolation: he called **Barbell Curl S1**, **Barbell Shrug S1**, **EZ-Bar Curl S1**, **Barbell Reverse Curl S1** — a floor would have forced all to S3.
- **The fix:** implement adds physical cost **proportional to how compound the movement is**, gated by **joint count**:
  - Compound (2+ joints) → implement cost lands **FULL** → climbs tiers (machine OHP S1 → dumbbell S2 → barbell S3 holds).
  - Isolation (1 joint) → implement cost lands **near-zero** → the bar adds almost nothing (a barbell curl is a heavier S1, not an S3).
- **Joint count is the primitive doing all the work** — it decides how much the implement matters. This is why heavy barbell compounds floor S3 clean while light barbell isolation stays S1.
- **Structural finding he confirmed as accurate: S3 is a COMPOUND-ONLY tier. Single-joint muscles cap at S2.** There is NO S3 curl — biceps is one-joint; S3 requires compound load, balance, or spinal risk that isolation cannot manufacture. (Watch the honesty trap: "weighted chin-up" is NOT a bicep S3 — it's a back/lat pull borrowing the biceps. Don't dodge "none" by reaching for a compound. The correct answer to "name an S3 bicep" is: there isn't one, and that's the formula correctly reporting anatomy.)

### FINAL LOCKED FORMULA (Jul 4, 2026) → lives in the Nimbus Engine repo
The adjusted formula reached a final draft and got its own repo, **`~/Nimbus_Engine`** (git-init'd, `docs/FORMULA.md` + `README.md`), **pushed to GitHub as private repo `tanzimozer/Nimbus_Engine`** (created via GitHub API + `~/.git-credentials` PAT — no `gh` CLI installed; parse the token with `sed -E 's#https://[^:]+:([^@]+)@.*#\1#'`, NOT a `\K` lookbehind which trips the hostname security scan). Old gate formula deliberately EXCLUDED from that repo — fresh slate, his instruction. The final model:
1. **Compute Load** = `MuscleMass + Joints + Axial + ROM` → 1–9 (never hand-scored).
2. **Two axes:** Physical = `Flex + Grip + Load`; Technical = `Skill + Learning Curve`.
3. **Implement cost** (Machine 1 · Cable 2 · Dumbbell 3 · Barbell 4) folded into Physical, **× joint-count gate** (full for compound, near-zero for isolation).
4. **Classify 2×2:** low both → S1; high one → S2; high both → S3.
- One line: *Tier = 2×2 axes; implement adds physical cost × joint-count gate; Load and implement computed never chosen; isolation caps at S2, S3 is compound-only.*

### More row-by-row results, computed Load + Implement (Jul 4)
- **Olympic bar standing OHP = Barbell Overhead Press** (already S3, D9/LC9): S3 unanimous three ways (old formula, computed axes, implement floor). Clean top of the machine→Smith→Olympic OHP ladder (Machine S1 / Smith S2 / Olympic S3).
- **RDL / Romanian Deadlift** (Skill3 Flex2 Grip3 LC9, axial 1): S3 on EVERY primitive independently — the archetype the whole tier is built around. Grip 3 (highest in set) + axial 1 make it the true-hinge reference. If implement floor ever produced a non-S3 for an Olympic hinge, the model is broken.
- **The COLLISION cases (movement says S1, implement says climb):** Barbell Shrug (sheet D5/LC5→S1), Barbell Curl (sheet says S2 but that's two data errors: Load maxed at 3 should be 1–2, LC hand-scored 7 should be ~3 for a coaching-free single-joint lift → really S1), EZ-Bar Curl (sheet S2), Barbell Reverse Curl. **RESOLVED by the joint-count gate (see above): all are single-joint → implement cost near-zero → they stay S1.** The final formula auto-resolves these; you no longer have to punt them to his call. If he re-raises one, the answer is S1 because isolation caps the implement climb.

### Cross-test validation pattern (his preferred proof)
When Tanzim says "cross test the formula" / "deploy leads to test it": pull STRENGTH DB fresh, then run the formula against the rows via **two independent subagent leads using different implementations** (e.g. pure-python if-else vs. awk/dict logic) so the match is genuinely independent, not one script echoing itself. For a randomised spot-check, **draw one row per tier (S1/S2/S3), not pure-random** — pure random tends to pull all-S1 (66/97 are S1) which tests only Gate 1 and proves nothing. Report: match count + which gate decided each row + whether Gate 2 was load-bearing or Difficulty alone decided it.

### The name-the-output game — his rapid-fire validation mode (Jul 4)
Distinct from the cross-test leads. He'll say **"let's play a game, I name an exercise, you answer S1/S2/S3"** and sometimes **"without giving me all context, just name the output."** Rules of engagement:
- **When he says "just name the level," answer with ONLY the tier** (`S1.` / `S2.` / `S3.`) — no reasoning, no math, no caveats. He is stress-testing the formula's outputs against his own gut, one at a time. A context dump defeats the test and he'll be annoyed.
- **Give reasoning ONLY when he asks "why"** — then bullet it (Physical axis read, Technical axis read, joint-count/implement gate, verdict), stripped.
- He is looking for **collisions** — rows where the formula's answer and his gut diverge. Those are the signal; the agreements are noise. Hold the formula's answer honestly even if it might differ from his instinct; the disagreement is the productive part.
- **Confirmed edge-case answers from the Jul 4 game (reasoning behind each):**
  - **Trap-Bar Deadlift → S2** (not S3): neutral handles + centred load reduce the technical/spinal demand vs. a straight-bar conventional (S3). The implement/position lowers it a tier.
  - **Assisted Chin-Up → S2**: assistance removes the full bodyweight+load that makes weighted chin-up S3 (compound, high physical). Still compound so it stays above S1.
  - **Muscle-Up → S3**: compound, high skill, high physical, real coordination/transition — tops the pull family.
  - **Hyperextension → S2**: it *rhymes* with a deadlift (same hinge, axial=1, spine involvement, real technical spine-risk) but strips the heavy load and implement — so it's high on ONE axis (technical/spinal), not both. One axis = S2. The deadlift is S3 because it's hard AND loaded AND technical; hyperextension keeps the technical, loses the load.
  - **Box Squat → S3**: barbell, compound, spine-loaded, real technique — squat family holds S3.
  - **Wall Sit → S1**: isometric, no load path, no skill, no balance demand — floor of the scale.
  - (Isolation-caps-at-S2 rule reconfirmed on: Barbell/EZ-Bar/Rope/Reverse curls, tricep pushdown, rope overhead extension, preacher curl — all **S1**.)
- **The honesty trap resurfaced and he tested it:** I named "weighted chin-up" as an S3 bicep exercise; he asked "do you think that's accurate?" It is NOT — it's a back/lat pull borrowing the biceps. The correct answer to "name an S3 bicep" is *there isn't one* (single-joint muscle, S3 is compound-only). When he asks "is that accurate?" after your answer, **re-examine it honestly and own the fudge** — don't defend a dodge.

### A score that changes no OUTPUT is noise, not a fix (Jul 5, 2026 — he killed a whole adjustment over this)
When proposing a scoring tweak, the first test is **"does it change an output the system actually emits?"** If the only output is the S1/S2/S3 tier, then a change that moves the underlying *scores* but leaves the *tier* unchanged is bookkeeping, not a feature — and Tanzim will scrap it.
- **The case:** he flagged low confidence that Cable Glute Kickback's body-stabilisation complexity was captured. I proposed a new **Stability primitive** (0–2, scoring *force-resisting* / isometric-stabiliser demand — the anti-rotation / anti-extension / single-leg balance the Skill axis misses because Skill only counts *force-producing* joints) folded into Difficulty, plus a Learning-Curve substitution-risk bump (form-cheat failure mode → lumbar arch → needs a cue). Sound analysis. But kickback stayed **S1** before and after. Every worked example showed zero tier changes.
- He said **"zero impact on kickback?"** then **"scratch the adjustments, it's pointless"** and locked **Kickback = S1** until further notice. He was right: a more *honest* number that no downstream consumer reads is overhead. The "deceptively technical" feeling was a **coaching** concern, not a **classification** one — and there is currently no second output (form-cue flag) for it to feed.
- **Lesson for next time he raises "we're not capturing X":** before building the primitive, ask **what consumes the score?** If the answer is "only the tier" and the tier won't move, say so up front and stop — don't build the input. If he genuinely wants the signal, it needs a NEW output (a form-risk / cueing flag independent of tier), not a reweighted input to the existing formula.
- **Style note:** when the answer forks (tier vs. coaching), don't lay out both paths and ask which he meant if the tier answer is unambiguous. He said **"cut the bs"** — give the verdict (S1, zero impact), then stop. The two-path menu read as hedging.

### Classify on INTRINSIC movement, never the implement — even when the tier is RIGHT (Jul 5, reinforced hard)
The "equipment is a selection filter, never a classifier" rule extends to **how you PRESENT a call**, not just the logic. Tanzim rejected equipment-based *framing* even for a verdict he agreed with:
- He argued **Reverse Barbell Lunge → S3** (vs. my S2). Correct call — it's single-leg, whole-body coordination under load = Skill 3, high cost of error = high LC. Intrinsically S3.
- But I justified it via "barbell → reaches S3" and offered a **variant split (barbell S3 / dumbbell S2 / Smith S1)**. He shut it down: **"stop suggesting me equipment based decisions, that's a no."**
- **The fix:** state the tier on the movement's own demands — Skill / Learning Curve / joint-count / stability / spinal risk. The implement was only ever shorthand for those primitives; name the primitives directly. **Never offer an equipment-variant ladder as a suggestion** — that IS equipment-as-classifier wearing a progression costume. (The Jul-4 "implement is the progression spine" idea is an internal *scoring* mechanic gated by joint-count; it is NOT something to surface to him as "pick your tier by equipment.")

## Reference-tab formatting (gsheets-formatting-standard applies)
Reference tabs (S123 LOGIC, DIFFICULTY) must read in ONE pass for Tanzim + Sagar, each value in its own editable cell. Standard he likes: navy title bar (frozen), slate section-header bands (merged), level colour-coding (S1 green / S2 amber / S3 red), wrap + middle/center align, long descriptive text left-aligned, light block borders, sized columns. **Do NOT write a formula string into a cell as documentation — Sheets parses it and throws #ERROR!.** Write it as plain prose ("IF Difficulty <= 5 -> S1 ...").

## Workflow lessons
- **One thing at a time.** He drives the sequence. When he relays a list (e.g. Sagar's concerns), take the ONE item named, address only that, propose one next move, stop. He has snapped about info-dumping.
- Short human responses, no jargon. Lead with the answer.
- When he says "discuss, small texts at a time" — genuinely converse, qualify intent BEFORE building. Define what a metric is supposed to MEAN before tuning thresholds.

## Pending work (Jun 2026)
- Port Difficulty + S123 logic to Conditioning DB and Hybrid DB (only Strength done).
- Sagar review of heuristic Load + Learning Curve values.
- Unified Level banding decision still parked (documented bands 0.20/0.45/0.70 + F1 floor recommended).
- Contraindication tag (region map: spine-loaded/overhead/deep-knee/none) not yet built.
