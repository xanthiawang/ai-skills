"""
15-panel stress test: maximum diversity for detect_overlaps validation.

Layout: 6 rows × 3 columns, two spanning panels.
Plot types: barh, scatter, heatmap, forest, volcano, violin, spaghetti,
line+bands, grouped bar, ROC, waterfall, box+strip, KM survival,
histogram, text summary.
"""
import sys, os
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from nature_figure_utils import (
    retro_style, trim_axes, figsize_nature, save_for_review,
    find_best_legend_loc, smart_annotate, place_stat_text,
    scatter_outlined, auto_pad_figure, add_panel_labels,
    add_elbow_annotation, detect_overlaps, fix_overlaps,
    RUST, GRAY, BLUE, GOLD, SAGE, PLUM,
    INK, BG, BG_COLORS, ALPHA,
    CMAP_RUST, CMAP_DIVERGE,
)

np.random.seed(42)
FS = 7  # 7pt minimum

colors = retro_style()

# ── Layout ─────────────────────────────────────────────────────────
fig, axd = plt.subplot_mosaic(
    [["a", "b", "c"],
     ["d", "e", "f"],
     ["g", "g", "h"],
     ["i", "j", "k"],
     ["l", "m", "n"],
     ["o", "o", "o"]],
    figsize=(7.2, 11),  # bypass Nature height cap for 6-row stress test
    gridspec_kw=dict(height_ratios=[1, 1, 0.85, 1, 1, 0.5]),
)
fig.subplots_adjust(hspace=0.7, wspace=0.35)

# ══ a — barh ══════════════════════════════════════════════════════
ax = axd["a"]
genes = ["APOE", "CLU", "BIN1", "PICALM", "CR1", "ABCA7"]
vals = [4.2, 3.8, 3.5, 3.1, 2.9, 2.1]
yp = np.arange(len(genes))
bars = ax.barh(yp, vals, height=0.4, color=[RUST["400"], RUST["300"], RUST["200"],
               BLUE["300"], BLUE["200"], GRAY["200"]], edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp); ax.set_yticklabels(genes, fontsize=FS)
ax.set_xlabel("OR", fontsize=FS); ax.set_ylim(-0.5, 5.5)
ax.axvline(1.0, color=INK, ls="--", lw=0.5, alpha=0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)

# ══ b — density scatter ═══════════════════════════════════════════
ax = axd["b"]
x_sc = np.random.normal(5, 1.5, 400); y_sc = 0.7*x_sc + np.random.normal(0, 1.2, 400)
from scipy.stats import gaussian_kde, pearsonr
z = gaussian_kde(np.vstack([x_sc, y_sc]))(np.vstack([x_sc, y_sc]))
order = z.argsort()
scatter_outlined(ax, x_sc[order], y_sc[order], s=6, c=z[order], cmap=CMAP_RUST, alpha=0.8)
r_val, _ = pearsonr(x_sc, y_sc)
place_stat_text(ax, f"$r$ = {r_val:.2f}\n$p$ < 0.001", fontsize=FS)
ax.set_xlabel("Predicted", fontsize=FS); ax.set_ylabel("Observed", fontsize=FS)

# ══ c — heatmap ═══════════════════════════════════════════════════
ax = axd["c"]
hm = np.array([[1,.72,.45,.21],[.72,1,.58,.33],[.45,.58,1,.67],[.21,.33,.67,1]])
im = ax.imshow(hm, cmap=CMAP_RUST, aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(4)); ax.set_xticklabels(["Br","Bl","Li","Ki"], fontsize=FS, rotation=45, ha="right")
ax.set_yticks(range(4)); ax.set_yticklabels(["Brain","Blood","Liver","Kidney"], fontsize=FS)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
norm = Normalize(0, 1)
for i in range(4):
    for j in range(4):
        rgba = CMAP_RUST(norm(hm[i,j]))
        tc = "white" if 0.299*rgba[0]+0.587*rgba[1]+0.114*rgba[2] < 0.5 else INK
        ax.text(j, i, f"{hm[i,j]:.2f}", ha="center", va="center", fontsize=FS, color=tc)

# ══ d — forest plot ═══════════════════════════════════════════════
ax = axd["d"]
tissues = ["Hippocampus", "Cortex", "Cerebellum", "Amygdala", "Striatum"]
eff = [1.35, 1.22, 1.08, 0.95, 0.88]
ci_l = [1.12, 1.05, 0.92, 0.78, 0.71]; ci_h = [1.62, 1.42, 1.26, 1.15, 1.09]
yf = np.arange(len(tissues))
ax.errorbar(eff, yf, xerr=[[e-l for e,l in zip(eff,ci_l)],[h-e for e,h in zip(eff,ci_h)]],
            fmt="s", color="black", markersize=3, capsize=2, elinewidth=0.6, capthick=0.6, clip_on=False)
