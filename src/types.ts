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

export interface AnalysisResult {
  detections: Detection[];
  summary: string;
  weedCount: number;
  cropCount: number;
  actionPlan?: string;
  identifiedCrop?: CropIdentification;
  removalTechniques?: RemovalTechniques;
}

// Maps to the PD-YOLO paper concepts
export enum ProcessingMode {
  FAST = 'gemini-2.5-flash', // Comparable to YOLOv8n speed
  ACCURATE = 'gemini-2.5-pro', // Comparable to DyHead/HARFM precision
}

export type DetectionBackend = 'yolo' | 'gemini';
