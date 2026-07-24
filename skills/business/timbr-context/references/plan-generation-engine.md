# TIMBR — Plan Generation Engine & Exercise Data Model

The architecture behind TIMBR's workout plan generator. Load when working on the exercise DB, stages, muscle pairings, or any plan-generation task. Source-of-truth doc lives in Quip (being retired Mar 2027 — migrate to Drive/Sheets).

## Source-of-truth spreadsheet
**"TIMBR — Muscle Pairing (Right vs Wrong)"** — Sheet ID `1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo`. Owned by Sagar (so copy with `copy_permissions=False`). Tabs:
- **Strength DB / Foundation DB / Performance DB** — each 120 exercises. As of this session they were IDENTICAL placeholders (all tagged "Strength Training"); the real work is sorting the exercise universe into the three tiers.
- **DIFFICULTY / LEARNING CURVE / RISK SCORING** — the scoring methodologies (formulas below).
- **STAGES** — the full 9-stage journey, fully built (F0 → Level 3).
- **Pairings** — right/wrong muscle pairing matrix. The "WHAT'S WRONG" side is TRUNCATED at 6 rows in both the doc and this sheet — this is a known gap to fill.

Working draft created this session: "TIMBR — Plan Generation DRAFT (Friday × Tanzim)" `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`.

## The 9 columns of the Exercise DB
`Exercise Name | Muscle Group | Muscle Size (Big/Small) | Muscle Part | Difficulty (1-10) | Learning Curve (1-10) | Risk of Injury (1-10) | Type of Exercise | Needs Spotter/Safeties`

12 muscle groups, 10 exercises each: Chest, Back, Shoulder/Deltoid, Traps, Bicep, Tricep, Forearms, Core, Glute, Hamstring, Quad, Calf.

### Dual classification (Tanzim's explicit decision) — DESIGN INTENT, NOT YET BUILT
Keep TWO type columns, not one:
- **TIMBR Classification** = Strength / Performance (the stage-engine selection label)
- **Actual Classification** = Strength / Aerobic (the raw physical nature of the movement)

**CORRECTION (verified live 2026-06-20):** the "Actual Classification" column does NOT exist in the sheet yet. Performance DB has exactly **8 columns**: `Level | Exercise Name | Muscle Group | Muscle Size | Muscle Part | Difficulty | Learning Curve | Risk of Injury`. The dual-classification scheme above is a design decision, not a built field. Do not claim it exists — verify the header row before relying on any column. (I asserted it was "built on the 19th" and was wrong twice this session; always read the actual header.)

**The Aerobic pool already lives inside Performance DB** as the **"Full Body" muscle-group rows** (~19: Rowing Machine, Ski Erg, Stair Climber, Spin Bike, Assault Bike, Air Bike Tabata, Treadmill Sprints, Shuttle Runs, High Knees, Jump Rope ×2, Mountain Climbers, Burpees, Squat Thrusts, Sprawls, Bear Crawl ×2, Crab Walk, Inchworms). They're just not tagged aerobic-vs-explosive.

