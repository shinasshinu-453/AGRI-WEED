import React, { useRef } from 'react';
import { Upload, Image as ImageIcon } from 'lucide-react';

interface ImageUploaderProps {
  onImageUpload: (file: File) => void;
  isProcessing: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageUpload, isProcessing }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onImageUpload(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onImageUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div 
      className={`border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-white transition-all
        ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:border-emerald-500 hover:bg-emerald-50 cursor-pointer'}`}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => !isProcessing && fileInputRef.current?.click()}
    >
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        accept="image/*" 
        className="hidden" 
        disabled={isProcessing}
      />
      <div className="flex flex-col items-center justify-center space-y-3">
        <div className="p-4 bg-emerald-100 rounded-full text-emerald-600">
          <Upload size={32} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Upload Field Image</h3>
          <p className="text-slate-500 text-sm mt-1">Drag & drop or click to browse</p>
          <p className="text-xs text-slate-400 mt-2">Supports JPG, PNG (Max 5MB)</p>
        </div>
      </div>
    </div>
  );
};
