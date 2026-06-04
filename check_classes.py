
import os
from collections import Counter
import yaml

def check_dataset_classes(data_yaml_path):
    with open(data_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    class_names = data['names']
    train_labels_dir = os.path.join(data['path'], 'labels', 'train')
    val_labels_dir = os.path.join(data['path'], 'labels', 'val')
    
    def count_classes(directory):
        counter = Counter()
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return counter
        
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                with open(os.path.join(directory, filename), 'r') as f:
                    for line in f:
                        cls = line.split()[0]
                        counter[int(cls)] += 1
        return counter

    print("--- Train Set ---")
    train_counts = count_classes(train_labels_dir)
    for i, name in enumerate(class_names):
        print(f"ID {i} ({name}): {train_counts[i]} instances")
    
    print("\n--- Val Set ---")
    val_counts = count_classes(val_labels_dir)
    for i, name in enumerate(class_names):
        print(f"ID {i} ({name}): {val_counts[i]} instances")

if __name__ == "__main__":
    check_dataset_classes('data.yaml')
