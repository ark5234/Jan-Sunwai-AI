import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { User, Lock, LogIn, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API_BASE_URL = 'http://localhost:8000';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Backend expects: { username: "...", password: "..." }
      const response = await axios.post(`${API_BASE_URL}/users/login`, formData);
      
      // Response data: { message: "...", username: "...", role: "..." }
      // We store this in our AuthContext
      login(response.data);
      
      // Redirect to home/analyze
      navigate('/analyze');

    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-8 bg-white rounded-xl shadow-lg border border-slate-100">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-4">
            <LogIn className="w-6 h-6 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-slate-800">Welcome Back</h2>
        <p className="text-slate-500 text-sm mt-1">Please sign in to continue.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200 flex items-start">
          <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Username</label>
          <div className="relative">
            <User className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
            <input
              type="text"
              name="username"
              required
              className="pl-10 w-full p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              placeholder="Enter your username"
              value={formData.username}
              onChange={handleChange}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="block text-sm font-medium text-slate-700">Password</label>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
            <input
              type="password"
              name="password"
              required
              className="pl-10 w-full p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-white py-2.5 px-4 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-70 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <div className="mt-8 text-center text-sm text-slate-600">
        Don't have an account?{' '}
        <Link to="/register" className="font-semibold text-primary hover:text-blue-700 hover:underline">
          Create account
        </Link>
      </div>
    </div>
  );
}
