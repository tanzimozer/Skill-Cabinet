
# voicelint.py — VoiceLint module for TIMBR eval harness
# Lexical fingerprint scoring per section voice register. MVP: no embeddings.

import re
import statistics
from voice_config import (
    SECTION_VOICE_MAP,
    ATHLETIC_POSITIVE, ATHLETIC_NEGATIVE,
    PEOPLE_POSITIVE, PEOPLE_NEGATIVE,
    FITT_POSITIVE_PARA_MAX, FITT_POSITIVE_KICKER_MAX,
    FITT_STRONG_OPINION, FITT_DECLARATIVE, FITT_DATA_LEAD, FITT_NEGATIVE,
    PASS_THRESHOLD, CROSS_CONTAMINATION_THRESHOLD, CROSS_CONTAMINATION_PENALTY,
)


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


def score_athletic(text):
    score = 100
    flags = []

    pos_count, pos_hits = _count_matches(ATHLETIC_POSITIVE, text)
    score += pos_count * 2

    neg_count, neg_hits = _count_matches(ATHLETIC_NEGATIVE, text)
    score -= neg_count * 3
    for h in neg_hits:
        flags.append(f"Athletic negative marker: {h['pattern']} ({h['count']}x)")

    # Sentence length variance (earned rhythm)
    sents = _sentences(text)
    if len(sents) >= 4:
        lengths = [len(s.split()) for s in sents]
        short = sum(1 for l in lengths if l < 8)
        long_ = sum(1 for l in lengths if l > 20)
        if short >= 2 and long_ >= 2:
            score += 5

    return min(100, max(0, score)), flags


def score_people(text):
    score = 100
    flags = []
    paras = _paragraphs(text)

    pos_count, pos_hits = _count_matches(PEOPLE_POSITIVE, text)
    score += pos_count * 2

    neg_count, neg_hits = _count_matches(PEOPLE_NEGATIVE, text, re.IGNORECASE | re.MULTILINE)
    score -= neg_count * 3
    for h in neg_hits:
        flags.append(f"People negative marker: {h['pattern']} ({h['count']}x)")

    # Named person in first 50 words
    first_50 = ' '.join(text.split()[:50])
    if re.search(r'[A-Z][a-z]+\s[A-Z][a-z]+', first_50):
        score += 5
    else:
        score -= 8
        flags.append("No named person in opening 50 words")

    return min(100, max(0, score)), flags


def score_fitt(text):
    score = 100
    flags = []
    paras = _paragraphs(text)

    # Staccato: majority of paragraphs <= 40 words
    if paras:
        short_paras = sum(1 for p in paras if _word_count(p) <= FITT_POSITIVE_PARA_MAX)
        ratio = short_paras / len(paras)
        if ratio >= 0.6:
            score += 8
        else:
            score -= 10
            flags.append(f"Only {ratio:.0%} of paragraphs are staccato (<=40 words)")

        # Long paragraph penalty
        for p in paras:
            if _word_count(p) > 80:
                score -= 5
                flags.append(f"Paragraph exceeds 80 words ({_word_count(p)} words)")

    # Opinionated kicker
    sents = _sentences(text)
    if sents:
        last = sents[-1]
        if _word_count(last) <= FITT_POSITIVE_KICKER_MAX:
            kicker_match, _ = _count_matches(FITT_STRONG_OPINION, last)
            if kicker_match:
                score += 6

    # Declarative openings
    declarative_count = 0
    for p in paras:
        first_sent = _sentences(p)[0] if _sentences(p) else ''
        if re.match(FITT_DECLARATIVE, first_sent):
            declarative_count += 1
    if paras and declarative_count / len(paras) >= 0.5:
        score += 5

    # Data-led sentences
    data_count = sum(1 for s in sents if re.match(FITT_DATA_LEAD, s.strip()))
    score += data_count * 2

    # Negatives
    neg_count, neg_hits = _count_matches(FITT_NEGATIVE, text, re.IGNORECASE | re.MULTILINE)
    score -= neg_count * 3
    for h in neg_hits:
        flags.append(f"Fitt negative marker: {h['pattern']} ({h['count']}x)")

    return min(100, max(0, score)), flags


SCORERS = {
    "athletic": score_athletic,
    "people": score_people,
    "fitt": score_fitt,
}


def run(sections: dict) -> dict:
    """
    sections: {section_name: text}
    Returns: {section_name: {voice_required, voice_score, contamination_flags, passed}}
    """
    results = {}

    # Score each section against all voices for cross-contamination detection
    all_scores = {}
    for section, text in sections.items():
        voice_req = SECTION_VOICE_MAP.get(section, "athletic")
        scores = {}
        for voice_name, scorer in SCORERS.items():
            s, _ = scorer(text)
            scores[voice_name] = s
        all_scores[section] = scores

    for section, text in sections.items():
        voice_req = SECTION_VOICE_MAP.get(section, "athletic")
        scorer = SCORERS[voice_req]
        primary_score, primary_flags = scorer(text)

        contamination_flags = list(primary_flags)

        # Cross-contamination check
        for other_voice, other_scorer in SCORERS.items():
            if other_voice == voice_req:
                continue
            other_score, _ = other_scorer(text)
            if other_score > CROSS_CONTAMINATION_THRESHOLD * 10:
                contamination_flags.append(
                    f"Cross-contamination: section scores {other_score} on {other_voice} voice (required: {voice_req})"
                )
                primary_score -= CROSS_CONTAMINATION_PENALTY

        primary_score = max(0, min(100, primary_score))
        passed = primary_score >= PASS_THRESHOLD

        results[section] = {
            "voice_required": voice_req,
            "voice_score": primary_score,
            "contamination_flags": contamination_flags,
            "passed": passed,
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
