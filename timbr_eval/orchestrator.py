#!/usr/bin/env python3
# orchestrator.py — TIMBR Eval Harness Orchestrator
# Wires ProhibLint + VoiceLint, emits scorecard JSON + stdout table.
# Usage: python3 orchestrator.py --issue issue.json [--ci] [--fail-fast]

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add module paths
sys.path.insert(0, str(Path(__file__).parent / "prohiblint"))
sys.path.insert(0, str(Path(__file__).parent / "voicelint"))

import prohiblint
import voicelint


def run_eval(issue_path: str, ci: bool = False, fail_fast: bool = False) -> dict:
    with open(issue_path) as f:
        issue = json.load(f)

    issue_id = issue.get("issue_id", "UNKNOWN")
    sections = issue.get("sections", {})

    if not ci:
        print(f"\n{'='*60}")
        print(f"  TIMBR EVAL HARNESS — {issue_id}")
        print(f"  Theme: {issue.get('theme', 'N/A')}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")

    # Run modules
    prohib_raw = prohiblint.run_prohiblint(sections)
    prohib_section_results = prohib_raw.get("sections", {})
    prohib_issue_level = prohib_raw.get("issue_level", {})
    voice_results = voicelint.run(sections)

    # Build scorecard
    section_scores = {}
    all_violations = []
    any_failed = False

    for section in sections:
        p = prohib_section_results.get(section, {})
        v = voice_results.get(section, {})

        prohib_pass = p.get("passed", True)
        voice_pass = v.get("passed", True)
        section_pass = prohib_pass and voice_pass

        if not section_pass:
            any_failed = True

        p_violations = p.get("violations", [])
        violations = p_violations + v.get("contamination_flags", [])
        all_violations.extend(violations)

        section_scores[section] = {
            "voice_score": v.get("voice_score", 0),
            "voice_passed": voice_pass,
            "prohib_score": p.get("score", 100),
            "prohib_passed": prohib_pass,
            "violations": violations,
            "status": "PASS" if section_pass else "FAIL",
        }

        if fail_fast and not section_pass:
            if not ci:
                print(f"FAIL-FAST: {section} failed. Stopping.")
            break

    # Issue-level checks
    issue_checks = prohib_issue_level

    scorecard = {
        "issue_id": issue_id,
        "overall": "FAIL" if any_failed else "PASS",
        "sections": section_scores,
        "blocking_violations": all_violations[:10],
        "issue_level_checks": issue_checks,
        "generated_at": datetime.now().isoformat(),
    }

    # Print table
    if not ci:
        print(f"{'Section':<14} {'Voice':>6} {'Prohib':>7} {'Status':>8}")
        print(f"{'-'*14} {'-'*6} {'-'*7} {'-'*8}")
        for sec, res in section_scores.items():
            status_icon = "✅" if res["status"] == "PASS" else "❌"
            print(f"{sec:<14} {res['voice_score']:>5}  {res['prohib_score']:>6}  {status_icon} {res['status']}")

        print(f"\n{'─'*60}")
        print(f"  OVERALL: {scorecard['overall']}")
        if any_failed:
            print(f"  TOP VIOLATIONS:")
            for v in all_violations[:3]:
                print(f"    • {v}")
        print(f"{'─'*60}\n")
    else:
        # CI mode: only violations + final result
        if any_failed:
            for sec, res in section_scores.items():
                if res["status"] == "FAIL":
                    for v in res["violations"][:3]:
                        print(f"[{sec}] {v}")
        print(scorecard["overall"])

    # Write results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f"{issue_id.replace('.', '_')}_scorecard.json"
    with open(out_path, "w") as f:
        json.dump(scorecard, f, indent=2)

    if not ci:
        print(f"Scorecard written: {out_path}")

    return scorecard


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TIMBR Eval Harness")
    parser.add_argument("--issue", required=True, help="Path to issue.json")
    parser.add_argument("--ci", action="store_true", help="CI mode: minimal output")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    args = parser.parse_args()

    scorecard = run_eval(args.issue, ci=args.ci, fail_fast=args.fail_fast)
    sys.exit(0 if scorecard["overall"] == "PASS" else 1)
