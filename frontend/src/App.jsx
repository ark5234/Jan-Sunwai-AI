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
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import ComplaintsMap from './pages/ComplaintsMap';
import PublicStatus from './pages/PublicStatus';

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

// Guest-only Route — logged-in users are sent straight to their dashboard
function GuestRoute({ children }) {
  const { user } = useAuth();
  if (user) {
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
          <div className="min-h-screen bg-gray-50 font-sans">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<GuestRoute><Home /></GuestRoute>} />
              <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
              <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
              
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
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <Profile />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/notifications" 
                element={
                  <ProtectedRoute>
                    <Notifications />
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
              <Route path="/dept-head" element={<ProtectedRoute allowedRoles={['dept_head']}><DeptHeadDashboard /></ProtectedRoute>} />
              <Route path="/citizen" element={<ProtectedRoute allowedRoles={['citizen']}><CitizenDashboard /></ProtectedRoute>} />

              {/* Analytics (admin only) */}
              <Route path="/analytics" element={<ProtectedRoute allowedRoles={['admin']}><AnalyticsDashboard /></ProtectedRoute>} />

              {/* Map (admin + dept_head) */}
              <Route path="/map" element={<ProtectedRoute allowedRoles={['admin', 'dept_head']}><ComplaintsMap /></ProtectedRoute>} />

              {/* Public transparency board — no auth needed */}
              <Route path="/public" element={<PublicStatus />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
