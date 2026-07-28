"""
charlint.py — CharLint module for the TIMBR eval harness.

Enforces the char-count locks of PRINCIPLES.txt Section 3 ("CHAR-COUNT LOCKS —
THE LAYOUT IS LAW"):

    "Once a page is owner-approved, every dynamic text slot is locked to the
     EXACT character count of the approved baseline (including spaces) ...
     Counts are exact, not approximate: never hand-count, always machine-count
     ... If a count breaks, the layout breaks — line wraps, overflows, rhythm."

CharLint is that machine count. It is the gate between "copy someone wrote" and
"copy that can be poured into a locked Canva box".

Usage:
    from charlint import run_charlint, load_locks, chars_to_target

    locks = load_locks("charlint/locks_seattle_series.json")
    results = run_charlint({"cover_body": "...", ...}, locks)

    # or let run_charlint load it (any path — nothing is hard-coded):
    results = run_charlint(candidates, "charlint/locks_seattle_series.json")

    # writer convergence loop (PRINCIPLES Sec. 3: "swapping word-level
    # alternates until the count lands on the lock to the character"):
    chars_to_target("cover_body", draft, locks)
    # -> {..., "chars_needed": -3, "action": "remove", "message": "..."}

Design notes that are load-bearing — read before changing anything:

  * CHARACTERS, NOT BYTES. Baselines carry em-dashes (U+2014), en-dashes
    (U+2013), curly apostrophes, é and middle dots (·). len() on a Python 3
    str is the correct measure; len(s.encode("utf-8")) is NOT and would let
    real overflows through (see test_charlint.py::TestUnicode).

  * NO WHITESPACE NORMALIZATION. Candidate text is never stripped, trimmed or
    collapsed before counting. A trailing space is a real character that
    really breaks a real layout, and newlines inside an element are characters
    too. We count exactly what the layout will receive.

  * CANONICAL FORM: NFC, AND ONLY NFC. Counting is done on the canonically
    composed (NFC) form of the text. This is NOT an exception to the rule
    above — it is a different problem, and the two do not overlap:

      - Whitespace normalisation DELETES characters the writer typed. NFC
        deletes nothing: it only re-encodes a character that has two legal
        spellings (é as U+00E9, or as "e" + U+0301) into the one the layout
        renders. NFC touches no whitespace at all — space, tab, newline and
        even U+00A0 are all NFC-invariant.
      - Without it, NFD input produces a PHANTOM overflow. macOS filesystems,
        editors and clipboards emit NFD routinely, so "café" arrives as five
        code points and the gate says "OVERFLOW by 1 — remove 1 character".
        There is no character to remove: the text is visually identical to the
        baseline and renders identically in the box. An instruction a writer
        cannot act on is worse than no gate, and the owner's standing rule is
        that char counts must never break.
      - NFC, never NFKC. NFKC is a COMPATIBILITY mapping: it rewrites U+00A0
        to a plain space, "…" to "...", ligatures to their parts. Those are
        real edits to the text and would silently launder exactly the
        whitespace defects the rule above exists to catch.
      - Every other character in the baselines — em-dash, en-dash, middle dot,
        curly apostrophe — has no canonical decomposition, so NFC is the
        identity on them. The decision changes nothing for them by design.

    Canonical equivalence is applied uniformly: it is how CharLint measures a
    count-locked slot AND how it compares a PERMANENT slot. Two canonically
    equivalent code point sequences are the SAME TEXT, so the same answer has
    to come back either way. When the raw candidate is not already NFC the run
    says so in a warning (never a failure) and the per-slot result carries
    `nfc_normalized: True`, so the re-encoding is recorded, never silent.

  * WHOLE ELEMENT, NEVER A SUB-SLICE. One Canva element can hold a title line,
    a rule line, a blank line and prose (see the `night_page` slot: 616 chars
    = the whole element, header block included). Newlines are characters.

  * ENFORCED LOCK vs DOCUMENTED LOCK. A slot may carry both `principles_lock`
    (the number written down in PRINCIPLES.txt) and `observed` (the number the
    live template actually measures). CharLint enforces `observed` when it is
    present, `principles_lock` otherwise — the live template is what the copy
    has to fit. Any disagreement between the two is reported as a WARNING on
    every single run and never silently absorbed: the owner decides which
    number is canonical, the harness just keeps asking.

Return shape matches the sibling linters (prohiblint / voicelint) so the
orchestrator can consume all three uniformly. The verdict, however, is NOT a
threshold: a count-locked slot passes if and only if it lands on its lock
within the declared tolerance. `score` starts at 100 and takes penalties, but
it is a SEVERITY READ-OUT only — how badly the copy missed, for triage — and
is never consulted in the pass/fail decision. One character over is a hard
fail at score 90 exactly as it is at score 0, because one character over
breaks the layout either way (PRINCIPLES.txt Sec. 3). There is deliberately no
PASS_THRESHOLD constant in this module: a threshold is what a char lock is
not.
"""

