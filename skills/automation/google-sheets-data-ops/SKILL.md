---
name: google-sheets-data-ops
description: Read, edit, audit, and reverse-engineer Google Sheets programmatically via the gs.py helper — tab/gid discovery, formula recovery from live data, scoring-system maintenance, safe cascade edits with backups.
category: automation
---

# Google Sheets Data Ops

Class-level skill for working with Tanzim's Google Sheets databases through the
Sheets API: reading, editing, auditing structure, and reverse-engineering the
formulas behind computed columns. Covers the multi-tab "fitness exercise DB"
spreadsheets (Strength/Conditioning/Hybrid/Foundation/Performance tabs, SCORING
LOGIC, FX, etc.) and any similar structured sheet.

## The gs.py helper (use this first)

There is a ready-made, authorised helper at `~/gs.py`. Import it from
`execute_code` (`import sys; sys.path.insert(0,'/home/hermes'); import gs`).
It exposes:

- `gs.get(rng)` → values for an A1 range, e.g. `gs.get("'STRENGTH DB'!A1:Q200")`
- `gs.put(rng, values)` → write a 2D list, USER_ENTERED
- `gs.meta()` → full spreadsheet metadata (all sheets, gridProperties)
- `gs.gid(title)` → sheetId for a tab title
- `gs.svc` → the raw `sheets` service for batchUpdate / valueRenderOption calls
- `gs.SHEET` → the spreadsheet ID currently wired in

It auto-refreshes the OAuth token (`~/.hermes/google_token.json` +
`google_client_secret.json`). If you need a DIFFERENT spreadsheet, copy the
`_svc()` pattern or temporarily reassign `gs.SHEET`.

**Never claim gs.py is "blocking / hanging / broken" without TESTING it first.**
Friday burned most of a July 2026 session telling Tanzim the helper was "hanging"
and offering to "debug it" — a pure fabrication, never actually run. The moment it
was invoked for real (with a 30s `timeout` guard), the token auto-refreshed and it
returned every tab first try. The rule: `gs.py` is authorised and works. If you're
unsure it's alive, RUN a cheap probe — `timeout 30 python3 -c "import gs; print([s['properties']['title'] for s in gs.meta()['sheets']])"` —
and report what actually happened. Do NOT invent a failure to explain away a step
you haven't taken, and do NOT offer to "debug" a tool you never called. If a real
call hangs, wrap it in `timeout` and show the actual error; the browser hangs on
Sheets, but the API helper does not.

Prefer `execute_code` over `terminal` heredocs — the env warns/blocks on `&`
backgrounding and the import path is cleaner. Run `gs` calls in `execute_code`.

**Module-shadowing trap:** if you DO use a terminal script, run it from `~`
(home), NOT from `/tmp`. A script placed in `/tmp` and run from there resolves a
DIFFERENT `gs` on the path and fails with `module 'gs' has no attribute 'get'`.
Fix: `cp /tmp/script.py ~/script.py && cd ~ && python3 ~/script.py`. Verify with
`python3 -c "import gs; print(gs.__file__)"` → must be `/home/hermes/gs.py`.

## Reading a tab's real structure

`gs.meta()` gives every tab's title, sheetId (gid), rowCount, columnCount.
Distinguishing rows that have data: `[r for r in rows[1:] if len(r)>1 and r[1].strip()]`.
Watch for **stale/duplicate tabs**: a DB tab may have an out-of-date twin
(e.g. STRENGTH DB at 9 cols vs S-123 at 17 cols, same exercises). Compare row
counts, headers, and exercise-name sets before assuming which is canonical.

## Tab/gid discovery when the browser hangs

Google Sheets often hangs headless browser tools. To get the tab list + gids
WITHOUT the browser, fetch the htmlview and regex out the tab menu:

```bash
curl -sL "https://docs.google.com/spreadsheets/d/<ID>/htmlview" -o /tmp/hv.html
```
```python
import re
h=open('/tmp/hv.html',encoding='utf-8',errors='ignore').read()
for m in re.finditer(r'\{name:\s*"([^"]+)",\s*[^}]*?gid:\s*"?(\d+)', h):
    print(m.group(2),'=>',m.group(1))   # gid => TAB NAME
```
For quick read-only CSV of one tab by gid (no auth, if shared):
`https://docs.google.com/spreadsheets/d/<ID>/gviz/tq?tqx=out:csv&gid=<GID>`
Prefer the numeric `&gid=` (from the htmlview regex above). The `&sheet=<name>`
lookup (URL-encode spaces, e.g. `sheet=S123%20LOGIC`) DOES work as a fallback
when you can't get the gid — but it CAN silently fall back to another tab and
return the WRONG data, so ALWAYS verify by checking the header row matches the
tab you asked for before trusting the values.

## Don't fight the browser to read a sheet — go straight to the API

