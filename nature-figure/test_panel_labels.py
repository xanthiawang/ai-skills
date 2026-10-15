"""Regression test for add_panel_labels clamping. A label must not intrude into ANY other
panel's region: neither its axes area nor its outside-axes decorations (legend/annotation)."""
import sys, importlib, numpy as np, matplotlib
matplotlib.use("Agg")
sys.path.insert(0, sys.argv[1]); import nature_figure_utils as nfu; importlib.reload(nfu)
import matplotlib.pyplot as plt

def intrusions(fig, axd):
    fig.canvas.draw(); r = fig.canvas.get_renderer(); bad = []
    labels = [t for t in fig.texts if t.get_text() in axd]
    for t in labels:
        tb = t.get_window_extent(r)
        for k, ax in axd.items():
            if k == t.get_text(): continue
            for what, bb in (("axes", ax.get_window_extent(r)), ("tightbbox", ax.get_tightbbox(r))):
                ix = min(tb.x1, bb.x1) - max(tb.x0, bb.x0); iy = min(tb.y1, bb.y1) - max(tb.y0, bb.y0)
                if ix > 1 and iy > 1: bad.append(f"label {t.get_text()} -> panel {k} {what} ({ix:.0f}x{iy:.0f}px)")
    return bad

def case_spanning():
    nfu.retro_style()
    fig, axd = plt.subplot_mosaic([["a","a","b"],["a","a","c"]], figsize=(7.2,4), layout="constrained")
    for ax in axd.values(): ax.plot([0,1],[0,1]); ax.set_ylabel("Y label long text")
    nfu.add_panel_labels(fig, axd, pad_x=-0.12)   # aggressive negative pad
    return fig, axd

def case_right_decoration():
    nfu.retro_style()
    fig, axd = plt.subplot_mosaic([["a","b"]], figsize=(7.2,3), layout="constrained")
    axd["a"].plot([0,1],[0,1], label="series with a long legend name")
    axd["a"].legend(loc="center left", bbox_to_anchor=(1.0, 0.85), frameon=False)  # sits outside a, toward b
    axd["b"].plot([0,1],[1,0]); axd["b"].set_ylabel("Y")
    nfu.add_panel_labels(fig, axd, pad_x=-0.12)
    return fig, axd

fails = 0
for name, fn in [("row-spanning neighbour", case_spanning), ("neighbour outside-axes legend", case_right_decoration)]:
    fig, axd = fn(); bad = intrusions(fig, axd); plt.close(fig)
    print(("FAIL " if bad else "PASS ") + name); [print("   ", b) for b in bad]; fails += bool(bad)
sys.exit(1 if fails else 0)
