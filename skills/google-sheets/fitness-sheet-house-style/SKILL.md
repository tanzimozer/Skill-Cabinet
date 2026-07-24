---
name: fitness-sheet-house-style
description: Tanzim's house formatting style for the fitness training Google Sheet (STRENGTH/CONDITIONING/HYBRID DB and all reference/logic tabs). Apply automatically whenever creating or rewriting a tab in this sheet — never ask whether to format, just do it.
---

# Fitness Sheet House Style

**Rule: when I create or rewrite any tab in Tanzim's fitness sheet, I format it to this style automatically. Never ask "want me to format it?" — he's asked for this many times. Just deliver it formatted.**

Sheet id: `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`
Helper: `/home/hermes/gs.py` (functions: get, put, meta, gid, svc, SHEET). Write access authorised.

## CURRENT TAB STATE (post-consolidation + curate, 2026-07-09) — 8 tabs
After the cleanup + curate passes the sheet is: `SOURCE OF TRUTH · TRAINING SPLIT · FX - 2 · STRENGTH DB · CONDITIONING DB · HYBRID DB · MUSCLE PAIRING · S Level Progression`. (An **archive** tab `STRENGTH DB — FULL 95 (archive)` also exists — see em-dash warning below — holding the pre-curate full 95.)
- **FX - 2** = declared source of truth for S123 (tables + live worst-axis formula + S1/S2/S3 glossary).
- **SOURCE OF TRUTH** (all-caps, renamed from RUBRIC 2026-07-09) = the full framework: scoring rubrics (Skill/LC/Risk + Conditioning + Hybrid) → validation roadmap → Difficulty inputs → Muscle:Fat → Exercise Classification (ex-RULES) → Progression Matrix (ex-PROGRESSION LOGIC). This is now the accretion sink, NOT "Rubric" — re-list titles, don't trust old names.
- **STRENGTH DB** = now a **curated 150-row 50/50/50** tab (was full 95 → curated to 60 20/20/20 → 90 30/30/30 → 150 50/50/50), col A live worst-axis formula. The full 95 lives in the archive tab. **S Level Progression** = a live-mirror tab now at **150 rows, 5 columns**: A Computed Level + B Exercise Name (live cell-refs) · **C Vector Plane (hardcoded plane-of-motion text, manual attribute)** · D Muscle Group + E Muscle Part (live cell-refs from STRENGTH DB C/E). Tier tints on col A (green/amber/red), plane column centred.
- **RETIRED (all backed up to /tmp before deletion):** `S123 LOGIC` (folded glossary into FX-2), `RULES` + `PROGRESSION LOGIC` (merged into SOURCE OF TRUTH), `Nimbus` (dead sandbox), `fx` (100% redundant). Also the empty husks S-1-2-3/F-0-1-2-3/P-1-2-3 were confirmed blank. If an old note below still calls any of these "live", it's stale — this state block wins.

## ⚠ Em-dash (or any non-ASCII) in a tab name BREAKS A1-range API calls — silent HTTP 400 (bit me 2026-07-09)
Naming a tab `STRENGTH DB — FULL 95 (archive)` (em-dash `—`, U+2014) makes **every** `values().get/update` and `spreadsheets().get(ranges=[...])` on it fail with `HttpError 400 "Unable to parse range"` — even with the title single-quoted. The URL-encoded em-dash (`%E2%80%94`) doesn't round-trip through the range parser.
- **Workaround that works:** read the tab from a **backup JSON** you saved earlier, OR read by **gid** via `includeGridData=True` WITHOUT a `ranges=` filter (whole-sheet grid pull), then slice locally. `deleteSheet`/`updateSheetProperties` by sheetId still work fine — it's only *range-string* ops that break.
- **Better fix: don't create the problem.** Name archive/scratch tabs ASCII-clean — `STRENGTH DB ARCHIVE 95`, not `— FULL 95`. Offer to rename any em-dash tab you inherit.

## The style
- **Title row**: merged across used columns, navy background `{0.12,0.18,0.32}`, white bold ~13pt, centred/middle. **Freeze row 1.**
- **Subtitle/anchor row** (if any): merged, italic ~10pt.
- **Header row**: light grey-blue background `{0.85,0.87,0.92}`, bold, centred.
- **Body**: wrap = WRAP, vertical = MIDDLE, horizontal = CENTER by default. Left-align long prose columns (definitions/meanings).
- **Band/level colours** (green→red severity ramp):
  - S1 / easy / low: green `{0.78,0.91,0.79}`
  - S2 / mid: amber `{1.0,0.95,0.70}`
  - S3 / hard / high: red `{0.96,0.78,0.76}`
  - For finer ramps insert light-green `{0.85,0.93,0.78}` and orange `{0.99,0.85,0.65}`.
- **Borders**: SOLID around + inside the main data block.
- **Column widths**: size to content — narrow for codes/scores (~90px), wide for prose (~300–460px).
- Font: Arial, body ~10pt.

## How
Use `gs.svc.spreadsheets().batchUpdate` with repeatCell (userEnteredFormat), mergeCells, updateBorders, updateDimensionProperties (widths), updateSheetProperties (frozenRowCount). Get sheetId via `gs.gid("TAB NAME")`.

### Pitfalls / patterns (learned)
- **Pad short rows before indexing.** `gs.get()` returns ragged rows — trailing empty cells are dropped, so a row may have fewer than the expected columns. Indexing `r[1]`/`r[3]` then throws IndexError. Always normalise first: `data = [(r + [""]*4)[:4] for r in data]` (match your column count). This bit me mid-format and forced a re-run.
- **Find section rows dynamically, never hard-code row numbers.** When rewriting a multi-section logic tab (definitions / formula / decision tree / mapping), the row offsets shift whenever content changes. Use a `findrow(prefix)` helper that scans col A for a section title prefix and returns its index, then build all merge/colour/freeze ranges relative to those. Makes the formatter survive content edits.
- **Colouring level bands in a mapping:** distinguish lone band sub-headers (`r[0] in S1/S2/S3 and not r[1]` → merge + colour full width) from body rows (`r[0] in S1/S2/S3 and r[1]` → colour just the level cell). Same green/amber/red ramp.

### Syncing rule (cross-tab consistency)
Tanzim's standing expectation: **things should always sync.** When STRENGTH DB changes (column values, formula location, distribution counts, naming), any reference/logic tab that describes it (e.g. S123 LOGIC, the Rubric tab) must be updated in the same pass. Rebuild dependent tabs *from live DB data* rather than hand-editing — read the DB, recompute counts, regenerate the mapping. Check for stale references: formula cell pointers (col letter), "X/97 match" figures, and per-level counts are the usual drift points.

### Re-scoring an input column — CHECK STATIC vs LIVE FIRST (learned, bit me)
Before changing any input that feeds a formula (Skill, Flex, Grip, Load → Difficulty; Difficulty/LC → Level), check whether the *downstream* column is a live formula or static pasted numbers. Read it with `valueRenderOption="FORMULA"`:
```
gs.svc.spreadsheets().values().get(spreadsheetId=gs.SHEET, range="STRENGTH DB!F2:F5", valueRenderOption="FORMULA").execute()
```
- **Computed Level (col A) IS live** — it recomputes from Difficulty/LC automatically.
- **Difficulty (col F) is STATIC numbers**, not a formula. Changing Skill does NOT ripple — you must manually recompute Difficulty `max(2,min(9,(Skill*2)+Flex+Grip+Load-3))` for the changed rows and write F too, else the DB goes internally inconsistent.
- **Always model the blast radius before writing**: print old→new for the changed input AND every downstream value (Difficulty, Level, distribution counts), confirm it matches intent, THEN write. Tanzim wants to see the fallout before it lands — especially when a column feeds the classifier.

## Column design principle: INTRINSIC, never circumstance (load-bearing rule)
Tanzim's core modelling rule, enforced repeatedly. **A scoring/classification column must measure a property of the exercise itself — not the gym, the user, or the situation.** Anything circumstantial is a *filter*, not a classifier, and belongs in its own separate column.
- **Equipment never classifies** — the gym may lack the tool; it's a selection filter.
- **Mitigation never classifies** — "needs a spotter / needs a coach" is a Risk Gate (filter), separate from intrinsic Risk of Injury (consequence if the rep goes wrong). Deadlifts: low spotter-need but max intrinsic risk → score 9, not low.
- **Watch for proxy leakage.** A score can secretly re-encode a banned axis. Learning Curve tracked equipment almost perfectly (machine→2, barbell→9) — equipment sneaking back in wearing a different hat. Flag and rescore against an explicit rubric when you spot this.
- **The fix is always: write an explicit rubric tab** (anchored definition per score band), then re-score every row against it. Heuristic numbers "mean whatever the last person felt" — a rubric makes them defensible and survives Sagar's review.
- **All scoring rubrics now live in ONE tab: `Rubric`** (consolidated 2026-06-22 — the old separate `LC RUBRIC`/`RISK RUBRIC`/`SKILL RUBRIC` tabs were merged then deleted). Sections, stacked: Skill/Coordination → Learning Curve → Risk of Injury → Classification Gates. Each axis: anchor line + score bands (green→red) + a "why this grain" note. Keep adding new axes as sections here, not as new tabs.
  - Skill/Coordination is **1–3** (NOT 1–9) because it's doubled in the Difficulty formula `(Skill×2)+Flex+Grip+Load−3` which caps at 9 — keep it coarse or the scale blows out. A 2→3 Skill bump = +2 Difficulty, enough to cross the S1 gate, so the 3-band must be earned (genuine full-body coordination, not just "heavy").
  - Learning Curve: 1–9, anchor = time-to-unsupervised-competence. Risk: 1–9 intrinsic consequence, with explicit risk≠mitigation note.
