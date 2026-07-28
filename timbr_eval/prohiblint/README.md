# ProhibLint — TIMBR Content Linter

ProhibLint is a static-analysis module for the TIMBR eval harness. It scans per-section prose for
prohibited language and structural violations, and separately checks a full issue for mandatory
value elements. It supports **two rulesets**, one per TIMBR product line.

## Sections

`prohiblint.SECTIONS` is a fixed list of seven names: Training, Nutrition, Supplements, Recovery,
Culture, Social, Nightlife. `run_prohiblint()` always scores exactly these seven section keys,
under both rulesets — see "Rulesets" for how the Workout Series line reuses them.

## Rulesets

```python
from prohiblint import run_prohiblint

run_prohiblint(sections)                          # ruleset="magazine" (default)
run_prohiblint(sections, ruleset="workout_series")
```

`prohiblint.VALID_RULESETS = ("magazine", "workout_series")`. An unrecognized ruleset raises
`ValueError` — there is no silent fallback to `"magazine"`.

| Check | magazine (default) | workout_series |
|---|---|---|
| A — em-dash | any em-dash is a **hard fail** | one em-dash **aside** per sentence is legal; 2+ asides in the *same* sentence ("stacked") is a **hard fail** |
| B — AI-vocabulary blocklist | runs | runs (unchanged) |
| C — fictional cold-open | runs | runs (unchanged) |
| D — second-person register | runs, full Handbook list (penalty only) | runs, a **narrower** prescriptive/predictive-only list (penalty only) |
| E — word-count range | runs, out-of-range is a **hard fail** | **skipped entirely** — that line is governed by CharLint's exact character-count locks instead (see `charlint/README.md`) |
| G — hype-word blocklist | not checked | **hard fail on any hit**: `ultimate, amazing, game-changing, level up, unlock, transform, crush, beast mode, no excuses` |
| H — exclamation points | not checked | **hard fail on any hit** |

### Em-dash, re-measured against the real baselines

The governed unit under `workout_series` is the **aside**, not the dash character (see Check A'
below). Real numbers, run directly against `prohiblint.check_em_dash` /
`check_em_dash_workout_series` over all 7 baseline strings in `charlint/locks_seattle_series.json`:

```
slot              em-dashes   magazine   workout_series
cover_body                2  HARD FAIL             pass
city_intro                3  HARD FAIL             pass
anchor_venue              1  HARD FAIL             pass
anchor_cafe               6  HARD FAIL             pass
counter_venue             2  HARD FAIL             pass
counter_cafe              2  HARD FAIL             pass
night_page                3  HARD FAIL             pass
```

All 7 of 7 (100%) of the real Seattle Series reference baselines hard-fail under the magazine
em-dash rule alone — every one of them uses at least one em-dash, which magazine treats as an
unconditional hard fail. **0 of 7 hard-fail the em-dash check itself under `workout_series`** —
`anchor_cafe`'s six em-dashes are three matched pairs, one per sentence, each bracketing a single
aside, so none of its sentences stack two or more asides.

This is the em-dash check in isolation. Running the **full** `workout_series` ruleset (every check)
over the same 7 baselines, unmodified, fails **1 of 7** — `night_page`, on Check H (one exclamation
point in "Take the night — cheers!"), nothing to do with em-dashes at all:

```
$ python3 -c "
import json
locks = json.load(open('charlint/locks_seattle_series.json'))
slots = {name: spec['baseline'] for name, spec in locks['slots'].items()}
json.dump({'issue_id': 'SEA.RAW', 'slots': slots}, open('/tmp/raw_baselines.json', 'w'), indent=2)
"
$ python3 orchestrator.py --issue /tmp/raw_baselines.json --ruleset workout_series \
    --locks charlint/locks_seattle_series.json
...
Slot               Lock  Actual   Delta  Prohib   Status
---------------- ------ ------- ------- ------- --------
cover_body          351     351      +0     100  ✅ PASS
city_intro          628     628      +0     100  ✅ PASS
anchor_venue        667     667      +0     100  ✅ PASS
anchor_cafe         694     694      +0     100  ✅ PASS
counter_venue       602     602      +0     100  ✅ PASS
counter_cafe        414     414      +0     100  ✅ PASS
night_page          616     616      +0      95  ❌ FAIL
```

