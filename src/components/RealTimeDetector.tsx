import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera, StopCircle, AlertCircle, Loader2, RefreshCw,
  Wifi, WifiOff, Zap, ShieldAlert, ExternalLink,
} from 'lucide-react';
import { analyzeImage } from '../services/yoloService';

import { addDetection } from '../services/firebaseService';
import { getCurrentLocation, LocationData } from '../services/locationService';
import { useAuthStore } from '../store/authStore';
import { AnalysisResult, Detection } from '../types';
import toast, { Toaster } from 'react-hot-toast';



export const RealTimeDetector: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const cropType = 'Cotton'; // Internal default, no UI input needed
  const [detectionStats, setDetectionStats] = useState({ weeds: 0, fps: 0 });
  const [lastDetectionTime, setLastDetectionTime] = useState<Date | null>(null);
  const [frameStatus, setFrameStatus] = useState<'idle' | 'capturing' | 'analyzing'>('idle');
  const [location, setLocation] = useState<LocationData | null>(null);

  // identifyCrop is intentionally false for real-time — per-frame crop ID adds ~1 s latency
  const identifyCrop = false;

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const activeRef = useRef(false);
  const isAnalyzingRef = useRef(false);          // skip frame when server still busy
  const sessionIdRef = useRef(`rt_${Date.now()}`); // groups real-time saves by session

  const lastSaveTimeRef = useRef<number>(0);
  const fpsHistoryRef = useRef<number[]>([]);
  const lastFrameTimeRef = useRef<number>(0);
  const { user } = useAuthStore();

  // ─── Acquire GPS once (reused for Firebase location logging) ──────────────────
  useEffect(() => {
    getCurrentLocation()
      .then(setLocation)
      .catch(() => {/* silently fall back to default */ });
  }, []);

  // ─── Draw bounding boxes on canvas ───────────────────────────────────────────
  const drawDetections = useCallback(
    (canvas: HTMLCanvasElement, detections: Detection[], ctx: CanvasRenderingContext2D) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (!detections || detections.length === 0) return;

      detections.forEach((detection, idx) => {
        const x = detection.box.xmin * canvas.width;
        const y = detection.box.ymin * canvas.height;
        const x2 = detection.box.xmax * canvas.width;
        const y2 = detection.box.ymax * canvas.height;
        const w = x2 - x;
        const h = y2 - y;

        if (w <= 0 || h <= 0) return;

        const isWeed = detection.type === 'weed';
        if (!isWeed) return; // Only draw weed detections
        const color = '#ef4444';
        const bgColor = 'rgba(239,68,68,0.12)';

        ctx.fillStyle = bgColor;
        ctx.fillRect(x, y, w, h);

        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.shadowColor = color;
        ctx.shadowBlur = 6;
        ctx.strokeRect(x, y, w, h);
        ctx.shadowBlur = 0;

        // Corner accents
        const cs = Math.min(12, w * 0.15, h * 0.15);
        ctx.lineWidth = 3;
        [[x, y, cs, 0, 0, cs], [x + w, y, -cs, 0, 0, cs],
        [x, y + h, cs, 0, 0, -cs], [x + w, y + h, -cs, 0, 0, -cs]].forEach(
          ([cx, cy, dx1, dy1, dx2, dy2]) => {
            ctx.beginPath();
            ctx.moveTo(cx + dx1, cy + dy1);
            ctx.lineTo(cx, cy);
            ctx.lineTo(cx + dx2, cy + dy2);
            ctx.stroke();
          });

        const confPct = Math.round(detection.confidence * 100);
        const labelText = `${isWeed ? '🌿 ' : '🌾 '}${detection.label} ${confPct}%`;
        ctx.font = 'bold 13px Inter, Arial, sans-serif';
        const textW = ctx.measureText(labelText).width;
        const labelH = 22;
        const labelY = y > labelH + 4 ? y - labelH - 2 : y + 2;

        ctx.fillStyle = isWeed ? 'rgba(127,29,29,0.92)' : 'rgba(20,83,45,0.92)';
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x, labelY, textW + 12, labelH, 4);
        else ctx.rect(x, labelY, textW + 12, labelH);
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.fillText(labelText, x + 6, labelY + 15);
      });
    }, []);

  // ─── Sync canvas pixel dimensions to video rendered size ─────────────────────
  const syncCanvasToVideo = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    if (video.videoWidth > 0 &&
      (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight)) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }
  }, []);

  const MIN_FRAME_DELAY = 200; // ms poll interval

  // Adaptive self-scheduling detection loop
  const runDetectionLoop = useCallback(async () => {
    if (!activeRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || video.videoWidth === 0) {
      setTimeout(() => { if (activeRef.current) runDetectionLoop(); }, 200);
      return;
    }

    // Skip if a server request is still in-flight (prevents frame queue buildup)
    if (isAnalyzingRef.current) {
      setTimeout(() => { if (activeRef.current) runDetectionLoop(); }, MIN_FRAME_DELAY);
      return;
    }

    setFrameStatus('capturing');

    try {
      syncCanvasToVideo();
      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('No 2d context');

      const scaledCanvas = document.createElement('canvas');
      scaledCanvas.width = 640;
      scaledCanvas.height = 360;
      const scaledCtx = scaledCanvas.getContext('2d');
      if (scaledCtx) scaledCtx.drawImage(video, 0, 0, 640, 360);

      const frameBase64 = scaledCanvas.toDataURL('image/jpeg', 0.55).split(',')[1];

      // FPS: measure capture interval
      const captureTime = Date.now();
      const delta = captureTime - lastFrameTimeRef.current;
      lastFrameTimeRef.current = captureTime;
      if (delta > 0 && delta < 5000) {
        fpsHistoryRef.current.push(1000 / delta);
        if (fpsHistoryRef.current.length > 8) fpsHistoryRef.current.shift();
      }

      isAnalyzingRef.current = true;
      setFrameStatus('analyzing');
      const analysisResult = await analyzeImage(frameBase64, cropType, identifyCrop);
      isAnalyzingRef.current = false;
      if (!activeRef.current) return;

      // Count only weed detections (ignore crop detections)
      const dets = analysisResult.detections ?? [];
      const weedDets = dets.filter(d => d.type === 'weed');
      const weedCount = weedDets.length;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawDetections(canvas, weedDets, ctx);

      setResult({ ...analysisResult, weedCount, cropCount: 0, detections: weedDets });
      setLastDetectionTime(new Date());

      const avgFps = fpsHistoryRef.current.length > 0
        ? Math.round(fpsHistoryRef.current.reduce((a, b) => a + b, 0) / fpsHistoryRef.current.length)
        : 0;
      setDetectionStats({ weeds: weedCount, fps: avgFps });

      // Firebase: save every 15s unconditionally so admin history is always populated
      const nowMs = Date.now();
      if (nowMs - lastSaveTimeRef.current > 15_000) {
        lastSaveTimeRef.current = nowMs;
        addDetection({
          filename: `realtime_${sessionIdRef.current}_${new Date().toISOString()}.jpg`,
          weedsDetected: weedCount,
          cropsDetected: 0,
          status: 'processed',
          userId: user?.id || 'anonymous',     // must match auth.uid for Firestore rules
          userEmail: user?.email,

          batchId: sessionIdRef.current,
          ...(location ? {
            location: {
              latitude: location.latitude,
              longitude: location.longitude,
              accuracy: location.accuracy,
              locationName: location.locationName,
            },
          } : {}),
        }).catch((e) => console.error('Firebase save error:', e));
      }

    } catch (err: any) {
      isAnalyzingRef.current = false;
      if (!activeRef.current) return;
      if (!err.message?.includes('aborted'))
        setError(`Detection failed: ${err.message}`);
    } finally {
      setFrameStatus('idle');
      if (activeRef.current) setTimeout(runDetectionLoop, MIN_FRAME_DELAY);
    }
  }, [drawDetections, syncCanvasToVideo, user, location]);

  // ─── Start camera ─────────────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    // Check for secure context first — camera & GPS require HTTPS or localhost
    if (!window.isSecureContext) {
      const httpsUrl = window.location.href.replace('http://', 'https://');
      setError(
        `Camera requires a secure connection (HTTPS). ` +
        `Try: ${httpsUrl} — or set VITE_API_URL to your ngrok URL in .env`
      );
      return;
    }

    try {
      setError(null);
      setResult(null);
      setDetectionStats({ weeds: 0, crops: 0, fps: 0 });
      fpsHistoryRef.current = [];
      lastFrameTimeRef.current = 0;

      if (!navigator.mediaDevices?.getUserMedia)
        throw new Error('Camera API not available in this browser.');

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      });

      streamRef.current = stream;
      const video = videoRef.current!;
      video.srcObject = stream;
      await new Promise<void>((res) => { video.onloadedmetadata = () => res(); });
      await video.play();

      if (canvasRef.current) {
        canvasRef.current.width = video.videoWidth;
        canvasRef.current.height = video.videoHeight;
      }

      activeRef.current = true;
      setIsActive(true);
      runDetectionLoop();

    } catch (err: any) {
      let msg = 'Failed to start camera. ';
      if (!window.isSecureContext) {
        const httpsUrl = window.location.href.replace('http://', 'https://');
        msg = `Camera blocked — page must be served over HTTPS. Try: ${httpsUrl}`;
      } else if (err.name === 'NotAllowedError') {
        msg += 'Camera permission denied. Tap the camera icon in your browser address bar to allow it.';
      } else if (err.name === 'NotFoundError') {
        msg += 'No camera device found on this device.';
      } else if (err.name === 'NotReadableError') {
        msg += 'Camera is already in use by another app.';
      } else {
        msg += err.message || 'Unknown error.';
      }
      setError(msg);
      setIsActive(false);
    }
  }, [runDetectionLoop]);

  // ─── Stop camera ─────────────────────────────────────────────────────────────
  const stopCamera = useCallback(() => {
    activeRef.current = false;

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }

    setIsActive(false);
    setFrameStatus('idle');
    setResult(null);
    setDetectionStats({ weeds: 0, fps: 0 });
    setLastDetectionTime(null);
    isAnalyzingRef.current = false;
    sessionIdRef.current = `rt_${Date.now()}`;  // new session for next start
    fpsHistoryRef.current = [];
  }, []);





  // ─── Cleanup on unmount ───────────────────────────────────────────────────────
  useEffect(() => () => { stopCamera(); }, [stopCamera]);

  // ─── Derived display values ───────────────────────────────────────────────────
  const statusDot =
    frameStatus === 'analyzing' ? 'bg-amber-400 animate-pulse' :
      frameStatus === 'capturing' ? 'bg-blue-400  animate-pulse' :
        isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-400';

  const statusLabel =
    frameStatus === 'analyzing' ? 'Analyzing…' :
      frameStatus === 'capturing' ? 'Capturing…' :
        isActive ? 'Live' : 'Offline';

  return (
    <div className="p-6 rounded-2xl" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
      <Toaster position="top-right" />

      {/* ── Insecure Context Warning ── */}
      {!window.isSecureContext && (
        <div className="mb-4 rounded-xl border border-amber-300 bg-amber-50 p-4 flex items-start gap-3">
          <ShieldAlert size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-amber-800">Camera &amp; GPS require HTTPS</p>
            <p className="text-xs text-amber-700 mt-1 leading-relaxed">
              You are on an insecure HTTP page. Browsers block camera and location access on HTTP.
            </p>
            <a
              href={window.location.href.replace('http://', 'https://')}
              className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-amber-800 underline hover:text-amber-900 break-all"
            >
              <ExternalLink size={12} />
              {window.location.href.replace('http://', 'https://')}
            </a>
            <p className="text-[11px] text-amber-600 mt-1">
              Click the link above → browser shows "Not Secure" warning → click <strong>Advanced → Proceed</strong> to accept the self-signed certificate.
            </p>
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <Zap size={20} className="text-emerald-600" />
          <h3 className="text-lg font-bold" style={{ color: '#0a3d2e' }}>Real-Time <span className="serif-accent">Detection</span></h3>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${statusDot}`} />
          <span className="text-xs font-semibold text-slate-600">{statusLabel}</span>
        </div>
      </div>





      {/* ── Video + Canvas ── */}
      <div className="relative bg-black rounded-2xl overflow-hidden mb-4 border-2 border-slate-700" style={{ lineHeight: 0 }}>
        <video
          ref={videoRef}
          className="w-full block"
          style={{ maxHeight: '500px', backgroundColor: '#000' }}
          autoPlay playsInline muted
        />
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none"
          style={{ width: '100%', height: '100%', display: 'block' }}
        />

        {/* LIVE badge */}
        {isActive && (
          <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm rounded-full px-3 py-1">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-white text-xs font-bold tracking-wide">LIVE</span>
          </div>
        )}



        {/* Placeholder */}
        {!isActive && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400">
            <Camera size={48} strokeWidth={1} />
            <p className="mt-3 text-sm">Start camera to begin detection</p>
          </div>
        )}
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="bg-red-50 border border-red-100 p-3 rounded-xl flex items-start justify-between space-x-3 mb-4">
          <div className="flex items-start space-x-2 text-red-700">
            <AlertCircle size={17} className="mt-0.5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
          {!isActive && (
            <button onClick={() => { setError(null); startCamera(); }} className="flex-shrink-0 flex items-center gap-1 text-xs text-red-700 underline">
              <RefreshCw size={12} /> Retry
            </button>
          )}
        </div>
      )}

      {/* ── Start / Stop ── */}
      <div className="flex gap-3 mb-4">
        {!isActive ? (
          <button onClick={startCamera} className="flex-1 font-semibold py-2.5 px-4 rounded-full flex items-center justify-center gap-2 transition-all verdantix-btn">
            <Camera size={18} /> Start Camera
          </button>
        ) : (
          <button onClick={stopCamera} className="flex-1 bg-red-600 hover:bg-red-700 active:scale-95 text-white font-semibold py-2.5 px-4 rounded-full flex items-center justify-center gap-2 transition-all">
            <StopCircle size={18} /> Stop Camera
          </button>
        )}
      </div>

      {/* ── Analyzing indicator ── */}
      {isActive && frameStatus === 'analyzing' && (
        <div className="bg-amber-50 border border-amber-100 p-2.5 rounded-xl flex items-center space-x-2 text-amber-700 mb-4">
          <Loader2 className="animate-spin flex-shrink-0" size={15} />
          <span className="text-xs font-medium">Analyzing frame with YOLOv11…</span>
        </div>
      )}

      {/* ── Detection Stats ── */}
      {result && (
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-sm" style={{ color: '#0a3d2e' }}>Detection Results</h4>
            {lastDetectionTime && (
              <span className="text-[11px] text-slate-400">Updated {lastDetectionTime.toLocaleTimeString()}</span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white rounded-lg p-3 border border-red-100">
              <div className="flex items-center gap-1 mb-1">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <p className="text-xs text-slate-600 font-medium">Weeds Detected</p>
              </div>
              <p className="text-2xl font-bold text-red-600">{detectionStats.weeds}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="flex items-center gap-1 mb-1">
                {detectionStats.fps > 0 ? <Wifi size={12} className="text-blue-500" /> : <WifiOff size={12} className="text-slate-400" />}
                <p className="text-xs text-slate-600 font-medium">Speed</p>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {detectionStats.fps > 0 ? `${detectionStats.fps} FPS` : '—'}
              </p>
            </div>
          </div>

          {/* Per-detection list */}
          {result.detections && result.detections.length > 0 && (
            <div className="space-y-1.5 mb-3">
              {result.detections.slice(0, 6).map((det, i) => (
                <div key={i} className="flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-red-50">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full flex-shrink-0 bg-red-500" />
                    <span className="text-xs font-medium text-slate-700 capitalize">{det.label}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-50 text-red-600 font-medium">weed</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-red-400"
                        style={{ width: `${Math.round(det.confidence * 100)}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 w-8 text-right">{Math.round(det.confidence * 100)}%</span>
                  </div>
                </div>
              ))}
              {result.detections.length > 6 && (
                <p className="text-[11px] text-slate-400 text-center">+{result.detections.length - 6} more</p>
              )}
            </div>
          )}

          <p className="text-xs text-slate-500 italic">{result.summary}</p>


        </div>
      )}


    </div>
  );
};
