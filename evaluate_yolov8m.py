"""
╔══════════════════════════════════════════════════════════════════════╗
║   YOLOv8m — Full Model Evaluation Script                           ║
║                                                                     ║
║   Reports ALL metrics:                                              ║
║     • Precision, Recall, F1-Score (per-class + overall)            ║
║     • mAP@50, mAP@50-95                                            ║
║     • Accuracy (classification accuracy from detections)           ║
║     • Confusion Matrix                                              ║
║     • Inference speed                                               ║
║     • Per-class breakdown table                                     ║
║     • Detection count analysis                                      ║
║                                                                     ║
║   Run:  python evaluate_yolov8m.py                                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import multiprocessing
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
# Try best.pt first, fall back to last.pt
BEST_PT     = r"C:\dataset\cotton_runs\yolov8m_cotton_v1\weights\best.pt"
LAST_PT     = r"C:\dataset\cotton_runs\yolov8m_cotton_v1\weights\last.pt"
DATA_YAML   = r"C:\dataset\cotton_yolo_split\data.yaml"
IMG_SIZE    = 640
CONF_THRESH = 0.25       # confidence threshold for detections
IOU_THRESH  = 0.5        # IoU threshold for NMS
DEVICE      = 0          # 0 = GPU, 'cpu' = CPU
WORKERS     = 0          # 0 for Windows compatibility
SAVE_DIR    = r"C:\dataset\cotton_runs\yolov8m_cotton_v1\evaluation"
# ──────────────────────────────────────────────────────────────────────────────


def select_weights():
    """Choose best.pt if it exists, otherwise last.pt."""
    if os.path.exists(BEST_PT):
        print(f"  Using best.pt : {BEST_PT}")
        return BEST_PT
    elif os.path.exists(LAST_PT):
        print(f"  ⚠️  best.pt not found, using last.pt : {LAST_PT}")
        return LAST_PT
    else:
        print(f"  ❌ No weights found!")
        print(f"     Checked: {BEST_PT}")
        print(f"     Checked: {LAST_PT}")
        sys.exit(1)


def run_yolo_validation(weights_path):
    """Run YOLO's built-in validation and return results."""
    from ultralytics import YOLO

    print("\n  Loading model...")
    model = YOLO(weights_path)

    print("  Running validation on dataset...")
    print(f"  Dataset    : {DATA_YAML}")
    print(f"  Image size : {IMG_SIZE}")
    print(f"  Conf thresh: {CONF_THRESH}")
    print(f"  IoU thresh : {IOU_THRESH}")
    print()

    results = model.val(
        data      = DATA_YAML,
        imgsz     = IMG_SIZE,
        conf      = CONF_THRESH,
        iou       = IOU_THRESH,
        device    = DEVICE,
        workers   = WORKERS,
        verbose   = True,
        plots     = True,         # generates confusion matrix, PR curves, etc.
        save_json = False,
    )

    return model, results


def print_overall_metrics(results):
    """Print overall (macro) metrics."""
    box = results.box

    # Core metrics
    precision  = float(box.mp)       # mean precision
    recall     = float(box.mr)       # mean recall
    map50      = float(box.map50)    # mAP @ IoU=0.50
    map50_95   = float(box.map)      # mAP @ IoU=0.50:0.95

    # F1 score
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    # Accuracy approximation (based on correct detections)
    # True accuracy requires matching each detection to ground truth
    # We use the per-class precision*recall as a proxy
    accuracy = precision * recall  # detection accuracy proxy

    print("=" * 70)
    print("  📊 OVERALL METRICS")
    print("=" * 70)
    print()
    print(f"  ┌────────────────────┬─────────────┬────────────┐")
    print(f"  │ Metric             │    Value    │  Percent   │")
    print(f"  ├────────────────────┼─────────────┼────────────┤")
    print(f"  │ Precision          │  {precision:9.4f}  │  {precision*100:6.2f}%   │")
    print(f"  │ Recall             │  {recall:9.4f}  │  {recall*100:6.2f}%   │")
    print(f"  │ F1-Score           │  {f1:9.4f}  │  {f1*100:6.2f}%   │")
    print(f"  │ mAP@50             │  {map50:9.4f}  │  {map50*100:6.2f}%   │")
    print(f"  │ mAP@50-95          │  {map50_95:9.4f}  │  {map50_95*100:6.2f}%   │")
    print(f"  │ Det. Accuracy      │  {accuracy:9.4f}  │  {accuracy*100:6.2f}%   │")
    print(f"  └────────────────────┴─────────────┴────────────┘")
    print()

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'map50': map50,
        'map50_95': map50_95,
        'accuracy': accuracy,
    }


