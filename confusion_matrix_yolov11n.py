"""
Confusion Matrix + Train/Val/Test Split for YOLOv11n (CottonWeedDet12)
=======================================================================
Steps performed:
  1. Split CottonWeedDet12 raw dataset → train (70%) / val (15%) / test (15%)
  2. Write/update  data.yaml  with the new split paths
  3. Run  model.val()  on BOTH val and test splits
  4. Plot a richly styled confusion matrix (raw + normalised) using matplotlib
  5. Save all artefacts to  runs/confusion_matrix/

Usage:
    python confusion_matrix_yolov11n.py
"""

import io, os, sys, shutil, random
from pathlib import Path

# Force UTF-8 output on Windows (avoids UnicodeEncodeError with emojis/box chars)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────  CONFIG  ──────────────────────────────────────
MODEL_PATH   = Path(r"C:\Users\shina\Downloads\yolov11n_cotton12_2026-03-27\cotton_yolov11n\weights\best.pt")
RAW_IMAGES   = Path(r"C:\dataset\CottonWeedDet12\weedImages")
RAW_LABELS   = Path(r"C:\dataset\CottonWeedDet12\annotation_YOLO_txt")
DATASET_DIR  = Path(r"C:\dataset\wheat_yolo_dataset")   # output of split
DATA_YAML    = Path(r"c:\main project\Main-project-Wheat\data.yaml")
OUTPUT_DIR   = Path(r"c:\main project\Main-project-Wheat\runs\confusion_matrix")

TRAIN_RATIO  = 0.70
VAL_RATIO    = 0.15
# TEST_RATIO  = 1 - TRAIN - VAL = 0.15   (implicit)
SEED         = 42
IMG_SIZE     = 640
CONF         = 0.25
IOU          = 0.60

