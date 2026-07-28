"""
test_prohiblint.py — pytest tests for ProhibLint module.
Run with: pytest test_prohiblint.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import inspect
import json
import re

import pytest
import prohiblint
from prohiblint import (
    check_em_dash,
    check_em_dash_workout_series,
    check_ai_blocklist,
    check_cold_open,
    check_second_person,
    check_word_count,
    check_mandatory_elements,
    check_workout_series_blocklist,
    check_exclamation_points,
    run_prohiblint,
    WORD_COUNT_RANGES,
    SECTIONS,
    VALID_RULESETS,
    _matches_cold_open_pattern,
    _cold_open_rule,
    _has_narrative_present_tense,
    _split_into_sentences,
    _first_paragraph,
    _word_count,
    _TITLE_CASE_STOPLIST,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_text(word_count, filler="The athlete trains hard every day at the local gym."):
    """Generate a text of approximately word_count words."""
    words = filler.split()
    repeats = (word_count // len(words)) + 2
    return " ".join((words * repeats)[:word_count])


def make_section_dict(**overrides):
    """Build a minimal valid sections dict, overriding specific sections."""
    defaults = {}
    for s in SECTIONS:
        lo, hi = WORD_COUNT_RANGES[s]
        target = (lo + hi) // 2
        defaults[s] = make_text(target)
    defaults.update(overrides)
    return defaults


#: Filler carrying no marker any check looks for: no fitness keyword, no place
#: type, no capitalised name, no blocklist term, no second-person pattern, no
#: narrative verb. The default make_text filler mentions a "gym", which is a
#: Check-F fitness keyword — useless when the count itself is under test.
NEUTRAL_FILLER = "The athlete trains hard every day without fail."


def neutral_sections(**overrides):
    """make_section_dict, but with filler that scores zero on every check."""
    defaults = {}
    for s in SECTIONS:
        lo, hi = WORD_COUNT_RANGES[s]
        defaults[s] = make_text((lo + hi) // 2, NEUTRAL_FILLER)
    defaults.update(overrides)
    return defaults


def real_sample_sections():
    """The checked-in sample issue, or skip if the harness fixture is absent."""
    path = os.path.join(os.path.dirname(__file__), os.pardir, "sample_issue.json")
    if not os.path.exists(path):
        pytest.skip("sample_issue.json not available")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["sections"]


# ---------------------------------------------------------------------------
# Check A — Em-dash detector
# ---------------------------------------------------------------------------

class TestEmDash:
    def test_no_em_dash_passes(self):
        v, penalty, hard_fail = check_em_dash("No em dashes here.")
        assert hard_fail is False
        assert penalty == 0
        assert v == []

    def test_single_em_dash_fails(self):
        v, penalty, hard_fail = check_em_dash("This is good\u2014or is it?")
        assert hard_fail is True
        assert penalty == -10
        assert len(v) == 1

    def test_multiple_em_dashes_cumulative_penalty(self):
        v, penalty, hard_fail = check_em_dash("A\u2014B\u2014C\u2014D")
        assert hard_fail is True
        assert penalty == -30  # 3 em-dashes × -10


# ---------------------------------------------------------------------------
# Check B — AI vocabulary blocklist
# ---------------------------------------------------------------------------

class TestAIBlocklist:
    def test_clean_text_passes(self):
        v, penalty, hard_fail = check_ai_blocklist(
            "The runner finished the 5k race in under 20 minutes."
        )
        assert hard_fail is False
        assert penalty == 0

    def test_single_blocked_term_penalty(self):
        v, penalty, hard_fail = check_ai_blocklist(
            "This holistic approach to fitness changed everything."
        )
        assert hard_fail is False
        assert penalty == -5
        assert any("holistic" in viol for viol in v)

    def test_two_blocked_terms_no_hard_fail(self):
        v, penalty, hard_fail = check_ai_blocklist(
            "A vibrant and robust community gathers here."
        )
        assert hard_fail is False
        assert penalty == -10

    def test_three_blocked_terms_hard_fail(self):
        v, penalty, hard_fail = check_ai_blocklist(
            "This vibrant and robust ecosystem will empower you."
        )
        assert hard_fail is True
        assert penalty <= -15  # at least 3 × -5

    def test_case_insensitive_match(self):
        v, penalty, hard_fail = check_ai_blocklist("DELVE into the details.")
        assert penalty == -5

    def test_multi_word_term_deep_dive(self):
        v, penalty, hard_fail = check_ai_blocklist("Let's do a deep dive into recovery.")
        assert penalty == -5

    def test_partial_word_no_match(self):
        """'foster' should not match 'fostering' if boundaries are strict — but
        word-boundary regex WILL match 'fostering' at the start... reconsider.
        The spec says word boundary so 'holistically' should not match 'holistic'."""
        v, penalty, hard_fail = check_ai_blocklist("A holistically designed plan.")
        # 'holistic' has a word boundary before but NOT after (followed by 'ally')
        # \bholistic\b would NOT match 'holistically'
        assert penalty == 0


# ---------------------------------------------------------------------------
# Check C — Fictional cold-open heuristic
# ---------------------------------------------------------------------------

class TestColdOpen:
    def test_short_opening_no_flag(self):
        """Short first paragraph (<= 30 words) should never be flagged."""
        short = "It is 5am. Time to train."
        v, penalty, _ = check_cold_open(short)
        assert penalty == 0

    def test_narrative_no_proper_noun_flagged(self):
        """Long narrative present tense opening without proper noun should flag."""
        narrative = (
            "It is 5:30 in the morning and the alarm goes off. "
            "Someone sits up in bed, checks the time, and reaches for their shoes. "
            "Outside it is still dark and cold as they head out the door."
        )
        v, penalty, _ = check_cold_open(narrative)
        assert penalty == -15

    def test_proper_noun_clears_flag(self):
        """Opening with a clear attributed proper noun should pass."""
        attributed = (
            "Seattle trainer Marcus Webb wakes at 5:30am every Monday to lead "
            "the Capitol Hill Run Club through Volunteer Park. The group has grown "
            "from six regulars to over forty members in the past year alone."
        )
        v, penalty, _ = check_cold_open(attributed)
        assert penalty == 0

    def test_it_is_time_pattern_flagged(self):
        """'It is [time]' pattern triggers flag when >30 words."""
        text = (
            "It is 5:30am and the city is still dark. Someone walks through "
            "the empty streets toward the gym, bag slung over one shoulder, "
            "already thinking about the session ahead. The routine never changes."
        )
        v, penalty, _ = check_cold_open(text)
        assert penalty == -15


# ---------------------------------------------------------------------------
# Check D — Second-person coaching register
# ---------------------------------------------------------------------------

class TestSecondPerson:
    def test_clean_text_passes(self):
        v, penalty, _ = check_second_person(
            "Athletes benefit from progressive overload over time."
        )
        assert penalty == 0

    def test_single_hit_penalty(self):
        v, penalty, _ = check_second_person(
            "You should start with a warm-up before lifting."
        )
        assert penalty == -3

    def test_multiple_hits_accumulate(self):
        v, penalty, _ = check_second_person(
            "You should stretch first. Your body needs recovery. You can try this later."
        )
        assert penalty <= -9

    def test_sidebar_exempt(self):
        text = (
            "The training block focuses on hypertrophy. "
            "[SIDEBAR] You should always consult a coach. Your body will adapt. [/SIDEBAR] "
            "Progressive overload is the key principle."
        )
        v, penalty, _ = check_second_person(text)
        assert penalty == 0

    def test_sidebar_outside_still_flagged(self):
        text = (
            "You should eat well. "
            "[SIDEBAR] Rest is key. [/SIDEBAR] "
            "Your workout matters."
        )
        v, penalty, _ = check_second_person(text)
        assert penalty == -6  # 2 hits outside sidebar


# ---------------------------------------------------------------------------
# Check E — Word count range
# ---------------------------------------------------------------------------

class TestWordCount:
    def test_training_in_range(self):
        text = make_text(1000)
        v, penalty, hard_fail = check_word_count("Training", text)
        assert penalty == 0
        assert hard_fail is False

    def test_training_too_short(self):
        text = make_text(500)
        v, penalty, hard_fail = check_word_count("Training", text)
        assert penalty == -20
        assert hard_fail is True

    def test_nightlife_in_range(self):
        text = make_text(500)
        v, penalty, hard_fail = check_word_count("Nightlife", text)
        assert penalty == 0

    def test_supplements_too_long(self):
        text = make_text(700)
        v, penalty, hard_fail = check_word_count("Supplements", text)
        assert penalty == -20
        assert hard_fail is True


# ---------------------------------------------------------------------------
# Check F — Mandatory value elements (issue-level)
# ---------------------------------------------------------------------------

class TestMandatoryElements:
    def test_rep_set_notation_present(self):
        sections = make_section_dict(Training="Complete 3x8 squats and 4 sets of deadlifts for reps.")
        result = check_mandatory_elements(sections)
        assert result["element_results"]["workout_plan_rep_set"] is True

    def test_rep_set_notation_missing(self):
        sections = make_section_dict(Training="Train hard every day with lots of cardio and effort.")
        result = check_mandatory_elements(sections)
        assert result["element_results"]["workout_plan_rep_set"] is False
        assert any("rep/set" in v for v in result["violations"])

    def test_fitness_spots_present(self):
        sections = make_section_dict(
            Training=(
                "Seattle's Rainier Crossfit gym is a local favourite. "
                "The Capitol Hill Yoga Studio offers morning classes. "
                "Fremont Running Club meets at 6am on Saturdays."
            )
        )
        result = check_mandatory_elements(sections)
        assert result["element_results"]["local_fitness_spots_2"] is True

    def test_all_elements_missing_max_penalty(self):
        sections = {s: "Nothing useful here at all." for s in SECTIONS}
        result = check_mandatory_elements(sections)
        assert result["penalty"] <= -75  # 3+ missing at -25 each


# ---------------------------------------------------------------------------
# Composite / integration tests
# ---------------------------------------------------------------------------

class TestComposite:
    def test_clean_issue_passes(self):
        """A carefully constructed clean issue should score well and pass."""
        training = (
            "Seattle trainer Marcus Webb leads the Capitol Hill Run Club every Saturday. "
            "The program focuses on progressive overload. Athletes complete 3x8 back squats, "
            "4 sets of Romanian deadlifts, and 3 sets of 10 push-ups each session. "
            "Rainier Crossfit gym also offers supplementary strength sessions. "
        ) + make_text(950, "The athlete trains hard at the local gym every single week.")

        nutrition = (
            "Capitol Hill has several excellent options. Cafe Vida, located at "
            "Broadway and Pike, serves high-protein breakfasts. Fremont's "
            "Nourish Kitchen at 123 N 36th St offers balanced meal prep. "
            "Ballard's The Grain Bar is a favourite for carb loading. "
            "Pioneer Square's Iron Fork restaurant rounds out the list. "
        ) + make_text(700, "Nutrition is critical for athletic performance and recovery.")

        supplements = make_text(500, "Protein powder supports muscle recovery and growth.")
        recovery = make_text(650, "Sleep and rest days are critical for adaptation.")
        culture = make_text(1000, "Seattle fitness culture values outdoor activities greatly.")
        social = make_text(600, "The running community is growing rapidly across Seattle.")
        nightlife = (
            "After training, Seattle offers great spots. The Westlake Rooftop Bar "
            "is popular. Green Lake Park is perfect for evening walks. "
            "Belltown's Copper Tavern and the Capitol Hill Bistro round things out. "
        ) + make_text(400, "Nightlife in Seattle is vibrant for fitness enthusiasts.")

        sections = {
            "Training": training,
            "Nutrition": nutrition,
            "Supplements": supplements,
            "Recovery": recovery,
            "Culture": culture,
            "Social": social,
            "Nightlife": nightlife,
        }
        result = run_prohiblint(sections)
        # Should have a reasonable total score and no catastrophic failures
        assert result["summary"]["total_score"] > 0

    def test_em_dash_causes_section_fail(self):
        sections = make_section_dict(
            Training=make_text(1000, "The athlete trains hard\u2014every single day.")
        )
        result = run_prohiblint(sections)
        assert result["sections"]["Training"]["passed"] is False

    def test_result_structure(self):
        sections = make_section_dict()
        result = run_prohiblint(sections)
        assert "sections" in result
        assert "issue_level" in result
        assert "summary" in result
        for s in SECTIONS:
            assert s in result["sections"]
            assert "violations" in result["sections"][s]
            assert "score" in result["sections"][s]
            assert "passed" in result["sections"][s]


# ---------------------------------------------------------------------------
# Defect 1 — Fictional cold-open pattern tightening (case-sensitivity)
# ---------------------------------------------------------------------------
#
# _matches_cold_open_pattern used to compile all three patterns with
# re.IGNORECASE, which folds [A-Z] into also matching lowercase — defeating
# the capitalisation signal the patterns are built on. Pattern 3 additionally
# matched ANY lowercase word ending in "s" as the "verb" (plurals,
# possessives, ordinary third-person verbs like "matters" or "builds"), so
# it fired on totally ordinary editorial sentences. These tests hit the
# private matcher directly (white-box) to isolate the regex from the rest
# of check_cold_open's heuristics, then confirm the same result through the
# public API.

class TestColdOpenPatternTightening:
    def test_real_cold_open_name_verb_pattern_flags(self):
        """A genuine '[Name] verbs ...' cold-open should still match."""
        assert _matches_cold_open_pattern("Marcus checks his watch before the sun comes up.") is True

    def test_real_cold_open_time_pattern_flags(self):
        assert _matches_cold_open_pattern("It is 5:30am and the gym is still dark.") is True

    def test_real_cold_open_name_already_pattern_flags(self):
        assert _matches_cold_open_pattern("Marcus is already lacing his shoes.") is True

    def test_ordinary_prose_recovery_matters_not_flagged(self):
        """The old pattern 3 ('[A-Z][a-z]+ [a-z]+s ') matched this: 'Recovery'
        (capitalised) + 'matters' (lowercase, ends in s). The tightened
        pattern requires an actual narrative-movement verb, so this no
        longer fires."""
        assert _matches_cold_open_pattern("Recovery matters more than people often realize.") is False

    def test_ordinary_prose_training_builds_not_flagged(self):
        assert _matches_cold_open_pattern("Training builds strength over many months of effort.") is False

    def test_ordinary_prose_sleep_improves_not_flagged(self):
        assert _matches_cold_open_pattern("Sleep improves performance according to every major study.") is False

    def test_lowercase_sentence_start_no_longer_matches(self):
        """Removing IGNORECASE means a lowercase 'it is' at the very start
        (not real sentence casing) no longer matches pattern 1 either."""
        assert _matches_cold_open_pattern("it is 5:30am and the gym is still dark.") is False

    def test_public_api_ordinary_prose_not_flagged(self):
        """Same proof through the public check_cold_open entry point: a
        long, ordinary editorial paragraph with no true narrative-movement
        verb and no cold-open pattern should score 0, not -15."""
        ordinary = (
            "Recovery matters more than people often realize during heavy training blocks. "
            "Nutrition builds the foundation for every gain athletes eventually see over time. "
            "Consistency wins in the end, not any single dramatic session or supplement stack."
        )
        v, penalty, _ = check_cold_open(ordinary)
        assert penalty == 0

    def test_public_api_real_cold_open_still_flagged(self):
        """And a genuine fictional cold-open (unattributed, narrative,
        pattern-matching, >30 words) should still score -15 through the
        public API."""
        cold_open = (
            "Marcus checks his phone one more time before every set. He ties his shoes, "
            "grabs his bag, and heads out the door before the sun is even up over the "
            "block where he trains."
        )
        v, penalty, _ = check_cold_open(cold_open)
        assert penalty == -15


# ---------------------------------------------------------------------------
# Defect 2 — "Seattle" removed from the title-case stoplist
# ---------------------------------------------------------------------------

class TestSeattleNotStoplisted:
    def test_seattle_not_in_stoplist(self):
        assert "Seattle" not in _TITLE_CASE_STOPLIST

    def test_seattle_mention_no_longer_false_flagged_as_cold_open(self):
        """
        Before the fix, "Seattle" was in the stoplist, so _has_proper_noun
        discounted every Seattle mention. In a paragraph where Seattle is
        the ONLY capitalised non-sentence-initial word, that made
        has_proper_noun return False, and combined with ordinary
        narrative-adjacent verbs (walks/checks/reaches) this ordinary,
        real-place editorial paragraph was wrongly flagged as a fictional
        cold-open. It must not be flagged now that Seattle counts.
        """
        text = (
            "Morning training in Seattle starts the same way for everyone who shows up. "
            "The regular crew walks through the door, checks the clock, and reaches for the rack "
            "before the sun even clears the buildings outside on any average weekday."
        )
        v, penalty, _ = check_cold_open(text)
        assert penalty == 0


# ---------------------------------------------------------------------------
# Defect 3 — "journey" is context-sensitive (wellness only)
# ---------------------------------------------------------------------------
#
# TIMBR Editorial Handbook Section 6 qualifies "journey" as blocklisted only
# "in wellness context" — unlike every other AI_BLOCKLIST term, which is
# unconditional. "the journey home" / "a train journey" must not fire;
# "your fitness journey" / "this transformation journey" must.

class TestJourneyContextSensitivity:
    def test_fitness_journey_flags(self):
        v, penalty, _ = check_ai_blocklist(
            "Our fitness journey together starts with a single warm-up rep."
        )
        assert penalty == -5
        assert any("journey" in item for item in v)

    def test_transformation_journey_flags(self):
        v, penalty, _ = check_ai_blocklist(
            "This transformation journey begins with the first honest rep."
        )
        assert penalty == -5

    def test_journey_toward_health_flags(self):
        v, penalty, _ = check_ai_blocklist(
            "Every session is part of your journey toward better health overall."
        )
        assert penalty == -5

    def test_journey_home_does_not_flag(self):
        v, penalty, _ = check_ai_blocklist(
            "The journey home after leg day is always the hardest part of the night."
        )
        assert penalty == 0
        assert v == []

    def test_train_journey_does_not_flag(self):
        v, penalty, _ = check_ai_blocklist(
            "A train journey through the Cascades makes for a nice rest day off."
        )
        assert penalty == 0
        assert v == []

    def test_other_blocklist_terms_still_unconditional(self):
        """Sanity check: the fix is scoped to "journey" only — every other
        term is still an unconditional flat match."""
        v, penalty, _ = check_ai_blocklist("This holistic plan changed everything.")
        assert penalty == -5


# ---------------------------------------------------------------------------
# Defect 4 — ruleset switch (magazine vs workout_series)
# ---------------------------------------------------------------------------

class TestEmDashWorkoutSeries:
    def test_no_em_dash_passes(self):
        v, penalty, hard_fail = check_em_dash_workout_series("No em dashes in this sentence at all.")
        assert v == []
        assert penalty == 0
        assert hard_fail is False

    def test_single_em_dash_per_sentence_allowed(self):
        text = "The lift feels heavy—almost too heavy. But you finish it anyway—every time."
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert v == []
        assert penalty == 0
        assert hard_fail is False

    def test_a_matched_pair_is_one_aside_and_is_legal(self):
        """Two em-dashes bracketing one phrase is ONE aside, not a stack. The
        unit Sec. 7 governs is the aside; see TestEmDashAsideIsTheUnit."""
        text = "The lift feels heavy—your legs shake—but you finish it anyway. Rest ninety seconds."
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert v == []
        assert penalty == 0
        assert hard_fail is False

    def test_stacked_em_dash_in_one_sentence_hard_fails(self):
        """Three em-dashes is a bracketed pair PLUS a trailing aside: two
        asides in one sentence, which is the stacking Sec. 7 bans."""
        text = ("The lift feels heavy—your legs shake—but you finish it anyway—every time. "
                "Rest ninety seconds.")
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is True
        assert penalty == -10
        assert len(v) == 1

    def test_two_separate_stacked_sentences_cumulative(self):
        text = (
            "The bar feels heavy—your grip slips—but you hold on anyway—somehow. "
            "The next set is worse—your legs shake—but you finish it anyway—again."
        )
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is True
        assert penalty == -20
        assert len(v) == 2


class TestWorkoutSeriesBlocklist:
    def test_clean_text_passes(self):
        v, penalty, hard_fail = check_workout_series_blocklist(
            "The program builds real strength over a full training block."
        )
        assert v == []
        assert penalty == 0
        assert hard_fail is False

    def test_banned_term_hard_fails_on_single_hit(self):
        """Unlike the generic AI blocklist (3+ hits to hard fail), these
        PRINCIPLES.txt Sec. 7 terms are banned outright — one hit fails."""
        v, penalty, hard_fail = check_workout_series_blocklist(
            "This is the ultimate program for anyone serious about training."
        )
        assert hard_fail is True
        assert penalty == -10

    def test_multiple_banned_terms_cumulative(self):
        v, penalty, hard_fail = check_workout_series_blocklist(
            "This is the ultimate program. It will crush your old PRs and help you level up fast."
        )
        assert hard_fail is True
        assert penalty == -30  # ultimate, crush, level up


class TestExclamationPoints:
    def test_no_exclamation_points_passes(self):
        v, penalty, hard_fail = check_exclamation_points("Rest ninety seconds between sets.")
        assert v == []
        assert penalty == 0
        assert hard_fail is False

    def test_exclamation_point_hard_fails(self):
        v, penalty, hard_fail = check_exclamation_points("Let's go! Time to train!")
        assert hard_fail is True
        assert penalty == -10  # 2 instances x -5


class TestRulesetSwitch:
    def test_valid_rulesets_constant(self):
        assert "magazine" in VALID_RULESETS
        assert "workout_series" in VALID_RULESETS

    def test_unknown_ruleset_raises(self):
        with pytest.raises(ValueError):
            run_prohiblint(make_section_dict(), ruleset="bogus")

    def test_default_ruleset_is_magazine(self):
        """Calling run_prohiblint with no ruleset arg must behave exactly
        like ruleset='magazine' — existing callers (orchestrator.py) must
        keep working unchanged."""
        sections = make_section_dict(
            Training=make_text(1000, "The athlete trains hard—every single day.")
        )
        default_result = run_prohiblint(sections)
        explicit_result = run_prohiblint(sections, ruleset="magazine")
        assert default_result["sections"]["Training"]["passed"] is False
        assert explicit_result["sections"]["Training"]["passed"] is False
        assert default_result["summary"]["total_score"] == explicit_result["summary"]["total_score"]

    def test_magazine_hard_fails_single_em_dash(self):
        sections = make_section_dict(
            Training=make_text(1000, "The athlete trains hard—every single day.")
        )
        result = run_prohiblint(sections, ruleset="magazine")
        assert result["sections"]["Training"]["passed"] is False

    def test_workout_series_allows_single_em_dash_per_sentence(self):
        """The motivating case: real Seattle Series copy uses one em-dash
        aside per sentence throughout. Under magazine rules that is a 100%
        hard fail; under workout_series it must pass clean."""
        body = (
            "Seattle wears its fitness in the open—runners on the waterfront, "
            "climbers on the bluffs, coffee in every hand. Train like a local—"
            "wherever you are. "
        ) + make_text(900, "The city moves and so does the plan for every session.")
        sections = make_section_dict(Training=body)
        result = run_prohiblint(sections, ruleset="workout_series")
        assert result["sections"]["Training"]["passed"] is True
        assert result["sections"]["Training"]["violations"] == []

    def test_workout_series_flags_stacked_em_dash(self):
        body = (
            "The bar feels heavy—your grip slips—but you hold on anyway—somehow. "
        ) + make_text(900, "The city moves and so does the plan for every session.")
        sections = make_section_dict(Training=body)
        result = run_prohiblint(sections, ruleset="workout_series")
        assert result["sections"]["Training"]["passed"] is False
        assert any("Stacked em-dash" in v for v in result["sections"]["Training"]["violations"])

    def test_workout_series_skips_word_count_check(self):
        """A wildly out-of-range word count must NOT fail under
        workout_series — that line is governed by CharLint's exact
        character-count locks instead."""
        sections = make_section_dict(Training="Way too short for the magazine range.")
        result = run_prohiblint(sections, ruleset="workout_series")
        assert not any("Word count" in v for v in result["sections"]["Training"]["violations"])
        assert result["sections"]["Training"]["passed"] is True

    def test_magazine_still_enforces_word_count(self):
        sections = make_section_dict(Training="Way too short for the magazine range.")
        result = run_prohiblint(sections, ruleset="magazine")
        assert any("Word count" in v for v in result["sections"]["Training"]["violations"])
        assert result["sections"]["Training"]["passed"] is False

    def test_workout_series_hype_words_banned(self):
        sections = make_section_dict(
            Training="This is the ultimate plan. No excuses, just beast mode every single day. "
            + make_text(900, "The plan holds up over the full training block."),
        )
        result = run_prohiblint(sections, ruleset="workout_series")
        assert result["sections"]["Training"]["passed"] is False
        assert any("Banned outright" in v for v in result["sections"]["Training"]["violations"])

    def test_workout_series_exclamation_points_banned(self):
        sections = make_section_dict(
            Training="Let's go! " + make_text(900, "The plan holds up over the full training block."),
        )
        result = run_prohiblint(sections, ruleset="workout_series")
        assert result["sections"]["Training"]["passed"] is False
        assert any("Exclamation point" in v for v in result["sections"]["Training"]["violations"])

    def test_return_shape_unchanged_for_workout_series(self):
        """CONSTRAINT: run_prohiblint's return shape must not change across
        rulesets — orchestrator.py depends on these exact keys."""
        sections = make_section_dict()
        result = run_prohiblint(sections, ruleset="workout_series")
        assert set(result.keys()) >= {"sections", "issue_level", "summary"}
        for s in SECTIONS:
            assert set(result["sections"][s].keys()) >= {"violations", "score", "passed"}
        assert set(result["issue_level"].keys()) >= {"violations", "penalty", "passed", "element_results"}
        assert set(result["summary"].keys()) >= {"total_score", "all_passed"}


# ===========================================================================
# Defect 5 — check_mandatory_elements passed lowercase filler
# ===========================================================================
#
# This block is BLOCKING (the orchestrator folds it into the overall verdict),
# and both of its location patterns were compiled with re.IGNORECASE. Case is
# the entire signal these checks run on: "the coffee place, 12 main" and
# "Bluebird Provisions, 123 Broadway E" are the same string shape and differ
# only in capitalisation. A third hole was structural rather than about case —
# "a capitalised word within 80 chars" is satisfied by the "The" that starts
# every English sentence.

JUNK_TRAINING = ("The gym here does 3x8. The studio next door does the same thing "
                 "every week of the year without fail.")
JUNK_NUTRITION = ("the coffee place, 12 main and the bread place, 34 pine and the soup "
                  "place, 56 cedar and the rice place, 78 alder and the egg place, 90 "
                  "birch and the bean place, 11 maple.")
JUNK_CULTURE = "cafe blue. bar red. park green. diner grey. bistro tan."


def junk_issue():
    junk = {s: "" for s in SECTIONS}
    junk["Training"] = JUNK_TRAINING
    junk["Nutrition"] = JUNK_NUTRITION
    junk["Culture"] = JUNK_CULTURE
    return junk


class TestMandatoryElementsRejectLowercaseFiller:
    def test_junk_issue_fails_the_block(self):
        result = check_mandatory_elements(junk_issue())
        assert result["passed"] is False

    def test_junk_nutrition_names_no_places(self):
        """"the coffee place, 12 main" is a place name only if you throw away
        the capital letters."""
        result = check_mandatory_elements(junk_issue())
        assert result["element_results"]["nutrition_spots_4_places"] is False

    def test_junk_the_gym_the_studio_is_not_a_named_fitness_spot(self):
        """The context test used to accept any capitalised word within 80
        chars, which "The gym"/"The studio" satisfies twice over."""
        result = check_mandatory_elements(junk_issue())
        assert result["element_results"]["local_fitness_spots_2"] is False

    def test_junk_lowercase_place_types_are_not_venues(self):
        result = check_mandatory_elements(junk_issue())
        assert result["element_results"]["location_features_3_places"] is False

    def test_junk_rep_set_notation_is_genuinely_present(self):
        """Honesty check on the fixture: "3x8" IS real rep/set notation, so
        element 1 is correctly True. The block still fails on the other three
        — the point is that it no longer passes all four."""
        result = check_mandatory_elements(junk_issue())
        assert result["element_results"]["workout_plan_rep_set"] is True

    def test_junk_penalty_is_three_missing_elements(self):
        assert check_mandatory_elements(junk_issue())["penalty"] == -75

    # -- the other direction: real copy must still pass --------------------

    def test_real_sample_issue_nutrition_still_passes(self):
        """The real Nutrition section names four venues, each with a street
        address and a neighbourhood. Case-sensitivity must not cost it."""
        result = check_mandatory_elements(real_sample_sections())
        assert result["element_results"]["nutrition_spots_4_places"] is True

    def test_real_sample_issue_passes_every_element(self):
        result = check_mandatory_elements(real_sample_sections())
        assert result["element_results"] == {
            "workout_plan_rep_set": True,
            "nutrition_spots_4_places": True,
            "local_fitness_spots_2": True,
            "location_features_3_places": True,
        }
        assert result["passed"] is True
        assert result["penalty"] == 0

    def test_location_patterns_are_not_case_folded(self):
        """The defect named directly. re.IGNORECASE is the one flag that stops
        these patterns working, because capitalisation is the whole signal. In
        _TYPED_VENUE_RE only the place-TYPE word is case-insensitive, via a
        scoped (?i:...) group ("Copper Tavern" and "the bar: Navy Strength" are
        both real); the pattern-level flag must stay off."""
        assert not (prohiblint._LOCATED_PLACE_RE.flags & re.IGNORECASE)
        assert not (prohiblint._TYPED_VENUE_RE.flags & re.IGNORECASE)

    def test_a_name_has_to_be_capitalised_to_be_a_name(self):
        """The load-bearing guard behind both patterns: whatever the regex
        captures still has to contain a real proper-noun token."""
        assert prohiblint._proper_name_tokens("Copper Tavern") == ["Copper", "Tavern"]
        assert prohiblint._proper_name_tokens("the coffee place") == []
        assert prohiblint._proper_name_tokens("The coffee shop") == []

    def test_a_venue_name_stops_at_the_venue(self):
        """The name half of the venue pattern is case-sensitive so the capture
        ends where the name ends. Widening it to accept lowercase makes the
        capture run on through "on Eastlake" and invent a venue called Fuel
        House Eastlake."""
        found = prohiblint._distinct_named_places(
            "After the gym, before the bar: Fuel House on Eastlake.",
            prohiblint._TYPED_VENUE_RE)
        assert found == {"fuel house"}

    def test_a_quantity_and_a_month_are_not_venues(self):
        """"One gym in March 2025" names a count and a date."""
        assert prohiblint._distinct_named_places(
            "One gym in March 2025. Another studio in April 2025. A third bar in May 2025.",
            prohiblint._TYPED_VENUE_RE) == set()

    def test_same_copy_lowercased_fails(self):
        """The sharpest statement of the defect: identical text, identical
        addresses, only the capitalisation removed — and the verdict flips."""
        sections = real_sample_sections()
        lowered = {name: text.lower() for name, text in sections.items()}
        assert check_mandatory_elements(sections)["passed"] is True
        assert check_mandatory_elements(lowered)["passed"] is False


# ---------------------------------------------------------------------------
# Defect 5b — the mandatory-element thresholds themselves
# ---------------------------------------------------------------------------
#
# >=4 / >=2 / >=3 all carry the blocking verdict, so each is pinned from both
# sides: exactly at the threshold passes, one below fails. Dropping any of them
# to >=0 (or raising it) breaks a test here.

NUTRITION_VENUES = [
    "Bluebird Provisions, 123 Broadway E, Capitol Hill.",
    "Fuel House, 456 Eastlake Ave E, South Lake Union.",
    "Green District, 789 Queen Anne Ave N, Queen Anne.",
    "Big Mario's, 1009 E Pike St, Capitol Hill.",
]


class TestMandatoryElementThresholds:
    @pytest.mark.parametrize("count, expected", [(3, False), (4, True)])
    def test_nutrition_needs_four_named_places(self, count, expected):
        sections = neutral_sections(Nutrition=" ".join(NUTRITION_VENUES[:count]))
        result = check_mandatory_elements(sections)
        assert result["element_results"]["nutrition_spots_4_places"] is expected

    def test_nutrition_repeating_one_venue_does_not_reach_four(self):
        """Names are counted distinct: six mentions of one cafe is one place."""
        sections = neutral_sections(Nutrition=" ".join([NUTRITION_VENUES[0]] * 6))
        result = check_mandatory_elements(sections)
        assert result["element_results"]["nutrition_spots_4_places"] is False

    @pytest.mark.parametrize("text, expected", [
        ("Rainier Barbell gym opens early.", False),
        ("Rainier Barbell gym opens early. Fremont Hot Yoga runs classes.", True),
    ])
    def test_fitness_spots_needs_two(self, text, expected):
        sections = neutral_sections(Training=text)
        result = check_mandatory_elements(sections)
        assert result["element_results"]["local_fitness_spots_2"] is expected

    @pytest.mark.parametrize("count, expected", [(2, False), (3, True)])
    def test_location_features_needs_three(self, count, expected):
        venues = ["Copper Tavern serves food late.",
                  "Volunteer Park fills up by seven.",
                  "Navy Strength in Belltown opens at five."]
        sections = neutral_sections(Nightlife=" ".join(venues[:count]))
        result = check_mandatory_elements(sections)
        assert result["element_results"]["location_features_3_places"] is expected

    def test_missing_rep_set_notation_still_fails(self):
        sections = neutral_sections()
        result = check_mandatory_elements(sections)
        assert result["element_results"]["workout_plan_rep_set"] is False


# ===========================================================================
# Defect 6 — cold-open false negatives: the canonical "[Name] [verb]s ..." form
# ===========================================================================
#
# Restricting the pattern to a 15-verb list bought two fewer false positives at
# the cost of missing the textbook form for every verb outside the list. The
# rule is now structural (bare first name + open-class present-tense verb +
# scene marker), so it does not depend on having enumerated "laces".

CANONICAL_COLD_OPENS = [
    "Marcus laces his shoes in the dark of the stairwell, counting the flights down to the street...",
    "Jenna pushes through the door at 5:40am with her hood still up...",
    "Nadia laces up outside the Ballard studio before the doors open...",
]


class TestColdOpenCanonicalForm:
    @pytest.mark.parametrize("text", CANONICAL_COLD_OPENS)
    def test_canonical_cold_open_matches(self, text):
        assert _matches_cold_open_pattern(text) is True

    @pytest.mark.parametrize("opener", CANONICAL_COLD_OPENS)
    def test_canonical_cold_open_penalised_through_public_api(self, opener):
        """Same three openers as whole paragraphs, over the 30-word gate."""
        para = opener.replace("...", ", ") + (
            "and the block outside has not started moving yet on a plain "
            "weekday that looks like every other one this month.")
        v, penalty, hard_fail = check_cold_open(para)
        assert penalty == -15
        assert hard_fail is False
        assert len(v) == 1

    def test_verb_outside_any_list_still_caught(self):
        """The point of the structural rule: a verb nobody thought to
        enumerate is still a verb."""
        assert _matches_cold_open_pattern(
            "Priya shoulders her bag before the doors open on a wet Tuesday."
        ) is True

    def test_full_name_reads_as_attribution_not_a_scene(self):
        """A surname is the difference between a reported source and an
        invented character: "Jade Kim orders ..." opens the real issue."""
        assert _matches_cold_open_pattern(
            "Jade Kim orders the same thing every Tuesday: the black sesame "
            "smoothie and a side of turkey avocado toast."
        ) is False


# ===========================================================================
# Defect 7 — "is" in the narrative-verb list fired on every "X is ..." lede
# ===========================================================================
#
# The docstring claimed the pattern fired only on "actual narrative-movement
# verbs, not on ordinary editorial sentences". With "is" in the list it did the
# exact opposite: EVERY "<Capitalised word> is ..." opener matched. That, not
# any Cascade-specific quirk, is the root cause of the known city_intro false
# positive.

ORDINARY_LEDES = [
    "Recovery is the part of the week most lifters get wrong.",
    "Creatine is the only supplement on this page worth the shelf space.",
    "Ballard is where the 5am crowd went after the Fremont lease fell through.",
    "Protein is not the bottleneck for most people in this city.",
]


class TestOrdinaryLedesAreNotColdOpens:
    @pytest.mark.parametrize("text", ORDINARY_LEDES)
    def test_ordinary_lede_does_not_match(self, text):
        assert _matches_cold_open_pattern(text) is False

    @pytest.mark.parametrize("lede", ORDINARY_LEDES)
    def test_ordinary_lede_not_penalised_through_public_api(self, lede):
        para = lede + (" The rest of the page argues the case with numbers "
                       "rather than adjectives, which is the only way anyone "
                       "should be reading a claim like that one.")
        v, penalty, _ = check_cold_open(para)
        assert penalty == 0
        assert v == []

    def test_is_is_not_a_narrative_verb(self):
        """Re-adding "is" to _NARRATIVE_VERBS reintroduces the defect: a
        copula is not movement."""
        assert _has_narrative_present_tense(
            "Recovery is the part of the week most lifters get wrong."
        ) is False

    def test_narrative_verbs_still_detect_actual_movement(self):
        assert _has_narrative_present_tense(
            "Someone sits up in bed and reaches for a phone."
        ) is True

    def test_city_intro_real_baseline_is_not_flagged(self):
        """The reported false positive, on the real Seattle Series city_intro
        baseline: a neighbourhood, a copula, and no scene."""
        assert _matches_cold_open_pattern(
            "Cascade is the quieter end of South Lake Union, ten minutes "
            "across, and this volume walks its two best doors."
        ) is False

    def test_cover_body_real_baseline_is_not_flagged(self):
        body = ("Seattle wears its fitness in the open, runners on the waterfront, "
                "climbers on the bluffs, coffee in every hand. Train like a local, "
                "wherever you are. The city moves and so does the plan for every "
                "session of the week.")
        v, penalty, _ = check_cold_open(body)
        assert penalty == 0

    def test_recovery_section_scores_84_not_69(self):
        """The decisive case. An ordinary "Recovery is..." lede, two real
        AI-blocklist hits (-10) and two real second-person hits (-6) is an
        84/PASS. The cold-open false positive turned it into a 69/FAIL."""
        body = (
            "Recovery is the part of the week most lifters get wrong. "
            "A holistic plan beats a vibrant one. "
            "You should sleep more, and your body will thank you for it. "
        ) + make_text(600, NEUTRAL_FILLER)
        result = run_prohiblint(neutral_sections(Recovery=body))
        section = result["sections"]["Recovery"]
        assert not any("cold-open" in v for v in section["violations"])
        assert section["score"] == 84
        assert section["passed"] is True


# ---------------------------------------------------------------------------
# Defect 7b — the cold-open rules that carry the verdict, pinned one at a time
# ---------------------------------------------------------------------------
#
# Each test below is built so that exactly ONE rule can flag it: the others are
# structurally unable to fire. Delete the rule under test and the penalty goes
# to zero.

class TestColdOpenRulesArePinned:
    #: has_proper is True (Yesler), so the unattributed-scene branch is off;
    #: "It" is sentence furniture, so the person rule is off. Only the clock
    #: opener can flag this.
    CLOCK_ONLY = ("It is 5:30am on Yesler and the block is quiet. The crew arrives "
                  "in ones and twos, and the door stays propped open until the last "
                  "of them is inside before six.")

    #: has_proper is True (Ballard), so the branch is off; the verb is the
    #: copula "is", so only the progressive arm of the person rule can flag it.
    PROGRESSIVE_ONLY = ("Marcus is already lacing up when the Ballard crew arrives, and "
                        "the room has not even warmed enough for anyone to take a jacket "
                        "off yet, and the door still stands open to the street.")

    #: Nothing is named and nothing is capitalised except sentence openers, so
    #: neither pattern rule can fire. Only the unattributed-scene branch can.
    BRANCH_ONLY = ("The room stays dark at this hour. Someone sits up in bed, reaches "
                   "for a phone, and pulls on the same clothes as always, then heads "
                   "down the stairs before the sun is up.")

    def test_clock_opener_rule_carries_its_case(self):
        assert check_cold_open(self.CLOCK_ONLY)[1] == -15
        assert _matches_cold_open_pattern(self.CLOCK_ONLY) is True

    def test_progressive_rule_carries_its_case(self):
        assert check_cold_open(self.PROGRESSIVE_ONLY)[1] == -15
        assert _matches_cold_open_pattern(self.PROGRESSIVE_ONLY) is True

    def test_unattributed_scene_branch_carries_its_case(self):
        """"no proper noun + narrative present tense" is the only rule that
        can reach this text; deleting the branch drops the penalty to 0."""
        assert _matches_cold_open_pattern(self.BRANCH_ONLY) is False
        assert check_cold_open(self.BRANCH_ONLY)[1] == -15

    def test_unattributed_scene_branch_needs_a_scene(self):
        """The branch is not "no names + any verb": without a moment anchor it
        does not fire, which is what keeps it off ordinary unattributed copy."""
        no_moment = ("The room stays dark at this hour. Someone sits up in bed, reaches "
                     "for a phone, and pulls on the same clothes as always, then heads "
                     "down the stairs and out onto the street.")
        assert check_cold_open(no_moment)[1] == 0

    def test_thirty_word_gate_is_exact_for_the_one_signal_rules(self):
        """The >30-word floor still carries a verdict, but only for the rules
        that are one signal wide. The clock opener is the cleanest case: at 30
        words it is not flagged, at 31 it is.

        (Deliberate design change — see check_cold_open. The floor used to
        apply to every rule, which meant a one-line cold-open was never
        examined at all. The person rule is a four-way conjunction and now runs
        at any length; the clock opener and the unattributed-scene branch keep
        the floor because on short copy they would fire on a deck or a
        standfirst.)"""
        at_30 = ("It is 5:30am on Yesler and the block outside is quiet, with the door "
                 "propped open to the street and nobody through it yet on a plain grey "
                 "weekday in")
        at_31 = at_30 + " winter"
        assert _word_count(_first_paragraph(at_30)) == 30
        assert _word_count(_first_paragraph(at_31)) == 31
        assert _cold_open_rule(at_30) == "clock"      # the rule matches at both
        assert check_cold_open(at_30)[1] == 0         # but the floor gates it
        assert check_cold_open(at_31)[1] == -15

    def test_unattributed_branch_keeps_the_thirty_word_floor(self):
        """The other gated rule: no name in it at all, so short copy carries
        too little evidence to spend -15 on."""
        at_30 = ("The room stays dark. Someone sits up in bed before the sun is up, "
                 "reaches for a phone and pulls on the same clothes as always, then goes "
                 "down the")
        at_31 = at_30 + " stairs"
        assert _word_count(_first_paragraph(at_30)) == 30
        assert _word_count(_first_paragraph(at_31)) == 31
        assert _cold_open_rule(at_30) is None         # branch, not a pattern
        assert check_cold_open(at_30)[1] == 0
        assert check_cold_open(at_31)[1] == -15

    def test_short_named_cold_open_is_no_longer_a_bypass(self):
        """The point of splitting the gate. Six words, every conjunct of the
        person rule satisfied, and under the old single floor it scored 0."""
        assert _word_count("Maya laces her shoes before dawn.") == 6
        assert check_cold_open("Maya laces her shoes before dawn.")[1] == -15

    def test_short_furniture_is_still_not_a_cold_open(self):
        """And the reason the clock rule keeps its floor: a deck says the time
        too."""
        assert check_cold_open("It is 5am. Time to train.")[1] == 0
        assert check_cold_open("Recovery is the whole point.")[1] == 0

    def test_place_name_subject_is_never_a_person(self):
        assert _matches_cold_open_pattern(
            "Fremont wakes up slowly before the sun does, and he knows it."
        ) is False

    def test_copula_alone_blocks_a_full_scene(self):
        """Isolates the copula rule. A venue name the place list does not know,
        a genuine scene marker, and a full moment anchor — everything a
        cold-open needs EXCEPT a verb of action. "X is her favourite ..." is a
        recommendation, not a scene, and only _COPULA_VERBS says so."""
        assert _matches_cold_open_pattern(
            "Victrola is her favourite counter before the doors open on Thomas."
        ) is False

    def test_copula_rule_does_not_swallow_a_real_progressive(self):
        """The other side of it: "is" followed by a progressive is still a
        person mid-action, and must stay caught."""
        assert _matches_cold_open_pattern(
            "Victrola is her favourite counter, but Marcus is lacing up before "
            "the doors open on Thomas."
        ) is False       # not at the paragraph start, so out of scope
        assert _matches_cold_open_pattern(
            "Marcus is lacing up before the doors open on Thomas."
        ) is True

    @pytest.mark.parametrize("lede", [
        "Tuesday starts with the hardest session of his week before the doors open.",
        "Morning belongs to his crew before the doors open at the studio on Thomas.",
    ])
    def test_calendar_and_time_words_are_not_people(self, lede):
        """Isolates _NON_PERSON_SUBJECTS: an action verb, a possessive pronoun
        and a threshold clause all fire here. Only "is this token a name?"
        keeps these ordinary ledes clean."""
        assert _matches_cold_open_pattern(lede) is False

    def test_lowercase_elsewhere_demotes_a_capitalised_common_noun(self):
        """A word this copy writes in lowercase somewhere else is a common
        noun that started a sentence, not a name."""
        section = ("Creatine carries his whole week before the doors open. "
                   "Cheap creatine is the boring half of the plan.")
        assert _matches_cold_open_pattern(section, full_text=section) is False
        # Same sentence, without the section that writes "creatine" in
        # lowercase: nothing left says it is a common noun.
        assert _matches_cold_open_pattern(
            "Creatine carries his whole week before the doors open.") is True

    def test_lowercase_evidence_is_read_from_the_whole_section(self):
        """check_cold_open hands the matcher the WHOLE section, not just the
        200-char snippet it flags on: the sentence that proves "Creatine" is a
        common noun is normally further down the page, and the check would be
        useless if it could only see the opening.

        Named venue in the opener, so the unattributed-scene branch is off and
        the person rule is the only thing that can fire."""
        opener = ("Creatine carries his whole week before the doors open at Rainier "
                  "Barbell, and the rest of the plan follows from that one single "
                  "decision more than anything else on the page.")
        assert check_cold_open(opener)[1] == -15

        with_later_paragraph = opener + "\n\nCheap creatine is the boring half of the plan."
        assert "creatine" not in _first_paragraph(with_later_paragraph)
        assert check_cold_open(with_later_paragraph)[1] == 0

    def test_ing_nouns_are_not_progressive_verbs(self):
        """"nothing" ends in "ing" and is not a verb. Without that guard,
        "<Name> is nothing without ..." reads as a person mid-action."""
        assert _matches_cold_open_pattern(
            "Creatine is nothing without his hardest session before the doors "
            "open on a plain grey Tuesday in the middle of the week."
        ) is False


# ===========================================================================
# Defect 8 — an abbreviation bypassed the stacked-em-dash hard fail
# ===========================================================================
#
# _SENTENCE_SPLIT_RE split on any period followed by whitespace, so "Mr." or
# "9th St." cut a stacked sentence into two "sentences" with one aside each —
# legal under PRINCIPLES.txt Sec. 7. St./Ave./Vol./No./Mr. are ordinary
# Seattle Series venue copy, so this was the common case.
#
# The examples below carry THREE em-dashes each — a bracketed pair around the
# abbreviation plus a trailing aside, i.e. two asides — because two em-dashes
# is one aside and legal (see Defect 12). The guard is still exactly as
# load-bearing: split at "Mr." and the three dashes become 1 + 2, which is one
# legal aside followed by another, and the stack ships.

EM = "—"

STACKED_WITH_ABBREVIATION = [
    "The bar {d} Mr. Schomer's {d} is the grand one on Yale {d} open until two.",
    "Open on Yale {d} 9th St. north {d} until two in the morning {d} every night.",
    "The issue {d} Vol. 1 of the run {d} lands in March {d} the first one.",
]


class TestStackedEmDashAbbreviationBypass:
    @pytest.mark.parametrize("template", STACKED_WITH_ABBREVIATION)
    def test_abbreviation_no_longer_bypasses_the_hard_fail(self, template):
        text = template.format(d=EM)
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is True
        assert penalty == -10
        assert len(v) == 1

    @pytest.mark.parametrize("template", STACKED_WITH_ABBREVIATION)
    def test_the_abbreviation_guard_is_what_catches_them(self, template):
        """Proves the guard is still load-bearing under the aside rule rather
        than assuming it: split naively at the abbreviation's period and each
        half holds one legal aside, so the stack would ship."""
        text = template.format(d=EM)
        naive = re.split(r'(?<=[.!?])\s+', text)
        assert len(naive) == 2
        assert [prohiblint._count_asides(half) for half in naive] == [1, 1]

    def test_control_without_abbreviation_still_caught(self):
        text = f"The bar {EM} loud, cheap {EM} is the grand one on Yale {EM} open until two."
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is True
        assert penalty == -10

    def test_real_sentence_breaks_are_still_breaks(self):
        """The guard must not over-merge: two sentences that each stack their
        own asides stay two sentences and cost two violations, not one."""
        text = (f"The bar {EM} Mr. Schomer's {EM} is grand {EM} always. "
                f"The cafe {EM} small {EM} is quiet {EM} mostly.")
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is True
        assert len(v) == 2          # one violation per stacked sentence

    def test_one_em_dash_per_sentence_around_an_abbreviation_is_legal(self):
        text = (f"Open on Yale {EM} 9th St. north. "
                f"The issue lands in March {EM} Vol. 1 of the run.")
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is False
        assert penalty == 0

    def test_splitter_keeps_abbreviations_inside_one_sentence(self):
        assert _split_into_sentences("The bar is Mr. Schomer's place on Yale.") == [
            "The bar is Mr. Schomer's place on Yale."]
        assert _split_into_sentences("Open on 9th St. north until two.") == [
            "Open on 9th St. north until two."]

    def test_splitter_still_splits_ordinary_sentences(self):
        assert _split_into_sentences("Rest ninety seconds. Then go again.") == [
            "Rest ninety seconds.", "Then go again."]

    def test_unknown_abbreviation_is_held_by_the_opener_test(self):
        """No abbreviation list is complete, which is why the abbreviation list
        is not the only guard: "Bldg." is not on it, and the boundary is still
        rejected because "north" does not open a sentence."""
        text = f"The room {EM} 12 Yale Bldg. north {EM} stays open until two {EM} nightly."
        assert _split_into_sentences(text) == [text]
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert hard_fail is True
        assert penalty == -10

    def test_workout_series_run_still_hard_fails_on_abbreviated_stack(self):
        body = (f"The bar {EM} Mr. Schomer's {EM} is the grand one on Yale {EM} open until two. "
                + make_text(900, NEUTRAL_FILLER))
        result = run_prohiblint(neutral_sections(Training=body), ruleset="workout_series")
        assert result["sections"]["Training"]["passed"] is False
        assert any("Stacked em-dash" in v for v in result["sections"]["Training"]["violations"])


# ===========================================================================
# Defect 9 — the section pass threshold was never pinned
# ===========================================================================

def scored_training(second_person=0, ai_terms=0, words=1000):
    """Training copy carrying exactly the requested number of penalty hits."""
    body = ("The training block runs for six weeks. "
            + "You should rest well. " * second_person
            + "This holistic plan works. " * ai_terms)
    pad = words - len(body.split())
    return body + " " + make_text(pad, NEUTRAL_FILLER)


class TestSectionPassThreshold:
    def test_penalties_land_where_expected(self):
        """Fixture honesty check before the boundary test leans on it."""
        result = run_prohiblint(neutral_sections(Training=scored_training(second_person=1)))
        assert result["sections"]["Training"]["score"] == 97
        result = run_prohiblint(neutral_sections(Training=scored_training(ai_terms=1)))
        assert result["sections"]["Training"]["score"] == 95

    def test_exactly_seventy_passes(self):
        """The threshold is `score >= 70`, so 70 is a pass. Ten second-person
        hits at -3 is exactly -30."""
        result = run_prohiblint(neutral_sections(Training=scored_training(second_person=10)))
        section = result["sections"]["Training"]
        assert section["score"] == 70
        assert section["passed"] is True

    def test_sixty_nine_fails(self):
        """One point below the threshold: seven second-person hits (-21) plus
        two AI-blocklist hits (-10). Two, not three — three is a hard fail and
        would prove nothing about the threshold."""
        result = run_prohiblint(neutral_sections(Training=scored_training(second_person=7, ai_terms=2)))
        section = result["sections"]["Training"]
        assert section["score"] == 69
        assert section["passed"] is False

    def test_hard_fail_overrides_a_passing_score(self):
        """`passed = not hard_fail and score >= 70`: the conjunction matters,
        a single em-dash scores 90 and still fails."""
        body = f"The block runs for six weeks {EM} and then it repeats. " + make_text(980, NEUTRAL_FILLER)
        section = run_prohiblint(neutral_sections(Training=body))["sections"]["Training"]
        assert section["score"] == 90
        assert section["passed"] is False


# ===========================================================================
# Defect 10 — dead code
# ===========================================================================

class TestNoDeadCode:
    def test_defaultdict_import_removed(self):
        assert not hasattr(prohiblint, "defaultdict")

    def test_unused_sentence_start_regex_removed(self):
        assert not hasattr(prohiblint, "_SENTENCE_START_RE")


# ===========================================================================
# Defect 11 — a PERSON with a neighbourhood was counted as a named PLACE
# ===========================================================================
#
# `Name, Neighbourhood` is the shape of a venue with a location and equally the
# shape of a person with an address, and the mandatory-element block is
# BLOCKING — so an issue containing no venues at all cleared the check that
# exists to require venues. Worse, it is the realistic shape rather than an
# edge case: Nutrition is a people-register section (Handbook Sec. 5.2), so
# naming four subjects and where they live is what that copy is meant to do.
#
# Both directions are pinned: real venues must still count, people must not.

FOUR_PEOPLE_WITH_NEIGHBOURHOODS = (
    "Aisha Coleman, Beacon Hill, eats the same breakfast before every shift at "
    "the hospital. Marcus Webb, Georgetown, cooks on Sundays for the whole week "
    "ahead of him. Delphine Okoro, Wallingford, keeps a protein target and hits "
    "it most days. Tomas Herrera, Ravenna, stopped counting macros in March and "
    "has not gone back to it since then."
)

FOUR_PEOPLE_PREPOSITIONAL = (
    "Aisha Coleman in Beacon Hill eats early. Marcus Webb in Georgetown cooks on "
    "Sundays. Delphine Okoro in Wallingford hits her target. Tomas Herrera in "
    "Ravenna stopped counting macros last spring."
)


class TestPeopleAreNotPlaces:
    def test_four_people_do_not_satisfy_the_nutrition_spots_element(self):
        result = check_mandatory_elements(
            neutral_sections(Nutrition=FOUR_PEOPLE_WITH_NEIGHBOURHOODS))
        assert result["element_results"]["nutrition_spots_4_places"] is False

    def test_four_people_do_not_satisfy_location_features(self):
        result = check_mandatory_elements(
            neutral_sections(Nutrition=FOUR_PEOPLE_WITH_NEIGHBOURHOODS))
        assert result["element_results"]["location_features_3_places"] is False

    def test_the_prepositional_form_is_not_a_way_round_it(self):
        """"Aisha Coleman in Beacon Hill" is the same claim as "Aisha Coleman,
        Beacon Hill" — the separator is not the signal."""
        result = check_mandatory_elements(
            neutral_sections(Nutrition=FOUR_PEOPLE_PREPOSITIONAL))
        assert result["element_results"]["nutrition_spots_4_places"] is False

    def test_an_issue_of_only_people_fails_the_blocking_check(self):
        """The verdict that was being bypassed. Rep/set notation is genuinely
        present, so the other three elements carry the failure."""
        sections = neutral_sections(
            Nutrition=FOUR_PEOPLE_WITH_NEIGHBOURHOODS,
            Training="The gym Marcus uses has no name on the door. He does 3x8 and leaves.")
        result = check_mandatory_elements(sections)
        assert result["element_results"]["workout_plan_rep_set"] is True
        assert result["passed"] is False
        assert result["penalty"] == -75

    def test_a_person_who_opens_something_is_still_a_person(self):
        """The venue predicate is "opens AT a time", not "opens" — otherwise
        whoever has the key to the gym becomes a venue."""
        text = ("Aisha Coleman, Beacon Hill, opens the gym at five. Marcus Webb, "
                "Georgetown, opens the shop. Delphine Okoro, Wallingford, opens the "
                "pool. Tomas Herrera, Ravenna, opens the desk.")
        assert prohiblint._located_venue_names(text) == set()

    def test_a_gym_in_the_same_sentence_does_not_make_a_person_a_venue(self):
        """The venue evidence has to be that NAME's own predicate. Reading it
        anywhere in the sentence puts the person and the gym on the same
        footing."""
        assert prohiblint._located_venue_names(
            "Marcus Webb, Georgetown, trains at a gym near the water.") == set()

    # -- the other direction: real venues still count ----------------------

    def test_a_street_address_still_makes_a_venue(self):
        assert prohiblint._located_venue_names(
            "Bluebird Provisions, 123 Broadway E, Capitol Hill.") == {"bluebird provisions"}

    def test_a_neighbourhood_plus_opening_hours_still_makes_a_venue(self):
        assert prohiblint._located_venue_names(
            "Navy Strength in Belltown opens at five.") == {"navy strength"}

    def test_the_real_sample_nutrition_still_names_its_four_venues(self):
        assert prohiblint._located_venue_names(
            real_sample_sections()["Nutrition"], require_address=True) == {
                "bluebird provisions", "fuel house", "green district", "big mario's"}

    @pytest.mark.parametrize("cue", [
        "Bluebird Provisions, Capitol Hill, 34, opens at five.",
        "Bluebird Provisions, Capitol Hill, who opens at five, is closed today.",
        "Bluebird Provisions, Capitol Hill, says the counter opens at five.",
        "Bluebird Provisions, Capitol Hill, a head coach, opens at five.",
    ])
    def test_a_person_cue_vetoes_even_a_perfect_venue_predicate(self, cue):
        """Ages, ", who", reported speech and role appositions belong to people.
        Whatever follows them, the name in front is not a room.

        These four DOCUMENT the veto but do not PIN it: none of them also
        matches _VENUE_PREDICATE_RE, so the anchor tier split alone would keep
        them out. The two classes below are the ones that fail without it."""
        assert prohiblint._located_venue_names(cue) == set()

    # -- the veto, pinned. Delete _PERSON_CUE_RE from _located_venue_names and
    #    both of these classes start counting people as venues. --------------

    @pytest.mark.parametrize("text", [
        "Marcus Webb in Fremont, a gym owner, trains at six every morning.",
        "Jade Kim in Ballard, a bar manager, trains at six.",
        "Priya Raman on Capitol Hill, a studio founder, is up before five.",
        "Ana Silva in Fremont, a yoga studio instructor, runs the class.",
    ])
    def test_a_role_apposition_can_look_exactly_like_a_venue_predicate(self, text):
        """The overlap the two patterns really have. "a gym owner" is a role
        apposition AND, read three words shorter, "a gym" — a place type behind
        an article, which is one of _VENUE_PREDICATE_RE's own arms. The tier
        split cannot separate these; only the person cue can."""
        assert prohiblint._VENUE_PREDICATE_RE.match(text[text.index(","):])
        assert prohiblint._located_venue_names(text) == set()

    @pytest.mark.parametrize("text", [
        "Aisha Coleman, 123 Broadway E, 34, says she trains at five.",
        "Marcus Webb at 456 Eastlake Ave E, 41, says he trains at six.",
        "Delphine Okoro, 789 Pike St, who trains at seven, says so.",
        "Tomas Herrera at 900 Rainier Ave S, a head coach, says he trains.",
    ])
    def test_a_person_with_a_street_address_is_still_a_person(self, text):
        """The address tier is venue-grade on the anchor alone, so the person
        cue is the ONLY thing standing between it and a bylined human."""
        assert prohiblint._located_venue_names(text, require_address=True) == set()

    def test_the_person_cue_has_to_be_read_past_the_address(self):
        """_ADDRESS_ANCHOR stops one character into the street name, so reading
        the cue from the raw match end starts it mid-word and it can never fire.
        This is the assertion that catches a regression to text[m.end():]."""
        text = "Marcus Webb at 456 Eastlake Ave E, 41, says he trains."
        m = prohiblint._LOCATED_PLACE_RE.search(text)
        assert m.group("anchor") == "456 E"                      # mid-word
        assert prohiblint._PERSON_CUE_RE.match(text[m.end():]) is None
        assert prohiblint._PERSON_CUE_RE.match(
            prohiblint._tail_after_anchor(text, m.end())) is not None

    def test_four_people_with_addresses_do_not_satisfy_the_nutrition_element(self):
        """The bypass end to end: the strictest tier in the check, the one
        Handbook Sec. 9 locks, satisfied by four humans and their post."""
        nutrition = (
            "Aisha Coleman, 123 Broadway E, 34, says she trains at five. "
            "Marcus Webb at 456 Eastlake Ave E, 41, says he trains at six. "
            "Delphine Okoro, 789 Pike St, who trains at seven, says so. "
            "Tomas Herrera at 900 Rainier Ave S, a head coach, says he trains.")
        result = check_mandatory_elements(neutral_sections(Nutrition=nutrition))
        assert result["element_results"]["nutrition_spots_4_places"] is False

    def test_and_real_venues_with_addresses_still_count(self):
        """The other direction, on the real issue: reading past the address
        must not cost a single genuine venue."""
        assert prohiblint._located_venue_names(
            real_sample_sections()["Nutrition"], require_address=True) == {
                "bluebird provisions", "fuel house", "green district", "big mario's"}


