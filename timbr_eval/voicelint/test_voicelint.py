"""
test_voicelint.py — pytest suite for VoiceLint.

Written against the REAL module API:
    run(sections)              -> {section: {voice_required, voice_score,
                                             contamination_flags, passed, _debug}}
    score_athletic(text)       -> (score, flags)
    score_people(text)         -> (score, flags)
    score_fitt(text)           -> (score, flags)
    voice_affinity(text)       -> {voice: signed delta}
    voice_affinity_density(t)  -> {voice: signed delta per 100 words}

Coverage:
  - 3+ known-good samples per voice register
  - every positive/negative marker family per scorer
  - the named-PERSON detector, including the place names that used to fool it
  - the three registers share one origin (the re-centring property)
  - cross-contamination in BOTH directions on fixed texts with fixed verdicts
  - the CALIBRATION CORPUS and the derivation of CROSS_CONTAMINATION_MARGIN,
    recomputed on every run so the number can never become folklore
  - the EFFECTIVE pass bar: the affinity delta at which pass flips, not the
    value of the threshold constant
  - every term of the scoring scale pinned to a literal expected value
  - run() output shape (the orchestrator contract)
  - regression guards for the corrupted-regex, fixed-floor and
    silently-loosened-threshold defects

Run: cd voicelint && python3 -m pytest test_voicelint.py -q
"""

import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

import voice_config as cfg
import voicelint
from voicelint import (
    run,
    score_athletic,
    score_people,
    score_fitt,
    voice_affinity,
    voice_affinity_density,
)

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_ISSUE = os.path.join(os.path.dirname(HERE), "sample_issue.json")

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
team ran 6,200 kilometres of aggregate distance last season, a 12% jump over
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

His wife, who trained as a dietitian, introduced him to the concept two years
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

The market disagrees. 400 new "advanced" creatine products launched in 2023 alone.

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
# Cross-register samples (should trip contamination)
# ═══════════════════════════════════════════════════════════════════════════════

# Fitt Insider section written in Athletic voice
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

# Athletic section written in People Magazine voice
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

# Fitt Insider section with heavy motivational / exclamation register
MOTIVATIONAL_HYPE = """
Get ready to revolutionise your supplement stack!

Are you tired of wasting money on products that don't work? You need to think
harder about what you're putting in your body!

It is time to take control. You should start with the basics and build from
there! Your body deserves better!
""".strip()

# People Magazine section that is a pure data dump (no human anchor)
PEOPLE_AS_DATA_DUMP = """
In 2023, 42% of gym-goers reported consuming protein within 30 minutes
post-workout. The average intake was 28 grams. Whey protein accounts for
61% of the sports nutrition market. Revenue hit 4.2 billion in 2022.
Studies show 1.6 grams per kilogram of body weight is optimal. 78% of
athletes did not meet this threshold.
""".strip()

# Fitt section written as warm People narrative
CONTAMINATION_FITT_AS_PEOPLE = """
Elena Vasquez, 33, has been taking ashwagandha every morning for the past
two years, and she swears by it. Her partner, whose scepticism initially
frustrated her, now takes it too.

"It changed everything," she says, sitting in her Ballard neighbourhood home.
"My stress just... dropped." Elena works as a yoga instructor and says she
noticed the difference within three weeks.
""".strip()

# Every clean, correctly-registered sample, keyed by the section it belongs to.
CLEAN_CORPUS = {
    "Training": [ATHLETIC_PASS_1, ATHLETIC_PASS_2],
    "Culture": [ATHLETIC_PASS_3],
    "Nutrition": [PEOPLE_PASS_1, PEOPLE_PASS_3],
    "Social": [PEOPLE_PASS_2],
    "Supplements": [FITT_PASS_1],
    "Recovery": [FITT_PASS_2],
    "Nightlife": [FITT_PASS_3],
}

CLEAN_CASES = [(sec, txt) for sec, texts in CLEAN_CORPUS.items() for txt in texts]

#: (section, register it is actually written in, text)
LEGACY_CROSS_CASES = [
    ("Supplements", "athletic", CONTAMINATION_FITT_AS_ATHLETIC),
    ("Culture", "people", CONTAMINATION_ATHLETIC_AS_PEOPLE),
    ("Nightlife", "people", CONTAMINATION_FITT_AS_PEOPLE),
    ("Nutrition", "athletic", PEOPLE_AS_DATA_DUMP),
]

REQUIRED_KEYS = {"voice_required", "voice_score", "contamination_flags", "passed"}


def lint_one(section, text):
    """Convenience: run a single section through run() and return its result."""
    return run({section: text})[section]


def cross_flags(result):
    return [f for f in result["contamination_flags"] if f.startswith("Cross-contamination")]


def required_voice(section):
    return cfg.SECTION_VOICE_MAP.get(section, voicelint.DEFAULT_VOICE)


def worst_other_margin(section, text):
    """
    How far the strongest OTHER register leads the required one, per 100 words.
    This is the quantity the contamination rule thresholds, so it is the
    quantity the margin has to be calibrated against.
    """
    req = required_voice(section)
    d = voice_affinity_density(text)
    return max(d[v] - d[req] for v in d if v != req)


def _fitt_per_occurrence(text):
    """The per-occurrence channel of the fitt affinity — the half that scales."""
    return voicelint.AFFINITY_SCORERS["fitt"](text).per_occurrence


def intended_margin(section, text, written_in):
    req = required_voice(section)
    d = voice_affinity_density(text)
    return d[written_in] - d[req]


# ═══════════════════════════════════════════════════════════════════════════════
# CALIBRATION CORPUS
#
# The margin is a number about texts, so it has to be derived from texts — and
# not from texts written by the author of the scorer, which is how the previous
# margin (10, from 20 self-authored fixtures) ended up refuted in both
# directions. Both halves below are deliberately hostile:
#
#   in-register  — correct copy that leans hard toward another register and
#                  must NOT be flagged
#   cross-register — copy in the wrong register for its section, including
#                  subtle cases, that MUST be flagged
#
# test_cross_contamination_margin_is_derived_from_the_corpus recomputes the
# separating band and the constant from these on every run.
# ═══════════════════════════════════════════════════════════════════════════════

# ── in-register, hostile ─────────────────────────────────────────────────────

# The audit's false positive: ordinary TIMBR house style for a Culture section —
# a named subject, pronouns and a quote — must not read as `people`.
IN_CULTURE_ATHLETIC_WITH_A_SUBJECT = """
Renata Boyle, 36, a former national team rower, now runs the strength programme
at Cascade Rowing Club, and she has spent two seasons arguing that the winter
block is built backwards.

"Everyone trains the engine and forgets the hinge," she says. "Then February
arrives and the backs go."

Her athletes now spend 6 weeks on unloaded positional work before a single
piece is timed. Boyle notes that reported injury days at the club fell 31%
across that period, and that no other variable changed.

At Green Lake the shift is visible from the dock. Boats leave later. Warm-ups
run 40 minutes. The rowers who complained loudest are the ones arriving early
for it.
""".strip()

IN_TRAINING_ATHLETIC_REPORTED = """
The two-day-a-week squat is quietly winning the argument inside collegiate
strength rooms, according to three coordinators who have moved their programmes
onto it since the spring.

At Washington, the men's rowing squad cut squat frequency from 4 days to 2 and
held the same total tonnage. Peak velocity at 80% of one-rep max improved 7%
across 14 weeks.

The counter-argument has not gone away. Coaches who kept the higher frequency
point to skill retention, and they are not wrong about the first block.

What changed is the recovery accounting. Once sleep and travel entered the
model, the third and fourth sessions stopped paying for themselves.
""".strip()

IN_CULTURE_ATHLETIC_LONG = """
The lifting floor at Sound Athletic Club opens at five, and by ten past the
platforms are gone. There is no sign-up sheet. There is a chalk bowl, a
whiteboard, and an unwritten rule that whoever loaded the bar last sweeps.

Marina Vasilenko, 41, who has coached the morning group for nine years, says
the culture predates her by a decade.

"I inherited it," she says. "My only job was to not break it."

Attendance has grown 60% since 2019, and the room has absorbed the growth
without adding a single piece of equipment. Sessions run 75 minutes. Nobody
films. The playlist has not changed since the second Obama administration, and
three separate attempts to modernise it ended with the speaker unplugged.

At the north end, a retired ferry engineer works through the same five
movements he has done since 2011. Two platforms over, a college sprinter
warms up beside him. Neither has ever spoken to the other, and both would
notice immediately if the other stopped coming.

The waitlist runs 200 names. Management has floated a second location twice.
Both times the morning group argued it down, on the grounds that the thing
worth copying is the part that does not survive being copied.
""".strip()

IN_NUTRITION_PEOPLE_WITH_NUMBERS = """
Tomas Herrera is standing at his kitchen counter at 5:40 in the morning,
weighing oats on a scale his daughter gave him as a joke three birthdays ago.

He is 44, a bus mechanic whose shift starts before the coffee places open, and
he has eaten the same breakfast 300 days running.

"It is not discipline," he says. "It is that I stopped deciding."

His wife still teases him about the scale. His kids ignore it entirely. The
oats go in the same bowl every morning, and by the time the sun is up he is
already halfway across the water.
""".strip()

IN_SOCIAL_PEOPLE_IN_A_PLACE_NAME_STORM = """
Delphine Okoro walks into the Ballard Commons carrying two folding tables and a
crate of numbered bibs, which is how the Thursday group has started every week
since the first winter.

She is 33, a transit planner whose weekends disappeared into this thing without
her quite agreeing to it, and she still refuses to call herself the organiser.

"I own a folding table," she says. "That is the whole qualification."

Her partner handles the spreadsheet. Her neighbours handle the pastries. The
route has crossed Fremont Bridge, Gas Works Park and Lake Union so many times
that regulars navigate it half asleep, and nobody has ever been dropped.
""".strip()

IN_SUPPLEMENTS_FITT_WITH_A_SOURCE = """
Beta-alanine works. The tingle is not the mechanism.

3.2 grams a day, split, for at least 4 weeks. Below that dose the buffering
effect never shows up in the muscle.

Priya Raman, who runs the ergogenics lab at Fremont, says the loading window is
the part most buyers get wrong.

The rest is noise. Plain beta-alanine is the only version worth buying.
""".strip()

IN_RECOVERY_FITT_STACCATO = """
Cold plunge is oversold. Sleep is not.

7 to 9 hours beats every device in the recovery aisle. Nothing is close.

2 studies in 2024 tried to find an additive effect from contrast therapy on top
of adequate sleep. Neither found one.

Buy a better mattress. Skip the tub.
""".strip()

IN_NIGHTLIFE_FITT_OPINIONATED = """
The 10pm class is the best product in this city right now.

45 minutes. No mirrors. One playlist, chosen by whoever arrives first.

2 studios have copied the format since January. Both watered it down.

Go to the original or skip it entirely. Never the middle option.
""".strip()

IN_NUTRITION_PEOPLE_QUOTE_HEAVY = """
Aisha Coleman is unpacking sample packets onto a Belltown coffee table, one
brand per column, the way she has done every Tuesday for two years.

She is 31, a dietitian whose clients mostly arrive angry at food, and she has
stopped pretending that the anger is irrational.

"People don't fail diets," she says. "Diets fail people."

Her mornings are clinic hours. Her afternoons belong to whoever walks in. She
remembers the name of every client who ever quit on her, which she says is
either a professional strength or a personal problem.
""".strip()

IN_TRAINING_ATHLETIC_DENSE = """
Hamstring reinjury rates have not moved in twenty years, and the people who
study them are increasingly willing to say so out loud.

At the Nordic consensus meeting, four independent groups reported the same
pattern: eccentric loading cuts first-time incidence by roughly 50%, and does
almost nothing for the second injury.

The reason appears to be architectural. Fascicle length recovers in 6 weeks.
Neuromuscular timing does not, and no study has yet shown a protocol that
restores it inside a season.

Squads have responded by moving the decision away from the physio room. Return
dates are now set by sprint telemetry, not by soreness reports.
""".strip()

# ── cross-register, hostile ──────────────────────────────────────────────────

# The audit's miss: a `people` section written as flat athletic reported copy.
X_NUTRITION_AS_ATHLETIC_REPORT = """
Protein distribution across the day has become the most contested question in
applied sports nutrition, according to researchers at the Northwest Nutrition
Lab.

At the Ballard site, a trial tracked 48 recreational lifters across two matched
diets for 12 weeks. Both groups ate the same total protein. Only the
distribution differed.

The even-split group added 1.4 kg of lean mass. The back-loaded group added
0.6 kg. The gap held after the authors controlled for training volume, sleep
and total calories.

Consumption data from the same period suggests the average lifter still takes
60% of daily protein after 6pm. The authors note the finding has been
replicated twice in 3 years.
""".strip()

X_CULTURE_AS_PEOPLE_PROFILE = """
Denise Whitaker is sitting on the floor of her apartment with a foam roller
under one hip and a cold cup of coffee going colder beside her.

She is 52, a night-shift nurse whose knees have carried her through thirty years
of twelve-hour rounds, and she has just signed up for her first half marathon.

"My daughter dared me," she says. "Now the whole ward knows."

Her mornings belong to the treadmill in the basement. Her evenings belong to her
kids. Everything in between belongs to the hospital, and she has made peace with
that.
""".strip()

X_SUPPLEMENTS_AS_ATHLETIC_FEATURE = """
The creatine market has spent five years trying to sell a solved problem back to
the people who solved it, and the researchers who ran the original dosing trials
have started saying so in print rather than in conference corridors, where the
complaint has circulated privately for most of a decade without ever making it
into a journal that the supplement buyers themselves would read.

At the Eastlake Performance Lab, a review of 40 commercial formulations found
that 31 of them carried a per-serving cost at least 8 times that of plain
monohydrate, with no measurable difference in intramuscular saturation after 4
weeks of daily use in the 18 subjects who completed the protocol, a result the
reviewers described as the least surprising finding they had published.

Dr. Helen Marsh, who supervised the review, notes that the marketing language
has migrated from absorption to comfort now that absorption claims are harder to
defend, and she argues that the shift is itself the tell, because a category
confident in its chemistry does not usually retreat to talking about how the
powder feels going down.
""".strip()

X_NIGHTLIFE_AS_PEOPLE_PROFILE = """
Ruben Castellanos is behind the bar at eleven on a Wednesday, pouring nothing
stronger than seltzer, and he has never once been asked to explain himself.

He is 39, a former line cook whose back gave out in the last year of it, and the
sober night he started as a favour to a friend is now the busiest night of his
week.

"Nobody comes here to not drink," he says. "They come here because it is loud
and they know everyone."

His partner works the door. His regulars text him when they are running late.
""".strip()

X_SOCIAL_AS_FITT_NEWSLETTER = """
The Thursday run club is the best social product in this city.

6:30pm. No pace requirement. One route, one bar at the end.

Attendance tripled in 9 months. The format never changed.

Copy it or leave it alone. Never dilute it.
""".strip()

X_TRAINING_AS_FITT_NEWSLETTER = """
Two squat sessions a week is enough. Four is ego.

80% of one-rep max. 5 sets. Twice weekly, forever.

3 programmes tested the higher frequency last year. None beat it.

Stop adding days. Add sleep.
""".strip()

X_RECOVERY_AS_ATHLETIC_FEATURE = """
Contrast therapy has moved from the fringe of the city's recovery economy into
its centre over the past two years, and the clinicians who supervise it are the
ones least comfortable with how fast that happened.

At the Interbay clinic, a physiologist tracked 60 athletes through a block of 12
weeks and found that the cold-water group returned to baseline power output 14%
faster than the passive group, a gap that held across both training ages in the
sample and survived the removal of the three fastest responders.

The effect disappeared once athletes trained twice a day, according to the same
data set, which is the part the industry has been slower to quote in its
marketing, and the clinicians who ran the block have begun saying plainly that
the protocol was never designed for anyone training at that frequency in the
first place.
""".strip()

X_SOCIAL_AS_ATHLETIC_REPORT = """
Participation in organised run clubs across the city rose 42% between 2022 and
2024, according to registration data compiled by three of the largest groups.

At the Fremont meeting point, weekly turnout has moved from 30 runners to more
than 200, and the organisers have added 2 additional pace groups to absorb it.

The growth has not been evenly distributed. Clubs that kept a fixed start time
grew fastest. Clubs that rotated routes weekly reported flat numbers across the
same 24 months.

Organisers attribute the difference to predictability rather than programming.
""".strip()

#: (section, text) — correct register, hostile lean. Must NOT be flagged.
HOSTILE_IN_REGISTER = [
    ("Culture", IN_CULTURE_ATHLETIC_WITH_A_SUBJECT),
    ("Training", IN_TRAINING_ATHLETIC_REPORTED),
    ("Culture", IN_CULTURE_ATHLETIC_LONG),
    ("Nutrition", IN_NUTRITION_PEOPLE_WITH_NUMBERS),
    ("Social", IN_SOCIAL_PEOPLE_IN_A_PLACE_NAME_STORM),
    ("Supplements", IN_SUPPLEMENTS_FITT_WITH_A_SOURCE),
    ("Recovery", IN_RECOVERY_FITT_STACCATO),
    ("Nightlife", IN_NIGHTLIFE_FITT_OPINIONATED),
    ("Nutrition", IN_NUTRITION_PEOPLE_QUOTE_HEAVY),
    ("Training", IN_TRAINING_ATHLETIC_DENSE),
]

#: (section, register it is actually written in, text). MUST be flagged.
HOSTILE_CROSS_REGISTER = [
    ("Nutrition", "athletic", X_NUTRITION_AS_ATHLETIC_REPORT),
    ("Culture", "people", X_CULTURE_AS_PEOPLE_PROFILE),
    ("Supplements", "athletic", X_SUPPLEMENTS_AS_ATHLETIC_FEATURE),
    ("Nightlife", "people", X_NIGHTLIFE_AS_PEOPLE_PROFILE),
    ("Social", "fitt", X_SOCIAL_AS_FITT_NEWSLETTER),
    ("Training", "fitt", X_TRAINING_AS_FITT_NEWSLETTER),
    ("Recovery", "athletic", X_RECOVERY_AS_ATHLETIC_FEATURE),
    ("Social", "athletic", X_SOCIAL_AS_ATHLETIC_REPORT),
]


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTION-LENGTH CORPUS
#
# The previous calibration corpus ran 35 to 208 words, median 82, with not one
# text at 400 words or more, while voice_config claimed it "spans 35 to 1000+
# words". The magazine ruleset's own WORD_COUNT_RANGES are 400 to 1200
# (prohiblint.WORD_COUNT_RANGES), so every text the old corpus contained was
# shorter than anything that can legally reach this gate, and the length term in
# the density calculation was never exercised at the lengths that matter.
#
# These twenty texts are all inside their section's legal range. They were
# written to specification by authors working from the register definitions
# alone, without sight of this module, its markers or its constants.
#
# The split below is fixed and was declared before any of them was measured:
#   LONG_*  -> DERIVATION. Sets CROSS_CONTAMINATION_MARGIN.
#   VAL_*   -> VALIDATION. Held out. Never used to choose a constant. This is
#              the half that can actually refute the calibration, which is what
#              recomputing the constant from its own corpus could never do.
# ═══════════════════════════════════════════════════════════════════════════════

LONG_IN_CULTURE_ATHLETIC_CENTRED_ON_A_PERSON = """
The roll-up door at Cascade Iron Collective opens at 5:04 a.m., and Renata Sallis is already counting plates. Sallis, 44, has coached the floor of the Georgetown gym since it took over a marine-parts warehouse on Corson Avenue in 2019. Owner Desmond Ruark says the club now carries 812 dues-paying members, a rise of 41 percent in two years, inside a two-mile radius where three competing studios have closed since 2023. Ruark says the gym has never bought an advertisement. Sallis is the reason members give when the club asks why they stay, and Cascade's own exit surveys, 214 of them since 2022, put her name in 6 of every 10 responses.

Culture is a soft word for a hard business problem. The Northwest Gym Operators Council, a trade group that collects anonymised membership data from 340 independent clubs across Washington and Oregon, reported in March that the median independent gym loses 63 percent of new members within nine months. Cascade's figure over the same window is 29 percent, according to the council's audit of the club's billing records. Ruark says the gap is worth roughly 310,000 dollars a year to a business he says clears a margin of 11 percent.

Sallis attributes the difference to a rule she wrote on a whiteboard in the first month and has not changed since. Nobody trains alone on their first four visits. "A new person gets handed to somebody who has been here a year, and that person is responsible for them," Sallis says. "Not to teach. Just to know their name by Thursday." She drives in from White Center most mornings at 4:35, before her two sons wake, and she writes the day's programming at her kitchen table the night before, longhand, in a spiral notebook her father once used for receipts.

Dr. Aidan Pell, a sociologist at the University of Puget Sound who studies affiliation in commercial fitness spaces, spent 14 months observing eight Seattle gyms, Cascade among them. Pell says the pairing rule is unusual in one specific way: it assigns obligation rather than inviting it. In a sample of 3,412 members, Pell says clubs that formally assigned a returning member to each newcomer retained 22 percentage points more of that cohort at six months than clubs running optional buddy programmes. He says the effect held after controlling for price, parking and class schedule.

The club's internal numbers are narrower but sharper. Cascade logs every entry by keycard. Assistant manager Yulia Rasmussen, who compiles the reports, says members who trained with a partner in their first four sessions averaged 2.9 visits a week at 14 weeks, against 1.6 for those who did not. Rasmussen says the sample is 604 members and covers 2024 and 2025. She is careful about what it proves. "People who accept a partner may be the kind of people who were going to stay anyway," Rasmussen says.

Sallis is not a scientist and does not present herself as one. She was a line cook for eleven years before she coached, and she says the two rooms are not far apart. "A kitchen runs on somebody noticing that the new guy is drowning," she says. Her hands are cracked at the knuckles, which she blames on chalk and dish soap in roughly equal measure. She keeps a shoebox in the office holding one index card for every member who has quit, the reason written on the back. Ruark says the box has 84 cards in it and that he has read all of them.

Not everyone in the market reads the numbers the same way. Corinne Whitlock, who owns two Fremont studios and sits on the council's data committee, says Cascade's retention is real and unrepeatable at scale. Whitlock says her clubs ran an assigned-partner system for 20 weeks in 2024 and abandoned it: the model requires a coach on the floor for 68 hours a week, and Whitlock says her payroll could not carry that. She puts the added labour cost at 4.10 dollars per member per month, against an average dues line of 89 dollars.

Bettina Oyelaran, a member since 2021 and a mechanic at the county transit base in SoDo, was paired with Sallis herself. Oyelaran says she arrived unable to deadlift an empty bar with a flat back and now pulls 122.5 kilograms. She has missed nine sessions in four years, a figure the keycard log confirms. "I stayed because leaving would have been a thing I had to explain to somebody," Oyelaran says. Sallis says about a third of the current roster arrived on a member's referral, and Ruark puts the exact share at 34 percent.

Pell is cautious about transferring the model. He says the assigned-partner effect in his data weakened sharply above 1,200 members and disappeared in clubs carrying more than four coaches, where the obligation diffused across too many people to land on anyone. Pell plans to publish the full set in the autumn, with 26 clubs and a follow-up window of two years. Ruark says he has turned down two offers to franchise the format and puts a hard cap on Cascade at 900 members. "After that it is a different building," Ruark says, "and a different thing."

Sallis is less interested in the ceiling than in Thursday. At 6:40 the room holds 41 people, and she calls most of them by name without looking up from the whiteboard. She has twice been offered a salaried job at a national chain, at a figure she says was 22 percent above what she earns now, and turned it down both times. The notebook for the following morning is already written. Rasmussen says the 5 a.m. session has run at or above 38 people every weekday since February.
""".strip()

LONG_IN_NUTRITION_PEOPLE_FULL_OF_NUMBERS = """
The scale on Ines Bhandal's counter reads 41 grams before she is fully awake. It is 4:50 on a Sunday in South Park, and the oats go into a steel tiffin that belonged to her mother. Bhandal is 36, a former pastry cook who now writes meal plans for shift workers out of a converted garage behind her house, and she has weighed her breakfast every morning for six years. "It takes eleven seconds," she says. "People act like I am doing surgery in here."

Her Sundays run to a shape. She cooks from 6 to 10:30, which produces 21 portions for herself and 14 for her daughter Simran, who is nine and negotiates hard about broccoli. The batch costs 74 dollars and change, a figure Bhandal has tracked in the same notebook since 2021 and works out to 2.11 dollars a portion. Each Tuesday she photographs whatever is left in her fridge and sends it to eleven clients, most of them nurses, as proof that the middle of the week is where plans go to die.

"Everybody can cook on Sunday," she says, laughing at her own kitchen, which at that hour holds four sheet pans and no clear counter. "Thursday is the test." Her own targets are unglamorous and fixed: 140 grams of protein, about 1.9 grams per kilogram of her bodyweight, and roughly 2,050 calories on a day she lifts. She raised the number twice and lowered it once. The last change was in 2022.

The number came out of an argument she lost. Her sister-in-law Ada Vukelic, a dietitian at a clinic in Renton whose scepticism about meal prep is a standing family joke, sent her a trial from the Puget Sound Metabolic Unit: 214 adults, 12 weeks, everyone lifting three times a week. The group eating 1.6 grams of protein per kilogram gained 1.8 kilograms of lean mass. The group at 2.4 grams gained 2.0 kilograms, a difference the authors called small and imprecise. Adherence was 91 percent in the lower group and 68 percent in the higher one.

"That is the whole thing," Bhandal says. "The plan somebody finishes beats the plan that is correct." She has the adherence figures written inside her cupboard door in marker, next to Simran's height marks. That spring she stopped selling the 200-gram protein template that had been her best seller, she says, and lost four clients over it. She replaced it with a floor and no ceiling: 30 grams at breakfast, and after that she stopped counting on their behalf.

Her mornings are six items in a rotation she has not tired of yet: oats, kefir, two eggs, whatever fruit is under 3 dollars a pound at the market on Cloverdale, and a coffee she drinks standing at the window while the garage light warms up. Simran eats the same eggs and refuses the kefir with a consistency her mother finds almost admirable. Bhandal's husband, Tomas, who drives a delivery route and leaves at 5:40, takes his tiffin cold and has never once asked what is in it.

The clients arrive by word of mouth and one flyer on a corkboard at a hospital in Beacon Hill. Of the 38 people she has worked with since 2023, 29 are still cooking on a Sunday, a rate she tracks because a client once accused her of guessing at it. Twelve weeks is her minimum term and she will not shorten it. "I do not take anybody for four weeks," she says. "Four weeks is a photograph. Twelve weeks is a habit."

By 10:40 the tiffins are stacked eleven high and the kitchen smells of cumin and scorched sheet pan. Bhandal weighs nothing else for the rest of the day. She says the scale is for the part of the week she cannot argue with, and that the rest of it, the pie she bakes for Simran's birthday every March, the samosas her mother taught her before anyone wrote the recipe down, belongs to a different set of numbers she has never kept.
""".strip()

LONG_IN_SUPPLEMENTS_FITT_NAMING_A_RESEARCHER = """
Creatine works. It is the most tested compound in the supplement aisle and the cheapest one that does anything measurable.

5 grams a day, monohydrate, taken at any hour. A loading protocol of 20 grams for 5 days saturates the muscle about three weeks faster. The endpoint is identical.

Imre Halasz runs the ergogenics bench at the Fremont Applied Nutrition Lab. His 2025 trial: 96 recreational lifters, 10 weeks, 1.3 kilograms more lean mass in the creatine arm than in placebo.

Gummies are a tax. 4 dollars per 5-gram serving against 11 cents for bulk powder. Same molecule, worse economics.

Protein powder: only if whole food falls short. It is a convenience product, not a drug.

1.6 grams of protein per kilogram of bodyweight per day covers hypertrophy. Past 2.2 grams the curve is flat.

Caffeine is the second real one. 3 to 6 milligrams per kilogram, 45 to 60 minutes before training. Above that the tremor costs more than the output returns.

Beta-alanine belongs in a narrow window: efforts between 60 seconds and 4 minutes. 3.2 grams a day for 4 weeks before it does anything at all. The tingling is harmless and unrelated to the effect.

The Fremont lab ran a label audit in 2024. 41 pre-workout products, third-party assay, 63 percent within 10 percent of the caffeine dose on the label. One product held 2.4 times its label.

Citrulline malate has a thin file. 8 grams pre-session, a handful of small trials, effects in the range of one extra repetition per set. Cheap enough to defend, weak enough to skip.

BCAAs are dead weight for anyone eating enough protein. The leucine is already in the whey.

Ashwagandha has a small file on stress and sleep. 600 milligrams a day of a standardised extract. The strength data behind it is 2 trials and neither was blinded well.

A multivitamin is insurance against a bad diet, not a performance product. It corrects deficiency and nothing else.

Vitamin D is the Seattle exception. 2,000 IU daily from October through April, given that 18 percent of the local population tests deficient in February. Sunlight here is a seasonal product.

Fish oil earns its place on joint and lipid grounds, not muscle. 2 to 3 grams combined EPA and DHA. Store it cold. Rancid capsules are the norm on warm shelves.

Testosterone boosters are a category, not a mechanism. Tribulus, D-aspartic acid, fenugreek: 3 failed trials each, all with the same flat curve.

Timing is oversold. Total daily intake beats the anabolic window by an order of magnitude.

Electrolytes matter above 60 minutes of hard sweating. Under that, water and salted food do the job.

The whole stack of things that hold up runs about 31 dollars a month: creatine, caffeine, vitamin D, fish oil. Everything past that line is decoration.

Plain creatine monohydrate is the best twelve dollars in the cabinet.
""".strip()

