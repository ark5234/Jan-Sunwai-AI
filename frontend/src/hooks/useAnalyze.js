import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000'; // Hardcoded for dev

export default function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const analyzeImage = async (file, username = "Concerned Citizen") => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('username', username);

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      // Success! Navigate to results page with data
      navigate('/result', { state: { result: response.data } });
      
    } catch (err) {
        console.error("Analysis failed:", err);
        setError(err.response?.data?.detail || "Failed to analyze image. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return { analyzeImage, loading, error };
}
