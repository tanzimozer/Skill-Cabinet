
# voice_config.py — Lexical fingerprints for TIMBR voice registers

SECTION_VOICE_MAP = {
    "Training": "athletic",
    "Nutrition": "people",
    "Supplements": "fitt",
    "Recovery": "fitt",
    "Culture": "athletic",
    "Social": "people",
    "Nightlife": "fitt",
}

# ── Case sensitivity ─────────────────────────────────────────────────────────
# Patterns whose meaning depends on CAPITALISATION (proper nouns, sentence
# openers) live in the *_CAPS lists and are matched case-SENSITIVELY.
# Everything else is matched case-insensitively.
#
# This is not cosmetic. Under re.IGNORECASE the pattern
#     r'\bIn (?:the )?[A-Z][a-zA-Z]+\b'
# matches "in the room", so the athletic register used to collect free points
# from any prepositional phrase — the same class of defect as a named-person
# test that matches any Titlecase bigram. Free per-register points are what
# make a cross-register margin meaningless.

# ── athletic ─────────────────────────────────────────────────────────────────
# GATE (see voicelint._athletic_affinity): SOURCED attribution. This pattern is
# the gate only — it is deliberately NOT also in ATHLETIC_POSITIVE, so no signal
# is counted twice.
#
# "Sourced" is load-bearing and it used to be missing. The pattern was a bare
# list of reporting verbs, so any prose containing the word "reported" or
# "writes" passed the gate: a Culture section written as a pure Fitt newsletter,
# with no quoted source anywhere in 1135 words, collected +REGISTER_GATE for the
# athletic register and its cross-register margin collapsed from about +22 to
# +1.6. This register does not merely use reporting verbs, it names who is
# talking — by name, by role, or by institution.
# The class is "verbs of stance in reported speech", and it was cut off in the
# middle of itself: `maintains` and `contends` were in, `concedes`,
# `acknowledges`, `insists`, `admits` and `denies` were not, which is not a
# distinction anybody drew on purpose. The completion is the semantic class, not
# a list of words that happened to appear in some text — verbs that report a
# speaker's position and are not also ordinary nouns or adjectives. `confirmed`,
# `described`, `warns` and `estimates` are deliberately still OUT: each of them
# reads as often as a document, a modifier or a number as it does as a source,
# and every verb added here also widens the fitt register's reporting penalty.
ATTRIBUTION_VERB = (
    r'says|said|notes|noted|adds|added|argues|argued|explains|explained'
    r'|told|writes|wrote|reports|reported|maintains|contends'
    r'|concedes|conceded|acknowledges|acknowledged|insists|insisted'
    r'|admits|admitted|denies|denied'
)

# Any reporting verb at all, sourced or not. Used by the fitt register, which
# violates itself the moment it reports anything. See FITT_NEGATIVE.
#
# `according\s+to` and not `according to`. A literal space does not match a line
# break, and every text this module is ever shown is hard-wrapped prose, so the
# single commonest attribution phrase in English was invisible roughly one time
# in eight — whenever the wrap happened to fall between the two words.
REPORTING_VERB_ANY = r'\b(?:' + ATTRIBUTION_VERB + r'|according\s+to)\b'

# Capitalised tokens that are not a source. Without this, "Nobody writes the
# programme down" reads as an attribution and hands a Fitt newsletter the
# athletic register's gate. He/She/They are excluded on purpose and not by
# accident: a bare pronoun tag is a profile quoting its subject, and this
# register attributes to who said it, by name, role or institution.
NON_SOURCE_TOKEN = (
    r'(?:The|A|An|It|This|That|These|Those|There|Here|Nobody|Everyone|Everybody'
    r'|Someone|Somebody|Anyone|Anybody|No|Not|Nothing|But|And|Or|So|Then|Than'
    r'|When|While|After|Before|Since|Because|If|Though|Although|However|Still'
    r'|Yet|Despite|Meanwhile|Instead|What|Where|Why|How|Who|Whose|Which|Now'
    r'|Today|Most|Many|Some|Every|Each|All|Both|One|Two|Three|Four|Five|First'
    r'|Second|Third|Last|Next|He|She|They|We|You|I|His|Her|Their|Its|Our|Your'
    r'|My|Everything|Anything|Something)'
)

# CASE-SENSITIVE, like the other patterns that encode proper nouns. Under
# re.IGNORECASE the branch "[A-Z][a-z]+ says" matches "nobody says", and the
# NON_SOURCE_TOKEN lookahead stops working because it is spelled in capitals, so
# a Fitt newsletter with no source anywhere in 1135 words passed the athletic
# gate. Where a branch can legitimately begin a sentence its first letter is
# spelled both ways instead. voicelint matches this pattern WITHOUT
# re.IGNORECASE and the sentence-opener test below pins that.
ATHLETIC_ATTRIBUTION = (
    # "according to the council" / "According to Nair"
    r'\b[Aa]ccording\s+to\s+[A-Za-z]'
    # "Nair says", "Nakashima noted"
    r'|\b(?!' + NON_SOURCE_TOKEN + r'\b)[A-Z][a-z]+\s+(?:' + ATTRIBUTION_VERB + r')\b'
    # "says Nair"
    r'|\b(?:' + ATTRIBUTION_VERB + r')\s+(?!' + NON_SOURCE_TOKEN + r'\b)[A-Z][a-z]+'
    # "Priya Nair, 29, head of performance science at Northwest Sports
    # Institute, says ..." — the source is named and then described, so the verb
    # is a long way from the name. This is the commonest shape in the register
    # and a name-adjacent pattern alone misses all of it.
    #
    # The span may cross a LINE break but not a PARAGRAPH break. It used to be
    # `[^.!?\n]{0,150}`, which cannot cross a line break at all — and an
    # apposition long enough to need this branch is, by construction, long
    # enough to wrap. "Nadia Whitfield, who came to the college side after nine
    # years in professional\nrugby, says" was invisible for no reason except
    # where the line happened to end. `(?!\n\n)` keeps the original intent: the
    # source and the verb must still be inside one paragraph.
    r'|\b(?!' + NON_SOURCE_TOKEN + r'\b)[A-Z][a-z]+(?:(?!\n\n)[^.!?]){0,150},\s*'
    r'(?:' + ATTRIBUTION_VERB + r')\b'
    # "the coach says", "the study found", "four independent groups reported".
    # The source noun is an OPEN slot with up to two modifiers in front of it:
    # attribution by role is still attribution, and the set of roles a source
    # can hold is not enumerable. The determiner is what carries the weight.
    # "she says" has none, and a bare pronoun tag is a profile quoting its
    # subject rather than a report naming a source.
    r'|\b(?:[Tt]he|[Aa]n?|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|[Ss]ix|[Ss]even'
    r'|[Ee]ight|[Nn]ine|[Tt]en|[Ss]everal|[Mm]any|[Ss]ome|[Bb]oth|[Aa]ll'
    r'|[Ii]ts|[Tt]heir|[Oo]ur)\s+'
    # The modifiers must be modifiers. A relativiser or a conjunction in this
    # slot means the verb belongs to a different clause: "the ones who found"
    # is not an attribution, and letting it count handed the athletic gate to a
    # 1135-word Fitt newsletter with no source in it.
    #
    # A PASSIVE AUXILIARY in this slot means the noun is not the actor, and
    # attribution requires an actor: "the effect was found" is the passive
    # research construction — the effect did not find anything — and "the coach
    # was told" names the listener, not the source. This mattered the moment
    # sourcing became per-occurrence evidence AND a people negative, because
    # "The effect was found" is ALSO PEOPLE_NEGATIVE[0], so one phrase was
    # costing the people register two negative markers for the same four words.
    r'(?:(?!(?:who|whom|whose|which|that|and|or|but|if|when|while|because'
    r'|is|are|was|were|been|being)\s)'
    r'[a-z]+\s+){0,2}(?:'
    + ATTRIBUTION_VERB + r'|shows|showed|found|suggests|suggested|projects)\b'
    # "researchers say", "organisers reported" — same thing without an article.
    r'|\b(?:[Rr]esearchers?|[Aa]nalysts?|[Ss]cientists?|[Cc]linicians?'
    r'|[Cc]oaches|[Oo]rganisers|[Oo]rganizers|[Oo]fficials|[Pp]hysiologists?'
    r'|[Aa]uthors?)\s+(?:say|said|note|noted|report|reported|argue|argued)\b'
)

