import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Lock, CheckCircle, Info, MapPin, Briefcase } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const DEPARTMENTS = [
  'Health Department',
  'Civil Department',
  'Horticulture',
  'Electrical Department',
  'IT Department',
  'Commercial',
  'Enforcement',
  'VBD Department',
  'EBR Department',
  'Fire Department',
];

export default function WorkerRegister() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    department: '',
    locality: '',
    lat: '',
    lon: '',
    radius_km: '10',
  });

  const [useGPS, setUseGPS] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleGetGPS = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setFormData(prev => ({
          ...prev,
          lat: pos.coords.latitude.toFixed(6),
          lon: pos.coords.longitude.toFixed(6),
        }));
        setUseGPS(true);
        setGpsLoading(false);
      },
      () => {
        setError('Could not get your location. Please enter coordinates manually.');
        setGpsLoading(false);
      }
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!/[A-Z]/.test(formData.password) || !/[0-9]/.test(formData.password)) {
      setError('Password must include at least one uppercase letter and one digit.');
      return;
    }
    if (!formData.department) {
      setError('Please select your department.');
      return;
    }

    setLoading(true);

    try {
      // Build service_area only if coordinates are provided
      let service_area = null;
      if (formData.lat && formData.lon) {
        const lat = parseFloat(formData.lat);
        const lon = parseFloat(formData.lon);
        if (isNaN(lat) || isNaN(lon)) {
          setError('Invalid latitude or longitude.');
          setLoading(false);
          return;
        }
        service_area = {
          lat,
          lon,
          radius_km: parseFloat(formData.radius_km) || 10,
          locality: formData.locality || undefined,
        };
      }

      const payload = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        role: 'worker',
        department: formData.department,
        ...(service_area ? { service_area } : {}),
      };

      await axios.post(`${API_BASE_URL}/users/register`, payload, {
        withCredentials: true,
      });

      setSuccess('Registration submitted! Your account is pending admin approval. You will be redirected to login shortly…');
      setTimeout(() => navigate('/login'), 3500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Government header */}
        <div className="bg-primary rounded-t-lg px-6 py-5 text-center">
          <div className="text-saffron text-2xl mb-1">&#9784;</div>
          <h2 className="text-white text-xl font-bold">जन-सुनवाई</h2>
          <p className="text-blue-200 text-xs mt-1">Field Worker Registration</p>
        </div>
        <div className="tricolor-bar" />

        <div className="bg-white border border-gray-200 rounded-b-lg shadow-lg px-6 sm:px-8 py-8">
          {/* Info banner */}
          <div className="mb-6 p-3 bg-blue-50 text-blue-800 rounded border border-blue-200 text-xs flex items-start">
            <Info className="w-4 h-4 mr-2 shrink-0 mt-0.5" />
            <span>
              Your account will require <strong>admin approval</strong>.
              The department and service area you set here will be used to auto-assign nearby grievances to you.
            </span>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-danger rounded border border-red-200 text-sm">{error}</div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-green-50 text-success rounded border border-green-200 text-sm flex items-center">
              <CheckCircle className="w-4 h-4 mr-2" /> {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <input
                  type="text" name="username" required
                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                  placeholder="rajesh_kumar"
                  value={formData.username} onChange={handleChange}
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <input
                  type="email" name="email" required
                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                  placeholder="worker@example.com"
                  value={formData.email} onChange={handleChange}
                />
              </div>
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Department <span className="text-red-500">*</span></label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <select
                  name="department" required
                  value={formData.department} onChange={handleChange}
                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm bg-white"
                >
                  <option value="">— Select your department —</option>
                  {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>

            {/* Service Area */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
              <p className="text-sm font-medium text-gray-700 flex items-center gap-1.5">
                <MapPin className="h-4 w-4 text-gray-400" />
                Service Area <span className="text-xs text-gray-500 font-normal">(complaints within this radius will be assigned to you)</span>
              </p>

              <div>
                <label className="block text-xs text-gray-600 mb-1">Area / Locality Name</label>
                <input
                  type="text" name="locality"
                  className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-primary"
                  placeholder="e.g. Ghatlodiya, Ahmedabad"
                  value={formData.locality} onChange={handleChange}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Latitude</label>
                  <input
                    type="number" step="any" name="lat"
                    className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-primary"
                    placeholder="23.0225"
                    value={formData.lat} onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Longitude</label>
                  <input
                    type="number" step="any" name="lon"
                    className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-primary"
                    placeholder="72.5714"
                    value={formData.lon} onChange={handleChange}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="block text-xs text-gray-600 mb-1">Radius (km)</label>
                  <input
                    type="number" name="radius_km" min="1" max="100"
                    className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-primary"
                    value={formData.radius_km} onChange={handleChange}
                  />
                </div>
                <button
                  type="button"
                  onClick={handleGetGPS}
                  disabled={gpsLoading}
                  className="mt-5 flex items-center gap-1.5 px-3 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded text-xs font-medium hover:bg-indigo-100 disabled:opacity-50"
                >
                  <MapPin className="h-3.5 w-3.5" />
                  {gpsLoading ? 'Getting…' : useGPS ? '✓ GPS Set' : 'Use My GPS'}
                </button>
              </div>
              <p className="text-xs text-gray-400">Leave latitude/longitude blank if your admin will set your area later.</p>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <input
                  type="password" name="password" required minLength={10}
                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                  placeholder="At least 10 chars, 1 uppercase, 1 digit"
                  value={formData.password} onChange={handleChange}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <input
                  type="password" name="confirmPassword" required
                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                  placeholder="••••••••"
                  value={formData.confirmPassword} onChange={handleChange}
                />
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full bg-primary text-white py-2.5 px-4 rounded font-semibold hover:bg-primary-light transition disabled:opacity-50"
            >
              {loading ? 'Submitting…' : 'Submit Registration'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-gray-100 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-primary hover:text-primary-light hover:underline">Sign in</Link>
          </div>
          <div className="mt-2 text-center text-sm text-gray-500">
            Not a worker?{' '}
            <Link to="/register" className="font-medium text-primary hover:text-primary-light hover:underline">Register here</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
