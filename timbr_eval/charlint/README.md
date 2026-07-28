# CharLint — TIMBR Char-Count Lock Gate

CharLint is the eval-harness module for the **Workout Series** (Seattle Series) product line. It
has nothing to do with word counts or voice registers. It measures exact character counts against
a per-slot "lock" and fails anything that does not land on the lock to the character.

It is used only under `--ruleset workout_series` (see the top-level `README.md`'s "Two Rulesets"
section). The magazine line does not use CharLint at all — it is governed by ProhibLint's word-count
check instead.

---

## What a lock is, and why exact counts matter

Source: `PRINCIPLES.txt` (the TIMBR Design Framework document, maintained in the sibling
Seattle-Magazine-Engine project — not part of this repo), Section 3 ("CHAR-COUNT LOCKS — THE
LAYOUT IS LAW"):

> Once a page is owner-approved, every dynamic text slot is locked to the EXACT character count of
> the approved baseline (including spaces) ... Counts are exact, not approximate: never hand-count,
> always machine-count ... If a count breaks, the layout breaks — line wraps, overflows, rhythm.

The design is a fixed Canva layout. A text box is sized for one specific string. Any other string
of a *different length* either overflows the box (text pushed off the page) or underfills it (a
short last line that breaks the block's visual rhythm) — regardless of whether the new copy is
good writing. CharLint is the machine count that PRINCIPLES.txt Section 3 says must replace
hand-counting. It is the gate between "copy someone wrote" and "copy that can be poured into a
locked Canva box."

PRINCIPLES.txt Section 3 names seven reference locks: cover body 357, city intro 628, anchor venue
667, its cafe 694, counter venue 602, its cafe 414, night page 616. These seven numbers are exactly
the seven slots `charlint/locks_seattle_series.json` defines and `charlint.py` enforces:
`cover_body`, `city_intro`, `anchor_venue`, `anchor_cafe`, `counter_venue`, `counter_cafe`,
`night_page`.

**CharLint covers only these seven slots.** PRINCIPLES.txt Section 2 lays out a much longer page
order for a Workout Series volume — cover, straight talk, the work (a program with a progression
page), the fuel, the place, the night off, the ask — and the seven locked slots' own `page` fields
in `locks_seattle_series.json` only cover pages 1, 8, 9, 9, 10, 10, and 11. Pages 2 through 7 (the
straight-talk page, the program, its progression page, the fuel page) and anything past page 11
carry no CharLint lock at all. **A CharLint PASS is not evidence that a whole volume's dynamic text
is count-clean — it is evidence for these seven slots only.**

---

## The open `cover_body` drift

`locks_seattle_series.json`'s `cover_body` slot carries both numbers:

```json
"principles_lock": 357,
"observed": 351,
"drift": -6,
```

PRINCIPLES.txt Section 3 documents the cover-body lock as **357**. The live Canva design
(`DAHQoZJm12w`, captured 2026-07-27) measures **351**. CharLint enforces `observed` (351) when it is
present, because copy has to fit the template that actually exists, not the number written down —
but it never silently picks a winner. Every run of `run_charlint()` over this locks file emits a
warning:

```
DRIFT: cover_body — PRINCIPLES.txt documents a lock of 357, the template measures 351 (drift -6).
CharLint is enforcing 351 (`observed`), because copy has to fit the template that exists. Either
the template drifted from the approved baseline or PRINCIPLES.txt records a different baseline;
the owner decides which number is canonical. This warning repeats on every run until the locks
file is reconciled.
```

This is real output — it appears on every run against `locks_seattle_series.json`, pass or fail,
filled or not, truncated or not (`drift_warnings()` in `charlint.py`; see `TestDrift` in
`test_charlint.py`). It never affects `passed`/`all_passed`, and it is not something CharLint can
resolve on its own — only the owner reconciling PRINCIPLES.txt against the live template makes it
go away. Until then, expect this warning on every single `--ruleset workout_series` run.

---

## The locks-file format

A locks file is one JSON object with two blocks: `slots` (count-locked, rewritten each issue) and
`permanent_slots` (never touched, checked for exact-string identity instead of a count). Both
accept a `_comment`-prefixed key for human notes, which CharLint ignores.

```json
{
  "ruleset": "workout_series",
  "design_id": "DAHQoZJm12w",
  "tolerance": 0,
  "slots": {
    "cover_body": {
      "type": "DYNAMIC",
      "principles_lock": 357,
      "observed": 351,
      "drift": -6,
      "baseline": "Seattle wears its fitness in the open ..."
    }
  },
  "permanent_slots": {
    "brand_subline": { "baseline": "THE CITY IS THE GYM." }
  }
}
```

| Key | Where | Meaning |
|---|---|---|
| `tolerance` | top level, optional | Non-negative int; how many characters of slack every slot in this file gets. Defaults to `DEFAULT_TOLERANCE` = **0** (exact match) when absent. |
| `type` | per slot | One of the 7 Section-4 slot types below. Defaults to `DEFAULT_SLOT_TYPE` = `"DYNAMIC"` in `slots`, `"PERMANENT"` in `permanent_slots`. |
| `principles_lock` | per slot | The count PRINCIPLES.txt (or the master sheet) documents. |
| `observed` | per slot, optional | The count actually measured off the live template. Wins over `principles_lock` when present. |
| `drift` | per slot, optional | Must equal `observed - principles_lock` exactly, or the file is rejected as corrupt. |
| `baseline` | per slot, required | The approved string itself. `len(baseline)` is the ground truth every other number is checked against. |
| `element_id` | per slot, informational | The Canva element ID. Not read by CharLint's logic. |

### Slot taxonomy (PRINCIPLES.txt Section 4)

`charlint.SLOT_TYPES`, in full:

| Type | Meaning | Lives in |
|---|---|---|
| `FIXED` | URLs, footers, header strips — never touched | `permanent_slots` |
| `PERMANENT` | The brand line (e.g. "THE CITY IS THE GYM.") — never touched | `permanent_slots` |
| `ROLLS MONTHLY` | The issue/date line | `slots` |
| `ROLLS PER VOLUME` | Title, kicker, neighborhood, overview | `slots` |
| `DYNAMIC` | Count-locked bodies, rewritten every issue | `slots` |
| `UNLOCKED` | Owner-flagged; counts may flex (e.g. an editor's note) | `slots`, but not count-gated |
| `MANUAL` | Owner-swapped only (e.g. next-issue upsell) | `slots`, but not required to be filled |

A type mismatch is rejected at load time, in both directions: a `FIXED`/`PERMANENT` type sitting in
`slots`, or any other type sitting in `permanent_slots`, raises `CorruptLocksError`
(`charlint.NEVER_TOUCHED_TYPES = ("FIXED", "PERMANENT")`).

`UNLOCKED` slots (`charlint.FLEX_TYPES`) are measured and reported but never count-gated — and a
warning is emitted every run so an un-gated slot is never invisible (`"UNLOCKED: <name> is
owner-flagged UNLOCKED ..."`). `UNLOCKED` and `MANUAL` slots (`charlint.OPTIONAL_TYPES`) are also
exempt from the "not filled" check: an issue submission is not expected to supply them at all, and
their absence is not a failure.

### Validation, at load time

`load_locks()` / `validate_locks()` reject a file that disagrees with itself — this runs on every
load, including an in-memory dict a caller edited after loading it:

- No `slots` object, or `slots` is empty (a locks file that gates nothing would pass anything).
- A slot's `observed` (when present) does not equal `len(baseline)`.
- A slot's `drift` (when present) does not equal `observed - principles_lock`.
- Neither `principles_lock` nor `observed` is present.
- The enforced number (`observed` if present, else `principles_lock`) disagrees with
  `len(baseline)` — i.e. the baseline would fail its own lock.
- `tolerance` is present and is not a non-negative int (a `true` is rejected too — `bool` is an
  `int` subclass in Python, so a boolean here is corrupt data, not a valid 0/1).
- The same slot name appears in both `slots` and `permanent_slots`.
- An unrecognized `type` value.

All of these raise `charlint.CorruptLocksError` (a `ValueError` subclass). None of them are
warnings — a locks file that disagrees with itself is refused outright, never partially trusted.

---

## The API

```python
from charlint import (
    load_locks, validate_locks, run_charlint, check_slot, chars_to_target,
    drift_warnings, slot_names, permanent_slot_names, target_for, enforced_lock,
    format_report, SEATTLE_SERIES_LOCKS,
    CharLintError, CorruptLocksError, UnknownSlotError,
)
```

| Function | Purpose |
|---|---|
| `load_locks(path)` | Load + validate a locks JSON file from a path. |
| `validate_locks(data, source=...)` | Validate an already-loaded mapping in place (idempotent). |
| `run_charlint(candidates, locks)` | The main entry point — see below. `locks` accepts a path or an already-loaded mapping. |
| `check_slot(name, candidate, locks)` | Check one slot's candidate string. |
| `chars_to_target(name, candidate, locks)` | Writer-convergence readout — how many characters to add/remove, and which direction. |
| `drift_warnings(locks)` | The list of drift + un-gated-slot warnings for a locks file. |
| `slot_names(locks)` / `permanent_slot_names(locks)` | Slot names, in file order. |
| `target_for(name, locks)` | The enforced character target for one slot (works for permanent slots too — their target is `len(baseline)`). |
| `enforced_lock(spec)` | `observed` if present, else `principles_lock`, for one slot's raw spec dict. |
| `format_report(result)` | Render a `run_charlint()` result as a plain-text table + violations + warnings. |
| `SEATTLE_SERIES_LOCKS` | A convenience path constant pointing at `locks_seattle_series.json` next to this module. **Not** a default — `run_charlint()` always requires an explicit locks argument. |

There is no default locks file anywhere in this module — `run_charlint(candidates)` with no locks
argument raises `TypeError`, by design, so a new product line can bring its own locks file without
editing `charlint.py`.

### `run_charlint(candidates, locks)` — return shape

```python
{
  "slots": {
    slot_name: {
      "violations": [str, ...],
      "score": int,          # starts at 100, penalties applied, floor 0
      "passed": bool,
      "expected": int,       # the ENFORCED lock for this slot
      "actual": int,         # canonical (NFC) character count — what the layout renders, not a raw len()
      "delta": int,          # actual - expected; + over, - under
      "failure_mode": str | None,   # "overflow" | "underfill" | "permanent_mutation" | "not_filled" | None
      "nfc_normalized": bool,        # True when the raw candidate was not already NFC-composed
    },
    ...
  },
  "warnings": [str, ...],    # drift + un-gated-slot warnings, every run, pass or fail
  "summary": {"total_score": int, "all_passed": bool},
}
```

Which slots appear in `"slots"`:
- Every count-locked slot, **always** — filled or not. A missing slot is reported as `not_filled`,
  never silently skipped (a gate that passes an empty submission is worthless).
- A `PERMANENT`/`FIXED` slot **only if a candidate was supplied for it**. An issue fill is not
  expected to touch these at all, so omitting them is correct and not a failure — but if one *is*
  supplied, it must match its baseline exactly.
- `UNLOCKED`/`MANUAL` slots that were not supplied are simply absent from the result (not reported
  as failing, not reported as passing — they are owner-governed).

An unknown slot name in `candidates` — one the locks file does not define — raises
`UnknownSlotError` rather than being silently dropped, mirroring ProhibLint's "unknown ruleset
raises" and the orchestrator's "unknown section name raises" policy throughout this harness.

---

## Overflow vs. underfill

`delta = actual - expected` is signed and the two directions are named and handled distinctly,
because they break the layout differently:

- **overflow** (`delta > 0`, `failure_mode = "overflow"`): the candidate is too long. "the box
  overruns — the text wraps past its last line and pushes off the page."
- **underfill** (`delta < 0`, `failure_mode = "underfill"`): the candidate is too short. "the box
  runs short — a runt last line, and the block loses the rhythm the layout was approved on."

Penalty: `PENALTY_PER_CHAR = -10` per character beyond `tolerance`, floored at
`MAX_CHAR_PENALTY = -100` (so `score = max(0, 100 + max(-100, -10 * excess))`). **Any excess beyond
tolerance is an automatic hard fail — `passed` is `False` regardless of the resulting score.** A
3-character miss scores exactly 70 and still fails; there is no "close enough" band (see "There is
no `PASS_THRESHOLD` in this module" below).

Real example — `python3 charlint.py --locks locks_seattle_series.json --candidates <a file with
"cover_body" 17 characters over its lock>`:

```
Slot               Lock  Actual   Delta  Status
---------------- ------ ------- -------  ------
cover_body          351     368     +17  FAIL
city_intro          628     628      +0  PASS
anchor_venue        667     667      +0  PASS
anchor_cafe         694     694      +0  PASS
counter_venue       602     602      +0  PASS
counter_cafe        414     414      +0  PASS
night_page          616     616      +0  PASS
  [cover_body] OVERFLOW: cover_body is 17 character(s) over the enforced lock. Enforced lock 351,
  candidate 368, delta +17. Remove 17 character(s) to land on the lock. Hard fail — the box
  overruns — the text wraps past its last line and pushes off the page.
  [warning] DRIFT: cover_body — PRINCIPLES.txt documents a lock of 357, the template measures 351
  (drift -6). ...

TOTAL 600  OVERALL FAIL
```

Note the count is **characters, not bytes**: baselines carry em-dashes, en-dashes, curly
apostrophes, é, and middle dots; `len()` on a Python 3 `str` is what CharLint uses.
`test_charlint.py::TestUnicode` pins the decisive case directly — swapping one em-dash for three
ASCII hyphens leaves the UTF-8 byte count unchanged but changes the character count by 2, and
CharLint must (and does) fail that. There is also **no normalization**: a trailing space, a leading
space, a doubled inter-sentence space, or a `\n` vs `\r\n` line ending are all real characters that
change `delta` and can flip `passed` — nothing is stripped or collapsed before counting, because the
layout receives exactly what was submitted.

### The writer-convergence helper

PRINCIPLES.txt Section 3 describes writing to a lock as "assembling candidate segments and
swapping word-level alternates until the count lands on the lock to the character." `chars_to_target()`
is the read-out for that loop — real example:

```python
>>> chars_to_target("counter_venue", draft, locks)
{
  "slot": "counter_venue", "expected": 602, "actual": 577, "delta": -25,
  "chars_needed": 25, "action": "add", "tolerance": 0, "within_tolerance": false,
  "message": "counter_venue: 577 characters, lock 602. Add 25 character(s)."
}
```

`chars_needed` is signed from the writer's point of view (`+` = add, `-` = remove) — the opposite
sign convention from `delta`, which is signed from the lock's point of view.

---

## Permanent-slot protection

A `PERMANENT`/`FIXED` slot is checked by **exact string identity**, not by character count. Any
difference at all — one letter's case, a period swapped for an exclamation point, a middle dot
swapped for an ASCII period, one trailing space — is `failure_mode = "permanent_mutation"`, a hard
fail, `score = 0`, **even when the length does not change at all** (`delta == 0`). This is
deliberately not a count check: `"THE CITY IS THE GYM!"` for `"THE CITY IS THE GYM."` has `delta =
0` and still fails, because PRINCIPLES.txt Section 4 says the brand line is never touched by an
issue fill, full stop — not "touched only in ways that don't change its length." The violation
message names the first index at which the candidate diverges from the baseline
(`_first_diff_index`).

---

## The drift-warning mechanism, in full

`drift_warnings(locks)` emits two kinds of warning, both unconditional (every run, pass or fail,
filled or not) and both incapable of affecting `passed`/`all_passed`:

1. **`DRIFT: <slot>`** — a slot's `principles_lock` and `observed` disagree. Today this fires for
   exactly one slot in `locks_seattle_series.json` (`cover_body`, 357 vs 351 — see above);
   `night_page` records `observed == principles_lock == 616` and produces no warning, and every
   other slot has no `observed` at all (only `principles_lock`), which is also not drift — drift
   requires both numbers to be present and to disagree.
2. **`UNLOCKED: <slot>`** — a slot is typed `UNLOCKED`, so its count is not gated at all. Listed on
   every run so an un-gated slot is never invisible. (`locks_seattle_series.json` has none of
   these today; all 7 slots are `DYNAMIC`.)

Drift is a property of the **locks file**, not of the candidate copy, so it is reported even for an
empty submission, a submission that never reaches this slot under `--fail-fast`, or a fully passing
run — `test_charlint.py::TestDrift::test_drift_warning_appears_on_a_fully_passing_run` pins this
directly. Only the owner reconciling the two numbers in the locks file makes the warning go away;
CharLint does not pick a winner on its own.

---

## Command-line usage

```bash
# Identity run: every baseline fed back as its own candidate (proves the file is self-consistent)
python3 charlint.py --locks locks_seattle_series.json

# Check specific candidate text against the locks
python3 charlint.py --locks locks_seattle_series.json --candidates candidates.json
```

`--candidates` points at a JSON file of `{slot_name: text}`. Omit it to run the identity case.
Real identity-run output (from this repo, `charlint/` as the working directory):

```
Slot               Lock  Actual   Delta  Status
---------------- ------ ------- -------  ------
cover_body          351     351      +0  PASS
city_intro          628     628      +0  PASS
anchor_venue        667     667      +0  PASS
anchor_cafe         694     694      +0  PASS
counter_venue       602     602      +0  PASS
counter_cafe        414     414      +0  PASS
night_page          616     616      +0  PASS
  [warning] DRIFT: cover_body — PRINCIPLES.txt documents a lock of 357, the template measures 351
  (drift -6). CharLint is enforcing 351 (`observed`), because copy has to fit the template that
  exists. ...

TOTAL 700  OVERALL PASS
```

Exit code: `0` if `summary.all_passed`, else `1`.

### Through the orchestrator

CharLint is not usually called directly — the harness calls it as part of `--ruleset
workout_series` (see the top-level `README.md`). CharLint only ever gates character counts; it does
not lint prose at all (no em-dash/hype-word/exclamation checks — that is ProhibLint's job, run
separately by the orchestrator over the same slot text). A slot can be exactly on its char lock and
still fail the overall run because its prose fails ProhibLint, or vice versa — the orchestrator's
per-slot `status` is `char_passed AND prohib_passed`, not either alone.

Real example: feeding the raw Canva baselines straight through
`orchestrator.py --ruleset workout_series` (no rewriting at all) passes every slot's char count
(delta `+0` everywhere) and passes **6 of 7** on prose too. Only `night_page` fails — it ends "Take
the night — cheers!", which trips ProhibLint's workout_series exclamation-point ban (Check H); this
has nothing to do with em-dashes. `anchor_cafe`'s six em-dashes are three matched pairs, one
aside per sentence, so it is not the stacked-dash offender an earlier pass of this document claimed:

Run from the repo root:

```
$ python3 -c "
import json
locks = json.load(open('charlint/locks_seattle_series.json'))
slots = {name: spec['baseline'] for name, spec in locks['slots'].items()}
json.dump({'issue_id': 'SEA.RAW', 'slots': slots}, open('/tmp/raw_baselines.json', 'w'), indent=2)
"
$ python3 orchestrator.py --issue /tmp/raw_baselines.json --ruleset workout_series \
    --locks charlint/locks_seattle_series.json
...
Slot               Lock  Actual   Delta  Prohib   Status
---------------- ------ ------- ------- ------- --------
cover_body          351     351      +0     100  ✅ PASS
city_intro          628     628      +0     100  ✅ PASS
anchor_venue        667     667      +0     100  ✅ PASS
anchor_cafe         694     694      +0     100  ✅ PASS
counter_venue       602     602      +0     100  ✅ PASS
counter_cafe        414     414      +0     100  ✅ PASS
night_page          616     616      +0      95  ❌ FAIL
```

This is the live baseline text captured from the Canva design, run as-is — it is not a
hypothetical. Whoever next reuses `night_page` as a starting point for new copy should drop the
exclamation point; the other six baselines currently clear every ProhibLint workout_series prose
check as written.

---

## There is no `PASS_THRESHOLD` in this module

`charlint.py` defines no `PASS_THRESHOLD` constant of any kind — verified directly:
`test_charlint.py` pins `not hasattr(charlint_module, "PASS_THRESHOLD")` as its own test, and the
module's docstring states the reason in as many words: "There is deliberately no `PASS_THRESHOLD`
constant in this module: a threshold is what a char lock is not." This is a real design position,
not an oversight — a scored severity band ("close enough") is exactly what PRINCIPLES.txt Section 3
rules out for a locked slot.

The actual rule, unconditionally: any character-count miss beyond `tolerance` (default 0) is
`passed = False`, independent of the resulting `score`; any candidate within tolerance is `passed =
True` with `score = 100`. `test_charlint.py`'s own
`test_score_at_threshold_still_fails_because_char_miss_is_a_hard_fail` pins this directly: a
candidate 3 characters over its lock scores exactly 70 and still fails — `score` is a severity
read-out for triage, and it is never consulted in the pass/fail decision.

---

## Running Tests

From the repo root:

```bash
cd charlint
python3 -m pytest test_charlint.py -q
```

143 tests, all passing as of this writing (`143 passed`).

---

## File Structure

```
charlint/
├── charlint.py               — load_locks, run_charlint, check_slot, chars_to_target, CLI
├── locks_seattle_series.json — the real Seattle Series locks (7 DYNAMIC + 2 PERMANENT slots)
├── test_charlint.py          — pytest suite (143 tests)
├── __init__.py
└── README.md                 — this file
```

---

## Dependencies

stdlib only: `json`, `pathlib`. `pytest` is required to run the test suite, not the module itself.