# ── The athletic register's PER-OCCURRENCE vocabulary: sourcing ──────────────
# This is the half of the register that was missing, and its absence is what
# made in-register reported copy read as a profile.
#
# Before this the whole athletic per-occurrence channel was DATA_CLAIM (SHARED
# with fitt, so it cancels in an athletic/fitt margin and says nothing about
# athletic/people) plus four capitalised place-and-name patterns. The register
# had, in effect, ONE per-occurrence signal: numeric data claims. So an athletic
# section that is a HUMAN story rather than a DATA story — which is what a
# Culture feature IS — had no vocabulary to compete in, and the people
# register's pronoun density won the margin unopposed. A 447-word Culture
# closure feature carrying "according to", three sourced quotes, "did not
# respond to two requests for comment" and "declined to discuss an active
# listing" scored -3 on the athletic per-occurrence channel and +46 on the
# people one. It passed the athletic gate and was blocked as people-contaminated
# anyway. Two ordinary sentences of human colour were enough to do it.
#
# WHY THIS AND NOT A BIGGER MARGIN. Gate 2 established that reverting the
# contamination penalty lets a genuinely cross-register text back through, and
# widening the margin trades the false positive straight for a miss. The defect
# is not the threshold; it is that one side of the comparison had nothing to say.
#
# ── ON COUNTING ATTRIBUTION TWICE ────────────────────────────────────────────
# ATHLETIC_ATTRIBUTION is BOTH the gate and, below, per-occurrence evidence, and
# the comment above it used to say the opposite ("deliberately NOT also in
# ATHLETIC_POSITIVE, so no signal is counted twice"). That rule was applied to
# exactly one of the three registers. PEOPLE_POSITIVE is literally
# `PEOPLE_ACCESS + [...]`: the people register has always scored its gate
# evidence in both channels. So the old arrangement was not a principle, it was
# an asymmetry, and it fell on the one axis where the two registers share their
# machinery.
#
# The two channels also ask different questions, and the difference is the whole
# athletic/people distinction:
#     gate            does this section attribute a claim to an identified
#                     source AT ALL?  (once, boolean)
#     per-occurrence  how much of its sentence-by-sentence machinery is SOURCING
#                     machinery?  (density)
# A report attributes continuously and to many sources. A profile attributes to
# its one subject and then narrates. A boolean cannot tell those apart; a density
# can, and the pattern is what keeps it honest: ATHLETIC_ATTRIBUTION requires a
# NON-PRONOUN source, so a profile's "she says" / "he adds" earns nothing here.
# That is the same exclusion PEOPLE_PRONOUN makes in the other direction, and
# the two together are what hold this axis apart.

# The non-response frame. Nothing but reported journalism writes these
# sentences. A profile does not record that its subject declined to comment, and
# a newsletter has nobody to ask. This is the cleanest per-occurrence evidence in
# the register: it has no counterpart in either of the other two, so unlike
# DATA_CLAIM it does not cancel.
ATHLETIC_NON_RESPONSE = (
    r'\b(?:[Dd]eclined|[Rr]efused)\s+to\s+'
    r'(?:comment|discuss|say|answer|elaborate|confirm|provide|participate'
    r'|respond|be\s+interviewed|be\s+drawn)\b'
    # The perfect takes a past participle ("has not replied"), so the verbs are
    # spelled with their inflections rather than as bare stems.
    r'|\b(?:did|does|do|has|have|had|would|could)\s+not\s+'
    r'(?:respond(?:ed|s)?|repl(?:y|ied|ies)|answer(?:ed|s)?'
    r'|comment(?:ed|s)?)\b'
    # `return` needs its object and the others do not. "Did not respond" can
    # only be a non-response; "did not return" is usually the intransitive "go
    # back to" — the quiet-profile fixture's "did not return to normal hours
    # until the following spring" was scoring as a source declining to comment,
    # which handed a wrong-register PROFILE a point of athletic sourcing and,
    # once REPORTING_MACHINERY existed, the licence in _reported_by_pronoun as
    # well. A marker that fires on the wrong sense is worse than a missing one
    # when something else is keyed to it.
    r'|\b(?:did|does|do|has|have|had|would|could)\s+not\s+return(?:ed|s)?\s+'
    r'(?:\w+\s+){0,2}(?:calls?|messages?|e-?mails?|requests?|voicemails?'
    r'|texts?|enquir(?:y|ies)|inquir(?:y|ies))\b'
    r'|\b[Rr]equests?\s+for\s+comment\b'
    r'|\b(?:was|were)\s+not\s+(?:made\s+available|available\s+for\s+comment'
    r'|reachable)\b'
    r'|\bon\s+condition\s+of\s+anonymity\b'
    r'|\bbefore\s+publication\b'
)

