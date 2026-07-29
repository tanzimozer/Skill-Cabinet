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

## v3 — full tonality reimagine + real photography

`live_post_v3.md` / `live_post_v3.judge.json` / `live_post_v3.scorecard.json`

Owner feedback on v2: "the article needs to be better in writing, it has to go with our
tonality. reimagine it." Rewrote every section from clean magazine-editorial prose into
[[timbr_voice]]'s actual specified register — short fragments, contractions, an edge
("That's not marketing language. That's the actual stake.") — matching the voice guide's own
gold-standard example ("The same lifts. A smarter order.") instead of approximating it.
`voice_brand_compliance` 95→97, `ai_pattern_detection` 85→90.

Also swapped all imagery: owner supplied real photos of Taylor Crow herself (confirmed rights/
permission in chat before use — these are not stock, and using an identifiable named person's
photo without that confirmation would have violated [[timbr_image_tonality]]'s no-identifiable-
face hard rule). Cover image is now a real training-floor action shot; two body portraits replace
the generic stock kettlebell/city-walk photos entirely. Overall: PASS.