class TestNamedFitnessSpotsNeedANameAttached:
    def test_the_gym_marcus_uses_is_not_a_named_gym(self):
        """The sentence says in words that the gym has no name. Proximity to a
        capitalised token is not a name — it is a person standing nearby."""
        assert prohiblint._named_fitness_spots(
            "The gym Marcus uses has no name on the door.") == set()

    def test_two_people_near_two_keywords_do_not_make_two_spots(self):
        result = check_mandatory_elements(neutral_sections(
            Training=("The gym Marcus uses has no name on the door. Aisha trains at "
                      "a studio with no sign either.")))
        assert result["element_results"]["local_fitness_spots_2"] is False

    def test_a_room_described_by_where_it_is_is_not_named(self):
        """"the Ballard gym" is a location said twice; the name has to
        contribute a word of its own, or the type word has to be part of it."""
        assert prohiblint._named_fitness_spots(
            "the Ballard gym opens early and the Capitol Hill gym does not.") == set()

    def test_a_club_named_after_its_neighbourhood_still_counts(self):
        """The other side of that: "Capitol Hill Run Club" IS the name, and
        there the type word is capitalised because it is part of it."""
        assert prohiblint._named_fitness_spots(
            "Capitol Hill Run Club meets at six.") == {"capitol hill run club"}

    def test_one_gym_matched_through_two_of_its_own_words_is_one_gym(self):
        """"Rainier Barbell gym" matches on "barbell" and again on "gym". The
        prefix dedup is what keeps that from clearing a >=2 threshold alone."""
        assert prohiblint._named_fitness_spots(
            "Rainier Barbell gym opens early.") == {"rainier barbell gym"}

    def test_the_real_sample_still_names_its_gyms(self):
        sections = real_sample_sections()
        full = "\n\n".join(sections.get(s, "") for s in SECTIONS)
        found = prohiblint._named_fitness_spots(full)
        assert {"rainier barbell", "cascade athletic club"} <= found


