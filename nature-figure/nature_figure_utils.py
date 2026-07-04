"""
nature_figure_utils.py — Publication-quality figures with base-R-style axes.

Ying Lab visual identity: warm, low-saturation color system built on
rust/dry-blood + warm gray families. Floating trimmed spines, outward ticks,
no gridlines, #705B66 annotation ink. Pure matplotlib — no dependencies
beyond matplotlib, numpy, and cycler.

    from nature_figure_utils import (
        retro_style, trim_axes, figsize_nature, save_for_review,
        add_panel_labels, auto_pad_figure, stitch_panels,
        find_best_legend_loc, smart_annotate, place_stat_text,
        scatter_outlined, detect_overlaps, pad_categorical_axis,
        PALETTES, CMAPS, FAMILIES,
        RUST, GRAY, BLUE, GOLD, SAGE, PLUM,
        INK, BG, BG_COLORS, ALPHA,
    )

Requires: matplotlib, numpy, cycler
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import numpy as np
from collections import defaultdict
from itertools import combinations
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.container import BarContainer


# ---------------------------------------------------------------------------
# Color system — Ying Lab signature palette
# ---------------------------------------------------------------------------
# Six families, each with 6 shades (100=lightest, 600=darkest).
# 300 shades are luminance-equalized across families.
# Default shade for any family is 300 (mid-tone).
#
# Primary families (used 80% of the time):
#   RUST — hero / treatment / significant / main finding
#   GRAY — control / baseline / non-significant
# Extended families (when data demands more hues):
#   BLUE — down-regulated / cold / alternative
#   GOLD — highlight / warning / third condition
#   SAGE — growth / positive / biological (teal-shifted for colorblind safety)
#   PLUM — rare fifth condition / decorative

RUST = {"100": "#DFC7C2", "200": "#C79C93", "300": "#B3796D",
        "400": "#78483E", "500": "#57342D", "600": "#39221D"}
GRAY = {"100": "#D3D0CE", "200": "#B2ACA8", "300": "#8E8680",
        "400": "#615B56", "500": "#46413E", "600": "#2D2A28"}
BLUE = {"100": "#C8D0D9", "200": "#9EABBC", "300": "#7689A0",
        "400": "#4B5A6C", "500": "#36414E", "600": "#232A33"}
GOLD = {"100": "#E3D8BE", "200": "#CEB98C", "300": "#A08344",
        "400": "#816936", "500": "#5D4C27", "600": "#3C3119"}
SAGE = {"100": "#C7DAD5", "200": "#9CBEB5", "300": "#5C8F82",
        "400": "#486F65", "500": "#345049", "600": "#22342F"}
PLUM = {"100": "#D4CDD2", "200": "#B3A7AF", "300": "#94838F",
        "400": "#62555E", "500": "#473D44", "600": "#2E282C"}

FAMILIES = {"Rust": RUST, "Gray": GRAY, "Blue": BLUE,
            "Gold": GOLD, "Sage": SAGE, "Plum": PLUM}

# Annotation ink — warm mauve for axes, ticks, spines, leader lines
INK = "#181114"

# Figure background
BG = "#EEEAE0"

# Alpha / transparency standards
ALPHA = {
    "bar":        0.85,
    "violin":     0.30,
    "band":       0.13,   # confidence bands / fill_between
    "ns_scatter": 0.30,   # non-significant scatter points
    "scatter":    0.75,   # significant scatter points
    "box":        0.70,   # boxplot patch fill
}

# Paired condition encoding: use same family at 200 (before) + 400 (after)
PAIR_LIGHT = "200"
PAIR_DARK  = "400"

# Backward-compatible semantic aliases (point into families)
HERO    = RUST["300"]
NEUTRAL = GRAY["200"]
ACCENT  = BLUE["300"]
WARM    = GOLD["300"]
DEEP    = SAGE["300"]
SOFT    = PLUM["300"]
NS_GRAY = GRAY["100"]

# ---------------------------------------------------------------------------
# Color palettes & colormaps
# ---------------------------------------------------------------------------
def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

def _make_cmap(stops, name):
    return LinearSegmentedColormap.from_list(
        name, [_hex_to_rgb(c) for c in stops], N=256)

PALETTES = {
    # Default: 300-level from each family (luminance-equalized)
    "default": [RUST["300"], GRAY["300"], BLUE["300"],
                GOLD["300"], SAGE["300"], PLUM["300"]],
    # Primary only (rust + gray shades)
    "primary": [RUST["300"], GRAY["300"], RUST["200"],
                GRAY["200"], RUST["400"], GRAY["400"]],
    # Legacy palettes for backward compatibility
    "classic": ["#4C72B0", "#55A868", "#C44E52", "#8172B3", "#CCB974", "#64B5CD"],
    "retro": ["#f04a3a", "#619ac3", "#d6a01d", "#12aa9c", "#806332", "#eea6b7"],
    "synbio": [RUST["300"], GRAY["300"], SAGE["300"],
               GOLD["300"], PLUM["300"], BLUE["300"]],
    "grayscale": [GRAY["600"], GRAY["500"], GRAY["400"],
                  GRAY["300"], GRAY["200"], GRAY["100"]],
}

# Sequential & diverging colormaps
CMAP_RUST = _make_cmap(
    [RUST["600"], RUST["400"], RUST["200"], "#F2E6D8"], "ying_rust")
CMAP_BLUE = _make_cmap(
    [BLUE["600"], BLUE["400"], BLUE["200"], "#E8EDF2"], "ying_blue")
CMAP_DIVERGE = _make_cmap(
    [BLUE["500"], BLUE["200"], "#F0EAE0", RUST["200"], RUST["500"]],
    "ying_diverge")

CMAPS = {
    "sequential": CMAP_RUST,
    "sequential_blue": CMAP_BLUE,
    "diverging": CMAP_DIVERGE,
    # Legacy string-based cmaps still available
    "RdBu_r": "RdBu_r",
    "YlOrRd": "YlOrRd",
    "blues": "Blues",
    "greens": "Greens",
}

# Background colors for panel grouping
BG_COLORS = {
    "figure": BG,           # main figure background
    "cream": "#FAF3E8",     # experimental data panels
    "linen": "#F5F0E6",     # alternative warm panel
    "beige": "#F0EBE1",     # legacy
    "blue_gray": "#E6EBF0",
    "light_gray": "#F2F2F2",
}


# ---------------------------------------------------------------------------
# Figure dimensions — Nature column specifications
# ---------------------------------------------------------------------------
NATURE_DIMS = {
    "single": (3.50, 9.72),   # 89 mm  — single column max width
    "1.5col": (4.72, 9.72),   # 120 mm — 1.5 column max width
    "double": (7.20, 9.72),   # 183 mm — double column max width
}


def figsize_nature(columns="single", aspect=0.75):
    max_w, max_h = NATURE_DIMS[columns]
    h = min(max_w * aspect, max_h)
    return (max_w, h)


# ---------------------------------------------------------------------------
# Retro style — rcParams matching ggRetro / base R axes
# ---------------------------------------------------------------------------
RETRO_STYLE = {
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.bottom": True,
    "axes.spines.left": True,
    "axes.xmargin": 0.05,
    "axes.ymargin": 0.05,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica"],
    "font.size": 7,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.minor.visible": False,
    "ytick.minor.visible": False,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.labelcolor": INK,
    "ytick.labelcolor": INK,
    "axes.grid": False,
    "axes.labelpad": 4,
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "text.color": INK,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "axes.linewidth": 0.6,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
}


def retro_style(palette="default"):
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams.update(RETRO_STYLE)
    if isinstance(palette, str):
        colors = PALETTES.get(palette, PALETTES["default"])
    else:
        colors = list(palette)
    mpl.rcParams["axes.prop_cycle"] = cycler("color", colors)
    return colors


def trim_axes(fig=None, exclude=None):
    if fig is None:
        fig = plt.gcf()
    exclude = exclude or set()
    for ax in fig.axes:
        if ax in exclude:
            continue
        _trim_axis_spines(ax)


def _tighten_limits(ax, axis, ticks, is_log, pts):
    """Tighten axis limits to spine bounds so no bare axis extends past ticks.

    Starts with tight margins around the outermost ticks, then expands just
    enough to cover any data (error bar caps, bar edges, etc.) that extends
    beyond the spine.  Result: limits are always close to the spine, but
    nothing is clipped.
    """
    t_lo, t_hi = float(ticks[0]), float(ticks[-1])
    if is_log:
        spine_pad = 1.1  # ~0.04 decades
        new_lo, new_hi = t_lo / spine_pad, t_hi * spine_pad
    else:
        r = t_hi - t_lo
        spine_pad = r * 0.02 if r > 0 else 0.1
        new_lo, new_hi = t_lo - spine_pad, t_hi + spine_pad

    # Expand to cover data that extends beyond the tight spine bounds
    col = 0 if axis == "x" else 1
    if pts.shape[0] > 0:
        data_min = float(np.nanmin(pts[:, col]))
        data_max = float(np.nanmax(pts[:, col]))
        if is_log:
            data_pad = 1.05
            if data_min < new_lo:
                new_lo = data_min / data_pad
            if data_max > new_hi:
                new_hi = data_max * data_pad
        else:
            data_pad = r * 0.01 if r > 0 else 0.05
            if data_min < new_lo:
                new_lo = data_min - data_pad
            if data_max > new_hi:
                new_hi = data_max + data_pad

    if axis == "x":
        ax.set_xlim(new_lo, new_hi)
    else:
        ax.set_ylim(new_lo, new_hi)


def _bar_axis_info(ax):
    """Detect bar containers and return categorical-axis padding info.

    Bar charts place ticks at bar *centers*, so trimming the categorical-axis
    spine to the tick range leaves the first/last bars hanging past the spine
    ends (bar overlaps the axis).  This returns the outer bar-edge extent plus
    a margin for that axis so the spine can be extended to enclose every bar.

    Returns ``{"axis": "x"|"y", "lo": float, "hi": float, "pad": float}`` for
    the categorical axis (x for ``ax.bar``, y for ``ax.barh``), or ``None`` when
    the axes has no bar containers or mixes both orientations.
    """
    orientations = set()
    edges_lo, edges_hi, sizes = [], [], []
    for cont in ax.containers:
        if not isinstance(cont, BarContainer):
            continue
        patches = list(cont.patches)
        if not patches:
            continue
        orient = getattr(cont, "orientation", None)
        if orient not in ("vertical", "horizontal"):
            # Infer: vertical bars share a constant baseline y; horizontal x.
            y0s = {round(float(p.get_y()), 9) for p in patches}
            x0s = {round(float(p.get_x()), 9) for p in patches}
            orient = "vertical" if len(y0s) <= len(x0s) else "horizontal"
        orientations.add(orient)
        for p in patches:
            if orient == "vertical":
                lo, size = float(p.get_x()), abs(float(p.get_width()))
            else:
                lo, size = float(p.get_y()), abs(float(p.get_height()))
            if not np.isfinite([lo, size]).all():
                continue
            edges_lo.append(lo)
            edges_hi.append(lo + size)
            sizes.append(size)
    if not edges_lo or len(orientations) != 1:
        return None
    bar_w = float(np.median(sizes)) if sizes else 0.0

    # Distinguish a categorical bar chart (gaps between bars/clusters) from a
    # histogram (fully contiguous bars).  Histograms have a continuous numeric
    # axis and should NOT be padded — let normal trimming handle them.  A
    # categorical chart has at least one real gap between adjacent bars; a
    # grouped chart has gaps between clusters; a histogram has none.
    intervals = sorted(zip(edges_lo, edges_hi))
    if len(intervals) >= 2 and bar_w > 0:
        max_gap, run_hi = 0.0, intervals[0][1]
        for lo, hi in intervals[1:]:
            max_gap = max(max_gap, lo - run_hi)
            run_hi = max(run_hi, hi)
        if max_gap <= 0.1 * bar_w:
            return None  # contiguous bars (histogram) — not categorical

    return {
        "axis": "x" if orientations.pop() == "vertical" else "y",
        "lo": min(edges_lo),
        "hi": max(edges_hi),
        "pad": 0.75 * bar_w if bar_w > 0 else 0.5,
    }


def _pad_categorical_axis(ax, axis, bar_info):
    """Extend the categorical-axis spine past the outer bar edges.

    Set the spine bounds (and matching limit) to the outer bar edges plus a
    margin so every bar sits inside the axis frame with a visible gap, instead
    of trimming the spine to the bar-center tick range.  Respects an inverted
    axis (common for ``barh`` drawn top-to-bottom).
    """
    lo = bar_info["lo"] - bar_info["pad"]
    hi = bar_info["hi"] + bar_info["pad"]
    if axis == "x":
        ax.spines["bottom"].set_bounds(lo, hi)
        cur = ax.get_xlim()
        ax.set_xlim((hi, lo) if cur[0] > cur[1] else (lo, hi))
    else:
        ax.spines["left"].set_bounds(lo, hi)
        cur = ax.get_ylim()
        ax.set_ylim((hi, lo) if cur[0] > cur[1] else (lo, hi))


def pad_categorical_axis(ax, axis="y", pad=0.5):
    """Add breathing room so end categories don't touch the frame.

    For manually-built categorical plots (forest plots, dot/lollipop plots,
    cleveland plots) where categories sit at integer tick positions and
    ``trim_axes()`` is intentionally NOT used.  Extends the limit on ``axis`` by
    ``pad`` category-units beyond the outermost tick so the first/last marker
    and its value label clear the frame.  Respects an inverted axis (e.g. a
    forest plot drawn top-to-bottom with ``invert_yaxis()``).

    ``pad=0.5`` (half a category step) matches the bar-chart padding convention.
    """
    ticks = ax.get_yticks() if axis == "y" else ax.get_xticks()
    ticks = np.asarray(ticks, dtype=float)
    ticks = ticks[np.isfinite(ticks)]
    if ticks.size < 1:
        return
    lo, hi = float(ticks.min()) - pad, float(ticks.max()) + pad
    if axis == "y":
        cur = ax.get_ylim()
        ax.set_ylim((hi, lo) if cur[0] > cur[1] else (lo, hi))
    else:
        cur = ax.get_xlim()
        ax.set_xlim((hi, lo) if cur[0] > cur[1] else (lo, hi))


def _trim_axis_spines(ax):
    """Trim spines to the tick range, adding ticks to cover data if needed.

    ggplot/base-R style: spines ALWAYS end at a tick mark, and no tick exists
    outside the spine line.  xlim/ylim are tightened to the spine bounds so
    nothing floats beyond the axis.

    Linear axes: extends ticks at regular spacing to cover data.
    Log axes: generates ticks at every power of 10 covering the data range.
    Bar charts: the categorical axis is padded past the outer bar edges
    (instead of trimmed to bar centers) so no bar overlaps the spine.
    """
    pts = _collect_data_points(ax)
    x_is_log = ax.get_xscale() == "log"
    y_is_log = ax.get_yscale() == "log"
    bar_info = _bar_axis_info(ax)

    # --- X axis ---
    if bar_info is not None and bar_info["axis"] == "x" and not x_is_log:
        _pad_categorical_axis(ax, "x", bar_info)
    else:
        xt_in = _compute_trimmed_ticks(ax, "x", x_is_log, pts, 0)
        if xt_in is not None and len(xt_in) >= 2:
            _set_ticks_preserve_fmt(ax, "x", xt_in, x_is_log)
            ax.spines["bottom"].set_bounds(float(xt_in[0]), float(xt_in[-1]))
            _tighten_limits(ax, "x", xt_in, x_is_log, pts)

    # --- Y axis ---
    if bar_info is not None and bar_info["axis"] == "y" and not y_is_log:
        _pad_categorical_axis(ax, "y", bar_info)
    else:
        yt_in = _compute_trimmed_ticks(ax, "y", y_is_log, pts, 1)
        if yt_in is not None and len(yt_in) >= 2:
            _set_ticks_preserve_fmt(ax, "y", yt_in, y_is_log)
            ax.spines["left"].set_bounds(float(yt_in[0]), float(yt_in[-1]))
            _tighten_limits(ax, "y", yt_in, y_is_log, pts)


def _compute_trimmed_ticks(ax, axis, is_log, pts, col):
    """Return the tick array for one axis, covering data range.

    Log axes: generate ticks at every power of 10 that fits inside the
    current axis limits. Uses limits (not collected data points) because
    some artists (hexbin) store offsets in transformed space.

    Linear axes: use existing ticks, extending at regular spacing if
    data points extend beyond the current tick range.
    """
    if axis == "x":
        ticks = np.asarray(ax.get_xticks(minor=False))
        lim = ax.get_xlim()
    else:
        ticks = np.asarray(ax.get_yticks(minor=False))
        lim = ax.get_ylim()
    lo, hi = min(lim), max(lim)

    if is_log:
        if lo <= 0 or hi <= 0:
            return None
        # Start with inward-snapped ticks at powers of 10
        lo_exp = int(np.ceil(np.log10(lo)))
        hi_exp = int(np.floor(np.log10(hi)))
        # Extend outward when axis limits extend past the nearest
        # power-of-10 tick.  Uses limits (not collected pts) because
        # some artists like hexbin store offsets in transformed space.
        # Upper end: always extend — data floating past the spine
        # trailing edge looks broken.
        if hi_exp >= lo_exp and 10.0 ** hi_exp < hi * 0.99:
            hi_exp += 1
        # Lower end: only extend when the gap exceeds half a decade,
        # otherwise the small gap before the first tick is acceptable.
        if lo_exp <= hi_exp and 10.0 ** lo_exp > lo * 1.01:
            gap = np.log10(10.0 ** lo_exp / lo)
            if gap > 0.5:
                lo_exp -= 1
        if hi_exp < lo_exp:
            return None
        t_in = 10.0 ** np.arange(lo_exp, hi_exp + 1)
        return t_in if len(t_in) >= 2 else None

    # Linear axis
    t_in = ticks[(ticks >= lo) & (ticks <= hi)]
    if len(t_in) < 2:
        return None
    if pts.shape[0] > 0:
        t_in = _extend_ticks_to_data(
            t_in, float(np.nanmin(pts[:, col])),
            float(np.nanmax(pts[:, col])), lo, hi)
    return t_in if len(t_in) >= 2 else None


def _set_ticks_preserve_fmt(ax, axis, ticks, is_log):
    """Set major ticks, preserving the log formatter if needed."""
    axis_obj = ax.xaxis if axis == "x" else ax.yaxis
    if is_log:
        fmt = axis_obj.get_major_formatter()
    if axis == "x":
        ax.set_xticks(ticks)
    else:
        ax.set_yticks(ticks)
    if is_log:
        axis_obj.set_major_formatter(fmt)


def _extend_ticks_to_data(ticks_in, data_min, data_max, lim_lo, lim_hi):
    """Add ticks to cover data range, keeping regular spacing.

    If data extends below the first tick or above the last tick,
    new ticks are prepended/appended at the same spacing so the spine
    always ends at a tick mark (ggplot/base-R style).
    """
    if len(ticks_in) < 2:
        return ticks_in
    step = round(float(ticks_in[1] - ticks_in[0]), 10)
    if step <= 0:
        return ticks_in

    ticks = list(float(t) for t in ticks_in)

    # Extend downward to cover data_min
    while ticks[0] > data_min and round(ticks[0] - step, 10) >= lim_lo:
        ticks.insert(0, round(ticks[0] - step, 10))

    # Extend upward to cover data_max
    while ticks[-1] < data_max and round(ticks[-1] + step, 10) <= lim_hi:
        ticks.append(round(ticks[-1] + step, 10))

    return np.array(ticks)


LABEL_PROPS = dict(fontsize=10, fontweight="bold", fontfamily="Arial",
                   va="top", ha="left", color="black")


# ---------------------------------------------------------------------------
# Outlined scatter — three-layer dots for crowded plots
# ---------------------------------------------------------------------------

def scatter_outlined(ax, x, y, s=15, c=None, outline_color="black",
                     outline_scale=2.5, ring_scale=1.7, alpha=0.8,
                     zorder=2, **kwargs):
    """Scatter plot with outlined dots (3-layer: black bg -> white ring -> color).

    Creates a clean outlined appearance where each dot has a visible border,
    preventing visual merging in crowded scatter plots.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    x, y : array-like
    s : float
        Size of the colored fill (innermost layer).
    c : color or array-like
        Color(s) for the fill layer.
    outline_color : str
        Color of the outermost ring (default "black").
    outline_scale : float
        Size multiplier for the outermost black ring (default 2.5).
    ring_scale : float
        Size multiplier for the white middle ring (default 1.7).
    alpha : float
    zorder : int
    **kwargs
        Passed to the innermost scatter call (e.g., cmap, vmin, vmax).

    Returns
    -------
    sc : PathCollection
        The innermost (colored) scatter artist.
    """
    # Remove keys that shouldn't go to background layers
    bg_safe = {k: v for k, v in kwargs.items()
               if k not in ("cmap", "vmin", "vmax", "norm", "label")}

    ax.scatter(x, y, s=s * outline_scale, c=outline_color, alpha=alpha,
               clip_on=False, zorder=zorder, edgecolors="none", **bg_safe)
    ax.scatter(x, y, s=s * ring_scale, c="white",
               clip_on=False, zorder=zorder + 0.1, edgecolors="none", **bg_safe)
    sc = ax.scatter(x, y, s=s, c=c, alpha=alpha,
                    clip_on=False, zorder=zorder + 0.2, edgecolors="none",
                    **kwargs)
    return sc


# ---------------------------------------------------------------------------
# Horizontal bar labels — overlap-aware placement
# ---------------------------------------------------------------------------

def _label_width_data(text, fontsize, x_range, ax_width_inches):
    """Estimate text width in data coordinates (resolution-independent)."""
    char_width_inches = fontsize * 0.55 / 72.0  # average char width (Arial)
    text_width_inches = char_width_inches * len(text)
    data_per_inch = x_range / ax_width_inches if ax_width_inches > 0 else 1
    return text_width_inches * data_per_inch


def smart_bar_labels(ax, bars, labels, fontsize=7, color=None,
                     inside_color="white", pad_frac=0.02,
                     connector_color=None, connector_lw=0.4,
                     y_clearance=4.0):
    """Non-overlapping value labels for horizontal bar charts.

    Places labels at bar tips for barh() charts.  Uses a data-coordinate
    heuristic to detect when adjacent labels would visually collide
    (common when bars have similar lengths), then resolves by:

      1. Moving the **shorter** bar's label INSIDE (right-aligned, white).
      2. If the bar is too narrow for the text, staggering rightward
         with a thin connector line.

    The heuristic estimates text width in data units and compares bar-end
    proximity against it — works reliably across all figure sizes, DPIs,
    and backends.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    bars : BarContainer
        Return value of ``ax.barh()``.
    labels : list of str
        One label per bar (e.g. ``"820 (9.9%)"``).
    fontsize : float
    color : str or None
        Outer label color (default: INK).
    inside_color : str
        Color for labels placed inside bars (default: ``"white"``).
    pad_frac : float
        Horizontal gap between bar end and label, as fraction of x-range.
    connector_color : str or None
        Color for stagger connector lines (default: GRAY["300"]).
    connector_lw : float
        Line width for connector lines.
    y_clearance : float
        Adjacent labels within this many text-heights are checked for
        x-overlap.  Default 4.0 provides comfortable reading clearance
        for tightly packed bars.

    Returns
    -------
    list of matplotlib.text.Text
    """
    if color is None:
        color = INK
    if connector_color is None:
        connector_color = GRAY["300"]

    rects = bars.patches if hasattr(bars, "patches") else list(bars)
    n = len(rects)
    if n == 0:
        return []
    labels = list(labels)[:n]

    xlim = ax.get_xlim()
    x_range = xlim[1] - xlim[0]
    pad = x_range * pad_frac

    # --- Geometry collection ---
    geo = []
    for i, (r, lab) in enumerate(zip(rects, labels)):
        x0 = r.get_x()
        w = r.get_width()
        geo.append({
            "i": i,
            "x_end": x0 + w,
            "w": w,
            "y": r.get_y() + r.get_height() / 2,
            "h": r.get_height(),
            "label": lab,
        })
    # Sort top → bottom (highest y first)
    geo.sort(key=lambda d: -d["y"])

    # --- Compute text dimensions in data coordinates ---
    fig = ax.get_figure()
    ax_pos = ax.get_position()
    ax_w_inch = fig.get_figwidth() * ax_pos.width
    ax_h_inch = fig.get_figheight() * ax_pos.height

    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    y_per_inch = y_range / ax_h_inch if ax_h_inch > 0 else 1
    text_height = fontsize / 72.0 * y_per_inch

    def lw_data(text):
        return _label_width_data(text, fontsize, x_range, ax_w_inch)

    # --- Detect overlaps via data-coordinate heuristic ---
    placement = ["outside"] * n  # "outside", "inside", or "offset"
    relocated = set()

    for j in range(len(geo) - 1):
        a, b = geo[j], geo[j + 1]
        ai, bi = a["i"], b["i"]

        # Skip if either already relocated
        if ai in relocated or bi in relocated:
            continue

        # Y-proximity: are bars close enough for labels to collide?
        y_gap = abs(a["y"] - b["y"])
        if y_gap > text_height * y_clearance:
            continue

        # X-overlap: would the label text regions intersect?
        tw_a = lw_data(a["label"])
        tw_b = lw_data(b["label"])
        a_start = a["x_end"] + pad
        b_start = b["x_end"] + pad
        if not (a_start < b_start + tw_b and b_start < a_start + tw_a):
            continue

        # Collision detected — try to move one bar's label inside
        if a["w"] <= b["w"]:
            shorter, longer = a, b
        else:
            shorter, longer = b, a

        def _fits_inside(bar_geo):
            """Renderer-based check: can this bar hold its label?"""
            t_probe = ax.text(0, 0, bar_geo["label"], fontsize=fontsize,
                              va="center", ha="left")
            fig.canvas.draw()
            _r = fig.canvas.get_renderer()
            _tw = t_probe.get_window_extent(_r).width
            t_probe.remove()
            _be = ax.transData.transform((bar_geo["x_end"], 0))[0]
            _bs = ax.transData.transform(
                (bar_geo["x_end"] - bar_geo["w"], 0))[0]
            # Account for pad inset: text is placed at x_end - pad,
            # so effective space = bar_width - pad (in pixels)
            _pad_px = abs(ax.transData.transform((pad * 0.7, 0))[0]
                          - ax.transData.transform((0, 0))[0])
            return (abs(_be - _bs) - _pad_px) > _tw * 1.15

        if _fits_inside(shorter):
            placement[shorter["i"]] = "inside"
            relocated.add(shorter["i"])
        elif _fits_inside(longer):
            # Shorter doesn't fit — move longer inside instead
            placement[longer["i"]] = "inside"
            relocated.add(longer["i"])
        else:
            # Neither fits — offset the shorter
            placement[shorter["i"]] = "offset"
            relocated.add(shorter["i"])

    # --- Place all labels ---
    texts = {}
    connectors = []

    for d in geo:
        i = d["i"]
        if placement[i] == "inside":
            texts[i] = ax.text(
                d["x_end"] - pad * 0.7, d["y"], d["label"],
                va="center", ha="right", fontsize=fontsize,
                color=inside_color, clip_on=False,
            )
        elif placement[i] == "offset":
            # Find the outside neighbor that caused the collision
            # and place label past its full text extent
            neighbor_geo = None
            for j in range(len(geo) - 1):
                a, b = geo[j], geo[j + 1]
                if a["i"] == i and placement[b["i"]] == "outside":
                    neighbor_geo = b
                    break
                if b["i"] == i and placement[a["i"]] == "outside":
                    neighbor_geo = a
                    break
            if neighbor_geo:
                # Place AFTER the neighbor's outside label ends
                neighbor_label_end = (neighbor_geo["x_end"] + pad
                                      + lw_data(neighbor_geo["label"]))
                offset_x = neighbor_label_end + pad
            else:
                offset_x = d["x_end"] + pad  # fallback
            texts[i] = ax.text(
                offset_x, d["y"], d["label"],
                va="center", ha="left", fontsize=fontsize,
                color=color, clip_on=False,
            )
            # Connector line
            line, = ax.plot(
                [d["x_end"], offset_x - pad * 0.3],
                [d["y"], d["y"]],
                color=connector_color, lw=connector_lw,
                solid_capstyle="butt", clip_on=False,
            )
            connectors.append(line)
        else:
            texts[i] = ax.text(
                d["x_end"] + pad, d["y"], d["label"],
                va="center", ha="left", fontsize=fontsize,
                color=color, clip_on=False,
            )

    # Auto-extend xlim to fit any labels past axis
    max_x = xlim[1]
    for d in geo:
        i = d["i"]
        if placement[i] == "outside":
            needed = d["x_end"] + pad + lw_data(d["label"])
        elif placement[i] == "offset":
            t = texts[i]
            needed = float(t.get_position()[0]) + lw_data(d["label"])
        else:
            needed = 0
        max_x = max(max_x, needed)
    if max_x > xlim[1]:
        ax.set_xlim(xlim[0], max_x + pad)

    return [texts[i] for i in range(n)]


# ---------------------------------------------------------------------------
# Leader-line annotation — slanted line + horizontal stub
# ---------------------------------------------------------------------------

def add_elbow_annotation(ax, text, xy, xytext, direction="right",
                         color="black", lw=0.6, fontsize=None,
                         stub=None, **text_kw):
    x0, y0 = xy
    x1, y1 = xytext
    if stub is None:
        x_range = abs(ax.get_xlim()[1] - ax.get_xlim()[0])
        stub = x_range * 0.05
    if direction == "right":
        mid_x = x1 - stub
        line_x = [x0, mid_x, x1]
        line_y = [y0, y1, y1]
        ha = "left"
        text_x = x1
    else:
        mid_x = x1 + stub
        line_x = [x0, mid_x, x1]
        line_y = [y0, y1, y1]
        ha = "right"
        text_x = x1
    line, = ax.plot(line_x, line_y, color=color, lw=lw,
                    solid_capstyle="butt", clip_on=False)
    text_kw.setdefault("va", "center")
    text_kw.setdefault("ha", ha)
    pad = stub * 0.3 if direction == "right" else -stub * 0.3
    t = ax.text(text_x + pad, y1, text,
                color=color, fontsize=fontsize, **text_kw)
    return line, t


def add_elbow_annotations(ax, labels, xy_points, xytext_points,
                          direction="right", color="black", lw=0.6,
                          fontsize=None, stub=None, **text_kw):
    results = []
    for label, xy, xyt in zip(labels, xy_points, xytext_points):
        results.append(add_elbow_annotation(
            ax, label, xy, xyt, direction=direction, color=color,
            lw=lw, fontsize=fontsize, stub=stub, **text_kw
        ))
    return results


# ---------------------------------------------------------------------------
# Smart placement — data-density-aware legend, annotation, and stat-text
# ---------------------------------------------------------------------------


def _has_blended_transform(artist):
    """Check if an artist uses a blended transform (axvspan/axhspan).

    These patches mix data and axes-fraction coordinate systems, so their
    get_x/get_y values cannot be interpreted as pure data coordinates.
    """
    import matplotlib.transforms as mtransforms
    t = getattr(artist, "get_transform", lambda: None)()
    if t is None:
        return False
    # Walk the transform tree looking for a BlendedGenericTransform or
    # BlendedAffine2D at any level.
    def _walk(node):
        if isinstance(node, (mtransforms.BlendedGenericTransform,
                             mtransforms.BlendedAffine2D)):
            return True
        for attr in ("_a", "_b"):
            child = getattr(node, attr, None)
            if child is not None and _walk(child):
                return True
        return False
    return _walk(t)


def _collect_data_points(ax):
    """Collect all visible data coordinates from an axes as (N, 2) array."""
    points = []
    for line in ax.get_lines():
        try:
            xd = np.asarray(line.get_xdata(), dtype=float)
            yd = np.asarray(line.get_ydata(), dtype=float)
            mask = np.isfinite(xd) & np.isfinite(yd)
            if mask.any():
                points.append(np.column_stack([xd[mask], yd[mask]]))
        except (ValueError, TypeError):
            # Skip lines with non-numeric data (e.g., bar chart error bars
            # with categorical x-axis)
            continue
    for coll in ax.collections:
        offsets = np.asarray(coll.get_offsets(), dtype=float)
        has_offsets = False
        if offsets.size > 0:
            mask = np.isfinite(offsets).all(axis=1)
            if mask.any():
                clean = offsets[mask]
                # Skip trivial transform offsets (e.g., LineCollection from
                # errorbar stores a single [0,0] offset, not real data)
                if len(clean) == 1 and np.allclose(clean[0], 0):
                    pass
                else:
                    points.append(clean)
                    has_offsets = True
        # Detect fill_between PolyCollection — sample vertices to mark
        # the filled band as occupied space.  Skip if collection already
        # provided offsets (scatter PathCollections have marker paths
        # centered at origin that would pollute coordinates).
        if not has_offsets:
            try:
                for path in coll.get_paths():
                    verts = path.vertices
                    if verts.shape[0] > 4:  # real polygon, not a simple marker
                        mask = np.isfinite(verts).all(axis=1)
                        if mask.any():
                            v = verts[mask]
                            step = max(1, len(v) // 20)
                            points.append(v[::step])
            except (AttributeError, TypeError):
                pass
    for patch in ax.patches:
        try:
            # Skip patches with blended transforms (axvspan / axhspan) —
            # their coordinates mix data and axes-fraction systems, so
            # reading get_x/get_y returns axes-fraction values (0–1) that
            # would be misinterpreted as data coordinates.
            if _has_blended_transform(patch):
                continue
            # Rectangle patches (bars) have get_x/get_y
            if hasattr(patch, "get_x") and hasattr(patch, "get_width"):
                x0 = float(patch.get_x())
                y0 = float(patch.get_y())
                w = float(patch.get_width())
                h = float(patch.get_height())
                if np.isfinite([x0, y0, w, h]).all():
                    pts = np.array([
                        [x0, y0 + h], [x0 + w, y0 + h], [x0 + w / 2, y0 + h],
                    ])
                    points.append(pts)
            else:
                # PathPatch (boxplot) — extract vertices from path
                verts = patch.get_path().vertices
                if verts.size > 0:
                    mask = np.isfinite(verts).all(axis=1)
                    if mask.any():
                        points.append(verts[mask])
        except (TypeError, ValueError, AttributeError):
            continue
    if not points:
        return np.empty((0, 2))
    return np.vstack(points)


def find_best_legend_loc(ax, n_items=3):
    """Find the axes corner with least data for legend placement.

    Uses a smaller footprint than before (~18% x variable height) and
    checks all 8 standard positions. For line-heavy plots, also penalizes
    regions where lines pass through (not just point count).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    n_items : int
        Approximate number of legend items (affects vertical footprint).

    Returns
    -------
    loc : str
        Best matplotlib legend loc string.
    count : int
        Number of data points in that region.
    """
    pts = _collect_data_points(ax)
    if pts.shape[0] == 0:
        return "upper right", 0

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xr = xlim[1] - xlim[0]
    yr = ylim[1] - ylim[0]

    # Adaptive legend footprint — smaller than before
    lw = xr * 0.18
    lh = yr * (0.08 + 0.04 * n_items)

    regions = {
        "upper left":   (xlim[0],               xlim[0] + lw,            ylim[1] - lh, ylim[1]),
        "upper right":  (xlim[1] - lw,          xlim[1],                 ylim[1] - lh, ylim[1]),
        "lower left":   (xlim[0],               xlim[0] + lw,            ylim[0],       ylim[0] + lh),
        "lower right":  (xlim[1] - lw,          xlim[1],                 ylim[0],       ylim[0] + lh),
        "center left":  (xlim[0],               xlim[0] + lw,            ylim[0] + yr * 0.4, ylim[0] + yr * 0.6),
        "center right": (xlim[1] - lw,          xlim[1],                 ylim[0] + yr * 0.4, ylim[0] + yr * 0.6),
        "upper center": (xlim[0] + xr * 0.375,  xlim[0] + xr * 0.625,   ylim[1] - lh, ylim[1]),
        "lower center": (xlim[0] + xr * 0.375,  xlim[0] + xr * 0.625,   ylim[0],       ylim[0] + lh),
    }

    # Also check how many line segments cross each region
    lines_data = []
    for line in ax.get_lines():
        xd = np.asarray(line.get_xdata(), dtype=float)
        yd = np.asarray(line.get_ydata(), dtype=float)
        mask = np.isfinite(xd) & np.isfinite(yd)
        if mask.sum() > 1:
            lines_data.append((xd[mask], yd[mask]))

    best_loc = "upper right"
    best_score = float("inf")

    for loc, (x0, x1, y0, y1) in regions.items():
        # Point count in region
        inside = ((pts[:, 0] >= x0) & (pts[:, 0] <= x1) &
                  (pts[:, 1] >= y0) & (pts[:, 1] <= y1))
        count = int(inside.sum())

        # Line crossing penalty: count line segments that cross the region
        line_crossings = 0
        for lx, ly in lines_data:
            in_x = (lx >= x0) & (lx <= x1)
            in_y = (ly >= y0) & (ly <= y1)
            in_region = in_x & in_y
            line_crossings += int(in_region.sum())

        # Combined score: points + line crossings (heavily penalized)
        score = count + line_crossings * 5

        if score < best_score:
            best_score = score
            best_loc = loc
            if score == 0:
                break

    # If every tested region has data, widen ylim to create headroom
    # above the data and place the legend in upper right
    if best_score > 3:
        data_ymax = pts[:, 1].max()
        headroom = yr * (0.08 + 0.05 * n_items)
        new_top = data_ymax + headroom
        if new_top > ylim[1]:
            ax.set_ylim(ylim[0], new_top)
        # Re-check upper right / upper left with expanded ylim
        new_ylim = ax.get_ylim()
        new_yr = new_ylim[1] - new_ylim[0]
        new_lh = new_yr * (0.08 + 0.04 * n_items)
        for loc in ["upper right", "upper left"]:
            if loc == "upper right":
                x0, x1 = xlim[1] - lw, xlim[1]
            else:
                x0, x1 = xlim[0], xlim[0] + lw
            y0, y1 = new_ylim[1] - new_lh, new_ylim[1]
            inside = ((pts[:, 0] >= x0) & (pts[:, 0] <= x1) &
                      (pts[:, 1] >= y0) & (pts[:, 1] <= y1))
            new_count = int(inside.sum())
            if new_count < best_score:
                best_score = new_count
                best_loc = loc
                if new_count == 0:
                    break

    return best_loc, best_score


def smart_annotate(ax, labels, xy_points, fontsize=7, color="black",
                   direction="auto", lw=0.6, stub=None,
                   min_gap_frac=0.08, **text_kw):
    """Place leader-line annotations OUTWARD from all data.

    Labels are placed past ALL data points (not just the annotated ones),
    ensuring annotations never overlap with scatter dots or other data.
    Automatically extends the axis limits to accommodate the label column.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    labels : list of str
    xy_points : list of (x, y)
    fontsize : float
    color : str
    direction : "auto", "left", or "right"
        "auto" annotates right unless points are in the right 25%.
    lw : float
    stub : float or None
    min_gap_frac : float
        Minimum label gap as fraction of full y-axis range.
    **text_kw
        Passed through to add_elbow_annotation.
    """
    n = len(labels)
    if n == 0:
        return []

    xs = np.array([p[0] for p in xy_points])
    ys = np.array([p[1] for p in xy_points])
    order = np.argsort(-ys)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]

    # Collect ALL data to place labels past the entire data extent
    all_pts = _collect_data_points(ax)

    if direction == "auto":
        # Default to "right" (safest — annotates away from y-axis)
        # Only go "left" when points are at the extreme right edge (>90%)
        mean_x = xs.mean()
        if mean_x > xlim[0] + 0.90 * x_range:
            direction = "left"
        else:
            direction = "right"

    # Place label column PAST all data, not just annotated points
    offset = x_range * 0.12
    if direction == "right":
        all_max_x = float(all_pts[:, 0].max()) if all_pts.shape[0] > 0 else xs.max()
        # Use the further of: all data max or annotated points max
        ref_x = max(all_max_x, xs.max())
        label_col = ref_x + offset
        # Auto-extend xlim to fit labels + text
        text_room = x_range * 0.18
        needed = label_col + text_room
        if needed > xlim[1]:
            ax.set_xlim(xlim[0], needed)
    else:
        all_min_x = float(all_pts[:, 0].min()) if all_pts.shape[0] > 0 else xs.min()
        ref_x = min(all_min_x, xs.min())
        label_col = ref_x - offset
        text_room = x_range * 0.18
        needed = label_col - text_room
        if needed < xlim[0]:
            ax.set_xlim(needed, xlim[1])

    # Y positions: sorted top-to-bottom with minimum gap
    min_gap = y_range * min_gap_frac
    y_top = ys[order[0]] + y_range * 0.02

    if n > 1:
        data_y_span = ys[order[0]] - ys[order[-1]]
        y_gap = max(data_y_span / (n - 1), min_gap)
    else:
        y_gap = min_gap

    results = []
    for rank, idx in enumerate(order):
        label_y = y_top - rank * y_gap
        line, text = add_elbow_annotation(
            ax, labels[idx],
            xy=(xs[idx], ys[idx]),
            xytext=(label_col, label_y),
            direction=direction, color=color, lw=lw,
            fontsize=fontsize, stub=stub, **text_kw,
        )
        results.append((line, text))

    return results


_STAT_LOC_COORDS = {
    "upper left":   (0.05, 0.95, "top",    "left"),
    "upper right":  (0.95, 0.95, "top",    "right"),
    "lower left":   (0.05, 0.05, "bottom", "left"),
    "lower right":  (0.95, 0.05, "bottom", "right"),
    "center left":  (0.05, 0.50, "center", "left"),
    "center right": (0.95, 0.50, "center", "right"),
    "upper center": (0.50, 0.95, "top",    "center"),
    "lower center": (0.50, 0.05, "bottom", "center"),
}


def place_stat_text(ax, text, fontsize=7, **text_kw):
    """Place a stat text box in the least-crowded corner."""
    loc, _ = find_best_legend_loc(ax)
    x, y, va, ha = _STAT_LOC_COORDS.get(loc, (0.05, 0.95, "top", "left"))
    text_kw.setdefault("va", va)
    text_kw.setdefault("ha", ha)
    text_kw.setdefault("transform", ax.transAxes)
    # Default bbox: white background, no border
    text_kw.setdefault("bbox", dict(boxstyle="round,pad=0.3", facecolor="white",
                                     edgecolor="none", alpha=0.9))
    return ax.text(x, y, text, fontsize=fontsize, **text_kw)


# ---------------------------------------------------------------------------
# AI Visual Review — low-res save for Claude to inspect
# ---------------------------------------------------------------------------

def save_for_review(fig, path="figure_review.png", dpi=100):
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path


def check_overlaps(fig, axes_dict, min_px=5):
    renderer = fig.canvas.get_renderer()
    boxes = {lbl: ax.get_tightbbox(renderer) for lbl, ax in axes_dict.items()}
    max_area = 0
    pairs = []
    for (la, ba), (lb, bb) in combinations(boxes.items(), 2):
        ow = min(ba.x1, bb.x1) - max(ba.x0, bb.x0)
        oh = min(ba.y1, bb.y1) - max(ba.y0, bb.y0)
        if ow > min_px and oh > min_px:
            area = ow * oh
            pairs.append((la, lb, round(ow, 1), round(oh, 1)))
            max_area = max(max_area, area)
    return max_area, pairs


# ---------------------------------------------------------------------------
# Overlap Detection — programmatic QA for all element pairs
# ---------------------------------------------------------------------------

def _get_scatter_bboxes(coll, ax, renderer):
    """Get per-point bboxes for a PathCollection (scatter).

    PathCollection.get_window_extent() returns degenerate bbox.
    Compute individual marker bboxes from offsets + marker size.
    """
    from matplotlib.transforms import Bbox
    offsets = coll.get_offsets()
    if len(offsets) == 0:
        return []
    # Transform offsets to display coords
    trans = coll.get_offset_transform()
    if trans is None:
        trans = ax.transData
    pts = trans.transform(offsets)
    # Marker size in points → pixels
    sizes = coll.get_sizes()
    if len(sizes) == 0:
        return []
    dpi = ax.get_figure().get_dpi()
    radii = np.sqrt(sizes) * 0.5 * dpi / 72.0  # half-side in pixels
    if len(radii) == 1:
        radii = np.full(len(pts), radii[0])
    elif len(radii) < len(pts):
        radii = np.resize(radii, len(pts))
    bboxes = []
    for (px, py), r in zip(pts, radii):
        bboxes.append(Bbox.from_extents(px - r, py - r, px + r, py + r))
    return bboxes


def _bbox_overlap_area(bb1, bb2):
    """Compute overlap area in pixels² between two Bbox objects."""
    from matplotlib.transforms import Bbox
    inter = Bbox.intersection(bb1, bb2)
    if inter is None:
        return 0.0
    return max(0.0, inter.width) * max(0.0, inter.height)


def _identify_element(artist):
    """Return a short human-readable identifier for an artist."""
    from matplotlib.text import Text, Annotation
    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from matplotlib.collections import PathCollection

    if isinstance(artist, Annotation):
        txt = artist.get_text()[:30]
        return f"Annotation('{txt}')"
    if isinstance(artist, Text):
        txt = artist.get_text()[:30]
        return f"Text('{txt}')"
    if isinstance(artist, Legend):
        return "Legend"
    if isinstance(artist, Line2D):
        lbl = artist.get_label()
        return f"Line2D('{lbl}')" if not lbl.startswith("_") else "Line2D"
    if isinstance(artist, PathCollection):
        lbl = artist.get_label()
        return f"Scatter('{lbl}')" if not lbl.startswith("_") else "Scatter"
    if isinstance(artist, (Rectangle, FancyBboxPatch)):
        return f"Patch({type(artist).__name__})"
    return type(artist).__name__


def _classify_element(artist):
    """Classify an artist into a category for overlap reporting."""
    from matplotlib.text import Text, Annotation
    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from matplotlib.collections import PathCollection, PolyCollection

    if isinstance(artist, Legend):
        return "legend"
    if isinstance(artist, (Text, Annotation)):
        return "text"
    if isinstance(artist, (Line2D, PathCollection, PolyCollection,
                           Rectangle, FancyBboxPatch)):
        return "data"
    return "other"


def _find_axes_label(ax, axes_dict):
    """Find the panel label key for an axes in axes_dict."""
    if axes_dict is None:
        return "?"
    for lbl, a in axes_dict.items():
        if a is ax:
            return lbl
    return "fig"


def _is_internal(artist):
    """Check if an artist is a matplotlib internal element."""
    lbl = getattr(artist, "get_label", lambda: "")()
    if isinstance(lbl, str) and lbl.startswith("_"):
        return True
    return False


def _should_skip_pair(a, b, parent_a, parent_b):
    """Check if an overlap between two artists is expected/structural."""
    from matplotlib.text import Text
    from matplotlib.legend import Legend
    from matplotlib.spines import Spine
    from matplotlib.axis import XAxis, YAxis, Tick

    # Same legend: frame + text always overlap
    if isinstance(parent_a, Legend) and parent_a is parent_b:
        return True
    # Legend text overlaps legend frame
    for x, y in [(a, b), (b, a)]:
        if isinstance(x, Legend):
            if hasattr(y, "axes") and hasattr(x, "axes"):
                if y in x.get_children():
                    return True
    # Spine + tick labels
    if isinstance(a, Spine) or isinstance(b, Spine):
        return True
    # Both are internal matplotlib elements
    if _is_internal(a) and _is_internal(b):
        return True

    # Adjacent tick labels on the same axis — structural, not a defect
    if isinstance(a, Text) and isinstance(b, Text):
        # Check if both are tick labels on the same axes
        a_ax = getattr(a, "axes", None)
        b_ax = getattr(b, "axes", None)
        if a_ax is not None and a_ax is b_ax:
            a_in_xticks = a in a_ax.get_xticklabels()
            b_in_xticks = b in a_ax.get_xticklabels()
            a_in_yticks = a in a_ax.get_yticklabels()
            b_in_yticks = b in a_ax.get_yticklabels()
            # Both on same axis → skip only if overlap is small
            # (normal adjacent labels). Large overlaps from wrapped
            # multi-line labels should be detected.
            if (a_in_xticks and b_in_xticks) or (a_in_yticks and b_in_yticks):
                # Let the caller decide based on overlap area
                # (returning False means it will be checked)
                return False

    # Heatmap cell annotations: text placed at grid positions on same axes
    # with imshow — these are expected to be close in grid layout
    if isinstance(a, Text) and isinstance(b, Text):
        a_ax = getattr(a, "axes", None)
        b_ax = getattr(b, "axes", None)
        if a_ax is not None and a_ax is b_ax:
            # Check if axes has an AxesImage (heatmap)
            import matplotlib.image as mimage
            has_image = any(isinstance(c, mimage.AxesImage)
                           for c in a_ax.get_children())
            if has_image:
                # Both are user text (not tick labels, not titles)
                if a in a_ax.texts and b in a_ax.texts:
                    return True

    return False


def detect_overlaps(fig, axes_dict=None, padding=2.0, min_overlap_px=4.0):
    """Detect all visual overlaps in a figure.

    Checks both within-panel and cross-panel overlaps by comparing
    bounding boxes in display (pixel) coordinates.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    axes_dict : dict, optional
        Mapping of panel labels to Axes (e.g., from subplot_mosaic).
        Used for labeling which panel an element belongs to.
    padding : float
        Padding in pixels added to each bbox edge before overlap check.
        Catches near-misses that look like overlaps visually.
    min_overlap_px : float
        Minimum overlap area (px²) to report. Filters out sub-pixel
        touches from floating-point imprecision.

    Returns
    -------
    list of dict
        Each dict has keys:
        - elem_a, elem_b: human-readable element identifiers
        - category: overlap type (e.g., "text-text", "legend-data")
        - panel_a, panel_b: panel labels (or "fig" for figure-level)
        - overlap_area_px: overlap area in pixels²
        - severity: "minor" (<50px²), "moderate" (<200px²), "severe" (≥200px²)
    """
    from matplotlib.text import Text, Annotation
    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D
    from matplotlib.collections import PathCollection, PolyCollection
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from matplotlib.transforms import Bbox

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # ── Collect all elements with their bboxes ──────────────────────
    Element = namedtuple("Element", ["artist", "bbox", "category",
                                      "panel", "parent"])

    elements = []

    def _add(artist, panel, parent=None):
        """Try to get bbox and add to elements list."""
        try:
            if not artist.get_visible():
                return
            bb = artist.get_window_extent(renderer)
            if bb is None or bb.width <= 0 or bb.height <= 0:
                return
            # Skip degenerate bboxes (inf values from PathCollection)
            if not np.isfinite([bb.x0, bb.y0, bb.x1, bb.y1]).all():
                return
            cat = _classify_element(artist)
            elements.append(Element(artist, bb, cat, panel, parent))
        except (AttributeError, RuntimeError, TypeError):
            pass

    # Figure-level text (panel labels, suptitle)
    for child in fig.get_children():
        if isinstance(child, Text) and child.get_text().strip():
            _add(child, "fig")

    # Per-axes elements
    all_axes = list((axes_dict or {}).values())
    if not all_axes:
        all_axes = fig.get_axes()

    for ax in all_axes:
        panel = _find_axes_label(ax, axes_dict)

        # Titles
        for title in [ax.title, ax.xaxis.label, ax.yaxis.label]:
            if title.get_text().strip():
                _add(title, panel)

        # Tick labels
        for tl in ax.get_xticklabels() + ax.get_yticklabels():
            if tl.get_text().strip():
                _add(tl, panel)

        # User text and annotations (deduplicate by id)
        _seen = set()
        for txt in ax.texts:
            if id(txt) not in _seen:
                _add(txt, panel)
                _seen.add(id(txt))
        for child in ax.get_children():
            if (isinstance(child, Annotation)
                    and child.get_text().strip()
                    and id(child) not in _seen):
                _add(child, panel)
                _seen.add(id(child))

        # Legend
        legend = ax.get_legend()
        if legend is not None:
            _add(legend, panel)

        # Data elements: lines
        for line in ax.lines:
            if not _is_internal(line):
                _add(line, panel)

        # Data elements: bars (patches) — always include Rectangle
        # patches regardless of label (ax.bar() sets "_nolegend_")
        for patch in ax.patches:
            if isinstance(patch, Rectangle):
                _add(patch, panel)

        # Data elements: scatter (PathCollection) — use per-point bboxes
        # for precise detection, but also add the collection envelope
        for coll in ax.collections:
            if isinstance(coll, PathCollection) and not _is_internal(coll):
                # Add overall envelope for legend/text vs scatter checks
                try:
                    bb = coll.get_window_extent(renderer)
                    if bb is not None and np.isfinite([bb.x0, bb.y0,
                                                       bb.x1, bb.y1]).all():
                        if bb.width > 0 and bb.height > 0:
                            elements.append(Element(coll, bb, "data",
                                                     panel, None))
                except (AttributeError, RuntimeError):
                    pass
            elif isinstance(coll, PolyCollection) and not _is_internal(coll):
                _add(coll, panel)

    # ── Legend-exceeds-axes detection ────────────────────────────────
    # Check if any legend extends past its parent axes boundary
    results = []
    for ax in all_axes:
        legend = ax.get_legend()
        if legend is None:
            continue
        # Skip bbox_to_anchor legends — they're outside by design.
        # Cross-panel bleed from these is caught by pairwise detection.
        if legend._bbox_to_anchor is not None:
            continue
        panel = _find_axes_label(ax, axes_dict)
        try:
            leg_bb = legend.get_window_extent(renderer)
            ax_bb = ax.get_window_extent(renderer)
            if leg_bb is None or ax_bb is None:
                continue
            # Check each edge
            bleeds = []
            if leg_bb.x1 > ax_bb.x1 + padding:
                bleeds.append("right")
            if leg_bb.x0 < ax_bb.x0 - padding:
                bleeds.append("left")
            if leg_bb.y1 > ax_bb.y1 + padding:
                bleeds.append("top")
            if leg_bb.y0 < ax_bb.y0 - padding:
                bleeds.append("bottom")
            if bleeds:
                # Compute how much it exceeds
                overshoot = max(
                    max(0, leg_bb.x1 - ax_bb.x1),
                    max(0, ax_bb.x0 - leg_bb.x0),
                    max(0, leg_bb.y1 - ax_bb.y1),
                    max(0, ax_bb.y0 - leg_bb.y0),
                )
                severity = "severe" if overshoot > 15 else "moderate"
                results.append({
                    "elem_a": "Legend",
                    "elem_b": f"Axes boundary ({', '.join(bleeds)})",
                    "category": "legend-overflow",
                    "panel_a": panel,
                    "panel_b": panel,
                    "scope": "within",
                    "overlap_area_px": round(overshoot, 1),
                    "severity": severity,
                    "_legend_ax": ax,  # internal: for fix_overlaps
                    "_bleeds": bleeds,
                })
        except (AttributeError, RuntimeError):
            pass

    # ── Pairwise overlap detection ──────────────────────────────────
    n = len(elements)

    def _legend_has_backdrop(artist):
        """Check if a legend has an opaque white background."""
        from matplotlib.legend import Legend
        if not isinstance(artist, Legend):
            return False
        frame = artist.get_frame()
        if frame is None:
            return False
        fc = frame.get_facecolor()
        # Check: white-ish and opaque (alpha > 0.7)
        if fc is not None and len(fc) >= 4:
            r, g, b, a = fc[:4]
            if r > 0.9 and g > 0.9 and b > 0.9 and a > 0.7:
                return True
        return False

    for i in range(n):
        for j in range(i + 1, n):
            ei, ej = elements[i], elements[j]

            # Skip expected/structural overlaps
            if _should_skip_pair(ei.artist, ej.artist,
                                  ei.parent, ej.parent):
                continue

            # Skip two internal elements
            if ei.category == "other" and ej.category == "other":
                continue

            # Skip same-panel data-data overlaps (lines crossing, bars
            # adjacent, scatter overlap — all expected in normal plots)
            if (ei.category == "data" and ej.category == "data"
                    and ei.panel == ej.panel):
                continue

            # Track if legend has white backdrop — used for severity
            _has_backdrop = False
            if ei.panel == ej.panel:
                if ((ei.category == "legend" and ej.category == "data"
                     and _legend_has_backdrop(ei.artist))
                    or (ej.category == "legend" and ei.category == "data"
                        and _legend_has_backdrop(ej.artist))):
                    _has_backdrop = True

            # Apply padding and check overlap
            bb_i = ei.bbox.expanded(
                1.0 + padding / max(ei.bbox.width, 1),
                1.0 + padding / max(ei.bbox.height, 1),
            )
            bb_j = ej.bbox.expanded(
                1.0 + padding / max(ej.bbox.width, 1),
                1.0 + padding / max(ej.bbox.height, 1),
            )

            if not bb_i.overlaps(bb_j):
                continue

            area = _bbox_overlap_area(bb_i, bb_j)
            if area < min_overlap_px:
                continue

            # Classify
            cats = sorted([ei.category, ej.category])
            category = f"{cats[0]}-{cats[1]}"

            # Severity
            if area >= 200:
                severity = "severe"
            elif area >= 50:
                severity = "moderate"
            else:
                severity = "minor"

            # Cross-panel or within-panel
            scope = "within" if ei.panel == ej.panel else "cross-panel"

            # Upgrade: panel labels bleeding cross-panel are at least
            # moderate — they indicate layout problems
            if (scope == "cross-panel" and category == "text-text"
                    and ("fig" in (ei.panel, ej.panel))
                    and severity == "minor"):
                severity = "moderate"

            # Legend with white backdrop over data: downgrade one level
            # ONLY for small overlaps (<100px²). Large overlaps are
            # still a problem even with backdrop.
            if (_has_backdrop and "legend" in category
                    and severity != "minor" and area < 100):
                severity = {"severe": "moderate",
                            "moderate": "minor"}[severity]

            results.append({
                "elem_a": _identify_element(ei.artist),
                "elem_b": _identify_element(ej.artist),
                "category": category,
                "panel_a": ei.panel,
                "panel_b": ej.panel,
                "scope": scope,
                "overlap_area_px": round(area, 1),
                "severity": severity,
            })

    # Sort: severe first, then by area
    results.sort(key=lambda r: (-{"severe": 3, "moderate": 2,
                                   "minor": 1}[r["severity"]],
                                  -r["overlap_area_px"]))
    return results


# Import namedtuple at module level if not already present
from collections import namedtuple


# ---------------------------------------------------------------------------
# Overlap Resolution — auto-fix detected overlaps
# ---------------------------------------------------------------------------

def _find_artist_axes(artist, axes_dict):
    """Find the Axes object that owns an artist, and its panel key."""
    ax = getattr(artist, "axes", None)
    if ax is not None and axes_dict:
        for key, a in axes_dict.items():
            if a is ax:
                return ax, key
    return ax, None


def _move_legend_outside(ax):
    """Move legend above the axes with bbox_to_anchor."""
    legend = ax.get_legend()
    if legend is None:
        return False
    handles, labels = ax.get_legend_handles_labels()
    if not labels:
        return False
    legend.remove()
    n = len(labels)
    ax.legend(handles, labels,
              loc="lower center", bbox_to_anchor=(0.5, 1.01),
              frameon=False, ncol=min(n, 3), fontsize=7,
              columnspacing=0.6, handletextpad=0.3)
    return True


def _shrink_legend_bbox(ax, amount=0.03):
    """Pull an outside legend's bbox_to_anchor closer to the axes."""
    legend = ax.get_legend()
    if legend is None:
        return False
    bb = legend.get_bbox_to_anchor()
    # Try to detect if legend is above the axes (y > 1 in axes coords)
    handles, labels = ax.get_legend_handles_labels()
    if not labels:
        return False
    # Re-create with a tighter bbox
    loc = legend._loc  # preserve original loc code
    legend.remove()
    ax.legend(handles, labels,
              loc="lower center", bbox_to_anchor=(0.5, 1.005),
              frameon=False, ncol=min(len(labels), 3), fontsize=7,
              columnspacing=0.5, handletextpad=0.2)
    return True


