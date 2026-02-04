"""
uptrain_yolo.py
Fine-tunes existing weed detection model with merged weed+crop dataset
"""
from ultralytics import YOLO
import os

# ============ CONFIGURATION ============
# Your existing best model weights
EXISTING_MODEL = "runs/detect/train6/weights/best.pt"

# Merged dataset config
DATA_YAML = "C:/dataset/merged_weed_crop_dataset/data.yaml"

# Training parameters
EPOCHS = 30
BATCH_SIZE = 8
IMAGE_SIZE = 640
DEVICE = 0  # GPU
# =======================================

def uptrain():
    print("=" * 60)
    print("  YOLO MODEL UPTRAINING - Weeds + Crops")
    print("=" * 60)
    
    # Check paths
    if not os.path.exists(EXISTING_MODEL):
        print(f"❌ Model not found: {EXISTING_MODEL}")
        print("   Using pretrained yolov8n.pt instead...")
        model_path = "yolov8n.pt"
    else:
        model_path = EXISTING_MODEL
        print(f"✅ Loading existing model: {model_path}")
    
    if not os.path.exists(DATA_YAML):
        print(f"❌ Data config not found: {DATA_YAML}")
        print("   Run merge_datasets.py first!")
        return
    
    # Load model
    model = YOLO(model_path)
    
    print(f"\n🚀 Starting uptraining...")
    print(f"   Dataset: {DATA_YAML}")
    print(f"   Epochs: {EPOCHS}")
    print(f"   Batch size: {BATCH_SIZE}")
    
    # Fine-tune with lower learning rate
    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        device=DEVICE,
        
        # Lower learning rate for fine-tuning
        lr0=0.001,
        lrf=0.001,
        
        # Freeze early layers to preserve learned weed features
        # Set to 0 to train all layers (may be better for adding new classes)
        freeze=0,
        
        # Patience for early stopping
        patience=10,
        
        # Augmentations (same as original training)
        mosaic=0.7,
        mixup=0.15,
        copy_paste=0.05,
        fliplr=0.4,
        degrees=10,
        hsv_h=0.012,
        hsv_s=0.6,
        hsv_v=0.3,
        
        # Project naming
        name="uptrain_weed_crops",
        
        # Other settings
        workers=0,
        warmup_epochs=2,
        close_mosaic=8,
    )
    
    print("\n" + "=" * 60)
    print("  🎉 UPTRAINING COMPLETE!")
    print("=" * 60)
    print(f"\n📁 Best weights saved to: {results.save_dir}/weights/best.pt")
    print(f"\nTo use the new model in your app:")
    print(f'  model = YOLO("{results.save_dir}/weights/best.pt")')
    
    return results

if __name__ == "__main__":
    uptrain()
