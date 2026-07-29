# -*- coding: utf-8 -*-
"""
synth_config.py — SynthLint's lexicons, patterns, thresholds, and the written
record of how every threshold was derived.

WHY THIS FILE EXISTS SEPARATELY
-------------------------------
Every number in SynthLint is a claim about two corpora: that real TIMBR copy
sits on one side of it and genuine AI-generated prose sits on the other. A
number without its derivation is folklore, and folklore is what lets a
threshold drift. Everything here is written down so the next engineer can
re-run the derivation instead of trusting it. test_synthlint.py recomputes the
corpus statistics on every run, so a threshold that stops being true fails the
suite rather than quietly changing what ships.

THE CONSTRAINT THIS MODULE WAS BUILT AROUND
-------------------------------------------
TIMBR's own locked voice uses devices that generic LLM prose also overuses.
PRINCIPLES.txt Sec. 7 explicitly endorses:

    "Triads and parallelism (your history, your joints, your limits)."
    "Colon-led micro-lists for instructions."
    "Short declaratives. Fragments allowed for punch."

A check that fires on the PRESENCE of one of those devices is not an AI
detector, it is a rejection of the house voice. The differentiator is almost
always DENSITY or RATE, never presence — and where a rate could not be found
that clears real copy while still catching slop, the check was DROPPED rather
than shipped loose. See DROPPED_CHECKS at the bottom of this file.

THE CORPORA
-----------
DERIVATION (thresholds were tuned against these):
  * 21 prose slots from runs/vol11_slu/copy.py — real, shipped Seattle Series
    Vol 10 copy (workout line-lists, kickers and titles excluded: not prose).
  * all 7 sections of timbr_eval/sample_issue.json
  * 4 of the 7 sections of timbr_eval/fixtures/magazine_pass.json
  = 29 texts, 114 paragraphs, 400 sentences, 4,792 words of real
    TIMBR-register prose. It carries ZERO hits on all six shipped checks.
  * 12 adversarial texts written to read like LLM fitness/lifestyle copy,
    varying in severity and in WHICH tell they carry.

HELD OUT (never inspected while a threshold was being chosen; the finished
module was run against them cold):
  * magazine_pass Culture / Social / Nightlife
  * vol11 night_body / counter_cafe / anchor_cafe
  * 4 adversarial texts.

Both splits live as literal fixtures in test_synthlint.py.
"""

import re

try:                                    # repo-root pytest: `import synthlint...`
    from prohiblint.prohiblint import AI_BLOCKLIST as _PROHIB_AI_BLOCKLIST
except ImportError:                     # `cd synthlint && pytest`
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "prohiblint"))
    from prohiblint import AI_BLOCKLIST as _PROHIB_AI_BLOCKLIST


# ===========================================================================
# THE SCORING SCALE
# ===========================================================================
# One unit of evidence that a text was machine-written is a TELL. Every check
# reports its findings in whole tells, so penalties from different checks are
# denominated in the same thing and can be compared and summed.
SCORE_START = 100

# TELL is a pure scale factor; only the RATIO of penalties to the budget below
# carries meaning. 8 was chosen over 10 so that PASS_THRESHOLD lands on 84
# rather than 80: a non-round number is harder to hard-code by accident
# somewhere else in the repo, which is the same reasoning behind voicelint's
# PASS_THRESHOLD = 85.
TELL = 8

# ── PASS_THRESHOLD: DERIVED, not chosen ────────────────────────────────────
# The threshold encodes exactly ONE editorial decision: how many tells a text
# may carry and still ship. Measured, not guessed:
#
#   REAL CEILING   the 29-text TIMBR derivation corpus carries ZERO tells.
#                  Not "few" — zero, on every one of the six shipped checks.
#   AI FLOOR       the weakest of the 12 adversarial derivation texts
#                  (adv10_brand_subtle: no banned vocabulary, no transitions,
#                  no contrastive frames, no hedge stacks, no opener runs —
#                  only a flat rhythm at CV 0.274) carries 3 tells.
#
# So the two corpora are separated by the interval [0, 3) and the budget is the
# only free choice inside it. It is set to 2, the largest value that still
# fails every adversarial text:
NOISE_BUDGET = 2
#
# 2 rather than 0 or 1 because every tell in this module is the verdict of a
# regex or a summary statistic, and the specific failure this module must not
# reproduce is a single mechanical pattern match rejecting owner-approved copy
# (the em-dash rule that counted dashes instead of asides). A budget of 2 makes
# corroboration structural: no single tell can fail a text on its own; a FAIL
# always needs a second tell, or the same tell twice.
FAIL_FLOOR_DELTA = NOISE_BUDGET * -TELL          # -16