import json
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Tolerance used when a locks file does not declare one. 0 = exact match,
#: including spaces (PRINCIPLES.txt Sec. 3). Files may override via
#: their top-level "tolerance" field, but 0 is the product standard.
DEFAULT_TOLERANCE = 0

#: The canonical form every count is taken in, and every comparison made in.
#: NFC, never NFKC — see the "CANONICAL FORM" note in the module docstring.
CANONICAL_FORM = "NFC"

PENALTY_PER_CHAR = -10          # per character outside the lock
MAX_CHAR_PENALTY = -100         # floor for the per-character penalty
PENALTY_PERMANENT_MUTATION = -100
PENALTY_NOT_FILLED = -100

#: Convenience pointer to the locks captured from Canva design DAHQoZJm12w.
#: Provided so callers and tests have a discoverable path — it is NOT a
#: default: run_charlint() requires the caller to name a locks file, so other
#: volumes and future product lines can supply their own.
SEATTLE_SERIES_LOCKS = str(Path(__file__).with_name("locks_seattle_series.json"))

# PRINCIPLES.txt Section 4 — the slot taxonomy. Every `type` in a locks file
# must be one of these; an unrecognised type is a corrupt file, not a shrug.
SLOT_TYPES = (
    "FIXED",              # urls, footers, header strips — never touched
    "PERMANENT",          # the brand line — never touched
    "ROLLS MONTHLY",      # the issue/date line
    "ROLLS PER VOLUME",   # title, kicker, neighborhood, overview
    "DYNAMIC",            # count-locked bodies, rewritten each issue
    "UNLOCKED",           # owner-flagged, counts may flex (e.g. editor's note)
    "MANUAL",             # owner-swapped only (e.g. next-issue upsell)
)
DEFAULT_SLOT_TYPE = "DYNAMIC"

#: Types that are "never touched" and therefore must live in the
#: `permanent_slots` block, not in `slots`.
NEVER_TOUCHED_TYPES = ("FIXED", "PERMANENT")

#: Section 4: UNLOCKED slots are "owner-flagged pages where counts may flex".
#: Enforcing an exact count on one would be wrong, so CharLint does not — but
#: it warns on every run, because a silently un-gated slot is how locks rot.
FLEX_TYPES = ("UNLOCKED",)

#: Types an issue fill is not expected to supply. Absence is correct for these,
#: so they are exempt from the not-filled check. Everything else is required:
#: a gate that passes an empty submission is worthless.
#:
#: Exempt from FAILING is not the same as invisible. An unsupplied optional slot
#: produces no row — there was nothing to gate — but it does produce a
#: NOT SUBMITTED warning naming its type, for the same reason UNLOCKED slots are
#: warned about on every run: a silently un-gated slot is how locks rot.
OPTIONAL_TYPES = ("UNLOCKED", "MANUAL")

# failure_mode values
FAILURE_OVERFLOW = "overflow"
FAILURE_UNDERFILL = "underfill"
FAILURE_PERMANENT_MUTATION = "permanent_mutation"
FAILURE_NOT_FILLED = "not_filled"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CharLintError(Exception):
    """Base class for every CharLint error."""


class CorruptLocksError(CharLintError, ValueError):
    """
    The locks file disagrees with itself.

    Raised — never warned — when a file's own numbers do not match its own
    strings (e.g. `observed` != len(baseline)). That combination means somebody
    edited a baseline and forgot the count, and every downstream count is now
    lies. Also subclasses ValueError so `except ValueError` callers still work.
    """


class UnknownSlotError(CharLintError, ValueError):
    """
    A candidate was supplied under a slot name the locks file does not define.

    An error, not a silent no-op: a typo'd slot name means the real slot
    silently goes unfilled and the copy silently goes nowhere. Mirrors
    prohiblint's "unknown ruleset raises ValueError — there is no silent
    fallback".
    """


# ---------------------------------------------------------------------------
# Canonical form — the one place NFC is applied
# ---------------------------------------------------------------------------

def _canonical(text):
    """
    The canonically composed (NFC) form of `text`.

    Every count CharLint takes and every comparison it makes goes through here,
    so a decomposed candidate can never disagree with a composed one about the
    same visible text. See the "CANONICAL FORM" note in the module docstring
    for why this is NFC and not NFKC, and why it is not an exception to the
    no-whitespace-normalisation rule.
    """
    return unicodedata.normalize(CANONICAL_FORM, text)


# ---------------------------------------------------------------------------
# Locks loading + validation
# ---------------------------------------------------------------------------

def _iter_slot_items(block):
    """Yield (name, spec) for real slots, skipping `_`-prefixed metadata keys."""
    for name, spec in block.items():
        if name.startswith("_"):
            continue
        yield name, spec


