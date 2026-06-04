"""
Quick Validation Script — CottonWeedDet12
Checks mAP50, mAP50-95, Precision, Recall for any .pt model.
Run:  python validate_cotton.py
"""

import os
import glob
import multiprocessing
from ultralytics import YOLO

# ── Config ─────────────────────────────────────────────────────────────────────
MODEL_PATH = r"C:\dataset\cotton_runs\yolov8m_cotton_v1\weights\last.pt"
DATA_YAML  = r"C:\dataset\cotton_yolo_split\data.yaml"
# ───────────────────────────────────────────────────────────────────────────────

def main():
    # ── Clear stale cache first (prevents NaN results) ────────────────────────
    for cache in glob.glob(r"C:\dataset\cotton_yolo_split\labels\*.cache"):
        os.remove(cache)
        print(f"  Cleared cache: {cache}")

    # ── Check model exists ─────────────────────────────────────────────────────
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found: {MODEL_PATH}")
        return

    size_mb = os.path.getsize(MODEL_PATH) / 1e6
    print(f"\n{'='*55}")
    print(f"  Validating: {os.path.basename(MODEL_PATH)}  ({size_mb:.1f} MB)")
    print(f"  Dataset   : {DATA_YAML}")
    print(f"{'='*55}\n")

    # ── Run validation ─────────────────────────────────────────────────────────
    model   = YOLO(MODEL_PATH)
    results = model.val(
        data    = DATA_YAML,
        imgsz   = 640,
        device  = 0,
        workers = 0,
        verbose = True,
    )

    # ── Print summary ──────────────────────────────────────────────────────────
    map50    = float(results.box.map50)
    map5095  = float(results.box.map)
    prec     = float(results.box.mp)
    rec      = float(results.box.mr)

    print(f"\n{'='*55}")
    print(f"  VALIDATION RESULTS — {os.path.basename(MODEL_PATH)}")
    print(f"{'='*55}")
    print(f"  mAP@50       : {map50:.4f}  ({map50*100:.1f}%)")
    print(f"  mAP@50-95    : {map5095:.4f}  ({map5095*100:.1f}%)")
    print(f"  Precision    : {prec:.4f}  ({prec*100:.1f}%)")
    print(f"  Recall       : {rec:.4f}  ({rec*100:.1f}%)")
    print(f"{'='*55}")

    target = 0.85
    if map50 >= target:
        print(f"  ✅ TARGET REACHED! mAP@50 = {map50:.4f} ≥ {target}")
    else:
        gap = target - map50
        print(f"  ⚠️  Target mAP@50 = {target}  |  Gap = {gap:.4f}")
        print(f"  💡 Continue training to close the gap.")
    print(f"{'='*55}\n")

    # ── Per-class breakdown ────────────────────────────────────────────────────
    print("  Per-Class Results:")
    print(f"  {'Class':<20} {'mAP@50':>8} {'Precision':>10} {'Recall':>8}")
    print(f"  {'-'*50}")
    class_names = [
        "waterhemp", "morningglory", "ragweed", "cocklebur",
        "spurred_anteria", "prickly_sida", "velvetleaf",
        "palmer_amaranth", "redroot_pigweed", "johnsongrass",
        "tall_morningglory", "sicklepod",
    ]
    try:
        maps   = results.box.maps        # per-class mAP50-95
        ap50   = results.box.ap50        # per-class mAP50
        p_list = results.box.p           # per-class precision
        r_list = results.box.r           # per-class recall
        for i, name in enumerate(class_names):
            if i < len(ap50):
                print(f"  {name:<20} {ap50[i]:>8.4f} {p_list[i]:>10.4f} {r_list[i]:>8.4f}")
    except Exception:
        print("  (per-class breakdown not available)")

    print(f"\n  Results saved to: runs/detect/val*\n")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
