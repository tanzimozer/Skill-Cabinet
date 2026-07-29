# TIMBR Eval Harness

Automated quality gate for TIMBR copy. Runs linters over one submission and produces a pass/fail
scorecard (console table + JSON on disk). It supports **two product lines**, gated by different
rulesets and different linter combinations — see "Two Rulesets" below before running anything.

There are **four** linters. Three are ruleset-aware and two of those sit out a product line
(VoiceLint does not run on `workout_series`; CharLint does not run on `magazine`). The fourth,
**SynthLint, has no ruleset switch and no opt-out**: it runs on every unit of every submission,
because "this reads as machine-written" is a defect on both product lines. Every unit's verdict is
the **conjunction** of the linters that looked at it — three per line — and one failed unit fails
the run.

---

## Quick Start

All commands below assume your shell is in this repository's root directory (the directory
containing this README, `orchestrator.py`, and `run_eval.sh`) — every command here was run from
there and verified to work as shown.

```bash
./run_eval.sh sample_issue.json
```

Or directly:

```bash
python3 orchestrator.py --issue sample_issue.json
```

For CI pipelines (minimal, machine-readable output):

```bash
python3 orchestrator.py --issue sample_issue.json --ci
```

Stop at the first failing section (the resulting scorecard is a **partial** result — see "Fail-Fast
and Partial Runs" below):

```bash
python3 orchestrator.py --issue sample_issue.json --fail-fast
```

`sample_issue.json` ships with two planted issues (an AI-blocklist term in Supplements and in
Recovery) and every section far under its magazine word-count floor, so a default run **fails**:

```
$ python3 orchestrator.py --issue sample_issue.json
...
Section         Voice  Prohib  Synth   Status
-------------- ------ ------- ------ --------
Training         100      80    100  ❌ FAIL
Nutrition        100      80    100  ❌ FAIL
Supplements      100      75    100  ❌ FAIL
Recovery         100      75    100  ❌ FAIL
Culture          100      80    100  ❌ FAIL
Social           100      80    100  ❌ FAIL
Nightlife        100      80    100  ❌ FAIL
────────────────────────────────────────────────────────────
  RUN: complete (7 section(s) evaluated, 7 required by the ruleset)
  OVERALL: FAIL
  TOP VIOLATIONS (9 blocking):
    • Word count 177 is outside allowed range [800–1200] for section 'Training'.
    • Word count 208 is outside allowed range [600–900] for section 'Nutrition'.
    • AI blocklist term 'delve' found 1 time(s). Penalty: -5.
  Advisory notes: 1 — non-blocking, did not affect OVERALL (full list in the scorecard JSON)
────────────────────────────────────────────────────────────
Scorecard written: results/VOL_04_scorecard.json
```

This is real, current output — not an invented example. All 7 sections fail on word count alone
(the sample text is much shorter than the magazine ranges); Supplements and Recovery additionally
carry one planted AI-blocklist word each ("delve", "vibrant"). Voice and Synth scores are a clean
100 across the board — none of this failure is a VoiceLint or a SynthLint problem.

---

## Two Rulesets

TIMBR has two product lines with **contradictory** copy rules, and the harness gates them with two
different `--ruleset` values. There is no default that silently works for both; picking the wrong
one is a hard usage error, and even where it "runs", it gates the copy against the wrong rules.

```
python3 orchestrator.py --issue issue.json                                          # ruleset=magazine (default)
python3 orchestrator.py --issue slots.json --ruleset workout_series \
                        --locks charlint/locks_seattle_series.json                   # --locks is required here
```

| | **magazine** (default) | **workout_series** (Seattle Series) |
|---|---|---|
| Input container key | `"sections"` | `"slots"` |
| Unit names | the 7 fixed magazine sections | whatever `--locks` defines |
| Em-dash rule | **any** em-dash is a hard fail | one em-dash **aside** per sentence is legal (a matched pair bracketing a phrase is one aside); only *stacked* (2+ asides in one sentence) hard-fails |
| Length gate | ProhibLint word-count ranges | CharLint exact character-count locks (`--locks`) |
| Linters run | ProhibLint (magazine mode) + VoiceLint + **SynthLint** | ProhibLint (workout_series mode) + CharLint + **SynthLint** |
| Linter **not** run | CharLint (word counts, not char locks) | VoiceLint (its register map is built for the 7 magazine sections) |
| SynthLint | **runs** — no ruleset switch, no opt-out | **runs** — same module, same call, same threshold |
| Issue-level mandatory elements (ProhibLint Check F) | applicable | **not** applicable (Editorial Handbook rules; this line is gated by CharLint instead) |

**The gate is a three-way conjunction on each line**, and SynthLint is a full blocking member of
both. A section that clears ProhibLint and VoiceLint and still reads as machine-written **fails**;
a slot that lands its char lock to the character and clears ProhibLint and still reads as
machine-written **fails**. SynthLint is the only linter with no `ruleset` parameter to thread
through and no slot type it skips — the false positive it once had on the locked exercise tables
was fixed inside SynthLint itself, on the shape of the text, rather than by giving the orchestrator
a list of slots to route around.

**Pick `magazine`** for the 7-section magazine issue copy (Training/Nutrition/.../Nightlife).
**Pick `workout_series`** for Workout Series (Seattle Series) volumes — the char-locked cover,
city intro, anchor venue/cafe, counter venue/cafe, and night-off page (see `charlint/README.md`).

**Pointing the magazine ruleset at Workout Series copy does not "mostly work" — it fails almost
everything on em-dashes alone.** Real numbers, run directly against ProhibLint's two em-dash checks
over all 7 of the real Seattle Series reference baselines (`charlint/locks_seattle_series.json`):

```
slot              em-dashes   magazine   workout_series
cover_body                2  HARD FAIL             pass
city_intro                3  HARD FAIL             pass
anchor_venue              1  HARD FAIL             pass
anchor_cafe               6  HARD FAIL             pass
counter_venue             2  HARD FAIL             pass
counter_cafe              2  HARD FAIL             pass
night_page                3  HARD FAIL             pass
```

7 of 7 (100%) hard-fail under `magazine`, because Workout Series prose uses em-dashes as a
deliberate stylistic device (PRINCIPLES.txt Sec. 7) and magazine treats any em-dash as an
unconditional hard fail. **0 of 7 hard-fail the em-dash check under `workout_series`** — the
governed unit there is the em-dash *aside* (PRINCIPLES.txt Sec. 7: "one em-dash aside per sentence,
never stacked"), and a matched **pair** of em-dashes bracketing one phrase is a single legal aside,
not two stacked dashes. `anchor_cafe`'s six em-dashes are three such pairs, one per sentence, so
none of its sentences stack 2+ asides. Running the *full* workout_series ruleset (every check, not
just em-dash) over these same 7 baselines fails 1 of 7 — `night_page`, on the unrelated
exclamation-point ban — see the workout_series example under "Scorecard Output" below. See
`prohiblint/README.md` for the full Check-by-check comparison and the aside-counting rule.

The reverse mismatch — a workout_series-shaped `slots` file run under `--ruleset magazine`, or a
magazine-shaped `sections` file run under `--ruleset workout_series` — is refused outright with an
error naming both the key found and the key expected, real output:

```
$ python3 orchestrator.py --issue <a slots-shaped file> --ruleset magazine
ERROR: <file> has no 'sections' key but does have 'slots', which is the workout_series shape.
Under --ruleset magazine the harness reads 'sections': an object of section name -> text. Either
pass --ruleset workout_series or supply 'sections'.

$ python3 orchestrator.py --issue sample_issue.json --ruleset workout_series --locks ...
ERROR: sample_issue.json has no 'slots' key but does have 'sections', which is the magazine shape.
Under --ruleset workout_series the harness reads 'slots': an object of slot name -> text. Either
pass --ruleset magazine or supply 'slots'.
```

`--locks` is required for `workout_series` and rejected (an error) for `magazine` — real output:

```
$ python3 orchestrator.py --issue sample_issue.json --ruleset workout_series
ERROR: --locks is required for --ruleset workout_series: CharLint has no default locks file, so
the harness cannot know which char locks to gate against (e.g. --locks charlint/locks_seattle_series.json).

$ python3 orchestrator.py --issue sample_issue.json --locks charlint/locks_seattle_series.json
ERROR: --locks is meaningless for --ruleset magazine: CharLint does not run on the magazine line,
which is governed by word counts, not char locks. Drop --locks, or pass --ruleset workout_series
if this submission is Workout Series copy.
```

---

## Issue JSON Format

### magazine

```json
{
  "issue_id": "VOL.04",
  "theme": "The Strength Issue",
  "sections": {
    "Training":    "...full section text...",
    "Nutrition":   "...full section text...",
    "Supplements": "...full section text...",
    "Recovery":    "...full section text...",
    "Culture":     "...full section text...",
    "Social":      "...full section text...",
    "Nightlife":   "...full section text..."
  }
}
```

All 7 section names are required. A missing section is not skipped — it is scored as a
**failing** unit (`status: "FAIL"`, `present: false`), because a gate that passes an
unwritten section is worthless. An unrecognized section name (a typo) is a hard input error, not a
silent no-op — ProhibLint and VoiceLint only score their own 7 names, so a typo'd section would
otherwise be handed default scores and pass without ever being linted.

### workout_series

```json
{
  "issue_id": "SEA.VOL.01",
  "theme": "Chest & Tricep — Cascade",
  "slots": {
    "cover_body":    "...",
    "city_intro":    "...",
    "anchor_venue":  "...",
    "anchor_cafe":   "...",
    "counter_venue": "...",
    "counter_cafe":  "...",
    "night_page":    "..."
  }
}
```

Keys are **slot** names defined by the `--locks` file (see `charlint/README.md`), not the
magazine's section names. A missing count-locked slot is reported by CharLint as `NOT FILLED` and
fails; an unknown slot name raises `charlint.UnknownSlotError`. The `slots` object is required
under this ruleset — supplying `sections` instead (the magazine shape) is the wrong-container-key
error shown above.

---

## What Each Module Catches

Full detail lives in each module's own README — this is a pointer, not a substitute.

### ProhibLint (`prohiblint/prohiblint.py`) — see `prohiblint/README.md`

Runs under **both** rulesets (with ruleset-dependent behavior on a few checks). Real rule names, not
the `banned_phrase`/`passive_overuse` rules a previous version of this README documented — **those
two do not exist anywhere in the code**:

| Rule | Runs under | Severity |
|---|---|---|
| `check_em_dash` / `check_em_dash_workout_series` | both (different rule) | hard fail |
| `check_ai_blocklist` | both | hard fail at 3+ hits, else penalty |
| `check_cold_open` | both (same rule) | penalty only |
| `check_second_person` | both (**different pattern list per ruleset** — see below) | penalty only |
| `check_word_count` | magazine only | hard fail |
| `check_workout_series_blocklist` | workout_series only | hard fail on any hit |
| `check_exclamation_points` | workout_series only | hard fail on any hit |

`check_second_person` is no longer identical across rulesets: `magazine` bans the full Editorial
Handbook Sec. 6 list outright, while `workout_series` flags only *prescriptive* (`you should`, `you
must`, ...) or *predictive* (`you will feel`) address, because PRINCIPLES.txt Sections 6–7
explicitly endorse direct address and reader autonomy for that line. Both take a `ruleset=`
parameter (default `"magazine"`); an unrecognized name raises. See `prohiblint/README.md` for both
pattern lists and the reasoning behind each dropped/kept phrase.

Also runs an **issue-level** check (magazine only, applicable) confirming four mandatory value
elements appear somewhere in the issue — the real `element_results` keys the code emits are
`workout_plan_rep_set`, `nutrition_spots_4_places`, `local_fitness_spots_2`, and
`location_features_3_places`. (A previous version of this README described these as
`workout`/`recipe`/`tip`/`gear`/`interview` — that is not what the code checks, and the code has
four elements, not five.)

### VoiceLint (`voicelint/voicelint.py`) — see `voicelint/README.md`

**magazine only** — not run under `workout_series` (its section/voice map is built for the
magazine's 7 sections; that line's register discipline is enforced by ProhibLint + CharLint +
SynthLint instead).

Maps each section to one of **three** registers via `SECTION_VOICE_MAP` — not seven bespoke
per-section voices:

| Section | Register |
|---|---|
| Training, Culture | `athletic` |
| Nutrition, Social | `people` |
| Supplements, Recovery, Nightlife | `fitt` |

A previous version of this README described 7 distinct per-section voice profiles (e.g. "Training:
Authoritative, punchy, **second-person**, imperative commands") — that is wrong on two counts: the
code only has three registers, not seven, and telling writers to use second person in Training
directly contradicted ProhibLint's Check D, which penalizes second-person patterns in *every*
section regardless of register. **No VoiceLint register's positive markers reward second-person
address, in any section.** See `voicelint/README.md` for the full fingerprint of each register and
how cross-contamination between them actually works (it is a relative-margin comparison against
both other registers, not two fixed absolute-threshold pairs).

**Pass threshold: 85** — `voicelint.voice_config.PASS_THRESHOLD`, verified directly against the
constant. It is *derived*, not picked: a section may carry at most `NEGATIVE_MARKER_BUDGET` (5)
negative-marker hits at `NEGATIVE_HIT` (-3) each and still pass, so
`PASS_THRESHOLD = SCORE_START + 5 * NEGATIVE_HIT = 100 - 15 = 85`. Also new: one
cross-contamination flag now costs 18 points (`CROSS_CONTAMINATION_PENALTY`) — one more than the
entire 15-point negative-marker budget — so a section that reads like the wrong register now
**fails outright** rather than merely picking up an advisory note, even if it is otherwise perfect.
`test_voicelint.py::TestEffectivePassBar` pins the *effective* bar (the delta at which pass flips),
not the constant by name, and a companion test greps `voicelint.py`'s own source to confirm the
threshold is never hard-coded there. See `voicelint/README.md` for the full derivation and the
calibration corpora behind `CROSS_CONTAMINATION_MARGIN`.

### CharLint (`charlint/charlint.py`) — see `charlint/README.md`

**workout_series only.** Enforces the exact character-count locks from PRINCIPLES.txt Section 3
against the 7 named slots in a locks file (e.g. `charlint/locks_seattle_series.json`). Covers
**only** those 7 slots — not every dynamic text slot in a full volume — and a full pass on CharLint
is not evidence the rest of the volume is count-clean. CharLint is also the **only** source of
`warnings` (drift, un-gated slots, unsubmitted owner-governed slots, non-NFC candidates); the other
three linters have no warnings channel and the orchestrator does not invent one for them. The
shipped locks file currently raises **no** drift warning — `cover_body` is range-locked to 350–358
(the master workbook's band), so the old "documented 357 vs measured 351" disagreement was a point
being compared to a range and is not a drift;
`test_orchestrator.py::test_the_shipped_locks_file_raises_no_drift` pins that.
Full detail, including the locks-file format, overflow-vs-underfill,
permanent-slot protection, and the drift mechanism, is in `charlint/README.md`.

### SynthLint (`synthlint/synthlint.py`) — see `synthlint/README.md`

**Both rulesets, every unit, no exceptions.** The other three linters ask what the handbook bans,
which register the copy is in, and whether it fits the layout. SynthLint asks the one question none
of them asks: **does this read like a machine wrote it?**

```python
run_synthlint(text) -> {"violations": [str], "score": int, "passed": bool, "flags": {...}}
```

Note the shape difference from the other three: it takes **one string**, not a `{name: text}` map,
and there is **no `ruleset` parameter** — that is the design, not an omission. It raises `TypeError`
rather than silently scoring something if handed a dict.

Six checks, every threshold derived from measured corpora rather than chosen:

| # | Check | Fires on |
|---|---|---|
| 1 | Extended AI vocabulary | phrasal scaffolding (`it's important to note`, `when it comes to`, ...); hard fail at 5 hits |
| 2 | Formulaic transition density | ≥2 paragraph-**initial** connectives at a rate > 0.20 |
| 3 | Contrastive-frame overuse | ≥2 compressed `not just X, it's Y` pivots per 250 words |
| 4 | Hedge stacking | two hedges compounding on one proposition; hard fail at 3 |
| 5 | Sentence-length burstiness | CV < 0.29 (flattest real TIMBR text measured 0.3867) |
| 6 | Repeated-opener runs | same first word ×4, or generic-class opener ×3 |

**Pass threshold: 84** — `synthlint.PASS_THRESHOLD`, derived as `100 - 2 × 8`: a text may carry a
2-tell noise budget, and the budget is 2 because the 29-text real-TIMBR corpus carries **0** tells
while the weakest adversarial text carries **3**. Two rather than zero makes corroboration
structural — no single regex match can fail owner-approved copy on its own. **`orchestrator.py`
never writes that number down**; it reads `passed` off the verdict, so moving the threshold cannot
leave the gate disagreeing with the module — the test
`test_the_orchestrator_never_hard_codes_synthlints_pass_threshold` greps the source to keep it
that way.

What it deliberately does **not** do: em-dashes (ProhibLint owns them, and it counts *asides*),
"is this paragraph filler" (the editorial board's call), vocabulary diversity, and rule-of-three
rate — that last one was built, measured, and **dropped**, because real TIMBR copy uses triads
*more* than the adversarial corpus does, so no threshold fires on slop before it fires on the house
voice. Check 5 is the one with a shape-dependent unit: on an enumerated spec list (PRINCIPLES.txt
Sec. 12's locked exercise table) it measures the longest free-text field of each row rather than
the row, because a templated table is uniform by format. It is never switched off for a shape the
writer controls. See `synthlint/README.md` for every derivation and the held-out validation split.

---

## Scorecard Output

### Console

Standard mode prints a table (shape depends on `ruleset`) followed by a run summary — one score
column per linter that ran, so the magazine table carries Voice/Prohib/Synth and the workout_series
table carries Lock/Actual/Delta/Prohib/Synth. The magazine example is under "Quick Start" above.
workout_series example — real output, the raw Seattle Series baseline text (unmodified — see "Two
Rulesets" above for the em-dash-check-only numbers) through `--ruleset workout_series`:

```
Slot               Lock  Actual   Delta  Prohib  Synth   Status
---------------- ------ ------- ------- ------- ------ --------
cover_body          351     351      +0     100    100  ✅ PASS
city_intro          628     628      +0     100    100  ✅ PASS
anchor_venue        667     667      +0     100    100  ✅ PASS
anchor_cafe         694     694      +0     100    100  ✅ PASS
counter_venue       602     602      +0     100    100  ✅ PASS
counter_cafe        414     414      +0     100    100  ✅ PASS
night_page          616     616      +0     100    100  ✅ PASS

────────────────────────────────────────────────────────────
  RUN: complete (7 slot(s) evaluated, 7 required by the ruleset)
  OVERALL: PASS
────────────────────────────────────────────────────────────
```

All 7 pass, with no warnings. Two things in this block used to read differently and are worth
naming rather than quietly editing: `night_page` used to fail Check H on one exclamation point
("Take the night — cheers!"), which the shipped baseline no longer carries, and the run used to
emit a `DRIFT: cover_body` warning, which the range lock retired (see CharLint above). **SynthLint
scores all 7 of these baselines 100 — this is the owner's real, live Canva template content, and
the universal AI-fingerprint check has nothing to say about it.**

### JSON Output

Written to `results/<issue_id>_scorecard.json` by default (sanitized filename — e.g. `VOL.04` ->
`VOL_04_scorecard.json`), or to `--out-dir <dir>` when given. Real (trimmed) output, magazine
ruleset, from the "Quick Start" run above:

```json
{
  "issue_id": "VOL.04",
  "theme": "The Strength Issue",
  "ruleset": "magazine",
  "unit_kind": "section",
  "overall": "FAIL",
  "run": {
    "fail_fast": false,
    "complete": true,
    "truncated": false,
    "truncated_at": null,
    "truncation_reason": null,
    "incomplete_reason": null,
    "units_expected": 7,
    "units_evaluated": 7,
    "evaluated": ["Training", "Nutrition", "Supplements", "Recovery", "Culture", "Social", "Nightlife"],
    "not_evaluated": []
  },
  "linters": {
    "prohiblint": {"applied": true, "ruleset": "magazine"},
    "voicelint":  {"applied": true},
    "charlint":   {"applied": false, "reason": "The magazine line is governed by word counts, not char locks; CharLint does not apply."},
    "synthlint":  {"applied": true, "universal": true, "note": "SynthLint has no ruleset switch and no opt-out: ..."}
  },
  "sections": {
    "Training": {
      "voice_score": 100, "voice_passed": true,
      "prohib_score": 80, "prohib_passed": false,
      "synth_score": 100, "synth_passed": true,
      "violations": ["Word count 177 is outside allowed range [800–1200] for section 'Training'."],
      "status": "FAIL", "present": true
    }
  },
  "blocking_violations": ["Word count 177 is outside allowed range [800–1200] for section 'Training'.", "..."],
  "blocking_violations_total": 9,
  "advisory_notes": ["Fitt negative marker: reporting verb (this register asserts, it does not report) (1x)"],
  "advisory_notes_total": 1,
  "warnings": [],
  "issue_level_checks": {
    "violations": [], "penalty": 0, "passed": true,
    "element_results": {
      "workout_plan_rep_set": true, "nutrition_spots_4_places": true,
      "local_fitness_spots_2": true, "location_features_3_places": true
    },
    "applicable": true
  },
  "generated_at": "2026-07-27T19:53:06.759993"
}
```

Notes on the keys:
- The timestamp key is **`generated_at`** (an ISO-format string from `datetime.now().isoformat()`)
  — not `timestamp`.
- There is no `voice_issues` key anywhere in this shape, under either ruleset. It has never existed.
- `blocking_violations`/`blocking_violations_total` and **`advisory_notes`/`advisory_notes_total`**
  are both always present (`orchestrator.SCORECARD_KEYS`). Blocking violations come from a check
  that actually failed; advisory notes are penalty-only findings from a check that *passed* — both
  linters can emit these, and routing a passing check's findings into `blocking_violations` is what
  previously produced a run reporting `PASS` next to a nonzero blocking-violation count.
- Every unit carries **one `<linter>_score` / `<linter>_passed` pair per linter that looked at it**:
  `prohib_*`, `voice_*` and `synth_*` under magazine; `char_*`, `prohib_*` and `synth_*` under
  workout_series. `synth_score`/`synth_passed` are present on **both** lines — that pair is the
  one field set the two rulesets share, because SynthLint is the one linter both lines run.
- Under `workout_series`, the per-unit container key is `"slots"` (not `"sections"`), each unit
  carries `char_expected`/`char_actual`/`char_delta`/`char_score`/`char_passed`/`failure_mode`
  instead of `voice_score`/`voice_passed`, and `issue_level_checks.applicable` is `false`.
- SynthLint's findings land in the unit's `violations` list exactly like ProhibLint's, and split
  into `blocking_violations` / `advisory_notes` by the same rule: blocking when SynthLint failed
  the unit, advisory when it passed. SynthLint scores several findings a unit can carry and still
  pass (a single contrastive pivot, a single hedge stack), so the advisory case is a live one.
- `warnings` is always present (an empty list under magazine, since CharLint is the only source of
  warnings today) and never affects `overall` or the exit code. **SynthLint has no warnings
  channel** — its result is `violations`/`score`/`passed`/`flags` and nothing else — and the
  orchestrator does not invent one for it.

A **fail-fast** run produces a self-describing, explicitly **partial** scorecard rather than a
scorecard that merely stops short. Real output, `--fail-fast` on the sample issue:

```
FAIL-FAST: section 'Training' failed. Stopping — 6 section(s) will NOT be evaluated.

Section         Voice  Prohib  Synth   Status
-------------- ------ ------- ------ --------
Training         100      80    100  ❌ FAIL
Nutrition          —       —      —  ⏭ NOT_EVALUATED
Supplements        —       —      —  ⏭ NOT_EVALUATED
Recovery           —       —      —  ⏭ NOT_EVALUATED
Culture            —       —      —  ⏭ NOT_EVALUATED
Social             —       —      —  ⏭ NOT_EVALUATED
Nightlife          —       —      —  ⏭ NOT_EVALUATED

────────────────────────────────────────────────────────────
  RUN: TRUNCATED (--fail-fast) — PARTIAL RESULT, NOT A FULL EVALUATION
  Stopped at: Training
  Evaluated (1/7): Training
  NOT evaluated (6): Nutrition, Supplements, Recovery, Culture, Social, Nightlife
  OVERALL: FAIL
```

In the JSON, every expected unit is still a key in `sections`/`slots` — a unit the run never
reached carries `"status": "NOT_EVALUATED"` and **null** scores (never `0`, never `100` — a
NOT_EVALUATED unit must be impossible to mistake for either a pass or a fail). That includes
`synth_score`/`synth_passed`: the one universal check is not allowed to be the one field that reads
clean on copy nobody read, and the fail-fast stop genuinely stops the SynthLint call too — the
skipped units' text is never handed to it. `run.truncated` is
`true`, `run.complete` is `false`, `run.truncated_at` names the unit that tripped the stop, and
`run.not_evaluated` lists every unit the run never reached. **A truncated run is a PARTIAL result
and can never report `overall: "PASS"`** — even if every unit the run did reach happened to pass
(see `test_orchestrator.py::test_truncation_alone_forces_a_failure`).

`warnings` (e.g. CharLint drift) survive a truncated run too — they are a property of the locks
file, not of how far the run got, so they are reported even when the run stops at the very first
unit.

### `--out-dir`

`--out-dir <dir>` writes the scorecard JSON there instead of the default `results/` next to
`orchestrator.py`. Useful for keeping test/demo runs out of the tracked `results/` directory.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0    | `overall == "PASS"` — at least one unit was evaluated, none failed, the run was not truncated, and applicable issue-level checks passed |
| 1    | `overall == "FAIL"` — including a fail-fast-truncated run and a run in which zero units were evaluated. Warnings never produce a 1 |
| 2    | usage / config / input-shape error: unknown `--ruleset`, `--locks` missing or misapplied, an unreadable or malformed issue file, a wrong-container-key issue file, an unrecognized unit name, or a corrupt locks file. Matches argparse's own exit code for CLI misuse |

A previous version of this README documented only 0 and 1. Real demonstrations of exit code 2:

```
$ python3 orchestrator.py --issue sample_issue.json --ruleset seattle
ERROR: Unknown ruleset 'seattle'. Valid rulesets: 'magazine', 'workout_series'. There is no silent
fallback to 'magazine' — a typo'd ruleset would gate the copy against the wrong product line's rules.
$ echo $?
2
```

`run_eval.sh` mirrors the same three codes — `./run_eval.sh` with no arguments prints a usage
message to stderr and exits 2; otherwise it forwards the orchestrator's own exit code untouched.

---

## CI Integration

```bash
python3 orchestrator.py --issue issue.json --ci
# Prints: per-unit violations, then warnings (if any), then PASS or FAIL on the final line
# Exit code 0 PASS / 1 FAIL / 2 usage error
```

Example GitHub Actions step:

```yaml
- name: TIMBR Eval
  run: python3 timbr_eval/orchestrator.py --issue issue.json --ci
```

For Workout Series copy in CI:

```yaml
- name: TIMBR Eval (Workout Series)
  run: |
    python3 timbr_eval/orchestrator.py --issue issue.json \
      --ruleset workout_series --locks timbr_eval/charlint/locks_seattle_series.json --ci
```

---

## File Structure

```
timbr_eval/
├── orchestrator.py                # Main harness — wires all four linters together
├── run_eval.sh                    # Shell convenience wrapper (forwards every flag untouched)
├── sample_issue.json              # Sample magazine issue; fails today on word count + 2 AI-blocklist hits
├── test_orchestrator.py           # pytest suite for orchestrator.py (147 tests)
├── test_positive_control.py       # Guards the magazine positive-control fixture (43 tests)
├── README.md                      # This file
├── __init__.py
├── fixtures/
│   └── magazine_pass.json         # The ONLY magazine submission known to return PASS — the line's positive control
├── results/                       # Tracked in git; scorecard JSON lands here by default
│   └── VOL_04_scorecard.json
├── prohiblint/
│   ├── __init__.py
│   ├── prohiblint.py              # Prohibited-language + structure linter, both rulesets
│   ├── test_prohiblint.py         # 443 tests
│   └── README.md
├── voicelint/
│   ├── __init__.py
│   ├── voicelint.py               # Voice-register linter (run(), score_*, voice_affinity(), voice_affinity_density())
│   ├── voice_config.py            # SECTION_VOICE_MAP, regex patterns, scoring constants
│   ├── test_voicelint.py          # 419 tests
│   └── README.md
├── charlint/
│   ├── __init__.py
│   ├── charlint.py                # Char-count lock gate (load_locks, run_charlint, chars_to_target)
│   ├── locks_seattle_series.json  # The real Seattle Series locks — 7 DYNAMIC + 2 PERMANENT slots
│   ├── test_charlint.py           # 230 tests
│   └── README.md
└── synthlint/
    ├── __init__.py
    ├── synthlint.py               # AI-fingerprint linter (run_synthlint) — BOTH rulesets, no ruleset switch
    ├── synth_config.py            # Vocabulary lists, thresholds, and every derivation note behind them
    ├── test_synthlint.py          # 312 tests
    └── README.md
```

---

## Running Tests

Six suites, 1594 tests total as of this writing. From the repo root, all six at once:

```bash
python3 -m pytest -q
```

```
1594 passed in 15.15s
```

Or individually (each suite's own README has the exact invocation it expects):

```bash
python3 -m pytest prohiblint/test_prohiblint.py -q      # 443 passed
cd voicelint && python3 -m pytest test_voicelint.py -q   # 419 passed
cd charlint  && python3 -m pytest test_charlint.py -q    # 230 passed
cd synthlint && python3 -m pytest test_synthlint.py -q   # 312 passed
python3 -m pytest test_orchestrator.py -q                # 147 passed  (from the repo root)
python3 -m pytest test_positive_control.py -q            # 43 passed   (from the repo root)
```

`test_orchestrator.py` guards, among other things, that no test run ever writes into the tracked
`results/` directory (`_guard_real_results_dir` fails the test suite if anything does), and it
asserts the four-linter conjunction **once per ruleset** rather than once and generalised — the two
evaluation paths are separate functions, and "the wiring works for one ruleset" does not imply it
works for both.

---

## Dependencies

stdlib only across all four linters and the orchestrator: `re` (prohiblint, voicelint, synthlint),
`typing.NamedTuple` (voicelint), `json`/`pathlib`/`unicodedata` (charlint), `statistics`
(synthlint), and `argparse`/`json`/`re`/`pathlib`/`datetime` (orchestrator). Nothing in this repo
imports `collections`. `pytest` is required to run the test suites, not to run the harness itself.
