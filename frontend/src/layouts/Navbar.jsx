import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Menu, X, LogOut, User, LayoutDashboard, PlusCircle, UserCircle, Bell, CheckCircle2, ArrowUpRight, Clock, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Navbar() {
  const [isOpen, setIsOpen] = React.useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  // Notification state
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const bellRef = useRef(null);
  const dropdownRef = useRef(null);

  const isActive = (path) => location.pathname === path 
    ? "text-white border-b-2 border-saffron" 
    : "text-blue-200 hover:text-white border-b-2 border-transparent hover:border-white/30";

  const roleLabel = user?.role === 'dept_head' ? 'Dept Head' : user?.role === 'admin' ? 'Admin' : 'Citizen';

  // Fetch unread count periodically
  useEffect(() => {
    if (!user?.access_token) return;
    const headers = { Authorization: `Bearer ${user.access_token}` };

    const fetchCount = async () => {
      try {
        const res = await fetch(`${API}/notifications/unread-count`, { headers });
        if (res.ok) {
          const data = await res.json();
          setUnreadCount(data.count);
        }
      } catch { /* ignore */ }
    };

    fetchCount();
    const interval = setInterval(fetchCount, 30000); // poll every 30s
    return () => clearInterval(interval);
  }, [user?.access_token]);

  // Fetch recent notifications when dropdown opens
  useEffect(() => {
    if (!showNotifications || !user?.access_token) return;
    const headers = { Authorization: `Bearer ${user.access_token}` };

    (async () => {
      try {
        const res = await fetch(`${API}/notifications?limit=10`, { headers });
        if (res.ok) setNotifications(await res.json());
      } catch { /* ignore */ }
    })();
  }, [showNotifications, user?.access_token]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target) &&
        bellRef.current && !bellRef.current.contains(e.target)
      ) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const markAsRead = async (id) => {
    if (!user?.access_token) return;
    try {
      await fetch(`${API}/notifications/${id}/read`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${user.access_token}` },
      });
      setNotifications(prev => prev.map(n => n._id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch { /* ignore */ }
  };

  const markAllRead = async () => {
    if (!user?.access_token) return;
    try {
      await fetch(`${API}/notifications/read-all`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${user.access_token}` },
      });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch { /* ignore */ }
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  const notifIcon = (type, statusTo) => {
    if (type === 'escalation') return <ArrowUpRight className="w-4 h-4 text-amber-500" />;
    if (statusTo === 'Resolved') return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    if (statusTo === 'Rejected') return <AlertCircle className="w-4 h-4 text-red-500" />;
    if (statusTo === 'In Progress') return <Clock className="w-4 h-4 text-amber-500" />;
    return <Bell className="w-4 h-4 text-blue-500" />;
  };

  return (
    <header>
      {/* Main Navy Bar */}
      <nav className="bg-primary-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Brand / Emblem */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-3">
                {/* National Emblem */}
                <img 
                  src="/emblem.svg" 
                  alt="National Emblem" 
                  className="h-10 w-10 opacity-90"
                />
                <div className="hidden sm:block">
                  <div className="text-white font-bold text-lg tracking-tight leading-tight">
                    जन-सुनवाई
                  </div>
                  <div className="text-blue-200 text-[11px] tracking-wide leading-tight">
                    Public Grievance Redressal System
                  </div>
                </div>
                <div className="sm:hidden">
                  <span className="text-white font-bold text-base">जन-सुनवाई</span>
                </div>
              </Link>
            </div>
            
            {/* Desktop Nav Links */}
            <div className="hidden md:flex md:items-center md:space-x-1">
              <Link to="/" className={`px-3 py-[18px] text-sm font-medium transition-colors ${isActive('/')}`}>
                <Home className="inline-block w-4 h-4 mr-1 -mt-0.5" />
                Home
              </Link>
              {user && (
                <>
                  <Link to="/dashboard" className={`px-3 py-[18px] text-sm font-medium transition-colors ${isActive('/dashboard')}`}>
                    <LayoutDashboard className="inline-block w-4 h-4 mr-1 -mt-0.5" />
                    Dashboard
                  </Link>
                  <Link to="/analyze" className={`px-3 py-[18px] text-sm font-medium transition-colors ${isActive('/analyze')}`}>
                    <PlusCircle className="inline-block w-4 h-4 mr-1 -mt-0.5" />
                    File Complaint
                  </Link>
                </>
              )}

              <div className="h-6 w-px bg-white/20 mx-2"></div>

              {user ? (
                <div className="flex items-center space-x-2">
                  {/* Notification Bell */}
                  <div className="relative">
                    <button
                      ref={bellRef}
                      onClick={() => setShowNotifications(!showNotifications)}
                      className="relative text-blue-200 hover:text-white transition p-1.5 rounded hover:bg-white/10"
                      title="Notifications"
                    >
                      <Bell className="w-4.5 h-4.5" />
                      {unreadCount > 0 && (
                        <span className="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 bg-saffron text-white text-[9px] font-bold rounded-full flex items-center justify-center leading-none">
                          {unreadCount > 9 ? '9+' : unreadCount}
                        </span>
                      )}
                    </button>

                    {/* Dropdown */}
                    {showNotifications && (
                      <div
                        ref={dropdownRef}
                        className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden"
                      >
                        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                          <h4 className="text-sm font-bold text-gray-800">Notifications</h4>
                          {unreadCount > 0 && (
                            <button
                              onClick={markAllRead}
                              className="text-[10px] text-primary hover:underline font-medium"
                            >
                              Mark all read
                            </button>
                          )}
                        </div>
                        <div className="max-h-80 overflow-y-auto">
                          {notifications.length === 0 ? (
                            <div className="px-4 py-8 text-center">
                              <Bell className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                              <p className="text-sm text-gray-500">No notifications yet</p>
                            </div>
                          ) : (
                            notifications.map((n) => (
                              <div
                                key={n._id}
                                onClick={() => {
                                  if (!n.is_read) markAsRead(n._id);
                                  setShowNotifications(false);
                                  if (n.complaint_id) navigate('/dashboard');
                                }}
                                className={`px-4 py-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition flex gap-3 ${
                                  !n.is_read ? 'bg-blue-50/50' : ''
                                }`}
                              >
                                <div className="mt-0.5 shrink-0">
                                  {notifIcon(n.type, n.status_to)}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <div className="flex items-start justify-between gap-2">
                                    <p className={`text-sm leading-tight ${!n.is_read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                                      {n.title}
                                    </p>
                                    {!n.is_read && (
                                      <span className="w-2 h-2 bg-primary rounded-full shrink-0 mt-1" />
                                    )}
                                  </div>
                                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                                  <p className="text-[10px] text-gray-400 mt-1">{timeAgo(n.created_at)}</p>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                        {notifications.length > 0 && (
                          <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-200 text-center">
                            <Link
                              to="/notifications"
                              onClick={() => setShowNotifications(false)}
                              className="text-xs text-primary hover:underline font-medium"
                            >
                              View All Notifications
                            </Link>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Profile link */}
                  <Link 
                    to="/profile" 
                    className="flex items-center gap-2 text-blue-100 hover:text-white transition px-2 py-1.5 rounded hover:bg-white/10"
                    title="View Profile"
                  >
                    <div className="w-7 h-7 rounded-full bg-white/15 border border-white/25 flex items-center justify-center">
                      <UserCircle className="w-4 h-4" />
                    </div>
                    <div className="flex flex-col leading-none">
                      <span className="text-sm font-medium">{user.username}</span>
                      <span className="text-[9px] text-blue-300 uppercase tracking-wider mt-0.5">{roleLabel}</span>
                    </div>
                  </Link>
                  <button 
                    onClick={logout} 
                    className="text-blue-300 hover:text-white transition p-1.5 rounded hover:bg-white/10" 
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Link to="/login" className="px-3 py-1.5 rounded text-sm font-medium text-blue-100 hover:text-white hover:bg-white/10 transition">
                    Log In
                  </Link>
                  <Link to="/register" className="bg-saffron text-white px-4 py-1.5 rounded text-sm font-semibold hover:bg-saffron-light transition">
                    Register
                  </Link>
                </div>
              )}
            </div>

            {/* Mobile menu button */}
            <div className="-mr-2 flex items-center md:hidden">
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="inline-flex items-center justify-center p-2 rounded text-blue-200 hover:text-white hover:bg-white/10 focus:outline-none"
              >
                {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Tricolor Stripe */}
      <div className="tricolor-bar" aria-hidden="true"></div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-primary border-t border-white/10">
          <div className="px-4 pt-2 pb-3 space-y-1">
            <Link 
              to="/" 
              onClick={() => setIsOpen(false)}
              className="block px-3 py-2.5 rounded text-base font-medium text-blue-100 hover:text-white hover:bg-white/10"
            >
              Home
            </Link>
            {user && (
              <>
                <Link 
                  to="/dashboard" 
                  onClick={() => setIsOpen(false)}
                  className="block px-3 py-2.5 rounded text-base font-medium text-blue-100 hover:text-white hover:bg-white/10"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/analyze" 
                  onClick={() => setIsOpen(false)}
                  className="block px-3 py-2.5 rounded text-base font-medium text-blue-100 hover:text-white hover:bg-white/10"
                >
                  File Complaint
                </Link>
              </>
            )}
            <div className="border-t border-white/10 my-2"></div>
            {user ? (
              <>
                <Link 
                  to="/notifications" 
                  onClick={() => setIsOpen(false)}
                  className="flex items-center justify-between px-3 py-2.5 rounded text-blue-100 hover:text-white hover:bg-white/10"
                >
                  <span className="flex items-center gap-2 text-base font-medium">
                    <Bell className="w-4 h-4" />
                    Notifications
                  </span>
                  {unreadCount > 0 && (
                    <span className="bg-saffron text-white text-xs font-bold px-2 py-0.5 rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </Link>
                <Link 
                  to="/profile" 
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded text-blue-100 hover:text-white hover:bg-white/10"
                >
                  <div className="w-8 h-8 rounded-full bg-white/15 border border-white/25 flex items-center justify-center">
                    <UserCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">{user.username}</div>
                    <div className="text-[10px] text-blue-300 uppercase tracking-wider">{roleLabel} — View Profile</div>
                  </div>
                </Link>
                <button 
                  onClick={() => { logout(); setIsOpen(false); }} 
                  className="w-full text-left px-3 py-2.5 rounded text-red-300 hover:text-red-200 hover:bg-white/10 text-sm font-medium flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-2 px-3">
                <Link to="/login" onClick={() => setIsOpen(false)} className="block py-2 text-center rounded text-blue-100 hover:text-white hover:bg-white/10 font-medium">
                  Log In
                </Link>
                <Link to="/register" onClick={() => setIsOpen(false)} className="block py-2 text-center rounded bg-saffron text-white font-semibold hover:bg-saffron-light">
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
