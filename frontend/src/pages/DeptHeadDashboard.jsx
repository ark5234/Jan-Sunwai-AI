import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { FileText, MapPin, Calendar, Filter, ArrowRightLeft, StickyNote, ChevronDown, ChevronUp, Flame } from 'lucide-react';
import axios from 'axios';
import SLABadge from '../components/SLABadge';
import ComplaintComments from '../components/ComplaintComments';

const DeptHeadDashboard = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [updateError, setUpdateError] = useState(null);
  const [transferPanel, setTransferPanel] = useState({});

  const [notePanel, setNotePanel] = useState({});
  const [noteText, setNoteText] = useState({});
  const [deptWorkers, setDeptWorkers] = useState([]);

  const DEPARTMENTS = [
    'Health Department',
    'Civil Department',
    'Horticulture',
    'Electrical Department',
    'IT Department',
    'Commercial',
    'Enforcement',
    'VBD Department',
    'EBR Department',
    'Fire Department',
    'Uncategorized',
  ];

  useEffect(() => {
    if (user?.access_token) {
      fetchDepartmentComplaints();
      fetchDeptWorkers();
    }
  }, [statusFilter, user]);

  const fetchDepartmentComplaints = async () => {
    if (!user?.access_token) return;
    try {
      setLoading(true);
      const params = {};
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      
      const response = await axios.get('http://localhost:8000/complaints', {
        headers: {
          Authorization: `Bearer ${user.access_token}`
        },
        params
      });
      setComplaints(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching complaints:', err);
      if (err.response?.status === 401) {
        setError('Session expired. Please log out and log back in.');
      } else {
        setError('Failed to load complaints');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchDeptWorkers = async () => {
    try {
      const res = await axios.get('http://localhost:8000/workers', {
        headers: { Authorization: `Bearer ${user.access_token}` },
      });
      const myDept = user.department;
      setDeptWorkers(res.data.filter(w => w.is_approved && (!myDept || w.department === myDept)));
    } catch { /* silent — dept head may not have admin perms, ignore */ }
  };

  const updateComplaintStatus = async (complaintId, newStatus) => {
    setUpdateError(null);
    try {
      await axios.patch(
        `http://localhost:8000/complaints/${complaintId}/status`,
        { status: newStatus },
        {
          headers: {
            Authorization: `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      fetchDepartmentComplaints();
    } catch (err) {
      console.error('Error updating status:', err);
      setUpdateError('Failed to update status. Please try again.');
      setTimeout(() => setUpdateError(null), 5000);
    }
  };

  const submitNote = async (complaintId) => {
    const note = noteText[complaintId]?.trim();
    if (!note) return;
    try {
      await axios.post(
        `http://localhost:8000/complaints/${complaintId}/notes`,
        { note },
        { headers: { Authorization: `Bearer ${user.access_token}`, 'Content-Type': 'application/json' } }
      );
      setNoteText(prev => ({ ...prev, [complaintId]: '' }));
      fetchDepartmentComplaints();
    } catch (err) {
      setUpdateError(err.response?.data?.detail || 'Failed to save note.');
      setTimeout(() => setUpdateError(null), 5000);
    }
  };

  const openTransferPanel = (complaintId, currentDept) => {
    const defaultDept = DEPARTMENTS.find(d => d !== currentDept) || DEPARTMENTS[0];
    setTransferPanel(prev => ({
      ...prev,
      [complaintId]: { dept: defaultDept, reason: '' }
    }));
  };

  const closeTransferPanel = (complaintId) => {
    setTransferPanel(prev => {
      const next = { ...prev };
      delete next[complaintId];
      return next;
    });
  };

  const transferComplaint = async (complaintId) => {
    const panel = transferPanel[complaintId];
    if (!panel?.dept) return;
    setUpdateError(null);
    try {
      await axios.patch(
        `http://localhost:8000/complaints/${complaintId}/transfer`,
        { new_department: panel.dept, reason: panel.reason || undefined },
        {
          headers: {
            Authorization: `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      closeTransferPanel(complaintId);
      fetchDepartmentComplaints();
    } catch (err) {
      console.error('Error transferring complaint:', err);
      const detail = err.response?.data?.detail || 'Failed to transfer complaint. Please try again.';
      setUpdateError(detail);
      setTimeout(() => setUpdateError(null), 6000);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Open':
        return 'bg-blue-100 text-blue-800';
      case 'In Progress':
        return 'bg-yellow-100 text-yellow-800';
      case 'Resolved':
        return 'bg-green-100 text-green-800';
      case 'Rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Department Dashboard</h1>
        <p className="mt-2 text-sm sm:text-base text-gray-600">
          Managing complaints for: <span className="font-semibold">{user.department || 'All Departments'}</span>
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/map" className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-600 text-white text-sm rounded-md hover:bg-teal-700">
            🗺️ Map View
          </Link>
          <Link to="/heatmap" className="inline-flex items-center gap-1.5 px-4 py-2 bg-orange-500 text-white text-sm rounded-md hover:bg-orange-600">
            <Flame size={14} /> Heatmap
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <div className="flex items-center">
            <FileText className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
            <div className="ml-3 sm:ml-4">
              <p className="text-xl sm:text-2xl font-semibold">{complaints.length}</p>
              <p className="text-xs sm:text-sm text-gray-600">Total</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <div className="flex items-center">
            <FileText className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-600" />
            <div className="ml-3 sm:ml-4">
              <p className="text-xl sm:text-2xl font-semibold">
                {complaints.filter(c => c.status === 'Open').length}
              </p>
              <p className="text-xs sm:text-sm text-gray-600">Open</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <div className="flex items-center">
            <FileText className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
            <div className="ml-3 sm:ml-4">
              <p className="text-xl sm:text-2xl font-semibold">
                {complaints.filter(c => c.status === 'In Progress').length}
              </p>
              <p className="text-xs sm:text-sm text-gray-600">In Progress</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <div className="flex items-center">
            <FileText className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
            <div className="ml-3 sm:ml-4">
              <p className="text-xl sm:text-2xl font-semibold">
                {complaints.filter(c => c.status === 'Resolved').length}
              </p>
              <p className="text-xs sm:text-sm text-gray-600">Resolved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Workers in this department (read-only) */}
      {deptWorkers.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            👷 Field Workers — {user.department || 'Your Department'} ({deptWorkers.length})
          </h3>
          <div className="flex flex-wrap gap-3">
            {deptWorkers.map(w => {
              const colorMap = { available: 'bg-green-100 text-green-800', busy: 'bg-yellow-100 text-yellow-800', offline: 'bg-gray-100 text-gray-500' };
              return (
                <div key={w._id} className="flex items-center gap-2 border border-gray-100 rounded-lg px-3 py-2 bg-gray-50">
                  <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
                    {w.username?.[0]?.toUpperCase()}
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-800">{w.username}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                      <span className={`text-xs px-1.5 py-0.5 rounded-full ${colorMap[w.worker_status] || 'bg-gray-100 text-gray-500'}`}>
                        {w.worker_status || 'offline'}
                      </span>
                      <span className="text-xs text-gray-400">{w.active_task_count || 0} task{w.active_task_count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
          <Filter className="h-5 w-5 text-gray-400 hidden sm:block" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full sm:w-auto border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          >
            <option value="all">All Status</option>
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Complaints List */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {updateError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 animate-fadeIn">
          <p className="text-red-800">{updateError}</p>
        </div>
      )}

      {complaints.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No complaints found</h3>
          <p className="text-gray-600">There are no complaints for your department yet</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <ul className="divide-y divide-gray-200">
            {complaints.map((complaint) => (
              <li key={complaint._id} className="hover:bg-gray-50">
                <div className="px-4 sm:px-6 py-4">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                        <h3 className="text-base sm:text-lg font-medium text-gray-900 truncate">
                          {complaint.department}
                        </h3>
                        <div className="flex items-center gap-2 flex-wrap self-start sm:self-center">
                          {complaint.priority && (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              { Critical: 'bg-red-100 text-red-700', High: 'bg-orange-100 text-orange-700',
                                Medium: 'bg-yellow-100 text-yellow-700', Low: 'bg-green-100 text-green-700' }
                              [complaint.priority] || 'bg-slate-100 text-slate-600'
                            }`}>{complaint.priority}</span>
                          )}
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(complaint.status)} whitespace-nowrap`}>
                            {complaint.status}
                          </span>
                          <SLABadge createdAt={complaint.created_at} department={complaint.department} status={complaint.status} updatedAt={complaint.updated_at} />
                        </div>
                      </div>
                      <p className="mt-2 text-sm text-gray-600">
                        {complaint.description}
                      </p>
                      <div className="mt-2 flex flex-col sm:flex-row sm:items-center text-sm text-gray-500 gap-2">
                        <div className="flex items-center">
                          <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                          <span className="truncate">{complaint.location?.address || 'Location not available'}</span>
                        </div>
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 sm:ml-4 mr-1 flex-shrink-0" />
                          <span>{new Date(complaint.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      {complaint.ai_metadata && (
                        <div className="mt-2 text-xs text-gray-500">
                          Confidence: {(complaint.ai_metadata.confidence_score * 100).toFixed(1)}%
                        </div>
                      )}

                      {/* Dept notes display */}
                      {complaint.dept_notes?.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {complaint.dept_notes.map((n, i) => (
                            <div key={i} className="text-xs bg-purple-50 border border-purple-100 rounded px-2 py-1">
                              <span className="font-medium text-purple-700">{n.created_by}: </span>
                              <span className="text-slate-600">{n.note}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Add note toggle */}
                      <button
                        onClick={() => setNotePanel(prev => ({ ...prev, [complaint._id]: !prev[complaint._id] }))}
                        className="mt-2 inline-flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800"
                      >
                        <StickyNote size={12} />
                        {notePanel[complaint._id] ? 'Hide note' : 'Add internal note'}
                        {notePanel[complaint._id] ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                      </button>
                      {notePanel[complaint._id] && (
                        <div className="mt-1 flex gap-2">
                          <input
                            value={noteText[complaint._id] || ''}
                            onChange={e => setNoteText(prev => ({ ...prev, [complaint._id]: e.target.value }))}
                            placeholder="Internal note (not visible to citizen)…"
                            maxLength={1000}
                            className="flex-1 text-xs border border-slate-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-400"
                          />
                          <button
                            onClick={() => submitNote(complaint._id)}
                            disabled={!noteText[complaint._id]?.trim()}
                            className="px-3 py-1.5 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 disabled:opacity-50"
                          >Save</button>
                        </div>
                      )}
                      <ComplaintComments complaintId={complaint._id} currentRole="dept_head" />

                      {/* Action Buttons */}
                      <div className="mt-4 flex flex-wrap gap-2">
                        {complaint.status === 'Open' && (
                          <button
                            onClick={() => updateComplaintStatus(complaint._id, 'In Progress')}
                            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 touch-manipulation"
                          >
                            Mark In Progress
                          </button>
                        )}
                        {complaint.status === 'In Progress' && (
                          <button
                            onClick={() => updateComplaintStatus(complaint._id, 'Resolved')}
                            className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 touch-manipulation"
                          >
                            Mark Resolved
                          </button>
                        )}
                        {(complaint.status === 'Open' || complaint.status === 'In Progress') && (
                          <button
                            onClick={() => updateComplaintStatus(complaint._id, 'Rejected')}
                            className="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 touch-manipulation"
                          >
                            Reject
                          </button>
                        )}
                        {!transferPanel[complaint._id] ? (
                          <button
                            onClick={() => openTransferPanel(complaint._id, complaint.department)}
                            className="px-3 py-1.5 bg-amber-500 text-white text-sm rounded hover:bg-amber-600 touch-manipulation flex items-center gap-1"
                          >
                            <ArrowRightLeft className="h-3.5 w-3.5" />
                            Transfer
                          </button>
                        ) : (
                          <div className="w-full mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                            <p className="text-xs font-medium text-amber-800 mb-2">Transfer to department:</p>
                            <select
                              value={transferPanel[complaint._id].dept}
                              onChange={(e) =>
                                setTransferPanel(prev => ({
                                  ...prev,
                                  [complaint._id]: { ...prev[complaint._id], dept: e.target.value }
                                }))
                              }
                              className="w-full text-sm border-gray-300 rounded-md mb-2"
                            >
                              {DEPARTMENTS
                                .filter(d => d !== complaint.department)
                                .map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                            <input
                              type="text"
                              placeholder="Reason for transfer (optional)"
                              value={transferPanel[complaint._id].reason}
                              onChange={(e) =>
                                setTransferPanel(prev => ({
                                  ...prev,
                                  [complaint._id]: { ...prev[complaint._id], reason: e.target.value }
                                }))
                              }
                              className="w-full text-sm border-gray-300 rounded-md px-2 py-1.5 mb-2 border"
                            />
                            <div className="flex gap-2">
                              <button
                                onClick={() => transferComplaint(complaint._id)}
                                className="px-3 py-1.5 bg-amber-600 text-white text-sm rounded hover:bg-amber-700"
                              >
                                Confirm Transfer
                              </button>
                              <button
                                onClick={() => closeTransferPanel(complaint._id)}
                                className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    {complaint.image_url && (
                      <div className="sm:ml-4 flex-shrink-0">
                        <img
                          src={`http://localhost:8000/${complaint.image_url}`}
                          alt="Complaint"
                          className="h-32 w-32 sm:h-32 sm:w-32 object-cover rounded"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default DeptHeadDashboard;
