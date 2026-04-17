import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

/**
 * Decode the exp claim from a JWT payload (no library needed).
 * Returns 0 if the token is malformed.
 */
function getTokenExpiry(token) {
  try {
    const payload = token.split('.')[1];
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    const decoded = JSON.parse(atob(padded));
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

  /**
   * P4-E: login() still stores the token in localStorage for backwards compat
   * with all existing components that read user.access_token for the
   * Authorization: Bearer header. The httpOnly cookie is now ALSO issued by
   * the server on every login response — so any request made with
   * credentials: 'include' (see api.js) will automatically carry the cookie.
   *
   * Migration path: once all axios calls are migrated to credentials:include
   * and read from cookie, remove the localStorage write and Authorization header.
   * Target: 2026-07-17 (same as route deprecation window).
   */
  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('jan_sunwai_user', JSON.stringify(userData));
  };

  const logout = useCallback(async () => {
    // P4-E: Call backend logout to clear httpOnly cookie server-side
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      await fetch(`${API_BASE}/users/logout`, {
        method: 'POST',
        credentials: 'include',  // P4-E: send cookie so server can clear it
      });
    } catch {
      // Non-fatal — clear client state regardless
    }
    setUser(null);
    localStorage.removeItem('jan_sunwai_user');
  }, []);

  /**
   * Call this whenever an API call returns 401.
   * Clears local session and redirects to login.
   */
  const handleAuthError = useCallback(async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      await fetch(`${API_BASE}/users/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Non-fatal
    }
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
