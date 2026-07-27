# ProhibLint — TIMBR Magazine Content Linter

ProhibLint is a static analysis module for the TIMBR magazine AI-content eval harness.
It scans all 7 magazine sections for prohibited content, structural violations, and
mandatory value elements.

## Sections

Training, Nutrition, Supplements, Recovery, Culture, Social, Nightlife

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

results = run_prohiblint(sections)
```

## Return Structure

```python
{
  "sections": {
    "Training": {
      "violations": ["Em-dash found: 1 instance(s). Hard fail.", ...],
      "score": 70,      # starts at 100, penalties applied, floor 0
      "passed": False,
    },
    # ... all 7 sections
  },
  "issue_level": {
    "violations": [...],
    "penalty": -50,
    "passed": False,
    "element_results": {
      "workout_plan_rep_set": True,
      "nutrition_spots_4_places": False,
      "local_fitness_spots_2": True,
      "location_features_3_places": False,
    }
  },
  "summary": {
    "total_score": 580,   # sum of section scores + issue-level penalty
    "all_passed": False,
  }
}
```

## Checks

### A — Em-dash Detector
Flags every U+2014 (—) character. Any em-dash is a **hard fail**.
Penalty: **-10 per instance**.

### B — AI Vocabulary Blocklist
Scans for 25 AI-generated prose tells:
`delve, foster, tapestry, vibrant, robust, holistic, leverage, seamless,
pivotal, transformative, unlock, elevate, revolutionize, journey, empower,
thrive, curated, game-changer, deep dive, synergy, ecosystem, impactful,
actionable, harness, spearhead`

Word-boundary, case-insensitive match. Penalty: **-5 per hit**.
**Hard fail** if 3+ hits in a single section.

### C — Fictional Cold-Open Heuristic
Checks the first paragraph (first 200 chars). Flags if:
- Word count > 30, AND
- No verified proper noun, AND
- Narrative present-tense verbs present

OR if text matches patterns like `"It is [time]..."` or `"[Name] is already..."`.
Penalty: **-15**.

### D — Second-Person Coaching Register
Patterns: `you should`, `your body`, `try this`, `you need to`, `you can`,
`you will feel`, `your workout`, `you want to`.

Case-insensitive word-boundary match. Penalty: **-3 per hit**.
Content inside `[SIDEBAR]...[/SIDEBAR]` tags is **exempt**.

### E — Word Count Range (hard binary)
| Section      | Range     |
|-------------|-----------|
| Training    | 800–1200  |
| Nutrition   | 600–900   |
| Supplements | 400–600   |
| Recovery    | 500–800   |
| Culture     | 800–1200  |
| Social      | 500–700   |
| Nightlife   | 400–600   |

Out-of-range is a **hard fail**. Penalty: **-20**.

### F — Mandatory Value Elements (issue-level)
Run across the full issue. Each missing element: penalty **-25**, issue-level fail.

| Element | Requirement |
|---------|-------------|
| Workout plan | Rep/set notation (e.g. `3x8`, `4 sets`, `reps`) |
| Nutrition spots | ≥4 named places with addresses or neighbourhoods |
| Local fitness spots | ≥2 named gyms/studios/run clubs with location |
| Location features | ≥3 place-type named entities (cafe, bar, park, restaurant + name) |

## Scoring

Each section starts at **100 points**. Penalties are subtracted; score floors at 0.
A section **passes** if: no hard fail AND score ≥ 70.
Issue-level checks pass only if all 4 mandatory elements are present.

## Running Tests

```bash
cd /home/hermes/timbr_eval/prohiblint
pytest test_prohiblint.py -v
```

## Dependencies

stdlib only: `re`, `collections` — no external packages required.
