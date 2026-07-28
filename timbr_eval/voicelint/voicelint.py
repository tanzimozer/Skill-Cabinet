
# voicelint.py — VoiceLint module for TIMBR eval harness
# Lexical fingerprint scoring per section voice register. MVP: no embeddings.

import re
from typing import NamedTuple

from voice_config import (
    SECTION_VOICE_MAP,
    ATHLETIC_ATTRIBUTION, ATHLETIC_POSITIVE, ATHLETIC_POSITIVE_CAPS, ATHLETIC_NEGATIVE,
    ATHLETIC_SOURCING, PRONOUN_ATTRIBUTION, REPORTING_MACHINERY,
    ATHLETIC_EXCLAMATION, ATHLETIC_EXCLAMATION_ALLOWANCE,
    FLAG_LABELS,
    PEOPLE_POSITIVE, PEOPLE_ACCESS, PEOPLE_NEGATIVE, PEOPLE_NEGATIVE_CAPS,
    PEOPLE_NEGATIVE_SOURCED,
    FITT_POSITIVE,
    FITT_POSITIVE_PARA_MAX, FITT_POSITIVE_KICKER_MAX, FITT_LONG_PARA_MAX,
    FITT_STACCATO_RATIO,
    FITT_STRONG_OPINION, FITT_DECLARATIVE, FITT_DATA_LEAD,
    FITT_NEGATIVE, FITT_NEGATIVE_CAPS,
    SCORE_START, POSITIVE_HIT, NEGATIVE_HIT, STRUCTURAL_HIT, REGISTER_GATE,
    PASS_THRESHOLD, DENSITY_BASELINE_WORDS,
    CROSS_CONTAMINATION_MARGIN, CROSS_CONTAMINATION_PENALTY,
)

# Section names absent from SECTION_VOICE_MAP fall back to this register.
DEFAULT_VOICE = "athletic"

# Named-person detection window, in words from the top of the section.
PERSON_WINDOW_WORDS = 50


def _word_count(text):
    return len(text.split())


def _sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def _paragraphs(text):
    return [p.strip() for p in text.split('\n\n') if p.strip()]


def _count_matches(patterns, text, flags=re.IGNORECASE):
    total = 0
    hits = []
    for pat in patterns:
        found = re.findall(pat, text, flags)
        total += len(found)
        if found:
            hits.append({"pattern": pat, "count": len(found)})
    return total, hits


def _clamp(score):
    return max(0, min(SCORE_START, score))


def _gate(passed):
    """The register's defining test: +REGISTER_GATE pass, -REGISTER_GATE fail."""
    return REGISTER_GATE if passed else -REGISTER_GATE


def _flag_name(pattern):
    """
    Plain-language name for a marker. Flags reach an editor through the
    orchestrator's violations list, so a regex must never be the thing a writer
    reads. The labels live beside the patterns in voice_config.
    """
    return FLAG_LABELS.get(pattern, pattern)


# ─────────────────────────────────────────────────────────────────────────────
# Named-person detection
#
# History of this function is a history of enumeration failing in both
# directions.
#
#   v1  re.search(r'[A-Z][a-z]+\s[A-Z][a-z]+', ...) — ANY Titlecase bigram. It
#       fired on "At Cascade the room" and "South Lake Union is quiet", so in a
#       product saturated with Seattle place names the people register collected
#       a free +REGISTER_GATE on essentially every section.
#   v2  a Titlecase bigram followed by a cue from a CLOSED 23-VERB LIST. That
#       inverted the failure: it missed every real person doing anything the
#       list did not happen to contain. "Devon Ashworth carries the cones out",
#       "Priya Raman cooks the same thing every Sunday", "Renata Boyle coaches
#       the 6am group" were all invisible, and each miss costs the people
#       register 2 * REGISTER_GATE — the largest single term in the scale.
#
# The set of things a person can DO is open. It cannot be enumerated and every
# attempt to enumerate it is a list that today's copy has already outgrown. The
# sets that must be EXCLUDED, on the other hand, are genuinely closed classes of
# English: copulas and auxiliaries, function words, and the irregular past
# forms. So the predicate test below is an OPEN class for the action and CLOSED
# classes only for the exclusions.
#
# A person is a Titlecase bigram that
#   (a) does not open or close with sentence furniture, and either
#   (b) carries a PERSON-ONLY cue — age apposition ("Daniel Park, 45,"), a
#       directly-adjacent reporting verb ("Marcus Webb says"), or ", who".
#       Nothing but a person is written this way, so these override the
#       place/organisation filter, which matters because real surnames collide
#       with place words (Park, Hill, Rivers, Lake); or
#   (c) survives the place/organisation filter AND takes a person predicate:
#       an open-class finite action verb, a possessive, or a role apposition.
#
# Everything here is deliberately case-sensitive. The capital IS the name
# signal.
# ─────────────────────────────────────────────────────────────────────────────

_NAME_BIGRAM = re.compile(r'\b([A-Z][a-z]{1,14})\s+([A-Z][a-z]{1,14})\b')

