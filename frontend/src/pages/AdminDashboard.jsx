import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { FileText, MapPin, Calendar, Filter, Users, Building, ArrowRightLeft, Download, BarChart2, Map, UserCheck, Flame } from 'lucide-react';
import axios from 'axios';
import SLABadge from '../components/SLABadge';
import ComplaintComments from '../components/ComplaintComments';
import FormattedComplaintText from '../components/FormattedComplaintText';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const STATIC_BASE_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');

const AdminDashboard = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [updateError, setUpdateError] = useState(null);
  const [activeTab, setActiveTab] = useState('complaints'); // 'complaints' | 'workers'
  const [workers, setWorkers] = useState([]);
  const [workersLoading, setWorkersLoading] = useState(false);
  const [workerActionMsg, setWorkerActionMsg] = useState('');
  const [transferPanel, setTransferPanel] = useState({}); // { [complaintId]: { dept: '', reason: '' } }
  const [selected, setSelected] = useState(new Set()); // bulk selection
  const [bulkModal, setBulkModal] = useState(null); // 'status' | 'transfer' | null
  const [bulkStatus, setBulkStatus] = useState('Resolved');
  const [bulkDept, setBulkDept] = useState('');
  const [bulkReason, setBulkReason] = useState('');
  const [reassignLoading, setReassignLoading] = useState(false);
  const [reassignResult, setReassignResult] = useState(null);
  const [assignPanel, setAssignPanel] = useState({}); // { [workerId]: complaintId }
  const [unassignedComplaints, setUnassignedComplaints] = useState([]);

  // Full canonical department list — always show all 11 departments regardless of
  // how many complaints exist, so the filter is useful from day one.
  const departments = [
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
      fetchAllComplaints();
      fetchWorkers();
      fetchUnassigned();
    }
  }, [statusFilter, departmentFilter, user]);

  const fetchAllComplaints = async () => {
    if (!user?.access_token) return;
    try {
      setLoading(true);
      const params = {};
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      if (departmentFilter !== 'all') {
        params.department = departmentFilter;
      }
      
      const response = await axios.get(`${API_BASE_URL}/complaints`, {
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

  const fetchWorkers = async () => {
    if (!user?.access_token) return;
    setWorkersLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/workers`, {
        headers: { Authorization: `Bearer ${user.access_token}` },
      });
      setWorkers(res.data);
    } catch (err) {
      console.error('Error fetching workers:', err);
    } finally {
      setWorkersLoading(false);
    }
  };

  const fetchUnassigned = async () => {
    if (!user?.access_token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/complaints`, {
        headers: { Authorization: `Bearer ${user.access_token}` },
        params: { status: 'Open', limit: 200 },
      });
      setUnassignedComplaints(res.data.filter(c => !c.assigned_to));
    } catch {}
  };

  const handleReassignAll = async () => {
    setReassignLoading(true);
    setReassignResult(null);
    try {
      const res = await axios.post(
        `${API_BASE_URL}/workers/reassign-unassigned`,
        {},
        { headers: { Authorization: `Bearer ${user.access_token}` } }
      );
      setReassignResult(res.data);
      fetchWorkers();
      fetchAllComplaints();
      fetchUnassigned();
    } catch (err) {
      setReassignResult({ message: err.response?.data?.detail || 'Re-assignment failed.' });
    } finally {
      setReassignLoading(false);
    }
  };

  const handleManualAssign = async (workerId, complaintId) => {
    if (!complaintId) return;
    try {
      await axios.post(
        `${API_BASE_URL}/workers/${workerId}/assign/${complaintId}`,
        {},
        { headers: { Authorization: `Bearer ${user.access_token}` } }
      );
      setWorkerActionMsg('Complaint assigned successfully!');
      setTimeout(() => setWorkerActionMsg(''), 3000);
      setAssignPanel(prev => { const n = { ...prev }; delete n[workerId]; return n; });
      fetchWorkers();
      fetchAllComplaints();
      fetchUnassigned();
    } catch (err) {
      setWorkerActionMsg(err.response?.data?.detail || 'Assignment failed.');
    }
  };

  const handleApproveWorker = async (workerId) => {
    try {
      await axios.patch(`${API_BASE_URL}/workers/${workerId}/approve`, {},
        { headers: { Authorization: `Bearer ${user.access_token}` } }
      );
      setWorkerActionMsg('Worker approved!');
      setTimeout(() => setWorkerActionMsg(''), 3000);
      fetchWorkers();
    } catch (err) {
      setWorkerActionMsg(err.response?.data?.detail || 'Approval failed.');
    }
  };

  const handleRejectWorker = async (workerId) => {
    if (!window.confirm('Permanently reject and delete this worker registration?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/workers/${workerId}/reject`, {
        headers: { Authorization: `Bearer ${user.access_token}` },
        data: { reason: 'Rejected by admin' },
      });
      setWorkerActionMsg('Registration rejected.');
      setTimeout(() => setWorkerActionMsg(''), 3000);
      fetchWorkers();
    } catch (err) {
      setWorkerActionMsg(err.response?.data?.detail || 'Rejection failed.');
    }
  };

  const updateComplaintStatus = async (complaintId, newStatus) => {
    setUpdateError(null);
    try {
      await axios.patch(
        `${API_BASE_URL}/complaints/${complaintId}/status`,
        { status: newStatus },
        {
          headers: {
            Authorization: `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      fetchAllComplaints();
    } catch (err) {
      console.error('Error updating status:', err);
      setUpdateError('Failed to update status. Please try again.');
      setTimeout(() => setUpdateError(null), 5000);
    }
  };

  const toggleSelect = (id) => setSelected(prev => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });
  const toggleSelectAll = () => {
    if (selected.size === complaints.length) setSelected(new Set());
    else setSelected(new Set(complaints.map(c => c._id)));
  };

  const handleBulkStatus = async () => {
    if (!selected.size) return;
    try {
      await axios.post(`${API_BASE_URL}/complaints/bulk/status`,
        { complaint_ids: [...selected], status: bulkStatus },
        { headers: { Authorization: `Bearer ${user.access_token}`, 'Content-Type': 'application/json' } }
      );
      setSelected(new Set()); setBulkModal(null); fetchAllComplaints();
    } catch (err) {
      setUpdateError(err.response?.data?.detail || 'Bulk update failed.');
      setTimeout(() => setUpdateError(null), 5000);
    }
  };

  const handleBulkTransfer = async () => {
    if (!selected.size || !bulkDept) return;
    try {
      await axios.post(`${API_BASE_URL}/complaints/bulk/transfer`,
        { complaint_ids: [...selected], new_department: bulkDept, reason: bulkReason || undefined },
        { headers: { Authorization: `Bearer ${user.access_token}`, 'Content-Type': 'application/json' } }
      );
      setSelected(new Set()); setBulkModal(null); setBulkReason(''); fetchAllComplaints();
    } catch (err) {
      setUpdateError(err.response?.data?.detail || 'Bulk transfer failed.');
      setTimeout(() => setUpdateError(null), 5000);
    }
  };

  const handleExportCSV = async () => {
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (departmentFilter !== 'all') params.department = departmentFilter;
      const r = await axios.get(`${API_BASE_URL}/complaints/export/csv`, {
        headers: { Authorization: `Bearer ${user.access_token}` },
        params,
        responseType: 'blob',
      });
      const url = URL.createObjectURL(new Blob([r.data], { type: 'text/csv' }));
      const a = document.createElement('a'); a.href = url; a.download = 'complaints.csv'; a.click();
      URL.revokeObjectURL(url);
    } catch { setUpdateError('Export failed.'); setTimeout(() => setUpdateError(null), 4000); }
  };

  const openTransferPanel = (complaintId, currentDept) => {
    const defaultDept = departments.find(d => d !== currentDept) || departments[0];
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
        `${API_BASE_URL}/complaints/${complaintId}/transfer`,
        { new_department: panel.dept, reason: panel.reason || undefined },
        {
          headers: {
            Authorization: `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      closeTransferPanel(complaintId);
      fetchAllComplaints();
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
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-sm sm:text-base text-gray-600">System-wide complaint management and oversight</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/triage-review" className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700">
            Open Triage Human Review
          </Link>
          <Link to="/analytics" className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700">
            <BarChart2 size={14} /> Analytics
          </Link>
          <Link to="/map" className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-600 text-white text-sm rounded-md hover:bg-teal-700">
            <Map size={14} /> Map View
          </Link>
          <Link to="/heatmap" className="inline-flex items-center gap-1.5 px-4 py-2 bg-orange-500 text-white text-sm rounded-md hover:bg-orange-600">
            <Flame size={14} /> Heatmap
          </Link>
          <button onClick={handleExportCSV} className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-600 text-white text-sm rounded-md hover:bg-slate-700">
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('complaints')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium ${
            activeTab === 'complaints' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <FileText size={14} /> Complaints
        </button>
        <button
          onClick={() => setActiveTab('workers')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium ${
            activeTab === 'workers' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <UserCheck size={14} /> Workers
          {workers.filter(w => !w.is_approved).length > 0 && (
            <span className="ml-1 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
              {workers.filter(w => !w.is_approved).length}
            </span>
          )}
        </button>
      </div>

      {/* Workers Tab */}
      {activeTab === 'workers' && (
        <div className="space-y-6">
          {workerActionMsg && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-800 text-sm">{workerActionMsg}</div>
          )}

          {/* Re-assign toolbar */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleReassignAll}
              disabled={reassignLoading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              <UserCheck size={14} />
              {reassignLoading ? 'Running…' : 'Re-assign All Unassigned Complaints'}
            </button>
            {reassignResult && (
              <span className="text-sm text-gray-700 bg-gray-100 px-3 py-1.5 rounded-md">
                ✅ Assigned: <strong>{reassignResult.assigned}</strong> &nbsp;·&nbsp;
                ⏭ Skipped: <strong>{reassignResult.skipped}</strong>
              </span>
            )}
          </div>

          {/* Pending Approvals */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 bg-red-50 border-b border-red-100">
              <h2 className="text-base font-semibold text-red-800 flex items-center gap-2">
                <UserCheck size={16} /> Pending Approvals ({workers.filter(w => !w.is_approved).length})
              </h2>
            </div>
            {workers.filter(w => !w.is_approved).length === 0 ? (
              <p className="p-6 text-gray-500 text-sm">No pending worker registrations.</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {workers.filter(w => !w.is_approved).map(w => (
                  <li key={w._id} className="px-6 py-4 flex items-center justify-between gap-4">
                    <div>
                      <p className="font-medium text-gray-900">{w.username}</p>
                      <p className="text-sm text-gray-500">{w.email} · {w.department}</p>
                      {w.service_area && (
                        <p className="text-xs text-gray-400 mt-1">
                          📍 {w.service_area.locality || `${w.service_area.lat?.toFixed(3)}, ${w.service_area.lon?.toFixed(3)}`} · {w.service_area.radius_km}km radius
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button onClick={() => handleApproveWorker(w._id)}
                        className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                        Approve
                      </button>
                      <button onClick={() => handleRejectWorker(w._id)}
                        className="px-3 py-1.5 bg-red-500 text-white text-sm rounded hover:bg-red-600">
                        Reject
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Active Workers */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h2 className="text-base font-semibold text-gray-900">Active Workers ({workers.filter(w => w.is_approved).length})</h2>
            </div>
            {workers.filter(w => w.is_approved).length === 0 ? (
              <p className="p-6 text-gray-500 text-sm">No approved workers yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {['Name', 'Department', 'Service Area', 'Status', 'Active Tasks', 'Actions'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {workers.filter(w => w.is_approved).map(w => {
                      const statusColor = { available: 'bg-green-100 text-green-800', busy: 'bg-yellow-100 text-yellow-800', offline: 'bg-gray-100 text-gray-600' };
                      const workerUnassigned = unassignedComplaints.filter(c => c.department === w.department);
                      return (
                        <tr key={w._id} className="hover:bg-gray-50 align-top">
                          <td className="px-4 py-3">
                            <p className="text-sm font-medium text-gray-900">{w.username}</p>
                            <p className="text-xs text-gray-500">{w.email}</p>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">{w.department}</td>
                          <td className="px-4 py-3 text-xs text-gray-500">
                            {w.service_area ? (
                              <>{w.service_area.locality || '—'}<br />{w.service_area.radius_km}km radius</>
                            ) : <span className="text-amber-600">⚠ No area set — matches all</span>}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[w.worker_status] || 'bg-gray-100 text-gray-600'}`}>
                              {w.worker_status || 'offline'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-indigo-700">{w.active_task_count || 0}</td>
                          <td className="px-4 py-3">
                            {w.worker_status === 'offline' ? (
                              <span className="text-xs text-gray-400">Worker offline</span>
                            ) : assignPanel[w._id] !== undefined ? (
                              <div className="flex flex-col gap-1.5 min-w-[200px]">
                                <select
                                  value={assignPanel[w._id]}
                                  onChange={e => setAssignPanel(prev => ({ ...prev, [w._id]: e.target.value }))}
                                  className="text-xs border border-gray-300 rounded px-2 py-1"
                                >
                                  <option value="">— pick complaint —</option>
                                  {workerUnassigned.map(c => (
                                    <option key={c._id} value={c._id}>
                                      [{c.priority}] {c.description?.slice(0, 50)}…
                                    </option>
                                  ))}
                                </select>
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => handleManualAssign(w._id, assignPanel[w._id])}
                                    disabled={!assignPanel[w._id]}
                                    className="px-2 py-1 bg-indigo-600 text-white text-xs rounded hover:bg-indigo-700 disabled:opacity-40"
                                  >
                                    Confirm
                                  </button>
                                  <button
                                    onClick={() => setAssignPanel(prev => { const n = { ...prev }; delete n[w._id]; return n; })}
                                    className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded hover:bg-gray-300"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <button
                                onClick={() => setAssignPanel(prev => ({ ...prev, [w._id]: '' }))}
                                disabled={workerUnassigned.length === 0}
                                className="px-3 py-1.5 bg-indigo-50 text-indigo-700 text-xs rounded border border-indigo-200 hover:bg-indigo-100 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
                              >
                                Assign Task {workerUnassigned.length > 0 ? `(${workerUnassigned.length} available)` : '(none)'}
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Complaints Tab */}
      {activeTab === 'complaints' && (
      <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4 mb-6 sm:mb-8">
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
        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <div className="flex items-center">
            <Building className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600" />
            <div className="ml-3 sm:ml-4">
              <p className="text-xl sm:text-2xl font-semibold">{departments.length}</p>
              <p className="text-xs sm:text-sm text-gray-600">Departments</p>
            </div>
          </div>
        </div>
      </div>

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
          
          <Building className="h-5 w-5 text-gray-400 hidden sm:block" />
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="w-full sm:w-auto border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          >
            <option value="all">All Departments</option>
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
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
          <p className="text-gray-600">No complaints match the selected filters</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between flex-wrap gap-3">
            <h2 className="text-lg font-medium text-gray-900">
              Showing {complaints.length} complaint{complaints.length !== 1 ? 's' : ''}
            </h2>
            {selected.size > 0 && (
              <div className="flex gap-2">
                <span className="text-sm text-slate-600">{selected.size} selected</span>
                <button onClick={() => { setBulkStatus('Resolved'); setBulkModal('status'); }}
                  className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">
                  Bulk Status
                </button>
                <button onClick={() => { setBulkDept(departments[0]); setBulkModal('transfer'); }}
                  className="px-3 py-1.5 bg-amber-500 text-white text-xs rounded hover:bg-amber-600">
                  Bulk Transfer
                </button>
                <button onClick={() => setSelected(new Set())}
                  className="px-3 py-1.5 bg-slate-200 text-slate-700 text-xs rounded hover:bg-slate-300">
                  Clear
                </button>
              </div>
            )}
          </div>
          <ul className="divide-y divide-gray-200">
            {complaints.map((complaint) => (
              <li key={complaint._id} className="hover:bg-gray-50">
                <div className="px-4 sm:px-6 py-4">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    {/* Row selector */}
                    <input
                      type="checkbox"
                      checked={selected.has(complaint._id)}
                      onChange={() => toggleSelect(complaint._id)}
                      className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                          <h3 className="text-base sm:text-lg font-medium text-gray-900 truncate">
                            {complaint.department}
                          </h3>
                          <div className="flex items-center gap-2 flex-wrap">
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
                      </div>
                      <p className="mt-2 text-sm text-gray-600">
                        <FormattedComplaintText text={complaint.description} />
                      </p>
                      <div className="mt-2 flex flex-col sm:flex-row sm:items-center text-sm text-gray-500 gap-2">
                        <div className="flex items-center">
                          <MapPin className="h-4 w-4 mr-1 shrink-0" />
                          <span className="truncate">{complaint.location?.address || 'Location not available'}</span>
                        </div>
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 sm:ml-4 mr-1 shrink-0" />
                          <span>{new Date(complaint.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center">
                          <Users className="h-4 w-4 sm:ml-4 mr-1 shrink-0" />
                          <span className="truncate">User ID: {complaint.user_id?.substring(0, 8)}...</span>
                        </div>
                      </div>
                      {complaint.ai_metadata && (
                        <div className="mt-2 text-xs text-gray-500">
                          AI Model: {complaint.ai_metadata.model_used} | 
                          Confidence: {(complaint.ai_metadata.confidence_score * 100).toFixed(1)}%
                        </div>
                      )}
                      {/* Assigned worker */}
                      {complaint.assigned_to && (() => {
                        const w = workers.find(x => x._id === complaint.assigned_to);
                        return (
                          <div className="mt-1 text-xs text-indigo-700 font-medium flex items-center gap-1">
                            <UserCheck size={12} />
                            Assigned to: {w ? w.username : complaint.assigned_to.slice(0, 8) + '…'}
                          </div>
                        );
                      })()}
                      <ComplaintComments complaintId={complaint._id} currentRole="admin" />

                      {/* Admin Action Buttons */}
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
                        {complaint.status === 'Rejected' && (
                          <button
                            onClick={() => updateComplaintStatus(complaint._id, 'Open')}
                            className="px-3 py-1.5 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 touch-manipulation"
                          >
                            Reopen
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
                              {departments
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
                      <div className="ml-4">
                        <img
                          src={`${STATIC_BASE_URL}/${complaint.image_url.replace(/^\//,'')}`}
                          alt="Complaint"
                          className="h-32 w-32 object-cover rounded cursor-pointer"
                          onClick={() => window.open(`${STATIC_BASE_URL}/${complaint.image_url.replace(/^\//,'')}`, '_blank')}
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

      {/* Bulk Status Modal */}
      {bulkModal === 'status' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80 space-y-4">
            <h3 className="font-semibold text-slate-800">Bulk Status Update</h3>
            <p className="text-sm text-slate-500">Updating {selected.size} complaint(s)</p>
            <select
              value={bulkStatus}
              onChange={e => setBulkStatus(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            >
              {['Open', 'In Progress', 'Resolved', 'Rejected'].map(s => <option key={s}>{s}</option>)}
            </select>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setBulkModal(null)} className="px-4 py-2 text-sm bg-slate-100 rounded-lg hover:bg-slate-200">Cancel</button>
              <button onClick={handleBulkStatus} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">Apply</button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Transfer Modal */}
      {bulkModal === 'transfer' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-96 space-y-4">
            <h3 className="font-semibold text-slate-800">Bulk Transfer</h3>
            <p className="text-sm text-slate-500">Transferring {selected.size} complaint(s)</p>
            <select
              value={bulkDept}
              onChange={e => setBulkDept(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            >
              {departments.map(d => <option key={d}>{d}</option>)}
            </select>
            <input
              value={bulkReason}
              onChange={e => setBulkReason(e.target.value)}
              placeholder="Reason (optional)"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setBulkModal(null)} className="px-4 py-2 text-sm bg-slate-100 rounded-lg hover:bg-slate-200">Cancel</button>
              <button onClick={handleBulkTransfer} disabled={!bulkDept} className="px-4 py-2 text-sm bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50">Transfer</button>
            </div>
          </div>
        </div>
      )}
      </>
      )}
    </div>
  );
};

export default AdminDashboard;