`anchor_cafe`, `anchor_venue`, and `city_intro` all read `prohib 100` — not the em-dash offender the
check used to report. Pointing the *magazine* ruleset at this same copy still fails essentially all
of it (7 of 7 on em-dash alone), because Workout Series prose uses em-dashes as a deliberate
stylistic device (PRINCIPLES.txt Sec. 7) and magazine treats any em-dash as an unconditional hard
fail.

### Which section name to use under `workout_series`

`run_prohiblint()` has no notion of a "slot" — it always iterates its own fixed 7-name `SECTIONS`
list, regardless of ruleset. The orchestrator's workout_series path calls ProhibLint once per
CharLint slot, handing each slot's prose in under one of the 7 magazine section names as a carrier
(`_PROSE_PROBE_SECTION` in `orchestrator.py`, currently `"Training"`). Which of the 7 names is used
does not change the verdict under `workout_series`, because Check E — the only check whose behavior
depends on the section name — is skipped entirely in that ruleset.

## Usage

```python
from prohiblint import run_prohiblint

sections = {
    "Training":    "...",
    "Nutrition":   "...",
    "Supplements": "...",
    "Recovery":    "...",
    "Culture":     "...",
    "Social":      "...",
    "Nightlife":   "...",
}

results = run_prohiblint(sections)                        # magazine
results = run_prohiblint(sections, ruleset="workout_series")
```

## Return Structure

Shape is identical across both rulesets (`test_return_shape_unchanged_for_workout_series` pins
this). Real output — `run_prohiblint()` over this repo's `sample_issue.json` sections, magazine
ruleset (trimmed to 2 of 7 sections for space; run it yourself, see "Verifying" below):

```json
{
  "sections": {
    "Training": {
      "violations": [
        "Word count 177 is outside allowed range [800–1200] for section 'Training'."
      ],
      "score": 80,
      "passed": false
    },
    "Supplements": {
      "violations": [
        "AI blocklist term 'delve' found 1 time(s). Penalty: -5.",
        "Word count 78 is outside allowed range [400–600] for section 'Supplements'."
      ],
      "score": 75,
      "passed": false
    }
  },
  "issue_level": {
    "violations": [],
    "penalty": 0,
    "passed": true,
    "element_results": {
      "workout_plan_rep_set": true,
      "nutrition_spots_4_places": true,
      "local_fitness_spots_2": true,
      "location_features_3_places": true
    }
  },
  "summary": {
    "total_score": 550,
    "all_passed": false
  }
}
```

## Checks

### A / A' — Em-dash detector

**magazine** (`check_em_dash`): flags every U+2014 (—) character. Any em-dash is a **hard fail**.
Penalty: **-10 per character**.

**workout_series** (`check_em_dash_workout_series`): the governed unit is the **ASIDE**, not the
dash character. PRINCIPLES.txt Sec. 7: "One em-dash aside per sentence, never stacked." An aside is
punctuated one of two ways — a matched **pair** of em-dashes bracketing a phrase mid-sentence (two
characters, one aside), or a single **trailing** em-dash introducing a final phrase (one character,
one aside). Counting dash *characters* instead of asides mis-reads the rule at exactly the place it
matters most: a correctly punctuated bracketed aside spends two characters on one legal aside. This
is what previously hard-failed `anchor_cafe` — owner-approved shipping copy — even though none of
its sentences actually stack.

Dashes pair off left to right, so:

```
asides = ceil(dashes / 2)          violation ("stacked") when asides >= 2
```

i.e. **1 or 2 em-dashes in one sentence is legal; 3 or more is stacked.** Penalty: **-10 per
offending sentence** (not per em-dash — a sentence with 8 stacked em-dashes still costs -10, not
-80).

