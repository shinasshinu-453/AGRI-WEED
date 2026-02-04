import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { RealTimeDetector } from '../components/RealTimeDetector';
import { ImageUploader } from '../components/ImageUploader';
import { ResultsOverlay } from '../components/ResultsOverlay';
import { MetricsPanel } from '../components/MetricsPanel';
import { WeatherWidget } from '../components/WeatherWidget';
import CropIdentificationCard from '../components/CropIdentificationCard';
import RemovalTechniquesPanel from '../components/RemovalTechniquesPanel';
import { analyzeImage as analyzeWithYolo } from '../services/yoloService';
import { generateWeedTreatmentPlan } from '../services/geminiService';
import { addDetection } from '../services/firebaseService';
import { AnalysisResult, ProcessingMode } from '../types';
import { Sprout, Camera, Upload, LogOut, Loader2, AlertCircle } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

const envGeminiKey = import.meta.env.VITE_GEMINI_API_KEY || '';

export const UserDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [cropType, setCropType] = useState<string>('Wheat');
  const [processingMode, setProcessingMode] = useState<ProcessingMode>(ProcessingMode.FAST);
  const [geminiKey, setGeminiKey] = useState<string>(envGeminiKey);
  const [identifyCrop, setIdentifyCrop] = useState<boolean>(true); // New state
  const useRoboflow = false; // Use hybrid mode: YOLO + Roboflow

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
              resolve(canvas.toDataURL('image/jpeg', 0.6));
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

      const base64 = await fileToBase64(file);
      setImageSrc(base64);

      const base64Data = base64.split(',')[1];
      if (!base64Data) {
        throw new Error('Failed to process image data');
      }

      const data = await analyzeWithYolo(base64Data, cropType, identifyCrop, useRoboflow);

      if (!data || !data.detections) {
        throw new Error('Invalid API response');
      }

      const keyToUse = geminiKey || envGeminiKey;
      let actionPlan = '';
      let planError: string | null = null;

      if (keyToUse) {
        try {
          actionPlan = await generateWeedTreatmentPlan(
            keyToUse,
            data,
            cropType,
            processingMode,
          );
        } catch (planErr: any) {
          planError = planErr?.message || 'Gemini plan failed';
        }
      } else {
        actionPlan = 'Add a Gemini API key to generate the weed-control plan.';
      }

      setResult({ ...data, actionPlan });

      // Save detection to Firebase
      try {
        await addDetection({
          filename: file.name,
          weedsDetected: data.weedCount || 0,
          cropsDetected: data.cropCount || 0,
          status: 'processed',
          userId: user?.email || 'anonymous',
          cropType: cropType,
        });
        toast.success('Detection saved to history!');
      } catch (firebaseErr) {
        console.error('Failed to save detection to Firebase:', firebaseErr);
        toast.error('Detection analyzed but not saved to history');
      }

      if (planError) {
        setError(planError);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze image');
      setResult(null);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background cyber-grid">
      <Toaster position="top-right" />
      {/* Header */}
      <header className="glass-effect border-b border-white/10 sticky top-0 z-50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/20 border border-primary/30">
              <Sprout size={24} className="text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">AgriVision</h1>
              <p className="text-xs text-muted-foreground">User Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Avatar className="border-2 border-primary/30">
                <AvatarFallback className="bg-primary/20 text-primary font-semibold">
                  {user?.name?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">
            Welcome back, <span className="gradient-text">{user?.name}</span>!
          </h2>
          <p className="text-muted-foreground">
            Choose between real-time camera detection or upload your field images for analysis
          </p>
        </div>

        {/* Weather Widget */}
        <div className="mb-8">
          <WeatherWidget compact />
        </div>

        <Tabs defaultValue="camera" className="w-full">
          <TabsList className="grid w-full grid-cols-2 h-12 mb-8 glass-effect">
            <TabsTrigger value="camera" className="gap-2 text-base">
              <Camera size={18} />
              Real-Time Detection
            </TabsTrigger>
            <TabsTrigger value="upload" className="gap-2 text-base">
              <Upload size={18} />
              Photo Upload
            </TabsTrigger>
          </TabsList>

          {/* Real-Time Camera Tab */}
          <TabsContent value="camera" className="space-y-6">
            <Card className="glass-effect border-white/20 p-6">
              <RealTimeDetector />
            </Card>
          </TabsContent>

          {/* Photo Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Controls */}
              <div className="lg:col-span-4 space-y-6">
                <Card className="glass-effect border-white/20 p-6">
                  <h3 className="text-lg font-bold mb-4">Upload & Analyze</h3>

                  <div className="mb-6">
                    <label className="block text-sm font-semibold mb-2">
                      Target Crop Type
                    </label>
                    <input
                      type="text"
                      value={cropType}
                      onChange={(e) => setCropType(e.target.value)}
                      className="w-full px-4 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all"
                      placeholder="e.g. Cotton, Wheat, Corn"
                    />
                    <p className="text-xs text-muted-foreground mt-2">
                      Specify your crop to improve detection accuracy
                    </p>
                  </div>

                  <div className="mb-6">
                    <label className="block text-xs font-semibold mb-1">Gemini API Key (for the weed-control plan)</label>
                    <input
                      type="password"
                      value={geminiKey}
                      onChange={(e) => setGeminiKey(e.target.value)}
                      placeholder="VITE_GEMINI_API_KEY"
                      className="w-full px-3 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
                    />
                    <p className="text-[11px] text-muted-foreground mt-1">Optional: YOLO detection still runs; add a key to generate the plan.</p>
                  </div>

                  <div className="mb-6">
                    <label className="block text-xs font-semibold mb-1">Gemini Model for Plan</label>
                    <select
                      value={processingMode}
                      onChange={(e) => setProcessingMode(e.target.value as ProcessingMode)}
                      className="w-full px-3 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
                    >
                      <option value={ProcessingMode.FAST}>gemini-2.5-flash (fast)</option>
                      <option value={ProcessingMode.ACCURATE}>gemini-2.5-pro (accurate)</option>
                    </select>
                  </div>

                  <div className="mb-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={identifyCrop}
                        onChange={(e) => setIdentifyCrop(e.target.checked)}
                        className="w-4 h-4 rounded border-border text-primary focus:ring-2 focus:ring-primary"
                        disabled={true}
                      />
                      <span className="text-sm font-semibold text-muted-foreground">🌾 Identify Crop with Roboflow</span>
                    </label>
                    <p className="text-xs text-muted-foreground mt-1 ml-6">
                      Auto-enabled when using Roboflow model
                    </p>
                  </div>

                  <ImageUploader onImageUpload={handleImageUpload} isProcessing={isProcessing} />
                </Card>

                {isProcessing && (
                  <Card className="glass-effect border-primary/30 p-4">
                    <div className="flex items-center gap-3 text-primary">
                      <Loader2 className="animate-spin" size={20} />
                      <span className="text-sm font-medium">Analyzing image...</span>
                    </div>
                  </Card>
                )}

                {error && (
                  <Card className="glass-effect border-destructive/30 p-4">
                    <div className="flex items-start gap-3 text-destructive">
                      <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{error}</span>
                    </div>
                  </Card>
                )}
              </div>

              {/* Right Column: Results */}
              <div className="lg:col-span-8">
                {imageSrc ? (
                  <div className="space-y-6">
                    {result?.identifiedCrop && <CropIdentificationCard cropData={result.identifiedCrop} />}
                    {result?.removalTechniques && <RemovalTechniquesPanel techniques={result.removalTechniques} />}
                    {result && <MetricsPanel result={result} />}
                    <ResultsOverlay imageSrc={imageSrc} result={result} />
                  </div>
                ) : (
                  <Card className="glass-effect border-white/20 h-96 flex flex-col items-center justify-center text-center p-8">
                    <div className="p-6 rounded-full bg-primary/10 border border-primary/20 mb-4">
                      <Upload size={48} className="text-primary" />
                    </div>
                    <p className="text-lg font-medium mb-2">No image uploaded yet</p>
                    <p className="text-sm text-muted-foreground">
                      Upload a field image to begin weed detection analysis
                    </p>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};