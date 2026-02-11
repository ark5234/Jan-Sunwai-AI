import React, { useState } from 'react';
import ImageUpload from '../components/ImageUpload';
import { ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import useAnalyze from '../hooks/useAnalyze';

export default function Analyze() {
  const [selectedImage, setSelectedImage] = useState(null);
  const { analyzeImage, loading, error } = useAnalyze();

  const handleAnalysis = async () => {
    if (!selectedImage) return;
    // Default username for now
    await analyzeImage(selectedImage, "Vikram Singh");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-slate-900">Upload Evidence</h1>
          <p className="mt-4 text-lg text-slate-600">
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
