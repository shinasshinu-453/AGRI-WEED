import React, { useState, useRef } from 'react';
import { Upload, X, Loader2, CheckCircle2, AlertCircle, Play, Pause } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';

export interface QueueItem {
    id: string;
    file: File;
    preview: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress?: number;
    error?: string;
}

interface BatchUploaderProps {
    onProcess: (file: File) => Promise<void>;
    maxFiles?: number;
    isProcessing: boolean;
}

export const BatchUploader: React.FC<BatchUploaderProps> = ({
    onProcess,
    maxFiles = 20,
    isProcessing,
}) => {
    const [queue, setQueue] = useState<QueueItem[]>([]);
    const [isPaused, setIsPaused] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const processingRef = useRef(false);

    const handleFileSelect = (files: FileList | null) => {
        if (!files) return;

        const newFiles = Array.from(files).slice(0, maxFiles - queue.length);
        const newQueueItems: QueueItem[] = newFiles.map((file) => ({
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            file,
            preview: URL.createObjectURL(file),
            status: 'pending',
        }));

        setQueue((prev) => [...prev, ...newQueueItems]);
    };

    const removeFile = (id: string) => {
        setQueue((prev) => {
            const updated = prev.filter((item) => item.id !== id);
            const removed = prev.find((item) => item.id === id);
            if (removed?.preview) {
                URL.revokeObjectURL(removed.preview);
            }
            return updated;
        });
    };

    const clearCompleted = () => {
        setQueue((prev) => {
            const completed = prev.filter((item) => item.status === 'completed' || item.status === 'failed');
            completed.forEach((item) => URL.revokeObjectURL(item.preview));
            return prev.filter((item) => item.status === 'pending' || item.status === 'processing');
        });
    };

    const clearAll = () => {
        queue.forEach((item) => URL.revokeObjectURL(item.preview));
        setQueue([]);
    };

    const processQueue = async () => {
        if (processingRef.current || isPaused) return;
        processingRef.current = true;

        for (const item of queue) {
            if (isPaused) break;
            if (item.status !== 'pending') continue;

            // Update to processing
            setQueue((prev) =>
                prev.map((q) => (q.id === item.id ? { ...q, status: 'processing' as const } : q))
            );

            try {
                await onProcess(item.file);

                // Update to completed
                setQueue((prev) =>
                    prev.map((q) => (q.id === item.id ? { ...q, status: 'completed' as const } : q))
                );
            } catch (error: any) {
                // Update to failed
                setQueue((prev) =>
                    prev.map((q) =>
                        q.id === item.id
                            ? { ...q, status: 'failed' as const, error: error.message || 'Processing failed' }
                            : q
                    )
                );
            }

            // Small delay between items
            await new Promise((resolve) => setTimeout(resolve, 500));
        }

        processingRef.current = false;
    };

    const handleProcessAll = () => {
        setIsPaused(false);
        processQueue();
    };

    const togglePause = () => {
        setIsPaused((prev) => !prev);
    };

    const pendingCount = queue.filter((q) => q.status === 'pending').length;
    const processingCount = queue.filter((q) => q.status === 'processing').length;
    const completedCount = queue.filter((q) => q.status === 'completed').length;
    const failedCount = queue.filter((q) => q.status === 'failed').length;

    const canProcess = pendingCount > 0 && !isProcessing;

    return (
        <div className="space-y-4">
            {/* Upload Zone */}
            <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${queue.length >= maxFiles
                        ? 'border-muted bg-muted/30 cursor-not-allowed'
                        : 'border-border bg-card hover:bg-accent/50 cursor-pointer'
                    }`}
                onClick={() => queue.length < maxFiles && fileInputRef.current?.click()}
                onDragOver={(e) => {
                    e.preventDefault();
                    if (queue.length < maxFiles) {
                        e.currentTarget.classList.add('border-primary');
                    }
                }}
                onDragLeave={(e) => {
                    e.currentTarget.classList.remove('border-primary');
                }}
                onDrop={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.remove('border-primary');
                    if (queue.length < maxFiles) {
                        handleFileSelect(e.dataTransfer.files);
                    }
                }}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleFileSelect(e.target.files)}
                    disabled={queue.length >= maxFiles}
                />
                <div className="flex flex-col items-center gap-3">
                    <div className="p-4 rounded-full bg-primary/10 border border-primary/20">
                        <Upload size={32} className="text-primary" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold">
                            {queue.length >= maxFiles ? 'Maximum files reached' : 'Upload Multiple Images'}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            Drag & drop or click • Max {maxFiles} images • {queue.length}/{maxFiles} added
                        </p>
                    </div>
                </div>
            </div>

            {/* Queue Statistics */}
            {queue.length > 0 && (
                <Card className="p-4 glass-effect border-white/20">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-yellow-600">{pendingCount}</p>
                            <p className="text-xs text-muted-foreground">Pending</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-bold text-blue-600">{processingCount}</p>
                            <p className="text-xs text-muted-foreground">Processing</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-bold text-green-600">{completedCount}</p>
                            <p className="text-xs text-muted-foreground">Completed</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-bold text-red-600">{failedCount}</p>
                            <p className="text-xs text-muted-foreground">Failed</p>
                        </div>
                    </div>
                </Card>
            )}

            {/* Action Buttons */}
            {queue.length > 0 && (
                <div className="flex gap-2">
                    <Button
                        onClick={handleProcessAll}
                        disabled={!canProcess || processingCount > 0}
                        className="flex-1 gap-2"
                        size="lg"
                    >
                        <Play size={20} />
                        Process All ({pendingCount})
                    </Button>
                    {processingCount > 0 && (
                        <Button onClick={togglePause} variant="outline" size="lg" className="gap-2">
                            {isPaused ? <Play size={20} /> : <Pause size={20} />}
                            {isPaused ? 'Resume' : 'Pause'}
                        </Button>
                    )}
                    <Button onClick={clearCompleted} variant="outline" size="lg" disabled={completedCount === 0 && failedCount === 0}>
                        Clear Done
                    </Button>
                    <Button onClick={clearAll} variant="outline" size="lg">
                        Clear All
                    </Button>
                </div>
            )}

            {/* Queue List */}
            {queue.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {queue.map((item) => (
                        <Card key={item.id} className="relative overflow-hidden group">
                            <div className="aspect-square relative">
                                <img
                                    src={item.preview}
                                    alt={item.file.name}
                                    className="w-full h-full object-cover"
                                />

                                {/* Status Overlay */}
                                <div className={`absolute inset-0 flex items-center justify-center ${item.status === 'pending' ? 'bg-black/20' :
                                        item.status === 'processing' ? 'bg-blue-500/50' :
                                            item.status === 'completed' ? 'bg-green-500/50' :
                                                'bg-red-500/50'
                                    }`}>
                                    {item.status === 'pending' && (
                                        <button
                                            onClick={() => removeFile(item.id)}
                                            className="absolute top-2 right-2 p-1 bg-black/50 hover:bg-black/70 rounded-full transition-colors"
                                        >
                                            <X size={16} className="text-white" />
                                        </button>
                                    )}
                                    {item.status === 'processing' && (
                                        <Loader2 size={32} className="text-white animate-spin" />
                                    )}
                                    {item.status === 'completed' && (
                                        <CheckCircle2 size={32} className="text-white" />
                                    )}
                                    {item.status === 'failed' && (
                                        <AlertCircle size={32} className="text-white" />
                                    )}
                                </div>
                            </div>

                            <div className="p-2">
                                <p className="text-xs truncate font-medium">{item.file.name}</p>
                                <p className="text-[10px] text-muted-foreground">
                                    {(item.file.size / 1024).toFixed(0)} KB
                                </p>
                                {item.error && (
                                    <p className="text-[10px] text-red-600 truncate mt-1">{item.error}</p>
                                )}
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};
