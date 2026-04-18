import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './layouts/Navbar';
import Home from './pages/Home';
import Register from './pages/Register';
import Login from './pages/Login';

const Analyze = lazy(() => import('./pages/Analyze'));
const Result = lazy(() => import('./pages/Result'));
const CitizenDashboard = lazy(() => import('./pages/CitizenDashboard'));
const DeptHeadDashboard = lazy(() => import('./pages/DeptHeadDashboard'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const TriageReview = lazy(() => import('./pages/TriageReview'));
const Profile = lazy(() => import('./pages/Profile'));
const Notifications = lazy(() => import('./pages/Notifications'));
const AnalyticsDashboard = lazy(() => import('./pages/AnalyticsDashboard'));
const ComplaintsMap = lazy(() => import('./pages/ComplaintsMap'));
const PublicStatus = lazy(() => import('./pages/PublicStatus'));
const WorkerDashboard = lazy(() => import('./pages/WorkerDashboard'));
const WorkerRegister = lazy(() => import('./pages/WorkerRegister'));
const GrievanceHeatmap = lazy(() => import('./pages/GrievanceHeatmap'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));

// Protected Route Component
function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return null;
  }
  
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
  const { user, loading } = useAuth();
  if (loading) {
    return null;
  }
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

// Dashboard Router - redirects to appropriate dashboard based on role
function DashboardRouter() {
  const { user, loading } = useAuth();

  if (loading) {
    return null;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  switch (user.role) {
    case 'admin':
      return <AdminDashboard />;
    case 'dept_head':
      return <DeptHeadDashboard />;
    case 'worker':
      return <WorkerDashboard />;
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
            <Suspense
              fallback={
                <div className="min-h-[60vh] flex items-center justify-center">
                  <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-primary" />
                </div>
              }
            >
            <Routes>
              <Route path="/" element={<GuestRoute><Home /></GuestRoute>} />
              <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
              <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
              <Route path="/forgot-password" element={<GuestRoute><ForgotPassword /></GuestRoute>} />
              <Route path="/reset-password" element={<GuestRoute><ResetPassword /></GuestRoute>} />
              
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

              {/* Worker self-registration — unauthenticated */}
              <Route path="/worker/register" element={<GuestRoute><WorkerRegister /></GuestRoute>} />

              {/* Worker dashboard */}
              <Route
                path="/worker"
                element={
                  <ProtectedRoute allowedRoles={['worker']}>
                    <WorkerDashboard />
                  </ProtectedRoute>
                }
              />

              {/* Grievance heatmap — admin and dept_head only */}
              <Route
                path="/heatmap"
                element={
                  <ProtectedRoute allowedRoles={['admin', 'dept_head']}>
                    <GrievanceHeatmap />
                  </ProtectedRoute>
                }
              />
            </Routes>
            </Suspense>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
