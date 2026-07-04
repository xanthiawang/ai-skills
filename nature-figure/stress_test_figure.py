"""
Stress-test figure: 8 diverse panel types in a 3-row mosaic.

Tests: barh, density scatter, heatmap, forest plot, volcano,
violin+strip, spaghetti trajectories (spanning), line+confidence bands.

This is a RENDERING UTILITY TEST — data is illustrative, not scientific.
"""
import sys, os
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import Normalize
import numpy as np
from nature_figure_utils import (
    retro_style, trim_axes, figsize_nature, save_for_review,
    find_best_legend_loc, smart_annotate, place_stat_text,
    scatter_outlined, auto_pad_figure, add_panel_labels,
    add_elbow_annotation,
    RUST, GRAY, BLUE, GOLD, SAGE, PLUM,
    INK, BG, BG_COLORS, ALPHA,
    CMAP_RUST, CMAP_DIVERGE,
)

np.random.seed(42)

# ── Font size floor: 7pt minimum for ALL text at print size ────────
FS_TICK = 7      # tick labels (retro_style default)
FS_LABEL = 7     # axis labels — match tick labels
FS_TITLE = 7     # panel titles
FS_ANN = 7       # annotations, bar labels, heatmap cell text
FS_LEGEND = 7    # legend text
FS_STAT = 7      # stat text boxes

# ── Style ──────────────────────────────────────────────────────────
colors = retro_style()

# ── Layout: 3 rows, panel g spans 2 columns ───────────────────────
fig, axd = plt.subplot_mosaic(
    [["a", "b", "c"],
     ["d", "e", "f"],
     ["g", "g", "h"]],
    figsize=figsize_nature("double", aspect=0.6),
    layout="constrained",
    gridspec_kw=dict(height_ratios=[1, 1, 0.85]),
)
fig.get_layout_engine().set(h_pad=0.01, w_pad=0.01, hspace=0.04, wspace=0.04)

# ══════════════════════════════════════════════════════════════════
# Panel a — Horizontal bar chart (barh)
# ══════════════════════════════════════════════════════════════════
ax = axd["a"]
conditions = ["APOE", "CLU", "BIN1", "PICALM", "CR1", "ABCA7"]
values = [4.2, 3.8, 3.5, 3.1, 2.9, 2.1]
bar_colors = [RUST["400"], RUST["300"], RUST["200"],
              BLUE["300"], BLUE["200"], GRAY["200"]]