def _slot_type(spec, default=DEFAULT_SLOT_TYPE):
    """Normalised Section 4 type for a slot spec."""
    raw = spec.get("type", default)
    if not isinstance(raw, str):
        return raw
    return " ".join(raw.upper().split())


def _is_nonneg_int(value):
    # bool is a subclass of int; a `true` in a count field is corrupt data.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def enforced_lock(spec):
    """
    The number CharLint actually enforces for a slot spec.

    `observed` (what the live template measures) wins when present, otherwise
    `principles_lock` (what PRINCIPLES.txt documents). The copy has to fit the
    template that exists, not the number in the write-up.
    """
    observed = spec.get("observed")
    if observed is not None:
        return observed
    return spec.get("principles_lock")


def _validate_slot(name, spec, source, permanent=False):
    where = f"{source}: slot {name!r}"

    if not isinstance(spec, dict):
        raise CorruptLocksError(f"{where} is not an object.")

    baseline = spec.get("baseline")
    if not isinstance(baseline, str):
        raise CorruptLocksError(
            f"{where} has no string `baseline`. The baseline text is the "
            f"only source of truth for a lock; a slot without one is unusable."
        )

    # Baselines are stored in canonical NFC form, because that is the form
    # every candidate is measured and compared in. A decomposed baseline would
    # count its own combining marks as characters, so the baseline would fail
    # its own lock the moment it was fed back — the identity case, broken by
    # the lock data itself. Canonically re-encoding it is loss-free and renders
    # identically, so this is a fix-the-file error, not a warning.
    if baseline != _canonical(baseline):
        raise CorruptLocksError(
            f"{where} has a baseline that is not in canonical {CANONICAL_FORM} "
            f"form ({len(baseline)} code points, "
            f"{len(_canonical(baseline))} characters composed). CharLint counts "
            f"and compares the {CANONICAL_FORM} form, so this baseline would "
            f"fail its own lock. Re-save the capture normalised to "
            f"{CANONICAL_FORM}: it is the same text and renders identically."
        )

    measured = len(baseline)
    slot_type = _slot_type(spec, default="PERMANENT" if permanent else DEFAULT_SLOT_TYPE)
    if slot_type not in SLOT_TYPES:
        raise CorruptLocksError(
            f"{where} has unknown type {spec.get('type')!r}. Valid types "
            f"(PRINCIPLES.txt Sec. 4): {', '.join(SLOT_TYPES)}."
        )

    if permanent:
        # Mis-filing is checked in both directions: `permanent_slots` is only
        # for never-touched slots. A slot that gets rewritten belongs in
        # `slots`, where its character count is actually enforced.
        if slot_type not in NEVER_TOUCHED_TYPES:
            raise CorruptLocksError(
                f"{where} sits in `permanent_slots` but is typed {slot_type}. "
                f"That block is for never-touched slots "
                f"({', '.join(NEVER_TOUCHED_TYPES)}); a slot that is rewritten "
                f"belongs in `slots`, where its char count is enforced."
            )
        # Permanent slots are matched by exact string, so they need no count.
        # If one carries counts anyway, they still have to be honest.
        for field in ("principles_lock", "observed"):
            value = spec.get(field)
            if value is not None and value != measured:
                raise CorruptLocksError(
                    f"{where} declares {field}={value} but len(baseline)="
                    f"{measured}."
                )
        return

    if slot_type in NEVER_TOUCHED_TYPES:
        raise CorruptLocksError(
            f"{where} is typed {slot_type} — a never-touched slot "
            f"(PRINCIPLES.txt Sec. 4). It belongs in the `permanent_slots` "
            f"block, where it is checked for mutation, not char count."
        )

    principles_lock = spec.get("principles_lock")
    observed = spec.get("observed")

    for field, value in (("principles_lock", principles_lock), ("observed", observed)):
        if value is not None and not _is_nonneg_int(value):
            raise CorruptLocksError(
                f"{where} has {field}={value!r}; expected a non-negative int."
            )

    if principles_lock is None and observed is None:
        raise CorruptLocksError(
            f"{where} declares neither `principles_lock` nor `observed`. "
            f"A locked slot needs a number to enforce."
        )

    # Guard 1 (the spec'd one): a file whose own count disagrees with its own
    # string is corrupt. This is what catches "edited the baseline, forgot the
    # count".
    if observed is not None and observed != measured:
        raise CorruptLocksError(
            f"{where} declares observed={observed} but len(baseline)="
            f"{measured}. The locks file disagrees with itself — someone "
            f"edited the baseline string without re-measuring it. Fix the "
            f"count (or restore the string) before any copy is gated."
        )

    # Guard 2: `drift` is a derived number, so it must derive correctly.
    drift = spec.get("drift")
    if drift is not None:
        if principles_lock is None or observed is None:
            raise CorruptLocksError(
                f"{where} declares drift={drift} but is missing "
                f"`principles_lock` and/or `observed`; drift is defined as "
                f"observed - principles_lock."
            )
        if drift != observed - principles_lock:
            raise CorruptLocksError(
                f"{where} declares drift={drift} but observed - "
                f"principles_lock = {observed - principles_lock}."
            )

    # Guard 3: whatever we enforce must be what the baseline measures, or the
    # identity case (baseline fed back as its own candidate) would fail and the
    # lock data would be self-defeating. When only `principles_lock` is present
    # and it disagrees with the string, the fix is to record the measurement in
    # `observed` (+ `drift`) exactly as cover_body does — that keeps the
    # disagreement visible instead of quietly rewriting the documented number.
    if slot_type not in FLEX_TYPES:
        target = enforced_lock(spec)
        if target != measured:
            raise CorruptLocksError(
                f"{where} enforces {target} but len(baseline)={measured}; the "
                f"baseline would fail its own lock. If the template really "
                f"measures {measured}, record it as \"observed\": {measured} "
                f"with \"drift\": {measured - target} so the disagreement with "
                f"PRINCIPLES.txt stays visible."
            )


