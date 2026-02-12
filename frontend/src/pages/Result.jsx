import React, { useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { MapPin, FileText, CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

export default function Result() {
  const { state } = useLocation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const result = state?.result;
  
  const [complaintText, setComplaintText] = useState(result?.generated_complaint || '');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <h2 className="text-2xl font-bold text-slate-800">No Result Found</h2>
        <p className="text-slate-600 mb-6">Please upload an image first.</p>
        <Link to="/analyze" className="text-primary hover:underline">Go back to Upload</Link>
      </div>
    );
  }

  const { classification, location, generated_complaint, image_url } = result;
  
  // Handle complaint submission
  const handleSubmit = async () => {
    if (!user?.access_token) {
      setSubmitError('Please login to submit a complaint');
      setTimeout(() => navigate('/login'), 2000);
      return;
    }
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      const complaintData = {
        description: complaintText,
        department: classification.department,
        image_url: image_url,
        location: {
          lat: location.coordinates?.lat || 0,
          lon: location.coordinates?.lon || 0,
          address: location.address,
          source: location.coordinates ? 'exif' : 'manual'
        },
        ai_metadata: {
          model_used: 'CLIP-ViT-B/32',
          confidence_score: classification.confidence,
          detected_department: classification.department,
          detected_issue: classification.label,
          labels: classification.all_scores?.map(s => s.label) || [classification.label]
        }
      };
      
      const response = await axios.post(
        'http://localhost:8000/complaints',
        complaintData,
        {
          headers: {
            'Authorization': `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Success! Show success message and navigate after brief delay
      setSubmitSuccess(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000); // Navigate after 2 seconds
      
    } catch (error) {
      console.error('Submission error:', error);
      setSubmitError(error.response?.data?.detail || 'Failed to submit complaint. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };
  
  // Construct full image URL (assuming backend is on localhost:8000)
  // Ensure image_url is sanitized of backslashes from Windows paths
  const cleanPath = image_url.replace(/\\/g, '/');
  const fullImageUrl = `http://localhost:8000/${cleanPath}`;

  const confidence = (classification.confidence * 100).toFixed(1);
  const isHighConfidence = classification.confidence > 0.8;
  const isInvalid = ['Invalid Content', 'Uncertain'].includes(classification.department);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-6">
        <Link to="/analyze" className="inline-flex items-center text-sm text-slate-500 hover:text-primary transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Upload Another
        </Link>
      </div>

      {/* Success Notification */}
      {submitSuccess && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3 animate-fadeIn">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
          <div>
            <p className="text-green-800 font-medium">Complaint submitted successfully!</p>
            <p className="text-green-700 text-sm">Redirecting to your dashboard...</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Evidence & Details */}
        <div className="space-y-6">
          {/* Image Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-semibold text-slate-700">Visual Evidence</h3>
              <span className={`text-xs px-2 py-1 rounded-full border ${isHighConfidence ? 'bg-green-50 text-green-700 border-green-200' : 'bg-yellow-50 text-yellow-700 border-yellow-200'}`}>
                AI Confidence: {confidence}%
              </span>
            </div>
            <div className="aspect-video w-full bg-slate-100 flex items-center justify-center overflow-hidden">
              <img src={fullImageUrl} alt="Evidence" className="w-full h-full object-contain" />
            </div>
            <div className="p-4 bg-white border-t border-slate-100">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg text-primary">
                    <CheckCircle className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Detected Issue</p>
                    <p className="text-base font-semibold text-slate-900">{classification.label}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 pl-11">
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-1">Assigned Department</p>
                    <span className={`inline-block px-3 py-1.5 text-sm font-bold text-white rounded-full shadow-sm ${
                      isInvalid ? 'bg-red-500' : 'bg-primary'
                    }`}>
                      {classification.department}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Location Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
             <div className="flex items-start gap-3">
                <div className="p-2 bg-orange-100 rounded-lg text-secondary">
                  <MapPin className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Location</p>
                  <p className="text-slate-800 text-sm mt-1">{location.address}</p>
                  {location.coordinates && (
                    <p className="text-xs text-slate-400 mt-1">
                      Lat: {location.coordinates.lat.toFixed(4)}, Lon: {location.coordinates.lon.toFixed(4)}
                    </p>
                  )}
                  {!location.coordinates && (
                    <div className="mt-2 flex items-center text-xs text-amber-600 bg-amber-50 p-2 rounded">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        GPS Data missing from image. Using default defaults.
                    </div>
                  )}
                </div>
              </div>
          </div>
        </div>

        {/* Right Column: The Generated Letter */}
        <div className="bg-white rounded-xl shadow-lg border border-primary/20 flex flex-col h-full">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center rounded-t-xl">
                 <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    <h3 className="font-bold text-slate-800">Official Complaint Draft</h3>
                 </div>
                 <button 
                    onClick={() => navigator.clipboard.writeText(generated_complaint)}
                    className="text-xs font-medium text-primary hover:text-blue-700"
                 >
                    Copy Text
                 </button>
            </div>
            <div className="p-6 flex-grow">
                <textarea 
                    className="w-full h-full min-h-[400px] p-4 text-slate-700 bg-slate-50 border border-slate-200 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none font-serif leading-relaxed"
                    value={complaintText}
                    onChange={(e) => setComplaintText(e.target.value)}
                />
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 rounded-b-xl">
                {submitError && (
                  <div className="mb-3 p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200">
                    {submitError}
                  </div>
                )}
                <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">
                        Generated by LLaVA AI
                    </span>
                    <button 
                        onClick={handleSubmit}
                        disabled={submitting || isInvalid}
                        className={`px-4 py-2 text-white text-sm font-medium rounded transition disabled:opacity-50 disabled:cursor-not-allowed ${
                          isInvalid ? 'bg-slate-400' : 'bg-primary hover:bg-blue-700'
                        }`}
                        title={isInvalid ? "Cannot submit invalid complaint" : "Submit to authorities"}
                    >
                        {isInvalid ? 'Invalid Complaint' : (submitting ? 'Submitting...' : 'Submit Complaint')}
                    </button>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
