import React, { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { MapPin, FileText, CheckCircle, AlertTriangle, ArrowLeft, Shield, Copy, Edit3, Navigation, Search } from 'lucide-react';
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

  // Location state — editable if EXIF not found
  const hasExifLocation = !!result?.location?.coordinates;
  const [manualAddress, setManualAddress] = useState('');
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');
  const [locationSource, setLocationSource] = useState(hasExifLocation ? 'exif' : 'manual');
  const [detectingGPS, setDetectingGPS] = useState(false);

  // Determine the effective location
  const getEffectiveLocation = () => {
    if (locationSource === 'exif' && result?.location?.coordinates) {
      return {
        lat: result.location.coordinates.lat,
        lon: result.location.coordinates.lon,
        address: result.location.address,
        source: 'exif',
      };
    }
    return {
      lat: parseFloat(manualLat) || 0,
      lon: parseFloat(manualLon) || 0,
      address: manualAddress.trim(),
      source: locationSource === 'device' ? 'device' : 'manual',
    };
  };

  const effectiveLocation = getEffectiveLocation();
  const isLocationValid = effectiveLocation.address.length > 0 && 
    (effectiveLocation.lat !== 0 || effectiveLocation.lon !== 0);

  // Try browser geolocation
  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setSubmitError('Geolocation is not supported by your browser');
      return;
    }
    setDetectingGPS(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        setManualLat(lat.toFixed(6));
        setManualLon(lon.toFixed(6));
        setLocationSource('device');

        // Reverse geocode via Nominatim
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&addressdetails=1`,
            { headers: { 'User-Agent': 'JanSunwaiAI/1.0' } }
          );
          if (res.ok) {
            const data = await res.json();
            setManualAddress(data.display_name || `${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`);
          }
        } catch {
          setManualAddress(`${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`);
        }
        setDetectingGPS(false);
      },
      (err) => {
        console.error('Geolocation error:', err);
        setSubmitError('Could not detect location. Please enter manually.');
        setDetectingGPS(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

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
    if (!isLocationValid) {
      setSubmitError('Location is required. Please enter the location of the issue or use "Detect My Location".');
      return;
    }

    if (!user?.access_token) {
      setSubmitError('Please login to submit a complaint');
      setTimeout(() => navigate('/login'), 2000);
      return;
    }

    if (!complaintText.trim()) {
      setSubmitError('Grievance description cannot be empty.');
      return;
    }
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      const loc = getEffectiveLocation();
      const complaintData = {
        description: complaintText,
        department: classification.department,
        image_url: image_url,
        location: {
          lat: loc.lat,
          lon: loc.lon,
          address: loc.address,
          source: loc.source,
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
  const canSubmit = !isInvalid && isLocationValid && complaintText.trim().length > 0;

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
            <p className="text-green-800 font-medium text-sm">Grievance registered successfully!</p>
            <p className="text-green-700 text-xs">Redirecting to your dashboard...</p>
          </div>
        </div>
      )}

      {/* Step indicator */}
      <div className="mb-6 flex items-center gap-2 text-xs text-gray-400">
        <span className="text-primary font-semibold">Step 1: Upload</span>
        <span>→</span>
        <span className="text-primary font-semibold bg-primary/5 px-2 py-0.5 rounded">Step 2: Review & Submit</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 lg:gap-8">
        {/* Left Column: Evidence (2/5) */}
        <div className="lg:col-span-2 space-y-5">
          {/* Image Evidence Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-primary px-4 py-3 flex justify-between items-center">
              <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Evidence Photo
              </h3>
              <span className={`text-xs px-2.5 py-1 rounded font-medium ${
                isHighConfidence 
                  ? 'bg-green-500/20 text-green-100 border border-green-400/30' 
                  : 'bg-amber-500/20 text-amber-100 border border-amber-400/30'
              }`}>
                {confidence}%
              </span>
            </div>
            <div className="aspect-video w-full bg-gray-100 flex items-center justify-center overflow-hidden">
              <img src={fullImageUrl} alt="Evidence" className="w-full h-full object-contain" />
            </div>
          </div>

          {/* AI Detection Summary */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 space-y-3">
            <h4 className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">AI Analysis</h4>
            <div>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-1">Issue Detected</p>
              <p className="text-sm text-gray-900">{classification.label}</p>
            </div>
            <div>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-1">Department</p>
              <span className={`inline-block px-3 py-1 text-xs font-bold text-white rounded ${
                isInvalid ? 'bg-danger' : 'bg-primary'
              }`}>
                {classification.department}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Grievance Form (3/5) */}
        <div className="lg:col-span-3 space-y-5">
          
          {/* Location Section */}
          <div className={`bg-white rounded-lg shadow-sm border overflow-hidden ${
            !isLocationValid && !hasExifLocation ? 'border-amber-300' : 'border-gray-200'
          }`}>
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-saffron" />
              <h3 className="font-bold text-gray-800 text-sm">Incident Location</h3>
              {!isLocationValid && (
                <span className="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded font-semibold ml-auto">REQUIRED</span>
              )}
              {isLocationValid && (
                <CheckCircle className="w-3.5 h-3.5 text-success ml-auto" />
              )}
            </div>

            <div className="p-5">
              {hasExifLocation ? (
                /* EXIF data found — show read-only */
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 p-2 rounded border border-green-200">
                    <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                    Location extracted from image GPS data
                  </div>
                  <p className="text-sm text-gray-800">{location.address}</p>
                  <p className="text-xs text-gray-400">
                    {location.coordinates.lat.toFixed(4)}°N, {location.coordinates.lon.toFixed(4)}°E
                  </p>
                </div>
              ) : (
                /* No EXIF — manual entry */
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 p-2.5 rounded border border-amber-200">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    No GPS data in image. Please provide the location of the issue.
                  </div>

                  {/* Quick actions */}
                  <button
                    type="button"
                    onClick={handleDetectLocation}
                    disabled={detectingGPS}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded border-2 border-dashed border-primary/30 text-primary text-sm font-medium hover:bg-primary/5 hover:border-primary/50 transition disabled:opacity-50"
                  >
                    {detectingGPS ? (
                      <>
                        <Navigation className="w-4 h-4 animate-pulse" />
                        Detecting location...
                      </>
                    ) : (
                      <>
                        <Navigation className="w-4 h-4" />
                        Use My Current Location
                      </>
                    )}
                  </button>
                  
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-200"></div>
                    </div>
                    <div className="relative flex justify-center text-xs">
                      <span className="bg-white px-3 text-gray-400">or enter manually</span>
                    </div>
                  </div>

                  {/* Manual address */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                      Address / Locality *
                    </label>
                    <input
                      type="text"
                      value={manualAddress}
                      onChange={(e) => { setManualAddress(e.target.value); setLocationSource('manual'); }}
                      placeholder="e.g. MG Road, near Central Mall, Pune"
                      className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                    />
                  </div>

                  {/* Lat/Lon row */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                        Latitude
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={manualLat}
                        onChange={(e) => { setManualLat(e.target.value); setLocationSource('manual'); }}
                        placeholder="e.g. 18.5204"
                        className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                        Longitude
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={manualLon}
                        onChange={(e) => { setManualLon(e.target.value); setLocationSource('manual'); }}
                        placeholder="e.g. 73.8567"
                        className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                      />
                    </div>
                  </div>
                  <p className="text-[10px] text-gray-400">
                    Tip: You can find coordinates from Google Maps — right-click any point and copy the numbers.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Grievance Details — Structured Form, not mail */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <h3 className="font-bold text-gray-800 text-sm">Grievance Description</h3>
              </div>
              <button 
                onClick={handleCopy}
                className="text-xs font-medium text-primary hover:text-primary-light flex items-center gap-1 transition"
              >
                <Copy className="w-3.5 h-3.5" />
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>

            <div className="p-5 space-y-4">
              {/* Read-only summary fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded p-3 border border-gray-100">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-0.5">Complainant</div>
                  <div className="text-sm font-medium text-gray-800">{user?.username || 'Citizen'}</div>
                </div>
                <div className="bg-gray-50 rounded p-3 border border-gray-100">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-0.5">Routed To</div>
                  <div className="text-sm font-medium text-gray-800">{classification.department}</div>
                </div>
              </div>

              {/* Editable complaint description */}
              <div>
                <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                  <Edit3 className="w-3 h-3" />
                  Issue Details (AI-generated — edit if needed)
                </label>
                <textarea 
                  className="w-full min-h-44 p-4 text-gray-700 bg-white border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-y text-sm leading-relaxed"
                  value={complaintText}
                  onChange={(e) => setComplaintText(e.target.value)}
                  placeholder="Describe the issue in detail..."
                />
              </div>
            </div>

            {/* Submit footer */}
            <div className="px-5 py-4 bg-gray-50 border-t border-gray-100">
              {submitError && (
                <div className="mb-3 p-2.5 bg-red-50 text-danger text-sm rounded border border-red-200 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  {submitError}
                </div>
              )}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div className="text-xs text-gray-400 space-y-0.5">
                  {!isLocationValid && (
                    <p className="text-amber-600 font-medium">⚠ Location required to submit</p>
                  )}
                  {!complaintText.trim() && (
                    <p className="text-amber-600 font-medium">⚠ Description required</p>
                  )}
                </div>
                <button 
                  onClick={handleSubmit}
                  disabled={submitting || !canSubmit}
                  className={`px-6 py-2.5 text-white text-sm font-semibold rounded transition disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto ${
                    !canSubmit ? 'bg-gray-400' : 'bg-saffron hover:bg-saffron-light shadow-md hover:shadow-lg'
                  }`}
                  title={
                    isInvalid ? "Cannot submit invalid complaint" 
                    : !isLocationValid ? "Location is required" 
                    : "Submit to authorities"
                  }
                >
                  {isInvalid ? 'Invalid — Cannot Submit' : (submitting ? 'Submitting...' : 'Submit Grievance')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