def fix_overlaps(fig, axes_dict=None, max_iter=6, padding=2.0,
                 verbose=False):
    """Iteratively detect and auto-fix overlaps in a figure.

    Handles these overlap categories:
    - legend ↔ data (within panel): move legend outside above
    - legend ↔ text (cross-panel): tighten bbox_to_anchor
    - text ↔ text (panel labels vs xlabels): increase spacing
    - text summary panel overflow: trim text

    Parameters
    ----------
    fig : Figure
    axes_dict : dict, optional
        Panel label → Axes mapping.
    max_iter : int
        Maximum fix-detect-fix iterations.
    padding : float
        Pixel padding for overlap detection.
    verbose : bool
        Print fix actions.

    Returns
    -------
    list of dict
        Remaining unfixed overlaps after all iterations.
    """
    from matplotlib.text import Text
    from matplotlib.legend import Legend

    all_actions = []
    fixed_panels = set()  # track what we've already tried
    overflow_resized = set()  # panels where legend was resized to fit

    for iteration in range(max_iter):
        fig.canvas.draw()
        results = detect_overlaps(fig, axes_dict, padding=padding)

        if not results:
            if verbose:
                print(f"  Iteration {iteration + 1}: all clear")
            break

        severe_moderate = [r for r in results
                           if r["severity"] in ("severe", "moderate")]
        # Process overflow FIRST, then cross-panel, then within-panel
        priority = {"legend-overflow": 0, "cross-panel": 1, "within": 2}
        severe_moderate.sort(
            key=lambda r: (priority.get(r["category"],
                           priority.get(r["scope"], 3)),))
        if not severe_moderate:
            if verbose:
                print(f"  Iteration {iteration + 1}: only minor issues remain")
            break

        fixed_any = False

        for r in severe_moderate:
            cat = r["category"]
            scope = r["scope"]
            panel_a = r["panel_a"]
            panel_b = r["panel_b"]
            fix_key = f"{cat}:{panel_a}:{panel_b}"

            # Skip if we already tried this exact fix — BUT allow
            # retrying if it's a cross-panel legend issue (outside
            # placement in one iteration can cause new cross-panel
            # bleed that needs spacing fix in the next)
            if fix_key in fixed_panels:
                if not ("legend" in cat and scope == "cross-panel"):
                    continue

            # ── Fix: legend overflowing its axes boundary ────────
            #   Skip bbox_to_anchor legends (outside by design) —
            #   cross-panel handler will handle their bleed
            if cat == "legend-overflow":
                ax = r.get("_legend_ax")
                # bbox_to_anchor legends that overflow: move inside
                if (ax and ax.get_legend()
                        and ax.get_legend()._bbox_to_anchor is not None):
                    legend = ax.get_legend()
                    handles, labels = ax.get_legend_handles_labels()
                    legend.remove()
                    panel = _find_axes_label(ax, axes_dict)
                    # Try all positions, pick least data overlap
                    best_loc = "upper left"
                    best_ov = float("inf")
                    for try_loc in ["lower right", "upper right",
                                    "lower left", "upper left",
                                    "center right", "center left"]:
                        ax.legend(handles, labels, loc=try_loc,
                                  frameon=True, facecolor="white",
                                  edgecolor="none", framealpha=0.9,
                                  fontsize=7, ncol=1,
                                  handletextpad=0.2,
                                  handlelength=0.8, borderpad=0.3)
                        fig.canvas.draw()
                        rdr = fig.canvas.get_renderer()
                        lbb = ax.get_legend().get_window_extent(rdr)
                        abb = ax.get_window_extent(rdr)
                        if (lbb.x1 > abb.x1 + 2 or lbb.x0 < abb.x0 - 2
                                or lbb.y1 > abb.y1 + 2
                                or lbb.y0 < abb.y0 - 2):
                            continue
                        ov = 0
                        for ln in ax.lines:
                            if ln.get_label().startswith("_"):
                                continue
                            try:
                                ov += _bbox_overlap_area(
                                    lbb, ln.get_window_extent(rdr))
                            except Exception:
                                pass
                        from matplotlib.patches import Rectangle as _R
                        for patch in ax.patches:
                            if isinstance(patch, _R):
                                try:
                                    ov += _bbox_overlap_area(
                                        lbb, patch.get_window_extent(rdr))
                                except Exception:
                                    pass
                        if ov < best_ov:
                            best_ov = ov
                            best_loc = try_loc
                    if best_ov == 0:
                        ax.legend(handles, labels, loc=best_loc,
                                  frameon=True, facecolor="white",
                                  edgecolor="none", framealpha=0.9,
                                  fontsize=7, ncol=1,
                                  handletextpad=0.2,
                                  handlelength=0.8, borderpad=0.3)
                        action = (f"Moved legend to clean "
                                  f"loc='{best_loc}' in {panel}")
                    else:
                        # Keep outside — width-aware ncol
                        fig.canvas.draw()
                        rdr = fig.canvas.get_renderer()
                        ax_w = ax.get_window_extent(rdr).width
                        for try_nc in [min(len(labels), 3), 2, 1]:
                            ax.legend(handles, labels,
                                      loc="lower center",
                                      bbox_to_anchor=(0.5, 1.005),
                                      frameon=False, ncol=try_nc,
                                      fontsize=7,
                                      columnspacing=0.5,
                                      handletextpad=0.2)
                            fig.canvas.draw()
                            rdr = fig.canvas.get_renderer()
                            lw = ax.get_legend().get_window_extent(
                                rdr).width
                            if lw <= ax_w * 1.05:
                                break
                        # Height check
                        fig.canvas.draw()
                        rdr = fig.canvas.get_renderer()
                        leg_bb = ax.get_legend().get_window_extent(rdr)
                        ax_bb = ax.get_window_extent(rdr)
                        overshoot = leg_bb.y1 - ax_bb.y1
                        ss = ax.get_subplotspec().get_topmost_subplotspec()
                        this_row = ss.rowspan.start
                        gap_avail = float("inf")
                        for k2, ax2 in (axes_dict or {}).items():
                            ss2 = ax2.get_subplotspec().get_topmost_subplotspec()
                            if ss2.rowspan.start < this_row:
                                ax2_bb = ax2.get_window_extent(rdr)
                                gap_avail = min(gap_avail,
                                                ax_bb.y1 - ax2_bb.y0)
                        if overshoot > gap_avail - 5:
                            cur_h = fig.get_figheight()
                            extra = (overshoot - gap_avail + 10) / fig.dpi
                            fig.set_figheight(cur_h + extra)
                        action = (f"Kept legend outside {panel} "
                                  f"(ncol={try_nc})")
                    overflow_resized.add(panel)
                    all_actions.append(action)
                    fixed_panels.add(fix_key)
                    if verbose:
                        print(f"  FIX: {action}")
                    fixed_any = True
                    continue
                if ax is not None:
                    legend = ax.get_legend()
                    if legend is not None:
                        handles, labels = (
                            ax.get_legend_handles_labels())
                        bleeds = r.get("_bleeds", [])
                        legend.remove()

                        # Strategy: progressively compact
                        # Try ncol=1 first, then shrink font, then
                        # abbreviate more aggressively
                        trunc_levels = [
                            lambda lb: lb,  # full
                            lambda lb: (lb.split("(")[0].strip()[:6]
                                        + " (" + lb.split("(")[1]
                                        if "(" in lb and len(lb) > 10
                                        else lb[:10]
                                        if len(lb) > 10 else lb),
                            lambda lb: (lb[0] + " (" + lb.split("(")[1]
                                        if "(" in lb
                                        else lb[:6]),  # first char only
                        ]
                        fits = False
                        for trunc_fn in trunc_levels:
                          for attempt_fs in [7, 6, 5.5]:
                            for attempt_ncol in [1, 2]:
                                short = [trunc_fn(lb) for lb in labels]
                                loc, _ = find_best_legend_loc(
                                    ax, n_items=len(short))
                                ax.legend(
                                    handles, short, loc=loc,
                                    frameon=True, facecolor="white",
                                    edgecolor="none", framealpha=0.9,
                                    fontsize=attempt_fs,
                                    ncol=attempt_ncol,
                                    columnspacing=0.3,
                                    handletextpad=0.15,
                                    handlelength=0.8,
                                    borderpad=0.3)
                                fig.canvas.draw()
                                renderer = fig.canvas.get_renderer()
                                leg_bb = ax.get_legend(
                                    ).get_window_extent(renderer)
                                ax_bb = ax.get_window_extent(renderer)
                                # Check if it fits now
                                fits = (leg_bb.x1 <= ax_bb.x1 + 2
                                        and leg_bb.x0 >= ax_bb.x0 - 2
                                        and leg_bb.y1 <= ax_bb.y1 + 2
                                        and leg_bb.y0 >= ax_bb.y0 - 2)
                                if fits:
                                    break
                            if fits:
                                break
                          if fits:
                              break

                        action = (f"Resized legend to fit in panel "
                                  f"{panel_a} (fs={attempt_fs}, "
                                  f"ncol={attempt_ncol})")
                        all_actions.append(action)
                        fixed_panels.add(fix_key)
                        overflow_resized.add(panel_a)
                        if verbose:
                            print(f"  FIX: {action}")
                        fixed_any = True
                        continue

            # ── Fix: legend overlapping data (within panel) ──────
            #   Try best inside position first. If still overlapping,
            #   move legend outside above the panel.
            #   Skip if already resized by overflow handler.
            if ("legend" in cat and scope == "within"
                    and cat != "legend-overflow"):
                ax = None
                legend_panel = None
                for p in [panel_a, panel_b]:
                    if axes_dict and p in axes_dict:
                        if axes_dict[p].get_legend() is not None:
                            ax = axes_dict[p]
                            legend_panel = p
                            break
                if legend_panel in overflow_resized:
                    fixed_panels.add(fix_key)
                    continue
                if ax is not None:
                    legend = ax.get_legend()
                    if legend is not None:
                        handles, labels = ax.get_legend_handles_labels()
                        legend.remove()

                        # Check if overlap involves lines — line-heavy
                        # panels never have clean inside positions
                        from matplotlib.lines import Line2D as _L2D
                        has_lines = any(isinstance(l, _L2D)
                                        for l in ax.lines
                                        if not l.get_label()
                                        .startswith("_"))
                        loc, count = find_best_legend_loc(
                            ax, n_items=len(labels))

                        # Try ALL 8 positions, measure actual pixel
                        # overlap with data, pick the LEAST overlap
                        best_loc = loc
                        best_overlap = float("inf")
                        locs_to_try = [
                            "lower right", "upper right", "lower left",
                            "upper left", "center right", "center left",
                            "upper center", "lower center",
                        ]
                        fig.canvas.draw()
                        for try_loc in locs_to_try:
                            ax.legend(handles, labels, loc=try_loc,
                                      frameon=True, facecolor="white",
                                      edgecolor="none", framealpha=0.9,
                                      fontsize=7, ncol=1,
                                      handletextpad=0.2,
                                      handlelength=0.8,
                                      borderpad=0.3)
                            fig.canvas.draw()
                            rdr = fig.canvas.get_renderer()
                            leg = ax.get_legend()
                            leg_bb = leg.get_window_extent(rdr)
                            ax_bb = ax.get_window_extent(rdr)
                            # Check it fits within axes
                            if (leg_bb.x1 > ax_bb.x1 + 2
                                    or leg_bb.x0 < ax_bb.x0 - 2
                                    or leg_bb.y1 > ax_bb.y1 + 2
                                    or leg_bb.y0 < ax_bb.y0 - 2):
                                continue  # doesn't fit — skip
                            # Measure overlap with data elements
                            total_ov = 0
                            for line in ax.lines:
                                if line.get_label().startswith("_"):
                                    continue
                                try:
                                    lbb = line.get_window_extent(rdr)
                                    total_ov += _bbox_overlap_area(
                                        leg_bb, lbb)
                                except Exception:
                                    pass
                            for coll in ax.collections:
                                try:
                                    cbb = coll.get_window_extent(rdr)
                                    if np.isfinite([cbb.x0, cbb.y0,
                                                    cbb.x1, cbb.y1]).all():
                                        total_ov += _bbox_overlap_area(
                                            leg_bb, cbb)
                                except Exception:
                                    pass
                            # Check bars (Rectangle patches)
                            from matplotlib.patches import Rectangle \
                                as _Rect
                            for patch in ax.patches:
                                if isinstance(patch, _Rect):
                                    try:
                                        pbb = patch.get_window_extent(
                                            rdr)
                                        total_ov += _bbox_overlap_area(
                                            leg_bb, pbb)
                                    except Exception:
                                        pass
                            if total_ov < best_overlap:
                                best_overlap = total_ov
                                best_loc = try_loc

                        if best_overlap == 0:
                            # Clean inside position found
                            ax.legend(handles, labels, loc=best_loc,
                                      frameon=True, facecolor="white",
                                      edgecolor="none", framealpha=0.9,
                                      fontsize=7, ncol=1,
                                      handletextpad=0.2,
                                      handlelength=0.8, borderpad=0.3)
                            action = (f"Placed legend at clean "
                                      f"loc='{best_loc}' in "
                                      f"{legend_panel}")
                        else:
                            # All inside positions overlap → outside.
                            # Width-aware: try ncol=3,2,1 until legend
                            # fits within the panel width.
                            fig.canvas.draw()
                            rdr = fig.canvas.get_renderer()
                            ax_w = ax.get_window_extent(rdr).width
                            placed = False
                            for try_ncol in [min(len(labels), 3), 2, 1]:
                                ax.legend(
                                    handles, labels,
                                    loc="lower center",
                                    bbox_to_anchor=(0.5, 1.005),
                                    frameon=False,
                                    ncol=try_ncol, fontsize=7,
                                    columnspacing=0.5,
                                    handletextpad=0.2)
                                fig.canvas.draw()
                                rdr = fig.canvas.get_renderer()
                                lw = ax.get_legend().get_window_extent(
                                    rdr).width
                                if lw <= ax_w * 1.05:
                                    placed = True
                                    break
                            if not placed:
                                # Even ncol=1 too wide → shrink font
                                ax.legend(
                                    handles, labels,
                                    loc="lower center",
                                    bbox_to_anchor=(0.5, 1.005),
                                    frameon=False, ncol=1, fontsize=6,
                                    handletextpad=0.15)
                            # Height check: does the outside legend
                            # fit in the gap above this panel?
                            fig.canvas.draw()
                            rdr = fig.canvas.get_renderer()
                            leg_bb = ax.get_legend().get_window_extent(rdr)
                            ax_bb = ax.get_window_extent(rdr)
                            overshoot = leg_bb.y1 - ax_bb.y1
                            # Find the panel directly above (if any)
                            ss = ax.get_subplotspec().get_topmost_subplotspec()
                            this_row = ss.rowspan.start
                            gap_available = float("inf")
                            for k2, ax2 in (axes_dict or {}).items():
                                ss2 = ax2.get_subplotspec().get_topmost_subplotspec()
                                if ss2.rowspan.start < this_row:
                                    # Use tightbbox — includes tick
                                    # labels that extend past axes
                                    ax2_tb = ax2.get_tightbbox(rdr)
                                    if ax2_tb is None:
                                        continue
                                    gap = ax2_tb.y0 - leg_bb.y1
                                    if gap < gap_available:
                                        gap_available = gap
                            if gap_available < 5:
                                # Legend too tall for gap — increase
                                # figure height to accommodate
                                cur_h = fig.get_figheight()
                                extra = (abs(gap_available) + 15) / fig.dpi
                                fig.set_figheight(cur_h + extra)
                                action_extra = (f" +{extra:.2f}in height")
                            else:
                                action_extra = ""
                            overflow_resized.add(legend_panel)
                            action = (f"Moved legend outside above "
                                      f"{legend_panel} (ncol="
                                      f"{try_ncol}){action_extra}")
                        all_actions.append(action)
                        fixed_panels.add(fix_key)
                        if verbose:
                            print(f"  FIX: {action}")
                        fixed_any = True
                        continue

            # ── Fix: legend bleeding cross-panel ─────────────────
            if "legend" in cat and scope == "cross-panel":
                # Identify which panel's LEGEND is involved (not just
                # which panel has a legend — the overlap report tells
                # us which element is the legend)
                legend_panel = None
                elem_a_is_legend = "Legend" in r["elem_a"]
                if elem_a_is_legend:
                    legend_panel = panel_a
                else:
                    legend_panel = panel_b
                # Verify the panel actually has a legend
                if (legend_panel and axes_dict
                        and legend_panel in axes_dict
                        and axes_dict[legend_panel].get_legend() is None):
                    # Fallback: try the other panel
                    other = panel_b if elem_a_is_legend else panel_a
                    if (other in axes_dict
                            and axes_dict[other].get_legend() is not None):
                        legend_panel = other
                # If overflow-resized, don't move the legend (it was
                # Outside legend bleeds cross-panel → increase hspace
                if legend_panel in overflow_resized:
                    space_key = f"hspace:{iteration}"
                    if space_key not in fixed_panels:
                        try:
                            hs = fig.subplotpars.hspace
                            bump = min(0.05, max(0.02, hs * 0.1))
                            fig.subplots_adjust(hspace=hs + bump)
                            action = (f"Increased hspace "
                                      f"({hs:.2f}→{hs+bump:.2f}) "
                                      f"for legend in {legend_panel}")
                            all_actions.append(action)
                            fixed_panels.add(space_key)
                            if verbose:
                                print(f"  FIX: {action}")
                            fixed_any = True
                        except Exception:
                            pass
                        break
                    fixed_panels.add(fix_key)
                    continue
                if legend_panel and axes_dict:
                    ax = axes_dict[legend_panel]
                    legend = ax.get_legend()
                    if legend is not None:
                        handles, labels = ax.get_legend_handles_labels()
                        # Escalation 1: move inside with compact layout
                        inside_key = f"inside:{legend_panel}"
                        if inside_key not in fixed_panels:
                            legend.remove()
                            loc, _ = find_best_legend_loc(
                                ax, n_items=len(labels))
                            ax.legend(handles, labels, loc=loc,
                                      frameon=True, facecolor="white",
                                      edgecolor="none", framealpha=0.9,
                                      fontsize=7,
                                      ncol=min(len(labels), 3),
                                      columnspacing=0.5,
                                      handletextpad=0.2)
                            action = (f"Moved legend inside panel "
                                      f"{legend_panel} (loc='{loc}')")
                            all_actions.append(action)
                            fixed_panels.add(fix_key)
                            fixed_panels.add(inside_key)
                            if verbose:
                                print(f"  FIX: {action}")
                            fixed_any = True
                            continue

                        # Escalation 2: compact the legend — fewer
                        # columns, abbreviate long labels
                        compact_key = f"compact:{legend_panel}"
                        if compact_key not in fixed_panels:
                            legend = ax.get_legend()
                            if legend is not None:
                                handles, labels = (
                                    ax.get_legend_handles_labels())
                                legend.remove()
                                # Abbreviate long labels
                                short = []
                                for lb in labels:
                                    if len(lb) > 12:
                                        # Keep first word + parenthetical
                                        parts = lb.split("(")
                                        if len(parts) > 1:
                                            short.append(
                                                parts[0].strip()[:8]
                                                + " (" + parts[1])
                                        else:
                                            short.append(lb[:12])
                                    else:
                                        short.append(lb)
                                loc, _ = find_best_legend_loc(
                                    ax, n_items=len(short))
                                ax.legend(handles, short, loc=loc,
                                          frameon=True,
                                          facecolor="white",
                                          edgecolor="none",
                                          framealpha=0.9, fontsize=6,
                                          ncol=1,  # vertical = narrowest
                                          handletextpad=0.2,
                                          handlelength=0.8,
                                          borderpad=0.3)
                                action = (f"Compacted legend in panel "
                                          f"{legend_panel}")
                                all_actions.append(action)
                                fixed_panels.add(fix_key)
                                fixed_panels.add(compact_key)
                                if verbose:
                                    print(f"  FIX: {action}")
                                fixed_any = True
                                continue

                        # Escalation 3: increase figure spacing
                        space_key = f"hspace:{legend_panel}"
                        if space_key not in fixed_panels:
                            try:
                                hs = fig.subplotpars.hspace
                                ws = fig.subplotpars.wspace
                                bump = min(0.05, max(0.02, hs * 0.1))
                                fig.subplots_adjust(hspace=hs + bump,
                                                     wspace=ws + 0.01)
                                action = (f"Increased spacing for "
                                          f"panel {legend_panel} "
                                          f"legend clearance")
                                all_actions.append(action)
                                fixed_panels.add(fix_key)
                                fixed_panels.add(space_key)
                                if verbose:
                                    print(f"  FIX: {action}")
                                fixed_any = True
                            except Exception:
                                pass
                            break  # only adjust spacing once per iter

            # ── Fix: cross-panel text/data bleed ─────────────────
            #   Abbreviate tick labels in the panel whose labels
            #   bleed into the neighbor, then increase spacing
            if scope == "cross-panel" and "legend" not in cat:
                # Find which panel has labels bleeding out
                for bleed_panel in [panel_a, panel_b]:
                    if bleed_panel == "fig" or bleed_panel not in (
                            axes_dict or {}):
                        continue
                    abbrev_key = f"abbrev:{bleed_panel}"
                    if abbrev_key in fixed_panels:
                        continue
                    bax = axes_dict[bleed_panel]
                    bpos = bax.get_position()
                    fig.canvas.draw()
                    rdr = fig.canvas.get_renderer()
                    btb = bax.get_tightbbox(rdr)
                    if btb is None:
                        continue
                    btb_fig = fig.transFigure.inverted().transform_bbox(btb)
                    overshoot_left = bpos.x0 - btb_fig.x0
                    overshoot_right = btb_fig.x1 - bpos.x1

                    if overshoot_left > 0.02 or overshoot_right > 0.02:
                        # Y-tick labels bleed — abbreviate
                        ytls = bax.get_yticklabels()
                        cur = [t.get_text() for t in ytls]
                        short = []
                        for lb in cur:
                            lb1 = lb.replace("\n", " ").strip()
                            if len(lb1) > 15:
                                idx = lb1.find("(")
                                if idx > 0:
                                    lb1 = lb1[:idx].strip()
                                if len(lb1) > 15:
                                    lb1 = lb1[:15]
                            short.append(lb1)
                        if short != cur:
                            bax.set_yticklabels(short, fontsize=7)
                            action = (f"Abbreviated y-labels in "
                                      f"panel {bleed_panel}")
                            all_actions.append(action)
                            fixed_panels.add(abbrev_key)
                            if verbose:
                                print(f"  FIX: {action}")
                            fixed_any = True

                continue

            # ── Fix: panel label overlapping cross-panel text ────
            if (cat == "text-text" and scope == "cross-panel"
                    and "fig" in (panel_a, panel_b)):
                try:
                    current_hs = fig.subplotpars.hspace
                    bump = min(0.05, max(0.02, current_hs * 0.1))
                    fig.subplots_adjust(hspace=current_hs + bump)
                    action = (f"Increased hspace "
                              f"({current_hs:.2f}→{current_hs+bump:.2f}) "
                              f"for panel label clearance")
                    all_actions.append(action)
                    fixed_panels.add(fix_key)
                    if verbose:
                        print(f"  FIX: {action}")
                    fixed_any = True
                except Exception:
                    pass
                break

            # ── Fix: text overlapping within panel ───────────────
            #   Handles tick label overlaps (long/wrapped labels)
            if cat == "text-text" and scope == "within":
                target_panel = panel_a if panel_a != "fig" else panel_b
                if target_panel not in (axes_dict or {}):
                    fixed_panels.add(fix_key)
                    continue
                ax = axes_dict[target_panel]
                tick_key = f"tickfix:{target_panel}:{iteration}"
                if tick_key in fixed_panels:
                    continue

                # Check if overlapping texts are tick labels.
                # Extract label text from "Text('foo')" → "foo"
                def _extract(s):
                    if s.startswith("Text('") and s.endswith("')"):
                        return s[6:-2]
                    if s.startswith("Text(") and s.endswith(")"):
                        return s[5:-1]
                    return s
                ea = _extract(r["elem_a"])
                eb = _extract(r["elem_b"])
                xtick_texts = {t.get_text() for t in
                               ax.get_xticklabels() if t.get_text()}
                ytick_texts = {t.get_text() for t in
                               ax.get_yticklabels() if t.get_text()}
                a_is_xtick = ea in xtick_texts
                b_is_xtick = eb in xtick_texts
                a_is_ytick = ea in ytick_texts
                b_is_ytick = eb in ytick_texts

                if a_is_ytick or b_is_ytick:
                    # Y-tick labels overlapping at 7pt → abbreviate
                    # (NEVER reduce below 7pt)
                    # Skip if thinning already applied
                    n_positions = len(ax.get_yticks())
                    vis_labels = [t for t in ax.get_yticklabels()
                                  if t.get_visible()]
                    if len(vis_labels) < n_positions:
                        fixed_panels.add(tick_key)
                        continue
                    cur = [t.get_text() for t in
                           ax.get_yticklabels()
                           if t.get_text()]
                    if len(cur) != n_positions:
                        fixed_panels.add(tick_key)
                        continue
                    # If all labels already ≤ 3 chars, skip
                    # truncation — go straight to thinning.
                    max_cur = max((len(lb.strip()) for lb in cur),
                                  default=0)
                    if max_cur <= 3:
                        import matplotlib.ticker as _mt
                        ypos = list(ax.get_yticks())
                        keep_pos = [p for i, p in enumerate(ypos)
                                    if i % 2 == 0]
                        keep_lbl = [lb for i, lb in enumerate(cur)
                                    if i % 2 == 0]
                        ax.yaxis.set_major_locator(
                            _mt.FixedLocator(keep_pos))
                        ax.set_yticklabels(keep_lbl, fontsize=7)
                        action = (f"Thinned y-ticks in panel "
                                  f"{target_panel}")
                        all_actions.append(action)
                        fixed_panels.add(tick_key)
                        if verbose:
                            print(f"  FIX: {action}")
                        fixed_any = True
                        continue
                    resolved = False
                    any_shortened = False
                    for trunc in [15, 10, 7, 5, 3]:
                        short = []
                        for lb in cur:
                            lb1 = lb.replace("\n", " ").strip()
                            if len(lb1) > trunc:
                                idx = lb1.find("(")
                                if idx > 0 and idx <= trunc:
                                    lb1 = lb1[:idx].strip()
                                else:
                                    lb1 = lb1[:trunc]
                                any_shortened = True
                            short.append(lb1)
                        ax.set_yticklabels(short, fontsize=7)
                        fig.canvas.draw()
                        rdr = fig.canvas.get_renderer()
                        tls = [t for t in ax.get_yticklabels()
                               if t.get_text()]
                        bbs = [t.get_window_extent(rdr).expanded(
                                   1.0 + 2.0/max(t.get_window_extent(rdr).width, 1),
                                   1.0 + 2.0/max(t.get_window_extent(rdr).height, 1))
                               for t in tls]
                        still_bad = False
                        for ti in range(len(bbs)):
                            for tj in range(ti+1, len(bbs)):
                                if bbs[ti].overlaps(bbs[tj]):
                                    still_bad = True
                                    break
                            if still_bad:
                                break
                        if not still_bad:
                            resolved = True
                            break
                    # If resolved without shortening anything,
                    # it's a transient state — thin to be safe.
                    if not resolved or not any_shortened:
                        import matplotlib.ticker as _mt
                        ypos = list(ax.get_yticks())
                        ylbls = [t.get_text() for t in
                                 ax.get_yticklabels()]
                        keep_pos = [p for i, p in enumerate(ypos)
                                    if i % 2 == 0]
                        keep_lbl = [lb for i, lb in enumerate(ylbls)
                                    if i % 2 == 0 and i < len(ylbls)]
                        if keep_pos:
                            ax.yaxis.set_major_locator(
                                _mt.FixedLocator(keep_pos))
                            ax.set_yticklabels(keep_lbl, fontsize=7)
                        # Also thin x-ticks if same labels (corr matrix)
                        xpos = list(ax.get_xticks())
                        xlbls = [t.get_text() for t in
                                 ax.get_xticklabels()]
                        if (set(xlbls) & set(ylbls)
                                and len(xpos) > len(keep_pos)):
                            kx_pos = [p for i, p in enumerate(xpos)
                                      if i % 2 == 0]
                            kx_lbl = [lb for i, lb in enumerate(xlbls)
                                      if i % 2 == 0 and i < len(xlbls)]
                            if kx_pos:
                                rot = 45
                                for t in ax.get_xticklabels():
                                    if t.get_rotation() > 0:
                                        rot = t.get_rotation()
                                        break
                                ax.xaxis.set_major_locator(
                                    _mt.FixedLocator(kx_pos))
                                ax.set_xticklabels(kx_lbl, fontsize=7,
                                                    rotation=rot,
                                                    ha="right")
                        trunc = f"{trunc}+thin"
                    action = (f"Abbreviated y-ticks to {trunc} chars "
                              f"in panel {target_panel}")
                    all_actions.append(action)
                    fixed_panels.add(tick_key)
                    if verbose:
                        print(f"  FIX: {action}")
                    fixed_any = True
                    continue

                if a_is_xtick or b_is_xtick:
                    # X-tick labels overlapping at 7pt → abbreviate
                    # + rotate to 45° (NEVER below 7pt).
                    # If still overlapping at shortest, thin labels.
                    cur = [t.get_text()
                           for t in ax.get_xticklabels()]
                    resolved = False
                    for trunc in [12, 8, 6, 4, 3]:
                        short = []
                        for lb in cur:
                            lb1 = lb.replace("\n", " ").strip()
                            if len(lb1) > trunc:
                                lb1 = lb1[:trunc]
                            short.append(lb1)
                        ax.set_xticklabels(short, fontsize=7,
                                            rotation=45, ha="right")
                        fig.canvas.draw()
                        rdr = fig.canvas.get_renderer()
                        tls = [t for t in ax.get_xticklabels()
                               if t.get_text() and t.get_visible()]
                        bbs = [t.get_window_extent(rdr).expanded(
                                   1.0 + 2.0/max(t.get_window_extent(rdr).width, 1),
                                   1.0 + 2.0/max(t.get_window_extent(rdr).height, 1))
                               for t in tls]
                        still_bad = False
                        for ti in range(len(bbs)):
                            for tj in range(ti+1, len(bbs)):
                                if bbs[ti].overlaps(bbs[tj]):
                                    still_bad = True
                                    break
                            if still_bad:
                                break
                        if not still_bad:
                            resolved = True
                            break
                    if not resolved:
                        # Last resort: show every other tick
                        import matplotlib.ticker as _mt
                        xpos = list(ax.get_xticks())
                        xlbls = [t.get_text() for t in
                                 ax.get_xticklabels()]
                        keep_pos = [p for i, p in enumerate(xpos)
                                    if i % 2 == 0]
                        keep_lbl = [lb for i, lb in enumerate(xlbls)
                                    if i % 2 == 0 and i < len(xlbls)]
                        if keep_pos:
                            ax.xaxis.set_major_locator(
                                _mt.FixedLocator(keep_pos))
                            ax.set_xticklabels(keep_lbl, fontsize=7,
                                                rotation=45,
                                                ha="right")
                        trunc = f"{trunc}+thin"
                    action = (f"Abbreviated x-ticks to {trunc} chars "
                              f"+ 45° in panel {target_panel}")
                    all_actions.append(action)
                    fixed_panels.add(tick_key)
                    if verbose:
                        print(f"  FIX: {action}")
                    fixed_any = True
                    continue

                # ── Fix: annotation overlaps within panel ───────
                from matplotlib.text import Annotation as _Ann
                a_is_ann = isinstance(r.get("_artist_a"), _Ann) or \
                    "Annotation" in r["elem_a"]
                b_is_ann = isinstance(r.get("_artist_b"), _Ann) or \
                    "Annotation" in r["elem_b"]
                if (a_is_ann or b_is_ann) and scope == "within":
                    ann_key = f"annfix:{target_panel}:{iteration}"
                    if ann_key not in fixed_panels:
                        anns = [c for c in ax.get_children()
                                if isinstance(c, _Ann)
                                and c.get_text().strip()
                                and c.get_visible()]
                        if anns:
                            ok = False
                            for trunc in [25, 15, 10, 7, 5]:
                                for ann in anns:
                                    txt = ann.get_text().strip()
                                    if len(txt) > trunc:
                                        for sep in [" — ", " (", ", "]:
                                            idx = txt.find(sep)
                                            if 0 < idx <= trunc:
                                                txt = txt[:idx]
                                                break
                                        else:
                                            txt = txt[:trunc]
                                        ann.set_text(txt)
                                        ann.set_fontsize(7)
                                fig.canvas.draw()
                                rdr = fig.canvas.get_renderer()
                                ok = True
                                bbs = []
                                for ann in anns:
                                    try:
                                        bbs.append(
                                            ann.get_window_extent(rdr))
                                    except Exception:
                                        pass
                                for ii in range(len(bbs)):
                                    for jj in range(ii+1, len(bbs)):
                                        if bbs[ii].overlaps(bbs[jj]):
                                            ok = False
                                            break
                                    if not ok:
                                        break
                                if ok:
                                    break
                            if not ok:
                                # Last resort: hide overlapping anns
                                fig.canvas.draw()
                                rdr = fig.canvas.get_renderer()
                                visible = []
                                for ann in anns:
                                    bb = ann.get_window_extent(rdr)
                                    conflict = any(
                                        bb.overlaps(vb)
                                        for vb in visible)
                                    if conflict:
                                        ann.set_visible(False)
                                    else:
                                        visible.append(bb)
                                trunc = f"{trunc}+hide"
                            action = (f"Abbreviated annotations to "
                                      f"{trunc} chars in "
                                      f"{target_panel}")
                            all_actions.append(action)
                            fixed_panels.add(ann_key)
                            if verbose:
                                print(f"  FIX: {action}")
                            fixed_any = True
                            continue

                fixed_panels.add(fix_key)

        if not fixed_any:
            if verbose:
                print(f"  Iteration {iteration + 1}: no new fixes "
                      f"available ({len(severe_moderate)} remain)")
            break

    # Final check
    fig.canvas.draw()
    remaining = detect_overlaps(fig, axes_dict, padding=padding)
    remaining_sm = [r for r in remaining
                    if r["severity"] in ("severe", "moderate")]

    if verbose:
        print(f"\nFix summary: {len(all_actions)} actions taken, "
              f"{len(remaining_sm)} severe/moderate issues remain")
        for a in all_actions:
            print(f"  ✓ {a}")
        for r in remaining_sm:
            print(f"  ✗ {r['severity']}: {r['elem_a']} ↔ {r['elem_b']} "
                  f"({r['panel_a']}-{r['panel_b']})")

    return remaining