class TestAVenueNameStopsAtItsOwnSentence:
    def test_a_name_does_not_swallow_a_full_stop(self):
        """The name class allows a trailing period so "Ave." stays inside a
        name — which also let a name run through one and into the next
        sentence, inventing a venue out of two unrelated words."""
        assert prohiblint._named_fitness_spots(
            "Fremont Hot Yoga adds sessions Tuesdays. Seattle's gyms are busy."
        ) == {"fremont hot yoga"}

    def test_a_name_does_not_span_a_paragraph_break(self):
        """"Tuesdays" ends one paragraph and "Copper" opens the next; without
        the newline guard the name pattern joins them into one venue."""
        assert prohiblint._distinct_named_places(
            "Sessions run Tuesdays\n\nCopper Tavern is on Pike.",
            prohiblint._TYPED_VENUE_RE) == {"copper"}

    def test_a_possessive_is_still_the_place_it_names(self):
        """"Seattle's" is Seattle. Without normalising the possessive it walked
        past the neighbourhood filter and named a venue."""
        assert prohiblint._bare_token("Seattle's") == "Seattle"
        assert prohiblint._named_fitness_spots("Seattle's gyms are busy.") == set()


class TestTypedVenueNeedsPunctuationAfterTheTypeWord:
    def test_type_word_then_name_needs_a_colon_or_comma(self):
        assert prohiblint._distinct_named_places(
            "before the bar: Fuel House on Eastlake.",
            prohiblint._TYPED_VENUE_RE) == {"fuel house"}

    def test_an_unpunctuated_type_word_reads_as_a_relative_clause(self):
        """English elides the relative pronoun: "the gym [that] Marcus uses".
        Without the punctuation guard that names a venue called Marcus."""
        assert prohiblint._distinct_named_places(
            "at the gym Marcus uses", prohiblint._TYPED_VENUE_RE) == set()

    def test_called_and_named_still_bridge_to_the_name(self):
        assert prohiblint._distinct_named_places(
            "a club called Cascade Rowing", prohiblint._TYPED_VENUE_RE) == {"cascade rowing"}


