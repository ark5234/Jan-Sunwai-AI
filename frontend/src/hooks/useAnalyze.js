import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import imageCompression from 'browser-image-compression';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

  const analyzeImage = async (file, _username = "Concerned Citizen", language = "en") => {
    setLoading(true);
    setError(null);
    setUploadMetrics(null);

    // Get Token
    const storedUser = localStorage.getItem('jan_sunwai_user');
    let token = null;
    if (storedUser) {
        try {
            const parsed = JSON.parse(storedUser);
            token = parsed.access_token;
      } catch (_e) {
        // Ignore malformed local session; handled as missing token below.
        }
    }

    if (!token) {
        setError("Session invalid or expired. Please log out and log back in to get a new token.");
        setLoading(false);
        return;
    }

    let uploadFile = file;
    try {
      // Compress to reduce upload time and backend load.
      uploadFile = await imageCompression(file, {
        maxSizeMB: 1,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        initialQuality: 0.85,
      });
    } catch (compressionError) {
      void compressionError
      uploadFile = file;
    }

    const dimensions = await getImageDimensions(uploadFile);
    setUploadMetrics({
      originalBytes: file.size,
      compressedBytes: uploadFile.size,
      width: dimensions.width,
      height: dimensions.height,
    });

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('language', language);
    // Username is extracted from Token in backend now
    
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
      });
      
      // Success! Navigate to results page with data
      navigate('/result', { state: { result: response.data, language } });
      
    } catch (err) {
        if (err.response?.status === 401) {
            setError("Session expired. Please log out and log back in.");
            // Clear invalid session
            localStorage.removeItem('jan_sunwai_user');
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