def contain_panels(fig, axes_dict, max_iter=4, min_fs=7):
    """Ensure each panel's decorations stay within its grid cell.

    Iteratively abbreviates tick labels that extend past the panel's
    allocated grid cell into neighboring panels. Keeps font at min_fs
    (default 7pt) — never reduces below the minimum.

    Call AFTER all plotting and BEFORE add_panel_labels().
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_inv = fig.transFigure.inverted()

    # Strategy: SHRINK plot area first to give labels room.
    # Only truncate labels when they're wider than the entire cell.
    # Truncation threshold decreases each iteration.
    trunc_limits = [60, 40, 25, 18]

    # Save original gridspec positions so we never shrink below 35%
    orig_positions = {lbl: ax.get_position().frozen()
                      for lbl, ax in axes_dict.items()}

    for iteration in range(max_iter):
        changed = False
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        trunc = trunc_limits[min(iteration, len(trunc_limits) - 1)]

        for lbl, ax in axes_dict.items():
            tb = ax.get_tightbbox(renderer)
            if tb is None:
                continue
            tb_fig = fig_inv.transform_bbox(tb)
            pos = ax.get_position()

            # Check if tightbbox bleeds into any neighbor
            bleeds_left = False
            bleeds_right = False
            bleeds_top = False
            bleeds_bottom = False
            max_overshoot_l = 0
            max_overshoot_r = 0

            # Leftmost panels: panel label position is the left limit.
            # Only applies when no neighbor exists to the left.
            has_left_neighbor = False
            for lbl2, ax2 in axes_dict.items():
                if ax2 is ax:
                    continue
                pos2 = ax2.get_position()
                # Same row-ish and to our left?
                if (pos2.x1 < pos.x0 + 0.05
                        and abs(pos2.y0 - pos.y0) < pos.height * 1.5):
                    has_left_neighbor = True
                    break
            if not has_left_neighbor:
                left_limit = max(pos.x0 - 0.15, 0.02)
                if tb_fig.x0 < left_limit:
                    bleeds_left = True

            for lbl2, ax2 in axes_dict.items():
                if ax2 is ax:
                    continue
                tb2 = ax2.get_tightbbox(renderer)
                if tb2 is None:
                    continue
                tb2_fig = fig_inv.transform_bbox(tb2)
                pos2 = ax2.get_position()

                if tb_fig.x0 < tb2_fig.x1 and tb_fig.x1 > tb2_fig.x0 and \
                   tb_fig.y0 < tb2_fig.y1 and tb_fig.y1 > tb2_fig.y0:
                    if pos.x0 > pos2.x0:
                        bleeds_left = True
                        ol = tb2_fig.x1 - tb_fig.x0
                        max_overshoot_l = max(max_overshoot_l, ol)
                    if pos.x1 < pos2.x1:
                        bleeds_right = True
                        or_ = tb_fig.x1 - tb2_fig.x0
                        max_overshoot_r = max(max_overshoot_r, or_)
                    if pos.y1 < pos2.y1:
                        bleeds_top = True
                    if pos.y0 > pos2.y0:
                        bleeds_bottom = True

            if bleeds_left or bleeds_right:
                # Step 1: SHRINK the plot area to give labels room.
                # Move the axes inward so labels fit within the cell.
                label_w_left = pos.x0 - tb_fig.x0  # label width on left
                label_w_right = tb_fig.x1 - pos.x1  # label width on right
                # How much to shrink? Move axes to accommodate labels
                shrink_l = label_w_left * 0.6 if bleeds_left else 0
                shrink_r = label_w_right * 0.6 if bleeds_right else 0
                new_x0 = pos.x0 + shrink_l
                new_x1 = pos.x1 - shrink_r
                # Only shrink if plot area stays > 35% of ORIGINAL
                orig_w = orig_positions[lbl].width
                if (new_x1 - new_x0) > orig_w * 0.35:
                    ax.set_position([new_x0, pos.y0,
                                     new_x1 - new_x0, pos.height])
                    changed = True

                # Step 2: if labels STILL too long for the cell,
                # truncate to trunc chars (starts generous at 60)
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                tb_new = ax.get_tightbbox(renderer)
                if tb_new is not None:
                    tb_new_fig = fig_inv.transform_bbox(tb_new)
                    still_bleeds = False
                    # Leftmost panels: re-check against left_limit
                    if not has_left_neighbor:
                        cur_pos = ax.get_position()
                        ll = max(cur_pos.x0 - 0.15, 0.02)
                        if tb_new_fig.x0 < ll:
                            still_bleeds = True
                    for lbl2, ax2 in axes_dict.items():
                        if ax2 is ax:
                            continue
                        tb2 = ax2.get_tightbbox(renderer)
                        if tb2 is None:
                            continue
                        tb2_fig = fig_inv.transform_bbox(tb2)
                        if tb_new_fig.x0 < tb2_fig.x1 and \
                           tb_new_fig.x1 > tb2_fig.x0 and \
                           tb_new_fig.y0 < tb2_fig.y1 and \
                           tb_new_fig.y1 > tb2_fig.y0:
                            still_bleeds = True
                            break

                    if still_bleeds:
                        ytls = ax.get_yticklabels()
                        cur = [t.get_text() for t in ytls
                               if t.get_text()]
                        if cur:
                            short = []
                            for lb in cur:
                                lb1 = lb.replace("\n", " ").strip()
                                if len(lb1) > trunc:
                                    # Try to cut at a natural break
                                    for sep in [" — ", " (", ", ", " "]:
                                        idx = lb1.find(sep)
                                        if 0 < idx <= trunc:
                                            lb1 = lb1[:idx]
                                            break
                                    else:
                                        lb1 = lb1[:trunc]
                                short.append(lb1)
                            if short != cur:
                                ax.set_yticklabels(short,
                                                    fontsize=min_fs)
                                changed = True

            # Bar value labels that bleed right: hide them
            if bleeds_right:
                fig.canvas.draw()
                rdr = fig.canvas.get_renderer()
                ax_bb = ax.get_window_extent(rdr)
                for txt in ax.texts:
                    try:
                        tbb = txt.get_window_extent(rdr)
                        if tbb.x1 > ax_bb.x1 + 5:
                            txt.set_visible(False)
                            changed = True
                    except Exception:
                        pass

            if bleeds_bottom or bleeds_top:
                # Step 1: SHRINK plot area vertically
                label_h_top = tb_fig.y1 - pos.y1 if bleeds_top else 0
                label_h_bot = pos.y0 - tb_fig.y0 if bleeds_bottom else 0
                shrink_t = label_h_top * 0.5 if bleeds_top else 0
                shrink_b = label_h_bot * 0.5 if bleeds_bottom else 0
                new_y0 = pos.y0 + shrink_b
                new_y1 = pos.y1 - shrink_t
                orig_h = orig_positions[lbl].height
                if (new_y1 - new_y0) > orig_h * 0.35:
                    ax.set_position([pos.x0, new_y0,
                                     pos.width, new_y1 - new_y0])
                    pos = ax.get_position()  # update for next check
                    changed = True

                # Step 2: if still bleeding, abbreviate + rotate
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                tb_new = ax.get_tightbbox(renderer)
                still_bleeds_v = False
                if tb_new is not None:
                    tb_new_fig = fig_inv.transform_bbox(tb_new)
                    for lbl2, ax2 in axes_dict.items():
                        if ax2 is ax:
                            continue
                        tb2 = ax2.get_tightbbox(renderer)
                        if tb2 is None:
                            continue
                        tb2_fig = fig_inv.transform_bbox(tb2)
                        if tb_new_fig.x0 < tb2_fig.x1 and \
                           tb_new_fig.x1 > tb2_fig.x0 and \
                           tb_new_fig.y0 < tb2_fig.y1 and \
                           tb_new_fig.y1 > tb2_fig.y0:
                            still_bleeds_v = True
                            break

                if still_bleeds_v:
                    xtls = ax.get_xticklabels()
                    cur = [t.get_text() for t in xtls
                           if t.get_text()]
                    if cur:
                        short = []
                        for lb in cur:
                            lb1 = lb.replace("\n", " ").strip()
                            if len(lb1) > trunc:
                                for sep in [" — ", " (", ", "]:
                                    idx = lb1.find(sep)
                                    if 0 < idx <= trunc:
                                        lb1 = lb1[:idx]
                                        break
                                else:
                                    lb1 = lb1[:trunc]
                            short.append(lb1)
                        if short != cur:
                            rot = xtls[0].get_rotation() \
                                if xtls else 0
                            if rot < 60:
                                rot = 45
                            ax.set_xticklabels(short,
                                                fontsize=min_fs,
                                                rotation=rot,
                                                ha="right")
                            changed = True

                # Also handle title bleeding into panel above
                if bleeds_top and ax.get_title():
                    fig.canvas.draw()
                    rdr = fig.canvas.get_renderer()
                    title_bb = ax.title.get_window_extent(rdr)
                    ax_bb = ax.get_window_extent(rdr)
                    if title_bb.y1 > ax_bb.y1 + 10:
                        # Title extends far above — reduce pad
                        ax.set_title(ax.get_title(), fontsize=min_fs,
                                      pad=1)
                        changed = True

        if not changed:
            break

    # ── Cross-panel bleed cleanup ─────────────────────────────
    # Use ORIGINAL gridspec positions to compute the gap midpoint
    # so that shrinking doesn't move the goalposts.
    #   Left side:  truncate y-tick labels until tightbbox stays
    #               right of the midpoint with the left neighbour.
    #   Right side: hide bar-value texts that cross the midpoint
    #               with the right neighbour.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for lbl, ax in axes_dict.items():
        pos = ax.get_position()

        # ── Left neighbour: truncate our y-tick labels ──────
        left_lbl = None
        for lbl2, ax2 in axes_dict.items():
            if ax2 is ax:
                continue
            opos2 = orig_positions[lbl2]
            opos = orig_positions[lbl]
            if (opos2.x1 < opos.x0 + 0.05
                    and abs(opos2.y0 - opos.y0) < opos.height * 1.5):
                left_lbl = lbl2
                break

        if left_lbl is not None:
            # Midpoint from ORIGINAL positions (stable reference)
            opos = orig_positions[lbl]
            opos_l = orig_positions[left_lbl]
            midpoint = (opos.x0 + opos_l.x1) / 2
            mid_disp = fig.transFigure.transform((midpoint, 0))[0]

            for trunc in [25, 20, 15, 12, 10, 8]:
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                # Check individual tick labels, not tightbbox
                any_past = False
                for tl in ax.get_yticklabels():
                    if not tl.get_text():
                        continue
                    try:
                        tbb = tl.get_window_extent(renderer)
                        if tbb.x0 < mid_disp:
                            any_past = True
                            break
                    except Exception:
                        pass
                if not any_past:
                    break
                ytls = ax.get_yticklabels()
                cur = [t.get_text() for t in ytls if t.get_text()]
                if not cur:
                    break
                short = []
                any_changed = False
                for lb in cur:
                    lb1 = lb.replace("\n", " ").strip()
                    if len(lb1) > trunc:
                        for sep in [" — ", " (", ", "]:
                            idx = lb1.find(sep)
                            if 0 < idx <= trunc:
                                lb1 = lb1[:idx]
                                break
                        else:
                            lb1 = lb1[:trunc]
                        any_changed = True
                    short.append(lb1)
                if not any_changed:
                    break
                ax.set_yticklabels(short, fontsize=min_fs)

        # ── Right neighbour: hide bar-value labels that cross ─
        right_lbl = None
        for lbl2, ax2 in axes_dict.items():
            if ax2 is ax:
                continue
            opos2 = orig_positions[lbl2]
            opos = orig_positions[lbl]
            if (opos2.x0 > opos.x1 - 0.05
                    and abs(opos2.y0 - opos.y0) < opos.height * 1.5):
                right_lbl = lbl2
                break

        if right_lbl is not None:
            opos = orig_positions[lbl]
            opos_r = orig_positions[right_lbl]
            mid_r = (opos.x1 + opos_r.x0) / 2
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            # mid_r in figure coords → display coords
            mid_r_disp = fig.transFigure.transform((mid_r, 0))[0]
            for txt in ax.texts:
                try:
                    if not txt.get_visible():
                        continue
                    tbb = txt.get_window_extent(renderer)
                    if tbb.x1 > mid_r_disp:
                        txt.set_visible(False)
                except Exception:
                    pass

    align_left_edges(fig, axes_dict)
    return iteration + 1


def align_left_edges(fig, axes_dict):
    """Align tightbbox left edges of leftmost panels across rows.

    Widens leftmost panels so all rows crop at the same left edge
    when saved with ``bbox_inches='tight'``.  Safe to call multiple
    times (idempotent) and after fix_overlaps.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_inv = fig.transFigure.inverted()

    rows_left = {}
    for lbl, ax in axes_dict.items():
        ss = ax.get_subplotspec().get_topmost_subplotspec()
        r = ss.rowspan.start
        c = ss.colspan.start
        if r not in rows_left or c < rows_left[r][1]:
            rows_left[r] = (lbl, c)

    leftmost_axes = [(r, axes_dict[info[0]])
                     for r, info in rows_left.items()]
    if not leftmost_axes:
        return
    tb_x0s = []
    for r, ax in leftmost_axes:
        tb = ax.get_tightbbox(renderer)
        if tb is not None:
            tb_fig = fig_inv.transform_bbox(tb)
            tb_x0s.append((r, ax, tb_fig.x0))
    if not tb_x0s:
        return
    # Use the leftmost reachable target (x0 >= 0 so all panels
    # can actually shift to it without going off-figure).
    reachable = [x for _, _, x in tb_x0s if x >= 0]
    if not reachable:
        return
    target_x0 = min(reachable)
    for r, ax, cur_x0 in tb_x0s:
        if cur_x0 > target_x0 + 0.005:
            shift = cur_x0 - target_x0
            pos = ax.get_position()
            new_x0 = pos.x0 - shift
            if new_x0 >= 0.0:
                ax.set_position([new_x0, pos.y0,
                                 pos.width + shift,
                                 pos.height])