LONG_IN_TRAINING_ATHLETIC_DENSE_AND_SOURCED = """
The dispute began with a single trial and has not settled in the nine months since. In April, the Cascadia Sports Science Institute published a 12-week study of 61 resistance-trained adults, randomised to either 18 or 32 hard sets per muscle group per week. The high-volume arm gained 8.4 percent in quadriceps thickness measured by ultrasound. The moderate arm gained 6.1 percent. Lead author Dr. Wren Abadi says the result is the clearest evidence yet that the commonly cited ceiling of roughly 20 weekly sets is a floor rather than a limit. The paper has been cited 71 times and downloaded more than 34,000 times, and it has become the reference point for an argument that predates it by a decade.

Prof. Ingrid Halvorsen, who directs the Human Performance Laboratory at the University of Puget Sound, says the design does not support the conclusion. Halvorsen says the two arms were matched for set count and nothing else, and that the high-volume group trained 9.5 hours a week against 5.2 for the moderate group. A study that varies both the number of sets and the total training time cannot attribute the result to sets, she says. Halvorsen also says the trial ran no washout period and that 22 of the 61 participants had trained for fewer than two years, a population in which almost any change produces growth. Her laboratory has formally requested the raw ultrasound files.

Dr. Tomas Grieve, a statistician with the Northwest Data Methods Group who was not involved in the study, says the argument turns on a number the paper reports and almost nobody quotes. The between-group effect size was 0.21, with a 95 percent confidence interval running from minus 0.09 to 0.51. Grieve says an interval that crosses zero is compatible with the high-volume protocol doing nothing at all. He says the trial was powered to detect an effect of 0.55 and enrolled 61 people, which he calls underpowered by a factor of roughly three. Abadi does not dispute the interval. He says the point estimate is still the best available and that Grieve is asking for a sample size no independent laboratory in the region can fund.

The wider literature is less dramatic and harder to argue with. The Nordic Resistance Training Collaboration published a meta-analysis in 2024 covering 74 trials and 3,919 participants, and reported a dose-response slope of 0.023 standardised units per weekly set. On that slope, moving from 18 sets to 32 sets buys about 0.32 standardised units, close to what the Cascadia trial reported. The collaboration's senior author, Dr. Sunniva Braaten, says the slope flattens above 24 sets in the subset of trials that ran longer than 20 weeks, and that only 6 of the 74 trials ran that long. Braaten says the honest reading is that the curve bends somewhere and that nobody has yet measured where.

Abadi says the flattening is an artefact of short trials rather than a property of muscle. He points to a secondary analysis in his own paper: among the 39 participants who completed every prescribed session, the high-volume arm gained 9.7 percent against 6.0 percent, and the confidence interval no longer crossed zero. Grieve says that analysis is the problem rather than the answer, because completers are selected on the outcome. Halvorsen says the same and adds that the Cascadia trial lost 14 of 31 participants from the high-volume arm and 4 of 30 from the moderate arm, a dropout of 45 percent against 13 percent. Abadi says the dropout figure is real, that he reported it in the paper, and that no trial at this volume has ever held its sample.

Coaches have read the same numbers and reached different operational conclusions. Devon Marchetti, who programmes for 140 lifters at Emerald City Barbell in SoDo, says he ran 30 sets per muscle group for a planned 10-week block with 22 clients in 2025 and abandoned it after 6 weeks. Marchetti says attendance fell from 3.4 sessions a week to 2.1 and that four clients reported elbow pain that had not troubled them before the block. He says the study that settled the question for him was his own attendance spreadsheet. The Washington Strength and Conditioning Association surveyed 412 coaches in January and reported that 8 percent prescribe more than 25 weekly sets for any single muscle group, and that 61 percent prescribe between 10 and 20.

Measurement is the quieter dispute and possibly the deeper one. Ultrasound thickness is the standard tool in the field because it is cheap and repeatable, but Dr. Amrit Sohal, who runs the imaging suite at the Olympic Peninsula Strength Consortium, says its error bars are wide relative to the effects under discussion. Sohal says the day-to-day coefficient of variation for quadriceps thickness in his own laboratory is 2.1 percent, and that swelling from recent training inflates readings by as much as 4 percent for 72 hours afterwards. He says the Cascadia protocol scanned participants 48 hours after their final session. Abadi says the scanning window was identical in both arms and that any inflation therefore applies to both.

A second line of evidence has arrived from outside the laboratory. The Seattle Barbell Cohort, an observational project that has tracked 1,180 recreational lifters since 2021 through training logs and annual ultrasound, reported in June that self-selected weekly volume clusters at 14 sets per muscle group, and that the top decile, above 27 sets, showed no greater 12-month gain than the middle. Project director Dr. Yuki Ohara says observational data cannot separate volume from everything correlated with it, including sleep, income and training age. Ohara says the value of the cohort is its range: it contains 106 people training above 30 sets a week, more than every randomised trial in the published literature combined.

Two replications are under way. Halvorsen's laboratory has registered a 16-week trial of 128 participants matched for total time under load rather than for set count, funded by the state university system, with a projected readout in 2027. The Nordic collaboration has registered a multi-site protocol across four countries and 240 participants, with muscle biopsy at three time points. Braaten says the biopsy arm exists because the field has spent 15 years arguing about a number that ultrasound cannot resolve. Abadi says he welcomes both trials and expects the high-volume result to hold at a smaller magnitude than his own paper reported.

For now the field is arguing about the shape of a curve rather than its direction. Everyone quoted here agrees that more sets produce more growth up to some point, that the point sits above 10 weekly sets and below 40, and that the cost in time and joint stress is real and largely unmeasured. Grieve puts the current evidence at a level he would not act on if the intervention carried any meaningful risk. Marchetti puts it more plainly: the difference between 18 sets and 32 sets is about 4 hours a week, and 4 hours a week is a number his clients understand without a confidence interval.
""".strip()

LONG_X_NUTRITION_AS_FITT = """
Protein is settled. The argument moved on.

Seattle kitchens spent five years litigating grams per kilogram. That fight is over. 1.6 grams per kilogram of bodyweight covers the hypertrophy ceiling for nearly every trainee lifting three or more sessions a week. Above that line, returns flatten. Below it, repair stalls.

Distribution is the live question now.

4 feedings of 40 grams beat 2 feedings of 80. Muscle protein synthesis runs on a refractory clock, not a storage tank. Overload one meal and the surplus oxidizes.

Breakfast is the weak link. Most lifters take in 12 grams before noon and 70 at dinner. That is backwards.

30 grams before 10 a.m. Non-negotiable past the age of 40.

Leucine sets the threshold. 2.5 grams per feeding flips the switch. Whey clears it at 25 grams of powder. Pea protein needs 35. Read the panel on the back, not the claim on the front.

Creatine works.

It is the only supplement on the shelf with three decades of replication behind it. 5 grams a day, monohydrate, no loading phase, no cycling, no micronized upcharge.

Skip the gummies. 4 of 6 gummy brands pulled off Seattle shelves this spring came in under label claim.

Protein powder: only if whole food falls short. It is a convenience product, not a supplement. Cottage cheese, eggs and chicken thighs do the same work for a third of the money.

Carbohydrate is not the enemy and never was.

The low-carb decade cost recreational lifters more training quality than any other idea of the 2010s. Glycogen pays for set volume. Cut it and the last three sets of every session quietly disappear.

3 to 5 grams per kilogram for anyone running four or more sessions a week. Higher on leg days. Lower on rest days when bodyweight is the target.

Fat has a floor, not a target. 0.6 grams per kilogram is that floor. Under it, hormones and satiety both fall, and the diet dies of hunger before it dies of math.

Fiber is the most neglected number in the Pacific Northwest.

38 grams a day for men. 25 for women. Most lifters hit half of that, then blame the protein for the gut trouble. It is the fiber.

Beans, oats, berries, cruciferous vegetables. Cheap, dull, effective.

Hydration got hijacked by electrolyte marketing. Sodium is a real variable for endurance athletes sweating past 90 minutes. It is not a variable for a 55 minute hypertrophy session in a 68 degree room.

Water. 35 millilitres per kilogram. Salt the food and move on.

Alcohol is the cleanest lever nobody pulls.

3 drinks blunt overnight protein synthesis. 6 wreck the following day's session outright. The arithmetic is unkind and it is consistent across every dataset that has looked at it.

Seattle makes this a local problem. The city has more taprooms per capita than squat racks. Two of those numbers are the same industry.

Timing is overrated. It is not irrelevant.

The anabolic window was oversold in 2009 and overcorrected in 2019. The honest position sits between the two. Total daily intake carries almost all of the load. Peri-workout feeding buys a thin margin for lifters training fasted before 7 a.m.

Fasted training is not superior. It is not inferior either. It is a scheduling choice wearing a physiology costume.

Bulking is over-prescribed. 300 calories above maintenance builds the same tissue as 800 and brings a third of the fat.

Cutting is under-planned. 0.7 percent of bodyweight per week is the ceiling before lean mass leaves with the fat.

Diet breaks work. 10 days at maintenance every 8 to 10 weeks restores training output, appetite regulation and mood.

The supplement aisle stocks 40 products. 3 justify the money: creatine, caffeine, vitamin D. The rest is inventory with a marketing budget.

Caffeine: 3 to 6 milligrams per kilogram, 45 minutes out. Cut it 8 hours before bed or the sleep debt eats the performance gain and then some.

Vitamin D is a latitude problem, not a wellness problem. Seattle sits at 47 degrees north under 226 cloudy days a year. 2000 IU daily, October through April.

Meal prep beats meal planning. A plan is a document. Prep is 40 minutes on Sunday and six containers in the fridge.

2 proteins, 2 carbohydrates, 1 vegetable, 1 sauce. Rotate the sauce, keep everything else. Novelty is the enemy of adherence.

Eating out is not a failure state. Order the protein, order the starch, skip the drink, leave.

Weigh food for 14 days, then stop. Long enough to learn portion sizes, short enough to avoid building a second job out of a kitchen scale.

Whole food first. Powder second. Pills last. That is the entire model, and every complication after it is packaging.

The best diet is the one measured in years, never weeks.
""".strip()

LONG_X_TRAINING_AS_PEOPLE = """
At 5:40 on a Tuesday morning, before the light gets over the hill, Renata Salcedo carries two bumper plates through her own kitchen and sets them by the back door without making a sound. The coffee is already burnt. On the stove there is a pot of cinnamon oatmeal her nine-year-old will refuse at 7:15, and then eat at 7:20, the way he does every week.

"The trick is the plates," she says. "You put them down like they are eggs. Otherwise the whole house is awake and my morning belongs to somebody else."

Renata is 38, a pediatric nurse on First Hill, and for six years she has coached a women's barbell group out of the driveway of her Beacon Hill bungalow. It began with three friends and a used squat rack she bought from a man in Kent who threw in a bar with a bent sleeve. There are 22 women in the group now. They train in two waves, Tuesdays and Thursdays, 6 a.m. and 7 a.m., under a canopy her husband Teo bolted into the concrete the winter the rain refused to stop.

Her hands tell the story better than any certificate on the wall. There is a callus at the base of each finger and a pale line across her right palm from a bar she caught badly in 2021. She keeps chalk in a coffee tin on the porch rail and a roll of athletic tape in the pocket of her jacket, next to a hair tie and a pediatric penlight she has never once remembered to leave at work.

The driveway holds four platforms if nobody parks badly. On a good morning it holds nine women, two thermoses and a golden retriever named Bishop who belongs to a neighbour and attends anyway.

"He is on the roster," she says. "He has better attendance than half of us."

The group is called Wednesday Club, which confuses everyone, because it does not meet on Wednesdays. It is named after the first session, which was a Wednesday, in a garage that is now her son's bedroom. Renata has been asked to change the name eleven times. She has declined eleven times.

Her mother, whose scepticism about weights lasted from 2019 until the afternoon Renata deadlifted her out of a bathtub after a hip replacement, now tells the neighbours her daughter is a trainer. Renata corrects her every time and her mother continues every time, and this has become one of the small permanent arguments of the family, conducted with great affection over the phone on Sunday nights.

What happens in the driveway is not complicated, and Renata is protective of that. Squat, hinge, press, pull, carry. Five sets of five for the first block, then three sets of eight, then a week where everybody does less than they want to. She writes the programme on an index card taped inside the recycling bin lid, because that is the surface at eye level when the lid is open, and she is the one who takes the bins out on Thursdays.

"People think a coach is somebody with a philosophy," she says. "A coach is somebody who remembers what you lifted last week. That is ninety percent of it. The rest is showing up before everyone else and making the coffee."

She keeps their numbers in a green notebook with a cracked spine, one page per woman, dated in her nurse's handwriting. Marguerite, 61, a retired ferry captain, whose first session ended in tears at a 15 kilogram bar and who pulled 90 kilograms off the floor last April. Ana and Bea, sisters, who argue in Tagalog about tempo and in English about everything else. Priya, who came in eight weeks after a c-section and spent a month doing nothing but goblet squats and breathing drills while Renata watched her ribs.

"I did not know I was allowed to be strong at 61," Marguerite says, over the fence, hands in her pockets. "Renata never made it a big announcement. She just kept adding two and a half kilos."

Teo makes breakfast on training mornings. He is a bus mechanic, up at four anyway, and he has developed a system involving one enormous pan of eggs and an alarming quantity of hot sauce. Their son sits at the counter with a book about sharks and narrates the driveway through the window, which is how the group learned that he refers to all of them collectively as the Ladies of Weight.

"He asked me last year why the ladies come to our house to be tired," Renata says, and laughs. "I told him it is the opposite. They come here tired and they leave less tired. He thought about it for a while and said that is not how tired works."

The rules of the driveway are short and unwritten and everybody knows them. Nobody comments on anybody's body. Nobody apologises for the weight on their bar. Nobody talks about what they ate. Renata enforces the third rule the hardest, and enforces it on herself first, because she spent her twenties in a gym in Georgetown where the conversation between sets was almost entirely calories, and she left that gym weighing less and lifting less and liking herself less.

"That room was full of people making themselves smaller," she says. "I did not want to build another one of those in my own house."

Each Saturday morning she opens the driveway to anybody who wants to try, and the sessions are free, and they always have been. A studio in Fremont offered to buy the name in 2024. Renata thought about it for a weekend, mostly at the kitchen table with a pencil and the back of an envelope, then said no in a single sentence and never brought it up again.

There are things she wants. A second rack. A roof that does not drip on platform three. A morning where nobody has to leave at 6:50 for a shift.

Mostly she wants Thursday to arrive so she can find out what Priya does with 70 kilograms.

"The best part of my week is not the lifting," she says, taping the index card back inside the bin lid. "It is watching someone realise the number went up while they were not paying attention. Every single time. That never gets old for me."

The plates go back under the porch at 8:05. The oatmeal gets eaten. The bins go out.
""".strip()

LONG_X_RECOVERY_AS_PEOPLE = """
Aaron Kalani is asleep by 9:15 most nights, which he is aware is a strange thing for a grown man to be proud of. His wife Bev finds it funny. His daughter finds it embarrassing. He keeps the blackout curtain in their Delridge bedroom taped at the corner with a strip of gaffer tape he took off a pallet at work, because the streetlight outside their window is the kind of orange that gets through fabric.

"That tape has been up four years," he says. "Bev has asked me to fix it properly maybe two hundred times. It is on the list."

Aaron is 51, a longshoreman at Terminal 18, third generation, and for most of his working life he treated recovery as something that happened to him rather than something he did. He lifted at a gym off Delridge Way three nights a week, slept when the shift schedule permitted, and iced whatever hurt on the drive home with a bag of frozen peas his mother-in-law had bought in 2013.

Then his back went. Not dramatically, which is the part he still finds insulting. He bent to pick up his daughter's swim bag off the hall floor and could not straighten.

"Nine hours a day of container work and it was a swim bag," he says. "A swim bag with one towel in it."

The recovery he built afterwards lives almost entirely in his house, which is the reason it has lasted. There is a foam roller under the couch in the front room, where he can reach it without a decision. There is a yoga strap looped over the closet door. On the kitchen table, next to the fruit bowl and the mail he has not opened, there is a spiral notebook where he writes two numbers every morning: hours slept, and how his back feels out of ten.

He has 1,340 mornings of numbers in there now, across four notebooks. Bev has suggested a phone app. Aaron has considered a phone app for four years.

"The notebook is on the table," he says. "The phone is in my pocket, and the pocket has the whole world in it. I am not opening the world at five in the morning."

His mornings are short and identical. Up at 4:40. Coffee. Ten minutes on the floor of the front room, hips and thoracic spine, in the dark, while the kettle cools. He calls it his ten minutes and he has done it, by his own count, on 91 percent of days since 2022, including the three days after his father's funeral, when Bev found him on the carpet at four in the morning working through the same six positions with his eyes closed.

Each Sunday he goes to the sauna at the community pool in West Seattle, where his daughter swims, and sits for twenty minutes while she trains. This began as convenience and turned into the thing he protects most.

"It is the only twenty minutes in my week where there is nothing to do," he says. "You cannot bring anything in there. No phone, no book, no talking to anybody, because it is a hundred and eighty degrees and nobody wants to chat. My shoulders come down about ten minutes in. I did not know they were up."

His daughter Malia, 16, whose scepticism about all of her father's routines is thorough and stated freely, has started sitting in with him for the last five minutes. She says it is because the changing rooms are cold. Aaron reports this development to anyone who will listen.

Bev is the one who enforces the bedtime, because Aaron will find one more thing to do in the garage every night of his life. She started calling 9 p.m. the announcement, in the tone of a flight attendant, and it stuck, and now their daughter does it too, from her room, without looking up.

There are things Aaron gave up. He stopped training four nights a week and settled at three, which took him two years to accept. He stopped icing everything. He stopped taking Saturday overtime he did not need.

What he got back he lists the way people list features of a truck. He can carry his own bags. He can sit through a swim meet on a metal bench for three hours. He has not missed a shift for his back in 27 months.

"People want the recovery thing to be a gadget," he says. "It is a curtain, a notebook and going to bed. It is the least interesting answer anybody ever gave, and it is the one that worked on me."

The tape on the curtain is still there. He points at it on the way out, almost fondly.
""".strip()

LONG_X_CULTURE_AS_FITT = """
The gym replaced the bar. That is the decade in one sentence.

Seattle lost 31 neighborhood bars between 2019 and 2025. It opened 44 fitness venues in the same window. The city did not get healthier. It found a new room to be lonely in together, and the new room has better flooring.

Run clubs won.

7 of the 12 fastest-growing fitness communities in the city are run clubs. Zero of them charge a membership fee. All of them finish at a coffee counter or a taproom, which is the entire business model of the thing that is not a business.

The format works because it asks for nothing. Show up, run 5 kilometres, leave. No contract, no front desk, no consultation about goals with a 23-year-old holding a clipboard.

Run clubs are also dating apps with better lighting. Everyone knows this. Nobody writes it in the group chat.

3 of the largest Seattle clubs now cap attendance. That is the tell. Scarcity arrived in the one corner of fitness that was built on abundance.

Boutique studios are in trouble.

$34 a class is not a fitness price. It is an entertainment price, and entertainment is the most competitive category in the economy. The studio is not competing with the gym down the street. It is competing with a concert ticket and a bar tab and staying home.

The 2016 cohort had one advantage: nobody else had figured out the room. That advantage is gone. 9 studios within a mile of Cap Hill now sell functionally the same 50 minutes.

Verdict: the boutique model survives only where the coach is the product and the coach is not replaceable.

The big-box gym is winning quietly.

$12 a month, 24 hours, no personality, no community, no candles. It is the least fashionable idea in fitness and it is taking share every quarter while the discourse looks the other way.

People do not want a tribe at 6 a.m. on a Wednesday. They want a squat rack that is free and a parking spot.

2 things sell a gym: proximity and availability. Everything after that is decoration with a monthly fee attached.

Hyrox is eating CrossFit's lunch.

Same appetite, different packaging. Competition without the identity commitment. A person can enter one race, train for 12 weeks, finish, and go back to a normal life without joining anything.

CrossFit asked for a lifestyle. Hyrox asks for a Saturday. The second ask is smaller and that is why it is spreading.

12 weeks is the perfect commitment length. Long enough to change something, short enough to picture the end of it.

Powerlifting's cultural share is falling and its technical standard has never been higher. Both facts are true. The sport got very good at itself while the audience walked to the next room.

The sauna is the new third place.

4 dedicated sauna and cold plunge venues opened in Seattle in 18 months. None of them sell exercise. They sell an hour with no phone in it, priced at $40, which is roughly what people used to pay for two drinks and a conversation.

The cold plunge is 20 percent physiology and 80 percent theatre. That ratio is fine. Theatre has value. The dishonesty is in pricing the theatre as medicine.

20 minutes with no phone in it is now a paid product. That is the whole culture in one line.

Gym etiquette got worse and the reason is the tripod.

Filming in a shared room converts other people into set dressing without their consent. 60 percent of large Seattle gyms have added some form of filming rule since 2023. The rules are unenforced and everybody involved knows it.

2 pieces of equipment define the era: the barbell and the tripod. Only one of them makes anybody stronger.

The phone is the new spotter. It gets used more and helps less.

Online coaching hit its ceiling.

$300 a month for a spreadsheet and a check-in message on Sunday is a product with no floor under its price. The market figured that out in 2024. What survives is in-person, hands-on and local, at 3 times the hourly rate and a fraction of the volume.

Credentials mean less every year. A weekend certification and 400,000 followers is the standard résumé, and neither half of it predicts whether a coach can fix a squat.

3 questions separate a coach from a content account: what did the client lift last week, what hurts today, what changes on Monday.

The best coaches in this city are largely invisible online. That is not romantic. It is a scheduling reality: a full book leaves no time to post.

Lifting content is 90 percent fine and boring. The other 10 percent is monetized outrage, and the outrage travels 40 times faster than the fine and boring, which is the whole distortion in one number.

Women's participation in barbell training in Seattle is up sharply since 2019. It is the single healthiest cultural shift in the sport and it happened almost entirely without institutional help, driven by garage groups, driveway clubs and word of mouth.

The industry did not build that. The industry is now trying to sell to it.

Class-based training peaked as a social technology, not a training technology. It solved attendance, which was always the real problem. It never solved progression, which is why the 3-year retention numbers stay ugly.

14 percent of members in this city use a gym more than eight times a month. The rest are paying rent on an intention.

Hybrid is the aesthetic of the moment. Lift heavy, run far, look like both. It is a demanding standard and most people running it are doing two sports badly instead of one sport well.

Longevity replaced aesthetics as the stated goal and did not replace it as the actual goal. The stated goal is VO2 max. The actual goal is the mirror. Marketing adjusted, behaviour did not.

Seattle's weather is the most underrated force in its fitness culture. 226 cloudy days a year builds indoor habits, and indoor habits build memberships. The rain is the industry's best salesperson and it works for free.

Group chats are the real infrastructure. Not apps, not memberships, not loyalty programs. A group chat with 14 people in it holds more attendance power than any retention software ever sold.

Nobody has monetized the group chat. Somebody will try in 2027 and it will fail, because the moment it costs money it stops being a group of friends and starts being a subscription.

The verdict on the whole scene: the equipment got better, the coaching got louder, the community got thinner, and the people who kept going are the ones who found four others to go with.

The best gym in Seattle is the one people never quit.
""".strip()


# ── The shape BOTH halves of the derivation corpus were missing ──────────────
# Gate 2 refuted the previous calibration with a reported HUMAN-INTEREST feature:
# an athletic-register section that is a story about a person rather than a story
# about data. Culture is REQUIRED to be that (the handbook opens it on a cultural
# observation), so it is not an edge case, it is the section. The derivation
# corpus contained reported copy and it contained profiles, and nothing in
# between, which is why the false positive was invisible here and obvious to a
# reviewer with fresh text.
#
# The cross half was missing the mirror image for the same reason: every
# wrong-register profile in it was a SATURATED profile. A long magazine profile
# is diluted with room-and-scene prose and tags a quote with the subject's
# surname now and again, and that is the version that sits near the line.

#: Culture, in register: reported, sourced, and about a person. 816 words.
LONG_IN_CULTURE_REPORTED_HUMAN_INTEREST = """
The wall of the stairwell at Foundry Barbell carries about two hundred names in
marker, and the oldest of them has been painted over twice and written back both
times by the same hand.

Ana Obradovic, 58, has swept that stairwell every closing shift for nineteen
years. She is not the owner and has never wanted to be. She came in 2007 to
clean three nights a week while her son was small, took over the front desk
when the previous manager left mid-shift, and has run the schedule, the
membership list and the arguments ever since.

"I never applied for anything here," she says. "Things just stopped having
anybody else attached to them."

The building is owned by a family trust that has held the block since the
1960s, according to county records, and the current lease runs to 2031. A
trustee named on the filing declined to discuss the arrangement. The management
company that collects the rent did not respond to two requests for comment.

That stability is unusual and the people who train here know it. Nineteen
independent strength rooms inside the city have closed since 2022, according to
a count maintained by the Seattle Small Business Council, and commercial rents
on light-industrial space rose 31 percent across the same period. Analysts who
track the sector say the survivors are almost all on long leases signed before
2019.

Obradovic's mornings start at four forty. Her husband drives her in on the days
the bus is unreliable, which is most of them in winter, and waits in the car
with the radio on until the lights come up inside. Her son, now 24, still has a
key.

What she does with the schedule is the part the members talk about. There are
eleven coaches on the board and none of them chose their own hours. She assigns
them, and she assigns them around the members rather than around the staff,
which two of the coaches said in separate conversations is the reason the
six o'clock hour has never once been cancelled.

"She knows who is in a bad year," one of them said. "She will not say it out
loud and she will not put a new coach in front of them."

The room itself is unremarkable. Fourteen platforms, a rack of bars that have
been re-knurled rather than replaced, and a heating system that the members
describe with more affection than it deserves. Attendance runs to about 340
members, a figure Obradovic keeps on paper and has never published.

She has been asked to. A regional chain approached the trust in 2021 with an
offer for the lease, according to two people with knowledge of the discussion,
and a representative for the chain did not return a call. The trust declined
the offer. Obradovic says she found out about all of it four months afterwards
and only because a member who works in commercial property told her.

"Nobody here tells me anything until it is over," she says. "That is fine. It
is not my building."

Her hands are the thing people notice. She has a wrist that has not bent
properly since a fall in 2014 and she moves plates one-handed without appearing
to think about it. She has never trained in the room she runs, and she says the
question embarrasses her every time somebody asks it.

The names on the stairwell started as a joke. A member wrote his own on the way
out after a first competition and Obradovic did not clean it off, which the
coaches read as permission and the members read as an instruction. There are
now names from four countries and at least two people who have died.

"I am not sentimental about it," she says. "I am sentimental about two of
them."

The trust's lawyer, reached by phone, confirmed the term of the lease and said
nothing further. A spokesperson for the county assessor's office confirmed the
ownership record.

What happens in 2031 is a question nobody in the building has an answer to.
Obradovic will be 63. She says she has not thought about it and then, later in
the same conversation, says she has a folder.

Her last act on a closing shift has not changed in nineteen years. She turns
the heaters down, checks the back door twice, and walks up the stairwell
looking at the wall on her way out.

The members have started a fund. It has 40 dollars in it and a name nobody will
admit to choosing, and Obradovic has told them twice that she will not touch
it. Two of the coaches say she checks the balance anyway.

The stairwell gets painted every spring by whoever is available. The names go
back on the same weekend, from a list Obradovic keeps in a ring binder behind
the desk, and she has never once got one wrong.
""".strip()

#: Training, in register: same shape, different section. 825 words.
LONG_IN_TRAINING_REPORTED_HUMAN_INTEREST = """
Four of the region's high-school throwing programmes have dropped their winter
lifting maxes entirely, according to the coaches who made the change, and all
four credit the same retired shot-putter with talking them into it.

Bea Kaufmann, 61, spent eleven years on a national team and thirty more
teaching biology in Renton. She has no formal coaching qualification and no
website. She has been driving to four schools a week since 2019 in a car her
daughter describes as structurally optimistic.

"I am not a coach," she says. "I am a woman with a stopwatch and opinions."

The change she argued for is unglamorous. The programmes replaced their
January testing week with eight weeks of submaximal work capped by bar speed,
and three of the four reported fewer in-season shoulder complaints across the
following spring. The fourth reported no change and its head coach said he is
keeping the format anyway.

Kaufmann did not invent any of it. She says so before anyone can say it for
her, and she credits a review published in 2018 that she found because a
student's mother left it on her desk.

Her mornings start at five. Her husband died in 2017 and she says the driving
is the part of the week she would keep if she had to give up the rest. Her
daughter comes on Thursdays and sits in the car with a laptop.

The resistance was not from the athletes. Two athletic directors declined to
comment on the record about the internal discussions, and a third did not
respond to a request for comment, but coaches at three of the four programmes
describe the same eighteen months of meetings.

"Nobody wants to be the person who stopped testing," one of them said. "It
looks like you stopped caring."

State participation figures show throwing events have lost 14 percent of their
entrants across the district since 2019, a decline the coaches attribute mostly
to specialisation elsewhere. Kaufmann attributes it to January.

"You cannot ask a sixteen-year-old to peak in a month and then wonder why she
is done by twenty," she says.

Her method with the athletes themselves is almost entirely conversational. She
learns names in the first session and uses nothing else for a fortnight. Her
notebooks, which she keeps in the boot of the car, run to nine volumes and are
organised by nobody's system but hers.

She acknowledges that the evidence she is working from is thin. Two of the
coaches said she raises this herself, unprompted, at every meeting, and one
said it is the reason he trusted her.

The athletic department at one of the four schools has begun paying her a
stipend. She insisted on being paid the same rate as the assistant coaches and
refused a title. A district spokesperson confirmed the arrangement and declined
to discuss the amount.

Her knees are the reason she stopped competing and she talks about them the way
other people talk about weather. She still demonstrates the first position with
a broom handle, once per athlete, and then never again.

"They should not be watching me," she says. "I am fifty years past useful."

What she will not do is travel. Three programmes outside the district have
asked and she has said no to all of them, and her daughter says the reason is
the drive home rather than the drive out.

Kaufmann keeps a list of every athlete she has worked with since 2019. There
are 214 names on it. She has not shown it to anybody and says the list is not
about them.

The four programmes have begun sharing their sheets. A district administrator
confirmed the arrangement and said it is informal and has no budget attached.
Two of the coaches say that is precisely why it works.

Kaufmann has been asked to write it up. She has declined three times, most
recently in an email that one of the coaches described as four words long.

Her car failed its inspection in March. The athletes found out and the fund
they started reached 900 dollars in eleven days, which she accepted only after
being told the alternative was that they would fix the car themselves.

The district's own participation figures are published once a year and have not
been broken out by event since 2018, a gap two of the coaches raised
independently. A district spokesperson said the reporting format is set at the
state level and declined to discuss whether it would change.

Three of the four programmes now run their January weeks as open sessions with
parents invited. The fourth does not, and its head coach says the reason is
space rather than principle.

What none of them has is a control group. Kaufmann raises this herself, every
time, and one of the athletic directors who declined to comment on the record
said it is the reason the change was approved rather than the reason it was
resisted.
""".strip()

