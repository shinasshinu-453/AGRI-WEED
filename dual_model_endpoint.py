"""
Dual Model Analyze Endpoint - Runs both YOLO and Roboflow simultaneously
This replaces the old /analyze endpoint in server.py
"""

@app.route('/analyze', methods=['POST'])
def analyze():
    start_time = time.time()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        base64_image = data.get('image')
        crop_name = (data.get('cropName') or 'Wheat').strip()
        identify_crop = data.get('identifyCrop', False)
        
        print(f"\n📋 Request: Running BOTH models simultaneously for {crop_name}")

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

        # ============================================
        # RUN BOTH MODELS SIMULTANEOUSLY
        # ============================================
        
        # --- YOLO Detection ---
        print("\n🎯 YOLOv11n Detection:")
        orig_h, orig_w = img.shape[:2]
        img_resized = resize_image_for_inference(img, max_size=640)
        h, w = img_resized.shape[:2]

        yolo_start = time.time()
        results = model(img_resized, conf=0.1, verbose=False, device=device, imgsz=640, max_det=100)
        yolo_time = time.time() - yolo_start

        yolo_detections = []
        yolo_weed_count = 0
        yolo_crop_count = 0
        yolo_weed_types = []

        for result in results:
            if result.boxes is not None:
                for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                    x1, y1, x2, y2 = box.tolist()
                    class_name = model.names[int(cls)]
                    
                    scale_x = orig_w / w
                    scale_y = orig_h / h
                    
                    det_type = get_crop_type(class_name, crop_name)

                    if det_type == "weed":
                        yolo_weed_count += 1
                        yolo_weed_types.append(class_name)
                    else:
                        yolo_crop_count += 1

                    yolo_detections.append({
                        "label": class_name,
                        "confidence": float(conf),
                        "box": {
                            "xmin": (x1 * scale_x) / orig_w,
                            "ymin": (y1 * scale_y) / orig_h,
                            "xmax": (x2 * scale_x) / orig_w,
                            "ymax": (y2 * scale_y) / orig_h,
                        },
                        "type": det_type,
                        "description": f"{class_name} ({float(conf)*100:.1f}%)",
                        "raw_class": class_name
                    })

        print(f"✅ YOLO: {yolo_weed_count} weeds, {yolo_crop_count} crops ({yolo_time:.3f}s)")

        # --- Roboflow Detection ---
        print("\n🌐 Roboflow Detection:")
        roboflow_start = time.time()
        roboflow_result = detect_with_roboflow(image_data, crop_name)
        roboflow_time = time.time() - roboflow_start
        
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
            print(f"✅ Roboflow: {roboflow_weed_count} weeds, {roboflow_crop_count} crops ({roboflow_time:.3f}s)")
        else:
            roboflow_error = roboflow_result['error']
            print(f"⚠️ Roboflow error: {roboflow_error}")

        # --- Crop Identification ---
        identified_crop = None
        if identify_crop:
            crop_id_result = identify_crop_with_roboflow(image_data)
            if 'error' not in crop_id_result:
                identified_crop = crop_id_result

        # --- Weed Removal Techniques ---
        removal_techniques = None
        combined_weed_types = list(set(yolo_weed_types + roboflow_weed_types))
        total_weed_count = max(yolo_weed_count, roboflow_weed_count)
        
        if total_weed_count > 0:
            techniques = generate_removal_techniques(crop_name, combined_weed_types, total_weed_count)
            if 'error' not in techniques:
                removal_techniques = techniques

        total_time = time.time() - start_time

        # ============================================
        # RETURN DUAL MODEL RESULTS
        # ============================================
        response_data = {
            "dualModel": True,
            "yolo": {
                "detections": yolo_detections,
                "count": len(yolo_detections),
                "weedCount": yolo_weed_count,
                "cropCount": yolo_crop_count,
                "summary": f"{yolo_weed_count} weed(s), {yolo_crop_count} crop(s)",
                "inferenceTime": round(yolo_time, 3),
                "model": "YOLOv11n"
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
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
