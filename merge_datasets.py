"""
merge_datasets.py
Merges Roboflow crop dataset with existing weed detection dataset
Creates a unified dataset with all 14 classes
"""
import os
import shutil
import yaml
from pathlib import Path

# ============ CONFIGURATION ============
# Existing weed dataset
WEED_DATASET = "C:/dataset/wheat_yolo_dataset"

# Roboflow crop dataset (downloaded from download_roboflow.py)
CROP_DATASET = "C:/dataset1/roboflow_crop_dataset"

# Output merged dataset
MERGED_DATASET = "C:/dataset/merged_weed_crop_dataset"

# Existing weed classes (12 classes, indices 0-11)
WEED_CLASSES = [
    "waterhemp", "morningglory", "ragweed", "cocklebur",
    "spurred_anteria", "prickly_sida", "velvetleaf", "palmer_amaranth",
    "redroot_pigweed", "johnsongrass", "tall_morningglory", "sicklepod"
]

# New crop classes to add (will be indices 12-13)
CROP_CLASSES = ["wheat", "banana"]

# All classes combined
ALL_CLASSES = WEED_CLASSES + CROP_CLASSES
# =======================================

def create_merged_structure():
    """Create the merged dataset directory structure"""
    print("📁 Creating merged dataset structure...")
    
    for split in ["train", "val"]:
        os.makedirs(f"{MERGED_DATASET}/images/{split}", exist_ok=True)
        os.makedirs(f"{MERGED_DATASET}/labels/{split}", exist_ok=True)
    
    print(f"   Created: {MERGED_DATASET}")

def copy_weed_dataset():
    """Copy existing weed dataset to merged location"""
    print("\n🌿 Copying weed dataset...")
    
    for split in ["train", "val"]:
        # Copy images
        src_images = f"{WEED_DATASET}/images/{split}"
        dst_images = f"{MERGED_DATASET}/images/{split}"
        
        if os.path.exists(src_images):
            count = 0
            for img in os.listdir(src_images):
                shutil.copy2(f"{src_images}/{img}", f"{dst_images}/{img}")
                count += 1
            print(f"   Copied {count} {split} images")
        
        # Copy labels (no modification needed - class indices stay the same)
        src_labels = f"{WEED_DATASET}/labels/{split}"
        dst_labels = f"{MERGED_DATASET}/labels/{split}"
        
        if os.path.exists(src_labels):
            count = 0
            for lbl in os.listdir(src_labels):
                shutil.copy2(f"{src_labels}/{lbl}", f"{dst_labels}/{lbl}")
                count += 1
            print(f"   Copied {count} {split} labels")

def get_crop_class_mapping(crop_data_yaml):
    """Read the crop dataset's data.yaml to get class names and create mapping"""
    with open(crop_data_yaml, 'r') as f:
        data = yaml.safe_load(f)
    
    crop_names = data.get('names', [])
    if isinstance(crop_names, dict):
        crop_names = [crop_names[i] for i in sorted(crop_names.keys())]
    
    print(f"\n📋 Crop dataset classes: {crop_names}")
    
    # Create mapping: old_index -> new_index
    # New indices start at 12 (after 12 weed classes)
    mapping = {}
    for old_idx, name in enumerate(crop_names):
        # Find or assign new index
        name_lower = name.lower().replace(" ", "_").replace("-", "_")
        
        if name_lower in [c.lower() for c in CROP_CLASSES]:
            new_idx = ALL_CLASSES.index([c for c in ALL_CLASSES if c.lower() == name_lower][0])
        else:
            # Add to ALL_CLASSES if not already there
            ALL_CLASSES.append(name_lower)
            new_idx = len(ALL_CLASSES) - 1
            print(f"   ⚠️ Added new class: {name_lower} (index {new_idx})")
        
        mapping[old_idx] = new_idx
        print(f"   Mapping: {name} ({old_idx}) -> index {new_idx}")
    
    return mapping