def validate_locks(data, source="<locks>"):
    """
    Validate a loaded locks mapping in place. Raises CorruptLocksError.

    Cheap and idempotent, so it runs on every entry point — including when a
    caller hands run_charlint() a dict it loaded (and possibly edited) itself.
    """
    if not isinstance(data, dict):
        raise CorruptLocksError(f"{source}: top level is not an object.")

    slots = data.get("slots")
    if not isinstance(slots, dict):
        raise CorruptLocksError(f"{source}: missing `slots` object.")

    real_slots = dict(_iter_slot_items(slots))
    if not real_slots:
        raise CorruptLocksError(
            f"{source}: `slots` is empty. A locks file with no slots gates "
            f"nothing and would pass any submission."
        )

    tolerance = data.get("tolerance", DEFAULT_TOLERANCE)
    if not _is_nonneg_int(tolerance):
        raise CorruptLocksError(
            f"{source}: tolerance={tolerance!r}; expected a non-negative int "
            f"(0 = exact match, the product standard)."
        )

    permanent = data.get("permanent_slots", {})
    if not isinstance(permanent, dict):
        raise CorruptLocksError(f"{source}: `permanent_slots` is not an object.")
    real_permanent = dict(_iter_slot_items(permanent))

    collisions = sorted(set(real_slots) & set(real_permanent))
    if collisions:
        raise CorruptLocksError(
            f"{source}: slot name(s) {collisions} appear in both `slots` and "
            f"`permanent_slots`. A slot is either rewritten or never touched, "
            f"not both."
        )

    for name, spec in real_slots.items():
        _validate_slot(name, spec, source, permanent=False)
    for name, spec in real_permanent.items():
        _validate_slot(name, spec, source, permanent=True)

    return data