y_pos = np.arange(len(conditions))
bars = ax.barh(y_pos, values, height=0.4, color=bar_colors,
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(y_pos)
ax.set_yticklabels(conditions, fontsize=FS_TICK)
ax.set_xlabel("OR", fontsize=FS_LABEL)
ax.set_title("AD risk loci", fontsize=FS_TITLE, pad=2)
ax.set_ylim(y_pos[0] - 0.5, y_pos[-1] + 0.5)
ax.axvline(1.0, color=INK, ls="--", lw=0.5, alpha=0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, val in zip(bars, values):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", ha="left", fontsize=FS_ANN, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══════════════════════════════════════════════════════════════════
# Panel b — Density scatter (scatter_outlined)
# ══════════════════════════════════════════════════════════════════
ax = axd["b"]
n_pts = 400
x_sc = np.random.normal(5, 1.5, n_pts)
y_sc = 0.7 * x_sc + np.random.normal(0, 1.2, n_pts)
from scipy.stats import gaussian_kde, pearsonr
xy = np.vstack([x_sc, y_sc])
z = gaussian_kde(xy)(xy)
order = z.argsort()
scatter_outlined(ax, x_sc[order], y_sc[order], s=8, c=z[order],
                 cmap=CMAP_RUST, alpha=0.8)
r_val, p_val = pearsonr(x_sc, y_sc)
place_stat_text(ax, f"$r$ = {r_val:.2f}\n$p$ < 0.001", fontsize=FS_STAT)
ax.set_xlabel("Predicted expr.", fontsize=FS_LABEL)
ax.set_ylabel("Observed expr.", fontsize=FS_LABEL)
ax.set_title("Expression correlation", fontsize=FS_TITLE, pad=2)

# ══════════════════════════════════════════════════════════════════
# Panel c — Annotated heatmap (5×5)
# ══════════════════════════════════════════════════════════════════
ax = axd["c"]
hm_data = np.array([
    [1.0, 0.72, 0.45, 0.21, 0.08],
    [0.72, 1.0, 0.58, 0.33, 0.15],
    [0.45, 0.58, 1.0, 0.67, 0.29],
    [0.21, 0.33, 0.67, 1.0, 0.54],
    [0.08, 0.15, 0.29, 0.54, 1.0],
])
hm_labels = ["Brain", "Blood", "Liver", "Kidney", "Lung"]
im = ax.imshow(hm_data, cmap=CMAP_RUST, aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(5))
ax.set_xticklabels(hm_labels, fontsize=FS_TICK, rotation=45, ha="right")
ax.set_yticks(range(5))
ax.set_yticklabels(hm_labels, fontsize=FS_TICK)
ax.set_title("Tissue correlation", fontsize=FS_TITLE, pad=2)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(length=0)
norm = Normalize(vmin=0, vmax=1)
for i in range(5):
    for j in range(5):
        val = hm_data[i, j]
        rgba = CMAP_RUST(norm(val))
        brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
        text_color = "white" if brightness < 0.5 else INK
        ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                fontsize=FS_ANN, color=text_color)

# ══════════════════════════════════════════════════════════════════
# Panel d — Forest plot
# ══════════════════════════════════════════════════════════════════
ax = axd["d"]
tissues = ["Hippocampus", "Cortex", "Cerebellum", "Amygdala", "Striatum"]
effect = [1.35, 1.22, 1.08, 0.95, 0.88]
ci_lo = [1.12, 1.05, 0.92, 0.78, 0.71]
ci_hi = [1.62, 1.42, 1.26, 1.15, 1.09]

y_fp = np.arange(len(tissues))
xerr = [[e - l for e, l in zip(effect, ci_lo)],
        [h - e for e, h in zip(effect, ci_hi)]]
ax.errorbar(effect, y_fp, xerr=xerr, fmt="s", color="black",
            markersize=3, capsize=2, elinewidth=0.6, capthick=0.6,
            clip_on=False)
ax.axvline(1.0, color=GRAY["300"], ls="--", lw=0.5)
ax.set_yticks(y_fp)
ax.set_yticklabels(tissues, fontsize=FS_TICK)
ax.set_xlabel("Hazard ratio", fontsize=FS_LABEL)
ax.set_title("Tissue-specific risk", fontsize=FS_TITLE, pad=2)
ax.invert_yaxis()
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
xt = np.asarray(ax.get_xticks(minor=False))
xl = ax.get_xlim()
xt_in = xt[(xt >= xl[0]) & (xt <= xl[1])]
if len(xt_in) >= 2:
    ax.spines["bottom"].set_bounds(float(xt_in[0]), float(xt_in[-1]))

# ══════════════════════════════════════════════════════════════════
# Panel e — Volcano plot
# ══════════════════════════════════════════════════════════════════
ax = axd["e"]
n_genes = 300
log2fc = np.random.normal(0, 1.5, n_genes)
pvals = 10 ** (-np.abs(log2fc) * np.random.uniform(0.5, 3, n_genes))
neg_log_p = -np.log10(pvals)
fc_thresh, p_thresh = 1.0, 0.05
sig_up = (log2fc > fc_thresh) & (pvals < p_thresh)
sig_down = (log2fc < -fc_thresh) & (pvals < p_thresh)
ns = ~(sig_up | sig_down)

ax.scatter(log2fc[ns], neg_log_p[ns], s=4, alpha=ALPHA["ns_scatter"],
           c=GRAY["100"], zorder=1, clip_on=False)
ax.scatter(log2fc[sig_up], neg_log_p[sig_up], s=6, alpha=ALPHA["scatter"],
           c=RUST["400"], label="Up", zorder=2, clip_on=False)
ax.scatter(log2fc[sig_down], neg_log_p[sig_down], s=6, alpha=ALPHA["scatter"],
           c=BLUE["300"], label="Down", zorder=2, clip_on=False)
ax.axvline(fc_thresh, color=INK, ls="--", lw=0.4, alpha=0.4)
ax.axvline(-fc_thresh, color=INK, ls="--", lw=0.4, alpha=0.4)
ax.axhline(-np.log10(p_thresh), color=INK, ls="--", lw=0.4, alpha=0.4)

x_range = log2fc.max() - log2fc.min()
data_margin = x_range * 0.05
stub_len = 0.3

score = neg_log_p * np.abs(log2fc)
y_range = neg_log_p.max() - neg_log_p.min()
# Gap must account for 7pt text height in data coords
ax_h_inch = fig.get_figheight() * ax.get_position().height
text_h_data = (FS_ANN / 72.0) * (y_range / ax_h_inch) if ax_h_inch > 0 else 1
y_gap = max(y_range * 0.10, text_h_data * 2.0)

up_indices = np.where(sig_up)[0]
down_indices = np.where(sig_down)[0]
top_up = up_indices[np.argsort(score[up_indices])[-3:]] if len(up_indices) > 0 else []
top_dn = down_indices[np.argsort(score[down_indices])[-2:]] if len(down_indices) > 0 else []

# Generous symmetric xlim — extra space IS the annotation clearance
# Symmetric xlim: extend enough that 7pt annotation text has visible
# clearance from the y-axis spine in a compact 3-column panel
x_absmax = max(abs(log2fc.min()), abs(log2fc.max()))
ax.set_xlim(-x_absmax * 2.5, x_absmax * 2.5)
ax.set_ylim(-0.2, neg_log_p.max() + neg_log_p.max() * 0.1)
ax.set_xlabel("log$_2$ FC", fontsize=FS_LABEL)
ax.set_ylabel("$-$log$_{10}$ $p$", fontsize=FS_LABEL)

right_names = ["KRAS", "TP53", "MYC"]
left_names = ["BRCA1", "EGFR"]
left_text_objs = []
right_text_objs = []

if len(top_up) > 0:
    sorted_up = sorted(top_up, key=lambda i: -neg_log_p[i])
    up_name_map = {sorted_up[k]: n for k, n in enumerate(right_names)}
    right_col = max(log2fc[i] for i in sorted_up) + data_margin + 0.4
    y_top_r = max(neg_log_p[i] for i in sorted_up) + 0.3
    for rank, idx in enumerate(sorted_up):
        _, txt = add_elbow_annotation(ax, up_name_map[idx],
            xy=(log2fc[idx], neg_log_p[idx]),
            xytext=(right_col, y_top_r - rank * y_gap),
            direction="right", color=INK, lw=0.4, fontsize=FS_ANN, stub=stub_len)
        right_text_objs.append(txt)

if len(top_dn) > 0:
    sorted_dn = sorted(top_dn, key=lambda i: -neg_log_p[i])
    dn_name_map = {sorted_dn[k]: n for k, n in enumerate(left_names)}
    left_col = min(log2fc[i] for i in sorted_dn) - data_margin - 0.4
    y_top_l = max(neg_log_p[i] for i in sorted_dn) + 0.3
    for rank, idx in enumerate(sorted_dn):
        _, txt = add_elbow_annotation(ax, dn_name_map[idx],
            xy=(log2fc[idx], neg_log_p[idx]),
            xytext=(left_col, y_top_l - rank * y_gap),
            direction="left", color=INK, lw=0.4, fontsize=FS_ANN, stub=stub_len)
        left_text_objs.append(txt)

# No tightening — the generous xlim provides the annotation clearance

ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01),
          frameon=False, ncol=2, fontsize=FS_LEGEND, columnspacing=0.8,
          handletextpad=0.3)

