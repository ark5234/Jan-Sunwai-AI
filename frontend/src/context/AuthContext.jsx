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
    let cancelled = false;

    const bootstrapSession = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
        const res = await fetch(`${API_BASE}/users/me`, {
          method: 'GET',
          credentials: 'include',
        });
        if (!cancelled && res.ok) {
          const me = await res.json();
          // Compatibility shim for components still checking user.access_token.
          setUser({ ...me, access_token: '__cookie__' });
        }
      } catch {
        // no-op: unauthenticated startup is expected for guests
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    bootstrapSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = (userData) => {
    // Compatibility shim for components still checking user.access_token.
    setUser({ ...userData, access_token: '__cookie__' });
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
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, isTokenExpired, handleAuthError }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
