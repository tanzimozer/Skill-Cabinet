# TIMBR Eval Harness

Automated quality gate for TIMBR magazine copy. Runs two linters — ProhibLint and VoiceLint — across all seven issue sections and produces a pass/fail scorecard.

---

## Quick Start

    cd /home/hermes/timbr_eval
    ./run_eval.sh sample_issue.json

Or directly:

    python3 orchestrator.py --issue sample_issue.json

For CI pipelines (clean output, non-zero exit on failure):

    python3 orchestrator.py --issue sample_issue.json --ci

Stop on first failure:

    python3 orchestrator.py --issue sample_issue.json --fail-fast

---

## Issue JSON Format

    {
      "issue_id": "VOL.04",
      "theme": "The Strength Issue",
      "sections": {
        "Training":    "...full section text...",
        "Nutrition":   "...full section text...",
        "Supplements": "...full section text...",
        "Recovery":    "...full section text...",
        "Culture":     "...full section text...",
        "Social":      "...full section text...",
        "Nightlife":   "...full section text..."
      }
    }

All seven sections are required.

---

## What Each Module Catches

### ProhibLint  (`prohiblint/prohiblint.py`)

Catches prohibited language and structural failures:

| Rule            | Severity | Description |
|-----------------|----------|-------------|
| `em_dash`       | blocking | Em-dash character found. Use comma, colon, or restructure the sentence. |
| `ai_vocab`      | blocking | AI/corporate vocabulary (utilize, leverage, delve, seamless, robust, etc.) |
| `banned_phrase` | blocking | Explicitly banned phrases (in conclusion, feel free to, certainly, etc.) |
| `passive_overuse` | warning | Passive voice rate exceeds 8% of word count. TIMBR voice is active. |

Also runs issue-level checks to confirm mandatory value elements (workout, recipe, tip, gear, interview) appear somewhere in the issue.

### VoiceLint  (`voicelint/voicelint.py`)

Validates voice register compliance per section. Each section has a defined profile:

| Section     | Voice Profile |
|-------------|---------------|
| Training    | Authoritative, punchy, second-person, imperative commands |
| Nutrition   | Practical, conversational, evidence-light |
| Supplements | Cautious, factual, evidential language required |
| Recovery    | Warm, empathetic, sensory |
| Culture     | Editorial, opinionated, referential |
| Social      | Casual, first-person plural, community-forward |
| Nightlife   | Playful, sensory-rich, present-tense |

Sections scoring below 70 fail voice lint.

---

## Scorecard Output

### Console (standard mode)

A formatted table is printed to stdout:

    Section        Voice  Prohib   Status
    -------------- ------  ------- --------
    Training          100      100    PASS
    Nutrition         100      100    PASS
    Supplements       100       90    PASS
    Recovery          100      100    PASS
    Culture           100      100    PASS
    Social            100      100    PASS
    Nightlife          70       55    FAIL

Followed by a list of blocking violations and issue-level check results.

### JSON Output

Written to `results/[issue_id]_scorecard.json`:

    {
      "issue_id": "VOL.04",
      "theme": "The Strength Issue",
      "overall": "PASS" or "FAIL",
      "timestamp": "2026-07-27T...",
      "sections": {
        "Training": {
          "voice_score": 100,
          "voice_passed": true,
          "voice_issues": [],
          "prohib_score": 100,
          "prohib_passed": true,
          "violations": [],
          "status": "PASS"
        },
        ...
      },
      "blocking_violations": [...],
      "issue_level_checks": {
        "workout": true,
        "recipe": false,
        "tip": true,
        "gear": false,
        "interview": false
      }
    }

### Exit Codes

| Code | Meaning |
|------|---------|
| 0    | All sections pass |
| 1    | One or more sections fail (or input error) |

---

## CI Integration

    python3 orchestrator.py --issue issue.json --ci
    # Prints: violations + PASS or FAIL
    # Exit code 1 on any failure

Example GitHub Actions step:

    - name: TIMBR Eval
      run: python3 timbr_eval/orchestrator.py --issue issue.json --ci

---

## File Structure

    timbr_eval/
    ├── orchestrator.py          # Main harness — wires everything together
    ├── run_eval.sh              # Shell convenience wrapper
    ├── sample_issue.json        # Sample issue with deliberate failures in Nightlife
    ├── README.md                # This file
    ├── __init__.py
    ├── prohiblint/
    │   ├── __init__.py
    │   └── prohiblint.py        # Prohibited language + structure linter
    ├── voicelint/
    │   ├── __init__.py
    │   └── voicelint.py         # Voice register linter
    └── results/                 # Auto-created; scorecard JSON files land here