# ══════════════════════════════════════════════════════════════════
# Panel f — Violin + strip plot
# ══════════════════════════════════════════════════════════════════
ax = axd["f"]
viol_data = [np.random.normal(m, 0.8, 25) for m in [2.5, 3.2, 4.1, 3.8]]
group_names = ["Ctrl", "Low", "Mid", "High"]
pal = [GRAY["200"], RUST["200"], RUST["300"], RUST["400"]]

parts = ax.violinplot(viol_data, positions=range(1, 5), showextrema=False,
                      showmedians=False)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(pal[i])
    pc.set_alpha(ALPHA["violin"])
    pc.set_edgecolor("none")
for i, d in enumerate(viol_data):
    jitter = np.random.uniform(-0.08, 0.08, len(d))
    ax.scatter(np.full_like(d, i + 1) + jitter, d, s=4, c="black",
               alpha=0.4, zorder=3, clip_on=False)
means = [np.mean(d) for d in viol_data]
ax.scatter(range(1, 5), means, s=25, facecolors="white",
           edgecolors="black", linewidths=0.6, zorder=5, clip_on=False)
ax.set_xticks(range(1, 5))
ax.set_xticklabels(group_names, fontsize=FS_TICK)
ax.set_ylabel("Expression", fontsize=FS_LABEL)
ax.set_title("Dose response", fontsize=FS_TITLE, pad=2)
all_vals = np.concatenate(viol_data)
ax.set_ylim(all_vals.min() - 0.3, all_vals.max() + 0.3)

