"""
download_roboflow.py
Downloads the crop dataset from Roboflow and prepares it for merging
"""
from roboflow import Roboflow
import os
import shutil

# ============ CONFIGURATION ============
# Get your API key from: https://app.roboflow.com/settings/api
ROBOFLOW_API_KEY = "YOUR_API_KEY_HERE"  # <-- Replace with your API key
WORKSPACE = "YOUR_WORKSPACE"            # <-- Replace (visible in URL before /)
PROJECT = "weed-ryn8z"                  # Your project name
VERSION = 1                              # Dataset version number

# Download location
DOWNLOAD_PATH = "C:/dataset1/roboflow_crop_dataset"
# =======================================

def download_dataset():
    print("🔄 Connecting to Roboflow...")
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    
    print(f"📦 Accessing project: {PROJECT}")
    project = rf.workspace(WORKSPACE).project(PROJECT)
    
    print(f"⬇️ Downloading version {VERSION} in YOLOv8 format...")
    dataset = project.version(VERSION).download("yolov8", location=DOWNLOAD_PATH)
    
    print(f"\n✅ Dataset downloaded to: {DOWNLOAD_PATH}")
    print(f"📁 Structure:")
    for root, dirs, files in os.walk(DOWNLOAD_PATH):
        level = root.replace(DOWNLOAD_PATH, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # Show first 5 files only
            print(f'{subindent}{file}')
        if len(files) > 5:
            print(f'{subindent}... and {len(files) - 5} more files')
    
    return dataset

if __name__ == "__main__":
    print("=" * 50)
    print("  ROBOFLOW DATASET DOWNLOADER")
    print("=" * 50)
    
    # Check if API key is set
    if ROBOFLOW_API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠️  Please set your Roboflow API key!")
        print("   1. Go to: https://app.roboflow.com/settings/api")
        print("   2. Copy your Private API Key")
        print("   3. Paste it in this script (line 10)")
        print("\n   Also set your WORKSPACE name (visible in the URL)")
    else:
        download_dataset()