# Provenance: where the fact came from. A report says how it knows; a profile
# knows because it was in the room, and a newsletter because it has an opinion.
ATHLETIC_PROVENANCE = (
    r'\b[Ss]pokes(?:person|man|woman)\b'
    r'|\b[Aa]\s+representative\s+(?:for|of)\b'
    r'|\b[Ii]n\s+an?\s+(?:written\s+|prepared\s+)?statement\b'
    r'|\b(?:[Pp]ublic|[Cc]ounty|[Cc]ourt|[Cc]ity|[Ss]tate|[Ff]ederal)\s+'
    r'(?:records|filings|documents)\b'
    r'|\b[Rr]ecords?\s+(?:show|showed|indicate|indicated|list|listed)\b'
    # Both cases on the leading token: these open sentences ("Reached by phone,
    # the broker gave the same account") and the whole family is matched
    # case-SENSITIVELY, so a lowercase-only spelling is a dead branch.
    r'|\b(?:[Rr]eached|[Cc]ontacted|[Aa]sked)\s+'
    r'(?:by\s+(?:phone|e-?mail)|for\s+comment)\b'
    r'|\b(?:[Ii]n|[Dd]uring)\s+an\s+interview\b'
    r'|\b[Ww]hen\s+(?:reached|contacted|asked)\b'
    r'|\b(?:[Cc]ompiled|[Pp]rovided|[Ss]hared|[Rr]eleased|[Ss]ubmitted)\s+'
    r'(?:by|to|with)\b'
)

# Reported hedging: the writer marks a claim as somebody else's.
ATHLETIC_REPORTED_HEDGE = (
    r'\b[Rr]eportedly\b|\b(?:is|are|was|were)\s+said\s+to\b'
)

#: Matched CASE-SENSITIVELY, like every other pattern here that encodes proper
#: nouns or a capitalised exclusion list. ATHLETIC_ATTRIBUTION in particular is
#: meaningless under re.IGNORECASE — see the note above it.
ATHLETIC_SOURCING = [
    ATHLETIC_ATTRIBUTION,
    ATHLETIC_NON_RESPONSE,
    ATHLETIC_PROVENANCE,
    ATHLETIC_REPORTED_HEDGE,
]

# ── DE-DUPLICATED ATTRIBUTION: "she says" after the source has been named ────
# ATHLETIC_ATTRIBUTION requires a NON-PRONOUN source, and that requirement is
# right at the GATE and wrong everywhere else. In a single-subject reported
# feature every attribution after the first is a pronoun, because de-duplicating
# a repeated surname is what a copy editor does and it is better prose. Measured
# on the reviewer's D1: taking a 368-word Culture feature that passes and doing
# nothing but that edit moved it from -1.73 to +28.61 and from 100/PASS to
# 56/FAIL. Same story, same subject, same facts. Pronoun-versus-name is a
# COREFERENCE artifact, not a register signal, and charging it was a defect.
#
# The trap, and it is the whole difficulty: a PROFILE also names its subject in
# the opening 50 words (that is literally the people gate) and also then writes
# "she says". The presence of a name does not separate the two shapes. Licensing
# pronoun attribution on "a name appeared" was measured and it converts
# VAL_X_CULTURE_AS_PEOPLE — a wrong-register profile that MUST fire — into a
# miss, while still not rescuing the report. See THE MACHINERY OF ASKING below
# for what does separate them, and THE RESIDUAL HOLE for what does not.
PRONOUN_ATTRIBUTION = (
    r'\b(?:[Ss]he|[Hh]e|[Tt]hey)\s+(?:' + ATTRIBUTION_VERB + r')\b'
)

# ── THE MACHINERY OF ASKING ──────────────────────────────────────────────────
# What separates a report that quotes its named subject from a profile that
# quotes its named subject is not the name and not the pronoun. It is whether
# the section records the ACT OF ASKING somebody who is not the writer.
#
# A report writes "declined to comment", "did not respond", "a representative
# for", "records show", "reached by phone", "in an interview", "according to".
# A profile never has occasion to write any of them: its authority is ACCESS —
# the writer was in the room — so it has nothing to report about having asked.
# This is the same argument the ATHLETIC_NON_RESPONSE block already makes
# ("Nothing but reported journalism writes these sentences"), used as a licence
# rather than as a marker.
#
# MEASURED, across 32 texts pooled from all four corpora, per 100 words:
#
#     marker family        reported features   profiles      separates?
#     profile access            0.00 - 2.65    0.90 - 6.32   no, overlaps
#     pronoun attribution       0.00 - 1.34    0.00 - 2.17   no, overlaps
#     of which quote-tagged     0.00 - 0.88    0.00 - 1.09   no, overlaps
#     of which indirect         0.00 - 0.73    0.00 - 1.22   no, overlaps
#     named attribution         0.00 - 3.04    0.00 - 0.91   no, overlaps
#     distinct named sources    0    - 7       0    - 3      no, overlaps
#     year references           0.00 - 1.94    0.00 - 1.29   no, overlaps
#     MACHINERY OF ASKING       0.00 - 1.74    0.00 - 0.12   nearly
#
# Every family overlaps. Machinery is the only one that comes close, and it is
# near-conclusive in ONE direction only: of sixteen profiles exactly one carries
# any at all, and it carries 0.12. Its PRESENCE is strong evidence of reporting.
# Its ABSENCE is not evidence of anything, because plenty of reported features
# carry none either — which is exactly THE RESIDUAL HOLE below.
REPORTING_MACHINERY = [
    ATHLETIC_NON_RESPONSE,
    ATHLETIC_PROVENANCE,
    ATHLETIC_REPORTED_HEDGE,
    r'\b[Aa]ccording\s+to\s+[A-Za-z]',
]