# ===========================================================================
# Defect 12 — ordinary connectives were being read as scene markers
# ===========================================================================
#
# `\balready\b` and `(before|after|until|while) (the|a|an|its|it)` are plain
# English, not scenery. Combined with the unattributed-scene branch they cost
# -15 on realistic no-proper-noun ledes — the same false-positive class as "is"
# in the narrative-verb list.

CONNECTIVE_LEDES = [
    "The taper week runs shorter than the block before it, and the floor empties "
    "after the first hour, which is the whole point of a week that asks for less "
    "than the one before it did.",

    "The programme moves faster than most people expect, and the second block is "
    "already harder than the first, which is what the numbers on the sheet say "
    "before anyone has to be told it out loud.",

    "The room fills after the shift change and empties again before the last hour, "
    "and the racks turn over twice in that window without anyone having to wait "
    "for a bar longer than a minute.",

    "The plan runs four days and the fourth is already the easiest of them, "
    "because a deload is not a rest week and the difference matters more than "
    "most lifters are told when they start out.",

    "The bar moves slower on the last set until the rep is done, and that is the "
    "signal to stop, not a reason to add another plate to a lift that is already "
    "finished for the day.",
]


class TestConnectivesAreNotSceneMarkers:
    @pytest.mark.parametrize("lede", CONNECTIVE_LEDES)
    def test_connective_lede_is_not_a_cold_open(self, lede):
        assert _word_count(_first_paragraph(lede)) > 30      # gate is not doing it
        assert check_cold_open(lede)[1] == 0

    @pytest.mark.parametrize("text, expected", [
        ("the second block is already harder than the first", False),
        ("Marcus is already lacing his shoes", True),
        ("the floor empties after the first hour", False),
        ("the crew leaves before the doors open", True),
        ("shorter than the block before it", False),
        ("out on the street before dawn", True),
        ("until the rep is done", False),
        ("until the lights come on", True),
        ("before anyone has to be told", False),
        ("before anyone else is through the door", True),
    ])
    def test_scene_moment_test_directly(self, text, expected):
        assert prohiblint._has_scene_moment(text) is expected

    def test_a_bare_already_is_not_a_moment(self):
        """Named directly: "already" plus a participle is a body caught
        mid-action, "already" alone is an adverb."""
        assert prohiblint._SCENE_MOMENT_RE.search("is already harder") is None
        assert prohiblint._SCENE_MOMENT_RE.search("is already lacing") is not None


