"""
test_charlint.py — pytest tests for the CharLint module.
Run with: cd charlint && python3 -m pytest test_charlint.py -q
"""
import copy
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))

import pytest
import charlint as charlint_module
from charlint import (
    CANONICAL_FORM,
    CorruptLocksError,
    RangeLockedSlotError,
    UnknownSlotError,
    DEFAULT_TOLERANCE,
    LOCK_RANGE_KEY,
    FAILURE_NOT_FILLED,
    FAILURE_OVERFLOW,
    FAILURE_PERMANENT_MUTATION,
    FAILURE_UNDERFILL,
    SEATTLE_SERIES_LOCKS,
    chars_to_target,
    check_slot,
    drift_warnings,
    enforced_lock,
    format_report,
    is_range_locked,
    load_locks,
    lock_band,
    nearest_legal,
    permanent_slot_names,
    required_slot_names,
    run_charlint,
    slot_names,
    target_for,
    target_range_for,
    validate_locks,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

ALL_SLOTS = [
    "cover_body", "city_intro", "anchor_venue", "anchor_cafe",
    "counter_venue", "counter_cafe", "night_page",
]

#: The one slot the master workbook states as a BAND rather than a point.
RANGE_LOCKED_SLOTS = ["cover_body"]

#: The other six, which are genuine point locks at tolerance 0 and must stay
#: that way — a range that leaked onto them would be a gate looser than its
#: rulebook, the mirror of the defect ranges were added to fix.
POINT_LOCKED_SLOTS = [s for s in ALL_SLOTS if s not in RANGE_LOCKED_SLOTS]

#: cover_body's band, from the Magazine Layout tab of the master workbook:
#: CHAR COUNT "~353 (lock 350-358 incl. spaces)". Written out here rather than
#: read from the locks file, so a test can catch the file changing.
COVER_BODY_BAND = (350, 358)


def sized(text, target):
    """`text` grown or trimmed to exactly `target` characters."""
    if target <= len(text):
        return text[:target]
    return text + "x" * (target - len(text))


@pytest.fixture
def locks():
    """The real Seattle Series locks, freshly loaded and validated."""
    return load_locks(SEATTLE_SERIES_LOCKS)


@pytest.fixture
def baselines(locks):
    """{slot_name: baseline} for the count-locked slots."""
    return {name: spec["baseline"] for name, spec in locks["slots"].items()}


@pytest.fixture
def identity(baselines):
    """The identity submission: every baseline fed back as its own candidate."""
    return dict(baselines)


def write_locks(tmp_path, data, name="locks.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def minimal_locks(baseline="abcde", **slot_overrides):
    """A tiny hand-built locks file, used for negative/edge cases."""
    slot = {"type": "DYNAMIC", "principles_lock": len(baseline), "baseline": baseline}
    slot.update(slot_overrides)
    return {
        "ruleset": "test",
        "tolerance": 0,
        "slots": {"body": slot},
        "permanent_slots": {
            "brand": {"baseline": "THE CITY IS THE GYM."},
        },
    }


# ---------------------------------------------------------------------------
# Loading + locks-file validation
# ---------------------------------------------------------------------------

class TestLoadLocks:
    def test_loads_the_seattle_file(self, locks):
        assert locks["ruleset"] == "workout_series"
        assert locks["design_id"] == "DAHQoZJm12w"
        assert slot_names(locks) == ALL_SLOTS

    def test_permanent_slots_are_listed_and_metadata_skipped(self, locks):
        # `permanent_slots` carries a `_comment` key that is metadata, not a slot.
        assert permanent_slot_names(locks) == ["brand_subline", "cover_spec_line"]

    def test_required_slots_are_the_ones_an_issue_fill_must_supply(self, locks):
        # Every Seattle slot is DYNAMIC, so all seven are required.
        assert required_slot_names(locks) == ALL_SLOTS

    def test_required_slots_exclude_the_owner_governed_types(self, tmp_path):
        data = minimal_locks()
        data["slots"]["editors_note"] = {
            "type": "UNLOCKED", "principles_lock": 5, "baseline": "abcde"}
        data["slots"]["upsell"] = {
            "type": "MANUAL", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)
        assert slot_names(path) == ["body", "editors_note", "upsell"]
        assert required_slot_names(path) == ["body"]

    def test_required_slots_do_not_depend_on_any_submission(self, locks, identity):
        # The number a scorecard reports as "expected" has to be a property of
        # the locks file. Nothing a submitter sends or omits may move it.
        before = required_slot_names(locks)
        run_charlint({}, locks)
        run_charlint(dict(identity, brand_subline="THE CITY IS THE GYM."), locks)
        assert required_slot_names(locks) == before

    def test_accepts_a_path_object(self, tmp_path):
        path = tmp_path / "locks.json"
        path.write_text(json.dumps(minimal_locks()), encoding="utf-8")
        assert slot_names(path) == ["body"]

    def test_tolerance_defaults_to_zero_when_absent(self, tmp_path):
        data = minimal_locks()
        del data["tolerance"]
        path = write_locks(tmp_path, data)
        loaded = load_locks(path)
        assert loaded.get("tolerance", DEFAULT_TOLERANCE) == 0
        assert DEFAULT_TOLERANCE == 0

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_locks(tmp_path / "nope.json")

    def test_no_default_locks_file(self):
        # locks is a required argument: nothing about Seattle is baked in.
        with pytest.raises(TypeError):
            run_charlint({})


class TestCorruptLocks:
    """A file whose own numbers disagree with its own strings must RAISE."""

    def test_observed_not_equal_to_len_baseline_raises(self, tmp_path):
        data = minimal_locks("abcde")
        data["slots"]["body"]["observed"] = 99
        data["slots"]["body"]["drift"] = 99 - 5
        path = write_locks(tmp_path, data)
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(path)
        assert "observed=99" in str(exc.value)
        assert "len(baseline)=5" in str(exc.value)

    def test_edited_baseline_without_remeasuring_is_caught(self, locks, tmp_path):
        # The exact failure this guard exists for: somebody tweaks a word in a
        # baseline and forgets the count. observed stays 351, string becomes 352.
        data = copy.deepcopy(locks)
        data["slots"]["cover_body"]["baseline"] += "."
        path = write_locks(tmp_path, data)
        with pytest.raises(CorruptLocksError):
            load_locks(path)

    def test_drift_must_equal_observed_minus_principles_lock(self, tmp_path):
        data = minimal_locks("abcde")
        data["slots"]["body"]["principles_lock"] = 7
        data["slots"]["body"]["observed"] = 5
        data["slots"]["body"]["drift"] = -1          # should be -2
        path = write_locks(tmp_path, data)
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(path)
        assert "drift" in str(exc.value)

    def test_principles_lock_alone_disagreeing_with_baseline_raises(self, tmp_path):
        # No `observed` recorded, and the documented lock does not match the
        # string: the baseline would fail its own lock, breaking identity.
        data = minimal_locks("abcde")
        data["slots"]["body"]["principles_lock"] = 9
        path = write_locks(tmp_path, data)
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(path)
        assert "observed" in str(exc.value)  # tells you how to record the drift

    def test_missing_baseline_raises(self, tmp_path):
        data = minimal_locks()
        del data["slots"]["body"]["baseline"]
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_non_string_baseline_raises(self, tmp_path):
        data = minimal_locks()
        data["slots"]["body"]["baseline"] = 357
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_slot_with_no_lock_number_raises(self, tmp_path):
        data = minimal_locks()
        del data["slots"]["body"]["principles_lock"]
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_empty_slots_block_raises(self, tmp_path):
        data = minimal_locks()
        data["slots"] = {}
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "gates nothing" in str(exc.value)

    def test_negative_tolerance_raises(self, tmp_path):
        data = minimal_locks()
        data["tolerance"] = -1
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_boolean_tolerance_raises(self, tmp_path):
        # bool is an int subclass in Python; `true` in a count field is corrupt.
        data = minimal_locks()
        data["tolerance"] = True
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_name_collision_between_blocks_raises(self, tmp_path):
        data = minimal_locks()
        data["permanent_slots"]["body"] = {"baseline": "abcde"}
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "both" in str(exc.value)

    def test_never_touched_type_in_slots_block_raises(self, tmp_path):
        data = minimal_locks()
        data["slots"]["body"]["type"] = "PERMANENT"
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "permanent_slots" in str(exc.value)

    def test_rewritten_type_in_permanent_block_raises(self, tmp_path):
        # The mirror of the check above: mis-filing is caught both ways.
        data = minimal_locks()
        data["permanent_slots"]["brand"]["type"] = "DYNAMIC"
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "never-touched" in str(exc.value)

    def test_permanent_block_defaults_to_permanent_type(self, tmp_path):
        # The real file states no `type` on its permanent slots; the block
        # itself is the declaration, so that must load.
        assert "type" not in minimal_locks()["permanent_slots"]["brand"]
        data = minimal_locks()
        data["permanent_slots"]["brand"]["type"] = "FIXED"
        assert permanent_slot_names(write_locks(tmp_path, data)) == ["brand"]

    def test_unknown_slot_type_raises(self, tmp_path):
        data = minimal_locks()
        data["slots"]["body"]["type"] = "SEMI-DYNAMIC"
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_permanent_slot_with_dishonest_count_raises(self, tmp_path):
        data = minimal_locks()
        data["permanent_slots"]["brand"]["observed"] = 21   # real length is 20
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_in_memory_mutation_is_revalidated_on_run(self, locks, baselines):
        # A caller that loads the file and then edits a baseline in memory must
        # not get a pass out of it: every entry point revalidates.
        locks["slots"]["cover_body"]["baseline"] += "x"
        with pytest.raises(CorruptLocksError):
            run_charlint(baselines, locks)

    def test_validate_locks_is_idempotent(self, locks):
        assert validate_locks(validate_locks(locks)) is locks


# ---------------------------------------------------------------------------
# The identity case — every baseline must pass its own lock
# ---------------------------------------------------------------------------

class TestIdentity:
    @pytest.mark.parametrize("slot", ALL_SLOTS)
    def test_each_baseline_passes_its_own_lock(self, slot, locks, baselines):
        res = check_slot(slot, baselines[slot], locks)
        assert res["passed"] is True, res["violations"]
        assert res["delta"] == 0
        assert res["actual"] == res["expected"]
        assert res["score"] == 100
        assert res["violations"] == []
        assert res["failure_mode"] is None

    def test_full_identity_submission_passes(self, locks, identity):
        result = run_charlint(identity, locks)
        assert result["summary"]["all_passed"] is True
        assert result["summary"]["total_score"] == 100 * len(ALL_SLOTS)
        assert sorted(result["slots"]) == sorted(ALL_SLOTS)

    def test_enforced_locks_match_the_captured_numbers(self, locks):
        # Six point locks enforce the OBSERVED count. cover_body is the one
        # range lock: the workbook states it as a band, so it has a window and
        # deliberately no single target (see TestRangeLocks).
        expected = {
            "city_intro": 628, "anchor_venue": 667, "anchor_cafe": 694,
            "counter_venue": 602, "counter_cafe": 414, "night_page": 616,
        }
        assert {s: target_for(s, locks) for s in POINT_LOCKED_SLOTS} == expected
        assert {s: target_range_for(s, locks) for s in ALL_SLOTS} == dict(
            {s: (n, n) for s, n in expected.items()}, cover_body=(350, 358))


# ---------------------------------------------------------------------------
# Overflow / underfill — distinct failure modes
# ---------------------------------------------------------------------------

class TestOverflowUnderfill:
    def test_one_char_overflow_fails(self, locks, baselines):
        res = check_slot("city_intro", baselines["city_intro"] + "x", locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_OVERFLOW
        assert res["delta"] == 1
        assert res["actual"] == 629
        assert res["expected"] == 628
        assert "OVERFLOW" in res["violations"][0]
        assert "+1" in res["violations"][0]
        assert "628" in res["violations"][0]

    def test_one_char_underfill_fails(self, locks, baselines):
        res = check_slot("city_intro", baselines["city_intro"][:-1], locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_UNDERFILL
        assert res["delta"] == -1
        assert res["actual"] == 627
        assert "UNDERFILL" in res["violations"][0]
        assert "-1" in res["violations"][0]

    def test_overflow_and_underfill_are_named_distinctly(self, locks, baselines):
        over = check_slot("counter_cafe", baselines["counter_cafe"] + "xx", locks)
        under = check_slot("counter_cafe", baselines["counter_cafe"][:-2], locks)
        assert over["failure_mode"] != under["failure_mode"]
        assert "OVERFLOW" in over["violations"][0]
        assert "UNDERFILL" not in over["violations"][0]
        assert "UNDERFILL" in under["violations"][0]
        assert "OVERFLOW" not in under["violations"][0]

    def test_score_degrades_with_distance(self, locks, baselines):
        base = baselines["counter_cafe"]
        assert check_slot("counter_cafe", base + "x", locks)["score"] == 90
        assert check_slot("counter_cafe", base + "x" * 3, locks)["score"] == 70
        assert check_slot("counter_cafe", base + "x" * 40, locks)["score"] == 0

    def test_score_at_threshold_still_fails_because_char_miss_is_a_hard_fail(
        self, locks, baselines
    ):
        # 3 chars over scores exactly 70 — the number every sibling linter
        # treats as a passing grade — and must still fail: in a char-locked
        # product any miss breaks the layout.
        res = check_slot("counter_cafe", baselines["counter_cafe"] + "xxx", locks)
        assert res["score"] == 70
        assert res["passed"] is False

    @pytest.mark.parametrize("over, score", [(1, 90), (2, 80), (3, 70), (5, 50), (40, 0)])
    def test_the_verdict_is_binary_and_never_reads_the_score(
        self, over, score, locks, baselines
    ):
        """
        The rule is the count, not a grade. A slot fails at every distance
        outside tolerance, whatever the score says — including scores well
        above any threshold a sibling linter would pass on. Pins that no
        threshold can be reintroduced into the decision without a test dying.
        """
        res = check_slot("counter_cafe", baselines["counter_cafe"] + "x" * over, locks)
        assert res["score"] == score
        assert res["passed"] is False
        assert res["violations"]

    def test_the_module_declares_no_pass_threshold(self):
        # The score is a severity read-out, never an input to `passed`. A
        # PASS_THRESHOLD constant here would be a claim the code does not make,
        # which is exactly how the docstring and the code drifted apart before.
        assert not hasattr(charlint_module, "PASS_THRESHOLD")
        assert "score >= 70" not in (charlint_module.__doc__ or "")

    def test_a_perfect_score_is_not_what_makes_a_slot_pass(self, locks, baselines):
        # The other direction: passing slots all score 100, but it is the zero
        # delta that passed them — score alone never decides anything.
        res = check_slot("counter_cafe", baselines["counter_cafe"], locks)
        assert res["score"] == 100 and res["delta"] == 0 and res["passed"] is True

    def test_one_char_miss_fails_the_whole_run(self, locks, identity):
        identity["anchor_venue"] += "!"
        result = run_charlint(identity, locks)
        assert result["summary"]["all_passed"] is False
        assert result["slots"]["anchor_venue"]["passed"] is False
        assert result["slots"]["city_intro"]["passed"] is True

    def test_declared_tolerance_is_honored(self, tmp_path):
        data = minimal_locks("abcde")
        data["tolerance"] = 2
        path = write_locks(tmp_path, data)
        assert check_slot("body", "abcdefg", path)["passed"] is True     # +2
        assert check_slot("body", "abc", path)["passed"] is True         # -2
        res = check_slot("body", "abcdefgh", path)                       # +3
        assert res["passed"] is False
        assert "tolerance 2" in res["violations"][0]
        # penalty counts only the excess beyond tolerance: 1 char -> -10
        assert res["score"] == 90

    def test_default_tolerance_is_exact(self, locks, baselines):
        # On a POINT-locked slot, which is what tolerance governs. (cover_body
        # is range-locked and one extra space lands inside its band — that is
        # the workbook's rule, not a tolerance; see TestRangeLocks.)
        assert locks["tolerance"] == 0
        assert check_slot("city_intro", baselines["city_intro"] + " ", locks)["passed"] is False


# ---------------------------------------------------------------------------
# Unicode — characters, not bytes
# ---------------------------------------------------------------------------

class TestUnicode:
    def test_baselines_are_multibyte(self, baselines):
        # em-dash U+2014, en-dash U+2013, é U+00E9, middle dot U+00B7
        cover = baselines["cover_body"]
        assert "—" in cover and "é" in cover
        assert "–" in baselines["counter_venue"]
        assert "·" in baselines["night_page"]
        assert len(cover) == 351
        # 2 em-dashes (+2 bytes each) and one é (+1 byte) = 356 bytes.
        assert len(cover.encode("utf-8")) == 356      # byte count is different
        assert len(cover.encode("utf-8")) != len(cover)

    def test_byte_counting_would_pass_what_char_counting_fails(self, locks, baselines):
        """
        The decisive case. Replace one em-dash (3 UTF-8 bytes) with three ASCII
        hyphens (3 bytes): the BYTE length is unchanged, so a byte-counting
        implementation sees a perfect match. The CHARACTER length is +2 and the
        layout really does overflow. CharLint must fail it.

        Run on city_intro, a point lock, so the +2 is a miss on its own terms.
        (The same substitution on the range-locked cover_body lands at 353,
        inside 350-358, and is legal — which is the workbook's rule, not a
        byte-vs-character question. TestRangeLocks covers that separately.)
        """
        candidate = baselines["city_intro"].replace("—", "---", 1)
        assert len(candidate.encode("utf-8")) == len(baselines["city_intro"].encode("utf-8"))
        assert len(candidate) == 630

        res = check_slot("city_intro", candidate, locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_OVERFLOW
        assert res["actual"] == 630
        assert res["delta"] == 2

    def test_ascii_substitution_of_accented_char_shifts_bytes_not_chars(
        self, locks, baselines
    ):
        # "café" -> "cafe": one byte shorter, same character count. A byte
        # counter would call this an underfill; CharLint must pass it.
        candidate = baselines["cover_body"].replace("é", "e", 1)
        assert len(candidate.encode("utf-8")) < len(baselines["cover_body"].encode("utf-8"))
        res = check_slot("cover_body", candidate, locks)
        assert res["actual"] == 351
        assert res["delta"] == 0
        assert res["passed"] is True

    def test_nfd_input_is_not_a_phantom_overflow(self, locks, baselines):
        """
        THE case this rule exists for. "café" arrives from an editor, a
        clipboard or a macOS filename as "cafe" + U+0301: 352 code points for
        text that is visually and typographically identical to the 351-char
        baseline. Counting code points reports OVERFLOW +1 and tells the writer
        to "remove 1 character" — an instruction they cannot act on, because
        there is no character on the page to remove.
        """
        nfd = unicodedata.normalize("NFD", baselines["cover_body"])
        assert nfd != baselines["cover_body"]      # a genuinely different string
        assert len(nfd) == 352                     # ... and a longer one

        res = check_slot("cover_body", nfd, locks)
        assert res["passed"] is True
        assert res["delta"] == 0
        assert res["actual"] == 351
        assert res["failure_mode"] is None
        assert res["violations"] == []

    def test_nfd_input_is_reported_even_though_it_passes(self, locks, identity):
        # Not silent: the count moved from what the submitter's own tool would
        # report, so the run says so — as a warning, never a failure.
        identity["cover_body"] = unicodedata.normalize("NFD", identity["cover_body"])
        result = run_charlint(identity, locks)
        assert result["summary"]["all_passed"] is True
        assert result["slots"]["cover_body"]["nfc_normalized"] is True
        note = [w for w in result["warnings"] if w.startswith("CANONICAL FORM:")]
        assert len(note) == 1
        assert "cover_body" in note[0]
        assert "352" in note[0] and "351" in note[0]

    def test_nfc_input_is_not_flagged(self, locks, identity):
        result = run_charlint(identity, locks)
        assert all(r["nfc_normalized"] is False for r in result["slots"].values())
        assert not any(w.startswith("CANONICAL FORM:") for w in result["warnings"])

    def test_a_real_overflow_in_nfd_text_still_fails_with_an_actionable_count(
        self, locks, baselines
    ):
        # The fix must not swallow real misses: NFD copy that is genuinely too
        # long still fails, and the number it reports is a number the writer
        # can act on by deleting that many visible characters.
        #
        # cover_body is the only baseline carrying an é, so the NFD cases live
        # here — and it is range-locked, so "genuinely too long" means past the
        # 358 ceiling, not past 351. 12 extra characters compose to 363, and
        # the 5 it asks for are 5 real characters on the page.
        nfd = unicodedata.normalize("NFD", baselines["cover_body"]) + "x" * 12
        assert len(nfd) == 364          # 352 code points decomposed, + 12
        res = check_slot("cover_body", nfd, locks)
        assert res["actual"] == 363     # ... 363 characters once composed
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_OVERFLOW
        assert res["delta"] == 5
        assert "Remove 5 character(s)" in res["violations"][0]

    def test_composition_is_nfc_not_nfkc(self, locks, baselines):
        """
        NFKC is a COMPATIBILITY mapping and would launder real whitespace
        defects: it rewrites a non-breaking space to a plain space. A candidate
        that swaps a space for U+00A0 is a real edit to the text and must stay
        visible, so the composition applied here has to be NFC.
        """
        assert CANONICAL_FORM == "NFC"
        nbsp = baselines["counter_cafe"].replace(" ", "\u00a0", 1)
        assert len(nbsp) == len(baselines["counter_cafe"])
        assert unicodedata.normalize("NFKC", nbsp) == baselines["counter_cafe"]
        assert unicodedata.normalize("NFC", nbsp) == nbsp

        res = check_slot("counter_cafe", nbsp, locks)
        assert res["delta"] == 0            # NBSP is one character, like a space
        assert res["nfc_normalized"] is False   # ... and already canonical
        # Fed to a PERMANENT slot the same substitution is a mutation, which is
        # what NFKC would have hidden.
        perm = check_slot("brand_subline", "THE\u00a0CITY IS THE GYM.", locks)
        assert perm["passed"] is False
        assert perm["failure_mode"] == FAILURE_PERMANENT_MUTATION

    def test_composition_is_composing_not_decomposing(self, locks, baselines):
        # The inverse mutation: normalising to NFD instead of NFC would break
        # the identity case outright, since the baselines are composed.
        res = check_slot("cover_body", baselines["cover_body"], locks)
        assert res["actual"] == 351
        assert len(unicodedata.normalize("NFD", baselines["cover_body"])) == 352

    @pytest.mark.parametrize("char, name", [
        ("—", "em dash"),
        ("–", "en dash"),
        ("·", "middle dot"),
        ("’", "curly apostrophe"),
        ("é", "e acute"),
    ])
    def test_the_decision_is_coherent_across_every_special_character(
        self, char, name, tmp_path
    ):
        """
        Every non-ASCII character the baselines carry, counted one way: one
        character each, in whichever canonically equivalent spelling it
        arrives. Only é has a decomposition at all — for the other four NFC is
        the identity, so the rule changes nothing about how they are counted.
        """
        assert unicodedata.normalize("NFC", char) == char
        data = minimal_locks(f"ab{char}de")
        path = write_locks(tmp_path, data)
        assert target_for("body", path) == 5
        assert check_slot("body", f"ab{char}de", path)["passed"] is True
        decomposed = unicodedata.normalize("NFD", f"ab{char}de")
        assert check_slot("body", decomposed, path)["passed"] is True

    def test_permanent_slot_accepts_a_canonically_equivalent_spelling(self, tmp_path):
        # A PERMANENT slot is checked for mutation, and re-spelling é is not a
        # mutation: same text, same render, nothing for the owner to restore.
        data = minimal_locks()
        data["permanent_slots"]["tagline"] = {"baseline": "CAFÉ CITY"}
        path = write_locks(tmp_path, data)
        assert check_slot("tagline", "CAFÉ CITY", path)["passed"] is True
        assert check_slot(
            "tagline", unicodedata.normalize("NFD", "CAFÉ CITY"), path)["passed"] is True
        # ... while a real edit of the same length still fails.
        assert check_slot("tagline", "CAFE CITY", path)["passed"] is False

    def test_a_decomposed_baseline_in_the_locks_file_is_corrupt(self, tmp_path):
        """
        Locks are stored composed, because that is the form candidates are
        measured in. A decomposed baseline would count its own combining marks
        and fail its own lock the moment it was fed back, so the file is
        rejected rather than quietly re-encoded.
        """
        data = minimal_locks(unicodedata.normalize("NFD", "café"))
        data["slots"]["body"]["principles_lock"] = 5
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert CANONICAL_FORM in str(exc.value)

    def test_astral_characters_count_as_one_character(self, tmp_path):
        # Defensive: an emoji is 1 character and 4 UTF-8 bytes. (PRINCIPLES
        # Sec. 7 bans emoji in copy — that is ProhibLint's job, not ours; ours
        # is to count it as one.)
        data = minimal_locks("ab\U0001F600de")
        path = write_locks(tmp_path, data)
        assert target_for("body", path) == 5
        assert check_slot("body", "ab\U0001F600de", path)["passed"] is True


# ---------------------------------------------------------------------------
# Newlines — measure the whole element, never a sub-slice
# ---------------------------------------------------------------------------

class TestNewlines:
    def test_night_page_identity_covers_the_whole_element(self, locks, baselines):
        night = baselines["night_page"]
        assert night.count("\n") == 3          # title, rule line, blank line
        assert len(night) == 616
        res = check_slot("night_page", night, locks)
        assert res["passed"] is True
        assert res["expected"] == 616

    def test_prose_only_is_an_underfill_not_a_pass(self, locks, baselines):
        """
        The trap the `_note` on night_page warns about: the body prose alone is
        558 characters. Measuring that sub-slice against the 616 lock must fail
        by exactly the 58-character header block (title + rule line + blank).
        """
        prose = baselines["night_page"].split("\n\n", 1)[1]
        assert len(prose) == 558
        res = check_slot("night_page", prose, locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_UNDERFILL
        assert res["delta"] == -58

    def test_header_block_alone_is_an_underfill(self, locks, baselines):
        header = baselines["night_page"].split("\n\n", 1)[0]
        assert len(header) == 56               # + the "\n\n" separator = 58
        res = check_slot("night_page", header, locks)
        assert res["failure_mode"] == FAILURE_UNDERFILL
        assert res["delta"] == -560

    def test_newlines_are_counted_as_characters(self, locks, baselines):
        # Collapse the blank line: one character fewer, and the lock breaks.
        candidate = baselines["night_page"].replace("\n\n", "\n", 1)
        res = check_slot("night_page", candidate, locks)
        assert res["delta"] == -1
        assert res["passed"] is False

    def test_crlf_is_two_characters(self, locks, baselines):
        candidate = baselines["night_page"].replace("\n", "\r\n")
        res = check_slot("night_page", candidate, locks)
        assert res["delta"] == 3               # three newlines became CRLF
        assert res["failure_mode"] == FAILURE_OVERFLOW


# ---------------------------------------------------------------------------
# No normalization — count exactly what the layout receives
# ---------------------------------------------------------------------------

class TestNoNormalization:
    def test_trailing_space_is_an_overflow(self, locks, baselines):
        res = check_slot("anchor_cafe", baselines["anchor_cafe"] + " ", locks)
        assert res["passed"] is False
        assert res["delta"] == 1

    def test_leading_space_is_an_overflow(self, locks, baselines):
        res = check_slot("anchor_cafe", " " + baselines["anchor_cafe"], locks)
        assert res["passed"] is False
        assert res["delta"] == 1

    def test_trailing_newline_is_an_overflow(self, locks, baselines):
        res = check_slot("anchor_cafe", baselines["anchor_cafe"] + "\n", locks)
        assert res["passed"] is False
        assert res["delta"] == 1

    def test_text_that_would_pass_after_stripping_still_fails(self, locks, baselines):
        candidate = "  " + baselines["anchor_cafe"] + "  \n"
        assert candidate.strip() == baselines["anchor_cafe"]
        res = check_slot("anchor_cafe", candidate, locks)
        assert res["passed"] is False
        assert res["delta"] == 5

    def test_double_space_between_sentences_is_not_collapsed(self, locks, baselines):
        candidate = baselines["anchor_cafe"].replace(". ", ".  ", 1)
        res = check_slot("anchor_cafe", candidate, locks)
        assert res["delta"] == 1
        assert res["passed"] is False

    def test_non_string_candidate_raises(self, locks):
        with pytest.raises(TypeError):
            check_slot("cover_body", None, locks)
        with pytest.raises(TypeError):
            run_charlint({"cover_body": 351}, locks)

    @pytest.mark.parametrize("value, type_name", [
        (None, "NoneType"), (351, "int"), (35.1, "float"), (True, "bool"),
        (["a", "b"], "list"), (("a",), "tuple"), ({"text": "x"}, "dict"),
        (b"bytes", "bytes"),
    ])
    def test_the_non_str_guard_is_what_rejects_non_strings(self, value, type_name, locks):
        """
        Pins the guard itself, not the crash that happens to follow it.

        Without the isinstance check some of these still raise — len(None) and
        normalize(NFC, 351) both do — so a test that only asserts TypeError
        passes with the guard deleted. A list does not: len(["a", "b"]) is a
        happy 2, and a list of paragraphs would be silently "measured" as two
        characters. The message is asserted because it is the only thing that
        distinguishes the deliberate rejection from an incidental one.
        """
        with pytest.raises(TypeError) as exc:
            check_slot("cover_body", value, locks)
        assert f"must be a str, got {type_name}" in str(exc.value)
        assert "not an empty fill" in str(exc.value)

    def test_a_list_of_paragraphs_is_never_measured_as_its_length(self, locks):
        # The decisive one: len() would succeed here and report 2 characters.
        with pytest.raises(TypeError):
            check_slot("cover_body", ["para one", "para two"], locks)
        with pytest.raises(TypeError):
            run_charlint({"cover_body": ["para one", "para two"]}, locks)


# ---------------------------------------------------------------------------
# PERMANENT slots — never touched (PRINCIPLES.txt Sec. 4)
# ---------------------------------------------------------------------------

class TestPermanentSlots:
    def test_exact_baseline_passes(self, locks, identity):
        identity["brand_subline"] = "THE CITY IS THE GYM."
        identity["cover_spec_line"] = "9 EXERCISES · 50 MINUTES · ALL LEVELS"
        result = run_charlint(identity, locks)
        assert result["summary"]["all_passed"] is True
        assert result["slots"]["brand_subline"]["passed"] is True

    def test_same_length_mutation_is_a_hard_failure_not_a_delta(self, locks, identity):
        # "." -> "!": identical character count, still forbidden.
        identity["brand_subline"] = "THE CITY IS THE GYM!"
        result = run_charlint(identity, locks)
        res = result["slots"]["brand_subline"]
        assert res["delta"] == 0
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_PERMANENT_MUTATION
        assert res["score"] == 0
        assert "PERMANENT SLOT MUTATED" in res["violations"][0]
        assert "not a char-count delta" in res["violations"][0]
        assert result["summary"]["all_passed"] is False

    def test_case_change_is_a_mutation(self, locks):
        res = check_slot("brand_subline", "The City Is The Gym.", locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_PERMANENT_MUTATION

    def test_one_character_of_difference_is_enough(self, locks):
        res = check_slot("cover_spec_line",
                         "9 EXERCISES · 50 MINUTES · ALL LEVEL", locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_PERMANENT_MUTATION

    def test_middle_dot_swapped_for_ascii_dot_is_a_mutation(self, locks):
        res = check_slot("cover_spec_line",
                         "9 EXERCISES . 50 MINUTES . ALL LEVELS", locks)
        assert res["delta"] == 0                  # same character count
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_PERMANENT_MUTATION

    def test_omitting_permanent_slots_is_correct_behaviour(self, locks, identity):
        # An issue fill never touches them, so their absence must not fail and
        # must not be reported as "not filled".
        result = run_charlint(identity, locks)
        assert "brand_subline" not in result["slots"]
        assert "cover_spec_line" not in result["slots"]
        assert result["summary"]["all_passed"] is True

    def test_violation_names_the_first_differing_index(self, locks):
        res = check_slot("brand_subline", "THE CITY IS THE GYM!", locks)
        assert "index 19" in res["violations"][0]

    def test_first_differing_index_for_a_truncated_candidate(self, locks):
        # Dropped final period: the candidate is a strict prefix, so the
        # divergence is where it ends, not index 0.
        res = check_slot("brand_subline", "THE CITY IS THE GYM", locks)
        assert "index 19" in res["violations"][0]

    def test_first_differing_index_for_a_lengthened_candidate(self, locks):
        res = check_slot("brand_subline", "THE CITY IS THE GYM. ", locks)
        assert "index 20" in res["violations"][0]


# ---------------------------------------------------------------------------
# Unknown slots — an error, not a silent no-op
# ---------------------------------------------------------------------------

class TestUnknownSlot:
    def test_unknown_slot_name_raises(self, locks, identity):
        identity["cover_bdy"] = "typo'd slot name"
        with pytest.raises(UnknownSlotError):
            run_charlint(identity, locks)

    def test_error_names_the_offender_and_the_valid_slots(self, locks):
        with pytest.raises(UnknownSlotError) as exc:
            run_charlint({"nightlife": "..."}, locks)
        message = str(exc.value)
        assert "'nightlife'" in message
        assert "cover_body" in message
        assert "night_page" in message

    def test_unknown_slot_is_a_valueerror_subclass(self, locks):
        with pytest.raises(ValueError):
            run_charlint({"bogus": "..."}, locks)

    def test_permanent_slot_names_are_not_unknown(self, locks):
        result = run_charlint({"brand_subline": "THE CITY IS THE GYM."}, locks)
        assert result["slots"]["brand_subline"]["passed"] is True

    def test_check_slot_rejects_unknown_names_too(self, locks):
        with pytest.raises(UnknownSlotError):
            check_slot("no_such_slot", "text", locks)

    def test_all_unknown_names_are_reported_at_once(self, locks):
        with pytest.raises(UnknownSlotError) as exc:
            run_charlint({"aaa": "x", "zzz": "y"}, locks)
        assert "'aaa'" in str(exc.value) and "'zzz'" in str(exc.value)


# ---------------------------------------------------------------------------
# Missing slots — reported, never vacuously passed
# ---------------------------------------------------------------------------

class TestMissingSlot:
    def test_empty_submission_fails_every_slot(self, locks):
        result = run_charlint({}, locks)
        assert result["summary"]["all_passed"] is False
        assert sorted(result["slots"]) == sorted(ALL_SLOTS)
        for name, res in result["slots"].items():
            assert res["failure_mode"] == FAILURE_NOT_FILLED
            assert res["passed"] is False
        assert result["summary"]["total_score"] == 0

    def test_one_missing_slot_is_reported_and_the_rest_still_pass(self, locks, identity):
        del identity["night_page"]
        result = run_charlint(identity, locks)
        res = result["slots"]["night_page"]
        assert res["failure_mode"] == FAILURE_NOT_FILLED
        assert res["expected"] == 616
        assert res["delta"] == -616
        assert "NOT FILLED" in res["violations"][0]
        assert result["summary"]["all_passed"] is False
        assert result["slots"]["cover_body"]["passed"] is True

    def test_not_filled_is_distinct_from_underfill(self, locks, identity):
        del identity["counter_cafe"]
        empty = dict(identity, counter_cafe="")
        missing = run_charlint(identity, locks)["slots"]["counter_cafe"]
        submitted_empty = run_charlint(empty, locks)["slots"]["counter_cafe"]
        assert missing["failure_mode"] == FAILURE_NOT_FILLED
        assert submitted_empty["failure_mode"] == FAILURE_UNDERFILL
        assert missing["delta"] == submitted_empty["delta"] == -414

    def test_unlocked_and_manual_slots_are_exempt_from_not_filled(self, tmp_path):
        # PRINCIPLES Sec. 4: UNLOCKED counts may flex, MANUAL is owner-swapped.
        # An issue fill is not expected to supply either, so absence is fine.
        data = minimal_locks()
        data["slots"]["editors_note"] = {
            "type": "UNLOCKED", "principles_lock": 5, "baseline": "abcde"}
        data["slots"]["upsell"] = {
            "type": "MANUAL", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)
        result = run_charlint({"body": "abcde", "upsell": "abcde"}, path)
        assert "editors_note" not in result["slots"]
        assert result["summary"]["all_passed"] is True
        # MANUAL still has to hit its lock when it IS supplied.
        assert run_charlint(
            {"body": "abcde", "upsell": "abcdef"}, path
        )["slots"]["upsell"]["passed"] is False

    def test_an_unsubmitted_manual_slot_is_warned_about_not_vanished(self, tmp_path):
        """
        Exempt from failing is not the same as invisible. An unfilled MANUAL
        slot used to produce no row, no warning and no mention at all — leaving
        no way to tell "the owner governs this one" from "we forgot this one".
        """
        data = minimal_locks()
        data["slots"]["upsell"] = {
            "type": "MANUAL", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)

        result = run_charlint({"body": "abcde"}, path)
        assert "upsell" not in result["slots"]          # nothing to gate ...
        assert result["summary"]["all_passed"] is True  # ... and not a failure
        notes = [w for w in result["warnings"] if w.startswith("NOT SUBMITTED:")]
        assert len(notes) == 1
        assert "upsell" in notes[0]
        assert "MANUAL" in notes[0]

    def test_a_submitted_manual_slot_produces_no_not_submitted_warning(self, tmp_path):
        data = minimal_locks()
        data["slots"]["upsell"] = {
            "type": "MANUAL", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)
        result = run_charlint({"body": "abcde", "upsell": "abcde"}, path)
        assert not any(w.startswith("NOT SUBMITTED:") for w in result["warnings"])

    def test_an_unsubmitted_unlocked_slot_is_warned_about_too(self, tmp_path):
        # Both owner-governed types get the same treatment; UNLOCKED also keeps
        # its standing "not count-gated" warning, which says a different thing.
        data = minimal_locks()
        data["slots"]["editors_note"] = {
            "type": "UNLOCKED", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)
        warnings = run_charlint({"body": "abcde"}, path)["warnings"]
        assert any(w.startswith("NOT SUBMITTED:") and "editors_note" in w
                   for w in warnings)
        assert any(w.startswith("UNLOCKED:") and "editors_note" in w for w in warnings)

    def test_every_locked_slot_is_either_a_row_or_a_warning(self, tmp_path):
        """
        The invariant behind both of the above: after any run, no slot in the
        locks file is unaccounted for. Either it was gated (a row) or the run
        said why it was not (a warning naming it).
        """
        data = minimal_locks()
        data["slots"]["editors_note"] = {
            "type": "UNLOCKED", "principles_lock": 5, "baseline": "abcde"}
        data["slots"]["upsell"] = {
            "type": "MANUAL", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)
        result = run_charlint({}, path)
        for name in slot_names(path):
            assert name in result["slots"] or any(name in w for w in result["warnings"]), name

    def test_unlocked_slots_are_not_count_gated_but_are_warned_about(self, tmp_path):
        # PRINCIPLES Sec. 4: UNLOCKED is "owner-flagged ... where counts may
        # flex". Enforcing an exact count there would be wrong — but an
        # un-gated slot must never be invisible, so it is warned every run.
        data = minimal_locks()
        data["slots"]["editors_note"] = {
            "type": "UNLOCKED", "principles_lock": 5, "baseline": "abcde"}
        path = write_locks(tmp_path, data)

        result = run_charlint(
            {"body": "abcde", "editors_note": "a much longer editor's note"}, path)
        assert result["slots"]["editors_note"]["passed"] is True
        assert result["slots"]["editors_note"]["violations"] == []
        assert result["slots"]["editors_note"]["actual"] == 27
        assert result["summary"]["all_passed"] is True
        assert any("UNLOCKED" in w and "editors_note" in w
                   for w in result["warnings"])

    def test_unlocked_slot_baseline_need_not_match_its_recorded_count(self, tmp_path):
        # Corollary: a flex slot's number is advisory, so it is exempt from the
        # enforced-lock == len(baseline) guard that binds every locked slot.
        data = minimal_locks()
        data["slots"]["editors_note"] = {
            "type": "UNLOCKED", "principles_lock": 999, "baseline": "abcde"}
        assert slot_names(write_locks(tmp_path, data)) == ["body", "editors_note"]

    def test_a_run_that_checked_nothing_does_not_pass(self, tmp_path):
        # Degenerate case: every slot is owner-governed and nothing was
        # submitted, so zero slots were checked. "all() of nothing" is True in
        # Python — an empty run must not report PASS.
        data = {
            "tolerance": 0,
            "slots": {"upsell": {"type": "MANUAL", "principles_lock": 5,
                                 "baseline": "abcde"}},
        }
        result = run_charlint({}, write_locks(tmp_path, data))
        assert result["slots"] == {}
        assert result["summary"]["all_passed"] is False


# ---------------------------------------------------------------------------
# Drift — reported separately from failure, on every run
# ---------------------------------------------------------------------------

def drifting_locks(baseline="Hello world", documented=13):
    """A point-locked file with a GENUINE drift: documented != measured."""
    return {
        "ruleset": "test",
        "tolerance": 0,
        "slots": {
            "body": {
                "type": "DYNAMIC",
                "principles_lock": documented,
                "observed": len(baseline),
                "drift": len(baseline) - documented,
                "baseline": baseline,
            },
        },
    }


class TestDrift:
    """
    The drift mechanism is intact. What changed is that the shipped Seattle
    file no longer has an instance of it — cover_body's "-6" was a point being
    compared to a band, not a template that moved — so drift is pinned here on
    a file that genuinely drifts.
    """

    def test_drift_warning_appears_on_a_fully_passing_run(self, tmp_path):
        path = write_locks(tmp_path, drifting_locks())
        result = run_charlint({"body": "Hello world"}, path)
        assert result["summary"]["all_passed"] is True     # nothing failed
        assert len(result["warnings"]) == 1                # and yet
        assert "body" in result["warnings"][0]

    def test_warning_names_both_numbers_the_drift_and_the_enforced_one(self, tmp_path):
        path = write_locks(tmp_path, drifting_locks())
        warning = drift_warnings(path)[0]
        assert "DRIFT" in warning
        assert "13" in warning         # what PRINCIPLES.txt documents
        assert "11" in warning         # what the template measures
        assert "-2" in warning         # the signed drift
        assert "enforcing 11" in warning
        assert "owner decides" in warning

    def test_drift_never_fails_the_run(self, tmp_path):
        path = write_locks(tmp_path, drifting_locks())
        result = run_charlint({"body": "Hello world"}, path)
        assert result["slots"]["body"]["passed"] is True
        assert result["slots"]["body"]["score"] == 100

    def test_drift_is_reported_even_when_the_slot_is_not_filled(self, tmp_path):
        path = write_locks(tmp_path, drifting_locks())
        result = run_charlint({}, path)
        assert result["slots"]["body"]["passed"] is False   # not filled
        assert any("DRIFT" in w and "body" in w for w in result["warnings"])

    def test_zero_drift_slot_produces_no_warning(self, locks):
        # night_page records observed == principles_lock == 616.
        assert locks["slots"]["night_page"]["drift"] == 0
        assert not any("night_page" in w for w in drift_warnings(locks))

    def test_the_shipped_file_no_longer_drifts_at_all(self, locks, identity):
        # The finding, pinned. Every point lock reads drift 0, cover_body is
        # banded and carries no drift, and a fully passing run says nothing —
        # no "owner decides" nag left standing after the owner's own workbook
        # decided it.
        assert drift_warnings(locks) == []
        assert run_charlint(identity, locks)["warnings"] == []

    def test_enforced_lock_is_observed_not_the_documented_number(self, tmp_path):
        data = drifting_locks()
        loaded = load_locks(write_locks(tmp_path, data))
        assert enforced_lock(loaded["slots"]["body"]) == 11
        # Copy written to the DOCUMENTED 13 fails against the live 11.
        res = check_slot("body", "Hello world!!", loaded)
        assert res["actual"] == 13
        assert res["expected"] == 11
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_OVERFLOW

    def test_slot_without_observed_falls_back_to_principles_lock(self, tmp_path):
        # The real file now records `observed` on every slot (see
        # TestObservedIsRecordedEverywhere), so the fallback is pinned on a
        # hand-built file instead of on the shipped capture.
        data = minimal_locks("abcde")
        assert "observed" not in data["slots"]["body"]
        loaded = load_locks(write_locks(tmp_path, data))
        assert enforced_lock(loaded["slots"]["body"]) == 5
        assert target_for("body", loaded) == 5


# ---------------------------------------------------------------------------
# `observed` is recorded on every slot — measured, never assumed (C5)
# ---------------------------------------------------------------------------

class TestObservedIsRecordedEverywhere:
    """
    A slot with no `observed` is indistinguishable from a slot that was
    measured and happened to agree with PRINCIPLES.txt. The capture has to be
    able to tell "measured and equal" from "assumed, never measured", so every
    slot carries the number.
    """

    def test_every_slot_records_observed_and_drift(self, locks):
        for name, spec in locks["slots"].items():
            assert "observed" in spec, f"{name} has no observed count"
            if name in RANGE_LOCKED_SLOTS:
                # A band has no point to drift from, and saying so is not the
                # same silence the `observed` rule exists to prevent: the
                # measurement is still recorded, only the drift is undefined.
                assert "drift" not in spec, f"{name} is banded and cannot drift"
            else:
                assert "drift" in spec, f"{name} has no drift"

    @pytest.mark.parametrize("slot", ALL_SLOTS)
    def test_every_recorded_count_matches_the_baseline_it_describes(self, slot, locks):
        # Machine-counted here too: the file's number is checked against the
        # file's own string, never against a number typed into this test.
        spec = locks["slots"][slot]
        assert spec["observed"] == len(spec["baseline"])
        if slot not in RANGE_LOCKED_SLOTS:
            assert spec["drift"] == spec["observed"] - spec["principles_lock"]

    def test_nothing_in_the_shipped_file_drifts(self, locks):
        drifting = {n: s["drift"] for n, s in locks["slots"].items()
                    if s.get("drift")}
        assert drifting == {}

    def test_recording_observed_did_not_move_any_enforced_lock(self, locks, baselines):
        # The whole point is that the numbers were already true. Recording them
        # must be a no-op for every gate: identity still holds slot by slot.
        for slot in ALL_SLOTS:
            low, high = target_range_for(slot, locks)
            assert low <= len(baselines[slot]) <= high
            assert check_slot(slot, baselines[slot], locks)["passed"] is True
        for slot in POINT_LOCKED_SLOTS:
            assert target_for(slot, locks) == len(baselines[slot])


# ---------------------------------------------------------------------------
# RANGE LOCKS — a slot whose rule is a band, not a point
#
# The master workbook ("Seattle Series Magazine", the sheet PRINCIPLES.txt
# Sec. 5 names as the single source of truth) states the cover body as
# CHAR COUNT "~353 (lock 350-358 incl. spaces)". Enforcing a point there made
# the gate stricter than its own rulebook: a legal 355-character body was
# failed and told to delete 4 characters it was entitled to keep.
# ---------------------------------------------------------------------------

def banded_locks(low=350, high=358, baseline=None, **slot_overrides):
    """A tiny locks file whose single slot is range-locked."""
    baseline = "b" * low if baseline is None else baseline
    slot = {
        "type": "DYNAMIC",
        LOCK_RANGE_KEY: {"min": low, "max": high, "source": "test workbook row"},
        "baseline": baseline,
    }
    slot.update(slot_overrides)
    return {"ruleset": "test", "tolerance": 0, "slots": {"body": slot}}


class TestRangeLockEdges:
    """Both edges legal, one character past either edge is not."""

    @pytest.mark.parametrize("count", [350, 358])
    def test_both_edges_are_inclusive(self, count, locks, baselines):
        res = check_slot("cover_body", sized(baselines["cover_body"], count), locks)
        assert res["passed"] is True, res["violations"]
        assert res["delta"] == 0
        assert res["violations"] == []
        assert res["failure_mode"] is None
        assert res["score"] == 100

    @pytest.mark.parametrize("count", [350, 351, 352, 355, 357, 358])
    def test_every_count_in_the_window_passes(self, count, locks, baselines):
        # Including 351 (the live template) and 357 (what PRINCIPLES.txt
        # transcribed): the two numbers the old "-6 drift" asked the owner to
        # choose between are both simply legal.
        assert check_slot(
            "cover_body", sized(baselines["cover_body"], count), locks)["passed"] is True

    def test_one_character_under_the_floor_fails(self, locks, baselines):
        res = check_slot("cover_body", sized(baselines["cover_body"], 349), locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_UNDERFILL
        assert res["actual"] == 349
        assert res["delta"] == -1
        assert res["expected"] == 350

    def test_one_character_over_the_ceiling_fails(self, locks, baselines):
        res = check_slot("cover_body", sized(baselines["cover_body"], 359), locks)
        assert res["passed"] is False
        assert res["failure_mode"] == FAILURE_OVERFLOW
        assert res["actual"] == 359
        assert res["delta"] == 1
        assert res["expected"] == 358

    def test_the_edges_are_not_off_by_one_in_either_direction(self, locks, baselines):
        # 349/350 and 358/359 pinned together, so an edge cannot be moved
        # inward or outward without a test dying.
        verdicts = {n: check_slot(
            "cover_body", sized(baselines["cover_body"], n), locks)["passed"]
            for n in (349, 350, 358, 359)}
        assert verdicts == {349: False, 350: True, 358: True, 359: False}


class TestRangeLockRemediation:
    """Out of range points at the NEAREST legal edge, never at a midpoint."""

    def test_over_the_ceiling_is_told_to_reach_the_ceiling(self, locks, baselines):
        res = check_slot("cover_body", sized(baselines["cover_body"], 362), locks)
        violation = res["violations"][0]
        assert "OVERFLOW" in violation
        assert "350–358" in violation           # the whole rule, not one edge
        assert "Remove 4 character(s) to land on 358" in violation
        assert "nearest legal count" in violation
        # The midpoint (354) is 8 characters away and is NOT what is asked for.
        assert "354" not in violation
        assert "Remove 8" not in violation

    def test_under_the_floor_is_told_to_reach_the_floor(self, locks, baselines):
        res = check_slot("cover_body", sized(baselines["cover_body"], 344), locks)
        violation = res["violations"][0]
        assert "UNDERFILL" in violation
        assert "350–358" in violation
        assert "Add 6 character(s) to land on 350" in violation
        assert "nearest legal count" in violation
        assert "354" not in violation
        assert "Add 10" not in violation

    def test_the_number_asked_for_actually_lands(self, locks, baselines):
        # Both directions, acted on literally: the remediation is a number a
        # writer can execute, and executing it passes.
        for count in (344, 362):
            draft = sized(baselines["cover_body"], count)
            needed = chars_to_target("cover_body", draft, locks)["chars_needed"]
            fixed = draft + "y" * needed if needed > 0 else draft[:len(draft) + needed]
            assert check_slot("cover_body", fixed, locks)["passed"] is True

    def test_an_in_range_candidate_is_not_nagged(self, locks, baselines):
        # The defect in one test: a legal 355 must produce no violation, no
        # failure and no "move to 353" advice.
        res = check_slot("cover_body", sized(baselines["cover_body"], 355), locks)
        assert res["passed"] is True
        assert res["violations"] == []
        assert res["delta"] == 0
        assert res["score"] == 100
        info = chars_to_target("cover_body", sized(baselines["cover_body"], 355), locks)
        assert info["action"] == "none"
        assert info["chars_needed"] == 0

    def test_nearest_legal_is_the_clamp_not_the_midpoint(self):
        assert nearest_legal(344, (350, 358)) == 350
        assert nearest_legal(362, (350, 358)) == 358
        assert nearest_legal(355, (350, 358)) == 355     # already legal
        assert nearest_legal(7, (7, 7)) == 7             # a point lock


class TestRangeLockFileRules:
    """What a locks file may and may not say about a band."""

    def test_band_plus_conflicting_exact_count_raises(self, tmp_path):
        for field in ("principles_lock", "observed"):
            data = banded_locks(**{field: 400})
            with pytest.raises(CorruptLocksError) as exc:
                load_locks(write_locks(tmp_path, data, name=f"{field}.json"))
            assert "350–358" in str(exc.value)
            assert f"{field}=400" in str(exc.value)
            assert "no precedence rule" in str(exc.value)

    def test_a_conflicting_count_is_caught_below_the_band_too(self, tmp_path):
        data = banded_locks(principles_lock=300)
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_an_exact_count_inside_the_band_is_documentation_not_a_conflict(self, tmp_path):
        # This is what the real cover_body does: 351 measured, 357 documented,
        # both legal, neither enforced as a point.
        data = banded_locks(baseline="b" * 351, observed=351, principles_lock=357)
        loaded = load_locks(write_locks(tmp_path, data))
        assert lock_band(loaded["slots"]["body"]) == (350, 358)
        assert drift_warnings(loaded) == []

    @pytest.mark.parametrize("count", [350, 358])
    def test_an_exact_count_sitting_on_an_edge_is_not_a_conflict(self, count, tmp_path):
        # The band is inclusive for the FILE's own numbers too, not just for
        # candidates. A template that measures exactly the floor (or exactly
        # the ceiling) is legal data, not a second rule — rejecting it would
        # make the file format stricter than the band it records.
        data = banded_locks(baseline="b" * count, observed=count)
        loaded = load_locks(write_locks(tmp_path, data))
        assert lock_band(loaded["slots"]["body"]) == (350, 358)
        assert check_slot("body", "b" * count, loaded)["passed"] is True

    def test_drift_on_a_banded_slot_raises(self, tmp_path):
        data = banded_locks(baseline="b" * 351, observed=351,
                            principles_lock=357, drift=-6)
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "drift" in str(exc.value)
        assert "no single point to drift from" in str(exc.value)

    def test_a_baseline_outside_its_own_band_raises(self, tmp_path):
        data = banded_locks(baseline="b" * 349)
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "349" in str(exc.value)

    def test_an_empty_band_raises(self, tmp_path):
        data = banded_locks(low=358, high=350, baseline="b" * 350)
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "empty" in str(exc.value)

    @pytest.mark.parametrize("raw", [
        {"min": 350},                                  # no ceiling
        {"max": 358},                                  # no floor
        {"min": 350, "max": "358"},                    # a string edge
        {"min": 350, "max": 358.0},                    # a float edge
        {"min": True, "max": 358},                     # a bool edge
        {"min": -1, "max": 358},                       # a negative edge
        {"min": 350, "max": 358, "minimum": 350},      # a misspelled key
        {"min": 350, "max": 358, "source": ""},        # an empty provenance
        [350, 358],                                    # positional, not named
        350,                                           # not an object at all
    ])
    def test_a_malformed_band_raises(self, raw, tmp_path):
        data = banded_locks()
        data["slots"]["body"][LOCK_RANGE_KEY] = raw
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_a_band_on_a_permanent_slot_raises(self, tmp_path):
        data = minimal_locks()
        data["permanent_slots"]["brand"][LOCK_RANGE_KEY] = {"min": 1, "max": 99}
        with pytest.raises(CorruptLocksError) as exc:
            load_locks(write_locks(tmp_path, data))
        assert "exact strings" in str(exc.value)

    def test_a_band_alone_is_a_complete_lock(self, tmp_path):
        # No principles_lock, no observed: the band is the rule.
        data = banded_locks()
        assert "principles_lock" not in data["slots"]["body"]
        loaded = load_locks(write_locks(tmp_path, data))
        assert target_range_for("body", loaded) == (350, 358)

    def test_a_slot_with_no_rule_at_all_still_raises(self, tmp_path):
        data = banded_locks()
        del data["slots"]["body"][LOCK_RANGE_KEY]
        with pytest.raises(CorruptLocksError):
            load_locks(write_locks(tmp_path, data))

    def test_a_degenerate_band_is_legal_and_still_reads_as_a_band(self, tmp_path):
        data = banded_locks(low=5, high=5, baseline="abcde")
        loaded = load_locks(write_locks(tmp_path, data))
        assert is_range_locked(loaded["slots"]["body"]) is True
        assert check_slot("body", "abcde", loaded)["passed"] is True
        assert check_slot("body", "abcdef", loaded)["passed"] is False

    def test_the_file_level_tolerance_does_not_widen_a_band(self, tmp_path):
        # A band states its own edges. Widening them by the file's tolerance
        # would enforce a window the workbook never wrote.
        data = banded_locks()
        data["tolerance"] = 5
        path = write_locks(tmp_path, data)
        assert check_slot("body", "b" * 358, path)["passed"] is True
        assert check_slot("body", "b" * 359, path)["passed"] is False
        info = chars_to_target("body", "b" * 359, path)
        assert info["tolerance"] == 0
        assert info["action"] == "remove"

    def test_tolerance_still_applies_to_point_locks_in_the_same_file(self, tmp_path):
        data = banded_locks()
        data["tolerance"] = 2
        data["slots"]["point"] = {"type": "DYNAMIC", "principles_lock": 5,
                                  "baseline": "abcde"}
        path = write_locks(tmp_path, data)
        assert check_slot("point", "abcdefg", path)["passed"] is True    # +2
        assert check_slot("point", "abcdefgh", path)["passed"] is False  # +3


class TestRangeLockAccessors:
    """A band must never be handed back as if it were one number."""

    def test_lock_band_covers_both_kinds(self, locks):
        assert lock_band(locks["slots"]["cover_body"]) == COVER_BODY_BAND
        assert lock_band(locks["slots"]["night_page"]) == (616, 616)

    def test_is_range_locked_is_true_only_for_the_banded_slot(self, locks):
        banded = [n for n, s in locks["slots"].items() if is_range_locked(s)]
        assert banded == RANGE_LOCKED_SLOTS

    def test_enforced_lock_refuses_to_flatten_a_band(self, locks):
        with pytest.raises(RangeLockedSlotError):
            enforced_lock(locks["slots"]["cover_body"])
        assert enforced_lock(locks["slots"]["night_page"]) == 616

    def test_target_for_refuses_to_flatten_a_band(self, locks):
        with pytest.raises(RangeLockedSlotError) as exc:
            target_for("cover_body", locks)
        assert "target_range_for" in str(exc.value)

    def test_range_errors_are_valueerror_and_charlint_errors(self, locks):
        # The orchestrator catches charlint.CharLintError; `except ValueError`
        # callers exist too. Both must still see this.
        with pytest.raises(ValueError):
            target_for("cover_body", locks)
        with pytest.raises(charlint_module.CharLintError):
            target_for("cover_body", locks)

    def test_target_range_for_answers_for_every_slot(self, locks):
        assert target_range_for("cover_body", locks) == COVER_BODY_BAND
        assert target_range_for("night_page", locks) == (616, 616)
        assert target_range_for("brand_subline", locks) == (20, 20)

    def test_the_result_carries_the_band_not_just_an_edge(self, locks, baselines):
        res = check_slot("cover_body", baselines["cover_body"], locks)
        assert res["expected_range"] == [350, 358]
        assert res["expected"] == 351            # the nearest legal count
        assert check_slot(
            "night_page", baselines["night_page"], locks)["expected_range"] is None

    def test_the_band_survives_json(self, locks, identity):
        result = run_charlint(identity, locks)
        round_tripped = json.loads(json.dumps(result))
        assert round_tripped["slots"]["cover_body"]["expected_range"] == [350, 358]

    def test_an_unfilled_banded_slot_reports_the_whole_window(self, locks):
        res = run_charlint({}, locks)["slots"]["cover_body"]
        assert res["failure_mode"] == FAILURE_NOT_FILLED
        assert "350–358" in res["violations"][0]
        assert res["expected_range"] == [350, 358]


class TestPointLocksAreUnaffected:
    """
    Ranges are opt-in per slot. The other six are genuine point locks and stay
    tolerance-0 exact — a band leaking onto them would be the mirror defect:
    a gate looser than its rulebook.
    """

    def test_the_shipped_file_bands_exactly_one_slot(self, locks):
        assert [n for n, s in locks["slots"].items()
                if LOCK_RANGE_KEY in s] == RANGE_LOCKED_SLOTS

    @pytest.mark.parametrize("slot", POINT_LOCKED_SLOTS)
    def test_one_character_either_side_still_fails_a_point_lock(
        self, slot, locks, baselines
    ):
        over = check_slot(slot, baselines[slot] + "x", locks)
        under = check_slot(slot, baselines[slot][:-1], locks)
        assert over["passed"] is False and over["failure_mode"] == FAILURE_OVERFLOW
        assert under["passed"] is False and under["failure_mode"] == FAILURE_UNDERFILL

    @pytest.mark.parametrize("slot", POINT_LOCKED_SLOTS)
    def test_a_point_lock_reports_no_band(self, slot, locks, baselines):
        res = check_slot(slot, baselines[slot], locks)
        assert res["expected_range"] is None
        assert res["expected"] == len(baselines[slot])
        assert lock_band(locks["slots"][slot]) == (res["expected"], res["expected"])

    @pytest.mark.parametrize("slot", POINT_LOCKED_SLOTS)
    def test_a_point_lock_still_says_lock_not_window(self, slot, locks, baselines):
        violation = check_slot(slot, baselines[slot] + "x", locks)["violations"][0]
        assert "enforced lock" in violation
        assert "legal range" not in violation.lower()

    def test_no_slot_silently_acquires_the_cover_bands_window(self, locks, baselines):
        # The mutation "apply the band to every slot" is what this kills: a
        # ±4 window on a point lock would pass all of these.
        for slot in POINT_LOCKED_SLOTS:
            for offset in (-4, -1, 1, 4):
                candidate = sized(baselines[slot], len(baselines[slot]) + offset)
                assert check_slot(slot, candidate, locks)["passed"] is False, (
                    f"{slot} accepted {offset:+d}")


class TestIdentityStillHolds:
    """
    The anchor. Every captured baseline is still legal against the file as it
    now stands — seven count-locked slots and both permanent slots, in one run
    and one by one. If a range change had moved any other lock, this dies.
    """

    def test_all_seven_baselines_and_both_permanent_slots_pass_together(
        self, locks, baselines
    ):
        submission = dict(baselines)
        for name in permanent_slot_names(locks):
            submission[name] = locks["permanent_slots"][name]["baseline"]
        result = run_charlint(submission, locks)
        assert sorted(result["slots"]) == sorted(ALL_SLOTS + permanent_slot_names(locks))
        assert result["summary"]["all_passed"] is True
        assert result["summary"]["total_score"] == 100 * 9
        assert result["warnings"] == []

    @pytest.mark.parametrize("slot", ALL_SLOTS)
    def test_each_baseline_is_inside_its_own_lock(self, slot, locks, baselines):
        low, high = target_range_for(slot, locks)
        assert low <= len(baselines[slot]) <= high
        assert check_slot(slot, baselines[slot], locks)["delta"] == 0

    def test_the_cover_baseline_is_the_captured_351_and_sits_mid_band(
        self, locks, baselines
    ):
        # The reference text was not touched by the range change: still the
        # 351-character string captured from Canva DAHQoZJm12w, still legal.
        assert len(baselines["cover_body"]) == 351
        assert baselines["cover_body"].startswith("Seattle wears its fitness in the open")
        assert baselines["cover_body"].endswith("Train like a local — wherever you are.")
        low, high = COVER_BODY_BAND
        assert low < 351 < high
        assert check_slot("cover_body", baselines["cover_body"], locks)["passed"] is True


# ---------------------------------------------------------------------------
# The writer convergence helper
# ---------------------------------------------------------------------------

class TestCharsToTarget:
    def test_reports_removal_for_a_long_draft(self, locks, baselines):
        info = chars_to_target("counter_venue", baselines["counter_venue"] + "abc", locks)
        assert info["delta"] == 3
        assert info["chars_needed"] == -3
        assert info["action"] == "remove"
        assert info["expected"] == 602
        assert info["actual"] == 605
        assert "Remove 3" in info["message"]

    def test_reports_addition_for_a_short_draft(self, locks, baselines):
        info = chars_to_target("counter_venue", baselines["counter_venue"][:-9], locks)
        assert info["chars_needed"] == 9
        assert info["action"] == "add"
        assert "Add 9" in info["message"]

    def test_reports_none_when_on_the_lock(self, locks, baselines):
        info = chars_to_target("counter_venue", baselines["counter_venue"], locks)
        assert info["chars_needed"] == 0
        assert info["action"] == "none"
        assert info["within_tolerance"] is True
        assert "on the lock" in info["message"]

    def test_convergence_loop_terminates_on_the_reported_number(self, locks, baselines):
        draft = baselines["anchor_venue"][:-40]
        info = chars_to_target("anchor_venue", draft, locks)
        fixed = draft + "y" * info["chars_needed"]
        assert check_slot("anchor_venue", fixed, locks)["passed"] is True

    def test_works_for_permanent_slots(self, locks):
        info = chars_to_target("brand_subline", "THE CITY IS THE GYM", locks)
        assert info["expected"] == 20
        assert info["chars_needed"] == 1

    def test_unknown_slot_raises(self, locks):
        with pytest.raises(UnknownSlotError):
            chars_to_target("nope", "text", locks)

    def test_tolerance_is_surfaced(self, tmp_path):
        data = minimal_locks("abcde")
        data["tolerance"] = 2
        info = chars_to_target("body", "abcdef", write_locks(tmp_path, data))
        assert info["tolerance"] == 2
        assert info["within_tolerance"] is True
        assert info["action"] == "none"


class TestCharsToTargetOnABand:
    """
    The convergence loop has to be honest about what it is converging on.
    PRINCIPLES.txt Sec. 3 describes landing "on the lock to the character";
    for a banded slot there is no such character, there is a window, and
    pretending otherwise is what sent writers to delete legal characters.
    """

    def test_in_range_says_window_not_target(self, locks, baselines):
        info = chars_to_target("cover_body", sized(baselines["cover_body"], 355), locks)
        assert info["action"] == "none"
        assert info["chars_needed"] == 0
        assert info["within_tolerance"] is True
        assert info["expected_range"] == [350, 358]
        assert "window" in info["message"]
        assert "350–358" in info["message"]
        assert "not a single target" in info["message"]
        assert "on the lock" not in info["message"]

    def test_both_edges_read_as_done(self, locks, baselines):
        for count in (350, 358):
            info = chars_to_target(
                "cover_body", sized(baselines["cover_body"], count), locks)
            assert info["action"] == "none", count
            assert info["chars_needed"] == 0

    def test_over_the_ceiling_points_at_the_ceiling(self, locks, baselines):
        info = chars_to_target("cover_body", sized(baselines["cover_body"], 362), locks)
        assert info["action"] == "remove"
        assert info["chars_needed"] == -4          # to 358, not to 353 or 354
        assert info["expected"] == 358
        assert info["delta"] == 4
        assert "Remove 4 character(s) to reach 358" in info["message"]
        assert "nearest legal count" in info["message"]

    def test_under_the_floor_points_at_the_floor(self, locks, baselines):
        info = chars_to_target("cover_body", sized(baselines["cover_body"], 344), locks)
        assert info["action"] == "add"
        assert info["chars_needed"] == 6           # to 350, not to 353 or 354
        assert info["expected"] == 350
        assert info["delta"] == -6
        assert "Add 6 character(s) to reach 350" in info["message"]

    def test_a_point_lock_still_reads_as_a_point(self, locks, baselines):
        info = chars_to_target("city_intro", baselines["city_intro"], locks)
        assert info["expected_range"] is None
        assert "on the lock" in info["message"]
        assert "window" not in info["message"]

    def test_the_loop_terminates_from_either_side(self, locks, baselines):
        for count in (340, 370):
            draft = sized(baselines["cover_body"], count)
            info = chars_to_target("cover_body", draft, locks)
            needed = info["chars_needed"]
            fixed = draft + "y" * needed if needed > 0 else draft[:len(draft) + needed]
            assert check_slot("cover_body", fixed, locks)["passed"] is True
            # ... and the second pass asks for nothing, i.e. it converged.
            assert chars_to_target("cover_body", fixed, locks)["chars_needed"] == 0


# ---------------------------------------------------------------------------
# Output shape — the orchestrator contract
# ---------------------------------------------------------------------------

class TestOutputShape:
    def test_top_level_keys(self, locks, identity):
        result = run_charlint(identity, locks)
        assert set(result) == {"slots", "warnings", "summary"}
        assert set(result["summary"]) == {"total_score", "all_passed"}
        assert isinstance(result["warnings"], list)

    def test_per_slot_keys(self, locks, identity):
        identity["cover_body"] += "x"
        result = run_charlint(identity, locks)
        for res in result["slots"].values():
            assert {"violations", "score", "passed", "expected", "actual",
                    "delta", "failure_mode", "nfc_normalized"} <= set(res)
            assert isinstance(res["nfc_normalized"], bool)
            assert isinstance(res["violations"], list)
            assert isinstance(res["score"], int)
            assert isinstance(res["passed"], bool)
            assert isinstance(res["expected"], int)
            assert isinstance(res["actual"], int)
            assert isinstance(res["delta"], int)

    def test_result_is_json_serializable(self, locks, identity):
        del identity["night_page"]
        identity["brand_subline"] = "THE CITY IS THE GYM!"
        json.dumps(run_charlint(identity, locks))

    def test_total_score_is_the_sum_of_slot_scores(self, locks, identity):
        identity["city_intro"] += "x"
        result = run_charlint(identity, locks)
        assert result["summary"]["total_score"] == sum(
            r["score"] for r in result["slots"].values())
        assert result["summary"]["total_score"] == 690

    def test_format_report_renders_status_and_violations(self, locks, identity):
        assert "PASS" in format_report(run_charlint(identity, locks))
        identity["counter_cafe"] += "x"
        report = format_report(run_charlint(identity, locks))
        assert "FAIL" in report
        assert "OVERFLOW" in report

    def test_format_report_prints_a_band_as_a_band(self, locks, identity):
        # Printing one edge in the Lock column is how a range gets read back as
        # a point — the whole defect, re-created in the report.
        report = format_report(run_charlint(identity, locks))
        assert "350–358" in report
        assert "628" in report          # ... and a point lock still prints one number

    def test_format_report_still_renders_drift_when_there_is_drift(self, tmp_path):
        path = write_locks(tmp_path, drifting_locks())
        assert "DRIFT" in format_report(run_charlint({"body": "Hello world"}, path))