# SHARED evidence. A numeric claim with a unit is evidence for the athletic
# register AND for fitt: reported sports journalism and the newsletter register
# are both data-forward. Scoring it for athletic only made every data-dense
# fitt section read as athletic contamination — the sample issue's Recovery
# section (athletic +20 vs fitt +10 before this) is exactly that false
# positive. Shared evidence cancels in the margin, which is the point: what
# separates athletic from fitt is attribution and paragraph structure, not the
# presence of numbers.
#
# Note what that cancellation implies, and why the register needed ATHLETIC_
# SOURCING: shared evidence is worth nothing in ANY margin. DATA_CLAIM was the
# only lexical term the athletic register had, so on the athletic/people axis
# the register's entire per-occurrence vocabulary was four capitalised patterns.
DATA_CLAIM = (
    r'\d+\s*(?:%|percent|miles|minutes|pounds|lbs|kg|hours|days|weeks|seconds'
    r'|metres|meters|kilometres|kilometers|sessions|reps|sets|grams|mg)'
)

ATHLETIC_POSITIVE = [DATA_CLAIM]
ATHLETIC_POSITIVE_CAPS = [
    r'\bAt (?:the )?[A-Z][a-zA-Z]+\b',
    r'\bIn (?:the )?[A-Z][a-zA-Z]+\b',
    r'[A-Z][a-z]+,\s*\d{2},',
    r'[A-Z][a-z]+\s[A-Z][a-z]+,\s*[a-z]+\s+(?:at|of|for|with)\s+[A-Z]',
]

# The exclamation point is held as its own name because the athletic gate needs
# to count it as well as penalise it. See ATHLETIC_EXCLAMATION_ALLOWANCE below
# and voicelint._athletic_affinity.
ATHLETIC_EXCLAMATION = r'!'

ATHLETIC_NEGATIVE = [
    ATHLETIC_EXCLAMATION,
    r'\b(?:you should|you can|you need|get ready|are you ready|it is time)\b',
    r'\b(?:amazing|incredible|awesome|fantastic|wonderful)\b',
]

# The athletic GATE is a conjunction: reported copy attributes its claims AND
# does not shout. Attribution alone turned the gate into a +REGISTER_GATE credit
# that a section could spend on hype, which is a real loosening against the
# pre-repair scale where attribution was worth one +2 marker: a Culture section
# with one attributed quote and six exclamation points scored 64/FAIL before and
# 92/PASS after. Under the magazine ruleset nothing except VoiceLint looks at
# exclamation points at all, so this is the only place that line can be held.
#
# The allowance is ONE. An exclamation point inside a quotation is the subject's
# voice and legitimately appears in reported copy; the second one is the
# writer's own voice raised, which this register does not do.
ATHLETIC_EXCLAMATION_ALLOWANCE = 1

# ── people ───────────────────────────────────────────────────────────────────
# GATE (see voicelint._people_affinity): a named human anchor in the opening
# window WHO THE SECTION GIVES THE READER ACCESS TO. The name detector lives in
# voicelint._named_person — a regex alone cannot tell a person from a place.
#
# The access half of the gate is the part that was missing, and its absence is
# the reason athletic and people stopped separating on long copy. Reported
# copy names its sources: "Dee Nakashima, who opened the facility in 2019" is in
# the opening 50 words of a perfectly ordinary Culture report, so a name-only
# gate handed that section +REGISTER_GATE for the people register and left the
# two registers within 3 points of each other across 900 words. A name is not a
# profile. A profile hands the reader something about the person that reporting
# never does: their age, their kitchen, their kids, their week, their own voice
# in a tagged quote.
PEOPLE_ACCESS = [
    r'\bwhose\s+[a-z]+',
    r'\b(?:her|his|their)\s+(?:kids?|children|wife|husband|partner|mother'
    r'|father|parents|son|daughter|family|apartment|kitchen|home|house|dog'
    r'|roommate|friends?|voice|hands?|mornings?|routine|clients?|neighbours?'
    r'|neighbors?)\b',
    r'[A-Z][a-z]+,\s*\d{1,2},',                 # "Mia Tanaka, 29,"
    # The trailing \b is load-bearing: without it "an" matched inside "and", so
    # "... in 2019 and reviewed the block" read as an age-and-role apposition
    # and handed reported copy the people register's profile-access test.
    r'\d{2}(?:,|\s)\s*(?:a|the|an|is|was|works|lives|trains)\b',
    # A tagged quote. Straight and curly quotes both, because real copy uses
    # both and a pattern that only knows about one of them is a dead pattern.
    r'["“‘\'][^"”’\']{5,80}["”’\'],?\s*(?:she|he|they)\s+'
    r'(?:says|said|adds|added|explains|laughs|recalls)',
    r'\b(?:every|each)\s+(?:morning|Tuesday|week|Thursday|Sunday|day|evening'
    r'|night|Monday|Wednesday|Friday|Saturday)\b',
]

# Personal pronouns are back, as per-occurrence evidence.
#
# They were removed on the argument that "every register's prose contains them,
# so they discriminated nothing". Measured across 46 texts that turns out to be
# false at the lengths this gate actually runs at. Per 100 words, profiles carry
# 4.2 to 7.4 personal pronouns and reported athletic copy carries 0.0 to 3.1,
# because a profile stays with one human for its whole length and a report does
# not. The reason they looked undiscriminating before is that they were being
# counted as RAW points against a raw margin, where a long section's pronoun
# count swamped everything; per 100 words they are one of the strongest signals
# available on the axis that was collapsing.
#
# A pronoun that is a QUOTE TAG is excluded. "he says", "she adds" is the
# attribution machinery both registers share, and counting it would score
# reported copy for the one thing it has in common with a profile instead of
# for the thing that separates them.
PEOPLE_PRONOUN = (
    r'\b(?:she|her|hers|he|him|his)\b(?!\s+(?:' + ATTRIBUTION_VERB + r')\b)'
)

PEOPLE_POSITIVE = PEOPLE_ACCESS + [
    PEOPLE_PRONOUN,
    r'\b(?:lives|grew up|moved|walks|sits|stands|laughs|laughed|smiles|smiled'
    r'|cries|crying|remembers|recalls|swears|credits|wakes)\b',
]
PEOPLE_NEGATIVE = [
    r'\b(?:was found|has been shown|it is known|it has been)\b',
    r'(?:\d+\.\s){3,}',
]
PEOPLE_NEGATIVE_CAPS = [
    r'^(?:Studies|Research|Data|According to studies)',
]