#: Culture, WRONG register: a people profile, diluted with scene prose and
#: tagged twice by surname, so it clears the athletic gate on the way past.
#: This is the quiet version of the defect and it is the one that binds.
LONG_X_CULTURE_AS_A_QUIET_PROFILE = """
Imelda Varga keeps her chalk in a tobacco tin that belonged to her father, and
in twenty-two years she has never let anybody else open it.

She is 51, a hospital porter on permanent nights, and she has trained at the
same room on Airport Way since 2003. The building went up in 1948 as a marine
fitting works and kept the overhead crane rails, which are still bolted to the
ceiling above the platforms and which nobody has ever found a use for. The floor
is end-grain fir laid over concrete. It absorbs a dropped bar in a way that
newer rooms do not, and the regulars will tell you so at length.

Her shifts end at six in the morning. She sleeps from eight to two, trains at
three, and eats the meal she calls breakfast at five in the afternoon while her
husband eats dinner across the table. They have done this for nine years.

"I tried it the other way," Varga says. "I was miserable and everybody in the
house had to listen to me be miserable about it."

The room opens at four. There is no music and no front desk, and entry is a
five-digit code that has been changed twice since 2011. Fourteen platforms, a
rack of bars that have been re-knurled rather than replaced, and a heating
system that runs on a timer nobody can reset. Membership sits at about ninety
and has sat at about ninety since before the pandemic.

Varga grew up in Tukwila, the third of five. The tin held screws then. It has
held chalk since 1998 and gets cleaned out with a handkerchief on Sundays.

Her daughter trains in the same room on Saturdays and the two of them do not
speak while they are inside it. That was Varga's rule. Her son does not train
at all.

The room has changed hands three times, most recently in 2019, and each owner
has kept the same opening hours, the same code policy and the same refusal to
install mirrors. There is a whiteboard by the door that has said the same four
words since 2017. A clock above the chalk bowl has been eleven minutes fast for
at least a decade and the regulars have twice voted to leave it alone.

"I am not going to explain a hip hinge at four in the morning," Varga says. "I am
going to lift and then I am going to go home and go to bed."

Her routine has not moved in a decade. Four lifts, in the same order, written
into notebooks she buys in packs of five from a shop in Georgetown that has
closed and reopened twice.

The four o'clock hour is its own economy. Nurses, two bus drivers, a baker who
finishes at three and a man who has never told anybody what he does. Nobody
coaches anybody. The unwritten rule is that you may correct a person on safety
and on nothing else, and the last time somebody broke it the room discussed it
for a fortnight.

Her mother, who is 79 and lives in Renton, still asks whether the lifting is
sensible at her age. Her honest answer is that it is the only thing holding the
rest of the week together.

On bad-weather mornings her husband drives her in. He waits in the car with the
engine off and a flask, reading, and he has been doing it long enough that the
overnight cleaner knows his name.

2020 was the worst year. The room shut in March, reopened in July at a quarter
capacity, and did not return to normal hours until the following spring. Eleven
members did not come back. The owner at the time posted a sheet on the door
listing everybody who had kept paying, and the sheet is still there.

She trained in a garage on a borrowed bar that was never fully returned, and
the part she could not manage was not the training.

"Nobody to be quiet next to," she says. "That is the thing I missed. Not the
weights. The company of people who also do not want to talk."

Her weights have come down since. Three days a week now instead of five. The
reduction took two years to accept and about four minutes to feel better about.

The tin sits on the same corner of the same platform. The chalk in it came out
of a block bought in 2019 and is not finished.

The block outside has changed more than the room has. A parts distributor went
in 2016, a coffee roaster in 2018, and the lot on the corner has been a
permitted development site for four years with nothing on it. The rent on the
building has gone up twice and the current lease runs to 2029, which the
regulars discuss roughly as often as they discuss the clock.

At the end she wipes the bar down with the same handkerchief, puts the tin in
her coat, and walks out past the overnight cleaner without either of them
saying anything at all.
""".strip()


VAL_IN_SOCIAL_PEOPLE_ORDINARY = """
The kettle in Priya Raghunathan's kitchen goes on at ten past five, which is earlier than she would like and later than she used to manage. She fills two thermoses, one for herself and one for whoever forgets theirs, and sets them by the door next to her shoes. Her apartment is four blocks off Beacon Avenue. From the window over the sink, the hill is still a grey shape with a few lit rooms in it.

Raghunathan is 41, a transit planner for the county, and for six years she has organised the Tuesday and Saturday meetups of Foothill Social Run, a Seattle club that started with four people outside a bakery and now signs in somewhere between sixty and ninety.

"I was not trying to build a club," she says, screwing the lid onto the second thermos. "I was trying to have someone to run with on a Tuesday. Everything after that belongs to other people."

Her hallway is the clearest record of what the club has become. A plastic bin by the door holds spare headlamps, a roll of reflective tape, three unmatched gloves and a laminated route card that her husband, Amit, printed at his office and has since reprinted twice. Their daughter's cleats live in the same bin. Nobody has ever fixed this.

The Tuesday route is four and a half miles and has not changed since 2021. It goes down the hill, along the trail, past the bus base, and comes back up the long way, because Raghunathan decided early on that the climb should sit at the end, when people have already stopped worrying about their pace.

She sweeps the back of the group herself, every week, on purpose.

"The front takes care of itself," she says. "The person at the back is the one deciding whether to come again."

Amit, whose scepticism about run clubs was a standing joke in their building for most of a year, now handles the sign-in sheet and the group photograph. He is 44 and works in logistics, and he has developed firm opinions about lanyards. "I thought it was a phase," he says. "I was wrong in a way I do not mind being wrong about."

Saturdays are longer and slower and end at a cafe on 15th, where the owner, Beatriz, holds two tables from nine o'clock without being asked. Raghunathan buys the first coffee for anyone showing up for the first time, a rule she invented in the club's second month and has never once announced.

There have been three weddings out of the group, which she mentions the way other people mention weather, and one funeral, which she will not discuss on the record.

What she will discuss is logistics. There is a group text with 312 people in it. There are two volunteers who lead the slower pace group. There are the winter months, when the whole operation depends on whether enough people own a working headlamp. Every Sunday night she types the week's route into a shared document at her kitchen table while the dishwasher runs and Amit watches something with the sound low.

Her own training is unremarkable and she says so cheerfully. She runs four times a week and lifts twice at a gym on Rainier Avenue where she knows nobody at all.

"There is no secret to any of this," she says, and laughs. "I send the message. That is the entire skill. I have sent it every week for six years, including the week I had food poisoning, which was a mistake I would not repeat."

The club has no fee, no app and no sponsor, though a shoe brand asked twice last spring. Raghunathan turned both offers down, partly because she did not want to owe anyone a headcount, and partly because her daughter, who is nine, told her the free socks looked cheap.

At ten past six on a Tuesday, thirty people stand in the dark outside the bakery, and Raghunathan counts them twice with her hand in the air, the way she has counted them every Tuesday since the year there were four.
""".strip()

VAL_IN_RECOVERY_FITT_LONG = """
Recovery is a category now. Most of it is priced well above its evidence.

Sleep is the base layer. Everything else is decoration on top of it.

7 to 9 hours per night. That single range moves strength, mood, appetite and injury rate at the same time. Nothing else on this list is in the same weight class.

Sleep debt compounds. Five mediocre nights in a row cost more than one terrible night.

Naps work. 20 to 30 minutes, finished before 3pm.

Cold plunge after lifting: overrated. Cold blunts the growth signal from a hard session. Lifters who plunge inside four hours of a hypertrophy block leave size on the table.

Cold plunge for mood: fine. It works, it feels like it works, and the effect is worth something. It just belongs on rest days.

Sauna is the better purchase. 15 to 20 minutes, three or four times a week, after training rather than before it.

Contrast showers are a wash. No harm, no measurable benefit, decent theatre.

Massage guns are a warmup tool in a recovery costume. They raise tissue temperature and make people feel loose. That is the whole product.

Foam rolling has one job. 5 minutes before a session, for range of motion. It does not remove soreness and it never has.

Soreness is not a scoreboard. The most productive training blocks are frequently the least sore ones.

Compression boots feel excellent. The performance case behind them is thin. Renting beats owning.

Protein is recovery infrastructure. 1.6 to 2.2 grams per kilogram of bodyweight per day, split across three or four feedings.

Total intake outranks timing. The anabolic window is a marketing object with a 24-hour footprint.

Carbohydrate is the recovery nutrient nobody bothers to sell. Athletes training twice a day need 5 to 8 grams per kilogram to hold output through week three.

Underfeeding is the most common recovery failure in this city. It gets misdiagnosed as overtraining every single winter.

Alcohol is the fastest way to erase a good training week. Three drinks does more damage to overnight recovery than one skipped session.

Deloads are structural, not optional. Every fourth to sixth week, volume drops 40 to 50 percent while intensity holds.

The deload nobody schedules gets taken by force later, usually in February, usually as an injury.

HRV apps are useful as a trend and useless as a verdict. A single red morning means nothing. Nine red mornings out of fourteen means the block is too heavy.

Resting heart rate is the cheaper signal. 5 beats above baseline for three consecutive mornings is a real flag.

Active recovery is oversold for lifters. Rest days beat shakeout days for anyone training four hard sessions a week.

Walking is the most underrated recovery tool in Seattle. 8,000 steps on an off day, outdoors, no headphones required.

Stretching does not prevent injury. It improves range of motion. Those are two different products sold under one label.

Mobility work belongs at the front of a session, not the end. 6 to 8 minutes, targeted at the joints the session actually loads.

Ice on an acute injury: 48 hours, then movement. Longer than that and the swelling stops being the problem.

Habitual ibuprofen around training is a bad trade. It buys comfort this week and blunts adaptation across the block.

Massage is a luxury with a real effect on how training feels and a small effect on how it goes. Both things are true.

Float tanks are entertainment. Priced as medicine.

Cryo chambers are entertainment with worse air.

Rest between sets is training, not recovery. 2 to 3 minutes on compounds. Cutting it to 60 seconds turns a strength session into conditioning by accident.

Off-season is a real word. Two weeks fully off, once a year, resets more than any supplement stack in the store.

The recovery budget has an order of operations. Sleep first, food second, deloads third, everything else after that.

Most people buy the fourth thing and skip the first three.

Sleep is the only recovery tool that has never been oversold.
""".strip()

VAL_IN_TRAINING_ATHLETIC_FOLLOWING_A_COACH = """
Rainier Barbell occupies a former print shop in Georgetown, and on Monday nights the loudest object in the room is a sensor the size of a phone clipped to the end of a barbell. The gym's head coach, Tessa Nurmi, has spent three years programming her lifters against bar speed rather than against a percentage of their best single. She calls the method a velocity cap, and the rule fits on the whiteboard beside the chalk bowl: when the concentric speed of a working repetition falls below 0.30 meters per second, the set is over, regardless of what the program says.

"The number on the sheet is a prediction," Nurmi says. "The number on the bar is a measurement. When the two disagree, I take the measurement."

Nurmi arrived at the method after a bad season. In 2022, by her own count, seven of the nineteen lifters in her competitive group missed four weeks or more with an injury, and two withdrew from a regional meet during weigh-in week. Her training logs from that year, which she shared with TIMBR, show missed prescribed repetitions clustering in the fourth week of every block, the week her athletes were scheduled at 87 to 92 percent of a one-repetition maximum tested in December.

A Monday session under the current system runs about seventy minutes. Nurmi programs six to eight working sets across two main lifts, with a target repetition range rather than a target total. Lifters warm up to a load that moves at roughly 0.55 meters per second, then add weight until the bar slows to the cap. According to the gym's session logs, the average squat session in the group now ends at 21 total working repetitions, down from 28 under the percentage-based plans Nurmi used through 2022, while average session load has risen by 6 percent.

Marcus Teale, a 400-meter runner who lifts with the group twice a week in the off-season, says the change was uncomfortable at first. "I spent a decade being told to finish the sets," Teale says. "Being sent home with two sets left on the page felt like getting away with something. It stopped feeling that way around week five, when I was still fresh on Thursdays."

The method has been measured locally. Ines Bardales, an exercise physiologist at the Duwamish Human Performance Lab, ran a fourteen-week comparison beginning in January, enrolling 31 trained lifters from four Seattle gyms, of whom 26 completed the protocol. Half followed a conventional percentage-based plan and half trained under a 0.30 meter-per-second cap, with matched exercise selection and matched session frequency at three days per week. Bardales says the two groups were within 2 kilograms of one another on baseline back squat.

The lab reported that the velocity-capped group finished with a mean back squat increase of 12.5 kilograms against 11.1 kilograms for the percentage group, a difference Bardales describes as inside the noise. The training-load numbers separated more clearly. The capped group performed 17 percent fewer total repetitions across the block and recorded 41 percent fewer sessions rated 9 or above on a ten-point exertion scale. Adherence, which the lab tracked by attendance, was 91 percent in the capped group and 78 percent in the comparison group.

"The strength result is a tie, and I would report it as a tie," Bardales says. "What is not a tie is the cost. One group bought the same result at a lower price in fatigue and showed up more often to buy it."

Not everyone reads the data the same way. Halvard Pinn, a strength scientist at Cascadia University who was not involved in the study, notes that velocity thresholds drift with technique, bar type and even sleep, and that a single cutoff applied across a mixed group invites error. Pinn points to his own group's 2024 work, in which day-to-day variation in a lifter's velocity at a fixed load reached 0.08 meters per second, roughly a quarter of the cap Nurmi uses. "A cap can be a useful governor," Pinn says. "It is a poor prescription on its own, and it is close to meaningless without a stable technical model."

Nurmi does not dispute the drift. She says her group re-establishes each lifter's velocity profile every four weeks, a process that costs one full session, and that lifters with fewer than eighteen months of training are kept on repetition targets until their technique stabilises. Sensors cost the gym about 400 dollars per unit, she says, and Rainier Barbell owns five, shared across a roster of 34 members who train in three squads.

Adoption in the city is still narrow. A survey of 44 Seattle strength facilities conducted last spring by the Puget Sound Strength Collective found 9 gyms using velocity measurement in any form, and 3 using it as a stopping rule rather than as a feedback display. The collective's director, Rosalind Achebe, says cost is only part of it. "Coaches are asked to give up the thing that made them feel like coaches, which is the plan," Achebe says. "Handing that authority to a sensor is a professional adjustment before it is a technical one."

Nurmi's competitive results since the switch are modest and she reports them plainly. Across two seasons, her group has recorded 11 personal bests in the back squat and 8 in the deadlift, against 14 and 9 in the two seasons before the change. Injury weeks, which she defines as any week a lifter cannot train as written, fell from 61 across the roster in 2022 to 24 in 2024. Meet attendance rose from 12 lifters to 19.

She is now testing a second constraint, a per-session repetition floor, after noticing that three lifters were finishing sessions at 14 repetitions and losing conditioning across a block. Bardales is designing a follow-up with 60 participants and a 20-week window, funded, she says, by the lab rather than by any equipment manufacturer.

"I am not claiming this makes anyone stronger than the old way," Nurmi says. "The claim is smaller than that. It makes the same strength cheaper, and it keeps more of them in the room in March."
""".strip()

VAL_IN_NIGHTLIFE_FITT_OPINIONATED = """
Seattle trains late. The city has decided this quietly, without a press release.

9pm is the new second rush hour. Squat racks in Capitol Hill and Belltown run at capacity until 10:30 on weeknights.

Late training is not a compromise. Strength output peaks in the late afternoon and holds well into the evening. The body does not know it is dark outside.

Grip strength, power output and core temperature all sit higher at 8pm than at 6am. The morning crowd is training uphill and calling it discipline.

24-hour gyms are the best value in the city. Half the price, a third of the crowd, none of the queue for a bench.

The 11pm room is a different sport. Nurses, line cooks, bartenders, airport staff. Nobody is filming anything.

Night run crews solved the group-training problem before the gyms did. Lit routes, a bag drop, a bar at the end.

3 miles then a beer is a real training culture. It has kept more people running than any race entry ever has.

The bar-at-the-end model has one flaw. Two drinks after a session cuts overnight recovery more than the session gave back.

One drink is the honest ceiling on a training night.

DJ-lit spin rooms are entertainment with a heart rate attached. That is not an insult. Entertainment gets people through the door 40 times a year.

Late lifting has a genuine cost and it is sleep, not performance. A session ending at 10 is fine. A session ending at 10 followed by a 6am alarm is a slow injury.

90 minutes between the last set and the pillow. That is the buffer that makes night training sustainable.

Caffeine is where night lifters wreck themselves. A pre-workout at 8pm is still working at 2am.

2pm is the cutoff for anyone training after dark.

Cold showers before bed do nothing for sleep. Warm ones work better and cost nothing.

Night training and shift work are not the same problem. Rotating shifts break the clock. A stable 9pm session builds one.

Consistency of hour beats choice of hour. The same session time six days a week outperforms a smarter time hit at random.

The last light rail matters more than the program. Any gym that cannot be reached at 10:45 without a car is a gym for three months, not three years.

Neighbourhood beats equipment after dark. A mediocre gym eight minutes from home wins against a great one across the bridge, every week, forever.

Late group classes are shrinking and late open-gym hours are growing. The city wants the room, not the instruction.

Front desk staff after 9pm are the most underrated asset in Seattle fitness. They set the temperature of the whole room.

Headphones are the etiquette. Conversation is welcome, volume is not.

The 10pm crowd re-racks better than the 6am crowd. This is not a moral fact. It is just true.

Sunday night is the sleeper session. Empty floors, no music, the best hour of the week to train hard in this city.

Nightlife and training stopped being opposites here around 2021. The run club is the pre-game now.

The best night session is the one that ends before midnight.
""".strip()

VAL_IN_NUTRITION_PEOPLE_QUOTE_HEAVY = """
Renata Silvas is peeling boiled eggs over the sink in her Beacon Hill kitchen, and she is losing. The shells come off in flakes. Nine eggs sit in the colander, pitted like golf balls, and a tenth is disintegrating between her thumbs.

"Four years of this and I have never once got it right," she says. "Tomas has a method. Baking soda in the water, and a spoon under the shell. I do not believe in the spoon."

She is 39, a night baker at a bread house in Georgetown, which puts her body clock about eight hours behind the rest of Seattle. Her dinner happens at nine in the morning. Her breakfast, the meal she thinks about most, travels to work in a dented steel tiffin that belonged to her mother, and it goes into her bag at half past ten at night.

"People hear night shift and they assume I eat garbage," she says. "For two years I did. I ate whatever came out of the proof box at three in the morning. Croissant ends. The heels of the sourdough. I was not hungry, exactly. I was awake, and awake is not the same thing as hungry, but at three in the morning the body cannot tell the two apart. So you eat. And then at seven you are angry and you do not know why."

Every Sunday she cooks in one long block, from about noon until her daughter Ines gets bored of helping, which is usually around ninety minutes in. Ines is 11 and has opinions. The rice goes in the big pot. The chicken thighs go in the oven on two sheet pans, one seasoned for the adults and one plain, because Ines has been in a plain phase since March.

"The tiffin is the whole system," she says, and pulls it down off the shelf to show it. Three tiers, steel, the lid dented on one corner from a fall her mother never explained. "Bottom is rice. Middle is whatever protein I made on Sunday. Top is the vegetable, and the top tier is the one I skip when I am in a hurry, which I know is backwards. My mother used the same box for thirty years in Porto Alegre and she never once skipped the vegetable. She would be disgusted with me."

Silvas, whose scepticism about protein powder outlasted her scepticism about the gym itself, took nearly two years to buy a tub of it.

"I thought it was for a different kind of person," she says. "Men in the parking lot with a shaker. And then my coach at the gym on Airport Way asked me to write down what I actually ate in a week, not what I meant to eat, and the number was so low it embarrassed me. I was getting maybe sixty grams. She wanted a hundred and thirty. There is no version of my schedule where I chew a hundred and thirty grams of protein. So now there is a scoop in the tiffin bag, and I drink it in the van at four in the morning, and it tastes like chalk, and I am fine with that."

Tomas, her husband, does the school run and therefore owns the mornings she does not.

"She comes home when I am putting the coffee on," he adds. "She eats a full dinner at nine and I am eating toast. It looked insane to me for about a year. Then I watched her stop falling asleep at the wheel on Fourth Avenue South, and I stopped having an opinion about it."

Each Tuesday and Thursday she trains before her shift, at seven in the evening, which she describes as her lunch break with weights. She likes the deadlift and tolerates everything else. She has a note on her phone with four numbers on it, all of them heavier than they were in the spring.

"The food part took longer to believe than the lifting part," she says. "With lifting you see it in a month. With food you see it in your sleep first, then your mood, then months later you notice your arms. Nobody tells you that. They sell you the arms."

She rinses the last egg, gives up on the shell, and eats it broken over the sink.

"My mother thought protein was a thing you worried about if you were poor," she says. She laughs. "I told her on the phone that I count it now and she said, in Portuguese, that I have become a rich person's problem. She is not wrong. But she is also 71 and she carries her own groceries up two flights, so whatever she did, it worked."

The tiffin goes into the bag at 10:30. The rice is from Sunday. The vegetable, tonight, is in the top tier.
""".strip()

VAL_IN_CULTURE_ATHLETIC_PLAIN = """
The Foundry, a 5,800-square-foot strength gym on Leary Way in Ballard, reports 1,240 active members and a twelve-month retention rate of 71 percent. Dee Nakashima, who opened the facility in 2019 after eleven years managing commercial clubs, says the retention figure is the only number she reviews weekly. Revenue and headcount are reviewed monthly. "Retention is the only number that reports on the room," Nakashima says. "Everything else reports on the marketing."

The regional baseline is lower. Corinne Adeyemi, an analyst at Puget Retention Group, a Seattle consultancy that tracks independent fitness operators, puts twelve-month retention across 88 surveyed facilities in King and Snohomish counties at 54 percent for 2025, down from 57 percent in 2023. Adeyemi says gyms in the 4,000 to 8,000 square foot range with in-house coaching staff cluster near the top of that distribution, and that The Foundry sits in the ninetieth percentile of her sample.

Head coach Ellis Braun attributes part of the gap to the intake process. Every new member completes three onboarding sessions of roughly 90 minutes each before receiving unrestricted access to the floor. The sessions cover barbell technique, machine setup and the gym's written rules. Braun says the gym ran 412 onboardings in 2025 and that 84 percent of those members were still training at the six-month mark, against 61 percent of the 74 members who joined through corporate partnerships and skipped the sequence.

The written rules number four and are printed on a board near the water fountain. Chalk stays in the bucket. Bars are stripped after use. Phone calls happen in the stairwell. Anyone may be asked to share a rack. Nakashima says the list has not changed since 2020 and that the fourth rule generates almost all of the friction. Staff logged 31 rack disputes in 2025, she says, down from 58 in 2022, a decline she attributes to the addition of four racks rather than to any shift in member behavior.

Nils Ferreira, a sociologist at the University of Washington who studies informal membership organizations, has interviewed 240 members across six Seattle gyms since 2023 for a project on what he calls repeat-contact settings. Ferreira says gyms with published behavioral norms produce measurably higher rates of member-to-member acquaintance, and that in his sample the median member of a rules-posting gym could name 9 other members by first name, against 3 at gyms without posted norms. He cautions that the direction of the relationship is unresolved.

Morning traffic dominates the schedule. Alma Reyes, who manages the front desk and has worked at the gym since 2021, says 38 percent of check-ins occur before 7 a.m. and that the pre-7 group accounts for a disproportionate share of long-tenured members. Reyes says 63 of the gym's 91 members with five or more years of continuous membership train in the morning block. The gym opens at 5 a.m. on weekdays and 7 a.m. on weekends.

Staffing is unusually stable for the category. Braun says seven of the gym's nine coaches have been on staff for three years or longer, with average tenure at 4.1 years. Adeyemi puts median coach tenure at independent Seattle gyms at 14 months and at national chains at roughly 9 months. Braun says coaches at The Foundry are salaried rather than paid per session, a structure Nakashima adopted in 2021 after two departures, and that the change raised payroll by about 19 percent in its first year.

The class program has been the main source of internal disagreement. Attendance across the gym's 22 weekly classes rose 17 percent in 2025, and the additional sessions reduced open-floor access during the 6 p.m. hour. Nakashima says roughly 40 members raised objections, in writing or at the desk, over a four-month period. The gym responded by capping evening classes at two concurrent sessions and forming a six-member advisory council that meets quarterly. Reyes says complaints on the issue fell to two in the following quarter.

Pricing has moved twice. Membership is $109 a month with no contract, following increases of 4 percent in 2024 and 3 percent in 2026. Nakashima says the 2024 increase produced 27 cancellations in the following 60 days, about 2 percent of the membership, and that the 2026 increase produced 19. Adeyemi says that response is smaller than the 6 to 9 percent she typically records after price changes at comparable facilities, and that low price sensitivity is generally the clearest available proxy for what operators describe as culture.

Competition arrived in 2024, when a national chain opened a 24-hour location 0.6 miles south at $29 a month. Nakashima says the gym lost 34 members in the first quarter after the opening and regained 22 of them within a year. Adeyemi says overlap between the two membership bases is limited, and that in her 2025 survey only 11 percent of members at coached strength gyms listed price as their primary consideration, against 48 percent at budget chains.

Ferreira says the durability of any of this is unproven. His interview data covers three years, and he says the failure mode he most often records is founder dependence: gyms whose norms are enforced by an owner on the floor tend to lose those norms within eighteen months of that owner stepping back. January remains the sharpest test. The Foundry added 96 members in January 2026 and had lost 41 of them by April, an attrition rate Nakashima describes as unchanged in seven years.

A second location is under review. Nakashima says a Georgetown site of about 6,500 square feet is under negotiation and that she expects to decide by March. Braun says the constraint is staffing rather than capital, and that opening would require promoting two current coaches and hiring three more. "We can find the money," Braun says. "The question is whether we can find six people who will still be here in 2030."
""".strip()

VAL_X_SOCIAL_AS_ATHLETIC = """
Participation in organized group training across Seattle rose 41 percent between
2023 and 2026, according to figures released this month by the Puget Sound
Recreation Council, which has tracked registered club activity in King County
since 2011. The council counted 312 active clubs at the end of the last reporting
period, up from 221 three years earlier, with the sharpest growth in
neighborhood-level run clubs and outdoor strength meetups. Council research
director Priya Nair says the increase is concentrated in clubs that charge
nothing at the door. "The paid boutique segment has been flat for four
consecutive quarters," Nair says. "Everything moving is free and outdoors."

The council's data set draws on permit filings, park reservations and a
volunteer-reported attendance survey returned by 188 of the 312 clubs. Nair
cautions that the survey skews toward larger organizations, which have staff to
complete it, and that the true club count is probably higher. Median reported
attendance at a weeknight session was 34 people. The top decile of clubs
reported median attendance of 140. Fourteen clubs reported sessions exceeding
400 participants, all of them in the Ballard, Capitol Hill and Georgetown
corridors, and all of them convening between 6 and 7 p.m. on weekdays.

A separate analysis from the Kirkwood Institute, a Seattle sports-behavior lab
attached to the University of Washington, examined why participants stay. The
lab followed 640 first-time attendees across 22 clubs for 18 months. Retention
at six months was 52 percent for participants who reported making at least one
new acquaintance in their first three sessions, against 19 percent for those who
did not. Lead investigator Marcus Ehlert notes that the effect held after
controlling for prior training experience, commute distance and age. "Social tie
formation in the first three weeks is the strongest single predictor we
measured," Ehlert says. "It outperforms fitness level by a wide margin."

Ehlert's group also recorded a drop-off pattern the lab calls the fourth-week
cliff. Attendance across the sample fell 31 percent between week three and week
five, then stabilized. Clubs that assigned new attendees to a named pace group
or a rotating partner saw the same drop-off reduced to 12 percent. Ehlert says
the finding has been circulated to 40 Seattle clubs and that nine have adopted a
formal pairing protocol. Follow-up data on those nine is due in the spring.

Cost structure varies. The council's figures put the median annual operating
budget of a Seattle run club at 2,400 dollars, funded largely through apparel
sales and sponsorship from local cafes and breweries. Twenty-eight percent of
clubs reported no budget at all. Only 6 percent charge a membership fee, at a
median of 15 dollars per month. Nair says the sponsorship model has proved
durable through two soft retail years, though she notes that renewal rates
among cafe sponsors dropped from 81 percent to 66 percent over the same period.

Growth has produced friction with the city. Seattle Parks and Recreation
recorded 74 complaints in the last fiscal year relating to group training in
public spaces, up from 29 the year before, most concerning noise, trail
congestion and equipment left on turf. Department spokesperson Alan Doe says the
agency is drafting a group-use registration process that would apply to
gatherings above 50 people. Doe says no fee is currently proposed. The Puget
Sound Recreation Council has objected in written comment, arguing that
registration would suppress exactly the free, low-overhead formats driving the
growth.

The council projects the club count will pass 400 by the end of 2027 if current
rates hold. Nair says that projection assumes no regulatory change and no
material shift in sponsorship. Ehlert is less certain about the ceiling. "We
have never seen a participation curve like this in a single metro," he says.
"Nobody in this field knows where it flattens."
""".strip()

VAL_X_SUPPLEMENTS_AS_PEOPLE = """
The tub of creatine on Delia Okonkwo's kitchen counter has lost its label. She
peeled it off in January because the branding clashed with the tile, and now it
sits beside the kettle, an anonymous white cylinder that her husband keeps
mistaking for flour.

Okonkwo is 41, a pediatric nurse at a clinic in Beacon Hill, and she has been
taking the same five grams every morning for eleven years. She measures it with
a chipped teaspoon that came with a set her mother gave her when she moved out
at nineteen. "The scoop that comes in the tub is always buried," she says. "I
gave up looking for it in about 2017."

Her mornings run on a fixed order. Kettle on at 5:40. Creatine into the bottom
of a glass, hot water, stir, then cold water on top so she can drink it fast.
Then her scrubs, then the twins, then the 6:50 bus. The twins are nine and have
opinions about the glass. "Ben thinks it looks like a science experiment," she
says. "He's not wrong."

Okonkwo came to the habit sideways. She was not an athlete. She started lifting
at 30 after a back injury put her on desk duty for four months, and a colleague
in the ortho ward, a woman whose scepticism about supplements was total,
mentioned that creatine was the one thing she had bothered to read the papers
on. "Sandra hated everything in that industry," Okonkwo says. "So when Sandra
said take it, I took it."

Her husband, Theo, a high school geography teacher, does not take it and finds
the whole ritual faintly comic. He has a running joke about the unlabeled tub
that has been going for three years. She lets him have it. On Sundays they do
the shopping together and he puts the replacement tub in the cart without being
asked, which is its own kind of agreement.

There have been lapses. Two weeks in 2021 when the twins had chicken pox. A
month after her father's funeral in Lagos. She says she noticed nothing dramatic
either time, and she is careful about that. "People want me to say I felt weaker. I didn't feel
anything," she says. "It's not that kind of thing. It's a small edge, and small
edges don't announce themselves."

What she does notice is the rest of it. She keeps a protein powder in the
cupboard for the days a shift eats her lunch, which is maybe twice a week. She
bought a vitamin D bottle in her first Seattle winter and still finishes one
each year. Everything else has come and gone: the greens powder a friend sold
her, the pre-workout she took twice and hated, a collagen tub that went to a
neighbor. "The cupboard used to be full," she says, laughing. "Now it's three
things and a lot of tea."

Her daughter, Ada, has started asking about it. Nine years old and reading the
back of everything. Okonkwo has decided she will explain it properly when Ada is
older, the way she explains medication at work, dose and reason and evidence,
nothing mystical. For now the answer is that it is a powder that helps mum lift
heavy things at the gym, and that is enough.

She lifts three evenings a week at a converted warehouse near the clinic, and on
Tuesdays she takes both twins because the childcare is free and Ada likes to
count her mother's reps out loud. On those nights the teaspoon sits clean in the
drainer at 9 p.m., waiting for 5:40.
""".strip()