Decided ambiguous cases:
- **Range dash exemption, digit-flanked only**: a dash closed up between two digits (`"5—9 daily"`,
  `"1989—92"`) joins two numbers and is not counted as an aside dash. A word—word closed-up dash
  (`"heavy—your legs shake—but you finish"`) is **not** exempt — US house style sets aside dashes
  closed, so exempting `word—word` would excuse the entire closed-up style.
- **En dash (U+2013)** is never counted — Sec. 7 governs the em-dash aside only; the baselines'
  "45–60 minutes" and "Olson Kundig–designed" are en dashes.
- **A semicolon or colon does not start a new unit.** Sec. 7 says "per sentence," and a semicolon
  joins clauses into one sentence; letting it reset the count would make stacking legal for the
  price of one semicolon.
- **A hard line break (`\n`) does end a unit.** These checks read whole Canva text elements —
  `night_page` is a title line, a location rule, a blank line, then prose — and a mid-sentence `\n`
  is a layout defect, not a sentence continuation.

Real numbers, verified directly:

```python
>>> import prohiblint as pl
>>> pl._count_asides("The room is loud — cold — cold.")   # one bracketed pair
1
>>> pl.check_em_dash_workout_series("The room is loud — cold — cold — cold.")  # 3 dashes = 2 asides
(["Stacked em-dash asides: 2 asides (3 em-dashes) in one sentence ..."], -10, True)
```

### B — AI Vocabulary Blocklist
Scans `AI_BLOCKLIST` (25 terms): `delve, foster, tapestry, vibrant, robust, holistic, leverage,
seamless, pivotal, transformative, unlock, elevate, revolutionize, journey, empower, thrive,
curated, game-changer, deep dive, synergy, ecosystem, impactful, actionable, harness, spearhead`.

Word-boundary, case-insensitive match. Penalty: **-5 per hit**. **Hard fail if 3+ hits** in a
single section.

`journey` is the one context-sensitive term — it only counts in a wellness/fitness context (e.g.
"your fitness journey", "journey toward better health") via a dedicated pattern
(`_JOURNEY_PATTERN`); literal travel ("the journey home", "a train journey") does not match. Every
other term is an unconditional match regardless of context.

Runs identically under both rulesets.

### C — Fictional Cold-Open Heuristic

Checks the first paragraph, capped at 200 characters (`_first_paragraph`). Penalty: **-15**, never
a hard fail. Runs identically under both rulesets.

**The `>30`-word floor (`SHORT_OPENING_WORDS`) is no longer one global gate — it applies per rule,
by how much evidence that rule carries:**