CLASS_NAMES = [
    "waterhemp", "morningglory", "ragweed", "cocklebur",
    "spurred_anteria", "prickly_sida", "velvetleaf", "palmer_amaranth",
    "redroot_pigweed", "johnsongrass", "tall_morningglory", "sicklepod",
]
NC = len(CLASS_NAMES)
# ─────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# 1. TRAIN / VAL / TEST SPLIT
# ══════════════════════════════════════════════════════════════════════════════
def split_dataset(force_resplit: bool = False):
    """
    Copy images + labels from raw CottonWeedDet12 into YOLO-style
    train / val / test folders.  Skip if already done (unless force_resplit).
    """
    for split in ("train", "val", "test"):
        (DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    val_img_dir = DATASET_DIR / "images" / "val"
    # Skip if already populated and not forced
    existing = list(val_img_dir.glob("*.*"))
    if existing and not force_resplit:
        print(f"✅ Dataset split already exists — {len(existing)} val images found. Skipping.")
        return

    print("📂 Scanning raw dataset for image-label pairs …")
    IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    pairs = []
    for img in sorted(RAW_IMAGES.iterdir()):
        if img.suffix.lower() in IMG_EXTS:
            lbl = RAW_LABELS / (img.stem + ".txt")
            if lbl.exists():
                pairs.append((img, lbl))

    if not pairs:
        sys.exit("❌  No image-label pairs found — check RAW_IMAGES / RAW_LABELS paths.")

    print(f"   Total pairs found : {len(pairs)}")

    random.seed(SEED)
    random.shuffle(pairs)

    n_train = int(len(pairs) * TRAIN_RATIO)
    n_val   = int(len(pairs) * VAL_RATIO)
    splits = {
        "train": pairs[:n_train],
        "val"  : pairs[n_train : n_train + n_val],
        "test" : pairs[n_train + n_val :],
    }

    for split, items in splits.items():
        dst_img = DATASET_DIR / "images" / split
        dst_lbl = DATASET_DIR / "labels" / split
        for img, lbl in items:
            shutil.copy2(img, dst_img / img.name)
            shutil.copy2(lbl, dst_lbl / lbl.name)
        print(f"   {split:5s} → {len(items):5d} pairs  →  {dst_img}")

    print("✅ Dataset split complete.\n")
    _print_split_table(splits)


def _print_split_table(splits):
    total = sum(len(v) for v in splits.values())
    print("┌──────────┬──────────┬──────────┐")
    print("│  Split   │  Images  │    (%)   │")
    print("├──────────┼──────────┼──────────┤")
    for split, items in splits.items():
        pct = len(items) / total * 100
        print(f"│ {split:<8} │ {len(items):>8} │ {pct:>7.1f}% │")
    print("├──────────┼──────────┼──────────┤")
    print(f"│ {'TOTAL':<8} │ {total:>8} │ {'100.0%':>8} │")
    print("└──────────┴──────────┴──────────┘")


# ══════════════════════════════════════════════════════════════════════════════
# 2. WRITE / UPDATE data.yaml
# ══════════════════════════════════════════════════════════════════════════════
def write_data_yaml():
    fwd = lambda p: str(p).replace("\\", "/")
    content = (
        f"path: {fwd(DATASET_DIR)}        # dataset root\n"
        f"train: {fwd(DATASET_DIR / 'images' / 'train')}\n"
        f"val:   {fwd(DATASET_DIR / 'images' / 'val')}\n"
        f"test:  {fwd(DATASET_DIR / 'images' / 'test')}\n"
        f"\n"
        f"nc: {NC}\n"
        f"names:\n"
        f"  {CLASS_NAMES}\n"
    )
    DATA_YAML.write_text(content, encoding="utf-8")
    print(f"✅ data.yaml written → {DATA_YAML}\n")


# ══════════════════════════════════════════════════════════════════════════════
# 3. YOLO VALIDATION (val + test splits)
# ══════════════════════════════════════════════════════════════════════════════
def run_validation(split: str = "val"):
    """Run model.val() on the given split and return the results object."""
    from ultralytics import YOLO
    model = YOLO(str(MODEL_PATH))

    print(f"\n[>>] Running validation on [{split}] split ...")
    results = model.val(
        data=str(DATA_YAML),
        split=split,
        imgsz=IMG_SIZE,
        batch=16,
        conf=CONF,
        iou=IOU,
        plots=True,
        save_json=False,
        project=str(OUTPUT_DIR),
        name=f"yolov11n_{split}",
        exist_ok=True,
    )
    print(f"   mAP@50     : {results.box.map50:.4f}")
    print(f"   mAP@50-95  : {results.box.map:.4f}")
    print(f"   Precision  : {results.box.mp:.4f}")
    print(f"   Recall     : {results.box.mr:.4f}")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 4. STYLED CONFUSION MATRIX PLOT
# ══════════════════════════════════════════════════════════════════════════════
def plot_confusion_matrix(results, split: str):
    """
    Build a beautiful custom confusion matrix from YOLO's internal matrix and
    save it as PNG + SVG in OUTPUT_DIR / yolov11n_{split}/.
    """
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    from matplotlib.colors import LinearSegmentedColormap

    save_dir = OUTPUT_DIR / f"yolov11n_{split}"
    save_dir.mkdir(parents=True, exist_ok=True)

    # Grab the raw matrix from YOLO (shape: [NC+1, NC+1])
    raw_cm = results.confusion_matrix.matrix  # numpy ndarray
    # Trim to [NC, NC] — drop background row/col
    cm = raw_cm[:NC, :NC].copy().astype(float)

    # ── colour maps ──────────────────────────────────────────────────────────
    # Dark-mode colour map: deep navy → electric teal/green
    colors_raw  = ["#0d1117", "#0d2137", "#0a3d6b", "#0e6b8a", "#11a8a8", "#1de9b6"]
    colors_norm = ["#0d1117", "#1a2040", "#2d3a7a", "#6a3fa0", "#c040b0", "#ff6ec7"]
    cmap_raw    = LinearSegmentedColormap.from_list("neon_blue",  colors_raw,  N=256)
    cmap_norm   = LinearSegmentedColormap.from_list("neon_pink",  colors_norm, N=256)

    short_names = [
        "Waterhemp", "M.Glory", "Ragweed", "Cocklebur",
        "Sp.Anteria", "Pr.Sida", "Velvetleaf", "P.Amaranth",
        "R.Pigweed", "Johnsongrass", "T.M.Glory", "Sicklepod",
    ]

    def _draw(matrix, title, cmap, fmt_fn, filename):
        fig, ax = plt.subplots(figsize=(14, 11), facecolor="#0d1117")
        ax.set_facecolor("#0d1117")

        im = ax.imshow(matrix, cmap=cmap, aspect="auto", interpolation="nearest")

        # colour-bar
        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cbar.ax.yaxis.set_tick_params(color="white", labelcolor="white")
        cbar.outline.set_edgecolor("#334155")

        # annotate cells
        vmax = matrix.max() if matrix.max() > 0 else 1
        for row in range(NC):
            for col in range(NC):
                val = matrix[row, col]
                text_color = "white" if val < 0.6 * vmax else "#0d1117"
                ax.text(col, row, fmt_fn(val),
                        ha="center", va="center",
                        fontsize=7.5, color=text_color,
                        fontweight="bold" if row == col else "normal")

        # axes labels
        ax.set_xticks(range(NC))
        ax.set_yticks(range(NC))
        ax.set_xticklabels(short_names, rotation=45, ha="right",
                           fontsize=9, color="#94a3b8")
        ax.set_yticklabels(short_names, fontsize=9, color="#94a3b8")
        ax.tick_params(colors="#334155")
        for spine in ax.spines.values():
            spine.set_edgecolor("#334155")

        ax.set_xlabel("Predicted Class", fontsize=12, color="#94a3b8",
                      labelpad=10, fontweight="bold")
        ax.set_ylabel("True Class", fontsize=12, color="#94a3b8",
                      labelpad=10, fontweight="bold")

        # title block
        fig.text(0.5, 0.97, title, ha="center", va="top",
                 fontsize=16, color="white", fontweight="bold")
        fig.text(0.5, 0.94,
                 f"YOLOv11n · CottonWeedDet12 · {NC} classes · split={split}",
                 ha="center", va="top", fontsize=10, color="#64748b")

        # diagonal highlight (golden border around TP cells)
        for i in range(NC):
            rect = plt.Rectangle((i - 0.5, i - 0.5), 1, 1,
                                  linewidth=1.5,
                                  edgecolor="#facc15",
                                  facecolor="none")
            ax.add_patch(rect)

        plt.tight_layout(rect=[0, 0, 1, 0.93])

        for ext in (".png", ".svg"):
            out = save_dir / (filename + ext)
            fig.savefig(out, dpi=180, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            print(f"   💾 Saved → {out}")

        plt.close(fig)

    # ── raw counts ───────────────────────────────────────────────────────────
    _draw(
        matrix=cm,
        title="Confusion Matrix  (Raw Counts)",
        cmap=cmap_raw,
        fmt_fn=lambda v: str(int(v)) if v > 0 else "",
        filename="confusion_matrix_raw",
    )

    # ── row-normalised (recall view) ─────────────────────────────────────────
    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm  = np.divide(cm, row_sums, where=row_sums > 0)

    _draw(
        matrix=cm_norm,
        title="Confusion Matrix  (Row-Normalised  ·  Recall View)",
        cmap=cmap_norm,
        fmt_fn=lambda v: f"{v:.2f}" if v > 0 else "",
        filename="confusion_matrix_normalized",
    )

    # ── per-class recall bar ──────────────────────────────────────────────────
    recall_per_class = np.diag(cm_norm)
    _plot_recall_bar(recall_per_class, short_names, save_dir, split)

    print(f"\n[OK] All plots saved to: {save_dir}\n")


def _plot_recall_bar(recall, short_names, save_dir, split):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(14, 5), facecolor="#0d1117")
    ax.set_facecolor("#121827")

    colors = ["#1de9b6" if r >= 0.7 else "#facc15" if r >= 0.4 else "#f87171"
              for r in recall]
    bars = ax.barh(short_names, recall, color=colors, edgecolor="#1e293b",
                   height=0.65)

    for bar, val in zip(bars, recall):
        ax.text(min(val + 0.01, 0.98), bar.get_y() + bar.get_height() / 2,
                f"{val:.2%}", va="center", fontsize=9,
                color="white", fontweight="bold")

    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Per-Class Recall", fontsize=12, color="#94a3b8", labelpad=8)
    ax.set_title(f"Per-Class Recall — YOLOv11n  [{split}]",
                 fontsize=14, color="white", pad=14, fontweight="bold")
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))

    # legend
    from matplotlib.patches import Patch
    legend = [Patch(color="#1de9b6", label="≥ 70% (Good)"),
              Patch(color="#facc15", label="40–70% (Fair)"),
              Patch(color="#f87171", label="< 40% (Poor)")]
    ax.legend(handles=legend, loc="lower right",
              framealpha=0.2, labelcolor="white", fontsize=9)

    plt.tight_layout()
    out = save_dir / "per_class_recall_bar.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"   💾 Saved → {out}")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# 5. SUMMARY REPORT
