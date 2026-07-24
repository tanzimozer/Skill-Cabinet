# Formula Reverse-Engineering & Fitness DB Scoring

## The reverse-engineering pattern

When a column holds computed VALUES and you need the real formula:

```python
import sys; sys.path.insert(0,'/home/hermes'); import gs
h = gs.get("'STRENGTH DB'!A1:Q1")[0]
idx = {c:i for i,c in enumerate(h)}
rows = [r for r in gs.get("'STRENGTH DB'!A2:Q200") if len(r)>1 and r[1].strip()]
def g(r,c):
    try: return float(r[idx[c]])
    except: return None

# enumerate candidate formulas, score each against ALL rows
candidates = {
  "A: (Skill*2)+Flex+Grip-3": lambda r: (g(r,'Skill/Coordination')*2)+g(r,'Flexibility')+g(r,'Grip')-3,
  # ... add more guesses
}
for name,f in candidates.items():
    ok = sum(1 for r in rows
             if round(max(1,min(10,f(r)))) == round(g(r,'Difficulty')))
    print(name, ok, "/", len(rows))
# the formula at 97/97 is the truth
```

Check whether cells are values vs live formulas first:
```python
gs.svc.spreadsheets().values().get(
    spreadsheetId=gs.SHEET, range="'TAB'!A2:Q2",
    valueRenderOption='FORMULA').execute()['values']
```

To recover BAND cutoffs (score → label), sort by score and find where the label
flips:
```python
for ls,lvl,nm in sorted((g(r,'Level Score'), r[idx['Unified Level']], r[1]) for r in rows):
    # print first row of each new level → that's the band edge
```

## Recovered fitness-DB scoring (verified against live data, 2026-06)

These are the TRUE live formulas, recovered from the data — the SCORING LOGIC
and FX tabs documented stale/older versions. Inputs each scored 1–3.