VAL_X_CULTURE_AS_PEOPLE = """
There is a laminated sheet taped to the inside of the equipment cage at Ironbark
Barbell in Georgetown, and it has been there long enough that the tape has gone
amber. It reads: PUT IT BACK. SAY HELLO. DON'T FILM ANYONE. Rowan Achebe wrote
it in 2019 on a lunch break, printed it at a copy shop on Airport Way, and has
replaced it exactly twice.

Achebe is 47, a former structural engineer who now owns and coaches at Ironbark
six days a week, and she still has an engineer's hands, thick at the knuckle,
with a permanent callus on the left palm where the bar sits wrong. She arrives
at 5:15 every morning. She opens the roll-up door herself, turns on the two
back heaters, and puts on whatever record is stacked on the crate by the stereo.
"Whoever closes picks tomorrow's record," she says. "That's the only rule about
the music. It has caused more argument than the deadlift platform ever did."

Her gym occupies the ground floor of a building that used to make marine
fittings, and the ceiling is high enough that a dropped barbell sounds like
weather. There are 40 members. There has been a waiting list since the spring of
2023 and Achebe has refused, three times now, to expand into the empty bay next
door. "Every person who has ever offered me money to make this bigger has
described a room I would not want to train in," she says.

She grew up in Rainier Beach and did not touch a barbell until she was 34. Her
introduction was a chain gym on a January promotion, where she trained for two
years and spoke to nobody. "Two years," she says. "I could tell you what
everyone's headphones looked like. I could not tell you one name." That silence
is the origin story of the laminated sheet, and she is unsentimental about
saying so.

Her partner, Neve, a landscape architect whose scepticism about small-business
ownership was well documented at the time, co-signed the original lease in a
kitchen in Beacon Hill over a bottle of wine and a spreadsheet Achebe had built
in her old work software. Neve keeps the books now. They live twenty minutes
away in a house with a garage that Achebe swore would not become an overflow
storage unit for chalk and collars, and which is, she admits, exactly that.

The culture she has built runs on a set of small, stubborn practices. New
members are walked around and introduced by name to everyone in the room on
their first day, which takes fifteen minutes and which Achebe does personally.
Phones live in a wooden box by the door unless someone is filming their own set,
in which case they call it out first. There is a whiteboard for personal records
and a separate whiteboard, larger, for what Achebe calls the small wins: a member
who came back after surgery, someone's first full push-up, a member who finally
learned everyone's name.

"People think the culture is the loud stuff," she says. "The cheering. It isn't.
It's whether the plates are on the right pegs when you walk in at five in the
morning. It's whether somebody noticed you were gone for a week."

Her Tuesdays are the busiest. The 6 p.m. session runs to about eighteen people
and it is the one she coaches herself, moving between platforms with a piece of
chalk behind her ear, correcting a hip angle with two fingers and a word. On
Tuesdays a member named Ellis, 68, a retired ferry engineer, brings a thermos of
coffee and shares it with whoever is closing. This has happened every Tuesday
for four years. Achebe considers the thermos a load-bearing element of the
building.

She has been offered a podcast. She has been asked, twice, to franchise the
name. A clothing company from Portland wanted to shoot a campaign in the room
and offered enough to cover a quarter's rent. She said no to all of it, and she
says the reasons are less noble than people assume. "I'm not principled," she
says. "I'm tired. I know what this room costs me to keep good, and I don't have
another one of these in me."

There have been failures she brings up unprompted. A coach she hired in 2021 who
was technically excellent and made two members quit, and whom she kept on for
five months longer than she should have. A period after her mother died when she
stopped doing the introductions and watched, over about six weeks, the room go
quiet again. "That was the scariest thing I've seen here," she says. "It took
nothing. It took me being sad for a month and not talking to people, and the
whole thing started sliding back to that chain gym."

Her own training is unglamorous now. Three days a week, moderate, at a weight
she describes as boring. She does it at 4 p.m. before the evening rush, alone,
and she says the alone part is deliberate. "I need one hour where I am not
anybody's coach," she says. "Otherwise I get resentful, and resentful is the end
of a place like this."

At close she sweeps the platforms herself. The record on the stereo is whoever
locked up the night before. Ellis's thermos is upside down in the drainer. The
laminated sheet is still on the cage door, amber at the corners, and Achebe says
she will replace it when it falls off and not a day sooner.
""".strip()

VAL_X_NIGHTLIFE_AS_ATHLETIC = """
Late-night training volume in Seattle has grown faster than any other time block
over the past four years, according to access-control data compiled by the Puget
Sound Facilities Association, a trade body representing 140 gyms across King and
Snohomish counties. Entries logged between 9 p.m. and 2 a.m. accounted for 11.4
percent of all recorded visits in the last quarter, up from 4.9 percent in 2022.
Association analyst Teodora Vance says the shift is not evenly distributed.
Twenty-four-hour facilities inside the city limits recorded a 19 percent
late-block share, while suburban sites with staffed hours recorded 3 percent.
"The pattern follows shift work and it follows density," Vance says. "It does not
follow marketing spend, which is what most operators assumed."

The association's figures draw on anonymized badge and keypad records from 96
member sites that agreed to share data, representing roughly 210,000 individual
members. Vance cautions that the sample overrepresents chain operators and
excludes boutique studios, which rarely operate past 9 p.m. Median session
length in the late block was 47 minutes, against 61 minutes for the 5 to 7 p.m.
peak. Vance says the shorter sessions are consistent across every site in the
sample and across every month measured, and that the association has not yet
established a cause.

A study published in March by the Kirkwood Institute examined performance and
recovery outcomes in 214 Seattle residents who trained primarily after 9 p.m.
Participants were monitored for 14 weeks using wrist actigraphy and weekly
strength testing. Principal investigator Lena Brochu reports that late-block
trainees averaged 38 minutes less total sleep per night than a matched daytime
group, and that the gap widened over the study period rather than narrowing.
Strength gains, measured on a three-lift composite, were statistically
indistinguishable between the two groups. "The training worked," Brochu says.
"The sleep did not recover. Those are separate findings and we are careful not
to collapse them."

Brochu's group reported a secondary result concerning caffeine. Late-block
participants consumed a median 180 milligrams within two hours of training,
against 40 milligrams in the daytime group. Among participants who reported zero
caffeine after 6 p.m., the sleep deficit fell to 11 minutes. Brochu notes that
the subgroup was small, 31 participants, and that the finding should be treated
as preliminary. A larger replication is scheduled for the autumn with funding
from the association and from Seattle Parks and Recreation.

Operators report a different set of pressures. Ironclad Fitness, which runs six
sites in the metro, moved three locations to 24-hour access in 2024. Operations
director Samir Whitlock says late-block members show 22 percent higher annual
retention than the company average but generate 40 percent more incident
reports, most of them equipment misuse and unattended personal property.
Whitlock says staffing costs for the block run at 1.9 times revenue attributable
to it, and that the company treats the hours as a retention expense rather than
a profit center. Two competing chains contacted for this piece declined to share
comparable figures.

The city has taken an interest. A Seattle Office of Economic Development brief
issued in June counted 340 businesses operating past midnight within the
downtown core, of which 11 were fitness facilities, up from 4 in 2021. Policy
lead Corinne Adeyemi says the office is studying whether late-hour fitness
qualifies for the same permitting treatment as late-hour hospitality. Adeyemi
says no proposal has been drafted. Vance says the association would support
parity, and that the current framework classifies a 1 a.m. squat rack and a
1 a.m. bar under rules written for the latter.
""".strip()

VAL_X_TRAINING_AS_FITT = """
Training frequency is settled. Twice per muscle per week beats once.

2 sessions, identical weekly volume, more growth. The split that trains chest one day a week is a calendar artifact.

It fits a gym schedule. It does not fit the muscle.

10 to 20 hard sets per muscle per week. That is the working range.

Under 10: maintenance. Over 20: bookkeeping.

Hard sets are hard. 0 to 3 reps left in reserve. Anything easier is a warmup in costume.

Rep range is the least interesting variable in the room. 5 reps and 30 reps build similar muscle when both finish near failure.

Load is a dial. Effort is the doctrine.

Rest periods: 2 to 3 minutes between hard sets.

30-second rest is a conditioning protocol wearing a hypertrophy nametag. Total volume drops. Growth follows it down.

Tempo scripts are theater. 4 seconds down, 1 second up, 2 at the top: nobody counts past week three.

Control the lowering. Stop counting.

Range of motion is the free win. Full stretch under load outperforms the top half in every measured comparison.

Lengthened partials work. Half reps at the bottom of a curl beat half reps at the top.

Machines are not a downgrade. A leg press builds quads. A hack squat builds quads. The barbell has better mythology, not better tissue.

Free weights win on transfer and stability. Machines win on stimulus per unit of fatigue. Serious programs use both.

Upper/lower is the best default split for 4 days. Full body is the best default for 3.

The 5-day body part split needs a 5-day life. Most people have a 3-day life.

Exercise order matters at the margin. The first movement gets the best set. Everything after it inherits fatigue.

Compound first is a default, not a law. A lagging side delt goes first. Priority beats tradition.

Unilateral work is undersold. Single-leg training closes strength gaps that bilateral loading hides for years.

1 leg at a time also cuts spinal load in half.

Progressive overload is not a monthly personal record. It is 1 more rep, 2.5 more kilograms, 1 more set, in that order of preference.

Double progression is the cleanest system in strength training. Add reps to the top of the range. Then add load. Repeat.

Training to failure has a price. Every set taken past failure costs 24 to 48 hours of recovery on compounds.

Reserve failure for machines and isolations. Take squats to 2 reps short and go home.

Deloads are scheduled, not earned. Every 6 to 8 weeks, cut volume by half and keep the load.

The lifters who skip deloads do not avoid them. They take them involuntarily, in a physio waiting room.

Soreness is not a scoreboard. New exercises produce soreness. New growth does not require it.

Technique breakdown under fatigue is data, not disgrace. The set ends when the pattern changes.

Grip fails before the lats do on every heavy pull. Straps are equipment, not cheating.

Direct grip work: 2 sets of holds, twice a week. Done.

Calves respond to frequency more than to any single protocol. 4 sessions a week, 3 sets each.

Abs are trained like any other muscle. Loaded, progressive, 8 to 15 reps. Endless crunches are cardio with worse posture.

Cardio interference is real and small. 3 zone-two sessions per week cost nothing measurable in leg size.

Hill sprints on the Queen Anne counterweight are a different conversation. High-impact intervals and heavy squats compete for the same recovery.

Separate them by 6 hours. Or separate them by a day.

Session length: 45 to 75 minutes of working time.

The 2-hour session is mostly phone.

Warmups are 2 ramp sets and a general 5 minutes. Everything past that is procrastination with a foam roller.

Stretching before lifting reduces peak force for about an hour. Stretch after. Or stretch on a different day.

Program hopping is the most common failure in this city. 4 weeks is not a training block. It is a trial subscription.

12 weeks minimum on any structure before the verdict.

Plateaus are usually adherence problems in a physiology costume. Check attendance before changing the program.

A plateau at 8 weeks is normal variance. A plateau at 6 months is a program.

Tracking is not optional. A program that lives in memory drifts toward comfort within a month.

A notebook works. A spreadsheet works. The specific tool is irrelevant. The record is not.

Women and men respond to the same programming. Volume, intensity, progression: identical levers.

Recovery capacity varies by person, not by category.

Sleep is the only recovery method with an effect size worth naming. 7 to 9 hours.

Cold plunges do the opposite after lifting. Post-set cold blunts the growth signal for hours. Plunge on rest days or skip it.

Massage guns feel excellent and change nothing structural.

Bands are travel equipment. They fill 2 weeks of a work trip and nothing more.

Rest days are training days without lifting. Walking, food, sleep. That is the whole protocol.

Seattle introduces one real variable: 8 months of dark commutes. Morning training wins on adherence in this climate, not on physiology.

The 6 a.m. crowd at Interbay outlasts the 6 p.m. crowd by a wide margin. Attendance is the mechanism.

Garage gyms beat commercial gyms on friction. Commercial gyms beat garage gyms on equipment variety.

Friction wins over 5 years. Variety wins over 5 months.

The best program is the one never abandoned in February.
""".strip()

VAL_X_NUTRITION_AS_FITT = """
Protein is the only macro with a hard floor. 1.6 to 2.2 grams per kilogram of body weight per day.

Everything under that is a compromise. Everything over it is expensive urine.

4 meals beats 2. Distribution matters more than the total once the total is met.

30 to 40 grams per sitting, 4 sittings. That is the whole architecture.

Whole food first. Chicken thigh, eggs, skyr, tofu, cod, lentils with rice.

Protein powder: only if whole food falls short. It is a convenience product, not a supplement.

Whey isolate wins on cost per gram and on digestion speed. Casein wins on nothing worth paying extra for.

Plant blends work when they combine pea and rice. Pea alone runs short on methionine.

Collagen is not a protein supplement. It scores near zero on every completeness scale that matters.

BCAAs are the worst value in the aisle. 3 of the 9 essential amino acids, sold at a premium.

Creatine works. 5 grams per day, monohydrate, no loading phase, no cycling.

The loading protocol saves 2 weeks and costs a week of bloat.

Timing is the smallest lever in nutrition. The anabolic window is roughly the size of a workday.

Eat protein within a few hours on either side of training. That is the entire rule.

Carbs around training earn their place in sessions over 60 minutes. Under 60 minutes, normal daily intake covers it.

3 to 5 grams of carbohydrate per kilogram for most lifters. Higher for anyone running hills twice a week.

Low-carb training is a preference, not a strategy. Performance drops in the 8 to 15 rep range within 2 weeks.

Fat has a floor too. 0.6 grams per kilogram. Below it, hormones and fullness both fall.

Fiber is the most neglected number in a lifter's diet. 30 grams per day.

Seed oil discourse is noise. Total calories decide body composition. The oil in a restaurant pan ranks somewhere below sleep.

Fasted training does not burn more fat over 24 hours. It burns more during the hour and less afterward.

Intermittent fasting is a calorie-control tool with good branding. It beats nothing on protein distribution.

16:8 compresses 4 protein feedings into 3. That is a cost, not a feature.

Sugar is not uniquely fattening. 100 calories of honey and 100 calories of olive oil both count.

Ultra-processed food is a volume problem. It delivers calories faster than fullness arrives.

Fullness per calorie is the number that decides adherence. Potatoes, oats, lean meat, fruit, cottage cheese.

Tracking works. Not forever, and not for everyone, but a 3-week audit corrects portion drift that memory hides.

80 percent of intake comes from about 12 repeated foods. Fix those 12 and the spreadsheet becomes optional.

Meal prep is a logistics practice, not a diet. 2 hours on Sunday buys 5 clean weekdays.

Weekend drift erases 3 clean weekdays. 2 days of loose eating covers a 500-calorie deficit and then some.

Alcohol is the sharpest single lever in the whole category. 4 drinks blunt protein synthesis and wreck the sleep that follows.

1 or 2 drinks, occasionally, cost close to nothing. The math turns fast after that.

Breakfast is not mandatory. Protein at breakfast is close to it, because the day rarely catches up otherwise.

Hydration advice is mostly folklore. Thirst plus pale urine covers 95 percent of cases.

Electrolyte sachets matter for 90-minute sessions in heat. Seattle gets about 11 such days a year.

Seattle makes the protein part easy. Sockeye, cod, halibut, and a teriyaki counter on nearly every block.

A teriyaki chicken plate is 50 grams of protein for 12 dollars. The rice is not the problem.

Coffee is fine. 3 to 6 milligrams of caffeine per kilogram improves training performance and nothing else.

Greens powders replace vegetables the way a photograph replaces a room.

Multivitamins are cheap insurance for a narrow diet and irrelevant for a wide one.

Vitamin D is the exception in this city. 2,000 IU daily from October to April.

Deficits work at 300 to 500 calories below maintenance. Faster than that costs muscle.

Diet breaks work. 2 weeks at maintenance every 10 to 12 weeks of a deficit protects training quality.

Bulking at 500 calories over maintenance buys fat, not tissue. 200 is the honest number.

Protein first, always. The rest is seasoning.
""".strip()

# The external third of the in-register corpus: magazine copy this module's
# author did not write. Its Social section is the binding constraint on the
# margin, which is exactly why it is in here.
try:
    EXTERNAL_IN_REGISTER = sorted(
        json.load(open(SAMPLE_ISSUE, encoding="utf-8"))["sections"].items())
except (OSError, KeyError, ValueError):  # pragma: no cover - repo layout guard
    EXTERNAL_IN_REGISTER = []

#: Production-length half of the DERIVATION corpus. (section, text)
LONG_IN_REGISTER = [
    ("Culture", LONG_IN_CULTURE_ATHLETIC_CENTRED_ON_A_PERSON),
    ("Nutrition", LONG_IN_NUTRITION_PEOPLE_FULL_OF_NUMBERS),
    ("Supplements", LONG_IN_SUPPLEMENTS_FITT_NAMING_A_RESEARCHER),
    ("Training", LONG_IN_TRAINING_ATHLETIC_DENSE_AND_SOURCED),
    ("Culture", LONG_IN_CULTURE_REPORTED_HUMAN_INTEREST),
    ("Training", LONG_IN_TRAINING_REPORTED_HUMAN_INTEREST),
]

#: Production-length half of the DERIVATION corpus. (section, written_in, text)
LONG_CROSS_REGISTER = [
    ("Nutrition", "fitt", LONG_X_NUTRITION_AS_FITT),
    ("Training", "people", LONG_X_TRAINING_AS_PEOPLE),
    ("Recovery", "people", LONG_X_RECOVERY_AS_PEOPLE),
    ("Culture", "fitt", LONG_X_CULTURE_AS_FITT),
    ("Culture", "people", LONG_X_CULTURE_AS_A_QUIET_PROFILE),
]

# ── DERIVATION CORPUS: 46 texts, 35-1176 words. Sets the constant. ───────────
CALIBRATION_IN_REGISTER = (HOSTILE_IN_REGISTER + CLEAN_CASES
                           + EXTERNAL_IN_REGISTER + LONG_IN_REGISTER)
CALIBRATION_CROSS_REGISTER = (HOSTILE_CROSS_REGISTER + LEGACY_CROSS_CASES
                              + LONG_CROSS_REGISTER)

# ── VALIDATION CORPUS: 12 texts, 530-1023 words, all inside their section's
# legal word-count range. Disjoint from the derivation corpus and never used to
# choose a constant. This is the half that can refute the calibration.
VALIDATION_IN_REGISTER = [
    ("Social", VAL_IN_SOCIAL_PEOPLE_ORDINARY),
    ("Recovery", VAL_IN_RECOVERY_FITT_LONG),
    ("Training", VAL_IN_TRAINING_ATHLETIC_FOLLOWING_A_COACH),
    ("Nightlife", VAL_IN_NIGHTLIFE_FITT_OPINIONATED),
    ("Nutrition", VAL_IN_NUTRITION_PEOPLE_QUOTE_HEAVY),
    ("Culture", VAL_IN_CULTURE_ATHLETIC_PLAIN),
]
VALIDATION_CROSS_REGISTER = [
    ("Social", "athletic", VAL_X_SOCIAL_AS_ATHLETIC),
    ("Supplements", "people", VAL_X_SUPPLEMENTS_AS_PEOPLE),
    ("Culture", "people", VAL_X_CULTURE_AS_PEOPLE),
    ("Nightlife", "athletic", VAL_X_NIGHTLIFE_AS_ATHLETIC),
    ("Training", "fitt", VAL_X_TRAINING_AS_FITT),
    ("Nutrition", "fitt", VAL_X_NUTRITION_AS_FITT),
]


# ═══════════════════════════════════════════════════════════════════════════════
# GATE-2 REGRESSION CORPUS — the text that refuted the previous calibration
#
# Twelve sections written by the reviewer AFTER the two-channel rebuild and never
# seen by this module until they broke it. Four of the six in-register texts were
# hard-failed by cross-contamination; two of them are C1 and C2 below, an
# athletic-register section that is a HUMAN story rather than a DATA story. The
# athletic gate passed on both — this module certified the copy as properly
# attributed, non-shouting reported prose — and the section was blocked anyway on
# a per-occurrence channel the athletic register had no vocabulary in.
#
# It is copied in verbatim so the defect cannot come back quietly. Note what that
# costs: these texts have now been used while fixing the marker set, so they can
# no longer refute anything. They are a REGRESSION fixture from here on, not a
# validation one, and the next calibration needs text that none of the three
# corpora in this file contain.
# ═══════════════════════════════════════════════════════════════════════════════

G2_C1_CULTURE_CLOSURE = """
The lease at Iron Row expires in March, and the building's owner has shown the
space to three prospective tenants since the start of the year, according to two
members of the morning group who were on the floor when the broker walked
through.

Terrence Blake, who has coached the six o'clock hour since the room opened,
says he learned about it from a flyer taped inside the window.

"Nobody called," he says. "I read it the same way everybody else read it."

His mornings start at four thirty. His wife drives him in on the days his knee
will not take the bus steps, and his daughter has started coming on Saturdays
because she says she wants to see it before it goes.

The room has never advertised. Attendance grew by word of mouth and stayed
where it landed, and the coaches say they turned away more people last year
than they signed.

Marguerite Oyelowo, who has trained there since the second month, says the
thing she will miss is not the equipment.

"You can buy plates anywhere," she says. "What you cannot buy is the person who
notices when you stop showing up."

Her husband trains there too. Her sons learned to deadlift on the same bar she
did. She keeps a photograph of the original floor on her phone and shows it to
anyone who asks how long the place has been there.

The broker listed the unit as available at the end of the month. The owner did
not respond to two requests for comment, and a representative for the
management company declined to discuss an active listing.

Blake has begun looking at spaces in the industrial blocks south of the canal,
where the rents are lower and the ceilings are high enough for the racks. He
says the problem is not the room.

"I can find a room," he says. "I cannot find these people again on a Tuesday
at six."

Three members have offered to sign as guarantors. Two have offered money. The
group has not decided anything, and the coaches have not asked them to,
because the coaches say the decision belongs to whoever is willing to carry it
for the next ten years and nobody has volunteered for that.

Attendance in the final weeks has climbed rather than fallen. The regulars now
arrive early, which Blake reads as a kind of protest that nobody has agreed to
name out loud, and the room has begun to feel busier than it has in years.

His last class is scheduled for the second week of March. He has not written
anything for it, and he says he does not intend to.
""".strip()

G2_C2_TRAINING_REPORTED = """
Three of the region's collegiate strength programmes have moved their winter
blocks off percentage charts and onto velocity caps since the spring, according
to the coordinators who made the change.

Nadia Whitfield, who came to the college side after nine years in professional
rugby, says it began as a scheduling problem rather than a training one.

"We had eleven athletes and two platforms," she says. "A chart cannot tell me
who is cooked and who is sandbagging. The bar can."

She grew up in the sport. Her father coached her first team and her brother
still lifts in the same room she learned in, and she says the argument about
bar speed was fringe enough when she started that raising it in a staff meeting
got you a look.

Her staff now logs every top set. A bar that drops below the cut ends the
session for that athlete regardless of what the written programme says, and the
coordinators at the other two programmes describe the same rule in almost the
same words.

The counter-argument has not gone away. Coaches who kept the charts point to
compliance, and they are not wrong that an athlete who is told to stop early
will sometimes stop early for the rest of the week as well.

Whitfield concedes the point. Her answer is that the athletes who stop early
are the ones the chart was going to bury anyway, and she says two seasons of
availability data have made her more confident about that rather than less.

What changed underneath all of it is the accounting. Once sleep and travel
entered the model, the fourth session stopped paying for itself, and the
coordinators who ran the numbers say it was the first thing to go every time.

Her mother still asks when she is going to get a job with weekends. Whitfield
says the honest answer is that the six o'clock hour is the part she would keep
if she had to give up everything else, and that she has never found a way to
explain that at a family dinner.

Attendance at the department's own coaching clinic has doubled since the
change. Two neighbouring programmes have sent staff to observe, and a third
has asked for the spreadsheet.
""".strip()

G2_C3_NUTRITION_DATA_PROFILE = """
Tomas Herrera is at his kitchen counter at 5:40 in the morning, weighing oats on
a scale his daughter gave him as a joke three birthdays ago.

He is 44, a bus mechanic whose shift starts before the coffee places open, and
he has eaten the same breakfast 300 days running.

"It is not discipline," he says. "It is that I stopped deciding."

The numbers are the part he can recite. 90 grams of oats. 40 grams of protein.
2 eggs on the days he lifts and none on the days he does not. He worked it out
with a dietitian four years ago and has changed one thing since.

His wife teases him about the scale. His kids ignore it entirely. The bowl goes
back on the same shelf every morning and the scale goes into the same drawer,
and by the time the light is up he is already across the water.

He lost 18 kg in the first year and has held it for three. His blood pressure
came down 20 points. His doctor asked what programme he was on and he said he
was not on one.

"She wanted a name for it," he says. "There is no name for it. I eat the same
thing."

His father died at 61 and his brother had a stent at 47, and he says that is
the whole motivation, laid out plainly, without any of the language people put
around it.

The mechanics he works with have started asking. Two of them have copied the
breakfast. One lasted 3 weeks and one is at 8 months, and Herrera says he does
not offer advice unless somebody asks twice.

His daughter still sends him scales. He has four now, in a drawer, and he uses
the first one.
""".strip()

G2_C4_RECOVERY_NEWSLETTER = """
Sauna is undersold. Ice is oversold. That is the whole newsletter.

20 minutes at 80 degrees, 4 times a week. That is the dose with actual
replication behind it.

The cold aisle has better marketing and worse evidence. 6 of the 9 trials
published since 2022 found nothing once sleep was controlled.

Ilona Vartanen runs the thermal lab at Interbay. She has spent 11 years on
heat and says the fashionable half was never the half that worked.

Her position is not subtle. Buy the towel. Skip the tub.

3 studios in this city now sell contrast packages at $180 a month. None of them
will show you the protocol.

The honest version costs nothing. Sit in the heat. Sleep 8 hours. Do it for a
year.

Everything else on that shelf is a rounding error.
""".strip()

G2_C5_SOCIAL_PUNCHY = """
Devon Ashworth carries the cones. That is his entire job and he defends it at
length.

He is 29. A bike mechanic. His Saturdays disappeared into this two winters ago
and he has never once complained about it where anyone could hear.

60 runners on a good week. 9 on the week it snowed. Nobody has been dropped in
two years.

"I own a car," he says. "That is the whole qualification."

His partner brings the coffee. His neighbours bring their kids. His mother
came once and now comes monthly.

The route has not changed since the first winter. Regulars navigate it half
asleep and the newcomers follow whoever looks least uncertain.

He keeps the spreadsheet on his phone. 2 columns. Names and weeks. He has never
shown it to anyone and says he never will.

"It is not a club," he says. "It is a standing appointment that happens to have
forty people at it."
""".strip()

G2_C6_NIGHTLIFE_OPINION = """
The 9pm room is the best hour in this city and it is not close.

40 minutes. No mirrors. One playlist, chosen by whoever gets there first.

2 studios have copied the format since January. Both watered it down inside a
month and both are quieter for it.

Ruben Castellanos pours the seltzer afterwards and has never once been asked to
explain the concept to anybody.

The economics are the interesting part. $14 a class. 30 spots. It sells out in
under 4 minutes and always has.

Go early or skip it entirely. Never the middle option.
""".strip()

G2_X1_TRAINING_AS_PROFILE = """
Callum Reyes is sitting on an upturned crate outside the roll-up door with his
hands wrapped and nowhere to be for another forty minutes.

He is 34, a scaffolder whose shoulder went in the second year of it, and he has
been coming to this hour since before the door had a working lock.

"I do not know what else I would do at five," he says. "That is the honest
version and I have stopped dressing it up."

His mornings belong to the bar. His evenings belong to his kids. His wife
stopped asking when the block ends because there is not one and both of them
know it.

He grew up two streets from here. His father worked the same trade and never
lifted anything that was not attached to a building, and Reyes says the first
time he explained a deadlift at a family table it went badly.

His hands are the part he notices. They do not close all the way in the cold
any more. He remembers when they did.

"My daughter asked me why I do it," he says. "I told her I would tell her when
I worked it out."

His routine has not moved in six years. Same door. Same crate. Same forty
minutes before anyone else arrives, which he says is the part he would miss.

His neighbours think he owns the place. He has corrected them twice and given
up.
""".strip()

G2_X2_CULTURE_AS_NEWSLETTER = """
The members-only floor is the worst idea in this city right now.

$240 a month. 9 platforms. One rule nobody has ever enforced.

3 rooms tried the model since 2023. All 3 walked it back inside a year.

The maths never worked. 90 members at that price cannot fill 9 platforms and
cannot pay for them either.

Charge less or close. Never the middle.

2 of the 3 are now open-membership and both are busier. The third is a yoga
studio.

The lesson is free and nobody will take it.
""".strip()

G2_X3_SUPPLEMENTS_AS_REPORT = """
The creatine market has spent five years selling a solved problem back to the
people who solved it, according to three of the researchers who ran the
original dosing trials and who have begun saying so in print rather than in
conference corridors.

At the Eastlake Performance Lab, a review of 40 commercial formulations found
that 31 carried a per-serving cost at least 8 times that of plain monohydrate,
with no measurable difference in intramuscular saturation after 4 weeks of
daily use in the 18 subjects who completed the protocol.

Dr Helen Marsh, who supervised the review, notes that the marketing language
has migrated from absorption to comfort now that absorption claims are harder
to defend in front of a regulator.

She argues that the shift is itself the tell, because a category confident in
its chemistry does not usually retreat to talking about how the powder feels
going down, and two of her co-authors said the same thing independently when
asked.

The manufacturers dispute the framing. A trade body representing four of the
brands named in the review said the comparison ignores formulation costs and
described the saturation endpoint as reductive, according to a statement
provided to reviewers.

Marsh says she has heard the objection and does not find it serious. The
review has been submitted for replication at a second site, and the authors
say the enrolment target is 60 subjects across 12 weeks.
""".strip()

G2_X4_RECOVERY_AS_PROFILE = """
Hollis Bergman is sorting bottles on her kitchen table again, one brand per
column, the way she has done on the first Sunday of every month for six years.

She is 46, a pharmacist whose mornings start before her children do, and she
has stopped pretending that the sorting is about the supplements.

"My father took the same stack for thirty years and never read a label," she
says. "He trusted the box. I read boxes for a living."

Her cupboard holds four bottles now. It held nineteen when she started, and she
says the reduction took longer than the accumulation did.

Her husband finds the ritual funny. Her daughter has begun helping, which
Bergman says she did not expect and has not discussed with anyone.

Her mornings are clinic hours. Her afternoons belong to whoever walks in. She
remembers the name of every patient who ever asked her about a product she
could not defend.

"The hardest part of the job is saying no to someone who is frightened," she
says. "There is no protocol for that."

Her father died in the spring. She kept his last bottle and has not opened it.
""".strip()

G2_X5_SOCIAL_AS_REPORT = """
Participation in organised run clubs across the city rose 42% between 2022 and
2024, according to registration data compiled by three of the largest groups
and shared with reviewers on condition that individual clubs were not named.

At the Fremont meeting point, weekly turnout has moved from 30 runners to more
than 200, and the organisers have added 2 additional pace groups to absorb the
growth without lengthening the route.

The growth has not been evenly distributed. Clubs that kept a fixed start time
grew fastest across the 24 months covered by the data, while clubs that
rotated their routes weekly reported flat numbers over the same period.

Organisers attribute the difference to predictability rather than to
programming, and two of the three groups said they had stopped experimenting
with the format entirely once the pattern became clear in their own numbers.

Registration data from a fourth group was excluded after reviewers found that
its counting method had changed in 2023, according to a note appended to the
compiled set.

The clubs that grew fastest also reported the highest attrition. One group
recorded 400 sign-ups and 240 runners who never returned after a first
session, a ratio the organisers described as normal and the compilers
described as unexamined.

Two of the groups have begun publishing their numbers quarterly. A third
declined, saying the count was never the point, and the compilers noted the
refusal without comment.
""".strip()

