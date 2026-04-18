import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { MapPin, FileText, CheckCircle, AlertTriangle, ArrowLeft, Shield, Copy, Edit3, Navigation, Search, RefreshCw, Map as MapIcon, X, Layers, ChevronDown, ChevronRight } from 'lucide-react';
import Map, { Marker as MapMarker, NavigationControl } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useAuth } from '../context/AuthContext';
import FormattedComplaintText from '../components/FormattedComplaintText';

// Map tile sources. Set VITE_MAPPLS_API_KEY for official GoI-compliant tiles.
const _MAPPLS_KEY = import.meta.env.VITE_MAPPLS_API_KEY;

const _STREET_STYLE = _MAPPLS_KEY
  ? `https://apis.mappls.com/advancedmaps/v1/${_MAPPLS_KEY}/map_sdk_library/`
  : {
      version: 8,
      sources: {
        carto: {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          maxzoom: 19,
          attribution:
            '\u00a9 <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors \u00a9 <a href="https://carto.com/attributions">CARTO</a>',
        },
      },
      layers: [{ id: 'carto', type: 'raster', source: 'carto' }],
    };

const _SATELLITE_STYLE = {
  version: 8,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        'Tiles \u00a9 Esri \u2014 Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, GIS User Community',
    },
  },
  layers: [{ id: 'satellite', type: 'raster', source: 'satellite' }],
};
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
// Static files (uploads/) are served at the root, not under /api/v1
const STATIC_BASE_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');