# Capitalised tokens that open phrases and sentences but never a forename.
_NON_NAME_TOKENS = {
    'The', 'A', 'An', 'At', 'In', 'On', 'Of', 'For', 'From', 'With', 'By', 'To',
    'And', 'But', 'Or', 'So', 'Then', 'Than', 'As', 'Into', 'Over', 'Under',
    'This', 'That', 'These', 'Those', 'There', 'Here', 'It', 'Its', 'They',
    'Their', 'His', 'Her', 'She', 'He', 'We', 'Our', 'You', 'Your', 'My', 'I',
    'Some', 'Every', 'Each', 'Most', 'Many', 'Both', 'All', 'Another', 'Other',
    'Any', 'No', 'Not', 'Nothing', 'One', 'Two', 'Three', 'Four', 'Five', 'Six',
    'Seven', 'Eight', 'Nine', 'Ten', 'First', 'Second', 'Third', 'Last', 'Next',
    'When', 'While', 'After', 'Before', 'Since', 'Because', 'If', 'Though',
    'Although', 'However', 'Still', 'Yet', 'Despite', 'Meanwhile', 'Instead',
    'What', 'Where', 'Why', 'How', 'Who', 'Whose', 'Which',
    'Now', 'Today', 'Tomorrow', 'Yesterday', 'Later', 'Early', 'Late', 'Just',
    'Even', 'Only', 'More', 'Less', 'Much', 'Very', 'Once', 'Again', 'Almost',
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December',
}

# ─────────────────────────────────────────────────────────────────────────────
# Place / organisation exclusions, held at two different grains
#
# _PLACE_TOKENS is a list of CATEGORY NOUNS and contains no proper nouns at all.
# It answers one question: does this Titlecase bigram name a KIND of place or
# organisation rather than a person? Lake, Park, Club, Institute, Rowing,
# Collective. A category noun is never a forename and (Park, Hill, Field aside,
# which the person-only cues rescue) rarely a surname.
#
# _PLACE_BIGRAMS holds the multi-word Seattle proper names whose tokens are NOT
# category nouns, recorded as WHOLE bigrams.
#
# WHY THAT SPLIT, and why this list disagrees with prohiblint.SEATTLE_PLACE_NAMES
# on "Cascade". The two lists answer different questions at different grains.
# prohiblint's cold-open test only ever sees ONE leading capitalised token, so it
# needs a token-level gazetteer and must record "Cascade" as a place. This
# detector always sees a bigram, so it can be more precise, and being more
# precise matters: half the Seattle gazetteer doubles as ordinary surnames
# (Madison, Jefferson, Thomas, Denny, Harrison, Sunset, Cascade). Importing that
# gazetteer token-by-token would make "Cascade" a place everywhere and blind the
# people register to anyone called Cascade or Madison. So proper names are
# excluded only as complete bigrams ("Queen Anne", "West Seattle"), which costs
# nothing on surnames, and the organisation case is handled by category nouns
# instead.
#
# "Cascade Rowing is the older club" — the reported false positive — is rejected
# twice over: "Rowing" is an organisation category noun, and "is the" is the
# definitional copula form that names things rather than introducing people.
#
# The modules stay independent. Neither imports the other, and the disagreement
# between the two lists is a deliberate consequence of the different jobs.
# ─────────────────────────────────────────────────────────────────────────────
_PLACE_TOKENS = {
    # geography
    'Lake', 'Union', 'Hill', 'Hills', 'Park', 'Bay', 'Beach', 'Valley',
    'Heights', 'Point', 'Ridge', 'Creek', 'Sound', 'Island', 'County',
    'Harbor', 'Harbour', 'Trail', 'Locks', 'Falls', 'Cove', 'Inlet',
    # streets and structures
    'Street', 'Avenue', 'Road', 'Boulevard', 'Way', 'Place', 'Terrace',
    'Square', 'Bridge', 'Station', 'Tower', 'Building', 'Yard', 'Works',
    'Pier', 'Dock', 'Commons', 'Garden', 'Gardens', 'Plaza',
    # venues and premises
    'Stadium', 'Arena', 'Track', 'Court', 'Field', 'Hall', 'House', 'Room',
    'Floor', 'Studio', 'Gym', 'Lab', 'Laboratory', 'Center', 'Centre',
    'Complex', 'Bar', 'Cafe', 'Kitchen', 'Lodge', 'Inn', 'Hotel', 'Tavern',
    'Brewery', 'Roasters', 'Market', 'Shop', 'Store', 'Clinic',
    # organisations and their category words
    'Club', 'Company', 'Group', 'Collective', 'Project', 'Program', 'Programme',
    'Series', 'Journal', 'Review', 'Press', 'Institute', 'Academy', 'University',
    'College', 'School', 'District', 'City', 'Village', 'Foundation', 'Society',
    'Association', 'League', 'Team', 'Squad', 'Partners', 'Associates', 'Media',
    'Council', 'Board', 'Trust', 'Network', 'Alliance',
    # activity words that name clubs and facilities, never people
    'Sports', 'Sport', 'Athletic', 'Athletics', 'Fitness', 'Health', 'Science',
    'Sciences', 'Performance', 'Rowing', 'Running', 'Cycling', 'Boxing',
    'Climbing', 'Swimming', 'Lifting', 'Barbell', 'Strength', 'Conditioning',
    'Training', 'Nutrition', 'Recovery', 'Wellness', 'Rehab', 'Physio',
    'Springs', 'Marathon', 'Relay', 'Classic', 'Open',
}

