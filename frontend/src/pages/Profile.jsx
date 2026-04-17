import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  UserCircle, Mail, Shield, Building2, Calendar, FileText, 
  Clock, CheckCircle2, AlertCircle, Loader2, ArrowLeft 
} from 'lucide-react';
import { Link } from 'react-router-dom';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState(null);
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    phone_number: '',
  });

  const fetchData = async () => {
    if (!user?.access_token) return;
    try {
      setLoading(true);
      const headers = { Authorization: `Bearer ${user.access_token}` };

      const [profileRes, complaintsRes] = await Promise.all([
        fetch(`${API}/users/me`, { headers }),
        fetch(`${API}/complaints`, { headers }),
      ]);

      if (profileRes.ok) {
        setProfile(await profileRes.json());
      } else {
        setError('Failed to load profile data');
      }

      if (complaintsRes.ok) {
        setComplaints(await complaintsRes.json());
      }
    } catch (err) {
      console.error('Profile fetch error:', err);
      setError('Unable to connect to server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  useEffect(() => {
    setProfileForm({
      full_name: profile?.full_name || '',
      phone_number: profile?.phone_number || '',
    });
  }, [profile]);

  const saveProfile = async () => {
    if (!user?.access_token) return;
    setSavingProfile(true);
    setProfileMessage(null);
    try {
      const response = await fetch(`${API}/users/me`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${user.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: profileForm.full_name,
          phone_number: profileForm.phone_number,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload?.detail || 'Profile update failed');
      }

      const updated = await response.json();
      setProfile(updated);
      setEditMode(false);
      setProfileMessage({ type: 'success', text: 'Profile updated successfully.' });
    } catch (err) {
      setProfileMessage({ type: 'error', text: err.message || 'Could not update profile.' });
    } finally {
      setSavingProfile(false);
    }
  };

  // Complaint statistics
  const stats = {
    total: complaints.length,
    open: complaints.filter(c => c.status === 'Open').length,
    inProgress: complaints.filter(c => c.status === 'In Progress').length,
    resolved: complaints.filter(c => c.status === 'Resolved').length,
    rejected: complaints.filter(c => c.status === 'Rejected').length,
  };

  const roleDisplayName = {
    citizen: 'Citizen',
    dept_head: 'Department Head',
    admin: 'System Administrator',
  };

  const roleBadgeColor = {
    citizen: 'bg-blue-100 text-blue-800 border-blue-200',
    dept_head: 'bg-amber-100 text-amber-800 border-amber-200',
    admin: 'bg-red-100 text-red-800 border-red-200',
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
  };

  const initials = (name) => {
    if (!name) return '?';
    return name
      .split(/[\s_]+/)
      .map(w => w[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <AlertCircle className="w-12 h-12 text-danger mx-auto mb-4" />
        <p className="text-lg text-gray-700">{error}</p>
        <Link to="/dashboard" className="mt-4 inline-block text-primary hover:underline">
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  const displayName = profile?.username || user?.username || 'User';
  const displayRole = profile?.role || user?.role || 'citizen';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Band */}
      <div className="bg-linear-to-r from-primary-dark to-primary">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link 
            to="/dashboard" 
            className="inline-flex items-center gap-1.5 text-blue-200 hover:text-white text-sm mb-6 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>

          <div className="flex items-center gap-5">
            {/* Large Avatar */}
            <div className="w-20 h-20 rounded-full bg-white/15 border-2 border-white/30 flex items-center justify-center shrink-0">
              <span className="text-2xl font-bold text-white">{initials(displayName)}</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{displayName}</h1>
              <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${roleBadgeColor[displayRole] || roleBadgeColor.citizen}`}>
                  <Shield className="w-3 h-3" />
                  {roleDisplayName[displayRole] || 'Citizen'}
                </span>
                {profile?.created_at && (
                  <span className="text-blue-200 text-sm flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    Member since {formatDate(profile.created_at)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column — Personal Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* Account Details Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-5 py-3.5 bg-gray-50 border-b border-gray-200 flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Account Details</h2>
                <div className="flex items-center gap-2">
                  {editMode ? (
                    <>
                      <button
                        onClick={saveProfile}
                        disabled={savingProfile}
                        className="text-xs px-2.5 py-1 rounded bg-primary text-white hover:bg-primary-light disabled:opacity-60"
                      >
                        {savingProfile ? 'Saving...' : 'Save'}
                      </button>
                      <button
                        onClick={() => {
                          setEditMode(false);
                          setProfileForm({
                            full_name: profile?.full_name || '',
                            phone_number: profile?.phone_number || '',
                          });
                        }}
                        className="text-xs px-2.5 py-1 rounded border border-gray-300 text-gray-700 hover:bg-white"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setEditMode(true)}
                      className="text-xs px-2.5 py-1 rounded border border-gray-300 text-gray-700 hover:bg-white"
                    >
                      Edit
                    </button>
                  )}
                </div>
              </div>
              <div className="p-5 space-y-4">
                {profileMessage && (
                  <div className={`text-xs rounded px-2.5 py-2 ${
                    profileMessage.type === 'success'
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-red-50 text-red-700 border border-red-200'
                  }`}>
                    {profileMessage.text}
                  </div>
                )}
                <div className="flex items-start gap-3">
                  <UserCircle className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                  <div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Username</div>
                    <div className="text-sm font-medium text-gray-900 mt-0.5">{displayName}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <UserCircle className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                  <div className="w-full">
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Full Name</div>
                    {editMode ? (
                      <input
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, full_name: e.target.value }))}
                        placeholder="Enter full name"
                        className="mt-1 w-full text-sm border border-gray-300 rounded px-2 py-1.5"
                      />
                    ) : (
                      <div className="text-sm font-medium text-gray-900 mt-0.5">{profile?.full_name || '—'}</div>
                    )}
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <UserCircle className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                  <div className="w-full">
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Phone Number</div>
                    {editMode ? (
                      <input
                        value={profileForm.phone_number}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, phone_number: e.target.value }))}
                        placeholder="Enter phone number"
                        className="mt-1 w-full text-sm border border-gray-300 rounded px-2 py-1.5"
                      />
                    ) : (
                      <div className="text-sm font-medium text-gray-900 mt-0.5">{profile?.phone_number || '—'}</div>
                    )}
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Mail className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                  <div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Email</div>
                    <div className="text-sm font-medium text-gray-900 mt-0.5">{profile?.email || user?.email || '—'}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                  <div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Role</div>
                    <div className="text-sm font-medium text-gray-900 mt-0.5">{roleDisplayName[displayRole] || 'Citizen'}</div>
                  </div>
                </div>
                {profile?.department && (
                  <div className="flex items-start gap-3">
                    <Building2 className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                    <div>
                      <div className="text-xs text-gray-500 uppercase tracking-wide">Department</div>
                      <div className="text-sm font-medium text-gray-900 mt-0.5">{profile.department}</div>
                    </div>
                  </div>
                )}
                {profile?.created_at && (
                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-primary mt-0.5 shrink-0" />
                    <div>
                      <div className="text-xs text-gray-500 uppercase tracking-wide">Member Since</div>
                      <div className="text-sm font-medium text-gray-900 mt-0.5">{formatDate(profile.created_at)}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-5 py-3.5 bg-gray-50 border-b border-gray-200">
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Quick Actions</h2>
              </div>
              <div className="p-4 space-y-2">
                <Link 
                  to="/analyze" 
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-primary/5 hover:text-primary transition"
                >
                  <FileText className="w-4 h-4" />
                  File New Complaint
                </Link>
                <Link 
                  to="/dashboard" 
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-primary/5 hover:text-primary transition"
                >
                  <Clock className="w-4 h-4" />
                  View All Complaints
                </Link>
              </div>
            </div>
          </div>

          {/* Right Column — Stats & Recent */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatCard label="Total Filed" value={stats.total} icon={FileText} color="text-primary" bg="bg-blue-50" />
              <StatCard label="Open" value={stats.open} icon={AlertCircle} color="text-saffron" bg="bg-orange-50" />
              <StatCard label="In Progress" value={stats.inProgress} icon={Clock} color="text-amber-600" bg="bg-amber-50" />
              <StatCard label="Resolved" value={stats.resolved} icon={CheckCircle2} color="text-success" bg="bg-green-50" />
            </div>

            {/* Recent Complaints */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-5 py-3.5 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Recent Complaints</h2>
                {complaints.length > 5 && (
                  <Link to="/dashboard" className="text-xs text-primary hover:underline font-medium">
                    View All →
                  </Link>
                )}
              </div>
              {complaints.length === 0 ? (
                <div className="px-5 py-10 text-center">
                  <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-sm">No complaints filed yet.</p>
                  <Link 
                    to="/analyze" 
                    className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                  >
                    File your first complaint →
                  </Link>
                </div>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {complaints.slice(0, 5).map((c) => (
                    <li key={c._id || c.id} className="px-5 py-3.5 hover:bg-gray-50 transition">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm text-gray-900 font-medium truncate">
                            {c.description?.slice(0, 80)}{c.description?.length > 80 ? '…' : ''}
                          </p>
                          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                            <span>{c.department}</span>
                            <span className="text-gray-300">•</span>
                            <span>{formatDate(c.created_at)}</span>
                          </div>
                        </div>
                        <StatusBadge status={c.status} />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color, bg }) {
  return (
    <div className="stat-card bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center mb-2.5`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    'Open': 'bg-blue-50 text-blue-700 border-blue-200',
    'In Progress': 'bg-amber-50 text-amber-700 border-amber-200',
    'Resolved': 'bg-green-50 text-green-700 border-green-200',
    'Rejected': 'bg-red-50 text-red-700 border-red-200',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border shrink-0 ${styles[status] || styles.Open}`}>
      {status}
    </span>
  );
}
