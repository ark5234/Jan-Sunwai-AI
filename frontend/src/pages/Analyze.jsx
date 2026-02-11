import React, { useState } from 'react';
import ImageUpload from '../components/ImageUpload';
import { ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import useAnalyze from '../hooks/useAnalyze';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export default function Analyze() {
  const [selectedImage, setSelectedImage] = useState(null);
  const { analyzeImage, loading, error } = useAnalyze();
  const { user } = useAuth();

  const handleAnalysis = async () => {
    if (!selectedImage) return;
    
    if (!user) {
        // User check is already handled below with better UI
        return;
    }

    await analyzeImage(selectedImage, user.username);
  };

  if (!user || !user.access_token) {
      return (
          <div className="max-w-md mx-auto mt-20 text-center">
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-slate-800 mb-2">Login Required</h2>
                <p className="text-slate-600 mb-6">You must be logged in with a valid session to file a complaint.</p>
                <Link to="/login" className="bg-primary text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700">
                    Login
                </Link>
              </div>
          </div>
      )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3">File a Complaint</h1>
          <p className="text-base sm:text-lg text-slate-600">
            Welcome, <span className="font-semibold text-primary">{user.username}</span>! Upload a photo of the civic issue.
          </p>
          <p className="text-sm text-slate-500 mt-2">
            Our AI will automatically detect the issue type, location, and department.
          </p>
        </div>

        <div className="bg-white p-6 sm:p-8 rounded-xl shadow-sm border border-slate-200">
          <ImageUpload onImageSelect={setSelectedImage} />
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-md flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </div>
          )}

          <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="text-sm text-slate-500 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>Ensure the image clearly shows the issue</span>
            </div>
            <button
              onClick={handleAnalysis}
              disabled={!selectedImage || loading}
              className={`flex items-center px-8 py-3 rounded-lg text-white font-semibold transition-all text-base w-full sm:w-auto justify-center
                ${!selectedImage || loading 
                  ? 'bg-slate-300 cursor-not-allowed' 
                  : 'bg-primary hover:bg-blue-700 shadow-md hover:shadow-lg transform hover:scale-105'
                }
              `}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing Image...
                </>
              ) : (
                <>
                  Analyze & Generate Complaint
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
        
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 sm:p-5">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">What We Detect</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-blue-700">
                <div>• Road & Potholes</div>
                <div>• Drainage Issues</div>
                <div>• Garbage Dumps</div>
                <div>• Street Lights</div>
                <div>• Fallen Trees</div>
                <div>• Encroachments</div>
            </div>
        </div>

        <div className="mt-4 bg-slate-50 border border-slate-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-slate-700 mb-1">Privacy Note</h4>
            <p className="text-xs text-slate-600">
                Images are analyzed locally. GPS data is used only for complaint routing to the correct department.
            </p>
        </div>
      </div>
    </div>
  );
}
