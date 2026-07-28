"""
test_positive_control.py — the magazine line's POSITIVE CONTROL.

Run with:  python3 -m pytest test_positive_control.py -q   (from timbr_eval/)

-------------------------------------------------------------------------------
FIXTURE NOTICE — READ BEFORE TOUCHING fixtures/magazine_pass.json
-------------------------------------------------------------------------------
SYNTHETIC TEST DATA. Every venue, business, gym, person, address, price, quote,
study, statistic and organisation in fixtures/magazine_pass.json is FABRICATED.
None of them exists. Nothing in that file was reported, verified or sourced, and
no part of it describes any real Seattle business or any real person.

It exists for one purpose: to prove that this harness can return PASS on the
magazine ruleset, so that a gate which has only ever returned FAIL is tested in
the direction that matters. It is a positive control fixture, not copy. It must
never be published, republished, quoted, excerpted, or reused as editorial
material in any TIMBR issue or anywhere else.

TIMBR Editorial Handbook Sec. 4 (accuracy is non-negotiable) and Sec. 16 (no
AI-generated named people or addresses without verification) make the
distinction: a clearly labelled fixture is legitimate, the same text inside an
issue is not. `test_fixture_notice_is_present_and_first` below exists so the
label cannot be quietly dropped from the JSON.

Seattle neighbourhood names in the fixture are real public geography, used only
so the linters' location checks have something to read. Every street name,
street number, venue and person attached to them is invented.

-------------------------------------------------------------------------------
WHAT THIS SUITE IS FOR
-------------------------------------------------------------------------------
sample_issue.json is the magazine line's NEGATIVE fixture: it runs 100-200 words
per section against 400-1200 word ranges, so every magazine run in this repo's
history has returned FAIL. A gate that has only ever said no is untested in the
direction that matters — nothing in the suite distinguishes "correctly strict"
from "structurally incapable of passing".

So this file asserts the other half of the contract, on real copy rather than on
stubs: an issue written to the Handbook PASSES end to end. Overall PASS, exit
code 0, both linters green on all seven sections, all four mandatory elements
true, no blocking violations, and no cross-contamination flag anywhere.

The non-triviality tests are load-bearing. A positive control that could be
satisfied by an empty file proves nothing, so the fixture's seven sections and
their word counts are asserted directly, against prohiblint.WORD_COUNT_RANGES
rather than against numbers copied out of it.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import orchestrator
from orchestrator import MAGAZINE, STATUS_PASS

# The linters, reached through the orchestrator so this suite resolves exactly
# the modules it resolved.
prohiblint = orchestrator.prohiblint
voicelint = orchestrator.voicelint

HERE = orchestrator.HERE
FIXTURE = HERE / "fixtures" / "magazine_pass.json"

EM_DASH = "—"

#: The brief's floor for a real issue's worth of copy. The per-section ranges
#: already cap the total, so only the floor needs asserting: a fixture sitting
#: at the minimum of all seven ranges (4,000 words) is thinner than an issue and
#: would make this control weaker than the thing it certifies.
TOTAL_WORDS_FLOOR = 4500

#: prohiblint.run_prohiblint's own pass bar, which it applies inline rather than
#: exposing as a constant. Duplicated here with that stated, so a reader knows
#: this number is a mirror and not a second opinion.
PROHIBLINT_PASS_SCORE = 70


# ---------------------------------------------------------------------------
# Guards + fixtures
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


@pytest.fixture(scope="module")
def issue():
    """The fixture file, parsed. Module-scoped: the tests never mutate it."""
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def sections(issue):
    return issue["sections"]


@pytest.fixture
def scorecard(tmp_path):
    """A full orchestrator run over the fixture, written to a tmp dir."""
    return orchestrator.run_eval(
        str(FIXTURE), ci=True, ruleset=MAGAZINE,
        results_dir=str(tmp_path / "results"),
    )


# ---------------------------------------------------------------------------
# The synthetic-data label
# ---------------------------------------------------------------------------

def test_fixture_notice_is_present_and_first(issue):
    """
    The label is the thing that keeps this file a fixture rather than copy, so
    it is asserted before anything about linting. Position matters as much as
    presence: a reader opening the JSON has to hit it before the prose.
    """
    assert "_fixture_notice" in issue, (
        "fixtures/magazine_pass.json has lost its _fixture_notice. Every venue, "
        "person, address, price and quote in it is fabricated; without the "
        "notice the file reads as journalism about real Seattle businesses."
    )
    assert next(iter(issue)) == "_fixture_notice", (
        "_fixture_notice must be the FIRST key in the fixture, ahead of the copy."
    )
    notice = issue["_fixture_notice"]
    assert isinstance(notice, str) and len(notice.split()) >= 40

    lowered = notice.lower()
    for phrase in ("fabricated", "never be published", "positive control"):
        assert phrase in lowered, (
            f"the fixture notice must say, in plain language, {phrase!r}"
        )


# ---------------------------------------------------------------------------
# Non-triviality: this control cannot be satisfied by an empty file
# ---------------------------------------------------------------------------

def test_fixture_has_all_seven_sections(sections):
    assert list(sections) == list(prohiblint.SECTIONS), (
        "the positive control has to exercise every section the magazine "
        "ruleset requires, in the ruleset's own order"
    )


@pytest.mark.parametrize("section", prohiblint.SECTIONS)
def test_section_word_count_is_inside_its_range(sections, section):
    """
    Read off prohiblint.WORD_COUNT_RANGES, never copied out of it: if the
    ruleset's ranges move, this test moves with them and the fixture is the
    thing that has to be rewritten.
    """
    lo, hi = prohiblint.WORD_COUNT_RANGES[section]
    words = len(sections[section].split())
    assert lo <= words <= hi, (
        f"{section} is {words} words, outside its {lo}-{hi} range. The whole "
        f"point of this fixture is that it clears the range that "
        f"sample_issue.json fails."
    )


def test_fixture_is_a_full_issue_not_a_stub(sections):
    total = sum(len(text.split()) for text in sections.values())
    assert total >= TOTAL_WORDS_FLOOR, (
        f"{total} words total. A positive control that passes on a thin file "
        f"certifies less than the harness is asked to gate."
    )


def test_no_em_dash_anywhere_in_the_fixture(sections):
    """
    The magazine ruleset's headline hard fail, asserted on the text itself as
    well as through ProhibLint: a fixture that has to be em-dash-clean should
    say so where a writer editing it will see it.
    """
    for name, text in sections.items():
        assert EM_DASH not in text, f"{name} contains a U+2014 em-dash"


# ---------------------------------------------------------------------------
# The verdict: PASS, end to end
# ---------------------------------------------------------------------------

def test_overall_is_pass(scorecard):
    assert scorecard["overall"] == STATUS_PASS, (
        f"blocking violations: {scorecard['blocking_violations']}"
    )


def test_run_is_complete_and_untruncated(scorecard):
    run = scorecard["run"]
    assert run["complete"] is True
    assert run["truncated"] is False
    assert run["incomplete_reason"] is None
    assert run["units_evaluated"] == run["units_expected"] == len(prohiblint.SECTIONS)
    assert run["not_evaluated"] == []


def test_cli_exit_code_is_zero(tmp_path):
    """
    The real CLI, not just run_eval: exit code 0 is what a CI job reads, and it
    is produced by main() rather than by the scorecard dict.
    """
    out_dir = tmp_path / "results"
    proc = subprocess.run(
        [sys.executable, str(HERE / "orchestrator.py"),
         "--issue", str(FIXTURE), "--out-dir", str(out_dir)],
        cwd=str(HERE), capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        f"exit {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert "OVERALL: PASS" in proc.stdout
    written = list(out_dir.glob("*_scorecard.json"))
    assert len(written) == 1
    assert json.loads(written[0].read_text(encoding="utf-8"))["overall"] == STATUS_PASS


def test_main_returns_zero(tmp_path):
    assert orchestrator.main(
        ["--issue", str(FIXTURE), "--ci", "--out-dir", str(tmp_path)]
    ) == 0


# ---------------------------------------------------------------------------
# Both linters, every section
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("section", prohiblint.SECTIONS)
def test_section_passes_both_linters(scorecard, section):
    """
    The magazine verdict is ProhibLint AND VoiceLint, so both halves are named
    here. A section that passed on one linter and was carried by the other is
    not what this control is certifying.
    """
    unit = scorecard["sections"][section]
    assert unit["prohib_passed"] is True, unit["violations"]
    assert unit["voice_passed"] is True, unit["violations"]
    assert unit["status"] == STATUS_PASS
    assert unit["prohib_score"] >= PROHIBLINT_PASS_SCORE
    assert unit["voice_score"] >= voicelint.PASS_THRESHOLD


def test_prohiblint_passes_the_whole_issue(sections):
    """Straight at the linter, so a failure names the check rather than the run."""
    result = prohiblint.run_prohiblint(sections, ruleset=MAGAZINE)
    for section, verdict in result["sections"].items():
        assert verdict["passed"] is True, f"{section}: {verdict['violations']}"
    assert result["summary"]["all_passed"] is True


@pytest.mark.parametrize("section", prohiblint.SECTIONS)
def test_section_carries_no_prohiblint_violations_at_all(sections, section):
    """
    Not merely above the -30 penalty bar: clean. A cold-open (-15) or a pair of
    AI-vocabulary hits (-10) leaves a section passing at 85 and 90, so a control
    that only asserted `passed` would go quiet on exactly the defects the
    Handbook cares most about.
    """
    verdict = prohiblint.run_prohiblint(
        {section: sections[section]}, ruleset=MAGAZINE)["sections"][section]
    assert verdict["violations"] == []
    assert verdict["score"] == 100


@pytest.mark.parametrize("section", prohiblint.SECTIONS)
def test_section_is_in_its_required_register(sections, section):
    """
    Contamination costs 18 against a 15-point budget, so any flag fails a
    section. Asserting the flag list is empty says the stronger thing: each
    section reads as its own register, not as one that survived being another.
    """
    verdict = voicelint.run({section: sections[section]})[section]
    assert verdict["voice_required"] == voicelint.SECTION_VOICE_MAP[section]
    assert verdict["contamination_flags"] == []
    assert verdict["passed"] is True
    assert verdict["voice_score"] >= voicelint.PASS_THRESHOLD


# ---------------------------------------------------------------------------
# The four mandatory elements
# ---------------------------------------------------------------------------

def test_all_four_mandatory_elements_are_true(scorecard):
    checks = scorecard["issue_level_checks"]
    assert checks["applicable"] is True
    assert checks["evaluated"] is True
    assert checks["passed"] is True
    assert checks["penalty"] == 0
    assert checks["violations"] == []

    results = checks["element_results"]
    assert results == {
        "workout_plan_rep_set": True,
        "nutrition_spots_4_places": True,
        "local_fitness_spots_2": True,
        "location_features_3_places": True,
    }


def test_nutrition_venues_carry_street_addresses(sections):
    """
    The blocking tier, named: bare neighbourhoods no longer count, so this
    asserts the thing the element actually requires rather than its verdict.
    """
    venues = prohiblint._located_venue_names(
        sections["Nutrition"], require_address=True)
    assert len(venues) >= 4, sorted(venues)


def test_two_named_fitness_spots_are_attached_to_their_type_word(sections):
    full_text = "\n\n".join(sections[s] for s in prohiblint.SECTIONS)
    assert len(prohiblint._named_fitness_spots(full_text)) >= 2


# ---------------------------------------------------------------------------
# Nothing blocking, nothing advisory
# ---------------------------------------------------------------------------

def test_zero_blocking_violations(scorecard):
    assert scorecard["blocking_violations"] == []
    assert scorecard["blocking_violations_total"] == 0


def test_zero_advisory_notes_and_warnings(scorecard):
    """
    A PASS carrying advisory notes is still a PASS, so this is the softer of the
    two claims. It is asserted anyway because an advisory note on this fixture
    means a linter has an opinion about copy written to the Handbook, and that
    is worth surfacing as a failing test rather than as a line in a scorecard
    nobody reads.
    """
    assert scorecard["advisory_notes"] == []
    assert scorecard["advisory_notes_total"] == 0
    assert scorecard["warnings"] == []


def test_every_section_scores_a_clean_hundred(scorecard):
    for section, unit in scorecard["sections"].items():
        assert unit["violations"] == [], section
        assert (unit["prohib_score"], unit["voice_score"]) == (100, 100), section