#: Single source of truth for pass/fail. Import it; do not restate the number.
PASS_THRESHOLD = SCORE_START + FAIL_FLOOR_DELTA  # 84


# ===========================================================================
# CHECK 1 — EXTENDED AI-VOCABULARY BLOCKLIST
# ===========================================================================
# Connector and filler phrases that mark machine prose, covering ground
# prohiblint.AI_BLOCKLIST does not. prohiblint's list is single-word AI-register
# vocabulary (delve, tapestry, robust, leverage, seamless...); this one is
# phrasal scaffolding — the throat-clearing an LLM puts around a claim.
#
# DE-DUPLICATION IS PROGRAMMATIC, NOT BY HAND. Any term that appears in
# prohiblint.AI_BLOCKLIST is filtered out below, so if prohiblint later adds
# one of these the overlap disappears on its own instead of quietly
# double-penalising a section under two linters. As of this writing the
# intersection is empty.
_EXTENDED_AI_VOCAB_RAW = [
    # throat-clearing / hedged assertion frames
    "it's important to note", "it is important to note",
    "it's worth noting", "it is worth noting",
    "needless to say", "without a doubt", "at the end of the day",
    # scene-setting openers
    "in today's fast-paced world", "in the ever-evolving landscape of",
    "when it comes to", "navigate the complexities of", "the world of",
    "let's dive in", "picture this", "imagine a world where",
    # quantity inflation
    "a myriad of", "a plethora of", "a wide array of", "a wide range of",
    # brochure adjectives
    "cutting-edge", "state-of-the-art", "one-stop shop", "unprecedented",
    "groundbreaking", "paradigm shift",
    # consultant verbs
    "circle back", "double down", "low-hanging fruit", "move the needle",
    # inflated attribution verbs
    "boasts", "showcases", "underscores", "testament to",
    "plays a crucial role", "plays a vital role",
    # summary scaffolding
    "in conclusion", "to sum up", "to summarize", "in summary",
    "moreover", "furthermore", "in essence", "essentially", "fundamentally",
]

_PROHIB_LOWER = {t.lower() for t in _PROHIB_AI_BLOCKLIST}

#: The shipped list. Terms already owned by prohiblint are removed here.
EXTENDED_AI_VOCAB = [t for t in _EXTENDED_AI_VOCAB_RAW
                     if t.lower() not in _PROHIB_LOWER]

#: Terms dropped because prohiblint already flags them. Exposed so the test
#: suite can assert the de-duplication actually ran.
VOCAB_CEDED_TO_PROHIBLINT = [t for t in _EXTENDED_AI_VOCAB_RAW
                             if t.lower() in _PROHIB_LOWER]

# NOT on this list, deliberately, each because real TIMBR copy uses it:
#   "additionally", "overall"  — legitimate mid-sentence ("overall volume rose
#       31 percent"). They are tells only in PARAGRAPH-INITIAL position, which
#       is Check 2's job, not a lexical ban.
#   "roughly", "approximately", "about", "around" — measurement words.
#       PRINCIPLES Sec. 8 requires numbers in every body paragraph and these
#       are how a number gets qualified honestly.
#   "may", "might", "could", "seems", "suggests" — single hedges. Already
#       covered by voice_config.FITT_NEGATIVE[0]. Check 4 only takes them in
#       STACKS, which is a different and stronger defect.

VOCAB_PENALTY_TELLS = 1          # per hit
VOCAB_HARD_FAIL_HITS = 5
# 5 = saturation. TIMBR derivation: 0 hits across 29 texts. Adversarial
# derivation hit counts: 14, 9, 9, 7, 3, 2, 1, 0, 0, 0, 0, 0. Any text at 5+ is
# not a piece of prose with a bad phrase in it, it is machine scaffolding.
# (3 hits already scores 76 and FAILS on penalty alone; the hard fail exists so
# a saturated text cannot be redeemed by anything downstream.)


# ===========================================================================
# CHECK 2 — FORMULAIC TRANSITION DENSITY (paragraph-initial)
# ===========================================================================
# PARAGRAPH-INITIAL only. Mid-sentence "moreover" is a word; opening one
# paragraph in three with a connective adverb is a shape — the LLM habit of
# signposting every paragraph as the next item in a list.
FORMULAIC_TRANSITIONS = [
    "moreover", "furthermore", "additionally", "overall",
    "in conclusion", "in summary", "to summarize",
    "it's important to note", "it is important to note",
    "it's worth noting", "it is worth noting", "needless to say",
]

