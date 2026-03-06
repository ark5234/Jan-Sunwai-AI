import { useState, useEffect } from "react";
import { MapPin, Filter, RefreshCw } from "lucide-react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import api from "../context/api";

const STATUS_COLOR = {
  Open: "#3b82f6",
  "In Progress": "#f59e0b",
  Resolved: "#22c55e",
  Rejected: "#ef4444",
};

const PRIORITY_COLOR = {
  Critical: "#dc2626",
  High: "#ea580c",
  Medium: "#ca8a04",
  Low: "#16a34a",
};

const DEFAULT_CENTER = [20.5937, 78.9629]; // centre of India

function parseLatLng(location) {
  if (!location) return null;
  // Support "lat,lng" string or {lat, lng} object
  if (typeof location === "string") {
    const parts = location.split(",").map((s) => parseFloat(s.trim()));
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1]))
      return [parts[0], parts[1]];
  }
  if (typeof location === "object") {
    const lat = parseFloat(location.lat ?? location.latitude);
    const lng = parseFloat(location.lng ?? location.lon ?? location.longitude);
    if (!isNaN(lat) && !isNaN(lng)) return [lat, lng];
  }
  return null;
}

export default function ComplaintsMap() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [colorBy, setColorBy] = useState("status"); // "status" | "priority"
  const [statusFilter, setStatusFilter] = useState("All");

  const fetchComplaints = () => {
    setLoading(true);
    api
      .get("/complaints", { params: { limit: 500 } })
      .then((r) => setComplaints(r.data))
      .catch(() => setError("Failed to load complaints."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const visible = complaints.filter((c) => {
    const hasGeo = parseLatLng(c.location);
    if (!hasGeo) return false;
    if (statusFilter !== "All" && c.status !== statusFilter) return false;
    return true;
  });

  const mapped = visible.length;
  const total = complaints.length;
  const noGeo = total - complaints.filter((c) => parseLatLng(c.location)).length;

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Toolbar */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex flex-wrap items-center gap-3">
        <h1 className="text-lg font-bold text-slate-800 flex items-center gap-2">
          <MapPin size={20} className="text-blue-600" />
          Complaints Map
        </h1>

        <div className="flex items-center gap-2 ml-auto">
          {/* Color-by toggle */}
          <div className="flex items-center gap-1 border border-slate-200 rounded-lg p-1 text-xs">
            {["status", "priority"].map((opt) => (
              <button
                key={opt}
                onClick={() => setColorBy(opt)}
                className={`px-2.5 py-1 rounded capitalize transition-colors ${
                  colorBy === opt
                    ? "bg-blue-600 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <Filter size={13} className="text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-slate-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
            >
              {["All", "Open", "In Progress", "Resolved", "Rejected"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>

          <button
            onClick={fetchComplaints}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-500"
            title="Refresh"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {/* Stats bar */}
        <div className="w-full text-xs text-slate-500">
          Showing <strong>{mapped}</strong> complaints with location ·{" "}
          <span className="text-orange-500">{noGeo} without GPS data</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Map */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 bg-white/60 flex items-center justify-center z-[1000]">
            <div className="animate-spin h-8 w-8 rounded-full border-b-2 border-blue-600" />
          </div>
        )}

        <MapContainer
          center={DEFAULT_CENTER}
          zoom={5}
          className="h-full w-full"
          style={{ zIndex: 0 }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {visible.map((c) => {
            const latlng = parseLatLng(c.location);
            if (!latlng) return null;
            const colour =
              colorBy === "priority"
                ? PRIORITY_COLOR[c.priority] || "#64748b"
                : STATUS_COLOR[c.status] || "#64748b";

            return (
              <CircleMarker
                key={c._id}
                center={latlng}
                radius={7}
                pathOptions={{
                  color: "#fff",
                  weight: 1.5,
                  fillColor: colour,
                  fillOpacity: 0.85,
                }}
              >
                <Popup>
                  <div className="text-xs space-y-0.5 min-w-[160px]">
                    <p className="font-semibold text-sm">{c.department}</p>
                    <p>
                      Status:{" "}
                      <span className="font-medium">{c.status}</span>
                    </p>
                    {c.priority && (
                      <p>
                        Priority:{" "}
                        <span className="font-medium">{c.priority}</span>
                      </p>
                    )}
                    <p className="text-slate-400">
                      {new Date(c.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="bg-white border-t border-slate-200 px-4 py-2 flex flex-wrap gap-4 text-xs text-slate-600">
        {colorBy === "status"
          ? Object.entries(STATUS_COLOR).map(([label, colour]) => (
              <span key={label} className="flex items-center gap-1.5">
                <span
                  className="inline-block w-3 h-3 rounded-full"
                  style={{ background: colour }}
                />
                {label}
              </span>
            ))
          : Object.entries(PRIORITY_COLOR).map(([label, colour]) => (
              <span key={label} className="flex items-center gap-1.5">
                <span
                  className="inline-block w-3 h-3 rounded-full"
                  style={{ background: colour }}
                />
                {label}
              </span>
            ))}
      </div>
    </div>
  );
}