**Difficulty** (how hard to EXECUTE — definition locked by Tanzim):
- Live before Load was added: `(Skill/Coordination × 2) + Flexibility + Grip − 3` (matched 97/97)
- After adding Load (Tanzim's call, 2026-06): `(Skill/Coordination × 2) + Flexibility + Grip + Load − 3`, range 2–9
- Skill×2 because it's the one axis you CAN'T regress (you can always lower load).
- Stability deliberately excluded — it lives only in Learning Curve (no double-count).
- Strength was removed entirely; "Load" (1=machine/light, 2=moderate, 3=heavy barbell near-max) was added so heavy compounds aren't under-rated.
- Anchors Tanzim confirmed: Smith Incline=3 (rails → low Skill, but real barbell Load 2), Back Squat=8, Deadlift=9, Front Squat=9, Pec Deck floor=2.
- KEY INSIGHT: a Smith machine reduces SKILL (rails stabilise → Skill 1) but NOT Load (still a loaded barbell → Load 2). Score those independently.

**Learning Curve**: `(Learn × 3) + Stability − 2`, kept 1–10.

**Level Score** (verified 97/97): normalise Difficulty and Learning Curve each
to 0–1 over the 1–10 range, then weight:
`((Difficulty-1)/9) × 0.60 + ((LearningCurve-1)/9) × 0.40`

**Band cutoffs — UNRESOLVED FORK (as of session end):**
- Documented (SCORING LOGIC): F0 ≤0.20 · F1 ≤0.45 · F2 ≤0.70 · F3 >0.70
- What the live data actually used: ≈ F0 <0.10 · F1 <0.40 · F2 <0.61 · F3 ≥0.61
- They disagree on 39/97 rows. Recommended to Tanzim: use DOCUMENTED bands
  (real F0 floor, usable spread) PLUS the per-tab F1 floor rule (Strength/
  Performance DBs cannot read below F1 — a loaded barbell move is never an
  absolute-novice exercise). He had not final-confirmed when session paused.

**S1/S2/S3 classification (locked, per the S123 LOGIC tab, computed live in STRENGTH DB col A):**
`IF Difficulty ≤ 5 → S1 · ELSE IF Learning Curve ≤ 7 → S2 · ELSE → S3`.
Gates: (1) Difficulty ≤5 = beginner can do it unguided → S1; (2) LC >7 = long
to master / coaching-required → S3; (3) everything else → S2. Both axes are
intrinsic to the exercise (equipment is a filter, never a classifier). Current
split as a verification anchor: **S1=66 · S2=15 · S3=16 · total 97** (97/97 match).

**Load values: LOCKED at 1/2/3 by Tanzim, applied to STRENGTH DB only** (Conditioning/Hybrid still lack the column — extend them next to stay consistent).

**Load heuristic (first-pass auto-score — KNOWN MISFIRES, always eyeball before trusting):**
```python
def load_score(name):
    n=name.lower()
    heavy=['barbell','deadlift','back squat','front squat','overhead press',
           'behind-the-neck','sumo deadlift','romanian','stiff-leg','clean','snatch','hip thrust']
    if 'smith' in n: return 2                      # guided but real barbell load
    if any(k in n for k in heavy): return 3
    if any(k in n for k in ['machine','cable','band','pec deck']): return 1
    if any(k in n for k in ['crunch','raise','fly','pushdown','kickback','rear delt','face pull','lateral']): return 1
    return 2                                       # dumbbell/goblet/weighted bodyweight
```
Keyword heuristics misfire on two classes — fix manually after the auto-pass:
- **Equipment-keyword ordering bug**: "Cable Overhead Press" hits the `overhead press` heavy-rule (→3) BEFORE the cable check. Cables = Load 1 (pin stack, scales down instantly). Put the cable/machine guard FIRST, or special-case. (Tanzim's rule: cable always = Load 1, now in the DIFFICULTY tab Load anchor.)
- **Barbell isolation over-scored**: Barbell Curl / Front Raise / Shrug / Skullcrusher / Calf Raise catch the `barbell`→3 rule but aren't near-max compounds — they're arguably Load 2. The heuristic can't tell a heavy COMPOUND from a light barbell ISOLATION; that's a human judgement call.
- Lesson: when a misfire is found, fix the Load RULE (and the docs/anchor), not just the one cell — "if cable is wrong we need to factor that in with the formula" (Tanzim).

## Editable "calculator" explainer tab (Tanzim's preferred deliverable shape)

When he asks for a standalone explainer tab he + Sagar can "easily see or modify",
iterate toward: **every value in its own cell, with a live self-computing formula.**
- First attempt bundled values as text ("1 · 1 · 1 · 2") — he rejected it: "give each value their own cell."
- Final shape that landed: a worked-examples table with columns Exercise · Skill · Flexibility · Grip · Load · Difficulty, each input an editable numeric cell, and Difficulty a LIVE capped formula: `=MAX(2,MIN(9,(B24*2)+C24+D24+E24-3))`.
- ALWAYS cap live formulas with MAX/MIN — an uncapped `(B*2)+C+D+E-3` let Front Squat read 11 (over the 9 ceiling). The stored DB values are capped; a naive live formula is not.
- Also break the 1/2/3 anchor rubric into separate cells (one column per score level) so he can edit what "low/medium/high" means per input in place.
- Light formatting via batchUpdate repeatCell: bold section headers, tinted result column, wrapped cells, set column widths, centre the numeric block.

## Reorder rows by movement family (progression view)

Tanzim wanted exercises grouped so a family's S1→S2→S3 progression reads top to
bottom ("see the same category of exercise evolving"). Sort key:
**Muscle Group (fixed display order) → movement family → level (S1→S2→S3)**.
Derive the family by stripping equipment/variation words (barbell, dumbbell,
cable, smith, incline, wide-grip, seated, etc.) from the name to find the base
movement. Preview one or two muscle groups before committing; back up first
(it rewrites all rows in place). Offer the fork: family-grouped-within-muscle
(shows each movement evolving) vs flat-all-S1-then-S2 per muscle (shows the
muscle's difficulty ladder) — let him pick.

## Spreadsheet specifics (fitness DB)

- Spreadsheet ID (gs.SHEET as wired): `1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo`
- Canonical 17-col header order = CONDITIONING DB / HYBRID DB header.
- S-123, F-0123, P-123 are the fully-scored v2 tabs; STRENGTH/CONDITIONING/
  HYBRID DB are the consumer tabs. STRENGTH DB was rebuilt from S-123 this session.
- Reference tabs: SCORING LOGIC (gid 65557771), FX (1583317249) — keep these in
  sync with data after any formula change.
