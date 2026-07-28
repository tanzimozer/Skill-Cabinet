"""
test_orchestrator.py — pytest tests for the TIMBR eval harness orchestrator.

Run with:  python3 -m pytest test_orchestrator.py -q   (from timbr_eval/)

What this suite is defending, in order of how badly a regression would hurt:

  1. The verdict is the CONJUNCTION of the linters the line declares. magazine
     = ProhibLint AND VoiceLint; workout_series = CharLint AND ProhibLint.
     Both linters, both directions, on real copy and on stubs — dropping
     either one from either line has to break a test. A linter that returns no
     verdict at all is an error, never a pass.
  2. A --fail-fast run stops early and MUST say so. Sections it never reached
     are emitted as NOT_EVALUATED with null scores, the run block records what
     tripped the stop and what was skipped, and the exit code is never 0. The
     stop also has to STOP THE WORK: the skipped sections are never handed to
     a linter, and the scorecard's own description of what it skipped is
     checked against what actually did not run.
  3. An empty submission MUST NOT pass, and MUST NOT report itself complete.
  4. Ruleset routing: never a silent fallback, never a silently empty run on a
     mismatched input shape.
  5. The scorecard's names mean what they say: `blocking_violations` holds only
     findings that cost the run its PASS, `advisory_notes` holds the rest, and
     `units_expected` is a property of the ruleset and the locks file rather
     than of the submission being graded.
  6. CharLint's warnings (drift, un-gated slots, unsubmitted owner-governed
     slots, non-NFC candidates) reach both the console and the JSON, and never
     move the exit code.

Every test writes its scorecard to a pytest tmp dir; `_guard_real_results_dir`
below fails the test if anything touches the tracked results/ directory.
"""

import json
import os
import re
import subprocess
import sys
import unicodedata

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import orchestrator
from orchestrator import (
    IssueFormatError,
    LocksArgumentError,
    MAGAZINE,
    RUN_KEYS,
    SCORECARD_KEYS,
    STATUS_FAIL,
    STATUS_NOT_EVALUATED,
    STATUS_PASS,
    UnknownRulesetError,
    WORKOUT_SERIES,
)

# The linters, reached through the orchestrator so the tests resolve exactly the
# modules it resolved (charlint/ is both a package and a module name).
prohiblint = orchestrator.prohiblint
voicelint = orchestrator.voicelint
charlint = orchestrator.charlint

HERE = orchestrator.HERE
SAMPLE_ISSUE = HERE / "sample_issue.json"
REAL_LOCKS = HERE / "charlint" / "locks_seattle_series.json"
RUN_EVAL_SH = HERE / "run_eval.sh"

EM_DASH = "—"
EN_DASH = "–"


# ---------------------------------------------------------------------------
# Guards + helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _guard_real_results_dir():
    """results/*.json is tracked in git; no test may write there."""
    real = HERE / "results"
    snapshot = (
        {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in real.iterdir()}
        if real.exists() else None
    )
    yield
    after = (
        {p.name: (p.stat().st_mtime_ns, p.stat().st_size) for p in real.iterdir()}
        if real.exists() else None
    )
    assert after == snapshot, "a test wrote into the tracked results/ directory"


