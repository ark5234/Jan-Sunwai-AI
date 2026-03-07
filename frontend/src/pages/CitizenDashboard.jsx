import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { FileText, MapPin, Calendar, AlertCircle, PlusCircle, Clock, CheckCircle2, Star, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import SLABadge from '../components/SLABadge';
import ComplaintComments from '../components/ComplaintComments';

// Inline star-rating feedback widget
function FeedbackWidget({ complaintId, token, onSubmitted }) {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async () => {
    if (!rating) return;
    setSubmitting(true);
    try {
      await axios.post(
        `http://localhost:8000/complaints/${complaintId}/feedback`,
        { rating, comment: comment.trim() || undefined },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setDone(true);
      onSubmitted?.();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to submit feedback.');
    } finally {
      setSubmitting(false);
    }
  };

  if (done)
    return (
      <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
        <CheckCircle2 size={13} /> Thank you for your feedback!
      </p>
    );

  return (
    <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
      <p className="text-xs font-semibold text-green-800 mb-2">Rate this resolution</p>
      <div className="flex gap-1 mb-2">
        {[1, 2, 3, 4, 5].map((s) => (
          <button
            key={s}
            onMouseEnter={() => setHover(s)}
            onMouseLeave={() => setHover(0)}
            onClick={() => setRating(s)}
            className="focus:outline-none"
          >
            <Star
              size={20}
              className={s <= (hover || rating) ? 'text-yellow-400 fill-yellow-400' : 'text-slate-300'}
            />
          </button>
        ))}
      </div>
      <input
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Optional comment…"
        maxLength={500}
        className="w-full text-xs border border-slate-200 rounded px-2 py-1.5 mb-2 focus:outline-none focus:ring-1 focus:ring-green-400"
      />
      <button
        onClick={handleSubmit}
        disabled={!rating || submitting}
        className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700 disabled:opacity-50"
      >
        {submitting ? 'Submitting…' : 'Submit Feedback'}
      </button>
    </div>
  );
}

const CitizenDashboard = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user?.access_token) {
      fetchMyComplaints();
    }
  }, [user]);

  const fetchMyComplaints = async () => {
    if (!user?.access_token) return;
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/complaints', {
        headers: {
          Authorization: `Bearer ${user.access_token}`
        }
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'Open':
        return 'bg-blue-50 text-primary border border-blue-200';
      case 'In Progress':
        return 'bg-amber-50 text-saffron border border-amber-200';
      case 'Resolved':
        return 'bg-green-50 text-success border border-green-200';
      case 'Rejected':
        return 'bg-red-50 text-danger border border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border border-gray-200';
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
        <h1 className="govt-heading text-2xl sm:text-3xl text-gray-900">My Complaints</h1>
        <p className="mt-2 text-sm text-gray-600">Track and manage your submitted grievances</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-primary/10 rounded">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">{complaints.length}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
          </div>
        </div>
        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-saffron/10 rounded">
              <AlertCircle className="h-5 w-5 text-saffron" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">
                {complaints.filter(c => c.status === 'Open').length}
              </p>
              <p className="text-xs text-gray-500">Open</p>
            </div>
          </div>
        </div>
        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-blue-50 rounded">
              <Clock className="h-5 w-5 text-primary" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">
                {complaints.filter(c => c.status === 'In Progress').length}
              </p>
              <p className="text-xs text-gray-500">In Progress</p>
            </div>
          </div>
        </div>
        <div className="stat-card bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center">
            <div className="p-2 bg-green-50 rounded">
              <CheckCircle2 className="h-5 w-5 text-success" />
            </div>
            <div className="ml-3">
              <p className="text-xl font-bold text-gray-900">
                {complaints.filter(c => c.status === 'Resolved').length}
              </p>
              <p className="text-xs text-gray-500">Resolved</p>
            </div>
          </div>
        </div>
      </div>

      {/* New Complaint Button */}
      <div className="mb-6">
        <Link
          to="/analyze"
          className="inline-flex items-center px-5 py-2.5 rounded text-sm font-semibold text-white bg-saffron hover:bg-saffron-light transition shadow-sm w-full sm:w-auto justify-center"
        >
          <PlusCircle className="h-4 w-4 mr-2" />
          File New Complaint
        </Link>
      </div>

      {/* Complaints List */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {complaints.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No complaints yet</h3>
          <p className="text-gray-600 mb-6">Start by filing your first complaint</p>
          <Link
            to="/analyze"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            File Complaint
          </Link>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <ul className="divide-y divide-gray-200">
            {complaints.map((complaint) => (
              <li key={complaint._id} className="hover:bg-gray-50">
                <div className="px-4 sm:px-6 py-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <h3 className="text-base sm:text-lg font-medium text-gray-900 truncate">
                          {complaint.department}
                        </h3>
                        <div className="flex items-center gap-2 flex-wrap self-start sm:self-center">
                          {complaint.priority && (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              { Critical: 'bg-red-100 text-red-700', High: 'bg-orange-100 text-orange-700',
                                Medium: 'bg-yellow-100 text-yellow-700', Low: 'bg-green-100 text-green-700' }
                              [complaint.priority] || 'bg-slate-100 text-slate-600'
                            }`}>
                              {complaint.priority}
                            </span>
                          )}
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(complaint.status)} whitespace-nowrap`}>
                            {complaint.status}
                          </span>
                          <SLABadge
                            createdAt={complaint.created_at}
                            department={complaint.department}
                            status={complaint.status}
                            updatedAt={complaint.updated_at}
                          />
                        </div>
                      </div>
                      <p className="mt-2 text-sm text-gray-600 line-clamp-3">
                        {complaint.description}
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
                      </div>
                      {complaint.ai_metadata && (
                        <div className="mt-2 text-xs text-gray-500">
                          Confidence: {(complaint.ai_metadata.confidence_score * 100).toFixed(1)}%
                        </div>
                      )}
                      {complaint.is_duplicate && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-amber-600">
                          <AlertTriangle size={12} />
                          Possible duplicate of an existing complaint
                        </div>
                      )}
                      {/* Star feedback for resolved complaints */}
                      {complaint.status === 'Resolved' && !complaint.feedback && (
                        <FeedbackWidget
                          complaintId={complaint._id}
                          token={user.access_token}
                          onSubmitted={fetchMyComplaints}
                        />
                      )}
                      {complaint.feedback && (
                        <div className="mt-2 flex items-center gap-1">
                          {[1,2,3,4,5].map(s => (
                            <Star key={s} size={14}
                              className={s <= complaint.feedback.rating ? 'text-yellow-400 fill-yellow-400' : 'text-slate-200'}
                            />
                          ))}
                          {complaint.feedback.comment && (
                            <span className="text-xs text-slate-500 ml-1">"{complaint.feedback.comment}"</span>
                          )}
                        </div>
                      )}
                      <ComplaintComments complaintId={complaint._id} currentRole="citizen" />
                    </div>
                    {complaint.image_url && (
                      <div className="sm:ml-4 shrink-0">
                        <img
                          src={`http://localhost:8000/${complaint.image_url}`}
                          alt="Complaint"
                          className="h-24 w-24 sm:h-20 sm:w-20 object-cover rounded"
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

export default CitizenDashboard;