If the ask is "read the current formula / values in this sheet," do NOT open it
in the browser first. On a **view-only / no-sign-in** shared link the browser
tools cannot switch tabs at all — clicking a tab, using the All-Sheets menu, and
re-clicking all silently leave you on the first tab (name box stuck on A1:I1), so
you never reach the tab the user meant. July 2026: burned several browser round
-trips trying to reach an `fx` tab this way before pulling it via the API in one
call. The right move for ANY read-a-formula request: go straight to `gs.py` and
fetch with `valueRenderOption='FORMULA'`:

```python
import sys; sys.path.insert(0,'/home/hermes'); import gs
r = gs.svc.spreadsheets().values().get(
        spreadsheetId=gs.SHEET, range='fx',
        valueRenderOption='FORMULA').execute().get('values', [])
for i,row in enumerate(r,1):
    for j,c in enumerate(row):
        if c not in (None,''):
            col = chr(65+j) if j<26 else 'A'+chr(65+j-26)
            print(f'{col}{i}: {c}')
```

This returns the literal `=...` formulas (or text, if the cell is just text) for
every populated cell, tab-addressable by name, no browser needed. The browser is
only worth it when the user is reacting to what they SEE (rendered colours) — for
formulas and values, the API is faster and actually reaches the tab.

## Reverse-engineering a computed column's formula

When a column holds hard-coded VALUES (not live formulas — check with
`valueRenderOption='FORMULA'`) and the documented formula may be stale, recover
the TRUE formula from the data: enumerate candidate formulas, run each against
all rows, and report the exact match count. The formula that matches 97/97 is
the truth, regardless of what the docs say. See
See `references/formula-reverse-engineering.md` for the full pattern and the fitness
scoring formulas (Difficulty, Learning Curve, Level Score, band cutoffs).
- **See `references/blair-nutrition-sheet-conventions.md` for Blair Grimes' nutrition sheet layout, macro formula (Protein 1g/lb · Carbs 0.7g/lb · Fat = flex), two-tier day structure, Macro Builder tab spec, and BFR removal locations.**
- **See `references/timbr-workout-plan-db-logic.md` for STRENGTH DB - EXTENDED schema,
alternative column rules, colour convention, QA checklist, and stress test pattern.

Docs drift from data on these sheets REPEATEDLY (SCORING LOGIC and FX tabs lag
the actual S-123/DB values). Always trust the data, then fix the docs to match —
don't trust the written formula.

## Backtesting a proposed classification rule (challenge → data, not debate)