@pytest.fixture
def out_dir(tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    return d


@pytest.fixture
def write_issue(tmp_path):
    """write_issue(obj, name='issue.json') -> path"""
    def _write(obj, name="issue.json"):
        path = tmp_path / name
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return str(path)
    return _write


# -- magazine copy that actually passes both linters ------------------------

#: Filler sentences chosen to carry no ProhibLint or VoiceLint markers at all:
#: no em-dash, no AI-blocklist term, no second-person pattern, no digits with
#: units, no "at <word>"/"in <word>" (VoiceLint scores those case-insensitively,
#: see the notes in the report), no hedging verbs.
_FILLER = (
    "The platform on Yesler stays open from six to nine on weekday mornings.",
    "Chalk bowls sit beside the rack row and get filled twice daily.",
    "The programming board lists the week as plain text and nothing else.",
    "Plates go back on the tree before the next group steps onto the platform.",
    "Bar collars live on a shelf by the door and stay put.",
    "The rack row runs along the north wall toward the chalk stand.",
    "Sign-in happens on paper by the front desk, ordered by arrival.",
    "The lifting floor stays quiet between sets, which regulars treat as the house rule.",
)

#: VoiceLint's fitt register wants short paragraphs; the other two do not.
_FITT_SECTIONS = {"Supplements", "Recovery", "Nightlife"}


def _pad_to_word_range(text, target_words, short_paragraphs):
    out, words, i = [text], len(text.split()), 0
    while words < target_words:
        n = 2 if short_paragraphs else 6
        para = " ".join(_FILLER[(i + k) % len(_FILLER)] for k in range(n))
        i += n
        out.append(para)
        words += len(para.split())
    return "\n\n".join(out)


def magazine_sections_pass():
    """
    The sample issue, cleaned of its two planted AI-blocklist words and padded
    into every section's word-count range. Built rather than checked in so it
    tracks the linters' own constants instead of a stale copy of them.
    """
    sections = dict(json.loads(SAMPLE_ISSUE.read_text(encoding="utf-8"))["sections"])
    sections["Supplements"] = sections["Supplements"].replace(
        "Delve into the research if you want the mechanism.",
        "The mechanism is well documented.")
    sections["Recovery"] = sections["Recovery"].replace(
        "The vibrant recovery community at", "The recovery crowd at")
    return {
        name: _pad_to_word_range(
            text,
            sum(prohiblint.WORD_COUNT_RANGES[name]) // 2,
            name in _FITT_SECTIONS,
        )
        for name, text in sections.items()
    }


def magazine_issue_pass():
    return {"issue_id": "VOL.TEST.PASS", "theme": "Clean",
            "sections": magazine_sections_pass()}


# -- workout_series copy that actually passes both linters ------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])(\s+)")


def clean_prose(text):
    """
    Make a locks baseline pass ProhibLint's workout_series ruleset WITHOUT
    changing its length: exclamation points become periods, and any em-dash
    after the first in a sentence becomes an en-dash (PRINCIPLES.txt Sec. 7
    allows one em-dash aside per sentence, never stacked).

    Length-preserving on purpose: the copy still has to land on its char lock
    to the character, which is what makes this a real end-to-end fixture.
    """
    out = []
    for part in _SENTENCE_SPLIT.split(text.replace("!", ".")):
        if EM_DASH in part:
            first, *rest = part.split(EM_DASH)
            part = first + EM_DASH + EN_DASH.join(rest)
        out.append(part)
    return "".join(out)


@pytest.fixture(scope="module")
def real_locks():
    return charlint.load_locks(REAL_LOCKS)


@pytest.fixture
def ws_slots_pass(real_locks):
    slots = {}
    for name, spec in real_locks["slots"].items():
        cleaned = clean_prose(spec["baseline"])
        assert len(cleaned) == len(spec["baseline"]), name  # still on the lock
        slots[name] = cleaned
    # The fixture is only meaningful if it still carries em-dashes: they are a
    # hard fail under magazine and legal under workout_series, so their survival
    # is what proves the run used the workout_series ruleset.
    assert any(EM_DASH in text for text in slots.values())
    return slots


@pytest.fixture
def ws_issue_pass(ws_slots_pass):
    return {"issue_id": "SEA.VOL.01", "theme": "Chest & Tricep", "slots": ws_slots_pass}


def synthetic_locks(**overrides):
    """A tiny, self-consistent locks file so tests do not lean on the real one."""
    locks = {
        "ruleset": WORKOUT_SERIES,
        "tolerance": 0,
        "slots": {
            "slot_one": {"type": "DYNAMIC", "principles_lock": 11, "baseline": "Hello world"},
            "slot_two": {"type": "DYNAMIC", "principles_lock": 9, "baseline": "Good copy"},
            "slot_three": {"type": "DYNAMIC", "principles_lock": 9, "baseline": "Fine text"},
        },
    }
    locks.update(overrides)
    return locks


@pytest.fixture
def synthetic_locks_file(tmp_path):
    path = tmp_path / "locks_test.json"
    path.write_text(json.dumps(synthetic_locks()), encoding="utf-8")
    charlint.load_locks(path)  # fixture must be a valid locks file
    return str(path)


def run(issue_path, out_dir, **kwargs):
    kwargs.setdefault("ci", True)
    return orchestrator.run_eval(issue_path, results_dir=str(out_dir), **kwargs)


# ===========================================================================
# TASK 1 — fail-fast truncation is marked, and is never silently partial
# ===========================================================================

@pytest.fixture
def magazine_issue_second_section_fails():
    """Training passes; Nutrition carries an em-dash (a magazine hard fail)."""
    issue = magazine_issue_pass()
    issue["issue_id"] = "VOL.TEST.FF"
    issue["sections"]["Nutrition"] += f"\n\nThe counter opens early {EM_DASH} and closes late."
    return issue


def test_fail_fast_records_truncation(write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    r = sc["run"]
    assert r["truncated"] is True
    assert r["truncated_at"] == "Nutrition"          # not the first section
    assert r["complete"] is False
    assert r["incomplete_reason"] == "fail_fast_truncation"
    assert r["fail_fast"] is True
    assert r["evaluated"] == ["Training", "Nutrition"]
    assert r["not_evaluated"] == ["Supplements", "Recovery", "Culture", "Social", "Nightlife"]
    assert r["units_evaluated"] == 2
    assert r["units_expected"] == 7
    assert "Nutrition" in r["truncation_reason"]
    assert "PARTIAL" in r["truncation_reason"]


def test_fail_fast_unreached_sections_are_present_and_marked(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    # Every expected section is still a key: a reader diffing two scorecards
    # sees NOT_EVALUATED rather than an absent section.
    assert list(sc["sections"]) == list(prohiblint.SECTIONS)
    for name in sc["run"]["not_evaluated"]:
        unit = sc["sections"][name]
        assert unit["status"] == STATUS_NOT_EVALUATED
        # Null, never 0 and never 100: unreadable as either a pass or a fail.
        assert unit["voice_score"] is None
        assert unit["prohib_score"] is None
        assert unit["voice_passed"] is None
        assert unit["prohib_passed"] is None
        assert unit["violations"] == []


def test_fail_fast_truncated_run_never_exits_zero(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    assert sc["overall"] == STATUS_FAIL
    code = orchestrator.main(["--issue", path, "--ci", "--fail-fast", "--out-dir", str(out_dir)])
    assert code == 1


def test_fail_fast_truncation_is_in_the_written_json(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    on_disk = json.loads(
        (out_dir / orchestrator.scorecard_filename(sc["issue_id"])).read_text(encoding="utf-8"))
    assert on_disk["run"]["truncated"] is True
    assert on_disk["run"]["truncated_at"] == "Nutrition"
    assert on_disk["run"]["not_evaluated"]
    assert on_disk["overall"] == STATUS_FAIL


def test_fail_fast_truncation_announced_on_console(
        write_issue, out_dir, magazine_issue_second_section_fails, capsys):
    path = write_issue(magazine_issue_second_section_fails)
    run(path, out_dir, ci=False, fail_fast=True)
    console = capsys.readouterr().out
    assert "TRUNCATED" in console
    assert "NOT evaluated" in console
    assert "Supplements" in console
    assert STATUS_NOT_EVALUATED in console


def test_fail_fast_truncation_announced_in_ci_output(
        write_issue, out_dir, magazine_issue_second_section_fails, capsys):
    path = write_issue(magazine_issue_second_section_fails)
    run(path, out_dir, ci=True, fail_fast=True)
    console = capsys.readouterr().out
    assert "TRUNCATED" in console
    assert console.strip().splitlines()[-1] == STATUS_FAIL  # last line stays parseable


def test_without_fail_fast_every_section_is_evaluated(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=False)
    assert sc["run"]["truncated"] is False
    assert sc["run"]["truncated_at"] is None
    assert sc["run"]["complete"] is True
    assert sc["run"]["units_evaluated"] == 7
    assert sc["run"]["not_evaluated"] == []
    assert STATUS_NOT_EVALUATED not in {u["status"] for u in sc["sections"].values()}


def test_truncation_alone_forces_a_failure(write_issue, out_dir, monkeypatch):
    """
    Defence in depth for the fail-fast contract. On the normal path a truncation
    always follows a failing unit, so `any_failed` would carry the FAIL by
    itself and this rule would never be exercised. Pin it directly: if the
    evaluator reports that the run stopped early, the scorecard FAILS even when
    every unit it did reach passed.
    """
    real = orchestrator._evaluate_magazine

    def stop_after_first(sections, fail_fast, source="<issue>"):
        outcome = real(sections, fail_fast=False, source=source)
        first = outcome["expected"][0]
        outcome["units"] = {first: outcome["units"][first]}
        outcome["truncated_at"] = first
        return outcome

    monkeypatch.setattr(orchestrator, "_evaluate_magazine", stop_after_first)
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir, fail_fast=True)
    assert sc["run"]["truncated"] is True
    assert STATUS_FAIL not in {u["status"] for u in sc["sections"].values()}
    assert sc["overall"] == STATUS_FAIL
    assert orchestrator.main(
        ["--issue", path, "--ci", "--fail-fast", "--out-dir", str(out_dir)]) == 1


def test_fail_fast_truncates_workout_series_too(write_issue, out_dir, ws_issue_pass):
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["city_intro"] += "x"          # one char over its lock
    path = write_issue(issue)
    sc = run(path, out_dir, fail_fast=True, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["run"]["truncated"] is True
    assert sc["run"]["truncated_at"] == "city_intro"
    assert sc["run"]["not_evaluated"] == [
        "anchor_venue", "anchor_cafe", "counter_venue", "counter_cafe", "night_page"]
    assert sc["slots"]["night_page"]["status"] == STATUS_NOT_EVALUATED
    assert sc["slots"]["night_page"]["char_expected"] is None
    assert sc["overall"] == STATUS_FAIL


# ===========================================================================
# TASK 3 — the exit contract is honest
# ===========================================================================

def test_magazine_pass_exits_zero(write_issue, out_dir):
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_PASS
    assert orchestrator.main(["--issue", path, "--ci", "--out-dir", str(out_dir)]) == 0


def test_magazine_fail_exits_one(out_dir):
    sc = run(str(SAMPLE_ISSUE), out_dir)
    assert sc["overall"] == STATUS_FAIL
    assert orchestrator.main(
        ["--issue", str(SAMPLE_ISSUE), "--ci", "--out-dir", str(out_dir)]) == 1


def test_workout_series_pass_exits_zero(write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["overall"] == STATUS_PASS
    assert orchestrator.main(["--issue", path, "--ci", "--ruleset", WORKOUT_SERIES,
                              "--locks", str(REAL_LOCKS), "--out-dir", str(out_dir)]) == 0


def test_workout_series_fail_exits_one(write_issue, out_dir, ws_issue_pass):
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["cover_body"] = issue["slots"]["cover_body"][:-5]   # underfill
    path = write_issue(issue)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["overall"] == STATUS_FAIL
    assert sc["slots"]["cover_body"]["failure_mode"] == "underfill"
    assert orchestrator.main(["--issue", path, "--ci", "--ruleset", WORKOUT_SERIES,
                              "--locks", str(REAL_LOCKS), "--out-dir", str(out_dir)]) == 1


def test_empty_magazine_issue_does_not_pass(write_issue, out_dir):
    path = write_issue({"issue_id": "EMPTY", "sections": {}})
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_FAIL
    assert all(u["status"] == STATUS_FAIL for u in sc["sections"].values())
    assert all(u["present"] is False for u in sc["sections"].values())
    assert orchestrator.main(["--issue", path, "--ci", "--out-dir", str(out_dir)]) == 1


def test_empty_workout_series_issue_does_not_pass(write_issue, out_dir, synthetic_locks_file):
    path = write_issue({"issue_id": "EMPTY.WS", "slots": {}})
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=synthetic_locks_file)
    assert sc["overall"] == STATUS_FAIL
    assert {u["failure_mode"] for u in sc["slots"].values()} == {"not_filled"}


def test_zero_units_evaluated_does_not_pass(write_issue, tmp_path, out_dir):
    """
    A locks file whose only slot is owner-governed (MANUAL) and unsupplied:
    CharLint correctly returns no slot results, so nothing at all was gated.
    That must be a FAIL with a stated reason, never a PASS by vacuous truth.
    """
    locks = tmp_path / "locks_manual_only.json"
    locks.write_text(json.dumps({
        "ruleset": WORKOUT_SERIES, "tolerance": 0,
        "slots": {"owner_swap": {"type": "MANUAL", "principles_lock": 11,
                                 "baseline": "Hello world"}},
    }), encoding="utf-8")
    path = write_issue({"issue_id": "NOTHING", "slots": {}})
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(locks))
    assert sc["run"]["units_evaluated"] == 0
    assert sc["run"]["complete"] is False
    assert sc["run"]["incomplete_reason"] == "no_units_evaluated"
    assert sc["overall"] == STATUS_FAIL
    assert orchestrator.main(["--issue", path, "--ci", "--ruleset", WORKOUT_SERIES,
                              "--locks", str(locks), "--out-dir", str(out_dir)]) == 1


def test_missing_section_fails_rather_than_being_skipped(write_issue, out_dir):
    issue = magazine_issue_pass()
    del issue["sections"]["Nightlife"]
    path = write_issue(issue)
    sc = run(path, out_dir)
    unit = sc["sections"]["Nightlife"]
    assert unit["status"] == STATUS_FAIL
    assert unit["present"] is False
    assert "MISSING SECTION" in unit["violations"][0]
    assert sc["overall"] == STATUS_FAIL


def test_issue_level_failure_fails_the_whole_run(write_issue, out_dir):
    """
    ProhibLint's mandatory-element block used to be written to the scorecard and
    then ignored when computing `overall`: an issue could ship with no workout
    at all and still exit 0.
    """
    issue = magazine_issue_pass()
    issue["sections"]["Training"] = re.sub(
        r"\b\d+\s*[xX]\s*\d+\b", "as prescribed", issue["sections"]["Training"])
    path = write_issue(issue)
    sc = run(path, out_dir)
    assert sc["issue_level_checks"]["element_results"]["workout_plan_rep_set"] is False
    assert sc["issue_level_checks"]["passed"] is False
    # Every section still passes on its own — only the issue-level check failed.
    assert all(u["status"] == STATUS_PASS for u in sc["sections"].values())
    assert sc["overall"] == STATUS_FAIL


# ===========================================================================
# TASK 2 — ruleset routing, --locks, and input shapes
# ===========================================================================

def test_unknown_ruleset_raises(write_issue, out_dir):
    path = write_issue(magazine_issue_pass())
    with pytest.raises(UnknownRulesetError) as exc:
        run(path, out_dir, ruleset="magazin")
    assert "no silent fallback" in str(exc.value)
    assert WORKOUT_SERIES in str(exc.value)


def test_unknown_ruleset_from_cli_exits_two(write_issue, out_dir, capsys):
    path = write_issue(magazine_issue_pass())
    code = orchestrator.main(["--issue", path, "--ruleset", "seattle", "--out-dir", str(out_dir)])
    assert code == 2
    assert "Unknown ruleset" in capsys.readouterr().err


def test_locks_required_for_workout_series(write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    with pytest.raises(LocksArgumentError) as exc:
        run(path, out_dir, ruleset=WORKOUT_SERIES)
    assert "--locks is required" in str(exc.value)


def test_locks_rejected_for_magazine(write_issue, out_dir):
    path = write_issue(magazine_issue_pass())
    with pytest.raises(LocksArgumentError) as exc:
        run(path, out_dir, locks=str(REAL_LOCKS))
    assert "meaningless" in str(exc.value)


@pytest.mark.parametrize("argv_extra, needle", [
    (["--ruleset", WORKOUT_SERIES], "--locks is required"),
    ([], None),
])
def test_locks_flag_combinations_from_cli(write_issue, out_dir, capsys, argv_extra, needle):
    path = write_issue(magazine_issue_pass())
    argv = ["--issue", path, "--ci", "--out-dir", str(out_dir)] + argv_extra
    if needle is None:
        argv += ["--locks", str(REAL_LOCKS)]
        needle = "meaningless"
    assert orchestrator.main(argv) == 2
    assert needle in capsys.readouterr().err


def test_magazine_shape_under_workout_series_is_an_error(out_dir):
    with pytest.raises(IssueFormatError) as exc:
        run(str(SAMPLE_ISSUE), out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert "'slots'" in str(exc.value) and "'sections'" in str(exc.value)


def test_workout_series_shape_under_magazine_is_an_error(write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    with pytest.raises(IssueFormatError) as exc:
        run(path, out_dir)
    assert "magazine shape" not in str(exc.value)      # names the ACTUAL shape found
    assert "workout_series shape" in str(exc.value)


def test_missing_container_key_is_an_error(write_issue, out_dir):
    path = write_issue({"issue_id": "NO.KEYS", "body": "text"})
    with pytest.raises(IssueFormatError) as exc:
        run(path, out_dir)
    assert "no 'sections' key" in str(exc.value)


def test_unknown_slot_name_is_an_error(write_issue, out_dir, synthetic_locks_file):
    path = write_issue({"issue_id": "TYPO", "slots": {"slot_wun": "Hello world"}})
    with pytest.raises(IssueFormatError) as exc:
        run(path, out_dir, ruleset=WORKOUT_SERIES, locks=synthetic_locks_file)
    assert "slot_wun" in str(exc.value)
    assert "slot_one" in str(exc.value)                 # lists the known slots


def test_unknown_section_name_is_an_error(write_issue, out_dir):
    issue = magazine_issue_pass()
    issue["sections"]["Trainig"] = issue["sections"].pop("Training")
    path = write_issue(issue)
    with pytest.raises(IssueFormatError) as exc:
        run(path, out_dir)
    assert "Trainig" in str(exc.value)


def test_issue_file_declaring_a_different_ruleset_is_an_error(write_issue, out_dir):
    issue = magazine_issue_pass()
    issue["ruleset"] = WORKOUT_SERIES
    path = write_issue(issue)
    with pytest.raises(IssueFormatError) as exc:
        run(path, out_dir)
    assert "disagrees" in str(exc.value)


def test_non_string_unit_text_is_an_error(write_issue, out_dir):
    issue = magazine_issue_pass()
    issue["sections"]["Social"] = ["a", "list"]
    path = write_issue(issue)
    with pytest.raises(IssueFormatError) as exc:
        run(path, out_dir)
    assert "'Social'" in str(exc.value)


def test_unreadable_issue_file_is_an_error(tmp_path, out_dir):
    with pytest.raises(IssueFormatError):
        run(str(tmp_path / "does_not_exist.json"), out_dir)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(IssueFormatError):
        run(str(bad), out_dir)


def test_missing_locks_file_is_a_usage_error(write_issue, out_dir, ws_issue_pass, tmp_path):
    path = write_issue(ws_issue_pass)
    with pytest.raises(LocksArgumentError):
        run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(tmp_path / "nope.json"))


def test_magazine_runs_end_to_end(write_issue, out_dir):
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert sc["ruleset"] == MAGAZINE
    assert sc["unit_kind"] == "section"
    assert list(sc["sections"]) == list(prohiblint.SECTIONS)
    assert sc["linters"]["prohiblint"] == {"applied": True, "ruleset": MAGAZINE}
    assert sc["linters"]["voicelint"]["applied"] is True
    assert sc["linters"]["charlint"]["applied"] is False
    assert sc["issue_level_checks"]["applicable"] is True
    assert "slots" not in sc


def test_workout_series_runs_end_to_end(write_issue, out_dir, ws_issue_pass, real_locks):
    path = write_issue(ws_issue_pass)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["ruleset"] == WORKOUT_SERIES
    assert sc["unit_kind"] == "slot"
    assert list(sc["slots"]) == charlint.slot_names(real_locks)
    assert "sections" not in sc
    # The probe section name ProhibLint is fed must never leak into the report.
    assert not set(sc["slots"]) & set(prohiblint.SECTIONS)
    assert sc["linters"]["charlint"]["applied"] is True
    assert sc["linters"]["voicelint"]["applied"] is False
    assert "magazine" in sc["linters"]["voicelint"]["reason"]
    assert sc["issue_level_checks"]["applicable"] is False
    assert sc["issue_level_checks"]["passed"] is None
    for name, unit in sc["slots"].items():
        assert unit["char_delta"] == 0
        assert unit["char_expected"] == charlint.target_for(name, real_locks)
        assert unit["status"] == STATUS_PASS
    assert sc["overall"] == STATUS_PASS


def test_workout_series_does_not_run_voicelint(write_issue, out_dir, ws_issue_pass, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("VoiceLint must not run on the workout_series line")
    monkeypatch.setattr(voicelint, "run", boom)
    path = write_issue(ws_issue_pass)
    assert run(path, out_dir, ruleset=WORKOUT_SERIES,
               locks=str(REAL_LOCKS))["overall"] == STATUS_PASS


def test_magazine_does_not_run_charlint(write_issue, out_dir, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("CharLint must not run on the magazine line")
    monkeypatch.setattr(charlint, "run_charlint", boom)
    path = write_issue(magazine_issue_pass())
    assert run(path, out_dir)["overall"] == STATUS_PASS


def test_workout_series_uses_the_workout_series_prohiblint_ruleset(
        write_issue, out_dir, ws_issue_pass):
    """
    An exclamation point is a hard fail only under the workout_series ruleset,
    and em-dashes are a hard fail only under magazine. This fixture keeps its
    exact char count, so char passes and only the prose verdict moves.
    """
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["counter_cafe"] = issue["slots"]["counter_cafe"][:-1] + "!"
    path = write_issue(issue)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    unit = sc["slots"]["counter_cafe"]
    assert unit["char_passed"] is True and unit["char_delta"] == 0
    assert unit["prohib_passed"] is False
    assert unit["status"] == STATUS_FAIL
    assert any("Exclamation point" in v for v in unit["violations"])
    # ... while the untouched em-dash-carrying slots still pass.
    assert sc["slots"]["cover_body"]["status"] == STATUS_PASS


def test_missing_slot_is_reported_not_filled(write_issue, out_dir, ws_issue_pass):
    issue = dict(ws_issue_pass)
    issue["slots"] = {k: v for k, v in issue["slots"].items() if k != "night_page"}
    path = write_issue(issue)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    unit = sc["slots"]["night_page"]
    assert unit["status"] == STATUS_FAIL
    assert unit["present"] is False
    assert unit["failure_mode"] == "not_filled"
    assert unit["prohib_score"] is None          # no prose to lint, not a free pass
    assert sc["overall"] == STATUS_FAIL


def test_char_overflow_is_reported(write_issue, out_dir, synthetic_locks_file):
    path = write_issue({"issue_id": "OVER", "slots": {
        "slot_one": "Hello world!!", "slot_two": "Good copy", "slot_three": "Fine text"}})
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=synthetic_locks_file)
    unit = sc["slots"]["slot_one"]
    assert unit["char_delta"] == 2
    assert unit["failure_mode"] == "overflow"
    assert sc["overall"] == STATUS_FAIL


def test_permanent_slot_mutation_is_caught(write_issue, out_dir, ws_issue_pass):
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"], brand_subline="THE CITY IS THE GYM!")
    path = write_issue(issue)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    unit = sc["slots"]["brand_subline"]
    assert unit["failure_mode"] == "permanent_mutation"
    assert unit["status"] == STATUS_FAIL
    # PERMANENT slots are never rewritten, so they get no prose verdict at all.
    assert unit["prohib_score"] is None


# ===========================================================================
# TASK 4 — CharLint drift warnings surface everywhere and change nothing
# ===========================================================================

def test_drift_warnings_reach_the_scorecard_json(write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    on_disk = json.loads(
        (out_dir / orchestrator.scorecard_filename(sc["issue_id"])).read_text(encoding="utf-8"))
    assert on_disk["warnings"] == sc["warnings"]
    drift = [w for w in on_disk["warnings"] if w.startswith("DRIFT:")]
    assert drift, "the cover_body 351-vs-357 drift must not be dropped"
    assert "cover_body" in drift[0] and "357" in drift[0] and "351" in drift[0]


def test_drift_warnings_reach_the_console_in_both_modes(
        write_issue, out_dir, ws_issue_pass, capsys):
    path = write_issue(ws_issue_pass)
    run(path, out_dir, ci=False, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    normal = capsys.readouterr().out
    assert "WARNINGS" in normal and "DRIFT: cover_body" in normal

    run(path, out_dir, ci=True, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    ci = capsys.readouterr().out
    assert "[warning] DRIFT: cover_body" in ci


def test_warnings_do_not_flip_the_exit_code(write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["warnings"]                       # warnings present ...
    assert sc["overall"] == STATUS_PASS          # ... and the run still passes
    assert orchestrator.main(["--issue", path, "--ci", "--ruleset", WORKOUT_SERIES,
                              "--locks", str(REAL_LOCKS), "--out-dir", str(out_dir)]) == 0


def test_warnings_survive_a_truncated_run(write_issue, out_dir, ws_issue_pass):
    """Drift is a property of the locks file, so it is reported even when the
    run stops at the first slot."""
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["cover_body"] += "x"
    path = write_issue(issue)
    sc = run(path, out_dir, fail_fast=True, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["run"]["truncated"] is True
    assert any(w.startswith("DRIFT:") for w in sc["warnings"])


def test_magazine_scorecard_still_carries_a_warnings_key(write_issue, out_dir):
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert sc["warnings"] == []


# ===========================================================================
# The magazine verdict is ProhibLint AND VoiceLint
#
# The headline contract of the whole harness, and until now nothing pinned it:
# rewriting the verdict as `"PASS" if prohib_pass else "FAIL"` — dropping
# VoiceLint from the magazine gate entirely — left every test green. Both
# linters, both directions, on real copy and on stubs.
# ===========================================================================

#: Voice-only failure. People-register negative markers, which ProhibLint has no
#: opinion about whatsoever: no em-dash, no blocklist term, no second person,
#: and the section stays inside its word-count range.
#:
#: This paragraph must carry enough negative markers to fail on VoiceLint's OWN
#: budget (delta <= -16 against a 15-marker allowance). An earlier, shorter
#: version of it failed for the wrong reason: it tripped a cross-contamination
#: flag on an in-register Nutrition profile, which Quality Gate 2 identified as
#: a false-positive class and VoiceLint has since fixed. A test that passes
#: because of a bug in the code it is testing is worse than no test, so this
#: fixture is deliberately dense rather than merely long -- Nutrition's legal
#: range is 600-900 words, so it cannot be made to fail by padding.
_PEOPLE_NEGATIVE_PARAGRAPH = (
    "Studies show the effect was found in the lab first. The mechanism has been "
    "shown in repeated trials. It is known that the sample sizes were small. "
    "It has been the same story for a decade. The effect was found again in a "
    "later cohort. The result has been shown to hold at the same dose. It is "
    "known that the finding has been shown twice. The effect was found once "
    "more, and it has been reported since."
)


@pytest.fixture
def magazine_issue_voice_only_failure():
    """Nutrition fails VoiceLint and passes ProhibLint outright."""
    issue = magazine_issue_pass()
    issue["issue_id"] = "VOL.TEST.VOICE"
    issue["sections"]["Nutrition"] += "\n\n" + _PEOPLE_NEGATIVE_PARAGRAPH
    return issue


def _stub_voice_run(passed, score=100, flags=()):
    def _run(sections):
        return {name: {"voice_required": "athletic", "voice_score": score,
                       "contamination_flags": list(flags), "passed": passed}
                for name in sections}
    return _run


def _stub_prohib_run(passed, score=100, violations=()):
    real = prohiblint.run_prohiblint

    def _run(sections_dict, ruleset=MAGAZINE):
        raw = real(sections_dict, ruleset=ruleset)
        for name in sections_dict:
            raw["sections"][name] = {"violations": list(violations),
                                     "score": score, "passed": passed}
        return raw
    return _run


def test_a_section_that_fails_only_voicelint_fails_the_run(
        write_issue, out_dir, magazine_issue_voice_only_failure):
    path = write_issue(magazine_issue_voice_only_failure)
    sc = run(path, out_dir)
    unit = sc["sections"]["Nutrition"]
    assert unit["prohib_passed"] is True         # ProhibLint is perfectly happy
    assert unit["prohib_score"] == 100
    assert unit["voice_passed"] is False         # ... and VoiceLint is not
    assert unit["status"] == STATUS_FAIL
    assert sc["overall"] == STATUS_FAIL
    assert orchestrator.main(["--issue", path, "--ci", "--out-dir", str(out_dir)]) == 1


def test_a_section_that_fails_only_prohiblint_fails_the_run(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir)
    unit = sc["sections"]["Nutrition"]
    assert unit["voice_passed"] is True          # VoiceLint is perfectly happy
    assert unit["prohib_passed"] is False        # ... and ProhibLint is not
    assert unit["status"] == STATUS_FAIL
    assert sc["overall"] == STATUS_FAIL
    assert orchestrator.main(["--issue", path, "--ci", "--out-dir", str(out_dir)]) == 1


@pytest.mark.parametrize("prohib_pass, voice_pass, expected", [
    (True, True, STATUS_PASS),
    (True, False, STATUS_FAIL),
    (False, True, STATUS_FAIL),
    (False, False, STATUS_FAIL),
])
def test_the_magazine_verdict_is_the_conjunction_of_both_linters(
        write_issue, out_dir, monkeypatch, prohib_pass, voice_pass, expected):
    """
    The truth table, stubbed so it holds no matter how either linter's own
    thresholds move. Three of these four rows die if either linter is dropped
    from the conjunction.
    """
    monkeypatch.setattr(prohiblint, "run_prohiblint", _stub_prohib_run(prohib_pass))
    monkeypatch.setattr(voicelint, "run", _stub_voice_run(voice_pass))
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert {u["status"] for u in sc["sections"].values()} == {expected}
    if expected == STATUS_PASS:
        assert sc["overall"] == STATUS_PASS
    else:
        assert sc["overall"] == STATUS_FAIL


def test_a_linter_that_returns_no_verdict_is_not_a_pass(
        write_issue, out_dir, monkeypatch):
    """
    The failure mode one step beyond dropping a linter from the verdict:
    keeping the call and reading a missing answer as a clean one.
    """
    monkeypatch.setattr(voicelint, "run", lambda sections: {})
    path = write_issue(magazine_issue_pass())
    with pytest.raises(orchestrator.EvalHarnessError) as exc:
        run(path, out_dir)
    assert "VoiceLint" in str(exc.value)
    assert "not a pass" in str(exc.value)


def test_a_linter_verdict_without_a_passed_flag_is_not_a_pass(
        write_issue, out_dir, monkeypatch):
    monkeypatch.setattr(voicelint, "run",
                        lambda sections: {n: {"voice_score": 100} for n in sections})
    path = write_issue(magazine_issue_pass())
    with pytest.raises(orchestrator.EvalHarnessError):
        run(path, out_dir)


def test_the_workout_series_verdict_is_charlint_and_prohiblint(
        write_issue, out_dir, ws_issue_pass):
    """
    The same conjunction on the other product line, in both directions: the
    char lock alone does not pass a slot, and the prose verdict alone does not
    either. (The prose-only failure is covered end to end by
    test_workout_series_uses_the_workout_series_prohiblint_ruleset; this pins
    the char-only direction beside it.)
    """
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["counter_cafe"] += " and one more clause."     # clean prose
    path = write_issue(issue)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    unit = sc["slots"]["counter_cafe"]
    assert unit["prohib_passed"] is True
    assert unit["char_passed"] is False
    assert unit["status"] == STATUS_FAIL
    assert sc["overall"] == STATUS_FAIL


# ===========================================================================
# --fail-fast genuinely stops the work it says it stopped
# ===========================================================================

@pytest.fixture
def linter_spy(monkeypatch):
    """
    Records every section name each linter is actually asked about.

    `issue_level` records one entry PER CALL (the sorted names that call was
    given), not a flat list: run_prohiblint calls check_mandatory_elements
    itself on whatever it was handed, so the only way to see the orchestrator's
    own whole-submission call is by the shape of the argument.
    """
    seen = {"prohib": [], "voice": [], "issue_level": []}
    real_prohib = prohiblint.run_prohiblint
    real_voice = voicelint.run
    real_elements = prohiblint.check_mandatory_elements

    def prohib(sections_dict, ruleset=MAGAZINE):
        seen["prohib"].extend(sections_dict)
        return real_prohib(sections_dict, ruleset=ruleset)

    def voice(sections):
        seen["voice"].extend(sections)
        return real_voice(sections)

    def elements(sections_dict):
        seen["issue_level"].append(sorted(sections_dict))
        return real_elements(sections_dict)

    monkeypatch.setattr(prohiblint, "run_prohiblint", prohib)
    monkeypatch.setattr(voicelint, "run", voice)
    monkeypatch.setattr(prohiblint, "check_mandatory_elements", elements)
    return seen


def _whole_submission_calls(spy):
    """The issue-level calls that were given more than one section."""
    return [call for call in spy["issue_level"] if len(call) > 1]


def test_fail_fast_never_lints_the_sections_it_reports_as_not_evaluated(
        write_issue, out_dir, magazine_issue_second_section_fails, linter_spy):
    """
    "Never evaluated" has to mean the work did not happen, not that its result
    was computed and thrown away. Everything after the stop must be unseen by
    both linters.
    """
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    assert sc["run"]["not_evaluated"] == [
        "Supplements", "Recovery", "Culture", "Social", "Nightlife"]
    for skipped in sc["run"]["not_evaluated"]:
        assert skipped not in linter_spy["prohib"], skipped
        assert skipped not in linter_spy["voice"], skipped
    assert linter_spy["prohib"] == ["Training", "Nutrition"]
    assert linter_spy["voice"] == ["Training", "Nutrition"]


def test_fail_fast_does_not_run_the_issue_level_checks_either(
        write_issue, out_dir, magazine_issue_second_section_fails, linter_spy):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    assert _whole_submission_calls(linter_spy) == []
    checks = sc["issue_level_checks"]
    assert checks["applicable"] is True
    assert checks["passed"] is None              # not run — and not "passed"
    assert checks["element_results"] == {}
    assert "not run" in checks["reason"].lower()


def test_a_complete_run_does_run_the_issue_level_checks(
        write_issue, out_dir, linter_spy):
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert _whole_submission_calls(linter_spy) == [sorted(prohiblint.SECTIONS)]
    assert sc["issue_level_checks"]["passed"] is True


def test_every_section_is_still_linted_without_fail_fast(
        write_issue, out_dir, magazine_issue_second_section_fails, linter_spy):
    path = write_issue(magazine_issue_second_section_fails)
    run(path, out_dir, fail_fast=False)
    assert linter_spy["prohib"] == list(prohiblint.SECTIONS)
    assert linter_spy["voice"] == list(prohiblint.SECTIONS)


def test_truncation_reason_describes_what_the_stop_actually_stopped(
        write_issue, out_dir, magazine_issue_second_section_fails, ws_issue_pass):
    """
    The two product lines stop different amounts of work, and the block that
    describes the stop has to describe its own line accurately.
    """
    path = write_issue(magazine_issue_second_section_fails)
    magazine = run(path, out_dir, fail_fast=True)["run"]["truncation_reason"]
    assert "No linter was run on their text" in magazine
    assert "issue-level" in magazine

    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["cover_body"] += "x"
    ws_path = write_issue(issue, name="ws.json")
    ws = run(ws_path, out_dir, fail_fast=True,
             ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))["run"]["truncation_reason"]
    # CharLint gates in one pass, so this line claims less — and says so.
    assert "character counts were computed" in ws
    assert "no verdict was reached" in ws
    assert "No linter was run on their text" not in ws


def test_fail_fast_still_lints_nothing_extra_on_the_workout_series_line(
        write_issue, out_dir, ws_issue_pass, monkeypatch):
    """CharLint measures every slot in one pass, but the PROSE linting of the
    slots past the stop must not happen."""
    seen = []
    real = orchestrator._prose_result
    monkeypatch.setattr(orchestrator, "_prose_result",
                        lambda text: (seen.append(text), real(text))[1])
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    issue["slots"]["cover_body"] += "x"
    path = write_issue(issue)
    sc = run(path, out_dir, fail_fast=True, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["run"]["truncated_at"] == "cover_body"
    assert len(seen) == 1                      # only the slot that tripped it
    for skipped in sc["run"]["not_evaluated"]:
        assert issue["slots"][skipped] not in seen


# ===========================================================================
# blocking_violations holds only what actually blocked
# ===========================================================================

def test_a_passing_run_reports_no_blocking_violations(write_issue, out_dir):
    """
    The observed defect: a run with overall PASS and a blocking violation
    count of 4. Contamination flags and penalty-only findings from sections
    that PASSED are notes, not violations, and the key that holds them says so.
    """
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_PASS
    assert sc["blocking_violations"] == []
    assert sc["blocking_violations_total"] == 0
    # ... and the findings are still reported, just under an honest name.
    assert sc["advisory_notes_total"] == sum(
        len(u["violations"]) for u in sc["sections"].values())
    assert sc["advisory_notes_total"] > 0


def test_findings_from_a_passing_section_of_a_failing_run_stay_advisory(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_FAIL
    for name, unit in sc["sections"].items():
        if unit["status"] == STATUS_PASS:
            for finding in unit["violations"]:
                assert finding not in sc["blocking_violations"]
                assert finding in sc["advisory_notes"]


def test_a_failing_sections_own_violation_is_blocking(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir)
    em_dash_violations = [v for v in sc["sections"]["Nutrition"]["violations"]
                          if "dash" in v.lower()]
    assert em_dash_violations
    for v in em_dash_violations:
        assert v in sc["blocking_violations"]


def test_a_passing_slot_run_reports_no_blocking_violations(
        write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["overall"] == STATUS_PASS
    assert sc["blocking_violations_total"] == 0


def test_advisory_notes_are_capped_and_counted_like_violations(out_dir):
    sc = run(str(SAMPLE_ISSUE), out_dir)
    assert len(sc["advisory_notes"]) <= orchestrator.MAX_BLOCKING_VIOLATIONS
    assert sc["advisory_notes_total"] >= len(sc["advisory_notes"])


def test_the_console_calls_notes_notes_and_violations_violations(
        write_issue, out_dir, capsys):
    path = write_issue(magazine_issue_pass())
    run(path, out_dir, ci=False)
    console = capsys.readouterr().out
    assert "Advisory notes:" in console
    assert "non-blocking" in console
    assert "TOP VIOLATIONS" not in console        # nothing blocked anything


# ===========================================================================
# blocking_violations: what is in it, and how many
# ===========================================================================

def test_the_blocking_cap_is_ten(write_issue, out_dir):
    """
    Pins MAX_BLOCKING_VIOLATIONS at its value, not merely at "some cap": an
    empty magazine issue produces 12 blocking findings (the empty-submission
    reason, 7 missing sections, 4 issue-level checks) and must list 10.
    """
    path = write_issue({"issue_id": "CAP", "sections": {}})
    sc = run(path, out_dir)
    assert orchestrator.MAX_BLOCKING_VIOLATIONS == 10
    assert sc["blocking_violations_total"] == 12
    assert len(sc["blocking_violations"]) == 10


def test_the_truncation_reason_is_the_first_blocking_violation(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    assert sc["blocking_violations"][0] == sc["run"]["truncation_reason"]
    assert "PARTIAL" in sc["blocking_violations"][0]


def test_issue_level_violations_are_blocking_violations(write_issue, out_dir):
    """
    All seven sections pass; only the issue-level mandatory-element block
    fails. Its violations are the only evidence for the FAIL, so dropping them
    from `blocking_violations` would leave a FAIL with nothing behind it.
    """
    issue = magazine_issue_pass()
    issue["sections"]["Training"] = re.sub(
        r"\b\d+\s*[xX]\s*\d+\b", "as prescribed", issue["sections"]["Training"])
    path = write_issue(issue)
    sc = run(path, out_dir)
    assert all(u["status"] == STATUS_PASS for u in sc["sections"].values())
    assert sc["overall"] == STATUS_FAIL
    issue_level_violations = sc["issue_level_checks"]["violations"]
    assert issue_level_violations
    for v in issue_level_violations:
        assert v in sc["blocking_violations"]


def test_an_issue_level_block_that_returns_no_answer_is_not_a_pass(
        write_issue, out_dir, monkeypatch):
    """
    The sibling of "a linter that returns no verdict is not a pass", one level
    up. A mandatory-element block that RAN and answered null has not passed;
    only an explicit true does. `evaluated: false` is what marks the one case
    where a null is legitimate — the check the fail-fast stop skipped.
    """
    monkeypatch.setattr(prohiblint, "check_mandatory_elements",
                        lambda sections: {"passed": None, "violations": [],
                                          "penalty": 0, "element_results": {}})
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert all(u["status"] == STATUS_PASS for u in sc["sections"].values())
    assert sc["issue_level_checks"]["evaluated"] is True
    assert sc["overall"] == STATUS_FAIL


def test_a_skipped_issue_level_block_is_marked_not_evaluated(
        write_issue, out_dir, magazine_issue_second_section_fails):
    path = write_issue(magazine_issue_second_section_fails)
    sc = run(path, out_dir, fail_fast=True)
    assert sc["issue_level_checks"]["applicable"] is True
    assert sc["issue_level_checks"]["evaluated"] is False
    assert sc["issue_level_checks"]["passed"] is None


def test_issue_level_violations_stay_advisory_when_the_block_passed(
        write_issue, out_dir, monkeypatch):
    real = prohiblint.check_mandatory_elements

    def passing_with_a_note(sections_dict):
        return dict(real(sections_dict), passed=True,
                    violations=["a mandatory-element note that did not fail"])

    monkeypatch.setattr(prohiblint, "check_mandatory_elements", passing_with_a_note)
    path = write_issue(magazine_issue_pass())
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_PASS
    assert sc["blocking_violations"] == []
    assert "a mandatory-element note that did not fail" in sc["advisory_notes"]


# ===========================================================================
# run.complete tells the truth
# ===========================================================================

def test_an_empty_magazine_submission_is_not_a_complete_run(write_issue, out_dir):
    """
    The verdict was always right; the completeness flag was not. A run that
    read no copy at all has not completed an evaluation of anything.
    """
    path = write_issue({"issue_id": "EMPTY.MAG", "sections": {}})
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_FAIL
    assert sc["run"]["complete"] is False
    assert sc["run"]["incomplete_reason"] == "empty_submission"
    assert "no sections at all" in sc["run"]["truncation_reason"]
    assert sc["run"]["truncated"] is False       # nothing was truncated either


def test_an_empty_workout_series_submission_is_not_a_complete_run(
        write_issue, out_dir, synthetic_locks_file):
    path = write_issue({"issue_id": "EMPTY.WS2", "slots": {}})
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=synthetic_locks_file)
    assert sc["overall"] == STATUS_FAIL
    assert sc["run"]["complete"] is False
    assert sc["run"]["incomplete_reason"] == "empty_submission"


def test_an_empty_submission_alone_forces_a_failure(write_issue, out_dir, monkeypatch):
    """
    Defence in depth, in the shape of test_truncation_alone_forces_a_failure.
    On the normal path an empty submission always produces failing units, so
    `any_failed` carries the FAIL by itself and this rule is never exercised.
    Pinned directly: nothing submitted cannot report PASS even if every unit
    the evaluator returned claims to have passed.
    """
    real = orchestrator._evaluate_magazine

    def all_clean(sections, fail_fast, source="<issue>"):
        outcome = real(dict.fromkeys(prohiblint.SECTIONS, ""), fail_fast=False, source=source)
        for name, unit in outcome["units"].items():
            unit.update(status=STATUS_PASS, present=True, violations=[])
            outcome["blocking"][name] = []
            outcome["advisory"][name] = []
        outcome["issue_level"] = dict(outcome["issue_level"], passed=True, violations=[])
        return outcome

    monkeypatch.setattr(orchestrator, "_evaluate_magazine", all_clean)
    path = write_issue({"issue_id": "NOTHING.SENT", "sections": {}})
    sc = run(path, out_dir)
    assert STATUS_FAIL not in {u["status"] for u in sc["sections"].values()}
    assert sc["run"]["complete"] is False
    assert sc["overall"] == STATUS_FAIL
    assert orchestrator.main(["--issue", path, "--ci", "--out-dir", str(out_dir)]) == 1


def test_a_partly_filled_submission_is_still_a_complete_run(write_issue, out_dir):
    # The opposite over-correction: a run that read six sections and reported
    # the seventh as missing DID evaluate everything it was asked to.
    issue = magazine_issue_pass()
    del issue["sections"]["Nightlife"]
    path = write_issue(issue)
    sc = run(path, out_dir)
    assert sc["overall"] == STATUS_FAIL          # the missing section still fails
    assert sc["run"]["complete"] is True
    assert sc["run"]["incomplete_reason"] is None


def test_the_console_does_not_call_an_empty_submission_complete(
        write_issue, out_dir, capsys):
    path = write_issue({"issue_id": "EMPTY.CONSOLE", "sections": {}})
    run(path, out_dir, ci=False)
    console = capsys.readouterr().out
    assert "NOTHING SUBMITTED" in console
    assert "RUN: complete" not in console


# ===========================================================================
# units_expected is a property of the ruleset, not of the submission
# ===========================================================================

def test_sending_a_permanent_slot_does_not_change_what_was_expected(
        write_issue, out_dir, ws_issue_pass):
    """
    `units_expected` used to be len(the rows this run produced), so a submitter
    who sent an extra permanent slot was retroactively "expected" to send 8.
    """
    without = write_issue(ws_issue_pass, name="without.json")
    with_perm = write_issue(
        dict(ws_issue_pass,
             slots=dict(ws_issue_pass["slots"], brand_subline="THE CITY IS THE GYM.")),
        name="with.json")

    a = run(without, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    b = run(with_perm, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))

    assert a["run"]["units_expected"] == b["run"]["units_expected"] == 7
    assert len(b["slots"]) == 8                 # the extra slot is still reported
    assert b["run"]["units_evaluated"] == 8     # ... and still counted as evaluated
    assert b["slots"]["brand_subline"]["status"] == STATUS_PASS


def test_units_expected_matches_the_locks_file(write_issue, out_dir, ws_issue_pass,
                                               real_locks):
    path = write_issue(ws_issue_pass)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["run"]["units_expected"] == len(charlint.required_slot_names(real_locks))


def test_owner_governed_slots_are_not_expected_of_a_submission(
        write_issue, tmp_path, out_dir):
    locks = tmp_path / "locks_optional.json"
    locks.write_text(json.dumps({
        "ruleset": WORKOUT_SERIES, "tolerance": 0,
        "slots": {
            "body": {"type": "DYNAMIC", "principles_lock": 11, "baseline": "Hello world"},
            "upsell": {"type": "MANUAL", "principles_lock": 9, "baseline": "Good copy"},
        },
    }), encoding="utf-8")
    path = write_issue({"issue_id": "OPT", "slots": {"body": "Hello world"}})
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(locks))
    assert sc["run"]["units_expected"] == 1       # `upsell` is the owner's, not the fill's
    assert sc["overall"] == STATUS_PASS
    # ... and the un-gated slot is still named out loud, by CharLint.
    assert any("NOT SUBMITTED" in w and "upsell" in w for w in sc["warnings"])


@pytest.mark.parametrize("sections", [None, {}])
def test_magazine_units_expected_is_always_seven(write_issue, out_dir, sections):
    issue = magazine_issue_pass() if sections is None else {"issue_id": "E", "sections": {}}
    sc = run(write_issue(issue), out_dir)
    assert sc["run"]["units_expected"] == len(prohiblint.SECTIONS) == 7


# ===========================================================================
# CharLint's submission-level warnings reach the scorecard
# ===========================================================================

def test_a_non_nfc_candidate_passes_and_is_reported_as_a_warning(
        write_issue, out_dir, ws_issue_pass):
    """
    The phantom overflow, end to end: decomposed copy is the same text, so it
    lands on its lock and the run passes — with a warning, never a violation.
    """
    issue = dict(ws_issue_pass)
    issue["slots"] = dict(issue["slots"])
    raw = issue["slots"]["cover_body"]
    issue["slots"]["cover_body"] = unicodedata.normalize("NFD", raw)
    assert len(issue["slots"]["cover_body"]) == len(raw) + 1
    path = write_issue(issue)
    sc = run(path, out_dir, ruleset=WORKOUT_SERIES, locks=str(REAL_LOCKS))
    assert sc["slots"]["cover_body"]["char_delta"] == 0
    assert sc["overall"] == STATUS_PASS
    assert any(w.startswith("CANONICAL FORM:") for w in sc["warnings"])
    assert sc["blocking_violations_total"] == 0


# ===========================================================================
# Declared Python floor
# ===========================================================================

def test_the_python_floor_is_declared_and_this_interpreter_meets_it():
    assert orchestrator.MIN_PYTHON == (3, 8)
    assert sys.version_info >= orchestrator.MIN_PYTHON, (
        "the harness declares a floor it is not being run above")


# ===========================================================================
# Scorecard file contract
# ===========================================================================

@pytest.mark.parametrize("ruleset", [MAGAZINE, WORKOUT_SERIES])
def test_scorecard_round_trips_with_documented_keys(
        write_issue, out_dir, ws_issue_pass, ruleset):
    if ruleset == MAGAZINE:
        path, kwargs = write_issue(magazine_issue_pass()), {}
    else:
        path = write_issue(ws_issue_pass)
        kwargs = {"ruleset": WORKOUT_SERIES, "locks": str(REAL_LOCKS)}

    sc = run(path, out_dir, **kwargs)
    on_disk = json.loads(
        (out_dir / orchestrator.scorecard_filename(sc["issue_id"])).read_text(encoding="utf-8"))

    assert on_disk == sc                       # write -> re-read is lossless
    for key in SCORECARD_KEYS:
        assert key in on_disk, key
    assert (on_disk["unit_kind"] + "s") in on_disk
    for key in RUN_KEYS:
        assert key in on_disk["run"], key
    assert on_disk["blocking_violations_total"] >= len(on_disk["blocking_violations"])
    assert len(on_disk["blocking_violations"]) <= orchestrator.MAX_BLOCKING_VIOLATIONS


def test_every_finding_is_either_blocking_or_advisory_and_none_are_lost(out_dir):
    sc = run(str(SAMPLE_ISSUE), out_dir)
    findings = sum(len(u["violations"]) for u in sc["sections"].values()) + len(
        sc["issue_level_checks"]["violations"])
    assert sc["blocking_violations_total"] + sc["advisory_notes_total"] == findings
    assert sc["blocking_violations_total"] > 0        # this issue really does fail
    assert sc["advisory_notes_total"] > 0             # ... and really does carry notes


def test_scorecard_filename_matches_the_legacy_shape():
    assert orchestrator.scorecard_filename("VOL.04") == "VOL_04_scorecard.json"


def test_scorecard_filename_cannot_escape_the_results_dir(write_issue, out_dir):
    name = orchestrator.scorecard_filename("../../etc/passwd")
    assert "/" not in name and ".." not in name
    path = write_issue({"issue_id": "../../escape", "sections": {}})
    run(path, out_dir)
    assert [p.name for p in out_dir.iterdir()] == [
        orchestrator.scorecard_filename("../../escape")]


def test_write_can_be_disabled(write_issue, out_dir):
    path = write_issue(magazine_issue_pass())
    orchestrator.run_eval(path, ci=True, results_dir=str(out_dir), write=False)
    assert list(out_dir.iterdir()) == []


# ===========================================================================
# run_eval.sh still forwards everything
# ===========================================================================

def _sh(*args):
    return subprocess.run(["bash", str(RUN_EVAL_SH), *args],
                          capture_output=True, text=True)


def test_run_eval_sh_forwards_ci_flag(out_dir):
    proc = _sh(str(SAMPLE_ISSUE), "--ci", "--out-dir", str(out_dir))
    assert proc.returncode == 1
    assert proc.stdout.strip().splitlines()[-1] == STATUS_FAIL


def test_run_eval_sh_forwards_ruleset_and_locks(write_issue, out_dir, ws_issue_pass):
    path = write_issue(ws_issue_pass)
    proc = _sh(path, "--ci", "--ruleset", WORKOUT_SERIES,
               "--locks", str(REAL_LOCKS), "--out-dir", str(out_dir))
    assert proc.returncode == 0
    assert proc.stdout.strip().splitlines()[-1] == STATUS_PASS
    assert "[warning] DRIFT" in proc.stdout


def test_run_eval_sh_without_arguments_is_a_usage_error():
    proc = _sh()
    assert proc.returncode == 2
    assert "usage:" in proc.stderr