# Multi-word Seattle proper names whose tokens are NOT category nouns, so the
# list above cannot reach them. Held as whole bigrams on purpose: "Queen" and
# "Anne" and "Cal" and "Seattle" all remain usable as personal names on their
# own. Transcribed from the city, not imported from prohiblint.
_PLACE_BIGRAMS = frozenset({
    'Queen Anne', 'Lower Queen', 'West Seattle', 'South Seattle',
    'North Seattle', 'East Seattle', 'Cal Anderson', 'Maple Leaf',
    'Alki Point', 'Denny Triangle', 'Yesler Terrace', 'Madison Valley',
    'Union Bay', 'Foster Island', 'Mercer Island', 'Bainbridge Island',
})

# Cues that ONLY a person takes. These override the place/organisation filter,
# which matters because real surnames collide with category nouns: Park, Hill,
# Field, Rivers, Lake, Marsh.
_PERSON_ONLY_CUE = re.compile(
    r"""^(?:
          ,\s*\d{1,2}\s*,                       # ", 45,"  age apposition
        | \s+(?:is|was)\s+\d{1,2}\s*
              (?:,|\s+years\s+old)              # "is 31," / "is 31 years old"
        | \s+(?:says|said|explains|explained|notes|noted|adds|added|argues
              |argued|told|recalls|remembers|laughs|laughed|smiles|admits
              |insists|replies)\b               # directly-adjacent reporting verb
        | ,\s*who(?:se)?\b                      # ", who ..." — English reserves
                                                # who/whose for people; places
                                                # and organisations take which
    )""",
    re.VERBOSE,
)

# ── CLOSED class 1: copulas and auxiliaries ──────────────────────────────────
# "<X> is <noun phrase>" is a definition, not an action: "Cascade Rowing is the
# older club", "South Lake Union is quiet". A copula only carries a person when
# it carries a progressive ("Carmen Ruiz is standing in her kitchen"), which the
# progressive branch handles separately. This class is small and it does not
# grow, which is exactly what the set of ACTION verbs is not.
_COPULA_VERBS = frozenset({
    'is', 'was', 'are', 'were', 'has', 'have', 'had', 'does', 'did', 'do',
    'seems', 'appears', 'remains', 'becomes', 'became', 'means', 'stays',
    'exists', 'been', 'being',
})

# ── CLOSED class 2: function words ───────────────────────────────────────────
# Prepositions, conjunctions, determiners, pronouns and bare adverbs. A name
# followed by one of these has not yet reached its verb.
_FUNCTION_WORDS = frozenset("""
    of in on at to for with from by about into onto over under after before
    during since until through between among against without within across
    behind beyond near off out up down per via like than as toward towards
    upon along beside besides despite except
    and or but so yet nor if because while when where whether though although
    unless whenever wherever
    the a an this that these those his her their its our your my
    it he she they we you i who whom whose which what there here
    not never always also still already just only even too very really often
    sometimes again once now then later soon perhaps indeed instead thus yes
    more less most least well quite rather almost nearly ever
    will would can could may might must shall should
""".split())

# ── CLOSED class 3: the irregular past forms ─────────────────────────────────
# English irregular pasts are a closed class: the list is finite and it does not
# take new members, which is precisely why enumerating THEM is safe where
# enumerating action verbs was not. Regular pasts and third-person presents are
# handled morphologically and need no list.
_IRREGULAR_PAST = frozenset("""
    went came took made gave got saw said told kept left ran sat stood wrote
    spoke grew knew found held brought built bought sold drove won lost put cut
    set met felt meant sent spent taught thought caught began broke chose drew
    fell flew forgot hid led lay paid read rode rose shot slept sang swam threw
    understood woke wore quit drank ate wrote rebuilt kept swore stuck struck
    hung dug bent lent bound wound sank rang beat fed fled hit hurt let lit
    shook shrank slid spread stole swept swung tore wove
""".split())

# A copula or auxiliary DOES introduce a person, in every construction except
# one: "<X> is the <noun>" is the definitional form that names things.
#     "Carmen Ruiz is standing in her kitchen"   person (progressive)
#     "Marina Vasilenko has coached the group"   person (perfect)
#     "Marcus Webb is a strength coach"          person (role nominal)
#     "Ruben Castellanos is behind the bar"      person (locative)
#     "Cascade Rowing is the older club"         NOT a person
#     "Iron Mile is the best gym in the city"    NOT a person
# A following capital is excluded for the same reason: "Sound Athletic is
# Seattle's oldest room" names a room, not a person.
_COPULA_PERSON_RE = re.compile(
    r"^\s+(?:is|was|are|were|has|have|had)\s+(?!the\b)(?![A-Z])[a-z0-9]")

