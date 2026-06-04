"""
╔══════════════════════════════════════════════════════════════════════╗
║   YOLOv8m — CottonWeedDet12 Training Script                        ║
║   Features:                                                         ║
║     • Loads pretrained weights from last.pt (epoch 68 knowledge)   ║
║     • Early stopping if mAP@50 doesn't improve for 30 epochs      ║
║     • Clears stale cache to fix broken validation                  ║
║     • Saves checkpoint every 5 epochs                              ║
║     • Post-training summary with target check                     ║
║   Run:  python train_yolov8m_cotton.py                              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import glob
import time
import multiprocessing

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
LAST_PT      = r"C:\dataset\cotton_runs\yolov8m_cotton_v1\weights\last.pt"
DATA_YAML    = r"C:\dataset\cotton_yolo_split\data.yaml"
RUNS_DIR     = r"C:\dataset\cotton_runs"
RUN_NAME     = "yolov8m_cotton_v1"
CACHE_DIR    = r"C:\dataset\cotton_yolo_split\labels"

EPOCHS       = 150
IMG_SIZE     = 640
PATIENCE     = 30        # stop if mAP doesn't improve for 30 epochs
TARGET_MAP50 = 0.85      # target accuracy
# ──────────────────────────────────────────────────────────────────────────────


def clear_cache():
    """Delete stale .cache files that cause NaN validation."""
    print("\n[1/3] 🗑️  Clearing stale cache files...")
    removed = 0
    for cache in glob.glob(os.path.join(CACHE_DIR, "*.cache")):
        os.remove(cache)
        print(f"      Deleted: {os.path.basename(cache)}")
        removed += 1
    if removed == 0:
        print("      No stale cache files found.")
    print("      Done.\n")


def detect_gpu():
    """Detect GPU and pick appropriate batch size."""
    import torch
    if not torch.cuda.is_available():
        print("  ⚠️  No CUDA GPU — training on CPU (very slow)")
        return "cpu", 4

    gpu  = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_mem / 1e9
    print(f"      GPU  : {gpu}")
    print(f"      VRAM : {vram:.1f} GB")

    if   vram >= 16: batch = 16
    elif vram >= 8:  batch = 8
    elif vram >= 6:  batch = 4
    elif vram >= 4:  batch = 2
    else:            batch = 1

    print(f"      Batch: {batch}")
    return 0, batch


def train():
    """Load last.pt weights and train with early stopping."""
    from ultralytics import YOLO

    print("[2/3] 🏋️  Starting training...")
    print(f"      Weights : {LAST_PT}")
    print(f"      Dataset : {DATA_YAML}")
    print(f"      Epochs  : {EPOCHS}")
    print(f"      Patience: {PATIENCE} (auto-stop if no improvement)")
    print(f"      Target  : mAP@50 ≥ {TARGET_MAP50}\n")

    if not os.path.exists(LAST_PT):
        print(f"  ❌ Not found: {LAST_PT}")
        print("     Run a fresh training first or check the path.")
        return None

    model = YOLO(LAST_PT)

    results = model.train(
        data        = DATA_YAML,
        project     = RUNS_DIR,
        name        = RUN_NAME,
        exist_ok    = True,

        # ── Core ──────────────────────────────────────────────────────────────
        epochs      = EPOCHS,
        imgsz       = IMG_SIZE,
        batch       = 2,
        device      = 0,
        workers     = 0,

        # ── Early stopping — STOPS if mAP doesn't improve ────────────────────
        patience    = PATIENCE,

        # ── Optimiser ─────────────────────────────────────────────────────────
        optimizer   = "AdamW",
        lr0         = 0.005,
        lrf         = 0.005,
        cos_lr      = True,
        warmup_epochs   = 0,
        momentum        = 0.937,
        weight_decay    = 0.0005,
        close_mosaic    = 10,

        # ── Augmentation ──────────────────────────────────────────────────────
        mosaic      = 1.0,
        mixup       = 0.1,
        copy_paste  = 0.1,
        fliplr      = 0.5,
        degrees     = 5.0,
        translate   = 0.1,
        scale       = 0.5,
        hsv_h       = 0.015,
        hsv_s       = 0.7,
        hsv_v       = 0.4,

        # ── Saving ────────────────────────────────────────────────────────────
        save        = True,
        save_period = 5,
        amp         = True,
        val         = True,
        plots       = True,
        verbose     = True,
    )

    return results


def post_training_report(results, elapsed_hours):
    """Show what happened after training ends."""
    print("\n" + "=" * 60)
    print("  📊 TRAINING COMPLETE — SUMMARY")
    print("=" * 60)
    print(f"  ⏱️  Time: {elapsed_hours:.2f} hours")

    save_dir = str(results.save_dir)
    best_pt  = os.path.join(save_dir, "weights", "best.pt")

    if os.path.exists(best_pt):
        # Run a quick val on best.pt to get final numbers
        from ultralytics import YOLO
        model = YOLO(best_pt)
        val_results = model.val(
            data    = DATA_YAML,
            imgsz   = IMG_SIZE,
            device  = 0,
            workers = 0,
            verbose = False,
        )
        map50   = float(val_results.box.map50)
        map5095 = float(val_results.box.map)
        prec    = float(val_results.box.mp)
        rec     = float(val_results.box.mr)

        print(f"\n  mAP@50     : {map50:.4f}  ({map50*100:.1f}%)")
        print(f"  mAP@50-95  : {map5095:.4f}  ({map5095*100:.1f}%)")
        print(f"  Precision  : {prec:.4f}  ({prec*100:.1f}%)")
        print(f"  Recall     : {rec:.4f}  ({rec*100:.1f}%)")

        if map50 >= TARGET_MAP50:
            print(f"\n  ✅ TARGET REACHED! mAP@50 = {map50:.4f} ≥ {TARGET_MAP50}")
            print(f"  🏆 Model is ready for deployment!")
        else:
            gap = TARGET_MAP50 - map50
            print(f"\n  ⚠️  Target: {TARGET_MAP50}  |  Gap: {gap:.4f}")
            print(f"  💡 You can run this script again to continue training.")

    print(f"\n  📁 Best weights : {best_pt}")
    print(f"  📁 Last weights : {os.path.join(save_dir, 'weights', 'last.pt')}")
    print(f"  📊 Results CSV  : {os.path.join(save_dir, 'results.csv')}")
    print("=" * 60 + "\n")


def main():
    print("=" * 60)
    print("  🌾 YOLOv8m — CottonWeedDet12 (12 classes)")
    print("=" * 60)

    # Step 1: Clear stale cache
    clear_cache()

    # Step 2: Train with early stopping
    t0 = time.time()
    results = train()
    elapsed = (time.time() - t0) / 3600

    # Step 3: Report
    if results is not None:
        post_training_report(results, elapsed)
    else:
        print("\n  ❌ Training did not start. Check errors above.")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
