"""
Matplotlib Confusion Matrix for YOLOv11n (CottonWeedDet12)
===========================================================
- Runs model.val() on the validation split
- Extracts raw confusion matrix from YOLO internals
- Draws 3 publication-quality matplotlib figures:
    1. Raw-count confusion matrix (dark teal heatmap)
    2. Row-normalised confusion matrix (recall view, purple heatmap)
    3. Per-class recall bar chart (colour-coded)
- Saves PNG + SVG to:   runs/cm_plots/

Usage:
    python plot_confusion_matrix.py
"""

import io, sys
# ── UTF-8 on Windows ──────────────────────────────────────────────────────────
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
from pathlib import Path

# ─────────────────────────────  CONFIG  ──────────────────────────────────────
MODEL_PATH = Path(
    r"C:\Users\shina\Downloads\yolov11n_cotton12_2026-03-27"
    r"\cotton_yolov11n\weights\best.pt"
)
DATA_YAML  = Path(r"c:\main project\Main-project-Wheat\data.yaml")
OUT_DIR    = Path(r"c:\main project\Main-project-Wheat\runs\cm_plots")

IMG_SIZE   = 640
CONF       = 0.25
IOU        = 0.60
SPLIT      = "val"   # "val" or "test"

CLASS_NAMES = [
    "waterhemp", "morningglory", "ragweed",    "cocklebur",
    "spurred_anteria", "prickly_sida", "velvetleaf", "palmer_amaranth",
    "redroot_pigweed", "johnsongrass", "tall_morningglory", "sicklepod",
]
SHORT_NAMES = [
    "Waterhemp", "M.Glory", "Ragweed",   "Cocklebur",
    "Sp.Anteria","Pr.Sida", "Velvetleaf","P.Amaranth",
    "R.Pigweed", "J.Grass", "T.M.Glory", "Sicklepod",
]
NC = len(CLASS_NAMES)
# ─────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# 1.  Run YOLO validation and extract the confusion matrix numpy array
# ══════════════════════════════════════════════════════════════════════════════
def get_confusion_matrix():
    try:
        from ultralytics import YOLO
    except ImportError:
        sys.exit("[ERROR] pip install ultralytics")

    print(f"[+] Loading model: {MODEL_PATH}")
    model = YOLO(str(MODEL_PATH))

    print(f"[+] Running model.val() on split='{SPLIT}' ...")
    results = model.val(
        data=str(DATA_YAML),
        split=SPLIT,
        imgsz=IMG_SIZE,
        conf=CONF,
        iou=IOU,
        plots=False,        # we draw our own
        verbose=False,
        save_json=False,
    )

    # YOLO stores an (NC+1 x NC+1) matrix; last row/col = background
    raw = results.confusion_matrix.matrix          # numpy array
    cm  = raw[:NC, :NC].copy().astype("float64")  # keep only real classes

    print(f"\n   mAP@50    : {results.box.map50:.4f}")
    print(f"   mAP@50-95 : {results.box.map:.4f}")
    print(f"   Precision : {results.box.mp:.4f}")
    print(f"   Recall    : {results.box.mr:.4f}\n")

    return cm, results


# ══════════════════════════════════════════════════════════════════════════════
# 2.  Matplotlib helpers
# ══════════════════════════════════════════════════════════════════════════════
BG        = "#0d1117"
GRID_CLR  = "#1e2d3d"
TEXT_CLR  = "#e2e8f0"
AXIS_CLR  = "#64748b"

