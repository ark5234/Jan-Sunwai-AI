import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, CheckCircle2, Clock, AlertCircle, ArrowUpRight, ArrowLeft, Loader2, CheckCheck } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function Notifications() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all | unread

  useEffect(() => {
    if (!user) return;
    fetchNotifications();
  }, [user, filter]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (filter === 'unread') params.append('unread_only', 'true');
      const res = await fetch(`${API}/notifications?${params}`);
      if (res.ok) setNotifications(await res.json());
    } catch (err) {
      console.error('Failed to fetch notifications', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await fetch(`${API}/notifications/${id}/read`, {
        method: 'PATCH',
      });
      setNotifications(prev => prev.map(n => n._id === id ? { ...n, is_read: true } : n));
    } catch { /* ignore */ }
  };

  const markAllRead = async () => {
    try {
      await fetch(`${API}/notifications/read-all`, {
        method: 'PATCH',
      });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch { /* ignore */ }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hour${hrs > 1 ? 's' : ''} ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const getIcon = (type, statusTo) => {
    if (type === 'escalation') return <ArrowUpRight className="w-5 h-5 text-amber-500" />;
    if (statusTo === 'Resolved') return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    if (statusTo === 'Rejected') return <AlertCircle className="w-5 h-5 text-red-500" />;
    if (statusTo === 'In Progress') return <Clock className="w-5 h-5 text-amber-500" />;
    if (statusTo === 'Open') return <Bell className="w-5 h-5 text-blue-500" />;
    return <Bell className="w-5 h-5 text-gray-400" />;
  };

  const getAccentColor = (type, statusTo) => {
    if (type === 'escalation') return 'border-l-amber-400';
    if (statusTo === 'Resolved') return 'border-l-green-400';
    if (statusTo === 'Rejected') return 'border-l-red-400';
    if (statusTo === 'In Progress') return 'border-l-amber-400';
    return 'border-l-blue-400';
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link to="/dashboard" className="inline-flex items-center text-sm text-gray-500 hover:text-primary transition mb-4">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 govt-heading">Notifications</h1>
            <p className="text-sm text-gray-500 mt-1">
              Track the progress of your grievances
            </p>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="flex items-center gap-1.5 text-sm text-primary hover:text-primary-light font-medium transition"
            >
              <CheckCheck className="w-4 h-4" />
              Mark all read
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-5 bg-gray-100 rounded-lg p-1 w-fit">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
            filter === 'all' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
            filter === 'unread' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Unread
          {unreadCount > 0 && (
            <span className="bg-primary text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* List */}
      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
        </div>
      ) : notifications.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-lg border border-gray-200">
          <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">
            {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
          </p>
          <p className="text-sm text-gray-400 mt-1">
            You'll be notified when your grievance status changes.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n._id}
              onClick={() => {
                if (!n.is_read) markAsRead(n._id);
                if (n.complaint_id) navigate('/dashboard');
              }}
              className={`bg-white rounded-lg border border-gray-200 border-l-4 ${getAccentColor(n.type, n.status_to)} p-4 cursor-pointer hover:shadow-sm transition flex gap-3.5 ${
                !n.is_read ? 'ring-1 ring-primary/10' : ''
              }`}
            >
              <div className="mt-0.5 shrink-0">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                  !n.is_read ? 'bg-blue-50' : 'bg-gray-50'
                }`}>
                  {getIcon(n.type, n.status_to)}
                </div>
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <h4 className={`text-sm ${!n.is_read ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'}`}>
                    {n.title}
                  </h4>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-gray-400">{formatDate(n.created_at)}</span>
                    {!n.is_read && (
                      <span className="w-2.5 h-2.5 bg-primary rounded-full" title="Unread" />
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mt-0.5">{n.message}</p>
                {n.status_from && n.status_to && (
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    <StatusPill status={n.status_from} />
                    <span className="text-gray-400">→</span>
                    <StatusPill status={n.status_to} />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusPill({ status }) {
  const styles = {
    'Open': 'bg-blue-50 text-blue-700 border-blue-200',
    'In Progress': 'bg-amber-50 text-amber-700 border-amber-200',
    'Resolved': 'bg-green-50 text-green-700 border-green-200',
    'Rejected': 'bg-red-50 text-red-700 border-red-200',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${styles[status] || styles.Open}`}>
      {status}
    </span>
  );
}
