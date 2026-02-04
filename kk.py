from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('runs/detect/train6/weights/best.pt')
    metrics = model.val(workers=0)
    
    print(metrics)
    print(f"\nPrecision: {metrics.box.p}")
    print(f"Recall: {metrics.box.r}")
