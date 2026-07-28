#!/usr/bin/env python3
"""
orchestrator.py — TIMBR Eval Harness Orchestrator.

Runs the linters over one submission and emits a scorecard (stdout table +
JSON on disk). Two product lines, two rulesets:

    magazine (default)   ProhibLint (magazine ruleset) + VoiceLint, over the
                         7 magazine sections. CharLint does NOT apply: that
                         line is governed by word counts, not char locks.

    workout_series       ProhibLint (workout_series ruleset) + CharLint, over
                         the char-locked SLOTS of a locks file. VoiceLint does
                         NOT apply: its section/voice map is built for the
                         magazine's 7 sections.

Usage:
    python3 orchestrator.py --issue issue.json
    python3 orchestrator.py --issue issue.json --ci --fail-fast
    python3 orchestrator.py --issue slots.json --ruleset workout_series \
                            --locks charlint/locks_seattle_series.json

An unknown ruleset raises; there is no silent fallback to magazine.

-------------------------------------------------------------------------------
INPUT FORMATS
-------------------------------------------------------------------------------

magazine:

    {"issue_id": "VOL.04", "theme": "...",
     "sections": {"Training": "...", ... all 7 ...}}

    Section names must be exactly the 7 magazine sections. A missing section is
    a FAILING unit (status FAIL, present=false), never a skipped one — a gate
    that passes an empty submission is worthless. An unknown section name is a
    hard input error, not a silent no-op: ProhibLint only scores its own 7
    names, so a typo'd section would otherwise be handed the default score of
    100 and pass without ever being linted.

workout_series:

    {"issue_id": "SEA.VOL.01", "theme": "...",
     "slots": {"cover_body": "...", "city_intro": "...", ...}}

    Keys are SLOT names from the --locks file (see charlint/locks_*.json), not
    the magazine's sections. A missing count-locked slot is reported by CharLint
    as NOT FILLED and fails. An unknown slot name raises (charlint.UnknownSlotError).

The wrong container key for the ruleset ("sections" under workout_series, or
"slots" under magazine) is an explicit error naming both the key found and the
key expected — never a silently empty run.

-------------------------------------------------------------------------------
SCORECARD JSON — documented keys (see SCORECARD_KEYS)
-------------------------------------------------------------------------------

    issue_id                  str
    theme                     str | null
    ruleset                   "magazine" | "workout_series"
    unit_kind                 "section" | "slot"   <- names the per-unit key below
    overall                   "PASS" | "FAIL"
    run                       completeness block, see below
    linters                   which linters ran, which did not, and why
    sections / slots          per-unit results, keyed by unit_kind + "s".
                              ALWAYS contains every expected unit; units the run
                              never reached carry status "NOT_EVALUATED" and null
                              scores, so a partial run can never read as complete.
    blocking_violations       first 10 BLOCKING violations — the findings that
                              actually cost the run its PASS: violations from a
                              check that failed, the issue-level violations when
                              the issue-level check failed, and the fail-fast
                              stop itself (always first). A PASSING run has none.
    blocking_violations_total count before that cap
    advisory_notes            first 10 non-blocking notes: findings from checks
                              that PASSED (both linters emit penalty-only
                              findings a unit can carry and still pass). These
                              never affect `overall` or the exit code.
    advisory_notes_total      count before that cap
    warnings                  non-failing warnings. CharLint contributes facts
                              about the LOCKS FILE (drift, un-gated slots) on
                              every run, and about the SUBMISSION (an
                              owner-governed slot nobody supplied, a candidate
                              that arrived in a non-NFC spelling). Never affect
                              `overall` or the exit code, and are never dropped.
    issue_level_checks        ProhibLint's mandatory-element block, plus
                              "applicable" (false for workout_series — those
                              checks are magazine Editorial Handbook rules) and
                              "evaluated" (false when applicable but not run).
                              On a fail-fast-truncated magazine run they carry
                              evaluated=false and "passed": null with a reason:
                              they read the whole submission, so a stopped run
                              does not run them. When they DID run, anything
                              other than passed=true fails the issue.
    generated_at              ISO timestamp

    run = {
      "fail_fast":          bool,        # was --fail-fast passed
      "complete":           bool,        # true only when incomplete_reason is null
      "truncated":          bool,        # stopped early by fail-fast
      "truncated_at":       str | null,  # the unit that tripped the stop
      "truncation_reason":  str | null,  # human-readable, in the JSON as well as the console
      "incomplete_reason":  null | "fail_fast_truncation" | "no_units_evaluated"
                                 | "empty_submission",
      "units_expected":     int,         # what the RULESET/locks file requires of
                                         # any submission. Never derived from the
                                         # submission being graded, so sending or
                                         # omitting an optional or permanent slot
                                         # cannot change what was expected of it.
      "units_evaluated":    int,         # can exceed units_expected when a
                                         # submission sends non-required slots
      "evaluated":          [str],
      "not_evaluated":      [str],
    }

-------------------------------------------------------------------------------
--fail-fast: WHAT IT ACTUALLY STOPS
-------------------------------------------------------------------------------

magazine:         everything. Each section is linted inside the loop, so the
                  text of a section past the stop is never handed to ProhibLint
                  or VoiceLint, and the issue-level mandatory-element checks
                  (which read the whole submission) are not run either.

workout_series:   the prose linting and the verdict. CharLint gates a submission
                  in ONE call — that is what lets it report every locked slot,
                  filled or not — so the character counts of the skipped slots
                  were computed before the loop began. `truncation_reason` says
                  so in as many words rather than claiming more than happened.

-------------------------------------------------------------------------------
EXIT CODES
-------------------------------------------------------------------------------

    0  overall == "PASS" — every expected unit was evaluated and passed
    1  overall == "FAIL" — including a fail-fast truncated run and a run in
       which zero units were evaluated. Warnings never produce a 1.
    2  usage / config / input-shape error (unknown ruleset, --locks missing or
       misapplied, unreadable or malformed issue file). Matches argparse's own
       exit code for CLI misuse.

`overall` is "PASS" only when: at least one unit was evaluated, no unit failed,
the run was not truncated, and the applicable issue-level checks passed.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

#: Declared floor, asserted rather than assumed. The harness is run by a bare
#: `python3` (run_eval.sh, CI, a developer's shell), which on any given machine
#: may be an interpreter nobody chose deliberately — this repo's __pycache__
#: carries 3.11 artefacts while the machine that wrote them answers `python3`
#: with 3.9. Everything here is plain 3.8-compatible syntax; the floor is 3.8
#: because that is the oldest interpreter these modules are actually known to
#: run on, and a version error at import is cheaper to read than a SyntaxError
#: three files deep.
MIN_PYTHON = (3, 8)
if sys.version_info < MIN_PYTHON:  # pragma: no cover - depends on the interpreter
    raise RuntimeError(
        "TIMBR eval harness requires Python "
        f"{'.'.join(map(str, MIN_PYTHON))} or newer; this is "
        f"{'.'.join(map(str, sys.version_info[:3]))} at {sys.executable}."
    )

HERE = Path(__file__).resolve().parent

# Add module paths
sys.path.insert(0, str(HERE / "prohiblint"))
sys.path.insert(0, str(HERE / "voicelint"))
sys.path.insert(0, str(HERE / "charlint"))

import prohiblint  # noqa: E402
import voicelint  # noqa: E402
import charlint  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAGAZINE = "magazine"
WORKOUT_SERIES = "workout_series"
VALID_RULESETS = (MAGAZINE, WORKOUT_SERIES)

#: Which container key each ruleset reads its units from.
UNIT_CONTAINER = {MAGAZINE: "sections", WORKOUT_SERIES: "slots"}
UNIT_KIND = {MAGAZINE: "section", WORKOUT_SERIES: "slot"}

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
#: Distinct from FAIL on purpose: "we never looked" is not "we looked and it was
#: bad". A fail-fast scorecard has to say which is which.
STATUS_NOT_EVALUATED = "NOT_EVALUATED"

#: ProhibLint scores only the 7 names in prohiblint.SECTIONS, so a slot's prose
#: has to be handed to it under one of those keys. Under the workout_series
#: ruleset the section name is inert — check_word_count (the only name-dependent
#: check) is skipped — so the choice of probe name cannot change a verdict.
_PROSE_PROBE_SECTION = prohiblint.SECTIONS[0]

VOICELINT_NA_REASON = (
    "VoiceLint's section/voice map is built for the magazine's 7 sections; it "
    "does not apply to the workout_series line."
)
CHARLINT_NA_REASON = (
    "The magazine line is governed by word counts, not char locks; CharLint "
    "does not apply."
)
ISSUE_LEVEL_NA_REASON = (
    "ProhibLint's mandatory-element checks (rep/set notation, >=4 named "
    "Nutrition places, >=2 gyms/studios, >=3 place-type entities) are magazine "
    "Editorial Handbook requirements keyed to the magazine's 7 sections. The "
    "workout_series line is gated by CharLint's char locks instead, so they are "
    "not run and not scored."
)

#: Every key a scorecard is documented to carry, plus the per-unit container
#: named by `unit_kind`. Tests assert on this; consumers can rely on it.
SCORECARD_KEYS = (
    "issue_id",
    "theme",
    "ruleset",
    "unit_kind",
    "overall",
    "run",
    "linters",
    "blocking_violations",
    "blocking_violations_total",
    "advisory_notes",
    "advisory_notes_total",
    "warnings",
    "issue_level_checks",
    "generated_at",
)

RUN_KEYS = (
    "fail_fast",
    "complete",
    "truncated",
    "truncated_at",
    "truncation_reason",
    "incomplete_reason",
    "units_expected",
    "units_evaluated",
    "evaluated",
    "not_evaluated",
)

MAX_BLOCKING_VIOLATIONS = 10


# ---------------------------------------------------------------------------
# Errors — all usage/config/input problems, all exit 2 from the CLI
# ---------------------------------------------------------------------------

class EvalHarnessError(Exception):
    """Base class for orchestrator-level errors."""


class UnknownRulesetError(EvalHarnessError, ValueError):
    """A ruleset name the harness does not implement. Never falls back."""


class IssueFormatError(EvalHarnessError, ValueError):
    """The issue file is unreadable, or is not shaped for the chosen ruleset."""


class LocksArgumentError(EvalHarnessError, ValueError):
    """--locks was omitted where it is required, or passed where it is meaningless."""


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

def validate_ruleset(ruleset):
    """Return `ruleset` if the harness implements it, else raise."""
    if ruleset not in VALID_RULESETS:
        raise UnknownRulesetError(
            f"Unknown ruleset {ruleset!r}. Valid rulesets: "
            f"{', '.join(repr(r) for r in VALID_RULESETS)}. There is no silent "
            f"fallback to {MAGAZINE!r} — a typo'd ruleset would gate the copy "
            f"against the wrong product line's rules."
        )
    return ruleset


def validate_locks_argument(ruleset, locks):
    """
    --locks is required for workout_series and meaningless for magazine.

    Checked before anything is read, so the mistake is reported as a usage
    error rather than surfacing later as a confusing empty or wrong-line run.
    """
    validate_ruleset(ruleset)
    if ruleset == WORKOUT_SERIES and not locks:
        raise LocksArgumentError(
            f"--locks is required for --ruleset {WORKOUT_SERIES}: CharLint has "
            f"no default locks file, so the harness cannot know which char "
            f"locks to gate against (e.g. --locks charlint/locks_seattle_series.json)."
        )
    if ruleset == MAGAZINE and locks:
        raise LocksArgumentError(
            f"--locks is meaningless for --ruleset {MAGAZINE}: CharLint does not "
            f"run on the magazine line, which is governed by word counts, not "
            f"char locks. Drop --locks, or pass --ruleset {WORKOUT_SERIES} if "
            f"this submission is Workout Series copy."
        )
    return locks


def load_issue(issue_path):
    """Read and JSON-parse an issue file. Raises IssueFormatError."""
    path = Path(issue_path)
    try:
        with open(path, encoding="utf-8") as fh:
            issue = json.load(fh)
    except FileNotFoundError:
        raise IssueFormatError(f"Issue file not found: {path}")
    except json.JSONDecodeError as exc:
        raise IssueFormatError(f"Issue file {path} is not valid JSON: {exc}")
    if not isinstance(issue, dict):
        raise IssueFormatError(
            f"Issue file {path} must contain a JSON object, got "
            f"{type(issue).__name__}."
        )
    return issue


def extract_units(issue, ruleset, source="<issue>"):
    """
    Pull the {name: text} unit map for `ruleset` out of a loaded issue.

    A mismatched shape (magazine sections handed to workout_series, or the
    reverse) is an error naming both the key found and the key expected. An
    unknown shape is an error too. Neither is allowed to become a silently
    empty run that then reports PASS.
    """
    validate_ruleset(ruleset)
    want = UNIT_CONTAINER[ruleset]
    other = UNIT_CONTAINER[WORKOUT_SERIES if ruleset == MAGAZINE else MAGAZINE]

    declared = issue.get("ruleset")
    if declared is not None and declared != ruleset:
        raise IssueFormatError(
            f"{source} declares \"ruleset\": {declared!r} but the harness was "
            f"asked to run {ruleset!r}. Refusing to gate copy against a "
            f"ruleset its own file disagrees with; pass --ruleset {declared!r} "
            f"or fix the file."
        )

    other_ruleset = WORKOUT_SERIES if ruleset == MAGAZINE else MAGAZINE

    if want not in issue:
        if other in issue:
            raise IssueFormatError(
                f"{source} has no {want!r} key but does have {other!r}, which is "
                f"the {other_ruleset} shape. Under --ruleset {ruleset} the "
                f"harness reads {want!r}: an object of {UNIT_KIND[ruleset]} "
                f"name -> text. Either pass --ruleset {other_ruleset} or supply "
                f"{want!r}."
            )
        raise IssueFormatError(
            f"{source} has no {want!r} key. Under --ruleset {ruleset} the "
            f"harness reads {want!r}: an object of "
            f"{UNIT_KIND[ruleset]} name -> text. Keys found: "
            f"{', '.join(sorted(map(str, issue))) or '(none)'}."
        )

    units = issue[want]
    if not isinstance(units, dict):
        raise IssueFormatError(
            f"{source}: {want!r} must be an object of {UNIT_KIND[ruleset]} "
            f"name -> text, got {type(units).__name__}."
        )
    bad = sorted(name for name, text in units.items() if not isinstance(text, str))
    if bad:
        raise IssueFormatError(
            f"{source}: {want!r} entries must be strings; these are not: "
            f"{', '.join(repr(b) for b in bad)}."
        )
    return units


# ---------------------------------------------------------------------------
# Unit result helpers
# ---------------------------------------------------------------------------

def _not_evaluated_unit(ruleset, present):
    """
    The placeholder for a unit the run never reached.

    Every score is null, never 0 and never 100: a NOT_EVALUATED unit must be
    impossible to mistake for either a pass or a fail.
    """
    unit = {
        "prohib_score": None,
        "prohib_passed": None,
        "violations": [],
        "status": STATUS_NOT_EVALUATED,
        "present": present,
    }
    if ruleset == MAGAZINE:
        unit["voice_score"] = None
        unit["voice_passed"] = None
    else:
        unit.update({
            "char_expected": None,
            "char_actual": None,
            "char_delta": None,
            "char_score": None,
            "char_passed": None,
            "failure_mode": None,
        })
    return unit


def _truncation_reason(unit_kind, name, not_evaluated, work_note=""):
    """
    The human-readable record of a fail-fast stop.

    `work_note` is supplied by the evaluator and says exactly what "never
    evaluated" means on that product line, because it is not identical on both
    and a block that describes itself has to describe itself accurately.
    """
    note = f" {work_note}" if work_note else ""
    return (
        f"fail-fast: {unit_kind} '{name}' failed and --fail-fast was set, so "
        f"evaluation stopped there. {len(not_evaluated)} {unit_kind}(s) were "
        f"never evaluated: {', '.join(not_evaluated)}.{note} This scorecard is a "
        f"PARTIAL run and is not evidence that the rest of the submission is "
        f"clean."
    )


#: What a magazine fail-fast stop actually stops. Each section is linted inside
#: the loop, one at a time, so a skipped section's text is never handed to
#: either linter.
MAGAZINE_TRUNCATION_NOTE = (
    "No linter was run on their text, and the issue-level mandatory-element "
    "checks were not run either."
)

#: The workout_series equivalent, and deliberately weaker. CharLint gates a
#: submission in ONE call — that is what lets it report every locked slot,
#: filled or not — so the char measurements exist before the loop starts. What
#: the stop genuinely stops is the prose linting and the verdict.
WORKOUT_SERIES_TRUNCATION_NOTE = (
    "CharLint measures every locked slot in a single whole-submission pass, so "
    "their character counts were computed; no prose linting was run on them and "
    "no verdict was reached for them."
)

ISSUE_LEVEL_TRUNCATED_REASON = (
    "Not evaluated: the run stopped at the first failing section (--fail-fast), "
    "and ProhibLint's mandatory-element checks read the whole submission. A "
    "partial submission cannot answer them, so they were not run rather than "
    "answered against copy the run never finished reading."
)


def _linter_section(results, section, linter):
    """
    One section's verdict out of a linter's result map, or a loud error.

    The magazine verdict is ProhibLint AND VoiceLint. A linter that returns
    nothing for a section must never be read as "nothing to report": that is a
    silent pass, which is the failure mode this whole harness exists to
    prevent.
    """
    verdict = results.get(section) if isinstance(results, dict) else None
    if not isinstance(verdict, dict) or not isinstance(verdict.get("passed"), bool):
        raise EvalHarnessError(
            f"{linter} returned no usable verdict for section {section!r} "
            f"(got {verdict!r}). The magazine verdict is ProhibLint AND "
            f"VoiceLint; a missing verdict is not a pass."
        )
    return verdict


# ---------------------------------------------------------------------------
# magazine ruleset
# ---------------------------------------------------------------------------

def _evaluate_magazine(sections, fail_fast, source="<issue>"):
    known = list(prohiblint.SECTIONS)
    unknown = sorted(set(sections) - set(known))
    if unknown:
        raise IssueFormatError(
            f"{source}: unknown section name(s) "
            f"{', '.join(repr(u) for u in unknown)}. The magazine ruleset "
            f"scores exactly these 7 sections: {', '.join(known)}. Names are "
            f"not silently ignored — ProhibLint and VoiceLint only score their "
            f"own section names, so a typo'd section would be handed default "
            f"scores and pass without ever being linted."
        )

    units = {}
    blocking = {}
    advisory = {}
    truncated_at = None

    for section in known:
        present = section in sections
        if not present:
            # Absent, not evaluated-and-clean. Mirrors CharLint's NOT FILLED.
            missing = (
                f"MISSING SECTION: '{section}' is required by the magazine "
                f"ruleset but absent from the issue file. Hard fail — an "
                f"unwritten section is not a passing section."
            )
            units[section] = {
                "voice_score": None,
                "voice_passed": False,
                "prohib_score": None,
                "prohib_passed": False,
                "violations": [missing],
                "status": STATUS_FAIL,
                "present": False,
            }
            blocking[section] = [missing]
            advisory[section] = []
        else:
            # Linted HERE, one section at a time, and not before the loop: with
            # --fail-fast the sections past the stop are never handed to either
            # linter, so "never evaluated" in the scorecard is literally true
            # rather than "evaluated, then thrown away".
            text = sections[section]
            p = _linter_section(
                prohiblint.run_prohiblint({section: text}, ruleset=MAGAZINE).get("sections"),
                section, "ProhibLint")
            v = _linter_section(voicelint.run({section: text}), section, "VoiceLint")

            prohib_pass = p["passed"]
            voice_pass = v["passed"]
            prohib_violations = list(p.get("violations", []))
            voice_flags = list(v.get("contamination_flags", []))

            # BOTH linters gate the magazine line. Dropping either one from
            # this conjunction is the single worst regression available to this
            # file, so it is spelled out rather than folded into a helper.
            passed = prohib_pass and voice_pass

            units[section] = {
                "voice_score": v.get("voice_score", 0),
                "voice_passed": voice_pass,
                "prohib_score": p.get("score", 100),
                "prohib_passed": prohib_pass,
                "violations": prohib_violations + voice_flags,
                "status": STATUS_PASS if passed else STATUS_FAIL,
                "present": True,
            }
            # A note from a linter that PASSED the section did not block
            # anything, and calling it a blocking violation is how a green run
            # ends up reporting a violation count.
            blocking[section] = ((prohib_violations if not prohib_pass else [])
                                 + (voice_flags if not voice_pass else []))
            advisory[section] = ((prohib_violations if prohib_pass else [])
                                 + (voice_flags if voice_pass else []))

        if fail_fast and units[section]["status"] == STATUS_FAIL:
            truncated_at = section
            break

    # Issue-level mandatory elements read the WHOLE submission, so they run
    # after the section loop — and not at all when the loop stopped early,
    # because that is work the stop is supposed to stop.
    if truncated_at is None:
        issue_level = dict(prohiblint.check_mandatory_elements(sections),
                           applicable=True, evaluated=True)
    else:
        # `evaluated: False` is stated rather than inferred from passed=None,
        # because "we did not run this" and "this returned no answer" have to
        # land differently: the first is covered by the truncation, the second
        # is a linter failing to answer and must never be read as a pass.
        issue_level = {
            "applicable": True,
            "evaluated": False,
            "passed": None,
            "violations": [],
            "penalty": 0,
            "element_results": {},
            "reason": ISSUE_LEVEL_TRUNCATED_REASON,
        }

    return {
        "unit_kind": UNIT_KIND[MAGAZINE],
        "units": units,
        "expected": known,
        # Required by the RULESET, not by what the submission happened to send.
        "required": known,
        "truncated_at": truncated_at,
        "truncation_note": MAGAZINE_TRUNCATION_NOTE,
        "issue_level": issue_level,
        "blocking": blocking,
        "advisory": advisory,
        "warnings": [],
        "linters": {
            "prohiblint": {"applied": True, "ruleset": MAGAZINE},
            "voicelint": {"applied": True},
            "charlint": {"applied": False, "reason": CHARLINT_NA_REASON},
        },
    }


# ---------------------------------------------------------------------------
# workout_series ruleset
# ---------------------------------------------------------------------------

def _prose_result(text):
    """
    ProhibLint's workout_series prose verdict for one slot's text.

    Handed to ProhibLint under a probe section name because run_prohiblint only
    scores prohiblint.SECTIONS; under this ruleset the name is inert (see
    _PROSE_PROBE_SECTION). The issue-level block of that call is discarded —
    it is a magazine check (ISSUE_LEVEL_NA_REASON).
    """
    raw = prohiblint.run_prohiblint({_PROSE_PROBE_SECTION: text}, ruleset=WORKOUT_SERIES)
    return raw["sections"][_PROSE_PROBE_SECTION]


def _evaluate_workout_series(slots, locks_path, fail_fast, source="<issue>"):
    # CorruptLocksError is left to propagate untouched: CharLint is the authority
    # on a locks file that disagrees with itself, and its message says exactly
    # which number is wrong. Unreadable/unparseable is a plain usage error.
    try:
        locks = charlint.load_locks(locks_path)
    except OSError as exc:
        raise LocksArgumentError(f"--locks {locks_path}: {exc.strerror or exc}") from exc
    except json.JSONDecodeError as exc:
        raise LocksArgumentError(f"--locks {locks_path} is not valid JSON: {exc}") from exc
    permanent = set(charlint.permanent_slot_names(locks))

    # CharLint gates the whole submission in one call: it reports every locked
    # slot, filled or not (a missing slot is NOT FILLED, never a skip), and it
    # rejects a slot name the locks file does not define.
    try:
        char_raw = charlint.run_charlint(slots, locks)
    except charlint.UnknownSlotError as exc:
        raise IssueFormatError(f"{source}: {exc}") from exc
    char_slots = char_raw.get("slots", {})

    expected = list(char_slots)
    units = {}
    blocking = {}
    advisory = {}
    truncated_at = None

    for name in expected:
        c = char_slots[name]
        present = name in slots
        unit = {
            "char_expected": c.get("expected"),
            "char_actual": c.get("actual"),
            "char_delta": c.get("delta"),
            "char_score": c.get("score"),
            "char_passed": c.get("passed"),
            "failure_mode": c.get("failure_mode"),
            "prohib_score": None,
            "prohib_passed": None,
            "violations": list(c.get("violations", [])),
            "present": present,
        }

        char_passed = bool(c.get("passed"))
        char_violations = list(c.get("violations", []))
        prose_violations = []
        prose_passed = None

        # Prose is linted only where there is prose to lint, and only when the
        # loop actually reaches this slot — so --fail-fast genuinely stops the
        # prose work. A PERMANENT slot is never rewritten (PRINCIPLES.txt
        # Sec. 4) — CharLint's exact-string check is its gate — and an unfilled
        # slot has no text at all.
        if present and name not in permanent:
            p = _prose_result(slots[name])
            prose_passed = p["passed"]
            prose_violations = list(p["violations"])
            unit["prohib_score"] = p["score"]
            unit["prohib_passed"] = prose_passed
            unit["violations"].extend(prose_violations)

        passed = char_passed and prose_passed is not False
        unit["status"] = STATUS_PASS if passed else STATUS_FAIL
        units[name] = unit
        blocking[name] = ((char_violations if not char_passed else [])
                          + (prose_violations if prose_passed is False else []))
        advisory[name] = ((char_violations if char_passed else [])
                          + (prose_violations if prose_passed is not False else []))

        if fail_fast and unit["status"] == STATUS_FAIL:
            truncated_at = name
            break

    return {
        "unit_kind": UNIT_KIND[WORKOUT_SERIES],
        "units": units,
        "expected": expected,
        # What the LOCKS FILE requires of any submission. Deliberately not
        # len(char_slots): that grows when a submitter sends a permanent slot
        # and shrinks when nobody sends an owner-governed one, which would make
        # "expected" a function of the submission being graded.
        "required": charlint.required_slot_names(locks),
        "truncated_at": truncated_at,
        "truncation_note": WORKOUT_SERIES_TRUNCATION_NOTE,
        "blocking": blocking,
        "advisory": advisory,
        # Not applicable, and said so out loud rather than reported as a pass.
        "issue_level": {
            "applicable": False,
            "evaluated": False,
            "passed": None,
            "violations": [],
            "penalty": 0,
            "element_results": {},
            "reason": ISSUE_LEVEL_NA_REASON,
        },
        # Drift / un-gated-slot warnings are a property of the LOCKS FILE, not
        # of the copy, so they are emitted on every run — including a truncated
        # or empty one — and never affect pass/fail.
        "warnings": list(char_raw.get("warnings", [])),
        "linters": {
            "prohiblint": {"applied": True, "ruleset": WORKOUT_SERIES},
            "voicelint": {"applied": False, "reason": VOICELINT_NA_REASON},
            "charlint": {"applied": True, "locks": str(locks_path)},
        },
    }


# ---------------------------------------------------------------------------
# Console rendering
# ---------------------------------------------------------------------------

def _fmt(value, width):
    return f"{'—' if value is None else value:>{width}}"


def _print_header(issue_id, ruleset, theme, locks):
    print(f"\n{'='*60}")
    print(f"  TIMBR EVAL HARNESS — {issue_id}")
    print(f"  Ruleset: {ruleset}")
    if locks:
        print(f"  Locks: {locks}")
    print(f"  Theme: {theme or 'N/A'}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")


def _status_cell(status):
    icon = {STATUS_PASS: "✅", STATUS_FAIL: "❌"}.get(status, "⏭")
    return f"{icon} {status}"


def _print_magazine_table(units):
    print(f"{'Section':<14} {'Voice':>6} {'Prohib':>7} {'Status':>8}")
    print(f"{'-'*14} {'-'*6} {'-'*7} {'-'*8}")
    for sec, res in units.items():
        print(f"{sec:<14} {_fmt(res['voice_score'], 5)}  {_fmt(res['prohib_score'], 6)}  "
              f"{_status_cell(res['status'])}")


def _print_workout_series_table(units):
    print(f"{'Slot':<16} {'Lock':>6} {'Actual':>7} {'Delta':>7} {'Prohib':>7} {'Status':>8}")
    print(f"{'-'*16} {'-'*6} {'-'*7} {'-'*7} {'-'*7} {'-'*8}")
    for slot, res in units.items():
        delta = res["char_delta"]
        delta_cell = "—" if delta is None else f"{delta:+d}"
        print(f"{slot:<16} {_fmt(res['char_expected'], 6)} {_fmt(res['char_actual'], 7)} "
              f"{delta_cell:>7} {_fmt(res['prohib_score'], 7)}  "
              f"{_status_cell(res['status'])}")


def _print_console(scorecard, ci):
    unit_key = scorecard["unit_kind"] + "s"
    units = scorecard[unit_key]
    run = scorecard["run"]
    warnings = scorecard["warnings"]

    if ci:
        for name, res in units.items():
            if res["status"] == STATUS_FAIL:
                for v in res["violations"][:3]:
                    print(f"[{name}] {v}")
        for v in scorecard["issue_level_checks"].get("violations", []):
            print(f"[issue-level] {v}")
        # Warnings are not failures and never change the exit code, but they are
        # never dropped either — CI is where the owner will actually see them.
        for w in warnings:
            print(f"[warning] {w}")
        if run["truncated"]:
            print(f"TRUNCATED: {run['truncation_reason']}")
        elif run["incomplete_reason"]:
            print(f"INCOMPLETE: {run['truncation_reason']}")
        print(scorecard["overall"])
        return

    if run["truncated"]:
        print(f"FAIL-FAST: {scorecard['unit_kind']} '{run['truncated_at']}' failed. "
              f"Stopping — {len(run['not_evaluated'])} "
              f"{scorecard['unit_kind']}(s) will NOT be evaluated.\n")

    if scorecard["ruleset"] == MAGAZINE:
        _print_magazine_table(units)
    else:
        _print_workout_series_table(units)

    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}) — not failures, exit code unaffected:")
        for w in warnings:
            print(f"    • {w}")

    print(f"\n{'─'*60}")
    if run["truncated"]:
        print("  RUN: TRUNCATED (--fail-fast) — PARTIAL RESULT, NOT A FULL EVALUATION")
        print(f"  Stopped at: {run['truncated_at']}")
        print(f"  Evaluated ({run['units_evaluated']}/{run['units_expected']}): "
              f"{', '.join(run['evaluated'])}")
        print(f"  NOT evaluated ({len(run['not_evaluated'])}): "
              f"{', '.join(run['not_evaluated'])}")
    elif run["incomplete_reason"] == "no_units_evaluated":
        print("  RUN: NOTHING EVALUATED — an empty submission cannot pass a quality gate")
    elif run["incomplete_reason"] == "empty_submission":
        print(f"  RUN: NOTHING SUBMITTED — no {scorecard['unit_kind']}s were sent, so "
              f"no copy was read")
        print(f"  Every expected {scorecard['unit_kind']} is reported missing; this is "
              f"not a completed evaluation")
    else:
        print(f"  RUN: complete ({run['units_evaluated']} {scorecard['unit_kind']}(s) "
              f"evaluated, {run['units_expected']} required by the ruleset)")

    print(f"  OVERALL: {scorecard['overall']}")
    blocking_total = scorecard["blocking_violations_total"]
    if blocking_total:
        print(f"  TOP VIOLATIONS ({blocking_total} blocking):")
        for v in scorecard["blocking_violations"][:3]:
            print(f"    • {v}")
    advisory_total = scorecard["advisory_notes_total"]
    if advisory_total:
        # Penalties too small to fail anything. Counted, and named for what they
        # are — these never blocked anything, so they are not violations.
        print(f"  Advisory notes: {advisory_total} — non-blocking, did not affect "
              f"OVERALL (full list in the scorecard JSON)")
    print(f"{'─'*60}\n")


# ---------------------------------------------------------------------------
# Scorecard assembly + main entry point
# ---------------------------------------------------------------------------

def scorecard_filename(issue_id):
    """`results/` filename for an issue id, sanitised so it cannot escape the dir."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", str(issue_id)).replace(".", "_").strip("_")
    return f"{safe or 'UNKNOWN'}_scorecard.json"