# ── Threshold derivation ───────────────────────────────────────────────────
# TIMBR derivation corpus: 0 paragraph-initial transitions in 114 paragraphs.
# With 0 events in 114 trials the rule of three puts the 95% upper bound on the
# real-copy rate at 3/114 = 0.026. The threshold sits at 0.20 — one paragraph
# in five — which is 7.6x that bound.
FORMULAIC_TRANSITION_RATE_MAX = 0.20

# A rate needs a denominator worth dividing by. Below this a text has no
# paragraph structure to have a rate about, and the check does not apply.
FORMULAIC_TRANSITION_MIN_PARAGRAPHS = 3

# And a rate needs more than one event. A single "Moreover" in a five-paragraph
# piece is presence, not density — and it is ALREADY penalised, once, by Check
# 1, which carries "moreover" as a lexical tell. This check is the surcharge
# for making it the text's default way into a paragraph, so it requires the
# habit to be visible at least twice.
FORMULAIC_TRANSITION_MIN_HITS = 2
#
# The deliberate overlap with Check 1 (moreover / furthermore / in conclusion /
# in summary / to summarize / it's important to note / it is worth noting /
# needless to say appear on both lists) is documented rather than removed:
# Check 1 prices the PHRASE, Check 2 prices the RATE at which paragraphs are
# opened with one. Two defects, two prices. Check 2's penalty is flat-plus-
# graduated rather than per-hit so the two cannot compound without limit.
TRANSITION_DENSITY_BASE_TELLS = 2
TRANSITION_DENSITY_PER_EXTRA_HIT = 1   # per hit past FORMULAIC_TRANSITION_MIN_HITS
#
# Adversarial derivation rates: 0.80, 0.40, 0.40, 0.25, 0.20, 0.00 x7.
# Fires on 0.80 (4 hits, 4 tells) / 0.40 (2 hits, 2 tells) / 0.40 (2 hits).
# The 0.25 and 0.20 texts carry a single hit each and are left to Check 1,
# which flags both.


# ===========================================================================
# CHECK 3 — CONTRASTIVE-FRAME OVERUSE
# ===========================================================================
# The "not just X, it's Y" pivot. This one needed the narrowest patterns in the
# module, because TIMBR's own voice is FULL of contrast:
#
#   "It is not CrossFit. It is not Pilates. It is the barbell."
#   "This is not a story about equipment. This is a story about what the city
#    decided to want."
#   "Not because they failed. Because the city moved on."
#   "It reads less like a workout and more like a city worth exploring."
#
# All of that is house voice — PRINCIPLES Sec. 7's "concede then redirect" is
# itself a contrastive move. What separates it from the LLM version is that
# TIMBR states the negation and the correction as SEPARATE sentences and never
# reaches for an intensifier. The machine version compresses both halves into
# one clause and props it up with just / merely / simply / only.
#
# So every pattern below requires the compression: a negation and its pivot
# inside one clause. None of them matches on a bare "is not".
CONTRASTIVE_FRAMES = {
    # "it's not just a gym", "the shift is not merely cosmetic"
    "not-just": r"\b(?:is|are|was|were|it'?s|that'?s|they'?re|there'?s)\s+"
                r"not\s+(?:just|merely|simply|only)\b",
    # "training isn't just about lifting"
    "nt-just": r"\b(?:isn'?t|aren'?t|wasn'?t|weren'?t|doesn'?t|don'?t|didn'?t)\s+"
               r"(?:just|merely|simply|only)\b",
    # "it's not about the weight, it's about the reps"
    "not-about": r"\b(?:it'?s|it\s+is|this\s+is|that'?s|there'?s)\s+not\s+about\b",
    # "not the absence of training but rather the process"
    "but-rather": r"\bnot\s+[^.;!?]{1,60}?\bbut\s+rather\b",
    # "more than just a gym"
    "more-than-just": r"\b(?:more|rather)\s+than\s+just\b",
}

# ── Threshold derivation ───────────────────────────────────────────────────
# TIMBR derivation corpus: 0 frames in 4,792 words, across all five patterns.
# Adversarial derivation, frames per 250 words: 16.5, 2.2, 1.8, 1.7, 0.0 x8.
CONTRASTIVE_RATE_WINDOW = 250          # words
CONTRASTIVE_RATE_MAX = 2.0             # frames per window
CONTRASTIVE_MIN_HITS = 2

