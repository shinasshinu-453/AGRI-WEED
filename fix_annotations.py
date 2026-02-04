import os
import glob

input_folder = r"C:\dataset\CottonWeedDet12\annotation_YOLO_txt"
output_folder = r"C:\dataset\wheat_yolo_dataset\labels\train_fixed"

os.makedirs(output_folder, exist_ok=True)

txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
print(f"Processing {len(txt_files)} files...")

for txt_file in txt_files:
    with open(txt_file, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        
        class_id = int(parts[0])
        coords = parts[1:]
        
        if class_id >= 2:
            class_id = 1
        
        fixed_line = f"{class_id} " + " ".join(coords) + "\n"
        fixed_lines.append(fixed_line)
    
    output_file = os.path.join(output_folder, os.path.basename(txt_file))
    with open(output_file, 'w') as f:
        f.writelines(fixed_lines)

print(f"Fixed annotations saved to {output_folder}")
print("Now update organize_dataset.py to use the fixed labels")