ax.axvline(1.0, color=GRAY["300"], ls="--", lw=0.5)
ax.set_yticks(yf); ax.set_yticklabels(tissues, fontsize=FS)
ax.set_xlabel("HR", fontsize=FS); ax.invert_yaxis()
ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)

# ══ e — volcano ═══════════════════════════════════════════════════
ax = axd["e"]
lfc = np.random.normal(0, 1.5, 300)
pv = 10**(-np.abs(lfc)*np.random.uniform(0.5, 3, 300))
nlp = -np.log10(pv)
su = (lfc > 1) & (pv < 0.05); sd = (lfc < -1) & (pv < 0.05); ns = ~(su|sd)
ax.scatter(lfc[ns], nlp[ns], s=3, alpha=ALPHA["ns_scatter"], c=GRAY["100"], clip_on=False)
ax.scatter(lfc[su], nlp[su], s=5, alpha=ALPHA["scatter"], c=RUST["400"], label="Up", clip_on=False)
ax.scatter(lfc[sd], nlp[sd], s=5, alpha=ALPHA["scatter"], c=BLUE["300"], label="Down", clip_on=False)
ax.axvline(1, color=INK, ls="--", lw=0.4, alpha=0.4); ax.axvline(-1, color=INK, ls="--", lw=0.4, alpha=0.4)
ax.axhline(-np.log10(0.05), color=INK, ls="--", lw=0.4, alpha=0.4)
x_abs = max(abs(lfc.min()), abs(lfc.max()))
ax.set_xlim(-x_abs*2.5, x_abs*2.5)
ax.set_xlabel("log$_2$ FC", fontsize=FS); ax.set_ylabel("$-$log$_{10}$ $p$", fontsize=FS)
# Annotate top 3 up
sc = nlp * np.abs(lfc)
up_idx = np.where(su)[0]; top3 = up_idx[np.argsort(sc[up_idx])[-3:]]
s3 = sorted(top3, key=lambda i: -nlp[i])
ax_h = fig.get_figheight() * ax.get_position().height
yr = nlp.max() - nlp.min()
th = (FS/72.0)*(yr/ax_h) if ax_h > 0 else 1
yg = max(yr*0.10, th*2.0)
rc = max(lfc[i] for i in s3) + 0.5
yt = max(nlp[i] for i in s3) + 0.3
for rk, idx in enumerate(s3):
    add_elbow_annotation(ax, ["KRAS","TP53","MYC"][rk], xy=(lfc[idx],nlp[idx]),
        xytext=(rc, yt - rk*yg), direction="right", color=INK, lw=0.4, fontsize=FS, stub=0.3)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), frameon=False, ncol=2,
          fontsize=FS, columnspacing=0.8, handletextpad=0.3)

# ══ f — violin + strip ════════════════════════════════════════════
ax = axd["f"]
vd = [np.random.normal(m, 0.8, 25) for m in [2.5, 3.2, 4.1, 3.8]]
pal = [GRAY["200"], RUST["200"], RUST["300"], RUST["400"]]
parts = ax.violinplot(vd, positions=range(1,5), showextrema=False, showmedians=False)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(pal[i]); pc.set_alpha(ALPHA["violin"]); pc.set_edgecolor("none")
for i, d in enumerate(vd):
    jit = np.random.uniform(-0.08, 0.08, len(d))
    ax.scatter(np.full_like(d, i+1)+jit, d, s=3, c="black", alpha=0.4, zorder=3, clip_on=False)
means = [np.mean(d) for d in vd]
ax.scatter(range(1,5), means, s=20, facecolors="white", edgecolors="black", linewidths=0.6, zorder=5, clip_on=False)
ax.set_xticks(range(1,5)); ax.set_xticklabels(["Ctrl","Low","Mid","High"], fontsize=FS)
ax.set_ylabel("Expr.", fontsize=FS)
av = np.concatenate(vd); ax.set_ylim(av.min()-0.3, av.max()+0.3)

# ══ g — spaghetti (spans 2) ══════════════════════════════════════
ax = axd["g"]
tp = np.array([0, 6, 12, 18, 24])
for grp, col, lbl in [("ctrl", GRAY["300"], "Control"), ("treat", RUST["300"], "Treatment")]:
    base = 50 if grp == "ctrl" else 55; sl = -0.3 if grp == "ctrl" else 0.8
    trajs = []
    for _ in range(20):
        t = base + np.random.normal(0,5) + (sl+np.random.normal(0,0.3))*tp + np.random.normal(0,2,5)
        trajs.append(t); ax.plot(tp, t, color=col, lw=0.5, alpha=0.25)
    ax.plot(tp, np.mean(trajs, axis=0), color=col, lw=1.8, label=lbl, zorder=10)