def run_eval(issue_path, ci=False, fail_fast=False, ruleset=MAGAZINE, locks=None,
             results_dir=None, write=True):
    """
    Evaluate one submission and return its scorecard dict.

    Args:
        issue_path: path to the issue JSON (shape depends on `ruleset`).
        ci: minimal, machine-readable stdout.
        fail_fast: stop at the first failing unit. The scorecard then records
            the truncation explicitly and can never report PASS.
        ruleset: "magazine" (default) or "workout_series". Unknown raises.
        locks: path to a CharLint locks file. Required for workout_series,
            rejected for magazine.
        results_dir: where the scorecard JSON is written. Defaults to
            ./results next to this file; tests should pass a tmp dir.
        write: set False to skip writing the JSON entirely.

    Raises:
        UnknownRulesetError, LocksArgumentError, IssueFormatError,
        charlint.CorruptLocksError, charlint.UnknownSlotError.
    """
    validate_ruleset(ruleset)
    validate_locks_argument(ruleset, locks)

    issue = load_issue(issue_path)
    units_in = extract_units(issue, ruleset, source=str(issue_path))

    issue_id = issue.get("issue_id", "UNKNOWN")
    theme = issue.get("theme")

    if not ci:
        _print_header(issue_id, ruleset, theme, locks)

    if ruleset == MAGAZINE:
        outcome = _evaluate_magazine(units_in, fail_fast, source=str(issue_path))
    else:
        outcome = _evaluate_workout_series(units_in, locks, fail_fast, source=str(issue_path))

    unit_kind = outcome["unit_kind"]
    units = dict(outcome["units"])
    expected = list(outcome["expected"])
    required = list(outcome["required"])
    evaluated = list(units)
    not_evaluated = [n for n in expected if n not in units]
    truncated_at = outcome["truncated_at"]
    truncated = truncated_at is not None

    # Units the run never reached are still emitted — as NOT_EVALUATED with null
    # scores — so `sections`/`slots` always holds the full expected set and a
    # partial scorecard cannot be mistaken for a complete one.
    for name in not_evaluated:
        units[name] = _not_evaluated_unit(ruleset, present=name in units_in)
    units = {name: units[name] for name in expected}

    issue_level = outcome["issue_level"]
    # Three states, kept distinct: not applicable to this line; applicable but
    # deliberately not run (a truncated run — the truncation is what fails it);
    # or it ran, in which case anything other than an explicit True is a
    # failure. A check that returns no answer is not a check that passed.
    issue_level_failed = (issue_level.get("applicable", True)
                          and issue_level.get("evaluated", True)
                          and issue_level.get("passed") is not True)

    any_failed = any(u["status"] == STATUS_FAIL for u in units.values())
    nothing_evaluated = len(evaluated) == 0
    #: Nothing was SUBMITTED, whatever the gate then reported about it. The
    #: magazine line still emits seven MISSING-SECTION failures for an empty
    #: file, which is correct — but a run that read no copy at all has not
    #: completed anything, and `complete: true` on it is a lie of the same
    #: family as a truncated run claiming completeness.
    nothing_submitted = len(units_in) == 0

    incomplete_reason = None
    truncation_reason = None
    if truncated:
        incomplete_reason = "fail_fast_truncation"
        truncation_reason = _truncation_reason(
            unit_kind, truncated_at, not_evaluated, outcome.get("truncation_note", ""))
    elif nothing_evaluated:
        incomplete_reason = "no_units_evaluated"
        truncation_reason = (
            f"No {unit_kind}s were evaluated: the submission supplied nothing "
            f"this ruleset gates. An empty submission cannot pass a quality "
            f"gate, so the run is a FAIL."
        )
    elif nothing_submitted:
        incomplete_reason = "empty_submission"
        truncation_reason = (
            f"The submission contained no {unit_kind}s at all. Every expected "
            f"{unit_kind} is reported as missing and the run is a FAIL, but no "
            f"copy was read, so this run is NOT a completed evaluation of "
            f"anything."
        )

    overall = STATUS_PASS
    if any_failed or issue_level_failed or truncated or nothing_evaluated or nothing_submitted:
        overall = STATUS_FAIL

    # BLOCKING vs ADVISORY. A violation is blocking when it belongs to a check
    # that actually failed; everything else is a note. Both linters emit
    # penalty-only findings that a unit can carry and still pass — filing those
    # under `blocking_violations` is what produced runs reporting PASS
    # alongside a blocking violation count of 4.
    blocking = []
    advisory = []
    for name in expected:
        blocking.extend(outcome["blocking"].get(name, []))
        advisory.extend(outcome["advisory"].get(name, []))
    if issue_level.get("applicable", True):
        issue_violations = list(issue_level.get("violations", []))
        (blocking if issue_level_failed else advisory).extend(issue_violations)
    if truncation_reason:
        # The stop itself is blocking: it is why the run cannot report PASS.
        blocking.insert(0, truncation_reason)

    scorecard = {
        "issue_id": issue_id,
        "theme": theme,
        "ruleset": ruleset,
        "unit_kind": unit_kind,
        "overall": overall,
        "run": {
            "fail_fast": fail_fast,
            "complete": incomplete_reason is None,
            "truncated": truncated,
            "truncated_at": truncated_at,
            "truncation_reason": truncation_reason,
            "incomplete_reason": incomplete_reason,
            # A property of the ruleset and the locks file — never of the
            # submission being graded. See outcome["required"].
            "units_expected": len(required),
            "units_evaluated": len(evaluated),
            "evaluated": evaluated,
            "not_evaluated": not_evaluated,
        },
        "linters": outcome["linters"],
        unit_kind + "s": units,
        "blocking_violations": blocking[:MAX_BLOCKING_VIOLATIONS],
        "blocking_violations_total": len(blocking),
        "advisory_notes": advisory[:MAX_BLOCKING_VIOLATIONS],
        "advisory_notes_total": len(advisory),
        "warnings": list(outcome["warnings"]),
        "issue_level_checks": issue_level,
        "generated_at": datetime.now().isoformat(),
    }

    _print_console(scorecard, ci)

    if write:
        out_dir = Path(results_dir) if results_dir else HERE / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / scorecard_filename(issue_id)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(scorecard, fh, indent=2)
        if not ci:
            print(f"Scorecard written: {out_path}")

    return scorecard


def build_parser():
    parser = argparse.ArgumentParser(description="TIMBR Eval Harness")
    parser.add_argument("--issue", required=True, help="Path to issue.json")
    parser.add_argument("--ci", action="store_true", help="CI mode: minimal output")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Stop at the first failing section/slot. The scorecard "
                             "records the truncation and can never report PASS.")
    parser.add_argument("--ruleset", default=MAGAZINE,
                        help=f"Product line ruleset: {' | '.join(VALID_RULESETS)} "
                             f"(default: {MAGAZINE}). Unknown names are rejected.")
    parser.add_argument("--locks", default=None,
                        help=f"Path to a CharLint locks JSON. Required for "
                             f"--ruleset {WORKOUT_SERIES}, rejected for --ruleset {MAGAZINE}.")
    parser.add_argument("--out-dir", default=None,
                        help="Directory for the scorecard JSON (default: ./results).")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        scorecard = run_eval(
            args.issue,
            ci=args.ci,
            fail_fast=args.fail_fast,
            ruleset=args.ruleset,
            locks=args.locks,
            results_dir=args.out_dir,
        )
    except (EvalHarnessError, charlint.CharLintError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0 if scorecard["overall"] == STATUS_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