def auto_pad_figure(fig, axes_dict, base_pad=0.06, max_iter=8, verbose=False):
    engine = fig.get_layout_engine()
    if engine is None:
        return 0, []
    pad = base_pad
    for i in range(max_iter):
        engine.set(w_pad=pad, h_pad=pad, wspace=0.03, hspace=0.04)
        fig.canvas.draw()
        max_area, pairs = check_overlaps(fig, axes_dict)
        if max_area == 0:
            return pad, []
        pad *= 1.5
    return pad, pairs


def add_panel_labels(fig, axes_dict, pad_x=-0.02, pad_y=0.01,
                     label_props=None):
    """Add bold panel labels at each panel's actual position.

    Each label is placed at the LEFT edge of its own panel's tight
    bounding box (x) and at a ROW-ALIGNED y position (the highest
    tight-bbox top in that row). The y position is clamped so labels
    never bleed into the row above.

    Parameters
    ----------
    pad_x : float
        Horizontal offset from tight-bbox left edge (figure-fraction).
    pad_y : float
        Vertical offset above row-aligned y (figure-fraction).
    """
    props = label_props or LABEL_PROPS
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_inv = fig.transFigure.inverted()

    info = {}
    for lbl, ax in axes_dict.items():
        tbox = ax.get_tightbbox(renderer)
        if tbox is None:
            continue
        tb_fig = fig_inv.transform_bbox(tbox)
        ax_pos = ax.get_position()
        ss = ax.get_subplotspec().get_topmost_subplotspec()
        info[lbl] = dict(
            x0=tb_fig.x0,       # tightbbox left (whole panel)
            y0=tb_fig.y0,       # tightbbox bottom
            y1=tb_fig.y1,       # tightbbox top
            row=ss.rowspan.start,
        )

    # Row-align y: all labels in the same grid row share the highest y1
    row_groups = defaultdict(list)
    for d in info.values():
        row_groups[d["row"]].append(d["y1"])
    row_y_top = {r: max(ys) for r, ys in row_groups.items()}

    # Also compute the BOTTOM of each row (lowest y0) for clamping
    row_y_bot = defaultdict(list)
    for d in info.values():
        row_y_bot[d["row"]].append(d["y0"])
    row_y_bot = {r: min(ys) for r, ys in row_y_bot.items()}

    # Sorted row indices
    sorted_rows = sorted(row_y_top.keys())

    for lbl, d in sorted(info.items()):
        # x: tight-bbox left edge (above all content), but clamped
        # to not bleed into the left neighbor's panel area
        ax_pos = axes_dict[lbl].get_position()
        target_x = d["x0"] + pad_x
        # Find left neighbor's right edge and don't cross it
        for lbl2, d2 in info.items():
            if lbl2 == lbl:
                continue
            ax2_pos = axes_dict[lbl2].get_position()
            # Same row, to our left?
            if (d2["row"] == d["row"]
                    and ax2_pos.x1 < ax_pos.x0):
                floor = ax2_pos.x1 + 0.005
                target_x = max(target_x, floor)
        target_x = max(target_x, 0.0)

        # y: row-aligned top + small offset — always above the panel
        target_y = row_y_top[d["row"]] + pad_y

        fig.text(target_x, target_y, lbl, **props)


