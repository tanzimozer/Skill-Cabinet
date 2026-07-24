#!/usr/bin/env python3.12
"""Score extracted frames for sharpness (variance-of-Laplacian) and select a
final set. Two modes:

  sharpest   — top-N sharpest frames, deduplicated by a minimum frame gap
               (best for max quality; may cluster around sharp windows)
  segment    — divide timeline into N segments, sharpest per segment
               (best for even coverage; will include soft frames if the clip
                has a blurry stretch)

USAGE:
  python3.12 score_frames.py <frames_dir> [N] [mode] [min_gap]
    frames_dir : dir of extracted frames (png/jpg)
    N          : how many to select (default 20)
    mode       : sharpest | segment (default sharpest)
    min_gap    : min frame-index spacing in sharpest mode (default 8)

IMPORTANT: run with python3.12 if cv2 is only installed for 3.12 (see SKILL.md
"cv2 interpreter gotcha"). Writes picks.txt (rank<TAB>path<TAB>sharpness) and
copies selections to <frames_dir>/../selected/shot_NN.png.
"""
import cv2, glob, os, sys, shutil
import numpy as np

frames_dir = sys.argv[1] if len(sys.argv) > 1 else "all_frames"
N          = int(sys.argv[2]) if len(sys.argv) > 2 else 20
mode       = sys.argv[3] if len(sys.argv) > 3 else "sharpest"
MIN_GAP    = int(sys.argv[4]) if len(sys.argv) > 4 else 8

frames = sorted(
    glob.glob(os.path.join(frames_dir, "*.png"))
    + glob.glob(os.path.join(frames_dir, "*.jpg"))
)
if not frames:
    sys.exit(f"No frames found in {frames_dir}")

scores = []
for i, fp in enumerate(frames):
    g = cv2.imread(fp, cv2.IMREAD_GRAYSCALE)
    scores.append((i, fp, cv2.Laplacian(g, cv2.CV_64F).var()))

vals = [s[2] for s in scores]
print(f"Frames: {len(scores)}  sharpness min {min(vals):.0f} "
      f"median {np.median(vals):.0f} max {max(vals):.0f}")

if mode == "segment":
    seg = len(scores) / N
    picks = [max(scores[int(k*seg):int((k+1)*seg)], key=lambda s: s[2])
             for k in range(N)]
else:  # sharpest-first, deduplicated by min frame gap
    picks = []
    for idx, fp, lap in sorted(scores, key=lambda s: -s[2]):
        if all(abs(idx - p[0]) >= MIN_GAP for p in picks):
            picks.append((idx, fp, lap))
        if len(picks) == N:
            break
    picks.sort(key=lambda s: s[0])

sel_dir = os.path.join(os.path.dirname(frames_dir.rstrip("/")) or ".", "selected")
os.makedirs(sel_dir, exist_ok=True)
picks_txt = os.path.join(os.path.dirname(frames_dir.rstrip("/")) or ".", "picks.txt")
with open(picks_txt, "w") as f:
    for k, (idx, fp, lap) in enumerate(picks, 1):
        shutil.copy(fp, os.path.join(sel_dir, f"shot_{k:02d}.png"))
        f.write(f"{k}\t{fp}\t{lap:.0f}\n")
        print(f"{k:2d}. frame {idx:4d}  sharp={lap:6.0f}")

sp = [p[2] for p in picks]
print(f"\nSelected {len(picks)} ({mode}): sharpness min {min(sp):.0f} "
      f"median {np.median(sp):.0f} max {max(sp):.0f}")
print(f"picks -> {picks_txt}\ncopies -> {sel_dir}")
print("NEXT: build a contact sheet and VISUALLY verify before delivering:")
print("  ffmpeg -y -framerate 1 -pattern_type glob -i "
      f"'{sel_dir}/shot_*.png' -vf \"scale=480:-1,tile=5x4\" contact_sheet.png")
