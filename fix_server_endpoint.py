# Script to fix the server.py analyze endpoint for dual model output
# Run this to complete the dual model implementation

import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the duplicate old code between lines 562-714
# This removes the old if use_roboflow and else YOLO-only branches

# Pattern to match from "# --- Crop Identification ---" at line 562 
# to the end of the old analyze function
pattern = r'(        # --- Crop Identification ---\n        identified_crop = None\n        if identify_crop:)\n            print\("🔬 Using Roboflow for detection..."\).*?(\n    except Exception as e:\n        return jsonify\(\{"error": str\(e\)\}\), 500)'

replacement = r'''\1
            print("\n🌾 Identifying crop with Roboflow...")
            crop_id_result = identify_crop_with_roboflow(image_data)
            if 'error' not in crop_id_result:
                identified_crop = crop_id_result
                if crop_id_result.get('cropName'):
                    crop_name = crop_id_result['cropName']
                    print(f"✅ Using identified crop: {crop_name}")

        # --- Generate Weed Removal Techniques ---
        removal_techniques = None
        combined_weed_types = list(set(yolo_weed_types + roboflow_weed_types))
        total_weed_count = max(yolo_weed_count, roboflow_weed_count)
        
        if total_weed_count > 0:
            print(f"\n🌿 Generating removal techniques for {crop_name}...")
            techniques = generate_removal_techniques(crop_name, combined_weed_types, total_weed_count)
            if 'error' not in techniques:
                removal_techniques = techniques

        total_time = time.time() - start_time

        print(f"\n✅ Dual model analysis complete in {total_time:.3f}s")
        print(f"   - YOLO: {yolo_weed_count} weeds, {yolo_crop_count} crops")
        print(f"   - Roboflow: {roboflow_weed_count} weeds, {roboflow_crop_count} crops")

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
                "model": "YOLOv11"
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

        return jsonify(response_data), 200\2'''

# Apply the replacement
content_new = re.sub(pattern, replacement, content, flags=re.DOTALL)

if content_new != content:
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content_new)
    print("✅ Successfully updated server.py with dual model endpoint")
else:
    print("⚠️ Pattern not found, manual fix needed")
    print("Trying simpler approach...")
    
    # Simpler approach: just remove lines 565-714
    lines = content.split('\n')
    # Keep everything before line 565 and after line 714
    # Insert our new code at line 565
    
    new_code = '''            print("\\n🌾 Identifying crop with Roboflow...")
            crop_id_result = identify_crop_with_roboflow(image_data)
            if 'error' not in crop_id_result:
                identified_crop = crop_id_result
                if crop_id_result.get('cropName'):
                    crop_name = crop_id_result['cropName']
                    print(f"✅ Using identified crop: {crop_name}")

        # --- Generate Weed Removal Techniques ---
        removal_techniques = None
        combined_weed_types = list(set(yolo_weed_types + roboflow_weed_types))
        total_weed_count = max(yolo_weed_count, roboflow_weed_count)
        
        if total_weed_count > 0:
            print(f"\\n🌿 Generating removal techniques for {crop_name}...")
            techniques = generate_removal_techniques(crop_name, combined_weed_types, total_weed_count)
            if 'error' not in techniques:
                removal_techniques = techniques

        total_time = time.time() - start_time

        print(f"\\n✅ Dual model analysis complete in {total_time:.3f}s")
        print(f"   - YOLO: {yolo_weed_count} weeds, {yolo_crop_count} crops")
        print(f"   - Roboflow: {roboflow_weed_count} weeds, {roboflow_crop_count} crops")

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
                "model": "YOLOv11"
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
        print(f"\\n❌ Error in analyze endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500'''
    
    # Find the line with "# --- Crop Identification ---" after our new YOLO/Roboflow code
    found_idx = -1
    for i in range(560, min(len(lines), 600)):
        if '# --- Crop Identification ---' in lines[i] and 'identified_crop = None' in lines[i+1]:
            found_idx = i
            break
    
    if found_idx > 0:
        # Find the end of the analyze function
        end_idx = -1
        for i in range(found_idx, min(len(lines), 750)):
            if i > found_idx and lines[i].startswith('@app.route'):
                end_idx = i
                break
        
        if end_idx > 0:
            # Replace lines from found_idx to end_idx
            new_lines = lines[:found_idx] + new_code.split('\n') + lines[end_idx:]
            with open('server.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            print(f"✅ Replaced lines {found_idx} to {end_idx}")
        else:
            print(f"❌ Could not find end of function")
    else:
        print("❌ Could not find insertion point")
