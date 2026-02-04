import React, { useState, useEffect, useRef } from 'react';
import { AnalysisResult, Detection } from '../types';
import { Maximize2, Info } from 'lucide-react';

interface ResultsOverlayProps {
  imageSrc: string;
  result: AnalysisResult | null;
}

export const ResultsOverlay: React.FC<ResultsOverlayProps> = ({ imageSrc, result }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredBox, setHoveredBox] = useState<number | null>(null);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    // Image loaded
  };

  // Determine color based on detection type
  const getBoxColor = (type: string) => {
    return type === 'weed' ? 'border-red-500 bg-red-500/20' : 'border-emerald-500 bg-emerald-500/10';
  };
  
  const getLabelColor = (type: string) => {
    return type === 'weed' ? 'bg-red-500' : 'bg-emerald-500';
  };

  return (
    <div className="relative w-full rounded-xl overflow-hidden shadow-lg border border-slate-200 bg-slate-900 group">
      <img 
        src={imageSrc} 
        alt="Analyzed Field" 
        className="w-full h-auto block"
        onLoad={handleImageLoad}
      />
      
      {/* Legend */}
      {result && (
        <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm p-3 rounded-lg shadow-lg z-40 border border-slate-200 flex flex-col gap-2">
           <div className="flex items-center gap-2">
             <div className="w-3 h-3 rounded-full bg-red-500"></div>
             <span className="text-xs font-semibold text-slate-700">Weed</span>
           </div>
           <div className="flex items-center gap-2">
             <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
             <span className="text-xs font-semibold text-slate-700">Crop</span>
           </div>
        </div>
      )}

      {/* Overlay Layer */}
      {result && (
        <div className="absolute inset-0 pointer-events-none">
          {!result.detections || result.detections.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-white text-sm bg-black/30">
              <span>No detections found in this image</span>
            </div>
          ) : (
            <>
              <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                {result.detections.length} detection{result.detections.length !== 1 ? 's' : ''}
              </div>
              {result.detections.map((det, index) => {
            // Convert normalized [0-1] coordinates from the server into percentages
            const top = det.box.ymin * 100;
            const left = det.box.xmin * 100;
            const width = (det.box.xmax - det.box.xmin) * 100;
            const height = (det.box.ymax - det.box.ymin) * 100;

            const isHovered = hoveredBox === index;

            return (
              <div
                key={index}
                className={`absolute transition-all duration-200 border-2 pointer-events-auto cursor-help
                  ${getBoxColor(det.type)} ${isHovered ? 'z-20 border-opacity-100 opacity-100' : 'border-opacity-70 opacity-80'}`}
                style={{
                  top: `${top}%`,
                  left: `${left}%`,
                  width: `${width}%`,
                  height: `${height}%`,
                }}
                onMouseEnter={() => setHoveredBox(index)}
                onMouseLeave={() => setHoveredBox(null)}
              >
                {/* Detection Label - mimics the bounding box labels in PD-YOLO */}
                <div className={`absolute -top-7 left-0 px-2 py-0.5 text-xs font-bold text-white rounded-t shadow-sm flex items-center gap-1
                  ${getLabelColor(det.type)} ${isHovered ? 'opacity-100' : 'opacity-80'}`}>
                  <span>{det.label}</span>
                  <span className="opacity-75 text-[10px]">{Math.round(det.confidence * 100)}%</span>
                </div>
                
                {/* Tooltip for morphological description (The "Feature Fusion" insight) */}
                {isHovered && det.description && (
                  <div className="absolute top-full mt-1 left-0 bg-slate-800 text-white text-xs p-2 rounded shadow-xl w-48 z-30 pointer-events-none">
                    <p className="font-semibold mb-1">Morphology:</p>
                    {det.description}
                  </div>
                )}
              </div>
            );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
};