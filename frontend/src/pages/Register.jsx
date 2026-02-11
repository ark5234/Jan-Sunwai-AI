import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Lock, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API_BASE_URL = 'http://localhost:8000';

export default function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      const payload = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          role: "citizen" 
      };
      
      const response = await axios.post(`${API_BASE_URL}/users/register`, payload);
      
      // Auto-login after registration
      login(response.data);

      setSuccess('Registration successful! Redirecting...');
      setTimeout(() => {
          navigate('/analyze'); // Go straight to upload
      }, 1500);

    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-md border border-slate-200">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Create Account</h2>
        <p className="text-slate-500 text-sm">Join Jan-Sunwai AI to report issues.</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm border border-red-200">
          {error}
        </div>
      )}
      
      {success && (
        <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md text-sm border border-green-200 flex items-center">
            <CheckCircle className="w-4 h-4 mr-2"/> {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
          <div className="relative">
            <User className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />
            <input
              type="text"
              name="username"
              required
              className="pl-10 w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              placeholder="johndoe"
              value={formData.username}
              onChange={handleChange}
            />
          </div>
        </div>

        <div>
           <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
           <div className="relative">
             <Mail className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />
             <input
               type="email"
               name="email"
               required
               className="pl-10 w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
               placeholder="john@example.com"
               value={formData.email}
               onChange={handleChange}
             />
           </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />
            <input
              type="password"
              name="password"
              required
              minLength={6}
              className="pl-10 w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Confirm Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />
            <input
              type="password"
              name="confirmPassword"
              required
              className="pl-10 w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={handleChange}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-white py-2 px-4 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? 'Registering...' : 'Sign Up'}
        </button>
      </form>
    </div>
  );
}
