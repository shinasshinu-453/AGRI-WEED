import os
import shutil
from pathlib import Path
import random

dataset_path = r"C:\dataset\CottonWeedDet12"
images_folder = os.path.join(dataset_path, "weedImages")
labels_folder = os.path.join(dataset_path, "annotation_YOLO_txt")

output_dir = r"C:\dataset\wheat_yolo_dataset"

os.makedirs(os.path.join(output_dir, "images", "train"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "images", "val"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "labels", "train"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "labels", "val"), exist_ok=True)

image_files = [f for f in os.listdir(images_folder) if f.endswith(('.jpg', '.png'))]
random.shuffle(image_files)

split_ratio = 0.8
train_count = int(len(image_files) * split_ratio)

train_images = image_files[:train_count]
val_images = image_files[train_count:]

print(f"Total images: {len(image_files)}")
print(f"Train: {len(train_images)}, Val: {len(val_images)}")

for img_file in train_images:
    src = os.path.join(images_folder, img_file)
    dst = os.path.join(output_dir, "images", "train", img_file)
    shutil.copy(src, dst)
    
    label_file = os.path.splitext(img_file)[0] + ".txt"
    src_label = os.path.join(labels_folder, label_file)
    dst_label = os.path.join(output_dir, "labels", "train", label_file)
    if os.path.exists(src_label):
        shutil.copy(src_label, dst_label)

for img_file in val_images:
    src = os.path.join(images_folder, img_file)
    dst = os.path.join(output_dir, "images", "val", img_file)
    shutil.copy(src, dst)
    
    label_file = os.path.splitext(img_file)[0] + ".txt"
    src_label = os.path.join(labels_folder, label_file)
    dst_label = os.path.join(output_dir, "labels", "val", label_file)
    if os.path.exists(src_label):
        shutil.copy(src_label, dst_label)

print("Dataset organized successfully!")