# Below this a text is a standfirst, a kicker or a caption, not a body, and
# extrapolating a per-250-word rate from it overstates what was measured.
#
# THIS NUMBER WAS WRONG ONCE AND THE CORPUS CAUGHT IT. It was first set to 120
# on the reasoning that short texts give jumpy rates. Running the finished
# module over the derivation split then showed adv05_contrastive — the single
# adversarial text written specifically to carry this tell, seven frames in it
# — scoring a clean 100, because at 106 words the gate exempted it before the
# rate was ever computed. A gate that swallows the case the check exists for is
# worse than no gate. Recorded rather than quietly edited, because the class of
# bug (a precondition silently eating the positive case) is the one a
# derive/validate split exists to find.
CONTRASTIVE_MIN_WORDS = 40
#
# The rate rule alone is already a real density filter: with MIN_HITS = 2 and a
# threshold of 2.0 per 250 words, a text fires only when words < 125 x frames,
# so a 500-word section needs five frames and a 250-word section needs three.
# Two frames inside 40 words is not a small-sample artefact, it is a text made
# of pivots.
# MIN_HITS = 2 is a deliberate false negative and it is the right one. ONE
# contrastive pivot is a legitimate rhetorical move and it is close kin to
# PRINCIPLES Sec. 7's "concede then redirect (admit a limit, hand
# responsibility back)". The defect is reaching for the same pivot repeatedly;
# a single instance is a sentence, not a fingerprint.
CONTRASTIVE_BASE_TELLS = 2
CONTRASTIVE_PER_EXTRA_FRAME = 1        # per frame past CONTRASTIVE_MIN_HITS


# ===========================================================================
# CHECK 4 — HEDGE STACKING
# ===========================================================================
# Two hedges compounding on one proposition ("may potentially", "it is possible
# that ... might"). Distinct from the single-hedge lists already in the repo:
#
#   voice_config.FITT_NEGATIVE[0] = (might|could|perhaps|possibly|seems|
#                                    appear|suggest|may)
#       — one hedge word, scored -3 as a register marker.
#   prohiblint.WORKOUT_SERIES_SECOND_PERSON_PATTERNS ("workout_series's SP
#       list") contains no hedges at all; it is prescriptive/predictive direct
#       address. Nothing here overlaps it.
#
# A stack is not a bigger version of a single hedge, it is a different defect.
# One hedge marks a claim as uncertain. Two hedges on the same claim mark the
# writer as unwilling to make it — the exact opposite of PRINCIPLES Sec. 9
# ("uncertain equals failed") and of Sec. 6's dry, quietly confident persona.
# There is no density at which stacking is house voice, so this check has no
# rate: every instance is a violation.
HEDGE_LEXICON = (
    r"may|might|could|possibly|potentially|perhaps|seemingly|arguably|"
    r"probably|likely|somewhat|relatively|fairly|generally|typically|"
    r"often|sometimes|appears?|seems?|suggests?|tends?|conceivably|"
    r"presumably|apparently"
)
# Deliberately NOT in the lexicon:
#   "can"    — ability and permission, not epistemic hedging, and prohiblint
#              already dropped "you can" from workout_series for exactly this
#              reason ("shakes you can pre-order before the last interval").
#   "about", "around", "roughly", "approximately" — measurement qualifiers.
#              A naive 2-hedges-per-clause rule flagged real TIMBR copy on
#              "has about twenty minutes in between to put roughly 40 grams of
#              protein somewhere", which is two numbers being reported
#              honestly, not a writer hiding. This is the specific false
#              positive that shaped the check.

#: A modal immediately negated is negation, not hedging: "a use the previous
#: tenant could not match" is a fact, "could possibly" is a hedge. Real TIMBR
#: copy uses the first form.
HEDGE_NEGATION_GUARD = r"(?!\s+(?:not|n'?t))"

#: Epistemic frames. A frame plus any hedge in the same sentence is a stack
#: even when they are not adjacent.
HEDGE_FRAMES = (
    r"\bit\s+(?:is|'?s)\s+possible\s+that\b"
    r"|\bit\s+may\s+be\s+that\b"
    r"|\bthere\s+is\s+a\s+chance\s+that\b"
    r"|\bit\s+could\s+be\s+argued\b"
    r"|\bone\s+might\s+argue\b"
    r"|\bit\s+is\s+conceivable\b"
)

#: Two hedges count as compounding when at most this many words separate them
#: inside one clause. 2 admits "may potentially" (0), "seems to possibly" (1),
#: "could well be possibly" (2) and excludes hedges that merely co-occur in a
#: long clause — the co-occurrence case is what produced the false positive
#: recorded above.
HEDGE_STACK_MAX_GAP_WORDS = 2

