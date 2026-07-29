# First real production run — Inside Taylor Crow Studio

The first time v2 ran against real (not synthetic) copy already live on seattlefitnessmag.com,
after the calibration pair in `../../calibration/` had already proven it discriminates.

## v1 pass — NEEDS_REVISION

`live_post.md` / `live_post_v1.judge.json` / `live_post_v1.scorecard.json`

Tier 1: clean PASS (814 words, no banned vocab, no em-dash).
Tier 2: `factual_venue_integrity` and `ai_pattern_detection` both scored NEEDS_REVISION:

- The two body images' alt text read as documentary claims ("representing Taylor Crow Studio's
  actual X") when both are generic stock photos — one of them a visibly non-Seattle streetscape.
  Ambiguous alt text like this is exactly what [[timbr_venue_preflight]]'s honest-generic standard
  exists to prevent.
- The piece's closing sentence was a textbook rule-of-three/tricolon ("X enough..., Y enough...,
  Z enough...") landing in the single most visible spot in the piece — the AI-pattern gate's
  reason for existing.

This run also caught two bugs in the harness itself while it was running for real, not just
against synthetic calibration text: `orchestrator.py`'s `print_report()` crashed with a raw
`KeyError` on `INVALID_JUDGE_OUTPUT` instead of reporting validation errors (fixed — see the
same commit), and my own first judge JSON left `seattle_local_specificity`'s evidence array
empty at a sub-100 score, which the schema validator correctly rejected.

## Fixes applied

1. Rewrote the closing sentence — cut the tricolon, replaced it with two short sentences ending
   on a new, concrete detail instead of restating earlier facts.
2. Rewrote both images' alt text to explicitly say "illustrative" / "stand-in" rather than
   implying the photos document the real business.
3. Repositioned the kettlebell/equipment image from after "Private, by design" to directly after
   "The studio" — the section that actually mentions equipment.

## v2 pass — PASS

`live_post_v2.md` / `live_post_v2.judge.json` / `live_post_v2.scorecard.json`

All three previously-flagged issues resolved; `factual_venue_integrity` 60→92,
`ai_pattern_detection` 62→85, `structural_format_compliance` 92→100. Overall: PASS.

Live post: https://www.seattlefitnessmag.com/post/inside-taylor-crow-studio-madrona-s-training-ground-for-every-stage-of-a-woman-s-life
