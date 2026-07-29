# -*- coding: utf-8 -*-
"""
synthlint.py — SynthLint, the AI-fingerprint linter for the TIMBR eval harness.

WHAT IT IS FOR
--------------
ProhibLint scores what the handbook bans. VoiceLint scores which register the
copy is written in. CharLint scores whether it fits the layout. None of them
asks the question this module asks: does this read like a machine wrote it?
"Sounding like an LLM" is a defect on every TIMBR product line, so SynthLint
runs UNIVERSALLY — there is no ruleset switch here, deliberately.

WHAT IT REFUSES TO DO
---------------------
  * Em-dashes. ProhibLint owns them, ruleset-aware, and it counts ASIDES rather
    than dashes for a reason. Nothing here touches punctuation.
  * "Is this paragraph filler / redundant?" That is the editorial board's
    qualitative call. A mechanical count cannot make it and should not pretend.
  * Type-token vocabulary diversity. Too noisy; it punishes concision, which is
    the house voice.
  * Triad rate. Measured, found to point the wrong way, dropped. The full
    numbers are in synth_config.DROPPED_CHECKS.

A NOTE ON WHAT THE RHYTHM CHECK MEASURES
----------------------------------------
Check 5 asks whether sentence lengths vary. It is the one check whose unit
depends on the shape of the text: an enumerated spec list — PRINCIPLES Sec.
12's locked exercise table, "- Name: sets x reps — cue" — has no sentence
rhythm to be flat, because its rows are a format rather than prose. On those
the check measures the free-text field inside each row instead. It is not
switched off; see synth_config's "CHECK 5, PART TWO" for the derivation and
for the evasion attempts it had to survive.

API
---
    run_synthlint(text) -> {"violations": [str], "score": int,
                            "passed": bool, "flags": {...}}

Every check is independently callable and returns the repo's standard
(violations, penalty, hard_fail) triple, penalties negative.

Run: cd synthlint && python3 -m pytest test_synthlint.py -q
"""

import re
import statistics

try:                                    # repo-root pytest
    from synthlint import synth_config as C
except ImportError:                     # cd synthlint && pytest
    import synth_config as C


__all__ = [
    "check_ai_vocabulary",
    "check_transition_density",
    "check_contrastive_frames",
    "check_hedge_stacking",
    "check_burstiness",
    "check_repeated_openers",
    "run_synthlint",
    "split_sentences",
    "split_paragraphs",
    "word_count",
    "burstiness",
    "is_spec_list",
    "spec_list_rows",
    "spec_list_fields",
]


# ---------------------------------------------------------------------------
# Text segmentation
# ---------------------------------------------------------------------------
# SynthLint owns its own splitter rather than importing prohiblint's private
# _split_into_sentences. The reason is calibration, not pride: every threshold
# in synth_config is a statistic computed by THESE functions, and a change to
# another module's private helper would silently move this module's numbers
# without failing its tests. Segmentation here is a measured input, so it is
# pinned here.

_WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*|\d+(?:[.,:/]\d+)*[%$]?|[$][\d.,]+")

#: Abbreviations that end in a period without ending a sentence. Short list on
#: purpose: a missed split raises the measured variance, which pushes the
#: burstiness check AWAY from firing, so errors here are safe in the direction
#: that matters.
_ABBREVIATIONS = frozenset("""
Dr Mr Mrs Ms Prof Sr Jr St Ave Blvd Rd Ln Ct Sq Mt Ft
approx est vs etc ie eg cf al inc Inc Co Ltd No no
a b c d e f g h i j k l m n o p q r s t u v w x y z
""".split())

_SENTENCE_BREAK_RE = re.compile(r'(?<=[.!?])["\'”’)\]]*\s+')
_ABBREV_TAIL_RE = re.compile(r"(?:^|[\s(\[\"'])([A-Za-z]+)\.[\"'”’)\]]*$")


def _ends_with_abbreviation(fragment):
    m = _ABBREV_TAIL_RE.search(fragment.strip())
    return bool(m) and m.group(1) in _ABBREVIATIONS


