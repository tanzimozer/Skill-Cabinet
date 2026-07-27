"""
test_voicelint.py — pytest suite for VoiceLint.

Coverage:
  - 3+ known-pass samples per voice register
  - 3+ cross-contamination / known-fail samples
  - Score-range and boundary tests
  - Unknown section handling
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from voicelint import lint_section, lint_sections
import voice_config as cfg

# ═══════════════════════════════════════════════════════════════════════════════
# Sample texts — The Athletic (Training / Culture)
# ═══════════════════════════════════════════════════════════════════════════════

ATHLETIC_PASS_1 = """
Marcus Webb, 34, a strength coach at Seattle Athletic Club, has spent the last
six years rethinking how professional athletes approach the final 400 metres.

At Husky Stadium, before the Tuesday session begins, he explains the philosophy
in a single sentence. Short. Efficient.

"The body knows," he says. "You just have to stop lying to it."

Webb notes that sprint intervals dropped his athletes' recovery time by 18%.
The data, he argues, is harder to ignore than any motivational speech.
""".strip()

ATHLETIC_PASS_2 = """
In Capitol Hill, the conversation about periodisation has finally reached the
mainstream fitness floor.

Priya Nair, 29, head of performance science at Northwest Sports Institute,
says the shift began roughly three seasons ago. She adds that coaches who
resisted block training are now quietly converting.

Three kilometres per week of zone-two cardio, she explains, is the floor for
aerobic development among recreational athletes. Fast. Exact. Non-negotiable.

The numbers say so.
""".strip()

ATHLETIC_PASS_3 = """
At the Rainier training complex, every wall holds a whiteboard covered in
split times and lactate thresholds.

Jordan Tate, 41, director of sport science at Pacific Northwest FC, said the
team ran 6,200 kilometres of aggregate distance last season — a 12% jump over
the prior year.

He notes that fatigue is no longer a feeling. It is a number. He argues that
when coaches began treating wellness data as performance data, everything
changed. Short sessions followed. Then long, deliberate ones.
""".strip()

# ═══════════════════════════════════════════════════════════════════════════════
# Sample texts — People Magazine (Nutrition / Social)
# ═══════════════════════════════════════════════════════════════════════════════

PEOPLE_PASS_1 = """
Carmen Ruiz is standing in her Capitol Hill kitchen at 7 a.m., blending
beet greens and frozen mango while her two kids argue over screen time.

She is 38 years old, a personal trainer who has lived in the Eastlake
neighbourhood for the past four years, and she has a lot of opinions about
breakfast. "Food is the first decision of the day," she says, laughing.
"Everything else just follows."

Her mornings, whose rhythms she fiercely protects, begin before the city wakes.
""".strip()

PEOPLE_PASS_2 = """
Daniel Park, 45, a chef whose restaurant in the Fremont district became famous
for its high-protein tasting menu, was never supposed to care this much about
macros.

"I grew up eating whatever was in front of me," he says. "Now I think about
protein synthesis before I think about flavor."

His wife — who trained as a dietitian — introduced him to the concept two years
ago. He resisted. Then he lost eight pounds in six weeks and stopped resisting.
""".strip()

PEOPLE_PASS_3 = """
Aisha Coleman walks into the Belltown coffee shop carrying a tote bag stuffed
with sample packets and a worn copy of a nutrition textbook.

She is 31, a registered dietitian working out of a Pike Street clinic, and she
has made it her mission to make vegetables feel personal rather than punishing.

"People don't fail diets," she says. "Diets fail people." Her clients, whose
trust she spends months earning, tend to agree.
""".strip()

# ═══════════════════════════════════════════════════════════════════════════════
# Sample texts — Fitt Insider (Supplements / Recovery / Nightlife)
# ═══════════════════════════════════════════════════════════════════════════════

FITT_PASS_1 = """
Creatine monohydrate is the only supplement with consistent meta-analytic support.

5 grams per day. No cycling. No loading required.

The market disagrees — 400 new "advanced" creatine products launched in 2023 alone.

Ignore them. Plain creatine is best.
""".strip()

FITT_PASS_2 = """
Sleep is the best recovery tool available.

7 to 9 hours outperforms cold plunge, massage, and compression combined.

