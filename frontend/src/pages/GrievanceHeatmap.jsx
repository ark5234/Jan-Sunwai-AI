import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useAuth } from '../context/AuthContext';

// Fix for leaflet-heat in Vite
window.L = window.L || L;
import 'leaflet.heat/dist/leaflet-heat.js';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DEPARTMENTS = [
  'All',
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
const STATUSES = ['All', 'Open', 'In Progress', 'Resolved'];

const DEPT_COLORS = {
  'Civil Department': '#ef4444',
  'Health Department': '#10b981',
  'Electrical Department': '#f59e0b',
  'Horticulture': '#14b8a6',
  'IT Department': '#3b82f6',
  'Commercial': '#8b5cf6',
  'Enforcement': '#374151',
  'VBD Department': '#ec4899',
  'EBR Department': '#f97316',
  'Fire Department': '#dc2626',
  'Uncategorized': '#6b7280',
};

// Leaflet heatmap layer component
function HeatLayer({ points }) {
  const map = useMap();
  const heatRef = useRef(null);

  useEffect(() => {
    if (heatRef.current) {
      map.removeLayer(heatRef.current);
    }
    const data = points.map(p => [p.lat, p.lon, p.count]);
    if (data.length > 0) {
      heatRef.current = L.heatLayer(data, {
        radius: 35,
        blur: 20,
        maxZoom: 12,
        gradient: { 0.2: '#93c5fd', 0.5: '#fde047', 0.8: '#f97316', 1.0: '#ef4444' },
      }).addTo(map);
    }
    return () => {
      if (heatRef.current) map.removeLayer(heatRef.current);
    };
  }, [points, map]);

  return null;
}

// Circle markers for individual points
function CircleMarkers({ points, selectedDept }) {
  const map = useMap();
  const layersRef = useRef([]);

  useEffect(() => {
    layersRef.current.forEach(l => map.removeLayer(l));
    layersRef.current = [];

    points.forEach(p => {
      const color = DEPT_COLORS[p.department] || '#6b7280';
      const circle = L.circleMarker([p.lat, p.lon], {
        radius: Math.min(6 + p.count * 2, 18),
        color: 'white', weight: 1.5,
        fillColor: color, fillOpacity: 0.85,
      }).addTo(map);
      circle.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:160px">
          <div style="font-weight:700;color:${color};margin-bottom:4px">${p.department}</div>
          <div style="font-size:0.85rem;color:#334155">${p.count} complaint${p.count !== 1 ? 's' : ''}</div>
          <div style="font-size:0.78rem;color:#94a3b8;margin-top:2px">${p.lat.toFixed(4)}, ${p.lon.toFixed(4)}</div>
        </div>
      `);
      layersRef.current.push(circle);
    });

    return () => layersRef.current.forEach(l => map.removeLayer(l));
  }, [points, map]);

  return null;
}

export default function GrievanceHeatmap() {
  const { user } = useAuth();
  const [points, setPoints] = useState([]);
  const [department, setDepartment] = useState('All');
  const [status, setStatus] = useState('All');
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('heat'); // 'heat' | 'circles'

  const headers = { Authorization: `Bearer ${user?.access_token}` };

  const fetchHeatmap = async () => {
    if (!user?.access_token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (department !== 'All') params.set('department', department);
      if (status !== 'All') params.set('status', status);
      const res = await fetch(`${API}/analytics/heatmap?${params}`, { headers });
      if (!res.ok) throw new Error('Failed to fetch heatmap data');
      const data = await res.json();
      const validPoints = (data.points || []).filter(p => p.lat != null && p.lon != null);
      setPoints(validPoints);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHeatmap(); }, [department, status]);

  // Top hotspots
  const topSpots = [...points].sort((a, b) => b.count - a.count).slice(0, 8);

  // Total by department (for legend)
  const deptTotals = points.reduce((acc, p) => {
    acc[p.department] = (acc[p.department] || 0) + p.count;
    return acc;
  }, {});
  const deptEntries = Object.entries(deptTotals).sort((a, b) => b[1] - a[1]);

  const mapCenter = points.length > 0
    ? [points.reduce((s, p) => s + p.lat, 0) / points.length, points.reduce((s, p) => s + p.lon, 0) / points.length]
    : [20.5937, 78.9629];

  return (
    <div className="gh-page">
      {/* Header */}
      <div className="gh-header">
        <div>
          <h1>🗺️ Grievance Heatmap</h1>
          <p>Geographic distribution of complaints — click markers for details</p>
        </div>
        <div className="gh-header-controls">
          <div className="gh-view-toggle">
            <button className={viewMode === 'heat' ? 'active' : ''} onClick={() => setViewMode('heat')}>🔥 Heatmap</button>
            <button className={viewMode === 'circles' ? 'active' : ''} onClick={() => setViewMode('circles')}>⭕ Markers</button>
          </div>
        </div>
      </div>

      <div className="gh-layout">
        {/* Left Sidebar */}
        <div className="gh-sidebar">
          <div className="gh-filters">
            <h3>Filters</h3>
            <div className="gh-filter-group">
              <label>Department</label>
              <select value={department} onChange={e => setDepartment(e.target.value)}>
                {DEPARTMENTS.map(d => <option key={d}>{d}</option>)}
              </select>
            </div>
            <div className="gh-filter-group">
              <label>Status</label>
              <select value={status} onChange={e => setStatus(e.target.value)}>
                {STATUSES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="gh-stats-mini">
              <span className="gh-total">{points.reduce((s, p) => s + p.count, 0)}</span>
              <span className="gh-total-label">Total complaints plotted</span>
            </div>
          </div>

          {/* Department Breakdown */}
          {deptEntries.length > 0 && (
            <div className="gh-dept-breakdown">
              <h3>By Department</h3>
              {deptEntries.map(([dept, count]) => (
                <div key={dept} className="gh-dept-row">
                  <span className="gh-dept-dot" style={{ background: DEPT_COLORS[dept] || '#6b7280' }} />
                  <span className="gh-dept-name">{dept}</span>
                  <span className="gh-dept-count">{count}</span>
                </div>
              ))}
            </div>
          )}

          {/* Gradient legend */}
          <div className="gh-legend">
            <h3>Intensity</h3>
            <div className="gh-gradient-bar" />
            <div className="gh-gradient-labels">
              <span>Low</span><span>High</span>
            </div>
          </div>

          {/* Top Hotspots */}
          {topSpots.length > 0 && (
            <div className="gh-hotspots">
              <h3>🔥 Top Hotspots</h3>
              {topSpots.map((p, i) => (
                <div key={i} className="gh-hotspot-row">
                  <span className="gh-hotspot-rank">#{i + 1}</span>
                  <div className="gh-hotspot-info">
                    <span style={{ color: DEPT_COLORS[p.department] || '#6b7280', fontWeight: 700, fontSize: '0.8rem' }}>{p.department}</span>
                    <span style={{ fontSize: '0.73rem', color: '#94a3b8' }}>{p.lat.toFixed(3)}°, {p.lon.toFixed(3)}°</span>
                  </div>
                  <span className="gh-hotspot-count">{p.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Map */}
        <div className="gh-map-container">
          {loading && (
            <div className="gh-map-overlay">
              <div className="gh-spinner" />
              <span>Loading heatmap data…</span>
            </div>
          )}
          {points.length === 0 && !loading && (
            <div className="gh-map-overlay">
              <span style={{ fontSize: '2rem' }}>📍</span>
              <span>No complaints with geo data for these filters</span>
            </div>
          )}
          <MapContainer
            center={mapCenter}
            zoom={5}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {viewMode === 'heat' && <HeatLayer points={points} />}
            {viewMode === 'circles' && <CircleMarkers points={points} />}
          </MapContainer>
        </div>
      </div>

      <style>{`
        .gh-page {
          min-height: 100vh;
          background: #f8fafc;
          font-family: 'Inter', sans-serif;
          display: flex;
          flex-direction: column;
          padding: 1.5rem;
          gap: 1.5rem;
        }
        .gh-header {
          display: flex; align-items: center; justify-content: space-between;
          background: white; border-radius: 16px;
          padding: 1.2rem 1.8rem;
          box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .gh-header h1 { margin: 0; font-size: 1.4rem; font-weight: 800; color: #1e293b; }
        .gh-header p { margin: 2px 0 0; color: #64748b; font-size: 0.87rem; }
        .gh-view-toggle {
          display: flex; border-radius: 10px; overflow: hidden;
          border: 1px solid #e2e8f0;
        }
        .gh-view-toggle button {
          padding: 8px 16px; border: none; background: white;
          color: #64748b; font-size: 0.85rem; font-weight: 600; cursor: pointer;
          transition: all 0.2s;
        }
        .gh-view-toggle button.active { background: #6366f1; color: white; }

        .gh-layout { display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; flex: 1; min-height: 0; }

        .gh-sidebar {
          display: flex; flex-direction: column; gap: 1.5rem; overflow-y: auto;
        }
        .gh-filters, .gh-dept-breakdown, .gh-legend, .gh-hotspots {
          background: white; border-radius: 16px; padding: 1.2rem 1.4rem;
          box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .gh-filters h3, .gh-dept-breakdown h3, .gh-legend h3, .gh-hotspots h3 {
          margin: 0 0 1rem; font-size: 0.9rem; font-weight: 700; color: #1e293b;
        }
        .gh-filter-group { margin-bottom: 1rem; }
        .gh-filter-group label { display: block; font-size: 0.78rem; font-weight: 600; color: #64748b; margin-bottom: 5px; }
        .gh-filter-group select {
          width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0;
          border-radius: 8px; font-size: 0.87rem; color: #334155; outline: none;
          background: #f8fafc; cursor: pointer;
        }
        .gh-stats-mini { text-align: center; margin-top: 1rem; }
        .gh-total { display: block; font-size: 2rem; font-weight: 800; color: #6366f1; }
        .gh-total-label { font-size: 0.78rem; color: #94a3b8; }

        .gh-dept-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
        .gh-dept-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
        .gh-dept-name { flex: 1; font-size: 0.82rem; color: #475569; font-weight: 500; }
        .gh-dept-count { font-size: 0.82rem; font-weight: 700; color: #1e293b; }

        .gh-gradient-bar {
          height: 12px; border-radius: 6px;
          background: linear-gradient(90deg, #93c5fd, #fde047, #f97316, #ef4444);
          margin-bottom: 6px;
        }
        .gh-gradient-labels { display: flex; justify-content: space-between; font-size: 0.76rem; color: #94a3b8; }

        .gh-hotspot-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .gh-hotspot-rank { width: 22px; height: 22px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; color: #64748b; flex-shrink: 0; }
        .gh-hotspot-info { flex: 1; display: flex; flex-direction: column; }
        .gh-hotspot-count { font-size: 0.9rem; font-weight: 800; color: #1e293b; }

        .gh-map-container {
          position: relative; border-radius: 16px; overflow: hidden;
          box-shadow: 0 4px 16px rgba(0,0,0,0.1);
          min-height: 520px;
        }
        .gh-map-overlay {
          position: absolute; inset: 0; z-index: 500;
          background: rgba(248,250,252,0.85); backdrop-filter: blur(4px);
          display: flex; flex-direction: column;
          align-items: center; justify-content: center; gap: 1rem;
          color: #64748b; font-size: 0.95rem; font-weight: 600;
        }
        .gh-spinner {
          width: 36px; height: 36px; border: 4px solid #e5e7eb;
          border-top-color: #6366f1; border-radius: 50%;
          animation: ghspin 0.8s linear infinite;
        }
        @keyframes ghspin { to { transform: rotate(360deg); } }

        @media (max-width: 900px) {
          .gh-layout { grid-template-columns: 1fr; }
          .gh-sidebar { flex-direction: row; flex-wrap: wrap; }
          .gh-filters, .gh-dept-breakdown { flex: 1; min-width: 200px; }
        }
      `}</style>
    </div>
  );
}
