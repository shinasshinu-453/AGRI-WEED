import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, StopCircle, AlertCircle, Loader2 } from 'lucide-react';
import { analyzeImage } from '../services/yoloService';
import { generateWeedTreatmentPlan } from '../services/geminiService';
import { addDetection } from '../services/firebaseService';
import { useAuthStore } from '../store/authStore';
import { AnalysisResult, Detection, ProcessingMode } from '../types';
import toast, { Toaster } from 'react-hot-toast';

const envGeminiKey = import.meta.env.VITE_GEMINI_API_KEY || '';

export const RealTimeDetector: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [cropType, setCropType] = useState('Wheat');
  const [detectionStats, setDetectionStats] = useState({ weeds: 0, crops: 0, fps: 0 });
  const [actionPlan, setActionPlan] = useState<string | null>(null);
  const [isPlanLoading, setIsPlanLoading] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [geminiKey, setGeminiKey] = useState(envGeminiKey);
  const [processingMode, setProcessingMode] = useState<ProcessingMode>(ProcessingMode.FAST);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const detectionIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const fpsCounterRef = useRef({ frames: 0, lastTime: Date.now() });
  const lastPlanSignatureRef = useRef<string | null>(null);
  const lastPlanTimeRef = useRef<number>(0);
  const lastSaveTimeRef = useRef<number>(0);
  const { user } = useAuthStore();

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      console.log('🎥 Requesting camera access...');

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera API not available. Your browser may not support camera access.');
      }

      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      console.log('✅ Camera access granted');

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          console.log('✅ Video stream ready');
        };
        await videoRef.current.play();
      }

      setIsActive(true);

      let isProcessing = false;
      let frameCount = 0;
      let fps = 0;
      let lastFpsTime = Date.now();

      detectionIntervalRef.current = setInterval(async () => {
        if (!videoRef.current || !canvasRef.current || isProcessing) return;

        isProcessing = true;

        try {
          const canvas = canvasRef.current;
          const video = videoRef.current;

          if (video.videoWidth === 0 || video.videoHeight === 0) {
            console.warn('⏳ Waiting for video dimensions...');
            isProcessing = false;
            return;
          }

          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          const ctx = canvas.getContext('2d');
          if (!ctx) {
            isProcessing = false;
            return;
          }

          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

          const scaledCanvas = document.createElement('canvas');
          scaledCanvas.width = 640;
          scaledCanvas.height = 360;
          const scaledCtx = scaledCanvas.getContext('2d');
          if (scaledCtx) {
            scaledCtx.drawImage(canvas, 0, 0, 640, 360);
          }

          const frameBase64 = scaledCanvas.toDataURL('image/jpeg', 0.35).split(',')[1];
          console.log(`📸 Frame captured: canvas=${canvas.width}x${canvas.height}, scaled=640x360, payload=${(frameBase64.length / 1024).toFixed(1)}KB`);

          const analysisResult = await analyzeImage(frameBase64, cropType);

          if (!analysisResult.detections) {
            console.warn('⚠️ No detections in response');
            console.log(`🎨 Drawing 0 detections (clearing canvas)`);
            drawDetections(canvas, [], ctx);
            setResult({ detections: [], weedCount: 0, cropCount: 0, summary: 'No detections found' });
          } else {
            console.log(`📊 Response: ${analysisResult.detections.length} detections (${analysisResult.weedCount} weeds, ${analysisResult.cropCount} crops)`);
            console.log(`🎨 Drawing ${analysisResult.detections.length} detections on canvas (${canvas.width}x${canvas.height})`);
            drawDetections(canvas, analysisResult.detections, ctx);
            setResult(analysisResult);
          }

          frameCount++;
          const now = Date.now();
          if (now - lastFpsTime >= 1000) {
            fps = frameCount;
            frameCount = 0;
            lastFpsTime = now;
            console.log(`📊 FPS: ${fps}`);
          }

          if (analysisResult.detections) {
            setDetectionStats({
              weeds: analysisResult.weedCount,
              crops: analysisResult.cropCount,
              fps: fps,
            });

            // Save to Firebase every 10 seconds if there are detections
            const now = Date.now();
            if (now - lastSaveTimeRef.current > 10000 && (analysisResult.weedCount > 0 || analysisResult.cropCount > 0)) {
              lastSaveTimeRef.current = now;
              try {
                await addDetection({
                  filename: `realtime_${new Date().toISOString()}.jpg`,
                  weedsDetected: analysisResult.weedCount || 0,
                  cropsDetected: analysisResult.cropCount || 0,
                  status: 'processed',
                  userId: user?.email || 'anonymous',
                  cropType: cropType,
                });
                toast.success('Real-time detection saved!', { duration: 2000 });
              } catch (firebaseErr) {
                console.error('Failed to save real-time detection:', firebaseErr);
              }
            }
          } else {
            setDetectionStats({
              weeds: 0,
              crops: 0,
              fps: fps,
            });
          }
        } catch (err: any) {
          console.error('❌ Error:', err.message);
          setError(`Detection failed: ${err.message}`);
        } finally {
          isProcessing = false;
        }
      }, 100);

    } catch (err: any) {
      console.error('❌ Camera error:', err);
      let errorMsg = 'Failed to access camera. ';

      if (err.name === 'NotAllowedError') {
        errorMsg += 'Camera permission denied. Check browser settings.';
      } else if (err.name === 'NotFoundError') {
        errorMsg += 'No camera device found.';
      } else if (err.name === 'NotReadableError') {
        errorMsg += 'Camera is being used by another application.';
      } else {
        errorMsg += err.message || 'Unknown error occurred.';
      }

      setError(errorMsg);
      setIsActive(false);
    }
  }, [cropType]);

  const stopCamera = useCallback(() => {
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    setResult(null);
    setDetectionStats({ weeds: 0, crops: 0, fps: 0 });
    setActionPlan(null);
    setPlanError(null);
    setIsPlanLoading(false);
    lastPlanSignatureRef.current = null;
    lastPlanTimeRef.current = 0;
  }, []);

  const drawDetections = (canvas: HTMLCanvasElement, detections: Detection[], ctx: CanvasRenderingContext2D) => {
    if (!detections || detections.length === 0) {
      console.log('✓ No detections to draw - canvas cleared');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    console.log(`✏️ Drawing ${detections.length} boxes on canvas`);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    detections.forEach((detection, idx) => {
      const x = detection.box.xmin * canvas.width;
      const y = detection.box.ymin * canvas.height;
      const x2 = detection.box.xmax * canvas.width;
      const y2 = detection.box.ymax * canvas.height;
      const width = x2 - x;
      const height = y2 - y;

      if (width <= 0 || height <= 0) {
        console.warn(`⚠️ Box ${idx} has invalid dimensions: ${width}x${height}`);
        return;
      }

      const color = detection.type === 'weed' ? '#ff0000' : '#00ff00';

      console.log(`  Box ${idx}: (${Math.round(x)}, ${Math.round(y)}) -> (${Math.round(x2)}, ${Math.round(y2)}) [${detection.type}]`);

      ctx.strokeStyle = color;
      ctx.lineWidth = 4;
      ctx.strokeRect(x, y, width, height);

      const labelText = `${detection.label} ${(detection.confidence * 100).toFixed(0)}%`;
      ctx.font = 'bold 16px Arial';
      const textMetrics = ctx.measureText(labelText);
      const textWidth = textMetrics.width;
      const textHeight = 20;

      ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
      ctx.fillRect(x, y - textHeight - 5, textWidth + 10, textHeight + 3);

      ctx.fillStyle = color;
      ctx.font = 'bold 16px Arial';
      ctx.fillText(labelText, x + 5, y - 8);
    });

    console.log(`✅ Finished drawing ${detections.length} boxes`);
  };

  useEffect(() => {
    if (!result || !result.detections || result.weedCount === 0) {
      setActionPlan(null);
      setPlanError(null);
      return;
    }

    const signature = JSON.stringify(
      result.detections.map((det) => `${det.label}:${det.type}:${Math.round(det.confidence * 100)}`)
    );
    const now = Date.now();

    if (
      signature === lastPlanSignatureRef.current &&
      now - lastPlanTimeRef.current < 5000
    ) {
      return;
    }

    lastPlanSignatureRef.current = signature;
    lastPlanTimeRef.current = now;

    const keyToUse = geminiKey || envGeminiKey;

    if (!keyToUse) {
      setActionPlan('Add a Gemini API key to generate live weed-control guidance.');
      setPlanError(null);
      return;
    }

    let cancelled = false;

    const run = async () => {
      setIsPlanLoading(true);
      setPlanError(null);
      try {
        const plan = await generateWeedTreatmentPlan(
          keyToUse,
          result,
          cropType,
          processingMode,
        );
        if (!cancelled) {
          setActionPlan(plan);
        }
      } catch (err: any) {
        if (!cancelled) {
          console.error('Gemini plan error (real-time):', err);
          setPlanError(err?.message || 'Failed to generate live weed-control plan.');
        }
      } finally {
        if (!cancelled) {
          setIsPlanLoading(false);
        }
      }
    };

    run();

    return () => {
      cancelled = true;
    };
  }, [result, cropType, geminiKey, processingMode]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
      <Toaster position="top-right" />
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-slate-800">Real-Time Detection</h3>
        <div className="flex items-center gap-2">
          {isActive && (
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          )}
          <span className="text-xs font-medium text-slate-600">
            {isActive ? 'Live' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-semibold text-slate-700 mb-2">Target Crop</label>
        <input
          type="text"
          value={cropType}
          onChange={(e) => setCropType(e.target.value)}
          disabled={isActive}
          className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-slate-50"
          placeholder="e.g. Cotton, Wheat, Corn"
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs font-semibold text-slate-700 mb-1">
          Gemini API Key (for live weed-control plan)
        </label>
        <input
          type="password"
          value={geminiKey}
          onChange={(e) => setGeminiKey(e.target.value)}
          disabled={isActive}
          className="w-full px-4 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-slate-50"
          placeholder="VITE_GEMINI_API_KEY"
        />
        <p className="text-[11px] text-slate-500 mt-1">
          Optional: YOLO detection still runs; add a key to generate live treatment suggestions.
        </p>
      </div>

      <div className="mb-4">
        <label className="block text-xs font-semibold text-slate-700 mb-1">
          Gemini Model for Plan
        </label>
        <select
          value={processingMode}
          onChange={(e) => setProcessingMode(e.target.value as ProcessingMode)}
          disabled={isActive}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-slate-50"
        >
          <option value={ProcessingMode.FAST}>gemini-2.5-flash (fast)</option>
          <option value={ProcessingMode.ACCURATE}>gemini-2.5-pro (accurate)</option>
        </select>
      </div>

      <div className="relative bg-black rounded-2xl overflow-hidden mb-4 border-2 border-slate-700 w-full">
        <video
          ref={videoRef}
          className="w-full h-auto block"
          style={{
            maxHeight: '500px',
            backgroundColor: '#000',
            display: 'block'
          }}
          autoPlay
          playsInline
          muted
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full"
          style={{
            cursor: 'crosshair',
            display: 'block',
            maxHeight: '500px',
            height: '100%',
            zIndex: 10
          }}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 p-3 rounded-xl flex items-start space-x-3 text-red-700 mb-4">
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <div className="flex gap-3 mb-4">
        {!isActive ? (
          <button
            onClick={startCamera}
            className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <Camera size={18} />
            Start Camera
          </button>
        ) : (
          <button
            onClick={stopCamera}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <StopCircle size={18} />
            Stop Camera
          </button>
        )}
      </div>

      {isActive && (
        <div className="bg-blue-50 border border-blue-100 p-3 rounded-xl flex items-center space-x-2 text-blue-700 mb-4">
          <Loader2 className="animate-spin" size={16} />
          <span className="text-sm font-medium">Analyzing frames...</span>
        </div>
      )}

      {result && (
        <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200">
          <h4 className="font-semibold text-slate-800 mb-3">Detection Stats</h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <p className="text-xs text-slate-600 font-medium">Weeds Found</p>
              <p className="text-2xl font-bold text-red-600">{detectionStats.weeds}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <p className="text-xs text-slate-600 font-medium">Crops Found</p>
              <p className="text-2xl font-bold text-green-600">{detectionStats.crops}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <p className="text-xs text-slate-600 font-medium">Process Speed</p>
              <p className="text-2xl font-bold text-blue-600">
                {detectionStats.fps > 0 ? `${detectionStats.fps} FPS` : '~2 FPS'}
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-600 mt-3 italic">{result.summary}</p>

          {(isPlanLoading || actionPlan || planError) && (
            <div className="mt-4 border-t border-slate-200 pt-3">
              <h5 className="text-sm font-semibold text-slate-800 mb-2">
                Gemini Weed-Control Plan
              </h5>
              {isPlanLoading && (
                <div className="flex items-center gap-2 text-emerald-700 text-xs">
                  <Loader2 className="animate-spin" size={14} />
                  <span>Generating plan from latest detections...</span>
                </div>
              )}
              {planError && (
                <div className="mt-1 text-xs text-red-600 flex items-start gap-1">
                  <AlertCircle size={12} className="mt-0.5" />
                  <span>{planError}</span>
                </div>
              )}
              {actionPlan && !isPlanLoading && (
                <div className="mt-2 text-xs text-slate-700 whitespace-pre-wrap">
                  {actionPlan}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