- **S123 classifier — LOCKED & LIVE (worst-axis MAX model, confirmed ~2026-07-09).** The long convergence (Sagar's symmetric MAX proposal) landed here: **S-Level = MAX(Difficulty, Learning Curve, Risk) → ≥7 → S3 · 4–6 → S2 · ≤3 → S1.** Lives as a live per-row formula in the **FX - 2 tab** (S-Level column A), which is now the **declared source of truth** for classification. Exact cell formula: `=IF(COUNT(C7,D7,E7)=0,"",IF(MAX(C7,D7,E7)>=7,"S3",IF(MAX(C7,D7,E7)<=3,"S1","S2")))` (C/D/E = Difficulty/LearningCurve/Risk on that row; auto-reapoints if columns are reordered).
  - **Threshold history — don't regress:** an earlier draft said ≥8→S3 and the even-older locked tree was Diff≤5→S1 / LC≤7→S2 / else→S3. Both are RETIRED. The ≥8 was an assistant error Tanzim corrected verbally ("7 or above → S3"); the two-gate tree was superseded by the symmetric MAX model. If any tab still cites either, it's stale — see the reconciliation pattern below.
  - **DEPRECATED (historical):** old locked rule Difficulty ≤5 → S1 · else LearningCurve ≤7 → S2 · else → S3, computed in STRENGTH DB col A. STRENGTH DB col A labels were scored under THIS dead rule and were wrong under the MAX model (e.g. Bent-Over Row read S2, truth S3). **RESOLVED 2026-07-09** — Tanzim explicitly said "apply FX-2 formula to STRENGTH DB", lifting the freeze: col A is now the live worst-axis formula (see "Applying the FX-2 formula to STRENGTH DB" below). The "DB stays frozen" rule is NOT permanent — he waives it when he wants the DB brought onto the truth.

## Applying the FX-2 formula to STRENGTH DB — column repoint + the freeze gets lifted (2026-07-09)

When Tanzim says "apply the FX-2 formula to STRENGTH DB", he is deliberately overriding the earlier "DB stays frozen" rule — col A goes from static old-rule labels to the live worst-axis formula. Run it:
- **The axis columns sit DIFFERENTLY than FX-2 — repoint before writing.** In FX-2, Difficulty/LearningCurve/Risk are **C/D/E**; in STRENGTH DB they're **F/G/H** (col order: A Computed Level · B Exercise · C MuscleGroup · D MuscleSize · E MusclePart · F Difficulty · G LearningCurve · H Risk · I Skill · J Flex · K Grip · L Load · M Cluster). Blindly copying FX-2's `MAX(C7,D7,E7)` would read MuscleGroup/Size/Part as numbers. Read the header row first, map the three axes to their real letters, THEN build the formula. STRENGTH-DB per-row formula: `=IF(COUNT(F2,G2,H2)=0,"",IF(MAX(F2,G2,H2)>=7,"S3",IF(MAX(F2,G2,H2)<=3,"S1","S2")))`.
- **Col A is NOT clear — it holds 95 static old-rule labels.** Back it up (`/tmp/strengthdb_preformula_backup.json`), then compute expected-new vs old-label per row to surface the corrections BEFORE writing (`valueInputOption="USER_ENTERED"` so the `=` formulas evaluate).
- **Report the corrections as a pattern, not a raw diff.** 31 of 95 labels were wrong under the dead rule. Two clean buckets: **6 promoted S2→S3** (7+ on an axis the old gated rule missed — Bent-Over Row, Barbell Curl, Close-Grip Bench 7/7/7, T-Bar/Pendlay/Yates Row, Hip Thrust, both Skullcrushers) and **25 promoted S1→S2** (mid-tier lifts the old `Diff≤5→S1` gate dumped into S1 — Lat Pulldowns, Leg Press, Hack Squat, Smith work, Shrugs). Naming the mechanism ("worst-axis catches the 7s the gated rule didn't") beats listing 31 rows.
- **Verify LIVE, not from your own compute.** Re-read col A with `valueRenderOption='FORMATTED_VALUE'` (evaluated results) AND `'FORMULA'` (confirm the formula landed), then assert every row matches `MAX>=7/S3, <=3/S1, else S2` — zero mismatches. Distribution came out **S1 47 · S2 20 · S3 28** across all 95.
- **Flag the full-DB vs curated-subset distinction:** STRENGTH DB's 47/20/28 is the *whole* 95-exercise DB; FX-2's 20/20/20 was Tanzim's curated subset. They're not supposed to match — say so, or he'll think one is wrong.

## Curating a DB to N-per-tier (95 → 60 20/20/20) — ARCHIVE FIRST, curate by diversity (2026-07-09)

When Tanzim says "turn STRENGTH DB into 20/20/20" (curate the master down to N-per-tier):
- **CHALLENGE IT FIRST — this deletes rows from the master.** STRENGTH DB is the record; trimming it to 20/20/20 means dropping 35 exercises AND FX-2 already IS the curated 20/20/20 view. Present numbered options: (1) leave DB full + FX-2 stays the curated view [recommend], (2) curate DB down but archive the full set first, (3) format DB into tables keeping all rows. Don't silently trim a master.
- **On "option 2": duplicate → archive → THEN trim.** `duplicateSheet` the tab first (`newSheetName` ASCII-clean, NOT em-dash) so the full set survives as a static snapshot. State plainly the archive is a snapshot, not a live mirror — edits to the trimmed tab won't propagate to it.
- **Curate for SPREAD, not the tail.** Don't just keep the first N rows. Greedy-select to maximise unique **Muscle Group** then unique **Cluster** per tier (multi-pass: new-group-AND-new-cluster first, then new-group, then new-cluster, then alphabetical fill). Each tier should span 8–11 muscle groups, no cluster over-stacked.
- Whichever tier already sits at exactly N (S2 was 20) → keep all, curate only the over-full tiers.
- Write with col A = **live formula** (not static labels), clear the tail below the last row, verify distribution + zero formula-mismatch + no dup names.

## Adding N-per-tier with AUTHORED exercises — compute Difficulty, QC before write (2026-07-09)

When Tanzim says "add 10 more per S level, compute and quality check":
- **Inventory the pool per tier FIRST.** Check the archive for leftover exercises not yet in the curated set (`set` diff on names). S1 had 27 spare → pull 10; S2 had **0 spare** → must author 10 new; S3 had 8 spare → pull 8 + author 2. Pull-from-archive beats inventing where possible.
- **When authoring: COMPUTE Difficulty, never eyeball it.** For each new exercise assign the raw inputs (Skill 1–3, Flex, Grip, Load) + hand-score LC and Risk against the rubric bands, then run `Difficulty = max(2, min(9, (Skill*2)+Flex+Grip+Load-3))`. Then compute the level via worst-axis `MAX(Diff,LC,Risk)` and **assert it lands in the intended tier BEFORE writing** — print `OK/BAD name D/LC/R sk/fl/gr/ld → level` for every authored row, require 0 BAD.
- **Authoring by category gap:** S2 needed a whole missing class — the **dumbbell tier** (DB bench/incline/Arnold/Bulgarian-split/goblet/step-up: Skill 2, moderate LC/Risk → lands S2 cleanly). When a tier can't be filled from archive, look for an equipment/movement category the DB lacks rather than nudging scores to force a level.
- **Final QC reads LIVE, not your own compute.** After writing (col A live formula, `valueInputOption="USER_ENTERED"`), re-read with `FORMATTED_VALUE` and assert every row's evaluated label matches `MAX>=7→S3 / <=3→S1 / else S2` — zero mismatches — plus no duplicate names, tier blocks in order (30 S1 / 30 S2 / 30 S3), tail empty. "Compute and quality check" means the QC verifies the SHEET's live output, not the numbers you fed in.

## Expanding a tier list to N-per-tier — AUTHOR AN OVER-POOL so any bad row is dropped, not backfilled (30→50, 2026-07-09)

When Tanzim says "increase each level to N, compute each row, check accuracy, and **if you find an error find another exercise so we still have N**" — the last clause is the whole design. He wants a guaranteed-N result with no scrambling at the end. The pattern that delivers it:
- **Inventory first: archive-leftover vs must-author, per tier.** `set`-diff current tab names against the archive to see what's reusable. This session S1 had 17 spare (pull) + author 3; S2 had **0 spare** (author all 20); S3 had 0 spare (author 20). Pull-from-archive always beats inventing.
- **Author an OVER-POOL, not exactly N.** Write MORE candidates than needed per tier (authored 22 for S2/S3 when 20 were needed). Compute every candidate's Difficulty `max(2,min(9,(Skill*2)+Flex+Grip+Load-3))` → worst-axis level → **keep only the ones that land in the intended tier AND aren't duplicate names**, then select the best 20 for muscle-group spread. The surplus IS the "find another exercise" instruction pre-satisfied: if 2 of 22 miscompute, you still have 20 clean ones and never come up short. All passed first-time this session, but the margin was there by design — that's what he asked for.
- **Selection = diversity greedy.** From the valid pool, pick to minimise repeat Muscle Group then repeat Cluster (sort each pick by `(seenGroup[g], seenCluster[c])`, take the least-represented). Each 50-tier spanned 8–11 groups.
- **Author by CATEGORY GAP, not score-nudging.** When a tier can't fill from archive, find an equipment/movement class the DB lacks: S2's gap was the **dumbbell + landmine** tier (Skill 2, moderate LC/Risk → S2 cleanly); S3's was **heavy-barbell + Olympic derivatives** (deficit deadlift, rack pull, power/hang clean, push press/jerk, thruster, overhead/pause squat → LC/Risk 7-9 → S3). Never tweak a score to force a level.
- **Two-stage QC — pre-write compute assert AND post-write live read.** (1) Before writing, print `OK/BAD name D/LC/R sk/fl/gr/ld → level` for every authored row, require 0 BAD. (2) After writing (col A live formula, `valueInputOption="USER_ENTERED"`), re-read `FORMATTED_VALUE` and assert: every evaluated label matches `MAX>=7→S3 / <=3→S1 / else S2` (0 mismatches), **Difficulty recomputes** correctly per row (`(Skill*2)+Flex+Grip+Load-3` vs stored F), no dup names, tier blocks in order (50/50/50), tail empty. "Check that everything is accurate" means QC the SHEET's live output plus a Difficulty re-derivation — not just the numbers you fed in.

## ⚠ `valueRenderOption` has NO 'USER_ENTERED' — that's a WRITE option. Reads take FORMULA/FORMATTED_VALUE/UNFORMATTED_VALUE (bit me 2026-07-09)

Backing up a tab's formulas before overwrite, I called `values().get(..., valueRenderOption="USER_ENTERED")` → instant `TypeError: "USER_ENTERED" is not an allowed value in ['FORMATTED_VALUE','UNFORMATTED_VALUE','FORMULA']`. `USER_ENTERED`/`RAW` are `valueInputOption` values for **writes** (update/batchUpdate); they are NOT read render options. To back up live formulas before a destructive write, read with **`valueRenderOption='FORMULA'`**. Easy to conflate the two option families — write=input, read=render.

## Populating a MANUAL attribute column — derive by cluster→value map, static text not live (Vector Plane, 2026-07-09)

When Tanzim adds a manual attribute column (Vector Plane = plane of motion) and says "populate it," derive the value per exercise from an existing intrinsic field rather than hand-typing 150 cells:
- **State your working definition up front so he can redirect in one word.** Vector Plane = NASM plane of motion — Sagittal (front-back: press/squat/hinge/curl), Frontal (side: lateral raise, abduction/adduction, shrug, upright row), Transverse (rotational/horizontal: horizontal press+row, incline/decline, flye, rear delt, woodchop, pallof). Give the mapping basis (by prime-mover *joint action*, so horizontal bench/row = Transverse via shoulder horizontal ad/abduction — flag this, since some coaches file bench under sagittal by *body travel*).
- **Map by CLUSTER, not by name.** Pull the unique Cluster set, assign each cluster → plane once, apply across all rows. Far fewer decisions than per-exercise, and consistent by construction. Show the Transverse + Frontal picks for eyeball QC (Sagittal is the default majority — don't list it). This session: 104 Sagittal · 33 Transverse · 13 Frontal.
- **It's HARDCODED text, not a formula** — a manual attribute has no source column to reference. Say so plainly: it won't auto-update if the DB reorders. Offer a Cluster→plane VLOOKUP wire-up as the alternative if he wants it live.
- **Sync the mirror to the source FIRST.** S Level Progression still mirrored 90 rows while STRENGTH DB was 150 — extend the live A/B/D/E refs to 150 before writing the plane column, then format the new rows (tier tints, centred plane col) since extension rows come in unstyled white.

## Live-mirror tab — two columns pulled by cell-ref, never a static copy (S Level Progression, 2026-07-09)

When Tanzim says "new tab, columns X and Y **from** STRENGTH DB" (emphasis on *from*): build it as a **live mirror**, not a paste. Each cell is a cross-tab reference `='STRENGTH DB'!A2` / `='STRENGTH DB'!B2` down all N rows, with the real header text on row 1. Edits to the source tab (score change → level recompute, name edit) propagate automatically — zero drift. State it's a live mirror, not a snapshot, so he knows it stays in sync. Then format to house style (below) — a mirror still needs formatting; the refs carry values, not styling.

## Source-of-truth reconciliation — when a rule locks, erase every contradicting restatement (2026-07-09)

When Tanzim declares one tab/formula "the source of truth" and says "scan the whole sheet and erase any misinformation / remove the previous logic that contradicts it," run this exact sequence — **read-only first, destructive only after confirmed scope:**
- **Enumerate ALL tabs before touching one** — `spreadsheets().get(includeGridData=False)` gives every title + gid + row/col dims. This sheet runs ~15 tabs; several are empty shells (S-1-2-3, F-0-1-2-3, P-1-2-3 returned 0 non-empty cells — confirm with `includeGridData=True` counting formattedValue, don't assume from a blank A1:Q read).
- **Pull with `valueRenderOption='FORMULA'`** so you see the actual live formula in logic cells, not its displayed result. This is how you catch a tab that *restates* the old rule in prose vs one that *computes* it.
- **Bucket every tab against the truth:** (a) **direct contradiction** — restates the retired formula as "current/locked" → replace; (b) **stale data** — labels computed under the old rule (STRENGTH DB col A) → flag, DON'T wipe if it's under the "DB stays intact" rule, ask; (c) **self-labelled sandbox** — Nimbus says "does NOT modify" → leave; (d) **different job** — RULES/PROGRESSION LOGIC/RUBRIC classify Foundation/Strength/Performance or hold axis rubrics, NOT S123 banding → no conflict, leave.
- **Present the scope as numbered options and get the pick before any write** — even when authorised, restate exactly which tabs you'll edit and which you'll leave frozen. Tanzim picked "remove the previous logic that contradicts" = the two formula tabs only (fx, S123 LOGIC), DB left frozen, sandbox untouched.
- **Edit surgically, not by rewrite.** Pull exact coordinates (`values().get` the small block), then a targeted `values().batchUpdate` (valueInputOption RAW) hitting only the offending cells: replace the formula string, clear the stale "proposed" row, rewrite the decision-tree gates, and **flag the old mapping/counts as SUPERSEDED with a pointer to the truth tab** rather than deleting the whole section.
- **Leave deliberate supersession breadcrumbs.** After the edit, a dead-rule regex sweep will still "find" the old rule inside your own notes ("Supersedes the old Diff≤5/LC≤7 tree", "SUPERSEDED... retired ... rule"). That's intentional — naming the retired rule stops a future session re-landing on it. Distinguish breadcrumb from residue in the verify step.
- **Verify: re-read the edited blocks + run a dead-rule regex across both tabs**, confirm the only surviving mentions are your supersession notes. Backup lives in the read-only scan JSON captured before any write.
- **Dead-rule regex has FALSE POSITIVES across DBs — the retired Strength gate `LC≤7` is ALSO a LIVE gate for Conditioning (C1/C2/C3) and Hybrid (H1/H2/H3).** When the sweep flags an `else Learning Curve ≤ 7` hit, check WHICH classifier the section belongs to before "fixing" it. FX-2 governs Strength S123 only; the C123 and H123 two-gate formulas legitimately reuse the same `LC≤7` mastery gate and are NOT misinformation. Confirmed 2026-07-09: two flagged hits at Rubric rows 68/164 were the Conditioning-Intensity and Hybrid-Demand gates → left correctly. Only the STRENGTH gate is dead.
- Inputs (LC, Risk, Skill) are *my* rubric scores until Sagar validates — always flag that caveat; never present heuristic scores as ground truth.

### Folding a near-redundant logic tab into the truth tab, then deleting it (S123 LOGIC → FX-2, 2026-07-09)
Once FX-2 became the declared source of truth, S123 LOGIC was ~90% a duplicate of FX-2's header (same formula, same decision tree). The one non-duplicate asset: the **S1/S2/S3 meaning glossary** (plain-English "what each level means") — FX-2 had the rule but not the definitions. Play when Tanzim says "do we need this tab?" then "you know it" (= yes, fold + delete):
- **Test each block: duplicate (drop) vs gap-filler (keep).** Formula/tree = duplicate → drop. Glossary = the one thing FX-2 lacked → fold in.
- **Append the survivor BELOW the last table so nothing shifts** — glossary went to FX-2 rows 74–77 under Table 3, not inserted mid-sheet.
- Delete the tab via `deleteSheet` (get its gid from `meta`), verify title is gone from the tab list. Backup was already in the read-only scan JSON from the reconciliation pass.
- Rationale to state: "two sources for one rule is how drift crept in the first time" — one tab owns rule + tables + glossary.

## Merging reference tabs by RENAMING THE ANCHOR — don't rebuild 150+ styled rows (Source of Truth, 2026-07-09)

When Tanzim says "merge tabs X, Y, Z and name it N," and one of them is large + already house-styled (RUBRIC = 165 rows of navy/blue banners + green→red bands), **rename the biggest styled tab to the new name and APPEND the others as new sections** — do NOT create a blank tab and rebuild everyone's formatting from scratch. Preserving the anchor's styling is the whole win.
- **Order sections by workflow logic**, not tab order: classify → score → place. Chosen order was RULES (how to sort) → RUBRIC axes → PROGRESSION LOGIC (the ladder), but the anchor (RUBRIC) stays first physically since it's the rename target; RULES + PROGRESSION appended after.
- **Pull the anchor's exact banner swatches first** (`includeGridData=True`, read effectiveFormat) so appended banners match: this tab uses navy `{0.12,0.16,0.22}` for major section banners, blue `{0.20,0.28,0.45}` for sub-banners, white bold. Merge each new banner across the used column span, set bold/white/navy to match.
- **Append math:** spacer row → banner row → the tab's values (pad ragged rows to the target col count) → spacer → next banner → next values. Compute row offsets from `len()` of each source block, never hard-code.
- **Fix contradictions found IN the anchor while you're there** — RUBRIC rows 33–36 still carried the retired Strength gates (`Diff≤5→S1 / LC≤7→S2`); a tab about to be named "Source of Truth" can't restate the dead rule. Rewrote them to the worst-axis gates (`≤3→S1 · 4–6→S2 · ≥7→S3`) in the same pass.
- **Delete the source tabs only after the append is verified** (`deleteSheet` each gid), confirm the new name is present and the old titles are gone. Backup all three (values + full grid formatting) to a JSON before any of this.
- **Stale self-references survive the merge** — the appended PROGRESSION LOGIC prose still says "see the RULES tab" which now lives in the same tab. Cosmetic, flag it, offer a "see above" repoint; don't silently rewrite his prose.

### Killing a dead SANDBOX tab (Nimbus, 2026-07-09) — "do we need X?" → "kill it"
Nimbus was a stress-test sandbox self-labelled "does NOT modify S123 LOGIC or STRENGTH DB", built to validate the **old gated formula** (v1/v2 both `LC≥8→S3 / Diff≤5→S1`). Once the worst-axis MAX model became truth, the whole tab tests a buried engine. The recommendation shape when Tanzim asks "do we need this?":
- **Trace every asset to the current truth.** Nimbus's "breaks" (isolation-floor myth, LC muted below Diff 5, knife-edge fit) were **artifacts of the gated formula** — worst-axis `MAX()` has no gates, so those failure modes don't even apply. Nothing transfers → "a museum of a formula we buried."
- **Check the one thing worth salvaging BEFORE recommending delete** — Nimbus's validation-roadmap thinking already lives in SOURCE OF TRUTH (rows 71–102), so it's fully redundant. Say that explicitly so the cut is clearly safe.
- Delete only on confirmation ("kill it") → backup (`/tmp/nimbus_backup.json`) → `deleteSheet` → verify title gone + report new tab count.

### Retiring a FULLY-redundant scratch tab (fx, 2026-07-09) — the last-mile cleanup
`fx` was the three-line formula-reference scratch pad the whole project grew from. By session end every line duplicated somewhere better: Difficulty derivation → SOURCE OF TRUTH rows 104–131; LC/Risk anchors → rows 12–31; S123 rule → FX-2 + SOURCE OF TRUTH. **100% redundant, nothing original left.** When a tab has zero unique content, there's nothing to fold — just back up + delete. State the per-line redundancy map ("this lives here now, that lives there") so the emptiness is demonstrated, not asserted, then delete on the go-ahead.

### Redundancy-first, THEN the rename (SOURCE OF TRUTH caps, 2026-07-09)
When Tanzim says "remove redundancy in tab X, also capitalize it", do the dedup pass FIRST, rename LAST (so the verify reads the final title). The internal-redundancy defects a merged/accreted tab carries:
- **Double headers** — the merge banner ("EXERCISE CLASSIFICATION…") sits right above the original tab's own title row ("TIMBR CLASSIFICATION — HOW WE SORT…"), saying the same thing twice. Collapse to one.
- **A fact restated 3×** — "F0–F3 bands the Difficulty score" appeared at three separate rows; keep the one in context, delete the standalone repeat.
- **Scaffolding tags left in banners** — "(merged from RULES)" / "(merged from PROGRESSION LOGIC)" are build artifacts; strip them from the final banners.
- **Stray multi-blank gaps** from the append math. Delete redundant rows **bottom-up** (0-indexed, highest first) so earlier deletions don't shift later indices, batch them with the rename `updateSheetProperties` in one `batchUpdate`.
- Rename to all-caps via `updateSheetProperties(title=...)`; verify the classification section still reads clean (no orphaned headers) after the row deletions.
- **Flag orphan notes, don't fold them:** a half-formed "Draft – if 5 muscle groups in a day, small muscle gets 1 exercise only" line rode along from RULES — a real rule with no home. Name it for his next pass; don't silently relocate or delete a half-baked rule.

## Column-review workflow (how Tanzim audits the DB)
He walks the STRENGTH DB **one column at a time** ("column J?", "what about flexibility?", "next"). For each, the expected response shape:
1. **Name it and pull it** — header + value distribution (`Counter`) + grouped examples. Don't theorise before reading.
2. **Classify its role** — this is the key judgement he wants:
   - **Live formula input** (Skill, Flex, Grip, Load → feed Difficulty) — changes ripple, must model blast radius.
   - **Standalone reference** (Risk of Injury) — scored, synced, but feeds nothing computed. Always state plainly that it gates nothing.
   - **Orphan** — feeds nothing AND has no clear job AND/OR overlaps an existing axis.
3. **Apply the orphan test → recommend a cut.** Stability was cut because it (a) fed no formula and (b) duplicated coordination already captured by Skill's band-3. When a column is an orphan that overlaps an existing axis, the lean is **cut it** for a cleaner DB — say so directly. He responded "cut it if we don't need it."
4. **For live inputs**: check whether the scoring is already sound before proposing changes. Grip and Flexibility needed no edits — say "well-scored already, no changes" rather than inventing work. Note when a correction would be *classification-neutral* (e.g. a lift already capped at Difficulty 9 — fixing its Flex 2→3 is cosmetically truer but moves no Level). Offer it as an honest "data-honesty pass" he can decline.
5. Close with the standing decision-question (next column / park here).

**Deleting a column**: back up first, then `deleteDimension` (COLUMNS, startIndex/endIndex). Re-verify Level distribution is unchanged after. Remember every column to the right shifts left by one — re-read headers before the next column op (after the Stability cut, Flexibility moved J→ its new index).

## Tab-audit pattern (when asked "what can we delete?")
Read every tab's first ~6 rows + dimensions, then bucket: **empty shells** (header-only, superseded → safe delete), **stale/contradictory** (old dropped formulas that would mislead Sagar → strong delete), **overlap/consolidate** (current but duplicative → merge call, not auto-delete), **keep** (distinct live purpose). Report buckets, recommend, but **take no action unless told** — he often says "report back" / "standby". Salvage-before-delete: flag any unique content worth rescuing (e.g. a validation plan) before a tab goes.

### Retire-and-salvage pattern (FX, DIFFICULTY — both folded into Rubric 2026-06-22)
When a tab is mostly stale BUT holds one section the live system lacks, **fold the useful part into Rubric, then delete the tab** — don't bin it whole, don't keep it standalone. Two ran this session:
- **FX**: formula definitions were actively wrong (still cited cut `−3`/Stability), the v2-critique described already-fixed bugs → all dead. The one survivor: the **5-phase validation roadmap + deferred-to-v3 items** (Sagar's coach-review path). Rescued as a "Validation Roadmap" section in Rubric, then FX deleted.
- **DIFFICULTY**: formula/Skill bits duplicated Rubric. The survivor: the **Flex/Grip/Load anchor definitions + 6 worked examples** — Rubric documented Skill in detail but only *named* the other three inputs, so this *completed* Rubric rather than duplicating it. Folded in, tab deleted.
**Test before folding:** does the section duplicate Rubric (drop it) or fill a gap (keep it)? State which. Always backup → append to Rubric (navy section title, bold sub-headers, house style) → delete tab. Four tabs retired this way across the session (FX, MUSCLE BUNDLES, DIFFICULTY, SCORING LOGIC) — Rubric is the consolidation sink for anything scoring/logic/validation related.
- **SCORING LOGIC** (retired 2026-06-22): both halves stale — v1 used the pre-today system (`Stability + Strength×2 − 4`, F0–F3 banding, Risk weighted 0.40); the v2 "active proposal" still cited the deleted Risk Gate column and cut Stability. The one survivor: **Muscle:Fat Ratio** (`(Load×0.5)+(Rest×0.3)+(Continuity×0.2)`, 0–1, with input anchors + worked examples) — unique, still-live, formula locked but values unscored. Folded into Rubric, stays flagged OPEN on TASK PENDING.

## Porting the classifier to CONDITIONING / HYBRID DB (the S123→C123 pattern)

The S123 logic ports to the other DBs by **swapping axes, keeping the two-gate shape** — don't copy the Strength formula literally, it's a *load* model that's meaningless for cardio.

**CONDITIONING DB (built 2026-06-22, 12 cols, 28 exercises):**
- Cols: `Computed Level · Exercise Name · Muscle Group · Muscle Size · Muscle Part · Intensity · Learning Curve · Risk of Injury · Output · Coordination · Impact · Cluster`. (12 vs Strength's 13 — cardio has 3 intrinsic axes, not 4; no Load/Grip/Flex.)
- **Engine:** `Intensity = (Output×2)+Coordination+Impact−2`, capped 2–9, live formula. Output is the doubled term (metabolic ceiling = dominant driver — same role Skill plays in Strength's Difficulty).
- **Computed Level (col A), live:** `=IF(Intensity≤5,"C1",IF(LearningCurve≤7,"C2","C3"))`. Same two-gate logic: Intensity gates entry, LC gates mastery.
- **Three intrinsic axes, all 1–3:** Output (steady-state 1 → all-out 3), Coordination (fixed pattern 1 → whole-body-under-fatigue 3), Impact (gliding/seated 1 → jumps/hard-decel 3). Equipment never classifies — same rule.
- **Cluster = modality:** Erg/Machine · Jump/Plyo · Bodyweight Cardio · Locomotion · Implement.
- Rubric gets a **Conditioning section** appended (Output / Coordination / Impact / Intensity formula / Classification gates) — same one-tab pattern, not a new tab.
- **No C3 will exist** unless LC ≥ 8 is reached — conditioning rarely is "months to own" (double-unders top at LC 7, sprints 6). That's honest. If Tanzim wants a populated C3, only skill-heavy movements (double-unders, Olympic complexes, pistol/plyo combos) qualify — flag it, don't invent C3s by nudging the gate without asking.
- **Quality cross-match check** after scoring: Output→Intensity, Coordination→LC, Impact→Risk should loosely track; flag divergences. A *true-positive* divergence is worth keeping, not fixing — e.g. Kettlebell Swings = Impact 1 / Risk 4 is correct (low ground-impact, real lumbar risk from the loaded hinge). The heuristic catching the one case where Risk rightly diverges from Impact is the model working, not an error.

## Wiring two reference tabs into one source (MUSCLE PAIRING + BUNDLES, done 2026-06-22)

When two reference tabs encode the **same rule at different scopes** (MUSCLE PAIRING = the 2-muscle grid + Why; MUSCLE BUNDLES = the 2–N enumeration of the same upper/lower/Core rule), they can silently **drift** — both were precomputed, nothing checked them against each other. Tanzim's fix when he says "wire them / put them in one tab":
- **Pick a single editable source-of-truth block** — here a **Region Key**: each muscle → Upper/Lower/Core, the *only* editable cells (highlight them cream).
- **Derive everything else by formula off that key.** Grid cells: `=IF($A=col_hdr,"—",IF(OR(VLOOKUP(row,key,2,0)="Core",VLOOKUP(col,key,2,0)="Core",rowReg=colReg),"✓","✗"))`. Bundle Valid flag: `=IF(AND(SUMPRODUCT((regCol="Upper")*ISNUMBER(SEARCH(muscleCol,$Bn)))>0, SUMPRODUCT((regCol="Lower")*ISNUMBER(SEARCH(muscleCol,$Bn)))>0),"✗","✓")` — i.e. invalid iff the bundle string contains both an Upper and a Lower muscle.
- **Prove the sync, don't claim it.** Flip one source cell (Biceps Upper→Lower), read back that the grid AND a dependent bundle both flipped, then revert. Tanzim values the demonstration — "they physically can't drift now" must be shown, not asserted.
- Preserve the human-readable "Why" reasons from the old pairing tab (capture them into a dict keyed by `frozenset({a,b})` before the rewrite), re-attach to the 2-muscle bundle rows.
- Delete the now-redundant tab only after backup + verification (273 bundles present, grid 38 valid / 28 invalid matches original).
- Caveat that survives: the inferred/judgment-call pairings (e.g. Traps↔legs) still ride on the region rule — wiring stops drift, it does NOT validate those calls. Keep them flagged for Sagar.

## Rebuilding a tab from a husk — strip OLD FORMATTING, not just values (bit me 3× in one session)

When recreating a tab that previously held data (clearing values, then writing fresh rows), **clearing the cell *values* does NOT clear the cell *formatting*.** Leftover formatting from the old layout silently corrupts the new build. Three distinct failures hit in one session, all from the same root:

1. **Merged cells eat your writes.** The old MUSCLE PAIRING tab had 75 leftover merges (cols C–M merged per row). Writing a full-width grid silently folded every D-onward cell into the merged C cell — readback showed only 3 columns despite the API reporting "13 columns updated". **Diagnose:** read `meta()['sheets'][i].get('merges')`. **Fix:** `unmergeCells` over the whole range *before* writing, then re-put.
2. **Stray band fills in dead columns.** CONDITIONING husk left green fill in cols M–Q (past the 12-col DB) and even tinted the Cluster col that should be plain white. **Fix:** `updateCells` with `fields:"userEnteredFormat"` (clears all format) on the dead range, then `deleteDimension` to trim the sheet to exactly the used column count. Cluster/label columns get plain white, never a score band.
3. **Inconsistent row heights.** Old rows kept their 38px height; newly-added rows came in at default 21px → ragged. **Fix:** `updateDimensionProperties` ROWS with `pixelSize:38` across all body rows. House body-row height is **38px**, header 21px (match STRENGTH DB).

**Standing habit after any husk rebuild:** before declaring done, verify three things that values-readback won't show — (a) no leftover merges, (b) no stray backgrounds past the used columns / on label columns, (c) uniform row heights. Tanzim catches all three by eye ("lacks formatting consistency", "row thickness lacks consistency") so check them proactively.

4. **Header text clips when it wraps onto two lines.** STRENGTH's headers are short single words (Skill, Grip, Load) that fit one line at the 21px header height, so it never clipped. CONDITIONING has longer two-word labels (Computed Level, Learning Curve, Coordination) that wrap to two lines and **get cut off at 21px even with wrap=WRAP set correctly**. The wrap flag was fine — the *row height* was the problem. **Fix:** bump the header row to ~40px (`updateDimensionProperties` ROWS startIndex 0). When matching a tab to a "reference" tab, don't blindly copy its header height — copy it *only if* your labels are equally short; otherwise size the header to fit the longest wrapped label.

## `gs.gid()` is case-sensitive and fails SILENTLY → returns 0 (bit me this session)

`gs.gid("Rubric")` returned **0** when the actual tab title was "RUBRIC" (uppercase). 0 is a *valid* sheetId (it's the default first sheet's id), so the bad lookup doesn't raise — it silently targets the wrong sheet, and the eventual `batchUpdate` fails with `"No grid with id: 0"` (or worse, edits the wrong tab if id 0 exists). Note: a `put`/`get` by **range string** ("Rubric!A1") resolves case-*insensitively* server-side, so the data write can succeed while the `gid()`-based formatting/delete in the same script fails — a confusing split failure.
- **Habit:** match the exact title case. If unsure, list titles first: `[s["properties"]["title"] for s in gs.meta()["sheets"]]`.
- **Defensive `gid` lookup:** raise on miss instead of returning a falsy default, e.g. `next(s["properties"]["sheetId"] for s in gs.meta()["sheets"] if s["properties"]["title"].upper()==name.upper())`.
- Tab titles in this sheet have drifted to UPPERCASE over time (RUBRIC, not Rubric) — don't trust an old cased name from memory; re-list.

## Strength DB's own bands are hand-painted and inconsistent (don't replicate the noise)

When matching CONDITIONING colours to STRENGTH, I found STRENGTH DB uses **static per-cell backgrounds, not conditional rules** — and they're internally inconsistent (the same Difficulty score shows green in one row, yellow/red in another; LC 8 shows green). It was hand-painted, never value-driven. **Don't replicate a broken pattern** — apply a *clean, value-driven* version of the same three house swatches: green `(0.847,0.918,0.776)` · yellow `(0.976,0.929,0.847)` · red `(0.969,0.847,0.847)`. Wide axes (1–9): 1–3 green, 4–6 yellow, 7–9 red. Narrow axes (1–3): 1 green, 2 yellow, 3 red. Flag that Strength itself could use the same clean re-band as a follow-up.

## Extending an existing tab — band EVERY coloured column, then verify by EYE (bit me twice in one session)

When adding rows to an already-formatted tab (e.g. CONDITIONING 28→50), the new rows come in **unformatted white** and must be banded to match. The failure that hit twice in one session:

1. **I banded only SOME of the coloured columns and called it done.** CONDITIONING bands six numeric columns — Intensity, Learning Curve, Risk **AND** the three intrinsic axes Output, Coordination, Impact. I coloured F/G/H, forgot I/J/K entirely, and reported "all 50 rows fully banded." Tanzim caught the 22 white cells per column by eye. **Before extending, enumerate ALL coloured columns in the existing rows** (read backgrounds across the full header, not the ones you remember) and band every one of them on the new rows.

2. **I "verified" by reading my own applied RGB back and comparing it to my own rule** — which trivially passes and proves nothing. Reading the colours I just wrote and confirming they match the rule I just used is circular. **Real verification = check the columns I did NOT touch too, and check for `WHITE/none` (default `(1,1,1)`) cells in every banded column across the FULL row range.** The tell for a missed column is uncoloured cells, not a wrong colour. A quick probe: count white backgrounds per numeric column over all body rows — any nonzero count on a column that should be banded = a gap.

3. **"Looks consistent" off a partial read is the trap, not a result.** Twice this session I declared "done"/"consistent" after checking a subset; Tanzim's line was *"Next time CHECK before you tell me that."* Standing rule: **never report a formatting/data pass complete until I've read back the ENTIRE affected range across ALL relevant columns** — not the few I was actively editing. When he sends a screenshot, he's already seen the gap I missed; assume a partial check will be caught.

**CONDITIONING band rule (confirmed all 50 rows, value→colour):**
- Intensity (2–9): 4–6 yellow, 7–9 red (nothing scores <4, so no green appears).
- Learning Curve (1–9): 1–3 green, 4–6 yellow, 7+ red.
- Risk (1–9): 1–3 green, 4–5 yellow (nothing ≥6 yet).
- Output / Coordination / Impact (all 1–3): **1 green, 2 yellow, 3 red.** ← these are the ones I forgot; they're banded just like every other numeric axis.

Distribution after extending to 50: C1 14 · C2 35 · C3 1 (Depth Jumps, LC 8 — the first-ever C3, honest).

## HYBRID DB extend (14→50, done 2026-06-22) — same play as CONDITIONING

Extending HYBRID followed the exact CONDITIONING pattern, and this time I banded **every** numeric column up front (lesson from the prior screenshot catch — no white-cell gap). Specifics worth keeping:
- HYBRID engine: `Demand=(Skill×2)+Load+Output−2` cap 2–9 live; Level `=IF(Demand≤5,"H1",IF(LC≤7,"H2","H3"))`. Six banded numeric cols: Demand·LC·Risk·Skill·Load·Output.
- **HYBRID band rule (derived live from the original 14 rows, confirmed all 50):** Demand: ≤6 yellow, 7–9 red (no green — loaded work never scores <4 Demand). LC: 1–3 green, 4–6 yellow, 7+ red. Risk: 1–3 green, 4–5 yellow. Skill/Load/Output (1–3): 1 green, 2 yellow, 3 red. Same house ramp as Conditioning.
- Two new clusters added for the heavier end: **Strongman** (Atlas stone, keg/frame/axle, heavy farmers) and **Ballistic** (power/hang clean, push press, DB snatch, loaded jumps) on top of Carry·Sled·Kettlebell·Implement.
- Dist after extend: H1 1 · H2 41 · H3 8 — honest; loaded-conditioning clusters mid/high, rarely absolute-beginner.
- **Cross-DB Output sync is mandatory** — Sled Push/Drag, Sandbag, Devil's Press, DB Thruster, KB Swing, Wall Ball appear in BOTH Conditioning and Hybrid; their Output is intrinsic and MUST match. Dedup-check new names AND cross-check shared-movement Output against the other DB *before* writing. Caught zero drift this pass because the check ran pre-write.
- **Count your list before writing.** Proposed +36, the literal list held 35 → landed at 49 not 50. Always `assert len(new)==target` before the put, or you'll be patching in a straggler row after.

## Hardening the MUSCLE PAIRING bundle formula — exact-token, not bare substring (done 2026-06-22)

The original bundle Valid flag used `SEARCH(muscleName, bundleString)` — a **bare substring match**. It worked only by luck (no muscle name was a substring of another). The latent landmine: add "Glute"/"Glutes" or "Calf"/"Calves" and `SEARCH("Calves",...)` could false-match inside another token, silently mis-flagging bundles with no error.
- **Fix:** delimiter-pad both sides — `SEARCH(", "&$A$6:$A$17&", ", ", "&$Bn&", ")`. Pad the bundle string the same way so first/last tokens still match. Keeps the SUMPRODUCT scan structure (needed because bundles run 2–8 muscles; per-cell VLOOKUP doesn't fit a variable-length list).
- **Prove the fix bites — inject a live collision.** Don't just re-verify the 273 flags pass (they pass trivially). Temporarily rename a Lower muscle to a token that's a substring of an Upper muscle (e.g. Calves→"Ce", which lives inside "Tri-ce-ps"), read back that a Triceps bundle stays ✓ under the hardened formula (the old one would've flipped it ✗), then revert. The torture test is the proof, not the clean re-pass.
- **Protect the derived ranges (warning-only).** `addProtectedRange` with `warningOnly:True` over the grid (A21:M33) and the bundle Valid column (C36:C309). The instruction text "edit only the Region column" wasn't enforced — a warning catches accidental overtypes of the formulas without locking Tanzim out. Region Key stays freely editable as the single source of truth.

## "Why do we need this tab?" — answer the purpose, then offer the honest cut

When Tanzim challenges a tab's existence ("why do we need this?"), he's not always asking to delete — he's testing that it earns its place. Shape: (1) state its concrete consumer and what breaks without it (MUSCLE PAIRING = the validity filter the workout generator queries so it never builds "Quads+Biceps" splits), (2) name the alternative (bury the rule in script — brittle, unauditable), (3) **then give the honest counter** — if the generator is the only consumer and he'd rather the rule live in code, the tab IS redundant; it earns its place only if he wants the logic human-readable and coach-editable. Close by putting the call back to him. Don't defend reflexively; give him the real trade-off.

## Style: when proposing a build plan, LEAD LEAN — he'll ask for depth if he wants it

Twice-relevant this session: my first HYBRID-extend proposal was a 6-line cluster breakdown with every candidate exercise named; Tanzim's reply was *"too much information, simplify and concise and ask again."* The right shape for a build proposal is the **counts and the new clusters only** (e.g. "Carry 5→11, Sled 2→7, ... +Strongman, +Ballistic. Same guarantees. Build it?") — NOT the full exercise manifest up front. He approves on the shape; he'll see the actual list in the sheet. Save the per-item detail for when he asks, or for the post-build report. Default to the one-screen version of any plan.

## Consolidating two reference tabs without a destructive merge (RULES + PROGRESSION LOGIC, 2026-06-22)

Not every overlap is a merge. RULES (the classifier — decision order + "the test" for sorting a NEW exercise into Foundation/Strength/Performance) and PROGRESSION LOGIC (the lookup matrix of which actual exercises sit where) describe the **same branching at different jobs**. The right move was **cross-reference, not fold**: point RULES' one redundant row (scattered examples) at PROGRESSION LOGIC's full matrix, and add a back-pointer in PROGRESSION LOGIC to RULES for *how to classify*. Each keeps its distinct job; the duplication (and drift risk) is removed. Read both fully before deciding — and **stop if you find a load-bearing dependency**: RULES still cites the dead `Level Score = Risk×0.40 + Difficulty×0.35 + LC×0.25` and the deleted SCORING LOGIC tab, because that Foundation F0–F3 model lives NOWHERE else and TRAINING SPLIT still runs the 9-stage Foundation ladder. "Clean the stale bits" would have gutted a live model — so I split the work: consolidate the safe branching now, leave the Foundation scoring parked for an explicit decision. Surface the load-bearing find and get the call before cutting.

## Two-method quality check on request ("run quality check twice, in different ways")

When Tanzim asks for a double quality pass, give him **two genuinely different methods**, not the same recompute twice:
- **Pass 1 — forward recompute:** re-derive every formula output (Intensity, Computed Level) from the raw axes; assert against the live cell. Catches math/formula-drift errors.
- **Pass 2 — independent structural + cross-DB + logic:** (a) structure: no blanks, no col-count mismatch, no dup names, expected row count; (b) axis bounds: each axis within its rubric range (Output/Coord/Impact 1–3, Intensity 2–9); (c) value-type sweep: no text-in-number cells; (d) cluster validity against the allowed set; (e) **cross-DB intrinsic drift** — shared movements (Sled Drag, Sandbag Carry, Devil's Press appear in both CONDITIONING and HYBRID) MUST carry identical intrinsic scores; flag any divergence as a real bug; (f) logical-outlier sweep — score-sense checks math can't catch (Jump/Plyo with Impact 1, Erg/Machine with high Impact, Risk≫Impact heuristic flags for Sagar). The Risk≫Impact divergences are true-positives to surface, not errors to fix.

## Formatting an ACCRETED multi-section tab (Rubric full-format pass, 2026-06-22)

Because Rubric is the consolidation sink (every retired tab folds in here), it grows by accretion — and the formatting does NOT come along for free. When asked to "format the rubric correctly," the actual defect is almost always: **only the ORIGINAL section is styled; every section folded in later is bare text.** Diagnose before styling:
- **Read the live formatting state, don't reformat blind.** Pull `includeGridData=True` with `fields="...userEnteredFormat(backgroundColor,textFormat(bold,fontSize,foregroundColor))"` over the full tab and list which rows have a non-white fill. The styled section lights up (banners, grey table headers, green→red bands); the accreted sections show as a long unstyled gap. That gap IS the work.
- **Also catch banner-shade drift.** Banners added in different eras use slightly different navies (saw `{0.12,0.18,0.32}` vs `{0.12,0.16,0.22}` vs `{0.118,0.176,0.318}` in one tab). Unify ALL major section banners to the one house navy `{0.118,0.157,0.22}` — including the very top title row, which often kept an older shade.
- **Derive the style vocabulary from the ONE formatted section, then replicate to all.** Read the existing section's exact swatches (sub-header blue `{0.2,0.28,0.45}` white-bold, table-header grey `{0.85,0.87,0.92}` bold, score bands green/yellow/red, descriptor/formula rows light lavender `{0.93,0.93,0.95}`) and apply the identical vocabulary to every later section so the tab reads as one document, not five eras stacked.
- **Score bands apply to the score CELL only (col A), not the whole row** — Output/Coordination/Impact/gate rows get the green→yellow→red ramp in col A; the meaning/examples columns stay neutral.
- **Wider sub-tables need wider header bands.** Worked-example tables run past col C (Difficulty A:F, Muscle:Fat A:E, Anchors A:D) — band their headers to the actual span, not a fixed A:C. Check which rows have content past col C first (`any(c.strip() for c in r[3:])`).
- Close with wrap=WRAP + vertical TOP across the whole tab, numeric columns centred. Then verify banner unification by reading col-A backgrounds back across all banner rows in one pass (the title row is the usual straggler).

## Backtesting a proposed classifier change — run BOTH schemes over all rows (Sagar challenge, 2026-06-30)

When Sagar or Tanzim challenges the S/C/H classification rule ("this categorisation is wrong / the hardest should go to S3"), **never answer with an opinion — backtest.** Pull all rows, run the current rule AND every candidate rule over the full set, tabulate splits, and name exactly which exercises move and why. The shape that landed well:
- **Read-only path when not signed in:** the gviz CSV export gives you the data without write access — `curl -sL "https://docs.google.com/spreadsheets/d/<ID>/gviz/tq?tqx=out:csv&sheet=STRENGTH%20DB"` (URL-encode spaces in tab names). Works when the browser canvas won't expose cell text and when you're anonymous/read-only. Use `&gid=<n>` or `&sheet=<name>` to pick the tab.
- **Tabulate the split for each candidate** (S1/S2/S3 counts) side by side — the count delta alone tells you if a proposed rule is a tweak or a bulldozer.
- **List the exact rows that MOVE and the trigger** (which axis fired). One-line-per-mover with old level + all axis scores. This is what makes the recommendation defensible instead of hand-wavy.
- **Prove an axis is redundant with correlation, not assertion.** Risk of Injury was near-collinear with Difficulty/LC (corr D–LC 0.94, D–R 0.88, LC–R 0.89) AND zero high-risk (R≥8) exercises sat in S1 — so adding Risk as a gate changed **no** outcome. That's the argument for keeping it a reference axis, not a classifier. Compute `corr()` across axes and check "does this axis ever flip a classification" before agreeing to add it.
- **Distinguish the blunt instrument from the real fix.** Sagar's literal "any axis maxed → S3" moved only 1 row (strict =9) or bloated S3 (broad ≥8 pulled Risk in). The *spirit* of his catch was right — the current logic let a max-Difficulty lift (D8–9) land in S2 because it's quick to learn. The clean encoding of his intuition, minus the redundant axis:
  - **Refined S3 gate (2026-06-30): `S3 IF Difficulty ≥ 8 OR Learning Curve ≥ 8`.** Difficulty ≥8 catches the hard-to-execute-but-fast-to-learn lifts (carries, rows, skullcrusher, hip thrust) the old LC-only gate missed; LC ≥8 keeps the coached technical lifts. Risk stays out. Gives S3 = 21 (vs current 16). S3 definition in one line: **"requires coaching, or it goes wrong."**
  - Note: under the *current* locked rule, `LC ≥ 8` alone reproduces the existing 16-row S3 list exactly — Difficulty's only job today is the S1 gate. That's the latent flaw the refined gate fixes.
- **Keep the answer short when he asks for the definition** — "S3 = requires coaching or it goes wrong" + the two-line formula, not the whole backtest. The backtest is the *working*; the deliverable is one gate.
- **The symmetric MAX-model (Sagar, 2026-07-02) — the direction this is converging on.** Sagar reframed the whole classifier as symmetric: **level = MAX(D, LC, Risk)**, then `S3 if max ≥ HIGH · S1 if max ≤ LOW · else S2`. He's unsure of thresholds ("7 or 8… 3, 4 or 5") — so run the full grid, don't pick for him. Best pick from the data: **HIGH ≥8, LOW ≤5 → 66/10/21.** The histogram of MAX(D,LC,R) has a **natural near-empty gap at max=6** (only 1 exercise) — that gap is where the S2 boundary belongs, and it argues for ≥8/≤5 over any ≥7 variant. Full grid this session: ≥7/≤3=47/20/30 · ≥7/≤5=66/1/30 · ≥8/≤3=47/29/21 · ≥8/≤5=66/10/21. The ≥7 gates are a **trap** — they pull barbell curl & front raise UP into S3, backwards. Note the ≥8-max model reproduces the same 21-row S3 as the refined `D≥8 OR LC≥8` gate (Risk never adds a row) — so MAX≥8 and the two-axis-OR gate are equivalent on today's data; MAX-model just also gives a symmetric S1 floor.
- **The S2 band only means anything AFTER the input errors are fixed** (see audit below). On dirty data, barbell curl/front raise read as intermediate purely from inflated Load=3 + LC=7; fixing them drops those lifts to max=5 → S1, where a curl belongs. Say this plainly when presenting the max-model: the frame is right, but the middle tier is polluted until the isolation-inflation is cleaned.

## The unguarded-invariant flaw + the guarded one-liner (2026-07 refresh)

When Tanzim says his **confidence on the formula is low but can't name why**, the answer is usually a *load-bearing assumption the formula never states*. For the S123 classifier the specific flaw:
- Locked rule `Diff ≤5 → S1 · else LC ≤7 → S2 · else → S3` asserts two **independent** gates but is only correct while the invariant **`low Difficulty ⟹ low Learning Curve`** holds. Nothing guards it. It's true today only because Difficulty and LC are both Skill-driven (machine → low Diff AND low LC; free-standing whole-body → high Diff AND LC 9), so the axes move together and it hits 97/97.
- **The one stress case that breaks it:** a **light-load but highly technical** move — low Difficulty, LC 8–9 (a technical balance/mobility drill, lightly-loaded Olympic derivative, pistol/TRX skill). `Diff ≤5` routes it straight to **S1 (anyone, unguided)** despite "months to own, technical failure is dangerous." And S3 requires `Diff >5 AND LC >7`, so a dangerous-but-light lift can **never** reach S3. That's the hole. Latent, not active — the current 97 are all heavy compounds where LC 9 rides with high Difficulty.
- **The guarded one-liner (bolt the LC override on the front):**
  `IF LC ≥ 8 → S3 | ELSE IF Difficulty ≤ 5 → S1 | ELSE IF LC ≤ 7 → S2 | ELSE → S3`
  Still 97/97 on current data; catches the technical-but-light move on the next exercise added. Equivalent framing = the refined `D≥8 OR LC≥8` S3 gate / the symmetric MAX-model, just written as the original tree with a leading guard.
- **Diagnosis habit for "why do I not trust this":** don't reassure — hunt the *unstated invariant*. Ask "what silent correlation is this formula leaning on that nothing enforces?" then construct the row that violates it. My first blind read (before re-opening the sheet) was WRONG — I claimed "S1 ignores LC" as a live bug; once I read the Rubric I saw the axes are correlated so it barely fires. **Re-read the live sheet (Rubric + S123 LOGIC) before diagnosing** — the intent is documented there; don't critique from the screenshot alone.

## Blind-ranking drill — how Tanzim spot-validates the classifier

Tanzim validates a formula change by **naming exercises one at a time and asking for S1/S2/S3 only, no reasoning** ("I name the exercise, you name only S1/S2/S3, ready?"). When he sets this frame:
- Answer with the **bare level and nothing else** — no axis scores, no justification, no rider. One token per line. Adding reasoning breaks the drill; he's testing the gut-level output, not the working.
- He's cross-checking the *refined/guarded* gate against his own intuition. Apply the current live rule (guarded S3 gate), not the old locked one.
- Reference calls from the 2026-07 pass (guarded gate): Barbell Lunges S2 · Incline Barbell Bench S3 · Incline DB Fly S1 · Incline DB Hammer Press S2 · Lat Pulldown S1 · Single-Arm DB Row S2 · Reverse Pec Deck S1 · Arnold Press S2 · Barbell Upright Row S2 · Barbell Thrusters S3 · Rack Pull S3 · Wide-Grip Chin-Up S3 · Muscle-Up S3.

## Two-spoke input audit — split by axis TYPE, not by row range (2026-07-02)

When Tanzim says "deploy hub-n-spoke to fix the value errors," the clean 2-agent split is **by how the score is derived**, not by chopping the row list in half:
- **Spoke 1 — computed-formula inputs (Skill/Flex/Grip/Load → Difficulty).** Audit for scores that break the movement's own logic or contradict near-identical siblings (barbell vs EZ-bar vs cable vs machine variant should form a gradient). Report Row · Exercise · which input · current→proposed · resulting Difficulty Δ · confidence.
- **Spoke 2 — hand-scored axes (Learning Curve, Risk).** Same sibling-gradient logic; note if a change flips the S-level under current AND proposed rules.
- **Give each agent the FULL 97-row TSV inline** (they have no sheet access) and instruct **PROPOSE ONLY, no writes** — Load is Sagar-locked.
- **The dominant defect this class of dataset carries = "isolation inflation."** Single-joint/small-muscle lifts (barbell curl, front raise, skullcrusher, EZ-bar work, shrugs, calf raises) get parked at Load=3 AND LC=5–7 — both wrong, both should be low (Load 2, LC 3). The two spokes independently flag the SAME lifts from two axes → strong signal it's a genuine data-entry pattern, not noise. Opposite, smaller defect: spinal-loaded rows (bent-over, Pendlay) UNDER-scored on Risk (6 should be 8).
- **Report the level impact honestly:** under the *locked* formula almost nothing reclassifies (LC fixes stay ≤7, Difficulty governs) — the cleanup matters for integrity and for the *new* S3 rule, not for today's S-levels. Don't oversell it.
- Both agents ran in parallel via one `subagent` batch call, ~3–4 min, opus, no tools needed (pure reasoning over inline data).
- **Honesty split when Sagar asks "is this assumption/hallucination/invented?":** separate VERIFIED (numbers/rubric quoted from the sheet) from INFERENCE (my reasoning, written nowhere). State plainly which is which. The unused-LC-1 "explanation" was inference and my first version of it (band-collapses-to-one-value) was wrong — 3 and 4 coexist, so a scorer CAN split within a band. Don't defend a dented explanation; concede and reframe the open question back to them.

## WORKOUT PLAN DB — alternative exercise logic (locked, 2026-07)

When populating Alt Exercise columns in WORKOUT PLAN DB (or any derivative tab), the rules are:

**Column D (Alt Exercise 1):** Same Computed Level + Same Muscle Group + Same Cluster (movement pattern) as Primary (Col C) + **Different equipment type** from Primary. Fallback if no cross-equipment same-cluster option exists: any same-level/same-muscle exercise not yet used.

**Column E (Alt Exercise 2):** Same Computed Level + Same Muscle Group + **Different Cluster** from Primary. Must not duplicate Col C or Col D.

**Global deduplication is a hard constraint** — track a single `used` set seeded with ALL Primary (Col C) values across the entire tab. Once an exercise appears anywhere (C, D, or E), it cannot appear again in any row. Process rows in order; add each assignment to the used set immediately.

**Blanks are honest** — if the pool is exhausted for a given slot, leave it blank rather than inventing a value. Blanks mean the STRENGTH DB pool needs more exercises at that level/muscle group, not a logic error.

**Equipment taxonomy** is derived from exercise name prefix (in priority order for multi-word prefixes):
Smith Machine · Stability Ball · Trap-Bar · T-Bar · EZ-Bar · Resistance Band · Machine · Cable · Dumbbell · Barbell · Bodyweight · TRX · Weighted · GHD · Hanging · Kettlebell

**Naming consistency rule:** Every exercise in STRENGTH DB must start with an equipment prefix. Five exercises were found without prefixes (Tricep Dip, Kneeling Ab Rollout, Nordic Curl, Dragon Flag, L-Sit) — all renamed to `Bodyweight [Name]`. Run a NO_PREFIX scan before any alt-exercise logic pass.

**Pool exhaustion → extend STRENGTH DB, not the logic.** When blanks persist after dedup, the fix is adding more exercises to the pool. Create a `STRENGTH DB - EXTENDED` tab (duplicate, don't touch original) and add exercises there. Target: 100 exercises per S-level (S1/S2/S3 = 300 total), spread across all 12 muscle groups.

**Colour coding for level tabs (Column A only):**
- Only Column A gets a background colour — all other columns stay white with black text.
- S1 → light green, S2 → medium green, S3 → dark green.
- Black font throughout, including Column A.
- Never apply colour to the full row — Tanzim called this out explicitly as "messing up the whole tab."

**Test before applying to the full tab** — always duplicate the tab first, run logic on 10 rows of one S-level, verify with Tanzim before going full-tab. Subagent (Opus) for the compute-heavy logic passes.

**Safe order of operations:**
1. Duplicate source tab (never touch originals)
2. Run naming consistency scan (NO_PREFIX check)
3. Build pool from STRENGTH DB (or EXTENDED version)
4. Apply alt logic to TEST tab, 10 rows
5. Verify with Tanzim — check sheet directly, not just terminal output
6. On approval, apply to full tab

## Blair sheet specifics (Blair Grimes client sheet — separate from Tanzim's own training sheet)

Blair's sheet ID: `1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk`
Auth: `~/.hermes/google_token.json`
Active programme tab: **Aug-Sep** (renamed from Q4 2026, built 2026-07-21)
Current tabs (4): Overview · Nutrition · Blair's Persona · Aug-Sep

**Blair's WhatsApp (3724340625515) is NOT on the bridge — cannot DM her. Message via Tanzim or drop in chat.**

**Formatting standard (Blair sheet, locked 2026-07-21):**
- Columns: Exercise | Sets | Reps | Rest | Cue | Progression
- Widths: A=280px · B=80px · C=100px · D=80px · E=380px · F=220px
- Text wrap ON, vertical MIDDLE, horizontal CENTER on A–D, LEFT on E–F
- Progression values in **lbs** (US metrics) — never kg

**Key formatting rule — DO NOT label hierarchy in training tabs:**
- Block headers = muscle group name ONLY: "GLUTES", "QUADS", "CALVES"
- Never append "(Primary — 8 sets)", "(Secondary — 6 sets)", "(Tertiary — 4 sets)"
- Tanzim explicitly stripped these — don't re-add them

**Tab hygiene (Blair sheet):**
- Dead/empty tabs: delete immediately on identification
- Superseded programme tabs: bin when new tab is live — don't accumulate history
- Contradicting tabs: the more recent / more specific wins; update older tab or delete
- Tabs with dated content (event-specific, expired phases): strip to evergreen-only or bin

**Sheet cleaning workflow (learned 2026-07-21):**
When Tanzim says "bin it" about a tab → delete immediately, no further confirmation needed
When he says "clean up" a tab → read first, propose what's actionable vs expired, await approval before cutting
When he says "fix formatting" → apply full house style: wrap, middle, centre, widen columns — all in one pass, don't ask what he wants formatted

## Reference files
- `references/blair-programme-design-2026-07-21.md` — Blair programme design decisions, redundancy audit findings, tab hygiene rules, endocrine hypothesis, Veronica QC subagent notes (session 2026-07-21)

## Other standing prefs in this project
- **Short, plainly-readable responses — enforced HARD, especially when Sagar's in the thread.** Mid-session (2026-07-02) Tanzim cut me off: *"keep the replies shorter and easier for us to read, let's try again."* The "us" is the tell — when the chat has Sagar/others, my analytical walls stop being for Tanzim and start being homework for the group. Lead with the answer (the formula, the one number, the verdict); park the backtest/table/reasoning for when someone asks. A classification answer is one gate + one line of plain English, not a grid. When he asks "why not 7?" — show the ONE damning consequence (barbell curl lands in S3), not the whole sweep. Default to the one-screen version; he'll pull the depth if he wants it.
- Short human responses, no jargon.
- Back up to `~/backups/STRENGTH_DB_<purpose>_<stamp>.json` before destructive writes.
- When building together, always close with the final decision as a question (same as he'd want for Sagar).
- Reference tabs must be one-pass readable by Tanzim + Sagar; each value its own editable cell.
