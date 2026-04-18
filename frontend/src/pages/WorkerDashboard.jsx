import React, { useState, useEffect, useCallback } from 'react';
import {
  MapPin, Calendar, CheckCircle2, Target, ClipboardList,
  Power, Activity, AlertCircle, Zap, BarChart2, Shield,
} from 'lucide-react';
import ComplaintComments from '../components/ComplaintComments';
import StatusTimeline from '../components/StatusTimeline';
import FormattedComplaintText from '../components/FormattedComplaintText';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const PRIORITY_COLORS = {
  Critical: 'bg-red-100 text-red-700',
  High:     'bg-orange-100 text-orange-700',
  Medium:   'bg-yellow-100 text-yellow-700',
  Low:      'bg-green-100 text-green-700',
};

const STATUS_STYLE = {
  available: { label: 'Available', dot: 'bg-emerald-500', badge: 'bg-green-50 text-success border border-green-200' },
  busy:      { label: 'Busy',      dot: 'bg-amber-500',   badge: 'bg-amber-50 text-saffron border border-amber-200' },
  offline:   { label: 'Offline',   dot: 'bg-slate-400',   badge: 'bg-gray-100 text-gray-600 border border-gray-200' },
};

function PriorityBadge({ priority }) {
  const cls = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Medium;
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {priority || 'Medium'}
    </span>
  );
}

function TaskCard({ complaint, onDone, doneLoading }) {
  const loc = complaint.location;
  const address = loc?.address || (loc ? `${loc.lat?.toFixed(4)}, ${loc.lon?.toFixed(4)}` : 'Location unknown');

  return (
    <div className="px-4 sm:px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        {/* Left: content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <h3 className="text-base sm:text-lg font-medium text-gray-900 truncate">
              {complaint.department}
            </h3>
            <div className="flex items-center gap-2 flex-wrap self-start sm:self-center">
              <PriorityBadge priority={complaint.priority} />
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-saffron border border-amber-200 whitespace-nowrap">
                In Progress
              </span>
            </div>
          </div>

          <p className="mt-2 text-sm text-gray-600 line-clamp-3">
            <FormattedComplaintText text={complaint.description} />
          </p>

          <div className="mt-2 flex flex-col sm:flex-row sm:items-center text-sm text-gray-500 gap-2">
            <div className="flex items-center">
              <MapPin className="h-4 w-4 mr-1 shrink-0" />
              <span className="truncate">{address}</span>
            </div>
            <div className="flex items-center">
              <Calendar className="h-4 w-4 sm:ml-4 mr-1 shrink-0" />
              <span>
                {new Date(complaint.created_at).toLocaleDateString('en-IN', {
                  day: 'numeric', month: 'short', year: 'numeric',
                })}
              </span>
            </div>
          </div>

          <StatusTimeline items={complaint.status_history || []} />
          <ComplaintComments complaintId={complaint._id} currentRole="worker" />
        </div>

        {/* Right: action */}
        <div className="shrink-0 flex flex-col items-end gap-3">
          <button
            className="inline-flex items-center gap-2 px-4 py-2 rounded text-sm font-semibold text-white bg-success hover:bg-green-700 transition shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={() => onDone(complaint._id)}
            disabled={doneLoading === complaint._id}
          >
            <CheckCircle2 className="h-4 w-4" />
            {doneLoading === complaint._id ? 'Marking...' : 'Mark as Done'}
          </button>
        </div>
      </div>
    </div>
  );
}