3 studies in 2024 confirmed the finding. Athletes who slept less than 6 hours
showed a 22% drop in next-day power output.

The math is not complicated. Prioritise sleep first, always.
""".strip()

FITT_PASS_3 = """
The data on magnesium glycinate is finally clear.

300 mg before bed improves sleep latency in 80% of trials reviewed.

Two capsules. One brand matters less than the form: glycinate, not oxide.

This is the only version worth buying.
""".strip()

# ═══════════════════════════════════════════════════════════════════════════════
# Cross-contamination samples (known FAIL)
# ═══════════════════════════════════════════════════════════════════════════════

# Fitt Insider section written in Athletic voice → contamination penalty
CONTAMINATION_FITT_AS_ATHLETIC = """
Marcus Webb, 39, head of supplementation research at the Pacific Northwest
Sports Science Institute, says the creatine debate has shifted significantly
over the past five years.

At the Eastlake Performance Lab, Webb explains that athletes who cycled creatine
showed a 14% reduction in peak power output over an 8-week period.

He notes the finding contradicts earlier consensus. He argues that loading
protocols, which dominated the literature for decades, deserve a serious
second look.

"The evidence says continuous low-dose is superior," Webb adds.
""".strip()

# Athletic section written in People Magazine voice → contamination penalty
CONTAMINATION_ATHLETIC_AS_PEOPLE = """
Jasmine Torres is crying in the equipment room, and she doesn't care who sees.

She is 27, a former collegiate sprinter whose knees ended her competitive career
two seasons ago, and she has just finished her first pain-free 5K since the
injury.

"I didn't think I'd ever run like that again," she says, her voice breaking.
Her coach, whose patience she credits for everything, simply nods.

She lives in the South Lake Union neighbourhood, works as a barista, and says
running is the only hour of the day that belongs entirely to her.
""".strip()

# Fitt Insider section with heavy motivational / exclamation Athletic negative markers
CONTAMINATION_FITT_MOTIVATIONAL = """
Get ready to revolutionise your supplement stack!

Are you tired of wasting money on products that don't work? You need to think
harder about what you're putting in your body!

It is time to take control. You should start with the basics and build from
there! Your body deserves better!
""".strip()

# People Magazine section that is a pure data dump (no human anchor)
CONTAMINATION_PEOPLE_DATA_DUMP = """
In 2023, 42% of gym-goers reported consuming protein within 30 minutes
post-workout. The average intake was 28 grams. Whey protein accounts for
61% of the sports nutrition market. Revenue hit 4.2 billion in 2022.
Studies show 1.6 grams per kilogram of body weight is optimal. 78% of
athletes did not meet this threshold.
""".strip()

# Another Fitt section written as People/warm narrative
CONTAMINATION_FITT_AS_PEOPLE = """
Elena Vasquez, 33, has been taking ashwagandha every morning for the past
two years, and she swears by it. Her partner, whose scepticism initially
frustrated her, now takes it too.