def _base_fig():
    """Return a figure + axes pre-styled for dark mode."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 11), facecolor=BG)
    ax.set_facecolor(BG)
    return fig, ax


def _save(fig, stem):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg"):
        p = OUT_DIR / (stem + ext)
        fig.savefig(p, dpi=180, bbox_inches="tight", facecolor=BG)
        print(f"   Saved -> {p}")


# ══════════════════════════════════════════════════════════════════════════════
# 3.  Raw-count confusion matrix
# ══════════════════════════════════════════════════════════════════════════════
def plot_raw(cm):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list(
        "teal_dark",
        ["#0d1117", "#0a3d6b", "#0e8a8a", "#1de9b6"],
        N=256,
    )

    fig, ax = _base_fig()
    im = ax.imshow(cm, cmap=cmap, aspect="auto")

    # colorbar
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.ax.tick_params(colors=TEXT_CLR)
    cb.outline.set_edgecolor(GRID_CLR)
    cb.set_label("Detection Count", color=AXIS_CLR, fontsize=10)

    # cell annotations
    vmax = cm.max() if cm.max() > 0 else 1
    for r in range(NC):
        for c in range(NC):
            v = cm[r, c]
            clr = "#0d1117" if v > 0.65 * vmax else TEXT_CLR
            ax.text(c, r, f"{int(v)}" if v > 0 else "",
                    ha="center", va="center", fontsize=8,
                    color=clr,
                    fontweight="bold" if r == c else "normal")

    # diagonal highlight
    for i in range(NC):
        ax.add_patch(plt.Rectangle(
            (i - 0.5, i - 0.5), 1, 1,
            linewidth=2, edgecolor="#facc15", facecolor="none"
        ))

    _style_axes(ax, fig,
                title="Confusion Matrix  —  Raw Counts",
                subtitle=f"YOLOv11n · CottonWeedDet12 · 12 classes · split={SPLIT}")

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    _save(fig, "confusion_matrix_raw")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 4.  Normalised confusion matrix  (row-wise → recall per class)
# ══════════════════════════════════════════════════════════════════════════════
def plot_normalised(cm):
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm  = np.divide(cm, row_sums, where=row_sums > 0)

    cmap = LinearSegmentedColormap.from_list(
        "purple_pink",
        ["#0d1117", "#1a1040", "#5c2a9d", "#c040b0", "#ff6ec7"],
        N=256,
    )

    fig, ax = _base_fig()
    im = ax.imshow(cm_norm, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.ax.tick_params(colors=TEXT_CLR)
    cb.outline.set_edgecolor(GRID_CLR)
    cb.set_label("Recall (row-normalised)", color=AXIS_CLR, fontsize=10)

    for r in range(NC):
        for c in range(NC):
            v = cm_norm[r, c]
            clr = "#0d1117" if v > 0.60 else TEXT_CLR
            ax.text(c, r, f"{v:.2f}" if v > 0 else "",
                    ha="center", va="center", fontsize=8,
                    color=clr,
                    fontweight="bold" if r == c else "normal")

    for i in range(NC):
        ax.add_patch(plt.Rectangle(
            (i - 0.5, i - 0.5), 1, 1,
            linewidth=2, edgecolor="#facc15", facecolor="none"
        ))

    _style_axes(ax, fig,
                title="Confusion Matrix  —  Normalised (Recall)",
                subtitle=f"YOLOv11n · CottonWeedDet12 · 12 classes · split={SPLIT}")

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    _save(fig, "confusion_matrix_normalised")
    plt.close(fig)

    return cm_norm


# ══════════════════════════════════════════════════════════════════════════════
# 5.  Per-class recall bar chart
# ══════════════════════════════════════════════════════════════════════════════
def plot_recall_bar(cm_norm):
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    recall = np.diag(cm_norm)

    fig, ax = plt.subplots(figsize=(13, 6), facecolor=BG)
    ax.set_facecolor("#0f1923")

    bar_colors = [
        "#1de9b6" if v >= 0.70 else
        "#facc15" if v >= 0.40 else
        "#f87171"
        for v in recall
    ]

    bars = ax.barh(SHORT_NAMES, recall, color=bar_colors,
                   edgecolor=GRID_CLR, height=0.62)

    for bar, val in zip(bars, recall):
        ax.text(
            min(val + 0.012, 0.97),
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1%}",
            va="center", fontsize=9.5, color=TEXT_CLR, fontweight="bold"
        )

    # reference lines
    for x, label in [(0.5, "50%"), (0.7, "70%")]:
        ax.axvline(x, color="#334155", linestyle="--", linewidth=1, alpha=0.7)
        ax.text(x + 0.005, NC - 0.5, label,
                color="#475569", fontsize=8, va="top")

    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Per-Class Recall", fontsize=12, color=AXIS_CLR, labelpad=8,
                  fontweight="bold")
    ax.set_title(
        f"Per-Class Recall  —  YOLOv11n  [{SPLIT}]\n"
        f"CottonWeedDet12 · 12 Weed Species",
        fontsize=14, color=TEXT_CLR, pad=14, fontweight="bold"
    )
    ax.tick_params(colors=AXIS_CLR, labelsize=10)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_CLR)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:.0%}")
    )
    ax.invert_yaxis()

    legend_handles = [
        Patch(color="#1de9b6", label=">= 70%  Good"),
        Patch(color="#facc15", label="40-70%  Fair"),
        Patch(color="#f87171", label="<  40%  Poor"),
    ]
    ax.legend(handles=legend_handles, loc="lower right",
              facecolor="#1e293b", edgecolor=GRID_CLR,
              labelcolor=TEXT_CLR, fontsize=9, framealpha=0.9)

    plt.tight_layout()
    _save(fig, "per_class_recall_bar")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 6.  Shared axes styling helper
# ══════════════════════════════════════════════════════════════════════════════
def _style_axes(ax, fig, title, subtitle):
    ax.set_xticks(range(NC))
    ax.set_yticks(range(NC))
    ax.set_xticklabels(SHORT_NAMES, rotation=45, ha="right",
                       fontsize=9, color=AXIS_CLR)
    ax.set_yticklabels(SHORT_NAMES, fontsize=9, color=AXIS_CLR)
    ax.tick_params(colors=GRID_CLR)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_CLR)

    ax.set_xlabel("Predicted Class", fontsize=12, color=AXIS_CLR,
                  labelpad=12, fontweight="bold")
    ax.set_ylabel("True Class",      fontsize=12, color=AXIS_CLR,
                  labelpad=12, fontweight="bold")

    fig.text(0.5, 0.97, title,    ha="center", va="top",
             fontsize=16, color=TEXT_CLR, fontweight="bold")
    fig.text(0.5, 0.94, subtitle, ha="center", va="top",
             fontsize=10, color=AXIS_CLR)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    print("=" * 60)
    print("  YOLOv11n  —  Matplotlib Confusion Matrix")
    print("  CottonWeedDet12  |  12 weed classes")
    print("=" * 60 + "\n")

    if not MODEL_PATH.exists():
        sys.exit(f"[ERROR] Model not found:\n  {MODEL_PATH}")
    if not DATA_YAML.exists():
        sys.exit(f"[ERROR] data.yaml not found:\n  {DATA_YAML}")

    try:
        import matplotlib, numpy
    except ImportError:
        sys.exit("[ERROR] pip install matplotlib numpy")

    import matplotlib
    matplotlib.use("Agg")   # non-interactive backend — safe on Windows

    # Step 1: validate model and get confusion matrix
    cm, results = get_confusion_matrix()

    # Step 2: draw plots
    print("[+] Plotting raw confusion matrix ...")
    plot_raw(cm)

    print("[+] Plotting normalised confusion matrix ...")
    cm_norm = plot_normalised(cm)

    print("[+] Plotting per-class recall bar chart ...")
    plot_recall_bar(cm_norm)

    print("\n" + "=" * 60)
    print("  All plots saved to:")
    print(f"  {OUT_DIR}")
    print("=" * 60)
