"""
╔══════════════════════════════════════════════════════════════════════╗
║   YOLOv8m — Pre-Training Validation Script                         ║
║   Checks ALL parameters before training to prevent wasted time     ║
║                                                                     ║
║   Validates:                                                        ║
║     1. Python & package versions                                    ║
║     2. GPU / CUDA / AMP compatibility                               ║
║     3. Dataset YAML configuration                                   ║
║     4. Image files (existence, readability, formats)                ║
║     5. Label files (format, class IDs, bounding boxes)              ║
║     6. Image ↔ Label pairing                                        ║
║     7. Class distribution & balance                                 ║
║     8. Model weights integrity                                      ║
║     9. Training hyperparameters sanity check                        ║
║    10. Disk space                                                    ║
║                                                                     ║
║   Run:  python validate_training_setup.py                            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import glob
import time
import yaml
import math
import struct
import platform
import shutil
from pathlib import Path
from collections import Counter, defaultdict

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION — Must match your training script
# ──────────────────────────────────────────────────────────────────────────────
WEIGHTS_PT   = r"C:\dataset\cotton_runs\yolov8m_cotton_v1\weights\last.pt"
DATA_YAML    = r"C:\dataset\cotton_yolo_split\data.yaml"
RUNS_DIR     = r"C:\dataset\cotton_runs"
EPOCHS       = 150
IMG_SIZE     = 640
BATCH_SIZE   = 2
LR0          = 0.005
AMP_ENABLED  = True       # What you plan to use in training
PATIENCE     = 30
WORKERS      = 0
# ──────────────────────────────────────────────────────────────────────────────

# Counters
PASS = 0
WARN = 0
FAIL = 0
CHECKS = []


def header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check_pass(msg):
    global PASS
    PASS += 1
    CHECKS.append(("✅ PASS", msg))
    print(f"  ✅ PASS : {msg}")


def check_warn(msg):
    global WARN
    WARN += 1
    CHECKS.append(("⚠️  WARN", msg))
    print(f"  ⚠️  WARN : {msg}")


def check_fail(msg):
    global FAIL
    FAIL += 1
    CHECKS.append(("❌ FAIL", msg))
    print(f"  ❌ FAIL : {msg}")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 1: Python & Package Versions
# ══════════════════════════════════════════════════════════════════════════════
def check_python_packages():
    header("1/10  PYTHON & PACKAGE VERSIONS")

    # Python version
    py_ver = platform.python_version()
    major, minor = sys.version_info[:2]
    print(f"  Python: {py_ver}")
    if major == 3 and minor >= 8:
        check_pass(f"Python {py_ver} is supported")
    else:
        check_fail(f"Python {py_ver} — need 3.8+")

    # PyTorch
    try:
        import torch
        print(f"  PyTorch: {torch.__version__}")
        check_pass(f"PyTorch {torch.__version__} installed")
    except ImportError:
        check_fail("PyTorch is NOT installed")
        return

    # Ultralytics
    try:
        import ultralytics
        print(f"  Ultralytics: {ultralytics.__version__}")
        check_pass(f"Ultralytics {ultralytics.__version__} installed")
    except ImportError:
        check_fail("Ultralytics (YOLOv8) is NOT installed — pip install ultralytics")

    # OpenCV
    try:
        import cv2
        print(f"  OpenCV: {cv2.__version__}")
        check_pass(f"OpenCV {cv2.__version__} installed")
    except ImportError:
        check_warn("OpenCV not found — some augmentations may fail")

    # NumPy
    try:
        import numpy as np
        print(f"  NumPy: {np.__version__}")
        check_pass(f"NumPy {np.__version__} installed")
    except ImportError:
        check_fail("NumPy not installed")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 2: GPU / CUDA / AMP
# ══════════════════════════════════════════════════════════════════════════════
def check_gpu():
    header("2/10  GPU / CUDA / AMP COMPATIBILITY")

    try:
        import torch
    except ImportError:
        check_fail("Cannot check GPU — PyTorch not installed")
        return

    # CUDA availability
    if not torch.cuda.is_available():
        check_fail("CUDA is NOT available — training will be extremely slow on CPU")
        return

    check_pass(f"CUDA is available (version {torch.version.cuda})")

    # GPU details
    gpu_name = torch.cuda.get_device_name(0)
    props = torch.cuda.get_device_properties(0)
    vram_gb = getattr(props, 'total_memory', getattr(props, 'total_mem', 0)) / (1024 ** 3)
    compute_cap = f"{props.major}.{props.minor}"

    print(f"  GPU Name      : {gpu_name}")
    print(f"  VRAM          : {vram_gb:.1f} GB")
    print(f"  Compute Cap.  : {compute_cap}")
    print(f"  CUDA Cores    : (see GPU specs)")

    # VRAM check for batch size
    estimated_vram = BATCH_SIZE * 0.5 + 1.0  # rough: ~0.5GB per batch + overhead
    if vram_gb >= estimated_vram:
        check_pass(f"VRAM {vram_gb:.1f} GB likely sufficient for batch={BATCH_SIZE}")
    else:
        check_warn(f"VRAM {vram_gb:.1f} GB may be tight for batch={BATCH_SIZE}")

    # AMP compatibility
    # GTX 16xx series (Turing without tensor cores) are known to have AMP issues
    amp_problem_gpus = ["GTX 1650", "GTX 1660", "GTX 1630", "MX"]
    has_amp_issue = any(g in gpu_name for g in amp_problem_gpus)

    if has_amp_issue and AMP_ENABLED:
        check_fail(
            f"AMP is ENABLED but {gpu_name} has known AMP issues!\n"
            f"           → This causes NaN validation losses and zero mAP.\n"
            f"           → Set amp=False in your training script."
        )
    elif has_amp_issue and not AMP_ENABLED:
        check_pass(f"AMP correctly disabled for {gpu_name}")
    elif not has_amp_issue and AMP_ENABLED:
        check_pass(f"AMP enabled — {gpu_name} supports FP16 training")
    else:
        check_pass(f"AMP disabled (not needed for {gpu_name})")

    # Compute capability check
    if props.major >= 7:
        check_pass(f"Compute capability {compute_cap} — supports tensor cores")
    elif props.major >= 6:
        check_warn(f"Compute capability {compute_cap} — no tensor cores, AMP may not help")
    else:
        check_fail(f"Compute capability {compute_cap} is very old — consider upgrading GPU")

    # Test actual FP16 computation
    print("\n  Running FP16 sanity test...")
    try:
        x = torch.randn(2, 3, 64, 64, device="cuda", dtype=torch.float16)
        conv = torch.nn.Conv2d(3, 16, 3, padding=1).cuda().half()
        y = conv(x)
        if torch.isnan(y).any() or torch.isinf(y).any():
            check_fail("FP16 computation produced NaN/Inf — disable AMP!")
        else:
            check_pass("FP16 basic computation works correctly")
    except Exception as e:
        check_warn(f"FP16 test failed: {e}")

    # Test AMP autocast
    if AMP_ENABLED:
        print("  Running AMP autocast test...")
        try:
            x = torch.randn(2, 3, 64, 64, device="cuda")
            conv = torch.nn.Conv2d(3, 16, 3, padding=1).cuda()
            with torch.amp.autocast("cuda"):
                y = conv(x)
            if torch.isnan(y).any() or torch.isinf(y).any():
                check_fail("AMP autocast produced NaN/Inf — disable AMP!")
            else:
                check_pass("AMP autocast test passed")
        except Exception as e:
            check_fail(f"AMP autocast test failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 3: Dataset YAML
# ══════════════════════════════════════════════════════════════════════════════
def check_data_yaml():
    header("3/10  DATASET YAML CONFIGURATION")

    if not os.path.exists(DATA_YAML):
        check_fail(f"data.yaml not found: {DATA_YAML}")
        return None

    check_pass(f"data.yaml found: {DATA_YAML}")

    with open(DATA_YAML, 'r') as f:
        data = yaml.safe_load(f)

    # Required keys
    required_keys = ['names', 'nc', 'train', 'val']
    for key in required_keys:
        if key in data:
            check_pass(f"Key '{key}' present in data.yaml")
        else:
            check_fail(f"Key '{key}' MISSING from data.yaml")

    # nc vs names consistency
    if 'nc' in data and 'names' in data:
        nc = data['nc']
        n_names = len(data['names'])
        if nc == n_names:
            check_pass(f"nc={nc} matches {n_names} class names")
        else:
            check_fail(f"nc={nc} but {n_names} class names — MISMATCH!")

        print(f"\n  Classes ({nc}):")
        for i, name in enumerate(data['names']):
            print(f"    {i}: {name}")

    # Path checks
    for split in ['train', 'val']:
        if split in data:
            path = data[split]
            if os.path.isdir(path):
                n_files = len(os.listdir(path))
                check_pass(f"{split} path exists: {path} ({n_files} files)")
            else:
                check_fail(f"{split} path NOT found: {path}")

    return data


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 4: Image Files
# ══════════════════════════════════════════════════════════════════════════════
def check_images(data):
    header("4/10  IMAGE FILES")

    if data is None:
        check_fail("Skipping — data.yaml could not be loaded")
        return

    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}
    results = {}

    for split in ['train', 'val']:
        if split not in data:
            continue

        img_dir = data[split]
        if not os.path.isdir(img_dir):
            check_fail(f"{split} image directory not found")
            continue

        all_files = os.listdir(img_dir)
        img_files = [f for f in all_files if Path(f).suffix.lower() in valid_exts]
        non_img = [f for f in all_files if Path(f).suffix.lower() not in valid_exts and not f.endswith('.cache')]

        print(f"\n  [{split.upper()}] {img_dir}")
        print(f"    Total files     : {len(all_files)}")
        print(f"    Image files     : {len(img_files)}")

        if len(img_files) == 0:
            check_fail(f"{split}: No image files found!")
            continue
        else:
            check_pass(f"{split}: {len(img_files)} images found")

        if non_img:
            check_warn(f"{split}: {len(non_img)} non-image files: {non_img[:5]}")

        # Check a sample of images for readability
        try:
            import cv2
            sample = img_files[:20]
            corrupt = 0
            for fname in sample:
                fpath = os.path.join(img_dir, fname)
                img = cv2.imread(fpath)
                if img is None:
                    corrupt += 1
                    print(f"    ❌ Unreadable: {fname}")

            if corrupt == 0:
                check_pass(f"{split}: Sample of {len(sample)} images all readable")
            else:
                check_fail(f"{split}: {corrupt}/{len(sample)} sampled images are CORRUPT")
        except ImportError:
            check_warn(f"{split}: OpenCV not available — skipping image readability check")

        # Extension distribution
        ext_counts = Counter(Path(f).suffix.lower() for f in img_files)
        print(f"    Extensions      : {dict(ext_counts)}")

        # Image size check (sample)
        try:
            import cv2
            sizes = set()
            for fname in img_files[:10]:
                fpath = os.path.join(img_dir, fname)
                img = cv2.imread(fpath)
                if img is not None:
                    sizes.add(img.shape[:2])
            print(f"    Sample sizes (H×W): {sizes}")
            if len(sizes) > 1:
                check_warn(f"{split}: Multiple image sizes found — YOLO will resize to {IMG_SIZE}")
            else:
                check_pass(f"{split}: Consistent image sizes")
        except ImportError:
            pass

        results[split] = img_files

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 5: Label Files
# ══════════════════════════════════════════════════════════════════════════════
def check_labels(data):
    header("5/10  LABEL FILES (FORMAT & VALIDITY)")

    if data is None:
        check_fail("Skipping — data.yaml could not be loaded")
        return

    nc = data.get('nc', 0)
    results = {}

    for split in ['train', 'val']:
        if split not in data:
            continue

        img_dir = data[split]
        # Labels should be in a parallel 'labels' directory
        label_dir = img_dir.replace('images', 'labels')

        print(f"\n  [{split.upper()}] {label_dir}")

        if not os.path.isdir(label_dir):
            check_fail(f"{split}: Label directory NOT found: {label_dir}")
            continue

        label_files = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
        print(f"    Label files: {len(label_files)}")

        if len(label_files) == 0:
            check_fail(f"{split}: No .txt label files found!")
            continue

        check_pass(f"{split}: {len(label_files)} label files found")

        # Validate label contents
        total_boxes = 0
        empty_labels = 0
        invalid_format = 0
        invalid_class = 0
        invalid_bbox = 0
        class_counts = Counter()
        bad_files = []

        for lbl_file in label_files:
            lbl_path = os.path.join(label_dir, lbl_file)
            try:
                with open(lbl_path, 'r') as f:
                    lines = f.readlines()

                if len(lines) == 0:
                    empty_labels += 1
                    continue

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split()
                    if len(parts) != 5:
                        invalid_format += 1
                        if len(bad_files) < 5:
                            bad_files.append(f"{lbl_file}:L{line_num} ({len(parts)} values)")
                        continue

                    try:
                        cls_id = int(parts[0])
                        x_c, y_c, w, h = [float(p) for p in parts[1:]]
                    except ValueError:
                        invalid_format += 1
                        continue

                    # Class ID check
                    if cls_id < 0 or cls_id >= nc:
                        invalid_class += 1
                        if len(bad_files) < 5:
                            bad_files.append(f"{lbl_file}: class {cls_id} out of range [0, {nc-1}]")
                    else:
                        class_counts[cls_id] += 1

                    # Bbox check (YOLO format: all values should be 0-1)
                    if not (0 <= x_c <= 1 and 0 <= y_c <= 1 and 0 < w <= 1 and 0 < h <= 1):
                        invalid_bbox += 1
                        if len(bad_files) < 5:
                            bad_files.append(f"{lbl_file}: bbox out of range ({x_c},{y_c},{w},{h})")

                    total_boxes += 1

            except Exception as e:
                invalid_format += 1
                if len(bad_files) < 5:
                    bad_files.append(f"{lbl_file}: {str(e)}")

        print(f"    Total bounding boxes : {total_boxes}")
        print(f"    Empty label files    : {empty_labels}")
        print(f"    Invalid format lines : {invalid_format}")
        print(f"    Invalid class IDs    : {invalid_class}")
        print(f"    Invalid bboxes       : {invalid_bbox}")

        if invalid_format > 0:
            check_fail(f"{split}: {invalid_format} lines with invalid format")
        else:
            check_pass(f"{split}: All label lines have valid YOLO format (cls x y w h)")

        if invalid_class > 0:
            check_fail(f"{split}: {invalid_class} annotations with class ID outside [0, {nc-1}]")
        else:
            check_pass(f"{split}: All class IDs valid [0, {nc-1}]")

        if invalid_bbox > 0:
            check_fail(f"{split}: {invalid_bbox} bounding boxes with values outside [0, 1]")
        else:
            check_pass(f"{split}: All bounding box coordinates within [0, 1]")

        if bad_files:
            print(f"    Sample issues:")
            for bf in bad_files:
                print(f"      → {bf}")

        # Class distribution
        if class_counts:
            print(f"\n    Class distribution:")
            names = data.get('names', [])
            for cls_id in sorted(class_counts.keys()):
                name = names[cls_id] if cls_id < len(names) else f"class_{cls_id}"
                count = class_counts[cls_id]
                bar = "█" * min(count // 50, 40)
                print(f"      {cls_id:2d} {name:20s} : {count:5d}  {bar}")

        results[split] = {
            'label_dir': label_dir,
            'label_files': label_files,
            'total_boxes': total_boxes,
            'class_counts': class_counts
        }

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 6: Image ↔ Label Pairing
# ══════════════════════════════════════════════════════════════════════════════
def check_pairing(data):
    header("6/10  IMAGE ↔ LABEL PAIRING")

    if data is None:
        check_fail("Skipping — data.yaml could not be loaded")
        return

    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}

    for split in ['train', 'val']:
        if split not in data:
            continue

        img_dir = data[split]
        label_dir = img_dir.replace('images', 'labels')

        if not os.path.isdir(img_dir) or not os.path.isdir(label_dir):
            check_fail(f"{split}: Cannot check pairing — directories missing")
            continue

        img_stems = {Path(f).stem for f in os.listdir(img_dir)
                     if Path(f).suffix.lower() in valid_exts}
        lbl_stems = {Path(f).stem for f in os.listdir(label_dir)
                     if f.endswith('.txt')}

        imgs_without_labels = img_stems - lbl_stems
        labels_without_imgs = lbl_stems - img_stems
        matched = img_stems & lbl_stems

        print(f"\n  [{split.upper()}]")
        print(f"    Images         : {len(img_stems)}")
        print(f"    Labels         : {len(lbl_stems)}")
        print(f"    Matched pairs  : {len(matched)}")
        print(f"    Images w/o lbl : {len(imgs_without_labels)}")
        print(f"    Labels w/o img : {len(labels_without_imgs)}")

        if len(matched) == 0:
            check_fail(f"{split}: NO image-label pairs matched! Check naming.")
        elif len(matched) == len(img_stems):
            check_pass(f"{split}: All {len(matched)} images have matching labels")
        else:
            pct = len(matched) / len(img_stems) * 100
            if pct >= 95:
                check_warn(f"{split}: {pct:.1f}% matched — {len(imgs_without_labels)} images missing labels")
            else:
                check_fail(f"{split}: Only {pct:.1f}% matched — major pairing issue!")

        if labels_without_imgs:
            check_warn(f"{split}: {len(labels_without_imgs)} orphan labels (no matching image)")
            for lbl in list(labels_without_imgs)[:3]:
                print(f"      → {lbl}")

        if imgs_without_labels:
            sample = list(imgs_without_labels)[:3]
            for img in sample:
                print(f"      → Missing label for: {img}")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 7: Class Distribution & Balance
# ══════════════════════════════════════════════════════════════════════════════
def check_class_balance(data):
    header("7/10  CLASS DISTRIBUTION & BALANCE")

    if data is None:
        check_fail("Skipping — data.yaml could not be loaded")
        return

    nc = data.get('nc', 0)
    names = data.get('names', [])

    # Read labels from train split
    img_dir = data.get('train', '')
    label_dir = img_dir.replace('images', 'labels')

    if not os.path.isdir(label_dir):
        check_fail("Train labels directory not found")
        return

    class_counts = Counter()
    for lbl_file in os.listdir(label_dir):
        if not lbl_file.endswith('.txt'):
            continue
        with open(os.path.join(label_dir, lbl_file), 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 1:
                    try:
                        cls_id = int(parts[0])
                        class_counts[cls_id] += 1
                    except ValueError:
                        pass

    if not class_counts:
        check_fail("No annotations found in training labels")
        return

    total = sum(class_counts.values())
    max_count = max(class_counts.values())
    min_count = min(class_counts.values()) if class_counts else 0
    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')

    print(f"  Total annotations : {total}")
    print(f"  Max class count   : {max_count}")
    print(f"  Min class count   : {min_count}")
    print(f"  Imbalance ratio   : {imbalance_ratio:.1f}x")

    # Check for missing classes
    missing_classes = [i for i in range(nc) if i not in class_counts]
    if missing_classes:
        missing_names = [names[i] if i < len(names) else f"class_{i}" for i in missing_classes]
        check_fail(f"Missing classes in training data: {missing_names}")
    else:
        check_pass(f"All {nc} classes present in training data")

    if imbalance_ratio > 20:
        check_warn(f"Severe class imbalance ({imbalance_ratio:.1f}x) — consider oversampling minority classes")
    elif imbalance_ratio > 5:
        check_warn(f"Moderate class imbalance ({imbalance_ratio:.1f}x) — may affect smaller classes")
    else:
        check_pass(f"Class balance acceptable (ratio: {imbalance_ratio:.1f}x)")

    # Annotations per image
    n_label_files = len([f for f in os.listdir(label_dir) if f.endswith('.txt')])
    avg_boxes = total / n_label_files if n_label_files > 0 else 0
    print(f"  Avg boxes/image   : {avg_boxes:.2f}")

    if avg_boxes < 1:
        check_warn("Very few annotations per image — model may struggle to learn")
    else:
        check_pass(f"Average {avg_boxes:.2f} annotations per image")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 8: Model Weights
# ══════════════════════════════════════════════════════════════════════════════
def check_weights():
    header("8/10  MODEL WEIGHTS INTEGRITY")

    if not os.path.exists(WEIGHTS_PT):
        check_fail(f"Weights not found: {WEIGHTS_PT}")
        return

    file_size = os.path.getsize(WEIGHTS_PT)
    print(f"  Weights file : {WEIGHTS_PT}")
    print(f"  File size    : {file_size / (1024**2):.1f} MB")

    if file_size < 1_000_000:  # < 1MB
        check_fail("Weights file is suspiciously small — may be corrupt")
        return
    else:
        check_pass(f"Weights file size OK ({file_size / (1024**2):.1f} MB)")

    # Try to load the model
    try:
        import torch
        from ultralytics import YOLO

        print("  Loading model...")
        model = YOLO(WEIGHTS_PT)
        check_pass("Model loaded successfully")

        # Check model type
        task = getattr(model, 'task', 'unknown')
        print(f"  Model task   : {task}")

        # Check number of classes in model
        if hasattr(model, 'model') and hasattr(model.model, 'nc'):
            model_nc = model.model.nc
            print(f"  Model classes: {model_nc}")

            # Load data yaml to compare
            with open(DATA_YAML, 'r') as f:
                data = yaml.safe_load(f)
            data_nc = data.get('nc', 0)

            if model_nc == data_nc:
                check_pass(f"Model nc={model_nc} matches data.yaml nc={data_nc}")
            else:
                check_fail(f"Model nc={model_nc} ≠ data.yaml nc={data_nc} — CLASS MISMATCH!")

        # Check for NaN/Inf in weights
        print("  Checking weights for NaN/Inf values...")
        nan_count = 0
        inf_count = 0
        total_params = 0
        for name, param in model.model.named_parameters():
            total_params += param.numel()
            nan_count += torch.isnan(param.data).sum().item()
            inf_count += torch.isinf(param.data).sum().item()

        print(f"  Total parameters : {total_params:,}")
        print(f"  NaN parameters   : {nan_count:,}")
        print(f"  Inf parameters   : {inf_count:,}")

        if nan_count > 0:
            check_fail(f"Model has {nan_count:,} NaN parameters — weights are CORRUPTED!")
        elif inf_count > 0:
            check_fail(f"Model has {inf_count:,} Inf parameters — weights are CORRUPTED!")
        else:
            check_pass("All model parameters are finite (no NaN/Inf)")

        # Quick inference test
        print("  Running inference test...")
        try:
            dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE).to(
                next(model.model.parameters()).device
            )
            with torch.no_grad():
                output = model.model(dummy)
            # Check output for NaN
            has_nan = False
            if isinstance(output, (list, tuple)):
                for o in output:
                    if isinstance(o, torch.Tensor) and torch.isnan(o).any():
                        has_nan = True
            elif isinstance(output, torch.Tensor):
                has_nan = torch.isnan(output).any()

            if has_nan:
                check_fail("Model produces NaN output — weights are CORRUPTED from AMP!")
            else:
                check_pass("Model inference test passed — output is clean")
        except Exception as e:
            check_warn(f"Inference test failed: {e}")

        # Check training epoch
        try:
            ckpt = torch.load(WEIGHTS_PT, map_location='cpu', weights_only=False)
            if 'epoch' in ckpt:
                print(f"  Checkpoint epoch : {ckpt['epoch']}")
                check_pass(f"Checkpoint from epoch {ckpt['epoch']}")
            if 'best_fitness' in ckpt:
                print(f"  Best fitness     : {ckpt['best_fitness']}")
                if ckpt['best_fitness'] == 0:
                    check_warn("Best fitness is 0 — model never achieved any mAP")
        except Exception as e:
            check_warn(f"Could not inspect checkpoint details: {e}")

    except Exception as e:
        check_fail(f"Failed to load model: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 9: Training Hyperparameters
# ══════════════════════════════════════════════════════════════════════════════
def check_hyperparams():
    header("9/10  TRAINING HYPERPARAMETERS")

    print(f"  Epochs       : {EPOCHS}")
    print(f"  Image size   : {IMG_SIZE}")
    print(f"  Batch size   : {BATCH_SIZE}")
    print(f"  Learning rate: {LR0}")
    print(f"  AMP          : {AMP_ENABLED}")
    print(f"  Patience     : {PATIENCE}")
    print(f"  Workers      : {WORKERS}")

    # Learning rate
    if LR0 > 0.01:
        check_warn(f"lr0={LR0} is very high — risk of unstable training")
    elif LR0 > 0.005:
        check_warn(f"lr0={LR0} is high for fine-tuning — consider 0.001 or lower")
    elif LR0 >= 0.0001:
        check_pass(f"lr0={LR0} is reasonable")
    else:
        check_warn(f"lr0={LR0} is very low — training may be too slow")

    # Batch size
    if BATCH_SIZE < 2:
        check_warn(f"batch={BATCH_SIZE} is very small — gradients will be noisy")
    elif BATCH_SIZE >= 2:
        check_pass(f"batch={BATCH_SIZE} is acceptable")

    # Patience
    if PATIENCE < 10:
        check_warn(f"patience={PATIENCE} is low — may stop too early")
    elif PATIENCE > 50:
        check_warn(f"patience={PATIENCE} is high — may waste time on a stuck model")
    else:
        check_pass(f"patience={PATIENCE} is reasonable")

    # Workers on Windows
    if platform.system() == 'Windows' and WORKERS > 0:
        check_warn(f"workers={WORKERS} on Windows may cause multiprocessing issues — use 0")
    elif WORKERS == 0:
        check_pass(f"workers={WORKERS} — safe for Windows")

    # Epochs
    if EPOCHS > 300:
        check_warn(f"epochs={EPOCHS} is very high — consider using early stopping")
    else:
        check_pass(f"epochs={EPOCHS} with patience={PATIENCE} early stopping")


# ══════════════════════════════════════════════════════════════════════════════
#  CHECK 10: Disk Space & Stale Cache
# ══════════════════════════════════════════════════════════════════════════════
def check_disk():
    header("10/10  DISK SPACE & STALE CACHE")

    # Disk space
    drive = os.path.splitdrive(RUNS_DIR)[0] or "C:"
    try:
        total, used, free = shutil.disk_usage(drive + "\\")
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        print(f"  Drive {drive}")
        print(f"    Total : {total_gb:.1f} GB")
        print(f"    Free  : {free_gb:.1f} GB")

        if free_gb < 5:
            check_fail(f"Only {free_gb:.1f} GB free — training may fail!")
        elif free_gb < 20:
            check_warn(f"{free_gb:.1f} GB free — may run low during training")
        else:
            check_pass(f"{free_gb:.1f} GB free disk space")
    except Exception as e:
        check_warn(f"Could not check disk space: {e}")

    # Stale cache files
    with open(DATA_YAML, 'r') as f:
        data = yaml.safe_load(f)

    cache_found = False
    for split in ['train', 'val']:
        if split not in data:
            continue
        img_dir = data[split]
        label_dir = img_dir.replace('images', 'labels')

        for cache_dir in [img_dir, label_dir]:
            caches = glob.glob(os.path.join(cache_dir, '*.cache'))
            if caches:
                cache_found = True
                for c in caches:
                    size = os.path.getsize(c)
                    print(f"  ⚠️  Stale cache: {c} ({size / 1024:.0f} KB)")

    if cache_found:
        check_warn("Stale .cache files found — delete before training to avoid issues")
    else:
        check_pass("No stale .cache files found")

    # Check runs directory
    if os.path.isdir(RUNS_DIR):
        check_pass(f"Runs directory exists: {RUNS_DIR}")
    else:
        check_warn(f"Runs directory will be created: {RUNS_DIR}")

    # Check for existing results that might indicate corrupted state
    results_csv = os.path.join(RUNS_DIR, "yolov8m_cotton_v1", "results.csv")
    if os.path.exists(results_csv):
        print(f"\n  Checking existing results.csv...")
        try:
            with open(results_csv, 'r') as f:
                lines = f.readlines()
            if len(lines) > 1:
                last_line = lines[-1].strip() if lines[-1].strip() else lines[-2].strip()
                values = last_line.split(',')
                # Check if val losses are NaN
                if 'nan' in last_line.lower():
                    check_fail("Existing results.csv contains NaN values — previous training was corrupted!")
                else:
                    check_pass("Existing results.csv looks clean")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
def print_summary():
    header("VALIDATION SUMMARY")

    print(f"\n  ✅ Passed : {PASS}")
    print(f"  ⚠️  Warnings: {WARN}")
    print(f"  ❌ Failed : {FAIL}")
    print()

    if FAIL > 0:
        print("  ┌─────────────────────────────────────────────────────────────┐")
        print("  │  🚫 TRAINING NOT RECOMMENDED — Fix the failures first!     │")
        print("  └─────────────────────────────────────────────────────────────┘")
        print("\n  Failed checks:")
        for status, msg in CHECKS:
            if "FAIL" in status:
                print(f"    {status}: {msg}")
    elif WARN > 0:
        print("  ┌─────────────────────────────────────────────────────────────┐")
        print("  │  ⚠️  PROCEED WITH CAUTION — Review warnings above           │")
        print("  └─────────────────────────────────────────────────────────────┘")
    else:
        print("  ┌─────────────────────────────────────────────────────────────┐")
        print("  │  ✅ ALL CHECKS PASSED — Safe to start training!             │")
        print("  └─────────────────────────────────────────────────────────────┘")

    print()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  🔍 YOLOv8m — Pre-Training Validation")
    print(f"  📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Run all checks
    check_python_packages()
    check_gpu()
    data = check_data_yaml()
    check_images(data)
    check_labels(data)
    check_pairing(data)
    check_class_balance(data)
    check_weights()
    check_hyperparams()
    check_disk()
    print_summary()


if __name__ == "__main__":
    main()
