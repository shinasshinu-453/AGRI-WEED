from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
import base64
import cv2
import numpy as np
import torch
import threading
from queue import Queue
import time
import os
import sys
import google.generativeai as genai
from io import BytesIO
from PIL import Image
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("Warning: pyngrok not installed. Remote access via ngrok unavailable.")

app = Flask(__name__, static_folder='dist', static_url_path='')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

model_path = 'runs/detect/train6/weights/best.pt'
if not os.path.exists(model_path):
    print(f"⚠️  Custom model not found at {model_path}")
    print(f"📦 Loading pretrained YOLOv8n model instead...")
    model_path = 'yolov8n.pt'

print(f"🔧 Loading model from: {model_path}")
model = YOLO(model_path)
model.to(device)
model.fuse()
print(f"✅ Model loaded successfully")
print(f"💡 Model optimization: fused layers for faster inference")

# Initialize Gemini API (for weed removal techniques only)
GEMINI_API_KEY = os.environ.get('VITE_GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"✅ Gemini API initialized for weed removal techniques")
else:
    print(f"⚠️  GEMINI_API_KEY not found. Weed removal techniques will be unavailable.")

# Initialize Roboflow API (for crop identification)
ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY')
ROBOFLOW_WORKSPACE = os.environ.get('ROBOFLOW_WORKSPACE', 'weed-ryn8z')
ROBOFLOW_PROJECT = os.environ.get('ROBOFLOW_PROJECT', 'my-first-project-9fmyh')
ROBOFLOW_VERSION = os.environ.get('ROBOFLOW_VERSION', '6')

if ROBOFLOW_API_KEY and ROBOFLOW_API_KEY != 'YOUR_API_KEY_HERE':
    print(f"✅ Roboflow API initialized for crop identification")
    print(f"   📦 Project: {ROBOFLOW_WORKSPACE}/{ROBOFLOW_PROJECT} (v{ROBOFLOW_VERSION})")
else:
    print(f"⚠️  ROBOFLOW_API_KEY not found. Roboflow crop detection will be unavailable.")

COMMON_CROP_NAMES = {
    'wheat': ['wheat', 'whe'],
    'cotton': ['cotton', 'cot'],
    'corn': ['corn', 'maize'],
    'rice': ['rice'],
    'soybean': ['soybean', 'soy'],
    'sugarcane': ['sugarcane', 'sugar'],
    'potato': ['potato'],
    'tomato': ['tomato'],
}

def get_crop_type(label: str, crop_name: str) -> str:
    """
    Classify a detected object as 'weed' or 'crop' based on its label and crop context.
    Improved logic to show bounding boxes for BOTH weeds and crops.
    """
    label_lower = label.lower().strip()
    crop_name_lower = crop_name.lower().strip()
    
    weed_keywords = [
        # Generic weed terms
        'weed', 'wild', 'unwanted',
        # Common broadleaf weeds
        'waterhemp', 'pigweed', 'palmer amaranth', 'amaranth', 'lambsquarters', 'lamb\'squarters',
        'smartweed', 'dock', 'plantain', 'chickweed', 'purslane', 'spurge',
        # Thistle family
        'dandelion', 'thistle', 'canada thistle', 'bull thistle',
        # Vines and climbers
        'bindweed', 'morningglory', 'morning-glory', 'morningglories', 'field bindweed',
        # Grassy weeds
        'crabgrass', 'foxtail', 'nutsedge', 'quackgrass', 'johnsongrass', 'barnyardgrass',
        # Other common weeds
        'ragweed', 'clover', 'nightshade', 'vetch', 'buckwheat', 'marestail', 'kochia',
        'velvetleaf', 'cocklebur', 'common ragweed', 'giant ragweed', 'horseweed'
    ]
    
    crop_keywords = ['wheat', 'corn', 'cotton', 'rice', 'soybean', 'potato', 'tomato', 'lettuce', 
                     'cabbage', 'barley', 'oat', 'rye', 'maize', 'bean', 'pea', 'peanut', 
                     'sunflower_crop', 'canola', 'rapeseed', 'banana']
    
    plant_keywords = ['plant', 'potted plant', 'flower', 'sunflower', 'daisy', 'leaf', 'leaves', 
                      'bush', 'shrub', 'seedling', 'vegetation', 'foliage', 'crop']
    
    print(f"🔍 Classifying: '{label}' (crop context: '{crop_name_lower}')")
    
    # Priority 1: Explicit weed keywords always return weed
    if any(weed_term in label_lower for weed_term in weed_keywords):
        print(f"   ✓ Classified as WEED (matched weed keyword)")
        return 'weed'
    
    # Priority 2: Explicit crop keywords return crop
    if any(crop_term in label_lower for crop_term in crop_keywords):
        print(f"   ✓ Classified as CROP (matched crop keyword)")
        return 'crop'
    
    # Priority 3: Check if label matches the specified crop context
    # E.g., if user says "wheat" and label contains "wheat", it's a crop
    if crop_name_lower and len(crop_name_lower) > 2:
        # Check for partial matches (e.g., "wheat" in "winter wheat")
        if crop_name_lower in label_lower or label_lower in crop_name_lower:
            print(f"   ✓ Classified as CROP (matches user-specified crop: {crop_name_lower})")
            return 'crop'
    
    # Priority 4: Generic plant labels - assume crop if crop context exists
    if any(plant_term in label_lower for plant_term in plant_keywords):
        # If user specified a crop type, assume generic plants are that crop
        if crop_name_lower and crop_name_lower != 'general crop':
            print(f"   ✓ Classified as CROP (generic plant + crop context)")
            return 'crop'
        else:
            # No crop context, could be either - default to crop
            print(f"   ? Classified as CROP (generic plant, no specific context)")
            return 'crop'
    
    # Priority 5: Check if it's a common object that's not a plant
    non_plant_objects = ['person', 'car', 'truck', 'bird', 'animal', 'dog', 'cat', 'stone', 'rock']
    if any(obj in label_lower for obj in non_plant_objects):
        print(f"   ✓ Classified as WEED (non-plant object)")
        return 'weed'
    
    # Default: If we're in a crop field context, assume it's part of the crop
    # This ensures crops get bounding boxes too!
    if crop_name_lower and crop_name_lower != 'general crop':
        print(f"   ? Classified as CROP (unknown label, defaulting to crop in {crop_name_lower} field)")
        return 'crop'
    else:
        print(f"   ? Classified as WEED (unknown label, no crop context - safety default)")
        return 'weed'

def resize_image_for_inference(img, max_size=320):
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img

def identify_crop_with_roboflow(image_data: bytes) -> dict:
    """Use Roboflow hosted inference API to identify crop type in the image."""
    if not ROBOFLOW_API_KEY or ROBOFLOW_API_KEY == 'YOUR_API_KEY_HERE':
        return {"error": "Roboflow API key not configured"}
    
    try:
        # Convert image bytes to base64 for Roboflow API
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Roboflow Hosted Inference API endpoint
        url = f"https://detect.roboflow.com/{ROBOFLOW_PROJECT}/{ROBOFLOW_VERSION}"
        
        params = {
            "api_key": ROBOFLOW_API_KEY,
            "confidence": 40,  # 40% confidence threshold
            "overlap": 30
        }
        
        # Send image to Roboflow
        response = requests.post(
            url,
            params=params,
            data=image_base64,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            return {"error": f"Roboflow API error: {response.status_code}"}
        
        result = response.json()
        predictions = result.get('predictions', [])
        
        if not predictions:
            return {
                "cropName": "Unknown Crop",
                "confidence": 0.0,
                "characteristics": "No crops detected by Roboflow model"
            }
        
        # Find the most confident crop detection
        # Assuming your model has classes like "wheat", "corn", "banana", etc.
        crop_detections = [p for p in predictions if p.get('class', '').lower() not in ['weed', 'grass']]
        
        if crop_detections:
            best_crop = max(crop_detections, key=lambda x: x.get('confidence', 0))
            crop_name = best_crop.get('class', 'Unknown Crop').title()
            confidence = best_crop.get('confidence', 0) / 100.0  # Convert to 0-1 scale
            
            # Count detections
            crop_count = len(crop_detections)
            
            result_data = {
                "cropName": crop_name,
                "confidence": confidence,
                "characteristics": f"Detected {crop_count} {crop_name.lower()} instance(s) in the field"
            }
            
            print(f"🌾 Crop identified (Roboflow): {crop_name} (confidence: {confidence:.2f})")
            return result_data
        else:
            return {
                "cropName": "Unknown Crop",
                "confidence": 0.3,
                "characteristics": "Only weeds detected in the image"
            }
        
    except Exception as e:
        print(f"❌ Roboflow crop identification error: {e}")
        return {"error": str(e)}

def detect_with_roboflow(image_data: bytes, crop_name: str = "Wheat") -> dict:
    """Use Roboflow for detection and return detections with bounding boxes."""
    if not ROBOFLOW_API_KEY or ROBOFLOW_API_KEY == 'YOUR_API_KEY_HERE':
        return {"error": "Roboflow API key not configured"}
    
    try:
        # Convert image bytes to base64 for Roboflow API
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Get image dimensions
        img = Image.open(BytesIO(image_data))
        img_width, img_height = img.size
        
        # Roboflow Hosted Inference API endpoint
        url = f"https://detect.roboflow.com/{ROBOFLOW_PROJECT}/{ROBOFLOW_VERSION}"
        
        params = {
            "api_key": ROBOFLOW_API_KEY,
            "confidence": 30,  # 30% confidence threshold
            "overlap": 30
        }
        
        print(f"📡 Sending to Roboflow: {url}")
        # Send image to Roboflow
        response = requests.post(
            url,
            params=params,
            data=image_base64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        
        if response.status_code != 200:
            return {"error": f"Roboflow API error: {response.status_code}"}
        
        result = response.json()
        predictions = result.get('predictions', [])
        
        print(f"🔍 Roboflow found {len(predictions)} detections")
        
        # Convert Roboflow predictions to our detection format
        detections = []
        weed_count = 0
        crop_count = 0
        weed_types = []
        crop_name_identified = None
        
        for pred in predictions:
            class_name = pred.get('class', 'unknown')
            confidence = pred.get('confidence', 0) / 100.0  # Convert to 0-1 scale
            
            # Roboflow returns x, y (center), width, height
            x_center = pred.get('x', 0)
            y_center = pred.get('y', 0)
            width = pred.get('width', 0)
            height = pred.get('height', 0)
            
            # Convert to normalized coordinates (0-1)
            xmin = (x_center - width/2) / img_width
            ymin = (y_center - height/2) / img_height
            xmax = (x_center + width/2) / img_width
            ymax = (y_center + height/2) / img_height
            
            # Classify as weed or crop
            det_type = get_crop_type(class_name, crop_name)
            print(f"  - {class_name} ({det_type}): {confidence*100:.1f}%")
            
            if det_type == "weed":
                weed_count += 1
                weed_types.append(class_name)
            else:
                crop_count += 1
                if not crop_name_identified:
                    crop_name_identified = class_name.title()
            
            detections.append({
                "label": class_name,
                "confidence": confidence,
                "box": {
                    "xmin": max(0, min(1, xmin)),
                    "ymin": max(0, min(1, ymin)),
                    "xmax": max(0, min(1, xmax)),
                    "ymax": max(0, min(1, ymax)),
                },
                "type": det_type,
                "description": f" Detected {class_name} ({confidence*100:.1f}%)",
                "raw_class": class_name
            })
        
        # Prepare crop identification result
        identified_crop = None
        if crop_name_identified and crop_count > 0:  # Must have actual crop detections
            # Calculate average confidence of crop detections
            crop_confidences = [d['confidence'] for d in detections if d['type'] == 'crop']
            avg_confidence = sum(crop_confidences) / len(crop_confidences) if crop_confidences else 0
            
            # Only show crop identification if confidence is reasonable
            if avg_confidence >= 0.6:  # 60% minimum confidence
                identified_crop = {
                    "cropName": crop_name_identified,
                    "confidence": avg_confidence,
                    "characteristics": f"Detected {crop_count} {crop_name_identified.lower()} instance(s) in the field"
                }
                print(f"✅ Identified crop: {crop_name_identified} ({avg_confidence*100:.1f}% avg confidence)")
            else:
                print(f"⚠️ Crop confidence too low ({avg_confidence*100:.1f}%), not showing crop identification")
        
        return {
            "detections": detections,
            "weed_count": weed_count,
            "crop_count": crop_count,
            "weed_types": weed_types,
            "identified_crop": identified_crop
        }
        
    except Exception as e:
        print(f"❌ Roboflow detection error: {e}")
        return {"error": str(e)}

def generate_removal_techniques(crop_name: str, weed_types: list, weed_count: int) -> dict:
    """Generate crop-specific weed removal techniques using Gemini."""
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key not configured"}
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        weed_list = ', '.join(set(weed_types)) if weed_types else 'various weeds'
        
        prompt = f"""You are an agricultural expert specializing in weed management.

Field Analysis:
- Crop: {crop_name}
- Weeds Detected: {weed_list}
- Weed Count: {weed_count}

Provide comprehensive weed removal techniques specifically for {crop_name} fields. Return your response in this exact JSON format:

{{
  "manual": "<detailed manual removal technique for {crop_name}>",
  "chemical": "<selective herbicide recommendations safe for {crop_name}>",
  "organic": "<organic/natural weed control methods for {crop_name}>",
  "mechanical": "<mechanical removal techniques suitable for {crop_name}>",
  "priority": "<one of: manual, chemical, organic, mechanical - recommend the most effective method>",
  "timing": "<optimal timing and conditions for weed removal in {crop_name} fields>"
}}

Guidelines:
- Be specific to {crop_name} - different crops have different weed management needs
- Consider crop growth stage and sensitivity
- Each technique should be 1-2 sentences, actionable and practical
- Priority should be the MOST effective and practical method for this crop
- Timing should consider weather, crop stage, and herbicide application windows
- For chemical, specify herbicide type (selective/non-selective) and active ingredients if appropriate"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        import json
        result = json.loads(text)
        
        print(f"✅ Generated removal techniques for {crop_name}")
        return result
        
    except Exception as e:
        print(f"❌ Removal technique generation error: {e}")
        return {"error": str(e)} 


@app.route('/', methods=['GET'])
def index():
    if os.path.exists('dist/index.html'):
        return send_from_directory('dist', 'index.html')
    else:
        return jsonify({
            "message": "Frontend not built yet",
            "instructions": "Run 'npm run build' to build the frontend",
            "api": "Backend API is ready at /analyze"
        }), 200

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    if os.path.exists(f'dist/{path}'):
        return send_from_directory('dist', path)
    return send_from_directory('dist', 'index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


@app.route('/analyze', methods=['POST'])
def analyze():
    start_time = time.time()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        base64_image = data.get('image')
        crop_name = (data.get('cropName') or 'Wheat').strip()
        identify_crop = data.get('identifyCrop', False)  # Crop identification flag
        use_roboflow = data.get('useRoboflow', False)  # NEW: Use Roboflow for detection
        
        # DEBUG: Log what we received
        print(f"\n📋 Request parameters:")
        print(f"   - Crop name: {crop_name}")
        print(f"   - Identify crop: {identify_crop}")
        print(f"   - Use Roboflow: {use_roboflow}")

        if not base64_image:
            return jsonify({"error": "No image provided"}), 400

        decode_start = time.time()
        try:
            image_data = base64.b64decode(base64_image)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({"error": f"Failed to decode image: {str(e)}"}), 400
        
        decode_time = time.time() - decode_start
        print(f"📥 Image decode time: {decode_time:.3f}s")

        if img is None:
            return jsonify({"error": "Invalid image data"}), 400

        # Check if user wants to use Roboflow for detection
        if use_roboflow:
            print("🔬 Using Roboflow for detection...")
            roboflow_result = detect_with_roboflow(image_data, crop_name)
            
            if 'error' in roboflow_result:
                return jsonify({"error": roboflow_result['error']}), 500
            
            detections = roboflow_result['detections']
            weed_count = roboflow_result['weed_count']
            crop_count = roboflow_result['crop_count']
            weed_types = roboflow_result['weed_types']
            identified_crop = roboflow_result.get('identified_crop')
            
            # Generate weed removal techniques if weeds detected
            removal_techniques = None
            if weed_count > 0:
                print(f"🌿 Generating removal techniques for {crop_name}...")
                techniques = generate_removal_techniques(crop_name, weed_types, weed_count)
                if 'error' not in techniques:
                    removal_techniques = techniques
            
            total_time = time.time() - start_time
            print(f"✅ Analysis complete in {total_time:.3f}s")
            print(f"   - Results: {weed_count} weeds, {crop_count} crops")
            
            response_data = {
                "detections": detections,
                "count": len(detections),
                "weedCount": weed_count,
                "cropCount": crop_count,
                "summary": f"Detected {weed_count} weed(s) and {crop_count} crop(s)",
                "inferenceTime": round(total_time, 3),
                "cropType": crop_name,
                "model": "roboflow"  # Indicate which model was used
            }
            
            # Only show crop identification if NO weeds detected
            if identified_crop and weed_count == 0:
                response_data["identifiedCrop"] = identified_crop
                print(f"✅ Showing Crop ID Card (weed-free field)")
            elif identified_crop and weed_count > 0:
                print(f"⚠️ Hiding Crop ID Card (weeds present: {weed_count})")
                
            if removal_techniques:
                response_data["removalTechniques"] = removal_techniques
            
            return jsonify(response_data), 200
        
        # Otherwise use YOLO (original behavior)
        # Crop identification using Roboflow (if requested)
        identified_crop = None
        if identify_crop:
            print("🌾 Identifying crop with Roboflow...")
            crop_id_result = identify_crop_with_roboflow(image_data)
            if 'error' not in crop_id_result:
                identified_crop = crop_id_result
                # Use identified crop name for analysis
                if crop_id_result.get('cropName'):
                    crop_name = crop_id_result['cropName']
                    print(f"✅ Using identified crop: {crop_name}")

        orig_h, orig_w = img.shape[:2]
        img = resize_image_for_inference(img, max_size=320)
        h, w = img.shape[:2]

        start_infer = time.time()
        results = model(img, conf=0.2, verbose=False, device=device, imgsz=320, max_det=100)
        infer_time = time.time() - start_infer
        print(f"⚡ Inference time: {infer_time:.3f}s")

        detections = []
        weed_count = 0
        crop_count = 0
        weed_types = []

        for result in results:
            if result.boxes is not None:
                print(f"🔍 Found {len(result.boxes)} detections")
                for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                    x1, y1, x2, y2 = box.tolist()
                    class_name = model.names[int(cls)]
                    
                    scale_x = orig_w / w
                    scale_y = orig_h / h
                    
                    x1_orig = x1 * scale_x
                    y1_orig = y1 * scale_y
                    x2_orig = x2 * scale_x
                    y2_orig = y2 * scale_y
                    
                    det_type = get_crop_type(class_name, crop_name)
                    print(f"  - {class_name} ({det_type}): {float(conf)*100:.1f}%")

                    if det_type == "weed":
                        weed_count += 1
                        weed_types.append(class_name)
                    else:
                        crop_count += 1

                    detections.append({
                        "label": class_name,
                        "confidence": float(conf),
                        "box": {
                            "xmin": x1_orig / orig_w,
                            "ymin": y1_orig / orig_h,
                            "xmax": x2_orig / orig_w,
                            "ymax": y2_orig / orig_h,
                        },
                        "type": det_type,
                        "description": f"Detected {class_name} ({float(conf)*100:.1f}%)",
                        "raw_class": class_name,
                        "model_class_id": int(cls)
                    })

        # Generate weed removal techniques if weeds detected
        removal_techniques = None
        if weed_count > 0:
            print(f"🌿 Generating removal techniques for {crop_name}...")
            techniques = generate_removal_techniques(crop_name, weed_types, weed_count)
            if 'error' not in techniques:
                removal_techniques = techniques

        total_time = time.time() - start_time

        print(f"✅ Analysis complete in {total_time:.3f}s")
        print(f"   - Decode: {decode_time:.3f}s")
        print(f"   - Inference: {infer_time:.3f}s")
        print(f"   - Results: {weed_count} weeds, {crop_count} crops")

        response_data = {
            "detections": detections,
            "count": len(detections),
            "weedCount": weed_count,
            "cropCount": crop_count,
            "summary": f"Detected {weed_count} weed(s) and {crop_count} crop(s)",
            "inferenceTime": round(infer_time, 3),
            "cropType": crop_name
        }
        
        # Add optional fields
        # Only show crop identification if NO weeds detected
        if identified_crop and weed_count == 0:
            response_data["identifiedCrop"] = identified_crop
            print(f"✅ Showing Crop ID Card (weed-free field)")
        elif identified_crop and weed_count > 0:
            print(f"⚠️ Hiding Crop ID Card (weeds present: {weed_count})")
            
        if removal_techniques:
            response_data["removalTechniques"] = removal_techniques

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "device": device,
        "model": "YOLOv8",
        "version": "1.0",
        "gemini_available": GEMINI_API_KEY is not None
    }), 200

@app.route('/identify-crop', methods=['POST'])
def identify_crop_endpoint():
    """Standalone endpoint for crop identification."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        base64_image = data.get('image')
        if not base64_image:
            return jsonify({"error": "No image provided"}), 400
        
        try:
            image_data = base64.b64decode(base64_image)
        except Exception as e:
            return jsonify({"error": f"Failed to decode image: {str(e)}"}), 400
        
        result = identify_crop_with_roboflow(image_data)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-treatment', methods=['POST'])
def get_treatment_endpoint():
    """Standalone endpoint for weed removal technique recommendations."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        crop_name = data.get('cropName', 'Wheat')
        weed_types = data.get('weedTypes', [])
        weed_count = data.get('weedCount', len(weed_types))
        
        result = generate_removal_techniques(crop_name, weed_types, weed_count)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Image too large. Maximum 10MB allowed."}), 413

@app.errorhandler(408)
def request_timeout(error):
    return jsonify({"error": "Request timeout. Please try again."}), 408

if __name__ == '__main__':
    use_ngrok = '--ngrok' in sys.argv or os.environ.get('USE_NGROK') == 'true'
    
    if use_ngrok and NGROK_AVAILABLE:
        try:
            ngrok_token = os.environ.get('NGROK_AUTH_TOKEN')
            if ngrok_token:
                ngrok.set_auth_token(ngrok_token)
            
            public_url = ngrok.connect(5000)
            print(f"\n{'='*60}")
            print(f"🌐 NGROK TUNNEL ACTIVE!")
            print(f"{'='*60}")
            print(f"🔗 Public URL: {public_url}")
            print(f"📱 Share this link to access from any device!")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"⚠️  Failed to create ngrok tunnel: {e}")
            print("Starting server without ngrok tunnel...\n")
    
    print(f"Starting Flask server on http://0.0.0.0:5000")
    print(f"Local access: http://localhost:5000")
    print(f"Network access: http://<your-ip>:5000")
    print(f"Use --ngrok flag for remote access: python server.py --ngrok\n")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )
