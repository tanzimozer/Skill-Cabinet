"""
prohiblint.py — ProhibLint module for TIMBR magazine eval harness.

Scans all 7 magazine sections for prohibited content and structural compliance.
Sections: Training, Nutrition, Supplements, Recovery, Culture, Social, Nightlife

Usage:
    from prohiblint import run_prohiblint
    results = run_prohiblint({"Training": "...", "Nutrition": "...", ...})

    # Or, for the Seattle Series / Workout Series product line (PRINCIPLES.txt
    # style spec instead of the magazine Editorial Handbook):
    results = run_prohiblint(sections, ruleset="workout_series")

Rulesets:
    "magazine" (default) — em-dash is a hard fail (any instance); section
        word counts are checked against WORD_COUNT_RANGES; second person is
        banned outright (Handbook Sec. 6, "second-person wellness coaching
        register").
    "workout_series" — at most one em-dash ASIDE per sentence is allowed
        (an aside bracketed by a matched PAIR of em-dashes is still one
        aside; 2+ asides in one sentence is a hard fail); word counts are
        NOT checked (that line is governed by CharLint's exact
        character-count locks instead); second person is allowed and only
        prescriptive coaching address is flagged (PRINCIPLES.txt Sec. 6-7
        endorse direct address); additionally bans a set of hype words and
        exclamation points outright (PRINCIPLES.txt Section 7).
"""

import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SECTIONS = ["Training", "Nutrition", "Supplements", "Recovery", "Culture", "Social", "Nightlife"]

WORD_COUNT_RANGES = {
    "Training":    (800, 1200),
    "Nutrition":   (600, 900),
    "Supplements": (400, 600),
    "Recovery":    (500, 800),
    "Culture":     (800, 1200),
    "Social":      (500, 700),
    "Nightlife":   (400, 600),
}

AI_BLOCKLIST = [
    "delve", "foster", "tapestry", "vibrant", "robust", "holistic",
    "leverage", "seamless", "pivotal", "transformative", "unlock",
    "elevate", "revolutionize", "journey", "empower", "thrive",
    "curated", "game-changer", "deep dive", "synergy", "ecosystem",
    "impactful", "actionable", "harness", "spearhead",
]

# Ruleset switch (see module docstring). "magazine" is the default so
# existing callers of run_prohiblint(sections_dict) are unaffected.
VALID_RULESETS = ("magazine", "workout_series")

# workout_series-only additions (PRINCIPLES.txt Section 7): "Banned forever:
# ultimate, amazing, game-changing, level up, unlock, transform, crush, beast
# mode, no excuses, superlatives, exclamation points, emoji, hype CTAs."
# We implement the enumerable terms below as a hard blocklist; "superlatives",
# "emoji", and "hype CTAs" aren't reliably matchable as literal strings and
# are left to human/editorial review. Exclamation points are handled
# separately by check_exclamation_points since they're punctuation, not a term.
# Note "unlock" also appears in AI_BLOCKLIST above — under workout_series a
# section using "unlock" is flagged by BOTH checks (generic AI-vocab tell,
# and PRINCIPLES.txt's specific outright ban). That double coverage is
# intentional, not a bug: they are two independent reasons the word is bad.
WORKOUT_SERIES_BLOCKLIST = [
    "ultimate", "amazing", "game-changing", "level up", "unlock",
    "transform", "crush", "beast mode", "no excuses",
]

# magazine ruleset. Editorial Handbook Sec. 6 bans the "second-person wellness
# coaching register" outright, so any direct address counts.
SECOND_PERSON_PATTERNS = [
    r"you should",
    r"your body",
    r"try this",
    r"you need to",
    r"you can",
    r"you will feel",
    r"your workout",
    r"you want to",
]

# ---------------------------------------------------------------------------
# SECOND PERSON IS NOT BANNED IN THE WORKOUT SERIES
# ---------------------------------------------------------------------------
# The magazine list above is the Handbook's, and the Handbook and PRINCIPLES.txt
# disagree about second person on purpose. Running the magazine list over
# workout_series copy imports a ban from the wrong rulebook, and it cost
# `anchor_venue` -3 for "shakes you can pre-order before the last interval",
# which is a description of what the Fuel Bar does.
#
# PRINCIPLES.txt does not ban direct address. It PRESCRIBES it:
#   Sec. 7  "Tiered direct address when segmenting readers (Beginners: ...
#           Intermediate: ...)"
#   Sec. 7  "Concede then redirect (admit a limit, hand responsibility back:
#           we bring the work, you bring the honesty)"
#   Sec. 6  the gold-standard test is whether a coach would say it "out loud,
#           plainly, to a smart friend" — one person addressing another
#   Sec. 6  belief 2 of 6 is "reader autonomy (you decide where you land)"
#   Sec. 6  belief 5 is worded "none of us has met your body" — the very
#           string "your body" is how PRINCIPLES states its own principle
#   Sec. 7  the parallelism example is "your history, your joints, your limits"
#
# So the second person itself is house voice. What PRINCIPLES still rules out is
# the narrower thing the Handbook was actually aiming at: address that
# PRESCRIBES or PREDICTS.
#
#   PRESCRIBES — "you should", "you need to", "you must", "you have to". A
#       modal of obligation aimed at the reader is the direct contradiction of
#       "reader autonomy (you decide where you land)" and of Sec. 7's concede-
#       then-redirect shape, which hands responsibility back rather than
#       issuing it.
#   PREDICTS — "you will feel", "you'll feel". Claiming to know what the
#       reader's body is about to do is the overclaim Sec. 6 names outright:
#       "defer to real expertise, never overclaim (none of us has met your
#       body)". Sec. 9's certainty rule points the same way — an unverifiable
#       claim is a failed claim.
#   "try this" — kept, on different grounds. Plain imperatives are all over the
#       approved baselines ("Train first.", "Order the Caffe Nico", "Turn the
#       page.", "go early") and Sec. 7 explicitly allows imperative CTAs, but
#       only flat ones: "CTAs are flat verbs: Read the issue. Get the guide.
#       Subscribe." "Try this" is the listicle CTA, which Sec. 7 bans as a
#       "hype CTA".
#
# Dropped for workout_series, each because PRINCIPLES either uses the form or
# endorses its shape:
#   "you can"      — describes what is possible, never instructs. The false
#                    positive that started this: "shakes you can pre-order".
#   "your body"    — Sec. 6 belief 5 is literally "none of us has met your body".
#   "your workout" — Sec. 7 parallelism: "your history, your joints, your limits".
#   "you want to"  — ambiguous: prescriptive as a softened "you should", but
#                    descriptive in "if you want to beat the line, come at six".
#                    It is not a modal of obligation, and Sec. 6's autonomy
#                    belief resolves the ambiguity in the reader's favour.
#                    Documented as a deliberate false negative.
WORKOUT_SERIES_SECOND_PERSON_PATTERNS = [
    r"you should",
    r"you need to",
    r"you must",
    r"you have to",
    r"you will feel",
    r"you'll feel",
    r"try this",
]

# Seattle place names, held once and used for two different jobs:
#   * the mandatory-element location checks (F), where a neighbourhood name is
#     one of the accepted "location anchors" that turns a bare capitalised name
#     into a *located* named place; and
#   * the cold-open person test (C), where a capitalised token naming a PLACE
#     can never be the person-subject of a cold-open — "Ballard is where the
#     5am crowd went after the Fremont lease fell through" is a lede about a
#     neighbourhood, not a scene about someone called Ballard.
# Two consumers, one list: the overlap is not a coincidence, it is the same
# fact (this token names a place, not a person or a venue) used twice.
SEATTLE_PLACE_NAMES = (
    "Capitol Hill", "Queen Anne", "South Lake Union", "Green Lake", "Crown Hill",
    "Sand Point", "View Ridge", "Pioneer Square", "White Center", "Beacon Hill",
    "Portage Bay", "West Seattle", "Lower Queen Anne",
    "Ballard", "Fremont", "SoDo", "Belltown", "Eastlake", "Westlake", "Madison",
    "Madrona", "Montlake", "Wallingford", "Ravenna", "Laurelhurst", "Leschi",
    "Georgetown", "Rainier", "Magnolia", "Phinney", "Greenwood", "Interbay",
    "Columbia", "Beacon", "Brighton", "Dunlap", "Holly", "Skyway", "Seward",
    "Jefferson", "Sunset", "Pike", "Pine", "Yesler", "Broadway", "Cascade",
    "Downtown", "Seattle", "Washington", "Puget", "Alki", "Roosevelt",
    "Northgate", "Fauntleroy", "Denny", "Harrison", "Thomas", "Yale",
)

