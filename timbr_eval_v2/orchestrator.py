#!/usr/bin/env python3
"""
orchestrator.py — TIMBR Eval Harness v2. Combines Tier-1 hard gates
(hardgate.py, deterministic) with Tier-2 judge output (judge_schema.py
contract, produced by an LLM briefed on RUBRIC.md) into one scorecard.

Usage:
    # Tier 1 only (no judge output yet) — fast pre-check:
    python3 orchestrator.py --text article.txt --content-type blog_training

    # Full scorecard, once a judge JSON exists:
    python3 orchestrator.py --text article.txt --content-type blog_training \\
        --judge judge_output.json --out scorecard.json
"""

import argparse
import json
import sys
from pathlib import Path

from hardgate import run_hardgate
from judge_schema import validate_judge_output, DIMENSIONS


def combine(hardgate_result, judge_output):
    """
    Applies RUBRIC.md "Overall verdict logic" exactly:
      1. Any Tier-1 blocking failure -> FAIL
      2. factual_venue_integrity = FAIL -> FAIL (non-negotiable, matches Maya's Fact Lock)
      3. Any Tier-2 dimension = FAIL -> FAIL
      4. Any Tier-2 dimension = NEEDS_REVISION -> NEEDS_REVISION
      5. Otherwise -> PASS
    """
    if hardgate_result["tier1_status"] == "FAIL":
        return "FAIL", "Tier-1 hard gate failure: " + "; ".join(
            f"{c['gate']}: {c['detail']}" for c in hardgate_result["blocking_failures"]
        )

    if judge_output is None:
        return "NEEDS_JUDGE", "Tier-1 passed. Tier-2 judge output not yet supplied."

    dims = judge_output["dimensions"]

    fact = dims.get("factual_venue_integrity", {})
    if fact.get("verdict") == "FAIL":
        return "FAIL", "Factual & Venue Integrity failed — non-negotiable per Fact Lock policy: " + fact.get("rationale", "")

    failing = [name for name in DIMENSIONS if dims.get(name, {}).get("verdict") == "FAIL"]
    if failing:
        return "FAIL", f"Tier-2 dimension(s) failed: {', '.join(failing)}"

    needs_revision = [name for name in DIMENSIONS if dims.get(name, {}).get("verdict") == "NEEDS_REVISION"]
    if needs_revision:
        return "NEEDS_REVISION", f"Tier-2 dimension(s) need revision: {', '.join(needs_revision)}"

    return "PASS", "All Tier-1 gates and Tier-2 dimensions passed."


def run_eval(text, content_type="unspecified", judge_output=None):
    hg = run_hardgate(text, content_type)

    judge_errors = []
    if judge_output is not None:
        ok, judge_errors = validate_judge_output(judge_output)
        if not ok:
            return {
                "overall": "INVALID_JUDGE_OUTPUT",
                "reason": "Judge output failed schema validation — see judge_errors.",
                "judge_errors": judge_errors,
                "hardgate": hg,
            }

    overall, reason = combine(hg, judge_output)

    return {
        "overall": overall,
        "reason": reason,
        "hardgate": hg,
        "judge": judge_output,
    }


def print_report(result):
    print("=" * 64)
    print("  TIMBR EVAL HARNESS v2")
    print("=" * 64)
    print()
    print("Tier 1 — Hard Gates")
    print(f"{'Gate':<26}{'Status':<10}{'Detail'}")
    print("-" * 64)
    for c in result["hardgate"]["checks"]:
        status = "PASS" if c["passed"] else ("FAIL" if c["blocking"] else "WARN")
        print(f"{c['gate']:<26}{status:<10}{c['detail']}")
    print()

    if result["overall"] == "INVALID_JUDGE_OUTPUT":
        print("Tier 2 — judge output failed schema validation:")
        for e in result["judge_errors"]:
            print(f"    ✗ {e}")
        print()
    elif result.get("judge"):
        print("Tier 2 — Judge Rubric")
        print(f"{'Dimension':<32}{'Score':<8}{'Verdict'}")
        print("-" * 64)
        for name in DIMENSIONS:
            d = result["judge"]["dimensions"].get(name, {})
            score = d.get("score")
            score_str = str(score) if score is not None else "n/a"
            print(f"{name:<32}{score_str:<8}{d.get('verdict', '?')}")
            if d.get("evidence"):
                for ev in d["evidence"][:2]:
                    print(f"    ↳ \"{ev}\"")
        print()
    elif result["overall"] == "NEEDS_JUDGE":
        print("Tier 2 — not yet run. Brief a judge with judge_schema.render_judge_prompt().")
        print()

    print("-" * 64)
    print(f"  OVERALL: {result['overall']}")
    print(f"  {result['reason']}")
    print("-" * 64)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TIMBR Eval Harness v2")
    parser.add_argument("--text", required=True, help="Path to the text file to grade")
    parser.add_argument("--content-type", default="unspecified")
    parser.add_argument("--judge", help="Path to judge output JSON (Tier 2). Omit to run Tier 1 only.")
    parser.add_argument("--out", help="Path to write the full scorecard JSON")
    parser.add_argument("--ci", action="store_true", help="Minimal output, exit code only")
    args = parser.parse_args()

    text = Path(args.text).read_text()
    judge_output = json.loads(Path(args.judge).read_text()) if args.judge else None

    result = run_eval(text, args.content_type, judge_output)

    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))

    if not args.ci:
        print_report(result)
    else:
        print(result["overall"])

    sys.exit(0 if result["overall"] == "PASS" else 1)