- the **person rule** is a four-way conjunction (see below) and can only be satisfied by an actual
  cold-open, so it runs at **any length** — a six-word cold-open ("Maya laces her shoes before
  dawn.") is caught, where the old single floor made writing less than 31 words a bypass anyone
  could find.
- the **clock-opener** rule and the **unattributed-scene** branch are each one signal wide (there is
  no name to weigh evidence against), so they keep the floor — under 31 words, `"It is 5am."` reads
  as ordinary short furniture (a deck, a standfirst, a kicker), not a cold-open.

#### The person rule: a four-way conjunction, not three patterns with a verb list

The rule is **not** "three patterns with a narrative-verb list." It is a conjunction of four tests,
tried at the start of every sentence in the opening (not only the first):

1. **SUBJECT** — a person's name at the start of a sentence: one to three capitalised tokens, or a
   family plural ("The Nakamura sisters"). Excludes sentence furniture, indefinites/number words,
   Seattle place tokens/bigrams, and any word this same copy also writes in lowercase elsewhere
   (which demotes "Recovery"/"Protein"/"Training" to the common nouns they are).
2. **PREDICATE** — an open-class present-tense verb: third-person `-s`, a bare verb for a plural
   subject, or a progressive (`"is lacing"`). Copulas, auxiliaries and function words are excluded by
   closed classes; there is no verb *list* to outgrow.
3. **MOMENT** — the paragraph anchors the action in a scene: a personal pronoun pointing back at the
   subject, a clock time, or a threshold (`"before the doors open"`, `"still dark"`). Ordinary
   connectives (`"after the first hour"`) do **not** qualify.
4. **NOT REPORTED** — see "Reported vs. constructed" below.

Verified directly — the person rule runs at any length:

```python
>>> import prohiblint as pl
>>> pl._word_count("Maya laces her shoes before dawn.")
6
>>> pl._matches_cold_open_pattern("Maya laces her shoes before dawn.")
True
```

`is` was **deliberately removed** from the narrative-verb list used by the unattributed-scene branch
(`_NARRATIVE_VERBS`) and from the motion-beat list used by the reported-vs-constructed weighing
(`_MOTION_BEAT_FORMS`) — a copula is not movement, and having it in the list made every "`<X> is
…`" sentence in the product read as narration (this was the root cause of a known `city_intro`
false positive: "Cascade is the quieter end of South Lake Union …"). **`looks` and `feels` are not
in either list either** — nothing in the current code enumerates them as movement.

#### Reported vs. constructed: the load-bearing half of the check

The habitual frame (`_HABITUAL_FRAME_RE` — `"every Tuesday"`, `"always orders"`, `"since
November"`, etc.) is what separates a People-register habit ("Jade Kim orders the same thing every
Tuesday") from a fictional scene ("Priya chalks her hands and steps onto the platform … the way she
always does"). Presence alone used to be a unconditional veto — one habitual phrase anywhere
switched the whole rule off — which was easier to evade than the binary it replaced: six words
appended to a staged scene turned the check off, and a genuine catch was lost the moment the
habitual phrase was about something *else* in the sentence (a door, an elevator) rather than the
subject.

A habitual frame now clears a scene **only when both** of the following hold:

- **it GOVERNS** the subject's own main clause — up to the first clause break (comma, semicolon,
  subordinator, or a coordinator introducing a new subject), and, when the following sentence is
  still about the same person, that sentence too; **and**
- **the scene stages fewer than `SCENE_BEATS_OUTWEIGH_FRAME` (2) physical beats** — a scene with 2
  or more staged bodily actions (`_MOTION_BEAT_FORMS`: laces, chalks, wraps, racks, shoulders, …)
  outweighs the habitual tag regardless of where it sits.

Verified directly:

```python
>>> import prohiblint as pl
>>> # habitual frame governs the main clause, and the scene is thin (1 beat): clears
>>> pl._matches_cold_open_pattern(
...     "Maya Okonkwo laces her shoes before dawn every Tuesday.")
False
>>> # same tag, but the scene stages 2 beats: the frame no longer outweighs it
>>> pl._matches_cold_open_pattern(
...     "Marcus pushes through the door with his bag on one shoulder every "
...     "morning and drops it by the rack.")
True
>>> # the People register's own reference sentence must stay clean
>>> pl._matches_cold_open_pattern(
...     "Jade Kim orders the same thing every Tuesday: the black sesame "
...     "smoothie and a side of turkey avocado toast.")
False
```

**Honest, documented limitation** (pinned in `TestOneBeatHabitClauseIsTheKnownLimit`, not papered
over): a **one-beat** scene whose habitual frame genuinely governs the subject's main clause is not
separable from a reported habit by scope or by weight — "Maya Okonkwo laces her shoes before dawn
every Tuesday." and the Handbook's own People reference sentence have the same shape, and both read
as reported here. This is a deliberate miss, not an oversight: separating the two needs discourse
structure (does the paragraph sustain the moment, or move on from it?) or a dependency parse,
neither of which this module has. Add a second beat and it flags:

```python
>>> pl._matches_cold_open_pattern(
...     "Maya Okonkwo laces her shoes and pulls the door shut before dawn "
...     "every Tuesday.")
True
```

