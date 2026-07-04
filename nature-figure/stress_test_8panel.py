"""
Stress test: 8 panels with long labels — barh, heatmap, forest, grouped barh, text.

Tests: long pathway/gene/drug names, multiline labels, spanning panels,
cross-panel collisions, grouped bars, correlation heatmap, text summary.
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

# Long biological labels for stress testing
PATHWAYS_A = [
    "Oxidative phosphorylation and mitochondrial electron transport chain assembly pathway",
    "Synaptic vesicle exocytosis and clathrin-mediated endocytosis cycle at presynaptic zone",
    "Classical complement activation cascade from C1q binding through MAC pore formation",
    "Extracellular matrix metalloproteinase-mediated collagen remodeling during wound healing",
    "Selective macroautophagy and PINK1/Parkin-mediated mitophagy of damaged organelles",
    "Ubiquitin-proteasome-mediated targeted protein degradation via K48 polyubiquitin chains",
    "Toll-like receptor 4 signaling through MyD88-dependent inflammatory cytokine production",
    "Wnt/beta-catenin canonical signaling pathway regulating hippocampal neurogenesis",
    "Blood-brain barrier claudin/occludin tight junction assembly and inflammatory disruption",
    "Retrograde endosomal sorting nexin-dependent recycling of transmembrane receptors",
]

PATHWAYS_B = [
    "Amyloid precursor protein processing via alpha/beta/gamma-secretase cleavage pathways",
    "Tau hyperphosphorylation by GSK-3beta/CDK5 and paired helical filament assembly",
    "Microglial TREM2-mediated phagocytosis of apoptotic neurons and synaptic debris",
    "Astrocyte aquaporin-4 polarization and glymphatic waste clearance during NREM sleep",
    "Oligodendrocyte precursor cell differentiation and remyelination in white matter tracts",
    "Dopamine D2 receptor signaling in striatal medium spiny neurons of indirect pathway",
    "GABA-A receptor trafficking and inhibitory postsynaptic current modulation by neurosteroids",
    "NMDA receptor GluN2B subunit-dependent long-term potentiation at Schaffer collateral synapses",
    "Cholinergic basal forebrain projection neuron degeneration in Alzheimer disease pathology",
    "Serotonin 5-HT2A receptor-mediated cortical excitation and psychedelic neuroplasticity",
]

DRUGS_FOREST = [
    "Donepezil hydrochloride (Aricept) — acetylcholinesterase inhibitor, 10mg oral daily",
    "Memantine extended-release (Namenda XR) — NMDA receptor antagonist, 28mg capsule",
    "Lecanemab-irmb (Leqembi) — anti-amyloid-beta protofibril antibody, IV biweekly",
    "Aducanumab-avwa (Aduhelm) — amyloid-beta plaque-directed antibody, IV monthly",
    "Donanemab-azbt (Kisunla) — anti-pyroglutamate amyloid-beta antibody, IV monthly",
    "Brexpiprazole (Rexulti) — serotonin-dopamine modulator for AD agitation",
    "Galantamine ER (Razadyne ER) — dual acetylcholinesterase/nicotinic modulator",
    "Rivastigmine transdermal (Exelon Patch) — pseudo-irreversible ChE inhibitor",
]

CELL_TYPES = [
    "Excitatory glutamatergic pyramidal neurons (layers II/III and V)",
    "Inhibitory GABAergic parvalbumin-positive fast-spiking interneurons",
    "Mature myelinating oligodendrocytes (MOL1-MOL6 subtypes)",
    "Homeostatic microglia vs disease-associated microglia (DAM)",
    "Protoplasmic astrocytes (gray matter) vs fibrous (white matter)",
    "Oligodendrocyte precursor cells / NG2-positive polydendrocytes",
]

METABS = [
    "N-acetylaspartate (NAA) — neuronal integrity marker in proton MRS",
    "Glutamate/glutamine complex (Glx) — excitatory neurotransmitter shuttle",
    "Myo-inositol (mI) — astrocyte proliferation and osmolyte marker",
    "Total choline (tCho = GPC + PCho) — membrane turnover indicator",
    "Total creatine (tCr = Cr + PCr) — cellular energy metabolism",
    "Lactate at 1.33 ppm (Lac) — anaerobic glycolysis marker",
    "NAAG — peptide neurotransmitter and NAA metabolite at 2.04 ppm",
    "GABA — primary inhibitory neurotransmitter measured by edited MRS",
]

# ── Layout: 3 rows, some spanning ────────────────────────────────
fig, axd = plt.subplot_mosaic(
    [["a", "b", "c"],
     ["d", "d", "e"],
     ["f", "g", "h"]],
    figsize=(7.2, 9),
    gridspec_kw=dict(height_ratios=[1.0, 0.8, 0.7]),
)
fig.subplots_adjust(hspace=0.45, wspace=0.5)

# ══ a — barh with 10 long pathway names ═════════════════════════
ax = axd["a"]
vals_a = np.sort(np.random.uniform(1.5, 8, len(PATHWAYS_A)))[::-1]
yp = np.arange(len(PATHWAYS_A))
bars = ax.barh(yp, vals_a, height=0.4,
               color=[RUST["300"]]*(len(PATHWAYS_A)//2) + [BLUE["300"]]*(len(PATHWAYS_A) - len(PATHWAYS_A)//2),
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(PATHWAYS_A, fontsize=FS)
ax.set_xlabel("$-$log$_{10}$ FDR", fontsize=FS)
ax.set_ylim(-0.5, len(PATHWAYS_A) - 0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_a):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ b — barh with 10 different long pathway names ════════════════
ax = axd["b"]
vals_b = np.sort(np.random.uniform(1, 5, len(PATHWAYS_B)))[::-1]
yp = np.arange(len(PATHWAYS_B))
b_colors = [RUST["400"], RUST["300"], RUST["200"], BLUE["300"],
            BLUE["200"], GRAY["300"], GRAY["200"], GOLD["300"],
            SAGE["300"], PLUM["300"]]
bars = ax.barh(yp, vals_b, height=0.4,
               color=b_colors[:len(PATHWAYS_B)],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(PATHWAYS_B, fontsize=FS)
ax.set_xlabel("OR", fontsize=FS)
ax.set_ylim(-0.5, len(PATHWAYS_B) - 0.5)
ax.axvline(1.0, color=INK, ls="--", lw=0.5, alpha=0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_b):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ c — heatmap 6×8 with multiline labels ═══════════════════════
ax = axd["c"]
hm = np.random.uniform(-2, 2, (6, 8))
row_labels = ["Oxidative\nphosphorylation", "Synaptic\nvesicle cycle",
              "Complement\nactivation", "ECM\norganization",
              "Autophagy\nregulation", "Protein\nubiquitination"]
col_labels = ["Prefrontal\ncortex", "Hippocampus\nCA1", "Entorhinal\ncortex",
              "Temporal\ncortex", "Cerebellum", "Caudate\nnucleus",
              "Substantia\nnigra", "Thalamus"]
im = ax.imshow(hm, cmap=CMAP_DIVERGE, aspect="auto", vmin=-2, vmax=2)
ax.set_xticks(range(8))
ax.set_xticklabels(col_labels, fontsize=5.5, rotation=45, ha="right")
ax.set_yticks(range(6))
ax.set_yticklabels(row_labels, fontsize=5.5)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
norm = Normalize(-2, 2)
for i in range(6):
    for j in range(8):
        rgba = CMAP_DIVERGE(norm(hm[i,j]))
        br = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
        ax.text(j, i, f"{hm[i,j]:.1f}", ha="center", va="center",
                fontsize=5.5, color="white" if br < 0.5 else INK)

# ══ d — forest plot with 8 drug names (spanning 2 cols) ══════════
ax = axd["d"]
eff = np.random.uniform(0.5, 2.0, len(DRUGS_FOREST))
ci_lo = eff - np.random.uniform(0.1, 0.4, len(DRUGS_FOREST))
ci_hi = eff + np.random.uniform(0.1, 0.4, len(DRUGS_FOREST))
yf = np.arange(len(DRUGS_FOREST))
ax.errorbar(eff, yf, xerr=[eff-ci_lo, ci_hi-eff], fmt="s", color="black",
            markersize=3, capsize=2, elinewidth=0.6, capthick=0.6, clip_on=False)
ax.axvline(1.0, color=GRAY["300"], ls="--", lw=0.5)
ax.set_yticks(yf)
ax.set_yticklabels(DRUGS_FOREST, fontsize=FS)
ax.set_xlabel("Odds ratio (95% CI)", fontsize=FS)
ax.invert_yaxis()
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ e — small correlation heatmap 5×5 ════════════════════════════
ax = axd["e"]
corr = np.corrcoef(np.random.randn(5, 50))
labels_e = ["APOE ε4", "Tau PET", "Aβ PET", "MMSE", "CDR-SB"]
im2 = ax.imshow(corr, cmap=CMAP_DIVERGE, aspect="auto", vmin=-1, vmax=1)
ax.set_xticks(range(5))
ax.set_xticklabels(labels_e, fontsize=FS, rotation=45, ha="right")
ax.set_yticks(range(5))
ax.set_yticklabels(labels_e, fontsize=FS)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
norm_corr = Normalize(-1, 1)
for i in range(5):
    for j in range(5):
        rgba = CMAP_DIVERGE(norm_corr(corr[i,j]))
        br = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
        ax.text(j, i, f"{corr[i,j]:.2f}", ha="center", va="center",
                fontsize=FS, color="white" if br < 0.5 else INK)

# ══ f — grouped barh with 6 cell type labels ════════════════════
ax = axd["f"]
yp = np.arange(len(CELL_TYPES))
w = 0.2
for ci, (cond, col) in enumerate(zip(["Young", "Old"],
                                       [BLUE["300"], RUST["300"]])):
    vals = np.random.uniform(0.5, 4, len(CELL_TYPES))
    ax.barh(yp + ci*w, vals, height=w, color=col,
            edgecolor="none", alpha=ALPHA["bar"], label=cond)
ax.set_yticks(yp + w/2)
ax.set_yticklabels(CELL_TYPES, fontsize=FS)
ax.set_xlabel("Fold enrichment", fontsize=FS)
ax.set_ylim(-0.5, len(CELL_TYPES))
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.legend(fontsize=FS, frameon=True, facecolor="white",
          edgecolor="none", framealpha=0.9)

# ══ g — barh with 8 metabolite labels (spanning 2 cols) ═════════
ax = axd["g"]
vals_g = np.sort(np.random.uniform(0.5, 3, len(METABS)))[::-1]
yp = np.arange(len(METABS))
bars = ax.barh(yp, vals_g, height=0.4,
               color=[GOLD[s] for s in ["100","200","300","400","500","600"]],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(METABS, fontsize=FS)
ax.set_xlabel("Concentration (mM)", fontsize=FS)
ax.set_ylim(-0.5, len(METABS) - 0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_g):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ h — text summary ════════════════════════════════════════════
ax = axd["h"]
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
summary = ("Key findings: Oxidative phosphorylation and synaptic vesicle cycle "
           "pathways are the most enriched (FDR < 0.001). APOE and CLU show "
           "strongest genetic associations. Lecanemab and donanemab show "
           "significant amyloid reduction with odds ratios below 1.0.")
ax.text(0.5, 0.5, summary, transform=ax.transAxes, fontsize=FS,
        ha="center", va="center", wrap=True,
        bbox=dict(boxstyle="round,pad=0.4", facecolor=BG_COLORS["cream"], edgecolor="none"))

# ══ Finalize ═════════════════════════════════════════════════════
exclude = {axd[k] for k in ["a", "b", "c", "d", "e", "f", "g", "h"]}
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
fig.savefig(os.path.join(out, "stress_test_8panel.png"), dpi=300, bbox_inches="tight")
save_for_review(fig, os.path.join(out, "stress_test_8panel_review.png"), dpi=72)
print("Saved stress_test_8panel.png")