def print_per_class_metrics(results, data_yaml_path):
    """Print per-class breakdown of metrics."""
    import yaml

    # Load class names
    with open(data_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    class_names = data.get('names', [])
    nc = data.get('nc', len(class_names))

    box = results.box

    # Per-class arrays
    # box.p = precision per class, box.r = recall per class
    # box.ap50 = AP@50 per class, box.ap = AP@50-95 per class
    p_arr    = box.p      # (nc,) array
    r_arr    = box.r      # (nc,) array
    ap50_arr = box.ap50() if callable(box.ap50) else box.ap50  # (nc,) array
    ap_arr   = box.ap     # (nc, 10) array — AP at different IoU thresholds

    print("=" * 70)
    print("  📋 PER-CLASS METRICS")
    print("=" * 70)
    print()
    print(f"  ┌─────┬──────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐")
    print(f"  │  ID │ Class                │ Prec.    │ Recall   │ F1       │ mAP@50   │ mAP@.5:.95│")
    print(f"  ├─────┼──────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤")

    class_metrics = []
    for i in range(min(nc, len(p_arr))):
        name = class_names[i] if i < len(class_names) else f"class_{i}"
        p   = float(p_arr[i])
        r   = float(r_arr[i])
        a50 = float(ap50_arr[i])
        a   = float(ap_arr[i].mean()) if len(ap_arr.shape) > 1 else float(ap_arr[i])

        # F1 per class
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0

        print(f"  │ {i:3d} │ {name:20s} │ {p:8.4f} │ {r:8.4f} │ {f1:8.4f} │ {a50:8.4f} │ {a:8.4f}  │")

        class_metrics.append({
            'id': i,
            'name': name,
            'precision': p,
            'recall': r,
            'f1': f1,
            'ap50': a50,
            'ap50_95': a,
        })

    print(f"  └─────┴──────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘")
    print()

    # Best and worst classes
    if class_metrics:
        sorted_by_f1 = sorted(class_metrics, key=lambda x: x['f1'], reverse=True)
        best = sorted_by_f1[0]
        worst = sorted_by_f1[-1]
        print(f"  🏆 Best  class: {best['name']} (F1={best['f1']:.4f}, mAP@50={best['ap50']:.4f})")
        print(f"  ⚠️  Worst class: {worst['name']} (F1={worst['f1']:.4f}, mAP@50={worst['ap50']:.4f})")
        print()

    return class_metrics


def print_speed_metrics(results):
    """Print inference speed metrics."""
    speed = results.speed

    print("=" * 70)
    print("  ⚡ INFERENCE SPEED")
    print("=" * 70)
    print()

    preprocess = speed.get('preprocess', 0)
    inference  = speed.get('inference', 0)
    postprocess = speed.get('postprocess', 0)
    total = preprocess + inference + postprocess

    print(f"  Pre-process  : {preprocess:.1f} ms")
    print(f"  Inference    : {inference:.1f} ms")
    print(f"  Post-process : {postprocess:.1f} ms")
    print(f"  Total/image  : {total:.1f} ms")

    if total > 0:
        fps = 1000.0 / total
        print(f"  FPS          : {fps:.1f}")
    print()


def compute_detailed_accuracy(model, data_yaml_path):
    """
    Run inference on validation images and compute detailed accuracy metrics
    by comparing predicted classes vs ground truth classes.
    """
    import yaml
    import torch
    import numpy as np

    print("=" * 70)
    print("  🎯 DETAILED DETECTION ANALYSIS")
    print("=" * 70)
    print()

    with open(data_yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    val_img_dir = data['val']
    val_lbl_dir = val_img_dir.replace('images', 'labels')
    class_names = data.get('names', [])
    nc = data.get('nc', len(class_names))

    if not os.path.isdir(val_img_dir):
        print(f"  ❌ Val directory not found: {val_img_dir}")
        return

    # Get image files
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
    img_files = sorted([
        f for f in os.listdir(val_img_dir)
        if Path(f).suffix.lower() in valid_exts
    ])

    print(f"  Validation images: {len(img_files)}")
    print(f"  Running inference on all images...\n")

    total_gt_boxes = 0
    total_pred_boxes = 0
    total_matched = 0
    correct_class = 0
    per_class_tp = {i: 0 for i in range(nc)}
    per_class_fp = {i: 0 for i in range(nc)}
    per_class_fn = {i: 0 for i in range(nc)}
    per_class_gt = {i: 0 for i in range(nc)}

    start_time = time.time()
    processed = 0

    for idx, img_name in enumerate(img_files):
        img_path = os.path.join(val_img_dir, img_name)
        lbl_path = os.path.join(val_lbl_dir, Path(img_name).stem + '.txt')

        # Read ground truth
        gt_boxes = []
        if os.path.exists(lbl_path):
            with open(lbl_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        x, y, w, h = [float(p) for p in parts[1:5]]
                        gt_boxes.append((cls_id, x, y, w, h))
                        per_class_gt[cls_id] = per_class_gt.get(cls_id, 0) + 1

        # Run prediction
        results = model.predict(
            img_path,
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            imgsz=IMG_SIZE,
            device=DEVICE,
            verbose=False,
        )

        pred_boxes = []
        if results and len(results) > 0:
            r = results[0]
            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    cls_id = int(box.cls.item())
                    conf = float(box.conf.item())
                    # Get xywhn (normalized xywh)
                    xywhn = box.xywhn[0].cpu().numpy()
                    pred_boxes.append((cls_id, conf, xywhn[0], xywhn[1], xywhn[2], xywhn[3]))

        total_gt_boxes += len(gt_boxes)
        total_pred_boxes += len(pred_boxes)

        # Match predictions to ground truth using IoU
        matched_gt = set()
        matched_pred = set()

        for pi, pred in enumerate(pred_boxes):
            p_cls, p_conf, px, py, pw, ph = pred
            best_iou = 0
            best_gi = -1

            for gi, gt in enumerate(gt_boxes):
                if gi in matched_gt:
                    continue
                g_cls, gx, gy, gw, gh = gt

                # Compute IoU (in normalized coordinates)
                iou = compute_iou_xywh(px, py, pw, ph, gx, gy, gw, gh)

                if iou > best_iou:
                    best_iou = iou
                    best_gi = gi

            if best_iou >= 0.5 and best_gi >= 0:
                matched_gt.add(best_gi)
                matched_pred.add(pi)
                total_matched += 1

                gt_cls = gt_boxes[best_gi][0]
                if p_cls == gt_cls:
                    correct_class += 1
                    per_class_tp[p_cls] = per_class_tp.get(p_cls, 0) + 1
                else:
                    per_class_fp[p_cls] = per_class_fp.get(p_cls, 0) + 1
                    per_class_fn[gt_cls] = per_class_fn.get(gt_cls, 0) + 1
            else:
                # False positive
                per_class_fp[p_cls] = per_class_fp.get(p_cls, 0) + 1

        # Unmatched ground truths are false negatives
        for gi, gt in enumerate(gt_boxes):
            if gi not in matched_gt:
                per_class_fn[gt[0]] = per_class_fn.get(gt[0], 0) + 1

        processed += 1
        if processed % 200 == 0 or processed == len(img_files):
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (len(img_files) - processed) / rate if rate > 0 else 0
            print(f"    Processed: {processed}/{len(img_files)} ({rate:.1f} img/s, ETA: {eta:.0f}s)")

    elapsed = time.time() - start_time

    # Overall stats
    print(f"\n  ────────────────────────────────────────")
    print(f"  Total GT boxes         : {total_gt_boxes}")
    print(f"  Total Predictions      : {total_pred_boxes}")
    print(f"  Matched (IoU ≥ 0.5)    : {total_matched}")
    print(f"  Correct class matches  : {correct_class}")
    print(f"  Processing time        : {elapsed:.1f}s")

    # Detection accuracy
    det_accuracy = correct_class / total_gt_boxes if total_gt_boxes > 0 else 0
    det_precision = correct_class / total_pred_boxes if total_pred_boxes > 0 else 0
    det_recall = correct_class / total_gt_boxes if total_gt_boxes > 0 else 0
    det_f1 = 2 * (det_precision * det_recall) / (det_precision + det_recall) if (det_precision + det_recall) > 0 else 0

    print(f"\n  ┌───────────────────────────┬─────────────┐")
    print(f"  │ Detection Metric          │    Value    │")
    print(f"  ├───────────────────────────┼─────────────┤")
    print(f"  │ Detection Accuracy        │  {det_accuracy*100:7.2f}%   │")
    print(f"  │ Detection Precision       │  {det_precision*100:7.2f}%   │")
    print(f"  │ Detection Recall          │  {det_recall*100:7.2f}%   │")
    print(f"  │ Detection F1-Score        │  {det_f1*100:7.2f}%   │")
    print(f"  │ Match Rate (IoU≥0.5)      │  {total_matched/total_gt_boxes*100 if total_gt_boxes > 0 else 0:7.2f}%   │")
    print(f"  └───────────────────────────┴─────────────┘")

    # Per-class detailed table
    print(f"\n  Per-Class Detection Breakdown:")
    print(f"  ┌─────┬──────────────────────┬────────┬────────┬────────┬──────────┬──────────┬──────────┐")
    print(f"  │  ID │ Class                │   GT   │   TP   │   FP   │ Prec.    │ Recall   │ F1       │")
    print(f"  ├─────┼──────────────────────┼────────┼────────┼────────┼──────────┼──────────┼──────────┤")

    for i in range(nc):
        name = class_names[i] if i < len(class_names) else f"class_{i}"
        gt = per_class_gt.get(i, 0)
        tp = per_class_tp.get(i, 0)
        fp = per_class_fp.get(i, 0)
        fn = per_class_fn.get(i, 0)

        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0

        print(f"  │ {i:3d} │ {name:20s} │ {gt:6d} │ {tp:6d} │ {fp:6d} │ {p:8.4f} │ {r:8.4f} │ {f1:8.4f} │")

    print(f"  └─────┴──────────────────────┴────────┴────────┴────────┴──────────┴──────────┴──────────┘")
    print()


def compute_iou_xywh(x1, y1, w1, h1, x2, y2, w2, h2):
    """Compute IoU between two boxes in (center_x, center_y, w, h) format."""
    # Convert to (x_min, y_min, x_max, y_max)
    ax1 = x1 - w1 / 2
    ay1 = y1 - h1 / 2
    ax2 = x1 + w1 / 2
    ay2 = y1 + h1 / 2

    bx1 = x2 - w2 / 2
    by1 = y2 - h2 / 2
    bx2 = x2 + w2 / 2
    by2 = y2 + h2 / 2

    # Intersection
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    # Union
    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def save_report(overall, class_metrics, weights_path):
    """Save evaluation report to a text file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    report_path = os.path.join(SAVE_DIR, "evaluation_report.txt")

    with open(report_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("  YOLOv8m — CottonWeedDet12 Evaluation Report\n")
        f.write(f"  Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Weights: {weights_path}\n")
        f.write("=" * 60 + "\n\n")

        f.write("OVERALL METRICS\n")
        f.write("-" * 40 + "\n")
        for key, value in overall.items():
            f.write(f"  {key:20s}: {value:.4f} ({value*100:.2f}%)\n")
        f.write("\n")

        if class_metrics:
            f.write("PER-CLASS METRICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"  {'Class':20s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s} {'mAP50':>8s} {'mAP.5:.95':>10s}\n")
            for cm in class_metrics:
                f.write(f"  {cm['name']:20s} {cm['precision']:8.4f} {cm['recall']:8.4f} "
                        f"{cm['f1']:8.4f} {cm['ap50']:8.4f} {cm['ap50_95']:10.4f}\n")

    print(f"  📁 Report saved: {report_path}")
    return report_path


def main():
    print("=" * 70)
    print("  🔍 YOLOv8m — Full Model Evaluation")
    print(f"  📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Step 1: Select weights
    weights_path = select_weights()

    # Step 2: Run YOLO built-in validation (gets mAP, PR curves, confusion matrix)
    print("\n" + "─" * 70)
    print("  PHASE 1: YOLO Built-in Validation")
    print("─" * 70)
    model, results = run_yolo_validation(weights_path)

    # Step 3: Print overall metrics
    overall = print_overall_metrics(results)

    # Step 4: Print per-class metrics
    class_metrics = print_per_class_metrics(results, DATA_YAML)

    # Step 5: Print speed
    print_speed_metrics(results)

    # Step 6: Detailed detection analysis (custom accuracy computation)
    print("\n" + "─" * 70)
    print("  PHASE 2: Detailed Detection Analysis")
    print("─" * 70)
    compute_detailed_accuracy(model, DATA_YAML)

    # Step 7: Save report
    print("\n" + "─" * 70)
    print("  SAVING REPORT")
    print("─" * 70)
    report_path = save_report(overall, class_metrics, weights_path)

    # Step 8: Show where plots are saved
    save_dir = str(results.save_dir) if hasattr(results, 'save_dir') else SAVE_DIR
    print(f"\n  📊 Plots saved to: {save_dir}")
    print(f"     Look for: confusion_matrix.png, PR_curve.png, F1_curve.png")

    # Final summary
    print("\n" + "=" * 70)
    print("  🏁 EVALUATION COMPLETE")
    print("=" * 70)

    target_map50 = 0.85
    if overall['map50'] >= target_map50:
        print(f"\n  ✅ TARGET ACHIEVED! mAP@50 = {overall['map50']:.4f} ≥ {target_map50}")
        print(f"  🏆 Model is ready for deployment!")
    else:
        gap = target_map50 - overall['map50']
        print(f"\n  ⚠️  Current mAP@50: {overall['map50']:.4f}")
        print(f"  ⚠️  Target mAP@50 : {target_map50}")
        print(f"  ⚠️  Gap           : {gap:.4f}")
        print(f"\n  💡 Recommendations:")
        if overall['map50'] == 0:
            print(f"     1. Model is producing zero detections — weights may be corrupted")
            print(f"     2. Retrain from scratch with amp=False (critical for GTX 1650)")
            print(f"     3. Start from yolov8m.pt pretrained weights, not corrupted last.pt")
        elif overall['map50'] < 0.5:
            print(f"     1. Continue training for more epochs")
            print(f"     2. Try lower learning rate (lr0=0.001)")
            print(f"     3. Check if dataset has enough samples per class")
        else:
            print(f"     1. Fine-tune with lower learning rate")
            print(f"     2. Add more training data for weak classes")
            print(f"     3. Increase image size to 1280 if GPU allows")

    print()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