# The first lowercase token after the name, with an optional adverb in front of
# it. This is the OPEN slot: no verb list, the token is judged by morphology and
# by the closed exclusion classes. Group 2 is the direct-object frame.
_PREDICATE_SLOT_RE = re.compile(
    r"^\s+(?:already\s+|still\s+|now\s+|never\s+|always\s+|often\s+|also\s+"
    r"|[a-z]+ly\s+)?([a-z]{2,})\b(\s+(?:the|a|an|his|her|their|its|two|three"
    r"|four|five|six|seven|eight|nine|ten|every|each|both|another|one)\b)?")

_POSSESSIVE_RE = re.compile(r"^(?:'s|’s)\s+[a-z]")
_ROLE_APPOSITION_RE = re.compile(r"^,\s*(?:a|an|the)\s+[a-z]")


def _is_action_verb(token, has_object):
    """
    True when `token` — the first lowercase word after a Titlecase bigram — is a
    finite ACTION verb rather than a copula, an auxiliary, a function word or a
    noun. The class of action verbs is open, so the test is morphological plus
    one syntactic frame, never a verb list:

      * third-person present: ends in "s"        (carries, cooks, coaches, pours)
      * regular past:         ends in "ed"       (carried, cooked, supervised)
      * irregular past:       closed class above (wrote, kept, ran)
      * anything else that takes a direct object (transitive frame), which
        catches irregular forms the closed class has not heard of. "-ing" is
        excluded from that frame because it is a participle, not a finite verb:
        "Ballard Commons carrying two folding tables" is a place with a load,
        not a person.
    """
    if token in _COPULA_VERBS or token in _FUNCTION_WORDS:
        return False
    if token in _IRREGULAR_PAST:
        return True
    if token.endswith('ing'):
        return False
    if token.endswith('s') and not token.endswith('ss'):
        return True
    if token.endswith('ed') and len(token) > 3:
        return True
    return bool(has_object)


def _person_predicate(rest):
    """True when what follows a Titlecase bigram is a person doing something."""
    if _POSSESSIVE_RE.match(rest) or _ROLE_APPOSITION_RE.match(rest):
        return True
    # The copula branch is tried FIRST. "is" also fills the predicate slot, and
    # _is_action_verb would otherwise have to decide whether "is" is an action
    # verb on morphology alone (it ends in "s"), which is exactly the judgement
    # the closed copula class exists to take away from it.
    if _COPULA_PERSON_RE.match(rest):
        return True
    m = _PREDICATE_SLOT_RE.match(rest)
    if m and _is_action_verb(m.group(1), bool(m.group(2))):
        return True
    return False


def _named_person(text) -> bool:
    """True when `text` contains a plausible named PERSON (not a place)."""
    for m in _NAME_BIGRAM.finditer(text):
        first, second = m.group(1), m.group(2)
        if first in _NON_NAME_TOKENS or second in _NON_NAME_TOKENS:
            continue
        rest = text[m.end():]
        if _PERSON_ONLY_CUE.match(rest):
            return True
        if first in _PLACE_TOKENS or second in _PLACE_TOKENS:
            continue
        if f"{first} {second}" in _PLACE_BIGRAMS:
            continue
        if _person_predicate(rest):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Affinity: two channels, because the section and the sentence are not the same
# unit of evidence
#
# Each register scores a section as a *signed adjustment* to SCORE_START rather
# than as a pre-clamped absolute. The delta is the discriminating signal: two
# sections can both clamp to 100 while carrying wildly different register
# fingerprints, so anything that compares registers against each other (i.e.
# cross-contamination) must compare deltas, never clamped scores.
#
# All three deltas share one origin and one unit system:
#     delta = lexical evidence + structural evidence + register gate
# Every register has exactly one gate, always evaluated, worth +/-REGISTER_GATE.
# That is what makes a margin mean the same thing in each register: a
# register-neutral paragraph fails all three gates and scores the same in all
# three, so its margins are zero instead of people +5 / athletic 0 / fitt -10.
#
# WHY TWO CHANNELS. Cross-contamination compares registers per 100 words, and
# the old density divided the WHOLE delta by length. But the terms in a delta do
# not all behave the same way as a section gets longer:
#
#   per-occurrence  lexical markers, data-led sentences, over-long paragraphs.
#                   These accrue with length, so dividing by length is exactly
#                   right and leaves them scale-free.
#   section-level   the register GATE, the earned-rhythm bonus, the opinionated
#                   kicker, the declarative-openings ratio. These are evaluated
#                   ONCE for the whole section and are already independent of
#                   length. Dividing them by length is not a normalisation, it
#                   is a decay: the +/-10 gate contributed 10 points of margin at
#                   100 words and 1.4 at 700, so a section written in the wrong
#                   register lost its lead purely by being long enough to ship.
#                   At the lengths the ruleset actually requires (400-1200 words
#                   per prohiblint.WORD_COUNT_RANGES) the gates had effectively
#                   switched off, and 12 of 12 cross-register fixtures stopped
#                   firing once padded to 900 words.
#
# So the two channels are normalised differently and only the per-occurrence one
# is divided by length. The result is exactly scale-invariant under duplication:
# concatenate a section with itself and every density stays identical, because
# the per-occurrence channel and the word count both double while the
# section-level channel is unchanged.
#
# The RAW delta — what voice_score is built from — is the plain sum of the two
# channels and is unaffected by any of this. The pass bar is unchanged.
# ─────────────────────────────────────────────────────────────────────────────