# ══════════════════════════════════════════════════════════════════════════════
def print_summary(results_val, results_test):
    import numpy as np

    print("\n" + "═" * 62)
    print("  📊  YOLOv11n EVALUATION SUMMARY  (CottonWeedDet12)")
    print("═" * 62)

    header = f"  {'Metric':<22} {'Val':>10} {'Test':>10}"
    print(header)
    print("  " + "─" * 44)

    def row(label, val, tst):
        print(f"  {label:<22} {val:>10.4f} {tst:>10.4f}")

    row("mAP@50",       results_val.box.map50, results_test.box.map50)
    row("mAP@50-95",    results_val.box.map,   results_test.box.map)
    row("Precision",    results_val.box.mp,    results_test.box.mp)
    row("Recall",       results_val.box.mr,    results_test.box.mr)

    # F1
    p_v, r_v = results_val.box.mp,  results_val.box.mr
    p_t, r_t = results_test.box.mp, results_test.box.mr
    f1_v = 2*p_v*r_v / (p_v+r_v+1e-9)
    f1_t = 2*p_t*r_t / (p_t+r_t+1e-9)
    row("F1 Score",     f1_v, f1_t)

    print("  " + "─" * 44)
    print(f"\n  📁 Artefacts saved under: {OUTPUT_DIR}")
    print("═" * 62 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    print("=" * 62)
    print("  YOLOv11n - Confusion Matrix & Dataset Split")
    print("  CottonWeedDet12 - 12 weed species")
    print("=" * 62 + "\n")

    # -- pre-flight checks --
    if not MODEL_PATH.exists():
        sys.exit(f"[ERROR] Model not found: {MODEL_PATH}")
    if not RAW_IMAGES.exists():
        sys.exit(f"[ERROR] Raw images dir not found: {RAW_IMAGES}")
    if not RAW_LABELS.exists():
        sys.exit(f"[ERROR] Raw labels dir not found: {RAW_LABELS}")

    try:
        import matplotlib
        import numpy
    except ImportError:
        sys.exit("[ERROR] Run:  pip install matplotlib numpy")

    # -- pipeline --
    split_dataset(force_resplit=False)  # set True to redo the split
    write_data_yaml()

    results_val  = run_validation("val")
    results_test = run_validation("test")

    print("\n[>>] Generating styled confusion matrices ...")
    plot_confusion_matrix(results_val,  "val")
    plot_confusion_matrix(results_test, "test")

    print_summary(results_val, results_test)
