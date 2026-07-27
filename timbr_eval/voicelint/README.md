# VoiceLint — TIMBR Magazine Voice-Register Checker

VoiceLint is a lexical-only (no embeddings) voice-register linter for the
TIMBR Seattle fitness + lifestyle magazine editorial harness.

It checks whether each magazine section is written in its assigned voice
register, flags cross-contamination, and returns a numeric score with
pass/fail verdict.

---

## Voice Assignments

| Section    | Required Voice    |
|------------|-------------------|
| Training   | The Athletic      |
| Nutrition  | People Magazine   |
| Supplements| Fitt Insider      |
| Recovery   | Fitt Insider      |
| Culture    | The Athletic      |
| Social     | People Magazine   |
| Nightlife  | Fitt Insider      |

---

## Voice Fingerprints

### The Athletic
Expert, analytical, sourced journalism.

**Positive markers (+2 each hit)**
- Named source patterns: `[Name], [age],` or `[Name], [title] at [Org]`
- Statistical claims: numbers + units or %
- Reporting verbs: says, said, explains, notes, adds, argues
- Scene-setting: `At [Place]`, `In [Neighbourhood]`
- Earned rhythm: mix of short (<8 word) and long (>20 word) sentences

**Negative markers (−3 each hit)**
- Exclamation marks
- `you should` / `you can` / `you need`
- Motivational openers: Get ready, It is time, Are you

---

### People Magazine
Warm, scene-first, named-people narrative.

**Positive markers (+2 each hit)**
- Named real person in first 50 words
- Present-tense quotes (quoted speech with present-tense verb)
- Scene-first opening: paragraph opens with a person doing something
- Warm connective tissue: who, whose, her, his (with named anchor)
- Specific personal detail: age + job + neighbourhood together

**Negative markers (−3 each hit)**
- Pure data dumps with 3+ numbers and no named person
- Passive constructions without attribution
- Semicolon/bullet fact lists with no person connecting them

---

### Fitt Insider
Staccato, declarative, opinionated, data-first.

**Positive markers (+2 each hit)**
- Paragraph ≤ 40 words
- Declarative opening sentence (no subordinate clause opener)
- Number within first 5 words of a sentence
- Opinionated kicker: last sentence ≤ 12 words + strong opinion word
- No hedging words (might, could, perhaps, possibly, seems)

**Negative markers (−3 each hit)**
- Paragraphs > 80 words
- Subordinate clause openers (Although, While, Despite, However)
- Second-person wellness register (`your body`, `your recovery`, etc.)

---

## Scoring

```
score = 100 + (positive hits × 2) + (negative hits × −3)
score = clamp(score, 0, 100)
```

**Cross-contamination penalties (−10 each)**
- A Fitt Insider section that scores >5 on Athletic markers
- An Athletic section that scores >5 on People markers

**Pass threshold:** 65

---

## Usage

```python
from voicelint import lint_section, lint_sections

# Single section
result = lint_section("Training", "Marcus Webb, 34, a coach at ...")
print(result["voice_score"])   # e.g. 88
print(result["passed"])        # True / False

# Batch
results = lint_sections({
    "Training":    "...",
    "Nutrition":   "...",
    "Supplements": "...",
})
```

### Output schema (per section)

```json
{
  "voice_required":      "The Athletic",
  "voice_score":         82,
  "contamination_flags": [],
  "passed":              true,
  "_debug": {
    "primary_delta":          16,
    "contamination_penalty":   0,
    "primary_details":        ["..."],
    "athletic_delta":         16,
    "people_delta":            4,
    "fitt_delta":              8
  }
}
```

---

## Running Tests

```bash
cd /home/hermes/timbr_eval/voicelint
python -m pytest test_voicelint.py -v
```

---

## File Structure

```
voicelint/
├── voicelint.py        — Main module (lint_section, lint_sections)
├── voice_config.py     — All regex patterns, thresholds, section map
├── test_voicelint.py   — pytest suite (pass, fail, contamination, range)
└── README.md           — This file
```

---

## Dependencies

- `re` (stdlib)
- `statistics` (stdlib — available for future sentence-variance work)
- `pytest` (test runner only)

No third-party packages required.

---

## Extending

To add a new section, add an entry to `SECTION_VOICE_MAP` in `voice_config.py`:

```python
SECTION_VOICE_MAP["gear"] = "the_athletic"
```

To adjust scoring thresholds, edit constants in `voice_config.py`:

```python
PASS_THRESHOLD       = 65   # minimum passing score
POSITIVE_HIT         = 2    # points per positive marker
NEGATIVE_HIT         = -3   # points per negative marker
CONTAMINATION_TRIGGER = 5   # cross-voice score that triggers penalty
CONTAMINATION_PENALTY = -10 # penalty applied when triggered
```
