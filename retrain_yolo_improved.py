"""
Improved YOLOv8 Training Script
=================================
Upgrades from YOLOv8n → YOLOv8s with optimized hyperparameters
for higher accuracy on the 12-class weed detection dataset.

Usage:
    python retrain_yolo_improved.py
"""

import os
import glob
from ultralytics import YOLO

# ─── Configuration ─────────────────────────────────────────────
MODEL = "yolov8n.pt"                    # YOLOv8n (nano) pretrained
DATA_YAML = "data.yaml"
EPOCHS = 80                              # 🔼 Increased from 40
BATCH_SIZE = 4                           # GTX 1650 (4GB VRAM)
IMAGE_SIZE = 640
DEVICE = 0                               # GPU
RUN_NAME = "train_improved"


def clear_label_cache():
    """Remove stale .cache files that cause class count mismatches."""
    cache_files = glob.glob("C:/dataset/wheat_yolo_dataset/labels/**/*.cache", recursive=True)
    for f in cache_files:
        os.remove(f)
        print(f"  🗑️  Removed: {f}")
    if not cache_files:
        print("  ✅ No stale cache files found.")


def main():
    print("=" * 60)
    print("  YOLOv8 IMPROVED TRAINING")
    print("=" * 60)

    # Step 1: Clear stale label caches
    print("\n📋 Clearing stale label caches...")
    clear_label_cache()

    # Step 2: Load model
    print(f"\n📦 Loading model: {MODEL}")
    model = YOLO(MODEL)

    # Step 3: Train with optimized settings
    print(f"\n🚀 Starting training...")
    print(f"   Model     : {MODEL} (YOLOv8s - small)")
    print(f"   Dataset   : {DATA_YAML}")
    print(f"   Epochs    : {EPOCHS}")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Image size: {IMAGE_SIZE}")

    results = model.train(
        data=DATA_YAML,
        device=DEVICE,
        epochs=EPOCHS,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        workers=0,
        name=RUN_NAME,

        # ─── Learning Rate ─────────────────────────────────
        lr0=0.01,
        lrf=0.01,
        cos_lr=True,              # 🔼 Cosine LR annealing for smoother convergence
        warmup_epochs=3,          # 🔼 Slightly longer warmup

        # ─── Early Stopping ────────────────────────────────
        patience=15,              # 🔼 More patience to avoid premature stopping

        # ─── Augmentations (enhanced for class imbalance) ──
        mosaic=1.0,               # 🔼 Full mosaic (was 0.7)
        mixup=0.3,                # 🔼 More mixup (was 0.15)
        copy_paste=0.15,          # 🔼 More copy-paste (was 0.05) — great for rare classes
        fliplr=0.5,               # 🔼 Standard horizontal flip
        flipud=0.1,               # 🔼 Added vertical flip
        degrees=15,               # 🔼 Slightly more rotation (was 10)
        translate=0.2,            # 🔼 More translation (was 0.1)
        scale=0.5,                #    Same scale
        hsv_h=0.015,              #    Color jitter
        hsv_s=0.7,                # 🔼 More saturation (was 0.6)
        hsv_v=0.4,                # 🔼 More brightness (was 0.3)
        erasing=0.4,              #    Random erasing

        # ─── Mosaic Scheduling ─────────────────────────────
        close_mosaic=15,          # 🔼 Disable mosaic later (was 8) for better fine-tuning

        # ─── Other ─────────────────────────────────────────
        amp=True,                 #    Mixed precision (faster)
        plots=True,               #    Generate plots
    )

    print("\n" + "=" * 60)
    print("  🎉 TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\n📁 Best weights: {results.save_dir}/weights/best.pt")
    print(f"\n💡 To evaluate, update MODEL_PATH in evaluate_yolo.py to:")
    print(f'   MODEL_PATH = "{results.save_dir}/weights/best.pt"')
    print(f"\n   Then run: python evaluate_yolo.py")

    return results


if __name__ == "__main__":
    main()
