import { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
          image: item.id || item.image,
          decision,
          corrected_label: item.final_label,
          note: 'Reviewed in admin panel'
        },
        {
          headers: {
            Authorization: `Bearer ${user.access_token}`
          }
        }
      );
      setItems(prev => prev.filter(row => (row.id || row.image) !== (item.id || item.image)));
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
      <p className="text-gray-600 mb-6">Images where the AI confidence was below 65% — approve the suggested label or reject it to flag for retraining.</p>

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
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Label</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rationale</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item) => {
                  const confidencePct = item.confidence != null
                    ? `${(parseFloat(item.confidence) * 100).toFixed(0)}%`
                    : '—';
                  const confidenceColor = parseFloat(item.confidence) >= 0.5
                    ? 'text-amber-600'
                    : 'text-red-600';
                  return (
                    <tr key={item.image}>
                      <td className="px-4 py-3 text-xs text-gray-500 break-all max-w-xs">
                        {item.image?.split(/[\\/]/).pop() || item.image}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-800">{item.final_label || '—'}</td>
                      <td className={`px-4 py-3 text-sm font-semibold ${confidenceColor}`}>{confidencePct}</td>
                      <td className="px-4 py-3 text-xs text-gray-500 max-w-sm">{item.rationale || item.vision_summary || '—'}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2 min-w-45">
                          <button
                            onClick={() => submitDecision(item, 'approve')}
                            className="px-3 h-11 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => submitDecision(item, 'reject')}
                            className="px-3 h-11 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default TriageReview;
