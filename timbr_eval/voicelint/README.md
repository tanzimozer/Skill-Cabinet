# VoiceLint — TIMBR Magazine Voice-Register Checker

VoiceLint is a lexical-only (no embeddings) voice-register linter for the **magazine** product
line only. The orchestrator does not run it under `--ruleset workout_series` — that line's own
register discipline is enforced by ProhibLint's workout_series checks and CharLint's exact
character-count locks instead (`voicelint`'s section/voice map is built for the magazine's 7
sections; see `orchestrator.py`'s `VOICELINT_NA_REASON`).

It checks whether each magazine section reads as its assigned register, flags a section that reads
more like one of the *other* two registers than its own ("cross-contamination"), and returns a
numeric score with a pass/fail verdict.

---

## The Three Registers

VoiceLint maps each of the 7 magazine sections to one of **three** voice registers via
`voice_config.SECTION_VOICE_MAP` — not a bespoke voice per section:

| Section     | Register (`SECTION_VOICE_MAP` value) |
|-------------|---------------------------------------|
| Training    | `athletic` |
| Nutrition   | `people` |
| Supplements | `fitt` |
| Recovery    | `fitt` |
| Culture     | `athletic` |
| Social      | `people` |
| Nightlife   | `fitt` |

A section name absent from `SECTION_VOICE_MAP` falls back to `voicelint.DEFAULT_VOICE`, which is
`"athletic"`.

`"athletic"`, `"people"`, and `"fitt"` are the literal, lowercase strings the code produces (e.g.
`voice_required` in the output below).

**No register asks for second person.** ProhibLint's Check D penalizes `you should` / `your body`
/ etc. in *every magazine* section, regardless of register (see `prohiblint/README.md`) — and the
`athletic` register's own negative markers separately penalize `you should`/`you can`/`you need`,
while `fitt`'s negative markers separately penalize `you should`/`your body`/`try this`/`you need`.
No register's *positive* markers reward second-person address anywhere. Do not write any magazine
section in second person, in any register.

---

## Two channels of evidence, not one

Each register scores a section as a signed **affinity delta** against `SCORE_START`. Before this
scale existed as a single flat sum, the delta was one number; it is now the sum of **two channels**
(`voicelint.Affinity`, a `NamedTuple`), and the split is load-bearing, not cosmetic:

| Channel | What lives here | Scaled by length? |
|---|---|---|
| `section_level` | the register's gate, the athletic "earned rhythm" bonus, the fitt "opinionated kicker" and "declarative openings" bonuses — evaluated **once** per section | **No** |
| `per_occurrence` | lexical marker hits, data-led sentences, the fitt long-paragraph penalty — anything that can fire more than once | **Yes** — to `DENSITY_BASELINE_WORDS` (100) words |

`Affinity.delta` (`section_level + per_occurrence`) is the raw, unclamped number `voice_affinity()`
returns and the number `score_*()` clamps into `0..100`. It is unaffected by the split.

The split matters for **density** (`voice_affinity_density()`), which is what cross-contamination
actually compares:

```
density = section_level + per_occurrence * DENSITY_BASELINE_WORDS / max(words, DENSITY_BASELINE_WORDS)
```

A once-per-section term (a gate worth ±10) contributed 10 points of margin at 100 words and 1.4 at
700 if it were divided by length too — dividing a section-level term by length is a **decay**, not
a normalisation, and at production lengths (400–1200 words per `prohiblint.WORD_COUNT_RANGES`) it
switched contamination detection off almost entirely. So only `per_occurrence` is divided by length;
`section_level` never is.

**Consequence, verified directly: density is exactly invariant under duplication.** Concatenating a
section with itself doubles both the word count and every per-occurrence count, so the ratio —
and therefore every register's density — is unchanged. Real output, run from the repo root against
this repo's `sample_issue.json` Training section (177 words):

```bash
$ python3 -c "
import sys, json
sys.path.insert(0, 'voicelint')
import voicelint as vl
training = json.load(open('sample_issue.json'))['sections']['Training']
print('single :', vl.voice_affinity_density(training))
print('doubled:', vl.voice_affinity_density(training + '\n\n' + training))
"
single : {'athletic': 16.779661016949152, 'people': 8.870056497175142, 'fitt': 10.0}
doubled: {'athletic': 16.779661016949152, 'people': 8.870056497175142, 'fitt': 10.0}
```
177 words doubled to 354; every density is identical. This is what makes a margin comparable between
a 400-word section and a 1200-word one of the same register.

---

## Register gates

Every register has **exactly one gate** — its single defining test — worth `±REGISTER_GATE` (10
points), evaluated for *every* section regardless of which register it is scored against. Before
this, the three registers' gates were not comparable at all: fitt carried an unconditional +8/−10,
people an unconditional +5/−8, and athletic had **no gate whatsoever** — so a register-neutral
paragraph already scored people > athletic > fitt before a single word of the actual copy was read.
Now all three are the same shape and the same size:

| Register | Gate (pass `+10` / fail `−10`) |
|---|---|
| `athletic` | claims are **attributed to a source** (`ATHLETIC_ATTRIBUTION` matches anywhere in the text) **AND** the section contains at most `ATHLETIC_EXCLAMATION_ALLOWANCE` (1) exclamation point |
| `people` | a **named person** appears in the opening `PERSON_WINDOW_WORDS` (50) words (`voicelint._named_person`) **AND** the section contains at least one `PEOPLE_ACCESS` marker (anywhere in the text, not only the opening window) |
| `fitt` | **staccato**: the share of paragraphs at or under `FITT_POSITIVE_PARA_MAX` (40) words is at least `FITT_STACCATO_RATIO` (0.6) |

The athletic gate is a conjunction on purpose: attribution alone used to be worth a flat +2 marker,
so a Culture section with one attributed quote and six exclamation points scored 64/FAIL on the old
scale and 92/PASS on an attribution-only gate. Six exclamation points are not reported copy however
carefully the quotes are sourced, and under the magazine ruleset VoiceLint is the only check that
looks at exclamation points at all.

The people gate's access half is what makes it a *profile* test and not a *name* test: reported
copy names its sources in the opening 50 words as a matter of routine ("Dee Nakashima, who opened
the facility in 2019 …" is an ordinary Culture-report opener), so a name-only gate handed the
people register a free `+REGISTER_GATE` on ordinary athletic reporting.

---

## Named-person detection is a function, not a regex

`voicelint._named_person(text)` decides whether a passage names a **person** rather than a place or
an organisation. It replaced two earlier failures in opposite directions: "any Titlecase bigram"
fired on "South Lake Union is quiet"; a Titlecase bigram plus a closed 23-verb cue list then missed
every real person doing anything the list did not happen to contain ("Devon Ashworth carries the
cones out", "Renata Boyle coaches the 6am group" were both invisible).

The set of things a person can *do* is open and cannot be enumerated; the set of things that must be
*excluded* is a genuinely closed class of English. So the test is an open action class by morphology,
plus closed exclusion classes:

- a Titlecase bigram, excluding sentence furniture (`_NON_NAME_TOKENS`) and known Seattle place
  words/bigrams (`_PLACE_TOKENS`, `_PLACE_BIGRAMS`);
- **overridden** by a person-only cue that no place or organisation ever takes — age apposition
  (`", 45,"`), a directly adjacent reporting verb (`"Marcus Webb says"`), or `", who"`;
- otherwise it must take a **person predicate**: a possessive (`'s`), a role apposition (`", a
  strength coach"`), a progressive/finite copula (`"is standing"`, `"has coached"` — but not `"is
  the club"`), or an **open-class finite action verb** — third-person present (`-s`, not `-ss`),
  regular past (`-ed`), a closed irregular-past list, or anything else that takes a direct object.

Verified directly:

```python
>>> import voicelint as vl
>>> vl._named_person("Devon Ashworth carries the cones out before the group arrives.")
True
>>> vl._named_person("Renata Boyle coaches the 6am group.")
True
>>> vl._named_person("Cascade Rowing is the older club.")
False
>>> vl._named_person("South Lake Union is quiet on a Sunday.")
False
```

---

## Register fingerprints

### `athletic`

Per-occurrence positive, `POSITIVE_HIT` (**+2**) each:
- `ATHLETIC_POSITIVE` (shared with `fitt` — see `DATA_CLAIM` below): a number followed by
  `%`/`percent`/`miles`/`minutes`/`pounds`/`lbs`/`kg`/`hours`/`days`/`weeks`/`seconds`/`metres`/
  `meters`/`kilometres`/`kilometers`/`sessions`/`reps`/`sets`/`grams`/`mg`
- `ATHLETIC_POSITIVE_CAPS` (case-**sensitive**): `At <Capitalized...>`, `In <Capitalized...>`,
  `<Word>, <2-digit-age>,`, `<Word> <Word>, <lowercase-word> at/of/for/with <Capitalized>`
- **`ATHLETIC_SOURCING`** (case-sensitive, new marker family — see below): counted here as the
  register's per-occurrence sourcing vocabulary, in addition to being tested once, as a boolean, by
  the gate

Per-occurrence negative, `NEGATIVE_HIT` (**−3**) each: an exclamation point; `you should`/`you
can`/`you need`/`get ready`/`are you ready`/`it is time`; `amazing`/`incredible`/`awesome`/
`fantastic`/`wonderful`.

Section-level structural, `STRUCTURAL_HIT` (**+2**, one-sided): "earned rhythm" — 4+ sentences with
at least 2 under 8 words and at least 2 over 20 words.

Section-level gate: see "Register gates" above (±10).

### `ATHLETIC_SOURCING` — the marker family that used to be missing

Before this, the athletic register's *entire* per-occurrence vocabulary was `DATA_CLAIM` — shared
with `fitt`, so it cancels in an athletic/fitt margin — plus four capitalised place-and-name
patterns. A Culture feature that is a **human story** rather than a **data story** (which is what a
Culture feature is) had nothing to compete with the people register's pronoun density, and lost. A
447-word Culture closure feature carrying `"according to"`, three sourced quotes, `"did not respond
to two requests for comment"` and `"declined to discuss an active listing"` scored −3 on the
athletic per-occurrence channel and +46 on the people one — it passed the gate and was blocked as
people-contaminated anyway.

`ATHLETIC_SOURCING` is four case-sensitive pattern groups, all counted per occurrence (+2 each) as
well as feeding the gate:

- **`ATHLETIC_ATTRIBUTION`** — attribution to a named/role/institutional source (`"Nair says"`,
  `"according to the council"`, the long-apposition shape `"Priya Nair, 29, head of performance
  science at Northwest Sports Institute, says …"`). A bare pronoun tag (`"she says"`) does **not**
  count — that is the people register's own access evidence, not sourcing.
- **`ATHLETIC_NON_RESPONSE`** — the non-response frame: `"declined/refused to comment/discuss/
  say/…"`, `"did/does/has not responded/replied/answered/commented"`, `"requests for comment"`,
  `"was not available for comment"`, `"on condition of anonymity"`, `"before publication"`.
- **`ATHLETIC_PROVENANCE`** — where the fact came from: `"spokesperson"`, `"a representative for"`,
  `"in a written statement"`, `"public/court/city/state/federal records"`, `"records show"`,
  `"reached by phone"`, `"in an interview"`, `"compiled/provided/shared/released/submitted by"`.
- **`ATHLETIC_REPORTED_HEDGE`** — `"reportedly"`, `"is/are/was/were said to"`.

`ATHLETIC_ATTRIBUTION` is deliberately counted **both** as the gate (a boolean: does this section
attribute at all?) and per occurrence (a density: how much of the section's sentence-by-sentence
machinery is sourcing machinery?). A report attributes continuously to many sources; a profile
attributes to its one subject and then narrates. Only the density question can tell those apart.

### `people`

Per-occurrence positive, `POSITIVE_HIT` (+2) each — `PEOPLE_POSITIVE` is `PEOPLE_ACCESS` plus two
more items:
- `PEOPLE_ACCESS`: `whose <word>`; `her/his/their kids/children/wife/husband/partner/mother/father/
  parents/son/daughter/family/apartment/kitchen/home/house/dog/roommate/friends/voice/hands/
  mornings/routine/clients/neighbours/neighbors`; `<Name>, <1–2 digit age>,`; `<2-digit>, (a|the|
  an|is|was|works|lives|trains)`; a tagged quote (`"…" she says/said/adds/added/explains/laughs/
  recalls`, straight or curly quotes); `every/each morning/Tuesday/week/Thursday/Sunday/day/
  evening/night/Monday/…`
- **`PEOPLE_PRONOUN`**: `she/her/hers/he/him/his`, **excluding** a pronoun immediately followed by
  an attribution verb (`"he says"`, `"she adds"`) — that is the shared quote-tag machinery both
  registers use, not evidence that separates them.
- a personal-life-verb list: `lives, grew up, moved, walks, sits, stands, laughs, laughed, smiles,
  smiled, cries, crying, remembers, recalls, swears, credits, wakes`

Per-occurrence negative, `NEGATIVE_HIT` (−3) each:
- `PEOPLE_NEGATIVE`: `was found`/`has been shown`/`it is known`/`it has been`; 3+ directly adjacent
  `<digits>. ` tokens with nothing in between (does not fire on an ordinary numbered list, which
  always has content between the numbers)
- `PEOPLE_NEGATIVE_CAPS`: opens with `Studies`/`Research`/`Data`/`According to studies`
- **`PEOPLE_NEGATIVE_SOURCED`** (new marker family — literally `list(ATHLETIC_SOURCING)`, the same
  four case-sensitive pattern groups documented above): borrowed authority is the people register's
  violation for the same reason it is the athletic register's virtue. See "Two-channel affinity" and
  "Calibration" below for why sourcing density, and *only* sourcing density, is what separates a
  reported feature about a person from a profile of one.

Section-level gate: see "Register gates" above (±10).

### `fitt`

Fitt now uses the **same** shared unit system as the other two registers — every one of its
signals is worth `POSITIVE_HIT`, `NEGATIVE_HIT`, or `STRUCTURAL_HIT`, and its one defining test is
the same `±REGISTER_GATE` every register gets. There are no bespoke point values left anywhere in
this register.

| Signal | Channel | Points | Condition |
|---|---|---|---|
| `FITT_POSITIVE` (`DATA_CLAIM`, shared with athletic) | per-occurrence | `POSITIVE_HIT` (+2) each | a number + unit |
| Staccato gate | section-level | `±REGISTER_GATE` (±10) | ≥ `FITT_STACCATO_RATIO` (0.6) of paragraphs ≤ `FITT_POSITIVE_PARA_MAX` (40) words |
| Long paragraph | per-occurrence | `NEGATIVE_HIT` (−3) each | any paragraph > `FITT_LONG_PARA_MAX` (80) words — can fire multiple times |
| Opinionated kicker | section-level | `STRUCTURAL_HIT` (+2) | last sentence ≤ `FITT_POSITIVE_KICKER_MAX` (12) words **and** contains a strong-opinion word (`best, worst, only, never, always, exactly, period, full stop, done`) |
| Declarative openings | section-level | `STRUCTURAL_HIT` (+2) | ≥50% of paragraphs open with a declarative sentence (`FITT_DECLARATIVE`) |
| Data-led sentence | per-occurrence | `STRUCTURAL_HIT` (+2) each | sentence starts with a digit (`FITT_DATA_LEAD`) |
| `FITT_NEGATIVE` | per-occurrence | `NEGATIVE_HIT` (−3) each | hedges (`might, could, perhaps, possibly, seems, appear, suggest, may`); `you should`/`your body`/`try this`/`you need`; **any reporting verb at all** (`REPORTING_VERB_ANY` — sourced or not; this is the bare verb list, deliberately not the stricter `ATHLETIC_ATTRIBUTION`, because fitt's question is "does this report at all", not "does this name a source") |
| `FITT_NEGATIVE_CAPS` | per-occurrence | `NEGATIVE_HIT` (−3) each | subordinate-clause opener (`Although, While, Despite, However, Nevertheless, Nonetheless`) |

---

## Scoring

```
delta  = <register>_affinity(text).delta      # section_level + per_occurrence; signed, NOT clamped
score  = clamp(SCORE_START + delta, 0, SCORE_START)      # SCORE_START = 100
```

The unclamped `delta` (`voice_affinity()`) and the unclamped per-100-word density
(`voice_affinity_density()`) are what cross-contamination compares — never the clamped score. Two
sections can both clamp to 100 on their own register while carrying very different fingerprints.

### The scale, one unit system, three registers

```
SCORE_START        = 100
POSITIVE_HIT        =  2     # points per positive marker hit
NEGATIVE_HIT        = -3     # points per negative marker hit
STRUCTURAL_HIT      =  2     # == POSITIVE_HIT; one structural feature counts like one marker hit
REGISTER_GATE       = 10     # == 5 * POSITIVE_HIT; every register's single defining test, +/-
```

### Pass threshold: derived, not chosen

With no contamination penalty, `passed <=> SCORE_START + delta >= PASS_THRESHOLD`, so the threshold
encodes exactly one editorial decision: how much negative evidence a section may carry and still
ship — denominated in the scale's own unit, the negative marker:

```
NEGATIVE_MARKER_BUDGET = 5                                      # marker hits
FAIL_FLOOR_DELTA       = NEGATIVE_MARKER_BUDGET * NEGATIVE_HIT  # 5 * -3 = -15
PASS_THRESHOLD         = SCORE_START + FAIL_FLOOR_DELTA         # 100 - 15 = 85
```

**`PASS_THRESHOLD` is 85**, verified directly against the constant. It is 85 *because* the budget is
5 negative-marker hits at −3 each, not a number picked and then rationalised — `test_voicelint.py`
pins the **effective** bar (the delta at which pass flips), not the constant by name, so a change
that moved the constant without moving the effective bar would still fail the suite.

---

## Cross-contamination

Relative and density-based, checked against **both** other registers on every section:

```
density[v]   = section_level[v] + per_occurrence[v] * DENSITY_BASELINE_WORDS / max(words, DENSITY_BASELINE_WORDS)
margin       = density[other] - density[required]
contaminated = density[other] > 0  AND  margin >= CROSS_CONTAMINATION_MARGIN
```

`DENSITY_BASELINE_WORDS = 100`. **`CROSS_CONTAMINATION_MARGIN` is 5** — measured in points **per
100 words**, not in raw affinity points. This is checked independently for each of the two
non-required registers, so a single section can take **two** contamination penalties at once if it
genuinely reads like both of the others.

```
final_score = clamp(primary_score - total_contamination_penalty, 0, 100)
passed      = final_score >= PASS_THRESHOLD
```

### The penalty now blocks a section — this is a deliberate change from annotate-only

**`CROSS_CONTAMINATION_PENALTY` is 18.** It used to cost 10 against a 15-point negative-marker
budget, so a section strong in its own register absorbed one contamination flag and still passed —
and the orchestrator routes a *passing* section's flags to advisory, so a Training section written
as a pure People profile shipped at 90 with a note attached, rather than failing. Finding the wrong
register and then waving it through is worse than not looking.

18 is `(NEGATIVE_MARKER_BUDGET + 1) * -NEGATIVE_HIT` — **one more negative marker than the entire
budget** — so even an otherwise-perfect section (delta 0, clamped score 100) takes one contamination
flag to 100 − 18 = 82, which is below `PASS_THRESHOLD` (85). Verified directly:

```python
>>> import voice_config as cfg
>>> cfg.SCORE_START - cfg.CROSS_CONTAMINATION_PENALTY < cfg.PASS_THRESHOLD
True     # 100 - 18 = 82 < 85
```

One contamination flag is now always enough to fail a section by itself, regardless of how clean
the rest of it is. This is the intended trade, made on the evidence that the validation corpus (see
Calibration below) produced zero false positives with 7.95 points to spare — a false positive now
blocks a section instead of annotating it, because a blocked section gets rewritten and an advisory
note gets ignored.

---

## Calibration

`CROSS_CONTAMINATION_MARGIN` was **derived, then validated against corpora the derivation never
saw** — not picked and rationalised after the fact. Three previous margins died the same way:
validated only against the data used to derive them (which cannot fail), or validated against a
held-out corpus that did not happen to contain the shape that breaks them.

**Derivation corpus** — 49 texts, 35–1176 words. 32 in-register (must **not** fire): 10 hostile
in-register texts, 9 clean per-register samples, 7 sections of `sample_issue.json` (text this
module's author did not write), 6 long hostile in-register texts at 480–1176 words (two of them the
reported human-interest shape that was previously missing). 17 cross-register (**must** fire): 8
hostile wrong-voice texts, 4 legacy cross-register samples, 5 long wrong-register texts at
793–1135 words (one the quiet-profile shape the cross half was missing).

```
worst in-register : +3.00   (an 80-word Recovery section from sample_issue.json; athletic/fitt axis)
weakest cross      : +6.57   (an 852-word Culture section written as a diluted, surname-tagged profile)
band               : (+3.00, +6.57]   width 3.57
margin             : midpoint 4.78 -> 5
```

**Validation corpus** — 12 texts, 530–1023 words, every one inside `prohiblint.WORD_COUNT_RANGES`
for its section:

```
band     : (-9.76, +5.91]   width 15.67
verdict  : 5 sits inside it. 6 of 6 wrong-register texts flagged, 0 of 6 in-register texts flagged.
```

**Gate-2 held-out corpus** — 12 texts, 90–447 words, written by the reviewer after the two-channel
rebuild and never seen while deriving the margin — this is the corpus that produced the blocker
that forced `ATHLETIC_SOURCING` and `PEOPLE_NEGATIVE_SOURCED` to exist:

```
band     : (+1.46, +24.25]   width 22.79
verdict  : 5 sits inside it. 6 of 6 wrong-register texts flagged, 0 of 6 in-register texts flagged.
```

Nothing is held out any more: all three corpora above were consulted while fixing the marker set,
so none of them can refute the current constant. The next calibration needs text none of these three
contain.

### Headroom, in both directions — and a retraction

An earlier version of this file stated: *"8.00 points of margin before a false positive and 1.21
before a miss … this mechanism is closer to missing contaminated copy than to blocking clean
copy."* **That claim was wrong, and the retraction is deliberate — it stays in this document.**
Measured against held-out text, the true ordering was the exact opposite: the mechanism was far more
likely to **block good copy** than to **pass bad copy**. The confident sentence above was measured
on a corpus that did not contain the shape that breaks it, and that is the second time a confident
headroom claim here has been refuted.

The real numbers — the worst case over every text this module has ever been measured against, all
three corpora pooled, nothing held out:

```
before a FALSE POSITIVE : +2.00   (binding text: the 80-word Recovery section, athletic/fitt axis)
before a MISS           : +0.91   (binding text: the 923-word Culture section written as a
                                    profile, athletic/people axis)
```

Both are under one marker hit at the length of the text that binds them, and the pooled band is
2.91 points wide against a scale whose smallest unit is 2. This constant is not comfortably placed
in either direction, and no honest reading of the data says otherwise.

### The resolution limit — a documented limitation, not a tuning problem

On the athletic/people axis, measured across 18 texts (8 reported features about a person, 10
profiles), per 100 words:

| Marker family | Reported features | Profiles | Separates? |
|---|---|---|---|
| profile access | 0.00–2.65 | 1.52–5.15 | no, overlaps |
| personal pronoun | 1.13–5.52 | 3.03–9.79 | no, overlaps |
| personal-life verb | 0.00–0.53 | 0.00–1.25 | no, overlaps |
| **sourcing** | 0.88–2.61 | 0.00–0.52 | **yes, cleanly** |

Exactly **one** marker family carries signal on this axis, and its whole dynamic range is about 2.6
markers per 100 words — roughly 5 points of density, counted on both sides. That is the mechanism's
actual resolution on this axis, and the threshold has to be placed inside it; a fifth constant will
not widen the band. VoiceLint separates a report from a profile with about one marker of headroom,
and borderline copy on this axis needs a human. A known, recorded, unfixed evasion: a profile
written in surnames and attribution tags instead of pronouns ("Varga says" for "she says") reads
athletic to this module and clears the gate — one source quoted many times is indistinguishable
here from many sources quoted once.

---

## Usage

The public API is `run(sections)`:

```python
import voicelint

results = voicelint.run({
    "Training":  "...",
    "Nutrition": "...",
})
```

Real output — `voicelint.run()` on this repo's `sample_issue.json`, Training and Nutrition
sections, unmodified:

```json
{
  "Training": {
    "voice_required": "athletic",
    "voice_score": 100,
    "contamination_flags": [],
    "passed": true,
    "_debug": {
      "primary_delta": 22,
      "contamination_penalty": 0,
      "primary_details": [
        "athletic positive markers x4 (+8)",
        "sourcing markers x2 (+4)",
        "gate: claims are attributed to a source (+10)"
      ],
      "athletic_delta": 22,
      "people_delta": 8,
      "fitt_delta": 10,
      "words": 177,
      "affinity_per_100w": {"athletic": 16.78, "people": 8.87, "fitt": 10.0}
    }
  },
  "Nutrition": {
    "voice_required": "people",
    "voice_score": 100,
    "contamination_flags": [],
    "passed": true,
    "_debug": {
      "primary_delta": 16,
      "contamination_penalty": 0,
      "primary_details": [
        "people positive markers x3 (+6)",
        "gate: named person in opening 50 words, and the section gives access to them (1 markers) (+10)"
      ],
      "athletic_delta": -10,
      "people_delta": 16,
      "fitt_delta": -8,
      "words": 208,
      "affinity_per_100w": {"athletic": -10.0, "people": 12.88, "fitt": -8.0}
    }
  }
}
```

Also available, lower-level:

```python
from voicelint import score_athletic, score_people, score_fitt, voice_affinity, voice_affinity_density

score, flags = score_athletic(text)     # -> (int, [str, ...]) — clamped score + negative-marker flags
voice_affinity(text)                    # -> {"athletic": int, "people": int, "fitt": int} — unclamped delta
voice_affinity_density(text)            # -> {"athletic": float, ...} — unclamped, per 100 words; what
                                         #    cross-contamination actually compares
```

### Output schema (per section, from `run()`)

```
{
  "voice_required":      str,     # "athletic" | "people" | "fitt"
  "voice_score":         int,     # 0-100, clamped
  "contamination_flags": [str],   # negative-marker flags for the required register + cross-contamination flags
  "passed":              bool,    # voice_score >= PASS_THRESHOLD
  "_debug": {
    "primary_delta":          int,    # unclamped delta (section_level + per_occurrence) for voice_required
    "contamination_penalty":  int,    # 0, 18, or 36 (two contaminating registers at once)
    "primary_details":        [str],
    "athletic_delta":         int,    # unclamped, all three always present regardless of voice_required
    "people_delta":           int,
    "fitt_delta":              int,
    "words":                  int,    # word count of the section
    "affinity_per_100w":      {"athletic": float, "people": float, "fitt": float},  # the density used for contamination
  }
}
```

---

## Running Tests

From the repo root:

```bash
cd voicelint
python3 -m pytest test_voicelint.py -q
```

387 tests, all passing as of this writing (`387 passed`).

---

## File Structure

```
voicelint/
├── voicelint.py        — run(), score_athletic/people/fitt(), voice_affinity(), voice_affinity_density()
├── voice_config.py     — SECTION_VOICE_MAP, all regex patterns, scoring constants
├── test_voicelint.py   — pytest suite (387 tests)
├── __init__.py
└── README.md            — this file
```

---

## Dependencies

stdlib only: `re` and `typing.NamedTuple` (the latter backs `voicelint.Affinity`). `pytest` is
required to run the test suite, not the module itself.

---

## Extending

To add a new section, add an entry to `SECTION_VOICE_MAP` in `voice_config.py`. The value must be
one of the three real register names:

```python
SECTION_VOICE_MAP["gear"] = "athletic"
```

To adjust scoring, the real constant names in `voice_config.py` are `SCORE_START`, `POSITIVE_HIT`,
`NEGATIVE_HIT`, `STRUCTURAL_HIT`, `REGISTER_GATE`, `NEGATIVE_MARKER_BUDGET`, `FAIL_FLOOR_DELTA`,
`PASS_THRESHOLD`, `DENSITY_BASELINE_WORDS`, `CROSS_CONTAMINATION_MARGIN`,
`CROSS_CONTAMINATION_PENALTY` — every one of them is derived from, or feeds, the others (see
"Scoring" above); moving one without re-deriving the rest is how the fixed-floor defect happened the
first time.
