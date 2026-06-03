import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Card } from '@/components/ui/card';
import { Sidebar } from '../components/Sidebar';
import { RealTimeDetector } from '../components/RealTimeDetector';
import { ImageUploadWithCrop } from '../components/ImageUploadWithCrop';
import { CameraCaptureWithCrop } from '../components/CameraCaptureWithCrop';
import { BatchUploader } from '../components/BatchUploader';
import { BatchResultsPanel } from '../components/BatchResultsPanel';
import { ResultsOverlay } from '../components/ResultsOverlay';
import { MetricsPanel } from '../components/MetricsPanel';
import RemovalTechniquesPanel from '../components/RemovalTechniquesPanel';
import ExplainableAIPanel from '../components/ExplainableAIPanel';
import ModelDashboard from '../components/ModelDashboard';
import { analyzeImage as analyzeWithYolo } from '../services/yoloService';
import { generateWeedTreatmentPlan } from '../services/geminiService';
import { getXAIExplanation } from '../services/xaiService';
import { getDefaultLocation } from '../services/weatherService';
import { addDetection, getDetections } from '../services/firebaseService';
import { getCurrentLocation, LocationData } from '../services/locationService';
import { AnalysisResult, ProcessingMode, Detection, XAIExplanation } from '../types';
import { Loader2, AlertCircle, MapPin, MapPinOff } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

const envGeminiKey = import.meta.env.VITE_GEMINI_API_KEY || '';

