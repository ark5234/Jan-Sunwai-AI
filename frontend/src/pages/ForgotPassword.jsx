import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Mail, AlertCircle, CheckCircle2 } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/users/forgot-password`, { email });
      setSuccess(response.data?.message || 'If an account exists for this email, a reset token has been issued.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to process request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-primary rounded-t-lg px-6 py-5 text-center">
          <div className="text-saffron text-2xl mb-1">&#9784;</div>
          <h2 className="text-white text-xl font-bold">Reset Password</h2>
          <p className="text-blue-200 text-xs mt-1">Enter your account email to request a reset token</p>
        </div>
        <div className="tricolor-bar"></div>

        <div className="bg-white border border-gray-200 rounded-b-lg shadow-lg px-6 sm:px-8 py-8">
          {error && (
            <div className="mb-5 p-3 bg-red-50 text-danger rounded border border-red-200 text-sm flex items-start">
              <AlertCircle className="w-4 h-4 mr-2 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-5 p-3 bg-green-50 text-green-700 rounded border border-green-200 text-sm flex items-start">
              <CheckCircle2 className="w-4 h-4 mr-2 shrink-0 mt-0.5" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="email"
                  required
                  className="pl-10 w-full p-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary transition text-sm"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-white py-2.5 px-4 rounded font-semibold hover:bg-primary-light transition disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? 'Submitting...' : 'Send Reset Request'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-gray-100 text-center text-sm text-gray-600">
            Already have a reset token?{' '}
            <Link to="/reset-password" className="font-semibold text-primary hover:text-primary-light hover:underline">
              Reset here
            </Link>
          </div>

          <div className="mt-2 text-center text-sm text-gray-500">
            Back to{' '}
            <Link to="/login" className="font-medium text-primary hover:text-primary-light hover:underline">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
