"""
╔══════════════════════════════════════════════════════════════════╗
║        YOLOv8m — Local GPU Training Script (Windows/CUDA)        ║
║        Dataset  : CottonWeedDet12 (12 weed classes)              ║
║        Run with : python train_local.py                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import glob
import random
import shutil
import time
import yaml
import subprocess

# ─── Windows multiprocessing fix (MUST be before any imports of torch) ────────
if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

# ══════════════════════════════════════════════════════════════════════════════
#  ✏️  CONFIGURATION — Edit these paths to match your setup
# ══════════════════════════════════════════════════════════════════════════════
DATASET_ROOT  = r'C:\dataset\CottonWeedDet12'   # ← your dataset folder
OUTPUT_DIR    = r'C:\dataset\yolo_training'      # ← where split + results go
PROJECT_DIR   = r'C:\dataset\yolo_runs'          # ← where runs/weights saved
RUN_NAME      = 'yolov8m_weed_v1'

MODEL         = 'yolov8m.pt'    # yolov8n / yolov8s / yolov8m / yolov8l
EPOCHS        = 100
IMG_SIZE      = 640
TRAIN_SPLIT   = 0.8             # 80% train, 20% val
RANDOM_SEED   = 42

CLASS_NAMES = [
    'waterhemp', 'morningglory', 'ragweed', 'cocklebur',
    'spurred_anteria', 'prickly_sida', 'velvetleaf',
    'palmer_amaranth', 'redroot_pigweed', 'johnsongrass',
    'tall_morningglory', 'sicklepod'
]

# ══════════════════════════════════════════════════════════════════════════════

def check_gpu():
    """Detect GPU and set optimal batch size."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f'  ✅ GPU    : {gpu_name}')
            print(f'  ✅ VRAM   : {vram_gb:.1f} GB')
            print(f'  ✅ CUDA   : {torch.version.cuda}')

            # Auto batch size based on VRAM
            if vram_gb >= 16:
                batch = 32
            elif vram_gb >= 8:
                batch = 16
            elif vram_gb >= 6:
                batch = 8
            elif vram_gb >= 4:
                batch = 4
            else:
                batch = 2
            print(f'  ✅ Batch  : {batch} (auto-selected for {vram_gb:.0f}GB VRAM)')
            return 0, batch           # device=0 (GPU), batch
        else:
            print('  ⚠️  No GPU detected — training on CPU (very slow!)')
            print('     Make sure CUDA-enabled PyTorch is installed:')
            print('     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121')
            return 'cpu', 4
    except ImportError:
        print('  ❌ PyTorch not installed. Run: pip install torch torchvision ultralytics')
        sys.exit(1)


def prepare_dataset():
    """
    Reorganize CottonWeedDet12 into YOLO train/val structure.
    Skips if already done.
    """
    img_src = os.path.join(DATASET_ROOT, 'weedImages')
    lbl_src = os.path.join(DATASET_ROOT, 'annotation_YOLO_txt')

    train_img = os.path.join(OUTPUT_DIR, 'images', 'train')
    val_img   = os.path.join(OUTPUT_DIR, 'images', 'val')
    train_lbl = os.path.join(OUTPUT_DIR, 'labels', 'train')
    val_lbl   = os.path.join(OUTPUT_DIR, 'labels', 'val')

    # Check if already split
    existing = glob.glob(os.path.join(train_img, '*.jpg'))
    if existing:
        n_train = len(glob.glob(os.path.join(train_img, '*.jpg')))
        n_val   = len(glob.glob(os.path.join(val_img,   '*.jpg')))
        print(f'  ✅ Dataset already split: {n_train} train / {n_val} val — skipping.')
        return train_img, val_img

    # Validate source folders
    if not os.path.isdir(img_src):
        print(f'  ❌ Images folder not found: {img_src}')
        sys.exit(1)
    if not os.path.isdir(lbl_src):
        print(f'  ❌ Labels folder not found: {lbl_src}')
        sys.exit(1)

    # Gather all images
    all_imgs = sorted(
        glob.glob(os.path.join(img_src, '*.jpg'))  +
        glob.glob(os.path.join(img_src, '*.JPG'))  +
        glob.glob(os.path.join(img_src, '*.jpeg')) +
        glob.glob(os.path.join(img_src, '*.png'))
    )
    print(f'  🔍 Found {len(all_imgs)} images in weedImages/')

    # Match image ↔ label pairs
    paired, skipped = [], 0
    for img_path in all_imgs:
        stem     = os.path.splitext(os.path.basename(img_path))[0]
        lbl_path = os.path.join(lbl_src, stem + '.txt')
        if os.path.exists(lbl_path):
            paired.append((img_path, lbl_path))
        else:
            skipped += 1

    print(f'  📊 Matched pairs     : {len(paired)}')
    print(f'  📊 No label (skipped): {skipped}')

    if len(paired) == 0:
        print('  ❌ No matched pairs! Check filenames in weedImages/ and annotation_YOLO_txt/')
        sys.exit(1)

    # 80/20 split
    random.seed(RANDOM_SEED)
    random.shuffle(paired)
    split_idx   = int(len(paired) * TRAIN_SPLIT)
    train_pairs = paired[:split_idx]
    val_pairs   = paired[split_idx:]

    print(f'  📊 Train : {len(train_pairs)} | Val : {len(val_pairs)}')

    # Create output dirs
    for d in [train_img, val_img, train_lbl, val_lbl]:
        os.makedirs(d, exist_ok=True)

    # Copy files
    print('  ⏳ Copying into YOLO structure...')
    for i, (img, lbl) in enumerate(train_pairs):
        shutil.copy(img, os.path.join(train_img, os.path.basename(img)))
        shutil.copy(lbl, os.path.join(train_lbl, os.path.basename(lbl)))
        if (i + 1) % 500 == 0:
            print(f'     Train: {i+1}/{len(train_pairs)} copied...')

    for i, (img, lbl) in enumerate(val_pairs):
        shutil.copy(img, os.path.join(val_img, os.path.basename(img)))
        shutil.copy(lbl, os.path.join(val_lbl, os.path.basename(lbl)))
        if (i + 1) % 100 == 0:
            print(f'     Val  : {i+1}/{len(val_pairs)} copied...')

    print(f'  ✅ Dataset split complete!')
    return train_img, val_img


