"""
Stress test: 13 panels with long labels — barh, forest, heatmap.

Tests: long gene/pathway names, tick label overflow, cross-panel
label collisions, legend placement with wide y-tick labels.
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
    find_best_legend_loc, place_stat_text, add_panel_labels,
    detect_overlaps, fix_overlaps, contain_panels, align_left_edges,
    RUST, GRAY, BLUE, GOLD, SAGE, PLUM,
    INK, BG, BG_COLORS, ALPHA,
    CMAP_RUST, CMAP_DIVERGE,
)

np.random.seed(42)
FS = 7

colors = retro_style()

# Long biological labels for stress testing
PATHWAYS = [
    "Oxidative phosphorylation and mitochondrial electron transport chain complex I-IV assembly and supercomplex formation",
    "Mitochondrial inner membrane cristae organization, biogenesis, and MICOS complex-dependent remodeling pathway",
    "Synaptic vesicle exocytosis, clathrin-mediated endocytosis cycle, and SNARE complex disassembly at presynaptic terminals",
    "Antigen processing and presentation of exogenous peptide antigen via MHC class II to CD4-positive T lymphocytes",
    "Classical complement activation cascade from C1q binding through membrane attack complex (C5b-9) pore formation",
    "Extracellular matrix metalloproteinase-mediated collagen and glycoprotein remodeling during wound healing response",
    "Selective macroautophagy, PINK1/Parkin-mediated mitophagy, and lysosomal degradation of damaged organelles",
    "Ubiquitin-proteasome-mediated targeted protein degradation via K48-linked polyubiquitin chain recognition pathway",
    "Retrograde endosomal sorting nexin-dependent recycling of transmembrane receptors to the trans-Golgi network",
    "Blood-brain barrier endothelial claudin/occludin tight junction complex assembly, maintenance, and inflammatory disruption",
    "Toll-like receptor 4 signaling through MyD88-dependent and TRIF-dependent inflammatory cytokine production pathways",
    "Wnt/beta-catenin canonical signaling pathway regulating adult hippocampal neurogenesis and synaptic plasticity",
]
GENES_LONG = [
    "Apolipoprotein E epsilon 4 allele — primary genetic risk factor for late-onset Alzheimer disease (APOE ε4, chr19q13.32)",
    "Clusterin / Apolipoprotein J — extracellular chaperone involved in amyloid-beta clearance (CLU / APOJ, chr8p21.1)",
    "Bridging integrator 1 / Amphiphysin II — BAR domain protein regulating clathrin-mediated endocytosis (BIN1, chr2q14.3)",
    "Phosphatidylinositol-binding clathrin assembly protein — endocytic adaptor at presynaptic terminals (PICALM, chr11q14.2)",
    "Complement component (3b/4b) receptor 1, Knops blood group — innate immune complement regulation (CR1, chr1q32.2)",
    "ATP-binding cassette sub-family A member 7 — lipid transporter implicated in phagocytic clearance (ABCA7, chr19p13.3)",
    "Sortilin-related receptor with LDLR class A repeats containing — APP trafficking receptor (SORL1, chr11q24.1)",
    "Triggering receptor expressed on myeloid cells 2 — microglial innate immune receptor for lipid sensing (TREM2, chr6p21.1)",
    "Membrane-spanning 4-domains subfamily A member 6A — transmembrane protein in immune cell signaling (MS4A6A, chr11q12.2)",
    "CD2-associated protein / Cas ligand with multiple SH3 domains — actin cytoskeleton regulator (CD2AP, chr6p12.3)",
    "Inositol polyphosphate-5-phosphatase D / SH2-containing inositol 5'-phosphatase 1 (INPP5D / SHIP1, chr2q37.1)",
    "Myocyte enhancer factor 2C — MADS-box transcription factor essential for neuronal survival (MEF2C, chr5q14.3)",
]
TISSUES = [
    "Dorsolateral prefrontal cortex, Brodmann area 9/46 — executive function and working memory circuits",
    "Hippocampus cornu ammonis 1 (CA1) pyramidal cell layer — episodic memory encoding and consolidation",
    "Entorhinal cortex layer II stellate cell islands — gateway between neocortex and hippocampal formation",
    "Superior temporal gyrus, Brodmann area 22 (Wernicke's area) — auditory association and language comprehension",
    "Cerebellar Purkinje cell layer — motor coordination, timing, and cerebellar cognitive affective syndrome",
    "Caudate nucleus head, body, and tail — basal ganglia motor loop and procedural learning circuitry",
    "Substantia nigra pars compacta dopaminergic A9 neurons — nigrostriatal pathway degeneration in Parkinson disease",
    "Anterior cingulate cortex, Brodmann area 24/32 — error monitoring, conflict detection, and affective processing",
    "Posterior cingulate cortex, Brodmann area 23/31 — default mode network hub and autobiographical memory retrieval",
    "Primary motor cortex, Brodmann area 4 (precentral gyrus) — upper motor neuron degeneration in ALS/MND",
]

# ── Layout: 5 rows × 3 columns, some spanning ─────────────────────
fig, axd = plt.subplot_mosaic(
    [["a", "b", "c"],
     ["d", "d", "e"],
     ["f", "g", "g"],
     ["h", "i", "j"],
     ["k", "k", "l"],
     ["m", "m", "m"]],
    figsize=(7.2, 13),
    gridspec_kw=dict(height_ratios=[1.2, 0.9, 0.7, 0.9, 1.0, 0.3]),
)
fig.subplots_adjust(hspace=0.45, wspace=0.5)

# ══ a — barh with long pathway names ═════════════════════════════
ax = axd["a"]
vals_a = np.sort(np.random.uniform(1.5, 8, len(PATHWAYS)))[::-1]
# Ensure barh color arrays match data length
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

# ══ b — barh with long gene names ════════════════════════════════
ax = axd["b"]
vals_b = np.sort(np.random.uniform(1, 5, len(GENES_LONG)))[::-1]
yp = np.arange(len(GENES_LONG))
b_colors = [RUST["400"], RUST["300"], RUST["200"], BLUE["300"],
            BLUE["200"], GRAY["300"], GRAY["200"], GOLD["300"],
            SAGE["300"], PLUM["300"], RUST["100"], BLUE["100"]]
bars = ax.barh(yp, vals_b, height=0.4,
               color=b_colors[:len(GENES_LONG)],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(GENES_LONG, fontsize=FS)
ax.set_xlabel("OR", fontsize=FS)
ax.set_ylim(-0.5, len(GENES_LONG) - 0.5)
ax.axvline(1.0, color=INK, ls="--", lw=0.5, alpha=0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_b):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ c — heatmap with long row/col labels ═════════════════════════
ax = axd["c"]
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

# ══ d — forest plot with long tissue names (spanning) ═════════════
ax = axd["d"]
eff = np.random.uniform(0.7, 1.8, len(TISSUES))
ci_lo = eff - np.random.uniform(0.1, 0.3, len(TISSUES))
ci_hi = eff + np.random.uniform(0.1, 0.3, len(TISSUES))
yf = np.arange(len(TISSUES))
ax.errorbar(eff, yf, xerr=[eff-ci_lo, ci_hi-eff], fmt="s", color="black",
            markersize=3, capsize=2, elinewidth=0.6, capthick=0.6, clip_on=False)
ax.axvline(1.0, color=GRAY["300"], ls="--", lw=0.5)
ax.set_yticks(yf)
ax.set_yticklabels(TISSUES, fontsize=FS)
ax.set_xlabel("Hazard ratio (95% CI)", fontsize=FS)
ax.invert_yaxis()
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ e — barh enrichment (different pathways) ═════════════════════
ax = axd["e"]
paths2 = ["Ribosome biogenesis", "mRNA splicing",
          "Chromatin remodeling", "DNA damage response",
          "Fatty acid metabolism", "Cholesterol biosynthesis"]
vals_e = np.sort(np.random.uniform(2, 10, len(paths2)))[::-1]
yp = np.arange(len(paths2))
bars = ax.barh(yp, vals_e, height=0.4,
               color=[SAGE[s] for s in ["100","200","300","400","500","600"]],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(paths2, fontsize=FS)
ax.set_xlabel("NES", fontsize=FS)
ax.set_ylim(-0.5, len(paths2) - 0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_e):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ f — grouped barh with cell type labels ═══════════════════════
ax = axd["f"]
cell_types = ["Excitatory neurons", "Inhibitory neurons",
              "Oligodendrocytes", "Microglia", "Astrocytes"]
yp = np.arange(len(cell_types))
w = 0.2
for ci, (cond, col) in enumerate(zip(["Young", "Old"],
                                       [BLUE["300"], RUST["300"]])):
    vals = np.random.uniform(0.5, 4, len(cell_types))
    ax.barh(yp + ci*w, vals, height=w, color=col,
            edgecolor="none", alpha=ALPHA["bar"], label=cond)
ax.set_yticks(yp + w/2)
ax.set_yticklabels(cell_types, fontsize=FS)
ax.set_xlabel("Fold enrichment", fontsize=FS)
ax.set_ylim(-0.5, len(cell_types))
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.legend(fontsize=FS, frameon=True, facecolor="white",
          edgecolor="none", framealpha=0.9)

# ══ g — large heatmap spanning 2 cols ════════════════════════════
ax = axd["g"]
hm2 = np.random.uniform(-3, 3, (8, 10))
gene_names = ["APP", "PSEN1", "PSEN2", "MAPT", "GRN", "C9orf72", "SNCA", "LRRK2"]
sample_names = [f"Sample {i+1}" for i in range(10)]
im2 = ax.imshow(hm2, cmap=CMAP_DIVERGE, aspect="auto", vmin=-3, vmax=3)
ax.set_xticks(range(10))
ax.set_xticklabels(sample_names, fontsize=5.5, rotation=45, ha="right")
ax.set_yticks(range(8))
ax.set_yticklabels(gene_names, fontsize=FS)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
fig.colorbar(im2, ax=ax, shrink=0.6, pad=0.02, label="Z-score")

# ══ h — forest with long drug names ══════════════════════════════
ax = axd["h"]
drugs = ["Donepezil hydrochloride (Aricept) — acetylcholinesterase inhibitor, 10mg once daily oral tablet",
         "Memantine hydrochloride extended-release (Namenda XR) — NMDA receptor antagonist, 28mg once daily capsule",
         "Lecanemab-irmb (Leqembi) — humanized IgG1 anti-amyloid-beta protofibril monoclonal antibody, IV biweekly",
         "Aducanumab-avwa (Aduhelm) — human IgG1 amyloid-beta plaque-directed monoclonal antibody, IV monthly",
         "Donanemab-azbt (Kisunla) — humanized IgG1 anti-N-terminal pyroglutamate amyloid-beta antibody, IV monthly",
         "Brexpiprazole (Rexulti) — serotonin-dopamine activity modulator, D2 partial agonist for agitation in AD",
         "Galantamine hydrobromide extended-release (Razadyne ER) — dual acetylcholinesterase/nicotinic modulator",
         "Rivastigmine transdermal system (Exelon Patch) — pseudo-irreversible cholinesterase inhibitor, 13.3mg/24hr"]
eff_d = np.random.uniform(0.5, 2.0, len(drugs))
ci_l_d = eff_d - np.random.uniform(0.1, 0.4, len(drugs))
ci_h_d = eff_d + np.random.uniform(0.1, 0.4, len(drugs))
yf = np.arange(len(drugs))
ax.errorbar(eff_d, yf, xerr=[eff_d-ci_l_d, ci_h_d-eff_d], fmt="s",
            color="black", markersize=3, capsize=2, elinewidth=0.6,
            capthick=0.6, clip_on=False)
ax.axvline(1.0, color=GRAY["300"], ls="--", lw=0.5)
ax.set_yticks(yf)
ax.set_yticklabels(drugs, fontsize=FS)
ax.set_xlabel("Odds ratio", fontsize=FS)
ax.invert_yaxis()
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ i — barh with p-value annotations ════════════════════════════
ax = axd["i"]
regions = ["Brodmann area 9", "Brodmann area 21",
           "Brodmann area 36", "Brodmann area 44",
           "Brodmann area 46"]
vals_i = np.sort(np.random.uniform(1.5, 6, len(regions)))[::-1]
pvals = 10**(-vals_i)
yp = np.arange(len(regions))
bars = ax.barh(yp, vals_i, height=0.4, color=RUST["300"],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(regions, fontsize=FS)
ax.set_xlabel("$-$log$_{10}$ $p$", fontsize=FS)
ax.set_ylim(-0.5, len(regions) - 0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v, p in zip(bars, vals_i, pvals):
    stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f} ({stars})", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ j — small heatmap correlation ════════════════════════════════
ax = axd["j"]
corr = np.corrcoef(np.random.randn(5, 50))
labels_j = ["APOE ε4", "Tau PET", "Aβ PET", "MMSE", "CDR-SB"]
im3 = ax.imshow(corr, cmap=CMAP_DIVERGE, aspect="auto", vmin=-1, vmax=1)
ax.set_xticks(range(5))
ax.set_xticklabels(labels_j, fontsize=FS, rotation=45, ha="right")
ax.set_yticks(range(5))
ax.set_yticklabels(labels_j, fontsize=FS)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
norm = Normalize(-1, 1)
for i in range(5):
    for j in range(5):
        rgba = CMAP_DIVERGE(norm(corr[i,j]))
        br = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
        ax.text(j, i, f"{corr[i,j]:.2f}", ha="center", va="center",
                fontsize=FS, color="white" if br < 0.5 else INK)

# ══ k — wide barh with very long labels (spanning) ═══════════════
ax = axd["k"]
long_paths = [
    "Regulation of mitochondrial outer membrane permeabilization involved in intrinsic apoptotic signaling pathway activation",
    "Positive regulation of alpha-amino-3-hydroxy-5-methyl-4-isoxazolepropionic acid (AMPA) receptor synaptic transmission",
    "Negative regulation of neuron apoptotic process in response to reactive oxygen species-induced oxidative stress damage",
    "Anterograde dendritic and axonal transport of mitochondria along microtubule cytoskeleton via kinesin motor proteins",
    "Microglial cell activation and polarization involved in complement-mediated neuroinflammatory immune response cascade",
    "Blood-brain barrier endothelial claudin-5/occludin/ZO-1 tight junction complex assembly, maintenance, and disruption",
    "Amyloid-beta (1-42) peptide clearance by low-density lipoprotein receptor-related protein 1 transcytosis across BBB",
    "Tau protein GSK-3beta/CDK5-mediated hyperphosphorylation, paired helical filament assembly, and tangle formation",
    "Receptor-interacting serine/threonine-protein kinase 1 (RIPK1)-dependent programmed necroptosis signaling pathway",
    "Calcium/calmodulin-dependent protein kinase II (CaMKII) autophosphorylation and long-term potentiation induction",
]
vals_k = np.sort(np.random.uniform(2, 12, len(long_paths)))[::-1]
# Adjust height_ratios for more items

yp = np.arange(len(long_paths))
bars = ax.barh(yp, vals_k, height=0.4,
               color=[RUST["300"] if v > 6 else GRAY["200"] for v in vals_k],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(long_paths, fontsize=FS)
ax.set_xlabel("Enrichment score", fontsize=FS)
ax.set_ylim(-0.5, len(long_paths) - 0.5)
pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
for bar, v in zip(bars, vals_k):
    ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}", va="center", ha="left", fontsize=FS, color=INK)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ l — barh metabolites ═════════════════════════════════════════
ax = axd["l"]
metabs = ["N-acetylaspartate (NAA) — neuronal integrity and mitochondrial function marker in proton MRS",
          "Glutamate/glutamine complex (Glx) — excitatory neurotransmitter and astrocyte-neuron shuttle marker",
          "Myo-inositol (mI) — astrocyte proliferation marker and cerebral osmolyte regulation indicator",
          "Total choline-containing compounds (tCho = GPC + PCho) — membrane phospholipid turnover marker",
          "Total creatine + phosphocreatine (tCr = Cr + PCr) — cellular energy metabolism reference standard",
          "Lactate doublet at 1.33 ppm (Lac) — anaerobic glycolysis and mitochondrial dysfunction indicator",
          "N-acetylaspartylglutamate (NAAG) — peptide neurotransmitter and NAA metabolite at 2.04 ppm",
          "Gamma-aminobutyric acid (GABA) — primary inhibitory neurotransmitter measured by edited MRS"]
vals_l = np.sort(np.random.uniform(0.5, 3, len(metabs)))[::-1]
yp = np.arange(len(metabs))
bars = ax.barh(yp, vals_l, height=0.4,
               color=[GOLD[s] for s in ["100","200","300","400","500","600"]],
               edgecolor="none", alpha=ALPHA["bar"])
ax.set_yticks(yp)
ax.set_yticklabels(metabs, fontsize=FS)
ax.set_xlabel("Concentration (mM)", fontsize=FS)
ax.set_ylim(-0.5, len(metabs) - 0.5)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

# ══ m — text summary (spanning full width) ════════════════════════
ax = axd["m"]
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
summary = ("Key findings: Oxidative phosphorylation and synaptic vesicle cycle pathways "
           "are the most enriched (FDR < 0.001). APOE and CLU show strongest genetic "
           "associations. Prefrontal cortex and hippocampus CA1 have highest hazard ratios.")
ax.text(0.5, 0.5, summary, transform=ax.transAxes, fontsize=FS,
        ha="center", va="center", wrap=True,
        bbox=dict(boxstyle="round,pad=0.4", facecolor=BG_COLORS["cream"], edgecolor="none"))

# ══ Finalize ══════════════════════════════════════════════════════
exclude = {axd[k] for k in ["a","b","c","d","e","f","g","h","i","j","k","l","m"]}
trim_axes(fig, exclude=exclude)
contain_panels(fig, axd)
add_panel_labels(fig, axd)

# ── Detect + Fix ──────────────────────────────────────────────────
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
print(f"{'='*60}")

severe = [r for r in remaining if r["severity"] == "severe"]
moderate = [r for r in remaining if r["severity"] == "moderate"]
minor = [r for r in remaining if r["severity"] == "minor"]
print(f"\nAFTER fix: {len(severe)} severe, {len(moderate)} moderate, {len(minor)} minor")

out = os.path.dirname(os.path.abspath(__file__))
fig.savefig(os.path.join(out, "stress_test_labels.png"), dpi=300, bbox_inches="tight")
save_for_review(fig, os.path.join(out, "stress_test_labels_review.png"), dpi=72)
print("Saved stress_test_labels.png")