def remap_and_copy_crop_labels(mapping):
    """Copy crop labels with remapped class indices"""
    print("\n🌾 Processing crop dataset labels...")
    
    for split in ["train", "valid", "val", "test"]:
        src_labels = f"{CROP_DATASET}/{split}/labels"
        src_images = f"{CROP_DATASET}/{split}/images"
        
        if not os.path.exists(src_labels):
            continue
        
        dst_split = "val" if split in ["valid", "test"] else "train"
        dst_labels = f"{MERGED_DATASET}/labels/{dst_split}"
        dst_images = f"{MERGED_DATASET}/images/{dst_split}"
        
        label_count = 0
        image_count = 0
        
        # Copy and remap labels
        for lbl_file in os.listdir(src_labels):
            if not lbl_file.endswith('.txt'):
                continue
            
            with open(f"{src_labels}/{lbl_file}", 'r') as f:
                lines = f.readlines()
            
            # Remap class indices
            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    old_class = int(parts[0])
                    new_class = mapping.get(old_class, old_class)
                    parts[0] = str(new_class)
                    new_lines.append(' '.join(parts) + '\n')
            
            # Add prefix to avoid filename conflicts
            new_filename = f"crop_{lbl_file}"
            with open(f"{dst_labels}/{new_filename}", 'w') as f:
                f.writelines(new_lines)
            label_count += 1
        
        # Copy images with same prefix
        if os.path.exists(src_images):
            for img_file in os.listdir(src_images):
                new_filename = f"crop_{img_file}"
                shutil.copy2(f"{src_images}/{img_file}", f"{dst_images}/{new_filename}")
                image_count += 1
        
        print(f"   {split}: Copied {image_count} images, {label_count} labels -> {dst_split}")

def create_merged_data_yaml():
    """Create data.yaml for the merged dataset"""
    print("\n📝 Creating merged data.yaml...")
    
    data = {
        'path': MERGED_DATASET,
        'train': f'{MERGED_DATASET}/images/train',
        'val': f'{MERGED_DATASET}/images/val',
        'nc': len(ALL_CLASSES),
        'names': ALL_CLASSES
    }
    
    yaml_path = f"{MERGED_DATASET}/data.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    print(f"   Saved: {yaml_path}")
    print(f"   Total classes: {len(ALL_CLASSES)}")
    print(f"   Classes: {ALL_CLASSES}")
    
    return yaml_path

def count_dataset_stats():
    """Print final dataset statistics"""
    print("\n📊 Merged Dataset Statistics:")
    
    for split in ["train", "val"]:
        images = len(os.listdir(f"{MERGED_DATASET}/images/{split}"))
        labels = len(os.listdir(f"{MERGED_DATASET}/labels/{split}"))
        print(f"   {split}: {images} images, {labels} labels")

def main():
    print("=" * 60)
    print("  DATASET MERGER - Weeds + Crops")
    print("=" * 60)
    
    # Check paths exist
    if not os.path.exists(WEED_DATASET):
        print(f"❌ Weed dataset not found: {WEED_DATASET}")
        return
    
    if not os.path.exists(CROP_DATASET):
        print(f"❌ Crop dataset not found: {CROP_DATASET}")
        print("   Run download_roboflow.py first!")
        return
    
    # Find crop data.yaml
    crop_yaml = None
    for name in ["data.yaml", "dataset.yaml"]:
        path = f"{CROP_DATASET}/{name}"
        if os.path.exists(path):
            crop_yaml = path
            break
    
    if not crop_yaml:
        print(f"❌ Could not find data.yaml in crop dataset")
        return
    
    # Execute merge
    create_merged_structure()
    copy_weed_dataset()
    mapping = get_crop_class_mapping(crop_yaml)
    remap_and_copy_crop_labels(mapping)
    yaml_path = create_merged_data_yaml()
    count_dataset_stats()
    
    print("\n" + "=" * 60)
    print("  ✅ MERGE COMPLETE!")
    print("=" * 60)
    print(f"\nNext step: Run uptraining with:")
    print(f'  python uptrain_yolo.py')

if __name__ == "__main__":
    main()