# Sourced attribution is the athletic register's GATE, the fitt register's
# violation — and, for exactly the same reason, the people register's violation.
# Athletic is the only second-hand register of the three. Fitt's authority is the
# writer's verdict and People's is the writer's ACCESS; neither of them borrows
# authority from a third party, and both of them stop being themselves the moment
# they do.
#
# This is the mirror of the note on REPORTING_VERB_ANY in FITT_NEGATIVE, and it
# is here because the held-out data forced it. Measured across 18 texts — eight
# reported features about a person and ten profiles — per 100 words:
#
#     marker family     reported features   profiles      separates?
#     profile access         0.00 - 2.65    1.52 - 5.15   no, overlaps
#     personal pronoun       1.13 - 5.52    3.03 - 9.79   no, overlaps
#     personal-life verb     0.00 - 0.53    0.00 - 1.25   no, overlaps
#     SOURCING               0.88 - 2.61    0.00 - 0.52   YES, cleanly
#
# Read that table again, because it says something the people register's own
# comments got wrong. NONE of the people markers can tell a report about a person
# from a profile of a person. PEOPLE_PRONOUN was added on the measurement that
# "profiles carry 4.2 to 7.4 personal pronouns per 100 words and reported
# athletic copy carries 0.0 to 3.1"; on reported HUMAN-INTEREST copy — a Culture
# feature, which is the shape Culture is required to be — reports run to 5.52 and
# profiles start at 3.03. The two ranges sit on top of each other. The pronoun
# term is not wrong, it is simply not evidence on this axis, and it was carrying
# the axis alone.
#
# So the axis is decided by sourcing, and by sourcing only. Counting it once (as
# athletic evidence) left the signal at roughly a third of the size of the people
# markers' spread, which is why the separating band was about one marker wide.
# Counting it on both sides — the register that does it, and the register that
# does not — is what makes the axis resolvable at all.
#
# NOTE this is ATHLETIC_SOURCING and emphatically NOT REPORTING_VERB_ANY. A
# profile's "she says" is its subject's own voice and PEOPLE_ACCESS counts it as
# access; penalising it would charge the people register for the one thing a
# profile is supposed to do. What is penalised is attribution to a NON-PRONOUN
# third party, plus the reporting frames — the machinery of borrowed authority.
#
# Matched CASE-SENSITIVELY, like ATHLETIC_SOURCING itself.
PEOPLE_NEGATIVE_SOURCED = list(ATHLETIC_SOURCING)

# ── fitt ─────────────────────────────────────────────────────────────────────
# GATE (see voicelint._fitt_delta): staccato paragraph structure.
FITT_POSITIVE = [DATA_CLAIM]   # shared with athletic — see DATA_CLAIM above
FITT_POSITIVE_PARA_MAX = 40    # words
FITT_POSITIVE_KICKER_MAX = 12  # words
FITT_LONG_PARA_MAX = 80        # words; a paragraph past this is a violation
FITT_STACCATO_RATIO = 0.6      # share of paragraphs that must be short
FITT_STRONG_OPINION = [r'\b(?:best|worst|only|never|always|exactly|period|full stop|done)\b']
FITT_DECLARATIVE = r'^[A-Z][^,;]{0,30}(?:\.|:)\s'
FITT_DATA_LEAD = r'^\d'
FITT_NEGATIVE = [
    r'\b(?:might|could|perhaps|possibly|seems|appear|suggest|may)\b',
    r'\b(?:you should|your body|try this|you need)\b',
    # Reporting is the athletic register's GATE and the fitt register's
    # violation: the newsletter's authority is the writer's verdict, not a
    # quoted expert. This is the only signal that separates athletic copy from
    # fitt copy when the athletic copy happens to be written in short
    # paragraphs, and the staccato gate alone cannot see that difference.
    #
    # Note this is the BARE verb list and not ATHLETIC_ATTRIBUTION. The two
    # patterns answer different questions and must not be shared. The athletic
    # gate asks "does this copy attribute to an identified source?", which
    # demands a name, a role or an institution. Fitt asks "does this copy report
    # at all?", and the answer is yes the moment a reporting verb appears,
    # sourced or not. Folding fitt's test into the stricter athletic one halved
    # the penalty on reported copy written in short paragraphs and let a Training
    # report read 16 points more like a newsletter than like its own register.
    REPORTING_VERB_ANY,
]
FITT_NEGATIVE_CAPS = [
    r'^(?:Although|While|Despite|However|Nevertheless|Nonetheless)',
]

# ── Plain-language names for the markers ─────────────────────────────────────
# Flags reach an editor through the orchestrator's violations list and end up in
# results/*.json. A regex is not a note to a writer. Every pattern that can
# produce a flag needs an entry here, and test_voicelint fails if one is
# missing, because adding a pattern without a label is the easy way to ship a
# regex into a scorecard.
FLAG_LABELS = {
    # Register-neutral wording on purpose: this pattern now flags for two
    # different registers and the reason differs. Fitt asserts instead of
    # reporting; People gets its authority from access instead of from a source.
    # The flag string already names the register, so the label must not.
    ATHLETIC_ATTRIBUTION:
        "attribution to a third-party source (named, role or institution)",
    ATHLETIC_NON_RESPONSE:
        "a non-response frame (declined to comment, did not respond)",
    ATHLETIC_PROVENANCE:
        "a sourcing frame (spokesperson, records, statement, interview)",
    ATHLETIC_REPORTED_HEDGE:
        "reported hedging (reportedly, is said to)",
    PRONOUN_ATTRIBUTION:
        "attribution by pronoun to a source the section has already named",
    REPORTING_VERB_ANY:
        "reporting verb (this register asserts, it does not report)",
    ATHLETIC_EXCLAMATION: "exclamation point",
    ATHLETIC_NEGATIVE[1]: "second-person coaching",
    ATHLETIC_NEGATIVE[2]: "hype adjective",
    PEOPLE_NEGATIVE[0]: "passive research construction",
    PEOPLE_NEGATIVE[1]: "a run of bare numbered items",
    PEOPLE_NEGATIVE_CAPS[0]: "opens on a study rather than on a person",
    FITT_NEGATIVE[0]: "hedging",
    FITT_NEGATIVE[1]: "second-person wellness register",
    FITT_NEGATIVE_CAPS[0]: "subordinate-clause opener",
}

