"""
Stress test: 4 panels with long labels — barh, heatmap, forest, scatter.

Tests: long pathway/drug/gene names, multiline heatmap labels, labeled
scatter points, cross-panel label collisions.
"""
import sys, os
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from nature_figure_utils import (
    retro_style, trim_axes, save_for_review,
    add_panel_labels, detect_overlaps, fix_overlaps,
    contain_panels, align_left_edges,
    RUST, GRAY, BLUE, GOLD, SAGE, PLUM,
    INK, BG, BG_COLORS, ALPHA,
    CMAP_RUST, CMAP_DIVERGE,
)

np.random.seed(42)
FS = 7

colors = retro_style()

# Long biological labels for stress testing (60-80 chars each)
PATHWAYS = [
    "Oxidative phosphorylation and mitochondrial electron transport chain assembly",
    "Synaptic vesicle exocytosis and clathrin-mediated endocytosis cycle regulation",
    "Classical complement activation cascade from C1q binding to MAC formation",
    "Extracellular matrix metalloproteinase-mediated collagen remodeling pathway",
    "Selective macroautophagy and PINK1/Parkin-mediated mitophagy signaling",
    "Ubiquitin-proteasome-mediated targeted protein degradation via K48 chains",
    "Toll-like receptor 4 signaling through MyD88-dependent cytokine production",
    "Wnt/beta-catenin canonical signaling regulating hippocampal neurogenesis",
]

DRUGS = [
    "Donepezil hydrochloride (Aricept) — acetylcholinesterase inhibitor, 10mg daily",
    "Memantine extended-release (Namenda XR) — NMDA receptor antagonist, 28mg",
    "Lecanemab-irmb (Leqembi) — anti-amyloid-beta protofibril antibody, IV biweekly",
    "Aducanumab-avwa (Aduhelm) — amyloid-beta plaque-directed antibody, IV monthly",
    "Donanemab-azbt (Kisunla) — anti-pyroglutamate amyloid-beta antibody, IV monthly",
    "Brexpiprazole (Rexulti) — serotonin-dopamine activity modulator for AD agitation",
    "Galantamine hydrobromide ER (Razadyne ER) — dual cholinesterase/nicotinic modulator",
    "Rivastigmine transdermal (Exelon Patch) — pseudo-irreversible ChE inhibitor",
]

GENES_CHR = [
    "APOE epsilon 4 allele — late-onset Alzheimer risk (chr19q13.32)",
    "CLU / Apolipoprotein J — amyloid-beta clearance (chr8p21.1)",
    "BIN1 / Amphiphysin II — clathrin-mediated endocytosis (chr2q14.3)",
    "PICALM — endocytic adaptor at presynaptic terminals (chr11q14.2)",
    "CR1 complement receptor 1 — innate immune regulation (chr1q32.2)",
    "ABCA7 — lipid transporter for phagocytic clearance (chr19p13.3)",
    "SORL1 — APP trafficking receptor with LDLR repeats (chr11q24.1)",
    "TREM2 — microglial innate immune lipid sensor (chr6p21.1)",
]

# ── Layout: 2 rows × 2 columns ──────────────────────────────────
fig, axd = plt.subplot_mosaic(
    [["a", "b"],
     ["c", "d"]],
    figsize=(7.2, 6),
    gridspec_kw=dict(height_ratios=[1, 0.9]),
)
fig.subplots_adjust(hspace=0.45, wspace=0.5)

