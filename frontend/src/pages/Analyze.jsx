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
        alert("Please login to submit a complaint");
        // Or handle this better URL direction
        return;
    }

    await analyzeImage(selectedImage, user.username);
  };

  if (!user) {
      return (
          <div className="max-w-md mx-auto mt-20 text-center">
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-slate-800 mb-2">Login Required</h2>
                <p className="text-slate-600 mb-6">You must be registered to file a complaint.</p>
                <Link to="/register" className="bg-primary text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700">
                    Register / Login
                </Link>
              </div>
          </div>
      )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-slate-900">Upload Evidence</h1>
          <p className="mt-4 text-lg text-slate-600">
            Welcome, <span className="font-semibold text-primary">{user.username}</span>.
            Our AI will detect the issue type, location, and severity automatically.
          </p>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
          <ImageUpload onImageSelect={setSelectedImage} />
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-md flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </div>
          )}

          <div className="mt-8 flex justify-end">
            <button
              onClick={handleAnalysis}
              disabled={!selectedImage || loading}
              className={`flex items-center px-6 py-3 rounded-md text-white font-medium transition-all
                ${!selectedImage || loading 
                  ? 'bg-slate-300 cursor-not-allowed' 
                  : 'bg-primary hover:bg-blue-700 shadow-md hover:shadow-lg'
                }
              `}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze Complaint
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
        
        <div className="mt-8 bg-blue-50 border border-blue-100 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-800">Privacy Note</h4>
            <p className="text-sm text-blue-600 mt-1">
                Images are processed locally where possible. GPS data is extracted solely for assigning the complaint to the correct municipal ward.
            </p>
        </div>
      </div>
    </div>
  );
}
