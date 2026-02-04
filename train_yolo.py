from ultralytics import YOLO

model = YOLO("yolov8n.pt")
# model = YOLO("yolov8s.pt")  # Use later for higher accuracy

results = model.train(
    data="data.yaml",
    device=0,              # 🔥 GPU enabled
    epochs=40,             # Faster training but still good accuracy
    imgsz=640,
    batch=8,               # stable batch for 4GB VRAM
    workers=0,             # speeds up loading

    # SPEED + Stability Optimized
    patience=8,            # early stop if no improvement
    warmup_epochs=2,
    close_mosaic=8,        # disable mosaic near end (prevents overfitting)

    # Light augmentations (faster than your previous ones)
    mosaic=0.7,
    mixup=0.15,
    copy_paste=0.05,
    fliplr=0.4,
    degrees=10,
    hsv_h=0.012,
    hsv_s=0.6,
    hsv_v=0.3,
)

print("\n🎉 Training Finished!")
print(f"📁 Best weights: {results.save_dir}/weights/best.pt")