_PRONOUN_ATTRIBUTION_RE = re.compile(PRONOUN_ATTRIBUTION)


def _reported_by_pronoun(text):
    """
    How many times the section attributes BY PRONOUN to a source it has named.

    Zero unless the section is licensed, and the licence is a conjunction:

      1. it carries the MACHINERY OF ASKING — a non-response frame, a provenance
         frame, a reported hedge or an "according to". A profile has no occasion
         to write any of those, because its authority is access rather than a
         source it had to approach. This is the register evidence.
      2. it anchors a NAMED PERSON in the same opening window the people gate
         uses, so the pronoun has an antecedent. This is the coreference half:
         "she says" is only de-duplication if there is a name to de-duplicate.

    Neither half is sufficient. (2) alone is the people gate's own test and
    licensing on it hands a wrong-register profile the athletic register — see
    THE RESIDUAL HOLE in voice_config for the measurement. (1) alone would count
    a pronoun with nothing behind it.

    A section that passes both is doing reporting and de-duplicating a name, and
    charging it for the second is charging it for a copy-editing convention.
    """
    if not text.strip():
        return 0
    if not any(re.search(p, text) for p in REPORTING_MACHINERY):
        return 0
    window = ' '.join(text.split()[:PERSON_WINDOW_WORDS])
    if not _named_person(window):
        return 0
    return len(_PRONOUN_ATTRIBUTION_RE.findall(text))


class Affinity(NamedTuple):
    """One register's verdict on one section, split by unit of evidence."""
    section_level: int      # evaluated once per section; never scaled by length
    per_occurrence: int     # accrues with length; scaled to DENSITY_BASELINE_WORDS
    flags: list
    details: list

    @property
    def delta(self):
        return self.section_level + self.per_occurrence


def _athletic_affinity(text):
    section_level = 0
    per_occurrence = 0
    flags = []
    details = []

    pos_count, _ = _count_matches(ATHLETIC_POSITIVE, text)
    caps_count, _ = _count_matches(ATHLETIC_POSITIVE_CAPS, text, 0)
    pos_count += caps_count
    if pos_count:
        per_occurrence += pos_count * POSITIVE_HIT
        details.append(f"athletic positive markers x{pos_count} ({pos_count * POSITIVE_HIT:+d})")

    # SOURCING — the register's per-occurrence vocabulary. Case-SENSITIVE, like
    # the caps patterns above and for the same reason: these encode proper nouns
    # and a capitalised exclusion list.
    #
    # This counts what the gate below merely tests, plus the reporting frames
    # that have no counterpart in the other two registers. The two channels are
    # answering different questions — "does this attribute at all" versus "how
    # continuously" — and only the second one can separate a report from a
    # profile, because both attribute and only one of them keeps doing it. See
    # ATHLETIC_SOURCING in voice_config for why this is not double counting and
    # for the asymmetry with PEOPLE_POSITIVE that it repairs.
    src_count, _ = _count_matches(ATHLETIC_SOURCING, text, 0)
    # Attribution the section makes by pronoun to a source it has already named,
    # in a section that has independently shown it does reporting. Same unit as
    # any other sourcing hit — see _reported_by_pronoun and PRONOUN_ATTRIBUTION.
    pron_src = _reported_by_pronoun(text)
    src_count += pron_src
    if src_count:
        per_occurrence += src_count * POSITIVE_HIT
        details.append(f"sourcing markers x{src_count} ({src_count * POSITIVE_HIT:+d})")

    neg_count, neg_hits = _count_matches(ATHLETIC_NEGATIVE, text)
    if neg_count:
        per_occurrence += neg_count * NEGATIVE_HIT
        details.append(f"athletic negative markers x{neg_count} ({neg_count * NEGATIVE_HIT:+d})")
    for h in neg_hits:
        flags.append(f"Athletic negative marker: {_flag_name(h['pattern'])} ({h['count']}x)")

    # GATE: reported copy attributes its claims AND does not shout.
    #
    # Both halves are necessary and the conjunction is the point. Attribution
    # alone made the gate a +REGISTER_GATE credit that a section could spend on
    # hype: a Culture section with one attributed quote and six exclamation
    # points came to -18 + 10 = -8 and passed at 92, where the pre-repair scale
    # (attribution as a +2 marker) failed it at 64. Six exclamation points are
    # not reported copy however scrupulously the quotes are sourced, and under
    # the magazine ruleset VoiceLint is the only thing that checks them at all.
    #
    # The allowance is one, because an exclamation point inside a quotation is
    # the subject's voice and legitimately appears in reported copy. Two is the
    # writer's own voice raised, which this register does not do.
    if text.strip():
        # Case-SENSITIVE on purpose: the pattern encodes proper nouns and a
        # capitalised exclusion list. See ATHLETIC_ATTRIBUTION in voice_config.
        # A licensed pronoun attribution satisfies the gate too. The gate asks
        # "does this section attribute a claim to an identified source at all?"
        # and telling a properly reported feature that NOTHING in it is
        # attributed, because it wrote "she says" instead of repeating a
        # surname, is a false statement about the copy. The licence is what
        # keeps this off a profile: a profile carries no machinery of asking, so
        # its "she says" still earns nothing here. See _reported_by_pronoun.
        attributed = bool(re.search(ATHLETIC_ATTRIBUTION, text)) or pron_src > 0
        shouts = len(re.findall(ATHLETIC_EXCLAMATION, text))
        gate_passed = attributed and shouts <= ATHLETIC_EXCLAMATION_ALLOWANCE
        section_level += _gate(gate_passed)
        if gate_passed:
            details.append(f"gate: claims are attributed to a source ({_gate(True):+d})")
        elif not attributed:
            details.append(f"gate: nothing in the section is attributed ({_gate(False):+d})")
            flags.append("No sourced attribution: the athletic register reports, it does not assert")
        else:
            details.append(
                f"gate: attributed, but {shouts} exclamation points is not reported "
                f"copy ({_gate(False):+d})")
            flags.append(
                f"Attributed but shouting: {shouts} exclamation points "
                f"(allowance {ATHLETIC_EXCLAMATION_ALLOWANCE}); the athletic register reports")

    # Structural: sentence length variance (earned rhythm). Section-level: it is
    # a property of the whole section's rhythm, evaluated once.
    sents = _sentences(text)
    # The length guard is implied by the test below — two short and two long
    # sentences cannot exist in fewer than four — so it is an early-out, not a
    # condition. Mutating it is an equivalent mutant and no test can kill it.
    if len(sents) >= 4:
        lengths = [len(s.split()) for s in sents]
        short = sum(1 for l in lengths if l < 8)
        long_ = sum(1 for l in lengths if l > 20)
        if short >= 2 and long_ >= 2:
            section_level += STRUCTURAL_HIT
            details.append(f"earned rhythm: short + long sentence mix ({STRUCTURAL_HIT:+d})")

    return Affinity(section_level, per_occurrence, flags, details)


