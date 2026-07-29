# TIMBR Editorial Rubric v2

Replaces v1's `voicelint` cross-contamination scorer. Read [MIGRATION.md](README.md#why-v2-exists) for why.

## Design principles (why this is built this way)

1. **Deterministic checks stay deterministic. Judgment calls get a judge, not a keyword count.**
   v1 tried to score "does this sound like TIMBR" with regex hit-counting (`ATHLETIC_POSITIVE`,
   `PEOPLE_POSITIVE`, etc.). That produces false signal: `score_people()` starts at a baseline of
   100 with no achievable floor in real-length prose, so any section mentioning a named person
   (i.e. almost every TIMBR piece) auto-triggers a "cross-contamination" penalty against whatever
   voice was actually required. The fix isn't a better regex — voice, editorial value, and factual
   integrity are judgment calls. They get a rubric and a reasoning judge (an LLM reading the rubric
   and the text, the way Maya does in `skills/timbr/timbr_magazine_eic`). Em-dashes, banned words,
   and word count are NOT judgment calls — those stay as fast, free, zero-ambiguity regex gates.

2. **Every score below 100 requires a quoted excerpt as evidence.** A judge that says "Voice: 62"
   with no receipt is unauditable and the number can't be trusted or improved against. Every
   dimension below a perfect score must cite the specific sentence(s) that cost points.

3. **Hard gates block. Soft dimensions inform.** A single em-dash or a fabricated venue address
   is not a "-10 point" nudge — it's an automatic FAIL, full stop, matching how Maya's Fact Lock
   and AI-audit double-gate already work for the print magazine. Tier 2 (judge) dimensions produce
   a graded verdict (PASS / NEEDS REVISION / FAIL) per dimension, not a single blended number that
   hides which specific thing is wrong.

4. **Calibrated, not vibes-based.** `calibration/` holds one known-good and one deliberately-bad
   passage with their actual scored output, committed alongside this rubric. Anyone changing the
   rubric re-runs both and confirms the good one still passes and the bad one still fails — the
   same discipline as a unit-test suite, applied to a text-quality judge.

---

## TIER 1 — Hard Gates (deterministic, `hardgate.py`, no LLM required)

Any Tier-1 failure is an automatic overall **FAIL**, regardless of Tier-2 scores. These run in
milliseconds and cost nothing — always run them first.

| Gate | Rule | Source |
|---|---|---|
| `em_dash` | Zero U+2014 characters in body copy. | [[est_no_em_dashes_body]], [[charcount_never_break]] |
| `banned_vocab` | Zero hits from the merged AI/corporate/wellness-coach blocklist (see below). | Maya's prohibited word list + v1 `AI_BLOCKLIST` |
| `banned_phrase` | Zero hits from the banned-phrase list ("in conclusion", "feel free to", "certainly", "no excuses", "clean eating", "crush it", "wellness journey", ...). | Maya's prohibited word list |
| `word_count` | Within the configured range for the content type (see table below). | v1 `WORD_COUNT_RANGES`, extended |
| `passive_voice_rate` | ≤ 8% of sentences passive. Warning-tier, not blocking (TIMBR voice is active but occasional passive constructions are fine). | v1 |
| `second_person_coaching` | No "you should / you need to / try this" outside an explicit `[SIDEBAR]` block. Warning-tier. | v1 |
| `paragraph_structure` | For Wix blog posts: one continuous paragraph per H2, no mid-section breaks. | [[timbr_magazine_blog_spacing]] |

### Word count ranges by content type

| Content type | Range | Notes |
|---|---|---|
| Blog: The Guide / Training / Culture | 800–1200 | Matches the 2026-07-27 gate correction — TIMBR's original posts ran ~480, half their own floor. |
| Magazine: Workout section | n/a (structural gate, not word count) | See `mandatory_elements` below. |
| Magazine: Nutrition / Fitness / Location spots | 150–400 per spot | 4 spots minimum per issue. |
| Product / venue card copy | 40–200 | Char-locked contexts use the char-lock engine instead — this gate does not apply. |

### Merged banned-vocabulary blocklist

`delve, dive deep, tapestry, nuanced, multifaceted, pivotal, seasoned, foster, realm, landscape, bustling, vibrant, beacon, testament, elevate, curate, curated, leverage, unlock, journey, cutting-edge, game-changer, game-changer, paradigm, holistic, robust, seamless, notion, crucial, vital, optimize, transformative, revolutionize, empower, thrive, synergy, ecosystem, impactful, actionable, harness, spearhead, foster`