G2_X6_NUTRITION_AS_NEWSLETTER = """
Breakfast is the only meal worth defending and the rest is noise.

40 grams of protein inside 90 minutes of waking. That is the entire rule.

2 trials in 2024 moved the timing and lost the effect. Neither found a fix and
neither has been replicated.

The supplement aisle has an answer for this. The answer costs $60 a month and
does nothing.

Eat early or stop pretending you are training for anything.

3 of the 4 largest professional bodies still publish a total-intake target with
no timing language attached. All 3 are wrong and all 3 know it.

Cook the eggs. Skip the powder.
""".strip()

#: (section, text) — must NOT fire. C1/C2 are the two that did.
GATE2_IN_REGISTER = [
    ("Culture", G2_C1_CULTURE_CLOSURE),
    ("Training", G2_C2_TRAINING_REPORTED),
    ("Nutrition", G2_C3_NUTRITION_DATA_PROFILE),
    ("Recovery", G2_C4_RECOVERY_NEWSLETTER),
    ("Social", G2_C5_SOCIAL_PUNCHY),
    ("Nightlife", G2_C6_NIGHTLIFE_OPINION),
]

#: (section, written_in, text) — MUST fire.
GATE2_CROSS_REGISTER = [
    ("Training", "people", G2_X1_TRAINING_AS_PROFILE),
    ("Culture", "fitt", G2_X2_CULTURE_AS_NEWSLETTER),
    ("Supplements", "athletic", G2_X3_SUPPLEMENTS_AS_REPORT),
    ("Recovery", "people", G2_X4_RECOVERY_AS_PROFILE),
    ("Social", "athletic", G2_X5_SOCIAL_AS_REPORT),
    ("Nutrition", "fitt", G2_X6_NUTRITION_AS_NEWSLETTER),
]

# The legal word-count ranges the magazine ruleset enforces. Transcribed rather
# than imported: VoiceLint does not depend on ProhibLint and must not start to.
# test_the_word_count_ranges_still_match_prohiblint keeps the copy honest.
WORD_COUNT_RANGES = {
    "Training":    (800, 1200),
    "Nutrition":   (600, 900),
    "Supplements": (400, 600),
    "Recovery":    (500, 800),
    "Culture":     (800, 1200),
    "Social":      (500, 700),
    "Nightlife":   (400, 600),
}


def band(in_register, cross_register):
    """(worst in-register margin, weakest cross-register margin)."""
    return (max(worst_other_margin(s, t) for s, t in in_register),
            min(intended_margin(s, t, v) for s, v, t in cross_register))


# ═══════════════════════════════════════════════════════════════════════════════
# run() output shape — the orchestrator contract
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunOutputShape:

    def test_run_returns_one_entry_per_section(self):
        results = run({"Training": ATHLETIC_PASS_1,
                       "Nutrition": PEOPLE_PASS_1,
                       "Supplements": FITT_PASS_1})
        assert set(results) == {"Training", "Nutrition", "Supplements"}

    def test_run_result_has_all_orchestrator_keys(self):
        for section, text in CLEAN_CASES:
            r = lint_one(section, text)
            assert REQUIRED_KEYS <= set(r), f"{section} missing {REQUIRED_KEYS - set(r)}"

    def test_run_result_key_types(self):
        r = lint_one("Training", ATHLETIC_PASS_1)
        assert isinstance(r["voice_required"], str)
        assert isinstance(r["voice_score"], int)
        assert isinstance(r["contamination_flags"], list)
        assert all(isinstance(f, str) for f in r["contamination_flags"])
        assert isinstance(r["passed"], bool)

    def test_run_output_is_json_serialisable(self):
        # orchestrator.py dumps these straight into results/*.json
        results = run({sec: txt for sec, txt in CLEAN_CASES})
        json.dumps(results)

    def test_run_empty_input_returns_empty(self):
        assert run({}) == {}

    def test_run_does_not_mutate_input(self):
        sections = {"Training": ATHLETIC_PASS_1}
        before = dict(sections)
        run(sections)
        assert sections == before

    def test_run_handles_empty_text_without_crashing(self):
        r = lint_one("Training", "")
        assert REQUIRED_KEYS <= set(r)
        assert 0 <= r["voice_score"] <= cfg.SCORE_START

    def test_empty_text_scores_no_register_gate_either_way(self):
        """Nothing to judge: an empty section is not evidence for or against."""
        assert voice_affinity("") == {"athletic": 0, "people": 0, "fitt": 0}

    def test_voice_required_matches_section_map(self):
        for section, expected in cfg.SECTION_VOICE_MAP.items():
            assert lint_one(section, "Placeholder text with some words.")["voice_required"] == expected

    def test_unmapped_section_falls_back_to_default_voice(self):
        r = lint_one("Mystery", "Some text here.")
        assert r["voice_required"] == voicelint.DEFAULT_VOICE == "athletic"

    def test_debug_block_exposes_all_three_affinities(self):
        r = lint_one("Training", ATHLETIC_PASS_1)
        d = r["_debug"]
        assert {"primary_delta", "contamination_penalty", "primary_details",
                "athletic_delta", "people_delta", "fitt_delta",
                "words", "affinity_per_100w"} <= set(d)
        assert d["primary_delta"] == d["athletic_delta"]

    def test_debug_density_matches_the_public_density_function(self):
        r = lint_one("Training", ATHLETIC_PASS_1)
        expected = {k: round(v, 2) for k, v in voice_affinity_density(ATHLETIC_PASS_1).items()}
        assert r["_debug"]["affinity_per_100w"] == expected


# ═══════════════════════════════════════════════════════════════════════════════
# The Athletic scorer
# ═══════════════════════════════════════════════════════════════════════════════

class TestAthleticScorer:

    def test_returns_score_and_flags(self):
        score, flags = score_athletic(ATHLETIC_PASS_1)
        assert isinstance(score, int)
        assert isinstance(flags, list)

    def test_clean_athletic_samples_pass(self):
        for text in (ATHLETIC_PASS_1, ATHLETIC_PASS_2, ATHLETIC_PASS_3):
            assert score_athletic(text)[0] >= cfg.PASS_THRESHOLD

    def test_attribution_is_the_gate_AND_per_occurrence_evidence(self):
        """
        It used to be the gate ONLY, and that is the defect Gate 2 found. A
        boolean cannot separate a report from a profile, because both attribute;
        what separates them is that a report keeps attributing, to source after
        source, and a profile attributes to its one subject and then narrates.
        So the same evidence is asked two different questions — "at all?" once,
        and "how continuously?" per occurrence — and it lands in both channels.

        The people register has always worked this way (PEOPLE_POSITIVE is
        literally PEOPLE_ACCESS + [...]). Applying the no-double-count rule to
        athletic alone was an asymmetry, not a principle, and it fell on the one
        axis where the two registers share their machinery.
        """
        unsourced = "The block is over and the crew has returned to the water."
        sourced = "The block is over, the coach says, and the crew has returned."
        assert voice_affinity(sourced)["athletic"] - voice_affinity(unsourced)["athletic"] == (
            2 * cfg.REGISTER_GATE + cfg.POSITIVE_HIT)

        aff = voicelint.AFFINITY_SCORERS["athletic"](sourced)
        assert aff.section_level == cfg.REGISTER_GATE       # the gate
        assert aff.per_occurrence == cfg.POSITIVE_HIT       # the density

    def test_a_bare_pronoun_quote_tag_is_not_sourcing(self):
        """
        The invariant the whole athletic/people axis rests on. A profile's
        "she says" is its subject's own voice; PEOPLE_ACCESS counts it as
        access, and if the athletic register also scored it, the two registers
        would be reading the same words as evidence for each of them.
        """
        pronoun = 'The block is over. "We are done," she says.'
        sourced = 'The block is over. "We are done," the coach says.'
        assert voicelint.AFFINITY_SCORERS["athletic"](pronoun).per_occurrence == 0
        assert voicelint.AFFINITY_SCORERS["athletic"](sourced).per_occurrence == cfg.POSITIVE_HIT

    def test_reporting_frames_are_sourcing_markers(self):
        """
        The families that have no counterpart in the other two registers, so
        unlike DATA_CLAIM they do not cancel in any margin. Nothing but reported
        journalism writes these sentences.
        """
        base = "The room closed in March and the equipment went into storage."
        for frame in (
            "The owner did not respond to two requests for comment.",
            "A representative for the company declined to discuss the sale.",
            "County records show the parcel changed hands in March.",
            "A spokesperson put the figure at four.",
            "The buyer was reportedly a development firm.",
            "Reached by phone, the broker gave the same account.",
        ):
            gain = (voicelint.AFFINITY_SCORERS["athletic"](base + " " + frame).per_occurrence
                    - voicelint.AFFINITY_SCORERS["athletic"](base).per_occurrence)
            assert gain >= cfg.POSITIVE_HIT, frame

    def test_sourcing_is_matched_case_sensitively(self):
        """
        ATHLETIC_ATTRIBUTION encodes proper nouns and a capitalised exclusion
        list, so under re.IGNORECASE it means nothing: "nobody says" would read
        as a named source. The gate is matched case-sensitively and the density
        has to be matched the same way or the two disagree about the same text.
        """
        upper = "The block is over, Nakashima says."
        lower = "the block is over, nakashima says."
        assert voicelint.AFFINITY_SCORERS["athletic"](upper).per_occurrence == cfg.POSITIVE_HIT
        assert voicelint.AFFINITY_SCORERS["athletic"](lower).per_occurrence == 0

    def test_according_to_survives_a_line_break(self):
        """
        A literal space does not match a newline, and every text this module
        sees is hard-wrapped prose. `according to` written as `according\\nto`
        was invisible — to the gate and to the density — for no reason except
        where the line happened to end.
        """
        one_line = "The lease ends in March, according to two members of the group."
        wrapped = "The lease ends in March, according\nto two members of the group."
        assert voice_affinity(wrapped)["athletic"] == voice_affinity(one_line)["athletic"]
        assert voice_affinity(wrapped)["athletic"] > 0

    def test_a_long_apposition_survives_a_line_break(self):
        """
        Same defect in the branch that exists FOR long appositions: it was
        spelled `[^.!?\\n]{0,150}`, so a source description long enough to need
        that branch was, by construction, long enough to wrap out of it. The
        span may cross a line break but still not a paragraph break.
        """
        wrapped = ("Nadia Whitfield, who came to the college side after nine years in "
                   "professional\nrugby, says it began as a scheduling problem.")
        assert voice_affinity(wrapped)["athletic"] > 0
        across_paragraphs = ("Nadia Whitfield, who came to the college side\n\n"
                             "after nine years, says it began as a scheduling problem.")
        assert voicelint.AFFINITY_SCORERS["athletic"](across_paragraphs).per_occurrence == 0

    def test_unsourced_section_is_flagged(self):
        _, flags = score_athletic("The block is over and the crew has returned.")
        assert any("No sourced attribution" in f for f in flags)

    def test_repeated_attribution_does_not_stack(self):
        """A gate is a gate: the second quote is not worth another 8 points."""
        one = "The block is over, the coach says."
        many = "The block is over, the coach says. She adds more. He notes it too."
        assert voice_affinity(many)["athletic"] == voice_affinity(one)["athletic"]

    def test_stat_claims_are_positive_markers(self):
        plain = "Recovery time dropped a lot after the intervention."
        stated = "Recovery time dropped 18 percent over 6 weeks and 12 days."
        assert voice_affinity(stated)["athletic"] > voice_affinity(plain)["athletic"]

    def test_named_source_pattern_is_a_positive_marker(self):
        plain = "A local coach reviewed the block."
        named = "Priya Nair, 29, reviewed the block."
        assert voice_affinity(named)["athletic"] > voice_affinity(plain)["athletic"]

    def test_place_markers_are_matched_case_sensitively(self):
        """
        Under re.IGNORECASE "In the room" and "in the room" both scored. That
        handed the athletic register free points on every prepositional phrase
        and is half of why it appeared to contaminate everything.
        """
        proper = "At Rainier the crew waited."
        common = "at the dock the crew waited."
        assert voice_affinity(proper)["athletic"] > voice_affinity(common)["athletic"]

    def test_exclamations_are_negative_markers(self):
        calm = "The programme works. The data supports it."
        shouty = "The programme works! The data supports it!"
        assert voice_affinity(shouty)["athletic"] < voice_affinity(calm)["athletic"]

    def test_second_person_coaching_is_a_negative_marker_and_flags(self):
        score, flags = score_athletic("You should train harder. You need more volume.")
        assert score < cfg.SCORE_START
        assert any("Athletic negative marker" in f for f in flags)

    def test_earned_rhythm_bonus_for_short_and_long_sentence_mix(self):
        flat = " ".join(["The athlete trained for a while today."] * 6)
        mixed = (
            "Short. Fast. "
            "The athlete trained through a long deliberate block that stretched across many "
            "weeks of progressive overload and careful monitoring of fatigue markers. "
            "The coach reviewed every single session in detail before deciding how the next "
            "training block would be structured for the whole squad."
        )
        assert voice_affinity(mixed)["athletic"] > voice_affinity(flat)["athletic"]

    def test_score_clamped_to_ceiling(self):
        loaded = "She says it. At Rainier the crew ran 12 miles in 40 minutes. " * 10
        assert score_athletic(loaded)[0] == cfg.SCORE_START

    def test_score_clamped_to_floor(self):
        worst = "Get ready! You should try this! You need it! Are you ready?! " * 10
        assert score_athletic(worst)[0] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# People Magazine scorer
# ═══════════════════════════════════════════════════════════════════════════════

class TestPeopleScorer:

    def test_returns_score_and_flags(self):
        score, flags = score_people(PEOPLE_PASS_1)
        assert isinstance(score, int)
        assert isinstance(flags, list)

    def test_clean_people_samples_pass(self):
        for text in (PEOPLE_PASS_1, PEOPLE_PASS_2, PEOPLE_PASS_3):
            assert score_people(text)[0] >= cfg.PASS_THRESHOLD

    def test_named_person_in_opening_beats_anonymous(self):
        anonymous = (
            "Someone is standing in a kitchen early in the morning. "
            "They are blending vegetables and thinking about protein."
        )
        assert voice_affinity(PEOPLE_PASS_1)["people"] > voice_affinity(anonymous)["people"]

    def test_missing_named_person_raises_a_flag(self):
        _, flags = score_people("Someone is standing in a kitchen early in the morning.")
        assert any("No named person" in f for f in flags)

    def test_named_person_must_be_in_the_opening_window(self):
        late = ("Padding sentence with nothing in it. " * 12) + "Carmen Ruiz is here."
        assert not voicelint._named_person(
            ' '.join(late.split()[:voicelint.PERSON_WINDOW_WORDS]))
        assert voice_affinity(late)["people"] < 0

    def test_warm_connective_tissue_is_a_positive_marker(self):
        plain = "Carmen Ruiz trains clients. The mornings start early."
        warm = "Carmen Ruiz, who trains clients whose mornings start early, protects her routine."
        assert voice_affinity(warm)["people"] > voice_affinity(plain)["people"]

    def test_age_plus_role_detail_is_a_positive_marker(self):
        plain = "Aisha Coleman works in Belltown."
        detailed = "Aisha Coleman is 31, a registered dietitian in Belltown."
        assert voice_affinity(detailed)["people"] > voice_affinity(plain)["people"]

    def test_domestic_possessives_are_positive_markers(self):
        neutral = "Carmen Ruiz is here. The room is quiet."
        domestic = "Carmen Ruiz is here. Her kids are loud and her kitchen is small."
        assert voice_affinity(domestic)["people"] > voice_affinity(neutral)["people"]

    def test_studies_opener_is_a_negative_marker(self):
        _, flags = score_people("Studies show protein timing is overrated.")
        assert any("People negative marker" in f for f in flags)

    def test_studies_opener_is_matched_case_sensitively(self):
        """The pattern encodes a sentence opener, so capitalisation is the signal."""
        assert not re.match(cfg.PEOPLE_NEGATIVE_CAPS[0], "studies show protein timing is fine")
        assert re.match(cfg.PEOPLE_NEGATIVE_CAPS[0], "Studies show protein timing is fine")

    # ── Defect 2 regression: the passive-voice pattern used to be dead ──────────

    def _passive_pattern(self):
        found = [p for p in cfg.PEOPLE_NEGATIVE if "was found" in p]
        assert len(found) == 1, "the passive-voice people marker went missing"
        return found[0]

    def test_passive_voice_pattern_has_a_clean_word_boundary(self):
        """It once ended in backslash + 0x08 (backspace), so it never matched."""
        pattern = self._passive_pattern()
        assert pattern.endswith(r'\b')
        assert '\x08' not in pattern

    def test_passive_voice_pattern_matches_real_prose(self):
        assert re.search(self._passive_pattern(), "the effect was found in")

    @pytest.mark.parametrize("phrase", [
        "The effect was found in the second cohort.",
        "The result has been shown repeatedly.",
        "It is known that timing matters.",
        "It has been reported for years.",
    ])
    def test_passive_constructions_now_penalise_the_people_register(self, phrase):
        """Appending a passive construction must cost exactly one negative hit."""
        anchor = "Carmen Ruiz is standing in her kitchen."
        assert (voice_affinity(anchor + " " + phrase)["people"]
                == voice_affinity(anchor)["people"] + cfg.NEGATIVE_HIT)

    def test_passive_construction_raises_a_flag(self):
        _, flags = score_people("Carmen Ruiz is here. The effect was found in the cohort.")
        assert any("People negative marker" in f for f in flags)

    def test_voice_config_source_has_no_control_bytes(self):
        """Guard against another 0x08-class corruption anywhere in the config."""
        raw = open(cfg.__file__, "rb").read()
        bad = [(i, b) for i, b in enumerate(raw) if b < 32 and b not in (9, 10, 13)]
        assert bad == [], f"control bytes in voice_config.py at {bad}"

    def test_every_config_pattern_compiles(self):
        pattern_lists = [cfg.ATHLETIC_POSITIVE, cfg.ATHLETIC_POSITIVE_CAPS, cfg.ATHLETIC_NEGATIVE,
                         cfg.PEOPLE_POSITIVE, cfg.PEOPLE_NEGATIVE, cfg.PEOPLE_NEGATIVE_CAPS,
                         cfg.FITT_POSITIVE, cfg.FITT_STRONG_OPINION,
                         cfg.FITT_NEGATIVE, cfg.FITT_NEGATIVE_CAPS]
        for patterns in pattern_lists:
            for p in patterns:
                re.compile(p)
        for p in (cfg.FITT_DECLARATIVE, cfg.FITT_DATA_LEAD, cfg.ATHLETIC_ATTRIBUTION,
                  cfg.DATA_CLAIM):
            re.compile(p)


# ═══════════════════════════════════════════════════════════════════════════════
# The named-PERSON detector
#
# The old gate was re.search(r'[A-Z][a-z]+\s[A-Z][a-z]+', first_50) — any
# Titlecase bigram at all. In a product saturated with Seattle place names that
# is a free bonus on essentially every section.
# ═══════════════════════════════════════════════════════════════════════════════

class TestNamedPersonDetector:

    @pytest.mark.parametrize("text", [
        "At Cascade the room is cold before six.",          # audit case 1
        "South Lake Union is quiet on a Sunday.",           # audit case 2
        "Some Tuesday mornings the platform is empty.",     # audit case 3
        "Seattle Athletic Club has spent a decade on this.",
        "Pike Place is busy by seven.",
        "Green Lake Trail runs three miles around the water.",
        "The Nordic consensus meeting was held in June.",
        "Every Thursday evening the group meets.",
    ])
    def test_place_and_phrase_bigrams_are_not_people(self, text):
        assert voicelint._named_person(text) is False, text

    @pytest.mark.parametrize("text", [
        "Marcus Webb, 34, a strength coach, opened the door.",
        "Carmen Ruiz is standing in her kitchen.",
        "Aisha Coleman walks into the coffee shop.",
        "Daniel Park, 45, a chef, resisted for years.",       # surname == place word
        "Priya Nair says the shift began three seasons ago.",
        "Marina Vasilenko has coached the group for nine years.",
        "Renata Boyle's athletes arrive early for it.",
    ])
    def test_real_people_are_detected(self, text):
        assert voicelint._named_person(text) is True, text

    def test_a_titlecase_bigram_alone_is_not_enough(self):
        """The old detector returned True for exactly this string."""
        assert re.search(r'[A-Z][a-z]+\s[A-Z][a-z]+', "South Lake Union is quiet.")
        assert voicelint._named_person("South Lake Union is quiet.") is False

    def test_the_gate_follows_the_detector(self):
        place = "At Cascade the room is cold. South Lake Union is quiet."
        person = "Carmen Ruiz is standing in her kitchen."
        gate_delta = voice_affinity(person)["people"] - voice_affinity(place)["people"]
        # the gate swing, plus the two markers "her kitchen" carries: the
        # possessive-plus-domestic-noun access marker and the pronoun itself
        assert gate_delta == 2 * cfg.REGISTER_GATE + 2 * cfg.POSITIVE_HIT

    def test_a_name_alone_does_not_pass_the_people_gate(self):
        """
        Reported copy names its sources in its opening 50 words as a matter of
        routine. A name-only gate paid the people register +REGISTER_GATE on
        ordinary athletic reporting, and that is what collapsed the two
        registers into 3 points of each other across 900 words.
        """
        name_only = "Renata Boyle opened the facility in 2019 and reviewed the block."
        assert voicelint._named_person(name_only) is True
        assert voice_affinity(name_only)["people"] == -cfg.REGISTER_GATE

    def test_a_name_plus_access_passes_the_people_gate(self):
        with_access = ("Renata Boyle opened the facility in 2019, and her kids "
                       "still do their homework in the office.")
        assert voice_affinity(with_access)["people"] > 0

    def test_place_name_storm_does_not_manufacture_a_people_section(self):
        """A Seattle-place-name-heavy fitt section must not read as people."""
        text = ("At Cascade the room is cold. South Lake Union is quiet. Pike Place "
                "is busy by seven. Green Lake Trail runs three miles.")
        assert voice_affinity(text)["people"] < 0


# ═══════════════════════════════════════════════════════════════════════════════
# Fitt Insider scorer — staccato / kicker / declarative / data-lead
# ═══════════════════════════════════════════════════════════════════════════════

class TestFittScorer:

    def test_returns_score_and_flags(self):
        score, flags = score_fitt(FITT_PASS_1)
        assert isinstance(score, int)
        assert isinstance(flags, list)

    def test_clean_fitt_samples_pass(self):
        for text in (FITT_PASS_1, FITT_PASS_2, FITT_PASS_3):
            assert score_fitt(text)[0] >= cfg.PASS_THRESHOLD

    def test_staccato_paragraphs_beat_dense_ones(self):
        staccato = "Creatine works.\n\nFive grams daily.\n\nNothing else comes close."
        dense = " ".join(["padding"] * (cfg.FITT_POSITIVE_PARA_MAX + 20))
        assert voice_affinity(staccato)["fitt"] > voice_affinity(dense)["fitt"]

    def test_non_staccato_raises_a_flag(self):
        dense = " ".join(["padding"] * (cfg.FITT_POSITIVE_PARA_MAX + 20))
        _, flags = score_fitt(dense)
        assert any("staccato" in f for f in flags)

    def test_paragraph_over_the_long_limit_is_penalised_and_flagged(self):
        long_para = " ".join(["padding"] * (cfg.FITT_LONG_PARA_MAX + 10))
        score, flags = score_fitt(long_para)
        assert any(f"exceeds {cfg.FITT_LONG_PARA_MAX} words" in f for f in flags)
        assert score < score_fitt(FITT_PASS_1)[0]

    def test_opinionated_kicker_bonus(self):
        base = "Creatine works.\n\nFive grams daily.\n\n"
        with_kicker = base + "Plain creatine is best."
        without_kicker = base + "Plain creatine remains a reasonable option for most."
        assert voice_affinity(with_kicker)["fitt"] > voice_affinity(without_kicker)["fitt"]

    def test_kicker_must_be_short(self):
        base = "Creatine works.\n\nFive grams daily.\n\n"
        short_kicker = base + "Plain creatine is best."
        long_kicker = base + (
            "Plain creatine is best when you consider the evidence base and the price "
            "and the total absence of any credible alternative on the market today."
        )
        assert voice_affinity(short_kicker)["fitt"] > voice_affinity(long_kicker)["fitt"]

    def test_declarative_openings_bonus(self):
        declarative = "Protein powder: only if whole food falls short.\n\nFoam rolling: 90 seconds per set."
        subordinate = "Protein powder is worth using when whole food falls short of the target."
        assert voice_affinity(declarative)["fitt"] > voice_affinity(subordinate)["fitt"]

    def test_data_led_sentences_bonus(self):
        data_led = "5 grams per day works.\n\n300 mg before bed helps."
        prose_led = "Take five grams per day.\n\nTake three hundred mg before bed."
        assert voice_affinity(data_led)["fitt"] > voice_affinity(prose_led)["fitt"]

    @pytest.mark.parametrize("hedge", ["might", "could", "perhaps", "possibly", "seems", "may"])
    def test_hedging_words_are_negative_markers(self, hedge):
        firm = "Creatine works.\n\nFive grams daily."
        hedged = f"Creatine {hedge} work.\n\nFive grams daily."
        assert voice_affinity(hedged)["fitt"] < voice_affinity(firm)["fitt"]

    def test_no_flag_an_editor_reads_is_a_raw_regex(self):
        """
        Flags reach an editor through the orchestrator's violations list. Every
        marker whose pattern does not read as English needs a FLAG_LABELS entry,
        and adding a pattern without one is the easy way to ship a regex into a
        scorecard.
        """
        for section, text in CALIBRATION_IN_REGISTER + VALIDATION_IN_REGISTER:
            for flag in lint_one(section, text)["contamination_flags"]:
                assert "(?:" not in flag and "\\b" not in flag, flag
        for section, _, text in CALIBRATION_CROSS_REGISTER + VALIDATION_CROSS_REGISTER:
            for flag in lint_one(section, text)["contamination_flags"]:
                assert "(?:" not in flag and "\\b" not in flag, flag

    def test_every_flagging_pattern_has_a_plain_language_label(self):
        missing = [p for p in cfg.FLAGGING_PATTERNS if p not in cfg.FLAG_LABELS]
        assert missing == [], missing

    def test_hedging_raises_a_flag(self):
        _, flags = score_fitt("Creatine might possibly work.")
        assert any("Fitt negative marker" in f for f in flags)

    def test_subordinate_openers_are_matched_case_sensitively(self):
        assert re.match(cfg.FITT_NEGATIVE_CAPS[0], "However the dose matters.")
        assert not re.match(cfg.FITT_NEGATIVE_CAPS[0], "however the dose matters.")

    def test_second_person_wellness_register_is_a_negative_marker(self):
        neutral = "Creatine works.\n\nFive grams daily."
        wellness = "Your body needs creatine.\n\nYou should try this."
        assert voice_affinity(wellness)["fitt"] < voice_affinity(neutral)["fitt"]

    def test_attribution_is_a_fitt_negative(self):
        """
        The newsletter asserts; it does not report. This is the only signal that
        separates athletic copy from fitt copy when the athletic copy happens to
        be written in short paragraphs — the staccato gate cannot see the
        difference on its own.
        """
        asserted = "Creatine works.\n\nFive grams daily."
        reported = "Creatine works, the researcher says.\n\nFive grams daily."
        assert (voice_affinity(reported)["fitt"]
                == voice_affinity(asserted)["fitt"] + cfg.NEGATIVE_HIT)

    def test_an_unsourced_reporting_verb_is_still_a_fitt_negative(self):
        """
        Fitt's test and the athletic gate's test are different questions and
        must not share a pattern. The athletic gate demands an IDENTIFIED source
        (a name, a role, an institution). Fitt is violated by reporting at all,
        so a bare pronoun tag with no source in it still costs the newsletter.
        Folding fitt's test into the stricter athletic one halved the penalty on
        reported copy written in short paragraphs.
        """
        asserted = "Creatine works.\n\nFive grams daily."
        tagged = "Creatine works, she says.\n\nFive grams daily."
        assert not re.search(cfg.ATHLETIC_ATTRIBUTION, tagged), (
            "the athletic gate must NOT see a bare pronoun tag as a source")
        assert (voice_affinity(tagged)["fitt"]
                == voice_affinity(asserted)["fitt"] + cfg.NEGATIVE_HIT)


# ═══════════════════════════════════════════════════════════════════════════════
# Voice affinity — the signal cross-contamination is built on
# ═══════════════════════════════════════════════════════════════════════════════