HEDGE_STACK_TELLS = 2            # per stacked clause
HEDGE_STACK_HARD_FAIL = 3        # stacks in one text
# 2 tells, not 3, so that one stack alone scores 84 and PASSES while one stack
# plus any other tell FAILS. This is the corroboration rule from NOISE_BUDGET
# applied honestly: a single regex hit does not get to reject a text by itself,
# however strong the tell is in principle. Two stacks (68) fail on their own.
# TIMBR derivation: 0 stacks. Adversarial derivation: 8, 2, 0 x10.


# ===========================================================================
# CHECK 5 — SENTENCE-LENGTH BURSTINESS
# ===========================================================================
# Real prose has rhythm: a four-word line against a thirty-word one. Machine
# prose regresses to the mean sentence. Measured as the coefficient of
# variation, CV = population stdev / mean, which is scale-free — a staccato
# section and a long-form feature are comparable.
#
# ── Floor derivation ───────────────────────────────────────────────────────
# All numbers below are measured with THIS module's own segmenter
# (synthlint.split_sentences / word_count), not an approximation of it. That
# matters: an early pass derived the floor from a rough splitter and landed on
# 0.30, which the shipped splitter then contradicted. The suite recomputes
# these on every run for the same reason.
#
# TIMBR derivation corpus, texts that clear both gates below, CV ascending:
#   0.3867  sample_issue:Nutrition   (menu listings — the flattest real copy)
#   0.4586  vol11:editor_body
#   0.4902  sample_issue:Social
#   0.5653  magazine_pass:Nutrition
#   0.5849  magazine_pass:Recovery
#   0.6020  vol11:city_intro
#   0.6208  magazine_pass:Training
#   0.6286  sample_issue:Training
#   0.6592  magazine_pass:Supplements
#   0.6798  sample_issue:Culture
# Worst (flattest) real sample: 0.3867. Floor = 0.3867 x 0.75 = 0.29002,
# rounded DOWN to two places:
BURSTINESS_CV_FLOOR = 0.29
# i.e. a real text would have to become 25% MORE uniform than the flattest
# TIMBR text ever measured before it trips. Adversarial derivation CVs:
#   0.083 0.091 0.145 0.219 0.274 | 0.292 0.332 0.407 0.437 0.446 0.553 0.620
# The floor catches the first five. The rest carry their tells elsewhere —
# burstiness is one channel, not the verdict.

#: Below this the statistic is noise. Real TIMBR slots of 2-3 sentences reach
#: CV 0.11-0.13 legitimately (pre_stack_body, post_stack_body), which would be
#: a false positive on every one of them.
BURSTINESS_MIN_SENTENCES = 8

#: The staccato exemption. PRINCIPLES Sec. 7: "Short declaratives. Fragments
#: allowed for punch." A section written in four-word lines is uniform because
#: uniformity IS the device there. Below this mean the check does not apply.
#: Exempts sample_issue Supplements (mean 4.3) and Nightlife (mean 5.2);
#: every adversarial flat text has mean 9.3-15.8 and is still measured.
BURSTINESS_MIN_MEAN_WORDS = 8

BURSTINESS_BASE_TELLS = 3
BURSTINESS_PER_CV_STEP = 0.05    # one extra tell per step below the floor
# 3 tells means a flat rhythm fails on its own (76). That is intended: unlike a
# lexical hit, this is a whole-text structural measurement over at least 8
# sentences, not a single pattern match, so it already carries its own
# corroboration.


# ===========================================================================
# CHECK 5, PART TWO — THE SPEC-LIST SHAPE, AND THE UNIT RHYTHM IS MEASURED OVER
# ===========================================================================
# THE DEFECT THIS EXISTS TO FIX
# -----------------------------
# Burstiness above was derived entirely from prose and then applied to
# everything, including text that is not prose. Run against real shipped copy,
# it failed vol11_slu's two workout pages:
#
#   workout_p4   9 rows, mean 9.8 words, CV 0.116  ->  52 FAIL
#   workout_p5   9 rows, mean 10.8 words, CV 0.085 ->  44 FAIL
#
# Those slots are the locked exercise table PRINCIPLES.txt Sec. 12 calls a
# structural contract ("the progression page mirrors the base page slot-for-
# slot, same movements, harder terms"). Every row is "- Name: sets x reps —
# cue". They measure as uniform because they ARE uniform: uniformity is the
# format. Nine rows of a locked table have no sentence rhythm to be flat.
#
# This is the same class of error as counting em-dashes instead of counting
# asides — a prose-shaped rule applied to a non-prose-shaped unit. The fix is
# the same in kind: count the governed unit.
#
# HOW BADLY IT WAS HIDDEN
# -----------------------
# Every shipped volume carries the same two slots, and all eight measured flat:
#
#   vol08 p4/p5  CV 0.123 / 0.157      mean 7.67 / 7.44   (passed)
#   vol09 p4/p5  CV 0.101 / 0.144      mean 7.78 / 6.89   (passed)
#   vol10 p4/p5  CV 0.137 / 0.144      mean 7.67 / 7.33   (passed)
#   vol11 p4/p5  CV 0.116 / 0.085      mean 9.78 / 10.78  (FAILED)
#
# The six that passed were not passing on merit. Their row means sat under
# BURSTINESS_MIN_MEAN_WORDS = 8, so the staccato exemption swallowed them
# before the CV was ever consulted. Vol 11's rows are one or two words longer,
# which is all it took. A latent false positive on every volume, held off by an
# accident of wording — so the fix has to be structural, not a nudge to a
# threshold.
#
# WHAT IS NOT DONE HERE
# ---------------------
# The rhythm check is NOT disabled for list-shaped text. Switching a check off
# on a shape a writer controls is a bypass, and "put a hyphen in front of every
# sentence" would be a cheap one. What changes is the UNIT: on a spec list the
# check stops measuring rows and measures the free-text field inside each row,
# which is the only part of a templated row that is written rather than filled.
# Both gates and the CV floor above are reused unchanged. See the measurements
# under SPEC_LIST_FIELD, below.

