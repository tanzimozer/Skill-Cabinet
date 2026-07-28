#!/bin/bash
# run_eval.sh — convenience wrapper around orchestrator.py.
#
# Usage:
#   ./run_eval.sh <issue.json> [--ci] [--fail-fast]
#                              [--ruleset magazine|workout_series]
#                              [--locks <locks.json>] [--out-dir <dir>]
#
# The first argument is the issue file; every remaining argument is forwarded
# to orchestrator.py untouched, so new flags need no change here.
#
# Exit codes are the orchestrator's: 0 PASS, 1 FAIL, 2 usage/config error.
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: $(basename "$0") <issue.json> [--ci] [--fail-fast]" >&2
  echo "       [--ruleset magazine|workout_series] [--locks <locks.json>] [--out-dir <dir>]" >&2
  exit 2
fi

exec python3 "$(dirname "$0")/orchestrator.py" --issue "$1" "${@:2}"
