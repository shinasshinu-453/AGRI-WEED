import React, { useState, useRef, useCallback } from 'react';
import ReactCrop, { Crop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { Upload, X, Check, Scissors } from 'lucide-react';
import { Button } from './ui/button';

interface ImageUploadWithCropProps {
    onImageReady: (file: File) => Promise<void>;
    isProcessing: boolean;
}

export const ImageUploadWithCrop: React.FC<ImageUploadWithCropProps> = ({
    onImageReady,
    isProcessing,
}) => {
    const [uploadedImage, setUploadedImage] = useState<string | null>(null);
    const [originalFile, setOriginalFile] = useState<File | null>(null);
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

    const fileInputRef = useRef<HTMLInputElement>(null);
    const imgRef = useRef<HTMLImageElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            setError('Please select a valid image file');
            return;
        }

        setError(null);
        setOriginalFile(file);

        const reader = new FileReader();
        reader.onload = () => {
            setUploadedImage(reader.result as string);
        };
        reader.readAsDataURL(file);
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            setError('Please select a valid image file');
            return;
        }

        setError(null);
        setOriginalFile(file);

        const reader = new FileReader();
        reader.onload = () => {
            setUploadedImage(reader.result as string);
        };
        reader.readAsDataURL(file);
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
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
            // No crop, use original file
            if (originalFile) {
                await onImageReady(originalFile);
                resetAll();
            }
            return;
        }

        try {
            const croppedBlob = await getCroppedImage(imgRef.current, completedCrop);
            const file = new File([croppedBlob], 'upload-cropped.jpg', {
                type: 'image/jpeg',
            });
            await onImageReady(file);
            resetAll();
        } catch (err: any) {
            setError('Failed to crop image: ' + err.message);
        }
    };

    const resetAll = () => {
        setUploadedImage(null);
        setOriginalFile(null);
        setCompletedCrop(null);
        setCrop({
            unit: '%',
            width: 80,
            height: 80,
            x: 10,
            y: 10,
        });
        setAspectRatio(undefined);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="space-y-4">
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                </div>
            )}

            {!uploadedImage && (
                <div
                    className="border-2 border-dashed border-border rounded-xl p-12 text-center bg-card hover:bg-accent/50 transition-all cursor-pointer group"
                    onClick={() => fileInputRef.current?.click()}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileSelect}
                        className="hidden"
                    />
                    <div className="flex flex-col items-center gap-4">
                        <div className="p-6 rounded-full bg-primary/10 border border-primary/20 group-hover:bg-primary/20 transition-all">
                            <Upload size={48} className="text-primary" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold mb-2">Upload Image</h3>
                            <p className="text-sm text-muted-foreground">
                                Click to browse or drag & drop an image
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                PNG, JPG, JPEG up to 10MB
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {uploadedImage && (
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
                                    src={uploadedImage}
                                    alt="Uploaded"
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
                        <Button onClick={resetAll} variant="outline" size="lg" className="gap-2">
                            <X size={20} />
                            Cancel
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};