def add_group_background(fig, axes_list, panel_labels=None, color=None,
                         pad=0.018, pad_bottom=0.005, rounding=0.02):
    """Draw a rounded background behind a group of axes, covering panel labels.

    Uses tight bottom padding to leave a clear gap between the background
    and any panels below the group.

    Parameters
    ----------
    fig : Figure
    axes_list : list of Axes to group
    panel_labels : list of str, optional
        Panel label characters (e.g. ["a", "b"]) to include in the bbox.
        If provided, extends the background to cover matching fig.text objects.
    color : str, optional
        Background color. Defaults to BG.
    pad : float
        Padding in figure-fraction units for left, right, and top.
    pad_bottom : float
        Bottom padding — kept small to leave a visible gap from panels below.
    rounding : float
        Corner rounding radius.
    """
    from matplotlib.patches import FancyBboxPatch

    if color is None:
        color = BG

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_inv = fig.transFigure.inverted()

    bboxes = [fig_inv.transform_bbox(ax.get_tightbbox(renderer))
              for ax in axes_list]
    x0 = min(b.x0 for b in bboxes)
    y0 = min(b.y0 for b in bboxes)
    x1 = max(b.x1 for b in bboxes)
    y1 = max(b.y1 for b in bboxes)

    # Extend bbox to cover panel label text objects
    if panel_labels:
        for txt in fig.texts:
            if txt.get_text() in panel_labels:
                tb = fig_inv.transform_bbox(txt.get_window_extent(renderer))
                x0 = min(x0, tb.x0)
                y1 = max(y1, tb.y1)

    fig.patches.append(FancyBboxPatch(
        (x0 - pad, y0 - pad_bottom),
        (x1 + pad) - (x0 - pad),
        (y1 + pad) - (y0 - pad_bottom),
        boxstyle=f"round,pad=0,rounding_size={rounding}",
        facecolor=color, edgecolor="none",
        transform=fig.transFigure, zorder=-1,
    ))