# ===========================================================================
# Defect 13 — cold-open misses: surname, plural, second sentence
# ===========================================================================
#
# The subject rule demanded a BARE first name, so one surname evaded the whole
# check. The tension it was solving for is real — "Jade Kim orders the same
# thing every Tuesday" is legitimate People-register copy — but the surname was
# never the signal. The frame is: a scene happens once at a moment the copy
# points to, a report describes a habit or attributes it to a source.

class TestSurnameIsNotAnEscapeHatch:
    def test_full_name_cold_open_is_caught(self):
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes before dawn.") is True

    def test_the_bare_first_name_form_is_still_caught(self):
        assert _matches_cold_open_pattern(
            "Maya laces her shoes before dawn.") is True

    def test_reported_people_copy_is_still_clean(self):
        """The Handbook's own People-register reference sentence (Sec. 5.2)."""
        assert _matches_cold_open_pattern(
            "Jade Kim orders the same thing every Tuesday: the black sesame "
            "smoothie and a side of turkey avocado toast.") is False

    def test_the_habit_is_what_clears_it_not_the_surname(self):
        """Same subject, same verb, both with a surname. Only the frame
        differs, and the frame is the whole rule."""
        scene = "Maya Okonkwo laces her shoes before dawn."
        habit = "Maya Okonkwo laces her shoes before dawn every Tuesday."
        assert _matches_cold_open_pattern(scene) is True
        assert _matches_cold_open_pattern(habit) is False

    def test_attributed_speech_is_not_a_scene(self):
        """A reporting verb in the subject's own predicate is attribution, not
        motion, however much motion the rest of the sentence carries."""
        assert _matches_cold_open_pattern(
            "Marcus Webb says he laces up before dawn and takes the hill twice."
        ) is False

    def test_a_bare_says_elsewhere_does_not_excuse_a_scene(self):
        """The other side of it: the reporting verb has to be the SUBJECT's
        verb. Vetoing on "says" anywhere cost a genuine cold-open."""
        assert _matches_cold_open_pattern(
            "The Nakamura sisters lace up in the dark before the doors open, "
            "and neither of them says a word about it.") is True


class TestPluralAndLateColdOpens:
    def test_a_family_plural_subject_is_caught(self):
        """A plural subject takes a plural verb, so the singular -s morphology
        that carries every other subject cannot see it."""
        assert _matches_cold_open_pattern(
            "The Nakamura sisters lace up in the dark before the doors open.") is True

    def test_a_plural_progressive_is_caught(self):
        assert _matches_cold_open_pattern(
            "The Okonkwo twins are already lacing up when the crew arrives.") is True

    def test_the_plural_rule_needs_a_family_not_any_plural(self):
        assert _matches_cold_open_pattern(
            "The Ballard racks fill up before the doors open.") is False

    def test_a_scene_in_the_second_sentence_is_caught(self):
        """A cold-open does not have to be one sentence. Anchoring on the
        paragraph let one line of throat clear the whole check.

        The first sentence names a venue, so the unattributed-scene branch is
        structurally unable to fire here — only the person rule can."""
        text = ("Rainier Barbell opens at five on weekdays. Marcus reaches for his "
                "shoes before the sun is up and takes the stairs down two at a time.")
        assert prohiblint._has_proper_noun(_first_paragraph(text)) is True
        assert _cold_open_rule(text) == "person"
        assert check_cold_open(text)[1] == -15

    def test_an_unrelated_sentence_does_not_switch_the_rule_off(self):
        """"opens at five on weekdays" is a venue's hours, not the subject's
        habit. Reading the reported frame across the whole opening made it one,
        which is a one-sentence bypass anyone could write."""
        assert prohiblint._is_reported("Rainier Barbell opens at five on weekdays.") is False

    def test_a_habit_in_the_next_sentence_does_clear_it(self):
        """The frame belongs to the subject's clause or the one elaborating
        it."""
        assert _matches_cold_open_pattern(
            "Marcus laces his shoes before dawn. He does this every morning."
        ) is False


class TestNonEnglishNamesAreNames:
    @pytest.mark.parametrize("name", ["Ayşe", "Xiulan", "José", "Ana-María", "Zoë"])
    def test_a_name_is_read_from_the_token_not_from_ascii(self, name):
        """[A-Z][a-z]+ is an ASCII test that quietly says Ayşe is not a name.
        Before the fix these were only caught by the unattributed-scene branch,
        which switches off the moment the copy names anything at all."""
        assert _matches_cold_open_pattern(
            f"{name} laces her shoes before dawn.") is True

    def test_caught_even_when_the_branch_cannot_fire(self):
        text = ("Rainier Barbell opens at five. Ayşe laces her shoes before dawn "
                "and takes the stairs down two at a time on her way out.")
        assert prohiblint._has_proper_noun(_first_paragraph(text)) is True
        assert _cold_open_rule(text) == "person"


class TestAdverbDoesNotEvadeTheSubjectRule:
    @pytest.mark.parametrize("lede", [
        "Maya laces her shoes before dawn.",
        "Maya quietly laces her shoes before dawn.",
        "Maya slowly laces her shoes before dawn.",
        "Maya still laces her shoes before dawn.",
    ])
    def test_an_adverb_between_name_and_verb_is_not_a_way_out(self, lede):
        """One word between the subject and its verb used to evade the whole
        rule. The progressive arm already allowed the adverb slot; the bare-verb
        arm did not."""
        assert _matches_cold_open_pattern(lede) is True

    def test_the_adverb_slot_does_not_swallow_a_copula(self):
        """It is still the VERB that has to be an action: an adverb in front of
        a copula changes nothing."""
        assert _matches_cold_open_pattern(
            "Victrola quietly is her favourite counter before the doors open.") is False


# ===========================================================================
# Defect 15 — the habitual frame was a one-phrase cold-open bypass
# ===========================================================================
#
# The fix for Defect 13 vetoed the person rule whenever a habitual frame
# appeared anywhere in the sentence. That traded one bad binary for another, and
# the new one was cheaper to trigger: appending "the way she always does" to any
# staged scene switched the check off, and a fiction writer produces that
# texture without being told to. It also cost a genuine catch, on a sentence
# whose habitual phrase modifies a DOOR rather than the subject.
#
# The replacement weighs two signals instead of vetoing on one — see the block
# comment above _CLAUSE_BREAK_RE. Each pair below is the SAME scene with and
# without a habitual tag, so a regression to any veto shows up as the second
# half of a pair going quiet while the first half still flags.

TAGGED_SCENE_PAIRS = [
    ("Priya chalks her hands and steps onto the platform, rolling her "
     "shoulders twice.",
     "Priya chalks her hands and steps onto the platform, rolling her "
     "shoulders twice the way she always does."),

    ("Marcus pushes through the door with his bag on one shoulder and drops "
     "it by the rack.",
     "Marcus pushes through the door with his bag on one shoulder every "
     "morning and drops it by the rack."),

    ("Jenna wraps her hands and leans against the cold wall, counting down "
     "from ten.",
     "Jenna wraps her hands and leans against the cold wall, counting down "
     "from ten as she does most days."),
]


class TestAHabitualTagDoesNotClearAStagedScene:
    @pytest.mark.parametrize("scene, tagged", TAGGED_SCENE_PAIRS)
    def test_both_halves_of_the_pair_flag(self, scene, tagged):
        assert _matches_cold_open_pattern(scene) is True
        assert _matches_cold_open_pattern(tagged) is True

    @pytest.mark.parametrize("scene, tagged", TAGGED_SCENE_PAIRS)
    def test_and_both_cost_the_same_through_the_public_api(self, scene, tagged):
        assert check_cold_open(scene)[1] == -15
        assert check_cold_open(tagged)[1] == -15

    @pytest.mark.parametrize("tail", [
        "the way she always does",
        "as she does most days",
        "every single morning",
        "the way she always has",
        "most mornings",
    ])
    def test_no_single_appended_phrase_turns_the_check_off(self, tail):
        """The shape of the bypass, generalised: one phrase must not decide the
        verdict, whichever phrase it is."""
        scene = ("Priya chalks her hands and steps onto the platform, rolling "
                 "her shoulders twice")
        assert _matches_cold_open_pattern(f"{scene}.") is True
        assert _matches_cold_open_pattern(f"{scene} {tail}.") is True

    def test_a_following_habit_sentence_does_not_clear_a_thick_scene(self):
        """The other half of the same bypass: a whole habitual SENTENCE after
        the scene. Compare TestPluralAndLateColdOpens, where the same move does
        clear a one-beat scene — the difference is the weight of the scene, not
        the presence of the sentence."""
        assert _matches_cold_open_pattern(
            "Priya chalks her hands and steps onto the platform. She does this "
            "every morning.") is True


class TestAFrameMustGovernTheSubjectsOwnClause:
    def test_a_date_about_a_door_is_not_the_subjects_habit(self):
        """The regression this fix restores. "since November" modifies the
        DOOR, inside a subordinate clause, and vetoing on it hid the scene."""
        assert _matches_cold_open_pattern(
            "Marcus laces his shoes in the stairwell because the lobby is cold "
            "and the door has not been fixed since November, and he counts the "
            "flights on the way down.") is True

    def test_dropping_the_date_changes_nothing(self):
        """Proves the date was the only thing standing between the checker and
        the catch — same sentence, same verdict, with and without it."""
        assert _matches_cold_open_pattern(
            "Marcus laces his shoes in the stairwell because the lobby is cold "
            "and the door has not been fixed, and he counts the flights on the "
            "way down.") is True

    def test_a_habit_about_something_else_entirely_does_not_clear_it(self):
        """A following sentence about an ELEVATOR is not the subject's habit,
        however many dates it carries."""
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes before dawn. The building is quiet "
            "and the elevator has not worked since November.") is True

    # Each of the three below is a ONE-beat scene, so the weight signal cannot
    # rescue it, and carries no comma, so the punctuation break cannot either.
    # Exactly one arm of the rule decides each — found by mutation testing,
    # which showed all three arms were unpinned by the tests above.

    def test_an_unpunctuated_the_way_tag_is_still_an_adjunct(self):
        """Isolates the "the way" arm of _CLAUSE_BREAK_RE. Without it the
        cheapest form of the original bypass survives on a thin scene."""
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes before dawn the way she always "
            "does.") is True

    def test_a_coordinated_clause_with_a_new_subject_is_a_new_clause(self):
        """Isolates the "and the ..." arm. Same defect as Finding 2's
        subordinate clause, reached by coordination instead: the date belongs
        to an ELEVATOR."""
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes before dawn and the elevator has not "
            "worked since November.") is True

    def test_a_following_sentence_about_something_else_is_not_the_subjects_habit(self):
        """Isolates _continues_the_subject. The habitual frame governs the main
        clause of the next sentence — but that sentence is about an elevator,
        so it is not evidence about the person at all."""
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes before dawn. The elevator has not "
            "worked since November.") is True
        assert prohiblint._continues_the_subject(
            "The elevator has not worked since November.", ["Maya", "Okonkwo"]
        ) is False
        assert prohiblint._continues_the_subject(
            "She has not missed a Tuesday since November.", ["Maya", "Okonkwo"]
        ) is True

    def test_the_main_clause_is_what_the_frame_has_to_govern(self):
        """Isolates _main_clause: the habitual phrase is identical in both, and
        only its position differs."""
        assert prohiblint._main_clause(
            "Marcus laces his shoes in the stairwell because the door has not "
            "been fixed since November") == "Marcus laces his shoes in the stairwell"
        assert prohiblint._main_clause(
            "Jade Kim orders the same thing every Tuesday: the black sesame "
            "smoothie") == "Jade Kim orders the same thing every Tuesday"