# ══ a — barh with long pathway names ════════════════════════════
ax = axd["a"]
vals_a = np.sort(np.random.uniform(1.5, 8, len(PATHWAYS)))[::-1]
yp = np.arange(len(PATHWAYS))
bars = ax.barh(yp, vals_a, height=0.4,
               color=[RUST["300"]]*(len(PATHWAYS)//2) + [BLUE["300"]]*(len(PATHWAYS) - len(PATHWAYS)//2),
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(PATHWAYS, fontsize=FS)
ax.set_xlabel("$-$log$_{10}$ FDR", fontsize=FS)
ax.set_ylim(-0.5, len(PATHWAYS) - 0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_a):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ b — heatmap 6×6 with multiline row/col labels ═══════════════
ax = axd["b"]
hm = np.random.uniform(-2, 2, (6, 6))
row_labels = ["Oxidative\nphosphorylation", "Synaptic\nvesicle cycle",
              "Complement\nactivation", "ECM\norganization",
              "Autophagy\nregulation", "Protein\nubiquitination"]
col_labels = ["Prefrontal\ncortex", "Hippocampus\nCA1", "Entorhinal\ncortex",
              "Temporal\ncortex", "Cerebellum", "Caudate\nnucleus"]
im = ax.imshow(hm, cmap=CMAP_DIVERGE, aspect="auto", vmin=-2, vmax=2)
ax.set_xticks(range(6))
ax.set_xticklabels(col_labels, fontsize=5.5, rotation=45, ha="right")
ax.set_yticks(range(6))
ax.set_yticklabels(row_labels, fontsize=5.5)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
norm = Normalize(-2, 2)
for i in range(6):
    for j in range(6):
        rgba = CMAP_DIVERGE(norm(hm[i,j]))
        br = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
        ax.text(j, i, f"{hm[i,j]:.1f}", ha="center", va="center",
                fontsize=5.5, color="white" if br < 0.5 else INK)

# ══ c — forest plot with long drug names ═════════════════════════
ax = axd["c"]
eff = np.random.uniform(0.5, 2.0, len(DRUGS))
ci_lo = eff - np.random.uniform(0.1, 0.4, len(DRUGS))
ci_hi = eff + np.random.uniform(0.1, 0.4, len(DRUGS))
yf = np.arange(len(DRUGS))
ax.errorbar(eff, yf, xerr=[eff-ci_lo, ci_hi-eff], fmt="s", color="black",
            markersize=3, capsize=2, elinewidth=0.6, capthick=0.6, clip_on=False)
ax.axvline(1.0, color=GRAY["300"], ls="--", lw=0.5)
ax.set_yticks(yf)
ax.set_yticklabels(DRUGS, fontsize=FS)
ax.set_xlabel("Odds ratio (95% CI)", fontsize=FS)
ax.invert_yaxis()
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ d — scatter with labeled gene/chromosomal location points ════
ax = axd["d"]
x_scatter = np.random.uniform(0, 10, len(GENES_CHR))
y_scatter = np.random.uniform(0, 8, len(GENES_CHR))
sizes = np.random.uniform(20, 100, len(GENES_CHR))
scatter_colors = [RUST["300"], RUST["400"], BLUE["300"], BLUE["400"],
                  GOLD["300"], SAGE["300"], PLUM["300"], GRAY["300"]]
ax.scatter(x_scatter, y_scatter, s=sizes, c=scatter_colors[:len(GENES_CHR)],
           alpha=ALPHA["bar"], edgecolors="none")
for xi, yi, label in zip(x_scatter, y_scatter, GENES_CHR):
    ax.annotate(label, (xi, yi), fontsize=5.5, color=INK,
                textcoords="offset points", xytext=(4, 2),
                ha="left", va="bottom")
ax.set_xlabel("$-$log$_{10}$ $p$-value", fontsize=FS)
ax.set_ylabel("Effect size (beta)", fontsize=FS)

# ══ Finalize ═════════════════════════════════════════════════════
exclude = {axd[k] for k in ["a", "b", "c", "d"]}
trim_axes(fig, exclude=exclude)
contain_panels(fig, axd)

# ── Detect + Fix ─────────────────────────────────────────────────
fig.canvas.draw()
before = detect_overlaps(fig, axd, padding=2.0)
print(f"\nBEFORE fix: {len(before)} overlaps")
for r in before[:15]:
    print(f"  [{r['severity']:>8}] {r['category']:>15} | {r['scope']:>11} | "
          f"{r['panel_a']}-{r['panel_b']} | {r['elem_a'][:30]} ↔ {r['elem_b'][:30]}")
if len(before) > 15:
    print(f"  ... and {len(before)-15} more")

print(f"\n{'='*60}")
remaining = fix_overlaps(fig, axd, max_iter=3, verbose=True)
align_left_edges(fig, axd)
add_panel_labels(fig, axd)
print(f"{'='*60}")

severe = [r for r in remaining if r["severity"] == "severe"]
moderate = [r for r in remaining if r["severity"] == "moderate"]
minor = [r for r in remaining if r["severity"] == "minor"]
print(f"\nAFTER fix: {len(severe)} severe, {len(moderate)} moderate, {len(minor)} minor")

out = os.path.dirname(os.path.abspath(__file__))
fig.savefig(os.path.join(out, "stress_test_4panel.png"), dpi=300, bbox_inches="tight")
save_for_review(fig, os.path.join(out, "stress_test_4panel_review.png"), dpi=72)
print("Saved stress_test_4panel.png")