class TestVoiceAffinity:

    def test_returns_all_three_registers_as_ints(self):
        aff = voice_affinity(ATHLETIC_PASS_1)
        assert set(aff) == {"athletic", "people", "fitt"}
        assert all(isinstance(v, int) for v in aff.values())

    def test_each_clean_sample_leads_on_its_own_register(self):
        for section, text in CLEAN_CASES:
            aff = voice_affinity(text)
            assert aff[required_voice(section)] == max(aff.values()), section

    def test_affinity_discriminates_where_clamped_scores_cannot(self):
        """Both texts clamp to 100 on their own register; only the deltas separate them."""
        assert score_people(PEOPLE_PASS_1)[0] == score_fitt(FITT_PASS_1)[0] == cfg.SCORE_START
        assert voice_affinity(PEOPLE_PASS_1)["people"] != voice_affinity(FITT_PASS_1)["people"]

    def test_affinity_is_not_clamped_at_zero(self):
        assert voice_affinity(MOTIVATIONAL_HYPE)["athletic"] < 0

    # ── density ────────────────────────────────────────────────────────────────

    def test_density_dampens_length(self):
        """
        Repeating a section multiplies its raw affinity but not its register
        identity, so a margin denominated in raw points means something
        different at 100 words than at 600.
        """
        one = VAL_IN_NIGHTLIFE_FITT_OPINIONATED
        three = "\n\n".join([one] * 3)
        raw_growth = voice_affinity(three)["fitt"] / voice_affinity(one)["fitt"]
        density_growth = (voice_affinity_density(three)["fitt"]
                          / voice_affinity_density(one)["fitt"])
        assert raw_growth > 1.5
        assert density_growth == pytest.approx(1.0)

    @pytest.mark.parametrize("copies", [2, 3, 5, 10])
    def test_density_is_exactly_invariant_under_duplication(self, copies):
        """
        THE scale-invariance property, and the one the old density did not have.

        Duplicating a section changes nothing about its register: it is the same
        prose, at N times the length. Per-occurrence evidence and the word count
        both scale by N and cancel; section-level evidence is unchanged because
        a duplicated staccato section is still staccato and a duplicated
        attributed section is still attributed. So every density must come back
        identical, exactly, not approximately.

        Under the old single-channel density the +/-10 gates were divided by the
        word count along with everything else, so this ratio decayed as 1/N and
        contamination switched itself off on long copy.
        """
        for base in (VAL_IN_CULTURE_ATHLETIC_PLAIN, VAL_IN_SOCIAL_PEOPLE_ORDINARY,
                     VAL_IN_RECOVERY_FITT_LONG):
            one = voice_affinity_density(base)
            many = voice_affinity_density("\n\n".join([base] * copies))
            for register in one:
                assert many[register] == pytest.approx(one[register]), (
                    f"{register} moved from {one[register]:.3f} to "
                    f"{many[register]:.3f} at {copies}x length")

    def test_section_level_evidence_is_not_divided_by_length(self):
        """
        The mechanism, stated directly. A section-level term is worth its full
        value in the density no matter how long the section is; a per-occurrence
        term is worth its value per DENSITY_BASELINE_WORDS words.
        """
        gate_only = " ".join(["padding"] * 900)          # fails all three gates
        for register in ("athletic", "people", "fitt"):
            assert voice_affinity_density(gate_only)[register] <= -cfg.REGISTER_GATE, (
                f"{register} gate decayed to "
                f"{voice_affinity_density(gate_only)[register]:.2f} at 900 words")

    def test_density_does_not_inflate_short_texts(self):
        """
        Under the baseline length the raw delta is used as-is, never scaled up:
        a 20-word fragment is too little evidence to multiply by five.

        The fixture carries real per-occurrence markers on purpose. A fragment
        with none of them has nothing to scale, so it would pass this test under
        any scaling rule at all and prove nothing.
        """
        short = "5 grams works.\n\n300 mg before bed helps.\n\nPlain creatine is best."
        assert len(short.split()) < cfg.DENSITY_BASELINE_WORDS
        assert _fitt_per_occurrence(short) != 0, "fixture must have something to scale"
        assert voice_affinity_density(short) == voice_affinity(short)

    def test_a_short_text_would_be_wildly_inflated_without_the_floor(self):
        """States what the floor is worth, so removing it cannot pass silently."""
        short = "5 grams works.\n\n300 mg before bed helps.\n\nPlain creatine is best."
        words = len(short.split())
        unfloored = (voice_affinity_density(short)["fitt"]
                     - _fitt_per_occurrence(short)
                     + _fitt_per_occurrence(short) * cfg.DENSITY_BASELINE_WORDS / words)
        assert unfloored > voice_affinity_density(short)["fitt"] + 3 * cfg.POSITIVE_HIT


# ═══════════════════════════════════════════════════════════════════════════════
# The re-centring property: three registers, one origin
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistersShareAnOrigin:

    NEUTRAL = (
        "The platform runs along the north wall and the collars stay on a shelf "
        "beside it. The board lists the week as plain text. Plates return to the "
        "tree between rounds and the floor gets swept at the end of the block."
    )

    def test_register_neutral_prose_scores_the_same_in_every_register(self):
        """
        The heart of the re-centring. Before, this paragraph scored people +5,
        athletic 0 and fitt -10 before a single register-specific word was read,
        so a fixed margin could not mean the same thing in the three registers.
        """
        aff = voice_affinity(self.NEUTRAL)
        assert len(set(aff.values())) == 1, aff

    def test_no_register_takes_a_free_unconditional_bonus(self):
        """Every register's unconditional term is a gate, and every gate can fail."""
        assert voice_affinity(self.NEUTRAL)["people"] == -cfg.REGISTER_GATE
        assert voice_affinity(self.NEUTRAL)["athletic"] == -cfg.REGISTER_GATE
        assert voice_affinity(self.NEUTRAL)["fitt"] == -cfg.REGISTER_GATE

    def test_each_gate_is_worth_the_same_in_every_register(self):
        """
        Passing one register's gate must be worth what passing another's is.

        Both the athletic and the people fixture also collect the evidence that
        opened their gate as one per-occurrence marker, and that symmetry is
        deliberate: the athletic register used to be the only one that did not,
        which is the asymmetry Gate 2's held-out corpus found. The GATE term
        itself is identical in all three.
        """
        athletic_pass = self.NEUTRAL + " The coach says so."
        people_pass = "Carmen Ruiz is here. Her kids are loud. " + self.NEUTRAL
        fitt_pass = "The platform stands along the wall.\n\nThe board lists the week."
        # athletic: the gate flips, and "the coach says" is also one sourcing marker
        assert voice_affinity(athletic_pass)["athletic"] - voice_affinity(self.NEUTRAL)["athletic"] == (
            2 * cfg.REGISTER_GATE + cfg.POSITIVE_HIT)
        # people: the gate flips, and the fixture carries two access markers
        assert voice_affinity(people_pass)["people"] - voice_affinity(self.NEUTRAL)["people"] == (
            2 * cfg.REGISTER_GATE + 2 * cfg.POSITIVE_HIT)
        assert voice_affinity(fitt_pass)["fitt"] == cfg.REGISTER_GATE

        # the gate TERM is the same in all three; only the marker count differs
        for register, text in (("athletic", athletic_pass),
                               ("people", people_pass),
                               ("fitt", fitt_pass)):
            aff = voicelint.AFFINITY_SCORERS[register](text)
            assert aff.section_level >= cfg.REGISTER_GATE, register

    def test_numeric_claims_are_shared_evidence_not_athletic_only(self):
        """
        Both registers are data-forward. Scoring numbers for athletic alone made
        every data-dense fitt section read as athletic contamination.
        """
        without = "The squad ran far.\n\nThe squad rested."
        with_ = "The squad ran 12 miles.\n\nThe squad rested."
        for register in ("athletic", "fitt"):
            assert (voice_affinity(with_)[register]
                    == voice_affinity(without)[register] + cfg.POSITIVE_HIT), register


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-contamination — fixed texts, fixed verdicts
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossContamination:

    # ── clean and hostile-but-correct copy must NOT trip ───────────────────────

    @pytest.mark.parametrize("section,text", CLEAN_CASES)
    def test_clean_in_register_section_does_not_trip(self, section, text):
        r = lint_one(section, text)
        assert cross_flags(r) == [], f"{section} falsely flagged: {cross_flags(r)}"

    @pytest.mark.parametrize("section,text", HOSTILE_IN_REGISTER)
    def test_hostile_in_register_copy_does_not_trip(self, section, text):
        r = lint_one(section, text)
        assert cross_flags(r) == [], f"{section} falsely flagged: {cross_flags(r)}"

    @pytest.mark.parametrize("section,text", EXTERNAL_IN_REGISTER)
    def test_external_magazine_copy_does_not_trip(self, section, text):
        """sample_issue.json: in-register copy this module's author did not write."""
        r = lint_one(section, text)
        assert cross_flags(r) == [], f"{section} falsely flagged: {cross_flags(r)}"

    def test_clean_sections_take_no_contamination_penalty(self):
        for section, text in CLEAN_CASES:
            assert lint_one(section, text)["_debug"]["contamination_penalty"] == 0

    def test_audit_false_positive_is_gone(self):
        """
        Ordinary TIMBR house style for Culture — a named subject, pronouns and a
        quote — was reported as reading 11 points more like `people`.
        """
        r = lint_one("Culture", IN_CULTURE_ATHLETIC_WITH_A_SUBJECT)
        assert cross_flags(r) == []
        assert r["passed"] is True

    def test_fixed_floor_regression_guard(self):
        """
        The original rule fired whenever another voice scored > 50, which every
        voice does. A Fitt section carrying real Athletic markers but still
        leading on Fitt must not be flagged.
        """
        r = lint_one("Recovery", FITT_PASS_2)
        assert score_athletic(FITT_PASS_2)[0] > 50, "old rule's trigger condition holds"
        assert cross_flags(r) == []

    # ── genuinely cross-register copy MUST trip ────────────────────────────────

    @pytest.mark.parametrize("section,written_in,text", CALIBRATION_CROSS_REGISTER)
    def test_cross_register_copy_trips_on_the_register_it_was_written_in(
            self, section, written_in, text):
        r = lint_one(section, text)
        assert any(f"more like {written_in} voice" in f for f in cross_flags(r)), (
            f"{section} written as {written_in} was not flagged: {r['_debug']}")

    def test_audit_miss_is_caught(self):
        """
        A `people`-required Nutrition section written as flat athletic reported
        copy: the worst wrong-voice margin was +1 and nothing fired.
        """
        r = lint_one("Nutrition", X_NUTRITION_AS_ATHLETIC_REPORT)
        assert any("more like athletic voice" in f for f in cross_flags(r))
        assert r["passed"] is False

    def test_contaminated_copy_scores_below_its_clean_counterpart(self):
        clean = lint_one("Nightlife", FITT_PASS_3)["voice_score"]
        contaminated = lint_one("Nightlife", CONTAMINATION_FITT_AS_PEOPLE)["voice_score"]
        assert contaminated < clean

    def test_each_flag_costs_exactly_one_penalty(self):
        r = lint_one("Supplements", CONTAMINATION_FITT_AS_ATHLETIC)
        assert r["_debug"]["contamination_penalty"] == (
            len(cross_flags(r)) * cfg.CROSS_CONTAMINATION_PENALTY)

    def test_off_voice_hype_is_not_mistaken_for_contamination(self):
        """Motivational hype is bad copy, not another register — no other voice leads."""
        r = lint_one("Recovery", MOTIVATIONAL_HYPE)
        assert cross_flags(r) == []
        assert any("Fitt negative marker" in f for f in r["contamination_flags"])

    def test_a_negative_affinity_never_counts_as_contamination(self):
        """
        Two registers can both be absent. "Less bad" is not "present": the other
        register's affinity has to be positive before a lead means anything.
        """
        text = (" ".join(["padding"] * 60) + " The result was amazing and the block "
                "was incredible and the session was awesome.")
        aff = voice_affinity_density(text)
        assert aff["people"] - aff["athletic"] >= cfg.CROSS_CONTAMINATION_MARGIN
        assert aff["people"] < 0 and aff["fitt"] < 0
        assert cross_flags(lint_one("Training", text)) == []

    # ── boundary conditions, added after mutation testing found them open ────

    def test_the_margin_comparison_fires_AT_the_constant_not_past_it(self):
        """
        Found by mutation: `margin >= MARGIN` -> `margin > MARGIN` survived the
        whole suite, because no text in any corpus lands exactly on the line.
        The rule is documented as "at least CROSS_CONTAMINATION_MARGIN points",
        so the boundary belongs to contamination.

        200 words: 12 people markers (+24) and 7 athletic place markers (+14),
        both gates failing. people -10+12 = +2, athletic -10+7 = -3, margin
        exactly +5.0.
        """
        text = (" ".join(["padding"] * 141)
                + " Her kids are loud." * 6
                + " At Rainier the crew waited." * 7)
        dens = voice_affinity_density(text)
        assert dens["people"] - dens["athletic"] == pytest.approx(
            cfg.CROSS_CONTAMINATION_MARGIN), "fixture drifted off the boundary"
        assert dens["people"] > 0, "the leading register must be present at all"
        assert cross_flags(lint_one("Training", text)), "the boundary must fire"

    def test_a_register_at_exactly_zero_affinity_is_not_present(self):
        """
        Found by mutation: `density[other] > 0` -> `>= 0` survived, because the
        corpus has registers that are absent (negative) and registers that are
        present (positive) and none sitting exactly on nothing. Zero affinity is
        the absence of evidence, so it cannot lead anything.

        120 words: 6 people markers (+12) against a failed people gate (-10) is
        exactly 0.0, and athletic is -10, so the LEAD is +10 — twice the margin.
        It must still not fire.
        """
        text = " ".join(["padding"] * 108) + " Her kids are loud." * 3
        dens = voice_affinity_density(text)
        assert dens["people"] == 0.0, "fixture drifted off zero"
        assert dens["people"] - dens["athletic"] >= 2 * cfg.CROSS_CONTAMINATION_MARGIN
        assert cross_flags(lint_one("Training", text)) == []

    def test_the_penalty_cannot_push_a_score_below_zero(self):
        """
        Found by mutation: dropping the floor clamp on the final score survived,
        because nothing in the corpus is both floored AND contaminated. A
        contaminated section that is also terrible in its own register would
        have reported -18 into results/*.json.
        """
        text = ("Get ready! You should try this! You need it! Are you ready?! " * 6
                + " Carmen Ruiz is standing in her kitchen. Her kids are loud."
                  " Her dog barks.")
        r = lint_one("Training", text)
        assert r["_debug"]["contamination_penalty"] > 0, "fixture is not contaminated"
        assert r["_debug"]["primary_delta"] < -cfg.SCORE_START, "fixture is not floored"
        assert r["voice_score"] == 0
        assert r["passed"] is False

    def test_margin_is_relative_not_absolute(self):
        """A high absolute other-voice score is harmless while the primary leads."""
        aff = voice_affinity_density(ATHLETIC_PASS_1)
        assert score_people(ATHLETIC_PASS_1)[0] == cfg.SCORE_START  # absolute is maxed
        assert aff["people"] - aff["athletic"] < cfg.CROSS_CONTAMINATION_MARGIN
        assert cross_flags(lint_one("Training", ATHLETIC_PASS_1)) == []

    def test_margin_is_measured_on_density_not_raw_points(self):
        """
        Raw points do not normalise for length, so an in-register section
        accumulates a wrong-register lead purely by being long enough to ship.
        Stated as a growth property rather than as one text's numbers, because
        one text's numbers move whenever the markers move and the property is
        what actually has to hold.

        The text is the 80-word Recovery section from sample_issue.json —
        external copy this module's author did not write, and the binding worst
        in-register case for the margin (+3.00, on the athletic/fitt axis).

        It used to be the Gate-2 held-out Training feature, and that text no
        longer exhibits the property: once PRONOUN_ATTRIBUTION gave a reported
        feature credit for de-duplicating its source's name, G2_C2 leads
        athletic in RAW points too (60 vs 52 at 1128 words), so there is no
        wrong-register raw lead left on it to demonstrate. That is the fix
        working, not the guard weakening — G2_C2 stays pinned as a Gate-2
        regression fixture in GATE2_IN_REGISTER. The property being guarded here
        is about the two UNITS, so it needs a text that still has a raw lead.
        """
        section = "Recovery"
        source = dict(EXTERNAL_IN_REGISTER)["Recovery"]
        # BOTH sides are taken above DENSITY_BASELINE_WORDS. The source section
        # is 80 words and _density deliberately does not scale a sub-baseline
        # text up ("a 20-word fragment is too little evidence to multiply by
        # five"), so an 80-word text is not a valid witness for an invariance
        # claim — its density is divided by 100 and its triple's by 300. That is
        # the documented floor doing its job, not a violation of the property.
        short = _grow(source, 400)
        grown = _grow(source, 1100)

        # The required register is read from the section, not hard-coded. It was
        # hard-coded to "athletic", which is why repointing this test at a
        # Recovery section silently inverted the lead instead of failing loudly.
        req = required_voice(section)
        raw = voice_affinity(grown)
        dens = voice_affinity_density(grown)
        raw_lead = max(raw[v] - raw[req] for v in raw if v != req)
        density_lead = max(dens[v] - dens[req] for v in dens if v != req)

        raw_short = voice_affinity(short)
        assert raw_lead >= 5 * cfg.CROSS_CONTAMINATION_MARGIN, "raw points would fire hard"
        assert raw_lead > max(raw_short[v] - raw_short[req] for v in raw_short if v != req), (
            "the raw lead must GROW with length — that is the defect")
        assert density_lead < cfg.CROSS_CONTAMINATION_MARGIN, "density must not"
        assert cross_flags(lint_one(section, grown)) == []

        # ... and the density is the SAME number the shorter text produced,
        # which is the whole claim.
        dens_short = voice_affinity_density(short)
        assert density_lead == pytest.approx(
            max(dens_short[v] - dens_short[req] for v in dens_short if v != req))


# ═══════════════════════════════════════════════════════════════════════════════
# CALIBRATION — the margin, re-derived from the corpus on every run
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarginDerivation:
    """
    The DERIVATION half. Everything here is measured on the corpus the constant
    came from, so on its own none of it can refute the constant. That is the
    trap the previous two margins fell into and the reason
    TestMarginValidation exists below.
    """

    def test_the_two_halves_of_the_corpus_separate(self):
        """
        If in-register and cross-register margins overlap, NO threshold works
        and the number is a coin flip. The margin of 10 hid exactly this: on 12
        texts its author had not written, in-register reached +11 while
        cross-register bottomed out at +1.
        """
        worst_in, weakest_cross = band(CALIBRATION_IN_REGISTER, CALIBRATION_CROSS_REGISTER)
        assert worst_in < weakest_cross, (
            f"bands overlap: in-register reaches {worst_in:+.1f}, "
            f"cross-register bottoms at {weakest_cross:+.1f}")

    def test_cross_contamination_margin_is_the_midpoint_of_the_derivation_band(self):
        """
        The constant is the MIDPOINT of the separating band, recomputed here.
        Re-run after any change to the markers or the scale: it is the
        derivation, not a record of one.

        This assertion is CIRCULAR by construction and is kept only because a
        derivation should be reproducible. It is not evidence that the constant
        works. TestMarginValidation is.
        """
        worst_in, weakest_cross = band(CALIBRATION_IN_REGISTER, CALIBRATION_CROSS_REGISTER)
        assert worst_in < cfg.CROSS_CONTAMINATION_MARGIN <= weakest_cross
        assert cfg.CROSS_CONTAMINATION_MARGIN == round((worst_in + weakest_cross) / 2), (
            f"band is ({worst_in:+.1f}, {weakest_cross:+.1f}]; midpoint is "
            f"{(worst_in + weakest_cross) / 2:+.1f}, constant is "
            f"{cfg.CROSS_CONTAMINATION_MARGIN}")

    def test_the_corpus_contains_texts_the_author_did_not_write(self):
        """A calibration on self-authored fixtures only is how the last one died."""
        assert len(EXTERNAL_IN_REGISTER) >= 7, "sample_issue.json missing from the corpus"

    def test_the_corpus_covers_every_wrong_voice_direction(self):
        directions = {(required_voice(s), v) for s, v, _ in CALIBRATION_CROSS_REGISTER}
        for required in ("athletic", "people", "fitt"):
            for written in ("athletic", "people", "fitt"):
                if required != written:
                    assert (required, written) in directions, (required, written)

    def test_the_band_width_is_recorded_and_is_below_the_two_marker_bar(self):
        """
        This used to assert `weakest_cross - worst_in >= 2 * POSITIVE_HIT` — a
        band at least two markers wide — and it passed, on a corpus that did not
        contain the shape that binds. It does now, and the band does not clear
        that bar any more. Pooled over all three corpora it is 2.91 wide against
        a scale whose smallest unit is 2.

        The bar is not lowered here, it is INVERTED into a guard on the
        limitation note. voice_config documents the narrow band as a resolution
        limit of a lexical mechanism on the athletic/people axis; if a future
        change ever widens the band past two markers, that note has gone stale
        and this test says so rather than passing quietly.

        It fired. PRONOUN_ATTRIBUTION widened the DERIVATION band from 3.57 to
        4.15 — past the two-marker bar — because it moved reported features up
        without moving profiles, and because fixing the `did not return` sense
        error in ATHLETIC_NON_RESPONSE stopped a wrong-register profile
        collecting a point of athletic sourcing it had never earned.

        So the bar now sits on the POOLED band, which is the honest bound and
        which did NOT move: 2.91, over every text in all four corpora with
        nothing held out. The derivation band on its own was never the binding
        number — a band measured on the corpus that set the constant cannot
        refute it — and the RESOLUTION LIMIT note is written against the pooled
        figure. Both are recorded here so neither can drift silently.
        """
        worst_in, weakest_cross = band(CALIBRATION_IN_REGISTER, CALIBRATION_CROSS_REGISTER)
        width = weakest_cross - worst_in
        assert width > 0, "the halves must at least separate"
        assert 4.0 <= width <= 5.0, f"recorded derivation width was 4.15, measured {width:.2f}"

        pooled_in = CALIBRATION_IN_REGISTER + VALIDATION_IN_REGISTER + GATE2_IN_REGISTER
        pooled_x = (CALIBRATION_CROSS_REGISTER + VALIDATION_CROSS_REGISTER
                    + GATE2_CROSS_REGISTER)
        p_in, p_cross = band(pooled_in, pooled_x)
        pooled_width = p_cross - p_in
        assert pooled_width > 0, "the pooled halves must at least separate"
        assert pooled_width < 2 * cfg.POSITIVE_HIT, (
            f"the POOLED band is now {pooled_width:.2f} wide, which clears the "
            f"two-marker bar. THE RESOLUTION LIMIT note in voice_config is stale "
            f"and must be rewritten before this test is changed back.")
        assert 2.5 <= pooled_width <= 3.5, (
            f"recorded pooled width was 2.91, measured {pooled_width:.2f}")

    def test_the_pooled_band_over_every_corpus_still_separates(self):
        """
        The number that actually bounds the constant. Nothing is held out any
        more — all three corpora were consulted while repairing the marker set —
        so the honest statement is the worst case over every text this module
        has ever been measured against, in one band.
        """
        all_in = CALIBRATION_IN_REGISTER + VALIDATION_IN_REGISTER + GATE2_IN_REGISTER
        all_x = (CALIBRATION_CROSS_REGISTER + VALIDATION_CROSS_REGISTER
                 + GATE2_CROSS_REGISTER)
        worst_in, weakest_cross = band(all_in, all_x)
        assert worst_in < cfg.CROSS_CONTAMINATION_MARGIN <= weakest_cross, (
            f"pooled band is ({worst_in:+.2f}, {weakest_cross:+.2f}] and the "
            f"constant is {cfg.CROSS_CONTAMINATION_MARGIN}")
        # the measured headroom, both directions, stated as fact
        assert cfg.CROSS_CONTAMINATION_MARGIN - worst_in == pytest.approx(2.00, abs=0.01)
        assert weakest_cross - cfg.CROSS_CONTAMINATION_MARGIN == pytest.approx(0.91, abs=0.01)

    def test_the_derivation_corpus_contains_the_shape_that_refuted_the_last_one(self):
        """
        The root cause of the previous miss was a corpus, not a constant: it had
        reported copy and it had profiles and nothing in between. Both halves now
        carry the in-between shape, and this test is what stops it being dropped.
        """
        assert ("Culture", LONG_IN_CULTURE_REPORTED_HUMAN_INTEREST) in CALIBRATION_IN_REGISTER
        assert ("Training", LONG_IN_TRAINING_REPORTED_HUMAN_INTEREST) in CALIBRATION_IN_REGISTER
        assert ("Culture", "people", LONG_X_CULTURE_AS_A_QUIET_PROFILE) in CALIBRATION_CROSS_REGISTER
        # and the in-between shape is what binds the cross half
        _, weakest_cross = band(CALIBRATION_IN_REGISTER, CALIBRATION_CROSS_REGISTER)
        assert weakest_cross == pytest.approx(
            intended_margin("Culture", LONG_X_CULTURE_AS_A_QUIET_PROFILE, "people"))

    # ── the root cause of the length defect: a corpus that never grew up ─────

    def test_the_derivation_corpus_reaches_production_length(self):
        """
        The previous corpus ran 35 to 208 words with nothing at 400 or more,
        while the config claimed it spanned "35 to 1000+ words". Every length
        that can legally reach this gate was outside it, so the length term in
        the density calculation was calibrated on copy that can never ship.
        """
        lengths = [len(t.split()) for _, t in CALIBRATION_IN_REGISTER]
        lengths += [len(t.split()) for _, _, t in CALIBRATION_CROSS_REGISTER]
        assert max(lengths) >= 1100, f"corpus tops out at {max(lengths)} words"
        assert sum(1 for l in lengths if l >= 400) >= 8
        assert sum(1 for l in lengths if l >= 800) >= 4

    def test_both_halves_reach_production_length(self):
        """A long in-register half alone would only prove it stopped firing."""
        assert sum(1 for _, t in CALIBRATION_IN_REGISTER if len(t.split()) >= 400) >= 4
        assert sum(1 for _, _, t in CALIBRATION_CROSS_REGISTER if len(t.split()) >= 400) >= 4

    def test_no_claim_about_the_corpus_that_the_corpus_does_not_support(self):
        """
        voice_config used to assert the corpus "spans 35 to 1000+ words and the
        band has to hold across all of it". It spanned 35 to 208. That sentence
        was the entire justification for trusting the normalisation.
        """
        lengths = [len(t.split()) for _, t in CALIBRATION_IN_REGISTER]
        lengths += [len(t.split()) for _, _, t in CALIBRATION_CROSS_REGISTER]
        config_src = open(cfg.__file__, encoding="utf-8").read()
        for claimed in re.findall(r'(\d+)\s*to\s*(\d+)\s+words', config_src):
            lo, hi = int(claimed[0]), int(claimed[1])
            if lo > 40:          # a range about section lengths, not about this corpus
                continue
            assert min(lengths) <= lo and max(lengths) >= hi, (
                f"voice_config claims a corpus of {lo}-{hi} words; it is "
                f"{min(lengths)}-{max(lengths)}")


class TestMarginValidation:
    """
    The HELD-OUT half. These texts were written independently, are disjoint from
    the derivation corpus, and were never consulted when the constant was
    chosen. Only these can refute it.
    """

    def test_the_two_corpora_are_disjoint(self):
        derivation = {t for _, t in CALIBRATION_IN_REGISTER}
        derivation |= {t for _, _, t in CALIBRATION_CROSS_REGISTER}
        validation = {t for _, t in VALIDATION_IN_REGISTER}
        validation |= {t for _, _, t in VALIDATION_CROSS_REGISTER}
        assert derivation & validation == set(), "validation corpus leaked into derivation"
        assert len(validation) == 12

    def test_every_validation_text_is_at_production_length(self):
        """
        A validation set below the legal minimum would validate nothing: those
        are lengths ProhibLint hard-fails on word count before VoiceLint's
        verdict can matter.
        """
        for section, text in VALIDATION_IN_REGISTER:
            lo, hi = WORD_COUNT_RANGES[section]
            assert lo <= len(text.split()) <= hi, (section, len(text.split()))
        for section, _, text in VALIDATION_CROSS_REGISTER:
            lo, hi = WORD_COUNT_RANGES[section]
            assert lo <= len(text.split()) <= hi, (section, len(text.split()))

    def test_the_validation_corpus_covers_every_wrong_voice_direction(self):
        directions = {(required_voice(s), v) for s, v, _ in VALIDATION_CROSS_REGISTER}
        for required in ("athletic", "people", "fitt"):
            for written in ("athletic", "people", "fitt"):
                if required != written:
                    assert (required, written) in directions, (required, written)

    def test_the_held_out_corpus_separates(self):
        """
        The whole point. If this fails the margin is refuted, whatever the
        derivation corpus says about it.
        """
        worst_in, weakest_cross = band(VALIDATION_IN_REGISTER, VALIDATION_CROSS_REGISTER)
        assert worst_in < weakest_cross, (
            f"held-out bands overlap: in-register reaches {worst_in:+.1f}, "
            f"cross-register bottoms at {weakest_cross:+.1f}")

    def test_the_derived_margin_sits_inside_the_held_out_band(self):
        worst_in, weakest_cross = band(VALIDATION_IN_REGISTER, VALIDATION_CROSS_REGISTER)
        assert worst_in < cfg.CROSS_CONTAMINATION_MARGIN <= weakest_cross, (
            f"margin {cfg.CROSS_CONTAMINATION_MARGIN} is outside the held-out "
            f"band ({worst_in:+.2f}, {weakest_cross:+.2f}]")

    @pytest.mark.parametrize("section,text", VALIDATION_IN_REGISTER)
    def test_held_out_in_register_copy_is_not_flagged(self, section, text):
        r = lint_one(section, text)
        assert cross_flags(r) == [], f"{section} falsely flagged: {cross_flags(r)}"
        assert r["passed"] is True

    @pytest.mark.parametrize("section,written_in,text", VALIDATION_CROSS_REGISTER)
    def test_held_out_cross_register_copy_is_flagged(self, section, written_in, text):
        r = lint_one(section, text)
        assert any(f"more like {written_in} voice" in f for f in cross_flags(r)), (
            f"{section} written as {written_in} was not flagged: {r['_debug']}")
        assert r["passed"] is False

    def test_the_headroom_is_reported_not_assumed(self):
        """
        The previous version of this test measured the headroom on THIS corpus
        only and concluded "8.00 points before a false positive and 1.21 before
        a miss", which voice_config then stated as a property of the mechanism.
        On Gate 2's held-out text the true ordering was inverted: -3.0 before a
        false positive and +14.8 before a miss. The mechanism was far more likely
        to block good copy than to pass bad copy, and the corpus that said
        otherwise simply did not contain the shape that breaks it.

        So the headroom is asserted per corpus AND pooled, and the pooled number
        is the one that counts. No assertion here is allowed to be softer than
        the pooled band in TestMarginDerivation.
        """
        per_corpus = {
            "derivation": band(CALIBRATION_IN_REGISTER, CALIBRATION_CROSS_REGISTER),
            "validation": band(VALIDATION_IN_REGISTER, VALIDATION_CROSS_REGISTER),
            "gate2": band(GATE2_IN_REGISTER, GATE2_CROSS_REGISTER),
        }
        for name, (worst_in, weakest_cross) in per_corpus.items():
            assert worst_in < cfg.CROSS_CONTAMINATION_MARGIN <= weakest_cross, (
                f"{name}: band ({worst_in:+.2f}, {weakest_cross:+.2f}] excludes "
                f"the constant {cfg.CROSS_CONTAMINATION_MARGIN}")

        fp = min(cfg.CROSS_CONTAMINATION_MARGIN - w for w, _ in per_corpus.values())
        miss = min(c - cfg.CROSS_CONTAMINATION_MARGIN for _, c in per_corpus.values())
        # Both are under one marker hit at the length of the text that binds
        # them. Recorded, not claimed to be adequate.
        assert fp == pytest.approx(2.00, abs=0.01), f"{fp:.2f} before a false positive"
        assert miss == pytest.approx(0.91, abs=0.01), f"{miss:.2f} before a miss"

    def test_voice_config_does_not_claim_headroom_it_does_not_have(self):
        """
        The specific sentence that was refuted: "8.00 points of margin before a
        false positive and 1.21 before a miss ... closer to missing contaminated
        copy than to blocking clean copy." Every one of those claims was false on
        held-out text. Nothing in the config may assert a headroom figure that
        this suite does not measure.
        """
        src = open(cfg.__file__, encoding="utf-8").read()
        per_corpus = [band(CALIBRATION_IN_REGISTER, CALIBRATION_CROSS_REGISTER),
                      band(VALIDATION_IN_REGISTER, VALIDATION_CROSS_REGISTER),
                      band(GATE2_IN_REGISTER, GATE2_CROSS_REGISTER)]
        fp = min(cfg.CROSS_CONTAMINATION_MARGIN - w for w, _ in per_corpus)
        miss = min(c - cfg.CROSS_CONTAMINATION_MARGIN for _, c in per_corpus)

        claimed_fp = re.search(r'before a FALSE POSITIVE\s*:\s*\+?([\d.]+)', src)
        claimed_miss = re.search(r'before a MISS\s*:\s*\+?([\d.]+)', src)
        assert claimed_fp and claimed_miss, "the config must state its headroom"
        assert float(claimed_fp.group(1)) == pytest.approx(fp, abs=0.01)
        assert float(claimed_miss.group(1)) == pytest.approx(miss, abs=0.01)

        # The refuted sentence may appear ONLY as a retraction. Quoting a claim
        # in order to record that it was wrong is the point; restating it as
        # current is the defect. So it has to sit inside a block that says so.
        for refuted in ("8.00 points of margin", "closer to missing contaminated copy"):
            at = src.find(refuted)
            if at == -1:
                continue
            context = src[max(0, at - 400):at]
            assert "used to read" in context or "was WRONG" in context, (
                f"{refuted!r} appears in voice_config without a retraction around it")

    # ── the corpus that refuted the previous constant, kept as a regression ──

    @pytest.mark.parametrize("section,text", GATE2_IN_REGISTER)
    def test_gate2_in_register_copy_is_not_flagged(self, section, text):
        r = lint_one(section, text)
        assert cross_flags(r) == [], f"{section} falsely flagged: {cross_flags(r)}"
        assert r["passed"] is True

    @pytest.mark.parametrize("section,written_in,text", GATE2_CROSS_REGISTER)
    def test_gate2_cross_register_copy_is_flagged(self, section, written_in, text):
        r = lint_one(section, text)
        assert any(f"more like {written_in} voice" in f for f in cross_flags(r)), (
            f"{section} written as {written_in} was not flagged: {r['_debug']}")
        assert r["passed"] is False

    def test_the_two_reported_human_interest_sections_pass(self):
        """
        The blocker, named. Both cleared the athletic gate — this module
        certified them as properly attributed, non-shouting reported prose — and
        were then hard-failed as people-contaminated on a per-occurrence channel
        the athletic register had no vocabulary in. Margins were +9.0 and +8.1
        against a margin of 6.
        """
        for section, text, was in (("Culture", G2_C1_CULTURE_CLOSURE, 8.96),
                                   ("Training", G2_C2_TRAINING_REPORTED, 8.11)):
            r = lint_one(section, text)
            assert r["passed"] is True, section
            assert cross_flags(r) == [], section
            assert worst_other_margin(section, text) < was - 3, (
                f"{section} margin barely moved; it was {was:+.2f}")

    def test_two_lines_of_human_colour_no_longer_fail_a_reported_feature(self):
        """
        Gate 2's severity measurement: the same reported Culture feature with
        ordinary human colour added a line at a time went from pass at one line
        to hard FAIL at two. "His mornings start at four thirty. His wife drives
        him in on the bad days." was enough to block it.
        """
        base = G2_C1_CULTURE_CLOSURE
        colour = (" His mornings start at four thirty."
                  " His wife drives him in on the bad days."
                  " His daughter has started coming on Saturdays."
                  " He grew up two streets away."
                  " His hands do not close in the cold any more."
                  " Her husband trains there too.")
        for extra in range(0, len(colour.split(".")) - 1):
            text = base + "\n\n" + ".".join(colour.split(".")[:extra + 1]).strip() + "."
            r = lint_one("Culture", text)
            assert r["passed"] is True, f"{extra + 1} lines of colour blocked the section"


