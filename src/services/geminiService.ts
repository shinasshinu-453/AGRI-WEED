import { GoogleGenAI, Type } from "@google/genai";
import { AnalysisResult, ProcessingMode } from "../types";
import { SYSTEM_INSTRUCTION, DETECTION_PROMPT } from "../constants";
import { getWeatherData, getDefaultLocation, formatTemperature, WeatherData } from './weatherService';

const envGeminiKey = import.meta.env.VITE_GEMINI_API_KEY || "";

const normalizeBox = (box: AnalysisResult["detections"][number]["box"]) => {
  const maxVal = Math.max(box.xmin, box.xmax, box.ymin, box.ymax);
  const divisor = maxVal > 1 ? 1000 : 1;
  return {
    ymin: box.ymin / divisor,
    xmin: box.xmin / divisor,
    ymax: box.ymax / divisor,
    xmax: box.xmax / divisor,
  };
};

export const generateWeedTreatmentPlan = async (
  apiKey: string = envGeminiKey,
  analysis: AnalysisResult,
  cropName: string = "General Crop",
  modelName: ProcessingMode = ProcessingMode.ACCURATE,
  includeWeather: boolean = true
): Promise<string> => {
  if (!apiKey) throw new Error("API Key is missing");

  const ai = new GoogleGenAI({ apiKey });

  // Fetch weather data if requested
  let weatherContext = '';
  if (includeWeather) {
    try {
      const location = getDefaultLocation();
      const weather = await getWeatherData(location.latitude, location.longitude);

      if (weather) {
        const sprayWindow = weather.sprayWindows.find(w => w.suitable);
        weatherContext = `

Current Environmental Conditions:
• Temperature: ${formatTemperature(weather.current.temperature)}
• Wind Speed: ${Math.round(weather.current.windSpeed)} mph
• Conditions: ${weather.current.conditions}
• Spray Suitability: ${sprayWindow ? '✓ SUITABLE - ' + sprayWindow.reason : '✗ NOT SUITABLE - Wait for better conditions'}
• Next Suitable Window: ${sprayWindow ? new Date(sprayWindow.date).toLocaleDateString() : 'Check forecast'}

Weather-Based Constraints:
- Avoid spraying if wind > 10 mph (current: ${Math.round(weather.current.windSpeed)} mph)
- Optimal temperature range: 50-85°F (current: ${formatTemperature(weather.current.temperature)})
- Check rain forecast before application
`;
      }
    } catch (error) {
      console.warn('Could not fetch weather data for treatment plan:', error);
    }
  }

  const detections = analysis.detections || [];
  const detectionSummary =
    detections
      .map(
        (det, idx) =>
          `#${idx + 1}: ${det.label} (${det.type}) conf=${Math.round(det.confidence * 100)}%`
      )
      .join("\n") || "No detections reported.";

  const prompt = `
You are an AI agronomy intelligence system operating within a precision weed-control platform.

System Inputs:
• Crop Profile: ${cropName}
• Weed Instances Detected: ${analysis.weedCount}
• Crop Instances Detected: ${analysis.cropCount}
${weatherContext}

Spatial Detection Data (class | type | confidence | coverage):
${detectionSummary}

Mission Objectives:
Analyze the detected weed signatures and generate optimized field actions:
- Recommend **precision control strategies** (selective/non-selective herbicide class, robotic or mechanical removal, or micro-dose spot spraying).
- Propose **intelligent herbicide timing** (pre-emergent vs post-emergent) aligned with crop growth stage.
- Estimate **operational cost impact** (low / medium / high per acre or hectare).
- Optimize **application windows** based on environmental constraints (rain probability, wind drift, thermal stress).
- Suggest **organic or low-impact alternatives** when chemical intervention is avoidable.
- Flag **safety, compliance, and human-in-the-loop requirements** for high-risk or low-confidence detections.
${includeWeather ? '- **CRITICAL**: Factor in current weather conditions for spray timing recommendations.' : ''}

Response Protocol:
• Output 3–6 high-signal bullet points
• Concise, data-driven, and action-oriented
• Maximum 120 words
• No brand names — reference methods or herbicide classes only
• Assume the output will guide semi-autonomous farm operations
`;


  const response = await ai.models.generateContent({
    model: modelName,
    contents: [
      {
        role: "user",
        parts: [
          {
            text: prompt,
          },
        ],
      },
    ],
  });

  const text = response.text;
  if (!text) throw new Error("No response from Gemini (treatment plan)");

  return text.trim();
};

