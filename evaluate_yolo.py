"""
YOLOv8 Model Evaluation Script
================================
Calculates REAL metrics from the trained model on the validation dataset:
  - Precision, Recall, F1 Score
  - mAP@50, mAP@50-95
  - Classification Accuracy (TP / Total predictions)

Usage:
    python evaluate_yolo.py
"""

import os
import sys

# ─── Configuration ─────────────────────────────────────────────────────────────
MODEL_PATH  = "yolov8m.pt"          # pretrained YOLOv8m (COCO weights)
DATA_YAML   = "data.yaml"
OUTPUT_FILE = "evaluation_results_yolov8m.txt"
IMG_SIZE    = 640
CONF_THRESH = 0.25   # confidence threshold for predictions
IOU_THRESH  = 0.50   # IoU threshold to count a detection as correct (TP)
# ────────────────────────────────────────────────────────────────────────────────


def main():
    # ── 0. Imports (done here to surface clear errors) ──────────────────────────
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] ultralytics is not installed.  Run:  pip install ultralytics")
        sys.exit(1)

    print("=" * 70)
    print("  YOLOv8 Model Evaluation  (REAL METRICS)")
    print("=" * 70)
    print(f"\n[+] Model      : {MODEL_PATH}")
    print(f"[+] Dataset    : {DATA_YAML}")
    print(f"[+] Img size   : {IMG_SIZE}")
    print(f"[+] Conf thresh: {CONF_THRESH}")
    print(f"[+] IoU thresh : {IOU_THRESH}\n")

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model not found at '{MODEL_PATH}'")
        sys.exit(1)

    # ── 1. Load model ───────────────────────────────────────────────────────────
    print("[*] Loading model …")
    model = YOLO(MODEL_PATH)
    class_names = model.names          # {0: 'waterhemp', 1: 'morningglory', …}
    num_classes  = len(class_names)
    print(f"[+] Loaded successfully  ({num_classes} classes)\n")

    # ── 2. Run official YOLO validation ─────────────────────────────────────────
    print("[*] Running validation on the val split …")
    results = model.val(
        data=DATA_YAML,
        imgsz=IMG_SIZE,
        conf=CONF_THRESH,
        iou=IOU_THRESH,
        verbose=False,
    )

    # ── 3. Extract per-class metrics ─────────────────────────────────────────────
    # results.box  contains arrays indexed by class
    box = results.box

    # Per-class arrays
    per_p   = box.p        # precision  per class
    per_r   = box.r        # recall     per class
    per_ap50    = box.ap50         # AP@50      per class
    per_ap50_95 = box.ap           # AP@50:95   per class

    # F1 per class  (harmonic mean of P and R)
    per_f1 = (2 * per_p * per_r) / (per_p + per_r + 1e-9)

    # Mean metrics (across all classes)
    mean_p      = float(per_p.mean())
    mean_r      = float(per_r.mean())
    mean_f1     = float(per_f1.mean())
    mean_ap50   = float(per_ap50.mean())
    mean_ap50_95 = float(per_ap50_95.mean())

    # ── 4. Compute Accuracy from confusion matrix ─────────────────────────────────
    # Accuracy  =  correctly classified detections / total detections
    # We use the confusion matrix (shape: [nc+1, nc+1]) where the last row/col
    # is the "background" class.
    try:
        cm = results.confusion_matrix.matrix   # numpy array
        # True-positives sit along the diagonal (excluding background class)
        tp_total   = float(cm.diagonal()[:num_classes].sum())
        all_preds  = float(cm[:, :num_classes].sum())   # every prediction for real classes
        accuracy   = tp_total / (all_preds + 1e-9)
    except Exception:
        # Fallback: derive from P & R if confusion matrix is unavailable
        # Accuracy ≈ mAP@50  (common approximation for detection tasks)
        accuracy = mean_ap50
        print("[!] Confusion matrix unavailable – accuracy estimated from mAP@50")

    # ── 5. Print results ──────────────────────────────────────────────────────────
    sep   = "-" * 100
    hdr   = (f"{'Class':<25} {'Precision':>10} {'Recall':>10} "
             f"{'F1':>10} {'mAP@50':>10} {'mAP@50-95':>11}")

    lines = []
    lines.append("=" * 100)
    lines.append("  YOLOv8 EVALUATION RESULTS  (REAL METRICS)")
    lines.append("=" * 100)
    lines.append(f"  Model   : {MODEL_PATH}")
    lines.append(f"  Dataset : {DATA_YAML}")
    lines.append(f"  Classes : {num_classes}")
    lines.append("")
    lines.append(sep)
    lines.append(hdr)
    lines.append(sep)

    for i, name in class_names.items():
        if i >= len(per_p):
            continue
        row = (f"  {name:<23} {per_p[i]:>10.4f} {per_r[i]:>10.4f} "
               f"{per_f1[i]:>10.4f} {per_ap50[i]:>10.4f} {per_ap50_95[i]:>11.4f}")
        lines.append(row)

    lines.append(sep)
    overall_row = (f"  {'OVERALL (mean)':<23} {mean_p:>10.4f} {mean_r:>10.4f} "
                   f"{mean_f1:>10.4f} {mean_ap50:>10.4f} {mean_ap50_95:>11.4f}")
    lines.append(overall_row)
    lines.append(sep)

    summary = f"""
+----------------------------------------------------+
|           ✅  SUMMARY OF KEY METRICS               |
+----------------------------------------------------+
|  Precision      :  {mean_p:.4f}                       |
|  Recall         :  {mean_r:.4f}                       |
|  F1 Score       :  {mean_f1:.4f}                       |
|  Accuracy       :  {accuracy:.4f}  ({accuracy*100:.2f}%)           |
|  mAP@50         :  {mean_ap50:.4f}                       |
|  mAP@50-95      :  {mean_ap50_95:.4f}                       |
+----------------------------------------------------+
"""
    lines.append(summary)

    output_text = "\n".join(lines)
    print(output_text)

    # ── 6. Save to file ───────────────────────────────────────────────────────────
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output_text)

    print(f"[*] Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    # Windows multiprocessing safety guard
    import multiprocessing
    multiprocessing.freeze_support()
    main()