class TestWordCountRangesAreCopiedFaithfully:

    def test_the_word_count_ranges_still_match_prohiblint(self):
        """
        VoiceLint does not import ProhibLint and must not start to. The ranges
        are transcribed, so the transcription is checked instead.
        """
        prohib = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                              "timbr_eval", "prohiblint", "prohiblint.py")
        if not os.path.exists(prohib):
            prohib = os.path.join(os.path.dirname(HERE), "prohiblint", "prohiblint.py")
        if not os.path.exists(prohib):        # pragma: no cover - repo layout guard
            pytest.skip("prohiblint not present")
        src = open(prohib, encoding="utf-8").read()
        block_ = re.search(r'WORD_COUNT_RANGES\s*=\s*\{(.*?)\}', src, re.DOTALL).group(1)
        theirs = {m[0]: (int(m[1]), int(m[2]))
                  for m in re.findall(r'"(\w+)":\s*\((\d+),\s*(\d+)\)', block_)}
        assert theirs == WORD_COUNT_RANGES

    def test_voicelint_does_not_import_prohiblint(self):
        """
        The two linters are independent by design. Referring to ProhibLint in a
        comment is fine and necessary; importing it is not.
        """
        for path in (voicelint.__file__, cfg.__file__):
            src = open(path, encoding="utf-8").read()
            assert not re.search(r'^\s*(?:import|from)\s+prohiblint', src, re.M), path


# ═══════════════════════════════════════════════════════════════════════════════
# The EFFECTIVE pass bar
#
# The bar that matters is the affinity delta at which `passed` flips, not the
# value of PASS_THRESHOLD. Asserting the constant is what let the gate loosen by
# 15 points while the report claimed it had tightened:
#     old effective rule: clamp(100+d) - 20 >= 65  =>  pass when d >= -15
#     the loosened rule:  clamp(100+d) -  0 >= 70  =>  pass when d >= -30
# ═══════════════════════════════════════════════════════════════════════════════

#: One long paragraph. Attributed (athletic gate passes, +8), no named person
#: (people gate fails), not staccato (fitt gate fails) — so people and fitt stay
#: negative and can never trigger a contamination penalty that would confound
#: the reading. Carries no athletic marker of its own.
_BAR_BASE = (
    "According to the club report, the winter block is over and the athletes "
    "have returned to the water for the first sessions of a long and "
    "unremarkable spring that nobody will remember, which the report notes at "
    "some length without ever explaining why the sessions were scheduled the "
    "way that they were in the first place, or who signed off on them."
)
_BAR_POS = " At Rainier the crew waited."      # +POSITIVE_HIT, athletic only
_BAR_NEG = " The result was amazing."          # +NEGATIVE_HIT, athletic only


#: What the base is worth on its own. It used to be assumed equal to
#: REGISTER_GATE, on the reasoning that the base "carries no athletic marker of
#: its own" — which stopped being true the moment sourced attribution became
#: per-occurrence evidence, since the base is built out of attribution. Measured
#: rather than assumed, and the constructed delta is asserted against `target`
#: in the test itself, so a drift in either direction still fails loudly.
def _bar_base_delta():
    return voice_affinity(_BAR_BASE)["athletic"]


def _text_with_athletic_delta(target):
    """A Training-section text whose athletic affinity delta is exactly `target`."""
    need = target - _bar_base_delta()
    best = None
    for negatives in range(0, 60):
        for positives in range(0, 60):
            if positives * cfg.POSITIVE_HIT + negatives * cfg.NEGATIVE_HIT == need:
                if best is None or positives + negatives < sum(best):
                    best = (positives, negatives)
    assert best is not None, f"cannot build a text with delta {target}"
    positives, negatives = best
    return _BAR_BASE + _BAR_POS * positives + _BAR_NEG * negatives


#: The delta at which passing must flip. Not derived from PASS_THRESHOLD on
#: purpose — this is the independent statement of the editorial bar, and the
#: threshold constant has to agree with it.
EFFECTIVE_FAIL_FLOOR = -15


