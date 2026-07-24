---
name: video-frame-extraction
category: media
description: Extracting still frames from video with ffmpeg — sampling strategies (fps / keyframe / scene-detect) and, for quality deliverables, an over-extract → sharpness-score → cull pipeline that guarantees distinct, non-blurry stills.
triggers:
  - "extract frames from video"
  - "pull stills / screenshots from a video"
  - "best frames for magazine / print / thumbnails"
  - "ffmpeg fps / scene detection"
  - "20 distinct shots / sharp frames"
---

# Video Frame Extraction

## When to use
Any request to pull still images out of a video: sampling for model/vision analysis, thumbnails, or high-quality stills for print/magazine/marketing.

## Two regimes — pick by the goal

### A) Sampling (analysis, thumbnails, overview) — use ffmpeg directly
- **Fixed rate:** `ffmpeg -i in.mp4 -vf fps=1 f_%05d.jpg` (1/sec). `fps=1/5` = one every 5s; `fps=5` = 5/sec.
  - `fps` samples on a *clock*, not on content — a static scene still yields N near-identical frames.
  - Rule: sample at least 2× faster than the shortest event you must not miss. Default `fps=1` for general video; lower for slides/lectures, higher for sport/action.
- **Keyframes only (fast, scene overview):** `-vf "select='eq(pict_type,I)'" -vsync vfr`
- **Scene-change (content-aware, distinct frames):** `-vf "select='gt(scene,0.3)'" -vsync vfr`
- Key flags: `-vsync vfr` (kills dup frames with `select` — essential), `-q:v 2` (high-quality JPEG), `-ss N -t M` before `-i` for fast seek window, PNG = lossless/large, JPEG = smaller.

### B) Quality deliverables (magazine / print / "N distinct, nothing blurry") — DO NOT trust a single ffmpeg pass
Over-extract, score, cull. `fps` is the WRONG tool here — it samples on a clock, ignores quality.

Pipeline:
1. **Extract candidates at native res, lossless.** For short clips (< a few thousand frames) just extract *every* frame: `ffmpeg -y -i in.mp4 -vsync 0 all/f_%04d.png`. For long clips, pre-filter with scene-detect first.
2. **Score each frame for sharpness** — variance-of-Laplacian (the standard blur metric). Higher = crisper. See `scripts/score_frames.py`.
3. **Select final set:** either (a) sharpest-first with a minimum frame gap to avoid near-dupes (best for max quality), or (b) divide timeline into N segments and take the sharpest per segment (best for even coverage). Coverage-mode will include soft frames if the clip has a blurry stretch — quality-mode skips them.
4. **VISUALLY VERIFY before delivering** — build a contact sheet and actually look. Sharpness math ≠ magazine-ready. `ffmpeg -y -framerate 1 -pattern_type glob -i 'shot_*.png' -vf "scale=480:-1,tile=5x4" contact_sheet.png`, then view it (browser_vision on the file://).
5. Upload winners to the requested destination.

## The honest-appraisal rule (learned the hard way)
**A clip can only contain as many distinct shots as it has distinct compositions.** An 18-second clip of one continuous action (e.g. two people jogging past camera) has ~2–4 real compositions — asking for 20 "distinct" stills yields 20 near-duplicates of the same 2–3 shots. Detect this at the contact-sheet step and TELL the user plainly rather than delivering duplicates dressed up as variety. Offer: (1) the 3–4 genuine keepers, (2) N-anyway spaced for max variety, (3) a better/longer source. Don't pad to hit a number.

## Print-resolution reality check
Magazines typically want 300 DPI — a full page needs ~8 MP. **1080p video = 2 MP**, under spec: fine for web / small placements / quarter-page, soft for full-page print. Flag source resolution up front (`ffprobe`) so the user isn't surprised at the designer.

## Probe first, always
`ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration -of default=noprint_wrappers=1 in.mp4`
Resolution, fps, and frame count decide whether "N distinct frames" is even physically possible and whether to extract-all vs. pre-filter.

## Pitfalls
- **cv2 interpreter gotcha:** `opencv-python-headless` may be installed under `python3.12` user packages while the default `python3` is a 3.11 venv without it. If `import cv2` fails with ModuleNotFoundError, run the scorer with `python3.12` explicitly (check `~/.local/lib/` for which version has it). Don't reinstall blindly.
- `execute_code` sandbox uses a different interpreter than `terminal` — cv2/opencv work ran fine via `terminal` + `python3.12`, not the sandbox.
- `-vsync vfr` (or `-vsync 0`) is mandatory with `select` filters, else you get duplicate frames.
- Scene-detect threshold: 0.3 is a good start; raise toward 0.4+ for fewer/more-distinct, lower for more candidates.
- Don't over-sample "to be safe" — you pay in storage and processing for frames nobody looks at.

## Google Drive I/O
When the source/destination is Drive, credentials live in the vault — see the `google-oauth-refresh` skill for the token-load-and-refresh pattern. Use `supportsAllDrives=True` + `includeItemsFromAllDrives=True` on list/get calls.

## References & scripts
- `scripts/score_frames.py` — variance-of-Laplacian scorer + both selection modes (sharpest-first spaced, and per-segment). Re-runnable.