export const analyzeImage = async (
  apiKey: string = envGeminiKey,
  base64Image: string,
  mimeType: string = "image/jpeg",
  cropName: string = "General Crop",
  modelName: ProcessingMode = ProcessingMode.FAST
): Promise<AnalysisResult> => {
  if (!apiKey) throw new Error("API Key is missing");

  const ai = new GoogleGenAI({ apiKey });

  // Define the schema to strictly structure the output,
  // replacing the traditional YOLO detection head.
  const responseSchema = {
    type: Type.OBJECT,
    properties: {
      detections: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            label: { type: Type.STRING, description: "Specific plant name if known, or 'Weed'/'Crop'" },
            type: { type: Type.STRING, enum: ["weed", "crop"] },
            confidence: { type: Type.NUMBER, description: "Confidence score 0.0 to 1.0" },
            box: {
              type: Type.OBJECT,
              properties: {
                ymin: { type: Type.NUMBER },
                xmin: { type: Type.NUMBER },
                ymax: { type: Type.NUMBER },
                xmax: { type: Type.NUMBER },
              },
              required: ["ymin", "xmin", "ymax", "xmax"],
            },
            description: { type: Type.STRING, description: "Brief morphological description (e.g., 'Broadleaf', 'Serrated edge')" },
          },
          required: ["label", "type", "confidence", "box"],
        },
      },
      summary: { type: Type.STRING, description: "Overall assessment of weed pressure." },
      weedCount: { type: Type.INTEGER },
      cropCount: { type: Type.INTEGER },
    },
    required: ["detections", "summary", "weedCount", "cropCount"],
  };

  // Construct a context-aware prompt to improve separation
  const dynamicPrompt = `${DETECTION_PROMPT}
  
  CONTEXTUAL OVERRIDE:
  The target planted crop is "${cropName}".
  
  CRITICAL CLASSIFICATION RULES:
  1. DOES IT LOOK LIKE ${cropName}? 
     -> If YES: Label as 'crop'.
     -> If NO: Label as 'weed'.
  
  2. ROW ALIGNMENT:
     -> If it is part of the main planted row and looks like ${cropName}: 'crop'.
     -> If it is between rows: 'weed'.
     -> If it is IN the row but looks different (shape/color): 'weed'.

  3. PHENOTYPIC SIMILARITY:
     -> Use the known visual traits of ${cropName} to separate it from everything else.
  `;

  try {
    const response = await ai.models.generateContent({
      model: modelName,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: "application/json",
        responseSchema: responseSchema,
        temperature: 0.2, // Low temperature for higher precision (like YOLO)
      },
      contents: [
        {
          role: "user",
          parts: [
            {
              inlineData: {
                mimeType: mimeType,
                data: base64Image,
              },
            },
            {
              text: dynamicPrompt,
            },
          ],
        },
      ],
    });

    const text = response.text;
    if (!text) throw new Error("No response from Gemini");

    const parsed = JSON.parse(text) as AnalysisResult;
    const normalizedDetections = (parsed.detections ?? []).map((det) => ({
      ...det,
      box: normalizeBox(det.box),
    }));

    return {
      ...parsed,
      detections: normalizedDetections,
    };
  } catch (error) {
    console.error("Gemini Vision API Error:", error);
    throw error;
  }
};
