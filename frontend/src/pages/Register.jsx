import React, { useState } from 'react';

import axios from 'axios';

import { useNavigate, Link } from 'react-router-dom';

import { User, Mail, Lock, CheckCircle } from 'lucide-react';

import { useAuth } from '../context/AuthContext';



const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';



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

      

      login(response.data);



      setSuccess('Registration successful! Redirecting...');

      setTimeout(() => {

          navigate('/dashboard');

      }, 1500);



    } catch (err) {

      setError(err.response?.data?.detail || 'Registration failed');

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

          <p className="text-blue-200 text-xs mt-1">Citizen Registration</p>

        </div>

        <div className="tricolor-bar"></div>



        {/* Form card */}

        <div className="bg-white border border-gray-200 rounded-b-lg shadow-lg px-6 sm:px-8 py-8">

          {error && (

            <div className="mb-4 p-3 bg-red-50 text-danger rounded border border-red-200 text-sm">

              {error}

            </div>

          )}

          

          {success && (

            <div className="mb-4 p-3 bg-green-50 text-success rounded border border-green-200 text-sm flex items-center">

                <CheckCircle className="w-4 h-4 mr-2"/> {success}

            </div>

          )}



          <form onSubmit={handleSubmit} className="space-y-4">

            <div>

              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>

              <div className="relative">

                <User className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />

                <input

                  type="text"

                  name="username"

                  required

                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"

                  placeholder="johndoe"

                  value={formData.username}

                  onChange={handleChange}

                />

              </div>

            </div>



            <div>

               <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>

               <div className="relative">

                 <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />

                 <input

                   type="email"

                   name="email"

                   required

                   className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"

                   placeholder="john@example.com"

                   value={formData.email}

                   onChange={handleChange}

                 />

               </div>

            </div>



            <div>

              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>

              <div className="relative">

                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />

                <input

                  type="password"

                  name="password"

                  required

                  minLength={6}

                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"

                  placeholder="********"

                  value={formData.password}

                  onChange={handleChange}

                />

              </div>

            </div>

            

            <div>

              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>

              <div className="relative">

                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />

                <input

                  type="password"

                  name="confirmPassword"

                  required

                  className="pl-10 w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-primary text-sm"

                  placeholder="********"

                  value={formData.confirmPassword}

                  onChange={handleChange}

                />

              </div>

            </div>



            <button

              type="submit"

              disabled={loading}

              className="w-full bg-primary text-white py-2.5 px-4 rounded font-semibold hover:bg-primary-light transition disabled:opacity-50"

            >

              {loading ? 'Registering...' : 'Register'}

            </button>

          </form>



          <div className="mt-6 pt-5 border-t border-gray-100 text-center text-sm text-gray-600">

            Already have an account?{' '}

            <Link to="/login" className="font-semibold text-primary hover:text-primary-light hover:underline">

              Sign in

            </Link>

          </div>

          <div className="mt-2 text-center text-sm text-gray-500">

            Are you a government worker?{' '}

            <Link to="/worker/register" className="font-medium text-primary hover:text-primary-light hover:underline">

              Register here

            </Link>

          </div>

        </div>

      </div>

    </div>

  );

}