def _people_affinity(text):
    section_level = 0
    per_occurrence = 0
    flags = []
    details = []

    pos_count, _ = _count_matches(PEOPLE_POSITIVE, text)
    if pos_count:
        per_occurrence += pos_count * POSITIVE_HIT
        details.append(f"people positive markers x{pos_count} ({pos_count * POSITIVE_HIT:+d})")

    neg_count, neg_hits = _count_matches(PEOPLE_NEGATIVE, text, re.IGNORECASE | re.MULTILINE)
    caps_neg, caps_hits = _count_matches(PEOPLE_NEGATIVE_CAPS, text, re.MULTILINE)
    # Borrowed authority. Case-SENSITIVE, and deliberately the SOURCED patterns
    # rather than the bare reporting verbs: a profile's "she says" is its
    # subject's own voice and PEOPLE_ACCESS counts it as access. See
    # PEOPLE_NEGATIVE_SOURCED in voice_config for the measurement that forced
    # this — sourcing density is the only marker family that separates a
    # reported feature about a person from a profile of one.
    src_neg, src_hits = _count_matches(PEOPLE_NEGATIVE_SOURCED, text, 0)
    # The mirror of the athletic credit, and it has to be the mirror: the axis is
    # only resolvable because sourcing is counted on both sides (see
    # PEOPLE_NEGATIVE_SOURCED). Crediting the athletic register for a licensed
    # pronoun attribution without debiting the people register would count the
    # evidence once and leave half the separation on the table.
    pron_src = _reported_by_pronoun(text)
    if pron_src:
        src_neg += pron_src
        src_hits = src_hits + [{"pattern": PRONOUN_ATTRIBUTION, "count": pron_src}]
    neg_count += caps_neg + src_neg
    neg_hits = neg_hits + caps_hits + src_hits
    if neg_count:
        per_occurrence += neg_count * NEGATIVE_HIT
        details.append(f"people negative markers x{neg_count} ({neg_count * NEGATIVE_HIT:+d})")
    for h in neg_hits:
        flags.append(f"People negative marker: {_flag_name(h['pattern'])} ({h['count']}x)")

    # GATE: a named human anchor in the opening window WHOM THE SECTION GIVES
    # THE READER ACCESS TO. Both halves are necessary. Reported copy names its
    # sources in its first fifty words as a matter of routine, so a name-only
    # gate paid the people register +REGISTER_GATE on ordinary athletic
    # reporting and left the two registers inside 3 points of each other across
    # 900 words. A name is not a profile. See PEOPLE_ACCESS in voice_config.
    if text.strip():
        window = ' '.join(text.split()[:PERSON_WINDOW_WORDS])
        anchored = _named_person(window)
        access_count, _ = _count_matches(PEOPLE_ACCESS, text)
        gate_passed = anchored and access_count > 0
        section_level += _gate(gate_passed)
        if gate_passed:
            details.append(
                f"gate: named person in opening {PERSON_WINDOW_WORDS} words, and the "
                f"section gives access to them ({access_count} markers) ({_gate(True):+d})")
        elif not anchored:
            details.append(f"gate: no named person in opening {PERSON_WINDOW_WORDS} words ({_gate(False):+d})")
            flags.append(f"No named person in opening {PERSON_WINDOW_WORDS} words")
        else:
            details.append(
                f"gate: a named person, but the section is about a subject rather "
                f"than about them ({_gate(False):+d})")
            flags.append(
                "A named person but no profile access: this register hands the reader "
                "the person (age, home, routine, their own voice), not just their name")

    return Affinity(section_level, per_occurrence, flags, details)


