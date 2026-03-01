import React, { useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { MapPin, FileText, CheckCircle, AlertTriangle, ArrowLeft, Shield, Copy } from 'lucide-react';
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
  const [copied, setCopied] = useState(false);

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <h2 className="text-xl font-bold text-gray-900">No Result Found</h2>
        <p className="text-gray-600 mb-6 text-sm">Please upload an image first.</p>
        <Link to="/analyze" className="text-primary hover:underline font-medium">Go back to Upload</Link>
      </div>
    );
  }

  const { classification, location, generated_complaint, image_url } = result;
  
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
          model_used: classification.model_used || 'qwen2.5vl:3b',
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
      
      setSubmitSuccess(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
      
    } catch (error) {
      console.error('Submission error:', error);
      setSubmitError(error.response?.data?.detail || 'Failed to submit complaint. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleCopy = () => {
    navigator.clipboard.writeText(complaintText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cleanPath = image_url.replace(/\\/g, '/');
  const fullImageUrl = `http://localhost:8000/${cleanPath}`;

  const confidence = (classification.confidence * 100).toFixed(1);
  const isHighConfidence = classification.confidence > 0.8;
  const isInvalid = ['Invalid Content', 'Uncertain'].includes(classification.department);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link to="/analyze" className="inline-flex items-center text-sm text-gray-500 hover:text-primary transition">
          <ArrowLeft className="w-4 h-4 mr-1" />
          File Another Complaint
        </Link>
      </div>

      {/* Success Banner */}
      {submitSuccess && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3 animate-fadeIn">
          <CheckCircle className="w-5 h-5 text-success shrink-0" />
          <div>
            <p className="text-green-800 font-medium text-sm">Complaint submitted successfully!</p>
            <p className="text-green-700 text-xs">Redirecting to your dashboard...</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        {/* Left Column: Evidence & Classification */}
        <div className="space-y-5">
          {/* Image Evidence Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-primary px-4 py-3 flex justify-between items-center">
              <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Visual Evidence
              </h3>
              <span className={`text-xs px-2.5 py-1 rounded font-medium ${
                isHighConfidence 
                  ? 'bg-green-500/20 text-green-100 border border-green-400/30' 
                  : 'bg-amber-500/20 text-amber-100 border border-amber-400/30'
              }`}>
                Confidence: {confidence}%
              </span>
            </div>
            <div className="aspect-video w-full bg-gray-100 flex items-center justify-center overflow-hidden">
              <img src={fullImageUrl} alt="Evidence" className="w-full h-full object-contain" />
            </div>
            <div className="p-4 bg-white space-y-3">
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-1">Detected Issue</p>
                <p className="text-sm font-semibold text-gray-900">{classification.label}</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-1">Assigned Department</p>
                <span className={`inline-block px-3 py-1 text-xs font-bold text-white rounded ${
                  isInvalid ? 'bg-danger' : 'bg-primary'
                }`}>
                  {classification.department}
                </span>
              </div>
            </div>
          </div>

          {/* Location Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-saffron/10 rounded text-saffron">
                <MapPin className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Location</p>
                <p className="text-gray-800 text-sm mt-0.5">{location.address}</p>
                {location.coordinates && (
                  <p className="text-xs text-gray-400 mt-1">
                    {location.coordinates.lat.toFixed(4)}°N, {location.coordinates.lon.toFixed(4)}°E
                  </p>
                )}
                {!location.coordinates && (
                  <div className="mt-2 flex items-center text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
                    <AlertTriangle className="w-3 h-3 mr-1.5 shrink-0" />
                    GPS data not found in image. Default location used.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Complaint Draft */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
          <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex justify-between items-center rounded-t-lg">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              <h3 className="font-bold text-gray-800 text-sm">Official Complaint Draft</h3>
            </div>
            <button 
              onClick={handleCopy}
              className="text-xs font-medium text-primary hover:text-primary-light flex items-center gap-1 transition"
            >
              <Copy className="w-3.5 h-3.5" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div className="p-5 grow">
            <textarea 
              className="w-full h-full min-h-95 p-4 text-gray-700 bg-gray-50 border border-gray-200 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none font-serif text-sm leading-relaxed"
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
            />
          </div>
          <div className="px-5 py-4 bg-gray-50 border-t border-gray-100 rounded-b-lg">
            {submitError && (
              <div className="mb-3 p-2.5 bg-red-50 text-danger text-xs rounded border border-red-200">
                {submitError}
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="text-[10px] text-gray-400 uppercase tracking-wider">
                AI-Generated • Editable
              </span>
              <button 
                onClick={handleSubmit}
                disabled={submitting || isInvalid}
                className={`px-5 py-2 text-white text-sm font-semibold rounded transition disabled:opacity-50 disabled:cursor-not-allowed ${
                  isInvalid ? 'bg-gray-400' : 'bg-saffron hover:bg-saffron-light'
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
