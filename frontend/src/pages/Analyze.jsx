import React, { useState } from 'react';
import ImageUpload from '../components/ImageUpload';
import { ArrowRight, Loader2, AlertCircle, Shield, Info } from 'lucide-react';
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
        return;
    }

    await analyzeImage(selectedImage, user.username);
  };

  if (!user || !user.access_token) {
      return (
          <div className="max-w-md mx-auto mt-20 text-center px-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
                <AlertCircle className="w-10 h-10 text-amber-600 mx-auto mb-3" />
                <h2 className="text-lg font-bold text-gray-900 mb-2">Authentication Required</h2>
                <p className="text-gray-600 text-sm mb-5">You must be logged in to file a complaint.</p>
                <Link to="/login" className="bg-primary text-white px-6 py-2.5 rounded font-medium hover:bg-primary-light transition">
                    Login
                </Link>
              </div>
          </div>
      )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div className="max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-xs text-saffron font-semibold uppercase tracking-widest mb-2">
            <Shield className="w-4 h-4" />
            File a Grievance
          </div>
          <h1 className="govt-heading text-2xl sm:text-3xl text-gray-900 mb-2">Upload Evidence</h1>
          <p className="text-gray-600 text-sm sm:text-base">
            Welcome, <span className="font-semibold text-primary">{user.username}</span>. Upload a photograph of the civic issue. 
            The system will identify the problem, extract location data, and route it to the appropriate department.
          </p>
        </div>

        {/* Upload Card */}
        <div className="bg-white p-6 sm:p-8 rounded-lg shadow-sm border border-gray-200">
          <ImageUpload onImageSelect={setSelectedImage} />
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 text-danger text-sm rounded border border-red-200 flex items-center">
              <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </div>
          )}

          <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="text-xs text-gray-500 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5" />
              <span>Ensure the image clearly shows the issue</span>
            </div>
            <button
              onClick={handleAnalysis}
              disabled={!selectedImage || loading}
              className={`flex items-center px-6 py-3 rounded text-white font-semibold transition text-sm w-full sm:w-auto justify-center
                ${!selectedImage || loading 
                  ? 'bg-gray-300 cursor-not-allowed' 
                  : 'bg-saffron hover:bg-saffron-light shadow-md hover:shadow-lg'
                }
              `}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing Image...
                </>
              ) : (
                <>
                  Analyze & Generate Complaint
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
        
        {/* Detectable Issues */}
        <div className="mt-6 bg-primary/5 border border-primary/10 rounded-lg p-4 sm:p-5">
            <h4 className="text-sm font-semibold text-primary mb-2">Detectable Issues</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-gray-600">
                <div>• Roads & Potholes</div>
                <div>• Drainage & Sewage</div>
                <div>• Garbage & Sanitation</div>
                <div>• Street Lighting</div>
                <div>• Power Supply</div>
                <div>• Traffic & Encroachment</div>
            </div>
        </div>

        {/* Privacy banner */}
        <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-xs font-semibold text-gray-600 mb-1">Data Privacy</h4>
            <p className="text-xs text-gray-500">
                All images are processed locally. GPS data is used solely for routing the complaint to the correct jurisdiction.
            </p>
        </div>
      </div>
    </div>
  );
}
