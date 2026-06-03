import React, { useState, useRef, useCallback } from 'react';
import ReactCrop, { Crop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { Camera, X, Check, RotateCcw, Upload, Scissors } from 'lucide-react';
import { Button } from './ui/button';

interface CameraCaptureWithCropProps {
    onImageReady: (file: File) => void;
    isProcessing: boolean;
}

export const CameraCaptureWithCrop: React.FC<CameraCaptureWithCropProps> = ({
    onImageReady,
    isProcessing,
}) => {
    const [isCameraActive, setIsCameraActive] = useState(false);
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [crop, setCrop] = useState<Crop>({
        unit: '%',
        width: 80,
        height: 80,
        x: 10,
        y: 10,
    });
    const [completedCrop, setCompletedCrop] = useState<PixelCrop | null>(null);
    const [aspectRatio, setAspectRatio] = useState<number | undefined>(undefined);
    const [error, setError] = useState<string | null>(null);

    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const imgRef = useRef<HTMLImageElement>(null);

    const startCamera = async () => {
        try {
            console.log('🎥 Starting camera...');
            setError(null);

            // Check camera permission first
            try {
                const permission = await navigator.permissions.query({ name: 'camera' as PermissionName });
                console.log('📹 Camera permission status:', permission.state);
            } catch (permErr) {
                console.warn('⚠️ Permission API not supported, trying direct access');
            }

            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                },
            });

            console.log('✅ Camera stream obtained:', stream.getTracks().map(t => t.label));

            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                console.log('📺 Set video source, waiting for metadata...');

                videoRef.current.onloadedmetadata = () => {
                    console.log('✅ Video metadata loaded:', {
                        width: videoRef.current?.videoWidth,
                        height: videoRef.current?.videoHeight
                    });
                };

                await videoRef.current.play();
                console.log('▶️ Video playback started');
            }
            setIsCameraActive(true);
            console.log('✅ Camera fully active');
        } catch (err: any) {
            console.error('❌ Camera error:', err);
            let errorMsg = 'Failed to access camera. ';
            if (err.name === 'NotAllowedError') {
                errorMsg += 'Camera permission denied. Please allow camera access in your browser settings.';
            } else if (err.name === 'NotFoundError') {
                errorMsg += 'No camera found on this device.';
            } else if (err.name === 'NotReadableError') {
                errorMsg += 'Camera is already in use by another application.';
            } else if (err.name === 'OverconstrainedError') {
                errorMsg += 'Camera does not support the requested settings.';
            } else {
                errorMsg += err.message || 'Unknown error.';
            }
            setError(errorMsg);
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setIsCameraActive(false);
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        if (ctx) {
            ctx.drawImage(video, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            setCapturedImage(imageData);
            stopCamera();
        }
    };

    const retakePhoto = () => {
        setCapturedImage(null);
        setCompletedCrop(null);
        startCamera();
    };

    const getCroppedImage = useCallback(
        async (image: HTMLImageElement, crop: PixelCrop): Promise<Blob> => {
            const canvas = document.createElement('canvas');
            const scaleX = image.naturalWidth / image.width;
            const scaleY = image.naturalHeight / image.height;

            canvas.width = crop.width;
            canvas.height = crop.height;

            const ctx = canvas.getContext('2d');
            if (!ctx) throw new Error('No 2d context');

            ctx.drawImage(
                image,
                crop.x * scaleX,
                crop.y * scaleY,
                crop.width * scaleX,
                crop.height * scaleY,
                0,
                0,
                crop.width,
                crop.height
            );

            return new Promise((resolve, reject) => {
                canvas.toBlob(
                    (blob) => {
                        if (blob) {
                            resolve(blob);
                        } else {
                            reject(new Error('Canvas is empty'));
                        }
                    },
                    'image/jpeg',
                    0.85
                );
            });
        },
        []
    );

    const handleConfirmCrop = async () => {
        if (!completedCrop || !imgRef.current) {
            // No crop, use full image
            if (capturedImage) {
                const response = await fetch(capturedImage);
                const blob = await response.blob();
                const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
                onImageReady(file);
                resetAll();
            }
            return;
        }

        try {
            const croppedBlob = await getCroppedImage(imgRef.current, completedCrop);
            const file = new File([croppedBlob], 'camera-capture-cropped.jpg', {
                type: 'image/jpeg',
            });
            onImageReady(file);
            resetAll();
        } catch (err: any) {
            setError('Failed to crop image: ' + err.message);
        }
    };

    const resetAll = () => {
        setCapturedImage(null);
        setCompletedCrop(null);
        setCrop({
            unit: '%',
            width: 80,
            height: 80,
            x: 10,
            y: 10,
        });
        setAspectRatio(undefined);
    };

    return (
        <div className="space-y-4">
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                </div>
            )}

            {!isCameraActive && !capturedImage && (
                <div
                    className="border-2 border-dashed border-border rounded-xl p-12 text-center bg-card hover:bg-accent/50 transition-all cursor-pointer group"
                    onClick={startCamera}
                >
                    <div className="flex flex-col items-center gap-4">
                        <div className="p-6 rounded-full bg-primary/10 border border-primary/20 group-hover:bg-primary/20 transition-all">
                            <Camera size={48} className="text-primary" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold mb-2">Open Camera</h3>
                            <p className="text-sm text-muted-foreground">
                                Take a photo of your field to analyze
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {isCameraActive && !capturedImage && (
                <div className="space-y-4">
                    <div className="relative bg-black rounded-xl overflow-hidden border-2 border-border">
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-auto max-h-[500px]"
                        />
                        <canvas ref={canvasRef} className="hidden" />
                    </div>
                    <div className="flex gap-3">
                        <Button
                            onClick={capturePhoto}
                            disabled={isProcessing}
                            className="flex-1 gap-2"
                            size="lg"
                        >
                            <Camera size={20} />
                            Capture Photo
                        </Button>
                        <Button onClick={stopCamera} variant="outline" size="lg">
                            <X size={20} />
                        </Button>
                    </div>
                </div>
            )}

            {capturedImage && (
                <div className="space-y-4">
                    <div className="bg-card rounded-xl p-4 border border-border">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-semibold flex items-center gap-2">
                                <Scissors size={18} className="text-primary" />
                                Crop Your Image (Optional)
                            </h4>
                            <div className="flex gap-2">
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setAspectRatio(undefined)}
                                    className={!aspectRatio ? 'bg-primary/10' : ''}
                                >
                                    Free
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setAspectRatio(1)}
                                    className={aspectRatio === 1 ? 'bg-primary/10' : ''}
                                >
                                    1:1
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setAspectRatio(4 / 3)}
                                    className={aspectRatio === 4 / 3 ? 'bg-primary/10' : ''}
                                >
                                    4:3
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setAspectRatio(16 / 9)}
                                    className={aspectRatio === 16 / 9 ? 'bg-primary/10' : ''}
                                >
                                    16:9
                                </Button>
                            </div>
                        </div>

                        <div className="relative bg-black rounded-lg overflow-hidden">
                            <ReactCrop
                                crop={crop}
                                onChange={(c) => setCrop(c)}
                                onComplete={(c) => setCompletedCrop(c)}
                                aspect={aspectRatio}
                            >
                                <img
                                    ref={imgRef}
                                    src={capturedImage}
                                    alt="Captured"
                                    className="max-h-[500px] w-full object-contain"
                                />
                            </ReactCrop>
                        </div>

                        <p className="text-xs text-muted-foreground mt-3 text-center">
                            Drag the corners to crop, or click "Analyze Full Image" to skip cropping
                        </p>
                    </div>

                    <div className="flex gap-3">
                        <Button
                            onClick={handleConfirmCrop}
                            disabled={isProcessing}
                            className="flex-1 gap-2"
                            size="lg"
                        >
                            <Check size={20} />
                            {completedCrop ? 'Analyze Cropped Image' : 'Analyze Full Image'}
                        </Button>
                        <Button onClick={retakePhoto} variant="outline" size="lg" className="gap-2">
                            <RotateCcw size={20} />
                            Retake
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};
