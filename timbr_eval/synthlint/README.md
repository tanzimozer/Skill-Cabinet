# SynthLint

The AI-fingerprint linter for the TIMBR eval harness.

ProhibLint scores what the handbook bans. VoiceLint scores which register the copy is written
in. CharLint scores whether it fits the layout. SynthLint asks the one question none of them
asks: **does this read like a machine wrote it?**

SynthLint runs **universally**. There is no `ruleset` argument, deliberately — sounding like an
LLM is a defect on the magazine line and on the Workout Series alike.

```python
from synthlint import run_synthlint

run_synthlint(text)
# {"violations": [str, ...], "score": int, "passed": bool, "flags": {...}}
```

---

## The constraint this module was built around

TIMBR's own locked voice uses devices that generic LLM prose also overuses. PRINCIPLES.txt
Sec. 7 explicitly endorses:

> "Triads and parallelism (your history, your joints, your limits)."
> "Colon-led micro-lists for instructions."
> "Short declaratives. Fragments allowed for punch."

A check that fires on the **presence** of one of those devices is not an AI detector, it is a
rejection of the house voice. The differentiator is almost always **density or rate**, never
presence.

Concretely, all of the following is real TIMBR copy and none of it may fire:

| Real copy | The naive check that would have flagged it |
|---|---|
| "It is not CrossFit. It is not Pilates. It is the barbell." | 3 consecutive `It`-openers |
| "No loading phase. No cycling. No timing protocol worth the attention it gets." | 3 consecutive `No`-openers |
| "The turkey and white bean bowl is 41g protein, 29g carbs, 19g fat, $16." ×3 | 3 consecutive `The`-openers |
| "This is not a story about equipment. This is a story about what the city decided to want." | contrastive-frame regex |
| "has about twenty minutes … to put roughly 40 grams of protein somewhere" | 2 hedges in one clause |
| a 19-sentence Supplements section at a mean of 4.3 words | flat-rhythm statistic |
| 25 rule-of-three triads across 114 paragraphs | any triad-rate check at all |
| nine rows of `- Name: sets × reps — cue`, every row the same shape | flat-rhythm statistic (**this one got through — see 5b**) |

Every one of those produced an exemption, a raised threshold, or — once — a dropped check. The
last row is the one that was not caught in derivation: the workout table is not prose, it was
excluded from the corpus as "not prose", and a prose statistic was then run over it anyway.

---

## What it checks

| # | Check | Unit | Threshold | Derived from |
|---|---|---|---|---|
| 1 | Extended AI vocabulary | per hit | any hit; hard fail at 5 | 0 hits in 4,792 words of real copy |
| 2 | Formulaic transition density | paragraph-initial rate | ≥2 hits **and** rate > 0.20 | 0 hits in 114 real paragraphs |
| 3 | Contrastive-frame overuse | frames per 250 words | ≥2 frames **and** rate > 2.0 | 0 frames in real copy |
| 4 | Hedge stacking | per stacked clause | any instance; hard fail at 3 | 0 stacks in real copy |
| 5 | Sentence-length burstiness | CV = stdev / mean, over sentences — or over row fields on a spec list | CV < 0.29 | flattest real text 0.3867 |
| 6 | Repeated-opener runs | consecutive sentences | same-word ≥4, generic-class ≥3 | real copy tops out at 3 |
| — | ~~Triad / rule-of-three rate~~ | — | **DROPPED** | see below |

### 1 — Extended AI vocabulary

Phrasal scaffolding: `it's important to note`, `when it comes to`, `a plethora of`,
`state-of-the-art`, `moreover`, `in conclusion`, `plays a crucial role` and 35 more.

Terms already carried by `prohiblint.AI_BLOCKLIST` are filtered out **programmatically** at
import (`synth_config.EXTENDED_AI_VOCAB`), so no word is priced twice across two linters. The
intersection is currently empty; if ProhibLint later adds one of these terms the overlap
disappears on its own. `VOCAB_CEDED_TO_PROHIBLINT` records what was handed over.

