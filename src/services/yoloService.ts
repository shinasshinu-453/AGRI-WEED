import { AnalysisResult } from "../types";

const getAPIURL = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  const protocol = window.location.protocol;
  const host = window.location.hostname;
  const port = window.location.port ? `:${window.location.port}` : '';

  if (host === 'localhost' || host === '127.0.0.1') {
    return `http://localhost:5000`;
  }

  return `${protocol}//${host}:5000`;
};

const API_URL = getAPIURL();

export const analyzeImage = async (
  base64Image: string,
  cropName: string = 'Wheat',
  identifyCrop: boolean = false,
  useRoboflow: boolean = false
): Promise<AnalysisResult> => {

  if (!base64Image) throw new Error("Image data is missing");

  try {
    const endpoint = `${API_URL}/analyze`;
    console.log(`📸 Sending frame to: ${endpoint}`);
    console.log(`📤 Frame size: ${(base64Image.length / 1024).toFixed(2)} KB`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image: base64Image,
        cropName: cropName,
        identifyCrop: identifyCrop,
        useRoboflow: useRoboflow,
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
    console.log(`✅ Got response: ${data.detections?.length || 0} detections, ${data.weedCount} weeds, ${data.cropCount} crops`);
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
      throw new Error(`Failed to reach backend at ${API_URL}/analyze. Ensure the YOLO server is running and reachable from your browser (check VITE_API_URL, CORS, and http/https).`);
    }
    throw error;
  }
};
