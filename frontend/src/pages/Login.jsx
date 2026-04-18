import React, { useState } from 'react';

import axios from 'axios';

import { useNavigate, Link } from 'react-router-dom';

import { User, Lock, AlertCircle } from 'lucide-react';

import { useAuth } from '../context/AuthContext';



const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';



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

      const params = new URLSearchParams();

      params.append('username', formData.username);

      params.append('password', formData.password);



      const response = await axios.post(`${API_BASE_URL}/users/login`, params, {

        headers: {

            'Content-Type': 'application/x-www-form-urlencoded'

        },
        withCredentials: true,

      });

      

      login(response.data);

      navigate('/dashboard');



    } catch (err) {

      console.error(err);

      setError(err.response?.data?.detail || 'Invalid username or password');

    } finally {

      setLoading(false);

    }

  };



  return (

    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">

      <div className="w-full max-w-md">

        {/* Government header bar */}

        <div className="bg-primary rounded-t-lg px-6 py-5 text-center">

          <div className="text-saffron text-2xl mb-1">&#9784;</div>

          <h2 className="text-white text-xl font-bold">जन-सुनवाई</h2>

          <p className="text-blue-200 text-xs mt-1">Public Grievance Redressal System — Login</p>

        </div>

        <div className="tricolor-bar"></div>

        

        {/* Form card */}

        <div className="bg-white border border-gray-200 rounded-b-lg shadow-lg px-6 sm:px-8 py-8">

          {error && (

            <div className="mb-5 p-3 bg-red-50 text-danger rounded border border-red-200 text-sm flex items-start">

              <AlertCircle className="w-4 h-4 mr-2 shrink-0 mt-0.5" />

              <span>{error}</span>

            </div>

          )}



          <form onSubmit={handleSubmit} className="space-y-5">

            <div>

              <label className="block text-sm font-medium text-gray-700 mb-1.5">Username</label>

              <div className="relative">

                <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />

                <input

                  type="text"

                  name="username"

                  autoComplete="username"

                  required

                  className="pl-10 w-full p-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary transition text-sm"

                  placeholder="Enter your username"

                  value={formData.username}

                  onChange={handleChange}

                />

              </div>

            </div>



            <div>

              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>

              <div className="relative">

                <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />

                <input

                  type="password"

                  name="password"

                  autoComplete="current-password"

                  required

                  className="pl-10 w-full p-2.5 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary transition text-sm"

                  placeholder="********"

                  value={formData.password}

                  onChange={handleChange}

                />

              </div>

              <div className="mt-2 text-right">
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-primary hover:text-primary-light hover:underline"
                >
                  Forgot password?
                </Link>
              </div>

            </div>



            <button

              type="submit"

              disabled={loading}

              className="w-full bg-primary text-white py-2.5 px-4 rounded font-semibold hover:bg-primary-light transition disabled:opacity-70 disabled:cursor-not-allowed"

            >

              {loading ? 'Signing in...' : 'Sign In'}

            </button>

          </form>



          <div className="mt-6 pt-5 border-t border-gray-100 text-center text-sm text-gray-600">

            Don't have an account?{' '}

            <Link to="/register" className="font-semibold text-primary hover:text-primary-light hover:underline">

              Register here

            </Link>

          </div>

          <div className="mt-2 text-center text-sm text-gray-500">

            Are you a government worker?{' '}

            <Link to="/worker/register" className="font-medium text-primary hover:text-primary-light hover:underline">

              Apply here

            </Link>

          </div>

        </div>

      </div>

    </div>

  );

}