# Single tokens drawn from the above — "South Lake Union" contributes South,
# Lake and Union. Used by the cold-open subject test, which only ever sees one
# leading token.
_PLACE_TOKENS = frozenset(
    token for name in SEATTLE_PLACE_NAMES for token in name.split()
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _word_count(text):
    return len(text.split())


def _strip_sidebars(text):
    """Remove [SIDEBAR]...[/SIDEBAR] blocks (case-insensitive) from text."""
    return re.sub(r'\[SIDEBAR\].*?\[/SIDEBAR\]', '', text, flags=re.IGNORECASE | re.DOTALL)


def _first_paragraph(text, max_chars=200):
    """Return the first paragraph, capped at max_chars characters."""
    # Split on double newline or take the whole thing
    para = re.split(r'\n\n+', text.strip())[0]
    return para[:max_chars]


# ---------------------------------------------------------------------------
# Check A — Em-dash detector
# ---------------------------------------------------------------------------

def check_em_dash(text):
    """
    magazine ruleset. Flag every U+2014 (—) character.
    Hard fail: any found. Penalty: -10 per instance.
    Returns (violations, penalty, hard_fail).
    """
    violations = []
    count = text.count('\u2014')
    if count:
        violations.append(
            f"Em-dash (U+2014) found: {count} instance(s). Hard fail."
        )
    penalty = count * -10
    hard_fail = count > 0
    return violations, penalty, hard_fail


_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

# Abbreviations whose trailing period is NOT the end of a sentence. Splitting a
# sentence in half at "Mr." or "9th St." would break a stacked em-dash pair into
# two single-em-dash "sentences" and silently bypass the workout_series hard
# fail: "The bar — Mr. Schomer's — is the grand one on Yale." is one sentence
# with two em-dashes, not two sentences with one each. St./Ave./Vol./No./Mr.
# are all over Seattle Series venue copy, so this is the common case, not an
# exotic one.
_ABBREVIATIONS = frozenset("""
    mr mrs ms dr prof rev sr jr st ave av blvd rd ln ct pl ter dr pkwy hwy
    vol no nos ste apt rm fl mt ft inc co ltd corp dept est approx dept
    jan feb mar apr jun jul aug sept sep oct nov dec
    mon tue tues wed thu thur thurs fri sat sun
    etc vs cf al ed eds pp fig figs sec secs ch chs
    max min sq lb lbs oz kg km mi
""".split())

_ABBREV_TAIL_RE = re.compile(r'(?:^|[\s(\["\'])([A-Za-z]+)\.$')

# A genuine new sentence starts with a capital, a digit, or an opening
# quote/bracket. "9th St. north" fails this (lowercase "north"), which catches
# abbreviations the list above does not know about.
_SENTENCE_OPENER_RE = re.compile(r'^[\'"‘“(\[]*[A-Z0-9]')


def _ends_with_abbreviation(fragment):
    """True when `fragment` ends in an abbreviation's period, not a full stop."""
    m = _ABBREV_TAIL_RE.search(fragment)
    if not m:
        return False
    word = m.group(1)
    # A single letter before a period is an initial or a directional
    # ("J. Smith", "456 Eastlake Ave E. north"), never a sentence end.
    return len(word) == 1 or word.lower() in _ABBREVIATIONS


def _sentence_spans(text):
    """
    (start, end) offsets of each sentence in `text`.

    A candidate boundary (period/!/? followed by whitespace) is only a real
    sentence break when the text to its left does not end in an abbreviation
    AND the text to its right opens like a sentence. Both guards are needed:
    "Vol. 1 of the run" is caught by the abbreviation list, "9th St. north" by
    the opener test, and "Mr. Schomer's" needs the list because "Schomer's"
    passes the opener test on its own.

    Offsets rather than substrings because the cold-open matcher needs to know
    where each sentence starts — a cold-open does not have to be the first
    sentence of its paragraph.
    """
    spans = []
    start = 0
    for m in _SENTENCE_SPLIT_RE.finditer(text):
        left = text[start:m.start()]
        right = text[m.end():]
        if _ends_with_abbreviation(left) or not _SENTENCE_OPENER_RE.match(right):
            continue
        if left:
            spans.append((start, m.start()))
        start = m.end()
    if text[start:]:
        spans.append((start, len(text)))
    return spans


def _split_into_sentences(text):
    """Sentences of `text`, for the em-dash stacking check."""
    text = text.strip()
    return [text[a:b] for a, b in _sentence_spans(text)]


# ---------------------------------------------------------------------------
# THE GOVERNED UNIT IS THE ASIDE, NOT THE DASH
# ---------------------------------------------------------------------------
# PRINCIPLES.txt Sec. 7: "One em-dash aside per sentence, never stacked."
#
# The noun is ASIDE. An aside is a phrase set off from the sentence, and in
# English it is punctuated one of two ways:
#
#   BRACKETED   ... — east on Denny, left on Yale — Espresso Vivace anchors ...
#               a matched PAIR of dashes around a phrase, mid-sentence.
#               TWO dash characters. ONE aside.
#   TRAILING    ... doors at 6am weekdays — early enough to beat the line.
#               a single dash introducing the final phrase.
#               ONE dash character. ONE aside.
#
# Counting dash CHARACTERS therefore mis-reads the rule at exactly the place it
# matters most: a correctly punctuated bracketed aside — the more careful of the
# two forms — spends two characters on one aside and was being reported as
# "stacked". That is how this check came to hard-fail `anchor_cafe`, owner-
# approved shipping copy from Canva DAHQoZJm12w, twice in one slot.
#
# The count. Dashes pair off left to right: 1+2 bracket an aside, 3+4 bracket
# the next one, and a leftover odd dash at the end opens a trailing aside. So
#
#       asides = ceil(dashes / 2)      violation when asides >= 2
#
# which is the same as saying: 1 or 2 dashes is legal, 3 or more is stacked.
# Every decomposition of 3+ dashes yields 2+ asides no matter how you pair
# them, so the verdict never depends on guessing which dash closes which — only
# the wording of the violation message does.
#
#   0 dashes -> 0 asides   legal
#   1 dash   -> 1 aside    legal   (trailing aside)
#   2 dashes -> 1 aside    legal   (matched pair; THE FIX)
#   3 dashes -> 2 asides   STACKED (a bracketed pair plus a trailing aside)
#   4 dashes -> 2 asides   STACKED (two bracketed pairs)
#   5, 6 ... -> 3+ asides  STACKED
#
# The ambiguous cases, decided:
#
#   RANGE DASH ("5—9 daily", "1989—92"). A dash closed up between two digits
#       joins two numbers; it does not interrupt the sentence, so it is not an
#       aside and is not counted. Without this, "the class runs 5—9 and the
#       roast — sweet caramel, never burnt — is Italian" reads as 3 dashes and
#       is falsely flagged, when it is one aside plus a number range. The
#       exemption only ever REMOVES non-asides from the count, and it is
#       deliberately narrow: digits on both sides, no spaces.
#   CLOSED-UP ASIDE ("heavy—your legs shake—but you finish"). NOT exempt. US
#       house style sets aside dashes closed, so exempting word—word would
#       excuse the entire closed-up style and leave the check catching nothing.
#       Only digit—digit is a range.
#   WORD RANGE ("Mon—Fri"). Counted as an aside dash, i.e. not exempt. It is
#       character-for-character identical to a closed-up aside, and the
#       typographically correct mark for a range is the en dash anyway.
#   EN DASH (U+2013). Never counted, and never was. The baselines' "45–60
#       minutes" and "Olson Kundig–designed" are en dashes; Sec. 7 governs the
#       em-dash aside only.
#   LEADING OR DANGLING DASH (a sentence that opens or ends on a dash).
#       Pairing is positional, so these fall out of ceil(n/2) with no special
#       case: one interruption of the sentence's flow, one aside.
#   INTERRUPTED SPEECH ('"I thought you said—" she stopped.'). A lone dash is
#       one aside and legal. Two broken-off utterances in one sentence read as
#       a pair and go unflagged — an accepted false negative: 2 dashes must be
#       legal for the bracketed case, and this product prints no dialogue.
#   SEMICOLON / COLON. Do NOT start a new unit. Sec. 7 says "per sentence" and
#       a semicolon joins clauses into one sentence; letting it reset the count
#       would make stacking legal for the price of one semicolon.
#   HARD LINE BREAK. DOES end a unit. These checks read whole Canva text
#       elements, where "\n" separates blocks — `night_page` is a title line, a
#       location rule, a blank line, then prose. Gluing a title with no
#       terminal period onto the first prose sentence would merge their dashes
#       into one phantom sentence. A sentence does not run across a manual line
#       break in this product; a mid-sentence "\n" is a layout defect that
#       would be visible on the page.

EM_DASH = '\u2014'

# Built by concatenation rather than as one raw literal: an escaped em-dash
# inside a raw string is six literal characters that the re module happens to
# re-interpret as an escape, which is a fact about re, not something the next
# reader should have to know.
_RANGE_DASH_RE = re.compile(r'(?<=\d)' + EM_DASH + r'(?=\d)')


def _aside_dash_count(sentence):
    """Em-dashes in `sentence` that punctuate an aside (ranges excluded)."""
    return _RANGE_DASH_RE.sub('', sentence).count(EM_DASH)


def _asides_from_dashes(dashes):
    """
    Asides carried by `dashes` em-dash characters.

    They pair off left to right and the odd one out is a trailing aside, so
    ceil(n / 2), written as (n + 1) // 2 to stay in integers. The single place
    this arithmetic lives — the check needs the dash count for its message and
    would otherwise re-derive the aside count beside it.
    """
    return (dashes + 1) // 2


def _count_asides(sentence):
    """How many em-dash asides `sentence` contains."""
    return _asides_from_dashes(_aside_dash_count(sentence))


def _aside_units(text):
    """
    The units the one-aside-per-sentence rule is measured over: sentences,
    with a hard line break also closing a unit. See the block comment above
    for why the line break counts and why a semicolon does not.
    """
    units = []
    for line in text.split('\n'):
        units.extend(_split_into_sentences(line))
    return units


def check_em_dash_workout_series(text):
    """
    workout_series ruleset. Per PRINCIPLES.txt Section 7: "One em-dash aside
    per sentence, never stacked."

    The governed unit is the ASIDE, not the dash character: a matched pair of
    em-dashes bracketing a phrase is ONE aside and is legal, and so is a
    single trailing em-dash introducing a final phrase. Two or more asides in
    one sentence is "stacked" — a violation and a hard fail. In dash terms
    that is 3 or more em-dashes in a sentence (ranges excluded). Unlike
    check_em_dash, a legal aside is not penalized at all.

    Returns (violations, penalty, hard_fail).
    """
    violations = []
    penalty = 0
    hard_fail = False
    for sentence in _aside_units(text):
        dashes = _aside_dash_count(sentence)
        asides = _asides_from_dashes(dashes)
        if asides >= 2:
            hard_fail = True
            penalty -= 10
            snippet = sentence.strip()
            if len(snippet) > 80:
                snippet = snippet[:80] + "..."
            violations.append(
                f"Stacked em-dash asides: {asides} asides ({dashes} em-dashes) "
                f"in one sentence (max 1 aside allowed per PRINCIPLES.txt "
                f"Sec. 7; a matched pair around one phrase is a single aside). "
                f"Hard fail. Sentence: \"{snippet}\""
            )
    return violations, penalty, hard_fail


# ---------------------------------------------------------------------------
# Check B — AI vocabulary blocklist
# ---------------------------------------------------------------------------

def _build_term_patterns(terms):
    """Build {term: compiled word-boundary regex} for a flat list of terms."""
    patterns = {}
    for term in terms:
        # For multi-word terms use simple case-insensitive search with word boundaries
        # on the first and last word
        escaped = re.escape(term)
        # Replace escaped space with \s+ to allow flexible spacing
        escaped = escaped.replace(r'\ ', r'\s+')
        pat = re.compile(r'(?<!\w)' + escaped + r'(?!\w)', re.IGNORECASE)
        patterns[term] = pat
    return patterns


# "journey" is qualified by the TIMBR Editorial Handbook (Section 6) as
# blocklisted only "in wellness context" — e.g. "your fitness journey",
# "this transformation journey" — unlike every other term in AI_BLOCKLIST,
# which is unconditional. Literal travel ("the journey home", "a train
# journey") should NOT fire. We special-case it below with a regex that
# requires a wellness/fitness qualifier immediately adjacent to "journey",
# instead of the plain word-boundary match every other term gets.
_JOURNEY_WELLNESS_QUALIFIERS = (
    r"fitness|wellness|health(?:y|ier)?|training|workout(?:s)?|"
    r"weight[\s-]?loss|transformation(?:al)?|transformative|strength|"
    r"recovery|nutrition|muscle|diet|self[\s-]?improvement|healing|"
    r"body[\s-]?transformation"
)

_JOURNEY_PATTERN = re.compile(
    r'(?:\b(?:' + _JOURNEY_WELLNESS_QUALIFIERS + r')\b\s+journey\b)'
    r'|'
    r'(?:\bjourney\b\s+(?:to|toward|towards|of)\s+(?:\w+\s+){0,2}'
    r'(?:' + _JOURNEY_WELLNESS_QUALIFIERS + r')\b)',
    re.IGNORECASE
)


def _build_blocklist_patterns():
    patterns = _build_term_patterns([t for t in AI_BLOCKLIST if t != "journey"])
    if "journey" in AI_BLOCKLIST:
        patterns["journey"] = _JOURNEY_PATTERN
    return patterns

_BLOCKLIST_PATTERNS = _build_blocklist_patterns()


def check_ai_blocklist(text):
    """
    Flag AI vocabulary terms.
    Penalty: -5 per hit. Hard fail: 3+ hits in section.
    Note: "journey" only counts as a hit in wellness/fitness context (see
    _JOURNEY_PATTERN above) — "the journey home" will not match, "your
    fitness journey" will.
    Returns (violations, penalty, hard_fail).
    """
    violations = []
    total_hits = 0
    for term, pat in _BLOCKLIST_PATTERNS.items():
        hits = pat.findall(text)
        if hits:
            count = len(hits)
            total_hits += count
            violations.append(
                f"AI blocklist term '{term}' found {count} time(s). Penalty: {count * -5}."
            )
    penalty = total_hits * -5
    hard_fail = total_hits >= 3
    if hard_fail:
        violations.append(
            f"AI blocklist hard fail: {total_hits} total hits (threshold: 3)."
        )
    return violations, penalty, hard_fail


# ---------------------------------------------------------------------------
# Check C — Fictional cold-open heuristic
# ---------------------------------------------------------------------------

# Simple list of common English proper-noun indicators:
# Capitalised words that are NOT sentence-start (after period/newline) and
# are NOT on a stoplist of common title-case words.
_TITLE_CASE_STOPLIST = {
    "The", "A", "An", "In", "On", "At", "It", "He", "She", "They",
    "We", "I", "And", "But", "Or", "For", "Of", "To", "Is", "Are",
    "Was", "Were", "Has", "Have", "Had", "This", "That", "These",
    "Those", "His", "Her", "Their", "Our", "Its", "My", "Your",
    "There", "Here", "When", "While", "After", "Before", "As",
}

# Capitalised tokens that are not people: indefinite pronouns, number words,
# calendar words, times of day, and this magazine's own section names. English
# capitalises all of these at a sentence start exactly as it capitalises a
# name, so the cold-open subject test has to know they are not names. ("Four
# minutes from DRIFT, Victrola pours..." opens real Seattle Series copy —
# "Four" is not a person.)
_NON_PERSON_SUBJECTS = frozenset({
    "Someone", "Somebody", "Anyone", "Anybody", "Everyone", "Everybody",
    "No", "Nobody", "None", "Nothing", "Something", "Anything", "Everything",
    "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Twenty", "Thirty", "Forty", "Fifty", "Hundred",
    "Half", "First", "Second", "Third", "Fourth", "Fifth", "Last", "Next",
    "Most", "Many", "Some", "Few", "Both", "Each", "Every", "All", "Another",
    "Morning", "Afternoon", "Evening", "Night", "Tonight", "Midnight", "Noon",
    "Today", "Tomorrow", "Yesterday", "Now", "Later", "Sometimes", "Often",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Sunday", "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
    "Training", "Recovery", "Nutrition", "Supplements", "Culture", "Social",
    "Nightlife",
})


def _has_proper_noun(text):
    """
    Heuristic: look for capitalised words that are not sentence starters
    and not on the title-case stoplist. If found, assume proper noun present.

    Sentence-initial words are skipped wherever they occur, not just at the
    very start of the text. English capitalises the first word of every
    sentence whether or not it is a proper noun, so counting them made
    _has_proper_noun return True for almost any multi-sentence paragraph
    ("... rest. Someone sits up ..." scored "Someone" as a proper noun) and
    silently disabled the unattributed-narrative branch of check_cold_open.
    """
    sentence_start = True
    for token in re.findall(r'\S+', text):
        clean = re.sub(r'[^A-Za-z]', '', token)
        if clean and not sentence_start and clean[0].isupper() \
                and clean not in _TITLE_CASE_STOPLIST:
            return True
        if re.search(r'[.!?][\'")\]]*$', token):
            sentence_start = True
        elif clean:
            sentence_start = False
    return False


# Third-person singular present-tense verbs of PHYSICAL action, used only by
# _has_narrative_present_tense — the "is this paragraph narrating a body moving
# through a scene?" scan. Deliberately does NOT contain "is": a copula is not
# movement, and treating it as narrative made every "<X> is ..." sentence in the
# product read as narration.
_NARRATIVE_VERBS = (
    r'sits|stands|walks|runs|jogs|laces|ties|pushes|pulls|steps|moves|checks|'
    r'opens|shuts|enters|leaves|heads|grabs|reaches|climbs|turns|leans|slips|'
    r'waits|counts|carries|drops|wakes|rises|shoulders|hauls|breathes'
)


def _has_narrative_present_tense(text):
    """
    Heuristic: look for third-person singular present-tense verbs of physical
    action typical of narrative prose (sits, stands, walks, laces, reaches...).
    Case-insensitive: verb identity is the signal here, not capitalisation.
    """
    narrative_verbs = re.compile(
        r'\b(' + _NARRATIVE_VERBS + r')\b',
        re.IGNORECASE
    )
    return bool(narrative_verbs.search(text))


# ---------------------------------------------------------------------------
# What the cold-open matcher is actually separating
# ---------------------------------------------------------------------------
# Handbook Sec. 6 bans "fictional cold-opens" and "invented characters or
# constructed scenes", with one worked example: "It is 7:14 on a Tuesday and
# Maya is already...". The thing being banned is FICTION — an invented person
# in an invented moment. Real reported detail about a real named person is the
# People register's whole job (Sec. 5.2), and its own reference sentence is
# "Jade Kim orders the same thing every Tuesday: the black sesame smoothie and
# a side of turkey avocado toast." That must never be flagged.
#
# So the line is not drawn at the name, and it is not drawn at the verb:
#
#   Maya Okonkwo laces her shoes before dawn      a specific moment, invented
#   Jade Kim orders the same thing every Tuesday  a habit, reported
#
# Both are a full name plus a present-tense action verb. What separates them is
# the FRAME. A scene happens once, at a moment the copy points to; a report
# describes what someone does repeatedly, or attributes it to them out loud.
# An earlier version tried to separate them by demanding a BARE first name, on
# the theory that a surname means attribution — which cost nothing to evade
# ("Maya Okonkwo" instead of "Maya") and flagged nothing that "every Tuesday"
# would not have cleared anyway.
#
# The person-in-motion rule is therefore a conjunction of four tests. Each one
# is necessary; none is sufficient; each alone kills the whole false-positive
# set, which is what makes the rule robust rather than tuned:
#
#   1. SUBJECT — a person's name at the start of a sentence: one to three
#      capitalised tokens ("Marcus", "Maya Okonkwo"), or a family plural ("The
#      Nakamura sisters"). Not sentence furniture ("The", "It"), not an
#      indefinite or a number word ("Someone", "Four"), not a place ("Ballard",
#      "Cascade"), and not a word this same copy writes in lowercase elsewhere —
#      that last test is what demotes "Recovery"/"Protein"/"Creatine" to the
#      common nouns they are, without needing a list of every abstract noun in
#      English. Read from the token itself, not from an ASCII regex, so Ayşe,
#      José and Xiulan are names like any other.
#   2. PREDICATE — an open-class present-tense verb: a lowercase token ending in
#      "s" for a singular subject, a bare verb for a plural one, or a
#      progressive ("is lacing"). Open-class on purpose, so there is no verb
#      list to outgrow. Copulas, auxiliaries and function words are excluded by
#      CLOSED classes, which are enumerable in a way that action verbs are not.
#   3. MOMENT — the paragraph anchors the action in a scene: a personal pronoun
#      pointing back at the subject, a clock time, a threshold ("before the
#      doors open", "still dark") or a body caught mid-action ("already
#      lacing"). Ordinary connectives do NOT qualify: "after the first hour"
#      and "before it" are English, not scenery.
#   4. NOT REPORTED — the copy does not frame the action as a habit ("every
#      Tuesday", "always", "most days") or attribute it to a source ("says",
#      "recalls"). This is the test that lets rule 1 accept a surname. It is a
#      WEIGHING, not a veto — see the next block.
#
# The rule is tried at the start of every sentence in the opening, not only the
# first: a cold-open does not have to be one sentence long, and anchoring on the
# paragraph let a writer clear the whole check by putting one line of throat
# before the scene.
#
# Everything is matched case-sensitively. A cold-open reads "Marcus checks his
# watch", not "marcus checks his watch" — the capital IS the name signal, and
# re.IGNORECASE folds [A-Z] into accepting lowercase, destroying it.

#: Below this, the one-signal-wide rules do not run. See check_cold_open.
SHORT_OPENING_WORDS = 30

# "It is 7:14 ..." / "It's 5:30am ..." — the Handbook's own example form: the
# scene opens on a clock. Kept as its own rule because "It" is sentence
# furniture, so the person rule can never reach it.
_CLOCK_OPENER_RE = re.compile(r'^It(?:\s+is|\'s|’s)\s+\d')

# A word, Unicode-aware: "Ayşe" and "Ana-María" are names, and [A-Z][a-z]+ is
# an ASCII test that quietly says they are not.
_NAME_TOKEN_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")

# Words ending in "ing" that are not verbs, so "<Name> is nothing without ..."
# is not read as a progressive.
_ING_NON_VERBS = frozenset({
    "nothing", "something", "anything", "everything", "morning", "evening",
    "during", "spring", "thing", "king", "ceiling",
})

# CLOSED class: copulas, auxiliaries and the stative verbs that behave like
# them, in both numbers. These can never carry a cold-open on their own —
# "Recovery is ...", "Creatine is ...", "Ballard is ..." are ledes, not scenes.
_COPULA_VERBS = frozenset({
    "is", "was", "are", "were", "be", "been", "being",
    "has", "have", "had", "does", "do", "did",
    "seems", "seem", "appears", "appear", "remains", "remain",
    "becomes", "become", "means", "mean", "stays", "stay", "exists", "exist",
    "will", "would", "can", "could", "may", "might", "must", "shall", "should",
})

# CLOSED class: function words. A name followed by one of these has not reached
# its verb yet, so there is nothing to call an action.
_FUNCTION_WORDS = frozenset("""
    of in on at to for with from by about into onto over under after before
    during since until through between among against without within across
    behind beyond near off out up down per via like than as toward towards
    upon along beside besides despite except plus versus
    and or but so yet nor if because while when where whether though although
    unless whenever wherever that which who whom whose what
    the a an this these those his her their its our your my
    it he she they we you i there here
    not never always also still already just only even too very really often
    sometimes again once now then later soon perhaps indeed instead thus
    more less most least well quite rather almost nearly ever no nothing
""".split())

# Capitalised sentence-openers that are not names. Held apart from
# _TITLE_CASE_STOPLIST on purpose: that set also drives venue-name validation,
# and widening it there would start discarding real venue name tokens.
_FUNCTION_WORD_SUBJECTS = frozenset(
    w.capitalize() for w in _FUNCTION_WORDS
) | frozenset({"I", "Yours", "Ours", "Theirs", "Hers"})

# Capitalised words that make a name an ORGANISATION rather than a person.
#
# SEATTLE_PLACE_NAMES holds NEIGHBOURHOODS, which is what the location anchors
# need, and it says nothing about the words venue names are actually built from.
# So "Fuel House opens its doors before the sun is up" and "Iron Works fills up
# before the doors open" — ordinary Location-Features copy — read as a person in
# motion and cost -15 each.
#
# Some of these are also real surnames (Park, Field, House, Bell). The override
# is a human personal pronoun in the same sentence: "Marcus Park laces HIS
# shoes" is a person, "Fuel House opens ITS doors" is not. That is the same
# shape as voicelint's person-only cue overriding its place filter — arrived at
# independently and kept independent, because the two lists are answering
# different questions and should not be merged.
_ORG_TOKENS = frozenset("""
    Cafe Café Bar Park Restaurant Pub Lounge Rooftop Terrace Garden Gardens
    Market Diner Bistro Eatery Grill Kitchen Tavern Taproom Brewery Winery
    Coffeehouse Roastery Gym Studio Club Barre Yoga Pilates Crossfit Dojo
    Barbell Athletic Athletics Weightlifting Powerlifting Boxing Rowing
    Swimming Cycling Climbing Fitness Strength Health Wellness Nutrition
    Works House Provisions Collective Company Room Hall Project Society
    Supply Goods Coffee Roasters Roasting Brewing Foods Mercantile Trading
    Union Exchange Institute Academy Center Centre Associates Group Partners
    Lab Labs Bakery Deli Larder Pantry Depot Station Yard Forge Field Bell
    Sports Sport Team Squad League Alliance Foundation Trust Council
""".split())

# Plural nouns that make "The <Surname> <noun>" a family rather than a thing.
_FAMILY_PLURALS = frozenset({
    "sisters", "brothers", "twins", "cousins", "boys", "girls", "women", "men",
    "kids", "children", "family", "parents", "couple", "crew", "household",
})

# Personal pronouns pointing back at a human subject. "you/your" is deliberately
# absent: that is the second-person coaching register (Check D), not narration.
_PERSON_PRONOUN_RE = re.compile(r'\b(?:he|him|his|she|her|hers)\b', re.IGNORECASE)

_CLOCK_TIME_RE = re.compile(
    r'\b\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?|\b\d{1,2}\s*[ap]\.?m\.?\b',
    re.IGNORECASE
)

# Nouns that turn "before/after/until/while <X>" into a threshold in a scene
# rather than an ordinary connective. This list is the whole point of the
# construction: `(before|after|until|while) (the|a|an|it|its)` accepted "the
# floor empties after the first hour" and "shorter than the block before it",
# which are two pieces of plain editorial English, and cost a -15 each.
_THRESHOLD_NOUN_ALT = (
    r"dawn|sunrise|sunup|sundown|dusk|daybreak|first\s+light|daylight|"
    r"sun|doors?|gates?|alarm|lights?|bell|whistle|city|streets?|traffic|"
    r"buses|crowd"
)

_SCENE_MOMENT_RE = re.compile(
    # "is already lacing" — the Handbook's own example form. Bare "already" is
    # an ordinary adverb ("the second block is already harder than the first");
    # "already" plus a participle is a body caught mid-action.
    r'\balready\s+(?:[a-z]+ly\s+)?[a-z]+ing\b'
    r'|\b(?:before|after|until|till|while)\s+'
     r'(?:the\s+|a\s+|an\s+|his\s+|her\s+|their\s+|its\s+)?'
     r'(?:' + _THRESHOLD_NOUN_ALT + r')\b'
    # "before anyone else" — the room is empty, which is scenery. Bare "before
    # anyone" is not: "before anyone has to be told it out loud" is a clause.
    r'|\b(?:before|after|until)\s+'
     r'(?:anyone|everyone|anybody|everybody)\s+else\b'
    r'|\b(?:still\s+dark|in\s+the\s+dark|first\s+light|half[\s-]light|'
     r'pre[\s-]?dawn)\b',
    re.IGNORECASE
)

# The reported/habitual frame: what makes copy a profile rather than a scene.
# A magazine's People register earns its living on exactly these words, so
# every one of them is a reason NOT to flag.
_HABITUAL_UNIT_ALT = (
    r"day|days|morning|mornings|evening|evenings|night|nights|week|weeks|"
    r"weekday|weekdays|weekend|weekends|month|months|year|years|time|"
    r"Monday|Mondays|Tuesday|Tuesdays|Wednesday|Wednesdays|Thursday|Thursdays|"
    r"Friday|Fridays|Saturday|Saturdays|Sunday|Sundays"
)

_HABITUAL_FRAME_RE = re.compile(
    r'\b(?:every|each)\s+(?:single\s+)?(?:' + _HABITUAL_UNIT_ALT + r')\b'
    # "on Tuesdays" is a person's habit. "on weekdays" and "on weekends" are
    # opening hours — deliberately absent, or "Rainier Barbell opens at five on
    # weekdays." would excuse the cold-open in the sentence after it.
    r'|\bon\s+(?:Mondays|Tuesdays|Wednesdays|Thursdays|Fridays|Saturdays|'
     r'Sundays)\b'
    # "always orders", "is usually first" — but NOT a bare "always". "the same
    # clothes as always" is a detail inside a scene, not a reported habit, and
    # a bare match there vetoed a genuine unattributed cold-open.
    r'|\b(?:always|usually|normally|routinely|habitually)\s+'
     r'(?:[a-z]+ly\s+)?[a-z]+(?:s|ed|ing)\b'
    r'|\b(?:is|are|was|were|has|have|had)\s+'
     r'(?:always|usually|normally|routinely|habitually)\b'
    r'|\bnever\s+(?:misses|missed|skips|skipped)\b'
    r'|\b(?:most|some)\s+(?:days|mornings|evenings|nights|weeks|weekends)\b'
    r'|\b(?:once|twice|three\s+times|four\s+times|five\s+times)\s+a\s+'
     r'(?:day|week|month|year)\b'
    r'|\bthe\s+same\s+(?:thing|order|table|seat|route|session|breakfast)\b'
    r'|\bhas\s+been\b|\bfor\s+the\s+past\b'
    r'|\bsince\s+(?:January|February|March|April|May|June|July|August|'
     r'September|October|November|December|\d{4})\b'
    r'|\bstarted\s+(?:coming|training|running|lifting|going|showing)\b',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Reported vs constructed: scope and weight, not presence
# ---------------------------------------------------------------------------
# _HABITUAL_FRAME_RE used to be an unconditional veto: one habitual phrase
# anywhere in the sentence switched the whole person rule off. That replaced a
# bad binary (bare first name vs surname) with another one, and the new binary
# was EASIER to evade, because a fiction writer produces this texture without
# being told to:
#
#   Priya chalks her hands and steps onto the platform, rolling her shoulders
#   twice THE WAY SHE ALWAYS DOES.
#
# Six words appended to a staged scene and the check went quiet. It also cost a
# genuine catch, on a sentence whose habitual phrase is not about the subject
# at all:
#
#   Marcus laces his shoes in the stairwell because the lobby is cold and the
#   door has not been fixed SINCE NOVEMBER, and he counts the flights down.
#
# A date in a subordinate clause about a DOOR is not evidence that the SUBJECT's
# action is a habit.
#
# What actually separates the two registers is not whether a habitual phrase is
# present but WHERE IT SITS and WHAT IT IS COMPETING WITH:
#
#   Jade Kim orders the same thing every Tuesday: ...        REPORTED
#   Priya chalks her hands and steps onto the platform ...   CONSTRUCTED
#
# In the reported sentence the frame governs the MAIN CLAUSE — "orders the same
# thing every Tuesday" IS the sentence, its spine is a pattern, and there is no
# staged physical action anywhere in it. In the constructed sentence the spine
# is a sequence of bodily events and the habitual phrase is decoration hung off
# the end of it. So two signals replace the veto:
#
#   SCOPE   (_main_clause) — a frame counts only inside the main clause of a
#           sentence whose subject is the person: up to the first clause break,
#           and in the following sentence only when that sentence is still
#           about the same person ("He does this every morning." elaborates;
#           "The elevator has not worked since November." does not).
#   WEIGHT  (_scene_beats) — a scene staging two or more physical beats is a
#           scene whatever tag is attached to it. This is what catches the one
#           evasion scope cannot see, where the writer puts the tag inside the
#           main clause with no punctuation ("... on one shoulder every morning
#           and drops it by the rack").
#
# Neither signal is a binary on its own: a frame that governs still loses to a
# staged scene, and a staged scene with no frame at all never needed the test.
#
# LIMITATION, stated rather than papered over. A ONE-beat scene whose habitual
# frame does govern the subject's main clause is not separable by these signals
# — "Maya Okonkwo laces her shoes before dawn every Tuesday." and "Jade Kim
# orders the same thing every Tuesday" have the same shape, and the second is
# the House Handbook's own People-register reference sentence. Both read as
# reported here. Separating them needs a signal this module does not have:
# whether the paragraph goes on to SUSTAIN the moment (a scene continues) or to
# leave it (a profile moves on to the person), which is discourse structure, or
# a dependency parse that can say which clause a modifier attaches to. Pinned in
# TestOneBeatHabitClauseIsTheKnownLimit so a future reader can see it is a
# decision and not an oversight.

# Punctuation and subordinators that close a main clause and open an adjunct.
# NOT here: before/after/since/until/while-as-preposition. Those introduce
# phrases far more often than clauses in this copy ("before dawn every
# Tuesday"), and cutting at them would push the People register back into scope.
_CLAUSE_BREAK_RE = re.compile(
    r'[,;:()\[\]—–]'
    r'|\b(?:because|although|though|unless|whereas|while|when|whenever|'
     r'wherever|if|as|that|which|who|whom|whose|where)\b'
    # "the way she always does" is an adjunct in anyone's grammar.
    r'|\bthe\s+way\b'
    # A coordinator introducing a NEW noun phrase starts a new clause with a
    # new subject: "and the door has not been fixed". "and drops it" and "and
    # he counts" do not — they are still the person, still the scene.
    r'|\b(?:and|but|or)\s+(?:the|a|an|this|that|these|those)\b',
    re.IGNORECASE
)

# Bodily actions: the beats a constructed scene is built out of. Surface forms
# are spelled out rather than derived, because English -s/-ing morphology is not
# worth a stemmer here and an explicit list is auditable.
#
# This list is EVIDENCE, never a gate. It is only ever consulted to override a
# habitual frame that already governs, so a verb missing from it costs a catch
# in that one narrow case and can never cause a false positive. That is the
# opposite failure mode from _NARRATIVE_VERBS, which gates the unattributed
# branch — which is why the two lists are separate and this one is wider.
#
# Deliberately absent: takes, lifts, presses, sets, works, trains, moves-as-noun
# — every one of them is ordinary training vocabulary, and a false beat here
# turns real People-register copy into a cold-open.
_MOTION_BEAT_FORMS = frozenset("""
    sits sitting stands standing walks walking runs running jogs jogging
    laces lacing ties tying pushes pushing pulls pulling steps stepping
    checks checking opens opening shuts shutting enters entering
    leaves leaving heads heading grabs grabbing reaches reaching
    climbs climbing turns turning leans leaning slips slipping
    waits waiting counts counting carries carrying drops dropping
    wakes waking rises rising hauls hauling breathes breathing
    chalks chalking wraps wrapping rolls rolling racks racking
    kneels kneeling crouches crouching bends bending
    hangs hanging swings swinging jumps jumping strides striding
    paces pacing crosses crossing knocks knocking shoves shoving
    hoists hoisting nods nodding shoulders shouldering
    grips gripping wipes wiping tightens tightening zips zipping
    slings slinging glances glancing unracks unracking clips clipping
    ducks ducking tugs tugging shuffles shuffling sips sipping
    drags dragging stamps stamping sprints sprinting spins spinning
    kicks kicking hops hopping tapes taping adjusts adjusting
    buckles buckling tosses tossing
""".split())

_MOTION_BEAT_RE = re.compile(
    r'\b(?:' + '|'.join(sorted(_MOTION_BEAT_FORMS)) + r')\b', re.IGNORECASE)

# A determiner, possessive or quantifier in front of one of those forms means it
# is the NOUN, not the verb: "rolling her SHOULDERS", "the RACKS turn over",
# "his HEADS". Without this guard the noun readings pad the beat count, and a
# padded count is a false positive.
_BEAT_NOUN_MARKERS = frozenset("""
    the a an his her its their our your my this that these those
    one two three four five six seven eight nine ten both each every
    no any some few many several other another such
""".split())

_LAST_WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*$")

# Personal pronouns that carry a subject forward into the next sentence.
_SUBJECT_CONTINUATION_RE = re.compile(r'^\s*(?:He|She|They|Both|Neither)\b')

#: Physical beats at which a staged scene outweighs a habitual frame.
SCENE_BEATS_OUTWEIGH_FRAME = 2

# CLOSED class: verbs of reported speech. "Marcus Webb says he laces up before
# dawn" is attribution — a source, quoted — not a scene, however much motion the
# rest of the sentence carries. Excluded HERE, in the subject's own predicate,
# rather than paragraph-wide: a bare "says" anywhere in the copy is not a
# reported frame ("neither of them says a word" is scene detail), and vetoing on
# it cost a genuine cold-open.
_REPORTING_VERBS = frozenset({
    "says", "said", "explains", "explained", "tells", "told", "notes", "noted",
    "adds", "added", "recalls", "recalled", "remembers", "remembered",
    "admits", "admitted", "insists", "insisted", "argues", "argued",
    "describes", "described", "reckons", "puts", "calls", "called",
})

_PROGRESSIVE_RE = re.compile(
    r"^\s+(?:is|was|are|were)\s+(?:already\s+)?(?:[a-z]+ly\s+)?([a-z]+ing)\b")
# The adverb slot is optional and comes BEFORE the verb: "Maya quietly laces
# her shoes" is the same scene as "Maya laces her shoes", and without this one
# word evaded the whole rule. The progressive arm already allowed it.
_BARE_VERB_RE = re.compile(
    r"^\s+(?:already\s+|still\s+|now\s+|just\s+|slowly\s+|[a-z]+ly\s+)?([a-z]+)\b")


def _is_capitalised(word):
    return bool(word) and word[0].isupper()


def _leading_words(text, limit=4):
    """
    The first `limit` words of `text` as (word, end_offset) pairs, stopping at
    the first thing that is not a plain space between two words. A comma or a
    full stop ends the run: "Jade Kim, 34," is two words, not four.
    """
    words = []
    pos = 0
    while len(words) < limit:
        m = _NAME_TOKEN_RE.match(text, pos)
        if not m:
            break
        words.append((m.group(), m.end()))
        gap = re.compile(r"[ \t]+").match(text, m.end())
        if not gap:
            break
        pos = gap.end()
    return words


def _read_person_subject(sentence):
    """
    Peel a candidate person-subject off the front of `sentence`.

    Returns (name_tokens, rest_of_sentence, is_plural), or None when the
    sentence does not open on a name-shaped run of words. This only reads the
    SHAPE; whether the shape is a person is _is_person_subject's job.
    """
    words = _leading_words(sentence)
    if not words:
        return None

    # "The Nakamura sisters lace up ..." — a family takes a plural verb, so the
    # singular -s morphology that carries every other subject cannot see it.
    if (len(words) >= 3
            and words[0][0].lower() == "the"
            and _is_capitalised(words[1][0])
            and words[2][0].lower() in _FAMILY_PLURALS):
        return [words[1][0]], sentence[words[2][1]:], True

    if not _is_capitalised(words[0][0]):
        return None
    name = [words[0][0]]
    end = words[0][1]
    for word, word_end in words[1:3]:          # up to three capitalised tokens
        if not _is_capitalised(word):
            break
        name.append(word)
        end = word_end
    return name, sentence[end:], False


def _person_predicate_verb(rest, plural):
    """
    The finite action verb `rest` opens with, or None.

    Morphology plus two closed exclusion classes, never a verb list: the set of
    action verbs is open and a list of them misses "shoulders" and "hauls" for
    exactly as long as nobody thinks to add them.
    """
    m = _PROGRESSIVE_RE.match(rest)
    if m:
        verb = m.group(1)
        return None if verb in _ING_NON_VERBS else verb
    m = _BARE_VERB_RE.match(rest)
    if not m:
        return None
    verb = m.group(1)
    if (verb in _COPULA_VERBS or verb in _FUNCTION_WORDS
            or verb in _REPORTING_VERBS):
        return None
    if plural:
        return verb                            # "lace up", "take the hill"
    return verb if verb.endswith('s') and not verb.endswith('ss') else None


def _is_person_subject(tokens, haystack, sentence=""):
    """
    True when `tokens` — the capitalised run opening a sentence — plausibly
    name a person rather than a place, an abstraction, or ordinary sentence
    furniture that English happened to capitalise.

    The lowercase test is the interesting one: if the same copy writes the head
    word in lowercase anywhere else, it is a common noun that got capitalised
    because it started a sentence ("Recovery", "Protein", "Training"). Personal
    names are never written lowercase, so this costs nothing on a real
    cold-open and it needs no dictionary of abstract nouns.
    """
    human = bool(_PERSON_PRONOUN_RE.search(sentence))
    for token in tokens:
        bare = _bare_token(token)
        if bare in _PLACE_TOKENS or bare in _NON_PERSON_SUBJECTS:
            return False
        if bare in _ORG_TOKENS and not human:
            return False
    head = _bare_token(tokens[0])
    if (head in _TITLE_CASE_STOPLIST or head in _FUNCTION_WORD_SUBJECTS
            or head in _NON_PERSON_SUBJECTS):
        return False
    if re.search(r'(?<!\w)' + re.escape(head.lower()) + r'(?!\w)', haystack):
        return False
    return True


def _has_scene_moment(text):
    """True when the copy anchors its action in a specific moment/scene."""
    return bool(
        _PERSON_PRONOUN_RE.search(text)
        or _CLOCK_TIME_RE.search(text)
        or _SCENE_MOMENT_RE.search(text)
    )


def _is_reported(text):
    """
    True when the copy carries a habitual frame ANYWHERE in it.

    Presence only. The person rule does not use this — see _reported_frame_wins
    for why presence is not enough there. It still gates the unattributed-scene
    branch, where there is no subject to scope a frame to in the first place.
    """
    return bool(_HABITUAL_FRAME_RE.search(text))


def _main_clause(sentence):
    """
    `sentence` up to its first clause break: the region a habitual frame has to
    sit in before it can be said to GOVERN rather than decorate.
    """
    m = _CLAUSE_BREAK_RE.search(sentence)
    return (sentence[:m.start()] if m else sentence).strip()


def _scene_beats(text):
    """
    How many physical beats `text` stages.

    Counts bodily-action verb forms, skipping the ones a determiner marks as
    nouns. This is the weight a staged scene puts on the scale against a
    habitual tag; see the block comment above _CLAUSE_BREAK_RE.
    """
    beats = 0
    for m in _MOTION_BEAT_RE.finditer(text):
        preceding = _LAST_WORD_RE.search(text[:m.start()].rstrip())
        if preceding and preceding.group().lower() in _BEAT_NOUN_MARKERS:
            continue
        beats += 1
    return beats


def _continues_the_subject(sentence, name_tokens):
    """
    True when `sentence` is still about the person `name_tokens` names, so a
    habitual frame in it is a frame on THEIR action.

    "He does this every morning." elaborates the scene before it. "The elevator
    has not worked since November." is about an elevator, and reading its date
    as the subject's habit is what made the Marcus-stairwell cold-open invisible.
    """
    if _SUBJECT_CONTINUATION_RE.match(sentence):
        return True
    lead = _leading_words(sentence, limit=1)
    return bool(lead) and _bare_token(lead[0][0]) in {
        _bare_token(t) for t in name_tokens}


def _reported_frame_wins(snippet, spans, index, name_tokens):
    """
    True when the copy reports a habit rather than staging a scene.

    Two signals, both required — a frame that GOVERNS a main clause about the
    subject, and a scene too thin to outweigh it. Either one alone is a binary
    that one phrase decides, which is the defect this replaced.
    """
    start, end = spans[index]
    window = [snippet[start:end]]
    if index + 1 < len(spans):
        following = snippet[spans[index + 1][0]:spans[index + 1][1]]
        if _continues_the_subject(following, name_tokens):
            window.append(following)

    governs = any(_HABITUAL_FRAME_RE.search(_main_clause(s)) for s in window)
    if not governs:
        return False
    return sum(_scene_beats(s) for s in window) < SCENE_BEATS_OUTWEIGH_FRAME


def _cold_open_rule(text, full_text=None):
    """
    Which cold-open rule `text` trips, or None. See the block comment above.

    Returns "clock" or "person". check_cold_open needs to know WHICH, because
    the two rules do not carry the same weight of evidence and so do not get
    the same length gate.

    `full_text` is the whole section, used only for the "does this copy write
    the subject in lowercase elsewhere?" test; it defaults to `text` so the
    matcher can still be called with a single paragraph.
    """
    snippet = text.strip()
    if not snippet:
        return None
    haystack = full_text if full_text is not None else text

    # Rule 1 — the scene opens on a clock ("It is 7:14 on a Tuesday and ...").
    if _CLOCK_OPENER_RE.match(snippet):
        return "clock"

    # Rule 2 — a person, in physical motion, at a specific moment, in copy that
    # does not frame the moment as a habit.
    if not _has_scene_moment(snippet):
        return None
    spans = _sentence_spans(snippet)
    for i, (start, end) in enumerate(spans):
        read = _read_person_subject(snippet[start:end])
        if not read:
            continue
        name, rest, plural = read
        if not _person_predicate_verb(rest, plural):
            continue
        if not _is_person_subject(name, haystack, snippet[start:end]):
            continue
        # Is this a report of a habit or a staged scene? Weighed, not vetoed:
        # scope decides whether a habitual frame governs the subject's own main
        # clause, and beats decide whether the scene outweighs it anyway.
        if _reported_frame_wins(snippet, spans, i, name):
            continue
        return "person"
    return None


def _matches_cold_open_pattern(text, full_text=None):
    """True when the opening reads as a fictional cold-open."""
    return _cold_open_rule(text, full_text) is not None


def check_cold_open(text):
    """
    Check the first paragraph (first 200 chars) for a fictional cold-open.
    Penalty: -15.
    Returns (violations, penalty, hard_fail=False).

    WHY TWO GATES. The old single `word_count > 30` floor meant a one-line
    cold-open was never examined at all — "Maya laces her shoes before dawn."
    is six words and is precisely the banned device, so the floor was a bypass
    anyone could find by writing less. But it cannot simply be removed: the
    other two rules are one signal wide, and one of them ("It is 5am.") matches
    ordinary short furniture — a deck, a standfirst, a kicker.

    So the floor is applied per rule, by how much evidence the rule actually
    carries:
      * the person rule is a four-way conjunction (a name, an action verb, a
        moment, and no reported frame). Short copy can satisfy all four only by
        being a cold-open, so it runs at any length.
      * the clock opener is one pattern, and the unattributed-scene branch has
        no name in it at all. Both keep the floor.
    """
    violations = []
    snippet = _first_paragraph(text)
    rule = _cold_open_rule(snippet, full_text=text)

    if rule == "person":
        flagged = True
    elif _word_count(snippet) > SHORT_OPENING_WORDS:
        # The unnamed-actor branch: a physical scene, set at a specific moment,
        # with nobody and nowhere named in it ("Someone sits up in bed, reaches
        # for a phone ... before the sun is up"). It covers the case the
        # person-in-motion rule structurally cannot — a cold-open whose
        # character is never given a name. It demands the same "specific
        # moment" evidence as that rule: without it, "no names + any physical
        # verb" flags ordinary copy, e.g. real Seattle Series cover body
        # ("Seattle wears its fitness in the open ... The city moves ...")
        # where the only capitalised words open their sentences.
        unattributed_scene = (
            not _has_proper_noun(snippet)
            and _has_narrative_present_tense(snippet)
            and _has_scene_moment(snippet)
            and not _is_reported(snippet)
        )
        flagged = (rule == "clock") or unattributed_scene
    else:
        flagged = False

    if flagged:
        violations.append(
            "Fictional cold-open heuristic triggered in first paragraph: "
            "no verified proper noun with narrative present tense, or matches "
            "known cold-open pattern."
        )

    penalty = -15 if flagged else 0
    return violations, penalty, False
# ---------------------------------------------------------------------------
# Check D — Second-person coaching register
# ---------------------------------------------------------------------------

def _compile_sp(terms):
    return [
        re.compile(r'(?<!\w)' + re.escape(p) + r'(?!\w)', re.IGNORECASE)
        for p in terms
    ]


_SP_PATTERNS = _compile_sp(SECOND_PERSON_PATTERNS)
_WS_SP_PATTERNS = _compile_sp(WORKOUT_SERIES_SECOND_PERSON_PATTERNS)

# {ruleset: (terms, compiled)}. No silent fallback for an unknown name, same
# stance as run_prohiblint: a typo'd ruleset must not quietly get magazine
# rules, because "quietly got the other rulebook" is exactly the defect this
# split exists to fix.
_SP_BY_RULESET = {
    "magazine": (SECOND_PERSON_PATTERNS, _SP_PATTERNS),
    "workout_series": (WORKOUT_SERIES_SECOND_PERSON_PATTERNS, _WS_SP_PATTERNS),
}


def check_second_person(text, ruleset="magazine"):
    """
    Flag second-person coaching language outside [SIDEBAR] blocks.

    magazine (default): the Handbook Sec. 6 ban on the second-person wellness
    coaching register — any direct address in SECOND_PERSON_PATTERNS.

    workout_series: PRINCIPLES.txt Sec. 6-7 endorse direct address, so only
    PRESCRIPTIVE and PREDICTIVE address is flagged (see the comment on
    WORKOUT_SERIES_SECOND_PERSON_PATTERNS). Descriptive second person —
    "shakes you can pre-order", "your history, your joints" — is house voice
    and passes.

    Penalty: -3 per hit, both rulesets. Never a hard fail.
    Returns (violations, penalty, hard_fail=False).
    """
    if ruleset not in _SP_BY_RULESET:
        raise ValueError(
            f"Unknown ruleset {ruleset!r}. Valid rulesets: "
            f"{', '.join(repr(r) for r in VALID_RULESETS)}."
        )
    terms, patterns = _SP_BY_RULESET[ruleset]
    # Curly apostrophes are what a word processor produces, and "you'll feel"
    # must not become invisible because the copy came through Canva.
    clean_text = _strip_sidebars(text).replace('’', "'")
    violations = []
    total_hits = 0
    for pat_str, pat in zip(terms, patterns):
        hits = pat.findall(clean_text)
        if hits:
            count = len(hits)
            total_hits += count
            violations.append(
                f"Second-person coaching pattern '{pat_str}' found {count} time(s). Penalty: {count * -3}."
            )
    penalty = total_hits * -3
    return violations, penalty, False


# ---------------------------------------------------------------------------
# Check E — Word count range
# ---------------------------------------------------------------------------

def check_word_count(section_name, text):
    """
    Binary pass/fail based on section word-count range.
    Penalty: -20 if out of range.
    Returns (violations, penalty, hard_fail).
    """
    violations = []
    lo, hi = WORD_COUNT_RANGES.get(section_name, (0, float('inf')))
    wc = _word_count(text)
    if wc < lo or wc > hi:
        violations.append(
            f"Word count {wc} is outside allowed range [{lo}–{hi}] for section '{section_name}'."
        )
        return violations, -20, True
    return violations, 0, False


# ---------------------------------------------------------------------------
# Check F — Mandatory value element checker (issue-level)
# ---------------------------------------------------------------------------
#
# Everything below turns on capitalisation, and none of it may be compiled with
# re.IGNORECASE. These checks ask "does the issue name real, located places?"
# and in English the answer is carried entirely by the capital letter: "the
# coffee place, 12 main" and "Bluebird Provisions, 123 Broadway E" are the same
# string shape and differ only in case. Folding case away turns the check into
# "does the issue contain some words and some digits", which passes lowercase
# filler — and this block is now blocking, so that verdict ships.
#
# A capital alone is not enough either, because English also capitalises the
# first word of every sentence. So a candidate name additionally has to contain
# at least one capitalised token that is not ordinary sentence furniture ("The
# coffee shop" is not a venue called The), and names are counted DISTINCT, so
# one venue repeated six times cannot satisfy a "≥4 named places" requirement.

_NEIGHBOURHOOD_ALT = '|'.join(
    re.escape(name).replace(r'\ ', r'\s+')
    for name in sorted(SEATTLE_PLACE_NAMES, key=len, reverse=True)
)

# Generic street-type words, for "456 Eastlake Ave E" style addresses.
_STREET_SUFFIX_ALT = (
    r'Ave|Avenue|St|Street|Blvd|Boulevard|Rd|Road|Way|Dr|Drive|Ln|Lane|'
    r'Pl|Place|Ct|Court|Ter|Terrace|Pkwy|Parkway|Hwy|Highway|Sq|Square'
)

# ---------------------------------------------------------------------------
# A VENUE IS NOT A PERSON
# ---------------------------------------------------------------------------
# "Name, Neighbourhood" is the shape of a venue with a location — and it is
# equally the shape of a person with an address:
#
#     Bluebird Provisions, Capitol Hill      a cafe
#     Aisha Coleman, Beacon Hill             a woman who lives there
#
# Nothing inside those five words tells them apart, and this matters more here
# than anywhere else in the module: Nutrition is a people-register section
# (Handbook Sec. 5.2), so naming four subjects and where they live is what that
# copy is SUPPOSED to do. Counting those four as "named places" let an issue
# with no venues in it at all clear a blocking check that exists to require
# venues.
#
# The separation is not in the name. It is in what a venue HAS and a person does
# not, and the anchors are therefore split into two tiers:
#
#   VENUE-GRADE — a street address ("123 Broadway E", "12th Avenue"). Copy in
#       this product does not print where a person lives to the house number;
#       an address is a venue. Handbook Sec. 9 makes it the locked minimum for a
#       nutrition spot ("Name of venue + neighbourhood + full address"), so
#       requiring it there is the spec, not a heuristic.
#   AMBIGUOUS — a bare neighbourhood. Shared by people and venues, so it counts
#       only when the name also does something only a venue does: opens at a
#       time, closes, serves, pours, or is introduced as "a bar"/"the cafe".
#       Merely mentioning a gym in the same sentence is not enough — the venue
#       evidence has to be that name's own predicate, or "Marcus Webb,
#       Georgetown, trains at a gym near the water" makes Marcus a venue.
#
# On top of both tiers sits a person veto: an age apposition (", 34,"), a
# directly-adjacent reporting verb ("says", "recalls"), ", who", or a role
# apposition (", a strength coach") means the name is a human being whatever
# anchor follows it.
#
# Neither tier is folded case-insensitively, for the reason above.

_ADDRESS_ANCHOR = (
    r"\d{1,5}\s+(?:[A-Z]|\d+(?:st|nd|rd|th))"                  # 123 Broadway
    r"|\d+(?:st|nd|rd|th)\s+(?:[A-Z]|" + _STREET_SUFFIX_ALT + r")"   # 12th Ave
)

# One to four capitalised tokens: the shape of a venue name. Two guards on the
# space BETWEEN tokens, because without them a "name" runs off the end of its
# own sentence and invents venues out of two unrelated words:
#   * `(?<![.!?])` — the character class allows a trailing period so "Ave." and
#     "St." stay inside a name, which also let a name swallow a full stop and
#     carry on into the next sentence ("... Tuesdays. Seattle's gyms" scored a
#     venue called "Tuesdays Seattle's").
#   * `[^\S\n]` instead of `\s` — a name does not span a paragraph break.
_PROPER_NAME = (
    r"[A-Z][A-Za-z'&.]*(?:(?<![.!?])[^\S\n]+[A-Z][A-Za-z'&.]*){0,3}"
)

# A named place with a location anchor. The name is 1-4 capitalised tokens; the
# anchor is captured so the tier can be read off it — a digit-initial anchor is
# a street address, anything else is a neighbourhood.
_LOCATED_PLACE_RE = re.compile(
    r"\b(?P<name>" + _PROPER_NAME + r")"                            # the name
    r"(?:\s*,\s*|\s+(?:in|at|on|near)\s+)"                          # separator
    r"(?P<anchor>"
        + _ADDRESS_ANCHOR +
        r"|(?:" + _NEIGHBOURHOOD_ALT + r")\b"                       # Capitol Hill
    r")"
)

# Place-type words that make a capitalised name a venue on their own
# ("Copper Tavern", "Green Lake Park", "the bar: Navy Strength").
_PLACE_TYPE_ALT = (
    r'cafe|café|bar|park|restaurant|pub|lounge|rooftop|terrace|garden|market|'
    r'diner|bistro|eatery|grill|kitchen|tavern|taproom|brewery|winery|'
    r'coffeehouse|coffee\s+shop|roastery|gym|studio|club'
)

# The place-type word itself may be capitalised ("Copper Tavern") or not ("the
# bar: Navy Strength"), so it — and only it — is matched case-insensitively,
# via a scoped inline flag. The NAME half stays case-sensitive. Word boundaries
# on both ends matter: without them "bar" matches inside "Barbell" and "park"
# inside "Parks", which is where the old pattern got most of its "hits".
#
# The type-word-FIRST arm requires real punctuation or "called"/"named" between
# the type and the name. Without it, "the gym Marcus uses has no name on the
# door" reads as a venue called Marcus — English elides the relative pronoun
# ("the gym [that] Marcus uses"), so an unpunctuated "<type> <Name>" is far more
# often a relative clause about a person than a naming. The cost is that
# type-first venue names ("Cafe Presse") are only counted through their location
# anchor; the benefit is that no person standing next to a gym becomes one.
#
# The space between the NAME and the type word carries the same two guards as
# the spaces inside the name, and for the same reason. Without them the name
# ends one sentence and the type word opens the next, and the two are read as
# one venue: "She trains with Marcus Webb. Club members meet at six" scored a
# venue called Marcus Webb, off a paragraph that names no venue at all. The
# guard existed on `_PROPER_NAME`'s internal spaces and was simply never
# carried across the join.
_TYPED_VENUE_RE = re.compile(
    r"\b(" + _PROPER_NAME + r")(?<![.!?])[^\S\n]+(?i:" + _PLACE_TYPE_ALT + r")\b"
    r"|\b(?i:" + _PLACE_TYPE_ALT + r")\b(?:\s*[:,]\s*|\s+(?:called|named)\s+)"
     r"(" + _PROPER_NAME + r")"
)

# Cues that ONLY a person takes, read off the text immediately following a
# name + anchor. Each is a closed, enumerable form: an age, a relative pronoun
# English reserves for humans, a reporting verb, a job title. Nothing here is
# the open class of "things a person might DO next" — that is handled
# separately, below `_VENUE_PREDICATE_RE`, because deciding it needs to know
# what a venue does first.
#
# LEADING SEPARATOR. Every branch accepts an optional comma, because the tail
# these are read off begins at the end of a LOCATION and English punctuates the
# end of a location with one:
#
#     Marcus Webb, 2201 Cavell Road, says the breakfast never changes.
#                                  ^ the tail starts here
#
# The reported-speech branch used to demand `\s+says`, which the comma made
# unreachable — on the address tier the tail ALWAYS starts with a comma, so a
# quoted human with a street address walked straight through the strictest,
# Handbook-locked tier of a blocking check. `\s*,?\s*` is the whole fix.
_PERSON_CUE_RE = re.compile(
    r"^(?:"
        r"\s*,\s*\d{1,2}\s*,"                               # ", 34," age
        r"|\s*,?\s*(?:is|was)\s+\d{1,2}\b"                  # "is 34"
        r"|\s*,\s*who(?:se|m)?\b"                           # who/whose/whom
        # Reported speech. "adds" and "notes" are deliberately absent: a venue
        # adds a class and a study notes a result, so vetoing on them threw
        # away real venues ("Fremont Hot Yoga adds breathwork sessions").
        r"|\s*,?\s*(?:says|said|explains|explained|tells|told|recalls|recalled|"
         r"remembers|remembered|laughs|laughed|admits|admitted|insists|"
         r"insisted|replies|replied|argues|argued)\b"
        r"|\s*(?:,|\s+(?:is|was))\s*(?:a|an|the)\s+(?:[a-z]+[\s-]){0,2}"
         r"(?:coach|trainer|lifter|runner|athlete|owner|founder|manager|"
         r"instructor|nurse|teacher|engineer|barista|chef|physio|therapist|"
         r"student|mother|father|parent|regular|member)\b"  # role apposition
    r")"
)

# What a venue does and a person does not, read off the text immediately
# following a name + neighbourhood. The opening/closing verbs must be followed
# by a time word: "opens at five" is a venue, "opens the gym" is whoever has
# the key.
_VENUE_PREDICATE_RE = re.compile(
    r"^\s*(?:,\s*|\s+)?(?:"
        r"(?:is\s+|now\s+|still\s+)?(?:opens?|opening|closes?|reopens?)\s+"
         r"(?:at|from|until|till|by|daily|early|late|weekdays?|weekends?|\d)"
        r"|(?:is\s+|stays?\s+)?(?:open|closed)\s+"
         r"(?:at|from|until|till|by|daily|early|late|weekdays?|weekends?|\d)"
        r"|(?:serves?|pours?|sells?|seats?|stocks?|brews?|roasts?|bakes?)\b"
        r"|(?:a|an|the)\s+(?:[a-z]+[\s-]){0,2}(?i:" + _PLACE_TYPE_ALT + r")\b"
        r"|(?i:" + _PLACE_TYPE_ALT + r")\b"
    r")"
)

# ---------------------------------------------------------------------------
# WHAT A PERSON DOES IS AN OPEN CLASS
# ---------------------------------------------------------------------------
# `_PERSON_CUE_RE` above is a list of CUES, and a list is the wrong shape for
# the commonest thing a person does after their address: an ordinary verb.
#
#     Aisha Coleman, 812 Harbor Street, Ballard, eats the same breakfast daily.
#     Marcus Webb,   2201 Cavell Road,  Georgetown, keeps his oats in a jar.
#
# "eats" and "keeps" are not cues and never will be, because the set of verbs a
# human can take is open and grows with the language. Enumerating it is the bug
# this module has now shipped three times (the cold-open verb list, the
# habitual-frame veto, this one). So the ACTION slot is judged by MORPHOLOGY —
# third-person -s, regular -ed, a direct-object frame — and the only lists kept
# are of the things that must be EXCLUDED. Those are all genuinely closed:
# English is not acquiring new prepositions, new auxiliaries, or new irregular
# past tenses.
#
# WHICH WAY THIS ERRS. A finite action verb that is not on the venue's own
# predicate list is read as a PERSON. That is deliberate for a BLOCKING check:
# a missed venue makes the gate stricter and fails an issue that could have
# passed, which the writer sees and fixes; a missed person lets a non-compliant
# issue ship silently. The strict tier is Handbook Sec. 9's, and its failure
# direction has to be the loud one.

# ── CLOSED classes 1 and 2 are ALREADY IN THIS MODULE ──────────────────────
# `_COPULA_VERBS` and `_FUNCTION_WORDS`, defined for the cold-open subject
# test, are the same two linguistic classes this test needs and they are
# reused rather than re-listed. A second copy under a second name is not a
# safety margin: the two would drift, and — this being how the duplicate was
# caught — a module-level `_FUNCTION_WORDS = ...` written a second time
# silently REBINDS the first, so the cold-open check would have started
# reading the venue check's copy.
#
# The one thing they do not cover is the stative past. "-ed" is read as a
# regular past below, which is right for "cooked" and wrong for "remained
# closed on Mondays" — a state, not a person acting. Stative verbs are a
# closed class and their pasts are enumerable.
_STATIVE_PAST = frozenset("""
    seemed appeared remained became meant stayed existed belonged
""".split())

# ── CLOSED class 3: the irregular past forms ───────────────────────────────
# Finite past tenses that carry no -ed. The list is finite and takes no new
# members — which is precisely why enumerating THESE is safe where enumerating
# action verbs was not. Regular pasts and third-person presents need no list.
_IRREGULAR_PAST = frozenset("""
    went came took made gave got saw said told kept left ran sat stood wrote
    spoke grew knew found held brought built bought sold drove won lost put cut
    set met felt meant sent spent taught thought caught began broke chose drew
    fell flew forgot hid led lay paid read rode rose shot slept sang swam threw
    understood woke wore quit drank ate rebuilt swore stuck struck hung dug
    bent lent bound wound sank rang beat fed fled hit hurt let lit shook shrank
    slid spread stole swept swung tore wove
""".split())

# The first lowercase token after the location, with an optional adverb in
# front and an optional direct-object determiner behind. The verb slot (group
# 1) is OPEN — no verb list — and group 2 is the transitive frame.
#
# The leading `,?` is the same separator problem `_PERSON_CUE_RE` has: a tail
# read off the end of an address starts at the comma that closed it.
_PREDICATE_SLOT_RE = re.compile(
    r"^\s*,?\s*(?:already\s+|still\s+|now\s+|never\s+|always\s+|often\s+|"
    r"also\s+|usually\s+|[a-z]+ly\s+)?"
    r"([a-z]{2,})\b"
    r"(?:\s+(the|a|an|his|her|their|its|two|three|four|five|six|seven|eight|"
    r"nine|ten|every|each|both|another|one)\b)?")

# A comma-closed apposition, up to three words: ", a chef,", ", a dietitian,",
# ", a warehouse-adjacent room,". It is STEPPED OVER, not judged — which is the
# point. The role list in `_PERSON_CUE_RE` is a list of JOBS, and jobs are an
# open class ("a dietitian", "a paramedic", "a bartender" are on it nowhere),
# so a person introduced by an unlisted job walked through the strict tier
# exactly like a person who "eats". Rather than grow the list, the parenthetical
# is skipped and whatever the name actually DOES is read on the other side:
#
#     ", a dietitian, eats the same breakfast."  -> ", eats ..."  person
#     ", a corner cafe, opens at six."           -> ", opens ..." venue
#
# The closing comma is required, and that is what keeps a venue's own
# description out of it: "..., a warehouse-adjacent room with six long tables."
# never closes, so nothing is skipped and nothing is decided.
_APPOSITION_RE = re.compile(
    r"^\s*,\s*(?:a|an|the)\s+(?:[a-z][a-z-]*\s+){0,2}[a-z][a-z-]*\s*(?=,)")


def _is_person_action(token, obj):
    """
    True when `token` — the first lowercase word after a name and its location
    — is a finite ACTION verb with a human subject. Morphology plus one
    syntactic frame, never a verb list:

      * third-person present: ends in "s"   (eats, keeps, cooks, carries)
      * regular past:         ends in "ed"  (ordered, walked, supervised)
      * irregular past:       closed class above (kept, ran, wrote)
      * anything else taking a direct object, which catches irregulars the
        closed class has not heard of. "-ing" is excluded: a participle is not
        a finite verb, and "Ballard Commons carrying two tables" is a place
        with a load on it.

    `obj == "its"` is the one inanimate signal in the frame and it wins
    outright. English reserves "its" for non-persons, so "makes its own bread"
    is the kitchen talking and no amount of verb morphology changes that.
    """
    if obj == "its":
        return False
    if (token in _COPULA_VERBS or token in _FUNCTION_WORDS
            or token in _STATIVE_PAST):
        return False
    if token in _IRREGULAR_PAST:
        return True
    if token.endswith("ing"):
        return False
    if token.endswith("s") and not token.endswith("ss"):
        return True
    if token.endswith("ed") and len(token) > 3:
        return True
    return bool(obj)


def _person_tail(tail):
    """
    True when what follows a name and its location belongs to a human being.

    Three layers, in this order:
      1. `_PERSON_CUE_RE` — closed, unambiguous person grammar. Wins outright,
         because "Bluebird Provisions, Capitol Hill, a head coach, opens at
         five" is a person however venue-shaped the rest of the sentence is.
      2. `_VENUE_PREDICATE_RE` — what only a venue does. Checked BEFORE the
         open class, and this order is load-bearing: "opens at six" and
         "serves until two" are third-person -s verbs, so morphology alone
         would read every real venue in the issue as a person.
      3. the open action class, reading past a comma-closed apposition to
         reach the predicate it is parenthetical to.
    """
    if _PERSON_CUE_RE.match(tail):
        return True
    if _VENUE_PREDICATE_RE.match(tail):
        return False
    m = _PREDICATE_SLOT_RE.match(tail)
    if m and _is_person_action(m.group(1), m.group(2)):
        return True
    apposition = _APPOSITION_RE.match(tail)
    return bool(apposition) and _person_tail(tail[apposition.end():])


def _proper_name_tokens(fragment):
    """
    Capitalised tokens in `fragment` that are not ordinary title-case sentence
    furniture. "The coffee shop" yields nothing; "Copper Tavern" yields both.

    Filters the same two sets the cold-open subject test uses: sentence
    furniture ("The", "It") and the capitalised non-names ("One gym in March
    2025" names a quantity and a month, not a venue).
    """
    return [
        token for token in re.findall(r"\b[A-Z][A-Za-z'&]*\b", fragment)
        if token.rstrip("'s") not in _TITLE_CASE_STOPLIST
        and token not in _TITLE_CASE_STOPLIST
        and token not in _NON_PERSON_SUBJECTS
    ]


# Street-address furniture. A venue is not named "Ave E" or "Pike St" — those
# are fragments of somebody else's address that the name pattern can slide onto
# ("Fuel House, 456 Eastlake Ave E, South Lake Union" contains both the real
# venue and the decoy "Ave E, South Lake Union").
#
# The compass words are spelled out in full as well as abbreviated: Seattle
# writes "Fenwold Avenue Northwest" as often as "Fenwold Ave NW", and with only
# the short forms listed the long ones read as a name — "Avenue Northwest"
# scored as a venue in its own right off the tail of a real one.
_ADDRESS_FURNITURE = frozenset(_STREET_SUFFIX_ALT.split('|')) | frozenset({
    'N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW', 'North', 'South', 'East', 'West',
    'Northeast', 'Northwest', 'Southeast', 'Southwest',
})


def _bare_token(token):
    """
    `token` without its possessive ending. "Seattle's" is still the place
    Seattle, and without this the possessive walked straight past the
    neighbourhood filter and made "Seattle's gyms" a named fitness spot.
    """
    return re.sub(r"['’]s$|s['’]$", "", token)


def _names_something(tokens):
    """
    True when `tokens` carry a name of their own — at least one token that is
    neither address furniture nor a bare neighbourhood. A venue is called
    "Bluebird Provisions"; "Pike St" and "Queen Anne Ave N" are a location said
    twice.
    """
    return any(_bare_token(t) not in _ADDRESS_FURNITURE
               and _bare_token(t) not in _PLACE_TOKENS
               for t in tokens)


def _validated_name(candidate):
    """The case-folded name a candidate fragment yields, or None if it names
    no place."""
    if not candidate:
        return None
    tokens = _proper_name_tokens(candidate)
    return " ".join(tokens).lower() if _names_something(tokens) else None


def _distinct_named_places(text, pattern):
    """
    Distinct validated place names matched by `pattern` in `text`.

    Candidate names are the pattern's "name" group when it has one, and all of
    its capture groups otherwise — `_TYPED_VENUE_RE` names a venue from either
    of two alternations, while `_LOCATED_PLACE_RE` also captures its anchor and
    the anchor is not a name.

    Returns a set of case-folded names, so one venue mentioned six times counts
    once and no issue can pad its way to "≥4 named places" by repetition.
    """
    named = "name" in pattern.groupindex
    names = set()
    for m in pattern.finditer(text):
        candidates = (m.group("name"),) if named else m.groups()
        for candidate in candidates:
            validated = _validated_name(candidate)
            if validated:
                names.add(validated)
    return names


# The rest of the anchor's own word; then one more capitalised token, reached
# across a space or a comma, with an optional abbreviating period.
_FINISH_TOKEN_RE = re.compile(r"[^\W\d_]*")
_NEXT_NAME_TOKEN_RE = re.compile(r"(?:[ \t]+|[ \t]*,[ \t]*)([A-Z][A-Za-z'&]*)(\.?)")
# A neighbourhood appended to an address: "…, 617 Harkness Street, Georgetown".
_NEXT_NEIGHBOURHOOD_RE = re.compile(
    r"(?:[ \t]+|[ \t]*,[ \t]*)(?:" + _NEIGHBOURHOOD_ALT + r")\b")


def _skip_street_run(text, pos):
    """
    Advance past the remainder of a street name, but only as far as its last
    piece of address FURNITURE.

    A street name can run several capitalised tokens ("789 Queen Anne Ave N"),
    so the scan has to be able to cross a word it does not recognise. What
    stops it running away is the backtrack: the position returned is the end of
    the last furniture token seen, not the end of the greedy run. So
    "Queen Anne Ave N" is consumed to the end of "N", while "Navy Strength,
    Belltown, Cafe and bar" consumes nothing — there is no furniture in it, and
    a capitalised place-type word is the venue's predicate, not its address.

    A neighbourhood always stops the run, and it has to be checked BEFORE the
    token is read: the compass words are address furniture AND the first word
    of real neighbourhood names, so "456 Eastlake Ave E, South Lake Union" ate
    "South" as furniture and left "Lake Union" — a capitalised word — sitting at
    the head of the tail where nothing anchored at ^ could match it.
    """
    last_furniture = pos
    cur = pos
    while True:
        if _NEXT_NEIGHBOURHOOD_RE.match(text, cur):
            return last_furniture              # the address ends, the area begins
        m = _NEXT_NAME_TOKEN_RE.match(text, cur)
        if not m:
            return last_furniture
        token, dot = m.group(1), m.group(2)
        # A period ends the sentence unless it is abbreviating "Ave." / "St."
        if dot and _bare_token(token) not in _ADDRESS_FURNITURE:
            return last_furniture
        cur = m.end()
        if _bare_token(token) in _ADDRESS_FURNITURE:
            last_furniture = cur


def _tail_after_anchor(text, end):
    """
    What follows a location anchor, read from the end of the WHOLE LOCATION.

    Two things sit between the anchor and the predicate that decides whether
    the name is a person or a room, and both had to be stepped over:

    1. THE REST OF THE ANCHOR'S WORD. _ADDRESS_ANCHOR deliberately stops one
       character into the street name — it matches "456 E" of "456 Eastlake Ave
       E" — because all the tier test needs is the leading digit. But that left
       `text[end:]` starting mid-word ("astlake Ave E, 41, says ..."), and the
       person cues are anchored at ^, so the veto could never fire on the
       address tier AT ALL.

    2. THE NEIGHBOURHOOD. Handbook Sec. 9 writes a location as "full address +
       neighbourhood", and so does anybody describing where a person lives:

           Aisha Coleman, 812 Harbor Street, Ballard, eats the same breakfast.

       Stopping at "Ballard" put a capitalised word at the head of the tail,
       where no person cue and no predicate slot can match — the veto fired on
       ", 41," and ", who" and on nothing that came after a neighbourhood.

    Both steps only ever consume LOCATION material: address furniture, a street
    name that ends in furniture, and a known neighbourhood. Sentence boundaries
    are never crossed, so a tail that has genuinely ended reads as "." and
    matches nothing.
    """
    pos = _FINISH_TOKEN_RE.match(text, end).end()
    while True:
        advanced = _skip_street_run(text, pos)
        neighbourhood = _NEXT_NEIGHBOURHOOD_RE.match(text, advanced)
        if neighbourhood:
            advanced = neighbourhood.end()
        if advanced == pos:
            return text[pos:]
        pos = advanced


def _located_venue_names(text, require_address=False):
    """
    Distinct venue names carrying a location anchor, with PEOPLE excluded.

    See the block comment above `_ADDRESS_ANCHOR` for why the anchor alone
    cannot decide this. A match counts when:
      * the name survives `_validated_name` (it is a name, not a location said
        twice), and
      * what follows the location is not a person — not a person cue (", 34,",
        ", who", ", says") and not a person's ordinary action verb (", eats
        the same breakfast", ", keeps his oats in a jar"); see `_person_tail`,
        and
      * its anchor is a street address — or, when a bare neighbourhood is
        allowed at all, the name's own predicate is something only a venue
        does.

    `require_address=True` enforces Handbook Sec. 9's locked minimum for a
    nutrition spot and drops the ambiguous tier entirely.
    """
    names = set()
    for m in _LOCATED_PLACE_RE.finditer(text):
        validated = _validated_name(m.group("name"))
        if not validated:
            continue
        tail = _tail_after_anchor(text, m.end())
        if _person_tail(tail):
            continue
        if m.group("anchor")[0].isdigit():          # street address: venue-grade
            names.add(validated)
        elif not require_address and _VENUE_PREDICATE_RE.match(tail):
            names.add(validated)
    return names


# Fitness keywords, and the two shapes in which one of them is actually
# ATTACHED to a name. Proximity is not attachment: a keyword anywhere within 80
# characters of a capitalised word made "The gym Marcus uses has no name on the
# door" a named fitness spot, on a sentence that says in words that the gym has
# no name. The name has to be in the same noun phrase as the keyword.
#
# The list carries the words gym NAMES are built from (barbell, athletic club,
# weightlifting) as well as the words for the room itself, because in this copy
# the type word is usually inside the name: "Rainier Barbell", "Cascade
# Athletic Club", "Fremont Hot Yoga".
_FITNESS_KEYWORD_ALT = (
    r"gyms?|studios?|run\s+clubs?|running\s+clubs?|crossfit|box|"
    r"fitness\s+cent(?:er|re)s?|yoga|pilates|barre|cycle|cycling|climbing|"
    r"dojo|YMCA|rec\s+cent(?:er|re)s?|barbell|athletic\s+clubs?|athletics|"
    r"weightlifting|powerlifting|boxing|martial\s+arts|rowing\s+clubs?|"
    r"swim\s+clubs?|track\s+clubs?|health\s+clubs?"
)

_NAMED_FITNESS_RE = re.compile(
    # "Rainier Barbell", "Fremont Hot Yoga" — name, then the keyword. The
    # `(?<![.!?])` is the same sentence-boundary guard `_TYPED_VENUE_RE` needs:
    # "He waited for Tomas Herrera. Gym staff opened at five" named a gym.
    r"\b(?P<before>" + _PROPER_NAME + r")(?<![.!?])[^\S\n]+"
     r"(?P<kw_after>(?i:" + _FITNESS_KEYWORD_ALT + r"))\b"
    # "the gym: Rainier Barbell", "a run club called Cascade Rowing".
    r"|\b(?P<kw_before>(?i:" + _FITNESS_KEYWORD_ALT + r"))\b"
     r"(?:\s*[:,]\s*|\s+(?:called|named)\s+)"
     r"(?P<after>" + _PROPER_NAME + r")"
)


def _named_fitness_spots(text):
    """
    Distinct named gyms/studios/clubs, people and unnamed rooms excluded.

    The recorded name includes the type word, because that is often the only
    part of the name that is not itself a neighbourhood ("Rainier Barbell",
    "Cascade Athletic Club"). A spot counts when the name contributes a word of
    its own, or when the type word is capitalised and therefore part of a
    proper name — which is what separates "Rainier Barbell" and "Capitol Hill
    Run Club" from "the Ballard gym", a room described by where it is.

    Names are deduplicated by prefix: one venue matched through two of its own
    words ("Rainier" + Barbell, "Rainier Barbell" + gym) is one venue.
    """
    names = set()
    for m in _NAMED_FITNESS_RE.finditer(text):
        if _PERSON_CUE_RE.match(text[m.end():]):
            continue
        if m.group("before") is not None:
            name_part, keyword = m.group("before"), m.group("kw_after")
            order = lambda n, k: n + k
        else:
            name_part, keyword = m.group("after"), m.group("kw_before")
            order = lambda n, k: k + n
        tokens = _proper_name_tokens(name_part)
        if not tokens:
            continue
        keyword_words = keyword.split()
        if not _names_something(tokens) and not keyword[0].isupper():
            continue
        names.add(" ".join(order(tokens, keyword_words)).lower())

    # Prefix dedup: drop any name that is a leading sub-phrase of another.
    return {
        name for name in names
        if not any(other != name and other.startswith(name + " ")
                   for other in names)
    }


def check_mandatory_elements(sections_dict):
    """
    Run across the full issue (all sections combined).
    Returns a dict:
        {
          "violations": [...],
          "penalty": int,
          "passed": bool,
          "element_results": {element_name: bool}
        }
    """
    full_text = "\n\n".join(sections_dict.get(s, "") for s in SECTIONS)

    violations = []
    penalty = 0

    element_results = {}

    # 1. Workout plan: rep/set notation
    rep_set_pat = re.compile(
        r'\b(\d+\s*[xX]\s*\d+|\d+\s+sets?|\d+\s+reps?|sets?\s+of\s+\d+|reps?\s+of\s+\d+)\b',
        re.IGNORECASE
    )
    has_rep_set = bool(rep_set_pat.search(full_text))
    element_results["workout_plan_rep_set"] = has_rep_set
    if not has_rep_set:
        violations.append(
            "Mandatory element missing: workout plan rep/set notation "
            "(e.g. '3x8', '4 sets', 'reps'). Penalty: -25."
        )
        penalty -= 25

    # 2. Nutrition spots: ≥4 DISTINCT named venues with a full street address.
    # Handbook Sec. 9 locks the write-up as "Name of venue + neighbourhood +
    # full address", so the address is the spec's own minimum and not a
    # heuristic — and it is the one anchor a person in this copy never carries.
    nutrition_text = sections_dict.get("Nutrition", "")
    nutrition_places = _located_venue_names(nutrition_text, require_address=True)
    nutrition_place_count = len(nutrition_places)

    has_nutrition_spots = nutrition_place_count >= 4
    element_results["nutrition_spots_4_places"] = has_nutrition_spots
    if not has_nutrition_spots:
        violations.append(
            f"Mandatory element missing: Nutrition section needs ≥4 named venues "
            f"with full street addresses (Handbook Sec. 9) "
            f"(found {nutrition_place_count} distinct). Penalty: -25."
        )
        penalty -= 25

    # 3. Local fitness spots: ≥2 DISTINCT named gyms/studios/run clubs. The
    # name has to be attached to the keyword, not merely near it — see
    # _NAMED_FITNESS_RE. Counted distinct for the same reason venues are: one
    # gym named twice is one gym.
    fitness_spots = _named_fitness_spots(full_text)

    has_fitness_spots = len(fitness_spots) >= 2
    element_results["local_fitness_spots_2"] = has_fitness_spots
    if not has_fitness_spots:
        violations.append(
            f"Mandatory element missing: ≥2 named gyms/studios/run clubs with location "
            f"(found {len(fitness_spots)} distinct). Penalty: -25."
        )
        penalty -= 25

    # 4. Location features: ≥3 DISTINCT named venues anywhere in the issue —
    # either a name carrying a place-type word ("Copper Tavern", "the bar: Navy
    # Strength") or a name with a location anchor ("Fuel House, 456 Eastlake
    # Ave E", "Navy Strength in Belltown opens at five"). A bare neighbourhood
    # is allowed here, unlike the nutrition spec, but only behind the
    # venue-predicate test — a person with a neighbourhood is not a venue.
    location_features = (
        _distinct_named_places(full_text, _TYPED_VENUE_RE)
        | _located_venue_names(full_text)
    )
    has_location_features = len(location_features) >= 3
    element_results["location_features_3_places"] = has_location_features
    if not has_location_features:
        violations.append(
            f"Mandatory element missing: ≥3 named venues with a place type or a "
            f"location anchor (found {len(location_features)}). Penalty: -25."
        )
        penalty -= 25

    passed = len(violations) == 0
    return {
        "violations": violations,
        "penalty": penalty,
        "passed": passed,
        "element_results": element_results,
    }


# ---------------------------------------------------------------------------
# Check G — workout_series hype-word blocklist (PRINCIPLES.txt Section 7)
# ---------------------------------------------------------------------------

_WORKOUT_SERIES_BLOCKLIST_PATTERNS = _build_term_patterns(WORKOUT_SERIES_BLOCKLIST)


def check_workout_series_blocklist(text):
    """
    workout_series ruleset only. PRINCIPLES.txt Section 7 bans these terms
    outright: ultimate, amazing, game-changing, level up, unlock, transform,
    crush, beast mode, no excuses.
    Penalty: -10 per hit. Hard fail: any hit (banned outright, not a
    threshold like the generic AI blocklist).
    Returns (violations, penalty, hard_fail).
    """
    violations = []
    total_hits = 0
    for term, pat in _WORKOUT_SERIES_BLOCKLIST_PATTERNS.items():
        hits = pat.findall(text)
        if hits:
            count = len(hits)
            total_hits += count
            violations.append(
                f"workout_series banned term '{term}' found {count} time(s). "
                f"Banned outright (PRINCIPLES.txt Sec. 7). Penalty: {count * -10}."
            )
    penalty = total_hits * -10
    hard_fail = total_hits > 0
    return violations, penalty, hard_fail


# ---------------------------------------------------------------------------
# Check H — workout_series exclamation-point ban (PRINCIPLES.txt Section 7)
# ---------------------------------------------------------------------------

def check_exclamation_points(text):
    """
    workout_series ruleset only. PRINCIPLES.txt Section 7 bans exclamation
    points outright.
    Penalty: -5 per instance. Hard fail: any found.
    Returns (violations, penalty, hard_fail).
    """
    violations = []
    count = text.count('!')
    if count:
        violations.append(
            f"Exclamation point found: {count} instance(s). Banned outright "
            f"under workout_series ruleset (PRINCIPLES.txt Sec. 7). Hard fail."
        )
    penalty = count * -5
    hard_fail = count > 0
    return violations, penalty, hard_fail


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_prohiblint(sections_dict, ruleset="magazine"):
    """
    Run all ProhibLint checks on a dict of {section_name: text}.

    Args:
        sections_dict: {section_name: text, ...}
        ruleset: "magazine" (default) or "workout_series". See the module
            docstring for what each ruleset does differently. Unknown
            ruleset names raise ValueError — there is no silent fallback.

    Returns (shape is fixed; additional keys may be added in future but
    these are never removed or renamed — orchestrator.py depends on them):
        {
          "sections": {
            section_name: {
              "violations": [str, ...],
              "score": int,          # starts at 100, penalties applied
              "passed": bool,
            },
            ...
          },
          "issue_level": {
            "violations": [str, ...],
            "penalty": int,
            "passed": bool,
            "element_results": {...},
          },
          "summary": {
            "total_score": int,
            "all_passed": bool,
          }
        }
    """
    if ruleset not in VALID_RULESETS:
        raise ValueError(
            f"Unknown ruleset {ruleset!r}. Valid rulesets: "
            f"{', '.join(repr(r) for r in VALID_RULESETS)}."
        )

    results = {}

    for section in SECTIONS:
        text = sections_dict.get(section, "")
        section_violations = []
        section_penalty = 0
        hard_fail = False

        # A) Em-dash — ruleset-dependent.
        # magazine: any em-dash is a hard fail (Handbook Sec. 6).
        # workout_series: one em-dash per sentence is fine; 2+ in the same
        # sentence ("stacked") is a hard fail (PRINCIPLES.txt Sec. 7).
        if ruleset == "workout_series":
            v, p, hf = check_em_dash_workout_series(text)
        else:
            v, p, hf = check_em_dash(text)
        section_violations.extend(v)
        section_penalty += p
        hard_fail = hard_fail or hf

        # B) AI blocklist — same generic AI-vocab check for both rulesets.
        v, p, hf = check_ai_blocklist(text)
        section_violations.extend(v)
        section_penalty += p
        hard_fail = hard_fail or hf

        # C) Cold-open
        v, p, _ = check_cold_open(text)
        section_violations.extend(v)
        section_penalty += p

        # D) Second-person — ruleset-dependent.
        # magazine: the Handbook's outright ban on direct address.
        # workout_series: PRINCIPLES.txt Sec. 6-7 endorse direct address; only
        # prescriptive/predictive coaching is flagged.
        v, p, _ = check_second_person(text, ruleset=ruleset)
        section_violations.extend(v)
        section_penalty += p

        # E) Word count — magazine only. workout_series is governed by
        # CharLint's exact character-count locks instead; skip entirely.
        if ruleset == "magazine":
            v, p, hf = check_word_count(section, text)
            section_violations.extend(v)
            section_penalty += p
            hard_fail = hard_fail or hf

        # G/H) workout_series-only PRINCIPLES.txt Sec. 7 bans: hype words
        # and exclamation points, both banned outright.
        if ruleset == "workout_series":
            v, p, hf = check_workout_series_blocklist(text)
            section_violations.extend(v)
            section_penalty += p
            hard_fail = hard_fail or hf

            v, p, hf = check_exclamation_points(text)
            section_violations.extend(v)
            section_penalty += p
            hard_fail = hard_fail or hf

        score = max(0, 100 + section_penalty)
        passed = (not hard_fail) and (score >= 70)

        results[section] = {
            "violations": section_violations,
            "score": score,
            "passed": passed,
        }

    # F) Issue-level mandatory elements — unchanged, applies to both rulesets
    issue_level = check_mandatory_elements(sections_dict)

    # Compute summary
    total_score = sum(r["score"] for r in results.values()) + issue_level["penalty"]
    all_passed = all(r["passed"] for r in results.values()) and issue_level["passed"]

    return {
        "sections": results,
        "issue_level": issue_level,
        "summary": {
            "total_score": total_score,
            "all_passed": all_passed,
        },
    }
