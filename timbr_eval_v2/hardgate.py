"""
hardgate.py — Tier-1 deterministic gates for the TIMBR Eval Harness v2.

No LLM required. Fast, free, zero-ambiguity. Every check here is a regex or
arithmetic rule, on purpose — see RUBRIC.md "Design principles" for why v1's
attempt to score *voice* with regex (voicelint) was the wrong tool for that
job. This module only owns the checks that genuinely ARE mechanical.

Usage:
    from hardgate import run_hardgate
    result = run_hardgate(text, content_type="blog_training")
"""

import re

# ---------------------------------------------------------------------------
# Content-type word count ranges (RUBRIC.md "Word count ranges by content type")
# ---------------------------------------------------------------------------

WORD_COUNT_RANGES = {
    "blog_the_guide": (800, 1200),
    "blog_training": (800, 1200),
    "blog_culture": (800, 1200),
    "magazine_nutrition_spot": (150, 400),
    "magazine_fitness_spot": (150, 400),
    "magazine_location_spot": (150, 400),
    "product_venue_card": (40, 200),
    "unspecified": (0, float("inf")),
}

# ---------------------------------------------------------------------------
# Banned vocabulary (merged: Maya's EIC prohibited list + v1 AI_BLOCKLIST)
# ---------------------------------------------------------------------------

BANNED_VOCAB = sorted(set([
    # v1 AI_BLOCKLIST
    "delve", "foster", "tapestry", "vibrant", "robust", "holistic",
    "leverage", "seamless", "pivotal", "transformative", "unlock",
    "elevate", "revolutionize", "journey", "empower", "thrive",
    "curated", "game-changer", "deep dive", "synergy", "ecosystem",
    "impactful", "actionable", "harness", "spearhead",
    # Maya's EIC prohibited list (additions only; overlaps deduped by set())
    "dive deep", "nuanced", "multifaceted", "seasoned", "realm",
    "landscape", "bustling", "beacon", "testament", "curate",
    "cutting-edge", "paradigm", "notion", "crucial", "vital",
    "optimize",
]))

BANNED_PHRASES = [
    "in conclusion", "feel free to", "certainly!", "no excuses",
    "clean eating", "crush it", "wellness journey",
    "unlock your potential", "take it to the next level",
]

SECOND_PERSON_PATTERNS = [
    r"you should", r"your body", r"try this", r"you need to",
    r"you can", r"you will feel", r"your workout", r"you want to",
]

PASSIVE_VOICE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|being|been)\s+\w+ed\b", re.IGNORECASE
)


def _word_count(text):
    return len(text.split())


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _strip_sidebars(text):
    return re.sub(r"\[SIDEBAR\].*?\[/SIDEBAR\]", "", text, flags=re.IGNORECASE | re.DOTALL)


def check_em_dash(text):
    count = text.count("—")
    return {
        "gate": "em_dash",
        "blocking": True,
        "passed": count == 0,
        "detail": f"{count} em-dash character(s) found." if count else "Clean.",
    }


def check_banned_vocab(text):
    hits = []
    for term in BANNED_VOCAB:
        pat = re.compile(r"(?<!\w)" + re.escape(term).replace(r"\ ", r"\s+") + r"(?!\w)", re.IGNORECASE)
        found = pat.findall(text)
        if found:
            hits.append((term, len(found)))
    return {
        "gate": "banned_vocab",
        "blocking": True,
        "passed": len(hits) == 0,
        "detail": "Clean." if not hits else "; ".join(f"'{t}' x{n}" for t, n in hits),
    }


def check_banned_phrases(text):
    hits = []
    for phrase in BANNED_PHRASES:
        pat = re.compile(re.escape(phrase), re.IGNORECASE)
        found = pat.findall(text)
        if found:
            hits.append((phrase, len(found)))
    return {
        "gate": "banned_phrase",
        "blocking": True,
        "passed": len(hits) == 0,
        "detail": "Clean." if not hits else "; ".join(f"'{p}' x{n}" for p, n in hits),
    }


def check_word_count(text, content_type):
    lo, hi = WORD_COUNT_RANGES.get(content_type, WORD_COUNT_RANGES["unspecified"])
    wc = _word_count(text)
    passed = lo <= wc <= hi
    return {
        "gate": "word_count",
        "blocking": True,
        "passed": passed,
        "detail": f"{wc} words (range [{lo}–{hi}] for '{content_type}').",
    }


def check_passive_voice(text):
    sents = _sentences(text)
    if not sents:
        return {"gate": "passive_voice_rate", "blocking": False, "passed": True, "detail": "No sentences."}
    passive_count = sum(1 for s in sents if PASSIVE_VOICE_RE.search(s))
    rate = passive_count / len(sents)
    passed = rate <= 0.08
    return {
        "gate": "passive_voice_rate",
        "blocking": False,
        "passed": passed,
        "detail": f"{passive_count}/{len(sents)} sentences passive ({rate:.0%}).",
    }


def check_second_person_coaching(text):
    clean = _strip_sidebars(text)
    hits = []
    for p in SECOND_PERSON_PATTERNS:
        found = re.findall(r"(?<!\w)" + re.escape(p) + r"(?!\w)", clean, re.IGNORECASE)
        if found:
            hits.append((p, len(found)))
    return {
        "gate": "second_person_coaching",
        "blocking": False,
        "passed": len(hits) == 0,
        "detail": "Clean." if not hits else "; ".join(f"'{p}' x{n}" for p, n in hits),
    }


def check_paragraph_structure(text):
    """
    For content pasted as Markdown with '## Heading' sub-headers: verify no
    blank-line paragraph breaks occur WITHIN a section (between two headings).
    Only meaningful for blog-post-shaped input; skipped (passed=True, informational)
    for content types where this doesn't apply.
    """
    if "##" not in text:
        return {
            "gate": "paragraph_structure",
            "blocking": False,
            "passed": True,
            "detail": "No markdown headings found — gate not applicable to this content type.",
        }
    sections = re.split(r"\n##+\s+.*\n", text)
    # sections[0] is pre-first-heading content (intro); each subsequent block is one section's body
    offenders = []
    for i, block in enumerate(sections[1:], start=1):
        paras = [p for p in block.strip().split("\n\n") if p.strip()]
        if len(paras) > 1:
            offenders.append(i)
    return {
        "gate": "paragraph_structure",
        "blocking": False,
        "passed": len(offenders) == 0,
        "detail": "Clean." if not offenders else f"{len(offenders)} section(s) have multiple paragraph breaks (should be one continuous paragraph per H2).",
    }


def run_hardgate(text, content_type="unspecified"):
    checks = [
        check_em_dash(text),
        check_banned_vocab(text),
        check_banned_phrases(text),
        check_word_count(text, content_type),
        check_passive_voice(text),
        check_second_person_coaching(text),
        check_paragraph_structure(text),
    ]
    blocking_failures = [c for c in checks if c["blocking"] and not c["passed"]]
    warning_failures = [c for c in checks if not c["blocking"] and not c["passed"]]
    return {
        "content_type": content_type,
        "word_count": _word_count(text),
        "checks": checks,
        "blocking_failures": blocking_failures,
        "warning_failures": warning_failures,
        "tier1_status": "FAIL" if blocking_failures else "PASS",
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 hardgate.py <text_file> [content_type]")
        sys.exit(1)
    text = open(sys.argv[1]).read()
    content_type = sys.argv[2] if len(sys.argv) > 2 else "unspecified"
    result = run_hardgate(text, content_type)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["tier1_status"] == "PASS" else 1)
