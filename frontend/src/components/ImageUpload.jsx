import React, { useState, useCallback } from 'react';
import { Upload, X, FileImage, AlertCircle } from 'lucide-react';

export default function ImageUpload({ onImageSelect }) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const validateFile = (file) => {
    if (!file.type.startsWith('image/')) {
      setError("Please upload an image file (JPG, PNG).");
      return false;
    }
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      setError("File size exceeds 5MB.");
      return false;
    }
    return true;
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setError(null);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        handleFile(file);
      }
    }
  }, []);

  const handleChange = (e) => {
    e.preventDefault();
    setError(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        handleFile(file);
      }
    }
  };

  const handleFile = (file) => {
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    onImageSelect(file);
  };

  const clearImage = (e) => {
    e.stopPropagation(); // Prevent triggering the dropzone click
    setPreview(null);
    onImageSelect(null);
    // Revoke object URL to avoid memory leaks
    if (preview) URL.revokeObjectURL(preview);
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div 
        className={`relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer transition-colors
          ${dragActive ? "border-primary bg-blue-50" : "border-slate-300 bg-slate-50 hover:bg-slate-100"}
          ${error ? "border-red-400 bg-red-50" : ""}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-upload').click()}
      >
        <input 
          id="file-upload" 
          type="file" 
          className="hidden" 
          accept="image/*"
          onChange={handleChange}
        />

        {preview ? (
          <div className="relative w-full h-full p-2">
            <img 
              src={preview} 
              alt="Upload Preview" 
              className="w-full h-full object-contain rounded"
            />
            <button 
              onClick={clearImage}
              className="absolute top-4 right-4 p-1 bg-white rounded-full shadow-md text-slate-500 hover:text-red-500"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="absolute bottom-4 left-0 right-0 text-center">
                <span className="inline-block px-3 py-1 text-xs font-medium text-white bg-slate-800 bg-opacity-75 rounded-full">
                    Change Image
                </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <Upload className={`w-12 h-12 mb-4 ${dragActive ? "text-primary" : "text-slate-400"}`} />
            <p className="mb-2 text-sm text-slate-500">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500">JPG, PNG (MAX. 5MB)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-center text-sm text-danger">
          <AlertCircle className="w-4 h-4 mr-2" />
          {error}
        </div>
      )}
    </div>
  );
}