const toImageUrl = (imagePath) => {
  const raw = typeof imagePath === 'string' ? imagePath.trim() : '';
  if (!raw) return '';
  if (/^https?:\/\//i.test(raw) || raw.startsWith('data:')) return raw;
  const cleanPath = raw.replace(/\\/g, '/').replace(/^\/+/, '');
  return cleanPath ? `${STATIC_BASE_URL}/${encodeURI(cleanPath)}` : '';
};


export default function Result() {
  const { state } = useLocation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const result = state?.result;
  const language = state?.language || 'en';
  const [classificationState, setClassificationState] = useState(result?.classification || {});
  const [analysisToken, setAnalysisToken] = useState(result?.analysis_token || '');
  const [userContextText, setUserContextText] = useState((result?.user_grievance_text || '').trim());
  const [showContextEditor, setShowContextEditor] = useState(true);
  const [showComplaintEditor, setShowComplaintEditor] = useState(false);
  
  const [complaintText, setComplaintText] = useState(result?.generated_complaint || '');
  const [generationStatus, setGenerationStatus] = useState(result?.generation_status || 'completed');
  const [generationJobId, setGenerationJobId] = useState(result?.generation_job_id);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [regenerateError, setRegenerateError] = useState(null);
  const [regenLang, setRegenLang] = useState(language);
  const [showRegenLang, setShowRegenLang] = useState(false);
  const regenLangRef = useRef(null);

  // Close regen-lang dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (regenLangRef.current && !regenLangRef.current.contains(e.target)) {
        setShowRegenLang(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    if (!generationJobId || !['queued', 'processing'].includes(generationStatus)) return;

    const POLL_INTERVAL_MS = 3000;
    const MAX_ATTEMPTS = 60; // give up after ~3 minutes
    let attempts = 0;
    let cancelled = false;

    const intervalId = setInterval(async () => {
      attempts += 1;
      try {
        const res = await axios.get(`${API_BASE_URL}/complaints/generation/${generationJobId}`);
        if (cancelled) return;
        const data = res.data;
        if (data.status === 'completed') {
          setComplaintText(data.generated_complaint || '');
          setGenerationStatus('completed');
          clearInterval(intervalId);
        } else if (data.status === 'failed') {
          setComplaintText('AI draft failed. Please write the complaint manually.');
          setGenerationStatus('failed');
          clearInterval(intervalId);
        } else if (attempts >= MAX_ATTEMPTS) {
          setGenerationStatus('timeout');
          clearInterval(intervalId);
        }
      } catch (err) {
        if (cancelled) return;
        console.error('Generation polling error:', err);
        if (attempts >= MAX_ATTEMPTS) clearInterval(intervalId);
      }
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [generationJobId, generationStatus, user]);

  // Location state — editable if EXIF not found
  const hasExifLocation = !!result?.location?.coordinates;
  const [manualAddress, setManualAddress] = useState('');
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');
  const [locationSource, setLocationSource] = useState(hasExifLocation ? 'exif' : 'manual');
  const [detectingGPS, setDetectingGPS] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [mapSatellite, setMapSatellite] = useState(false);
  const [pinPos, setPinPos] = useState(null); // {lat, lng}
  const [reverseGeocoding, setReverseGeocoding] = useState(false);
  const mapRef = useRef(null);

  // Address autocomplete state
  const [addressSuggestions, setAddressSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [fetchingSuggestions, setFetchingSuggestions] = useState(false);
  const suggestionRef = useRef(null);
  const debounceTimer = useRef(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (suggestionRef.current && !suggestionRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const fetchAddressSuggestions = useCallback((query) => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    if (!query || query.length < 3) {
      setAddressSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    debounceTimer.current = setTimeout(async () => {
      setFetchingSuggestions(true);
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=6&countrycodes=in&addressdetails=1`,
          { headers: { 'User-Agent': 'JanSunwaiAI/1.0' } }
        );
        if (res.ok) {
          const data = await res.json();
          setAddressSuggestions(data);
          setShowSuggestions(data.length > 0);
        }
      } catch {
        setAddressSuggestions([]);
      } finally {
        setFetchingSuggestions(false);
      }
    }, 350);
  }, []);

  const handleSelectSuggestion = (item) => {
    setManualAddress(item.display_name);
    setManualLat(parseFloat(item.lat).toFixed(6));
    setManualLon(parseFloat(item.lon).toFixed(6));
    setPinPos({ lat: parseFloat(item.lat), lng: parseFloat(item.lon) });
    setLocationSource('manual');
    setShowSuggestions(false);
    setAddressSuggestions([]);
    if (mapRef.current) {
      mapRef.current.flyTo({ center: [parseFloat(item.lon), parseFloat(item.lat)], zoom: 15, duration: 900 });
    }
  };

  const handleMapPin = async (lat, lng) => {
    setPinPos({ lat, lng });
    setManualLat(lat.toFixed(6));
    setManualLon(lng.toFixed(6));
    setLocationSource('manual');
    setReverseGeocoding(true);
    mapRef.current?.flyTo({ center: [lng, lat], zoom: 15, duration: 900 });
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1`,
        { headers: { 'User-Agent': 'JanSunwaiAI/1.0' } }
      );
      if (res.ok) {
        const data = await res.json();
        setManualAddress(data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`);
      }
    } catch {
      setManualAddress(`${lat.toFixed(4)}, ${lng.toFixed(4)}`);
    }
    setReverseGeocoding(false);
  };

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

  const { location, image_url } = result;
  
  const handleSubmit = async () => {
    if (!isLocationValid) {
      setSubmitError('Location is required. Please enter the location of the issue or use "Detect My Location".');
      return;
    }

    if (!user) {
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
      const userHint = userContextText.trim();
      const complaintData = {
        description: complaintText,
        department: classificationState.department,
        user_grievance_text: userHint || null,
        image_url: image_url,
        location: {
          lat: loc.lat,
          lon: loc.lon,
          address: loc.address,
          source: loc.source,
        },
        ai_metadata: {
          model_used: classificationState.model_used || 'qwen2.5vl:3b',
          confidence_score: classificationState.confidence,
          detected_department: classificationState.department,
          detected_issue: classificationState.label,
          labels: classificationState.all_scores?.map(s => s.label) || [classificationState.label]
        },
        analysis_token: analysisToken || null,
        language: language,
      };
      
      const response = await axios.post(
        `${API_BASE_URL}/complaints`,
        complaintData
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

  const handleRegenerate = async () => {
    setRegenerateError(null);
    setRegenerating(true);
    setShowRegenLang(false);
    try {
      const userHint = userContextText.trim();
      const res = await axios.post(
        `${API_BASE_URL}/analyze/regenerate`,
        {
          classification: classificationState,
          location: result?.location || {},
          image_url,
          language: regenLang,
          user_grievance_text: userHint,
        }
      );
      const { job_id } = res.data;
      if (res.data?.classification) {
        setClassificationState(res.data.classification);
      }
      if (res.data?.analysis_token) {
        setAnalysisToken(res.data.analysis_token);
      }
      setComplaintText('');
      setShowComplaintEditor(false);
      setGenerationJobId(job_id);
      setGenerationStatus('queued');
    } catch (err) {
      console.error('Regenerate error:', err);
      setRegenerateError('Failed to start regeneration. Please try again.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleApplyContextAndRegenerate = async () => {
    if (!userContextText.trim()) {
      setRegenerateError('Please enter corrected image context first.');
      return;
    }
    await handleRegenerate();
  };

  const fullImageUrl = toImageUrl(image_url);

  const confidenceValue = Number(classificationState?.confidence || 0);
  const confidence = (confidenceValue * 100).toFixed(1);
  const isHighConfidence = confidenceValue > 0.8;
  const isInvalid = ['Invalid Content', 'Uncertain'].includes(classificationState?.department);
  const isGenerating = ['queued', 'processing'].includes(generationStatus);
  const canSubmit = !isInvalid && isLocationValid && complaintText.trim().length > 0 && !isGenerating;

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
              <p className="text-sm text-gray-900">
                {(() => {
                  const raw = classificationState.label || '';
                  // Hide garbled/raw JSON output from the model
                  const isGarbled = !raw || raw.trim().startsWith('{') || raw.trim().startsWith('[') || raw.length < 4;
                  return isGarbled ? (classificationState.vision_description || classificationState.department || 'Civic issue detected') : raw;
                })()}
              </p>
            </div>
            <div>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-1">Department</p>
              <span className={`inline-block px-3 py-1 text-xs font-bold text-white rounded ${
                isInvalid ? 'bg-danger' : 'bg-primary'
              }`}>
                {classificationState.department}
              </span>
            </div>
            {classificationState?.routing_source === 'user_text' && userContextText.trim() && (
              <div className="p-2.5 bg-indigo-50 border border-indigo-200 rounded text-xs text-indigo-700">
                Routing used your optional grievance hint to refine department detection.
              </div>
            )}
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
                <div className="flex items-start gap-3 p-3.5 bg-green-50 rounded-xl border border-green-200">
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-green-700 mb-0.5">GPS extracted from photo</p>
                    <p className="text-sm text-gray-800 leading-snug">{location.address}</p>
                    <p className="text-xs text-gray-400 font-mono mt-1">
                      {location.coordinates.lat.toFixed(6)}, {location.coordinates.lon.toFixed(6)}
                    </p>
                  </div>
                </div>
              ) : (
                /* No EXIF — manual entry */
                <div className="space-y-4">
                  {/* Warning banner */}
                  <div className="flex items-center gap-2.5 text-sm text-amber-800 bg-amber-50 px-4 py-3 rounded-xl border border-amber-200">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500" />
                    <span className="text-xs font-medium">No GPS data in photo — please pin the location below.</span>
                  </div>

                  {/* GPS button */}
                  <button
                    type="button"
                    onClick={handleDetectLocation}
                    disabled={detectingGPS}
                    className="w-full flex items-center justify-center gap-2.5 px-4 py-3.5 rounded-xl bg-linear-to-r from-primary to-indigo-600 text-white text-sm font-semibold shadow-sm hover:shadow-md hover:from-indigo-700 hover:to-indigo-700 active:scale-[0.98] transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {detectingGPS ? (
                      <>
                        <Navigation className="w-4 h-4 animate-spin" />
                        Detecting your location…
                      </>
                    ) : (
                      <>
                        <Navigation className="w-4 h-4" />
                        Use My Current Location
                      </>
                    )}
                  </button>

                  {/* Map toggle button */}
                  <button
                    type="button"
                    onClick={() => setShowMap(v => !v)}
                    className={`w-full flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl border text-sm font-semibold transition-all duration-150 ${
                      showMap
                        ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                        : 'bg-white border-gray-200 text-gray-700 hover:border-indigo-300 hover:text-indigo-700 hover:bg-indigo-50'
                    }`}
                  >
                    <MapIcon className="w-4 h-4" />
                    {showMap ? 'Hide Map' : 'Pin on Map'}
                  </button>

                  {/* Interactive map */}
                  {showMap && (
                    <div className="rounded-xl overflow-hidden border border-indigo-200 shadow-sm">
                      <div className="bg-indigo-50 px-3 py-2 text-xs text-indigo-700 font-medium flex items-center gap-1.5 border-b border-indigo-200">
                        <MapPin className="w-3.5 h-3.5" />
                        Click anywhere on the map to drop a pin
                        {reverseGeocoding && <span className="ml-auto text-indigo-500 animate-pulse">Fetching address…</span>}
                        {pinPos && !reverseGeocoding && (
                          <span className="ml-auto text-green-700 font-mono">
                            {pinPos.lat.toFixed(4)}, {pinPos.lng.toFixed(4)}
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => setMapSatellite((s) => !s)}
                          title={mapSatellite ? "Switch to Street view" : "Switch to Satellite view"}
                          className={`ml-auto flex items-center gap-1 px-2 py-0.5 rounded border text-xs transition-colors ${
                            mapSatellite
                              ? "bg-slate-800 border-slate-700 text-white"
                              : "bg-white border-indigo-200 text-indigo-600 hover:bg-indigo-100"
                          }`}
                        >
                          <Layers className="w-3 h-3" />
                          {mapSatellite ? "Satellite" : "Street"}
                        </button>
                      </div>
                      <Map
                        ref={mapRef}
                        mapStyle={mapSatellite ? _SATELLITE_STYLE : _STREET_STYLE}
                        initialViewState={{
                          longitude: 78.9629,
                          latitude: 20.5937,
                          zoom: 4,
                        }}
                        maxBounds={[[67.0, 6.0], [98.0, 38.0]]}
                        style={{ height: '280px', width: '100%' }}
                        cursor="crosshair"
                        onClick={(e) => handleMapPin(e.lngLat.lat, e.lngLat.lng)}
                      >
                        <NavigationControl position="top-right" />
                        {pinPos && (
                          <MapMarker
                            latitude={pinPos.lat}
                            longitude={pinPos.lng}
                            color="#4f46e5"
                          />
                        )}
                      </Map>
                    </div>
                  )}

                  <div className="relative flex items-center gap-3">
                    <div className="flex-1 border-t border-gray-200" />
                    <span className="text-xs text-gray-400 shrink-0">or enter manually</span>
                    <div className="flex-1 border-t border-gray-200" />
                  </div>

                  {/* Address input */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                      Address / Locality <span className="text-red-500">*</span>
                    </label>
                    <div className="relative" ref={suggestionRef}>
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                      {fetchingSuggestions && (
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      )}
                      <input
                        type="text"
                        value={manualAddress}
                        onChange={(e) => {
                          setManualAddress(e.target.value);
                          setLocationSource('manual');
                          fetchAddressSuggestions(e.target.value);
                        }}
                        onFocus={() => addressSuggestions.length > 0 && setShowSuggestions(true)}
                        placeholder="e.g. MG Road, near Central Mall, Pune"
                        className="w-full pl-9 pr-8 py-2.5 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                        autoComplete="off"
                      />
                      {showSuggestions && addressSuggestions.length > 0 && (
                        <ul className="absolute z-50 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden max-h-56 overflow-y-auto">
                          {addressSuggestions.map((item) => (
                            <li
                              key={item.place_id}
                              onMouseDown={(e) => { e.preventDefault(); handleSelectSuggestion(item); }}
                              className="flex items-start gap-2 px-3 py-2.5 hover:bg-primary/5 cursor-pointer border-b border-gray-50 last:border-0 transition-colors"
                            >
                              <MapPin className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                              <span className="text-xs text-gray-700 leading-snug line-clamp-2">{item.display_name}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>

                  {/* Coordinates row */}
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Latitude', value: manualLat, setter: setManualLat, placeholder: '23.1859' },
                      { label: 'Longitude', value: manualLon, setter: setManualLon, placeholder: '72.6359' },
                    ].map(({ label, value, setter, placeholder }) => (
                      <div key={label}>
                        <label className="block text-xs font-semibold text-slate-600 mb-1.5">{label}</label>
                        <input
                          type="number"
                          step="any"
                          value={value}
                          onChange={(e) => { setter(e.target.value); setLocationSource('manual'); }}
                          placeholder={placeholder}
                          className="w-full px-3 py-2.5 text-sm font-mono border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                        />
                      </div>
                    ))}
                  </div>

                  {(manualLat || manualLon) ? (
                    <div className="flex items-center gap-2 text-xs text-indigo-700 bg-indigo-50 px-3 py-2 rounded-lg border border-indigo-100">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                      Coordinates set — {manualLat || '—'}, {manualLon || '—'}
                    </div>
                  ) : (
                    <p className="text-[11px] text-gray-400 flex items-center gap-1.5">
                      <span className="inline-block w-3.5 h-3.5 rounded-full bg-gray-200 text-center leading-3.5 shrink-0 font-bold text-gray-500 text-[9px]">?</span>
                      Tip: right-click any spot in Google Maps → "What's here?" to get coordinates.
                    </p>
                  )}
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
              <div className="flex items-center gap-2">
                {/* Regenerate with language picker */}
                <div className="relative flex items-center" ref={regenLangRef}>
                  <button
                    onClick={handleRegenerate}
                    disabled={isGenerating || regenerating}
                    title="Regenerate grievance description using AI"
                    className="text-xs font-medium text-gray-500 hover:text-primary flex items-center gap-1 transition disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${(isGenerating || regenerating) ? 'animate-spin' : ''}`} />
                    {regenerating ? 'Starting…' : isGenerating ? 'Generating…' : 'Regenerate'}
                  </button>
                  <button
                    onClick={() => !isGenerating && !regenerating && setShowRegenLang(v => !v)}
                    disabled={isGenerating || regenerating}
                    title="Choose language for regeneration"
                    className="ml-0.5 px-1 py-0.5 text-gray-400 hover:text-primary rounded transition disabled:opacity-40 disabled:cursor-not-allowed text-[10px] leading-none"
                  >
                    {'\u25be'} {regenLang !== language && <span className="ml-0.5 text-primary font-semibold">{regenLang.toUpperCase()}</span>}
                  </button>
                  {showRegenLang && (
                    <div className="absolute right-0 top-full mt-1.5 z-50 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden min-w-32.5">
                      <div className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wide border-b border-gray-100">Regenerate in…</div>
                      {[
                        { code: 'en', label: 'English' },
                        { code: 'hi', label: 'हिन्दी' },
                        { code: 'kn', label: 'ಕನ್ನಡ' },
                        { code: 'ta', label: 'தமிழ்' },
                        { code: 'te', label: 'తెలుగు' },
                        { code: 'bn', label: 'বাংলা' },
                        { code: 'mr', label: 'मराठी' },
                        { code: 'gu', label: 'ગુજરાતી' },
                      ].map(({ code, label }) => (
                        <button
                          key={code}
                          onMouseDown={(e) => {
                            e.preventDefault();
                            setRegenLang(code);
                            setShowRegenLang(false);
                            // Immediately trigger regeneration with chosen language
                            setRegenerateError(null);
                            setRegenerating(true);
                            axios.post(
                              `${API_BASE_URL}/analyze/regenerate`,
                              {
                                classification: classificationState,
                                location: result?.location || {},
                                image_url,
                                language: code,
                                user_grievance_text: userContextText,
                              }
                            ).then(res => {
                              if (res.data?.classification) {
                                setClassificationState(res.data.classification);
                              }
                              if (res.data?.analysis_token) {
                                setAnalysisToken(res.data.analysis_token);
                              }
                              setComplaintText('');
                              setShowComplaintEditor(false);
                              setGenerationJobId(res.data.job_id);
                              setGenerationStatus('queued');
                            }).catch(() => {
                              setRegenerateError('Failed to start regeneration. Please try again.');
                            }).finally(() => setRegenerating(false));
                          }}
                          className={`w-full text-left px-3 py-2 text-xs hover:bg-primary/5 transition flex justify-between items-center ${
                            regenLang === code ? 'text-primary font-semibold bg-primary/5' : 'text-gray-700'
                          }`}
                        >
                          <span>{label}</span>
                          {regenLang === code && <span className="text-[9px] text-primary">✓</span>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-gray-300">|</span>
                <button 
                  onClick={handleCopy}
                  className="text-xs font-medium text-primary hover:text-primary-light flex items-center gap-1 transition"
                >
                  <Copy className="w-3.5 h-3.5" />
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
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
                  <div className="text-sm font-medium text-gray-800">{classificationState.department}</div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    <Edit3 className="w-3 h-3" />
                    Optional: Correct Image Context For Routing
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowContextEditor((v) => !v)}
                    className="text-xs font-medium text-primary hover:text-primary-light flex items-center gap-1"
                  >
                    {showContextEditor ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    {showContextEditor ? 'Collapse' : 'Expand'}
                  </button>
                </div>

                {showContextEditor && (
                  <>
                    <textarea
                      className="w-full min-h-24 p-3 text-gray-700 bg-white border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-y text-sm leading-relaxed"
                      value={userContextText}
                      onChange={(e) => {
                        setUserContextText(e.target.value);
                        if (regenerateError) setRegenerateError(null);
                      }}
                      onKeyDown={(e) => {
                        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                          e.preventDefault();
                          void handleApplyContextAndRegenerate();
                        }
                      }}
                      placeholder="Example: Fractured footpath slab along road edge near crossing; pedestrian trip hazard"
                      maxLength={1200}
                    />
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={handleApplyContextAndRegenerate}
                        disabled={!userContextText.trim() || isGenerating || regenerating}
                        className="px-3 py-1.5 text-xs font-semibold text-white rounded bg-primary hover:bg-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isGenerating || regenerating ? 'Applying…' : 'Apply Context & Regenerate'}
                      </button>
                      <span className="text-[11px] text-gray-500">
                        Tip: press Ctrl+Enter after editing context.
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-gray-500">
                      Use the button above to update Issue Details from your corrected context.
                    </p>
                  </>
                )}
              </div>

              {/* Editable complaint description */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    <Edit3 className="w-3 h-3" />
                    Issue Details (AI-generated — edit if needed)
                    {['queued', 'processing'].includes(generationStatus) && (
                      <span className="ml-2 text-[10px] text-primary animate-pulse font-normal normal-case tracking-normal">Generating…</span>
                    )}
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowComplaintEditor((v) => !v)}
                    disabled={['queued', 'processing'].includes(generationStatus)}
                    className="text-xs font-medium text-primary hover:text-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {showComplaintEditor ? 'Hide Editor' : 'Edit Text'}
                  </button>
                </div>
                <div className="mb-2">
                  <div className="w-full max-h-48 overflow-y-auto p-3 text-gray-700 bg-gray-50 border border-gray-200 rounded text-sm leading-relaxed">
                    <FormattedComplaintText text={complaintText} />
                  </div>
                </div>
                {showComplaintEditor && (
                  <textarea 
                    className={`w-full min-h-44 p-4 text-gray-700 bg-white border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-y text-sm leading-relaxed ${
                      ['queued', 'processing'].includes(generationStatus) ? 'opacity-60 cursor-wait' : ''
                    }`}
                    value={complaintText}
                    onChange={(e) => setComplaintText(e.target.value)}
                    placeholder={['queued', 'processing'].includes(generationStatus) ? 'Generating complaint draft…' : 'Describe the issue in detail...'}
                    disabled={['queued', 'processing'].includes(generationStatus)}
                  />
                )}
              </div>
            </div>

            {/* Submit footer */}
            <div className="px-5 py-4 bg-gray-50 border-t border-gray-100">
              {regenerateError && (
                <div className="mb-3 p-2.5 bg-amber-50 text-amber-700 text-sm rounded border border-amber-200 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  {regenerateError}
                </div>
              )}
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
                  {isGenerating && (
                    <p className="text-primary font-medium animate-pulse">⏳ Generating complaint draft…</p>
                  )}
                  {!isGenerating && !complaintText.trim() && (
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
                    : isGenerating ? "Please wait for draft generation to complete"
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