def split_sentences(text):
    """Split into sentences. Line breaks are hard boundaries.

    A newline always ends a sentence: TIMBR copy sets workout rows, menu rows
    and headings on their own lines with no terminal punctuation, and gluing
    them onto the following prose would corrupt every length statistic here.
    """
    out = []
    for line in re.split(r"\n+", text):
        line = line.strip()
        if not line:
            continue
        pieces = _SENTENCE_BREAK_RE.split(line)
        buf = ""
        for piece in pieces:
            buf = (buf + " " + piece).strip() if buf else piece
            if _ends_with_abbreviation(buf):
                continue          # "Dr." — keep absorbing
            out.append(buf)
            buf = ""
        if buf:
            out.append(buf)
    return [s for s in out if _WORD_RE.search(s)]


def split_paragraphs(text):
    """Split into paragraphs.

    A blank line separates paragraphs. A single newline does too: the magazine
    sections in this repo are single-newline separated and treating the whole
    section as one paragraph would erase the denominator Check 2 divides by.
    """
    return [p.strip() for p in re.split(r"\n\s*\n+|\n", text) if p.strip()]


def word_count(text):
    return len(_WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# Check 1 — extended AI vocabulary
# ---------------------------------------------------------------------------
def check_ai_vocabulary(text):
    """Flag connector/filler phrases that mark machine prose.

    Terms already carried by prohiblint.AI_BLOCKLIST are excluded at import
    time (synth_config.EXTENDED_AI_VOCAB), so no word is priced twice across
    the two linters.

    Penalty: VOCAB_PENALTY_TELLS per hit. Hard fail at VOCAB_HARD_FAIL_HITS.
    Returns (violations, penalty, hard_fail).
    """
    violations = []
    total = 0
    for term in C.EXTENDED_AI_VOCAB:          # stable order, not dict order
        hits = C.VOCAB_PATTERNS[term].findall(text)
        if hits:
            total += len(hits)
            violations.append(
                f"AI vocabulary '{term}' found {len(hits)} time(s). "
                f"Penalty: {len(hits) * C.VOCAB_PENALTY_TELLS * -C.TELL}."
            )
    penalty = total * C.VOCAB_PENALTY_TELLS * -C.TELL
    hard_fail = total >= C.VOCAB_HARD_FAIL_HITS
    if hard_fail:
        violations.append(
            f"AI vocabulary hard fail: {total} total hits "
            f"(threshold: {C.VOCAB_HARD_FAIL_HITS}). The text is scaffolding."
        )
    return violations, penalty, hard_fail


# ---------------------------------------------------------------------------
# Check 2 — formulaic transition density
# ---------------------------------------------------------------------------
def transition_openers(text):
    """Paragraphs that OPEN with a formulaic transition. Returns [(i, term)]."""
    found = []
    for i, para in enumerate(split_paragraphs(text)):
        m = C.TRANSITION_OPENER_RE.match(para)
        if m:
            found.append((i, m.group(1)))
    return found


def check_transition_density(text):
    """Flag paragraph-initial formulaic transitions as a RATE.

    Not presence — one connective adverb is a word, and Check 1 already prices
    it. This is the surcharge for opening more than one paragraph in five with
    one, which is the LLM habit of signposting every paragraph as list item n.

    Returns (violations, penalty, hard_fail). hard_fail is always False: a
    signposting habit is a bad shape, not a disqualification.
    """
    paras = split_paragraphs(text)
    n = len(paras)
    if n < C.FORMULAIC_TRANSITION_MIN_PARAGRAPHS:
        return [], 0, False

    hits = transition_openers(text)
    if len(hits) < C.FORMULAIC_TRANSITION_MIN_HITS:
        return [], 0, False

    rate = len(hits) / n
    if rate <= C.FORMULAIC_TRANSITION_RATE_MAX:
        return [], 0, False

    extra = len(hits) - C.FORMULAIC_TRANSITION_MIN_HITS
    tells = C.TRANSITION_DENSITY_BASE_TELLS + extra * C.TRANSITION_DENSITY_PER_EXTRA_HIT
    terms = ", ".join(sorted({t.lower() for _, t in hits}))
    return (
        [f"Formulaic transition density: {len(hits)} of {n} paragraphs "
         f"({rate:.2f}) open with a formulaic transition ({terms}); "
         f"threshold {C.FORMULAIC_TRANSITION_RATE_MAX:.2f}. "
         f"Penalty: {tells * -C.TELL}."],
        tells * -C.TELL,
        False,
    )


# ---------------------------------------------------------------------------
# Check 3 — contrastive-frame overuse
# ---------------------------------------------------------------------------
def contrastive_frames(text):
    """Return [(pattern_name, matched_text)] for every compressed pivot."""
    found = []
    for name, pat in C.CONTRASTIVE_PATTERNS.items():
        for m in pat.finditer(text):
            found.append((name, m.group(0)))
    return found


def check_contrastive_frames(text):
    """Flag "not just X, it's Y" pivots as a RATE per CONTRASTIVE_RATE_WINDOW.

    A single pivot is never a violation: it is a legitimate rhetorical move and
    a cousin of PRINCIPLES Sec. 7's concede-then-redirect. Reaching for it
    repeatedly is the fingerprint.

    Returns (violations, penalty, hard_fail); hard_fail always False.
    """
    words = word_count(text)
    if words < C.CONTRASTIVE_MIN_WORDS:
        return [], 0, False

    hits = contrastive_frames(text)
    if len(hits) < C.CONTRASTIVE_MIN_HITS:
        return [], 0, False

    rate = len(hits) * C.CONTRASTIVE_RATE_WINDOW / words
    if rate <= C.CONTRASTIVE_RATE_MAX:
        return [], 0, False

    extra = len(hits) - C.CONTRASTIVE_MIN_HITS
    tells = C.CONTRASTIVE_BASE_TELLS + extra * C.CONTRASTIVE_PER_EXTRA_FRAME
    sample = "; ".join(repr(h[1]) for h in hits[:3])
    return (
        [f"Contrastive-frame overuse: {len(hits)} frames in {words} words "
         f"({rate:.2f} per {C.CONTRASTIVE_RATE_WINDOW}w, threshold "
         f"{C.CONTRASTIVE_RATE_MAX:.2f}). e.g. {sample}. "
         f"Penalty: {tells * -C.TELL}."],
        tells * -C.TELL,
        False,
    )


# ---------------------------------------------------------------------------
# Check 4 — hedge stacking
# ---------------------------------------------------------------------------
def _clauses(sentence):
    return [c for c in C.CLAUSE_SPLIT_RE.split(sentence) if c and c.strip()]


def hedge_stacks(text):
    """Return [(kind, a, b, clause)] for every stacked-hedge clause.

    At most ONE stack is reported per clause. A clause with three compounding
    hedges is one defect, not two, and counting the pairs would price a single
    bad sentence like a habit.
    """
    found = []
    for sentence in split_sentences(text):
        for clause in _clauses(sentence):
            marks = list(C.HEDGE_RE.finditer(clause))
            stacked = None
            for a, b in zip(marks, marks[1:]):
                gap = len(_WORD_RE.findall(clause[a.end():b.start()]))
                if gap <= C.HEDGE_STACK_MAX_GAP_WORDS:
                    stacked = ("adjacent", a.group(0), b.group(0))
                    break
            if stacked is None:
                fm = C.HEDGE_FRAME_RE.search(clause)
                if fm and C.HEDGE_RE.search(clause[fm.end():]):
                    stacked = ("frame", fm.group(0),
                               C.HEDGE_RE.search(clause[fm.end():]).group(0))
            if stacked is not None:
                found.append(stacked + (clause.strip(),))
                continue
            # A frame in one clause reaching a hedge later in the SAME sentence
            # ("It is possible that the effect, in some lifters, might vary").
            fm = C.HEDGE_FRAME_RE.search(clause)
            if fm:
                tail = sentence[sentence.find(clause) + len(clause):]
                hm = C.HEDGE_RE.search(tail)
                if hm:
                    found.append(("frame-sentence", fm.group(0), hm.group(0),
                                  sentence.strip()))
    return found


def check_hedge_stacking(text):
    """Flag TWO OR MORE hedges compounding on one proposition.

    Distinct from the single-hedge lists already in the repo
    (voice_config.FITT_NEGATIVE[0]); see synth_config for the full note. There
    is no legitimate density for stacking, so every instance is a violation and
    this check has no rate.

    Returns (violations, penalty, hard_fail).
    """
    stacks = hedge_stacks(text)
    if not stacks:
        return [], 0, False

    violations = [
        f"Hedge stacking ({kind}): '{a}' + '{b}' compounding in one clause — "
        f"{clause[:70]!r}. Penalty: {C.HEDGE_STACK_TELLS * -C.TELL}."
        for kind, a, b, clause in stacks
    ]
    hard_fail = len(stacks) >= C.HEDGE_STACK_HARD_FAIL
    if hard_fail:
        violations.append(
            f"Hedge-stacking hard fail: {len(stacks)} stacked clauses "
            f"(threshold: {C.HEDGE_STACK_HARD_FAIL})."
        )
    return violations, len(stacks) * C.HEDGE_STACK_TELLS * -C.TELL, hard_fail


# ---------------------------------------------------------------------------
# Check 5 — sentence-length burstiness
# ---------------------------------------------------------------------------
def spec_list_rows(text):
    """Return the row bodies if `text` is a spec list, else None.

    A spec list is an enumerated table set as text: PRINCIPLES Sec. 12's locked
    exercise block, "- Name: sets x reps — cue", nine rows to a page. It is not
    prose and it has no sentence rhythm, so the rhythm check governs a different
    unit on it (see check_burstiness). Detection is a plain conjunction, every
    clause derived in synth_config:

      1. at least SPEC_LIST_MIN_ROWS non-blank lines;
      2. EVERY non-blank line opens with a list marker — one prose line and the
         text is not a list;
      3. no row ends in terminal punctuation — a row is labelled fields, not a
         predication;
      4. every row shares at least SPEC_LIST_MIN_SHARED_DELIMITERS distinct
         structural delimiters with every other row, which is what "filled from
         the same skeleton" means mechanically. One shared dash is not enough,
         deliberately.

    Bodies are returned with the marker stripped. None (not []) means "not a
    spec list", so the caller can tell an empty text from a declined one.
    """
    rows = [line.strip() for line in (text or "").split("\n") if line.strip()]
    if len(rows) < C.SPEC_LIST_MIN_ROWS:
        return None
    if not all(C.SPEC_LIST_MARKER_RE.match(r) for r in rows):
        return None

    bodies = [C.SPEC_LIST_MARKER_RE.sub("", r, count=1).strip() for r in rows]
    if not all(bodies):
        return None
    if any(C.SPEC_LIST_TERMINAL_RE.search(b) for b in bodies):
        return None

    shared = set.intersection(*(set(C.SPEC_LIST_DELIM_RE.findall(b))
                                for b in bodies))
    if len(shared) < C.SPEC_LIST_MIN_SHARED_DELIMITERS:
        return None
    return bodies


def is_spec_list(text):
    """True when `text` is an enumerated spec list rather than prose."""
    return spec_list_rows(text) is not None


def spec_list_fields(text):
    """The longest free-text field of each row of a spec list.

    The rhythm-bearing unit of a templated row: split the row on its structural
    delimiters and keep the field carrying the most words. Longest rather than
    last because prose can sit in the label as easily as in the cue, and a
    cue-only rule would miss it there. Returns [] when `text` is not a spec
    list.
    """
    bodies = spec_list_rows(text)
    if bodies is None:
        return []
    fields = []
    for body in bodies:
        parts = [p.strip() for p in C.SPEC_LIST_DELIM_RE.split(body) if p.strip()]
        if parts:
            fields.append(max(parts, key=word_count))
    return [f for f in fields if _WORD_RE.search(f)]


def _rhythm(units):
    """(n, mean, stdev, cv) over a list of text units. Population stdev."""
    lengths = [word_count(u) for u in units]
    if not lengths:
        return 0, 0.0, 0.0, 0.0
    mean = statistics.mean(lengths)
    sd = statistics.pstdev(lengths)
    return len(lengths), mean, sd, (sd / mean if mean else 0.0)


def burstiness(text):
    """Return (n_sentences, mean_words, stdev_words, cv).

    Population stdev, so the value describes the spread of THIS text rather
    than estimating a population it was drawn from. cv is 0.0 when the mean is
    0 (no words), which cannot reach the check: the sentence-count gate is
    checked first.

    Always the SENTENCE statistic, on any text — it is the module's public
    measurement and scorecards report it. check_burstiness is the one that
    switches unit on a spec list; this does not.
    """
    return _rhythm(split_sentences(text))


def check_burstiness(text):
    """Flag suspiciously uniform rhythm.

    Two gates before the statistic is trusted at all: at least
    BURSTINESS_MIN_SENTENCES units (below that CV is noise), and a mean of
    at least BURSTINESS_MIN_MEAN_WORDS (below that the text is in the staccato
    register PRINCIPLES Sec. 7 endorses, where uniformity is the device).

    THE UNIT DEPENDS ON THE SHAPE. On prose it is the sentence. On a spec list
    it is the longest free-text field of each row: the rows themselves are a
    locked format whose uniformity is the format, and measuring their rhythm is
    a category error, but the field inside them is written rather than filled
    and it is still held to the floor. The gates and the floor are the same
    numbers in both modes; only what they are applied to changes.

    Returns (violations, penalty, hard_fail); hard_fail always False — the
    score already fails a flat text on its own.
    """
    spec = is_spec_list(text)
    if spec:
        unit, units = "row-field", spec_list_fields(text)
    else:
        unit, units = "sentence", split_sentences(text)

    n, mean, sd, cv = _rhythm(units)
    if n < C.BURSTINESS_MIN_SENTENCES:
        return [], 0, False
    if mean < C.BURSTINESS_MIN_MEAN_WORDS:
        return [], 0, False
    if cv >= C.BURSTINESS_CV_FLOOR:
        return [], 0, False

    gap = C.BURSTINESS_CV_FLOOR - cv
    extra = int(gap / C.BURSTINESS_PER_CV_STEP)
    tells = C.BURSTINESS_BASE_TELLS + extra
    where = (" The rows are a spec list, so this measures the free-text field "
             "inside each row, not the rows." if spec else "")
    return (
        [f"Flat sentence rhythm: {n} {unit}s, mean {mean:.1f} words, "
         f"stdev {sd:.1f}, CV {cv:.3f} (floor {C.BURSTINESS_CV_FLOOR:.2f}). "
         f"Real prose alternates short and long; this does not.{where} "
         f"Penalty: {tells * -C.TELL}."],
        tells * -C.TELL,
        False,
    )


# ---------------------------------------------------------------------------
# Check 6 — repeated-opener runs
# ---------------------------------------------------------------------------
_FIRST_WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
#: Number TOKENS, not digits. "It is 2026." carries one number, not four.
_NUMBER_RE = re.compile(r"\d+(?:[.,:/]\d+)*")


def _first_word(sentence):
    m = _FIRST_WORD_RE.search(sentence)
    return m.group(0).lower() if m else ""


def _is_generic_opener(sentence):
    return bool(C.GENERIC_OPENER_RE.match(sentence.strip().lstrip("\"'“‘([")))


def _is_anaphora(run):
    """Every sentence short enough to be a rhetorical figure, not exposition."""
    return all(word_count(s) <= C.ANAPHORA_MAX_WORDS for s in run)


def _is_data_listing(run):
    """Every sentence carries enough numbers to be a spec/menu row."""
    return all(len(_NUMBER_RE.findall(s)) >= C.DATA_LISTING_MIN_NUMBERS
               for s in run)


def _runs(flags):
    """Yield (start, end_exclusive) spans of consecutive truthy equal keys."""
    i = 0
    while i < len(flags):
        key = flags[i]
        j = i
        while j + 1 < len(flags) and flags[j + 1] == key:
            j += 1
        yield key, i, j + 1
        i = j + 1


def repeated_opener_runs(text):
    """Return [(kind, run_length, sentences)] for every flagged run.

    Same-word runs are collected first, then generic-class runs; a run whose
    sentences are already entirely covered by runs reported before it is
    dropped, so one bad passage is priced once. See synth_config note (e).
    """
    sentences = split_sentences(text)
    found = []
    covered = set()

    def take(kind, start, end):
        span = set(range(start, end))
        if span <= covered:
            return
        covered.update(span)
        found.append((kind, end - start, sentences[start:end]))

    # (a) same first word, length >= SAME_OPENER_RUN_MIN
    for key, start, end in _runs([_first_word(s) for s in sentences]):
        if not key or end - start < C.SAME_OPENER_RUN_MIN:
            continue
        run = sentences[start:end]
        if _is_anaphora(run) or _is_data_listing(run):
            continue
        take("same-opener", start, end)

    # (b) generic demonstrative + verb, length >= GENERIC_OPENER_RUN_MIN
    for key, start, end in _runs([_is_generic_opener(s) for s in sentences]):
        if not key or end - start < C.GENERIC_OPENER_RUN_MIN:
            continue
        run = sentences[start:end]
        if _is_anaphora(run) or _is_data_listing(run):
            continue
        take("generic-opener", start, end)

    return found


def check_repeated_openers(text):
    """Flag chains of sentences that all start the same way.

    Two rules with different thresholds, and two exemptions, all derived in
    synth_config: TIMBR's own parallelism device is a triad of SHORT lines, and
    its menu blocks are number-dense listings. Both are exempted by shape, not
    by carve-out.

    Returns (violations, penalty, hard_fail); hard_fail always False.
    """
    runs = repeated_opener_runs(text)
    if not runs:
        return [], 0, False

    violations = []
    for kind, length, run in runs:
        opener = " ".join(run[0].split()[:2])
        violations.append(
            f"Repeated-opener run ({kind}): {length} consecutive sentences "
            f"opening {opener!r} — {run[0][:60]!r}... "
            f"Penalty: {C.OPENER_RUN_TELLS * -C.TELL}."
        )
    return violations, len(runs) * C.OPENER_RUN_TELLS * -C.TELL, False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
#: (flag key, function). Order is the order violations appear in the output.
CHECKS = (
    ("ai_vocabulary", check_ai_vocabulary),
    ("transition_density", check_transition_density),
    ("contrastive_frames", check_contrastive_frames),
    ("hedge_stacking", check_hedge_stacking),
    ("burstiness", check_burstiness),
    ("repeated_openers", check_repeated_openers),
)


def run_synthlint(text):
    """
    Run every SynthLint check over one text.

    Universal: no ruleset argument, by design. Reading like an LLM is a defect
    on the magazine line and the workout series alike.

    Returns (shape is fixed; keys are never removed or renamed):
        {
          "violations": [str, ...],
          "score": int,            # SCORE_START, penalties applied, clamped >=0
          "passed": bool,          # no hard fail AND score >= PASS_THRESHOLD
          "flags": {
            check_name: {"violations": [...], "penalty": int,
                         "hard_fail": bool},
            ...,
            "_metrics": {...},     # the measured statistics, for scorecards
          },
        }
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise TypeError(
            f"run_synthlint expects str, got {type(text).__name__}. "
            f"SynthLint scores ONE text; callers holding a sections dict "
            f"should loop and call once per section."
        )

    violations = []
    flags = {}
    penalty = 0
    hard_fail = False

    for name, check in CHECKS:
        v, p, hf = check(text)
        violations.extend(v)
        penalty += p
        hard_fail = hard_fail or hf
        flags[name] = {"violations": v, "penalty": p, "hard_fail": hf}

    n, mean, sd, cv = burstiness(text)
    flags["_metrics"] = {
        "words": word_count(text),
        "paragraphs": len(split_paragraphs(text)),
        "sentences": n,
        "mean_sentence_words": round(mean, 2),
        "stdev_sentence_words": round(sd, 2),
        "burstiness_cv": round(cv, 4),
        # True when the text is an enumerated spec list. The sentence figures
        # above are still the sentence figures — they are a measurement, not a
        # verdict — but on a spec list they describe rows of a locked table, so
        # a flat CV here with no violation beside it is the format, not a miss.
        "spec_list": is_spec_list(text),
        "total_tells": abs(penalty) // C.TELL,
    }

    score = max(0, C.SCORE_START + penalty)
    return {
        "violations": violations,
        "score": score,
        "passed": (not hard_fail) and (score >= C.PASS_THRESHOLD),
        "flags": flags,
    }
