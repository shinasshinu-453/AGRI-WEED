import { Detection, XAIExplanation } from "../types";

const getAPIURL = () => {
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
        return `http://localhost:5000`;
    }
    return `http://${host}:5000`;
};

const API_URL = getAPIURL();

export const getXAIExplanation = async (
    detections: Detection[],
    cropName: string = 'Wheat',
    latitude?: number,
    longitude?: number
): Promise<XAIExplanation> => {
    try {
        const endpoint = `${API_URL}/xai-explain`;
        console.log(`🧠 Requesting XAI explanation: ${endpoint}`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',  // bypass ngrok interstitial page
            },
            body: JSON.stringify({
                detections,
                cropName,
                latitude: latitude || null,
                longitude: longitude || null,
            }),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            let errorMsg = `Server error: ${response.status}`;
            try {
                const error = await response.json();
                errorMsg = error.error || errorMsg;
            } catch { /* use default */ }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        console.log(`✅ XAI: ${data.herbicides?.length || 0} herbicides, spray=${data.sprayingAngle?.pattern}, weather=${data.weatherSuitability?.score}/100`);
        return data as XAIExplanation;

    } catch (error: any) {
        console.error("❌ XAI Error:", error.message);
        if (error.name === 'AbortError') {
            throw new Error('XAI request timeout — backend may be slow');
        }
        throw error;
    }
};