ax.set_xlabel("Time (mo)", fontsize=FS); ax.set_ylabel("Score", fontsize=FS)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), frameon=False,
          ncol=2, fontsize=FS, columnspacing=0.8, handletextpad=0.3)

# ══ h — line + confidence bands ══════════════════════════════════
ax = axd["h"]
t = np.linspace(0, 48, 50)
for i, (lbl, col) in enumerate(zip(["Placebo","Drug A","Drug B"],
                                    [GRAY["300"], RUST["300"], BLUE["300"]])):
    ym = 1.0 + i*0.3 + 0.02*t + 0.001*i*t; ye = 0.15 + 0.005*t
    ax.plot(t, ym, color=col, lw=1.0, label=lbl, zorder=2)
    ax.fill_between(t, ym-ye, ym+ye, alpha=ALPHA["band"], color=col)
ax.set_xlabel("Time (h)", fontsize=FS); ax.set_ylabel("Fold change", fontsize=FS)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), frameon=False,
          ncol=3, fontsize=FS, columnspacing=0.6, handletextpad=0.3)

# ══ i — grouped bar ══════════════════════════════════════════════
ax = axd["i"]
x_gb = np.arange(3); w = 0.25
gc = [GRAY["200"], RUST["300"], SAGE["300"]]
for ci, (cond, v, e) in enumerate(zip(["Ctrl","DrugA","DrugB"],
        [[2.1,3.4,1.8],[3.2,4.1,2.5],[2.8,3.9,3.1]],
        [[0.3,0.4,0.2],[0.4,0.5,0.3],[0.3,0.4,0.4]])):
    ax.bar(x_gb + ci*w, v, w, color=gc[ci], edgecolor="none", alpha=ALPHA["bar"], label=cond)
    ax.errorbar(x_gb + ci*w, v, yerr=e, fmt="none", ecolor="black", elinewidth=0.6, capsize=2)
ax.set_xticks(x_gb + w); ax.set_xticklabels(["IL-6","TNF","IL-1β"], fontsize=FS)
ax.set_ylabel("pg/mL", fontsize=FS)
loc_i, _ = find_best_legend_loc(ax, n_items=3)
ax.legend(loc=loc_i, frameon=True, facecolor="white", edgecolor="none",
          framealpha=0.9, fontsize=FS, ncol=1)

# ══ j — ROC curves ════════════════════════════════════════════════
ax = axd["j"]
for name, auc, col in [("Model A", 0.92, RUST["300"]),
                        ("Model B", 0.85, BLUE["300"]),
                        ("Model C", 0.78, GOLD["300"])]:
    fpr = np.sort(np.random.uniform(0, 1, 50)); fpr[0]=0; fpr[-1]=1
    tpr = np.clip(fpr**( (1-auc)*2 ) + np.random.normal(0, 0.03, 50), 0, 1)
    tpr = np.sort(tpr); tpr[0]=0; tpr[-1]=1
    ax.plot(fpr, tpr, color=col, lw=1.0, label=f"{name} ({auc:.2f})")
ax.plot([0,1],[0,1], "--", color=GRAY["300"], lw=0.5, alpha=0.5)
ax.set_xlabel("FPR", fontsize=FS); ax.set_ylabel("TPR", fontsize=FS)
ax.set_xlim(0,1); ax.set_ylim(0,1)
ax.legend(loc="lower right", frameon=True, facecolor="white",
          edgecolor="none", framealpha=0.9, fontsize=FS)

# ══ k — waterfall ═════════════════════════════════════════════════
ax = axd["k"]
eff_wf = np.sort(np.random.uniform(-60, 40, 30))[::-1]
wf_col = [RUST["300"] if e > 0 else BLUE["200"] for e in eff_wf]
ax.bar(range(len(eff_wf)), eff_wf, color=wf_col, edgecolor="none", width=0.8)
ax.axhline(0, color="black", lw=0.5)
ax.axhline(20, color=RUST["300"], ls="--", lw=0.4, alpha=0.5)
ax.axhline(-30, color=BLUE["300"], ls="--", lw=0.4, alpha=0.5)
ax.set_xlabel("Patient", fontsize=FS); ax.set_ylabel("Δ tumor (%)", fontsize=FS)
ax.set_xticks([])

