"""SynthLint — AI-fingerprint detection for the TIMBR eval harness.

Catches the textual tells of machine-written prose. Runs universally: there is
no ruleset switch, because reading like an LLM is a defect on every product
line.

    from synthlint import run_synthlint
    run_synthlint(text)  -> {"violations": [...], "score": int,
                             "passed": bool, "flags": {...}}

The package re-exports the whole surface of synthlint.synthlint, including the
segmentation and detector helpers. That is deliberate rather than incidental:
`timbr_eval/synthlint/test_synthlint.py` is collected as `synthlint.
test_synthlint` from the repo root, which imports THIS module first, so a
narrow __init__ would make the suite pass under `cd synthlint && pytest` and
fail under repo-root pytest. One import surface, both ways in.
"""

from . import synth_config, synthlint                       # noqa: F401
from .synthlint import (                                    # noqa: F401
    CHECKS,
    burstiness,
    check_ai_vocabulary,
    check_burstiness,
    check_contrastive_frames,
    check_hedge_stacking,
    check_repeated_openers,
    check_transition_density,
    contrastive_frames,
    hedge_stacks,
    is_spec_list,
    repeated_opener_runs,
    run_synthlint,
    spec_list_fields,
    spec_list_rows,
    split_paragraphs,
    split_sentences,
    transition_openers,
    word_count,
)
from .synth_config import (                                 # noqa: F401
    DROPPED_CHECKS,
    NOISE_BUDGET,
    PASS_THRESHOLD,
    SCORE_START,
    TELL,
)

__all__ = [
    "run_synthlint",
    "CHECKS",
    "check_ai_vocabulary",
    "check_transition_density",
    "check_contrastive_frames",
    "check_hedge_stacking",
    "check_burstiness",
    "check_repeated_openers",
    "burstiness",
    "contrastive_frames",
    "hedge_stacks",
    "repeated_opener_runs",
    "transition_openers",
    "is_spec_list",
    "spec_list_rows",
    "spec_list_fields",
    "split_sentences",
    "split_paragraphs",
    "word_count",
    "DROPPED_CHECKS",
    "NOISE_BUDGET",
    "PASS_THRESHOLD",
    "SCORE_START",
    "TELL",
]
