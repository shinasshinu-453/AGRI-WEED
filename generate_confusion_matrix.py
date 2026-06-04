"""
Generate Confusion Matrix for YOLOv11n (CottonWeedDet12)
========================================================
This script:
1. Prepares the CottonWeedDet12 dataset into YOLO train/val format
2. Runs YOLO validation on the val split
3. Saves the confusion matrix as an image
"""

import os
import sys
import shutil
import random
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
MODEL_PATH = r"C:\Users\shina\Downloads\yolov11n_cotton12_2026-03-27\cotton_yolov11n\weights\best.pt"
RAW_DATASET   = Path(r"C:\dataset\CottonWeedDet12")
IMAGES_DIR    = RAW_DATASET / "weedImages"
LABELS_DIR    = RAW_DATASET / "annotation_YOLO_txt"
PREPARED_DIR  = Path(r"C:\dataset\wheat_yolo_dataset")   # matches data.yaml path
VAL_SPLIT     = 0.2       # 20 % for validation
SEED          = 42

CLASS_NAMES = [
    "waterhemp", "morningglory", "ragweed", "cocklebur",
    "spurred_anteria", "prickly_sida", "velvetleaf", "palmer_amaranth",
    "redroot_pigweed", "johnsongrass", "tall_morningglory", "sicklepod",
]

DATA_YAML_PATH = Path(r"c:\main project\Main-project-Wheat\data.yaml")
OUTPUT_DIR = Path(r"c:\main project\Main-project-Wheat\runs\detect")


# ──────────────────────────────────────────────────────────────────────────────
# Step 1 – Prepare dataset (train / val split) if not already done
# ──────────────────────────────────────────────────────────────────────────────
def prepare_dataset():
    """Split raw CottonWeedDet12 into YOLO-style train/val folders."""
    train_img = PREPARED_DIR / "images" / "train"
    val_img   = PREPARED_DIR / "images" / "val"
    train_lbl = PREPARED_DIR / "labels" / "train"
    val_lbl   = PREPARED_DIR / "labels" / "val"

    # If val images already exist with content, skip preparation
    if val_img.exists() and any(val_img.iterdir()):
        count = len(list(val_img.glob("*.*")))
        print(f"✅ Dataset already prepared – {count} val images found.")
        return

    print("📂 Preparing dataset into YOLO train/val format …")

    for d in [train_img, val_img, train_lbl, val_lbl]:
        d.mkdir(parents=True, exist_ok=True)

    # Collect all image files that have a matching label
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    pairs = []
    for img_file in sorted(IMAGES_DIR.iterdir()):
        if img_file.suffix.lower() in image_exts:
            lbl_file = LABELS_DIR / (img_file.stem + ".txt")
            if lbl_file.exists():
                pairs.append((img_file, lbl_file))

    if not pairs:
        print("❌ No image-label pairs found. Check dataset paths.")
        sys.exit(1)

    print(f"   Found {len(pairs)} image-label pairs.")

    random.seed(SEED)
    random.shuffle(pairs)

    split_idx = int(len(pairs) * (1 - VAL_SPLIT))
    train_pairs = pairs[:split_idx]
    val_pairs   = pairs[split_idx:]

    print(f"   Train: {len(train_pairs)}  |  Val: {len(val_pairs)}")

    for img, lbl in train_pairs:
        shutil.copy2(img, train_img / img.name)
        shutil.copy2(lbl, train_lbl / lbl.name)

    for img, lbl in val_pairs:
        shutil.copy2(img, val_img / img.name)
        shutil.copy2(lbl, val_lbl / lbl.name)

    print("✅ Dataset preparation complete.")


# ──────────────────────────────────────────────────────────────────────────────
# Step 2 – Write / verify data.yaml
# ──────────────────────────────────────────────────────────────────────────────
def write_data_yaml():
    """Ensure data.yaml points to the prepared dataset with correct classes."""
    content = f"""path: {str(PREPARED_DIR).replace(chr(92), '/')}        # Use forward slashes for YOLO
train: {str(PREPARED_DIR / 'images' / 'train').replace(chr(92), '/')}
val: {str(PREPARED_DIR / 'images' / 'val').replace(chr(92), '/')}

nc: {len(CLASS_NAMES)}
names:
  {CLASS_NAMES}
"""
    DATA_YAML_PATH.write_text(content, encoding="utf-8")
    print(f"✅ data.yaml updated → {DATA_YAML_PATH}")


# ──────────────────────────────────────────────────────────────────────────────
# Step 3 – Run YOLO validation and generate confusion matrix
# ──────────────────────────────────────────────────────────────────────────────
def generate_confusion_matrix():
    """Run model.val() to produce the confusion matrix."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ultralytics not installed. Run:  pip install ultralytics")
        sys.exit(1)

    print(f"\n🔄 Loading model: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print(f"   Classes: {model.names}")

    print("\n🔄 Running validation on val split …")
    results = model.val(
        data=str(DATA_YAML_PATH),
        imgsz=640,
        batch=16,
        conf=0.25,
        iou=0.6,
        plots=True,          # This generates confusion_matrix.png
        save_json=False,
        project=str(OUTPUT_DIR.parent.parent / "runs" / "detect"),
        name="yolov11n_confusion_matrix",
        exist_ok=True,
    )

    # Find the generated confusion matrix image
    run_dir = Path(results.save_dir)
    cm_path = run_dir / "confusion_matrix.png"
    cm_norm_path = run_dir / "confusion_matrix_normalized.png"

    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    print(f"   mAP@50     : {results.box.map50:.4f}")
    print(f"   mAP@50-95  : {results.box.map:.4f}")
    print(f"   Precision   : {results.box.mp:.4f}")
    print(f"   Recall      : {results.box.mr:.4f}")

    if cm_path.exists():
        print(f"\n✅ Confusion Matrix saved to:\n   {cm_path}")
    if cm_norm_path.exists():
        print(f"✅ Normalized Confusion Matrix saved to:\n   {cm_norm_path}")

    print(f"\n📁 All results in: {run_dir}")
    return run_dir


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  YOLOv11n Confusion Matrix Generator")
    print("  Model: CottonWeedDet12 (12 classes)")
    print("=" * 60)

    # Verify model exists
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model not found: {MODEL_PATH}")
        sys.exit(1)

    prepare_dataset()
    write_data_yaml()
    generate_confusion_matrix()
