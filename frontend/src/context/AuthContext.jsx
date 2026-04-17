import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

function getTokenExpiry(token) {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded.exp || 0;
  } catch {
    return 0;
  }
}

function isTokenExpired(token) {
  const exp = getTokenExpiry(token);
  if (!exp) return true;
  return Date.now() / 1000 > exp;
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('jan_sunwai_user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        if (parsed && parsed.access_token) {
          if (isTokenExpired(parsed.access_token)) {
            console.warn('Stored session token expired — clearing.');
            localStorage.removeItem('jan_sunwai_user');
          } else {
            setUser(parsed);
          }
        } else {
          console.warn('Invalid session format detected. Please log in again.');
          localStorage.removeItem('jan_sunwai_user');
        }
      } catch (e) {
        console.error('Failed to parse stored user', e);
        localStorage.removeItem('jan_sunwai_user');
      }
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('jan_sunwai_user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('jan_sunwai_user');
  };

  // Call this whenever an API returns 401 — clears session and redirects to login.
  // Works without useNavigate by relying on window.location for simplicity.
  const handleAuthError = useCallback(() => {
    setUser(null);
    localStorage.removeItem('jan_sunwai_user');
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, isTokenExpired, handleAuthError }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