#: Every pattern that can reach an editor as a flag. Kept as data so the label
#: coverage test does not have to guess which lists those are.
FLAGGING_PATTERNS = (
    tuple(ATHLETIC_NEGATIVE) + tuple(PEOPLE_NEGATIVE) + tuple(PEOPLE_NEGATIVE_CAPS)
    + tuple(PEOPLE_NEGATIVE_SOURCED) + (PRONOUN_ATTRIBUTION,)
    + tuple(FITT_NEGATIVE) + tuple(FITT_NEGATIVE_CAPS)
)

# ── Scoring scale ────────────────────────────────────────────────────────────
# Every register scores a section as a signed "affinity delta" against
# SCORE_START. Three term families, ONE unit system, so the three registers
# share an origin and a step size:
#
#   lexical evidence   POSITIVE_HIT / NEGATIVE_HIT per marker hit
#   structural evidence STRUCTURAL_HIT per structural feature (one-sided,
#                       counted exactly like a lexical marker)
#   register gate      +/- REGISTER_GATE, the register's single defining test,
#                       evaluated for EVERY register so no register collects a
#                       free unconditional bonus the others cannot
#
# The gate is the part that makes cross-register margins comparable. Before,
# fitt carried an unconditional +8/-10 and people an unconditional +5/-8 while
# athletic carried nothing, so a register-neutral paragraph already scored
# people > athletic > fitt before a single word was read.
SCORE_START = 100
POSITIVE_HIT = 2    # points added per positive marker hit
NEGATIVE_HIT = -3   # points added per negative marker hit
STRUCTURAL_HIT = POSITIVE_HIT       # one structural feature == one marker
# The gate is worth 5 markers, which is what the original staccato test cost a
# section that failed it (-10). Keeping that magnitude matters: a fitt section
# that is one dense slab plus two hedge words has to stay a FAIL, and at 4
# markers it would land on -14 and squeak through the -15 floor.
#
# ── GATE-TO-MARKER WEIGHTING: assessed, recorded, not changed ───────────────
# The observation: this gate is worth 5 marker HITS at 100 words and 60 at 1200,
# a 12x swing across the legal range, so one constant may not mean the same
# editorial thing at both ends. The arithmetic is correct. Two things measured
# against it (TestGateToMarkerWeighting pins both):
#
# 1. In DENSITY — the unit the margin is actually thresholded in — the exchange
#    rate does not move at all. A gate is worth REGISTER_GATE at every length and
#    a marker is worth its own density at every length. The 12x is the definition
#    of a rate: one hit is a smaller share of a longer section, which is the
#    property the two-channel split was built to produce and which duplication
#    invariance proves exactly. So the ratio on its own is not evidence that the
#    constant fails at one end.
#
# 2. "At the long end contamination is decided almost entirely by the gates" is
#    overstated. Over all 73 texts in the suite the gate channel's share of the
#    absolute margin runs 36% below 200 words, 53% at 200-600 and 54% above 600.
#    It rises with length, as predicted, but above 600 words the spread is 14% to
#    94% and the typical case is close to an even split.
#
# WHAT IS ACTUALLY WRONG, and it is worse than the ratio: a gate is a BOOLEAN
# decided by ONE occurrence anywhere in the section, and it carries +/-10 of
# density however long the section is. A single phrase in 1200 words can outweigh
# the whole lexical channel. Both defects this module has shipped were exactly
# that — a 1135-word newsletter that took the athletic gate on one reporting
# verb, and a reported feature that handed the people register its gate on one
# access marker. The leverage of a boolean, not the size of the constant.
#
# The repair reduces the exposure on the athletic side without removing it: the
# gate's own evidence is now counted per occurrence too (ATHLETIC_SOURCING), so
# attributing once and attributing ten times are no longer the same score, and a
# section can no longer buy the gate with one phrase and then stop. The people
# register has worked this way all along. The fitt gate — a paragraph-length
# ratio — is the one that remains a pure boolean, and it is the obvious next
# candidate for being made proportional. That needs a corpus, not an opinion.
REGISTER_GATE = 5 * POSITIVE_HIT    # +/-10

# ── Pass threshold: DERIVED, not chosen ──────────────────────────────────────
# A section's score is clamp(SCORE_START + delta) minus contamination penalty,
# so with no penalty the gate is exactly:
#
#     pass  <=>  SCORE_START + delta >= PASS_THRESHOLD
#           <=>  delta >= PASS_THRESHOLD - SCORE_START
#
# The threshold therefore only ever encodes ONE editorial decision: how much
# negative evidence a section may carry and still ship. That budget is
# denominated in the scale's own unit — the negative marker:
#
#     NEGATIVE_MARKER_BUDGET = 5 marker hits
#     FAIL_FLOOR_DELTA       = 5 * NEGATIVE_HIT = -15
#     PASS_THRESHOLD         = 100 - 15         =  85
#
# 5 hits is where the bar has always sat, and it must not drift by accident.
# The pre-refactor code applied a flat -20 cross-contamination penalty to every
# section (the fixed-floor defect) against a 65 threshold, so its EFFECTIVE
# rule was clamp(100+d) - 20 >= 65, i.e. d >= -15. Removing the always-on
# penalty without moving the threshold from 65 to 85 silently loosened the gate
# by 15 points and flipped everything in delta [-30, -16] from FAIL to PASS.
# test_voicelint.py pins the EFFECTIVE bar (the delta at which pass flips), not
# this constant, because asserting the constant is what let that through.
NEGATIVE_MARKER_BUDGET = 5
FAIL_FLOOR_DELTA = NEGATIVE_MARKER_BUDGET * NEGATIVE_HIT   # -15

# The single source of truth for pass/fail. Do not hard-code this number
# anywhere else — import it.
PASS_THRESHOLD = SCORE_START + FAIL_FLOOR_DELTA             # 85