def _fitt_affinity(text):
    section_level = 0
    per_occurrence = 0
    flags = []
    details = []
    paras = _paragraphs(text)

    pos_count, _ = _count_matches(FITT_POSITIVE, text)
    if pos_count:
        per_occurrence += pos_count * POSITIVE_HIT
        details.append(f"fitt positive markers x{pos_count} ({pos_count * POSITIVE_HIT:+d})")

    # GATE: staccato. Majority of paragraphs <= FITT_POSITIVE_PARA_MAX words.
    # A ratio over the whole section, so section-level by construction.
    if paras:
        short_paras = sum(1 for p in paras if _word_count(p) <= FITT_POSITIVE_PARA_MAX)
        ratio = short_paras / len(paras)
        staccato = ratio >= FITT_STACCATO_RATIO
        section_level += _gate(staccato)
        if staccato:
            details.append(
                f"gate: staccato, {ratio:.0%} of paragraphs <= {FITT_POSITIVE_PARA_MAX} "
                f"words ({_gate(True):+d})")
        else:
            details.append(
                f"gate: not staccato, only {ratio:.0%} of paragraphs <= "
                f"{FITT_POSITIVE_PARA_MAX} words ({_gate(False):+d})")
            flags.append(f"Only {ratio:.0%} of paragraphs are staccato (<={FITT_POSITIVE_PARA_MAX} words)")

        # Long paragraph penalty — one negative marker per offending paragraph,
        # so it accrues with length.
        for p in paras:
            if _word_count(p) > FITT_LONG_PARA_MAX:
                per_occurrence += NEGATIVE_HIT
                details.append(
                    f"paragraph exceeds {FITT_LONG_PARA_MAX} words "
                    f"({_word_count(p)} words) ({NEGATIVE_HIT:+d})")
                flags.append(f"Paragraph exceeds {FITT_LONG_PARA_MAX} words ({_word_count(p)} words)")

    # Structural: opinionated kicker. One closing sentence per section.
    sents = _sentences(text)
    if sents:
        last = sents[-1]
        if _word_count(last) <= FITT_POSITIVE_KICKER_MAX:
            kicker_match, _ = _count_matches(FITT_STRONG_OPINION, last)
            if kicker_match:
                section_level += STRUCTURAL_HIT
                details.append(
                    f"opinionated kicker: short closing sentence + strong opinion ({STRUCTURAL_HIT:+d})")

    # Structural: declarative openings. A ratio over the whole section.
    declarative_count = 0
    for p in paras:
        para_sents = _sentences(p)
        first_sent = para_sents[0] if para_sents else ''
        if re.match(FITT_DECLARATIVE, first_sent):
            declarative_count += 1
    if paras and declarative_count / len(paras) >= 0.5:
        section_level += STRUCTURAL_HIT
        details.append(
            f"declarative openings on {declarative_count}/{len(paras)} paragraphs ({STRUCTURAL_HIT:+d})")

    # Structural: data-led sentences — one per sentence, so per-occurrence.
    data_count = sum(1 for s in sents if re.match(FITT_DATA_LEAD, s.strip()))
    if data_count:
        per_occurrence += data_count * STRUCTURAL_HIT
        details.append(f"data-led sentences x{data_count} ({data_count * STRUCTURAL_HIT:+d})")

    # Negatives
    neg_count, neg_hits = _count_matches(FITT_NEGATIVE, text, re.IGNORECASE | re.MULTILINE)
    caps_neg, caps_hits = _count_matches(FITT_NEGATIVE_CAPS, text, re.MULTILINE)
    neg_count += caps_neg
    neg_hits = neg_hits + caps_hits
    if neg_count:
        per_occurrence += neg_count * NEGATIVE_HIT
        details.append(f"fitt negative markers x{neg_count} ({neg_count * NEGATIVE_HIT:+d})")
    for h in neg_hits:
        flags.append(f"Fitt negative marker: {_flag_name(h['pattern'])} ({h['count']}x)")

    return Affinity(section_level, per_occurrence, flags, details)