def load_locks(path):
    """
    Load and validate a locks file from `path` (str or Path).

    Any locks file works — nothing about the Seattle Series is hard-coded here.
    Raises CorruptLocksError if the file disagrees with itself, so a bad file
    can never quietly gate a volume.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return validate_locks(data, source=str(path))


def _coerce_locks(locks):
    """Accept either a path or an already-loaded mapping; always validate."""
    if isinstance(locks, dict):
        return validate_locks(locks, source=locks.get("ruleset", "<locks dict>"))
    if locks is None:
        raise TypeError(
            "run_charlint() requires a locks file: pass a path or a mapping "
            "loaded by load_locks(). There is no default locks file."
        )
    return load_locks(locks)


# ---------------------------------------------------------------------------
# Introspection helpers
# ---------------------------------------------------------------------------

def slot_names(locks):
    """Count-locked slot names, in file order."""
    locks = _coerce_locks(locks)
    return [name for name, _ in _iter_slot_items(locks["slots"])]


def permanent_slot_names(locks):
    """Never-touched slot names, in file order (PRINCIPLES.txt Sec. 4)."""
    locks = _coerce_locks(locks)
    return [name for name, _ in _iter_slot_items(locks.get("permanent_slots", {}))]


def required_slot_names(locks):
    """
    Slot names an issue fill MUST supply, in file order.

    Count-locked slots minus the owner-governed ones (OPTIONAL_TYPES). This is
    a property of the LOCKS FILE alone — it does not depend on, and cannot be
    changed by, what a submission happened to contain. Callers that report
    "how much was expected of this submission" should use this rather than
    counting the rows a run produced, which vary with the optional and
    permanent slots the submitter chose to send.
    """
    locks = _coerce_locks(locks)
    return [name for name, spec in _iter_slot_items(locks["slots"])
            if _slot_type(spec) not in OPTIONAL_TYPES]


def _spec_for(slot_name, locks):
    """Return (spec, is_permanent) or raise UnknownSlotError."""
    for name, spec in _iter_slot_items(locks["slots"]):
        if name == slot_name:
            return spec, False
    for name, spec in _iter_slot_items(locks.get("permanent_slots", {})):
        if name == slot_name:
            return spec, True
    known = slot_names(locks) + permanent_slot_names(locks)
    raise UnknownSlotError(
        f"Unknown slot {slot_name!r}. Known slots: {', '.join(known)}."
    )


def target_for(slot_name, locks):
    """The enforced character target for a slot (permanent slots: their length)."""
    locks = _coerce_locks(locks)
    spec, is_permanent = _spec_for(slot_name, locks)
    if is_permanent:
        return len(spec["baseline"])
    return enforced_lock(spec)


# ---------------------------------------------------------------------------
# Drift reporting (requirement: WARNING on every run, never silently absorbed)
# ---------------------------------------------------------------------------

def drift_warnings(locks):
    """
    One warning per slot whose documented lock disagrees with the measurement.

    Emitted on every run, pass or fail, whether or not the slot was filled:
    drift is a property of the lock data, not of the candidate copy. CharLint
    does not pick a winner — it enforces the live measurement and keeps saying
    so until the owner reconciles the two numbers.
    """
    locks = _coerce_locks(locks)
    warnings = []

    for name, spec in _iter_slot_items(locks["slots"]):
        documented = spec.get("principles_lock")
        observed = spec.get("observed")
        if documented is None or observed is None or documented == observed:
            continue
        drift = observed - documented
        warnings.append(
            f"DRIFT: {name} — PRINCIPLES.txt documents a lock of {documented}, "
            f"the template measures {observed} (drift {drift:+d}). CharLint is "
            f"enforcing {observed} (`observed`), because copy has to fit the "
            f"template that exists. Either the template drifted from the "
            f"approved baseline or PRINCIPLES.txt records a different "
            f"baseline; the owner decides which number is canonical. This "
            f"warning repeats on every run until the locks file is reconciled."
        )

    for name, spec in _iter_slot_items(locks["slots"]):
        if _slot_type(spec) in FLEX_TYPES:
            warnings.append(
                f"UNLOCKED: {name} is owner-flagged UNLOCKED (PRINCIPLES.txt "
                f"Sec. 4), so its character count is NOT gated. Listed here so "
                f"an un-gated slot is never invisible."
            )

    return warnings


def _not_submitted_warning(slot_name, slot_type):
    """
    An owner-governed slot the submission did not supply.

    Absence is CORRECT for these — an issue fill is not expected to touch an
    UNLOCKED or MANUAL slot — so this is a warning and never a failure. It
    exists because the alternative is what the module used to do: produce no
    row, no warning and no mention at all, leaving no way to tell "owner
    governs this one" from "we forgot this one". A silently un-gated slot is
    how locks rot.
    """
    return (
        f"NOT SUBMITTED: {slot_name} is typed {slot_type} (PRINCIPLES.txt "
        f"Sec. 4 — owner-governed, not part of an issue fill) and no candidate "
        f"was supplied, so nothing was gated for it. Not a failure. Recorded so "
        f"an un-gated slot is never invisible: if this slot WAS meant to change "
        f"this issue, it has to be submitted to be checked."
    )


def _canonical_form_warning(slot_name, candidate):
    """A candidate that arrived in a non-NFC spelling of the same text."""
    return (
        f"CANONICAL FORM: {slot_name} arrived in a decomposed (non-"
        f"{CANONICAL_FORM}) spelling — {len(candidate)} code points, "
        f"{len(_canonical(candidate))} characters once composed. CharLint "
        f"counts the composed form, which is what the layout renders, so this "
        f"did NOT move the count and is not a failure. Reported because the "
        f"raw string differs from the string that was counted: editors, "
        f"clipboards and macOS filenames emit this form routinely, and it is "
        f"why a hand count may disagree by the number of accented characters."
    )


# ---------------------------------------------------------------------------
# The measurement itself
# ---------------------------------------------------------------------------

def _measure(text):
    """
    Character count of the text exactly as the layout will receive it.

    No strip, no trim, no whitespace collapsing: trailing whitespace is a real
    character that really breaks a real layout, and newlines inside an element
    are characters too. len() on a str counts characters; encoding to UTF-8
    first would count bytes and is wrong.

    The one transform applied is canonical composition (NFC), because "café"
    spelled with a combining acute is the same single character to the layout
    as "café" spelled with U+00E9 — and counting it as two would report an
    overflow the writer cannot fix by editing anything they can see. See
    _canonical() and the module docstring.

    The isinstance guard is load-bearing and must come first: len() and
    unicodedata.normalize() each reject SOME non-strings, but not the same
    ones. len(["a", "b"]) is a perfectly happy 2, and without this guard a list
    of paragraphs would be silently "measured" as two characters.
    """
    if not isinstance(text, str):
        raise TypeError(
            f"Candidate text must be a str, got {type(text).__name__}. "
            f"None/0/missing is not an empty fill — see the not-filled check."
        )
    return len(_canonical(text))


def _first_diff_index(a, b):
    """Index of the first character where two DIFFERENT strings diverge."""
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    # No difference in the overlap, so one is a strict prefix of the other and
    # the divergence is where the shorter one ends.
    return min(len(a), len(b))


def _was_recomposed(candidate):
    """True when the raw candidate was not already in canonical form."""
    return isinstance(candidate, str) and candidate != _canonical(candidate)


def _blank_result(expected, actual, delta, failure_mode=None, nfc_normalized=False):
    return {
        "violations": [],
        "score": 100,
        "passed": True,
        "expected": expected,
        "actual": actual,
        "delta": delta,
        "failure_mode": failure_mode,
        "nfc_normalized": nfc_normalized,
    }


def check_slot(slot_name, candidate, locks):
    """
    Check one candidate string against its lock. Returns a per-slot result:

        {"violations": [str], "score": int, "passed": bool,
         "expected": int, "actual": int, "delta": int, "failure_mode": str|None,
         "nfc_normalized": bool}

    `delta` is signed: positive = OVERFLOW (too long), negative = UNDERFILL
    (too short). The two are named distinctly because they break the layout
    differently — overflow overruns the box and pushes text off the page,
    underfill leaves a short last line and kills the rhythm of the block
    (PRINCIPLES.txt Sec. 3).

    `actual` is the CANONICAL (NFC) character count, which is what the layout
    renders; `nfc_normalized` is True when the raw candidate was spelled in
    some other canonically equivalent way, so a reader whose own count differs
    can see why.

    `passed` is decided by the count alone. `score` is severity only and is
    never consulted — see the module docstring.
    """
    locks = _coerce_locks(locks)
    spec, is_permanent = _spec_for(slot_name, locks)
    baseline = spec["baseline"]

    if is_permanent:
        return _check_permanent(slot_name, candidate, baseline)

    recomposed = _was_recomposed(candidate)

    if _slot_type(spec) in FLEX_TYPES:
        # Owner-flagged flex slot: measured and reported, never gated.
        actual = _measure(candidate)
        expected = enforced_lock(spec)
        result = _blank_result(expected, actual,
                               None if expected is None else actual - expected,
                               nfc_normalized=recomposed)
        return result

    tolerance = locks.get("tolerance", DEFAULT_TOLERANCE)
    expected = enforced_lock(spec)
    actual = _measure(candidate)
    delta = actual - expected
    excess = abs(delta) - tolerance

    if excess <= 0:
        return _blank_result(expected, actual, delta, nfc_normalized=recomposed)

    tol_note = "" if tolerance == 0 else f" (tolerance {tolerance})"
    if delta > 0:
        mode, label, fix = FAILURE_OVERFLOW, "OVERFLOW", "Remove"
        consequence = ("the box overruns — the text wraps past its last line "
                       "and pushes off the page")
    else:
        mode, label, fix = FAILURE_UNDERFILL, "UNDERFILL", "Add"
        consequence = ("the box runs short — a runt last line, and the block "
                       "loses the rhythm the layout was approved on")

    violation = (
        f"{label}: {slot_name} is {abs(delta)} character(s) "
        f"{'over' if delta > 0 else 'under'} the enforced lock{tol_note}. "
        f"Enforced lock {expected}, candidate {actual}, delta {delta:+d}. "
        f"{fix} {excess} character(s) to land on the lock. "
        f"Hard fail — {consequence}."
    )

    penalty = max(MAX_CHAR_PENALTY, PENALTY_PER_CHAR * excess)
    return {
        "violations": [violation],
        "score": max(0, 100 + penalty),
        "passed": False,
        "expected": expected,
        "actual": actual,
        "delta": delta,
        "failure_mode": mode,
        "nfc_normalized": recomposed,
    }


def _check_permanent(slot_name, candidate, baseline):
    """
    PERMANENT slots are never touched by an issue fill (PRINCIPLES.txt Sec. 4).

    Any difference at all — one character, one letter's case, one space — is a
    hard failure. This is deliberately NOT a char-count check: a same-length
    edit ("THE CITY IS THE GYM!" for "THE CITY IS THE GYM.") has delta 0 and
    still fails.

    "Difference" means difference in the TEXT, so the comparison is made in
    canonical form, exactly as the counting is (see _canonical). A é typed as
    "e" + combining acute is not a mutation of a é typed as U+00E9 — it is the
    same word, rendered identically, and calling it a mutation would hand the
    owner a defect report with nothing in it to fix. Everything that IS a
    different character stays a hard failure: U+00B7 for "." and the curly
    apostrophe for "'" have no canonical decomposition, so they are untouched
    by this and still fail.
    """
    actual = _measure(candidate)
    expected = len(baseline)
    delta = actual - expected

    canonical_candidate = _canonical(candidate)
    canonical_baseline = _canonical(baseline)
    if canonical_candidate == canonical_baseline:
        return _blank_result(expected, actual, delta,
                             nfc_normalized=_was_recomposed(candidate))

    at = (" First difference at index "
          f"{_first_diff_index(canonical_baseline, canonical_candidate)}.")
    violation = (
        f"PERMANENT SLOT MUTATED: {slot_name} is PERMANENT (PRINCIPLES.txt "
        f"Sec. 4) and is never touched by an issue fill. Baseline "
        f"{baseline!r}, candidate {candidate!r}.{at} Hard fail — this is a "
        f"mutation, not a char-count delta; restore the baseline exactly."
    )
    return {
        "violations": [violation],
        "score": max(0, 100 + PENALTY_PERMANENT_MUTATION),
        "passed": False,
        "expected": expected,
        "actual": actual,
        "delta": delta,
        "failure_mode": FAILURE_PERMANENT_MUTATION,
        "nfc_normalized": _was_recomposed(candidate),
    }


def _not_filled(slot_name, expected):
    violation = (
        f"NOT FILLED: {slot_name} is locked in the locks file but absent from "
        f"the candidate copy. Enforced lock {expected}, nothing submitted. "
        f"Hard fail — an unfilled slot is not a passing slot."
    )
    return {
        "violations": [violation],
        "score": max(0, 100 + PENALTY_NOT_FILLED),
        "passed": False,
        "expected": expected,
        "actual": 0,
        "delta": -expected,
        "failure_mode": FAILURE_NOT_FILLED,
        "nfc_normalized": False,
    }


# ---------------------------------------------------------------------------
# Writer convergence helper (PRINCIPLES.txt Sec. 3)
# ---------------------------------------------------------------------------

def chars_to_target(slot_name, candidate, locks):
    """
    How far a draft is from its lock, and which way to move.

    PRINCIPLES.txt Sec. 3 describes writing to a lock as "assembling candidate
    segments and swapping word-level alternates until the count lands on the
    lock to the character". This is the read-out for that loop.

    Returns:
        {"slot": str, "expected": int, "actual": int,
         "delta": int,          # signed: + = over the lock, - = under it
         "chars_needed": int,   # what the WRITER does: + = add, - = remove
         "action": "add" | "remove" | "none",
         "tolerance": int, "within_tolerance": bool, "message": str}
    """
    locks = _coerce_locks(locks)
    expected = target_for(slot_name, locks)
    actual = _measure(candidate)
    tolerance = locks.get("tolerance", DEFAULT_TOLERANCE)

    delta = actual - expected
    within = abs(delta) <= tolerance
    chars_needed = -delta

    if within:
        action = "none"
        message = (
            f"{slot_name}: on the lock at {actual} characters. Nothing to add "
            f"or remove."
            if delta == 0 else
            f"{slot_name}: {actual} characters vs lock {expected} "
            f"(delta {delta:+d}), inside the declared tolerance of {tolerance}."
        )
    elif chars_needed > 0:
        action = "add"
        message = (
            f"{slot_name}: {actual} characters, lock {expected}. "
            f"Add {chars_needed} character(s)."
        )
    else:
        action = "remove"
        message = (
            f"{slot_name}: {actual} characters, lock {expected}. "
            f"Remove {abs(chars_needed)} character(s)."
        )

    return {
        "slot": slot_name,
        "expected": expected,
        "actual": actual,
        "delta": delta,
        "chars_needed": chars_needed,
        "action": action,
        "tolerance": tolerance,
        "within_tolerance": within,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_charlint(candidates, locks):
    """
    Run CharLint over a dict of {slot_name: candidate_text}.

    Args:
        candidates: {slot_name: text, ...}. Slot names must exist in the locks
            file; an unknown name raises UnknownSlotError rather than being
            silently ignored (a typo'd name would otherwise vanish the copy and
            leave the real slot unfilled).
        locks: path to a locks JSON file (str/Path), or a mapping already
            loaded by load_locks(). Required — there is no default locks file,
            so any volume or product line can bring its own.

    Returns (shape matches prohiblint/voicelint so the orchestrator can consume
    all three uniformly; extra keys may be added later, never renamed):
        {
          "slots": {
            slot_name: {
              "violations": [str, ...],
              "score": int,        # starts at 100, penalties applied, floor 0
              "passed": bool,
              "expected": int,     # the ENFORCED lock for this slot
              "actual": int,       # canonical (NFC) character count; no strip
              "delta": int,        # actual - expected; + over, - under
              "failure_mode": str | None,
              "nfc_normalized": bool,  # the raw candidate was not already NFC
            },
            ...
          },
          "warnings": [str, ...],  # never failures, never dropped:
                                   #   DRIFT / UNLOCKED   — locks-file facts,
                                   #     emitted every run, candidate or not
                                   #   NOT SUBMITTED      — an owner-governed
                                   #     slot this submission did not supply
                                   #   CANONICAL FORM     — a candidate that
                                   #     arrived in a non-NFC spelling
          "summary": {"total_score": int, "all_passed": bool},
        }

    Which slots appear in "slots":
      * every count-locked slot, always — filled or not. A missing slot is
        reported as NOT FILLED (failure_mode "not_filled"), never passed over,
        because a gate that passes an empty submission is worthless.
      * EXCEPT the owner-governed types (OPTIONAL_TYPES) when they are not
        supplied: there is no candidate to gate, so there is no row. That is
        the one case where a locked slot produces no result, and it is never
        silent — it produces a NOT SUBMITTED warning naming the slot's type.
      * a PERMANENT slot only when a candidate was supplied for it. Omitting
        permanent slots is the correct behaviour for an issue fill
        (PRINCIPLES.txt Sec. 4: never touched), so their absence is not a
        failure — but if one IS supplied, it must match its baseline exactly.

    Raises:
        CorruptLocksError: the locks file disagrees with itself.
        UnknownSlotError: a candidate names a slot the locks file lacks.
        TypeError: a candidate value is not a str.
    """
    locks = _coerce_locks(locks)

    if not isinstance(candidates, dict):
        raise TypeError(
            f"candidates must be a dict of {{slot_name: text}}, got "
            f"{type(candidates).__name__}."
        )

    locked = dict(_iter_slot_items(locks["slots"]))
    permanent = dict(_iter_slot_items(locks.get("permanent_slots", {})))

    unknown = [name for name in candidates if name not in locked and name not in permanent]
    if unknown:
        known = list(locked) + list(permanent)
        raise UnknownSlotError(
            f"Unknown slot name(s) in candidate copy: "
            f"{', '.join(repr(u) for u in sorted(unknown))}. Known slots: "
            f"{', '.join(known)}. Slot names are not silently ignored — a "
            f"typo'd name would leave the real slot unfilled and drop the copy "
            f"on the floor."
        )

    results = {}
    # Warnings about the SUBMISSION, kept after the warnings about the LOCKS
    # FILE (drift, un-gated slots) so the standing lock-data warnings always
    # read first and their position never depends on the candidate copy.
    submission_warnings = []

    for name, spec in locked.items():
        if name in candidates:
            results[name] = check_slot(name, candidates[name], locks)
        elif _slot_type(spec) in OPTIONAL_TYPES:
            # Owner-governed: an issue fill is not expected to supply it, so
            # there is nothing to gate — but the absence is stated out loud.
            submission_warnings.append(_not_submitted_warning(name, _slot_type(spec)))
        else:
            results[name] = _not_filled(name, enforced_lock(spec))

    for name in permanent:
        if name in candidates:
            results[name] = check_slot(name, candidates[name], locks)

    for name, res in results.items():
        if res.get("nfc_normalized"):
            submission_warnings.append(_canonical_form_warning(name, candidates[name]))

    return {
        "slots": results,
        "warnings": drift_warnings(locks) + submission_warnings,
        "summary": {
            "total_score": sum(r["score"] for r in results.values()),
            "all_passed": all(r["passed"] for r in results.values()) and bool(results),
        },
    }


# ---------------------------------------------------------------------------
# Reporting / CLI
# ---------------------------------------------------------------------------

def format_report(result):
    """Render a run_charlint() result as plain text for a terminal."""
    lines = []
    lines.append(f"{'Slot':<16} {'Lock':>6} {'Actual':>7} {'Delta':>7}  Status")
    lines.append(f"{'-'*16} {'-'*6} {'-'*7} {'-'*7}  {'-'*6}")
    for name, res in result["slots"].items():
        status = "PASS" if res["passed"] else "FAIL"
        lines.append(
            f"{name:<16} {res['expected']:>6} {res['actual']:>7} "
            f"{res['delta']:>+7}  {status}"
        )

    for name, res in result["slots"].items():
        for violation in res["violations"]:
            lines.append(f"  [{name}] {violation}")

    for warning in result["warnings"]:
        lines.append(f"  [warning] {warning}")

    lines.append("")
    lines.append(f"TOTAL {result['summary']['total_score']}  "
                 f"OVERALL {'PASS' if result['summary']['all_passed'] else 'FAIL'}")
    return "\n".join(lines)


def main(argv=None):  # pragma: no cover - thin CLI wrapper
    import argparse

    parser = argparse.ArgumentParser(description="TIMBR CharLint — char-count lock gate")
    parser.add_argument("--locks", required=True, help="Path to a locks JSON file")
    parser.add_argument(
        "--candidates",
        help="Path to a JSON file of {slot_name: text}. Omit to run the "
             "identity case (every baseline fed back as its own candidate).",
    )
    args = parser.parse_args(argv)

    locks = load_locks(args.locks)
    if args.candidates:
        with open(args.candidates, encoding="utf-8") as fh:
            candidates = json.load(fh)
    else:
        candidates = {n: s["baseline"] for n, s in _iter_slot_items(locks["slots"])}

    result = run_charlint(candidates, locks)
    print(format_report(result))
    return 0 if result["summary"]["all_passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