# ── Cross-contamination ──────────────────────────────────────────────────────
# Contamination is RELATIVE and DENSITY-based: a section is contaminated when
# another register's affinity is positive AND leads the required register's
# affinity by at least CROSS_CONTAMINATION_MARGIN points per
# DENSITY_BASELINE_WORDS words.
#
# Density has TWO channels and only one of them is divided by length. See the
# block comment above voicelint.Affinity: dividing a once-per-section term (a
# gate, a rhythm ratio) by the word count is a decay, not a normalisation, and
# it switched contamination detection off at exactly the lengths this ruleset
# requires. Per-occurrence evidence is scaled to DENSITY_BASELINE_WORDS;
# section-level evidence is not scaled at all. The result is exactly invariant
# under duplication, which test_voicelint pins.
#
# CALIBRATION — derived on one corpus, checked against two others.
#
# Three previous margins died the same death. 10 came from 20 fixtures written by
# the author of the scorer and was refuted in both directions on texts that
# author had not written. 6 was first recomputed from its own corpus and asserted
# to be that corpus's midpoint, which validates a constant against the data it
# came from and cannot fail; re-derived against a held-out corpus it survived,
# and was then refuted anyway on a SECOND held-out corpus that contained a shape
# neither of the first two did — a reported HUMAN-INTEREST feature, which is what
# a Culture section is required to be.
#
# WHAT CHANGED THIS TIME, and why this is not simply a fourth number. The margin
# moved because the SCALE moved. The athletic register acquired the
# per-occurrence vocabulary it never had (ATHLETIC_SOURCING) and the people
# register acquired the matching negative (PEOPLE_NEGATIVE_SOURCED). A constant
# denominated in points of the old scale cannot survive a change to what the
# points measure. Re-deriving it was mandatory; leaving it at 6 would have been
# the error.
#
#   DERIVATION CORPUS — 49 texts, 35 to 1176 words. Sets the constant.
#     in-register (must NOT fire), 32 texts:
#       10 deliberately hostile in-register texts, 9 clean per-register samples,
#        7 sections of sample_issue.json (copy this module's author did not
#          write), 6 long hostile in-register texts at 480-1176 words, TWO of
#          which are the reported human-interest shape that was missing
#     cross-register (MUST fire), 17 texts:
#        8 hostile wrong-voice texts including the audit's miss and false
#          positive, 4 legacy cross-register samples, 5 long wrong-register
#          texts at 793-1135 words, one of which is the QUIET profile shape the
#          cross half was missing for the same reason
#     worst in-register  : +3.00   (an 80-word Recovery section from
#                                   sample_issue.json; athletic/fitt axis)
#     weakest cross      : +7.15   (an 852-word Culture section written as a
#                                   diluted, surname-tagged profile)
#     band               : (+3.00, +7.15]   width 4.15
#     margin             : midpoint = 5.08 -> 5
#
#   RE-DERIVED after PRONOUN_ATTRIBUTION, and it lands on the same constant.
#   The band WIDENED, from (+3.00, +6.57] to (+3.00, +7.15]: the in-register
#   half did not move at all (its binding text is on the athletic/fitt axis,
#   which this change does not touch) and the cross-register half moved AWAY
#   from the line, because the surname-tagged profile that binds it stopped
#   collecting a point of athletic sourcing from "did not return to normal
#   hours" once the `return` sense error was fixed. This is the first
#   calibration in this module's history that did not move the constant, and
#   the reason is that it changed what a REPORT scores rather than what the
#   scale means.
#
#   VALIDATION CORPUS — 12 texts, 530 to 1023 words, EVERY ONE inside
#   prohiblint.WORD_COUNT_RANGES for its section.
#     band               : (-9.76, +5.91]   width 15.67
#     verdict            : 5 sits inside it. 6 of 6 wrong-register texts flagged,
#                          0 of 6 in-register texts flagged.
#
#   GATE-2 HELD-OUT CORPUS — 12 texts, 90 to 447 words, written by the reviewer
#   after the two-channel rebuild and never seen here until it refuted the
#   previous constant. This is the corpus that produced the blocker.
#     band               : (+1.46, +24.25]   width 22.79
#     verdict            : 5 sits inside it. 6 of 6 wrong-register texts flagged,
#                          0 of 6 in-register texts flagged.
#
# ── HEADROOM: MEASURED, and the previous claim here was WRONG ────────────────
# This block used to read "8.00 points of margin before a false positive and 1.21
# before a miss ... this mechanism is closer to missing contaminated copy than to
# blocking clean copy." On held-out text the true ordering was the exact
# opposite: -3.0 before a false positive and +14.8 before a miss. The mechanism
# was far more likely to block good copy than to pass bad copy, and the sentence
# claiming otherwise was measured on a corpus that did not contain the shape that
# breaks it. That is the second time a confident sentence in this block has been
# refuted, so the numbers below are stated as what they are — the WORST case over
# every text this module has ever been measured against, all three corpora
# pooled, with nothing left held out.
#
#     before a FALSE POSITIVE : +2.00   (binding text: the 80-word Recovery
#                                        section, athletic/fitt axis)
#     before a MISS           : +0.91   (binding text: the 923-word Culture
#                                        section written as a profile,
#                                        athletic/people axis)
#
# Both are under one marker hit at the length of the text that binds them, and
# the pooled band is 2.91 points wide against a scale whose smallest unit is 2.
# So: this constant is NOT comfortably placed in either direction, and no honest
# reading of the data says otherwise. See THE RESOLUTION LIMIT below.
#
# NOTHING IS HELD OUT ANY MORE. All three corpora above were consulted while
# fixing the marker set, so none of them can refute this constant. The next
# calibration needs text none of these three contain.
#
# The band must exist before a margin means anything: the tests fail loudly if
# any corpus's two halves ever overlap.
DENSITY_BASELINE_WORDS = 100
CROSS_CONTAMINATION_MARGIN = 5

# ── THE RESOLUTION LIMIT — a documented limitation, not a tuning problem ─────
# Measured across 18 texts, eight reported features about a person and ten
# profiles, per 100 words (the table is repeated at PEOPLE_NEGATIVE_SOURCED):
#
#     profile access     reports 0.00-2.65   profiles 1.52-5.15   overlaps
#     personal pronoun   reports 1.13-5.52   profiles 3.03-9.79   overlaps
#     personal-life verb reports 0.00-0.53   profiles 0.00-1.25   overlaps
#     SOURCING           reports 0.88-2.61   profiles 0.00-0.52   separates
#
# On the athletic/people axis exactly ONE marker family carries signal, and its
# whole dynamic range is about 2.6 markers per 100 words — roughly 5 points of
# density, counted on both sides. Everything else is noise that varies by more
# than that. So the mechanism's resolution on this axis is a handful of points,
# and the threshold has to be placed inside it. That is why the pooled band is
# 2.91 wide and why two of the three previous constants were refuted on this
# axis and not on any other.
#
# The DERIVATION band is now 4.15 and the pooled band is still 2.91. Read that
# gap the right way round: the derivation corpus is the one the constant came
# from and it cannot refute anything, so the pooled figure is the bound and the
# resolution limit stands unchanged. REPORTING_MACHINERY (above) added a second
# family with signal on this axis, but only in one direction — its presence
# argues for reporting, its absence argues for nothing — so it raises the
# ceiling on how well a REPORT can be recognised without raising the floor on
# how badly a profile can be missed.
#
# This is a property of a lexical fingerprint, not of the number. A fifth
# constant will not widen the band. What would: counting DISTINCT sources rather
# than attributions (a report cites several people, a profile quotes one), which
# needs entity resolution this module does not have and should not grow without a
# corpus to validate it on. Until then the honest statement is that VoiceLint
# separates a report from a profile with about one marker of headroom, and that
# borderline copy on this axis will need a human.
#
# KNOWN EVASION, recorded rather than fixed: a profile written in surnames and
# attribution tags instead of pronouns ("Varga says" for "she says") reads
# athletic to this module and clears the gate. It was found while building the
# derivation corpus. It is a real hole, and it is the same hole as the paragraph
# above — one source quoted many times is indistinguishable here from many
# sources quoted once.