#: A row opens with a bullet glyph or a number enumerator. Letter enumerators
#: ("a)", "A.") are deliberately absent: they collide with initials and
#: single-letter abbreviations at line start, and no TIMBR format uses them.
SPEC_LIST_MARKER = r"^\s*(?:[-*•‣▪–—]|\d{1,2}[.)])\s+"

#: A format needs four rows. Three is a triad — the same reasoning that put
#: SAME_OPENER_RUN_MIN at 4 rather than 3, applied to rows instead of openers:
#: three parallel lines is a device, four is a format. Every real TIMBR spec
#: list measured has exactly nine rows, so the margin is wide.
SPEC_LIST_MIN_ROWS = 4

#: STRUCTURAL delimiters — field separators, not sentence punctuation. The
#: comma is excluded on purpose: it is prose punctuation and it appears inside
#: the cue field of most real rows ("activation, learn the hinge"), so counting
#: it would make the skeleton test meaningless.
SPEC_LIST_DELIMITERS = ":—–×|·→="

#: Rows must SHARE at least this many distinct delimiters. Not "the same
#: signature": measured across the eight real lists, rows differ in the
#: delimiters they carry, because a rep range ("3 x 12–15") adds an en dash to
#: some rows and not others. What every row does share is the skeleton —
#:
#:   intersection over all rows, all eight real lists = {':', '×', '—'}
#:
#: Two is the floor rather than one because ONE shared dash is not a template.
#: The brief that produced this check named that failure mode outright: do not
#: exempt anything that merely has a dash in it. A label separator plus at
#: least one field separator is the minimum that means "these rows are filled
#: from the same skeleton".
SPEC_LIST_MIN_SHARED_DELIMITERS = 2

#: A spec row does not end in a full stop. It is a set of labelled fields, not
#: a predication. True of all 72 rows across the eight real lists, and it is
#: the first thing a paragraph fails when it is bulleted without being
#: rewritten. Kept as a clause of the detector rather than as an anti-evasion
#: guard — the guard is SPEC_LIST_FIELD below — because it is the cleanest
#: mechanical statement of "this line is not a sentence".
SPEC_LIST_TERMINAL_PUNCTUATION = r"[.!?][\"'”’)\]]*$"