AFFINITY_SCORERS = {
    "athletic": _athletic_affinity,
    "people": _people_affinity,
    "fitt": _fitt_affinity,
}


def score_athletic(text):
    aff = _athletic_affinity(text)
    return _clamp(SCORE_START + aff.delta), aff.flags


def score_people(text):
    aff = _people_affinity(text)
    return _clamp(SCORE_START + aff.delta), aff.flags


def score_fitt(text):
    aff = _fitt_affinity(text)
    return _clamp(SCORE_START + aff.delta), aff.flags


SCORERS = {
    "athletic": score_athletic,
    "people": score_people,
    "fitt": score_fitt,
}


def voice_affinity(text) -> dict:
    """
    Signed affinity delta per register: {voice_name: delta}.

    Positive = the prose carries that register's markers. Unlike voice_score
    these are NOT clamped, so they stay comparable across registers.
    """
    return {name: fn(text).delta for name, fn in AFFINITY_SCORERS.items()}


def _density(aff, words):
    """
    One register's affinity per DENSITY_BASELINE_WORDS words.

    Only the per-occurrence channel is divided by length. See the block comment
    above Affinity for why the section-level channel must not be: dividing a
    once-per-section term by length is a decay, not a normalisation, and it is
    what switched contamination detection off at production length.
    """
    return (aff.section_level
            + aff.per_occurrence * DENSITY_BASELINE_WORDS / max(words, DENSITY_BASELINE_WORDS))


def voice_affinity_density(text) -> dict:
    """
    Affinity per DENSITY_BASELINE_WORDS words: {voice_name: float}.

    Per-occurrence evidence grows with length — a 600-word section collects six
    times the markers of a 100-word one — so raw margins are not comparable
    between sections of different lengths. Cross-contamination compares these
    instead. Texts shorter than the baseline are NOT scaled up: a 20-word
    fragment is too little evidence to multiply by five.
    """
    words = _word_count(text)
    return {name: _density(fn(text), words) for name, fn in AFFINITY_SCORERS.items()}


def run(sections: dict) -> dict:
    """
    sections: {section_name: text}
    Returns: {section_name: {voice_required, voice_score, contamination_flags, passed, _debug}}
    """
    results = {}

    for section, text in sections.items():
        voice_req = SECTION_VOICE_MAP.get(section, DEFAULT_VOICE)
        words = _word_count(text)

        # Score against every register once; keep the signed deltas so the
        # registers stay comparable to each other.
        affinities = {name: fn(text) for name, fn in AFFINITY_SCORERS.items()}
        deltas = {v: a.delta for v, a in affinities.items()}

        primary_delta = deltas[voice_req]
        primary_score = _clamp(SCORE_START + primary_delta)
        contamination_flags = list(affinities[voice_req].flags)

        # Cross-contamination: RELATIVE comparison on DENSITY. A section is
        # contaminated when another register is genuinely present (positive
        # affinity) AND leads the required register by at least
        # CROSS_CONTAMINATION_MARGIN points per DENSITY_BASELINE_WORDS words.
        density = {v: _density(a, words) for v, a in affinities.items()}
        primary_density = density[voice_req]

        penalty = 0
        for other_voice in AFFINITY_SCORERS:
            if other_voice == voice_req:
                continue
            margin = density[other_voice] - primary_density
            if density[other_voice] > 0 and margin >= CROSS_CONTAMINATION_MARGIN:
                contamination_flags.append(
                    f"Cross-contamination: section reads {margin:.1f} points per "
                    f"{DENSITY_BASELINE_WORDS} words more like {other_voice} voice "
                    f"than its required {voice_req} voice (affinity {other_voice} "
                    f"{density[other_voice]:+.1f} vs {voice_req} {primary_density:+.1f})"
                )
                penalty += CROSS_CONTAMINATION_PENALTY

        final_score = _clamp(primary_score - penalty)
        passed = final_score >= PASS_THRESHOLD

        results[section] = {
            "voice_required": voice_req,
            "voice_score": final_score,
            "contamination_flags": contamination_flags,
            "passed": passed,
            "_debug": {
                "primary_delta": primary_delta,
                "contamination_penalty": penalty,
                "primary_details": affinities[voice_req].details,
                "athletic_delta": deltas["athletic"],
                "people_delta": deltas["people"],
                "fitt_delta": deltas["fitt"],
                "words": words,
                "affinity_per_100w": {v: round(x, 2) for v, x in density.items()},
            },
        }

    return results


if __name__ == "__main__":
    import json, sys
    data = json.load(open(sys.argv[1]))
    sections = data.get("sections", {})
    out = run(sections)
    for sec, res in out.items():
        status = "PASS" if res["passed"] else "FAIL"
        print(f"[{status}] {sec:12s} | voice={res['voice_required']:8s} | score={res['voice_score']:3d}")
        for flag in res["contamination_flags"][:3]:
            print(f"         ↳ {flag}")