When the user challenges a classifier ("the S-levels are wrong," "highest score
should go straight to S3"), do NOT argue from theory. Pull ALL rows and run
BOTH schemes side by side, then report the delta. The standard play:

1. Enumerate candidate rules as lambdas (current, user's strict version, user's
   broad version, variants at each threshold).
2. Run each over all rows → print the S1/S2/S3 distribution table.
3. Print the DIFF set — exactly which named exercises move under the new rule,
   with their scores, so the change is concrete not abstract.
4. Threshold-sweep when the user asks "why not N?" — show N vs N±1 and name the
   exercises the looser threshold drags in. The tell that a threshold is too low
   is a nonsense inclusion (e.g. "Barbell Curl" landing in the coached tier).

**Collinearity check — kills redundant axes.** Before adding an axis to a
formula, correlate it against the ones already in play. On the fitness DBs the
three axes (Difficulty, Learning Curve, Risk of Injury) run r≈0.88–0.94 —
near-collinear. Risk NEVER changes an outcome: zero high-risk (R≥8) exercises
sit in a low tier, because every high-risk lift is already high-Difficulty.
Verdict pattern: "a gate that never fires is noise; keep it out of the live
formula, keep it as a reference score." Distinguish this from the *rule-level*
argument for including it (future-proofing against a future low-skill/high-risk
movement) — state both honestly and let the user pick. Don't pretend the axis
earns its place on today's data when it doesn't.

## Input error vs formula error (diagnose before you "fix")

When a single row scores wrong (e.g. Barbell Curl reads Difficulty 7 / LC 7 for
a trivial movement), decompose it before touching anything:
- Recompute the formula from that row's raw inputs. If the formula reproduces
  the wrong number, the FORMULA is fine and an INPUT is bad. Curl's D7 came from
  Load=3 (maxed) — a data-entry error, not a formula flaw.
- Hand-scored axes (Learning Curve) can just be mis-graded — LC7 on a
  single-joint curl is wrong at the source, no formula involved.
- Say plainly "the formula's right, the data entry isn't" and name the specific
  bad input + what it should be. Don't "fix" by rewriting the formula.
- **A locked input is not yours to quietly change.** Load=3 on STRENGTH DB is a
  locked decision (Sagar, to hold 97/97). Even when it's clearly wrong for one
  row, flag it for the owner — don't patch it under a "fix the errors" request.
  Separate the clean fix (hand-scored LC) from the locked-decision fix (Load).

## Safe cascade edits (the golden rule)

Changing one computed input cascades: e.g. Difficulty → Level Score →
Unified Level (band). Before writing:

1. **Back up the whole tab to JSON first** —
   `json.dump(gs.get("'TAB'!A1:Z200"), open(f"~/backups/TAB_pre<change>_{ts}.json",'w'))`.
   Always mention the backup path to the user so they can revert.
2. **Map the full dependency chain** and reverse-engineer EACH downstream
   formula before touching the upstream input.
3. **Widen the grid if adding a column** — tabs are capped at their current
   columnCount; appending col R to a 17-col tab fails with "exceeds grid limits"
   until you `updateSheetProperties` → `gridProperties.columnCount`.
4. **Verify anchors** the user gave you (e.g. "Smith press should be 3") before
   committing the full recompute. If an anchor misses, the heuristic is wrong.
5. **Stop at genuine forks** — when two rules conflict (e.g. documented band
   cutoffs vs the cutoffs the live data actually uses, differing on 39/97 rows),
   compute BOTH, show the distribution table, and let the user lock the choice.
   Don't silently pick one.

## Don't-invent-data discipline

Never fabricate values for a new scored column (e.g. inventing Load 1–3 scores)
and commit them as truth. Either: (a) add the empty column + live formula and
let the user/coach fill it, or (b) take a clearly-labelled first-pass heuristic
that the user reviews. State which one you're doing. This mirrors the same trap
as inventing F0 levels — unvalidated inputs poison everything downstream.

**Verify the required INPUT columns exist before promising a recompute.** When a
formula is refined to run on new primitives, PULL the sheet header and confirm
those columns are actually present before you say "I'll recompute all 97 rows."
July 2026: a refined classifier (Nimbus) ran on eight new computed inputs
(MuscleMass, AxialFlag, CoordinatedJointCount, Timing, Asymmetry, DynStab…) —
but STRENGTH DB still only carried the OLD hand-scored columns (Difficulty,
Learning Curve, Skill, Flex, Grip, Load). A "clean recompute" would have meant
hand-inventing ~8×97 ≈ 776 subjective scores to fit the new formula — the exact
hand-scoring the model was built to kill, and a straight violation of the rule
above. The honest move is to STOP and lay out the two real paths: (a) add the new
primitive columns properly, derive them once transparently, let the user
spot-check, then compute for real and reproducibly; or (b) approximate now by
mapping the new axes onto the columns that DO exist — fast but a lash-up that
likely preserves the collinearity you were trying to kill. Name which is the
model and which is moving numbers around; let the user pick. Do not quietly
invent the missing inputs and present the result as a validated recompute.

## NEVER declare "done" off a partial check (Tanzim caught this TWICE in one session)

The single sharpest correction from the June 22 2026 Hybrid/Conditioning extend
session: *"Next time CHECK before you tell me that."* Friday declared colour
bands "consistent across all 50" after reading back only RGB numbers and only
checking columns F/G/H — never actually inspecting the sheet, and never checking
the intrinsic columns (Output/Coord/Impact) which were left **white on every new
row**. Tanzim spotted it from a screenshot. Earlier the same session, the same
pattern: "done" announced after verifying gate math but not formatting.

Hard rule before you say "done / verified / consistent":
1. **Check EVERY dimension the claim covers, not a sample.** "All 50 formatted"
   means read all banded columns on all 50 rows — including intrinsic/secondary
   numeric cols, not just the gate columns. A claim about "the colours" must
   cover every coloured column.
2. **Reading the RGB back to yourself is NOT a check.** Validating your own
   output against your own rule proves nothing — it's circular. Compare against
   the INDEPENDENT reference (the original rows, the house tab) or eyeball the
   actual rendered sheet (`browser_vision`/screenshot) when the user is reacting
   to what they SEE.
3. **When extending a list, the NEW rows are the suspect set.** Diff new-vs-old:
   count non-default (white) cells per column — `len(new_rows)` white cells in a
   column that should be banded is the tell you skipped it. Run this before
   declaring formatting complete.
4. If the user is looking at a screenshot and says you're wrong, **stop
   re-validating your rule and go look at the sheet itself.** They can see a gap
   your value-readback can't.

## Band EVERY numeric scoring column, not just the gate columns

House style on these DBs bands all numeric scoring cells green→yellow→red — and
that includes the **intrinsic axes** (Strength: Skill/Flexibility/Grip/Load;
Conditioning: Output/Coordination/Impact; Hybrid: Skill/Load/Output), not only
the computed gate columns (Intensity/Demand/LC/Risk). For the 1–3 intrinsic
axes the rule is **1=Green, 2=Yellow, 3=Red**. Derive the exact value→colour
mapping from a CLEAN value-driven tab (Conditioning/Hybrid), never from
**STRENGTH DB — its bands are hand-painted and unreliable** (the same value
shows green, yellow AND red on different rows). Confirm the rule, then apply it
uniformly to all rows including the ones you just added.

## Extending an exercise list (the standard play)

When asked to grow a DB (e.g. 14→50 exercises): (1) backup JSON first;
(2) propose a cluster-balanced distribution and the candidate names, close on
the decision as a question; (3) on go: dedupe new names against live AND
internally, and cross-check any shared intrinsic (e.g. Output for a movement
that also lives in Conditioning) so the same movement can't carry different
scores across tabs — intrinsics are tab-independent; (4) write with LIVE
formulas in the computed cells (`=IF(...)`, `=MAX(MIN(...))`), never pasted
values, so the gates self-compute; (5) re-run both gates across ALL rows and
report 0 fails + level/cluster distribution; (6) band every numeric column per
the rule above; (7) flag the new heuristic scores for Sagar's review. Count the
rows you actually wrote — a "+36" that lands at 49 means you were one short.

## Verifying a classifier: inverse-think, don't self-confirm

A QC that checks a formula's output against the SAME rule the formula encodes is
circular — it always passes and proves nothing about correctness. July 2026:
Friday ran "error check" three times on FX-2, got ALL PASS each time, and
reported the sheet sound — while a ≥7-vs-≥8 threshold bug sat in it. The check
recomputed `MAX>=8?S3...` and compared it to the formula's `MAX>=8?S3...`: two
copies of the same mistake agreeing with each other. Tanzim had to explicitly
redirect: *"apply inverse thinking to find out where the formula FAILS."*

Two-layer discipline for validating any scoring/classification rule:

1. **Correctness (does it match INTENT):** recompute against the user's stated
   words, NOT against the formula. Hand-check the boundary values. If your check
   and your formula are the same expression, you've verified nothing.
2. **Robustness (inverse thinking — assume it's broken, hunt the failure):**
   don't ask "does it pass," ask "where does this rule embarrass itself." The
   standard probes on the real data:
   - **Dead axis / gate that never fires.** For each axis, count how often it is
     the SOLE driver of the outcome (the unique max). On the fitness DBs Risk of
     Injury drove 0/95 classifications — a 3-axis rule silently running on 2.
     An axis that never changes an outcome is decorative; say so.
   - **Collinearity.** Correlate the axes pairwise. r≈0.88–0.94 means you're
     measuring one thing three times; `max()` of three near-identical signals is
     just that signal wearing a costume. (Also see the collinearity note under
     backtesting.)
   - **Knife-edge fragility.** Count rows whose worst axis sits EXACTLY on a band
     boundary — one scoring point flips their tier. 50% of the DB on a boundary =
     a coin-toss rubric, not a robust one.
   - **OR/AND asymmetry.** A "any axis ≥ N → top tier" (OR) paired with "all axes
     ≤ M → bottom tier" (AND) is structurally skewed: easy to fall out of the
     bottom, easy to fall into the top. Count who gets DENIED the bottom tier by
     a single mid axis, and name them.
   Report failure MODES with counts and named examples, then give the verdict:
   the formula is coded right but the DESIGN is where it breaks (dead axis,
   redundant axes, boundary fragility). Tanzim wants the failure surface, not
   another green tick.

## Building a curated / balanced-tier copy tab (the standard play)

When asked to spin a NEW tab off an existing DB with a target shape — e.g.
"recreate Strength DB into FX-2, formula at top, but make every S-level have
exactly 15 exercises":

1. **Formula banner first, data second.** Rows 1–3 = the human-readable rule
   (title + one-line formula + the band cutoffs). Blank spacer rows. Then the
   header row, then data. Tanzim asks for the formula written FIRST, explicitly.
2. **Copy real rows, compute the tier LIVE.** Pull the source rows once
   (cache to `/tmp/*.json`), append a new S-Level column whose cell is a live
   `=IF(COUNT(F7,G7,H7)=0,"",IF(MAX(F7,G7,H7)>=8,"S3",IF(MAX(F7,G7,H7)<=3,"S1","S2")))`
   referencing THAT row's own axis cells — so re-editing a score recomputes.
   Never paste the tier as a static string.
   **Lock the threshold from the user's EXACT words, and never trust the example
   above verbatim.** July 2026: Tanzim's rule was "any axis 7 or above → S3" but
   Friday coded `>=8` (carried over from an earlier ≥8 variant discussed the same
   session) across the header, the whole DB column AND the stress block. Every QC
   passed — because QC tested the formula against its own ≥8 definition, not
   against what Tanzim said. He caught it only by hand-checking a boundary case
   (7/7/7, which he KNEW should be S3 but read S2). Before writing ANY banded
   formula: quote the user's threshold back verbatim, confirm which comparison
   (`>=` vs `>`), and dry-run the exact boundary values (the cutoff and cutoff-1)
   BY HAND against their stated words — not against your formula. `>=7` vs `>=8`
   is a one-character bug that reshuffles half the tiers and passes every
   self-referential check.
3. **Trim to the target count by popularity/relevance, not by score order.**
   When a band overflows (S1 had 47, needed 15), keep the mainstream, most-
   searched/most-programmed movements and cut redundant equipment variants
   (Smith/cable duplicates, niche or unsafe lifts like behind-the-neck press,
   near-duplicate hinges like stiff-leg vs RDL). Name the cuts and WHY in the
   reply so the choice is auditable. Order each tier most-popular-first.
4. **Recreate idempotently.** deleteSheet-if-exists then addSheet, so re-runs
   don't stack duplicate tabs. Assert `len==target` per tier before writing.
5. **Leave the source tab untouched** when told to — verify afterward that its
   row count is unchanged, and say so.
6. **Verify the live column agrees with the block order** you placed rows in
   (expected = `['S1']*15+['S2']*15+['S3']*15`); print mismatches (should be
   none) + the live distribution before declaring done.

## Stale carried-over label column = the "S3 has S2 in it" contradiction

When you re-classify a DB into a new tab (new S-Level rule), DO NOT carry the
source tab's OLD computed-level column across. STRENGTH DB leads with a
`Computed Level` column holding the PREVIOUS taxonomy. Copy the rows verbatim
into an FX tab that computes a NEW level in another column and you get two
disagreeing labels PER ROW — col A shows the old "S2", your live formula in the
new column shows the correct "S3". July 2026: Tanzim looked at the S3 table,
saw the stale col-A "S2" sitting beside the row, and (rightly) said *"table S3
has S2 in it??"*. It was not a placement bug and not a formula bug — it was a
second, stale opinion column I never should have kept.

Rule: when the new tab's job is to RE-tier exercises, strip the source's old
level column and keep exactly ONE authoritative level column — the live
`=IF(MAX(...)...)` one, placed FIRST. `row = list(src_row)[1:]` drops the leading
Computed Level; prepend the fresh formula. Then no two columns can contradict.
Before declaring done, scan for the trap explicitly: for every data row compare
col-A (old) vs the computed column and print any `A != computed` — a wall of
mismatches means you left the stale column in.

## Layman exercise naming — Tanzim's spec (Equipment + common name + (modifier))

Tanzim's naming standard for exercise tables (locked July 2026), isolated from
his examples ("Barbell Bench Press (flat)", "Cable Bicep Curl", "Machine Leg
Curl"):
1. **Equipment word first** — Barbell / Machine / Cable / Smith Machine /
   EZ-Bar / Trap-Bar / Bodyweight (a weighted bodyweight move like Weighted
   Pull-Up keeps its own name, no equipment prefix needed).
2. **Common gym name** for the movement — "Bench Press" not "Chest Press",
   "Bicep Curl", "Shoulder Press", "Lat Pulldown". Layman, not anatomical.
3. **Distinguisher in parentheses ONLY when needed** to separate variants:
   (flat)/(incline)/(close-grip)/(wide-grip)/(neutral-grip)/(seated)/(standing)
   /(conventional)/(sumo). No modifier when the base name is already unique.
4. Natural spacing + Title Case. NOT a rigid hyphen template.

**Rigid `Equipment-Bodypart-Action` templates COLLAPSE distinct exercises into
identical strings — reject them.** A hyphen template dropped the grip/angle word
and produced `Cable-Back-Pulldown ×4` (Lat/Close/Wide/Neutral), `Barbell-Back-
Row ×4` (Bent-Over/T-Bar/Pendlay/Yates), `Barbell-Quads-Squat ×2` (Back=Front) —
46 unique names out of 60. The distinguishing info lives in the modifier, which
the template throws away. ALWAYS run a duplicate check after any bulk rename
(`Counter(names)`, assert all-unique) and hand-author names for accuracy rather
than regex — layman naming is a judgement call per row, not a string transform.

## Stress-testing alternative exercise columns

When Tanzim says "stress test" the alt columns, the check is:
1. For each row, look up the alt exercise name in the full dataset (col B of other rows).
2. Verify: alt exists in DB, alt ≠ primary, same Computed Level, same Muscle Group, same Cluster.
3. Report pass/fail count + every failure with row number, primary, alt, and what specifically failed.

**Circular QC is NOT a stress test.** Checking alt's cluster against the alt's own row data is circular — you'll always pass because you assigned it that way. The validation must cross-reference the PRIMARY's cluster, not the alt's stored cluster value. Look up the alt name in col B, pull ITS attributes from the DB pool, then compare to the primary.

**Common failure pattern:** "shifted/rotated alternative" — alt is from an adjacent exercise (Lateral Raise↔Rear Delt, Incline Press↔Horizontal Press). This happens when the same-cluster pool is exhausted and the fallback picks a neighbouring-cluster exercise without flagging it clearly. These don't pass a stress test even if they pass a self-referential check.

**Stress test result → action:**
- Cluster mismatches → fix with same-cluster/different-equipment replacement; if none exists → blank (never use wrong-cluster fallback)
- Exercise not found in DB → flag as X placeholder for Tanzim to fill manually
- Invalid attributes (e.g. Muscle Size = '—') → flag for data correction

## Pool exhaustion → extend DB workflow

When alt columns have blanks because the pool lacks cross-equipment options for certain clusters:

1. **Diagnose first** — scan blank rows, record (Level, Muscle Group, Cluster, Primary Equipment) for each. This is the gap map.
2. **Generate targeted exercises** — one new exercise per gap slot, matching: same Level+MG+Cluster, DIFFERENT equipment than primary, unique name, FX-2 score correct.
3. **Append to DB** — do NOT touch existing rows. Append new rows only.
4. **Re-sort** — after appending, sort entire sheet S1→S2→S3 (col A).
5. **Rerun alt computation** — only for the previously-blank rows; seed used set with existing valid alts first.

**Task size warning:** Steps 1-5 in one subagent task times out at 600s. Split into two calls:
- Call 1: Diagnose gaps + generate + append + sort
- Call 2: Rerun alt column for blank rows only

**Gap diagnosis code pattern:**
```python
gaps = []
for i, row in enumerate(data, start=2):
    c = row[2] if len(row) > 2 else ''
    if not c or c == 'X':
        gaps.append({
            'row': i, 'level': row[0], 'name': row[1],
            'muscle': row[9],   # always read from actual header index
            'cluster': row[14], # always read from actual header index
            'equip': get_equip(row[1])
        })
```
Always derive column indexes from the header, never hard-code.

## Auditing formatting/design via the API (not by eyeball)

When Tanzim asks for a "format / design scan" (wrap, alignment, cell colour,
bold, frozen rows), pull the real cell formats — don't guess from a screenshot.
`spreadsheets().get(spreadsheetId, ranges=[...], includeGridData=True)` returns
`effectiveFormat` per cell: `wrapStrategy`, `horizontalAlignment`,
`verticalAlignment`, `backgroundColor` (r/g/b 0–1), `textFormat.bold/fontSize`.
Aggregate with a Counter per column to surface INCONSISTENCY (the tell that
formatting was applied by hand and drifted): e.g. grey header shading present on
table-1's header row but white on table-2/3's, or nothing bold so there's no
visual hierarchy, or `frozenRowCount==0` on a long stacked sheet. Report the
inconsistencies + a concrete proposed pass (bold headers, uniform header shade,
tier tint on the level column green/amber/red), then apply via batchUpdate
repeatCell only on go.

## User cut-paste column reorder auto-adjusts formula refs — verify, don't assume broken

When Tanzim reorganises columns himself (e.g. promotes Difficulty/LC/Risk to
sit right after Exercise Name, demotes the muscle block), a **cut-paste move in
Sheets auto-updates any formula that referenced those cells** — my
`MAX(F7,G7,H7)` re-pointed itself to `MAX(C7,D7,E7)` to follow the axes, and
kept computing correctly. Don't assume a reorder broke your live formulas;
PULL the formula (`valueRenderOption='FORMULA'`) from a data row and confirm it
now points at the axes' NEW positions. Only a delete+retype (not a move) would
have orphaned the refs into `#REF!`. Recognise and name the reorg the user did
(read it back), confirm the formula survived, then offer the end-to-end recheck.

## Spawning a subagent to scan a private sheet

When Tanzim asks a subagent to read a private Google Sheet:
- **Browser will fail** — the sheet redirects to a Google sign-in wall. Do NOT spawn a browser-only subagent for a private sheet.
- **Authenticate via token** — credentials live at `~/.hermes/google_token.json` + `~/.hermes/google_client_secret.json`. Brief the subagent to use `googleapiclient` or `gspread` with the stored token, or to use `gs.py` directly.
- If Tanzim provides a new sheet URL mid-session, reassign `gs.SHEET` to the new spreadsheet ID before any reads.
- The spreadsheet ID is the long string between `/d/` and `/edit` in the URL.

## Intermittent API 500s — retry with backoff, don't declare the tool dead

The Sheets API throws sporadic `HttpError 500 "Internal error encountered."` on
perfectly valid reads (July 2026: several in a row on `STRENGTH DB` reads that
then succeeded). This is Google's side, not gs.py. Wrap reads in a small retry:

```python
def rget(rng, n=8):
    for i in range(n):
        try: return gs.get(rng)
        except Exception as e:
            time.sleep(3+i*2)   # linear backoff
    raise SystemExit('failed '+rng)
```

A 500 that clears on retry is NOT a reason to say the helper is broken. Prefer
`execute_code`; if a read genuinely needs >60s of retries, run it in a tracked
background process (`terminal(background=true)` + `process wait`), never
`nohup`/`&` (the env blocks shell backgrounding).

## Bipartite matching > greedy for alt column assignment

When populating alternative exercise columns with a global uniqueness constraint,
a naive greedy pass (assign first available in row order) produces avoidable
blanks — early rows consume options that later rows needed. Use **maximum
bipartite matching** (Kuhn's algorithm or `scipy.optimize.linear_sum_assignment`)
per (Level, Muscle Group) group instead. Preference tiers feed the cost matrix:
- Tier 0: same cluster + different equipment from both B and C (ideal)
- Tier 1: same cluster, any different equipment
- Tier 2: fallback (any same Level + Muscle Group, unique, ≠B, ≠C)

This consistently eliminates avoidable blanks — a greedy pass that left 24 blanks
was reduced to 0 by bipartite matching on the same pool.

**When to use greedy vs matching:**
- Greedy is fine for early passes or when pool is very large relative to rows.
- Use matching when blanks are appearing and pool should theoretically cover them.

## Column index drift — the #1 bug when inserting columns mid-session

When you insert a column into a sheet mid-session (e.g. adding "Alternative Two
Exercise Name" between cols C and D), **every subsequent column index shifts by
one**. Any agent that was given a schema like "MuscleGroup=col I, Cluster=col N"
is now WRONG — those columns are now J and O.

This session: col C insert shifted MuscleGroup from index 8 to 9, and Cluster
from index 13 to 14. A subsequent Opus agent read the header but used hard-coded
offsets and silently populated the "Alternative Exercise 1" column using Muscle
Group values of `1` (it was reading the wrong column). The wrong values were
written to 300 rows before anyone noticed.

**Hard rules:**
1. **ALWAYS read the header row first and derive column indexes dynamically**
   from the actual header values — never hard-code index numbers.
2. After ANY column insert, any running agent or script MUST re-read the header
   before making assumptions about column positions.
3. When briefing a subagent on a schema, do NOT pass column letter/index — pass
   the column HEADER NAME and instruct the agent to find it dynamically.
   Example: "MuscleGroup is in the column headed 'Muscle Group'" — not "col I".
4. After an insert, verify the schema is intact with a quick header print before
   writing any data.

## Building exercise alternative columns (the TIMBR pattern)

When populating alternative exercise columns (Alt 1, Alt 2, etc.) for a
STRENGTH DB-style sheet:

**Alt 1 rule:** Same Computed Level + Same Muscle Group + Same Cluster (movement
pattern) + Different equipment type from primary. Fallback: same Level + Muscle
Group, any different exercise.

**Alt 2 rule:** Bodyweight-only alternative. Exercise name must start with:
Bodyweight, Hanging, TRX, GHD, Weighted (Pull-Up/Chin-Up). Same Level + Muscle
Group + Cluster. Leave blank if no bodyweight option exists — do not fabricate.

**Equipment taxonomy** — derive from name prefix, check longer prefixes first:
Smith Machine, Stability Ball, Resistance Band, Trap-Bar, T-Bar, EZ-Bar →
then: Machine, Cable, Dumbbell, Barbell, Bodyweight, TRX, Weighted, GHD,
Hanging, Kettlebell. Anything not matched = 'Other'.

**Global deduplication (hard constraint):**
- Track a global `used` set seeded with ALL col B (primary) values.
- Process rows in ORDER. Once an exercise is assigned anywhere, it cannot repeat.
- Each column must be unique from everything to its left on that row AND globally.
- Pool exhaustion (blank) is the correct outcome when the pool is genuinely
  exhausted — do not fabricate or recycle.

**Pool size vs. dedup tension:** If global dedup produces too many blanks, the
root cause is pool size, not logic. Fix = add more exercises to the DB for those
clusters, not relax the dedup rule.

**Naming convention for equipment prefix consistency:**
Every exercise name must start with its equipment type. Run a prefix scan before
finalising any DB extension. Five categories to watch for NO_PREFIX entries
(exercises that don't lead with equipment): Tricep Dip, Kneeling Ab Rollout,
Nordic Curl, Dragon Flag, L-Sit — these should be prefixed with 'Bodyweight'.

## Muscle size classification (Big vs Small) — TIMBR standard

Muscle Size in STRENGTH DB is a binary classification by muscle group, NOT by
score or exercise difficulty:

**Big:** Chest, Back, Shoulders, Quads, Hamstrings, Glutes, Calves, Full Body
**Small:** Biceps, Triceps, Core, Traps

Never varies within a muscle group. Wrong Muscle Size = wrong muscle group assignment.

## Column formatting — colour in col A only (TIMBR sheet standard)

For STRENGTH DB - EXTENDED and similar tiered exercise sheets:
- **Col A only** gets level colour: S1=light green, S2=medium green, S3=dark green
- **All other columns** — white background, black text
- Header row — dark navy (#141440-ish), white bold text
- Do NOT apply row-wide background colours — this "messes up the whole tab"
  (Tanzim's exact words, this session)

Apply using `repeatCell` batchUpdate targeting only `startColumnIndex:0,
endColumnIndex:1` for col A colour, and a separate pass resetting cols B-onwards
to white before applying col A.

## Hub-and-spoke QA pattern for DB tabs

When Tanzim says "deploy hub and spoke" for a QA task:
- 1 hub (you) + max 5 spokes, each with exactly ONE task
- Run spokes in parallel
- Hub does its own quality-check pass on combined results BEFORE reporting to Tanzim
- Report arrives pre-vetted — Tanzim should not be the first QC gate
- Standard 5-spoke QA set for exercise DBs:
  1. Formula validation (Difficulty + Computed Level vs FX-2)
  2. Naming convention (equipment prefix on every exercise)
  3. Duplicate detection (col B, col C, and within-row B==C)
  4. Alternative exercise validation (level + muscle group + cluster match)
  5. Completeness (row counts per level, blank cells, muscle group coverage)

## Consolidating overlapping reference tabs

When two tabs overlap (e.g. RULES = classifier vs PROGRESSION LOGIC = branching
matrix): READ BOTH FULLY before proposing a merge — they often do different
jobs and a wholesale fold loses unique logic. Identify only the TRUE redundancy
(the one duplicated row/table), replace it with a cross-reference pointer to the
single home, and tag the other tab back. Watch for **load-bearing stale
references**: RULES cited a deleted SCORING LOGIC tab and a dead Level Score
formula — but that was the ONLY surviving home for the Foundation F0–F3 model,
still live downstream in TRAINING SPLIT. "Cleaning the stale bit" would have
gutted a live dependency. When a "stale" reference is the last copy of a live
model, STOP and surface the decision; don't delete on a guess.

## Working style for these sessions (Tanzim)

- He wants the TRUTH reverse-engineered from data, not theory restated from docs.
- When he asks "is this right / find out the truth," run the data check, don't
  re-explain the documented formula.
- Honest pushback is wanted: if his proposed fix won't do what he thinks (e.g.
  "remove the −3" — a flat constant shifts all rows equally, doesn't change
  ranking), say so plainly with the reason, then offer the real fix.
- Keep replies short when he says "as short as possible." For a formula: give it,
  then one line per element with the reasoning, then stop.
- **DEFAULT to short on these analytical sessions — don't wait to be told.**
  Tanzim has cut Friday off mid-session for verbosity here more than once
  ("keep the replies shorter and easier for us to read"). The multi-column
  tables + tiered explanations that feel thorough read as walls to him and Sagar.
  Rule of thumb: lead with the answer/formula, ONE tight supporting line or a
  small table only if it's genuinely a list, then stop. The full backtest tables
  are for when he asks to see the working — the default answer is the verdict,
  not the whole audit. When in doubt, cut it in half.
- Standalone explainer tabs for him + a collaborator (Sagar): plain English, no
  jargon, formula + why-each-element + the alternative. Light formatting (bold
  section headers, wrapped cells, column widths) via batchUpdate repeatCell.
  When it's an EDITABLE calculator: every value in its own cell + a LIVE
  self-computing formula (always MAX/MIN-capped). He rejects bundled values
  ("give each value their own cell"). Break the 1/2/3 anchor rubric into
  per-score columns too. See `references/formula-reverse-engineering.md`.
- Heuristic auto-scores (e.g. Load 1/2/3) ALWAYS misfire on edge cases —
  equipment-keyword ordering bugs (cable caught by an "overhead press" rule)
  and isolation-vs-compound confusion. Eyeball the output, and when one's wrong
  fix the RULE + docs/anchor, not just the cell. Load is now LOCKED 1/2/3 on
  STRENGTH DB only; Conditioning/Hybrid still need the column.
- Reorder-by-movement-family / clusters: the STRENGTH DB exercises group into
  **clusters** = movement pattern within a muscle (Horizontal Press, Incline
  Press, Vertical Pull, Squat, Hip Hinge...), stored in a `Cluster` column.
  Grain is the MOVEMENT PATTERN (~3-4 per muscle), NOT the muscle part. Sort is
  TWO-LEVEL and the inner ordering matters — Tanzim rejected a first pass twice
  ("it does not") because the clusters themselves weren't ordered:
    1. Muscle Group (preserve first-appearance order).
    2. Cluster, ordered by its EASIEST entry — i.e. key each cluster on its
       min (level, difficulty) so every muscle group LEADS with an S1 cluster.
       A cluster that only has S2 rows (e.g. Chest › Decline) falls to the back.
    3. Within a cluster: level S1→S2→S3, then Difficulty as the tiebreak.
  So each cluster reads easiest→hardest top-to-bottom, and the cluster that
  starts easiest comes first. (Common bug: sorting rows by level/difficulty but
  leaving clusters in arbitrary order, so a muscle group opens on an S2 cluster.)
- Cluster-leading naming convention: within a cluster the variant/equipment word
  must LEAD so the eye scans the family instantly. Pattern is
  **`[Variant] [Equipment] [Movement]`** — e.g. "Incline Machine Chest Press",
  "Flat Barbell Chest Press", "Decline Barbell Chest Press". For clusters with
  no real variant (rows, pulldowns) the EQUIPMENT word leads instead. Also
  normalise stragglers: drop stray body-part words ("Machine Bicep Curl" →
  "Machine Curl"), fix hyphens ("Smith-Machine" → "Smith Machine"), and make the
  movement word match the cluster ("Machine Triceps Extension" in a Pressdown
  cluster → "Machine Triceps Pressdown"). After a bulk rename, FLAG that names
  may be keyed by exact string in other tabs (S-123, splits) and the app —
  offer to propagate, don't assume the links survive.