class TestSurnameHoldsInParagraphFormToo:
    """Finding 3: the surname fix was only half true — the sentence flagged in
    isolation and went quiet the moment it was surrounded by realistic prose."""

    MAYA_PARAGRAPHS = [
        "Maya Okonkwo laces her shoes before dawn, the way she always does, "
        "and takes the stairs down two at a time.",

        "Maya Okonkwo laces her shoes before dawn. The building is quiet and "
        "the elevator has not worked since November.",

        "Maya Okonkwo laces her shoes before dawn. Most days she is out the "
        "door before the buses start running on Twelfth.",

        "Maya Okonkwo laces her shoes before dawn and pulls the door shut "
        "behind her, the same way she has for the past two years.",

        "Maya Okonkwo laces her shoes before dawn, checks the weather on her "
        "phone, and steps out into the cold the way she always does.",

        "Maya Okonkwo laces her shoes before dawn in the stairwell because the "
        "lobby light has been broken since November, and she counts the "
        "flights on the way down.",
    ]

    def test_the_isolated_sentence_still_flags(self):
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes before dawn.") is True

    @pytest.mark.parametrize("para", MAYA_PARAGRAPHS)
    def test_and_so_does_the_paragraph_form(self, para):
        assert _matches_cold_open_pattern(para) is True

    @pytest.mark.parametrize("para", MAYA_PARAGRAPHS)
    def test_and_it_costs_the_full_penalty(self, para):
        assert check_cold_open(para)[1] == -15


class TestTheReportedRegisterIsStillClean:
    """The other side of the ledger. Widening the rule this far is only worth
    anything if the People register it exists to protect stays untouched."""

    REPORTED = [
        "Jade Kim orders the same thing every Tuesday: the black sesame "
        "smoothie and a side of turkey avocado toast.",
        "Jade Kim takes the same table every Tuesday and reads until the "
        "counter clears.",
        "Marcus Webb says he laces up before dawn and takes the hill twice.",
        "Priya Raman has been coming to the six a.m. class since January.",
        "Maya Okonkwo laces her shoes before dawn every Tuesday.",
        "Marcus laces his shoes before dawn. He does this every morning.",
    ]

    @pytest.mark.parametrize("text", REPORTED)
    def test_reported_copy_is_not_a_cold_open(self, text):
        assert _matches_cold_open_pattern(text) is False

    @pytest.mark.parametrize("text", REPORTED)
    def test_and_costs_nothing_through_the_public_api(self, text):
        para = text + (" The rest of the profile stays with the person rather "
                       "than the moment, which is what the register is for.")
        assert check_cold_open(para)[1] == 0


class TestBothSignalsCarryWeight:
    """Neither signal may be sufficient alone — that is the whole point of
    replacing a veto with a weighing. Each test here is built so that exactly
    one of the two decides it."""

    def test_scope_alone_catches_a_tag_outside_the_main_clause(self):
        """Two beats, but the tag is after a comma: scope decides."""
        text = ("Jenna wraps her hands and leans against the cold wall, "
                "counting down from ten as she does most days.")
        assert prohiblint._HABITUAL_FRAME_RE.search(text)          # frame present
        assert not prohiblint._HABITUAL_FRAME_RE.search(
            prohiblint._main_clause(text))                         # but not governing
        assert _matches_cold_open_pattern(text) is True

    def test_weight_alone_catches_a_tag_inside_the_main_clause(self):
        """No punctuation to cut on, so scope cannot see it — the beat count
        is the only thing left."""
        text = ("Marcus pushes through the door with his bag on one shoulder "
                "every morning and drops it by the rack.")
        assert prohiblint._HABITUAL_FRAME_RE.search(prohiblint._main_clause(text))
        assert prohiblint._scene_beats(text) >= prohiblint.SCENE_BEATS_OUTWEIGH_FRAME
        assert _matches_cold_open_pattern(text) is True

    def test_a_determiner_marks_a_beat_word_as_a_noun(self):
        """"rolling her shoulders" is one beat, not two: the second is a body
        part. Without this guard the count inflates and inflated counts are
        false positives."""
        assert prohiblint._scene_beats("rolling her shoulders twice") == 1
        assert prohiblint._scene_beats("shoulders the bar and rolls it back") == 2

    def test_the_beat_threshold_is_forced_not_tuned(self):
        """A threshold of 3 would miss the two-beat Marcus case; a threshold of
        1 would flag the one-beat People sentence. Two is the only value that
        satisfies both, which is why it is not a knob."""
        assert prohiblint.SCENE_BEATS_OUTWEIGH_FRAME == 2
        assert prohiblint._scene_beats(
            "Marcus pushes through the door with his bag on one shoulder "
            "every morning and drops it by the rack.") == 2
        assert prohiblint._scene_beats(
            "Maya Okonkwo laces her shoes before dawn every Tuesday.") == 1

    def test_the_beat_list_is_evidence_and_never_a_gate(self):
        """A scene with no habitual frame at all flags on verbs the beat list
        has never heard of — so a missing verb costs a catch only in the narrow
        override case, and can never cause a false positive."""
        assert prohiblint._scene_beats(
            "Priya unbuckles her belt and fidgets with the strap.") == 0
        assert _matches_cold_open_pattern(
            "Priya unbuckles her belt and fidgets with the strap before the "
            "doors open.") is True


class TestOneBeatHabitClauseIsTheKnownLimit:
    """The limitation, pinned rather than hidden.

    A ONE-beat scene whose habitual frame genuinely governs the subject's main
    clause is not separable from a reported habit by scope or by weight — the
    two have the same shape, and one of them is the Handbook's own People
    reference sentence. These MISS, on purpose. Separating them needs discourse
    structure (does the paragraph sustain the moment or move on from it?) or a
    dependency parse, neither of which this module has.

    If a future signal makes the split possible, these are the cases to flip.
    """

    KNOWN_MISSES = [
        "Maya Okonkwo laces her shoes before dawn every Tuesday.",
        "Maya Okonkwo laces her shoes before dawn every morning and takes the "
        "stairs down two at a time to the street.",
        "Maya Okonkwo laces her shoes before dawn. She never misses a Tuesday.",
        "Marcus laces his shoes before dawn. He does this every morning.",
    ]

    @pytest.mark.parametrize("text", KNOWN_MISSES)
    def test_documented_miss(self, text):
        assert _matches_cold_open_pattern(text) is False

    @pytest.mark.parametrize("text", KNOWN_MISSES)
    def test_and_the_scene_really_is_one_beat(self, text):
        """The limit is the thinness of the scene, not the phrase that clears
        it. Add a second beat and every one of these flags."""
        assert prohiblint._scene_beats(text) < prohiblint.SCENE_BEATS_OUTWEIGH_FRAME

    def test_a_second_beat_is_all_it_takes_to_flip_them(self):
        assert _matches_cold_open_pattern(
            "Maya Okonkwo laces her shoes and pulls the door shut before dawn "
            "every Tuesday.") is True


# ===========================================================================
# Defect 14 — a VENUE name was being read as a person in motion
# ===========================================================================
#
# Found by comparing this module's SEATTLE_PLACE_NAMES against voicelint's place
# list. They disagree almost completely, and the disagreement is not a bug in
# either: SEATTLE_PLACE_NAMES holds NEIGHBOURHOODS, which is what the location
# anchors need; voicelint's holds INSTITUTION words, which is what separating an
# org from a person needs. ProhibLint's cold-open subject test needed the second
# kind and only had the first, so ordinary Location-Features copy scored -15.

VENUE_SUBJECT_LEDES = [
    "Iron Works opens its doors before dawn and the first crew is inside by five.",
    "Fuel House opens its doors before the sun is up on Eastlake most mornings.",
    "Bluebird Provisions fills up before the doors open on Broadway.",
    "Cascade Athletic Club racks its bars before the doors open.",
    "Navy Strength pours its first drink before the crowd arrives.",
]


class TestAVenueIsNotAPersonInMotion:
    @pytest.mark.parametrize("lede", VENUE_SUBJECT_LEDES)
    def test_a_venue_subject_is_not_a_cold_open(self, lede):
        assert _matches_cold_open_pattern(lede) is False

    @pytest.mark.parametrize("lede", VENUE_SUBJECT_LEDES)
    def test_and_it_costs_nothing_through_the_public_api(self, lede):
        para = lede + (" The rest of the entry gives the address, the hours and "
                       "what to order once you are actually through the door.")
        assert check_cold_open(para)[1] == 0

    @pytest.mark.parametrize("name", ["Marcus Park", "Jade Field", "Ana House", "Tom Bell"])
    def test_a_surname_that_collides_with_a_venue_word_still_works(self, name):
        """Park, Field, House and Bell are venue words AND real surnames. The
        override is a human pronoun in the same sentence: "Marcus Park laces HIS
        shoes" is a person, "Fuel House opens ITS doors" is not."""
        assert _matches_cold_open_pattern(f"{name} laces his shoes before dawn.") is True

    def test_the_pronoun_is_what_does_it(self):
        """Same subject, same verb, same scene marker — only the pronoun
        differs, and that is the whole distinction."""
        assert _matches_cold_open_pattern("Ana House laces her shoes before dawn.") is True
        assert _matches_cold_open_pattern("Ana House opens its doors before dawn.") is False

    def test_the_two_modules_place_lists_are_answering_different_questions(self):
        """Documents the disagreement rather than papering over it: these are
        NEIGHBOURHOODS, and they are deliberately not institution words."""
        assert "Ballard" in prohiblint._PLACE_TOKENS       # a neighbourhood
        assert "Works" not in prohiblint._PLACE_TOKENS     # an institution word
        assert "Works" in prohiblint._ORG_TOKENS           # ... handled here


# ===========================================================================
# Defect 12 — the em-dash rule was implemented against the wrong unit
# ===========================================================================
#
# PRINCIPLES.txt Sec. 7 reads "One em-dash aside per sentence, never stacked."
# The governed unit is the ASIDE. check_em_dash_workout_series counted DASH
# CHARACTERS and hard-failed any sentence holding two or more, so a single
# correctly punctuated bracketed aside — a matched pair around one phrase, the
# more careful of the two aside forms — was reported as "stacked".
#
# It was not a hypothetical. It hard-failed `anchor_cafe` twice: owner-approved
# shipping copy from Canva DAHQoZJm12w, passed=False, score=80.
#
# The rule now counts asides: dashes pair off left to right, a leftover odd
# dash opens a trailing aside, so asides = ceil(dashes / 2) and two asides in
# one sentence is the stack. In dash terms 1 and 2 are legal, 3 and up are not.

LOCKS_PATH = os.path.join(os.path.dirname(__file__), os.pardir,
                          "charlint", "locks_seattle_series.json")