# ── SPEC_LIST_FIELD: what rhythm is measured on instead ────────────────────
# The unit is the LONGEST free-text field of the row: split the row on its
# structural delimiters and take the field carrying the most words. On
# "- Bulgarian Split Squat: 4 x 8 / leg — dumbbells, long stride" the fields
# are [Bulgarian Split Squat | 4 | 8 / leg | dumbbells, long stride] and the
# unit is "dumbbells, long stride".
#
# Longest field rather than "the cue after the em-dash" because the cue is not
# the only place free text can sit. A text that put its prose in the LABEL
# position instead ("- <whole sentence>: 3 x 10 — go") would defeat a
# cue-only rule while satisfying every other clause here. Taking the longest
# field finds the prose wherever the writer put it.
#
# MEASURED, real spec lists, mean words in the longest field per row:
#   vol08  3.11 / 2.78     vol09  3.56 / 2.89
#   vol10  3.00 / 2.56     vol11  4.33 / 5.11
# Worst (highest) real mean: 5.11, against BURSTINESS_MIN_MEAN_WORDS = 8. So
# every real list is exempted by the STACCATO gate, on its merits: a four-word
# coaching cue is a caption, and PRINCIPLES Sec. 7's "short declaratives"
# exemption is exactly the right one for it.
#
# MEASURED, the same adversarial texts rewritten into a fully compliant spec-
# list skeleton — marker, no full stop, ":" and "x" and "—" on every row, two
# numbers per row — with the slop pushed into the cue field, and again with it
# pushed into the label field:
#   adv03_flat_subtle     mean 11.06  CV 0.145   FIRES
#   adv08_subtle_flat     mean 11.57  CV 0.091   FIRES
#   adv10_brand_subtle    mean  9.27  CV 0.274   FIRES
#   adv15_HO_subtle_flat  mean 10.77  CV 0.083   FIRES
# Identical numbers for both placements, which is the point of using the
# longest field. Every one clears the mean gate, so every one is measured, and
# every one is flat enough to fire.
#
# That separation is what makes the exemption safe to grant, and it needed to
# be: adv03, adv10 and adv15 carry NO tell other than a flat rhythm. If the
# rhythm check were simply switched off for list-shaped text, all three would
# score a clean 100 the moment they were bulleted. Nothing else in the module
# catches them. The detector below refuses them on three independent clauses,
# and this field measurement catches anything that gets past it.
#
# THE BOUNDARY, STATED
# --------------------
# Detection is whole-text: a text is a spec list only when EVERY non-blank line
# is a row. Prose with a table embedded in it is not a spec list and is
# measured exactly as before. That is the conservative direction — the fallback
# for a text the detector declines is the shipped behaviour, not a new one —
# and it is why the detector is allowed to be a plain conjunction of clauses
# rather than a score.


# ===========================================================================
# CHECK 6 — REPEATED-OPENER RUNS
# ===========================================================================
# "This means... This allows... This ensures..." — the strongest single tell in
# the module, and the one that most nearly collided with the house voice.
#
# Real TIMBR derivation copy contains SIX runs of three consecutive sentences
# sharing an opener:
#   sample_issue:Training     "It is not CrossFit. It is not Pilates.
#                              It is the barbell."            lengths [4, 4, 4]
#   magazine_pass:Supplements "No loading phase. No cycling.
#                              No timing protocol worth..."   lengths [3, 2, 8]
#   magazine_pass:Nutrition   four menu blocks, "The <dish> is 41g protein,
#                              29g carbs, 19g fat, $16." x3   lengths [13-15]
#
# None of those is a defect. The first two are anaphora — PRINCIPLES Sec. 7's
# "Triads and parallelism" and "Fragments allowed for punch" in the same
# breath. The third is a data table set as prose, which Sec. 8 demands.
# A naive "3+ consecutive same opener" rule fires on real copy six times.
#
# Three separations, each measured:
#
# (a) SAME-WORD runs are flagged at FOUR, not three. TIMBR's parallelism device
#     is a TRIAD (Sec. 7 names it); three parallel sentences is the device
#     landing, four is the device running on. Derivation max in real copy: 3.
SAME_OPENER_RUN_MIN = 4
#
# (b) GENERIC-CLASS runs — This/It/These/Those/That/There followed immediately
#     by a verb — are flagged at three, because that chain is expository
#     scaffolding rather than parallelism. Real copy produced exactly one such
#     run (the CrossFit triad) and it is caught by (c).
GENERIC_OPENER_RUN_MIN = 3
GENERIC_OPENERS = frozenset({"this", "it", "these", "those", "that", "there"})
GENERIC_OPENER_VERB = (
    r"is|are|was|were|means?|allows?|ensures?|helps?|makes?|creates?|"
    r"provides?|offers?|gives?|leads?|results?|shows?|highlights?|"
    r"demonstrates?|represents?|reflects?|applies|apply|comes?|becomes?|"
    r"'s|’s|has|have|had|will|can|could|may|might|should|would|does|do|not"
)
#
# (c) The ANAPHORA EXEMPTION, applied to both rules. A run in which every
#     sentence is short is a rhetorical figure, not a chain of exposition.
#     Longest sentence inside a real exempt run: 8 words. Shortest sentence
#     inside the adversarial generic run: 11 words. The cut is placed at 10 —
#     two words of margin on the side that must never fire, one on the other,
#     because a false positive on house voice is the failure this module is
#     not allowed to have.
ANAPHORA_MAX_WORDS = 10
#
# (d) The DATA-LISTING EXEMPTION, applied to both rules. A run in which every
#     sentence carries two or more NUMBERS (tokens, not digits) is a spec
#     table, not prose. The menu runs carry four numbers a line. This is
#     belt-and-braces at the current same-word threshold of 4 (no real 4-run
#     exists yet), and it is what keeps a future venue with four dishes on the
#     menu from tripping the check.
DATA_LISTING_MIN_NUMBERS = 2
#
# (e) EACH PASSAGE IS PRICED ONCE. The two rules overlap by construction — a
#     chain of "This means... This allows..." is both a same-word run and a
#     generic-class run. A run whose sentences are already entirely covered by
#     runs reported before it is skipped, so one bad passage costs one penalty
#     instead of two or three. Without this, adv04_openers was charged three
#     times for one twelve-sentence stretch.