# ── THE RESIDUAL HOLE: a report with no machinery is NOT separable ───────────
# PRONOUN_ATTRIBUTION plus REPORTING_MACHINERY (above) fixes the reported
# feature that de-duplicates its source's name AND records having asked
# somebody. It does NOT fix, and nothing in a lexical fingerprint can fix, the
# reported feature that records no asking at all.
#
# The binding case is the reviewer's D2: a 315-word Training feature about one
# athlete's injury and comeback, one named source quoted twice as "he says", no
# institution, no non-response, no provenance, every number spelled out in
# words. It reads +31.97 people-over-athletic and hard-fails. Beside it, the
# reviewer's E1 — a quiet PROFILE submitted as Culture, which must fail — is
# structurally identical on every axis this module can see:
#
#                             D2 (report, must pass)   E1 (profile, must fail)
#     athletic section-level          -8                        -8
#     athletic per-occurrence          0                         0
#     named attributions               0                         0
#     machinery of asking              0                         0
#     pronoun attributions/100w     0.63                      0.47
#     profile access/100w           1.27                      3.32
#
# The two differ in ONE measurable: people per-occurrence density, 13.97 against
# 27.49. That is not a register signal, it is a length-normalised count of how
# much human colour each carries, and D4 — an in-register profile — sits at
# 14.03, on top of D2. Any uniform shift large enough to clear D2 (27 points)
# also clears E2 (28 points) and turns a wrong-register profile loose.
#
# WHAT WAS TRIED AND MEASURED. Five licences for pronoun attribution, crossed
# with athletic-credit-only versus credit-and-debit, with and without an
# indirect-speech restriction, and with and without the gate accepting a
# licensed pronoun — 20 configurations over 97 labelled texts:
#
#     licence                                  fixes D2?   cost
#     any earlier non-pronoun attribution         no       1 miss (a profile)
#     >= 2 distinct named sources                 no       none, and no effect
#     machinery of asking (SHIPPED)               no       see below
#     a named person appears at all               no       1 miss (a profile)
#     ... plus the gate accepting the pronoun     no       1 miss (a profile)
#
# Not one configuration fixed D2. The two that moved it at all did so by
# licensing pronoun attribution on the mere presence of a name, which is the
# people gate's own test, and both turned VAL_X_CULTURE_AS_PEOPLE into a miss
# while leaving D2 failing anyway.
#
# WHICH WAY THE MODULE ERRS, AND WHY. It errs toward the FALSE POSITIVE: a
# correctly-written single-subject report with no reporting machinery is
# blocked. That is the right side of this trade for this product. A blocked
# section is handed back to a writer who can see the flag, argue with it, and
# ship the piece; the orchestrator makes the flag blocking rather than advisory
# precisely so a human looks. A missed cross-register section ships as the
# magazine's voice and nobody ever looks again. The cost of the false positive
# is one editorial conversation; the cost of the miss is the defect this module
# exists to catch, published.
#
# WHAT WOULD ACTUALLY CLOSE IT, and it is not a marker: knowing whether the
# section's subject is its SOURCE or its STORY. That is a question about what
# the non-quote prose is ABOUT — events and decisions that exist independently
# of the subject, versus the subject's own life — and it needs semantics this
# module does not have and cannot get from a regex. Until then, borderline
# single-source human-interest copy on this axis needs a human, which is the
# same conclusion THE RESOLUTION LIMIT reached by a different route.
#
# COST OF THE SHIPPED RULE, measured rather than rounded off. Licensing pronoun
# attribution on machinery moves the weakest cross-register text in the
# derivation corpus — the 852-word surname-tagged quiet profile — from +6.57 to
# +5.98 against a margin of 5. Headroom before that text becomes a miss falls
# from 1.57 to 0.98 points. Injecting machinery sentences into it turns it into
# a miss after 2 injections where the previous build took 3. The rule widens the
# KNOWN EVASION above by about one sentence. It buys, in exchange, invariance to
# an editing decision that no editor should have to think about.

# ── Is contamination allowed to fail a section? YES. ─────────────────────────
# It was not, and that was an accident rather than a decision. One flag cost 10
# against a 15-point budget, so a section strong in its own register absorbed
# the hit and passed; the orchestrator then routes a PASSING section's flags to
# advisory, so a Training section written as a pure People profile shipped at 90
# with a note. A section in the wrong register is the whole defect this module
# exists to find, and finding it and then waving it through is worse than not
# looking.
#
# So the penalty is denominated to exceed the entire negative-evidence budget:
# one contamination flag costs NEGATIVE_MARKER_BUDGET + 1 negative markers, so
# even a section that is otherwise perfect (delta 0, clamped score 100) lands at
# 82 and fails. `passed` stays exactly `score >= PASS_THRESHOLD`, so this needs
# no second pass/fail rule and the orchestrator moves the flags from advisory to
# blocking on its own.
#
# This is a deliberate trade against the headroom above: a false positive now
# blocks a section rather than annotating it. It is made on the evidence that
# the validation corpus produced zero false positives with 7.95 points to spare,
# and it is the side of the trade the product wants, because a blocked section
# gets rewritten and an advisory note gets ignored.
CROSS_CONTAMINATION_PENALTY = (NEGATIVE_MARKER_BUDGET + 1) * -NEGATIVE_HIT   # 18
