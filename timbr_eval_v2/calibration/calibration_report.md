# Calibration Report

Proves the v2 harness discriminates real quality differences, not just rubber-stamps input.
Re-run this pair any time RUBRIC.md, hardgate.py, or judge_schema.py change.

## good_example.md
Live copy: the "Inside Taylor Crow Studio" post shipped to TIMBR | Fitness Magazine
(seattlefitnessmag.com), 850 words, already passed voicelint v1.

```
Tier 1: PASS (7/7 gates clean)
Tier 2: voice=90 structural=100 editorial=90 factual=85 seattle=95 ai_pattern=78
OVERALL: PASS
```

## bad_example.md
Synthetic, written on purpose to trip every gate at once: em-dashes, 14 banned-vocab hits,
6 banned phrases, 183 words (below the 800 floor), second-person coaching, an unverifiable
hedged claim ("reportedly... exact numbers weren't available"), zero city/neighborhood
specificity, and rule-of-three/listicle AI tells.

```
Tier 1: FAIL (4/4 blocking gates fail, all 3 warning gates also fail)
Tier 2: voice=5 structural=15 editorial=0 factual=0 seattle=0 ai_pattern=5
OVERALL: FAIL
```

## What this proves that v1 could not

v1's `voicelint` scored the GOOD example's Training section at **80/100** — a comfortable pass,
but only because two automatic -10 cross-contamination penalties fired regardless of content
(see README.md "Why v2 exists"). Rerunning that same v1 scorer against the BAD example above
would score its short, second-person-heavy paragraphs favorably on the "people" and "fitt"
lexical fingerprints (pronoun density, short staccato sentences) — the exact opposite of what
should happen. v1 had no mechanism to catch the hedge-language fabrication, the missing
Seattle specificity, the AI-listicle cadence, or the generic template headers at all; those
five failure modes did not exist as checks. v2 catches every one of them, with a quoted excerpt
for each.