**SUPERSEDED — Tanzim REVERSED this call (2026-06-21).** The earlier "TAG don't TAB" decision (mark a Col I Strength/Aerobic on Performance DB, no separate tab) was overturned. The settled architecture is now **separate tabs by movement nature**:
- **STRENGTH DB** — pure muscle/strength, sets-and-reps.
- **CONDITIONING DB** (NEW, gid 1295861004) — continuous, HR-driven HIIT/circuit/metabolic work. This is the home for the previously-orphaned "HIIT — Conditioning" day label (Sagar's point 1).
- **HYBRID DB** (NEW, gid 1185360157) — the grey-zone movements that serve both (loaded carries, sled push/drag, KB swings/clean&press, thrusters, wall ball, devil's press, sandbag work).

**Routing rule (locked 2026-06-21):**
- **Strength session** = 100% Strength (+ may pull from Hybrid).
- **Performance session** = 50% Strength(+Hybrid) / 50% Conditioning(+Hybrid).
- The tab IS the classification — an exercise lives in one tab by its nature, so no per-exercise ratio is needed to *route* it. The Muscle:Fat Ratio becomes optional nuance for grey cases, NOT the load-bearing router. (Tanzim's reframe: Performance is a session *recipe*, not a tag an exercise carries — no single exercise "belongs to" Performance; what's unique to Performance is the conditioning half.)

The new tabs were built this session mirroring the existing DB format exactly (navy header rgb(30,40,56), white text size 12 centered, frozen row 1 + 2 cols, identical 13-col widths) and verified with a 3-stage hub-n-spoke check (header parity / math integrity / business rules). Seed sets only: CONDITIONING DB ~15 rows (C-prefix levels), HYBRID DB ~14 rows (H-prefix), to be expanded after sign-off.

## The level taxonomy (branching periodization with F3 convergence)
This is the smart core of the product. Three categories:
- **Foundation** — beginner/teaching/reset phase. Mobility, stability, technique. KPIs: consistency, accuracy, recovery. Beginner-safe subset: low difficulty (≤4), low risk (≤3), bodyweight/band/machine, no spotter, plane-restricted basics + core stability.
- **Strength** — pure lean-mass / load progression. Machines + dumbbells + barbells, heavier/more sets/fewer reps, minimal cardio/core. KPIs: grip strength, tonnage, load progression, lean mass.
- **Performance** — overall human performance = 50% strength / 50% aerobic (HIIT, cardio, circuit, stamina). Fat-loss focus. KPIs: VO2max, work capacity, body comp. NOTE: Performance is a *block recipe* (mix per session), not purely a per-exercise tag — hence the dual-classification scheme above.

Later tiers (not yet built): Hyrox I/II (strength+conditioning circuit, timed), Longevity I/II (sauna/dexa/cryo/IV — runs parallel, conditional on app usage), Evolve (yoga/pilates/zumba), Elite (top tier, hyrox+spa+longevity).

### The flow (branching tree)
```
Foundation 1 → Foundation 2 → ┬ Strength 1 → Strength 2 ──┐
                              └ Performance 1 → Perf 2 ────┴→ Foundation 3 → ┬ Strength 3
                                                                             └ Performance 3
```
F3 is a deliberate **convergence/deload point** — resets before the next heavy block to prevent plateau and burnout. This is the design element to preserve and praise.

## 9-stage journey maps (the STAGES tab)
13 stages mapped (St0→St12), each 2–3 weeks, with ember/flame/asterix stage names. Two goal tracks diverge:
- **Muscle Building (MB):** F0 → F1 → S1 → F2 → S2 → P2 → F3 → S3 → P3 → h1 → L1 → h2 → L2
- **Fat Loss (FL):** F0 → F1 → P1 → F2 → P2 → S2 → F3 → P3 → S3 → h1 → L1 → h2 → L2

Key periodization moves:
- **Stage 6 & 9 = CROSSED**: MB lifter runs a Performance block (recomp), FL lifter runs a Strength block (preserve muscle while cutting). Deliberate cross.
- **Stage 8 = MATCHED**: MB→Strength 3, FL→Performance 3.
- **Sex priority (locked rule):** Male → upper-body emphasis (more upper days/splits); Female → lower-body emphasis (glutes/hams fractioned for volume).
- **Pairing splits progress:** antagonist pairs (Chest+Back) at Level 1 → tighter synergist pairs (Chest+Tri, Back+Bi) at Level 2 → body-part isolation at Level 3.
- **Inviolable rule:** no day mixes big-upper with big-lower.
- Each row covers 3/4/5 days/week × Male/Female. No "Push/Pull/Legs" naming — labels are muscle-pairing/body-part based.

## Scoring formulas (the SCORING tabs)
- **Difficulty** = Stability + (Strength×2) + Flexibility + Grip − 4, capped at 10. Each input scored 1–3. Strength counts double (biggest beginner limiter). "Learn" excluded — it has its own rating.
- **Learning Curve** = (Learn×3) + Stability − 2, kept 1–10. Machines ~2, barbell big lifts ~9, Olympic-style 10.
- **Risk** = Likelihood × Severity (worst-link, NOT a sum). Severity 1=benign / 2=tissue exposure / 3=catastrophic. Catastrophic = 8–9, −3 with spotter. 7 catastrophic-pin lifts flagged Spotter=Yes: barbell bench (flat/incline/decline), close-grip bench, back squat, front squat.
- **Level Score (F0–F3 composite)** = (Risk×0.40) + (Difficulty×0.35) + (Learning Curve×0.25), range 1–10. Bands: F0 = 1.0–2.5 (absolute novice), F1 = 2.6–4.5 (beginner w/ gym time), F2 = 4.6–7.0 (intermediate), F3 = 7.1–10 (advanced). **Per-tab floor:** Strength/Performance DBs cannot read below F1 (a loaded barbell move is never "absolute novice"); Foundation has no floor. This formula IS internally consistent — verified row-by-row it reproduces every Level Score exactly; the math is sound. The weak point is the *inputs*: Risk carries the highest weight (0.40) but in the data sits mostly at a lazy floor of 2 — under-rated risk silently corrupts the tier (Sagar's example: Barbell Reverse Lunge rated Risk 2 when it should be 6–7). Risk needs a per-exercise re-score pass; it was NOT validated per-exercise.
- **Muscle:Fat Ratio (LOCKED 2026-06-21, written into SCORING LOGIC as section ⑤)** = (Load×0.5) + (Rest×0.3) + (Continuity×0.2), 0–1 scale where **1 = pure muscle-building, 0 = pure fat-loss**. Inputs each 0–1: Load (heavy/low-rep→1, light/high-rep→0), Rest (long→1, circuit-pace→0), Continuity (discrete sets→1, sustained continuous→0). Replaces the dead binary "Actual Classification" column (which was flat "Strength" on all 96 Strength rows — Sagar's point 2: you can't binary-label cardio vs strength). Reference values: heavy barbell squat ~0.95, loaded carry ~0.5–0.6, HIIT sprint ~0.1.

## Muscle pairing matrix
12 groups → 66 possible pairs. Doc confirms 34 VALID + 6 INVALID; the rest must be inferred. Inference rules (from the doc's own logic):
- Same upper region → valid (shared push/pull pattern).
- Same lower region → valid.
- Core pairs with EVERYTHING (universal stabiliser/finisher).
- Any upper+lower cross → invalid (session fatigue, no synergy). Doc states "Chest + any leg" and "Bicep + any leg" explicitly — generalise from there.
When building the full matrix, tag each pair Confirmed (from doc) vs Inferred (filled by logic) so it can be audited fast.

## The selection engine (BUILT — `references/selection-engine-design.md`)
The pick-rule open question is RESOLVED and a working generator exists. Input `(goal, sex, days/week, stage)` → full weekly session with real exercises. Core logic:
- **STAGE_MAP**: each stage → (tier, difficulty_cap). E.g. St1=Foundation/cap4, St3 MB=Strength/cap6 + FL=Performance/cap6, St5=cap8, St8/9=cap10. Crossed stages (6,9) swap tier per goal.
- **Day-label → muscle resolver**: 'Upper'/'Chest+Back'/'Legs'/'Glutes+Hams' etc. map to muscle-group lists; 'Aerobic' pulls from Performance-Aerobic pool.
- **Pick rule**: filter tier DB by `muscle == slot AND difficulty <= cap`, sort by difficulty DESC (hardest allowed = progression feel), take N. **Big muscle → 2 exercises, small → 1.** Performance tier or FL goal → append an Aerobic conditioning finisher.
- **Guardrail**: flag/reject any day mixing big-upper {Chest,Back} with big-lower {Glute,Hamstring,Quad}.
See `references/selection-engine-design.md` for the full module + the WEEK_SPLITS lifted from the STAGES tab.

## Open questions Tanzim still owns (don't assume answers)
1. Whether MB and FL are eventually two entirely separate programmes or one DB filtered per stage.
2. Alternate-workout substitutions per exercise.
3. **Execution-level distinction** (reps/sets/load) is NOT yet in the DB — so Foundation 2 (free-weight intro, capped) and the crossed-execution stages (6, 9) currently differ by tier/cap only, not rep-scheme. Adding reps/sets/load columns is the next data layer for true execution-level plans.

## Working style for this project (observed)
- Tanzim drives via voice memos, one question at a time — he gets impatient with multi-question blasts ("one question at a time", "make it concise"). Ask ONE sharp question, wait.
- **HARDENED (2026-06-21): one thing at a time, and DON'T dump.** He snapped "YOU ARE DUMPING TOO MUCH INFORMATION ON ME — let's address one thing at a time" after Friday answered all six of Sagar's review points in one structured block. When he's working through a list of concerns, surface EXACTLY ONE — answer it, stop, let him pick the next. Do NOT pre-empt with the full triage even if you've already mapped all the issues internally. Hold the analysis; release it one beat at a time. This overrides any urge to be thorough or show the full picture.
- He wants visuals first — share the live sheet link before discussing.
- Formatting standard he asked for explicitly: **wrap text always, vertical-middle, horizontal-center, columns sized to content, rows spaced, header bold + frozen.** Apply this to any TIMBR sheet by default.
- Never touch the live source sheet — always work on a draft copy.
- He authorises generous subagent/research deployment ("deploy as many agents as you want, no limits") — Veronica is his research agent persona for deep web research.
- **The draft sheet is edited CONCURRENTLY** by Tanzim's own AI/other builders ("I will apply a lot to work on the sheet as well... let's see if our work is better"). Consequence: always re-read the DB tabs FRESH at generation time — never cache row counts or contents across turns. He runs a build-off and picks the better output; offer to fold in the best of both rather than defend yours.
- **State of the draft (`1WrA1wi...`):** Foundation/Strength/Performance DB tabs are POPULATED (Foundation ~67 beginner-safe, Strength = original 120, Performance ~54 conditioning movements filling the cardio gap). A `PLAN GENERATOR (demo)` tab holds worked examples. Strength DB had column I ("Needs Spotter/Safeties") removed at his request — it now has 8 columns.
- Honest-flag standard he values: ratings from research agents are a fast first pass and **have NOT been validated against the scoring formulas** — always surface this before he leans on the numbers.

## DRAFT sheet — verified live structure (2026-06-20)
Sheet `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`, title "TIMBR — Plan Generation DRAFT (Friday × Tanzim × Claude)". Tabs and gids:
- FOUNDATION DB (gid 1007006981) · STRENGTH DB (653476118) · PERFORMANCE DB (1615007886)
- CONDITIONING DB (gid 1295861004, NEW 2026-06-21) · HYBRID DB (gid 1185360157, NEW 2026-06-21)
- TRAINING SPLIT (1046226275) · MUSCLE PAIRING (2001) · MUSCLE BUNDLES (1363876170)
- RULES (1235482689) · SCORING LOGIC (65557771) · PROGRESSION LOGIC (314741848)

NOTE: the DRAFT DB tabs now carry a **13-column header** (not 8): `Level | Exercise Name | Muscle Group | Muscle Size | Muscle Part | Difficulty | Learning Curve | Risk of Injury | Actual Classification | Level Score | Unified Level | (blank) | Muscle:Fat Ratio`. Always read the live header — it has grown past the old 8-col schema noted elsewhere in this file.

DB tabs share the 8-column header: `Level | Exercise Name | Muscle Group | Muscle Size | Muscle Part | Difficulty | Learning Curve | Risk of Injury`. Level prefixes: F0–F3 (Foundation), S1–S3 (Strength), P1–P3 (Performance). Performance DB grid: 104 rows × 8 cols, frozen header + 2 cols, no banding, no conditional formats.

**TRAINING SPLIT** contains the per-stage day grids and is where "Aerobic" (Stage 2) and "HIIT — Conditioning" (Performance) appear as day labels that have no matching dataset rows — this is the mismatch Sagar flagged. **SCORING LOGIC** defines Difficulty (= Stability+Strength+Flexibility+Grip), Learning Curve (= Learn+Stability), and Risk (= Likelihood×Severity) with worked examples — this is the SAME Difficulty metric as the DB columns (Sagar's point 2: confirmed identical). The RULES tab defines the Foundation/Strength/Performance *buckets*, NOT difficulty — don't conflate RULES with SCORING LOGIC.

## Sagar's "step 2" definition asks (2026-06-20) — engine must absorb
Sagar reviews at night and drives definition-sharpening. Four points raised:
1. **Aerobic mismatch** — resolved by Tanzim's tag-don't-tab call above.
2. **Difficulty identity** — dataset Difficulty == SCORING LOGIC Difficulty. Confirmed, no change.
3. **F0–F3 must be a COMPOSITE**, not difficulty alone — combine Difficulty + Learning Curve + Risk of Injury. Needs: explicit 1–10 definitions for each of the three axes, the meaning of each score, then a documented methodology mapping the composite → F0/F1/F2/F3. (Currently the Level label is manual and only loosely tracks Difficulty — e.g. an F2 move at Difficulty 6 but Learning Curve 3.)
4. **New "Muscle-building : Fat-burn ratio" column (0–1)** in Strength & Performance DBs — routes each exercise Strength vs Performance by ratio. (His texted example "0.67→performance / 0.24→performance" is mistyped; one branch is Strength.) **RESOLVED 2026-06-21:** formula locked (see Scoring formulas), but the *routing* job moved off the ratio onto the tab split (Strength/Conditioning/Hybrid) — ratio is now nuance, not router.

## Sagar's SECOND review (2026-06-21) — 6 concerns, resolved/in-progress
Distilled to three real problems:
- **A. Taxonomy incoherence** (his pts 1,4,5): Level column says S1–S3 but output column says F1–F3 — sheet does both, reconciles neither. F0–F3 bands defined but no S/P bands. No rule for which tier a score-of-5 lands in. → being addressed by the clean tab architecture.
- **B. Dead classification column** (his pt 2): "Actual Classification" = "Strength" on all 96 rows, "Muscle:Fat Ratio" = flat 0.8 on all rows — zero information. → RESOLVED: retire binary column, Muscle:Fat Ratio formula locked (above).
- **C. Input data quality** (his pts 3,6): formula math is sound, but Risk inputs are under-rated (mostly floored at 2). Needs a per-exercise Risk re-score. NOT review-ready until done.
Build order agreed: A (architecture) → B (ratio) → C (re-score risk across all rows). Bottom line Friday gave Tanzim: the sheet is a coherent skeleton with three load-bearing cracks — not yet the validated foundation the app needs.

## Safe-edit discipline for these sheets (Sagar reads them; never break format)
Before ANY write to a TIMBR sheet a third party reviews:
1. Read the live header row fresh — never assume a column exists (see the Actual-Classification miss above).
2. Pull grid properties (`spreadsheets.get` with `fields=sheets(properties,bandedRanges,conditionalFormats)`): check `frozenRowCount`/`frozenColumnCount`, banding, conditional formats so a write won't disturb them.
3. Prefer **non-destructive column append** (write to the first empty column to the right) over in-place edits — a 400 on reading an empty range like `I1:K80` actually confirms the target is clear.
4. For borderline data calls (e.g. is Battle Rope aerobic or strength?), present the clear-cut buckets + the handful of borderline rows with a recommended lean, and get the ruling before writing. Single cells are trivially flippable, so bias to "write my defensible lean, you flip any you disagree with."
