import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import imageCompression from 'browser-image-compression';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadMetrics, setUploadMetrics] = useState(null);
  const navigate = useNavigate();

  const getImageDimensions = (imageFile) =>
    new Promise((resolve) => {
      const objectUrl = URL.createObjectURL(imageFile);
      const img = new Image();
      img.onload = () => {
        resolve({ width: img.naturalWidth, height: img.naturalHeight });
        URL.revokeObjectURL(objectUrl);
      };
      img.onerror = () => {
        resolve({ width: null, height: null });
        URL.revokeObjectURL(objectUrl);
      };
      img.src = objectUrl;
    });

  const getSafeUploadName = (originalName, mimeType) => {
    const fallbackBase = 'upload';
    const baseName = (originalName || fallbackBase).replace(/\.[^/.]+$/, '');
    const normalizedMime = (mimeType || '').toLowerCase();

    if (normalizedMime === 'image/webp') {
      return `${baseName}.webp`;
    }
    if (normalizedMime === 'image/png') {
      return `${baseName}.png`;
    }
    return `${baseName}.jpg`;
  };

  const analyzeImage = async (file, _username = "Concerned Citizen", language = "en", userGrievanceText = "") => {
    setLoading(true);
    setError(null);
    setUploadMetrics(null);

    let uploadFile = file;
    const preferredType = file.type && file.type.startsWith('image/') ? file.type : 'image/jpeg';
    const shouldCompress = file.size > (1024 * 1024);
    if (shouldCompress) {
      try {
        // Compress to reduce upload time and backend load, while preserving
        // camera metadata (including GPS EXIF) when available.
        uploadFile = await imageCompression(file, {
          maxSizeMB: 1,
          maxWidthOrHeight: 1920,
          useWebWorker: true,
          initialQuality: 0.85,
          fileType: preferredType,
          preserveExif: true,
        });
      } catch (compressionError) {
        void compressionError
        uploadFile = file;
      }
    }

    const dimensions = await getImageDimensions(uploadFile);
    setUploadMetrics({
      originalBytes: file.size,
      compressedBytes: uploadFile.size,
      width: dimensions.width,
      height: dimensions.height,
    });

    const formData = new FormData();
    const uploadMime = uploadFile.type || preferredType || 'image/jpeg';
    const uploadName = getSafeUploadName(file.name, uploadMime);
    formData.append('file', uploadFile, uploadName);
    formData.append('language', language);
    const normalizedUserText = typeof userGrievanceText === 'string' ? userGrievanceText.trim() : '';
    if (normalizedUserText.length > 0) {
      formData.append('user_grievance_text', normalizedUserText);
    }
    // Username is extracted from Token in backend now
    
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        withCredentials: true,
      });
      
      // Success! Navigate to results page with data
      navigate('/result', { state: { result: response.data, language } });
      
    } catch (err) {
        if (err.response?.status === 401) {
            setError("Session expired. Please sign in again.");
        } else if (err.response?.status === 503) {
          setError(err.response?.data?.message || "AI analysis unavailable — please try again in a few minutes.");
        } else {
            setError(err.response?.data?.detail || "Failed to analyze image. Please try again.");
        }
    } finally {
      setLoading(false);
    }
  };

  return { analyzeImage, loading, error, uploadMetrics };
}
