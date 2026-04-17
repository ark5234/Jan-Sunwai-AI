import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

/**
 * Decode JWT payload without verifying signature (signature is verified by server).
 * Returns the exp field in seconds, or 0 if not present.
 */
function getTokenExpiry(token: string): number {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded.exp || 0;
  } catch {
    return 0;
  }
}

function isTokenExpired(token: string): boolean {
  const exp = getTokenExpiry(token);
  if (!exp) return true; // no expiry = treat as expired
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
          // Check token expiry on page load — clear stale sessions immediately
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

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, isTokenExpired }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
