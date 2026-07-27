"""
prohiblint.py — ProhibLint module for TIMBR magazine eval harness.

Scans all 7 magazine sections for prohibited content and structural compliance.
Sections: Training, Nutrition, Supplements, Recovery, Culture, Social, Nightlife

Usage:
    from prohiblint import run_prohiblint
    results = run_prohiblint({"Training": "...", "Nutrition": "...", ...})
"""

import re
from collections import defaultdict

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
    Flag every U+2014 (—) character.
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


# ---------------------------------------------------------------------------
# Check B — AI vocabulary blocklist
# ---------------------------------------------------------------------------

def _build_blocklist_patterns():
    patterns = {}
    for term in AI_BLOCKLIST:
        # For multi-word terms use simple case-insensitive search with word boundaries
        # on the first and last word
        escaped = re.escape(term)
        # Replace escaped space with \s+ to allow flexible spacing
        escaped = escaped.replace(r'\ ', r'\s+')
        pat = re.compile(r'(?<!\w)' + escaped + r'(?!\w)', re.IGNORECASE)
        patterns[term] = pat
    return patterns

_BLOCKLIST_PATTERNS = _build_blocklist_patterns()


def check_ai_blocklist(text):
    """
    Flag AI vocabulary terms.
    Penalty: -5 per hit. Hard fail: 3+ hits in section.
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
    "Seattle", # keep as proper noun example — will NOT be in stoplist
}

_SENTENCE_START_RE = re.compile(r'(?:^|[.!?]\s+)([A-Z][a-z]+)')

def _has_proper_noun(text):
    """
    Heuristic: look for capitalised words that are not sentence starters
    and not on the title-case stoplist. If found, assume proper noun present.
    """
    words = text.split()
    # The very first word is always sentence-start; skip it
    for i, word in enumerate(words[1:], start=1):
        clean = re.sub(r'[^A-Za-z]', '', word)
        if clean and clean[0].isupper() and clean not in _TITLE_CASE_STOPLIST:
            return True
    return False


def _has_narrative_present_tense(text):
    """
    Heuristic: look for third-person singular present-tense verbs typical
    of narrative prose (is, sits, stands, walks, runs, looks, feels, etc.)
    NOT immediately preceded by 'he/she/they/it' — just raw occurrence.
    """
    narrative_verbs = re.compile(
        r'\b(is|sits|stands|walks|runs|looks|feels|moves|checks|opens|enters|heads|grabs|reaches)\b',
        re.IGNORECASE
    )
    return bool(narrative_verbs.search(text))


def _matches_cold_open_pattern(text):
    """
    Check for specific fictional cold-open patterns.
    """
    patterns = [
        re.compile(r'^it\s+is\s+\d', re.IGNORECASE),         # "It is 5:30am"
        re.compile(r'^[A-Z][a-z]+\s+is\s+already\b', re.IGNORECASE),  # "Marcus is already"
        re.compile(r'^[A-Z][a-z]+\s+[a-z]+s\s+', re.IGNORECASE),      # "[Name] verbs ..."
    ]
    for pat in patterns:
        if pat.match(text.strip()):
            return True
    return False


def check_cold_open(text):
    """
    Check first paragraph (first 200 chars) for fictional cold-open.
    Penalty: -15.
    Returns (violations, penalty, hard_fail=False).
    """
    violations = []
    snippet = _first_paragraph(text)
    word_count = _word_count(snippet)

    flagged = False
    if word_count > 30:
        has_proper = _has_proper_noun(snippet)
        has_narrative = _has_narrative_present_tense(snippet)
        has_pattern = _matches_cold_open_pattern(snippet)

        if (not has_proper and has_narrative) or has_pattern:
            flagged = True
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

_SP_PATTERNS = [
    re.compile(r'(?<!\w)' + re.escape(p) + r'(?!\w)', re.IGNORECASE)
    for p in SECOND_PERSON_PATTERNS
]

def check_second_person(text):
    """
    Flag second-person coaching language outside [SIDEBAR] blocks.
    Penalty: -3 per hit.
    Returns (violations, penalty, hard_fail=False).
    """
    clean_text = _strip_sidebars(text)
    violations = []
    total_hits = 0
    for pat_str, pat in zip(SECOND_PERSON_PATTERNS, _SP_PATTERNS):
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

    # 2. Nutrition spots: ≥4 named places with addresses or neighbourhoods
    # Heuristic: look for capitalised word(s) followed by address-like or
    # neighbourhood keywords within 60 chars
    nutrition_text = sections_dict.get("Nutrition", "")
    # Match patterns like "Joe's Diner, Capitol Hill" or "Cafe Verde (Fremont)"
    # or "123 Main St" near a proper noun
    address_pat = re.compile(
        r'[A-Z][A-Za-z\'&\s]{2,30}'       # name (2-30 chars, capitals)
        r'[\s,\(]+'                          # separator
        r'(?:'
            r'\d+\s+[A-Z][a-z]+|'           # street address
            r'[A-Z][a-z]+\s+(?:Hill|Ave|Blvd|St|Rd|Way|District|Neighborhood|'
             r'Capitol|Fremont|Ballard|SoDo|Pioneer|Belltown|Queen Anne|'
             r'Eastlake|Westlake|Madison|Central|South Lake|Green Lake|'
             r'University|Ravenna|Wallingford|Columbia|Beacon|Georgetown|'
             r'Rainier|Magnolia|Crown Hill|Phinney|Sunset|View Ridge|'
             r'Sand Point|Laurelhurst|Montlake|Portage Bay|Leschi|Madrona|'
             r'Seward|Jefferson|Brighton|Dunlap|Holly|Skyway|White Center)'
        r')',
        re.IGNORECASE
    )
    nutrition_matches = address_pat.findall(nutrition_text)
    # Also accept a simpler fallback: ≥4 occurrences of quoted/titled place names
    # near neighbourhood or address keywords
    simple_place_pat = re.compile(
        r'(?:[A-Z][A-Za-z\'&]+(?:\s+[A-Z][A-Za-z\'&]+){0,3})'
        r'(?:\s*,\s*|\s+(?:in|at|on|near)\s+)'
        r'(?:[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
        re.MULTILINE
    )
    simple_matches = simple_place_pat.findall(nutrition_text)
    nutrition_place_count = max(len(nutrition_matches), len(simple_matches) // 2)

    has_nutrition_spots = nutrition_place_count >= 4
    element_results["nutrition_spots_4_places"] = has_nutrition_spots
    if not has_nutrition_spots:
        violations.append(
            f"Mandatory element missing: Nutrition section needs ≥4 named places "
            f"with addresses/neighbourhoods (found ~{nutrition_place_count}). Penalty: -25."
        )
        penalty -= 25

    # 3. Local fitness spots: ≥2 named gyms/studios/run clubs with location
    fitness_keywords = re.compile(
        r'\b(gym|studio|run club|running club|crossfit|box|fitness center|'
        r'yoga|pilates|barre|cycle|cycling|climbing|dojo|YMCA|rec center)\b',
        re.IGNORECASE
    )
    # Look for fitness keyword near a proper noun (capitalised word within 80 chars)
    training_text = sections_dict.get("Training", "") + "\n" + sections_dict.get("Culture", "")
    fitness_spots = []
    for m in fitness_keywords.finditer(full_text):
        # Check 80 chars before and after for a capitalised proper-noun-like token
        start = max(0, m.start() - 80)
        end = min(len(full_text), m.end() + 80)
        context = full_text[start:end]
        if re.search(r'[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?', context):
            fitness_spots.append(m.group())

    has_fitness_spots = len(fitness_spots) >= 2
    element_results["local_fitness_spots_2"] = has_fitness_spots
    if not has_fitness_spots:
        violations.append(
            f"Mandatory element missing: ≥2 named gyms/studios/run clubs with location "
            f"(found ~{len(fitness_spots)}). Penalty: -25."
        )
        penalty -= 25

    # 4. Location features: ≥3 place-type named entities (cafe, bar, park, restaurant + name)
    place_type_pat = re.compile(
        r'(?:'
            r'[A-Z][A-Za-z\'&\s]{1,25}\s+(?:cafe|bar|park|restaurant|pub|lounge|'
            r'rooftop|terrace|garden|market|diner|bistro|eatery|grill|kitchen|'
            r'tavern|taproom|brewery|winery|coffeehouse|coffee shop)'
            r'|'
            r'(?:cafe|bar|park|restaurant|pub|lounge|rooftop|terrace|garden|'
            r'market|diner|bistro|eatery|grill|kitchen|tavern|taproom|brewery|'
            r'winery|coffeehouse|coffee shop)\s+[A-Z][A-Za-z\'&\s]{1,25}'
        r')',
        re.IGNORECASE
    )
    place_type_matches = place_type_pat.findall(full_text)
    has_location_features = len(place_type_matches) >= 3
    element_results["location_features_3_places"] = has_location_features
    if not has_location_features:
        violations.append(
            f"Mandatory element missing: ≥3 place-type named entities "
            f"(cafe, bar, park, restaurant + name) found {len(place_type_matches)}. Penalty: -25."
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
# Main entry point
# ---------------------------------------------------------------------------

def run_prohiblint(sections_dict):
    """
    Run all ProhibLint checks on a dict of {section_name: text}.

    Returns:
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
    results = {}

    for section in SECTIONS:
        text = sections_dict.get(section, "")
        section_violations = []
        section_penalty = 0
        hard_fail = False

        # A) Em-dash
        v, p, hf = check_em_dash(text)
        section_violations.extend(v)
        section_penalty += p
        hard_fail = hard_fail or hf

        # B) AI blocklist
        v, p, hf = check_ai_blocklist(text)
        section_violations.extend(v)
        section_penalty += p
        hard_fail = hard_fail or hf

        # C) Cold-open
        v, p, _ = check_cold_open(text)
        section_violations.extend(v)
        section_penalty += p

        # D) Second-person
        v, p, _ = check_second_person(text)
        section_violations.extend(v)
        section_penalty += p

        # E) Word count
        v, p, hf = check_word_count(section, text)
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

    # F) Issue-level mandatory elements
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