# ══ l — box + strip ══════════════════════════════════════════════
ax = axd["l"]
bd = [np.random.normal(m, 1, 30) for m in [5, 6.5, 8, 7.2]]
bp = ax.boxplot(bd, patch_artist=True, widths=0.5,
    boxprops=dict(facecolor=RUST["300"], alpha=ALPHA["box"], linewidth=0.6),
    whiskerprops=dict(linewidth=0.6), capprops=dict(linewidth=0.6),
    medianprops=dict(color="black", linewidth=0.8),
    flierprops=dict(marker="o", markersize=1.5, alpha=0.4))
for i, d in enumerate(bd):
    jit = np.random.uniform(-0.1, 0.1, len(d))
    ax.scatter(np.full_like(d, i+1)+jit, d, s=3, alpha=0.4, c="black", zorder=3, clip_on=False)
ax.set_xticklabels(["G1","G2","G3","G4"], fontsize=FS)
ax.set_ylabel("Value", fontsize=FS)
alv = np.concatenate(bd); ax.set_ylim(alv.min()-0.5, alv.max()+0.5)

# ══ m — KM survival ══════════════════════════════════════════════
ax = axd["m"]
for name, lam, col in [("High risk", 0.04, RUST["400"]),
                        ("Low risk", 0.015, BLUE["300"])]:
    t_km = np.linspace(0, 60, 200)
    surv = np.exp(-lam * t_km) + np.random.normal(0, 0.01, 200)
    surv = np.clip(np.sort(surv)[::-1], 0, 1)
    ax.step(t_km, surv, where="post", color=col, lw=1.0, label=name)
    ax.fill_between(t_km, np.clip(surv-0.05, 0, 1), np.clip(surv+0.05, 0, 1),
                    alpha=ALPHA["band"], color=col, step="post")
ax.set_xlabel("Time (mo)", fontsize=FS); ax.set_ylabel("Survival", fontsize=FS)
ax.set_xlim(0, 60); ax.set_ylim(0, 1.05)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), frameon=False,
          ncol=2, fontsize=FS, columnspacing=0.8, handletextpad=0.3)

# ══ n — histogram / distribution ═════════════════════════════════
ax = axd["n"]
ax.hist(np.random.normal(0, 1, 500), bins=30, color=GRAY["200"], edgecolor="none", alpha=0.7, label="Ctrl")
ax.hist(np.random.normal(0.8, 1.2, 500), bins=30, color=RUST["300"], edgecolor="none", alpha=0.7, label="Treat")
ax.set_xlabel("Effect size", fontsize=FS); ax.set_ylabel("Count", fontsize=FS)
ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="none",
          framealpha=0.9, fontsize=FS)

# ══ o — text summary panel (spans full width) ════════════════════
ax = axd["o"]
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
summary = ("Key findings: Treatment group shows significant improvement in cognitive score "
           "(p < 0.001, Cohen's d = 0.82). APOE and CLU are top risk loci (OR > 3.5). "
           "Model A achieves AUC = 0.92 for early detection.")
ax.text(0.5, 0.5, summary, transform=ax.transAxes, fontsize=FS,
        ha="center", va="center", wrap=True,
        bbox=dict(boxstyle="round,pad=0.4", facecolor=BG_COLORS["cream"], edgecolor="none"))

# ══ Finalize ══════════════════════════════════════════════════════
exclude = {axd["a"], axd["c"], axd["d"], axd["o"]}
trim_axes(fig, exclude=exclude)
add_panel_labels(fig, axd)

# ── Detect BEFORE fix ─────────────────────────────────────────────
fig.canvas.draw()
before = detect_overlaps(fig, axd, padding=2.0)
print(f"\nBEFORE fix: {len(before)} overlaps")
for r in before:
    print(f"  [{r['severity']:>8}] {r['category']:>15} | {r['scope']:>11} | "
          f"{r['panel_a']}-{r['panel_b']} | {r['elem_a']} ↔ {r['elem_b']}")

# ── Auto-fix ──────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("RUNNING fix_overlaps()...")
print(f"{'='*70}")
remaining = fix_overlaps(fig, axd, max_iter=3, verbose=True)

# ── Report AFTER fix ──────────────────────────────────────────────
print(f"\nAFTER fix: {len(remaining)} overlaps remain")
for r in remaining:
    print(f"  [{r['severity']:>8}] {r['category']:>15} | {r['scope']:>11} | "
          f"{r['panel_a']}-{r['panel_b']} | {r['elem_a']} ↔ {r['elem_b']}")

# Save
out = os.path.dirname(os.path.abspath(__file__))
fig.savefig(os.path.join(out, "stress_test_15.png"), dpi=300, bbox_inches="tight")
save_for_review(fig, os.path.join(out, "stress_test_15_review.png"), dpi=72)
print("Saved stress_test_15.png")
