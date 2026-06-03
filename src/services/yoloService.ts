import { AnalysisResult } from "../types";

const getAPIURL = () => {
  // Prefer explicit env override (set this to your ngrok URL for remote access)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  const host = window.location.hostname;

  // Local development — Flask always on 5000 via HTTP
  if (host === 'localhost' || host === '127.0.0.1') {
    return `http://localhost:5000`;
  }

  // LAN access (e.g. https://192.168.1.x:3000): Flask is still plain HTTP on port 5000.
  // Mixed-content will be blocked by Chrome unless VITE_API_URL points to the ngrok HTTPS URL.
  // We still try HTTP here; if blocked, user must set VITE_API_URL=<ngrok-url> in .env
  return `http://${host}:5000`;
};

const API_URL = getAPIURL();

// Calculate Intersection over Union (IoU) between two bounding boxes
const calculateIoU = (boxA: any, boxB: any): number => {
  const xA = Math.max(boxA.xmin, boxB.xmin);
  const yA = Math.max(boxA.ymin, boxB.ymin);
  const xB = Math.min(boxA.xmax, boxB.xmax);
  const yB = Math.min(boxA.ymax, boxB.ymax);

  const interWidth = Math.max(0, xB - xA);
  const interHeight = Math.max(0, yB - yA);
  const interArea = interWidth * interHeight;

  const areaA = (boxA.xmax - boxA.xmin) * (boxA.ymax - boxA.ymin);
  const areaB = (boxB.xmax - boxB.xmin) * (boxB.ymax - boxB.ymin);
  const unionArea = areaA + areaB - interArea;

  return unionArea > 0 ? interArea / unionArea : 0;
};

export const analyzeImage = async (
  base64Image: string,
  cropName: string = 'Wheat',
  identifyCrop: boolean = false
): Promise<AnalysisResult> => {

  if (!base64Image) throw new Error("Image data is missing");

  try {
    const endpoint = `${API_URL}/analyze`;
    console.log(`📸 Sending to backend (DUAL MODEL): ${endpoint}`);
    console.log(`📤 Image size: ${(base64Image.length / 1024).toFixed(2)} KB`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',  // bypass ngrok interstitial page
      },
      body: JSON.stringify({
        image: base64Image,
        cropName: cropName,
        identifyCrop: identifyCrop,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMsg = `Server error: ${response.status}`;
      try {
        const error = await response.json();
        errorMsg = error.error || errorMsg;
      } catch (e) {
        errorMsg = `${response.status} ${response.statusText}`;
      }
      throw new Error(errorMsg);
    }

    const data = await response.json();

    // Handle dual model response - transform to expected format
    if (data.dualModel) {
      console.log(`✅ DUAL MODEL RESPONSE:`);
      console.log(`   🎯 YOLO: ${data.yolo.weedCount} weeds, ${data.yolo.cropCount} crops (${data.yolo.inferenceTime}s)`);
      console.log(`   🌐 Roboflow: ${data.roboflow.weedCount} weeds, ${data.roboflow.cropCount} crops (${data.roboflow.inferenceTime}s)`);

      // Start with YOLO detections (trained on our 12 weed classes)
      const mergedDetections = [...(data.yolo.detections || [])];

      // Add Roboflow detections that don't overlap with YOLO (IoU < 0.3)
      if (data.roboflow.detections && !data.roboflow.error) {
        for (const rDet of data.roboflow.detections) {
          const overlaps = mergedDetections.some((yDet: any) => {
            if (!yDet.box || !rDet.box) return false;
            return calculateIoU(yDet.box, rDet.box) > 0.3;
          });
          if (!overlaps) {
            mergedDetections.push(rDet);
          }
        }
      }

      // Count from merged detections
      const weedCount = mergedDetections.filter((d: any) => d.type === 'weed').length;
      const cropCount = mergedDetections.filter((d: any) => d.type === 'crop').length;

      // Only include identifiedCrop if there are actual crop detections
      const identifiedCrop = cropCount > 0 ? data.identifiedCrop : undefined;

      const compatibleData = {
        detections: mergedDetections,
        count: mergedDetections.length,
        weedCount,
        cropCount,
        summary: `Detected ${weedCount} weed(s) and ${cropCount} crop(s)`,
        inferenceTime: data.totalInferenceTime,
        cropType: data.cropType,
        identifiedCrop,
        removalTechniques: data.removalTechniques,
        _dualModel: {
          yolo: data.yolo,
          roboflow: data.roboflow
        }
      };

      console.log(`🔄 Final: ${mergedDetections.length} detections (${weedCount} weeds, ${cropCount} crops)`);

      return compatibleData as AnalysisResult;
    } else {
      // Legacy single model response
      console.log(`✅ Got response: ${data.detections?.length || 0} detections, ${data.weedCount} weeds, ${data.cropCount} crops`);
    }

    if (data.identifiedCrop) {
      console.log(`🌾 Identified crop: ${data.identifiedCrop.cropName} (${(data.identifiedCrop.confidence * 100).toFixed(1)}%)`);
    }

    return data as AnalysisResult;

  } catch (error: any) {
    console.error("❌ Error:", error.message);
    console.error("📍 API URL:", API_URL);
    if (error.name === 'AbortError') {
      throw new Error('API request timeout - backend may be slow');
    }
    if (error.message?.includes('Failed to fetch')) {
      throw new Error(`Failed to reach backend at ${API_URL}/analyze. Ensure the server is running and reachable.`);
    }
    throw error;
  }
};