export const UserDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const [activeTab, setActiveTab] = useState('capture');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Single image states
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [xaiExplanation, setXaiExplanation] = useState<XAIExplanation | null>(null);
  const [xaiLoading, setXaiLoading] = useState(false);

  // Configuration states
  const [cropType, setCropType] = useState<string>('Wheat');
  const [processingMode, setProcessingMode] = useState<ProcessingMode>(ProcessingMode.FAST);
  const [geminiKey, setGeminiKey] = useState<string>(envGeminiKey);
  const [identifyCrop, setIdentifyCrop] = useState<boolean>(true);
  const [locationEnabled, setLocationEnabled] = useState<boolean>(true);
  const [currentLocation, setCurrentLocation] = useState<LocationData | null>(null);

  // Batch processing states
  const [batchResults, setBatchResults] = useState<Array<{
    id: string;
    filename: string;
    result: AnalysisResult;
    timestamp: string;
  }>>([]);

  // History states
  const [detectionHistory, setDetectionHistory] = useState<any[]>([]); const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (locationEnabled) {
      getCurrentLocation()
        .then((loc) => {
          setCurrentLocation(loc);
          toast.success(`Location: ${loc.locationName || 'Unknown'}`);
        })
        .catch((err) => {
          console.error('Failed to get location:', err);
          toast.error('Location access denied');
        });
    }
  }, [locationEnabled]);

  useEffect(() => {
    if (activeTab === 'history' && user) {
      loadHistory();
    }
  }, [activeTab, user]);

  const loadHistory = async () => {
    if (!user?.email) return;
    setHistoryLoading(true);
    try {
      const { detections } = await getDetections(50, undefined, { userId: user.email });
      setDetectionHistory(detections);
    } catch (err) {
      console.error('Failed to load history:', err);
      toast.error('Failed to load detection history');
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result as string;

        if (file.type.startsWith('image/')) {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            const maxWidth = 1024;
            const maxHeight = 768;
            let width = img.width;
            let height = img.height;

            if (width > maxWidth || height > maxHeight) {
              const ratio = Math.min(maxWidth / width, maxHeight / height);
              width = Math.round(width * ratio);
              height = Math.round(height * ratio);
            }

            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            if (ctx) {
              ctx.drawImage(img, 0, 0, width, height);
              resolve(canvas.toDataURL('image/jpeg', 0.75));
            } else {
              resolve(base64);
            }
          };
          img.onerror = () => resolve(base64);
          img.src = base64;
        } else {
          resolve(base64);
        }
      };
      reader.onerror = (error) => reject(error);
    });
  };

  const handleImageUpload = async (file: File) => {
    try {
      setIsProcessing(true);
      setError(null);
      setResult(null);
      setXaiExplanation(null);

      const base64 = await fileToBase64(file);
      setImageSrc(base64);

      const base64Data = base64.split(',')[1];
      if (!base64Data) {
        throw new Error('Failed to process image data');
      }

      const data = await analyzeWithYolo(base64Data, cropType, identifyCrop);

      if (!data || !data.detections) {
        throw new Error('Invalid API response');
      }

      const keyToUse = geminiKey || envGeminiKey;
      let actionPlan = '';

      if (keyToUse) {
        try {
          actionPlan = await generateWeedTreatmentPlan(keyToUse, data, cropType, processingMode);
        } catch (planErr: any) {
          console.error('Gemini plan failed:', planErr);
        }
      }

      const finalResult = { ...data, actionPlan };
      setResult(finalResult);

      // Auto-request XAI explanation
      if (data.detections && data.detections.length > 0) {
        setXaiLoading(true);
        try {
          // Get user location for live OpenMeteo weather fetch
          const loc = currentLocation || getDefaultLocation();
          const lat = 'latitude' in loc ? loc.latitude : (loc as any).latitude;
          const lon = 'longitude' in loc ? loc.longitude : (loc as any).longitude;

          const xai = await getXAIExplanation(data.detections, cropType, lat, lon);
          setXaiExplanation(xai);
        } catch (xaiErr: any) {
          console.error('XAI explanation failed:', xaiErr);
        } finally {
          setXaiLoading(false);
        }
      }

      // Save detection to Firebase with location
      try {
        await addDetection({
          filename: file.name,
          weedsDetected: data.weedCount || 0,
          cropsDetected: data.cropCount || 0,
          status: 'processed',
          userId: user?.id || 'anonymous',     // must match auth.uid for Firestore rules
          userEmail: user?.email,
          cropType: cropType,
          location: currentLocation ? {
            latitude: currentLocation.latitude,
            longitude: currentLocation.longitude,
            accuracy: currentLocation.accuracy,
            locationName: currentLocation.locationName,
          } : undefined,
        });
        toast.success('Detection saved to history!');
      } catch (firebaseErr) {
        console.error('Failed to save detection:', firebaseErr);
        toast.error('Detection analyzed but not saved');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze image');
      setResult(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchProcess = async (file: File) => {
    const base64 = await fileToBase64(file);
    const base64Data = base64.split(',')[1];

    if (!base64Data) {
      throw new Error('Failed to process image');
    }

    const data = await analyzeWithYolo(base64Data, cropType, identifyCrop);

    if (!data || !data.detections) {
      throw new Error('Invalid API response');
    }

    // Save to batch results
    const batchId = `batch_${Date.now()}`;
    setBatchResults((prev) => [
      ...prev,
      {
        id: `${Date.now()}_${Math.random()}`,
        filename: file.name,
        result: data,
        timestamp: new Date().toISOString(),
      },
    ]);

    // Save to Firebase
    try {
      await addDetection({
        filename: file.name,
        weedsDetected: data.weedCount || 0,
        cropsDetected: data.cropCount || 0,
        status: 'processed',
        userId: user?.id || 'anonymous',     // must match auth.uid for Firestore rules
        userEmail: user?.email,
        cropType: cropType,
        batchId: batchId,
        location: currentLocation ? {
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
          accuracy: currentLocation.accuracy,
          locationName: currentLocation.locationName,
        } : undefined,
      });
    } catch (err) {
      console.error('Failed to save batch item:', err);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: '#f8f9f6' }}>
      <Toaster position="top-right" />

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        user={user}
        onLogout={handleLogout}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        currentLocation={currentLocation}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          {/* Location Toggle */}
          <Card className="p-4 border-0 shadow-sm" style={{ background: '#ffffff', borderRadius: '16px' }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {locationEnabled ? (
                  <MapPin size={20} className="text-primary" />
                ) : (
                  <MapPinOff size={20} className="text-muted-foreground" />
                )}
                <div>
                  <p className="font-medium text-sm">Location Tracking</p>
                  <p className="text-xs text-muted-foreground">
                    {currentLocation?.locationName || 'Detecting location...'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setLocationEnabled(!locationEnabled)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${locationEnabled
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
                  }`}
              >
                {locationEnabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          </Card>

          {/* Tab Content */}
          {activeTab === 'realtime' && (
            <Card className="p-6 border-0 shadow-sm" style={{ background: '#ffffff', borderRadius: '20px' }}>
              <RealTimeDetector />
            </Card>
          )}

          {activeTab === 'capture' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-4 space-y-6">
                <Card className="p-6 border-0 shadow-sm" style={{ background: '#ffffff', borderRadius: '20px' }}>
                  <h3 className="text-lg font-bold mb-4" style={{ color: '#0a3d2e' }}>Camera Capture & <span className="serif-accent">Analyze</span></h3>

                  <CameraCaptureWithCrop onImageReady={handleImageUpload} isProcessing={isProcessing} />
                </Card>

                {isProcessing && (
                  <Card className="p-4 border-0 animate-pulse" style={{ background: '#eef0ea', borderRadius: '16px' }}>
                    <div className="flex items-center gap-3 text-primary">
                      <Loader2 className="animate-spin" size={20} />
                      <span className="text-sm font-medium">Analyzing...</span>
                    </div>
                  </Card>
                )}

                {error && (
                  <Card className="p-4 border-0" style={{ background: '#fef2f2', borderRadius: '16px' }}>
                    <div className="flex items-start gap-3 text-destructive">
                      <AlertCircle size={20} className="mt-0.5" />
                      <span className="text-sm">{error}</span>
                    </div>
                  </Card>
                )}
              </div>

              <div className="lg:col-span-8">
                {imageSrc && result ? (
                  <div className="space-y-6">
                    {result.removalTechniques && <RemovalTechniquesPanel techniques={result.removalTechniques} />}
                    {xaiLoading && (
                      <Card className="p-4 glass-effect border-purple-500/30 animate-pulse">
                        <div className="flex items-center gap-3 text-purple-400">
                          <Loader2 className="animate-spin" size={20} />
                          <span className="text-sm font-medium">Generating AI Explanation...</span>
                        </div>
                      </Card>
                    )}
                    {xaiExplanation && <ExplainableAIPanel explanation={xaiExplanation} />}
                    {result && <MetricsPanel result={result} />}
                    <ResultsOverlay imageSrc={imageSrc} result={result} />
                  </div>
                ) : (
                  <Card className="border-0 shadow-sm h-96 flex items-center justify-center" style={{ background: '#f3f4f1', borderRadius: '20px' }}>
                    <p className="text-muted-foreground">Capture a photo to begin analysis</p>
                  </Card>
                )}
              </div>
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-4 space-y-6">
                <Card className="p-6 border-0 shadow-sm" style={{ background: '#ffffff', borderRadius: '20px' }}>
                  <h3 className="text-lg font-bold mb-4" style={{ color: '#0a3d2e' }}>Upload & <span className="serif-accent">Analyze</span></h3>



                  <ImageUploadWithCrop onImageReady={handleImageUpload} isProcessing={isProcessing} />
                </Card>

                {isProcessing && (
                  <Card className="p-4 border-0 animate-pulse" style={{ background: '#eef0ea', borderRadius: '16px' }}>
                    <div className="flex items-center gap-3 text-primary">
                      <Loader2 className="animate-spin" size={20} />
                      <span className="text-sm font-medium">Analyzing...</span>
                    </div>
                  </Card>
                )}

                {error && (
                  <Card className="p-4 border-0" style={{ background: '#fef2f2', borderRadius: '16px' }}>
                    <div className="flex items-start gap-3 text-destructive">
                      <AlertCircle size={20} className="mt-0.5" />
                      <span className="text-sm">{error}</span>
                    </div>
                  </Card>
                )}
              </div>

              <div className="lg:col-span-8">
                {imageSrc && result ? (
                  <div className="space-y-6">
                    {result.removalTechniques && <RemovalTechniquesPanel techniques={result.removalTechniques} />}
                    {xaiLoading && (
                      <Card className="p-4 glass-effect border-purple-500/30 animate-pulse">
                        <div className="flex items-center gap-3 text-purple-400">
                          <Loader2 className="animate-spin" size={20} />
                          <span className="text-sm font-medium">Generating AI Explanation...</span>
                        </div>
                      </Card>
                    )}
                    {xaiExplanation && <ExplainableAIPanel explanation={xaiExplanation} />}
                    {result && <MetricsPanel result={result} />}
                    <ResultsOverlay imageSrc={imageSrc} result={result} />
                  </div>
                ) : (
                  <Card className="border-0 shadow-sm h-96 flex items-center justify-center" style={{ background: '#f3f4f1', borderRadius: '20px' }}>
                    <p className="text-muted-foreground">Upload an image to begin analysis</p>
                  </Card>
                )}
              </div>
            </div>
          )}

          {activeTab === 'batch' && (
            <div className="space-y-6">
              <Card className="p-6 border-0 shadow-sm" style={{ background: '#ffffff', borderRadius: '20px' }}>
                <h3 className="text-lg font-bold mb-4" style={{ color: '#0a3d2e' }}>Batch Image <span className="serif-accent">Processing</span></h3>

                <BatchUploader onProcess={handleBatchProcess} isProcessing={isProcessing} maxFiles={20} />
              </Card>

              <BatchResultsPanel results={batchResults} onClear={() => setBatchResults([])} />
            </div>
          )}

          {activeTab === 'model-dashboard' && (
            <div className="p-0">
              <ModelDashboard result={result} />
            </div>
          )}

          {activeTab === 'history' && (
            <Card className="p-6 border-0 shadow-sm" style={{ background: '#ffffff', borderRadius: '20px' }}>
              <h3 className="text-lg font-bold mb-4" style={{ color: '#0a3d2e' }}>Detection <span className="serif-accent">History</span></h3>
              {historyLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="animate-spin" size={32} />
                </div>
              ) : detectionHistory.length > 0 ? (
                <div className="space-y-3">
                  {detectionHistory.map((det: any) => (
                    <Card key={det.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{det.filename}</p>
                          <p className="text-xs text-muted-foreground">
                            {det.timestamp?.toDate?.().toLocaleString() || 'Unknown date'}
                          </p>
                        </div>
                        <div className="flex gap-4 text-sm">
                          <div>
                            <span className="text-red-600 font-bold">{det.weedsDetected}</span> weeds
                          </div>
                          <div>
                            <span className="text-green-600 font-bold">{det.cropsDetected}</span> crops
                          </div>
                        </div>
                      </div>
                      {det.location?.locationName && (
                        <p className="text-xs text-muted-foreground mt-2">
                          📍 {det.location.locationName}
                        </p>
                      )}
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-12">No detection history found</p>
              )}
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};