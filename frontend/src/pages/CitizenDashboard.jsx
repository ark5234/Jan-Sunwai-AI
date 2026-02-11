import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { FileText, MapPin, Calendar, AlertCircle } from 'lucide-react';
import axios from 'axios';

const CitizenDashboard = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMyComplaints();
  }, []);

  const fetchMyComplaints = async () => {
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
      setError('Failed to load complaints');
    } finally {
      setLoading(false);
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
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">My Complaints</h1>
        <p className="mt-2 text-sm sm:text-base text-gray-600">Track and manage your submitted complaints</p>
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
            <AlertCircle className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-600" />
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
            <AlertCircle className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
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
            <AlertCircle className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
            <div className="ml-3 sm:ml-4">
              <p className="text-xl sm:text-2xl font-semibold">
                {complaints.filter(c => c.status === 'Resolved').length}
              </p>
              <p className="text-xs sm:text-sm text-gray-600">Resolved</p>
            </div>
          </div>
        </div>
      </div>

      {/* New Complaint Button */}
      <div className="mb-6">
        <Link
          to="/analyze"
          className="inline-flex items-center px-4 py-2.5 sm:py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 w-full sm:w-auto justify-center"
        >
          <FileText className="h-5 w-5 mr-2" />
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
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(complaint.status)} whitespace-nowrap inline-block self-start sm:self-center`}>
                          {complaint.status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-gray-600 line-clamp-3">
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
                    </div>
                    {complaint.image_url && (
                      <div className="sm:ml-4 flex-shrink-0">
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
