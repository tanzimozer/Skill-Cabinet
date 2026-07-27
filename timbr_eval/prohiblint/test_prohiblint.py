"""
test_prohiblint.py — pytest tests for ProhibLint module.
Run with: pytest test_prohiblint.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from prohiblint import (
    check_em_dash,
    check_ai_blocklist,
    check_cold_open,
    check_second_person,
    check_word_count,
    check_mandatory_elements,
    run_prohiblint,
    WORD_COUNT_RANGES,
    SECTIONS,
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
