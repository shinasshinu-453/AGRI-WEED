import os
import glob

labels_folder = r"C:\dataset\CottonWeedDet12\annotation_YOLO_txt"

txt_files = glob.glob(os.path.join(labels_folder, "*.txt"))
print(f"Total txt files: {len(txt_files)}")

class_ids = set()
for txt_file in txt_files[:10]:
    with open(txt_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if parts:
                class_id = parts[0]
                class_ids.add(class_id)
                print(f"{os.path.basename(txt_file)}: class={class_id}")

print(f"\nUnique class IDs found: {sorted(class_ids)}")