function HistoryCard({ complaint }) {
  const loc = complaint.location;
  const address = loc?.address || (loc ? `${loc.lat?.toFixed(4)}, ${loc.lon?.toFixed(4)}` : 'Location unknown');

  return (
    <div className="px-4 sm:px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <h3 className="text-base sm:text-lg font-medium text-gray-900 truncate">
              {complaint.department}
            </h3>
            <div className="flex items-center gap-2 flex-wrap self-start sm:self-center">
              <PriorityBadge priority={complaint.priority} />
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-50 text-success border border-green-200 whitespace-nowrap flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Resolved
              </span>
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-600 line-clamp-2">
            <FormattedComplaintText text={complaint.description} />
          </p>
          <div className="mt-2 flex flex-col sm:flex-row sm:items-center text-sm text-gray-500 gap-2">
            <div className="flex items-center">
              <MapPin className="h-4 w-4 mr-1 shrink-0" />
              <span className="truncate">{address}</span>
            </div>
            <div className="flex items-center">
              <Calendar className="h-4 w-4 sm:ml-4 mr-1 shrink-0" />
              <span>
                Resolved{' '}
                {new Date(complaint.updated_at || complaint.created_at).toLocaleDateString('en-IN', {
                  day: 'numeric', month: 'short', year: 'numeric',
                })}
              </span>
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
             <StatusTimeline items={complaint.status_history || []} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function WorkerDashboard() {
  const [profile, setProfile] = useState(null);
  const [tab, setTab] = useState('active');
  const [doneLoading, setDoneLoading] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [toast, setToast] = useState('');
  const [error, setError] = useState('');

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 4000); };

  const fetchProfile = useCallback(async () => {
    try {
      const res = await fetch(`${API}/workers/me`);
      if (!res.ok) throw new Error('Failed to fetch profile');
      setProfile(await res.json());
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);
  useEffect(() => {
    const id = setInterval(fetchProfile, 30000);
    return () => clearInterval(id);
  }, [fetchProfile]);

  const handleStatusToggle = async () => {
    const current = profile?.worker_status;
    const next = current === 'offline' ? 'available' : 'offline';
    setStatusLoading(true);
    try {
      const res = await fetch(`${API}/workers/me/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ worker_status: next }),
      });
      if (!res.ok) throw new Error('Failed to update status');
      showToast(`Status updated to ${next}`);
      fetchProfile();
    } catch (e) {
      showToast(e.message);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleDone = async (complaintId) => {
    setDoneLoading(complaintId);
    try {
      const res = await fetch(`${API}/workers/me/complaints/${complaintId}/done`, {
        method: 'PATCH',
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Failed to mark done');
      }
      showToast('Complaint marked as resolved! 🎉');
      fetchProfile();
    } catch (e) {
      showToast(e.message);
    } finally {
      setDoneLoading(null);
    }
  };

  /* ── Loading / Error states ── */
  if (!profile && !error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-gray-50 text-gray-500">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
        <p className="font-medium">Loading your workspace…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-gray-50">
        <AlertCircle className="h-12 w-12 text-danger" />
        <p className="font-medium text-gray-800">{error}</p>
      </div>
    );
  }

  const wStatus   = profile.worker_status || 'offline';
  const ss        = STATUS_STYLE[wStatus] || STATUS_STYLE.offline;
  const activeTasks = profile.active_complaints   || [];
  const history     = profile.resolved_history    || [];
  const sa          = profile.service_area;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
      {/* Toast */}
      {toast && (
        <div className="fixed top-6 right-6 z-50 bg-gray-900 text-white px-5 py-3 rounded-xl shadow-lg border border-gray-700 text-sm font-medium">
          {toast}
        </div>
      )}

      {/* ── Page Header ── */}
      <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="govt-heading text-2xl sm:text-3xl text-gray-900">
            Worker Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            {profile.department} &bull; Field Worker
          </p>
        </div>

        {/* Status badge + toggle */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold ${ss.badge}`}>
            <span className={`w-2 h-2 rounded-full ${ss.dot}`} />
            {ss.label}
          </span>
          <button
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded text-sm font-semibold text-white bg-gray-900 hover:bg-gray-800 transition shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleStatusToggle}
            disabled={statusLoading || wStatus === 'busy'}
          >
            <Power className="h-4 w-4" />
            {statusLoading ? 'Updating…' : wStatus === 'offline' ? 'Go Available' : 'Go Offline'}
          </button>
        </div>
      </div>

      {/* ── Stat Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-primary/10 rounded">
              <Target className="h-5 w-5 text-primary" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">{activeTasks.length}</p>
              <p className="text-xs text-gray-500">Active Tasks</p>
            </div>
          </div>
        </div>

        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-green-50 rounded">
              <CheckCircle2 className="h-5 w-5 text-success" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">{history.length}</p>
              <p className="text-xs text-gray-500">Resolved</p>
            </div>
          </div>
        </div>

        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-saffron/10 rounded">
              <Activity className="h-5 w-5 text-saffron" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">{sa ? `${sa.radius_km}km` : 'N/A'}</p>
              <p className="text-xs text-gray-500">Service Radius</p>
            </div>
          </div>
        </div>

        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-primary/10 rounded">
              <Shield className="h-5 w-5 text-primary" />
            </div>
            <div className="ml-3">
              <p className={`text-xl font-bold ${wStatus === 'available' ? 'text-success' : wStatus === 'busy' ? 'text-saffron' : 'text-gray-500'}`}>
                {ss.label}
              </p>
              <p className="text-xs text-gray-500">Current Status</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Service Area Notice ── */}
      {sa && (
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 text-primary px-4 py-3 rounded-lg text-sm font-medium mb-6">
          <MapPin className="h-4 w-4 shrink-0" />
          <p>
            Your active operational area is centered at{' '}
            <span className="font-bold">{sa.locality || 'your assigned location'}</span>{' '}
            ({sa.lat?.toFixed(4)}, {sa.lon?.toFixed(4)}).
          </p>
        </div>
      )}

      {/* ── Tab Navigation ── */}
      <div className="flex gap-0 border-b border-gray-200 mb-0">
        <button
          onClick={() => setTab('active')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold transition-colors border-b-2 ${
            tab === 'active'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300'
          }`}
        >
          Active Tasks
          <span className={`px-2 py-0.5 rounded-full text-xs ${tab === 'active' ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-600'}`}>
            {activeTasks.length}
          </span>
        </button>
        <button
          onClick={() => setTab('history')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold transition-colors border-b-2 ${
            tab === 'history'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300'
          }`}
        >
          Resolved History
          <span className={`px-2 py-0.5 rounded-full text-xs ${tab === 'history' ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-600'}`}>
            {history.length}
          </span>
        </button>
      </div>

      {/* ── Tab Content ── */}
      {tab === 'active' && (
        activeTasks.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center mt-0">
            <Target className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Tasks</h3>
            <p className="text-gray-600">
              {wStatus === 'available'
                ? 'You are available and will receive notifications when new tasks are assigned to you based on your service area.'
                : 'You are currently offline. Go available to start receiving new tasks in your area.'}
            </p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <ul className="divide-y divide-gray-200">
              {activeTasks.map(c => (
                <li key={c._id}>
                  <TaskCard complaint={c} onDone={handleDone} doneLoading={doneLoading} />
                </li>
              ))}
            </ul>
          </div>
        )
      )}

      {tab === 'history' && (
        history.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center mt-0">
            <ClipboardList className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Resolved Tasks</h3>
            <p className="text-gray-600">Your completed assignments will appear here.</p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <ul className="divide-y divide-gray-200">
              {history.map(c => (
                <li key={c._id}>
                  <HistoryCard complaint={c} />
                </li>
              ))}
            </ul>
          </div>
        )
      )}
    </div>
  );
}