# ══════════════════════════════════════════════════════════════════
# Panel g — Spaghetti / trajectory plot (spans 2 columns)
# ══════════════════════════════════════════════════════════════════
ax = axd["g"]
timepoints = np.array([0, 6, 12, 18, 24])
n_subj = 20
for group, col, label in [("ctrl", GRAY["300"], "Control"),
                           ("treat", RUST["300"], "Treatment")]:
    base = 50 if group == "ctrl" else 55
    slope = -0.3 if group == "ctrl" else 0.8
    trajs = []
    for _ in range(n_subj):
        intercept = base + np.random.normal(0, 5)
        subj_slope = slope + np.random.normal(0, 0.3)
        traj = intercept + subj_slope * timepoints + np.random.normal(0, 2, len(timepoints))
        trajs.append(traj)
        ax.plot(timepoints, traj, color=col, lw=0.5, alpha=0.25)
    group_mean = np.mean(trajs, axis=0)
    ax.plot(timepoints, group_mean, color=col, lw=1.8, label=label, zorder=10)

ax.set_xlabel("Time (months)", fontsize=FS_LABEL)
ax.set_ylabel("Cognitive score", fontsize=FS_LABEL)
ax.legend(loc="upper left", frameon=True, facecolor="white",
          edgecolor="none", framealpha=0.9, fontsize=FS_LEGEND)

# ══════════════════════════════════════════════════════════════════
# Panel h — Line + confidence bands
# ══════════════════════════════════════════════════════════════════
ax = axd["h"]
t = np.linspace(0, 48, 50)
line_colors = [GRAY["300"], RUST["300"], BLUE["300"]]
cond_labels = ["Placebo", "Drug A", "Drug B"]
for i, (label, col) in enumerate(zip(cond_labels, line_colors)):
    base = 1.0 + i * 0.3
    y_mean = base + 0.02 * t + 0.001 * i * t
    y_err = 0.15 + 0.005 * t
    ax.plot(t, y_mean, color=col, lw=1.0, label=label, zorder=2)
    ax.fill_between(t, y_mean - y_err, y_mean + y_err,
                    alpha=ALPHA["band"], color=col)

ax.set_xlabel("Time (h)", fontsize=FS_LABEL)
ax.set_ylabel("Fold change", fontsize=FS_LABEL)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01),
          frameon=False, ncol=3, fontsize=FS_LEGEND, columnspacing=0.6,
          handletextpad=0.3)

# ══════════════════════════════════════════════════════════════════
# Finalize
# ══════════════════════════════════════════════════════════════════
auto_pad_figure(fig, axd)
exclude = {axd["a"], axd["c"], axd["d"]}
trim_axes(fig, exclude=exclude)
add_panel_labels(fig, axd)

out_dir = os.path.dirname(__file__)
fig.savefig(os.path.join(out_dir, "stress_test.png"), dpi=300, bbox_inches="tight")
save_for_review(fig, os.path.join(out_dir, "stress_test_review.png"), dpi=72)
print("Saved stress_test.png and stress_test_review.png")
