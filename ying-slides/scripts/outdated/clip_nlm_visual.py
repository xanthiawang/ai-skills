#!/usr/bin/env python3
"""
Content-aware clipping of NotebookLM slide visuals.

Extracts ONLY the diagram/visual — removes slide title and NLM watermark.
Supports both single-block and two-column layouts.

Algorithm:
  1. Find content bands in the top 40% — title = 2nd band (1st is section label)
  2. Cut at the gap after the title band (top crop)
  3. Bottom: widest gap in bottom 20% (removes NLM watermark)
  4. Column detection: scan for a vertical whitespace gap in the cropped region
  5. If two-column detected, extract the right column (figure side)
  6. ALL cut lines verified: the pixels along each cut must be near-white

Usage:
  python clip_nlm_visual.py input.png output.png [--pad 8] [--columns auto]
  python clip_nlm_visual.py slide_dir/ output_dir/ [--pad 8] [--columns auto]

  --columns auto   Detect layout automatically (default)
  --columns full   Always keep full width
  --columns right  Always extract right column
  --columns left   Always extract left column
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("pip install Pillow numpy", file=sys.stderr)
    sys.exit(1)


def row_density(arr, white_thresh=240):
    """Fraction of non-white pixels per row."""
    return np.any(arr < white_thresh, axis=2).mean(axis=1)


def col_density(arr, white_thresh=240):
    """Fraction of non-white pixels per column."""
    return np.any(arr < white_thresh, axis=2).mean(axis=0)


def find_gaps(density, min_width=4, threshold=0.015):
    """Find all whitespace gaps (runs of low-density values)."""
    gaps = []
    in_gap = False
    start = 0
    for i, d in enumerate(density):
        if d < threshold and not in_gap:
            start = i
            in_gap = True
        elif d >= threshold and in_gap:
            if i - start >= min_width:
                gaps.append((start, i, i - start))
            in_gap = False
    if in_gap and len(density) - start >= min_width:
        gaps.append((start, len(density), len(density) - start))
    return gaps


def cut_line_is_clean(arr, axis, position, margin=3, white_thresh=240):
    """
    Verify that a cut line passes through near-white pixels only.
    axis=0 means horizontal cut (check a row band), axis=1 means vertical cut (check a column band).
    Returns True if the cut line region is clean (all near-white).
    """
    if axis == 0:
        # Horizontal cut: check rows around position
        h = arr.shape[0]
        y0 = max(0, position - margin)
        y1 = min(h, position + margin)
        band = arr[y0:y1, :, :]
    else:
        # Vertical cut: check columns around position
        w = arr.shape[1]
        x0 = max(0, position - margin)
        x1 = min(w, position + margin)
        band = arr[:, x0:x1, :]
    # Clean if <2% of pixels are non-white
    non_white_frac = np.any(band < white_thresh, axis=2).mean()
    return non_white_frac < 0.02


def find_clean_cut(arr, axis, position, direction, max_search=80, margin=3, white_thresh=240):
    """
    Starting from position, search in direction (+1 or -1) for a clean cut line.
    Returns the first position where the cut line is clean, or the original position if none found.
    """
    limit = arr.shape[0] if axis == 0 else arr.shape[1]
    for offset in range(0, max_search):
        candidate = position + offset * direction
        if candidate < 0 or candidate >= limit:
            break
        if cut_line_is_clean(arr, axis, candidate, margin, white_thresh):
            return candidate
    return position


def detect_column_split(arr, white_thresh=240):
    """
    Detect if the content region has a two-column layout by finding a vertical
    whitespace gap in the middle 25%-75% of the image width.

    Returns (split_x, gap_width) if found, or (None, 0) if single-block layout.
    The split_x is the center of the gap.
    """
    w = arr.shape[1]
    density = col_density(arr, white_thresh)

    # Only look for gaps in the middle portion (25%-75% of width)
    search_start = int(w * 0.25)
    search_end = int(w * 0.75)

    # Find vertical gaps (columns of whitespace) with minimum width
    gaps = []
    in_gap = False
    start = 0
    threshold = 0.02  # columns with <2% non-white pixels are "empty"
    min_gap_width = int(w * 0.02)  # gap must be at least 2% of width

    for i in range(search_start, search_end):
        if density[i] < threshold and not in_gap:
            start = i
            in_gap = True
        elif density[i] >= threshold and in_gap:
            if i - start >= min_gap_width:
                gaps.append((start, i, i - start))
            in_gap = False
    if in_gap and search_end - start >= min_gap_width:
        gaps.append((start, search_end, search_end - start))

    if not gaps:
        return None, 0

    # Pick the widest gap in the middle zone
    best = max(gaps, key=lambda g: g[2])
    center = (best[0] + best[1]) // 2
    return center, best[2]


def clip_visual(input_path, output_path, pad=8, columns="auto"):
    """
    Content-aware clip: removes title and watermark, keeps diagram.
    Handles both single-block and two-column layouts.
    """
    img = Image.open(input_path).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    density = row_density(arr)
    gaps = find_gaps(density)

    # --- TOP: find title (2nd content band), cut after its gap ---
    top_content = []
    in_c = False
    start = 0
    for i in range(min(int(h * 0.40), h)):
        is_c = density[i] >= 0.015
        if is_c and not in_c:
            start = i
            in_c = True
        elif not is_c and in_c:
            top_content.append((start, i, i - start))
            in_c = False
    if in_c:
        top_content.append((start, int(h * 0.40), int(h * 0.40) - start))

    if len(top_content) >= 2:
        title_band = top_content[1]
        title_end = title_band[1]
        post_gaps = [g for g in gaps if g[0] >= title_end - 2 and g[2] >= 5]
        top_y = post_gaps[0][1] if post_gaps else title_end
    elif len(top_content) == 1:
        title_end = top_content[0][1]
        post_gaps = [g for g in gaps if g[0] >= title_end - 2 and g[2] >= 5]
        top_y = post_gaps[0][1] if post_gaps else title_end
    else:
        top_y = int(h * 0.18)

    # --- BOTTOM: widest gap in bottom 20% ---
    bottom_gaps = [g for g in gaps if g[1] > h * 0.80]
    if bottom_gaps:
        wm_gap = max(bottom_gaps, key=lambda g: g[2])
        bottom_y = wm_gap[0]
    else:
        bottom_y = int(h * 0.95)

    # Verify top/bottom cuts are clean (no content on the cut line)
    top_y = find_clean_cut(arr, axis=0, position=top_y, direction=-1)
    bottom_y = find_clean_cut(arr, axis=0, position=bottom_y, direction=1)

    # Sanity: content should be >= 30% of image
    method = "auto"
    if (bottom_y - top_y) < h * 0.30:
        top_y, bottom_y = int(h * 0.18), int(h * 0.95)
        method = "fallback"

    # Apply vertical padding
    top_y = max(0, top_y - pad)
    bottom_y = min(h, bottom_y + pad)

    # --- COLUMN DETECTION ---
    left_x = 0
    right_x = w
    col_method = "full"

    if columns != "full":
        # Analyze the content region (after top/bottom crop) for vertical split
        content_region = arr[top_y:bottom_y, :, :]
        split_x, gap_w = detect_column_split(content_region)

        if split_x is not None and (columns in ("right", "auto")):
            # Cut at the CENTER of the gap (guaranteed clean)
            cut_x = split_x
            if cut_line_is_clean(content_region, axis=1, position=cut_x, margin=4):
                left_x = cut_x
                col_method = "right"
            else:
                # Shouldn't happen (center of detected gap), but search nearby
                clean_x = find_clean_cut(content_region, axis=1, position=cut_x, direction=1, max_search=gap_w // 2)
                if cut_line_is_clean(content_region, axis=1, position=clean_x, margin=4):
                    left_x = clean_x
                    col_method = "right-adjusted"

        elif split_x is not None and columns == "left":
            cut_x = split_x
            if cut_line_is_clean(content_region, axis=1, position=cut_x, margin=4):
                right_x = cut_x
                col_method = "left"
            else:
                clean_x = find_clean_cut(content_region, axis=1, position=cut_x, direction=-1, max_search=gap_w // 2)
                if cut_line_is_clean(content_region, axis=1, position=clean_x, margin=4):
                    right_x = clean_x
                    col_method = "left-adjusted"

    # Apply horizontal padding
    if left_x > 0:
        left_x = max(0, left_x - pad)
    if right_x < w:
        right_x = min(w, right_x + pad)

    cropped = img.crop((left_x, top_y, right_x, bottom_y))
    cropped.save(output_path)

    return {
        "method": method,
        "col_method": col_method,
        "top": top_y, "bottom": bottom_y,
        "left": left_x, "right": right_x,
        "crop_h": bottom_y - top_y,
        "crop_w": right_x - left_x,
        "orig_h": h, "orig_w": w,
    }


def main():
    parser = argparse.ArgumentParser(description="NLM visual clipper")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--pad", type=int, default=8)
    parser.add_argument("--columns", choices=["auto", "full", "right", "left"],
                        default="auto",
                        help="Column extraction mode: auto detects layout, "
                             "full keeps entire width, right/left forces column")
    args = parser.parse_args()

    inp, out = Path(args.input), Path(args.output)

    if inp.is_dir():
        out.mkdir(parents=True, exist_ok=True)
        for f in sorted(list(inp.glob("*.png")) + list(inp.glob("*.jpg"))):
            info = clip_visual(f, out / f.name, args.pad, args.columns)
            print(f"{f.name}: [{info['method']}+{info['col_method']}] "
                  f"({info['crop_w']}x{info['crop_h']}) "
                  f"x={info['left']}..{info['right']} "
                  f"y={info['top']}..{info['bottom']}")
    else:
        info = clip_visual(inp, out, args.pad, args.columns)
        print(f"[{info['method']}+{info['col_method']}] "
              f"({info['crop_w']}x{info['crop_h']}) → {out}")


if __name__ == "__main__":
    main()
