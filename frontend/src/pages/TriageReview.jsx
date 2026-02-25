import { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const API_BASE = 'http://localhost:8000';

const TriageReview = () => {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/triage/review-queue`, {
        headers: {
          Authorization: `Bearer ${user.access_token}`
        }
      });
      setItems(response.data.items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load review queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const submitDecision = async (item, decision) => {
    try {
      await axios.post(
        `${API_BASE}/triage/review-queue/decision`,
        {
          image: item.image,
          decision,
          corrected_label: decision === 'reject' ? item.clip_top_label : item.llava_label,
          note: 'Reviewed in admin panel'
        },
        {
          headers: {
            Authorization: `Bearer ${user.access_token}`
          }
        }
      );
      setItems(prev => prev.filter(row => row.image !== item.image));
    } catch (err) {
      setError('Failed to save review decision');
    }
  };

  if (loading) {
    return <div className="p-6">Loading triage review queue...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Triage Human Review</h1>
      <p className="text-gray-600 mb-6">Review uncertain AI labels and approve or reject quickly.</p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-red-800">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-600">
          No pending review items.
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Image</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vision Model</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Label</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {items.map((item) => (
                <tr key={item.image}>
                  <td className="px-4 py-3 text-sm text-gray-700 break-all">{item.image}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.clip_top_label || item.vision_summary || '—'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.llava_label || item.ai_label || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => submitDecision(item, 'approve')}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => submitDecision(item, 'reject')}
                        className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TriageReview;