### D — Second-Person Coaching Register

**No longer identical across rulesets.** `check_second_person(text, ruleset="magazine")` — the
default — bans the full magazine Handbook Sec. 6 list outright:

`you should`, `your body`, `try this`, `you need to`, `you can`, `you will feel`, `your workout`,
`you want to`.

`check_second_person(text, ruleset="workout_series")` flags a **narrower** list, because
PRINCIPLES.txt Sections 6–7 explicitly **endorse** direct address and reader autonomy ("Tiered
direct address when segmenting readers", "reader autonomy (you decide where you land)", "none of us
has met your body"). Running the Handbook's list over Workout Series copy previously cost
`anchor_venue` a penalty for "shakes you can pre-order before the last interval" — a description of
what the Fuel Bar does, not coaching. Only **prescriptive** (a modal of obligation) or **predictive**
(claiming to know what the reader's body will do) address is flagged:

`you should`, `you need to`, `you must`, `you have to`, `you will feel`, `you'll feel`, `try this`.

Descriptive second person — `"you can"`, `"your body"`, `"your workout"`, `"you want to"` — is
dropped for `workout_series` (each because PRINCIPLES either uses the form verbatim or endorses its
shape) and is house voice under that ruleset, not a violation.

`check_second_person` and `run_prohiblint` both take a `ruleset=` parameter (default `"magazine"`);
an unrecognized name raises `ValueError` rather than silently falling back — the same stance as an
unknown top-level ruleset.

Case-insensitive, word-boundary match (a curly apostrophe in `"you'll feel"` is normalised before
matching). Penalty: **-3 per hit**, both rulesets, never a hard fail. Content inside
`[SIDEBAR]...[/SIDEBAR]` tags (case-insensitive) is stripped before matching under both rulesets, so
sidebar copy is exempt.

### E — Word Count Range (magazine only; hard binary)
| Section      | Range     |
|-------------|-----------|
| Training    | 800–1200  |
| Nutrition   | 600–900   |
| Supplements | 400–600   |
| Recovery    | 500–800   |
| Culture     | 800–1200  |
| Social      | 500–700   |
| Nightlife   | 400–600   |

(`WORD_COUNT_RANGES`.) Word count is `len(text.split())`. Out-of-range is a **hard fail**, penalty
**-20**.

**Skipped entirely under `ruleset="workout_series"`** — that line has no word-count target; it is
governed by CharLint's exact character-count locks instead.

### F — Mandatory Value Elements (issue-level)
Run once across the full issue (all 7 sections joined with blank lines), via
`check_mandatory_elements()`. Four checks, all counted by **distinct** name — repeating one venue
six times never satisfies a "≥N named places" requirement:

| `element_results` key | Requirement |
|---|---|
| `workout_plan_rep_set` | Rep/set notation somewhere in the full issue (e.g. `3x8`, `4 sets`, `sets of 10`, `reps of 12`) |
| `nutrition_spots_4_places` | ≥4 **distinct** named venues in the Nutrition section, each carrying a **street address** (`_located_venue_names(..., require_address=True)`) — Handbook Sec. 9 locks the write-up as "Name of venue + neighbourhood + full address," so the address is the spec's own minimum, not a heuristic. A bare neighbourhood no longer qualifies here: "Aisha Coleman, Beacon Hill" is a person's location, not a venue, and only an address anchor is unambiguous between the two. |
| `local_fitness_spots_2` | ≥2 **distinct** named gyms/studios/run clubs, anywhere in the full issue, where the fitness keyword is **attached** to the name in the same noun phrase ("Rainier Barbell", "the gym: Fremont Hot Yoga") — proximity is not attachment. A keyword merely within 80 characters of a capitalised word ("The gym Marcus uses has no name on the door") no longer counts. |
| `location_features_3_places` | ≥3 **distinct** named venues anywhere in the issue: either a name carrying a place-type word ("Copper Tavern") or a name with a location anchor (street address, or a bare neighbourhood behind a venue-predicate test — "opens/closes/serves/pours…" — since a neighbourhood alone is shared by people and venues) |

Each missing element costs **-25**; the issue-level block fails (`passed=False`) if any element is
missing. These are heuristic regex matches over free text (see `check_mandatory_elements` in
`prohiblint.py` for the exact patterns) — not an exhaustive NLP parser.

`run_prohiblint()` always computes this block under both rulesets, but the **orchestrator** only
treats it as applicable to `magazine`. Under `workout_series` the orchestrator's scorecard reports
`issue_level_checks: {"applicable": false, "passed": null, ...}` — these are magazine Editorial
Handbook rules, and the Workout Series line is gated by CharLint's char locks instead (see the
top-level `README.md`).

### G — Workout-Series Hype-Word Blocklist (workout_series only)
PRINCIPLES.txt Sec. 7 bans these outright: `ultimate, amazing, game-changing, level up, unlock,
transform, crush, beast mode, no excuses` (`WORKOUT_SERIES_BLOCKLIST`, 9 terms).

Penalty: **-10 per hit**. **Hard fail on any single hit** — unlike Check B's generic AI blocklist,
which needs 3+ hits before it hard-fails, one hit here is enough.

`unlock` also appears in `AI_BLOCKLIST` (Check B). Under `workout_series`, a section using "unlock"
is flagged by both checks at once — that is intentional, not a double-counting bug: they are two
independent reasons the word is disallowed (generic AI-vocab tell, and a PRINCIPLES.txt-specific
outright ban).

### H — Exclamation-Point Ban (workout_series only)
PRINCIPLES.txt Sec. 7 bans exclamation points outright. Penalty: **-5 per instance**. **Hard fail**
if any are found.

Real output — `run_prohiblint({"Training": text}, ruleset="workout_series")` where `text` contains
"ultimate", "beast mode", "no excuses", and one "!" (`"This is the ultimate beast mode session, no
excuses! Push through every rep."`):

```json
{
  "violations": [
    "workout_series banned term 'ultimate' found 1 time(s). Banned outright (PRINCIPLES.txt Sec. 7). Penalty: -10.",
    "workout_series banned term 'beast mode' found 1 time(s). Banned outright (PRINCIPLES.txt Sec. 7). Penalty: -10.",
    "workout_series banned term 'no excuses' found 1 time(s). Banned outright (PRINCIPLES.txt Sec. 7). Penalty: -10.",
    "Exclamation point found: 1 instance(s). Banned outright under workout_series ruleset (PRINCIPLES.txt Sec. 7). Hard fail."
  ],
  "score": 65,
  "passed": false
}
```

## Scoring

Each section starts at 100 points (`score = max(0, 100 + section_penalty)` — this `100` is a bare
literal in `run_prohiblint()`; there is no `SCORE_START`-style constant in this module, unlike
`voicelint.voice_config` and `charlint`).

A section **passes** when `not hard_fail and score >= 70`. This `70` is also a bare literal, in the
same function (`passed = (not hard_fail) and (score >= 70)`) — there is no named constant for it in
`prohiblint.py` at all. Contrast this with `voicelint.voice_config.PASS_THRESHOLD` (85, imported and
actually compared against) and `charlint`, which has no pass-threshold constant of any kind (see
`charlint/README.md`).

Issue-level (Check F) passes only if all 4 mandatory elements are present.

## Verifying

Real end-to-end run over this repo's `sample_issue.json`, from the repo root:

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'prohiblint')
import prohiblint
sample = json.load(open('sample_issue.json'))
print(json.dumps(prohiblint.run_prohiblint(sample['sections']), indent=2))
"
```

## Running Tests

From the repo root:

```bash
cd prohiblint
python3 -m pytest test_prohiblint.py -q
```

382 tests, all passing as of this writing (`382 passed`).

## Dependencies

stdlib only: `re` is used throughout, and nothing else is imported anywhere in the module. `pytest`
is required to run the test suite, not the module itself.
