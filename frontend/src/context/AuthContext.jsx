import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check localStorage on load
    const storedUser = localStorage.getItem('jan_sunwai_user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        // Validate that the stored user has an access_token (JWT implementation)
        if (parsed && parsed.access_token) {
          setUser(parsed);
        } else {
          // Old session format, clear it
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
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
