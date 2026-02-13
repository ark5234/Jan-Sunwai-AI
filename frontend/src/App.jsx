import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './layouts/Navbar';
import Home from './pages/Home';
import Analyze from './pages/Analyze';
import Result from './pages/Result';
import Register from './pages/Register';
import Login from './pages/Login';
import CitizenDashboard from './pages/CitizenDashboard';
import DeptHeadDashboard from './pages/DeptHeadDashboard';
import AdminDashboard from './pages/AdminDashboard';
import TriageReview from './pages/TriageReview';

// Protected Route Component
function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
}

// Dashboard Router - redirects to appropriate dashboard based on role
function DashboardRouter() {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  switch (user.role) {
    case 'admin':
      return <AdminDashboard />;
    case 'dept_head':
      return <DeptHeadDashboard />;
    case 'citizen':
    default:
      return <CitizenDashboard />;
  }
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-slate-50 font-sans">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              
              {/* Protected Routes */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <DashboardRouter />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/analyze" 
                element={
                  <ProtectedRoute>
                    <Analyze />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/result" 
                element={
                  <ProtectedRoute>
                    <Result />
                  </ProtectedRoute>
                } 
              />
              
              {/* Role-specific dashboard routes */}
              <Route 
                path="/admin" 
                element={
                  <ProtectedRoute allowedRoles={['admin']}>
                    <AdminDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/triage-review" 
                element={
                  <ProtectedRoute allowedRoles={['admin']}>
                    <TriageReview />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/dept-head" 
                element={
                  <ProtectedRoute allowedRoles={['dept_head']}>
                    <DeptHeadDashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/citizen" 
                element={
                  <ProtectedRoute allowedRoles={['citizen']}>
                    <CitizenDashboard />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
