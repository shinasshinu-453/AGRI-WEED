from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
import base64
import cv2
import numpy as np
import torch
import time
import os
import sys
import json
from google import genai
from io import BytesIO
from PIL import Image
import requests
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("Warning: pyngrok not installed. Remote access via ngrok unavailable.")

app = Flask(__name__, static_folder='dist', static_url_path='')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Device setup
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# --- CPU thread optimisation -------------------------------------------
# Give PyTorch all available logical cores for intra-op parallelism.
_cpu_count = os.cpu_count() or 2
torch.set_num_threads(_cpu_count)
torch.set_num_interop_threads(max(1, _cpu_count // 2))
print(f"[OPT] PyTorch using {_cpu_count} CPU threads")

# --- Load YOLOv11n — trained on CottonWeedDet12 (12 weed species) -------
# This model directly predicts all 12 species — no secondary classifier needed.
# Path resolution: env var > local absolute path > relative models/ > fallback yolov8n.pt
_YOLO11N_PATH = os.environ.get('YOLO_MODEL_PATH', '')
if not _YOLO11N_PATH or not os.path.exists(_YOLO11N_PATH):
    # Try local dev absolute path
    _LOCAL_PATH = r'C:\Users\shina\Downloads\yolov11n_cotton12_2026-03-27\cotton_yolov11n\weights\best.pt'
    if os.path.exists(_LOCAL_PATH):
        _YOLO11N_PATH = _LOCAL_PATH
    # Try relative models/ directory (for cloud deploy)
    elif os.path.exists(os.path.join(os.path.dirname(__file__), 'models', 'best.pt')):
        _YOLO11N_PATH = os.path.join(os.path.dirname(__file__), 'models', 'best.pt')
    # Fallback to yolov8n.pt in project root
    elif os.path.exists(os.path.join(os.path.dirname(__file__), 'yolov8n.pt')):
        _YOLO11N_PATH = os.path.join(os.path.dirname(__file__), 'yolov8n.pt')
        print("⚠️ Using fallback yolov8n.pt — accuracy will differ from trained model")
    else:
        raise FileNotFoundError(
            "Model weights missing. Set YOLO_MODEL_PATH env var or place best.pt in models/ directory.")

print(f"Loading YOLO model: {_YOLO11N_PATH}")

print(f"Loading YOLOv11n weed detector: {_YOLO11N_PATH}")
model = YOLO(_YOLO11N_PATH)
model.to(device)
model.fuse()
print(f"YOLOv11n loaded ✅ | classes: {model.names}")

# Warm-up
try:
    _warmup_img = np.zeros((640, 640, 3), dtype=np.uint8)
    model(_warmup_img, imgsz=640, verbose=False)
    print("YOLOv11n warmed up ✅")
except Exception as _we:
    print(f"Warm-up skipped: {_we}")

# Image size for YOLO inference
YOLO_IMGSZ = 640

# Global minimum — YOLO runs at this threshold to retrieve all candidates.
# Per-class thresholds below act as a second filter after inference.
YOLO_MIN_CONFIDENCE = 0.20   # low global conf: catch everything first

# Per-class confidence thresholds (tuned for each weed species).
# These match the exact class names in the new YOLOv11n best.pt.
# Higher value = stricter = fewer but more reliable detections.
# Lower value  = lenient  = more detections, higher false-positive risk.
CLASS_CONF_THRESHOLDS = {
    # Common weeds — model well-trained, allow lower threshold
    'waterhemp':          0.30,
    'palmer_amaranth':    0.30,
    'redroot_pigweed':    0.30,
    'velvetleaf':         0.32,
    'johnsongrass':       0.32,

    # Moderately common
    'morningglory':       0.35,
    'tall_morningglory':  0.35,
    'ragweed':            0.38,
    'cocklebur':          0.38,

    # Less common / visually similar — stricter threshold
    'spurred_antearia':   0.42,   # NOTE: spelled 'antearia' in model training
    'prickly_sida':       0.42,
    'sicklepod':          0.45,
}

def get_class_conf_threshold(class_name: str) -> float:
    """Return the per-class confidence threshold, fallback to 0.35."""
    return CLASS_CONF_THRESHOLDS.get(class_name.lower(), 0.35)

# Gemini API (for weed removal techniques)
GEMINI_API_KEY = os.environ.get('VITE_GEMINI_API_KEY')
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini API ready")
else:
    print("⚠️ GEMINI_API_KEY not found")

# Roboflow API (for detection)
ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY')
ROBOFLOW_WORKSPACE = os.environ.get('ROBOFLOW_WORKSPACE', 'weed-ryn8z')
ROBOFLOW_PROJECT = os.environ.get('ROBOFLOW_PROJECT', 'my-first-project-9fmyh')
ROBOFLOW_VERSION = os.environ.get('ROBOFLOW_VERSION', '6')

if ROBOFLOW_API_KEY and ROBOFLOW_API_KEY != 'YOUR_API_KEY_HERE':
    print(f"✅ Roboflow API ready ({ROBOFLOW_WORKSPACE}/{ROBOFLOW_PROJECT} v{ROBOFLOW_VERSION})")
else:
    print("⚠️ ROBOFLOW_API_KEY not found")

# Confidence thresholds
ROBOFLOW_MIN_CONFIDENCE = 0.55   # 55% — raised to reduce weed-as-crop noise
YOLO_MIN_CONFIDENCE = 0.25       # 25% — raised to reduce crop misclassification as weed

# Weed classes — exact names as stored in the YOLOv11n best.pt weights
DATASET_WEED_CLASSES = [
    'waterhemp', 'morningglory', 'ragweed', 'cocklebur',
    'spurred_antearia', 'prickly_sida', 'velvetleaf',
    'palmer_amaranth', 'redroot_pigweed', 'johnsongrass',
    'tall_morningglory', 'sicklepod'
]

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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_crop_type(label: str, crop_name: str) -> str:
    """Classify a detected object as 'weed' or 'crop'."""
    label_lower = label.lower().strip()
    crop_name_lower = crop_name.lower().strip()

    weed_keywords = [
        'weed', 'wild', 'unwanted',
        # YOLOv11n CottonWeedDet12 trained classes (exact names)
        'waterhemp', 'morningglory', 'ragweed', 'cocklebur',
        'spurred_antearia', 'spurred antearia', 'prickly_sida', 'prickly sida',
        'velvetleaf', 'palmer_amaranth', 'palmer amaranth',
        'redroot_pigweed', 'redroot pigweed', 'johnsongrass',
        'tall_morningglory', 'tall morningglory', 'sicklepod',
        # Common weeds
        'pigweed', 'amaranth', 'lambsquarters', 'smartweed', 'dock',
        'plantain', 'chickweed', 'purslane', 'spurge',
        'dandelion', 'thistle', 'canada thistle', 'bull thistle',
        'bindweed', 'morning-glory', 'field bindweed',
        'crabgrass', 'foxtail', 'nutsedge', 'quackgrass', 'barnyardgrass',
        'clover', 'nightshade', 'vetch', 'buckwheat', 'marestail', 'kochia',
        'common ragweed', 'giant ragweed', 'horseweed'
    ]

    crop_keywords = [
        'wheat', 'corn', 'cotton', 'rice', 'soybean', 'potato', 'tomato',
        'lettuce', 'cabbage', 'barley', 'oat', 'rye', 'maize', 'bean',
        'pea', 'peanut', 'sunflower_crop', 'canola', 'rapeseed', 'banana',
        'crop'  # Roboflow class label — always treat as crop
    ]

    # Priority 1: Explicit weed keywords
    if any(weed_term in label_lower for weed_term in weed_keywords):
        return 'weed'

    # Priority 2: Explicit crop keywords
    if any(crop_term in label_lower for crop_term in crop_keywords):
        return 'crop'

    # Priority 3: Matches user-specified crop context
    if crop_name_lower and len(crop_name_lower) > 2:
        if crop_name_lower in label_lower or label_lower in crop_name_lower:
            return 'crop'

    # Priority 4: Generic plant labels
    plant_keywords = [
        'plant', 'potted plant', 'flower', 'sunflower', 'daisy',
        'leaf', 'leaves', 'bush', 'shrub', 'seedling', 'vegetation',
        'foliage', 'crop'
    ]
    if any(term in label_lower for term in plant_keywords):
        if crop_name_lower and crop_name_lower != 'general crop':
            return 'crop'
        return 'weed'

    # Priority 5: Non-plant objects — skip
    non_plant = ['person', 'car', 'truck', 'bird', 'animal', 'dog', 'cat', 'stone', 'rock']
    if any(obj in label_lower for obj in non_plant):
        return 'weed'

    # Default
    if crop_name_lower and crop_name_lower != 'general crop':
        return 'crop'
    return 'weed'


def resize_image_for_inference(img, max_size=320):
    """Resize image to max_size while keeping aspect ratio."""
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def detect_with_roboflow(image_data: bytes, crop_name: str = "Wheat") -> dict:
    """Run Roboflow detection and return filtered results."""
    if not ROBOFLOW_API_KEY or ROBOFLOW_API_KEY == 'YOUR_API_KEY_HERE':
        return {"error": "Roboflow API key not configured"}

    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        img = Image.open(BytesIO(image_data))
        img_width, img_height = img.size

        url = f"https://detect.roboflow.com/{ROBOFLOW_PROJECT}/{ROBOFLOW_VERSION}"
        params = {
            "api_key": ROBOFLOW_API_KEY,
            "confidence": int(ROBOFLOW_MIN_CONFIDENCE * 100),  # API expects percentage
            "overlap": 30
        }

        response = requests.post(
            url,
            params=params,
            data=image_base64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        if response.status_code != 200:
            print(f"❌ Roboflow API error: {response.status_code}")
            return {"error": f"Roboflow API error: {response.status_code}"}

        result = response.json()
        predictions = result.get('predictions', [])
        print(f"🌐 Roboflow raw: {len(predictions)} predictions")

        detections = []
        weed_count = 0
        crop_count = 0
        weed_types = []
        crop_name_identified = None

        for pred in predictions:
            class_name = pred.get('class', 'unknown')
            confidence = pred.get('confidence', 0)  # Already 0-1

            # Skip low-confidence detections — no bounding box
            if confidence < ROBOFLOW_MIN_CONFIDENCE:
                print(f"   ⏭️ Skip: {class_name} ({confidence*100:.0f}%) — below {ROBOFLOW_MIN_CONFIDENCE*100:.0f}% threshold")
                continue

            # Convert center+size to normalized min/max coords
            x_center = pred.get('x', 0)
            y_center = pred.get('y', 0)
            width = pred.get('width', 0)
            height = pred.get('height', 0)

            xmin = max(0, min(1, (x_center - width / 2) / img_width))
            ymin = max(0, min(1, (y_center - height / 2) / img_height))
            xmax = max(0, min(1, (x_center + width / 2) / img_width))
            ymax = max(0, min(1, (y_center + height / 2) / img_height))

            det_type = get_crop_type(class_name, crop_name)

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
                "box": {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax},
                "type": det_type,
                "description": f"{class_name} ({confidence*100:.1f}%)",
                "raw_class": class_name
            })

        print(f"   ✅ Roboflow kept: {len(detections)} ({weed_count} weeds, {crop_count} crops)")

        # Crop identification from detections
        identified_crop = None
        if crop_name_identified and crop_count > 0:
            crop_confidences = [d['confidence'] for d in detections if d['type'] == 'crop']
            avg_conf = sum(crop_confidences) / len(crop_confidences) if crop_confidences else 0
            if avg_conf >= 0.6:
                identified_crop = {
                    "cropName": crop_name_identified,
                    "confidence": avg_conf,
                    "characteristics": f"Detected {crop_count} {crop_name_identified.lower()} instance(s)"
                }

        return {
            "detections": detections,
            "weed_count": weed_count,
            "crop_count": crop_count,
            "weed_types": weed_types,
            "identified_crop": identified_crop
        }

    except Exception as e:
        print(f"❌ Roboflow error: {e}")
        return {"error": str(e)}


def identify_crop_with_roboflow(image_data: bytes) -> dict:
    """Use Roboflow to identify the crop type in the image."""
    if not ROBOFLOW_API_KEY or ROBOFLOW_API_KEY == 'YOUR_API_KEY_HERE':
        return {"error": "Roboflow API key not configured"}

    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        url = f"https://detect.roboflow.com/{ROBOFLOW_PROJECT}/{ROBOFLOW_VERSION}"
        params = {"api_key": ROBOFLOW_API_KEY, "confidence": 40, "overlap": 30}

        response = requests.post(
            url, params=params, data=image_base64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        if response.status_code != 200:
            return {"error": f"Roboflow API error: {response.status_code}"}

        predictions = response.json().get('predictions', [])
        if not predictions:
            return {"cropName": "Unknown Crop", "confidence": 0.0, "characteristics": "No crops detected"}

        # Find the best crop detection (not weeds)
        # 'crop' is the Roboflow class label for crops
        crop_preds = [p for p in predictions if p.get('class', '').lower() not in ['weed', 'grass']]
        if crop_preds:
            best = max(crop_preds, key=lambda x: x.get('confidence', 0))
            return {
                "cropName": best['class'].title(),
                "confidence": best.get('confidence', 0),  # Already 0-1
                "characteristics": f"Detected {len(crop_preds)} instance(s)"
            }

        return {"cropName": "Unknown Crop", "confidence": 0.3, "characteristics": "Only weeds detected"}

    except Exception as e:
        print(f"❌ Crop identification error: {e}")
        return {"error": str(e)}


def generate_removal_techniques(crop_name: str, weed_types: list, weed_count: int) -> dict:
    """Generate weed removal recommendations using Gemini."""
    if not gemini_client:
        return {"error": "Gemini API key not configured"}

    try:
        weed_list = ', '.join(set(weed_types)) if weed_types else 'various weeds'

        prompt = f"""You are an agricultural expert specializing in weed management.

Field Analysis:
- Crop: {crop_name}
- Weeds Detected: {weed_list}
- Weed Count: {weed_count}

Provide weed removal techniques for {crop_name} fields. Return JSON:

{{
  "manual": "<manual removal technique>",
  "chemical": "<selective herbicide recommendations safe for {crop_name}>",
  "organic": "<organic/natural weed control methods>",
  "mechanical": "<mechanical removal techniques>",
  "priority": "<one of: manual, chemical, organic, mechanical>",
  "timing": "<optimal timing for weed removal>"
}}

Guidelines:
- Be specific to {crop_name}
- Each technique: 1-2 sentences, actionable
- For chemical, specify herbicide type and active ingredients"""

        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        text = response.text.strip()

        # Strip markdown code blocks
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        return json.loads(text.strip())

    except Exception as e:
        print(f"❌ Removal techniques error: {e}")
        return {"error": str(e)}


# ============================================================
# ROUTES
# ============================================================

@app.route('/', methods=['GET'])
def index():
    if os.path.exists('dist/index.html'):
        return send_from_directory('dist', 'index.html')
    return jsonify({"message": "Frontend not built. Run 'npm run build'", "api": "/analyze"}), 200

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    if os.path.exists(f'dist/{path}'):
        return send_from_directory('dist', path)
    return send_from_directory('dist', 'index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "device": device,
        "model": "YOLOv11n",
        "version": "1.0",
        "gemini_available": GEMINI_API_KEY is not None
    }), 200


@app.route('/analyze', methods=['POST'])
def analyze():
    """Main analysis endpoint — runs both YOLO and Roboflow."""
    start_time = time.time()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        base64_image = data.get('image')
        crop_name = (data.get('cropName') or 'Wheat').strip()
        identify_crop = data.get('identifyCrop', False)

        if not base64_image:
            return jsonify({"error": "No image provided"}), 400

        # Decode image
        try:
            image_data = base64.b64decode(base64_image)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({"error": f"Failed to decode image: {str(e)}"}), 400

        if img is None:
            return jsonify({"error": "Invalid image data"}), 400

        orig_h, orig_w = img.shape[:2]

        # ======================
        # Run YOLO + Roboflow IN PARALLEL
        # ======================
        from concurrent.futures import ThreadPoolExecutor

        def run_yolo():
            """Run YOLOv11n weed detection — predicts all 12 species directly."""
            img_resized = resize_image_for_inference(img, max_size=YOLO_IMGSZ)
            h, w = img_resized.shape[:2]
            sx, sy = orig_w / w, orig_h / h

            t0 = time.time()
            results = model(
                img_resized,
                conf=YOLO_MIN_CONFIDENCE,
                verbose=False,
                device=device,
                imgsz=YOLO_IMGSZ,
                max_det=50,
                agnostic_nms=True,
            )
            elapsed = time.time() - t0

            dets = []
            wc, cc = 0, 0
            wtypes = []

            for result in results:
                if result.boxes is not None:
                    for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                        x1, y1, x2, y2 = box.tolist()
                        conf_value = float(conf)
                        class_id = int(cls)

                        # Get species name directly from the multi-class YOLOv11n model
                        class_name = model.names.get(class_id, 'weed')

                        # Apply per-class confidence threshold
                        required_conf = get_class_conf_threshold(class_name)
                        if conf_value < required_conf:
                            continue   # skip — below class threshold

                        print(f"   🌿 YOLOv11n: {class_name} ({conf_value*100:.1f}%)")

                        det_type = get_crop_type(class_name, crop_name)

                        if det_type == "weed":
                            wc += 1
                            wtypes.append(class_name)
                        else:
                            cc += 1

                        dets.append({
                            "label": class_name,
                            "confidence": conf_value,
                            "box": {
                                "xmin": (x1 * sx) / orig_w,
                                "ymin": (y1 * sy) / orig_h,
                                "xmax": (x2 * sx) / orig_w,
                                "ymax": (y2 * sy) / orig_h,
                            },
                            "type": det_type,
                            "description": f"{class_name} ({conf_value*100:.1f}%) [YOLOv11n]",
                            "raw_class": class_name,
                            "model_class_id": class_id
                        })

            return {"detections": dets, "weed_count": wc, "crop_count": cc, "weed_types": wtypes, "time": elapsed}

        def run_roboflow():
            """Run Roboflow detection (API call)."""
            t0 = time.time()
            result = detect_with_roboflow(image_data, crop_name)
            elapsed = time.time() - t0
            return {"result": result, "time": elapsed}

        # Run both simultaneously
        with ThreadPoolExecutor(max_workers=2) as executor:
            yolo_future = executor.submit(run_yolo)
            robo_future = executor.submit(run_roboflow)

            yolo_data = yolo_future.result()
            robo_data = robo_future.result()

        # Unpack YOLO results
        yolo_detections = yolo_data["detections"]
        yolo_weed_count = yolo_data["weed_count"]
        yolo_crop_count = yolo_data["crop_count"]
        yolo_weed_types = yolo_data["weed_types"]
        yolo_time = yolo_data["time"]

        print(f"🎯 YOLO: {yolo_weed_count} weeds, {yolo_crop_count} crops ({yolo_time:.3f}s)")
        for d in yolo_detections:
            print(f"   → {d['label']} ({d['type']}): {d['confidence']*100:.1f}%")

        # Unpack Roboflow results
        roboflow_result = robo_data["result"]
        roboflow_time = robo_data["time"]

        roboflow_detections = []
        roboflow_weed_count = 0
        roboflow_crop_count = 0
        roboflow_weed_types = []
        roboflow_error = None

        if 'error' not in roboflow_result:
            roboflow_detections = roboflow_result.get('detections', [])
            roboflow_weed_count = roboflow_result.get('weed_count', 0)
            roboflow_crop_count = roboflow_result.get('crop_count', 0)
            roboflow_weed_types = roboflow_result.get('weed_types', [])
            print(f"🌐 Roboflow: {roboflow_weed_count} weeds, {roboflow_crop_count} crops ({roboflow_time:.3f}s)")
            for d in roboflow_detections:
                print(f"   → {d['label']} ({d['type']}): {d['confidence']*100:.1f}%")
        else:
            roboflow_error = roboflow_result['error']
            print(f"⚠️ Roboflow: {roboflow_error}")

        print(f"⚡ Parallel execution: YOLO={yolo_time:.3f}s, Roboflow={roboflow_time:.3f}s → saved {abs(yolo_time + roboflow_time - max(yolo_time, roboflow_time)):.3f}s")

        # ======================
        # Cross-Model Verification
        # ======================
        # If YOLO says 'weed' but Roboflow says 'crop' in the same area,
        # reclassify as crop (YOLO has no crop classes, so low-confidence
        # weed detections on crops are common)
        if roboflow_detections:
            roboflow_crops = [d for d in roboflow_detections if d['type'] == 'crop']
            for yolo_det in yolo_detections:
                if yolo_det['type'] != 'weed':
                    continue
                for robo_crop in roboflow_crops:
                    # Calculate IoU between YOLO weed and Roboflow crop
                    yb = yolo_det['box']
                    rb = robo_crop['box']
                    xA = max(yb['xmin'], rb['xmin'])
                    yA = max(yb['ymin'], rb['ymin'])
                    xB = min(yb['xmax'], rb['xmax'])
                    yB = min(yb['ymax'], rb['ymax'])
                    inter = max(0, xB - xA) * max(0, yB - yA)
                    areaY = (yb['xmax'] - yb['xmin']) * (yb['ymax'] - yb['ymin'])
                    areaR = (rb['xmax'] - rb['xmin']) * (rb['ymax'] - rb['ymin'])
                    union = areaY + areaR - inter
                    iou = inter / union if union > 0 else 0

                    if iou > 0.3 and yolo_det['confidence'] < 0.50:
                        # Roboflow says crop, YOLO is unsure → reclassify as crop
                        print(f"   🔄 Reclassified: {yolo_det['label']} (YOLO weed {yolo_det['confidence']*100:.0f}%) → crop (Roboflow {robo_crop['label']} {robo_crop['confidence']*100:.0f}%)")
                        yolo_det['type'] = 'crop'
                        yolo_det['label'] = crop_name
                        yolo_det['description'] = f"{crop_name} (verified by Roboflow)"
                        yolo_weed_count -= 1
                        yolo_crop_count += 1
                        break  # Only reclassify once per detection

        # ======================
        # Crop Identification (optional)
        # ======================
        identified_crop = None
        if identify_crop:
            crop_id_result = identify_crop_with_roboflow(image_data)
            if 'error' not in crop_id_result:
                identified_crop = crop_id_result
                if crop_id_result.get('cropName'):
                    crop_name = crop_id_result['cropName']

        # ======================
        # Weed Removal Techniques
        # ======================
        removal_techniques = None
        combined_weed_types = list(set(yolo_weed_types + roboflow_weed_types))
        total_weed_count = max(yolo_weed_count, roboflow_weed_count)

        if total_weed_count > 0:
            techniques = generate_removal_techniques(crop_name, combined_weed_types, total_weed_count)
            if 'error' not in techniques:
                removal_techniques = techniques

        total_time = time.time() - start_time
        print(f"✅ Analysis done in {total_time:.3f}s — YOLO: {yolo_weed_count}W/{yolo_crop_count}C, Roboflow: {roboflow_weed_count}W/{roboflow_crop_count}C")

        # ======================
        # Response
        # ======================
        response_data = {
            "dualModel": True,
            "yolo": {
                "detections": yolo_detections,
                "count": len(yolo_detections),
                "weedCount": yolo_weed_count,
                "cropCount": yolo_crop_count,
                "summary": f"{yolo_weed_count} weed(s), {yolo_crop_count} crop(s)",
                "inferenceTime": round(yolo_time, 3),
                "model": "YOLOv11n-CottonWeedDet12"
            },
            "roboflow": {
                "detections": roboflow_detections,
                "count": len(roboflow_detections),
                "weedCount": roboflow_weed_count,
                "cropCount": roboflow_crop_count,
                "summary": f"{roboflow_weed_count} weed(s), {roboflow_crop_count} crop(s)",
                "inferenceTime": round(roboflow_time, 3),
                "model": "Roboflow",
                "error": roboflow_error
            },
            "cropType": crop_name,
            "totalInferenceTime": round(total_time, 3)
        }

        if identified_crop:
            response_data["identifiedCrop"] = identified_crop
        if removal_techniques:
            response_data["removalTechniques"] = removal_techniques

        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Analyze error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/identify-crop', methods=['POST'])
def identify_crop_endpoint():
    """Standalone crop identification endpoint."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        base64_image = data.get('image')
        if not base64_image:
            return jsonify({"error": "No image provided"}), 400

        image_data = base64.b64decode(base64_image)
        result = identify_crop_with_roboflow(image_data)

        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get-treatment', methods=['POST'])
def get_treatment_endpoint():
    """Standalone weed removal technique endpoint."""
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


# ============================================================
# EXPLAINABLE AI (XAI) ENDPOINT
# ============================================================

def extract_xai_features(detections, crop_name):
    """Extract structured features from YOLO detections for XAI."""
    weed_dets = [d for d in detections if d.get('type') == 'weed']
    crop_dets = [d for d in detections if d.get('type') == 'crop']

    # Weed species aggregation
    species_map = {}
    for d in weed_dets:
        label = d.get('label', 'unknown')
        if label not in species_map:
            species_map[label] = {'name': label, 'count': 0, 'total_conf': 0}
        species_map[label]['count'] += 1
        species_map[label]['total_conf'] += d.get('confidence', 0)

    weed_species = []
    for s in species_map.values():
        weed_species.append({
            'name': s['name'],
            'count': s['count'],
            'avgConfidence': round(s['total_conf'] / s['count'], 3) if s['count'] > 0 else 0
        })
    weed_species.sort(key=lambda x: x['count'], reverse=True)

    # Confidence stats
    all_confs = [d.get('confidence', 0) for d in weed_dets]
    avg_conf = round(sum(all_confs) / len(all_confs), 3) if all_confs else 0

    # Weed density & ratio
    total_weeds = len(weed_dets)
    total_crops = len(crop_dets)
    weed_density = min(1.0, total_weeds / 20.0)  # normalize: 20+ weeds = max density
    weed_crop_ratio = round(total_weeds / max(total_crops, 1), 2)

    # Spatial distribution analysis via bounding box centroids
    centroids = []
    for d in weed_dets:
        box = d.get('box', {})
        cx = (box.get('xmin', 0) + box.get('xmax', 0)) / 2
        cy = (box.get('ymin', 0) + box.get('ymax', 0)) / 2
        centroids.append((cx, cy))

    spatial = 'scattered'
    dominant_x, dominant_y = 0.5, 0.5

    if centroids:
        avg_x = sum(c[0] for c in centroids) / len(centroids)
        avg_y = sum(c[1] for c in centroids) / len(centroids)
        dominant_x, dominant_y = round(avg_x, 3), round(avg_y, 3)

        # Variance to determine clustering
        import math
        var_x = sum((c[0] - avg_x) ** 2 for c in centroids) / len(centroids)
        var_y = sum((c[1] - avg_y) ** 2 for c in centroids) / len(centroids)
        spread = math.sqrt(var_x + var_y)

        if spread < 0.15:
            spatial = 'clustered'
        elif spread < 0.25:
            # Check if primarily between rows (y-axis variation < x-axis)
            if var_y < var_x * 0.5:
                spatial = 'inter-row'
            else:
                spatial = 'clustered'
        elif avg_x < 0.15 or avg_x > 0.85 or avg_y < 0.15 or avg_y > 0.85:
            spatial = 'edge'
        else:
            spatial = 'scattered'

    return {
        'weedSpecies': weed_species,
        'totalWeedCount': total_weeds,
        'totalCropCount': total_crops,
        'weedDensity': round(weed_density, 3),
        'weedCropRatio': weed_crop_ratio,
        'avgConfidence': avg_conf,
        'spatialDistribution': spatial,
        'dominantRegion': {'x': dominant_x, 'y': dominant_y}
    }


def compute_spray_angle(features):
    """Compute optimal spraying angle from spatial features."""
    import math

    spatial = features['spatialDistribution']
    dom = features['dominantRegion']
    weed_count = features['totalWeedCount']

    if weed_count == 0:
        return {
            'angle': 0,
            'pattern': 'spot',
            'nozzleType': 'None needed',
            'reasoning': 'No weeds detected — no spraying required.',
            'confidence': 1.0
        }

    # Compute angle from image center (0.5, 0.5) to weed cluster centroid
    dx = dom['x'] - 0.5
    dy = dom['y'] - 0.5
    angle_rad = math.atan2(dy, dx)
    angle_deg = round(math.degrees(angle_rad)) % 360

    if spatial == 'clustered':
        pattern = 'directional'
        nozzle = 'Flat Fan Nozzle (110° spray angle)'
        reasoning = (
            f'Weeds are clustered around ({dom["x"]:.0%}, {dom["y"]:.0%}) of the image. '
            f'Direct spray at {angle_deg}° from center for targeted application. '
            f'A flat fan nozzle provides even coverage over concentrated weed patches.'
        )
        confidence = 0.85
    elif spatial == 'inter-row':
        pattern = 'inter-row'
        angle_deg = 90  # perpendicular to rows
        nozzle = 'Even Flat Fan Nozzle (80° spray angle)'
        reasoning = (
            'Weeds are distributed between crop rows. '
            'Apply spray perpendicular to rows (90°) using shielded inter-row nozzles '
            'to minimize crop contact. Even flat fan nozzles provide uniform inter-row coverage.'
        )
        confidence = 0.90
    elif spatial == 'edge':
        pattern = 'directional'
        nozzle = 'Deflector Nozzle (adjustable angle)'
        reasoning = (
            f'Weeds are concentrated at the edge of the field ({dom["x"]:.0%}, {dom["y"]:.0%}). '
            f'Target spray at {angle_deg}° toward the edge. '
            f'Use a deflector nozzle with adjustable angle for border precision.'
        )
        confidence = 0.80
    else:  # scattered
        pattern = 'broadcast'
        angle_deg = 360
        nozzle = 'Hollow Cone Nozzle (360° coverage)'
        reasoning = (
            f'Weeds are widely scattered across the field ({weed_count} detected). '
            f'Broadcast application at full 360° coverage recommended. '
            f'Hollow cone nozzles provide fine droplets for maximum contact.'
        )
        confidence = 0.75

    return {
        'angle': angle_deg,
        'pattern': pattern,
        'nozzleType': nozzle,
        'reasoning': reasoning,
        'confidence': confidence
    }


def fetch_openmeteo_weather(latitude, longitude):
    """Fetch real-time weather from OpenMeteo API using coordinates."""
    try:
        url = 'https://api.open-meteo.com/v1/forecast'
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation',
            'daily': 'precipitation_probability_max',
            'timezone': 'auto',
            'forecast_days': 1
        }
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})
            daily = data.get('daily', {})

            # Get precipitation probability from daily forecast
            precip_prob = 0
            if daily and daily.get('precipitation_probability_max'):
                precip_prob = daily['precipitation_probability_max'][0] or 0

            weather = {
                'temperature': current.get('temperature_2m', 20),
                'windSpeed': current.get('wind_speed_10m', 0),
                'windDirection': current.get('wind_direction_10m', 0),
                'humidity': current.get('relative_humidity_2m', 50),
                'precipitation': precip_prob,
                'source': 'OpenMeteo API (live)',
                'coordinates': {'latitude': latitude, 'longitude': longitude}
            }
            print(f"🌤️ OpenMeteo: {weather['temperature']}°C, wind={weather['windSpeed']} km/h, humidity={weather['humidity']}%, rain={weather['precipitation']}%")
            return weather
        else:
            print(f"⚠️ OpenMeteo API returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ OpenMeteo fetch error: {e}")
        return None


def evaluate_weather_suitability(weather_data):
    """Evaluate weather conditions for spray suitability."""
    if not weather_data:
        return {
            'canSpray': True,
            'score': 50,
            'temperature': {'value': 0, 'unit': '°C', 'suitable': True, 'reason': 'No weather data available'},
            'wind': {'speed': 0, 'direction': 0, 'suitable': True, 'reason': 'No weather data available'},
            'humidity': {'value': 0, 'suitable': True, 'reason': 'No weather data available'},
            'precipitation': {'probability': 0, 'suitable': True, 'reason': 'No weather data available'},
            'overallReason': 'Weather data unavailable — proceed with caution.'
        }

    temp = weather_data.get('temperature', 20)
    wind_speed = weather_data.get('windSpeed', 0)
    wind_dir = weather_data.get('windDirection', 0)
    humidity = weather_data.get('humidity', 50)
    precip = weather_data.get('precipitation', 0)

    score = 100
    reasons = []

    # Temperature check (optimal: 10-30°C / 50-86°F)
    temp_suitable = 10 <= temp <= 30
    if temp < 5:
        score -= 35
        temp_reason = f'{temp}°C is too cold — herbicide absorption is poor below 5°C.'
    elif temp < 10:
        score -= 15
        temp_reason = f'{temp}°C is cool — some herbicides may have reduced efficacy.'
    elif temp > 35:
        score -= 35
        temp_reason = f'{temp}°C is too hot — rapid evaporation reduces spray effectiveness.'
    elif temp > 30:
        score -= 15
        temp_reason = f'{temp}°C is warm — spray early morning/late evening to avoid drift.'
    else:
        temp_reason = f'{temp}°C is in optimal range (10-30°C) for herbicide application.'

    # Wind check (optimal: < 15 km/h)
    wind_suitable = wind_speed < 15
    if wind_speed > 25:
        score -= 40
        wind_reason = f'{wind_speed} km/h — DO NOT SPRAY. Extreme drift risk.'
    elif wind_speed > 15:
        score -= 25
        wind_reason = f'{wind_speed} km/h is high — significant spray drift expected.'
    elif wind_speed > 10:
        score -= 10
        wind_reason = f'{wind_speed} km/h — moderate drift risk. Use low-drift nozzles.'
    else:
        wind_reason = f'{wind_speed} km/h is calm — ideal for spraying.'

    # Humidity check (optimal: 40-90%)
    humidity_suitable = 40 <= humidity <= 90
    if humidity < 30:
        score -= 20
        hum_reason = f'{humidity}% is very dry — rapid evaporation will reduce coverage.'
    elif humidity < 40:
        score -= 10
        hum_reason = f'{humidity}% is low — some evaporation expected.'
    elif humidity > 90:
        score -= 15
        hum_reason = f'{humidity}% is very high — droplets may not adhere properly.'
    else:
        hum_reason = f'{humidity}% is in optimal range (40-90%).'

    # Precipitation check
    precip_suitable = precip < 20
    if precip > 60:
        score -= 40
        precip_reason = f'{precip}% rain probability — spray will be washed off.'
    elif precip > 30:
        score -= 20
        precip_reason = f'{precip}% rain probability — risk of herbicide washoff.'
    elif precip > 20:
        score -= 10
        precip_reason = f'{precip}% rain probability — monitor before spraying.'
    else:
        precip_reason = f'{precip}% rain probability — clear conditions.'

    score = max(0, score)
    can_spray = score >= 50

    if score >= 80:
        overall = 'Excellent spray conditions — all factors within optimal range.'
    elif score >= 60:
        overall = 'Acceptable conditions — proceed with adjustments for risk factors.'
    elif score >= 40:
        overall = 'Marginal conditions — consider postponing or use drift reduction methods.'
    else:
        overall = 'Poor conditions — DO NOT SPRAY. Wait for better weather window.'
        reasons_list = []
        if not temp_suitable: reasons_list.append('temperature')
        if not wind_suitable: reasons_list.append('wind')
        if not humidity_suitable: reasons_list.append('humidity')
        if not precip_suitable: reasons_list.append('precipitation')
        if reasons_list:
            overall += f' Issues: {", ".join(reasons_list)}.'

    return {
        'canSpray': can_spray,
        'score': score,
        'temperature': {'value': temp, 'unit': '°C', 'suitable': temp_suitable, 'reason': temp_reason},
        'wind': {'speed': wind_speed, 'direction': wind_dir, 'suitable': wind_suitable, 'reason': wind_reason},
        'humidity': {'value': humidity, 'suitable': humidity_suitable, 'reason': hum_reason},
        'precipitation': {'probability': precip, 'suitable': precip_suitable, 'reason': precip_reason},
        'overallReason': overall
    }


def generate_herbicide_recommendations(crop_name, features, weather_suitability):
    """Generate herbicide recommendations using Gemini with reasoning traces."""
    if not gemini_client:
        return []

    try:
        weed_list = ', '.join([f"{s['name']} ({s['count']}x, {s['avgConfidence']*100:.0f}% conf)"
                               for s in features['weedSpecies']]) or 'unidentified weeds'

        weather_ctx = ''
        if weather_suitability and weather_suitability.get('score', 0) > 0:
            ws = weather_suitability
            weather_ctx = f"""
Weather Conditions:
- Temperature: {ws['temperature']['value']}°C ({ws['temperature']['reason']})
- Wind: {ws['wind']['speed']} km/h ({ws['wind']['reason']})
- Humidity: {ws['humidity']['value']}% ({ws['humidity']['reason']})
- Rain Risk: {ws['precipitation']['probability']}% ({ws['precipitation']['reason']})
- Spray Score: {ws['score']}/100
"""

        prompt = f"""You are an expert agronomist specializing in precision herbicide management.

Field Analysis:
- Crop: {crop_name}
- Weeds Detected: {weed_list}
- Total Weeds: {features['totalWeedCount']}, Crops: {features['totalCropCount']}
- Weed Density: {features['weedDensity']*100:.0f}%
- Spatial Pattern: {features['spatialDistribution']}
{weather_ctx}

Recommend 2-3 herbicides. Return ONLY a JSON array with this schema:
[
  {{
    "name": "<herbicide class name, NOT brand — e.g., 'Glyphosate-based systemic'>",
    "activeIngredient": "<e.g., 'Glyphosate 41% SL'>",
    "herbicideClass": "<e.g., 'Non-selective systemic'>",
    "modeOfAction": "<brief mechanism — e.g., 'Inhibits EPSPS enzyme in amino acid synthesis'>",
    "applicationRate": "<e.g., '2-3 L/ha'>",
    "safeForCrop": true/false,
    "targetWeeds": ["<weed names this targets>"],
    "reasoning": "<2-3 sentences explaining WHY this herbicide was chosen given the specific weeds, crop type, density, and weather conditions>",
    "confidence": 0.0-1.0
  }}
]

Rules:
- Be specific to {crop_name} — recommend SELECTIVE herbicides safe for {crop_name} first
- Factor in the weed species detected
- Factor in weather conditions for timing advice in the reasoning
- If weed density is high (>50%), recommend pre+post emergent combination
- Return ONLY the JSON array, no markdown"""

        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        text = response.text.strip()

        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        return json.loads(text.strip())

    except Exception as e:
        print(f"❌ XAI herbicide recommendation error: {e}")
        return []


def compute_feature_importance(features, spray, weather):
    """Compute feature importance scores for explainability."""
    importances = []

    # Weed count importance
    weed_imp = min(1.0, features['totalWeedCount'] / 10.0)
    importances.append({
        'feature': 'Weed Count',
        'importance': round(weed_imp, 2),
        'description': f"{features['totalWeedCount']} weed(s) detected — {'high' if weed_imp > 0.6 else 'moderate' if weed_imp > 0.3 else 'low'} infestation level"
    })

    # Confidence importance
    importances.append({
        'feature': 'Detection Confidence',
        'importance': round(features['avgConfidence'], 2),
        'description': f"Average confidence: {features['avgConfidence']*100:.0f}% — {'high' if features['avgConfidence'] > 0.7 else 'moderate' if features['avgConfidence'] > 0.4 else 'low'} reliability"
    })

    # Spatial distribution importance
    spatial_map = {'clustered': 0.9, 'inter-row': 0.8, 'edge': 0.7, 'scattered': 0.5}
    spatial_imp = spatial_map.get(features['spatialDistribution'], 0.5)
    importances.append({
        'feature': 'Spatial Distribution',
        'importance': spatial_imp,
        'description': f"Weeds are {features['spatialDistribution']} — determines spray pattern ({spray['pattern']})"
    })

    # Weed density importance
    importances.append({
        'feature': 'Weed Density',
        'importance': round(features['weedDensity'], 2),
        'description': f"Density: {features['weedDensity']*100:.0f}% — {'broadcast spray needed' if features['weedDensity'] > 0.5 else 'targeted spray sufficient'}"
    })

    # Species diversity importance
    diversity = min(1.0, len(features['weedSpecies']) / 5.0)
    importances.append({
        'feature': 'Species Diversity',
        'importance': round(diversity, 2),
        'description': f"{len(features['weedSpecies'])} species — {'broad-spectrum herbicide needed' if diversity > 0.5 else 'species-specific treatment possible'}"
    })

    # Weather importance
    weather_imp = 1.0 - (weather.get('score', 50) / 100.0)
    importances.append({
        'feature': 'Weather Risk',
        'importance': round(weather_imp, 2),
        'description': f"Weather score: {weather.get('score', 50)}/100 — {'spray timing critical' if weather_imp > 0.5 else 'conditions acceptable'}"
    })

    importances.sort(key=lambda x: x['importance'], reverse=True)
    return importances


@app.route('/xai-explain', methods=['POST'])
def xai_explain():
    """Explainable AI endpoint — generates spray, weather, and herbicide recommendations from YOLO features."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        detections = data.get('detections', [])
        crop_name = (data.get('cropName') or 'Wheat').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # 1. Extract features from detections
        features = extract_xai_features(detections, crop_name)

        # 2. Compute spraying angle
        spray = compute_spray_angle(features)

        # 3. Fetch live weather from OpenMeteo using user location, then evaluate
        weather_data = None
        if latitude and longitude:
            weather_data = fetch_openmeteo_weather(latitude, longitude)
        weather = evaluate_weather_suitability(weather_data)

        # 4. Generate herbicide recommendations (via Gemini)
        herbicides = []
        if features['totalWeedCount'] > 0:
            herbicides = generate_herbicide_recommendations(crop_name, features, weather)

        # 5. Compute feature importance for explainability
        importance = compute_feature_importance(features, spray, weather)

        # 6. Overall confidence
        overall_conf = round(
            (spray['confidence'] * 0.3) +
            (features['avgConfidence'] * 0.3) +
            ((weather['score'] / 100.0) * 0.2) +
            (0.2 if herbicides else 0),
            2
        )

        from datetime import datetime
        response = {
            'features': features,
            'sprayingAngle': spray,
            'weatherSuitability': weather,
            'herbicides': herbicides,
            'featureImportance': importance,
            'overallConfidence': overall_conf,
            'generatedAt': datetime.now().isoformat()
        }

        print(f"🧠 XAI: {features['totalWeedCount']} weeds, spray={spray['pattern']} @ {spray['angle']}°, weather={weather['score']}/100, herbicides={len(herbicides)}")
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ XAI error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Image too large. Maximum 10MB allowed."}), 413

@app.errorhandler(408)
def request_timeout(error):
    return jsonify({"error": "Request timeout. Please try again."}), 408


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    use_ngrok = '--ngrok' in sys.argv or os.environ.get('USE_NGROK') == 'true'

    if use_ngrok and NGROK_AVAILABLE:
        try:
            ngrok_token = os.environ.get('NGROK_AUTH_TOKEN')
            if ngrok_token:
                ngrok.set_auth_token(ngrok_token)
            public_url = ngrok.connect(5000)
            print(f"\n{'='*50}")
            print(f"🌐 NGROK: {public_url}")
            print(f"{'='*50}\n")
        except Exception as e:
            print(f"⚠️ Ngrok failed: {e}")

    print(f"\nServer: http://localhost:5000")
    print(f"Use --ngrok for remote access\n")

    _port = int(os.environ.get('PORT', 5000))
    app.run(
        host="0.0.0.0",
        port=_port,
        debug=False,
        threaded=True,
        use_reloader=False
    )
