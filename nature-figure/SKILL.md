---
name: nature-figure
description: "Use when creating ANY scientific figure for publication, including assembling a vectorized composite/multi-panel PDF with a/b/c panel index labels. Covers single-panel and multi-panel layouts, subplot_mosaic compositing, raster image stitching and true-vector PDF compositing (PyMuPDF), and a mandatory AI visual review loop that checks for overlaps, ink-to-canvas ratio, text legibility, and layout tightness — auto-fixing issues up to 3 iterations."
---

# Nature-Style Scientific Figures

## Overview

Create publication-quality scientific figures with an AI visual review loop. Every figure — single-panel or multi-panel — goes through a render-review-fix cycle that checks for overlapping elements, poor ink-to-canvas ratio, text legibility, and wasted whitespace.

## When to Use

- Plotting REAL data: any figure where the points, bars, curves, or cells come
  from an actual dataset (CSV, parquet, arrays computed from data)
- Combining different plot types into multi-panel composites
- Needing panels that span multiple rows/columns
- Stitching pre-existing figure images into a composite
- Any time a matplotlib figure of real data needs to look publication-ready

## When NOT to Use — Concept Figures Go to Codex ImageGen

**Concept / schematic / diagram figures ALWAYS use the Codex `imagegen` skill,
NEVER nature-figure.** This skill is for plotting real data with matplotlib.

Route to `imagegen` (start the Codex prompt with `$imagegen` on its own line)
for: study-design schematics, model/pipeline architecture diagrams, training
objectives, workflow/flowcharts, mechanism cartoons, slide visuals, and any
illustrative graphic with no real data behind it. Use a white background unless
asked otherwise.

### HARD RULE: ImageGen figures carry the SAME Ying Lab palette

The visual identity does not stop at matplotlib. Every `imagegen` prompt for a
concept figure MUST embed the exact lab hex values and the semantic role
mapping, so concept figures and data figures read as one system:

- **RUST `#B3796D`** — hero: treatment, intervention, Socratic, main finding
- **BLUE `#7689A0`** — alternative: direct/plain assistant, comparison condition
- **GRAY `#8E8680`** — neutral: control, baseline, system components (detectors,
  loggers), no-AI
- **INK `#181114`** for text/arrows; accents from GOLD `#A08344` / SAGE `#5C8F82`
  only when a 4th/5th role genuinely exists

Prompt requirements (paste into every imagegen figure prompt):
1. Name the hex codes explicitly next to each element ("the Socratic boxes in
   muted rust #B3796D") — current image models follow explicit hexes well;
   vague words like "terracotta" come back oversaturated.
2. Say "low-saturation, muted academic palette; flat fills; no gradients".
3. Keep one color = one role across ALL figures of the same paper (e.g. if
   Direct condition is BLUE in the design figure, the direct-reply box in the
   pipeline figure is BLUE too — never let the same hue play two roles).
4. State exact text labels and mark them CRITICAL; English labels render
   reliably, Chinese text does not — write dialogue/mockups in English or
   composite Chinese text as a vector layer.

After generation, verify against the checklist: labels exact, one-color-one-role,
saturation comparable to the matplotlib figures when placed side by side.

If a "concept" figure must also show real numbers/curves, generate the
schematic with `imagegen` and composite the real-data panels (made here with
matplotlib) over it — never let `imagegen` draw fabricated data points, bars, or
curves.

### Exception: editable ML/AI method figures go to `academic-figures-drawer`

When the figure is a model or method diagram for an ML/HCI venue (framework
overview, module detail, tensor/attention flow, training vs inference pipeline,
agent architecture) AND it must be editable vector for camera-ready revision,
use the `academic-figures-drawer` skill (draw.io XML as source of truth, PNG/PDF
derived, static validators plus screenshot review loop). Its optional concept
pass is where `imagegen` still fits: generate a no-text composition reference
first, then redraw the semantics as vectors. Vendored from
`github.com/M1n-n9/academic-figures-drawer` at `b2661ea` (2026-10-07).

Override its default palette with the lab palette so draw.io figures match the
matplotlib panels: paper contribution / hero = RUST `#B3796D` (2–3 px stroke);
standard or prior components = GRAY `#8E8680`; alternative or comparison path =
BLUE `#7689A0`; text, arrows and main flow = INK `#181114`; GOLD `#A08344` /
SAGE `#5C8F82` only for a genuine 4th/5th role. Keep its other rules (one
restrained accent, legend for every color, paper-scale type checks).

On this Mac: run its scripts with `python3` (the SKILL.md shows Windows
PowerShell paths); PNG/PDF export needs the draw.io desktop CLI
(`/Applications/draw.io.app/Contents/MacOS/draw.io`) and `autolayout.py` needs
Graphviz `dot`. Both installed via Homebrew on 2026-10-07 (draw.io 31.7.0,
Graphviz 16.1.0); the validate → CLI export → `repair_png.py` chain was tested
end to end on this machine.

## Style Setup (REQUIRED)

Every figure script MUST call `retro_style()` once at the top. This applies the Ying Lab visual identity: floating trimmed spines, outward ticks, no minor ticks, warm mauve ink (#705B66), warm linen background (#EEEAE0), Arial font. Pure matplotlib — no external theme packages.

```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from nature_figure_utils import (
    retro_style, trim_axes, figsize_nature, save_for_review,
    find_best_legend_loc, smart_annotate, place_stat_text,
    scatter_outlined, pad_categorical_axis, BG_COLORS,
    RUST, GRAY, BLUE, GOLD, SAGE, PLUM,  # color families
    INK, BG, ALPHA, FAMILIES,            # identity constants
    CMAP_RUST, CMAP_BLUE, CMAP_DIVERGE,  # custom colormaps
)

# Apply consistent style BEFORE creating any figures
colors = retro_style()                          # signature palette (default)
# colors = retro_style("primary")               # rust + gray shades only
# colors = retro_style("grayscale")             # grayscale gradient
# colors = retro_style(["#E41A1C", "#377EB8"])  # custom list
```

### CRITICAL: Trim Ordering

After all plotting is done, you MUST call `trim_axes()` for scatter plots and bar plots. This trims spines to the tick range (ggplot/base-R style): spines ALWAYS end at a tick mark, and ticks NEVER exist outside the spine line. If data extends beyond current ticks, new ticks are added at regular spacing. Log-scale axes generate ticks at powers of 10, extending outward when the axis limits extend past the nearest power-of-10 tick so the spine always covers the full visible data range. Call BEFORE any axis rotation or manipulation:

```python
# 1. Do all plotting first
ax.scatter(x, y, ...)
ax.set_xlabel("X Label")
ax.set_ylabel("Y Label")

# 2. Trim axes (floating spines)
trim_axes()

# 3. ONLY AFTER trim_axes(): do any rotation or axis actions
plt.xticks(rotation=45, ha="right")  # rotation MUST come after trim_axes()
ax.tick_params(...)                   # axis actions MUST come after trim_axes()
```

**When to skip trimming:** Heatmaps, clustermaps, and other grid-based plots where trimmed spines don't make sense. For these, do NOT call `trim_axes()`. For heatmaps specifically, reset to vanilla matplotlib using `mpl.rc_context()` + `mpl.rcdefaults()` (see Heatmap recipe).

**Histograms and density plots:** In multi-panel figures that mix histograms with scatter/bar plots, ALWAYS exclude histogram axes from `trim_axes()` using the `exclude` parameter: `trim_axes(fig, exclude=[ax_hist1, ax_hist2])`. Trimmed spines on histograms create dead space above the tallest bar where legends and annotations float disconnected from the data. Histograms don't benefit from trimmed spines — their bars fill the axis continuously.

Violating this order causes the trim to override your rotations/adjustments.

## Figure Dimensions

Use Nature's exact column widths. `figsize_nature()` returns `(width, height)` in inches.

| Column type | Width | Usage |
|-------------|-------|-------|
| `"single"` | 3.50 in (89 mm) | Single-column figures |
| `"1.5col"` | 4.72 in (120 mm) | Intermediate figures |
| `"double"` | 7.20 in (183 mm) | Full-width figures |

```python
fig, ax = plt.subplots(figsize=figsize_nature("single"), layout="constrained")
fig, axd = plt.subplot_mosaic(..., figsize=figsize_nature("double", aspect=0.6), layout="constrained")
```

The `aspect` parameter controls height/width ratio (default 0.75). Maximum height is 9.72 in (247 mm).

## Color System — Ying Lab Signature Palette

### Design Philosophy

The Ying Lab style is warm, low-saturation, and semantically consistent. Colors have MEANING — they're not decorative. The same color always means the same thing across all figures from the lab.

### Six Families (100–600 shades each)

Every family has 6 shades from lightest (100) to darkest (600). The 300 shade is the default mid-tone, and all 300s are **luminance-equalized** so no color appears brighter or darker than another at equal shade level.

```
Family   300 hex    Semantic role                               When to use
──────────────────────────────────────────────────────────────────────────────
RUST     #B3796D    Hero — treatment, significant, main finding  80% of the time
GRAY     #8E8680    Neutral — control, baseline, non-significant 80% of the time
BLUE     #7689A0    Down-regulated, cold, alternative condition  Extended hue
GOLD     #A08344    Third condition, highlight, warning           Extended hue
SAGE     #5C8F82    Biological, growth, positive (colorblind-safe) Extended hue
PLUM     #94838F    Fifth condition, decorative (use sparingly)  Extended hue
```

### Color Assignment Rules

| Scenario | Colors |
|----------|--------|
| 1 group | `RUST["300"]` |
| 2 groups (ctrl / treat) | `GRAY["200"]` + `RUST["300"]` or `RUST["400"]` |
| 3 groups | `GRAY["200"]` + `RUST["300"]` + `BLUE["300"]` |
| 5+ categories | `GRAY["300"]`, `RUST["300"]`, `BLUE["300"]`, `GOLD["300"]`, `SAGE["300"]` |
| Volcano (up/down/ns) | `RUST["400"]` up, `BLUE["300"]` down, `GRAY["100"]` ns |
| Paired before/after | Same family at `"200"` (before) + `"400"` (after) |
| Non-significant | `GRAY["100"]` always |
| Error bars | Black always |

### Using Families in Code

```python
from nature_figure_utils import RUST, GRAY, BLUE, GOLD, SAGE, PLUM, INK, BG, ALPHA

# Single shade
ax.bar(x, y, color=RUST["300"], alpha=ALPHA["bar"])

# Gradient within one family (e.g., dose-response)
dose_colors = [GRAY["200"], RUST["200"], RUST["300"], RUST["400"]]

# All families at default shade
cat_colors = [GRAY["300"], RUST["300"], BLUE["300"], GOLD["300"], SAGE["300"]]
```

### Identity Constants

| Constant | Value | Role |
|----------|-------|------|
| `INK` | `#181114` | Warm mauve for all axes, ticks, spines, text, leader lines |
| `BG` | `#EEEAE0` | Warm linen — for selective panel highlighting only (NOT default background) |
| `BG_COLORS["cream"]` | `#FAF3E8` | Cream — alternative panel highlight |

**Background rule:** Figure and axes are transparent by default. Only use `ax.set_facecolor(BG)` or `ax.set_facecolor(BG_COLORS["cream"])` when you want to visually group specific panels in a composite — e.g., highlight one row or one column. Not every panel gets a colored background.

### Alpha Standards

| Element | `ALPHA` key | Value |
|---------|-------------|-------|
| Bar fill | `"bar"` | 0.85 |
| Box patch | `"box"` | 0.70 |
| Scatter (significant) | `"scatter"` | 0.75 |
| Scatter (non-sig) | `"ns_scatter"` | 0.30 |
| Violin fill | `"violin"` | 0.30 |
| Confidence band | `"band"` | 0.13 |

### Custom Colormaps

Three lab-specific colormaps built from the palette families:

```python
from nature_figure_utils import CMAP_RUST, CMAP_BLUE, CMAP_DIVERGE

# Density scatter with rust sequential
scatter_outlined(ax, x, y, s=12, c=density, cmap=CMAP_RUST)

# Heatmap with rust↔blue diverging (warm midpoint #F0EAE0)
ax.imshow(data, cmap=CMAP_DIVERGE, vmin=-3, vmax=3)
```

| Colormap | Stops | Use for |
|----------|-------|---------|
| `CMAP_RUST` | Rust 600→400→200→cream | Sequential density, expression |
| `CMAP_BLUE` | Blue 600→400→200→ice | Sequential alternative |
| `CMAP_DIVERGE` | Blue 500→200→linen→Rust 200→500 | Diverging (fold change, z-score) |

## Visual Identity (Unified Style)

All figures share a cohesive visual identity — instantly recognizable as "Ying Lab" across every plot type:

| Element | Rule |
|---------|------|
| **Ink** | Warm mauve `INK` (#181114) for ALL axes, ticks, spines, text, leader lines — NOT black |
| **Panel labels** | Always pure **black** and bold (a, b, c, d) — NOT INK. Must NOT overlap with ylabel — `add_panel_labels()` uses `pad_x=-0.02, pad_y=0.025` for clearance |
| **Background** | Transparent by default (both figure and axes). Use `add_group_background()` to highlight specific panels in composites — the background MUST cover the panel labels (a, b, etc.), not just the axes area |
| **Axes** | Floating trimmed spines — trimmed to tick range, outward ticks, no minor ticks, no gridlines |
| **Palette** | Family-based: `RUST["300"]` hero, `GRAY["200"]` control, `BLUE["300"]` accent (see Color System above) |
| **Crowded scatter** | 3-layer outlined dots via `scatter_outlined()` — black bg → white ring → color fill |
| **Small-n scatter** | Open circles — `facecolors="white", edgecolors="black", linewidths=0.8` |
| **Clipping** | **ALWAYS `clip_on=False`** on all scatter/point plots — never clip dots at axes edges |
| **Error bars** | Black, thin: `elinewidth=0.8, capsize=3, capthick=0.8` |
| **Bars** | Solid fill, `edgecolor="none"`, `alpha=ALPHA["bar"]` (0.85) |
| **Legends** | White bbox (`frameon=True, facecolor="white", edgecolor="none", framealpha=0.9`) when near annotations; `frameon=False` otherwise |
| **Annotations** | Leader-line style (slant + horizontal stub) via `smart_annotate()`, color=`INK` |
| **Stat text** | White bbox, placed via `place_stat_text()` |
| **Confidence bands** | `fill_between` with `alpha=ALPHA["band"]` (0.13) |
| **Reference lines** | `color=INK, ls="--", lw=0.5, alpha=0.5` |
| **Censoring marks** | Open circles with colored edge matching the group curve |
| **Clinical thresholds** | Dashed lines with text labels at right edge |
| **Font** | Arial. Base 7pt (tick labels), axis labels 7pt, panel labels 10pt bold. Sized for Nature print dimensions — text renders at 7pt when figure is placed at full column width. |

### HARD RULE: 7pt minimum for ALL text at print size

Every text element — axis labels, tick labels, annotations, bar value labels, heatmap cell text, legend text, stat text — must be at least 7pt. This is the absolute floor for readability on an A4 page at Nature column widths.

Axis labels and titles must be AT LEAST as large as tick labels (both 7pt by default from `retro_style()`). Never reduce annotation text below tick label size — if annotations look too large, the panel is too small, not the text.

Font size constants for scripts:
```python
FS_TICK = 7      # tick labels (retro_style default)
FS_LABEL = 7     # axis labels — match tick labels
FS_TITLE = 7     # panel titles
FS_ANN = 7       # annotations, bar labels, heatmap text
FS_LEGEND = 7    # legend text
FS_STAT = 7      # stat text boxes
```

### Open-Circle Scatter (Small-N / Dose-Response)

For dose-response curves, calibration data, and any small-N scatter where individual points matter, use open circles with separate error bars:

```python
# Error bars only (no marker)
ax.errorbar(x, y, yerr=err, fmt="none", ecolor="black",
            elinewidth=0.8, capsize=3, capthick=0.8, zorder=2)
# Open circles (white fill, black edge, NEVER clipped)
ax.scatter(x, y, s=30, facecolors="white", edgecolors="black",
           linewidths=0.8, zorder=4, clip_on=False)
```

**When to use open circles vs outlined dots vs filled dots:**
- **Open circles**: small-N data (dose-response, calibration, summary statistics) — emphasizes individual measurements
- **Outlined dots** (`scatter_outlined`): large-N crowded scatter where dots merge — prevents visual blending
- **Filled dots**: simple scatter plots where dots don't overlap — default `ax.scatter(clip_on=False)`

### Log-Axis Best Practice

For log-scale axes, always set explicit power-of-10 limits so `trim_axes()` can generate clean ticks:

```python
ax.set_xscale("log")
ax.set_xlim(0.1, 1000)       # powers of 10
# trim_axes() will generate ticks at 10^-1, 10^0, 10^1, 10^2, 10^3
```

`trim_axes()` automatically handles log axes: generates ticks at every power of 10 within limits, and extends outward when the axis limit exceeds the nearest power-of-10 tick (so the spine always covers the full visible data range). Do NOT manually set ticks on log axes — let `trim_axes()` handle it.

## Core Workflow

Every figure follows this sequence:

```
Style → Create figure → Plot data → Smart placement → trim_axes() → Rotate/adjust → Save → AI Review → Fix → Done
```

### Step-by-step

```python
import matplotlib.pyplot as plt
from nature_figure_utils import (
    retro_style, trim_axes, figsize_nature, save_for_review,
    find_best_legend_loc, smart_annotate, place_stat_text,
    scatter_outlined,
)

# 0. Style (once per script)
colors = retro_style()

# 1. Create figure
fig, ax = plt.subplots(figsize=figsize_nature("single"), layout="constrained")

# 2. Plot data (use scatter_outlined for crowded scatter plots)
scatter_outlined(ax, x, y, s=12, c=RUST["300"])
ax.set_xlabel("X Label")
ax.set_ylabel("Y Label")

# 3. Smart placement — BEFORE trim_axes()
loc, _ = find_best_legend_loc(ax, n_items=3)  # find least-crowded corner
ax.legend(loc=loc, frameon=False)              # place legend there
# smart_annotate(ax, labels, points)           # if annotations needed
# place_stat_text(ax, "r = 0.65\np < 0.001")  # if stat text needed

# 4. Trim axes, THEN any rotation/axis adjustments
trim_axes()
# plt.xticks(rotation=45, ha="right")  # if needed — AFTER trim_axes()

# 5. Save high-res and low-res review copy
fig.savefig("figure.pdf", bbox_inches="tight")
fig.savefig("figure.png", dpi=600, bbox_inches="tight")
save_for_review(fig, "figure_review.png", dpi=72)  # low-res for AI review
```

**After saving, you MUST run the AI Visual Review (see below).**

## Multi-Panel Layout

Use `subplot_mosaic` for complex layouts. **Panel labels (a, b, c, d) are only added when explicitly requested by the user.**

### Layout Patterns

```
Banner top:     [["a","a","a"],        Large left:    [["a","a","b"],
                 ["b","c","d"]]                        ["a","a","c"]]

Wide bottom:    [["a","b"],            T-shape:       [["a","a","a","a"],
                 ["c","c"]]                             ["b","b","c","c"],
                                                        ["b","b","d","d"]]
```

Control relative sizes with `gridspec_kw`:
```python
gridspec_kw=dict(height_ratios=[1.2, 1], width_ratios=[1.4, 1])
```

### Multi-Panel Pattern

```python
import matplotlib.pyplot as plt
from nature_figure_utils import (
    retro_style, trim_axes, figsize_nature, auto_pad_figure, add_panel_labels,
    save_for_review, find_best_legend_loc, smart_annotate,
)

# Style (once per script)
colors = retro_style()

fig, axd = plt.subplot_mosaic(
    [["a", "a", "b"],
     ["a", "a", "c"]],
    figsize=figsize_nature("double", aspect=0.6),
    layout="constrained",
    gridspec_kw=dict(width_ratios=[1, 1, 1.1]),
)

# Plot into panels
plot_scatter(axd["a"])
plot_bar(axd["b"])
plot_boxplot(axd["c"])

# Smart placement — legends and annotations
for key in ["a", "b", "c"]:
    if axd[key].get_legend_handles_labels()[1]:  # has legend items
        loc, _ = find_best_legend_loc(axd[key])
        axd[key].legend(loc=loc, frameon=False)

# Auto-pad to prevent inter-panel overlap
auto_pad_figure(fig, axd)

# Trim axes, THEN any rotation/axis adjustments
trim_axes()

# Add panel labels ONLY if user requested them
# add_panel_labels(fig, axd)

# Save
fig.savefig("figure.pdf", bbox_inches="tight")
fig.savefig("figure.png", dpi=600, bbox_inches="tight")
save_for_review(fig, "figure_review.png")
```

## Stitching Pre-Existing Images

```python
from nature_figure_utils import stitch_panels

stitch_panels(
    panel_paths=["panel_a.png", "panel_b.png", "panel_c.png"],
    labels=["a", "b", "c"],  # set labels=None to skip panel labels
    ncols=2,
    width_ratios=[1.4, 1],
    figsize=(14, 10),
    output="composite_figure",
)
```

## Vectorized Composite Assembly (PyMuPDF) — true-vector multi-panel PDFs

Use this when the panels already exist as **separate vector PDFs** (one per
matplotlib script, or exported from any vector source) and you need ONE
multi-panel Nature figure that stays vector — **selectable text, infinite zoom**
— with proper `a, b, c` index labels. It is the vector sibling of
`stitch_panels` (which rasterises PNGs through `imshow` and is fine only for
panels that have no vector form).

**Why it exists — the failure it prevents.** Illustrator / Keynote / PowerPoint
export, and most "drop the panels into a layout" tools, silently **flatten the
whole composite to a single rasterised image** — `pdffonts figure.pdf` then shows
the tell-tale **"1 image, 0 fonts"** and every label is pixels. Do NOT re-export
from the layout tool. Re-composite the *original* per-panel vector PDFs with
PyMuPDF; the text and curves survive, only genuinely-pixel layers stay pixels.

### Recipe

1. **Render each panel as its own vector PDF** with matplotlib
   (`fig.savefig("panel.pdf", bbox_inches="tight")`). One script per panel is
   fine — they do not need to share a figure.
2. **Rasterize only heavy layers, in-panel.** A scatter/volcano/UMAP with
   `>~50k` points must NOT be 50k vector dots (huge file, slow viewers). Set
   `rasterized=True` on that artist and `savefig(dpi=600)` — the point cloud
   becomes one image while axes, ticks, labels, and annotations stay vector.
   This keeps the panel a vector PDF, so it does NOT go in as an `"image"`.
3. **Composite into one page** with `composite_vector_pdf` — vector panels via
   `show_pdf_page` (`keep_proportion=True`, never stretched), genuine raster
   bands (a hand-drawn/ImageGen schematic) via `insert_image`, panel letters as
   **bold black vector text** (`"hebo"` = Helvetica-Bold).
4. **Verify it is actually vector:** `pdffonts out.pdf` should list font rows and
   `pdfimages -list out.pdf` should show only the layers you deliberately
   rasterised — not one full-page image. **Discriminator:** a true flatten is a
   *single* image whose pixel size ≈ the whole page at export dpi (e.g. a
   600 pt × 400 pt page → one ~5000×3333 px image). Legitimate in-panel rasters
   are *several smaller* images each sized to their panel rect — so count images
   and check their dimensions, don't just check "are there any images."
5. **Render a 600-dpi PNG twin** for the Word/`.qmd` manuscript, which cannot
   place a vector PDF inline (`render_png=`). For `docx → PDF`, convert with
   LibreOffice headless (`soffice --headless --convert-to pdf …`) so the embedded
   figure is preserved. (Zixin's Mac has no LibreOffice: render the PDF directly
   from the `.qmd` via Quarto instead — that is the primary authoring path — or
   export from Word/WPS by hand.) If `pdffonts`/`pdfimages` (poppler) are
   missing, run the step-4 vector check with PyMuPDF:
   `python3 -c "import fitz; d=fitz.open('out.pdf'); p=d[0]; print(p.get_fonts()); print(p.get_images())"`
   — same discriminator: font rows must exist, and no single image ≈ the whole
   page at export dpi.

Each `"pdf"` source must be a **single-page** PDF (only page 0 composites; a
multi-page source raises). SVG/EPS panels have no PDF form — convert first
(`rsvg-convert -f pdf in.svg out.pdf`, or `cairosvg`) before adding as `"pdf"`.

```python
from nature_figure_utils import composite_vector_pdf

# rects are in PDF points, TOP-LEFT origin; make each rect match its panel aspect
composite_vector_pdf(
    panels=[
        {"image": "workflow_band.png", "rect": (0,   0, 600, 170)},   # raster schematic band (carries its own a-c)
        {"pdf":   "volcano.pdf",       "rect": (6,  178, 300, 380), "letter": "d", "lx": 8,   "ly": 190},
        {"pdf":   "bar_grid.pdf",      "rect": (300,178, 594, 380), "letter": "e", "lx": 302, "ly": 190},
    ],
    out_pdf="Figure5.pdf", page_w=600,
    render_png="Figure5.png", png_dpi=600,   # 600-dpi twin for the .docx/.qmd
)
```

### Grid layouts — compute rects from native panel aspect, don't eyeball them

For a regular `nrows × ncols` grid (the common case — e.g. the 12 box-plot
panels `d–o`), don't hand-pick magic numbers. **Read each source PDF's native
aspect** and lay the cells out on a formula so panels never stretch and letters
land consistently:

```python
import fitz
def panel_aspect(path):                         # native w/h of a source PDF page
    with fitz.open(path) as d:
        r = d[0].rect; return r.width / r.height

paths = [f"box_{k:02d}.pdf" for k in range(12)]  # 12 panels -> 6 rows x 2 cols
NCOLS, page_w, gut = 2, 600, 6
cell_w = (page_w - (NCOLS - 1) * gut) / NCOLS
cell_h = cell_w / min(panel_aspect(p) for p in paths)   # uniform row height; fits the widest-tall panel
panels = []
for k, p in enumerate(paths):
    r, c = divmod(k, NCOLS)
    x0 = c * (cell_w + gut); y0 = r * (cell_h + gut)
    panels.append({"pdf": p, "rect": (x0, y0, x0 + cell_w, y0 + cell_h),
                   "letter": chr(ord("d") + k), "lx": x0 + 4, "ly": y0 + 12})
composite_vector_pdf(panels, "Figure5_grid.pdf", page_w=page_w,
                     render_png="Figure5_grid.png")   # page_h inferred
```

For a **matplotlib-native** grid (panels drawn in one figure, not separate
PDFs), you don't need this helper at all — use `subplot_mosaic` +
`add_panel_labels()` and save once with `savefig("fig.pdf")`. Reach for
`composite_vector_pdf` only when the panels already exist as independent vector
PDFs (different scripts / tools) that must be welded into one page.

### Panel-letter conventions (index labels done right)

- **Bold, pure black, lowercase**, sitting at the **top-left just outside** each
  panel's box (a hair left of `x0`, a hair above `y0`). 13pt for a typical
  page-width composite, up to ~20pt for a very large canvas.
- **One global alphabet across sub-blocks.** If a workflow band carries `a–c`,
  the data grid below continues at `d`. In matplotlib-native grids, generate the
  letter per panel: `chr(ord("d") + i)`.
- **For matplotlib-native panels**, draw the letter in axes fraction just outside
  the axes so it never rides on the data:
  ```python
  ax.text(-0.045, 1.045, "d", transform=ax.transAxes, ha="left", va="top",
          fontsize=12, fontweight="bold", color="black", clip_on=False, zorder=30)
  ```
  For separate vector PDFs, place the letters in the composite step (above) so
  they live on the page, on top of every panel.
- Base-14 Helvetica-Bold letters are **vector (selectable) but not embedded** —
  fine for most journals. If a venue demands "all fonts embedded," embed at
  conversion time.

### Hard-won lessons (from production Nature figures)

- **A flattened composite is the default failure, not the exception.** Any time a
  figure round-trips through a slide/illustration tool, assume it came back as
  one image and check `pdffonts`. Rebuild from panels rather than babysitting the
  tool.
- **Lock panel → source provenance in the assembler.** Write the exact
  `panel-letter → source PDF → headline numbers` map into the script's docstring,
  and emit a `*_provenance.csv` (n, Δ, reported p, score, source path per panel).
  A silent swap to a look-alike "_combined" panel can change the numbers and flip
  a p-value across the significance line — provenance is what catches it.
- **Composites go stale silently.** If you regenerate a component panel *after*
  assembling, the composite still shows the old panel. Before shipping, confirm
  no source panel is newer than the composite (`mtime`), and re-assemble if so.
- **Carry the reported statistic; don't silently recompute a different one.** When
  a panel's headline p came from a batch-adjusted / linear model rather than the
  two-arm test the box plot would imply, pass that exact value through (a per-spec
  `pvalue` override) so the panel matches the table. Recomputing a naive t-test
  and labelling it as the result is a data-integrity violation.
- **Never stretch a raster to fill a panel.** `keep_proportion=True` fits it;
  to use more panel space, grow the inset rect, do not distort the image (same
  rule as `feedback_figure_aspect_ratio` / `feedback_pptx_figures`).
- **Keep tiny small-multiples readable by dividing labor.** In a 12-panel grid,
  put exact group names + `n` in the schematic and use generic axis labels
  (`Ctrl` / `Case`) on the plot; hold all text at the 7pt floor; thin y-ticks
  with `MaxNLocator(nbins=3, prune="upper")`; fix the jitter RNG seed for
  reproducible point clouds.

---

## Annotation Techniques

### smart_annotate() — Automatic Leader-Line Layout (MANDATORY DEFAULT)

**ALWAYS use `smart_annotate()` for annotating data points.** It automatically handles y-sorting, gap computation, direction selection, and label column placement — eliminating the most common annotation defects (overlapping labels, crossed leader lines, axis-tick collisions).

```python
from nature_figure_utils import smart_annotate

# Annotate 5 outlier points — smart_annotate handles everything
labels = ["TP53", "BRCA1", "MYC", "EGFR", "KRAS"]
points = [(10.5, 12.0), (9.8, 10.5), (11.2, 9.0), (8.5, 11.5), (10.0, 7.5)]
smart_annotate(ax, labels, points, fontsize=7, color=INK, lw=0.5, stub=0.4)
```

**What it does automatically:**
1. **Sorts points by descending y** — highest data point gets highest label (prevents line crossing)
2. **Computes minimum gap** — `min_gap_frac=0.08` of the full y-axis range (prevents label crowding)
3. **Chooses direction** — `direction="auto"` annotates right unless points are at the extreme right edge (>90% of axis range). Default is RIGHT (safest — extends outward from data)
4. **Places label column OUTWARD past ALL data** — scans all data points in the axes (not just annotated ones) and places labels past the rightmost/leftmost data + 12% offset. This prevents annotations from overlapping with scatter dots or other data
5. **Auto-extends axis limits** — if the label column + text would be clipped, automatically widens xlim

**Parameters for fine-tuning:**
```python
smart_annotate(ax, labels, points,
    direction="auto",     # "auto", "left", or "right"
    fontsize=7,           # label font size
    color="black",        # line and text color
    lw=0.6,               # leader line width
    stub=None,            # horizontal stub length (auto = 5% of x range)
    min_gap_frac=0.08,    # minimum gap as fraction of y-axis range
)
```

**Axis limits are auto-extended** — `smart_annotate()` automatically widens xlim to fit the label column + text. No manual extension needed in most cases. If you want even more room, set xlim explicitly after calling `smart_annotate()`.

### Manual Leader-Line Annotations (Low-Level)

Only use `add_elbow_annotation()` directly when `smart_annotate()` doesn't fit (e.g., annotating a single specific point, or needing per-annotation custom colors).

```
Direction "right":           Direction "left":

             ──── Label      Label ────\
            /                            \
           /                              \
          ●                                ●
```

```python
from nature_figure_utils import add_elbow_annotation

add_elbow_annotation(ax, "Gene A", xy=(2.5, 8.3), xytext=(3.5, 10.0),
                     direction="right", color="black", lw=0.6, fontsize=7)
```

**CRITICAL — Systematic leader-line placement (prevents ALL common errors):**

Two conditions together guarantee no crossing, no axis overlap, and clean short lines:

**Condition 0: Annotate AWAY from the nearest axis.**
Decide `direction="left"` or `direction="right"` based on WHERE the points are in x-space, NOT by the sign of their y-value or any other data metric:
- Points near the LEFT edge (near y-axis) → annotate **RIGHT** (away from y-axis)
- Points near the RIGHT edge → annotate **RIGHT** (extending beyond data) or **LEFT** (if well away from y-axis)
- The SAFEST default: annotate **RIGHT** for all groups, with each group's label column just past its rightmost data point

**Why this matters:** Annotating toward the y-axis causes text to collide with tick labels (e.g., annotation "LANCL1" overlapping the "0.2" tick). Annotating based on y-sign instead of x-position can also invert the xlim (axis reads 80→40).

**Condition 1: Label column NEAR data, not at plot edge.**
Compute the label column x from the actual annotated data points:
```python
# Right side: just past the rightmost annotated point
right_col = max(x[idx] for idx in annotated_indices) + small_offset

# Left side: just past the leftmost annotated point
left_col = min(x[idx] for idx in annotated_indices) - small_offset
```
- `small_offset` ≈ 5-10% of the data x-range (e.g., 1.0 for a volcano with x-range ~8)
- This produces SHORT slant lines close to the data — not long tangled lines to the axis edge
- This automatically prevents overlap with y-axis tick labels (labels are in the data region, not near the axis)
- Set explicit `stub=` parameter when auto-calculated stub (5% of xlim range) would be too long

**Condition 2: Sort annotated points by descending y, assign labels top-to-bottom.**
```python
sorted_idx = sorted(annotated_indices, key=lambda i: -y[i])
y_range = y.max() - y.min()  # FULL axis range, not just annotated points
min_gap = y_range * 0.08     # ≥8% of axis range per label row
y_top_label = max(y[i] for i in sorted_idx) + margin
y_gap = max(data_y_span / (n - 1), min_gap)
for rank, idx in enumerate(sorted_idx):
    add_elbow_annotation(ax, name, xy=(x[idx], y[idx]),
                         xytext=(label_col, y_top_label - rank * y_gap), ...)
```
- Highest data y → highest label y. This makes the data-to-label mapping monotonic.
- Combined with Condition 1 (label column beyond all data x), this mathematically guarantees no crossing.
- For left-side annotations: same descending sort (least-negative y first).
- **CRITICAL: min_gap must be proportional to the FULL y-axis range**, not the y-span of the annotated points. When annotated points are the top-N or bottom-N, their y-values cluster tightly. Using their span for gap calculation produces near-zero gaps and overlapping labels.
- **CRITICAL: min_gap must account for actual rendered text height.** At 7pt in a compact multi-panel figure, a fixed gap like 0.5 data units may be smaller than the text itself. Compute gap from fontsize and panel geometry:
```python
ax_h_inch = fig.get_figheight() * ax.get_position().height
text_h_data = (fontsize / 72.0) * (y_range / ax_h_inch)
y_gap = max(y_range * 0.10, text_h_data * 2.0)
```
This ensures labels never overlap regardless of panel size or font size.

**Why all three conditions matter:**
- Sort alone prevents crossing IF all lines go the same direction. But if the label column is between some data points' x positions, some lines go left and others go right — crossing becomes possible again.
- Near-data placement alone reduces tangling but doesn't prevent it if y-mapping is inverted.
- Direction-matching alone prevents axis inversion but doesn't prevent crossing.
- Together: correct direction + all lines go one way + vertical order preserved → no crossing guaranteed.

**Complete example (volcano plot):**
```python
# Select and sort
top_idx = np.argsort(score * sig_mask)[-6:]
sorted_idx = sorted(top_idx, key=lambda i: -neg_log_p[i])

# Compute label column from data
data_xs = [log2fc[i] for i in sorted_idx]
data_ys = [neg_log_p[i] for i in sorted_idx]
right_col = max(data_xs) + 0.8  # just past data

# Labels span the data y-range
y_top = max(data_ys) + 0.2
y_gap = max((max(data_ys) - min(data_ys)) / (len(sorted_idx) - 1), 0.5)

for rank, idx in enumerate(sorted_idx):
    add_elbow_annotation(ax, gene_names[idx],
        xy=(log2fc[idx], neg_log_p[idx]),
        xytext=(right_col, y_top - rank * y_gap),
        direction="right", color=INK, lw=0.5, fontsize=7, stub=0.4)
```

### Text Annotation with adjustText

**Applicability:** When you have many overlapping labels and need automatic layout.

Use `adjustText` to prevent label overlap. Use `path_effects` for legibility:

```python
from adjustText import adjust_text
import matplotlib.patheffects as pe

texts = []
# For each point (px, py, label) to annotate:
texts.append(
    plt.text(px, py, label, path_effects=[pe.withStroke(linewidth=3, foreground="white")])
)
adjust_text(texts, arrowprops=dict(arrowstyle="->", color="gray", alpha=0.5))
```

### Significance Brackets

**Applicability:** Comparing groups in bar/box plots.

```python
def add_bracket(ax, x1, x2, y, h, text, lw=0.8):
    """Draw a significance bracket between two x positions."""
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=lw, c="black")
    ax.text((x1 + x2) / 2, y + h + 0.15, text, ha="center", va="bottom",
            fontsize=7)

# Stack brackets with increasing y to avoid overlap
# Use h=0.3 and text offset=0.15 to prevent text-bracket overlap
y_base = max_bar_height + error + 0.4
add_bracket(ax, x1, x2, y_base, 0.3, "***")
add_bracket(ax, x1, x3, y_base + 0.8, 0.3, "n.s.")

# CRITICAL: set ylim to cover ALL data including strip-plot dots + brackets
ymin = min(d.min() for d in data)
ymax = max(d.max() for d in data)
ax.set_ylim(ymin - 0.5, ymax + 2.8)  # room for brackets above
```

### Inset Zoom

**Applicability:** Showing detail of a crowded region alongside the full view.

```python
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

axins = inset_axes(ax, width="35%", height="35%", loc="upper right")
axins.scatter(x, y, s=8, c=colors, alpha=0.7)
axins.set_xlim(x_zoom_min, x_zoom_max)
axins.set_ylim(y_zoom_min, y_zoom_max)
axins.set_xticks([])
axins.set_yticks([])
mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="gray", lw=0.5)
```

---

## Legend Placement (CRITICAL — ZERO TOLERANCE FOR OVERLAP)

**A legend must NEVER overlap ANY visual element** — not lines, not confidence bands, not bars, not scatter points, not reference lines, not annotations. This is the #1 defect in scientific figures and must be checked during every visual review.

### CRITICAL: fill_between bands ARE data elements

Semi-transparent confidence bands (`fill_between`, `fill_betweenx`) count as data. A legend sitting on top of a faint alpha=0.12 band IS an overlap — even though the band looks "faint," the legend text becomes harder to read and the band is visually disrupted. **When assessing overlap, check against bands, not just lines.**

### HARD RULE: legends ALWAYS outside for multi-panel figures

In multi-panel composite figures (4+ panels), legends MUST be placed OUTSIDE the axes to guarantee zero overlap with data. Use `bbox_to_anchor` to position above the panel:

```python
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18),
          frameon=False, ncol=2, fontsize=5, columnspacing=1.0)
```

`find_best_legend_loc()` is useful for single-panel figures where there may be a clear empty corner. For multi-panel figures, skip it and go directly to outside placement. The small overhead of an external legend is always better than risking data overlap.

### HARD RULE: individual panel aspect ratio

Each panel should be roughly **square or wider-than-tall** (landscape). Tall-and-narrow panels are almost never correct. Before choosing a chart type, consider the data shape:
- **Horizontal bar chart** for categorical data with 4+ items (names on y-axis, values on x-axis) — naturally fits square panels
- **Vertical bar chart** only when there are ≤3 categories and the panel is wide
- **Scatter/dot plots**: use `aspect="equal"` or ensure the panel is square
- **Spaghetti/trajectory plots**: wider-than-tall (landscape)
- **Heatmaps**: aspect depends on the matrix shape; use `aspect="auto"`
- **Forest plots**: horizontal (effect size on x-axis, items on y-axis)

If a panel ends up taller than wide, switch to a horizontal layout for that chart type.

### HARD RULE: figure height proportional to content (NEVER stretch)

Figures should be as COMPACT as their content allows. A figure should never be taller than it needs to be. Starting-point aspect ratios by row count:
- **2-row figures**: `aspect=0.5`
- **3-row figures**: `aspect=0.6`
- **4-row figures**: `aspect=0.8`

These are defaults — adjust based on content. The guiding principle: **~90% of panels should be wider-than-tall or square.** The rare exception is a panel whose content genuinely demands portrait orientation (e.g., a tall dendrogram or a very long categorical y-axis). If you find more than one panel taller than wide, reduce the aspect.

### HARD RULE: intelligent panel sizing — not uniform grids

Do NOT distribute panels evenly. Think about what each panel NEEDS:

**Use `height_ratios` and `width_ratios` to match content:**
- A barh chart with 4 items needs less height than a scatter plot
- A heatmap with a 10×5 matrix needs more height than a 3×3
- A UMAP or scatter should be roughly square
- A spaghetti/trajectory plot benefits from landscape (wide)

**Use spanning panels for important content:**
```python
# Large scatter spanning 2 rows on left, two smaller panels stacked on right
fig, axd = plt.subplot_mosaic(
    [["a", "a", "b"],
     ["a", "a", "c"]],
    figsize=figsize_nature("double", aspect=0.6),
    layout="constrained",
    gridspec_kw=dict(width_ratios=[1, 1, 1.1]),
)

# Banner top panel with details below
[["a", "a", "a"],
 ["b", "c", "d"]]

# Wide main result + column of supporting panels
[["main", "main", "s1"],
 ["main", "main", "s2"],
 ["main", "main", "s3"]]
```

**Decision logic for layout:**
1. Identify the "hero" panel (main result) — give it the most space (spanning rows or columns)
2. Group related panels in the same row
3. Give each row a `height_ratio` proportional to its tallest panel's content needs
4. Give each column a `width_ratio` based on the widest content (e.g., long y-tick labels need wider columns)
5. Verify each individual panel is wider-than-tall after layout

### Bar charts: trim_axes auto-pads the categorical axis

`trim_axes()` is bar-aware. It detects `ax.bar` / `ax.barh` containers and, on
the categorical axis (x for vertical bars, y for barh), extends the spine and
limit PAST the outer bar edges by ~0.75× the bar width. End bars no longer sit
on the spine — they get a visible gap automatically. The value axis is trimmed
normally (baseline stays at the 0 tick).

**You no longer need to exclude bar panels from `trim_axes()` for padding**, and
you do not need a manual `set_xlim`/`set_ylim` or `ax.margins()` call for it. Let
`trim_axes(fig)` handle every bar panel. Only exclude a bar panel if you are
intentionally hand-managing its spines for some other reason.

### HARD RULE: figure complexity and panel count

Do NOT force all figures into a uniform grid (e.g., 2×3). Each figure should have as many panels as its content requires — **8, 10, or even 12 panels** are appropriate for Nature-level figures. A full-width figure on an A4 page can accommodate 3-4 rows of 3-4 panels each. Design each figure's layout independently based on what the data demands — see "intelligent panel sizing" above for how to allocate space.

### HARD RULE: no clipping at edges

**ALWAYS use `clip_on=False`** for ALL scatter, errorbar, and point plots. For bar charts, the first/last bar must NEVER sit on the axis line — but you do NOT set this padding by hand: `trim_axes()` now pads the categorical axis automatically (~0.75× bar width, which gives the same ~0.5-unit clearance for `height=0.4` barh). Just call `trim_axes(fig)` after plotting.

After plotting, visually verify that no data point or bar edge touches the axis spine.

### HARD RULE: compact bar charts — no excessive vertical spacing

Horizontal bar charts should be DENSE, not airy. Rules:
- Use `height=0.4` (not 0.55 or 0.65) for `barh()` to keep bars compact
- For grouped bars, use `height=0.2` per group with tight offsets
- The gap between adjacent bars should be approximately equal to the bar height
- If a bar chart has N items, the panel height should be proportional to N — a 4-item bar chart should not fill the same height as a 10-item bar chart
- Never let bar annotations (value labels, stars) add excessive whitespace — keep fontsize at 4-5pt for annotations

### HARD RULE: axis limits must hug the data

The axis range should be tight around the data. Specific violations to avoid:
- **Volcano/scatter plots**: set xlim/ylim to `(data_min - 10%, data_max + 10%)`. Do NOT let reference lines (p=0.05 threshold, x=0 line) extend the axis range beyond the data. Clip reference lines to the data range instead.
- **Bar charts**: xlim should extend only 10-15% beyond the longest bar, not 50%
- **Dot plots**: axis range should cover only the data points plus small margin

If a panel has data covering only 50% of the axis range, the axis limits are wrong. Fix them.

### HARD RULE: volcano plot annotations — symmetric, generous xlim

For volcano plots, annotate up-regulated genes to the RIGHT and down-regulated genes to the LEFT (matching the data direction). This creates a balanced, publication-quality layout.

**Critical**: left-side annotations require generous xlim to avoid y-axis collision. At 7pt in a compact panel, annotation text is WIDE in data coordinates. Set symmetric xlim with at least 2.5x the data range:

```python
x_absmax = max(abs(log2fc.min()), abs(log2fc.max()))
ax.set_xlim(-x_absmax * 2.5, x_absmax * 2.5)
```

Do NOT try to "tighten" xlim after placing annotations — changing xlim causes constrained_layout to reflow, invalidating all text position measurements. Set generous limits ONCE before placing annotations.

For annotation y-gap, compute from actual text height in data coordinates to prevent label overlap:
```python
ax_h_inch = fig.get_figheight() * ax.get_position().height
text_h_data = (fontsize / 72.0) * (y_range / ax_h_inch)
y_gap = max(y_range * 0.10, text_h_data * 2.0)
```

### HARD RULE: heatmap text colors

For annotated heatmaps, text color must contrast with the cell background. Compute brightness from the ACTUAL colormap RGBA value — do NOT use a simple midpoint threshold, which fails for non-linear or asymmetric colormaps:
```python
from matplotlib.colors import Normalize
norm = Normalize(vmin=vmin, vmax=vmax)
rgba = cmap(norm(val))
brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
text_color = "white" if brightness < 0.5 else INK
```
This handles diverging, sequential, and custom colormaps correctly. Getting text color wrong (white on light, dark on dark) makes annotations unreadable.

### HARD RULE: bar value labels always OUTSIDE and consistent

For horizontal bar charts with value labels at bar tips, labels must ALWAYS be placed outside (to the right of) the bar, never inside. This ensures visual consistency across all bars regardless of length.

```python
for bar, label in zip(bars, labels):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            label, va="center", ha="left", fontsize=4.5, color=INK)
```

Do NOT use `smart_bar_labels` for publication figures — its inside/outside logic creates visual inconsistency. Use direct placement for full control.

### HARD RULE: panel labels aligned by row using tight bboxes

Panel labels must be:
1. At the LEFT edge of each panel's tight bounding box (includes tick labels)
2. At a CONSISTENT y position within each row (the highest tight bbox y1 in that row)

Using `get_position().x0` places labels at the center of the visual panel (wrong). Using per-panel y positions creates misalignment (also wrong).

```python
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
fig_inv = fig.transFigure.inverted()

# Define which panels are in each row
rows = [["a", "b", "c"], ["d", "e", "f"]]

for row_keys in rows:
    tbs = {}
    for k in row_keys:
        if k in axd:
            tb = axd[k].get_tightbbox(renderer)
            if tb is not None:
                tbs[k] = fig_inv.transform_bbox(tb)
    if not tbs:
        continue
    row_y = max(tb.y1 for tb in tbs.values()) + 0.01  # aligned y
    for k in row_keys:
        if k in tbs:
            fig.text(tbs[k].x0, row_y, k,
                     fontsize=10, fontweight="bold", va="bottom", ha="left")
```

### HARD RULE: never truncate gene/protein names

Scientific names must be shown in full. If a name is too long for one line:
1. **Wrap to 2 lines**: `"Urokinase-type\nplasminogen activator"` using `\n`
2. **Use a standard abbreviation**: "uPA" instead of "Urokinase-type plasminogen activator"
3. **Reduce fontsize** to 4-5pt if needed

NEVER truncate with "..." — readers cannot identify a gene from a partial name. This is especially important for forest plots and bar charts where the name IS the data.

### HARD RULE: rich annotations

Publication figures must carry annotation directly on the panels — readers should understand the key finding without reading the legend. For each panel:
- **Effect sizes**: annotate bars/points with Cohen's d, OR, beta values where appropriate
- **P-values**: add significance stars or exact p-values near significant results
- **Sample sizes**: show n= in panel title or as subtitle text
- **Key findings**: use colored text, arrows, or highlighted regions to draw attention to the main result
- **Reference lines**: dashed lines at meaningful thresholds (e.g., OR=1, p=0.05, d=0.5)

A figure that looks "simple" or "empty" is under-annotated. Every panel should be information-dense.

### HARD RULE: plots with confidence bands → legend OUTSIDE the axes

Survival curves, ROC curves, time courses with confidence/error bands — these have data spanning nearly the full plot area. There is NO clean internal spot. Do not attempt internal placement. Place the legend outside:

```python
# ABOVE the plot (preferred — horizontal row, no collision with xlabel)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02),
          frameon=False, ncol=3, columnspacing=1.0)

# RIGHT of the plot (if vertical list is needed)
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
```

### When to use inside vs outside placement:
- **Inside**: bar charts, scatter plots, volcano plots — usually have clear empty corners
- **Outside (above/right)**: survival curves, ROC curves, time courses with confidence bands, any plot where lines + bands fill most of the canvas. **Above** is preferred over below to avoid xlabel collision.
- **Compact horizontal (`ncol=N`)**: when there are only 2-3 short legend entries

### Programmatic Placement (for internal legends)

```python
from nature_figure_utils import find_best_legend_loc

# After plotting data, BEFORE trim_axes():
loc, count = find_best_legend_loc(ax, n_items=3)  # scans data density in 8 regions
if count > 3:
    # Too crowded inside — place outside
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
              frameon=False, ncol=3)
else:
    ax.legend(loc=loc, frameon=False)
```

`find_best_legend_loc(ax, n_items=3)` collects all data points (lines, scatter, bars, fill_between bands) and tests 8 standard positions. Returns the one with fewest data elements in a compact footprint. **Line crossing penalty**: line-plot regions are penalized 5x heavier than scattered points.

The `n_items` parameter adjusts the vertical footprint estimate — pass the number of legend items for accurate sizing.

### Stat Text Boxes — Use place_stat_text()

For stat annotations (R², p-value, etc.), use `place_stat_text()` which calls the same density scanner:
```python
from nature_figure_utils import place_stat_text
place_stat_text(ax, "$r$ = 0.65\n$p$ < 0.001")
```

### Fallback Strategy (in order of preference)

1. **`find_best_legend_loc()` returns count=0** — use that location, done.
2. **count > 0 but small** — use the location but verify in visual review. Consider `ncol=2` or `ncol=3` for compact horizontal layout:
   ```python
   ax.legend(loc=loc, frameon=False, ncol=2, columnspacing=1.5)
   ```
3. **Outside the plot** — ONLY for single-panel figures or when absolutely no internal region works. In multi-panel figures, `bbox_to_anchor` outside axes wastes space and can collapse `constrained_layout`:
   ```python
   ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
   ```
   **The legend should always visually belong to its sub-panel, not occupy its own dedicated column.**

### Scatter Plot Edge Clipping

Always use `clip_on=False` for scatter plots to prevent border points from being cut off:
```python
ax.scatter(x, y, s=15, c=colors, alpha=0.8, clip_on=False)
```
Also set axis limits wider than the data range to give breathing room:
```python
ax.set_xlim(x.min() - margin, x.max() + margin)
```

### Panel Background Highlighting

Use `add_group_background()` to visually group panels with a colored background. Two rules:

1. **Background MUST cover panel labels** — never use `ax.set_facecolor()` alone, as it only covers the axes area and leaves labels floating outside.
2. **Panels outside the group MUST have a clear gap** — the function uses tight bottom padding (`pad_bottom=0.005`) so the background doesn't bleed into neighboring panels below. Non-grouped panels (c, d, etc.) should feel clearly separate.

```python
from nature_figure_utils import add_group_background, BG, BG_COLORS

# After add_panel_labels(), draw background covering panels + labels
add_group_background(fig, [axd["a"], axd["b"]], panel_labels=["a", "b"],
                     color=BG_COLORS["cream"])
```

### Panel Sizing

Font sizes are calibrated for Nature's print dimensions — they render at 7–8pt when figures are placed at full column width on an A4 page (~180mm text area). The same `retro_style()` font sizes work for all column widths because `figsize_nature()` returns the actual print dimensions:
- **Single column (3.5 in):** 7pt text renders at 7pt in print — text takes up more space relative to the plot, which is correct for simpler single-panel figures.
- **Double column (7.2 in):** 7pt text renders at 7pt in print — proportionally smaller against the data, matching the dense multi-panel style of reference figures.
- Do NOT adjust font sizes per column width — the theme handles this automatically.

### Rules

- **Always `frameon=False`** — frameless legends look cleaner and waste less space.
- **Never place a legend at the default location without checking** — matplotlib's default `loc="best"` frequently overlaps data.
- **After placing a legend, verify in the review** that it doesn't overlap ANY data element (points, bars, lines, error bars, annotations, brackets).
- **Bar chart legends** must not overlap any bars or error bars — place above the data region or to the side.
- **When annotations (leader lines, brackets) are present**, check that the legend doesn't overlap those too.
- **Legend + significance brackets** — in bar charts with both a legend and significance brackets, these compete for the same vertical space above the bars. Always set an explicit `ylim` that accommodates both: `ax.set_ylim(0, max_bar + max_error + bracket_height + legend_height + margin)`. Place the legend at `"upper left"` (or wherever bars are shortest) so it doesn't collide with brackets above tall bars.
- **Stat text boxes (R², p-value, etc.)** — ALWAYS use `place_stat_text(ax, text)` which programmatically finds the least-crowded corner. Never manually hardcode a position.

### Axis Label Clipping Prevention

Long axis labels or tick labels get clipped at figure edges. Prevent this:
- Keep axis labels concise: "Predicted expr." not "Predicted expression level"
- Keep tick labels short: "C1"–"C4" not "Control_Sample_1"–"Control_Sample_4"
- Rotate long tick labels: `ax.set_xticklabels(labels, rotation=35, ha="right")` — but ONLY AFTER `trim_axes()`
- If clipping persists, increase the figure aspect ratio or use `figsize_nature("1.5col")` instead of `"single"`

---

## Plot-Specific Recipes

### Outlined Scatter (Crowded Plots)

For crowded scatter plots where dots merge visually, use `scatter_outlined()` which creates a 3-layer dot (black background -> white ring -> color fill) that gives each point a visible border:

```python
from nature_figure_utils import scatter_outlined

scatter_outlined(ax, x, y, s=12, c=RUST["300"], alpha=0.8)
# With density coloring:
scatter_outlined(ax, x[order], y[order], s=12, c=z[order], cmap=CMAP_RUST, alpha=0.8)
```

Parameters: `outline_scale=2.5` (black ring size), `ring_scale=1.7` (white ring size), `outline_color="black"`.

### Density Scatter Plot

Show correlation between two continuous variables, colored by point density. Uses a two-layer outline technique that gives each point a crisp black border — especially effective for crowded plots where points overlap heavily.

```python
from scipy.stats import gaussian_kde

xy = np.vstack([x, y])
z = gaussian_kde(xy)(xy)

# Sort so densest points are on top
order = z.argsort()
# Use scatter_outlined for crowded data; regular scatter for sparse data
scatter_outlined(ax, x[order], y[order], s=12, c=z[order], cmap='flare', alpha=0.8)
```

**Key details:**
- `scatter_outlined` draws a black outline layer (`s=size * 1.5`) behind colored data — creates a visible ring around each point
- Sort by density (`z.argsort()`) so the densest (darkest) points render on top, preventing sparse outliers from hiding the dense core
- The `"flare"` colormap transitions from dark purple (high density) to salmon/orange (low density), making cluster cores visually distinct
- Works well with `s=30` for typical scatter plots; adjust size based on point count

Use `smart_annotate()` for outlier point labels.

### Volcano Plot

Visualize effect size vs. statistical significance.

```python
logP = -np.log10(p_value)

# Non-significant (gray, small, transparent)
ax.scatter(effect_size[ns], logP[ns], s=8, alpha=ALPHA["ns_scatter"], c=GRAY["100"], zorder=1)
# Significant up (rust) / down (blue)
ax.scatter(effect_size[sig_up], logP[sig_up], s=12, alpha=ALPHA["scatter"],
           c=RUST["400"], label="Up", zorder=2)
ax.scatter(effect_size[sig_down], logP[sig_down], s=12, alpha=ALPHA["scatter"],
           c=BLUE["300"], label="Down", zorder=2)

# Context lines
ax.axvline(fc_thresh, color=INK, ls="--", lw=0.5, alpha=0.5)
ax.axvline(-fc_thresh, color=INK, ls="--", lw=0.5, alpha=0.5)
ax.axhline(-np.log10(p_thresh), color=INK, ls="--", lw=0.5, alpha=0.5)

# Smart legend placement
loc, _ = find_best_legend_loc(ax)
ax.legend(loc=loc, frameon=False)

# Annotate top hits with smart_annotate
top_idx = np.argsort(score)[-6:]
ann_labels = [gene_names[i] for i in top_idx]
ann_points = [(effect_size[i], logP[i]) for i in top_idx]
smart_annotate(ax, ann_labels, ann_points, color=INK, stub=0.4)
```

### Bar Chart

Solid fill, no edge lines. Use family 300 shades. Always include error bars when available.

```python
bar_colors = [GRAY["300"], RUST["300"], BLUE["300"], GOLD["300"], SAGE["300"]]
bars = ax.bar(categories, values, width=0.6, color=bar_colors[:len(categories)],
              edgecolor="none", alpha=ALPHA["bar"])
ax.set_ylabel("Value")
# Error bars
ax.errorbar(categories, values, yerr=errors, fmt="none", ecolor="black",
            elinewidth=0.8, capsize=3)
# trim_axes(fig) later auto-pads the x (categorical) axis so the first/last
# bar does not sit on the y-spine — no manual set_xlim/margins needed.
```

### Box Plot with Individual Points

Thin lines, filled boxes with `patch_artist`. Overlay individual data points for transparency.

```python
bp = ax.boxplot(data, patch_artist=True, widths=0.5,
                boxprops=dict(facecolor=RUST["300"], alpha=ALPHA["box"], linewidth=0.8),
                whiskerprops=dict(linewidth=0.8),
                capprops=dict(linewidth=0.8),
                medianprops=dict(color="black", linewidth=1.0),
                flierprops=dict(marker="o", markersize=2, alpha=0.4))

# Overlay strip plot
for i, d in enumerate(data):
    jitter = np.random.uniform(-0.1, 0.1, len(d))
    ax.scatter(np.full_like(d, i + 1) + jitter, d, s=8, alpha=0.5,
               c="black", zorder=3)

# CRITICAL: set ylim to cover ALL data including strip-plot dots
ymin = min(d.min() for d in data)
ymax = max(d.max() for d in data)
ax.set_ylim(ymin - 0.5, ymax + 0.5)
```

**Y-axis coverage rule:** The y-axis MUST cover all visible data points. When overlaying strip-plot dots on a boxplot, the dots often extend beyond the whiskers. If you don't set ylim explicitly, `trim_axes()` will trim the spine to the tick range, but dots below the first tick will appear to "float" outside the axis. Always compute `ymin`/`ymax` from the actual data arrays and set explicit limits.

### Clustermap / Heatmap

Visualize a matrix, clustering similar rows and columns.

**CRITICAL: Reset to vanilla matplotlib for heatmaps.** The scientific theme removes top/right spines, changes edge colors, and applies styling that looks wrong on heatmaps. Simply restoring spines is NOT enough — you must reset ALL rcParams to matplotlib defaults.

Use `mpl.rc_context()` + `mpl.rcdefaults()` to create an isolated context with clean matplotlib defaults:

```python
import matplotlib as mpl
from nature_figure_utils import CMAPS, figsize_nature, save_for_review

# Wrap entire heatmap in a clean context — scientific theme is fully suspended
with mpl.rc_context():
    mpl.rcdefaults()  # Reset to vanilla matplotlib
    # Keep just essentials: Arial font and high-res save
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial"],
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=figsize_nature("single", aspect=1.2),
                            layout="constrained")

    im = ax.imshow(data, cmap=CMAPS["diverging"], aspect="auto", vmin=-3, vmax=3)

    # Remove ALL frame elements — heatmaps should have NO spines or tick marks
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)  # no tick marks without spines

    # Colorbar — text size proportional to axis labels, no outline
    cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Z-score")
    cbar.ax.tick_params(labelsize=9)
    cbar.outline.set_visible(False)  # remove colorbar frame

    # NO trim_axes() — we're in vanilla matplotlib context

    fig.savefig("heatmap.pdf", bbox_inches="tight")
    fig.savefig("heatmap.png", dpi=600, bbox_inches="tight")
    save_for_review(fig, "heatmap_review.png", dpi=72)
# Scientific theme is automatically restored after exiting the context
```

For clustermaps:
```python
scaled_data = StandardScaler().fit_transform(data)
g = sns.clustermap(scaled_data, cmap='RdBu_r', center=0)
plt.setp(g.ax_heatmap.get_xticklabels(), rotation=90)
```

### Forest Plot

Visualize effect sizes (e.g., hazard ratios, odds ratios) with confidence intervals.

```python
categories = ["Brain", "Artery", "Pancreas"]
effect = [1.15, 1.08, 1.22]
ci_low = [1.05, 0.98, 1.10]
ci_high = [1.26, 1.19, 1.35]

y_pos = np.arange(len(categories))
xerr = [[e - l for e, l in zip(effect, ci_low)],
        [h - e for e, h in zip(effect, ci_high)]]

ax.errorbar(effect, y_pos, xerr=xerr, fmt="s", color="black",
            markersize=5, capsize=3, elinewidth=0.8, capthick=0.8)
ax.axvline(1.0, color="gray", ls="--", lw=0.5)
ax.set_yticks(y_pos)
ax.set_yticklabels(categories)
ax.set_xlabel("Hazard ratio")
ax.invert_yaxis()

# CRITICAL: Hide left spine for categorical y-axis (forest plots)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)  # no y-tick marks
# Then manually trim only the x-axis spine:
xticks = np.asarray(ax.get_xticks(minor=False))
xlim = ax.get_xlim()
xt_in = xticks[(xticks >= xlim[0]) & (xticks <= xlim[1])]
if len(xt_in) >= 2:
    ax.spines["bottom"].set_bounds(float(xt_in[0]), float(xt_in[-1]))
# REQUIRED: pad the categorical y-axis so the top/bottom rows (and their value
# labels) clear the frame — the default 5% margin crams them onto the edge.
pad_categorical_axis(ax, "y", pad=0.5)
# Do NOT call trim_axes() — handle forest plot axes manually
```

**Forest plot axis rule:** Forest plots have a categorical y-axis (tissue names, study labels). Trimming the left spine to tick positions makes it look broken because the ticks are at integer positions that don't align with the data. Instead: hide the left spine entirely and remove y-tick marks. Only trim the bottom (continuous) spine.

**Forest plot padding rule:** Because forest plots skip `trim_axes()`, they do NOT get its automatic bar-axis padding. The categorical y-axis falls back to the default 5% margin, which leaves the outermost rows (and their CI value labels) jammed against the top/bottom frame. ALWAYS call `pad_categorical_axis(ax, "y", pad=0.5)` after building the plot. The same applies to any manually-built categorical plot (dot plots, lollipop/cleveland plots) — pad whichever axis holds the categories.

### Trajectory / Spaghetti Plot

Show individual trajectories with highlighted subsets annotated by leader lines.

```python
# Background: many faint gray trajectories
for traj in all_trajectories:
    ax.plot(x, traj, color="#CCCCCC", lw=0.3, alpha=0.5)

# Highlight key trajectories with color + leader annotation
for name, traj, col in highlighted:
    ax.plot(x, traj, color=col, lw=1.5, alpha=0.9, zorder=3)
    add_elbow_annotation(ax, name, xy=(x[-1], traj[-1]),
                         xytext=(x[-1] + offset, traj[-1]),
                         direction="right", color=col, lw=0.5)
```

**Tips:**
- Ensure highlighted trajectories have sufficient y-separation at the annotation end — if two lines converge, their labels will overlap. Aim for at least 1 y-unit separation between adjacent highlighted trajectories at the annotation endpoint.
- Set `xlim` tight to the data range plus a small right margin for leader-line labels (e.g., `xlim = (x.min() - 2, x.max() + 8)`). Don't add excessive padding that breaks the ink-to-canvas ratio.

### Ridge Plot

Show distribution of a continuous variable across multiple categories.

```python
sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})

# Order categories by median
order = data.groupby('category_col')['numeric_col'].median().sort_values().index

g = sns.FacetGrid(data, row='category_col', hue='category_col',
                  aspect=15, height=0.5, palette='coolwarm', row_order=order)
g.map(sns.kdeplot, 'numeric_col', fill=True, alpha=1)
g.map(sns.kdeplot, 'numeric_col', color="w", lw=2)
g.fig.subplots_adjust(hspace=-0.3)
g.set_titles("")
g.set(yticks=[], ylabel="")
g.despine(bottom=True, left=True)
```

### UMAP Plot

Visualize high-dimensional data in 2D. Use `scatter_outlined` for defined cluster dots and `path_effects` for centroid labels.

```python
import matplotlib.patheffects as pe
from nature_figure_utils import scatter_outlined

# Plot each cluster separately for per-cluster coloring
for name, x, y, col in clusters:
    scatter_outlined(ax, x, y, s=10, c=col, alpha=0.7)
    cx, cy = x.mean(), y.mean()  # centroid
    ax.text(cx, cy, name, fontsize=7, fontweight="bold", ha="center",
            va="center", color=col,
            path_effects=[pe.withStroke(linewidth=3, foreground="white")])

ax.set_xlabel("UMAP 1")
ax.set_ylabel("UMAP 2")
```

**Style notes:** `scatter_outlined` keeps clusters visually distinct even when adjacent. White-halo centroid labels. No legend needed when centroids are labeled directly. Use `aspect=1.0` for square UMAP plots.

### Multi-Line Time Course

Show temporal dynamics across conditions with confidence bands.

```python
line_colors = [GRAY["300"], RUST["300"], BLUE["300"]]  # ctrl, treat1, treat2
for i, (label, y_mean, y_err) in enumerate(conditions):
    ax.plot(t, y_mean, color=line_colors[i], label=label, zorder=2)
    ax.fill_between(t, y_mean - y_err, y_mean + y_err,
                    alpha=ALPHA["band"], color=line_colors[i])

ax.set_xlabel("Time (h)")
ax.set_ylabel("Fold change")
loc, _ = find_best_legend_loc(ax, n_items=len(conditions))
ax.legend(loc=loc, frameon=False)
```

**Line plot legend tip:** `find_best_legend_loc()` includes a line-crossing penalty — regions where lines pass through are penalized 5x more than scattered points. For time courses where lines fan out from a common origin, the algorithm typically places the legend at the opposite corner from the highest line.

### Violin + Strip Plot

Show distribution shape with individual data points overlaid. Open-circle means for emphasis.

```python
parts = ax.violinplot(data, positions=range(1, n+1), showextrema=False,
                      showmedians=False)
pal = [GRAY["200"], RUST["200"], RUST["300"], RUST["400"]]  # gray ctrl, rust gradient
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(pal[i])
    pc.set_alpha(ALPHA["violin"])
    pc.set_edgecolor("none")

# Individual points (small black dots)
for i, d in enumerate(data):
    jitter = np.random.uniform(-0.08, 0.08, len(d))
    ax.scatter(np.full_like(d, i + 1) + jitter, d, s=8, c="black",
               alpha=0.5, zorder=3)

# Open-circle means
means = [np.mean(d) for d in data]
ax.scatter(range(1, n+1), means, s=50, facecolors="white",
           edgecolors="black", linewidths=1.0, zorder=5, clip_on=False)
```

**Style notes:** `GRAY["200"]` violins for control, rust gradient for treatment doses. Always overlay individual points (transparency matters). Open-circle means give a clear visual anchor.

### Grouped Bar Chart

Side-by-side bars for multi-condition comparisons.

```python
x = np.arange(len(readouts))
width = 0.25
grouped_colors = [GRAY["200"], RUST["300"], SAGE["300"]]  # ctrl, treat1, treat2

for i, cond in enumerate(conditions):
    ax.bar(x + i * width, vals[i], width, color=grouped_colors[i],
           edgecolor="none", alpha=ALPHA["bar"], label=cond)
    ax.errorbar(x + i * width, vals[i], yerr=errs[i], fmt="none",
                ecolor="black", elinewidth=0.8, capsize=2)

ax.set_xticks(x + width)
ax.set_xticklabels(readout_labels)
# trim_axes(fig) pads the categorical x-axis past the outer grouped bars.

loc, _ = find_best_legend_loc(ax, n_items=len(conditions))
ax.legend(loc=loc, frameon=True, facecolor="white", edgecolor="none",
          framealpha=0.9)
```

### ROC Curves

Diagnostic performance curves with AUC in legend text.

```python
for name, fpr, tpr, auc, col in models:
    ax.plot(fpr, tpr, color=col, lw=1.5, label=f"{name} (AUC={auc:.2f})")

# Diagonal reference
ax.plot([0, 1], [0, 1], "--", color="gray", lw=0.5, alpha=0.5)

ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_aspect("equal")

ax.legend(loc="lower right", frameon=True, facecolor="white",
          edgecolor="none", framealpha=0.9)
```

**Style notes:** ROC curves always need equal aspect ratio. Put AUC in the legend label string. Lower-right legend is canonical (away from the curves).

### Kaplan-Meier Survival Curves

Step functions with confidence bands and censoring marks.

```python
for name, t, surv, surv_lo, surv_hi, col in groups:
    ax.step(t, surv, where="post", color=col, lw=1.5, label=name)
    ax.fill_between(t, surv_lo, surv_hi, alpha=0.12, color=col, step="post")

# Censoring marks — open circles with colored edge
for censor_t, censor_s, col in censoring_events:
    ax.scatter(censor_t, censor_s, s=20, facecolors="white",
               edgecolors=col, linewidths=0.8, zorder=4, clip_on=False)

ax.set_xlabel("Time (months)")
ax.set_ylabel("Survival probability")
ax.set_xlim(0, max_time)
ax.set_ylim(0, 1.05)

ax.legend(loc="lower left", frameon=True, facecolor="white",
          edgecolor="none", framealpha=0.9)
```

**Style notes:** Use `step` (not `plot`) for survival curves — survival is piecewise constant. Open-circle censoring marks with colored edges matching the group. Lower-left legend is canonical (curves start high, drop down).

### Waterfall Plot

Sorted treatment effects for clinical trial response visualization.

```python
effects = np.sort(effects)[::-1]  # sort descending
bar_colors = [RUST["300"] if e > 0 else GRAY["200"] for e in effects]
ax.bar(range(n), effects, color=bar_colors, edgecolor="none", width=0.8)

ax.axhline(0, color="black", lw=0.5)
ax.set_xlabel("Patient")
ax.set_ylabel("Tumor change (%)")
ax.set_xticks([])  # no individual patient labels

# Clinical threshold lines
ax.axhline(20, color=RUST["300"], ls="--", lw=0.5, alpha=0.5)
ax.axhline(-30, color=BLUE["300"], ls="--", lw=0.5, alpha=0.5)
ax.text(n + 0.5, 20, "PD", va="center", fontsize=7, color=RUST["400"])
ax.text(n + 0.5, -30, "PR", va="center", fontsize=7, color=BLUE["300"])
```

**Style notes:** Sorted descending. Rust bars above zero, gray below. +20% = progressive disease (PD), -30% = partial response (PR). No x-tick labels (patients are anonymous). Threshold labels at right edge.

### Synbio / Circuit Paper Style (Reference Figure)

Reproduce the warm, high-density style from synbio/circuit biology papers: hexbin density scatters with warm colormaps, dose-response curves with sigmoidal fits, distribution histograms, and cream background grouping — all with our retro floating axes.

```python
from matplotlib.patches import FancyBboxPatch
from scipy.optimize import curve_fit
from nature_figure_utils import (
    retro_style, trim_axes, figsize_nature, save_for_review,
    scatter_outlined, find_best_legend_loc, place_stat_text,
    add_panel_labels, auto_pad_figure, BG_COLORS,
    RUST, GRAY, BLUE, GOLD, SAGE, INK, BG, ALPHA,
    CMAP_RUST, CMAP_BLUE,
)

colors = retro_style()  # signature palette

fig, axd = plt.subplot_mosaic(
    [["a", "b"], ["c", "d"]],
    figsize=figsize_nature("double", aspect=0.85),
    layout="constrained",
)

# Cream background for experimental data group
axd["a"].set_facecolor(BG_COLORS["cream"])
axd["b"].set_facecolor(BG_COLORS["cream"])

# Panel a: Hexbin density scatter (log axes, warm colormap)
axd["a"].hexbin(x, y, gridsize=25, cmap=CMAP_RUST, mincnt=1,
                xscale="log", yscale="log", linewidths=0.3,
                edgecolors=INK, alpha=0.9)
axd["a"].set_xscale("log")
axd["a"].set_yscale("log")
axd["a"].set_xlabel("Reporter (AU)")
axd["a"].set_ylabel("Phosphorylation (AU)")
# Compact stat annotation (reference style)
axd["a"].text(0.05, 0.95, f"$\\mu$ = {mean:.0f}\n$n$ = {n}",
              transform=axd["a"].transAxes, va="top", ha="left", fontsize=7,
              bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=2))

# Panel b: Dose-response with sigmoidal fit
def hill(x, top, ec50, n_hill, bottom):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** n_hill)

# Open circles (small-N style) — error bars + separate scatter for clip_on=False
axd["b"].errorbar(doses, response, yerr=sem, fmt="none", ecolor="black",
                  elinewidth=0.8, capsize=3, capthick=0.8, zorder=2)
axd["b"].scatter(doses, response, s=30, facecolors="white", edgecolors="black",
                 linewidths=0.8, zorder=4, clip_on=False)
x_fit = np.logspace(-1, 3, 200)
axd["b"].plot(x_fit, hill(x_fit, *popt), color=RUST["300"], lw=1.5)
axd["b"].set_xscale("log")
axd["b"].text(0.95, 0.05, f"EC$_{{50}}$ = {ec50:.1f} nM\n$n_H$ = {n_hill:.1f}",
              transform=axd["b"].transAxes, va="bottom", ha="right", fontsize=7,
              bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=2))

# Panel c: Distribution histograms (log-scale x)
axd["c"].hist(ctrl, bins=np.logspace(1, 4, 40), alpha=0.5, color=GRAY["200"],
              label="Control", edgecolor="none")
axd["c"].hist(treat, bins=np.logspace(1, 4, 40), alpha=0.5, color=RUST["300"],
              label="Treated", edgecolor="none")
axd["c"].set_xscale("log")
axd["c"].legend(loc="upper right", frameon=True, facecolor="white",
                edgecolor="none", framealpha=0.9)

# Panel d: Model vs data (outlined scatter + identity line)
scatter_outlined(axd["d"], x_model, y_data, s=10, c=residuals, cmap=CMAP_RUST)
axd["d"].plot(lims, lims, "--", color=INK, lw=0.8, alpha=0.6, zorder=1)
axd["d"].set_xscale("log"); axd["d"].set_yscale("log")
place_stat_text(axd["d"], f"$R^2$ = {r2:.2f}")

auto_pad_figure(fig, axd)
trim_axes()
add_panel_labels(fig, axd, pad_x=-0.02)

```

**Key style notes:**
- Use `retro_style()` (default) — the signature palette IS the synbio style
- Hexbin with `cmap=CMAP_RUST`, `edgecolors=INK`, `linewidths=0.3` for density scatters
- Cream backgrounds via `ax.set_facecolor(BG_COLORS["cream"])` — color stays within the plot canvas (axes face only). Use FancyBboxPatch only when you need the background to extend beyond the axes (see Sub-Figure Organization below).
- EC₅₀ / Hill coefficient annotations use white bbox (`facecolor="white", edgecolor="none"`)
- Log-scale axes are common — `trim_axes()` automatically skips tick extension on them
- Fold-change annotations use bold, colored text: `fontsize=9, fontweight="bold", color=RUST["400"]`

---

## Sub-Figure Organization (Backgrounds, Grouping, Connectors)

High-impact papers use colored rounded boxes to visually group related panels. Not every panel needs a box — use them selectively to highlight conceptual groupings, while other panels sit on the plain white canvas.

### Rounded-Box Panel Grouping

Group related panels inside a colored `FancyBboxPatch`. Panels inside the box get matching `ax.set_facecolor()` so the box blends seamlessly. Panels outside the box keep the default white background.

```python
from matplotlib.patches import FancyBboxPatch

BG_COLOR = BG_COLORS["cream"]  # warm cream for the group

fig, axd = plt.subplot_mosaic(
    [["a", "b"], ["c", "c"]],
    figsize=(14, 8), layout="constrained",
)

# Axes inside the group: match the box color
axd["a"].set_facecolor(BG_COLOR)
axd["b"].set_facecolor(BG_COLOR)
# Panel c: no box — stays white (default)

# ... plot data, trim_axes() ...

# Add rounded box AFTER fig.canvas.draw()
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
fig_inv = fig.transFigure.inverted()

def get_group_bbox(axes_list):
    """Raw union of tight-bboxes in figure-fraction coords (no padding)."""
    bboxes = [fig_inv.transform_bbox(ax.get_tightbbox(renderer))
              for ax in axes_list]
    return (min(b.x0 for b in bboxes), min(b.y0 for b in bboxes),
            max(b.x1 for b in bboxes), max(b.y1 for b in bboxes))

# Compute raw bboxes
ab_x0, ab_y0, ab_x1, ab_y1 = get_group_bbox([axd["a"], axd["b"]])
c_x0, c_y0, c_x1, c_y1 = get_group_bbox([axd["c"]])

# Gap-aware padding: box must not overlap panel c's tight bbox
pad = 0.018
gap = ab_y0 - c_y1  # vertical space between groups
min_gap = 0.025      # minimum visible white gap
safe_pad_bottom = max(min(pad, gap - min_gap), 0)

fig.patches.append(FancyBboxPatch(
    (ab_x0 - pad, ab_y0 - safe_pad_bottom),
    (ab_x1 + pad) - (ab_x0 - pad),
    (ab_y1 + pad) - (ab_y0 - safe_pad_bottom),
    boxstyle="round,pad=0,rounding_size=0.02",
    facecolor=BG_COLOR, edgecolor="none",
    transform=fig.transFigure, zorder=-1,
))
```

**Key rules:**
- **Axes facecolor must match the box** — if the box is `#F0EBE1`, set `ax.set_facecolor("#F0EBE1")` for every axes inside that box. Mismatched white axes inside a colored box looks broken.
- **Gap-aware padding** — compute the gap between the box group and its nearest neighbour, then clip: `safe_pad = max(min(pad, gap - min_gap), 0)`. This prevents the box from ever overlapping adjacent panels.
- **`boxstyle` pad MUST be 0** — `boxstyle="round,pad=0,rounding_size=0.02"`. The boxstyle `pad` silently expands the patch beyond specified coordinates. Setting it to anything >0 causes overlap because the expansion isn't accounted for in gap calculations. Handle all spacing explicitly.
- **Not every panel needs a box** — use boxes to group related panels; leave standalone panels on the white canvas.
- **Large rounded corners**: `rounding_size=0.02` for modern look.
- **No edge**: Always `edgecolor="none"`.
- **zorder=-1**: Behind all plot elements.
- **Place panel labels AFTER backgrounds** so labels render on top.

**Box color palette** (also available as `BG_COLORS` dict in `nature_figure_utils`):

```python
from nature_figure_utils import BG_COLORS
bg = BG_COLORS["beige"]  # "#F0EBE1"
```

| Color | Key | Hex | Use for |
|-------|-----|-----|---------|
| Warm beige | `"beige"` | `#F0EBE1` | General panel grouping |
| Cool blue-gray | `"blue_gray"` | `#E6EBF0` | Computational / results panels |
| Light green | `"green"` | `#E0EDDF` | Model / pipeline panels |
| Light pink | `"pink"` | `#F2E4E8` | Perturbation / treatment panels |
| Cream | `"cream"` | `#FAF3E8` | Warm neutral grouping |
| Light gray | `"light_gray"` | `#F2F2F2` | Subtle grouping |

### Connecting Arrows Between Groups

For workflow figures, add arrows to show data/analysis flow between panel groups:

```python
from matplotlib.patches import FancyArrowPatch

arrow = FancyArrowPatch(
    (0.5, y_start),  # figure-fraction coordinates
    (0.5, y_end),
    arrowstyle="->,head_width=6,head_length=4",
    color="#888888", linewidth=1.0,
    transform=fig.transFigure, clip_on=False,
)
fig.patches.append(arrow)
```

### Group Titles

Add italic text above a panel group to label conceptual sections:

```python
fig.text(0.5, y_above_group, "Cognitive aging associations",
         ha="center", fontsize=8, fontstyle="italic",
         transform=fig.transFigure)
```

---

## High Ink-to-Canvas Ratio Principles

Publication figures should be **dense** with information. Every pixel should convey data or essential context.

### DO
- Tighten axis limits to hug the data: `ax.set_xlim(x.min() - margin, x.max() + margin)`
- Use `np.percentile(data, [1, 99])` for limits when outliers stretch the axis
- Fill the panel area — if data only occupies a corner, adjust limits or aspect ratio
- Use `layout="constrained"` + `auto_pad_figure()` for tight multi-panel spacing
- Place legends inside the plot in data-sparse regions when possible
- Overlay individual data points on summary statistics (boxes, bars)

### DON'T
- Leave large empty regions inside any panel
- Use default axis limits when they add unnecessary whitespace
- Create oversized figures for sparse data
- Use separate legend panels when an in-plot legend would suffice
- Leave axis limits on auto when the data occupies only a fraction of the range
- **Make tall, narrow panels** — prefer wide or square panels. For multi-panel grids, use `aspect=0.6-0.85` (wider than tall). Tall panels waste vertical space and compress the x-axis, making data harder to read. If a 3x3 grid produces tall panels, reduce the figure aspect ratio. For bar charts, use `height=0.3-0.45` for barh and `width=0.4-0.5` for vertical bars to keep compact

---

## Dependencies

Install before running visualization scripts:
```bash
pip install matplotlib seaborn pandas numpy cycler adjustText scipy scikit-learn umap-learn
```

---

## AI Visual Review Loop (MANDATORY)

**After saving ANY figure — including every re-render during iterative fixes — you MUST perform this review.** This is the core quality gate. Never skip the review just because "only one thing changed." Overlap and layout regressions are caught visually, not by reasoning about code.

### Procedure

**Step 0 — Pre-render placement check (BEFORE saving):**
Verify that the code uses the smart placement utilities. This is a code-level check, not a visual check:
- [ ] Every `ax.legend()` call uses `loc=find_best_legend_loc(ax)[0]` or has an explicit justification for a hardcoded location
- [ ] Every multi-point annotation uses `smart_annotate()` (not manual xy/xytext computation)
- [ ] Every stat text box uses `place_stat_text()` (not manual `ax.text()` with hardcoded position)

**If any placement is hardcoded without justification, refactor to use the smart utilities BEFORE proceeding.**

1. **Run programmatic overlap detection** BEFORE visual review:
   ```python
   from nature_figure_utils import detect_overlaps
   results = detect_overlaps(fig, axd, padding=2.0)
   if results:
       for r in results:
           print(f"[{r['severity']}] {r['category']} {r['panel_a']}-{r['panel_b']}: "
                 f"{r['elem_a']} ↔ {r['elem_b']} ({r['overlap_area_px']:.0f}px²)")
   ```
   **Fix ALL severe and moderate overlaps before proceeding.** Minor overlaps may be acceptable but should be noted.
2. **Save a low-res review image** using `save_for_review(fig, "figure_review.png", dpi=72)` (72 dpi is enough for layout checks while keeping file size minimal)
3. **Read the image** using the `Read` tool to visually inspect it
4. **Evaluate against the checklist below**
5. **If ANY issue is found**: fix it in code, re-render, re-run `detect_overlaps()`, and **review again from step 1**
5. **Maximum 3 iterations** — if issues remain after 3 rounds, report them to the user
6. **Final save** at 600 dpi PNG + PDF after the last successful review
7. **Clean up review images** — delete all `*_review.png` files after the review loop completes:
   ```python
   import os
   for f in ["figure_review.png"]:
       if os.path.exists(f):
           os.remove(f)
   ```

### Review Checklist

Evaluate EVERY item. Be strict — Nature/Science figures have high visual standards.

#### 1. Overlap Detection

Check EVERY pair of text/visual elements within each panel. "Close enough to touch" = FAIL.

**Data vs decorations:**
- [ ] Legend box does NOT overlap any data points, lines, bars, or error bars
- [ ] Legend box does NOT overlap significance brackets or bracket text — in bar charts with both, verify vertical clearance
- [ ] Text annotations do NOT overlap any data points, markers, or error bars
- [ ] Stat text boxes (R², p-value) are in a data-sparse region — not covering data points
- [ ] Colorbars do NOT overlap adjacent panels or data

**Text vs text (CRITICAL — most commonly missed):**
- [ ] Text annotations do NOT overlap each other (check EVERY pair)
- [ ] Text annotations do NOT overlap legend boxes
- [ ] Legend box does NOT overlap axis titles, region labels, or other text
- [ ] Boxed annotations (bbox-styled text) do NOT overlap other boxed annotations
- [ ] Point labels that are spatially close in data space MUST be checked for pixel-space collision — two points with similar coordinates will have overlapping labels unless offset
- [ ] Region/zone labels (e.g., "Biological regime", "Constructive") do NOT overlap legends or annotations

**Annotations vs titles/data:**
- [ ] Custom annotations (brackets, arrows, callout text) do NOT overlap panel titles or subtitles — this is the most commonly missed overlap because annotations in data coordinates can collide with titles in figure coordinates when the data range is small. Use axes-fraction coordinates (`transform=ax.transAxes`) for annotations near the top of the plot.
- [ ] Custom annotations (brackets, callout text) do NOT overlap data elements (bars, error bars, markers) — a bracket grouping bars must sit fully above the tallest bar + error bar with visible clearance, not touching or intersecting
- [ ] No text or annotation is clipped at axes boundaries or figure edges — check all four edges, especially the right edge for right-aligned annotations

**Structural:**
- [ ] Axis labels do NOT overlap tick labels
- [ ] Tick labels do NOT overlap each other (especially rotated ones)
- [ ] Panel labels (a, b, c) do NOT overlap axis labels or titles
- [ ] **Leader-line annotations do NOT overlap axis tick labels** — check that annotation text placed near the axis boundary doesn't collide with tick labels. The fix is ALWAYS to annotate AWAY from the nearest axis (see Condition 0 in leader-line placement). If annotations are on the LEFT side of a panel, they WILL overlap y-axis tick labels.
- [ ] **Leader lines do NOT cross each other** — lines from data points to labels must not intersect. This happens when the data-to-label y-mapping is not monotonic (highest data point must map to highest label position)
- [ ] **Heatmaps have NO frame** — no visible spines, no tick marks, no colorbar outline. Group/category labels should not overlap the plot area

**How to check:** For every text element you placed (annotations, labels, legends, region text), mentally trace a rectangle around it and check if ANY other rectangle intersects it. When in doubt, it overlaps. Be paranoid.

**Common fixes:** Move legend with `loc=` or `bbox_to_anchor=`, use `adjustText` for point annotations, increase figure size, adjust tick frequency, remove redundant labels, offset annotations with `xytext`.

#### 2. Ink-to-Canvas Ratio
Nature figures should be DENSE with information — minimal wasted space.

- [ ] No large empty regions inside the plot area (data should fill the axes)
- [ ] Axis limits are tight around the data (no unnecessary padding)
- [ ] For diverging/bidirectional plots: both directions of the axis have enough range to make the smaller-magnitude data visually readable — do NOT let auto-scaling compress one side into a sliver because the other side dominates
- [ ] Margins between axis labels and the plot border are minimal
- [ ] Space between tick labels and axis labels is not excessive
- [ ] If multi-panel: inter-panel spacing is compact, not loose
- [ ] Overall figure dimensions match the content — no oversized canvas for sparse data

**Common fixes:** Tighten `xlim`/`ylim`, reduce `figsize`, reduce `pad` in constrained layout, use `bbox_inches="tight"`.

#### 3. Text Legibility and Rendering
- [ ] Axis labels are large enough to read (minimum ~12pt effective size at final print dimensions)
- [ ] Tick labels are readable and not too small
- [ ] Legend text is readable
- [ ] Title (if any) is appropriately sized
- [ ] Annotation text is large enough and has sufficient contrast against background
- [ ] No text is clipped or cut off at figure edges
- [ ] **No missing glyphs / box characters (□)** — if ANY character renders as a box, square, or tofu, the font is missing that glyph. This is a FAIL.

**Minimum text size rule:** ALL text must be at least 7pt at print dimensions — this is a HARD RULE (see "7pt minimum for ALL text" above). The theme defaults (7pt tick labels, 7pt axis labels) are calibrated for this. Do NOT increase font sizes beyond the theme defaults — oversized text looks unprofessional in multi-panel figures. If text appears too small at print size, the figure should use a wider column width (`"1.5col"` or `"double"`) rather than inflating font sizes.

**Unicode glyph rule:** NEVER use Unicode math symbols directly in matplotlib text (e.g., `⟨`, `⟩`, `≤`, `±`, `×`). These frequently fail to render across fonts and platforms. ALWAYS use LaTeX mathtext instead:
- `⟨k⟩` → `r"$\langle k \rangle$"`
- `≤` → `r"$\leq$"`
- `±` → `r"$\pm$"`
- `×` → `r"$\times$"`
- `Δ` → `r"$\Delta$"` (or keep if in a font that supports Greek; safer to use LaTeX)

When reviewing: look for any `□` or garbled characters in the rendered image. A single missing glyph = immediate FAIL.

**Common fixes:** Replace Unicode with LaTeX mathtext, increase `fontsize`, add `path_effects` for contrast, adjust `figsize` to give text more room.

#### 4. Legend Placement
- [ ] Legend does NOT overlap or obscure ANY data points — even partial occlusion is a FAIL
- [ ] Legend is compact (no excessive padding or spacing)
- [ ] **Verify `find_best_legend_loc()` was used** — if the legend location was hardcoded without using the density scanner, this is a FAIL. The AI must programmatically select placement.
- [ ] If `find_best_legend_loc()` returned count > 0 and the legend still overlaps visually, try `bbox_to_anchor` outside placement
- [ ] If legend items are many (>5), prefer placing outside the plot

**Common fixes:** Re-run `find_best_legend_loc()`, try `ncol=2` for compact horizontal layout, use `bbox_to_anchor` to place outside if all regions have data.

#### 5. Layout Tightness
- [ ] No excessive whitespace around the figure perimeter
- [ ] Subplot spacing is compact but not cramped
- [ ] Colorbars are appropriately sized (not too wide, not too far from their panel)
- [ ] The figure would look good at its intended print width (single column: ~3.5in, double column: ~7in)

### Review Response Format

After each review iteration, state:
```
REVIEW ITERATION [N]/3
- Overlap: [PASS/FAIL — details]
- Ink-to-canvas: [PASS/FAIL — details]
- Text legibility: [PASS/FAIL — details]
- Legend: [PASS/FAIL — details]
- Layout: [PASS/FAIL — details]

ACTION: [PASS — no changes needed / FIXING — list of changes to make]
```

---

## Panel Labels (Opt-In)

Only add panel labels when the user explicitly asks for them.

- **Font:** Bold Arial, 10pt
- **Position:** Top-left of each panel's tight bounding box
- **Alignment:** Labels sharing a grid starting-column get the same x. Labels sharing a starting-row get the same y.
- **Placed after `fig.canvas.draw()`** so all text extents are computed

```python
from nature_figure_utils import add_panel_labels
add_panel_labels(fig, axd)  # only when requested
```

## Key Implementation Details

### Overlap Prevention (Multi-Panel)
- `layout="constrained"` tells matplotlib to account for all decorations
- `auto_pad_figure()` starts at 0.12in padding, checks for tight-bbox overlaps (>5px threshold), escalates by 1.5x until clean (max 8 iterations)
- `check_overlaps()` checks inter-panel tight-bbox overlap for layout padding
- **`detect_overlaps(fig, axd)`** — comprehensive element-level overlap scanner (text-text, legend-data, text-data, cross-panel). Returns structured report with severity. Use in the AI review loop as a programmatic check BEFORE visual inspection:
```python
from nature_figure_utils import detect_overlaps
results = detect_overlaps(fig, axd, padding=2.0)
for r in results:
    print(f"[{r['severity']}] {r['category']} | {r['panel_a']}-{r['panel_b']} | "
          f"{r['elem_a']} ↔ {r['elem_b']}")
```

### Common Mistakes
- **Hardcoding legend location without `find_best_legend_loc()`** — the #1 source of legend-data overlap. ALWAYS call the density scanner. `loc="upper left"` might be right for one dataset but wrong for the next.
- **Manual annotation layout instead of `smart_annotate()`** — computing xy/xytext positions by hand is error-prone and produces crowded labels. `smart_annotate()` handles sorting, gap computation, and direction selection automatically.
- **Hardcoded stat text position** — `ax.text(0.05, 0.95, ...)` works only if the upper-left is data-sparse. Use `place_stat_text()` to scan all corners.
- Using `hspace`/`wspace` without `constrained_layout` — decorations still collide
- Placing labels in axes coordinates — they shift when data range changes
- Not calling `fig.canvas.draw()` before reading tight bounding boxes — returns stale positions
- Making figures too large for sparse data — wastes canvas, looks unprofessional
- Leaving axis limits on auto when data occupies only a fraction of the range
- Forgetting to call `trim_axes()` on scatter/bar plots — missing trimmed axes
- **Trimming histogram axes** — `trim_axes()` on histograms/density plots creates dead space above bars where legends float disconnected from data. ALWAYS exclude histogram axes: `trim_axes(fig, exclude=[ax_hist1, ax_hist2])`. Only scatter, bar, line, and box plots benefit from trimmed spines.
- **Not resetting style for heatmaps** — just restoring spines is insufficient. Use `mpl.rc_context()` + `mpl.rcdefaults()` to fully reset.
- **Long tick labels causing overlap** — abbreviate to short forms: "Ctrl", "DrA", "S1". If abbreviation isn't possible, rotate labels.
- **`bbox_to_anchor` outside axes collapsing constrained_layout** — prefer inside placement for multi-panel figures.
- **Complex mosaic grids (>3 columns) with constrained_layout** — prefer simpler grids with `width_ratios`.
- **Annotations placed AMONG data instead of OUTWARD** — `smart_annotate()` now places labels past ALL data points (not just annotated ones). If using manual `add_elbow_annotation()`, always compute the label column from the FULL data extent, not the annotated subset.
- **Y-axis spine not covering strip-plot dots** — `trim_axes()` now extends spines to the data range, but you MUST still set ylim to include all data. Without explicit ylim, dots below the first tick appear to float outside the axis.
- **Forest plot left spine looks broken** — categorical y-axes should NOT use `trim_axes()`. Hide the left spine (`ax.spines["left"].set_visible(False)`) and only trim the continuous x-axis manually.
- **Significance bracket text overlapping bracket line** — use `y + h + 0.35` for text offset and `h=0.35` for bracket height. Anything less than 0.3 offset causes text to touch the line. Also increase ylim to accommodate the tallest bracket + text.
- **Log-scale axes with tick extension** — `trim_axes()` generates ticks at every power of 10 and extends outward when the axis limit exceeds the nearest power-of-10 tick. For example, `xlim=(0.05, 500)` produces ticks at `[0.1, 1, 10, 100, 1000]` so the spine covers data up to 500. You can still set explicit power-of-10 limits (`ax.set_xlim(0.1, 1000)`) for exact control, but it's no longer required. Do NOT manually set ticks on log axes before calling `trim_axes()`.
- **Scatter dots clipped at axis edges** — ALWAYS use `clip_on=False` for all scatter/point plots. For small-N data (dose-response, calibration), use open circles: `ax.scatter(x, y, s=30, facecolors="white", edgecolors="black", linewidths=0.8, clip_on=False)`. Clipped dots at the axis edge look broken.
- **Background color extending beyond axes** — use `ax.set_facecolor(BG_CREAM)` to keep background within the plot canvas. Only use `FancyBboxPatch` when grouping multiple panels together (see Sub-Figure Organization).
- **Volcano/scatter legend overlapping annotations** — when annotations are on the right side, the legend often ends up in the same region. Use `frameon=True, facecolor="white", edgecolor="none", framealpha=0.9` for a white backdrop that sits cleanly over annotation lines.
- **Panel labels crossing into neighboring panels** — `add_panel_labels()` uses `col_x[colspan.start] + pad_x` to position labels. With negative `pad_x`, labels shift LEFT past the panel boundary (e.g., "b" inside panel a). **FIX**: the function now clamps with `col_left_boundary` so labels never cross. Applied to `programs/ai-skills/nature-figure/nature_figure_utils.py`. **CRITICAL**: when copying `nature_figure_utils.py` from any source, verify the clamping code exists — grep for `col_left_boundary` and `floor_x` in `add_panel_labels`. If missing, the fix was lost during copy and must be re-applied.
- **Line-plot legend overlapping lines** — `find_best_legend_loc()` now penalizes line crossings 5x heavier than point counts. Pass `n_items=` for accurate footprint sizing.
- **Mixed-type multi-panel figures (text + data + image panels)** — `constrained_layout` only considers ticklabels, axis labels, titles, and legends. It ignores `ax.text()` artists. Text panels that use `ax.text()` will overflow into adjacent panels. **ROOT CAUSE**: the layout engine cannot account for arbitrary text artists. **Two rules prevent this**: (1) Use `setup_text_panel(ax, bg_color=...)` instead of `axis('off')`, then place ALL text with `transform=ax.transAxes` so it's positioned relative to the axes rectangle and stays within it. (2) NEVER place text at data coordinates outside the axes limits (e.g., `ax.text(0.5, 13, ...)` when ylim is 5.5 — this creates a massive tight-bbox overflow that no layout fix can resolve). Keep fontsize at 5.5pt and text content compact (5-8 lines max). Use `layout="constrained"` with `auto_pad_figure()` for final spacing. Do NOT use `resolve_overlaps()` on figures with text panels — uniform shrinking makes text overflow WORSE because text at fixed fontsize doesn't scale with axes.
- **Embedding PNGs with imshow causes inconsistent font sizes** — when mixing recreated plots (which use retro_style fonts) with embedded PNG images from prior analyses, the font sizes mismatch visually. ALWAYS recreate plots from source data rather than embedding PNGs. The only exception is complex schematics (architecture diagrams, UI screenshots) that cannot be recreated programmatically.
- **Composite figure delivered as a flat image ("0 fonts, 1 image")** — slide/illustration "layout tools" silently rasterise the whole multi-panel composite, killing selectable text and zoom. Detect with `pdffonts figure.pdf`. FIX: re-composite the original per-panel vector PDFs with `composite_vector_pdf()` (see "Vectorized Composite Assembly"), not by re-exporting from the tool. Heavy point clouds should be rasterised in-panel with `rasterized=True`, everything else stays vector.
- **Stale composite (panel regenerated after assembly)** — re-running a component panel does NOT update the multi-panel figure that embedded it. Before shipping, verify no source panel `mtime` is newer than the composite, and re-assemble if so.
- **Spaghetti/trajectory plots with too few visible lines** — when plotting individual subject trajectories, ensure each subject is plotted as a separate `ax.plot()` call with `alpha=0.3-0.5` and `lw=0.8`. Group means should use `lw=2.0` and full opacity. Sort subjects so the mean line is plotted last (highest zorder). Common failure: plotting only the mean or aggregating subjects.
- **Wrong data loaded for pathway enrichment** — when CSV files have multiple cell types in a `cell_type` column, always filter for the correct cell type before plotting. Plotting unfiltered data shows pathways from the wrong cell type.
- **Compact layout for information-dense figures** — for 6-panel figures, use `aspect=1.0-1.2` (taller) rather than `aspect=0.85`. Use `auto_pad_figure()` after all plotting. Keep text panel fontsize at 6-6.5pt maximum. Abbreviate axis labels aggressively ("Expr." not "Expression", "Adj. p" not "Adjusted p-value").
- **Bump chart y-axis stretched by outliers** — when one category jumps to a very high rank (e.g., rank 20), it compresses all other data into a narrow band. Fix: cap the y-axis at a reasonable range (e.g., rank 12) and annotate outliers with arrows, or only show the top N stable targets.
- **Titles colliding with outside legends in multi-panel figures** — when using `bbox_to_anchor` to place legends above a panel, the legend and title compete for the same vertical space. In dense multi-panel figures (6+ panels), drop panel titles entirely — the panel label (a, b, c) plus axis labels provide sufficient context. Only use titles for standalone or 2-panel figures.

### Bar charts and `trim_axes()` interaction

`trim_axes()` is bar-aware: for `ax.bar`/`ax.barh` it pads the categorical-axis
spine and limit past the outer bar edges (so end bars get a gap) and trims the
value axis normally. **Just call `trim_axes(fig)` — no exclusion, no manual
`margins()`/`set_xlim` needed.**

This relies on detecting matplotlib `BarContainer`s, so the bars must be drawn
with `ax.bar()`/`ax.barh()` (not hand-built `Rectangle` patches). If you draw
bars as raw patches, `trim_axes()` can't detect them — either switch to
`ax.bar`/`ax.barh`, or exclude the panel and pad it yourself:

```python
exclude_bars = {ax_custom}              # panels with hand-built bar patches
trim_axes(fig, exclude=exclude_bars)
for ax_b in exclude_bars:
    ax_b.margins(x=0.08)                # padding survives — trim won't touch it
```

### Inverted y-axis coordinates

For `barh` or any plot with inverted y (`set_ylim(high, low)`), axes-fraction coordinates invert too:
- `(0.0, 0.0)` = visual TOP-LEFT
- `(1.0, 1.0)` = visual BOTTOM-RIGHT

`bbox_to_anchor=(x, 0.0)` places at VISUAL TOP (not bottom). Always test with inverted axes or place outside the frame.

### Legend placement for bar charts

1. **ABOVE the panel** (`bbox_to_anchor=(0.0, 1.02)`, outside frame) — zero overlap, always safe
2. **RIGHT of the panel** (`bbox_to_anchor=(1.02, 0.5)`) — if room exists
3. **Inside** — last resort, always verify visually; bar charts rarely have safe empty space

Never place legend at "lower right" inside a barh panel — short bars look like empty space but the legend box overlaps bar edges.

### Spine continuity

When `xlim` extends beyond the last tick, the spine ends at that tick but blank space continues. This creates a broken-looking axis.

**Fix:** Set xlim to end AT a tick value. If using `trim_axes()`, it handles this. If excluded, set explicitly: `ax.set_xlim(0, 12)` not `(0, 12.5)`.

### Multi-panel sizing

- **3x3 grid:** `figsize=(7.2, 5.4)` gives ~1.5:1 wide panels
- Never `aspect > 1.0` for grids with 3+ rows — produces tall narrow panels
- `constrained_layout` with `fig.get_layout_engine().set(h_pad=0.02, w_pad=0.02, hspace=0.05, wspace=0.05)` for minimal gaps
- Mix of text + data panels: use `height_ratios` to give text panels more space
- Fill every panel — spread content across full area, never cluster at one end with dead space elsewhere

### Heatmap annotation text color

Never hardcode a threshold. Colormaps vary in direction and linearity. Always compute brightness from the actual colormap RGBA:
```python
from matplotlib.colors import Normalize
norm = Normalize(vmin=vmin, vmax=vmax)
rgba = cmap(norm(val))
brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
text_color = "white" if brightness < 0.5 else INK
```

### Never fabricate figure data

Every data point in a figure must come from real analysis outputs. If data is missing, show it honestly (e.g., 0-count bars). Never use templates, simulations, or placeholder values to fill gaps.

## Nature-Parity QA Checklist (distilled from annotation/compactness/QA work)

> Provenance: these are **design rules and methodology** distilled from a focused nature-figure hardening pass (leader-line non-crossing, baked compactness scale, density colormap, overlap-in-`save()`, reference-figure reproduction). The rules are transcribed as guidance; the underlying algorithmic *implementations* (the geometric no-cross solver, per-side column placement, the `FIGURE_SCALE` plumbing) are **not reproduced here** — treat those as "to port from source" when the real diff is available. Everything below you can apply by hand today.

### 9 design rules

1. **Annotation leader lines must never cross** — each other or the data cloud. Split labels by which side of the axis each point sits on; when a side is crowded, stack that side into ONE y-sorted column and place it just past the **local** data at the labels' own y-level (NOT the global data extent, which blows up `xlim` and produces panel-slashing leaders). Put the legend on the side **opposite** the labels — `smart_annotate` cannot see the legend box.
2. **Density/count colormaps must map dense → dark.** A sequential map whose high end is near-white makes the dense core vanish on a white page; "draw densest on top" makes it worse. Use a reversed map (dense = dark ink) for density scatter / hexbin / count fields.
3. **To raise text-to-canvas ratio, shrink the canvas ~10% — do NOT enlarge text past 7pt.** 7pt is the Nature floor and is exactly what published references use. Bake the shrink as a single scale knob (one dial for the whole gallery), not a per-figure hand-tune. A smaller canvas raises the ratio; the font never moves.
4. **"Airy" comes from dead whitespace, not panel size.** Cut it at the theme level: data margins ~0.05 → 0.03, label pad 4 → ~2.5, add tick pad, figure border ~0.08 → 0.02, tighten inter-panel spacing. Kill the dead space before touching anything else.
5. **Confidence/error bands must carry a visible mean line on top, over sorted x.** A band with no center line reads as a fog; unsorted x produces a step-discontinuity artifact; ≥3 overlapping bands blend to mud — separate them or drop opacity and always keep the mean lines legible.
6. **Heatmaps have three recurring traps:** (a) an `rcdefaults()` reset context renders heatmap text at ~10pt instead of the 7pt theme — re-assert the font; (b) narrow columns collide tick labels ("Ctrl1Ctrl2Ctrl3", "HbA1cLDL") — abbreviate or rotate; (c) a diverging colormap on all-positive data wastes half the scale — use sequential.
7. **Significance-bracket stacks must not compress the data.** Stacking brackets pushes `ylim` up until boxes/points are crushed into the bottom ~40% of the panel — reserve headroom deliberately or cap the stack.
8. **Axis limits hug the data.** No trailing empty log decades, no rounding an x-limit up to the next tick, no stretching an axis just to host label text. Tight limits are part of the ink-to-canvas standard.
9. **Forest plots need a right-hand P/q value column aligned to each row** — and it must live **inside** the panel (extend `xlim` to open a blank right region, trim the bottom spine to the tick range) so it never collides with the next panel's bold letter label. (Bonus layout rule: dense/irregular mosaics collapse when panels carry heterogeneous decorations — colorbars, log axes, rotated ticks — because auto-padding under-reserves the inter-row gutter; enforce a minimum gutter in **points** and add a cross-row tight-bbox check.)

### 4 methodology practices

1. **Figure TDD — reproduce a real published reference figure with synthetic data.** Rebuilding a known-good target (e.g. a specific Nature figure) is the fastest way to surface skill gaps, and the reproduction doubles as a rich multi-panel example for the gallery.
2. **Measure, don't eyeball, text size.** Calibrate px-per-pt by rendering known 7pt/10pt text at the target dpi, then measure both the reference and your output the same way. Compare the **text-to-panel-width ratio**, not absolute pixels — and remember the correct lever to close a gap is canvas size, not font size (rule 3).
3. **Bake `detect_overlaps()` into `save()`.** Run the overlap check on every multipanel at save time and print any collision before writing the file, so a regression can't slip into the gallery unnoticed.
4. **Separate real overlaps from bbox false-positives.** Text–text collisions are real defects; a curve's full bounding box enclosing text that actually sits in empty space is a false positive. Triage on that distinction before "fixing" anything.

## Utility Code

Copy `nature_figure_utils.py` from this skill directory into your project. Pure matplotlib — no external theme dependencies. It provides:
- `retro_style(palette)` — apply base-R-style axes, returns color palette
- `trim_axes(fig, exclude)` — trim spines to tick range, adding ticks at regular spacing to cover data (log-scale axes skip tick extension)
- `figsize_nature(columns, aspect)` — Nature column width dimensions
- `PALETTES` / `CMAPS` — curated color palettes and colormaps
- `BG_COLORS` — background colors for panel grouping (beige, blue_gray, green, pink, cream, light_gray)
- `scatter_outlined(ax, x, y, s, c)` — 3-layer outlined dots for crowded scatter plots (black bg -> white ring -> color fill)
- `find_best_legend_loc(ax, n_items)` — **scan data density + line crossings, return best legend location** (MANDATORY for all legends)
- `smart_annotate(ax, labels, points)` — **auto-layout leader-line annotations OUTWARD past all data** (MANDATORY for multi-point annotations)
- `place_stat_text(ax, text)` — **place stat text in least-crowded corner** (MANDATORY for stat boxes)
- `add_elbow_annotation(ax, ...)` / `add_elbow_annotations(ax, ...)` — low-level leader-line annotations (use `smart_annotate` instead when possible)
- `save_for_review(fig, path, dpi)` — save low-res image for AI visual review
- `add_panel_labels(fig, axes_dict, pad_x, pad_y)` — aligned panel labels (opt-in, pad_x for leftward offset)
- `auto_pad_figure(fig, axes_dict)` — iterative overlap prevention
- `check_overlaps(fig, axes_dict)` — inter-panel tight-bbox overlap for layout padding
- `detect_overlaps(fig, axes_dict, padding)` — **comprehensive overlap scanner**: text-text, legend-data, text-data, cross-panel. Returns list of dicts with severity. MANDATORY in review loop.
- `stitch_panels(panel_paths, ...)` — RASTER composite from existing PNG images (imshow)
- `composite_vector_pdf(panels, out_pdf, page_w, ...)` — **TRUE-VECTOR composite** of per-panel PDFs via PyMuPDF (selectable text, vector `a,b,c` letters, rasterise-only-heavy-layers); use instead of `stitch_panels` whenever panels exist as vector PDFs. Lazy-imports `fitz` (PyMuPDF).