Deliberately **not** on the list, because real TIMBR copy uses each one: `additionally` and
`overall` (tells only in paragraph-initial position — Check 2's job, not a lexical ban);
`roughly`, `approximately`, `about`, `around` (measurement words: PRINCIPLES Sec. 8 requires a
number in every body paragraph and these are how a number gets qualified honestly); `may`,
`might`, `could`, `seems`, `suggests` (single hedges, already covered by
`voice_config.FITT_NEGATIVE[0]`).

### 2 — Formulaic transition density

Paragraph-**initial** only. Mid-sentence "the overall volume rose 31 percent" is a
measurement; opening one paragraph in three with a connective adverb is a shape.

Requires **two** hits before it fires. A single "Moreover" is presence, not density — and it is
already priced once by Check 1. The overlap between the two lists is intentional: Check 1
prices the phrase, Check 2 prices the rate at which paragraphs are opened with one.

### 3 — Contrastive-frame overuse

The compressed pivot: `isn't just about X`, `not just a gym, it's a community`, `it's not about
X, it's about Y`, `not X but rather Y`, `more than just`.

Every pattern requires the compression — a negation and its pivot **inside one clause**, with
an intensifier (`just` / `merely` / `simply` / `only`). TIMBR's own contrast states the
negation and the correction as separate sentences and never reaches for an intensifier, which
is exactly what separates the house device from the machine one.

**One frame is never a violation.** A single pivot is a legitimate rhetorical move and close kin
to PRINCIPLES Sec. 7's "concede then redirect". The defect is reaching for it repeatedly.

### 4 — Hedge stacking

Two hedges compounding on one proposition: `may potentially`, `could possibly`, `it is possible
that … might`. Fires on adjacency (≤2 words apart inside one clause) or on an epistemic frame
plus any hedge in the same sentence.

This is **not** a bigger version of a single hedge. One hedge marks a claim uncertain; two on
the same claim mark the writer unwilling to make it — the opposite of PRINCIPLES Sec. 9
("uncertain equals failed"). There is no density at which stacking is house voice, so this
check has no rate: every instance is a violation.

Guards that keep it off real copy: measurement qualifiers are not in the lexicon; `can` is not
in the lexicon (ability, not hedging — the same call ProhibLint made for `you can`); a modal
immediately followed by `not`/`n't` is negation, not hedging ("a use the previous tenant could
not match" is a fact).

### 5 — Sentence-length burstiness

`CV = population stdev / mean` of sentence word counts. Two gates before the statistic is
trusted: at least 8 sentences (below that CV is noise — a real two-sentence TIMBR slot reaches
0.13 legitimately), and a mean of at least 8 words (below that the text is in the staccato
register PRINCIPLES Sec. 7 endorses, where uniformity *is* the device).

Floor derivation: the flattest real TIMBR text that clears both gates is `sample_issue:Nutrition`
at **CV 0.3867**. The floor is `0.3867 × 0.75 = 0.29002`, rounded **down** to `0.29`. A real
text would have to become 25% more uniform than the flattest one ever measured before it trips.

#### 5b — The spec-list shape, and the unit rhythm is measured over

The check above was derived from prose and then applied to everything, including text that is
not prose. Run against real shipped copy it failed `vol11_slu`'s two workout pages — the locked
exercise table PRINCIPLES Sec. 12 calls a structural contract, nine rows of
`- Name: sets × reps — cue`:

| slot | rows | mean | CV | verdict |
|---|---|---|---|---|
| `workout_p4` | 9 | 9.8 | 0.116 | **52 FAIL** |
| `workout_p5` | 9 | 10.8 | 0.085 | **44 FAIL** |

They measure as uniform because they *are* uniform: uniformity is the format. This is the same
class of error as counting em-dashes instead of counting asides — a prose-shaped rule applied
to a non-prose-shaped unit — and the fix is the same in kind: **count the governed unit**.

It was not a vol11 anomaly. All eight shipped lists measure under the floor (CV 0.085–0.157);
the six that passed did so only because their row mean sat under the 8-word staccato gate. Vol
11's rows are one to two words longer. That is the entire difference between shipping and a 44.

**The rhythm check is not disabled for list-shaped text.** Switching a check off on a shape the
writer controls is a bypass, and "put a hyphen in front of every sentence" would be a cheap one.
What changes is the *unit*: on a spec list the check measures the **longest free-text field of
each row** — the only part of a templated row that is written rather than filled. Both gates and
the CV floor are reused unchanged.

A text is a spec list only when **every** non-blank line is a row and:

| clause | why | real-copy evidence |
|---|---|---|
| ≥ 4 rows | three is a triad, four is a format (same call as `SAME_OPENER_RUN_MIN`) | every real list has 9 |
| every line opens with a bullet glyph or number enumerator | that is what "enumerated" means; one prose line and it is not a list | — |
| no row ends in terminal punctuation | a row is labelled fields, not a predication | true of all 72 real rows |
| ≥ 2 delimiters shared by every row, from `:—–×\|·→=` | one shared dash is not a template | shared core `{: × —}` on all 8 lists |

Shared *core*, not identical signature: rep ranges (`3 × 8–10`) put an en dash on some rows and
not others, and an exact per-row match would reject five of the eight real lists. The comma is
excluded from the alphabet — it is prose punctuation and it lives inside the cue field.

Why the field is the *longest* one rather than the cue after the em-dash: prose can sit in the
label as easily as in the cue, and a cue-only rule would miss it there.

**Why the exemption is safe.** Real lists clear on the staccato gate honestly — their field means
are 2.56–5.11 words against a gate of 8, and a four-word coaching cue is a caption. Adversarial
texts forced into a fully compliant spec-row skeleton do not:

| | field mean | field CV | measured? |
|---|---|---|---|
| real spec lists (6) | 2.56 – 5.11 | — | exempt, under the 8-word gate |
| slop forged into rows, prose in the cue | 9.27 – 11.57 | 0.083 – 0.274 | **fires** |
| slop forged into rows, prose in the label | 9.27 – 11.57 | 0.083 – 0.274 | **fires** |

That separation had to hold, because `adv03`, `adv10` and `adv15` carry **no tell but a flat
rhythm** — nothing else in the module catches them. Bulleting them naively does not buy the
exemption either (no shared skeleton, and with full stops kept, no row that stops being a
sentence). Detection is whole-text: prose with a table embedded in it is not a spec list and is
measured exactly as before, which is the conservative direction — the fallback for a declined
text is the shipped behaviour, not a new one.

### 6 — Repeated-opener runs

Two rules and two exemptions, because this is the check that most nearly collided with the
house voice.

* **Same first word** fires at **four**, not three. TIMBR's parallelism device is a *triad*
  (Sec. 7 names it); three parallel sentences is the device landing, four is it running on.
* **Generic class** — `This / It / These / Those / That / There` followed immediately by a verb
  — fires at **three**, because that chain is expository scaffolding rather than parallelism.
* **Anaphora exemption** (both rules): a run in which every sentence is ≤10 words is a
  rhetorical figure. Longest sentence inside a real exempt run: 8 words. Shortest inside the
  adversarial run: 11.
* **Data-listing exemption** (both rules): a run in which every sentence carries ≥2 *number
  tokens* is a spec table, not prose.
* **Each passage is priced once.** The two rules overlap by construction; a run already covered
  by an earlier one is not charged again.

---

## The dropped check — triad / rule-of-three rate

**Dropped, and the drop is the finding.** The brief asked for a threshold conservative enough
never to fire on real TIMBR copy. No such threshold exists, because the metric points the
*wrong way*: real TIMBR copy uses triads **more** than the adversarial corpus does.

Measured with prose triads only (candidates containing digits, or clauses over six words,
excluded so addresses and menu rows do not count):

| Corpus | Triads | Max paragraph saturation |
|---|---|---|
| TIMBR derivation | 25 across 114 paragraphs (0.219/para), 13 paragraphs carrying ≥1 | **0.50** |
| Adversarial derivation | 11 of 12 texts score **0.00** | **0.50** (one text) |

Any threshold at or below 0.50 fires on TIMBR before it fires on slop. Any threshold above 0.50
fires on nothing. The device is TIMBR's and the machines are not overusing it, so there is
nothing here to detect.

The detector was also imprecise, counting appositions ("a change the head of programming,
Wendell Marnowitz, described as overdue") as triads. A better detector would have to clear that
first, and it would still face the direction problem. `synth_config.DROPPED_CHECKS["triad_rate"]`
holds the note; `TestDroppedTriadCheck` re-derives the finding on every test run so it cannot
become folklore.

Also not implemented, by instruction: em-dashes (ProhibLint owns them, ruleset-aware, and it
counts *asides* rather than dashes for a reason); "is this paragraph filler / redundant"
(the editorial board's qualitative call); type-token vocabulary diversity (too noisy, punishes
concision).

---

## Scoring

```
SCORE_START     = 100
TELL            = 8            # one unit of AI-fingerprint evidence
NOISE_BUDGET    = 2            # tells a text may carry and still ship
PASS_THRESHOLD  = 100 - 2×8 = 84
```

`PASS_THRESHOLD` is **derived, not chosen**. It encodes exactly one editorial decision — the
budget — and the budget was measured:

* **Real ceiling** — the 29-text TIMBR derivation corpus carries **0 tells**. Not "few": zero,
  on all six checks.
* **AI floor** — the weakest of the 12 adversarial derivation texts (`adv10_brand_subtle`: no
  banned vocabulary, no transitions, no frames, no stacks, no runs; only a flat rhythm at
  CV 0.274) carries **3 tells**.

The corpora are separated by the interval `[0, 3)`, and 2 is the largest budget inside it that
still fails every adversarial text. It is 2 rather than 0 or 1 because every tell here is the
verdict of a regex or a summary statistic, and the failure this module must not reproduce is a
single mechanical pattern match rejecting owner-approved copy. **A budget of 2 makes
corroboration structural: no single tell can fail a text on its own.** A FAIL always needs a
second tell, or the same tell twice.

`TELL = 8` is a pure scale factor — only the ratio matters. 8 rather than 10 so the threshold
lands on 84 rather than 80: a non-round number is harder to hard-code by accident elsewhere,
the same reasoning behind VoiceLint's `PASS_THRESHOLD = 85`.

Per-check strengths (in tells): vocabulary 1 per hit · transition density 2 + 1 per extra hit ·
contrastive 2 + 1 per extra frame · hedge stack 2 each · flat rhythm 3 + 1 per 0.05 CV below the
floor · opener run 2 each.

Hard fails (unredeemable regardless of score): 5+ vocabulary hits, 3+ hedge stacks.

---

## Calibration

**Derive/validate split.** A threshold validated on the corpus it was derived from proves
nothing, so the corpora were split before any number was chosen and the held-out half was run
cold against the finished module.

| Split | Corpus | Result |
|---|---|---|
| Derivation | 29 real TIMBR texts (114 paragraphs, 400 sentences, 4,792 words) | **29/29 PASS, every one at score 100, 0 tells** |
| Derivation | 12 adversarial texts | **12/12 FAIL** (scores 0–76) |
| Held out | 6 real TIMBR texts | **6/6 PASS, every one at 100, 0 tells** |
| Held out | 4 adversarial texts | **4/4 FAIL** (scores 0–60) |
| Validation | 6 real TIMBR spec lists (`TIMBR_SPEC_LISTS`) | **6/6 PASS at 100** — see 5b; two of them scored 52 and 44 before the fix |

The two corpora do not overlap in score at all: the lowest real text is 100, the highest
adversarial is 76. `TestHeldOutCorpus::test_the_two_corpora_do_not_overlap_in_score` pins it.

**Real corpus.** 21 prose slots from `Seattle-Magazine-Engine/runs/vol11_slu/copy.py` (shipped
Vol 10 copy), all 7 sections of `sample_issue.json`, all 7 sections of
`fixtures/magazine_pass.json`. Held-out: `magazine_pass` Culture / Social / Nightlife and
`vol11` night_body / counter_cafe / anchor_cafe.

**Adversarial corpus.** 16 texts written to read like LLM fitness and lifestyle copy, varying
in severity and in which tell they carry — some vocabulary-saturated, some carrying nothing but
a flat rhythm. All 16 live as literals in `test_synthlint.py`.

Everything is held as literals in the test file rather than read from disk: these are the
measurements the thresholds were derived from, and a corpus that can change underneath the
suite is not a calibration record.

**One bug the split caught.** `CONTRASTIVE_MIN_WORDS` was first set to 120 on the reasoning
that short texts give jumpy rates. Running the finished module then showed
`adv05_contrastive` — the text written specifically to carry that tell, eight frames in it —
scoring a clean 100, because at 98 words the gate exempted it before the rate was ever
computed. It is now 40, and the incident is recorded in `synth_config` because a precondition
silently eating the positive case is the class of bug a derive/validate split exists to find.

---

## Tests

```
cd synthlint && python3 -m pytest test_synthlint.py -q     # 312 passed
python3 -m pytest -q                                        # from repo root: 1542 passed
```

312 tests: per-check positives and negatives, every exemption with the real copy that forced
it, both corpus splits as parametrised contracts, the spec-list detector clause by clause with
a counterexample isolating each, the evasion attempts, the calibration statistics recomputed on
every run, the output shape, and mutation testing.

**Mutation results.** The harness validates itself before any kill is trusted: three no-op
mutations (a trailing comment, a blank line, a docstring whitespace change) must **survive**.
They do. A `test_the_harness_finds_the_import_block_it_strips` guard fails loudly if
`synthlint.py`'s import block is reworded, which would otherwise make the harness silently load
the real module and let every mutant survive.

* **In-suite:** 41 mutants, all killed. Threshold moves in both directions, exemptions disabled,
  exemptions widened to swallow exposition, both de-duplication passes removed, segmentation
  broken, population stdev swapped for sample stdev, digits counted instead of number tokens —
  and, for the spec-list logic: every detector clause loosened and tightened past real copy, the
  shared-skeleton intersection computed as a union, `all(...)` weakened to `any(...)`, the rhythm
  unit swapped for the whole row and for the last field instead of the longest, and the
  exemption made total (an early `return [], 0, False`), which is the mutant that proves the
  field measurement is load-bearing rather than decorative.
  Two of the new mutants survived a first pass — `any(...)` and the union — because a later
  clause covered for the loosened one. Both are now killed by contract assertions that call
  `is_spec_list` directly on a text isolating that single clause, rather than only through
  verdicts. The detector's clause set is part of the contract, so a clause that stops doing
  anything is a defect even when nothing downstream notices.
* **Independent second pass** (29 further mutants not encoded in the suite, run against the full
  suite as oracle): **25/29 killed**. The 4 survivors are equivalent mutants:
  * `TELL 8→10` and `SCORE_START 100→90` — the scale factor is documented as arbitrary and
    `PASS_THRESHOLD` follows it, so every verdict is unchanged by construction.
  * `transition matcher loses its ^ anchor` — the pattern is used with `re.match()`, which
    anchors at position 0 anyway.
  * `burstiness gate uses > instead of >=` — distinguishable only by a text whose CV is exactly
    0.29 at full float precision.

---

## Known false negatives, deliberately

* A **single** contrastive pivot, a **single** paragraph-initial transition, and a **single**
  hedge stack each score but none fails a text alone. Corroboration is the design.
* A 3-run of short same-opener sentences is never flagged (anaphora), so an LLM writing short
  parallel fragments gets through Check 6. That is the price of not fighting Sec. 7.
* Texts under 8 sentences are not measured for rhythm; texts under 3 paragraphs are not rated
  for transition density; texts under 40 words are not rated for contrastive frames.
* Sections written in the staccato register (mean sentence < 8 words) are exempt from Check 5
  entirely.
* A spec list is measured on its row fields rather than its rows, so a genuine data table whose
  fields are all short (< 8 words) is exempt from Check 5 — the same call Check 6's data-listing
  exemption already makes. Reaching that exemption from prose requires rewriting every line into
  a marked, full-stop-free row filled from one delimiter skeleton, at which point the text is a
  table and not the paragraph it started as. Bulleting a paragraph does not reach it.

---

## What the rest of the repo needs

SynthLint is additive and nothing outside `synthlint/` was changed. To wire it in:

**`orchestrator.py`** — the only file that needs code.
* `import synthlint` alongside the other three.
* Magazine path (`_evaluate_magazine`): call `synthlint.run_synthlint(text)` per section and add
  `synth_pass` to the `prohib_pass and voice_pass` conjunction. Note the shape difference from
  ProhibLint and VoiceLint: `run_synthlint` takes **one string**, not a sections dict, and
  raises `TypeError` if handed a dict rather than passing silently.
* Workout Series path (`_evaluate_workout_series`): call it per prose slot beside
  `_prose_result`. No ruleset argument to thread through — that is the point.
* Scorecard: `flags["_metrics"]` carries `words / paragraphs / sentences /
  mean_sentence_words / stdev_sentence_words / burstiness_cv / total_tells`, ready to print.
* Console table: one more score column.

**`prohiblint/README.md`** — record the vocabulary boundary: `AI_BLOCKLIST` is single-word
AI-register vocabulary, `synth_config.EXTENDED_AI_VOCAB` is phrasal scaffolding, and the
de-duplication runs automatically in SynthLint's direction, so adding a term to `AI_BLOCKLIST`
is always safe and never creates a double penalty.

**`voicelint/README.md`** — record the hedge boundary: `FITT_NEGATIVE[0]` flags **one** hedge
word as a register marker; SynthLint Check 4 needs **two compounding**. They are different
defects and the overlap is intentional and bounded.

**`charlint/README.md`** — nothing. No overlap; CharLint measures geometry, SynthLint measures
prose.

**Repo `README.md`** — add SynthLint to the module list, note that it is the only linter with
**no ruleset switch**, and note that the gate is now a four-way conjunction.