### Banned phrases

`in conclusion, feel free to, certainly!, no excuses, clean eating, crush it, wellness journey, unlock your potential, take it to the next level`

---

## TIER 2 — Judge Rubric (LLM-graded, `judge_schema.py` defines the output contract)

A judge (any Claude instance briefed with this rubric) reads the full text once, then scores each
dimension independently. **Do not blend dimensions into one number.** Report all six.

Scoring bands, applied per dimension:
- **70–100 PASS** — meets the bar. Minor nitpicks allowed without evidence.
- **40–69 NEEDS REVISION** — identifiable problems, listed with evidence, but not disqualifying.
- **0–39 FAIL** — disqualifying. Requires evidence.

### 1. Voice & Brand Compliance
Does this read like TIMBR — editorial-athletic spine, cultural-cool sensibility, confident without
picking fights — per [[timbr_voice]]? Specifically check:
- Short declarative sentences, not editorial-essay run-ons.
- No wellness-coach register ("you've got this", "listen to your body").
- No hype words even if not on the banned list (check for near-misses: "incredible", "next-level").
- **The Forbes test** (from Maya's AI-audit Gate 2): read every sentence. If it could run unchanged
  in a generic Forbes/Men's Health wellness listicle, that sentence fails. Quote any that do.

### 2. Structural & Format Compliance
Does the piece match the format contract for its surface?
- Blog: H2 sub-headers, one continuous paragraph per section, matches [[timbr_magazine_blog_spacing]].
- Magazine spot: location/what-it-is/training-or-menu/vibe/price/verdict present, per Maya's
  per-spot template.
- Required value elements present for the surface (workout OR recipe OR venue OR interview, per
  the issue-level check in v1 `prohiblint`, kept as a judge check since "is this substantively a
  workout" is a judgment call, not a regex match).

### 3. Editorial Value — the "So What" Test
Does the reader finish with something specific and usable? This is the dimension that most
directly answers "is this actually informative and valuable" — the standard the piece was
commissioned against. Fail this if the piece could be summarized as "[Business] offers [generic
services] in [city]" with the specifics swapped out for any competitor. Quote the single most
valuable concrete detail in the piece, and quote the vaguest/weakest sentence.

### 4. Factual & Venue Integrity (Fact Lock)
Operationalizes [[timbr_venue_preflight]] and Maya's Fact Lock as a scored gate:
- Every named business/address: was it verified against a live source in this session (not
  assumed)? List each claim and its verification status.
- Every named person: title/role stated accurately per source?
- Any hedge language ("reportedly", "it's said that") that signals an unverified claim slipped
  through — that's an automatic fail on this dimension, since [[timbr_venue_preflight]]'s
  certainty rule says doubt is never resolved in the venue's favor.
- **This dimension cannot be scored from the text alone** — the judge must have the research
  trail (what was looked up, what source confirmed it) to grade it. If no research trail is
  available, mark this dimension `UNSCORABLE` rather than guessing a number.

### 5. Seattle / Local Specificity
Per Maya's checklist: could this piece run unchanged in Portland or Denver with only the place
names swapped? If yes, it fails this dimension regardless of how well-written it is. Look for
neighborhood-level detail, not just "Seattle" as a label.

### 6. AI-Pattern Detection (Gate 2 companion)
Structural tells that survive the banned-word gate:
- Uniform paragraph/sentence cadence (every paragraph same length, every sentence same rhythm).
- Rule-of-three overuse ("X, Y, and Z" repeated as a crutch).
- Generic transitional scaffolding ("That said,", "At the end of the day,").
- Listicle cadence in prose that should read as a magazine feature, not a bulleted explainer.

---

## Overall verdict logic

```
if any Tier-1 gate = FAIL (hard gates only; warning-tier gates don't count here):
    overall = FAIL
elif Factual & Venue Integrity = FAIL:
    overall = FAIL   # matches Maya: factual failures are never negotiable
elif any Tier-2 dimension = FAIL:
    overall = FAIL
elif any Tier-2 dimension = NEEDS REVISION:
    overall = NEEDS REVISION
else:
    overall = PASS
```

Related: [[wix_article_rebuild_pipeline]], [[timbr_magazine_blog_spacing]], [[timbr_venue_preflight]], [[est_no_em_dashes_body]]
