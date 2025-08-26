import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Configure axios to include credentials
  axios.defaults.withCredentials = true;

  const checkAuthStatus = async () => {
    try {
      // First check for URL fragment authentication (from OAuth redirect)
      const fragment = window.location.hash;
      if (fragment.includes('session_id=')) {
        const sessionId = fragment.split('session_id=')[1].split('&')[0];
        await handleOAuthCallback(sessionId);
        // Clean up URL
        window.location.hash = '';
        return;
      }

      // Check existing authentication
      const response = await axios.get(`${API}/auth/me`);
      if (response.data.success) {
        setUser(response.data.data);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.log('Not authenticated');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthCallback = async (sessionId) => {
    try {
      const response = await axios.post(`${API}/auth/oauth/callback`, {
        session_id: sessionId
      });
      
      if (response.data.success) {
        setUser(response.data.data);
        setIsAuthenticated(true);
        return response.data.data;
      }
    } catch (error) {
      console.error('OAuth callback failed:', error);
      throw error;
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });

      if (response.data.access_token) {
        // Check user info after login
        await checkAuthStatus();
        return { success: true };
      }
    } catch (error) {
      console.error('Login failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      
      if (response.data.success) {
        // Auto-login after registration
        await login(userData.email, userData.password);
        return { success: true };
      }
    } catch (error) {
      console.error('Registration failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      };
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const loginWithOAuth = () => {
    const currentUrl = window.location.origin;
    const redirectUrl = `${currentUrl}/profile`;
    const oauthUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    window.location.href = oauthUrl;
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const isUser = () => {
    return user?.role === 'user';
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    loginWithOAuth,
    isAdmin,
    isUser,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};