class TestEffectivePassBar:

    @pytest.mark.parametrize("target", list(range(0, -25, -1)))
    def test_pass_flips_at_the_effective_bar_and_nowhere_else(self, target):
        text = _text_with_athletic_delta(target)
        r = lint_one("Training", text)
        assert voice_affinity(text)["athletic"] == target, "fixture construction drifted"
        assert r["_debug"]["contamination_penalty"] == 0, "contamination confounds the reading"
        assert r["passed"] is (target >= EFFECTIVE_FAIL_FLOOR), (
            f"delta {target:+d} scored {r['voice_score']} and "
            f"{'passed' if r['passed'] else 'failed'}")

    def test_the_worst_passing_section_is_exactly_five_negative_markers_down(self):
        """The bar is denominated in the scale's own unit, not in raw points."""
        assert EFFECTIVE_FAIL_FLOOR == cfg.NEGATIVE_MARKER_BUDGET * cfg.NEGATIVE_HIT

    def test_the_threshold_constant_agrees_with_the_effective_bar(self):
        assert cfg.PASS_THRESHOLD == cfg.SCORE_START + EFFECTIVE_FAIL_FLOOR

    def test_a_single_non_staccato_slab_plus_two_hedges_still_fails(self):
        """
        The audit's reproduction case: a fitt section that is one dense slab
        (gate -8) with two hedge words (-6). It scored 64/FAIL under the
        original rule and 74/PASS after the threshold was loosened.
        """
        text = (
            "Contrast therapy might work for some athletes and could plausibly "
            "help with next-day output, though the size of the effect is the "
            "part nobody agrees on, and the protocols in circulation differ "
            "enough that the comparison across studies is close to meaningless "
            "for anyone deciding what to actually do after a hard session."
        )
        r = lint_one("Recovery", text)
        assert r["_debug"]["primary_delta"] == -cfg.REGISTER_GATE + 2 * cfg.NEGATIVE_HIT
        assert r["passed"] is False

    def test_threshold_is_not_hard_coded_in_voicelint(self):
        src = open(voicelint.__file__).read()
        assert re.search(r'(?<![\d.])%d(?![\d.])' % cfg.PASS_THRESHOLD, src) is None, (
            "threshold literal leaked into voicelint.py")
        assert "PASS_THRESHOLD" in src

    def test_voicelint_uses_the_config_value(self):
        assert voicelint.PASS_THRESHOLD == cfg.PASS_THRESHOLD

    @pytest.mark.parametrize("section,text", CLEAN_CASES + [
        ("Supplements", CONTAMINATION_FITT_AS_ATHLETIC),
        ("Culture", CONTAMINATION_ATHLETIC_AS_PEOPLE),
        ("Nutrition", PEOPLE_AS_DATA_DUMP),
        ("Recovery", MOTIVATIONAL_HYPE),
        ("Training", _text_with_athletic_delta(-18)),
    ])
    def test_passed_always_tracks_the_threshold(self, section, text):
        r = lint_one(section, text)
        assert r["passed"] == (r["voice_score"] >= cfg.PASS_THRESHOLD)

    @pytest.mark.parametrize("section,text", CLEAN_CASES + [
        ("Training", "Get ready! You should try this! You need it! Are you ready?! " * 10),
        ("Nutrition", PEOPLE_AS_DATA_DUMP),
        ("Supplements", " ".join(["padding"] * 200)),
    ])
    def test_score_stays_within_range(self, section, text):
        r = lint_one(section, text)
        assert 0 <= r["voice_score"] <= cfg.SCORE_START

    def test_worst_case_text_never_goes_negative(self):
        r = lint_one("Training", "Get ready! You should try this! You need it! Are you ready?! " * 20)
        assert r["voice_score"] == 0
        assert r["passed"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# The scale is pinned
#
# The margin and the threshold are denominated in these units, so the units may
# not drift silently. Every assertion below is a LITERAL expected value with its
# arithmetic spelled out — recomputing the expectation from the same constants
# would be a tautology, which is how POSITIVE_HIT 2->3, the rhythm bonus 5->0
# and the long-paragraph penalty -5->0 all survived the previous suite.
# ═══════════════════════════════════════════════════════════════════════════════

class TestScaleIsPinned:

    def test_positive_hit_is_worth_two_points(self):
        # 2 place markers (+2 each) + failed attribution gate (-10) = -6
        text = "At Rainier the crew waited. At Fremont the boats left."
        assert voice_affinity(text)["athletic"] == -6

    def test_negative_hit_costs_three_points(self):
        # 2 hype markers (-3 each) + failed attribution gate (-10) = -16
        text = "The block was amazing. The block was incredible."
        assert voice_affinity(text)["athletic"] == -16

    def test_register_gate_is_worth_ten_points_either_way(self):
        # 2 place markers (+4) + 1 sourcing marker (+2) + passed gate (+10) = +16
        passed = "At Rainier the crew waited. At Fremont the boats left, the coach says."
        failed = "At Rainier the crew waited. At Fremont the boats left."
        assert voice_affinity(passed)["athletic"] == 16
        assert voice_affinity(failed)["athletic"] == -6

    def test_a_sourcing_marker_is_worth_two_points(self):
        # failed attribution gate (-10) + nothing else = -10; one sourced
        # attribution flips the gate (+20) and adds one marker (+2)
        assert voice_affinity("The crew waited on the water.")["athletic"] == -10
        assert voice_affinity("The crew waited, the coach says.")["athletic"] == 12
        # a second, different source is a second marker and not a second gate
        assert voice_affinity(
            "The crew waited, the coach says. Nakashima noted the delay.")["athletic"] == 14

    def test_a_sourcing_marker_costs_the_people_register_one_negative(self):
        # "Carmen Ruiz is standing in her kitchen." = gate (+10) + access (+2)
        # + pronoun (+2) = +14; borrowed authority costs one negative marker
        anchor = "Carmen Ruiz is standing in her kitchen."
        assert voice_affinity(anchor)["people"] == 14
        assert voice_affinity(anchor + " The landlord says the rent is due.")["people"] == 11
        # ... but her OWN tagged voice is access, not borrowed authority
        assert voice_affinity(anchor + ' "The rent is due," she says.')["people"] > 14

    def test_earned_rhythm_bonus_is_worth_two_points(self):
        flat = ("The squad trained hard today. The squad trained hard again. "
                "The squad trained hard once more. The squad trained hard at the end.")
        mixed = ("Short. Fast. "
                 "The squad worked through a long and deliberate block that stretched "
                 "across many weeks of progressive overload and careful monitoring of "
                 "fatigue. The coaching staff reviewed every single session in detail "
                 "before deciding how the next training block would be structured for "
                 "the whole squad.")
        # both: failed attribution gate (-10); mixed adds the rhythm bonus (+2)
        assert voice_affinity(flat)["athletic"] == -10
        assert voice_affinity(mixed)["athletic"] == -8

    def test_long_paragraph_penalty_is_worth_one_negative_marker(self):
        # failed staccato gate (-10) + one over-long paragraph (-3) = -13
        long_para = " ".join(["padding"] * 90)
        assert voice_affinity(long_para)["fitt"] == -13
        # ... and a paragraph under the limit takes the gate hit only
        short_of_the_limit = " ".join(["padding"] * 70)
        assert voice_affinity(short_of_the_limit)["fitt"] == -10

    def test_every_over_long_paragraph_is_charged(self):
        # failed staccato gate (-10) + two over-long paragraphs (-6) = -16
        two_slabs = " ".join(["padding"] * 90) + "\n\n" + " ".join(["padding"] * 90)
        assert voice_affinity(two_slabs)["fitt"] == -16

    def test_staccato_gate_fires_exactly_at_the_configured_ratio(self):
        short = "Creatine works."
        slab = " ".join(["padding"] * 45)
        # 3 of 5 paragraphs short == 60%, exactly the line: the gate passes
        assert voice_affinity("\n\n".join([short] * 3 + [slab] * 2))["fitt"] == 10
        # 2 of 4 == 50%, one step below it: the gate fails
        assert voice_affinity("\n\n".join([short] * 2 + [slab] * 2))["fitt"] == -10

    def test_staccato_gate_is_worth_ten_points(self):
        # 3 short paragraphs, no other fitt signal = +10
        assert voice_affinity(
            "Creatine works.\n\nFive grams daily.\n\nNothing else comes close.")["fitt"] == 10

    def test_data_lead_and_data_claim_each_score_two_points(self):
        # "5 grams works." = staccato gate (+10) + data-led sentence (+2)
        #                    + one numeric claim (+2) = +14
        assert voice_affinity("5 grams works.")["fitt"] == 14
        assert voice_affinity("Five grams works.")["fitt"] == 10

    def test_kicker_bonus_is_worth_two_points(self):
        base = "Creatine works.\n\nFive grams daily.\n\n"
        assert voice_affinity(base + "Plain creatine is best.")["fitt"] == 12
        assert voice_affinity(
            base + "Plain creatine remains a reasonable option for most.")["fitt"] == 10

    def test_declarative_openings_bonus_is_worth_two_points(self):
        # staccato gate (+10) + declarative openings on both paragraphs (+2) = +12
        text = ("Protein powder: only if whole food falls short of the target.\n\n"
                "Foam rolling: ninety seconds per muscle group after the session.")
        assert voice_affinity(text)["fitt"] == 12

    def test_people_gate_is_worth_ten_points_either_way(self):
        # passed gate (+10) + "her kitchen" access (+2) + the pronoun (+2) = +14
        assert voice_affinity("Carmen Ruiz is standing in her kitchen.")["people"] == 14
        assert voice_affinity("At Cascade the room is cold.")["people"] == -10

    def test_people_marker_is_worth_two_points(self):
        # passed gate (+10) + "Her kids" access (+2) + the pronoun (+2) = +14
        assert voice_affinity("Carmen Ruiz is here. Her kids are loud.")["people"] == 14
        # ... and dropping the two markers drops exactly four points, and the
        # gate with them, because a name with no access is not a profile
        assert voice_affinity("Carmen Ruiz is here.")["people"] == -10

    def test_structural_hit_equals_one_lexical_marker(self):
        """
        Structural features are counted in the same unit as lexical markers.
        If they drift apart, the three registers stop sharing a scale.
        """
        assert cfg.STRUCTURAL_HIT == cfg.POSITIVE_HIT
        assert cfg.REGISTER_GATE == 5 * cfg.POSITIVE_HIT


# ═══════════════════════════════════════════════════════════════════════════════
# Contamination detection must not switch itself off at section length
#
# The reported defect: density divided the WHOLE affinity delta by the word
# count, but the +/-REGISTER_GATE terms are per-SECTION constants. On long copy
# the gates contributed nothing and the margin decayed roughly as 1/length, so
# real cross-register copy lost its lead purely by being long enough to ship.
# A 737-word Nutrition section written as a flat athletic wire report scored 98
# and passed with no flags; the 110-word version of the same shape failed.
# ═══════════════════════════════════════════════════════════════════════════════

def _grow(text, target_words):
    """Repeat a section until it reaches `target_words`, preserving its register."""
    parts, grown = [text], text
    while len(grown.split()) < target_words:
        parts.append(text)
        grown = "\n\n".join(parts)
    return grown


def _shorten(text, target_words):
    """
    The first whole paragraphs of a section, up to `target_words`.

    Truncating on a word boundary and rejoining with spaces would delete the
    paragraph breaks, and paragraph structure is two of the three register
    gates. That would measure the truncation, not the register.
    """
    kept, total = [], 0
    for para in [p for p in text.split("\n\n") if p.strip()]:
        kept.append(para)
        total += len(para.split())
        if total >= target_words:
            break
    return "\n\n".join(kept)


class TestScaleInvarianceOfContamination:

    @pytest.mark.parametrize("section,written_in,text", VALIDATION_CROSS_REGISTER)
    def test_cross_register_copy_fires_at_every_length(self, section, written_in, text):
        """
        Truncating an authentic cross-register text used to show the switch-off
        directly: it fired at 57, 113, 169 and 281 words and stopped at 349. It
        must now fire at every prefix long enough to be evidence at all.
        """
        total = len(text.split())
        legal_minimum = WORD_COUNT_RANGES[section][0]
        for n in list(range(legal_minimum, total, 60)) + [total]:
            prefix = _shorten(text, n)
            r = lint_one(section, prefix)
            assert any(f"more like {written_in} voice" in f for f in cross_flags(r)), (
                f"{section} as {written_in} stopped firing at "
                f"{len(prefix.split())} words: {r['_debug']['affinity_per_100w']}")

    @pytest.mark.parametrize("section,written_in,text", CALIBRATION_CROSS_REGISTER)
    def test_every_cross_register_fixture_survives_being_grown(self, section, written_in, text):
        """
        6 of 12 cross-register fixtures stopped firing before 400 words. Growing
        a section without changing its register must not change the verdict:
        that is what a length-normalised measure is for.
        """
        grown = _grow(text, 900)
        r = lint_one(section, grown)
        assert any(f"more like {written_in} voice" in f for f in cross_flags(r)), (
            f"{section} as {written_in} stopped firing at "
            f"{len(grown.split())} words: {r['_debug']['affinity_per_100w']}")

    def test_the_audit_reproduction_fails_at_production_length(self):
        """
        The exact reported case: a Nutrition section (legal range 600-900) written
        as flat athletic reported copy, no named human, no domestic detail, a wire
        report start to finish. It scored 98/PASS with no contamination flag.
        """
        text = _grow(X_NUTRITION_AS_ATHLETIC_REPORT, 700)
        lo, hi = WORD_COUNT_RANGES["Nutrition"]
        assert lo <= len(text.split()) <= hi, "reproduction must be at a legal length"
        r = lint_one("Nutrition", text)
        assert any("more like athletic voice" in f for f in cross_flags(r))
        assert r["passed"] is False

    def test_the_margin_does_not_decay_across_the_legal_range(self):
        """
        The margin at 1200 words must be the margin at 400 words. Under the old
        density it fell by roughly a factor of three across that range.
        """
        base = VAL_X_SOCIAL_AS_ATHLETIC
        margins = [intended_margin("Social", _grow(base, n), "athletic")
                   for n in (400, 800, 1200)]
        assert max(margins) - min(margins) < cfg.POSITIVE_HIT, margins


# ═══════════════════════════════════════════════════════════════════════════════
# The person detector, after the closed verb list
#
# The weak cue used to be a CLOSED 23-verb list, so any named person doing
# anything outside it was invisible. 12 of 15 real people were missed and each
# miss cost the people register 2 * REGISTER_GATE, the largest single term in
# the scale. The replacement uses an OPEN class for the action and closed
# classes only for what has to be excluded.
# ═══════════════════════════════════════════════════════════════════════════════

#: Ordinary people doing ordinary things. Not one of these verbs was in the old
#: cue list, and none of them is in any list in voicelint.py either.
REAL_PEOPLE_ORDINARY_VERBS = [
    "Devon Ashworth carries the cones out before the group arrives.",
    "Priya Raman cooks the same thing every Sunday.",
    "Renata Boyle coaches the 6am group.",
    "Ruben Castellanos pours the first cup at five.",
    "Tomas Herrera weighs his oats on a kitchen scale.",
    "Marina Vasilenko unlocks the door at ten to five.",
    "Elena Vasquez drinks it with breakfast.",
    "Denise Whitaker signed up for her first half marathon.",
    "Jasmine Torres finished the 5K without stopping.",
    "Aisha Coleman unpacks sample packets onto the table.",
    "Carmen Ruiz blends beet greens and frozen mango.",
    "Marcus Webb rewrote the whole block over one weekend.",
    "Helen Marsh supervised the review.",
    "Delphine Okoro carried two folding tables across the park.",
    "Rowan Achebe sweeps the platforms herself.",
]

#: Things that are not people. The first is the reported false positive.
NOT_PEOPLE = [
    "Cascade Rowing is the older club.",
    "Green Lake Trail runs three miles around the water.",
    "Seattle Athletic Club has spent a decade on this.",
    "South Lake Union is quiet on a Sunday.",
    "Pike Place is busy by seven.",
    "At Cascade the room is cold before six.",
    "Some Tuesday mornings the platform is empty.",
    "The Nordic consensus meeting was held in June.",
    "Every Thursday evening the group meets.",
    "Husky Stadium opens at five.",
    "Queen Anne is steeper than it looks.",
    "West Seattle is a different city on a Sunday.",
    # Organisations whose name parts are NOT category nouns, so nothing but the
    # copula rule and the participle rule can reject them.
    "Ironbark Forge is the older club.",
    "Rainier Provisions is the quieter option on a Sunday.",
    "Rainier Forge hosting the winter meet is old news.",
    "Ironbark Provisions carrying two brands is unusual.",
]


class TestPersonDetectorUsesAnOpenVerbClass:

    @pytest.mark.parametrize("text", REAL_PEOPLE_ORDINARY_VERBS)
    def test_a_person_doing_anything_is_detected(self, text):
        assert voicelint._named_person(text) is True, text

    @pytest.mark.parametrize("text", NOT_PEOPLE)
    def test_places_and_organisations_are_not_people(self, text):
        assert voicelint._named_person(text) is False, text

    @pytest.mark.parametrize("verb", [
        "marinates", "recalibrates", "unspools", "resurfaces", "photographs",
        "rewires", "outlasts", "annotates", "chalks", "reseeds",
    ])
    def test_the_action_class_is_open_not_enumerated(self, verb):
        """
        Every verb here is one nobody would think to put in a cue list, which is
        the point: the detector must not have a cue list to leave them out of.
        """
        assert voicelint._named_person(f"Devon Ashworth {verb} the whole thing.") is True

    def test_the_copula_is_the_closed_class_that_does_the_excluding(self):
        """
        "X is the Y" names a thing. "X is <anything else>" introduces a person.
        This is the one distinction a closed class can carry, because copulas
        are enumerable and action verbs are not.
        """
        assert voicelint._named_person("Cascade Rowing is the older club.") is False
        assert voicelint._named_person("Marcus Webb is a strength coach.") is True
        assert voicelint._named_person("Ruben Castellanos is behind the bar.") is True
        assert voicelint._named_person("Carmen Ruiz is standing in her kitchen.") is True

    def test_a_missed_person_costs_the_full_gate(self):
        """Why the misses mattered: each one is a 20-point swing."""
        seen = "Priya Raman cooks the same thing every Sunday in her kitchen."
        unseen = "Priya Raman: the same thing every Sunday in her kitchen."
        assert voicelint._named_person(seen) is True
        assert voicelint._named_person(unseen) is False
        assert (voice_affinity(seen)["people"] - voice_affinity(unseen)["people"]
                >= 2 * cfg.REGISTER_GATE)

    def test_the_place_list_holds_no_proper_nouns(self):
        """
        Finding 6. This module's list answers "does this bigram name a KIND of
        place or organisation?", so it holds category nouns only. Proper names
        are excluded as whole bigrams instead, which keeps Madison, Jefferson,
        Cascade and Thomas usable as surnames. prohiblint's gazetteer answers a
        different question at a different grain and is allowed to disagree.
        """
        surnames_that_are_also_seattle_places = [
            "Cascade", "Madison", "Jefferson", "Thomas", "Denny", "Harrison",
            "Sunset", "Rainier", "Columbia", "Seward", "Pike", "Yale",
        ]
        for token in surnames_that_are_also_seattle_places:
            assert token not in voicelint._PLACE_TOKENS, token
            assert voicelint._named_person(f"{token} Okonkwo carries the cones out.") is True

    def test_the_one_known_residual_miss_is_recorded_not_hidden(self):
        """
        A surname that IS a place category noun, with an ordinary action verb
        and no person-only cue, is still missed. "Daniel Park cooked for thirty
        people" reads exactly like "Green Lake Trail runs three miles" to a
        bigram detector, and the category-noun filter cannot tell them apart.

        The cost is bounded: any person-only cue rescues it, and real profile
        copy supplies one within the opening window. "Daniel Park, 45, a chef"
        is detected. This is the trade the filter buys, and it is written down
        so that a future change either keeps it or fixes it on purpose.
        """
        assert voicelint._named_person("Daniel Park cooked for thirty people.") is False
        assert voicelint._named_person("Daniel Park, 45, a chef, cooked.") is True
        assert voicelint._named_person("Daniel Park, who cooked, arrived late.") is True
        assert voicelint._named_person("Daniel Park says the kitchen is small.") is True

    def test_multi_word_place_names_are_excluded_as_whole_bigrams(self):
        assert "Queen Anne" in voicelint._PLACE_BIGRAMS
        assert voicelint._named_person("Queen Anne is steeper than it looks.") is False
        # ... and the tokens stay available for people
        assert voicelint._named_person("Anne Sorenson carries the cones out.") is True


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 4 — the athletic gate is not a licence to shout
# ═══════════════════════════════════════════════════════════════════════════════

class TestAthleticGateIsAConjunction:

    SHOUTY_CULTURE = (
        "At Rainier the crew has never trained like this before! Renata Boyle "
        "says the block is the hardest thing the club has ever run! Attendance "
        "is up 40% since January! The waitlist has never been longer! Nobody "
        "who started in the autumn has quit! This is the best winter the "
        "programme has ever had!"
    )

    def test_one_attributed_quote_does_not_buy_six_exclamation_points(self):
        """
        Moving attribution from a +2-per-hit marker to a flat +REGISTER_GATE
        gave attribution-light copy about 8 points of headroom for hype: this
        section scored 64/FAIL on the pre-repair scale and 92/PASS after. Under
        the magazine ruleset nothing but VoiceLint checks exclamation points.
        """
        assert self.SHOUTY_CULTURE.count("!") == 6
        r = lint_one("Culture", self.SHOUTY_CULTURE)
        assert r["passed"] is False
        assert any("shouting" in f for f in r["contamination_flags"])

    def test_the_gate_fails_even_though_the_copy_is_attributed(self):
        assert re.search(cfg.ATHLETIC_ATTRIBUTION, self.SHOUTY_CULTURE)
        assert voice_affinity(self.SHOUTY_CULTURE)["athletic"] < -cfg.REGISTER_GATE

    def test_one_exclamation_point_is_allowed(self):
        """A quoted subject may raise their voice; the writer may not."""
        quoted = 'Renata Boyle says the block worked. "We were wrong!" she says.'
        assert quoted.count("!") == cfg.ATHLETIC_EXCLAMATION_ALLOWANCE
        assert voice_affinity(quoted)["athletic"] > 0

    def test_the_second_exclamation_point_costs_the_gate(self):
        one = 'Renata Boyle says the block worked. "We were wrong!" she says.'
        two = 'Renata Boyle says the block worked! "We were wrong!" she says.'
        drop = voice_affinity(one)["athletic"] - voice_affinity(two)["athletic"]
        # the gate flips (2 * REGISTER_GATE) and the extra mark is also a marker
        assert drop == 2 * cfg.REGISTER_GATE - cfg.NEGATIVE_HIT


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 5 — contamination is allowed to fail a section, on purpose
# ═══════════════════════════════════════════════════════════════════════════════

class TestGateToMarkerWeighting:
    """
    STRUCTURAL FINDING, recorded with numbers rather than fixed.

    Gate 2's reading: the +/-10 section-level gate is worth 5 marker hits at 100
    words and 60 at 1200, a 12x swing across the legal range, so "at the long end
    contamination is decided almost entirely by which gates passed and at the
    short end by lexical evidence", and one constant cannot mean the same
    editorial thing at both ends.

    The arithmetic is right. The consequence, measured, is not the one stated,
    and the thing it points at is a different and worse problem. Both are pinned
    below so the next person argues with numbers.
    """

    def test_the_twelve_times_exchange_rate_is_real(self):
        """One gate, expressed in MARKER HITS, across the legal length range."""
        def hits_per_gate(words):
            per_hit = cfg.POSITIVE_HIT * cfg.DENSITY_BASELINE_WORDS / max(
                words, cfg.DENSITY_BASELINE_WORDS)
            return cfg.REGISTER_GATE / per_hit

        assert hits_per_gate(100) == 5
        assert hits_per_gate(1200) == 60
        assert hits_per_gate(1200) / hits_per_gate(100) == 12

    def test_but_in_DENSITY_the_exchange_rate_does_not_move_at_all(self):
        """
        The margin is thresholded in density, not in marker hits, and in density
        a gate is worth exactly REGISTER_GATE at every length. The 12x is the
        definition of a rate — a marker hit is a smaller share of a longer
        section — and it is what the two-channel split exists to produce. It is
        not, on its own, evidence that one constant cannot work at both ends.
        """
        # at or above DENSITY_BASELINE_WORDS: below it the per-occurrence channel
        # is deliberately not scaled up, so invariance starts at the baseline
        short = "The crew waited, the coach says. " + " ".join(["padding"] * 110)
        long_ = _grow(short, 1200)
        assert len(short.split()) >= cfg.DENSITY_BASELINE_WORDS
        for text in (short, long_):
            aff = voicelint.AFFINITY_SCORERS["athletic"](text)
            assert aff.section_level == cfg.REGISTER_GATE
        # duplication invariance: the density is identical at both lengths
        assert (voice_affinity_density(short)["athletic"]
                == pytest.approx(voice_affinity_density(long_)["athletic"]))

    def test_gates_do_not_in_fact_dominate_at_the_long_end(self):
        """
        Measured over all 73 texts in this file: the gate channel's share of the
        absolute margin averages 36% below 200 words, 53% at 200-600 and 54%
        above 600. It rises with length, as the arithmetic predicts, but "almost
        entirely" overstates it — the spread above 600 words runs 14% to 94% and
        the median case is close to an even split.
        """
        def gate_share(section, text, written_in=None):
            req = required_voice(section)
            affs = {n: f(text) for n, f in voicelint.AFFINITY_SCORERS.items()}
            scale = cfg.DENSITY_BASELINE_WORDS / max(len(text.split()),
                                                     cfg.DENSITY_BASELINE_WORDS)
            other = written_in or max(
                (n for n in affs if n != req),
                key=lambda n: (affs[n].section_level - affs[req].section_level
                               + (affs[n].per_occurrence - affs[req].per_occurrence) * scale))
            sec = affs[other].section_level - affs[req].section_level
            lex = (affs[other].per_occurrence - affs[req].per_occurrence) * scale
            total = abs(sec) + abs(lex)
            return abs(sec) / total if total else 0.0

        long_shares = []
        short_shares = []
        for section, text in (CALIBRATION_IN_REGISTER + VALIDATION_IN_REGISTER
                              + GATE2_IN_REGISTER):
            (long_shares if len(text.split()) > 600 else short_shares).append(
                gate_share(section, text))
        for section, written_in, text in (CALIBRATION_CROSS_REGISTER
                                          + VALIDATION_CROSS_REGISTER
                                          + GATE2_CROSS_REGISTER):
            (long_shares if len(text.split()) > 600 else short_shares).append(
                gate_share(section, text, written_in))

        mean_long = sum(long_shares) / len(long_shares)
        assert 0.45 <= mean_long <= 0.65, f"gate share above 600 words is {mean_long:.0%}"
        assert min(long_shares) < 0.25, "some long sections are decided by lexis alone"
        assert mean_long > sum(short_shares) / len(short_shares), (
            "the gate share should still rise with length")

    def test_the_real_problem_is_a_booleans_leverage_not_the_ratio(self):
        """
        What IS wrong: a gate is decided by ONE occurrence anywhere in the
        section and is worth +/-REGISTER_GATE of density however long the section
        is. So a single phrase in 1200 words can outweigh the entire lexical
        channel, and both of the defects this module has shipped were exactly
        that — a 1135-word newsletter that took the athletic gate on one
        reporting verb, and a reported feature that handed the people register
        its gate on one access marker.

        The repair reduces the exposure on the athletic side rather than removing
        it: the gate's own evidence is now counted per occurrence too, so
        attributing once and attributing ten times are no longer the same score.
        A section cannot buy the whole gate with one phrase and then stop.
        """
        once = ("The crew waited, the coach says. " + " ".join(["padding"] * 300))
        often = once
        for source in ("Nakashima noted the delay.", "Obradovic said the same.",
                       "According to the club, it was scheduled.",
                       "The trustee declined to comment."):
            often += " " + source

        a_once = voicelint.AFFINITY_SCORERS["athletic"](once)
        a_often = voicelint.AFFINITY_SCORERS["athletic"](often)
        assert a_once.section_level == a_often.section_level == cfg.REGISTER_GATE
        assert a_often.per_occurrence > a_once.per_occurrence, (
            "attributing continuously must score above attributing once")
        assert a_often.per_occurrence - a_once.per_occurrence >= 4 * cfg.POSITIVE_HIT


class TestContaminationBlocks:

    def test_one_flag_fails_even_an_otherwise_perfect_section(self):
        """
        The decision. One flag used to cost 10 against a 15-point budget, so a
        section strong in its own register absorbed it and passed, and the
        orchestrator routes a PASSING section's flags to advisory. A Training
        section written as a pure People profile scored 90 and shipped.
        """
        assert (cfg.SCORE_START - cfg.CROSS_CONTAMINATION_PENALTY
                < cfg.PASS_THRESHOLD), "a contaminated section can still pass"

    def test_the_penalty_is_denominated_in_the_scales_own_unit(self):
        """One contamination flag costs one more than the whole budget."""
        assert cfg.CROSS_CONTAMINATION_PENALTY == (
            (cfg.NEGATIVE_MARKER_BUDGET + 1) * -cfg.NEGATIVE_HIT) == 18

    def test_the_reported_case_now_fails(self):
        """A Training section written as a pure people profile, margin +14, scored 90."""
        r = lint_one("Training", _grow(CONTAMINATION_ATHLETIC_AS_PEOPLE, 850))
        assert cross_flags(r)
        assert r["passed"] is False

    @pytest.mark.parametrize("section,written_in,text",
                             CALIBRATION_CROSS_REGISTER + VALIDATION_CROSS_REGISTER)
    def test_no_contaminated_section_passes(self, section, written_in, text):
        assert lint_one(section, text)["passed"] is False

    def test_passed_is_still_exactly_the_threshold_test(self):
        """
        No second pass/fail rule was added. The penalty simply exceeds the
        budget, so `passed` stays `score >= PASS_THRESHOLD` and the
        orchestrator moves the flags from advisory to blocking on its own.
        """
        src = open(voicelint.__file__, encoding="utf-8").read()
        assert len(re.findall(r'^\s+passed\s*=', src, re.M)) == 1
        assert "passed = final_score >= PASS_THRESHOLD" in src
        for section, _, text in VALIDATION_CROSS_REGISTER:
            r = lint_one(section, text)
            assert r["passed"] == (r["voice_score"] >= cfg.PASS_THRESHOLD)


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 3 — attribution STYLE must not decide a verdict
#
# A reported feature that de-duplicates its source's name ("Nair says" once,
# then "she says") was scored as though nothing in it were attributed at all.
# Pronoun-versus-name is a COREFERENCE artifact, not a register signal.
#
# The hard part is that a PROFILE also names its subject in the opening 50 words
# and also then writes "she says", so the presence of a name cannot license the
# credit. What licenses it is REPORTING_MACHINERY — whether the section records
# the act of ASKING somebody. See _reported_by_pronoun and THE RESIDUAL HOLE.
# ═══════════════════════════════════════════════════════════════════════════════

# The reviewer's D1: a 368-word reported Culture feature. Verbatim.
G3_D1_CULTURE_FEATURE = """
The Tuesday lifting group at Harbour Steel has met at five in the morning for
nineteen years, and for the last four of them it has met without a coach.

Ines Delacroix ran the hour from 2006 until her stroke in the spring of 2021.
The room did not close and did not appoint a replacement. It simply kept
meeting, and the people who had been there longest began writing the session on
the whiteboard the night before.

"We thought it would last a month," says Peter Anand, who has trained there
since 2009. "It has lasted four years and nobody has ever put their name on it."

His mornings begin at four. His wife works nights and they overlap for twenty
minutes in the kitchen, which he describes as the best part of his day and the
reason he has never moved to an evening slot.

The whiteboard is the whole system. Whoever arrives first writes the work.
Whoever arrives last sweeps. There is no roster, no membership fee beyond the
building's own, and no record of who has been coming for how long.

Delacroix still visits on the first Tuesday of the month. She uses a stick now
and does not lift, and the group has never once asked her to write the session.

"They stopped needing me and they were kind enough not to say so," she says.
"That is what you want. That is the whole job."

Her daughter drives her in. Her old training log sits in a drawer behind the
front desk and three separate people have asked to photograph it.

Building management has raised the room's rate twice since 2021, according to
correspondence shared with reviewers, and has twice been talked back down by a
letter the group writes collectively and nobody signs.

A representative for the management company declined to discuss the terms of an
active tenancy. Anand says the group expects the question to come back.

Attendance has grown from eleven to more than thirty. The equipment has not
changed. A rowing machine donated in 2014 is still the only cardio in the room,
and it is still broken in the same way it was broken when it arrived.
""".strip()

# D1 with ONE editorial change and no other: each source is introduced by name,
# and every later attribution to that source is a pronoun. Standard
# de-duplication, and better prose. Under the previous build this cost 3.26
# points of margin for nothing.
G3_D1_PRONOUN_ATTRIBUTED = """
The Tuesday lifting group at Harbour Steel has met at five in the morning for
nineteen years, and for the last four of them it has met without a coach.

Ines Delacroix ran the hour from 2006 until her stroke in the spring of 2021.
The room did not close and did not appoint a replacement. It simply kept
meeting, and the people who had been there longest began writing the session on
the whiteboard the night before.

Peter Anand has trained there since 2009. "We thought it would last a month," he
says. "It has lasted four years and nobody has ever put their name on it."

His mornings begin at four. His wife works nights and they overlap for twenty
minutes in the kitchen, which he describes as the best part of his day and the
reason he has never moved to an evening slot.

The whiteboard is the whole system. Whoever arrives first writes the work.
Whoever arrives last sweeps. There is no roster, no membership fee beyond the
building's own, and no record of who has been coming for how long.

Delacroix still visits on the first Tuesday of the month. She uses a stick now
and does not lift, and the group has never once asked her to write the session.

"They stopped needing me and they were kind enough not to say so," she says.
"That is what you want. That is the whole job."

Her daughter drives her in. Her old training log sits in a drawer behind the
front desk and three separate people have asked to photograph it.

Building management has raised the room's rate twice since 2021, according to
correspondence shared with reviewers, and has twice been talked back down by a
letter the group writes collectively and nobody signs.

A representative for the management company declined to discuss the terms of an
active tenancy. He says the group expects the question to come back.

Attendance has grown from eleven to more than thirty. The equipment has not
changed. A rowing machine donated in 2014 is still the only cardio in the room,
and it is still broken in the same way it was broken when it arrived.
""".strip()

# The reviewer's D3: a QUIET PROFILE that quotes NAMED THIRD PARTIES, in a
# people slot. Handbook Sec 5.2's reference shape. It must stay clean AND it
# must not collect athletic sourcing from its own "she says" — it carries no
# machinery of asking, so the licence never opens.
G3_D3_QUIET_SOURCED_PROFILE = """
Wren Halloway eats the same four dinners on a four-day rotation and has done
since the autumn of 2019.

She is 51, a ferry engineer, and she came to it the way most people come to
anything, which is badly and by accident. Her cholesterol came back high in a
routine screening and she decided, without telling anybody, to stop deciding
what to eat.

"She did not ask my opinion," says Dr Meredith Osei, the GP who ordered the
screening. "She came back nine months later with a spreadsheet."

The spreadsheet is still on her phone. Four dinners, four shopping lists, one
Sunday afternoon. Her kitchen is small and her freezer is mostly labelled boxes
in her own handwriting.

Her wife finds the rotation restful and says the arguing about food that ran
through their first decade together simply stopped.

"I used to dread six o'clock," says Fenella Ruiz, her wife of twenty-two years.
"Now it is the least interesting part of the evening. That is a gift."

Her numbers came down and stayed down. Osei notes that the effect held through
two winters and a bereavement, which she says is the part that impresses her,
because that is where most of these things come apart.

Her son thinks it is joyless. He says so at every visit and she lets him.

"He is twenty-four," she says. "He is supposed to think that."

She has never named the four dinners publicly and does not intend to. She says
the specific food is not the thing that worked and that anyone who copies the
menu instead of the rotation has misunderstood it.

Her mornings are the same. Coffee, the same bowl, the ferry at ten past six.
Her hands are her mother's hands and she notices it most in the galley.

Osei has since put two other patients onto the same idea and neither has stuck
with it. She says she is careful now about how she describes it.
""".strip()

# The reviewer's E1 and E2: quiet PROFILES submitted as Culture and Nightlife.
# Both must still fail as cross-register.
G3_E1_CULTURE_AS_QUIET_PROFILE = """
Solveig Ranta keeps her chalk in a tobacco tin that belonged to her father and
has never used any other container for it.

She is 44, a piano tuner, and she has trained in the same corner of the same
room for sixteen years without ever entering a competition or posting a lift.

Her mornings are quiet. She arrives before the desk is staffed, works through
five movements in the same order, and is gone before most of the room knows she
was there.

"I like the hour," she says. "I do not like being watched."

Her hands are the part she thinks about. Tuning is fine work and lifting is not,
and she has spent sixteen years negotiating between the two without ever quite
resolving it.

Her husband does not train. Her sons trained briefly and stopped. She keeps a
photograph of her father's tin on the wall of her workshop and has never
explained it to a client.

The tin is nearly empty now. She has not looked for a replacement and says she
will deal with it when it happens.

Her evenings belong to the workshop. Her Sundays belong to nobody, which she
describes as the only luxury she has ever wanted and the only one she has.
""".strip()

G3_E2_NIGHTLIFE_AS_QUIET_PROFILE = """
Bo Ferreira works the door on Wednesdays and has never turned anyone away for
what they were wearing.

He is 57, a retired postman, and he took the shift because his knees stopped him
doing anything that required standing still, which he says is a joke the job has
never stopped making.

His stool is by the radiator. His flask is on the ledge. He knows the regulars
by their coats rather than their faces and has said so to several of them.

"I am not security," he says. "I am a man on a stool who knows everybody."

His wife collects him at one. His grandson has started coming on Wednesdays,
which Bo has decided not to have an opinion about in public.

The room behind him has changed hands twice and neither owner has moved him.
His stool has been reupholstered once.

His mornings are his own. He sleeps until ten and walks the same route he
walked for thirty-one years with a bag on his shoulder.
""".strip()

# The reviewer's D2: a single-source reported feature with NO machinery of
# asking anywhere in it. THE RESIDUAL HOLE. It is a false positive and it stays
# one; see the limitation test below for why that is recorded, not fixed.
G3_D2_NO_MACHINERY = """
Kwame Boateng tore the hamstring in the second race of the outdoor season and
did not run again for fourteen months.

The injury itself was ordinary. What was not ordinary was the decision that
followed it, which was to stop sprinting entirely for a year and rebuild the leg
from positions he had never trained in his life.

"Everyone told me to come back at eighty percent and build," he says. "I had
already done that twice. Twice it went again."

His mornings that winter were forty minutes of unloaded work on a mat in his
own front room, because the clinic was an hour away and he could not afford the
travel four times a week.

He filmed every session on a phone propped against a chair. He kept the files.
There are two hundred and forty of them and he has not deleted any.

His mother thought he had retired and did not ask. His brother, who had watched
both previous returns fail, told him plainly that he thought the third one would
fail as well.

The leg came back slowly and then all at once. He ran a personal best in the
spring, at twenty-nine, on a hamstring that had been rebuilt from the floor of
a rented flat with no supervision and no equipment beyond a resistance band.

"I am not telling anyone to do it this way," he says. "I am saying it is what
was available."

He has since been asked to speak to two university squads about the protocol
and has declined both, on the grounds that there is no protocol and he does not
want to be responsible for someone copying a thing that was mostly desperation.

His coach at the time has since left the sport. The band is in a drawer. He has
not needed it in three seasons and has not thrown it away.
""".strip()


class TestAttributionStyleDoesNotDecideTheVerdict:
    """The blocker: de-duplicating a source's name must not flip a section."""

    def test_d1_passes_as_written(self):
        r = lint_one("Culture", G3_D1_CULTURE_FEATURE)
        assert r["voice_score"] == 100
        assert r["passed"] is True
        assert cross_flags(r) == []

    def test_d1_still_passes_when_attributions_are_de_duplicated(self):
        """
        The ONLY difference between these two texts is that the second one uses
        a pronoun where the first repeats a surname. Same story, same subject,
        same facts, same human colour. Under the previous build the edit cost
        3.26 points of margin; it must now cost the section nothing.
        """
        r = lint_one("Culture", G3_D1_PRONOUN_ATTRIBUTED)
        assert r["voice_score"] == 100
        assert r["passed"] is True
        assert cross_flags(r) == []

    def test_de_duplicating_names_barely_moves_the_section_toward_people(self):
        """
        3.26 points before, 0.54 after. NOT zero, and the remainder is not a
        defect: `"...," he says` is a tagged quote and PEOPLE_ACCESS counts a
        tagged quote as access, which it is — a report that quotes its subject
        directly does hand the reader that subject's voice. Driving this to zero
        would mean deleting one of the people register's defining markers to
        flatter a report. The number is recorded so it cannot creep back up.
        """
        as_written = worst_other_margin("Culture", G3_D1_CULTURE_FEATURE)
        dedup = worst_other_margin("Culture", G3_D1_PRONOUN_ATTRIBUTED)
        drift = dedup - as_written
        assert drift == pytest.approx(0.54, abs=0.02), (
            f"attribution style moved the margin by {drift:+.2f}, recorded at "
            f"+0.54 (it was +3.26 before PRONOUN_ATTRIBUTION)")
        one_marker = cfg.POSITIVE_HIT * 100 / voicelint._word_count(G3_D1_CULTURE_FEATURE)
        assert drift == pytest.approx(one_marker), (
            "the whole remainder is the tagged quote's single PEOPLE_ACCESS hit "
            "— exactly one marker at this length, and nothing else")

    def test_the_gate_does_not_call_a_de_duplicated_report_unattributed(self):
        """
        The gate's own words were "nothing in the section is attributed", said
        about a feature that attributes in every other paragraph.
        """
        _, flags = score_athletic(G3_D1_PRONOUN_ATTRIBUTED)
        assert not any("No sourced attribution" in f for f in flags)


class TestTheLicenceIsMachineryNotName:
    """
    What separates a report that quotes its named subject from a profile that
    quotes its named subject. Not the name — both have one.
    """

    def test_a_profile_gains_nothing_from_its_own_pronoun_attributions(self):
        """
        D3 quotes named third parties and quotes ITSELF by pronoun. It carries
        no machinery of asking, so the licence never opens and its margin is
        bit-for-bit what it was before PRONOUN_ATTRIBUTION existed.
        """
        assert voicelint._reported_by_pronoun(G3_D3_QUIET_SOURCED_PROFILE) == 0
        r = lint_one("Nutrition", G3_D3_QUIET_SOURCED_PROFILE)
        assert r["passed"] is True
        assert cross_flags(r) == []
        assert worst_other_margin("Nutrition", G3_D3_QUIET_SOURCED_PROFILE) == pytest.approx(
            -14.77, abs=0.01)

    @pytest.mark.parametrize("section,text,margin", [
        ("Culture", G3_E1_CULTURE_AS_QUIET_PROFILE, 45.49),
        ("Nightlife", G3_E2_NIGHTLIFE_AS_QUIET_PROFILE, 33.73),
    ])
    def test_quiet_profiles_in_the_wrong_slot_still_fail(self, section, text, margin):
        assert voicelint._reported_by_pronoun(text) == 0
        r = lint_one(section, text)
        assert r["passed"] is False
        assert cross_flags(r)
        assert worst_other_margin(section, text) == pytest.approx(margin, abs=0.01)

    def test_a_name_alone_does_not_license_the_credit(self):
        """
        The forbidden licence, pinned so it cannot be reintroduced by accident.
        Every one of these texts anchors a named person in its opening window —
        that is the people gate's own test — and not one of them may earn a
        pronoun-attribution credit on that basis.
        """
        for text in (G3_E1_CULTURE_AS_QUIET_PROFILE, G3_E2_NIGHTLIFE_AS_QUIET_PROFILE,
                     G3_D3_QUIET_SOURCED_PROFILE, LONG_X_CULTURE_AS_A_QUIET_PROFILE):
            window = ' '.join(text.split()[:voicelint.PERSON_WINDOW_WORDS])
            assert voicelint._named_person(window), "precondition: a name is present"
            assert voicelint._reported_by_pronoun(text) == 0

    def test_both_halves_of_the_licence_are_necessary(self):
        machinery = "A representative for the club declined to comment. "
        named = "Dee Nakashima runs the room. "
        pronoun = 'She says the lease expires in March.'
        assert voicelint._reported_by_pronoun(named + pronoun) == 0, "machinery missing"
        assert voicelint._reported_by_pronoun(machinery + pronoun) == 0, "no named anchor"
        assert voicelint._reported_by_pronoun(named + machinery + pronoun) == 1

    def test_did_not_return_needs_its_object(self):
        """
        `did not return to normal hours` is the intransitive "go back to", not a
        source declining to comment. It was scoring as a non-response frame,
        which handed a wrong-register PROFILE a point of athletic sourcing and,
        once REPORTING_MACHINERY existed, the pronoun licence as well.
        """
        assert re.search(cfg.ATHLETIC_NON_RESPONSE, "did not return a call")
        assert re.search(cfg.ATHLETIC_NON_RESPONSE, "has not returned our messages")
        assert not re.search(cfg.ATHLETIC_NON_RESPONSE,
                             "did not return to normal hours until the spring")
        # the other non-response verbs are unambiguous and keep their bare form
        assert re.search(cfg.ATHLETIC_NON_RESPONSE, "did not respond")
        assert re.search(cfg.ATHLETIC_NON_RESPONSE, "has not replied")


class TestTheResidualHoleIsRecordedNotRounded:
    """
    A reported feature that records NO asking is not separable from a profile,
    and this suite says so out loud rather than letting the limitation rot.
    """

    def test_a_report_with_no_machinery_is_still_a_false_positive(self):
        """
        D2. If this ever starts passing, something has widened the licence and
        THE RESIDUAL HOLE in voice_config needs re-measuring — check what it
        cost the cross-register half before celebrating.
        """
        assert voicelint._reported_by_pronoun(G3_D2_NO_MACHINERY) == 0
        r = lint_one("Training", G3_D2_NO_MACHINERY)
        assert r["passed"] is False, (
            "D2 passing means the licence widened; re-measure the cross-register "
            "half before accepting it")

    def test_d2_and_e1_are_indistinguishable_on_every_axis_the_module_has(self):
        """
        The evidence for the limitation. A report with no machinery and a
        profile in the wrong slot agree on every athletic-side measurement; the
        only thing that differs is how much human colour each carries, which is
        not a register signal — an in-register profile (D4-shaped) sits on top
        of the report.
        """
        athletic = voicelint.AFFINITY_SCORERS["athletic"]
        d2 = athletic(G3_D2_NO_MACHINERY)
        e1 = athletic(G3_E1_CULTURE_AS_QUIET_PROFILE)
        assert d2.section_level == e1.section_level == -8
        assert d2.per_occurrence == e1.per_occurrence == 0
        for text in (G3_D2_NO_MACHINERY, G3_E1_CULTURE_AS_QUIET_PROFILE):
            assert not re.search(cfg.ATHLETIC_ATTRIBUTION, text), "no named attribution"
            assert not any(re.search(p, text) for p in cfg.REPORTING_MACHINERY)
            assert voicelint._reported_by_pronoun(text) == 0

    def test_the_module_errs_toward_blocking_rather_than_missing(self):
        """
        The trade is deliberate and is stated in voice_config: a blocked section
        reaches a human, a missed one ships as the magazine's voice. So the
        unseparable shape lands on the FALSE POSITIVE side, and every profile in
        the wrong slot still fails.
        """
        assert lint_one("Training", G3_D2_NO_MACHINERY)["passed"] is False
        for section, text in (("Culture", G3_E1_CULTURE_AS_QUIET_PROFILE),
                              ("Nightlife", G3_E2_NIGHTLIFE_AS_QUIET_PROFILE)):
            assert lint_one(section, text)["passed"] is False

    def test_the_cost_of_the_licence_on_the_weakest_cross_register_text(self):
        """
        Measured, not rounded off. The 852-word surname-tagged quiet profile is
        the weakest cross-register text in the derivation corpus, and it is the
        one the licence costs the most. It must still fire, and the headroom is
        recorded so a future change cannot spend it silently.
        """
        margin = intended_margin("Culture", LONG_X_CULTURE_AS_A_QUIET_PROFILE, "people")
        assert margin >= cfg.CROSS_CONTAMINATION_MARGIN, "it must still fire"
        assert margin == pytest.approx(7.15, abs=0.01), (
            "recorded at +7.15 with 2.15 points of headroom above the margin")


# D1 de-duplicated all the way down: not one non-pronoun attribution anywhere,
# so ATHLETIC_ATTRIBUTION does not match and the athletic GATE has nothing to
# stand on except the licensed pronouns. What is left is one non-response frame
# — "declined to discuss" — which is the whole licence. Under the previous build
# this scored +27.22 and 58/FAIL: a properly reported feature told that nothing
# in it was attributed. It is the text that makes the gate half of the rule
# load-bearing, and the mutation suite uses it as such.
G3_D1_DEDUPLICATED_TO_THE_FLOOR = """
The Tuesday lifting group at Harbour Steel has met at five in the morning for
nineteen years, and for the last four of them it has met without a coach.

Ines Delacroix ran the hour from 2006 until her stroke in the spring of 2021.
The room did not close and did not appoint a replacement. It simply kept
meeting, and the people who had been there longest began writing the session on
the whiteboard the night before.

Peter Anand has trained there since 2009. "We thought it would last a month," he
says. "It has lasted four years and nobody has ever put their name on it."

His mornings begin at four. His wife works nights and they overlap for twenty
minutes in the kitchen, which he describes as the best part of his day and the
reason he has never moved to an evening slot.

The whiteboard is the whole system. Whoever arrives first writes the work.
Whoever arrives last sweeps. There is no roster, no membership fee beyond the
building's own, and no record of who has been coming for how long.

Delacroix still visits on the first Tuesday of the month. She uses a stick now
and does not lift, and the group has never once asked her to write the session.

"They stopped needing me and they were kind enough not to say so," she says.
"That is what you want. That is the whole job."

Her daughter drives her in. Her old training log sits in a drawer behind the
front desk and three separate people have asked to photograph it.

Building management has raised the room's rate twice since 2021, he says, and
has twice been talked back down by a letter the group signs collectively.

The management company declined to discuss the terms of an active tenancy. He
says the group expects the question to come back.

Attendance has grown from eleven to more than thirty. The equipment has not
changed. A rowing machine donated in 2014 is still the only cardio in the room,
and it is still broken in the same way it was broken when it arrived.
""".strip()


class TestTheGateAcceptsALicensedPronoun:
    """
    The gate half of the rule, pinned on the text where it is the only thing
    holding the section up. Found by mutation: removing `or pron_src > 0` from
    the gate survived the whole suite, because every other fixture also carries
    a non-pronoun attribution.
    """

    def test_precondition_there_is_no_non_pronoun_attribution_at_all(self):
        assert not re.search(cfg.ATHLETIC_ATTRIBUTION, G3_D1_DEDUPLICATED_TO_THE_FLOOR)
        assert voicelint._reported_by_pronoun(G3_D1_DEDUPLICATED_TO_THE_FLOOR) == 4

    def test_the_fully_de_duplicated_report_passes(self):
        r = lint_one("Culture", G3_D1_DEDUPLICATED_TO_THE_FLOOR)
        assert r["voice_score"] == 100
        assert r["passed"] is True
        assert cross_flags(r) == []

    def test_the_gate_is_satisfied_and_says_so(self):
        aff = voicelint.AFFINITY_SCORERS["athletic"](G3_D1_DEDUPLICATED_TO_THE_FLOOR)
        assert aff.section_level > 0, "the gate must be passed, not failed"
        assert not any("No sourced attribution" in f for f in aff.flags)

    def test_a_profile_with_the_same_pronouns_still_fails_the_gate(self):
        """The gate loosening must not reach a section with no machinery."""
        for text in (G3_E1_CULTURE_AS_QUIET_PROFILE, G3_E2_NIGHTLIFE_AS_QUIET_PROFILE):
            aff = voicelint.AFFINITY_SCORERS["athletic"](text)
            assert aff.section_level < 0, "a profile must still fail the athletic gate"


class TestEveryLicenceComponentIsLoadBearing:
    """
    Found by mutation: deleting individual REPORTING_MACHINERY families, and
    `they` from the pronoun pattern, survived the suite. Each piece is now
    exercised on a minimal text so it cannot be deleted quietly.
    """

    NAMED = "Dee Nakashima has run the room since 2019. "
    PRONOUN = "She says the lease expires in March."

    @pytest.mark.parametrize("machinery", [
        "A representative for the landlord declined to comment. ",   # non-response
        "The owner did not respond to two requests for comment. ",   # non-response
        "A spokesperson confirmed the filing. ",                     # provenance
        "Court records show the unit was listed in April. ",         # provenance
        "In an interview, the position was set out at length. ",     # provenance
        "The rent was reportedly raised twice. ",                    # reported hedge
        "According to the council, the permit lapsed. ",             # according to
    ])
    def test_each_machinery_family_licenses_on_its_own(self, machinery):
        assert voicelint._reported_by_pronoun(self.NAMED + machinery + self.PRONOUN) == 1
        assert voicelint._reported_by_pronoun(self.NAMED + self.PRONOUN) == 0

    @pytest.mark.parametrize("pronoun,verb", [
        ("She", "says"), ("he", "said"), ("They", "told"),
        ("she", "added"), ("He", "wrote"), ("they", "acknowledged"),
    ])
    def test_the_pronoun_pattern_covers_she_he_and_they(self, pronoun, verb):
        machinery = "A representative for the landlord declined to comment. "
        text = f"{self.NAMED}{machinery}{pronoun} {verb} the lease expires in March."
        assert voicelint._reported_by_pronoun(text) == 1

    def test_the_named_anchor_is_read_from_the_opening_window(self):
        """
        The anchor uses the same opening window as the people gate, on purpose
        and conservatively: a name that turns up only in the last paragraph is
        not what a de-duplicated attribution at the top refers back to. Widening
        this to the whole text changes no corpus verdict, which is exactly why
        it needs a test — an untested choice is one that drifts.
        """
        machinery = "A representative for the landlord declined to comment. "
        filler = "The room opened at four and the heating ran on a timer. " * 12
        late = machinery + filler + "Dee Nakashima has run it since 2019. She says so."
        assert voicelint._named_person(late), "precondition: the name is in the text"
        assert voicelint._reported_by_pronoun(late) == 0, (
            "a name outside the opening window must not license the credit")
