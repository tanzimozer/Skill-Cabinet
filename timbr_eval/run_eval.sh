#!/bin/bash
python3 "$(dirname "$0")/orchestrator.py" --issue "$1" "${@:2}"