OPENER_RUN_TELLS = 2             # per run
# 2 tells, so one run alone passes (84) and a run plus anything else fails.
# Adversarial derivation: adv04_openers carries two priced runs (same-word runs
# of 4 and 4; the generic run of 8 that spans them both is suppressed by (e))
# = 4 tells before its flat rhythm is counted.


# ===========================================================================
# DROPPED CHECKS — measured, refused, recorded
# ===========================================================================
DROPPED_CHECKS = {
    "triad_rate": (
        "DROPPED. Rule-of-three / 'X, Y, and Z' rate per paragraph. The brief "
        "required a threshold conservative enough never to fire on real TIMBR "
        "copy. No such threshold exists, because the metric points the WRONG "
        "WAY: real TIMBR copy uses triads MORE than the adversarial corpus "
        "does, not less.\n"
        "Measured, prose triads only (candidates containing digits or clauses "
        "over six words excluded, so addresses and menu rows do not count):\n"
        "  TIMBR derivation      25 triads / 114 paragraphs = 0.219 per "
        "paragraph; 13 paragraphs carry at least one; max paragraph "
        "saturation (share of a paragraph's sentences carrying a triad) 0.50.\n"
        "  Adversarial derivation  11 of 12 texts score saturation 0.00. The "
        "twelfth scores 0.50 — identical to the real-copy ceiling.\n"
        "Any threshold at or below 0.50 fires on TIMBR before it fires on "
        "slop; any threshold above 0.50 fires on nothing at all. The device is "
        "TIMBR's (PRINCIPLES Sec. 7 names it outright) and the machines are "
        "not overusing it, so there is nothing here to detect. Dropping it is "
        "the finding, not a shortfall.\n"
        "Re-run before reinstating: the detector was also imprecise, counting "
        "appositions ('a change the head of programming, Wendell Marnowitz, "
        "described as overdue') as triads. A better detector would have to "
        "clear that first, and it would still face the direction problem."
    ),
}


# ===========================================================================
# Compiled patterns
# ===========================================================================
def _term_pattern(term):
    """Word-boundary, case-insensitive, flexible internal whitespace.

    Mirrors prohiblint._build_term_patterns so that a term written the same way
    in both modules matches the same spans in both modules.
    """
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    return re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)


VOCAB_PATTERNS = {t: _term_pattern(t) for t in EXTENDED_AI_VOCAB}

TRANSITION_OPENER_RE = re.compile(
    r"^[\s\"'“‘(\[]*(" +
    "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in FORMULAIC_TRANSITIONS) +
    r")\b",
    re.IGNORECASE,
)

CONTRASTIVE_PATTERNS = {name: re.compile(pat, re.IGNORECASE)
                        for name, pat in CONTRASTIVE_FRAMES.items()}

HEDGE_RE = re.compile(r"\b(" + HEDGE_LEXICON + r")\b" + HEDGE_NEGATION_GUARD,
                      re.IGNORECASE)
HEDGE_FRAME_RE = re.compile(HEDGE_FRAMES, re.IGNORECASE)

#: Clause boundaries. Coarse on purpose — the job is to stop two hedges in
#: different thoughts from being read as one stack, not to parse English.
CLAUSE_SPLIT_RE = re.compile(
    r"[,;:()]|\b(?:and|but|or|because|which|when|while|though|although|so|"
    r"then|if)\b",
    re.IGNORECASE,
)

GENERIC_OPENER_RE = re.compile(
    r"^(?:" + "|".join(sorted(GENERIC_OPENERS)) + r")\s+(?:" +
    GENERIC_OPENER_VERB + r")\b",
    re.IGNORECASE,
)

SPEC_LIST_MARKER_RE = re.compile(SPEC_LIST_MARKER)
SPEC_LIST_DELIM_RE = re.compile("[" + re.escape(SPEC_LIST_DELIMITERS) + "]")
SPEC_LIST_TERMINAL_RE = re.compile(SPEC_LIST_TERMINAL_PUNCTUATION)