def _load_locks():
    """
    The real, owner-approved lock file — not a copy, not a fixture.

    A missing file is a hard failure, never a skip: the whole point of this
    block is that it cannot be quietly stopped from running.
    """
    assert os.path.exists(LOCKS_PATH), (
        f"The approved-baseline regression needs the real locks file at "
        f"{LOCKS_PATH}. It is not optional and this test must not be skipped."
    )
    with open(LOCKS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


APPROVED_SLOTS = sorted(_load_locks()["slots"])


class TestApprovedBaselinesAreNeverFlagged:
    """
    THE ACCEPTANCE TEST. Every slot in the real locks file is owner-approved,
    shipping copy. A prose rule that rejects the product's own approved copy is
    wrong about the rule, not about the copy — so this reads the live file and
    checks the actual baselines, and it is parametrized per slot so a failure
    names the slot it broke.
    """

    def test_the_locks_file_still_holds_all_seven_slots(self):
        """Guards the parametrization itself: if the lock file were trimmed,
        every test below would pass by having nothing to check."""
        assert len(APPROVED_SLOTS) == 7
        assert APPROVED_SLOTS == [
            "anchor_cafe", "anchor_venue", "city_intro", "counter_cafe",
            "counter_venue", "cover_body", "night_page",
        ]

    def test_the_baselines_really_do_carry_em_dashes(self):
        """And guards the point of the acceptance test: these baselines have
        to contain the punctuation under test, or passing means nothing.
        anchor_cafe carries six, two of them a bracketed pair."""
        slots = _load_locks()["slots"]
        assert sum(s["baseline"].count(EM) for s in slots.values()) >= 15
        assert slots["anchor_cafe"]["baseline"].count(EM) == 6

    @pytest.mark.parametrize("slot", APPROVED_SLOTS)
    def test_em_dash_check_flags_no_approved_baseline(self, slot):
        text = _load_locks()["slots"][slot]["baseline"]
        v, penalty, hard_fail = check_em_dash_workout_series(text)
        assert v == [], f"{slot} was flagged: {v}"
        assert penalty == 0
        assert hard_fail is False

    @pytest.mark.parametrize("slot", APPROVED_SLOTS)
    def test_second_person_check_flags_no_approved_baseline(self, slot):
        """Defect 2. `anchor_venue` took -3 for "shakes you can pre-order",
        which is description, not coaching — and the ban it was taking the
        penalty from is the magazine Handbook's, not PRINCIPLES.txt's."""
        text = _load_locks()["slots"][slot]["baseline"]
        v, penalty, _ = check_second_person(text, ruleset="workout_series")
        assert v == [], f"{slot} was flagged: {v}"
        assert penalty == 0

    @pytest.mark.parametrize("slot", APPROVED_SLOTS)
    def test_the_magazine_ruleset_is_deliberately_unchanged(self, slot):
        """The same copy under the magazine rulebook still fails on em-dashes.
        The fix is scoped to workout_series; it did not loosen the Handbook."""
        text = _load_locks()["slots"][slot]["baseline"]
        assert check_em_dash(text)[2] is True


# ---------------------------------------------------------------------------
# The counting rule, stated as a table
# ---------------------------------------------------------------------------

def sentence_with(dashes):
    """One sentence carrying exactly `dashes` spaced em-dashes."""
    parts = ["The room is loud"] + ["cold"] * dashes
    return f" {EM} ".join(parts) + "."


class TestEmDashAsideIsTheUnit:
    @pytest.mark.parametrize("dashes, asides", [
        (0, 0),   # no aside
        (1, 1),   # trailing aside
        (2, 1),   # ONE bracketed aside — the defect
        (3, 2),   # bracketed pair + trailing aside
        (4, 2),   # two bracketed pairs
        (5, 3),
        (6, 3),
    ])
    def test_dashes_to_asides(self, dashes, asides):
        assert prohiblint._count_asides(sentence_with(dashes)) == asides

    @pytest.mark.parametrize("dashes", [0, 1, 2])
    def test_one_aside_or_fewer_is_legal(self, dashes):
        v, penalty, hard_fail = check_em_dash_workout_series(sentence_with(dashes))
        assert (v, penalty, hard_fail) == ([], 0, False)

    @pytest.mark.parametrize("dashes", [3, 4, 5, 6, 7, 8])
    def test_two_asides_or_more_is_stacked(self, dashes):
        v, penalty, hard_fail = check_em_dash_workout_series(sentence_with(dashes))
        assert hard_fail is True
        assert penalty == -10
        assert len(v) == 1

    def test_the_violation_message_counts_asides_not_dashes(self):
        v, _, _ = check_em_dash_workout_series(sentence_with(4))
        assert "2 asides (4 em-dashes)" in v[0]

    def test_the_penalty_is_per_sentence_not_per_dash(self):
        """Unchanged from before the fix and pinned on purpose: eight dashes in
        one sentence is one -10, not one per dash."""
        assert check_em_dash_workout_series(sentence_with(8))[1] == -10


# ---------------------------------------------------------------------------
# The live copy that started it
# ---------------------------------------------------------------------------

ANCHOR_CAFE_ASIDES = [
    # A bracketed pair around a walking route: one aside.
    ("Ten flat minutes from the red room " + EM + " east on Denny, left on Yale "
     + EM + " Espresso Vivace anchors the Alley24 courtyard across from the REI "
     "flagship."),
    # A bracketed pair around a tasting note, inside a colon-led clause: one aside.
    ("This is the grand bar of David Schomer, the man who taught American espresso "
     "its manners: the heart pour was his signature by 1989, the rosetta followed "
     "in '92, and the roast has run Northern Italian " + EM + " sweet caramel, "
     "never burnt " + EM + " since 1992."),
    # A single trailing aside.
    ("Cards only, doors at 6am weekdays " + EM + " early enough to beat your own "
     "class to the line."),
]


class TestTheShippingSentencesThatWereRejected:
    @pytest.mark.parametrize("sentence", ANCHOR_CAFE_ASIDES)
    def test_each_is_one_aside_and_passes(self, sentence):
        assert prohiblint._count_asides(sentence) == 1
        assert check_em_dash_workout_series(sentence) == ([], 0, False)

    def test_adding_one_more_aside_to_the_real_sentence_is_caught(self):
        """Mutation: the same approved sentence with a trailing aside welded on
        is genuinely stacked, and is caught. Passing the baselines is not the
        same as passing everything."""
        stacked = ANCHOR_CAFE_ASIDES[0][:-1] + f" {EM} ten minutes, no more."
        v, penalty, hard_fail = check_em_dash_workout_series(stacked)
        assert hard_fail is True
        assert penalty == -10


# ---------------------------------------------------------------------------
# The ambiguous cases, each decided and each pinned
# ---------------------------------------------------------------------------

class TestAmbiguousDashCases:
    def test_a_range_dash_between_digits_is_not_an_aside(self):
        """"the class runs 5—9" joins two numbers; it does not interrupt the
        sentence. Counting it turned one aside plus a range into a false
        stack."""
        text = (f"The class runs 5{EM}9 and the roast {EM} sweet caramel, never "
                f"burnt {EM} is Northern Italian.")
        assert prohiblint._aside_dash_count(text) == 2
        assert check_em_dash_workout_series(text) == ([], 0, False)

    def test_a_range_dash_cannot_hide_a_real_stack(self):
        """The exemption only ever removes non-asides. Three real asides around
        a range are still three asides."""
        text = (f"Open 5{EM}9, the room {EM} loud {EM} is warm {EM} always, and "
                f"the coffee {EM} hot {EM} is good.")
        assert check_em_dash_workout_series(text)[2] is True

    def test_a_closed_up_aside_is_still_an_aside(self):
        """US house style sets aside dashes closed. Exempting word—word would
        excuse the entire closed-up style, so only digit—digit is a range."""
        text = f"The bar{EM}loud, cheap{EM}is grand{EM}always."
        assert prohiblint._aside_dash_count(text) == 3
        assert check_em_dash_workout_series(text)[2] is True

    def test_an_en_dash_is_not_counted_at_all(self):
        """The baselines' "45–60 minutes" and "Olson Kundig–designed" are en
        dashes (U+2013). Sec. 7 governs the em-dash aside only."""
        text = ("Power vinyasa, hatha, and yin run daily, 45–60 minutes — "
                "an Olson Kundig–designed room.")
        assert prohiblint._aside_dash_count(text) == 1
        assert check_em_dash_workout_series(text) == ([], 0, False)

    def test_a_sentence_that_opens_on_a_dash_is_one_aside(self):
        """Pairing is positional, so a leading dash needs no special case."""
        text = f"{EM} east on Denny, left on Yale {EM} Vivace anchors the courtyard."
        assert prohiblint._count_asides(text) == 1
        assert check_em_dash_workout_series(text) == ([], 0, False)

    # The clause after the mark is CAPITALISED in both tests below, and that is
    # the whole point of them. _sentence_spans already refuses to break before a
    # lowercase word, so "…is grand; the cafe…" would survive a semicolon-splits
    # mutation for the wrong reason. A proper noun after the mark — ordinary
    # Seattle Series copy — is where the decision actually bites.

    def test_a_semicolon_does_not_start_a_new_sentence(self):
        """Sec. 7 says "per sentence" and a semicolon joins clauses into one.
        If it reset the count, stacking would be legal for the price of one
        semicolon."""
        text = f"The bar {EM} loud {EM} is grand; Victrola {EM} small {EM} is quiet."
        assert len(prohiblint._aside_units(text)) == 1
        assert check_em_dash_workout_series(text)[2] is True

    def test_a_colon_does_not_start_a_new_sentence_either(self):
        text = f"The room runs on two things {EM} lights {EM} and noise: Vivace {EM} always."
        assert len(prohiblint._aside_units(text)) == 1
        assert check_em_dash_workout_series(text)[2] is True

    def test_the_lowercase_case_is_covered_by_the_splitter_not_by_luck(self):
        """Companion to the two above: a lowercase continuation is held by
        _sentence_spans' opener test, so both spellings of the same sentence
        get the same verdict."""
        lower = f"The bar {EM} loud {EM} is grand; the cafe {EM} small {EM} is quiet."
        upper = f"The bar {EM} loud {EM} is grand; Victrola {EM} small {EM} is quiet."
        assert len(prohiblint._aside_units(lower)) == len(prohiblint._aside_units(upper)) == 1

    def test_a_hard_line_break_ends_a_unit(self):
        """These checks read whole Canva text elements. `night_page` is a title
        line, a location rule, a blank line, then prose — and the title has no
        terminal period, so without this its dashes would merge into the first
        prose sentence and stack a phantom."""
        text = f"The Night Off {EM} Cascade\nSome nights the smartest recovery {EM} a night off {EM} wins."
        assert len(prohiblint._aside_units(text)) == 2
        assert check_em_dash_workout_series(text) == ([], 0, False)

    def test_the_line_break_does_not_excuse_a_stack_on_one_line(self):
        text = f"The Night Off\nThe bar {EM} loud {EM} is grand {EM} always."
        assert check_em_dash_workout_series(text)[2] is True

    def test_night_page_shape_end_to_end(self):
        """The real multi-line element, in its real shape."""
        text = _load_locks()["slots"]["night_page"]["baseline"]
        assert "\n" in text
        assert text.count(EM) == 3          # three sentences, one aside each
        assert check_em_dash_workout_series(text) == ([], 0, False)


# ---------------------------------------------------------------------------
# Defect 2 — second person under workout_series
# ---------------------------------------------------------------------------
#
# The magazine Handbook Sec. 6 bans the "second-person wellness coaching
# register". PRINCIPLES.txt, which governs the Workout Series, does the
# opposite: Sec. 7 prescribes "Tiered direct address when segmenting readers",
# Sec. 6 makes "reader autonomy (you decide where you land)" one of six core
# beliefs, and Sec. 6 words another of them "none of us has met your body".
# Running the Handbook's list over this copy imports the wrong rulebook.

DESCRIPTIVE_SECOND_PERSON = [
    # The line that took the -3.
    "The Fuel Bar blends post-class shakes you can pre-order before the last interval.",
    # PRINCIPLES Sec. 6, belief 5, verbatim.
    "None of us has met your body.",
    # PRINCIPLES Sec. 7's own parallelism example.
    "Your history, your joints, your limits.",
    # PRINCIPLES Sec. 6, belief 2, verbatim.
    "You decide where you land.",
    # PRINCIPLES Sec. 7's concede-then-redirect example, verbatim.
    "We bring the work, you bring the honesty.",
    "Cards only, doors at 6am weekdays, early enough to beat your own class.",
    "Your workout is on page nine.",
    "If you want to beat the line, come at six.",
]

PRESCRIPTIVE_SECOND_PERSON = [
    "You should start with a warm-up before lifting.",
    "You need to hit every set for this to work.",
    "You must rest ninety seconds between sets.",
    "You have to eat before the session.",
    "You will feel it in the lats by Thursday.",
    "You'll feel it in the lats by Thursday.",
    "Try this on your next session.",
]


class TestSecondPersonUnderWorkoutSeries:
    @pytest.mark.parametrize("line", DESCRIPTIVE_SECOND_PERSON)
    def test_descriptive_second_person_is_house_voice(self, line):
        v, penalty, _ = check_second_person(line, ruleset="workout_series")
        assert (v, penalty) == ([], 0)

    @pytest.mark.parametrize("line", PRESCRIPTIVE_SECOND_PERSON)
    def test_prescriptive_second_person_is_still_flagged(self, line):
        """The check is not switched off — it is aimed at the narrower thing
        PRINCIPLES actually rules out: address that prescribes or predicts."""
        v, penalty, hard_fail = check_second_person(line, ruleset="workout_series")
        assert penalty == -3
        assert len(v) == 1
        assert hard_fail is False

    def test_a_curly_apostrophe_does_not_hide_a_prediction(self):
        assert check_second_person("You’ll feel it by Thursday.",
                                   ruleset="workout_series")[1] == -3

    @pytest.mark.parametrize("line", DESCRIPTIVE_SECOND_PERSON[:1] + PRESCRIPTIVE_SECOND_PERSON[:1])
    def test_the_magazine_ruleset_still_bans_all_of_it(self, line):
        """Scoped fix: the Handbook's outright ban is untouched, and both a
        descriptive and a prescriptive line still cost -3 under magazine."""
        assert check_second_person(line)[1] == -3

    def test_the_default_ruleset_is_still_magazine(self):
        line = DESCRIPTIVE_SECOND_PERSON[0]
        assert check_second_person(line)[1] == -3
        assert check_second_person(line, ruleset="magazine")[1] == -3
        assert check_second_person(line, ruleset="workout_series")[1] == 0

    def test_every_valid_ruleset_has_a_second_person_list(self):
        """A ruleset added to VALID_RULESETS without a list here would raise on
        every section rather than quietly borrowing the Handbook's."""
        assert set(prohiblint._SP_BY_RULESET) == set(VALID_RULESETS)

    def test_an_unknown_ruleset_raises_rather_than_falling_back(self):
        """A typo'd ruleset must not quietly get the other rulebook — that is
        the defect this split exists to fix."""
        with pytest.raises(ValueError):
            check_second_person("You should rest.", ruleset="workout-series")

    def test_sidebars_are_still_exempt_under_workout_series(self):
        text = ("The room runs on low lights and loud music. "
                "[SIDEBAR] You should always consult a coach. [/SIDEBAR]")
        assert check_second_person(text, ruleset="workout_series")[1] == 0

    def test_every_workout_series_pattern_is_a_subset_of_the_magazine_list(self):
        """Except the two spelling variants added for prediction, the
        workout_series list only ever REMOVES from the Handbook's."""
        added = (set(prohiblint.WORKOUT_SERIES_SECOND_PERSON_PATTERNS)
                 - set(prohiblint.SECOND_PERSON_PATTERNS))
        assert added == {"you must", "you have to", "you'll feel"}


class TestSecondPersonThroughTheRunner:
    def test_run_prohiblint_routes_the_ruleset_to_the_second_person_check(self):
        body = ("The Fuel Bar blends post-class shakes you can pre-order before "
                "the last interval. ") + make_text(900, NEUTRAL_FILLER)
        ws = run_prohiblint(neutral_sections(Training=body), ruleset="workout_series")
        mag = run_prohiblint(make_section_dict(Training=body), ruleset="magazine")
        assert not any("Second-person" in v
                       for v in ws["sections"]["Training"]["violations"])
        assert any("Second-person" in v
                   for v in mag["sections"]["Training"]["violations"])

    def test_prescriptive_coaching_still_scores_against_a_workout_series_run(self):
        body = ("You should rest ninety seconds between sets. "
                + make_text(900, NEUTRAL_FILLER))
        ws = run_prohiblint(neutral_sections(Training=body), ruleset="workout_series")
        assert any("Second-person" in v
                   for v in ws["sections"]["Training"]["violations"])
        assert ws["sections"]["Training"]["score"] == 97


class TestApprovedBaselinesThroughTheRunner:
    """Slot text through the public API, the way orchestrator.py feeds it."""

    @pytest.mark.parametrize("slot", APPROVED_SLOTS)
    def test_no_baseline_trips_an_em_dash_or_second_person_violation(self, slot):
        text = _load_locks()["slots"][slot]["baseline"]
        result = run_prohiblint({"Training": text}, ruleset="workout_series")
        offending = [v for v in result["sections"]["Training"]["violations"]
                     if "em-dash" in v or "Second-person" in v]
        assert offending == [], f"{slot}: {offending}"


# ===========================================================================
# Defect 16 — the person veto was a closed cue LIST, and its reported-speech
#             branch could never fire on the tier it mattered on
# ===========================================================================
#
# Two separate faults, one consequence: four PEOPLE with street addresses
# satisfied nutrition_spots_4_places — the strictest tier in the module, on a
# BLOCKING check, the one Handbook Sec. 9 locks.
#
#   (a) _PERSON_CUE_RE enumerated CUES. It held ", 34,", ", who" and a list of
#       reporting verbs, and it therefore had nothing at all to say about the
#       commonest thing a person does after their address: an ordinary verb.
#       "eats", "keeps", "cooks" are on no list and never will be — the class
#       is open. This is the third time this module has shipped an enumerate-
#       an-open-class bug (the cold-open verb list, the habitual-frame veto,
#       this). The action slot is now judged by MORPHOLOGY, with closed lists
#       only for what must be EXCLUDED (copulas, function words, irregular
#       pasts) — all three of which are genuinely closed classes of English.
#
#   (b) The reported-speech branch was written `\s+says`. On the address tier
#       the tail begins at the comma that ends the address, so `, says` could
#       never match it: one character class, and a quoted human walked through
#       a blocking gate. Every branch now takes an optional leading comma.
#
# A third fix sits underneath both: the tail is now read past the NEIGHBOURHOOD
# as well as the street, because "812 Harbor Street, Ballard, eats ..." put a
# capitalised word at the head of the tail where nothing anchored at ^ could
# match.

FOUR_PEOPLE_WITH_STREET_ADDRESSES = (
    "Aisha Coleman, 812 Harbor Street, Ballard, eats the same breakfast daily. "
    "Delphine Okoro, 415 Wendell Avenue, Fremont, says the breakfast never "
    "changes. Marcus Webb, 2201 Cavell Road, Georgetown, keeps his oats in a "
    "jar. Tomas Herrera, 90 Pinegrove Street, Wallingford, cooks at six every "
    "morning."
)


class TestAPersonWithAStreetAddressIsStillAPerson:
    """The bypass end to end, and then each shape of it on its own."""

    def test_four_people_with_addresses_do_not_satisfy_the_nutrition_element(self):
        result = check_mandatory_elements(
            neutral_sections(Nutrition=FOUR_PEOPLE_WITH_STREET_ADDRESSES))
        assert result["element_results"]["nutrition_spots_4_places"] is False

    def test_the_strict_tier_accepts_none_of_their_names(self):
        assert prohiblint._located_venue_names(
            FOUR_PEOPLE_WITH_STREET_ADDRESSES, require_address=True) == set()

    @pytest.mark.parametrize("tail", [
        ", eats the same breakfast daily.",     # plain action verb  (was counted)
        ", says the breakfast never changes.",  # comma before the reporting verb
        ", keeps his oats in a jar.",           # action verb, possessive object
        ", who cooks at six.",                  # relative pronoun
        ", 45, still trains at five.",          # age apposition
        ", a chef, works the early service.",   # role apposition
    ])
    def test_every_person_shape_after_an_address_is_vetoed(self, tail):
        assert prohiblint._located_venue_names(
            "Marcus Webb, 2201 Cavell Road" + tail, require_address=True) == set()

    def test_the_reporting_verb_branch_is_reachable_across_a_comma(self):
        """Fault (b) on its own. Both separators, one pattern — before the fix
        the comma form returned None and the address tier only ever produced
        the comma form."""
        assert prohiblint._PERSON_CUE_RE.match(", says the breakfast never changes.")
        assert prohiblint._PERSON_CUE_RE.match(" says the breakfast never changes.")

    def test_the_tail_is_read_past_the_neighbourhood_as_well_as_the_street(self):
        """The tail has to start at the end of the LOCATION, not the end of the
        street. Stopping at "Ballard" leaves a capitalised word in front of
        every ^-anchored test in the module."""
        text = "Aisha Coleman, 812 Harbor Street, Ballard, eats the same breakfast."
        m = prohiblint._LOCATED_PLACE_RE.search(text)
        assert prohiblint._tail_after_anchor(text, m.end()) == \
            ", eats the same breakfast."


class TestWhatAPersonDoesIsAnOpenClass:
    """
    The fault that made the veto a list. These verbs are deliberately chosen to
    be ones nobody would think to enumerate — if the veto is a list again, the
    list will not have them.
    """

    @pytest.mark.parametrize("predicate", [
        "eats the same breakfast daily",
        "keeps his oats in a jar",
        "cooks at six every morning",
        "reheats yesterday's rice",
        "photographs every plate",
        "microwaves the same bowl twice",
        "commutes past it on the way",
        "grumbled about the queue",
        "shelved the whole idea",
        # irregular past, no -s and no -ed: the closed list carries these.
        "went to the counter first",
        "took his coffee outside",
        # irregular past the closed list has NOT heard of. Only the transitive
        # frame — a direct object behind the verb — catches these.
        "outgrew the place two years ago",
        "overspent his weekly budget",
        "misread the opening hours",
    ])
    def test_an_ordinary_verb_after_an_address_reads_as_a_person(self, predicate):
        assert prohiblint._located_venue_names(
            "Marcus Webb, 2201 Cavell Road, Georgetown, " + predicate + ".",
            require_address=True) == set()

    def test_the_verbs_are_on_no_list_anywhere_in_the_module(self):
        """The pin that stops the fix regressing into another enumeration. If
        someone answers a future miss by adding the verb to a set or to an
        alternation, this fails and points them back at the morphology.

        It reads the module's own containers and compiled patterns rather than
        its source text, so prose in a comment is not a false alarm."""
        vocabularies = {}
        for attr, value in vars(prohiblint).items():
            if isinstance(value, (set, frozenset, tuple, list)):
                vocabularies[attr] = {v for v in value if isinstance(v, str)}
            elif isinstance(value, re.Pattern):
                vocabularies[attr] = set(re.findall(r"[a-z]{3,}", value.pattern))
        for verb in ("eats", "keeps", "reheats", "photographs", "microwaves",
                     "commutes", "grumbled", "shelved"):
            for attr, vocabulary in vocabularies.items():
                assert verb not in vocabulary, (
                    f"{verb!r} was enumerated in {attr}. The class of things a "
                    f"person does is open; judge the slot by morphology, not "
                    f"by membership.")

    def test_the_excluded_classes_are_the_closed_ones(self):
        """Copulas, function words, stative pasts and irregular pasts are
        enumerable because English does not acquire new ones. Nothing else may
        be a list."""
        for token in ("is", "has", "been", "would"):
            assert token in prohiblint._COPULA_VERBS
        for token in ("in", "at", "and", "the", "its"):
            assert token in prohiblint._FUNCTION_WORDS
        for token in ("remained", "stayed", "became"):
            assert token in prohiblint._STATIVE_PAST
        for token in ("went", "took", "kept", "wrote"):
            assert token in prohiblint._IRREGULAR_PAST

    def test_the_closed_classes_are_not_re_listed_under_a_second_name(self):
        """The venue check reuses the cold-open check's copula and function-word
        sets. Writing a second module-level binding of the same name silently
        REBINDS the first — the cold-open subject test would have started
        reading the venue test's copy, and nothing in the suite would say so."""
        import ast, collections
        bindings = collections.Counter()
        for node in ast.parse(inspect.getsource(prohiblint)).body:
            if isinstance(node, ast.Assign):
                bindings.update(t.id for t in node.targets
                                if isinstance(t, ast.Name))
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                bindings[node.name] += 1
        assert [n for n, c in bindings.items() if c > 1] == []

    # -- the other direction: an open-class veto must not eat real venues ----

    @pytest.mark.parametrize("text,name", [
        # a venue predicate, which is checked BEFORE the open class — every one
        # of these verbs is third-person -s and would read as a person on
        # morphology alone.
        ("Bluebird Provisions, 123 Broadway E, Capitol Hill, opens at six.",
         "bluebird provisions"),
        ("Fuel House, 456 Eastlake Ave E, South Lake Union, serves lunch daily.",
         "fuel house"),
        ("Green District, 789 Queen Anne Ave N, Queen Anne, roasts its beans.",
         "green district"),
        # "its" — the one inanimate signal in the object frame.
        ("Vantry Coffee Room, 3308 Ombrey Street, Wallingford, makes its own bread.",
         "vantry coffee room"),
        # a copula, an auxiliary or a stative past is a state, not a person.
        ("Ostrey Larder, 617 Harkness Street, Georgetown, has been here two years.",
         "ostrey larder"),
        ("Copper Tavern, 1009 E Pike St, Capitol Hill, is a corner room with stools.",
         "copper tavern"),
        ("Anchor Room, 88 Fairmount Street, Ravenna, remained closed through March.",
         "anchor room"),
        # a function word: the name has not reached a verb at all.
        ("Navy Strength, 400 Bell Street, Belltown, on the corner of two arterials.",
         "navy strength"),
        # a participle is not a finite verb.
        ("Sallowmere Grill, 1122 Draycott Way, Beacon Hill, occupying an old shop.",
         "sallowmere grill"),
        # the tail ends with the address: nothing follows to judge.
        ("Brindlemoor Kitchen, 2140 Fenwold Avenue Northwest, Ballard. "
         "The turkey bowl is 41g protein.", "brindlemoor kitchen"),
    ])
    def test_a_venue_doing_venue_things_still_counts(self, text, name):
        assert name in prohiblint._located_venue_names(text, require_address=True)

    def test_the_real_sample_nutrition_is_untouched_by_the_open_class(self):
        assert prohiblint._located_venue_names(
            real_sample_sections()["Nutrition"], require_address=True) == {
                "bluebird provisions", "fuel house", "green district", "big mario's"}


class TestAJobTitleIsAnOpenClassToo:
    """
    The role apposition in `_PERSON_CUE_RE` is a list of JOBS, and jobs are as
    open a class as verbs — "a dietitian", "a paramedic", "a bartender" are on
    it nowhere, and each of them walked a human through the strict tier.

    The answer is not a longer list. A comma-closed apposition is a
    parenthetical, so it is STEPPED OVER and the predicate on the other side is
    read instead. That decides nothing by itself, which is what makes it safe.
    """

    @pytest.mark.parametrize("apposition,predicate", [
        ("a dietitian", "eats the same breakfast"),
        ("a paramedic", "keeps his oats in a jar"),
        ("a bartender", "says the same thing every week"),
        ("a night-shift charge", "reheats it at four"),
        ("a father of two", "shops on the way home"),
    ])
    def test_an_unlisted_job_title_does_not_hide_the_person(self, apposition,
                                                            predicate):
        assert prohiblint._located_venue_names(
            f"Marcus Webb, 2201 Cavell Road, Georgetown, {apposition}, "
            f"{predicate}.", require_address=True) == set()

    @pytest.mark.parametrize("text,name", [
        # the apposition closes, and what is on the other side is a venue.
        ("Bluebird Provisions, 123 Broadway E, Capitol Hill, a corner cafe, "
         "opens at six.", "bluebird provisions"),
        ("Fuel House, 456 Eastlake Ave E, South Lake Union, a favourite of "
         "runners, serves until three.", "fuel house"),
        # the apposition never closes, so nothing is skipped and nothing is
        # decided — this is what keeps a venue's own description out of it.
        ("Ostrey Larder, 617 Harkness Street, Georgetown, a warehouse-adjacent "
         "room with six long tables.", "ostrey larder"),
        ("Vantry Coffee Room, 3308 Ombrey Street, Wallingford, a counter with "
         "four stools.", "vantry coffee room"),
        # the apposition closes, but it is FIVE words long — past the bound.
        # A wider skip steps over the venue's own description and lands on
        # "draws the six a.m. crowd", which is third-person -s with an object
        # and reads as a person. The bound is what keeps the room a room.
        ("Fuel House, 456 Eastlake Ave E, South Lake Union, a bright room with "
         "good light, draws the six a.m. crowd.", "fuel house"),
    ])
    def test_a_venue_described_in_apposition_still_counts(self, text, name):
        assert name in prohiblint._located_venue_names(text, require_address=True)

    def test_the_closed_role_list_still_covers_the_unclosed_apposition(self):
        """", a chef." never reaches a second comma, so the skip cannot fire and
        the listed role is the only thing left to catch it."""
        assert prohiblint._located_venue_names(
            "Marcus Webb, 2201 Cavell Road, Georgetown, a chef.",
            require_address=True) == set()


class TestAVenueNameStopsAtItsOwnSentenceHereToo:
    """
    The same guard `_PROPER_NAME` carries on its INTERNAL spaces was never
    carried across the join between the name and its type word. So a person
    named at the end of one sentence and a capitalised place-type word opening
    the next were read as one venue — on two blocking elements at once, off
    copy that names no venue at all.
    """

    @pytest.mark.parametrize("text", [
        "She trains at Green Lake with Marcus Webb. Club members meet at six.",
        "The plan came from Aisha Coleman. Studio hours are posted on the door.",
        "He waited for Tomas Herrera. Gym staff opened at five.",
    ])
    def test_a_name_does_not_join_the_next_sentences_type_word(self, text):
        assert prohiblint._distinct_named_places(
            text, prohiblint._TYPED_VENUE_RE) == set()
        assert prohiblint._named_fitness_spots(text) == set()

    def test_real_venues_and_gyms_on_either_side_of_a_full_stop_still_count(self):
        assert prohiblint._distinct_named_places(
            "Copper Tavern is on Pike. Navy Strength opens at five.",
            prohiblint._TYPED_VENUE_RE) == {"copper"}
        assert prohiblint._named_fitness_spots(
            "Rainier Barbell opens at five. Fremont Hot Yoga adds sessions."
        ) == {"rainier barbell", "fremont hot yoga"}


class TestTheTailIsReadToTheEndOfTheLocation:
    """
    Everything between the anchor and the predicate has to be stepped over, or
    the person tests — all anchored at ^ — are reading a street name.
    """

    def test_the_spelled_out_compass_words_are_address_furniture(self):
        """The furniture list had NW but not Northwest, so "Fenwold Avenue
        Northwest" left "Northwest" in front of the tail, and "Avenue Northwest"
        validated as a venue name in its own right."""
        assert prohiblint._validated_name("Avenue Northwest") is None
        assert prohiblint._located_venue_names(
            "Aisha Coleman, 2140 Fenwold Avenue Northwest, Ballard, eats there "
            "on Tuesdays.", require_address=True) == set()

    def test_a_neighbourhood_that_opens_with_a_compass_word_is_not_eaten(self):
        """"South" is address furniture AND the first word of "South Lake
        Union". Read the address first and the neighbourhood is left as "Lake
        Union" — a capitalised word at the head of the tail, where nothing
        anchored at ^ can match, and the person behind it counts as a venue."""
        assert prohiblint._located_venue_names(
            "Marcus Webb, 456 Eastlake Ave E, South Lake Union, eats his oats.",
            require_address=True) == set()
        assert prohiblint._located_venue_names(
            "Fuel House, 456 Eastlake Ave E, South Lake Union, opens at six.",
            require_address=True) == {"fuel house"}

    def test_an_abbreviated_street_suffix_keeps_its_period(self):
        """"Rd." is an abbreviation, not the end of the sentence. Stop on it and
        the tail starts at "Rd., Georgetown, ..." where nothing can match."""
        assert prohiblint._located_venue_names(
            "Marcus Webb, 2201 Cavell Rd., Georgetown, eats his oats at home.",
            require_address=True) == set()

    def test_the_scan_does_not_run_past_the_last_piece_of_the_address(self):
        """A street name can cross a word the scan does not recognise ("789
        Queen Anne Ave N"), so it has to backtrack to the last address word
        rather than swallow every capitalised token it can reach. Here the
        capitalised token after the neighbourhood is the venue's own
        predicate."""
        assert prohiblint._located_venue_names(
            "Navy Strength, Belltown, Bar and bottle shop.") == {"navy strength"}
        assert prohiblint._tail_after_anchor(
            "Green District, 789 Queen Anne Ave N, Queen Anne. Steak bowls.",
            prohiblint._LOCATED_PLACE_RE.search(
                "Green District, 789 Queen Anne Ave N, Queen Anne. Steak bowls."
            ).end()) == ". Steak bowls."


# ===========================================================================
# Defect 17 — require_address=True was unpinned by the entire suite
# ===========================================================================
#
# One parameter enforces Handbook Sec. 9's locked strict tier for the nutrition
# element, and flipping it to False left all 1049 tests green. A blocking check
# whose strictness knob can be silently loosened is not a gate, so the knob
# gets its own tests: one on the parameter, one through the call site that
# passes it.

FOUR_VENUES_WITH_NO_ADDRESS = (
    "Bluebird Provisions, Ballard, opens at six and serves until two. "
    "Fuel House, Fremont, opens at seven and serves until three. "
    "Green District, Georgetown, opens at eight and serves until four. "
    "Copper Tavern, Wallingford, opens at nine and serves until five."
)


class TestTheStrictNutritionTierIsLocked:
    def test_the_parameter_is_the_whole_difference(self):
        """Both sides of the knob, on one sentence. These are real venues doing
        real venue things — the ONLY thing keeping them out of the nutrition
        element is the missing street address."""
        text = "Bluebird Provisions, Ballard, opens at six and serves until two."
        assert prohiblint._located_venue_names(text, require_address=True) == set()
        assert prohiblint._located_venue_names(text, require_address=False) == {
            "bluebird provisions"}

    def test_four_addressless_venues_do_not_satisfy_the_nutrition_element(self):
        """The pin on the CALL SITE. Flip check_mandatory_elements to
        require_address=False and this is the test that goes red: four venues
        become four nutrition spots without a street number between them."""
        result = check_mandatory_elements(
            neutral_sections(Nutrition=FOUR_VENUES_WITH_NO_ADDRESS))
        assert result["element_results"]["nutrition_spots_4_places"] is False
        assert any("found 0 distinct" in v for v in result["violations"])

    def test_the_same_four_venues_pass_once_they_carry_addresses(self):
        """The control on the test above: the sentences are otherwise
        identical, so what it proves is the address requirement and not some
        accident of the copy."""
        nutrition = (
            "Bluebird Provisions, 123 Broadway E, Ballard, opens at six. "
            "Fuel House, 456 Eastlake Ave E, Fremont, opens at seven. "
            "Green District, 789 Pike St, Georgetown, opens at eight. "
            "Copper Tavern, 1009 Draycott Way, Wallingford, opens at nine.")
        result = check_mandatory_elements(neutral_sections(Nutrition=nutrition))
        assert result["element_results"]["nutrition_spots_4_places"] is True

    def test_the_addressless_tier_is_still_open_to_location_features(self):
        """require_address is scoped to the nutrition element. Element 4
        deliberately allows a bare neighbourhood behind the venue predicate, so
        tightening one tier must not silently tighten the other."""
        result = check_mandatory_elements(
            neutral_sections(Nutrition=FOUR_VENUES_WITH_NO_ADDRESS))
        assert result["element_results"]["location_features_3_places"] is True