def stitch_panels(panel_paths, labels=None, ncols=2, width_ratios=None,
                  height_ratios=None, figsize=(14, 10), output="stitched_figure",
                  dpi=600, label_props=None):
    props = label_props or LABEL_PROPS
    n = len(panel_paths)
    nrows = int(np.ceil(n / ncols))
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(nrows, ncols,
                           width_ratios=width_ratios or [1] * ncols,
                           height_ratios=height_ratios or [1] * nrows,
                           hspace=0.05, wspace=0.05)
    for idx, path in enumerate(panel_paths):
        row, col = divmod(idx, ncols)
        ax = fig.add_subplot(gs[row, col])
        img = plt.imread(path)
        ax.imshow(img)
        ax.axis("off")
        if labels is not None:
            lbl = labels[idx] if idx < len(labels) else ""
            if lbl:
                bbox = gs[row, col].get_position(fig)
                fig.text(bbox.x0, bbox.y1, lbl, **props)
    fig.savefig(f"{output}.pdf", bbox_inches="tight")
    fig.savefig(f"{output}.png", dpi=dpi, bbox_inches="tight")
    save_for_review(fig, f"{output}_review.png")
    return fig


def composite_vector_pdf(panels, out_pdf, page_w, page_h=None, letters=None,
                         render_png=None, png_dpi=600, letter_fontsize=13,
                         garbage=4):
    """Composite pre-rendered VECTOR panel PDFs into ONE true-vector figure.

    Re-composites independent panel PDFs (one per matplotlib script, or exported
    from any vector source) into a single multi-panel page with PyMuPDF, so the
    result stays vector -- selectable text, infinite zoom -- instead of the
    flattened single-image PDF ("0 fonts, 1 image") that Illustrator/Keynote/
    PowerPoint export and most "layout tools" silently produce. Panel letters are
    drawn as vector bold text. This is the VECTOR sibling of ``stitch_panels``
    (which rasterises PNGs via imshow).

    Why this exists: when a journal-ready composite comes back as a single
    rasterised image, do NOT re-export from the layout tool -- re-composite the
    *original* per-panel vector PDFs here. Verify the result with
    ``pdffonts out.pdf`` (you want font rows + selectable text, not the tell-tale
    "1 image, 0 fonts").

    Parameters
    ----------
    panels : list of dict. Each places one source into a target rect (PDF points,
        TOP-LEFT origin):
          {"pdf":   path, "rect": (x0, y0, x1, y1)}   # vector panel -> show_pdf_page
          {"image": path, "rect": (x0, y0, x1, y1)}   # genuine raster band (e.g. a
                                                       #   schematic illustration)
        A heavy point cloud (>~50k points, e.g. a volcano/UMAP) is NOT a reason
        to use "image": keep the panel a vector PDF whose scatter layer was saved
        with ``rasterized=True`` so only the dots are pixels and axes/text stay
        vector. Reserve "image" for assets that have no vector form.
        Optional per-panel "letter"/"lx"/"ly" draws that panel's letter.
        ``keep_proportion=True`` is always used, so a panel is fit (never
        stretched) inside its rect -- make the rect match the panel aspect.
        Each "pdf" source must be a SINGLE-PAGE PDF (only page 0 composites; a
        multi-page source raises). Vector formats with no PDF form (SVG, EPS)
        must be converted to a one-page PDF first (e.g. ``rsvg-convert -f pdf``
        or ``cairosvg``) before going in as a "pdf" panel.
    page_w : float           page width in points (pick to match the panel block,
                             not a fixed paper size).
    page_h : float or None   page height; if None, inferred to bound all rect
                             bottoms AND any letter baselines (so nothing clips).
    letters : list of (char, x, y)   standalone panel letters in page points,
                             drawn bold black via the base-14 "hebo"
                             (Helvetica-Bold) font. (x, y) is the text BASELINE
                             in TOP-LEFT coords (y increases downward): ly ~ y0
                             sits the letter just ABOVE a panel, ly ~ y0 +
                             letter_fontsize sits it just inside the top-left.
                             Continue the alphabet across sub-blocks (band a-c,
                             grid d-o) for one global order.
    render_png : path or None   also rasterise the master to PNG (for Word/.qmd
                             embed, which cannot place a vector PDF inline). Its
                             parent dir is created if missing.
    png_dpi : int            dpi for that PNG fallback (600 for print).
    letter_fontsize : int    panel-letter size in points (bold).
    garbage : int            xref garbage-collection level passed to doc.save
                             (0-4; 4 = most aggressive / smallest file, default).

    Returns (page_w, page_h). Raises a data-integrity stop before writing
    anything (FileNotFoundError on a missing source, ValueError on a
    missing/malformed rect or a multi-page source) rather than emitting a
    half-built figure.
    """
    import os
    import fitz  # PyMuPDF -- lazy import; only this helper needs it.

    # Validate everything up front: a clear data-integrity stop beats a
    # half-built figure or a bare KeyError from deep inside the draw loop.
    for i, p in enumerate(panels):
        rect = p.get("rect")
        if rect is None or len(rect) != 4:
            raise ValueError(f"panel {i}: missing/malformed 'rect' (need "
                             f"(x0, y0, x1, y1) in PDF points): {rect!r}")
        src = p.get("pdf") or p.get("image")
        if not src or not os.path.exists(src):
            raise FileNotFoundError(
                f"Cannot proceed - required panel source not found: {src}")

    letter_seq = [(p["letter"], p.get("lx", p["rect"][0]), p.get("ly", p["rect"][1]))
                  for p in panels if p.get("letter")]
    letter_seq += list(letters or [])
    if page_h is None:
        # Bound rect bottoms AND any letter baseline, so a low letter (or a
        # standalone letter below the lowest panel) is never clipped off.
        page_h = max([p["rect"][3] for p in panels]
                     + [ly for _, _, ly in letter_seq])

    doc = fitz.open()
    try:
        page = doc.new_page(width=page_w, height=page_h)
        # Place every panel FIRST; draw letters LAST so they sit on top.
        for p in panels:
            rect = fitz.Rect(*p["rect"])
            if "pdf" in p:
                with fitz.open(p["pdf"]) as s:
                    if s.page_count != 1:
                        raise ValueError(
                            f"{p['pdf']}: source must be single-page (has "
                            f"{s.page_count}); only page 0 would composite. "
                            f"Export/convert each panel to one page first.")
                    page.show_pdf_page(rect, s, 0, keep_proportion=True)
            else:
                page.insert_image(rect, filename=p["image"], keep_proportion=True)
        for ch, lx, ly in letter_seq:
            page.insert_text((lx, ly), ch, fontsize=letter_fontsize,
                             fontname="hebo", color=(0, 0, 0))
        doc.save(out_pdf, garbage=garbage, deflate=True)
    finally:
        doc.close()  # never leak the master handle, even if a panel errors

    if render_png:
        os.makedirs(os.path.dirname(os.path.abspath(render_png)), exist_ok=True)
        with fitz.open(out_pdf) as d:
            d[0].get_pixmap(dpi=png_dpi, alpha=False).save(render_png)
    return page_w, page_h