def create_yaml(train_img, val_img):
    """Write data.yaml for YOLO."""
    yaml_path = os.path.join(OUTPUT_DIR, 'data.yaml')
    data = {
        'path' : OUTPUT_DIR,
        'train': train_img,
        'val'  : val_img,
        'nc'   : len(CLASS_NAMES),
        'names': CLASS_NAMES,
    }
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    print(f'  ✅ data.yaml → {yaml_path}')
    return yaml_path


def train(yaml_path, device, batch):
    """Run YOLOv8 training."""
    from ultralytics import YOLO

    os.makedirs(PROJECT_DIR, exist_ok=True)

    # ── Training config ────────────────────────────────────────────────
    config = {
        'data'           : yaml_path,
        'project'        : PROJECT_DIR,
        'name'           : RUN_NAME,
        'exist_ok'       : True,

        # ── Core ──────────────────────────────────────────────────────
        'epochs'         : EPOCHS,
        'imgsz'          : IMG_SIZE,
        'batch'          : batch,
        'device'         : device,
        'workers'        : 0,        # ← MUST be 0 on Windows to avoid crashes

        # ── Learning Rate ──────────────────────────────────────────────
        'optimizer'      : 'AdamW',
        'lr0'            : 0.01,
        'lrf'            : 0.01,
        'cos_lr'         : True,
        'warmup_epochs'  : 3,
        'warmup_momentum': 0.8,
        'momentum'       : 0.937,
        'weight_decay'   : 0.0005,

        # ── Regularization ─────────────────────────────────────────────
        'dropout'        : 0.0,
        'label_smoothing': 0.1,

        # ── Augmentation ───────────────────────────────────────────────
        'mosaic'         : 1.0,
        'mixup'          : 0.15,
        'copy_paste'     : 0.2,
        'fliplr'         : 0.5,
        'flipud'         : 0.1,
        'degrees'        : 10.0,
        'translate'      : 0.1,
        'scale'          : 0.5,
        'hsv_h'          : 0.015,
        'hsv_s'          : 0.7,
        'hsv_v'          : 0.4,
        'erasing'        : 0.4,
        'close_mosaic'   : 10,

        # ── Speed & Memory ─────────────────────────────────────────────
        'amp'            : True,     # Mixed precision (faster + less VRAM)
        'cache'          : False,    # Set to True if you have 16+ GB RAM

        # ── Early Stopping & Output ────────────────────────────────────
        'patience'       : 30,       # More patient than Colab version
        'save'           : True,
        'save_period'    : 10,
        'plots'          : True,
        'val'            : True,
    }

    print('\n  📋 Training Configuration:')
    print(f'     Model   : {MODEL}')
    for k, v in config.items():
        print(f'     {k:<18}: {v}')

    model   = YOLO(MODEL)
    results = model.train(**config)
    return results


def main():
    print('=' * 65)
    print('  🌾 YOLOv8m LOCAL GPU TRAINING — Weed Detection (12 classes)')
    print('=' * 65)

    # 1. Check GPU
    print('\n[1/4] 🔍 Checking GPU...')
    device, batch = check_gpu()

    # 2. Check dependencies
    print('\n[2/4] 📦 Checking dependencies...')
    try:
        import ultralytics
        import torch
        print(f'  ✅ ultralytics : {ultralytics.__version__}')
        print(f'  ✅ torch       : {torch.__version__}')
    except ImportError as e:
        print(f'  ❌ Missing: {e}')
        print('  Install with: pip install ultralytics torch torchvision')
        sys.exit(1)

    # 3. Prepare dataset
    print('\n[3/4] 📂 Preparing dataset...')
    train_img, val_img = prepare_dataset()

    # 4. Create yaml
    yaml_path = create_yaml(train_img, val_img)

    # 5. Train
    print('\n[4/4] 🚀 Starting training...')
    print(f'  Estimated time: ~{EPOCHS * 25 / 3600:.1f} hours')
    start = time.time()

    results = train(yaml_path, device, batch)

    elapsed = (time.time() - start) / 3600
    save_dir = results.save_dir

    print('\n' + '=' * 65)
    print('  ✅ TRAINING COMPLETE!')
    print('=' * 65)
    print(f'  ⏱️  Time          : {elapsed:.2f} hours')
    print(f'  📁 Best weights  : {save_dir}\\weights\\best.pt')
    print(f'  📁 Last weights  : {save_dir}\\weights\\last.pt')
    print(f'  📊 Results       : {save_dir}\\results.csv')
    print(f'  📈 Plots         : {save_dir}\\')
    print('=' * 65)
    print('\n  Usage after training:')
    print('  from ultralytics import YOLO')
    print(f'  model = YOLO(r"{save_dir}\\weights\\best.pt")')
    print('  results = model.predict("image.jpg", conf=0.25)')


if __name__ == '__main__':
    main()
