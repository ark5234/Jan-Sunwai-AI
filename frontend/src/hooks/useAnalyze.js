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

    // Get Token
    const storedUser = localStorage.getItem('jan_sunwai_user');
    let token = null;
    if (storedUser) {
        try {
            const parsed = JSON.parse(storedUser);
            token = parsed.access_token;
        } catch (e) {
            console.error("Failed to parse user token", e);
        }
    }

    if (!token) {
        setError("Session invalid or expired. Please log out and log back in to get a new token.");
        setLoading(false);
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    // Username is extracted from Token in backend now
    
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
      });
      
      // Success! Navigate to results page with data
      navigate('/result', { state: { result: response.data } });
      
    } catch (err) {
        console.error("Analysis failed:", err);
        if (err.response?.status === 401) {
            setError("Session expired. Please log out and log back in.");
            // Clear invalid session
            localStorage.removeItem('jan_sunwai_user');
        } else {
            setError(err.response?.data?.detail || "Failed to analyze image. Please try again.");
        }
    } finally {
      setLoading(false);
    }
  };

  return { analyzeImage, loading, error };
}