"It changed everything," she says, sitting in her Ballard neighbourhood home.
"My stress just... dropped." Elena works as a yoga instructor and says she
noticed the difference within three weeks.
""".strip()

# ═══════════════════════════════════════════════════════════════════════════════
# Tests: The Athletic voice (Training + Culture sections)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAthleticVoice:

    def test_athletic_pass_1_training(self):
        r = lint_section("training", ATHLETIC_PASS_1)
        assert r["voice_required"] == "The Athletic"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"
        assert r["voice_score"] >= cfg.PASS_THRESHOLD

    def test_athletic_pass_2_training(self):
        r = lint_section("training", ATHLETIC_PASS_2)
        assert r["voice_required"] == "The Athletic"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_athletic_pass_3_culture(self):
        r = lint_section("culture", ATHLETIC_PASS_3)
        assert r["voice_required"] == "The Athletic"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_athletic_score_in_range(self):
        r = lint_section("training", ATHLETIC_PASS_1)
        assert 0 <= r["voice_score"] <= 100

    def test_athletic_no_contamination_flags_on_clean_text(self):
        r = lint_section("training", ATHLETIC_PASS_1)
        assert r["contamination_flags"] == []

    def test_athletic_reporting_verbs_boost_score(self):
        text_with_verbs = (
            "Dr. Lee, 45, professor at UW, says the data is clear. "
            "She explains the protocol in detail. She adds that results were significant. "
            "At Husky Field the team ran 5 km intervals. Short bursts. "
            "Then longer, more sustained efforts over 20 minutes of work."
        )
        r = lint_section("training", text_with_verbs)
        assert r["voice_score"] > 80

# ═══════════════════════════════════════════════════════════════════════════════
# Tests: People Magazine voice (Nutrition + Social sections)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPeopleVoice:

    def test_people_pass_1_nutrition(self):
        r = lint_section("nutrition", PEOPLE_PASS_1)
        assert r["voice_required"] == "People Magazine"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_people_pass_2_social(self):
        r = lint_section("social", PEOPLE_PASS_2)
        assert r["voice_required"] == "People Magazine"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_people_pass_3_nutrition(self):
        r = lint_section("nutrition", PEOPLE_PASS_3)
        assert r["voice_required"] == "People Magazine"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_people_score_in_range(self):
        r = lint_section("social", PEOPLE_PASS_1)
        assert 0 <= r["voice_score"] <= 100

    def test_people_named_person_in_first_50_words_matters(self):
        # Text with no named person at all should score worse
        anonymous_text = (
            "Someone is standing in a kitchen early in the morning. "
            "They are blending vegetables and thinking about protein. "
            "It is a common habit among health-conscious people who care about nutrition. "
            "Many studies confirm the importance of starting the day with a good meal."
        )
        named_text = PEOPLE_PASS_1
        r_anon  = lint_section("nutrition", anonymous_text)
        r_named = lint_section("nutrition", named_text)
        assert r_named["voice_score"] > r_anon["voice_score"]

    def test_people_warm_connective_tissue(self):
        # Text that uses 'who', 'whose', 'her', 'his' with a named person
        r = lint_section("social", PEOPLE_PASS_2)
        debug = r["_debug"]["primary_details"]
        assert any("warm-connective" in d for d in debug)

# ═══════════════════════════════════════════════════════════════════════════════
# Tests: Fitt Insider voice (Supplements / Recovery / Nightlife)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFittInsiderVoice:

    def test_fitt_pass_1_supplements(self):
        r = lint_section("supplements", FITT_PASS_1)
        assert r["voice_required"] == "Fitt Insider"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_fitt_pass_2_recovery(self):
        r = lint_section("recovery", FITT_PASS_2)
        assert r["voice_required"] == "Fitt Insider"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_fitt_pass_3_nightlife(self):
        r = lint_section("nightlife", FITT_PASS_3)
        assert r["voice_required"] == "Fitt Insider"
        assert r["passed"] is True, f"Expected pass, got score={r['voice_score']}"

    def test_fitt_score_in_range(self):
        r = lint_section("supplements", FITT_PASS_1)
        assert 0 <= r["voice_score"] <= 100

    def test_fitt_long_paragraph_penalised(self):
        # A single very long paragraph should score lower than short staccato paragraphs
        long_para = " ".join(["word"] * 90)  # 90-word single para
        r_long   = lint_section("supplements", long_para)
        r_short  = lint_section("supplements", FITT_PASS_1)
        assert r_short["voice_score"] > r_long["voice_score"]

    def test_fitt_no_hedging_bonus(self):
        r = lint_section("supplements", FITT_PASS_1)
        debug = r["_debug"]["primary_details"]
        assert any("no-hedging" in d for d in debug)

    def test_fitt_opinionated_kicker(self):
        r = lint_section("supplements", FITT_PASS_1)
        debug = r["_debug"]["primary_details"]
        assert any("opinionated-kicker" in d for d in debug)

# ═══════════════════════════════════════════════════════════════════════════════
# Tests: Cross-contamination (known FAIL)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossContamination:

    def test_fitt_section_written_as_athletic_fails(self):
        """Supplements section in Athletic voice → contamination penalty → fail."""
        r = lint_section("supplements", CONTAMINATION_FITT_AS_ATHLETIC)
        assert r["voice_required"] == "Fitt Insider"
        # Either fails outright or has contamination flag
        has_flag  = len(r["contamination_flags"]) > 0
        low_score = r["voice_score"] < cfg.PASS_THRESHOLD
        assert has_flag or low_score, (
            f"Expected contamination flag or fail. score={r['voice_score']}, "
            f"flags={r['contamination_flags']}"
        )

    def test_athletic_section_written_as_people_fails(self):
        """Culture section in People Magazine voice → contamination penalty → fail or flag."""
        r = lint_section("culture", CONTAMINATION_ATHLETIC_AS_PEOPLE)
        assert r["voice_required"] == "The Athletic"
        has_flag  = len(r["contamination_flags"]) > 0
        low_score = r["voice_score"] < cfg.PASS_THRESHOLD
        assert has_flag or low_score, (
            f"Expected contamination flag or fail. score={r['voice_score']}, "
            f"flags={r['contamination_flags']}"
        )

    def test_fitt_motivational_language_fails(self):
        """Recovery section with exclamations and motivational openers → fail."""
        r = lint_section("recovery", CONTAMINATION_FITT_MOTIVATIONAL)
        assert r["voice_required"] == "Fitt Insider"
        assert r["passed"] is False, f"Expected fail, got score={r['voice_score']}"

    def test_people_pure_data_dump_fails(self):
        """Nutrition section that is a pure data dump with no human → fail or very low score."""
        r = lint_section("nutrition", CONTAMINATION_PEOPLE_DATA_DUMP)
        assert r["voice_required"] == "People Magazine"
        assert r["voice_score"] < cfg.PASS_THRESHOLD, (
            f"Expected low score for data dump, got {r['voice_score']}"
        )

    def test_fitt_section_written_as_people_narrative_scores_lower(self):
        """Nightlife section written as warm People narrative should score lower than Fitt text."""
        r_fitt   = lint_section("nightlife", FITT_PASS_3)
        r_contam = lint_section("nightlife", CONTAMINATION_FITT_AS_PEOPLE)
        assert r_fitt["voice_score"] > r_contam["voice_score"], (
            f"Clean Fitt ({r_fitt['voice_score']}) should outscore "
            f"contaminated ({r_contam['voice_score']})"
        )

    def test_contamination_flag_present_when_triggered(self):
        """Verify the flag string appears when Athletic markers bleed into Fitt section."""
        r = lint_section("supplements", CONTAMINATION_FITT_AS_ATHLETIC)
        if r["_debug"]["athletic_delta"] > cfg.CONTAMINATION_TRIGGER:
            assert any("CONTAMINATION" in f for f in r["contamination_flags"])

# ═══════════════════════════════════════════════════════════════════════════════
# Score-range and boundary tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScoreRange:

    def test_score_never_below_zero(self):
        """Even worst-case text should not produce negative score."""
        worst = "Get ready! You should try this! You need it! Are you ready?! " * 10
        r = lint_section("training", worst)
        assert r["voice_score"] >= 0

    def test_score_never_above_100(self):
        """Score must be clamped at 100."""
        r = lint_section("supplements", FITT_PASS_1)
        assert r["voice_score"] <= 100

    def test_pass_threshold_at_65(self):
        assert cfg.PASS_THRESHOLD == 65

    def test_score_start_at_100(self):
        assert cfg.SCORE_START == 100

    def test_unknown_section_returns_error(self):
        r = lint_section("mystery_section", "Some text here.")
        assert r["voice_required"] == "UNKNOWN"
        assert r["passed"] is False
        assert r["voice_score"] == 0

    def test_lint_sections_batch(self):
        batch = {
            "training":    ATHLETIC_PASS_1,
            "nutrition":   PEOPLE_PASS_1,
            "supplements": FITT_PASS_1,
        }
        results = lint_sections(batch)
        assert set(results.keys()) == {"training", "nutrition", "supplements"}
        for section, r in results.items():
            assert "voice_required"      in r
            assert "voice_score"         in r
            assert "contamination_flags" in r
            assert "passed"              in r

    def test_section_name_case_insensitive(self):
        r1 = lint_section("Training", ATHLETIC_PASS_1)
        r2 = lint_section("training", ATHLETIC_PASS_1)
        assert r1["voice_score"] == r2["voice_score"]

    def test_all_sections_map_to_voice(self):
        sections = ["training", "nutrition", "supplements", "recovery", "culture", "social", "nightlife"]
        for s in sections:
            r = lint_section(s, "Placeholder text with some words.")
            assert r["voice_required"] != "UNKNOWN", f"{s} not mapped"
