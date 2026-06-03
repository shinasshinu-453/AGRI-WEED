// Box coordinates normalized 0-1 for UI overlays. Gemini responses are normalized down if they return 0-1000.
export interface BoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
}

export interface Detection {
  label: string;
  confidence: number;
  box: BoundingBox;
  type: 'weed' | 'crop';
  description?: string;
  raw_class?: string;
  model_class_id?: number;
}

export interface CropIdentification {
  cropName: string;
  confidence: number;
  characteristics?: string;
}

export interface RemovalTechniques {
  manual?: string;
  chemical?: string;
  organic?: string;
  mechanical?: string;
  priority: 'manual' | 'chemical' | 'organic' | 'mechanical';
  timing?: string;
}

export interface ModelStats {
  detections: Detection[];
  count: number;
  weedCount: number;
  cropCount: number;
  summary: string;
  inferenceTime: number;
  model: string;
  error?: string | null;
}

export interface AnalysisResult {
  detections: Detection[];
  summary: string;
  weedCount: number;
  cropCount: number;
  inferenceTime?: number;
  actionPlan?: string;
  identifiedCrop?: CropIdentification;
  removalTechniques?: RemovalTechniques;
  _dualModel?: {
    yolo: ModelStats;
    roboflow: ModelStats;
  };
}

// ============================================================
// EXPLAINABLE AI (XAI) TYPES
// ============================================================

export interface XAIFeatures {
  weedSpecies: { name: string; count: number; avgConfidence: number }[];
  totalWeedCount: number;
  totalCropCount: number;
  weedDensity: number;
  weedCropRatio: number;
  avgConfidence: number;
  spatialDistribution: 'clustered' | 'scattered' | 'inter-row' | 'edge';
  dominantRegion: { x: number; y: number };
}

export interface SprayingAngleRecommendation {
  angle: number;
  pattern: 'directional' | 'broadcast' | 'inter-row' | 'spot';
  nozzleType: string;
  reasoning: string;
  confidence: number;
}

export interface WeatherSuitability {
  canSpray: boolean;
  score: number;
  temperature: { value: number; unit: string; suitable: boolean; reason: string };
  wind: { speed: number; direction: number; suitable: boolean; reason: string };
  humidity: { value: number; suitable: boolean; reason: string };
  precipitation: { probability: number; suitable: boolean; reason: string };
  overallReason: string;
}

export interface HerbicideRecommendation {
  name: string;
  activeIngredient: string;
  herbicideClass: string;
  modeOfAction: string;
  applicationRate: string;
  safeForCrop: boolean;
  targetWeeds: string[];
  reasoning: string;
  confidence: number;
}

export interface XAIExplanation {
  features: XAIFeatures;
  sprayingAngle: SprayingAngleRecommendation;
  weatherSuitability: WeatherSuitability;
  herbicides: HerbicideRecommendation[];
  featureImportance: { feature: string; importance: number; description: string }[];
  overallConfidence: number;
  generatedAt: string;
}

// Maps to the PD-YOLO paper concepts
export enum ProcessingMode {
  FAST = 'gemini-2.5-flash', // Comparable to YOLOv11n speed
  ACCURATE = 'gemini-2.5-pro', // Comparable to DyHead/HARFM precision
}

export type DetectionBackend = 'yolo' | 'gemini';
