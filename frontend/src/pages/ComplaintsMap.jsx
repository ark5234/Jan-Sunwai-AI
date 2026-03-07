import { useState, useEffect, useCallback } from "react";
import { MapPin, Filter, RefreshCw } from "lucide-react";
import Map, { Source, Layer, Popup, NavigationControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import api from "../context/api";

// Map tile source:
// - Set VITE_MAPPLS_API_KEY in frontend/.env for official GoI-compliant
//   MapmyIndia/Mappls tiles (free tier at https://developer.mappls.com)
//   → shows official Survey of India boundaries for J&K, Ladakh, etc.
// - Falls back to CARTO Voyager (English labels, full India coverage, no key needed)
const MAPPLS_KEY = import.meta.env.VITE_MAPPLS_API_KEY;
const MAP_STYLE = MAPPLS_KEY
  ? `https://apis.mappls.com/advancedmaps/v1/${MAPPLS_KEY}/map_sdk_library/`
  : {
      version: 8,
      sources: {
        carto: {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          maxzoom: 19,
          attribution:
            '\u00a9 <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors \u00a9 <a href="https://carto.com/attributions">CARTO</a>',
        },
      },
      layers: [{ id: 'carto', type: 'raster', source: 'carto' }],
    };

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

const DEFAULT_CENTER = { longitude: 78.9629, latitude: 20.5937, zoom: 4.5 };

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
  const [popupInfo, setPopupInfo] = useState(null); // {longitude, latitude, ...props}
  const [cursor, setCursor] = useState("grab");
  const [satellite, setSatellite] = useState(false);

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

  const geojson = {
    type: "FeatureCollection",
    features: visible.map((c) => {
      const ll = parseLatLng(c.location);
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [ll[1], ll[0]] },
        properties: {
          id: c._id,
          status: c.status,
          priority: c.priority,
          department: c.department,
          created_at: c.created_at,
          colour:
            colorBy === "priority"
              ? PRIORITY_COLOR[c.priority] || "#64748b"
              : STATUS_COLOR[c.status] || "#64748b",
        },
      };
    }),
  };

  const circleLayer = {
    id: "complaints-circles",
    type: "circle",
    paint: {
      "circle-radius": 7,
      "circle-color": ["get", "colour"],
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1.5,
      "circle-opacity": 0.88,
    },
  };

  const handleMapClick = useCallback((e) => {
    const features = e.features;
    if (features && features.length > 0) {
      const f = features[0];
      setPopupInfo({
        longitude: e.lngLat.lng,
        latitude: e.lngLat.lat,
        ...f.properties,
      });
    } else {
      setPopupInfo(null);
    }
  }, []);

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

          {/* Satellite toggle */}
          <button
            onClick={() => setSatellite((s) => !s)}
            title={satellite ? "Switch to Street view" : "Switch to Satellite view"}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs transition-colors ${
              satellite
                ? "bg-slate-800 border-slate-700 text-white"
                : "border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Layers size={13} />
            {satellite ? "Satellite" : "Street"}
          </button>

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
          <div className="absolute inset-0 bg-white/60 flex items-center justify-center z-10">
            <div className="animate-spin h-8 w-8 rounded-full border-b-2 border-blue-600" />
          </div>
        )}

        <Map
          mapStyle={satellite ? SATELLITE_STYLE : STREET_STYLE}
          initialViewState={DEFAULT_CENTER}
          maxBounds={[[67.0, 6.0], [98.0, 38.0]]}
          style={{ width: "100%", height: "100%" }}
          interactiveLayerIds={["complaints-circles"]}
          cursor={cursor}
          onClick={handleMapClick}
          onMouseEnter={() => setCursor("pointer")}
          onMouseLeave={() => setCursor("grab")}
        >
          <NavigationControl position="top-right" />

          <Source id="complaints" type="geojson" data={geojson}>
            <Layer {...circleLayer} />
          </Source>

          {popupInfo && (
            <Popup
              longitude={popupInfo.longitude}
              latitude={popupInfo.latitude}
              onClose={() => setPopupInfo(null)}
              closeOnClick={false}
              offset={12}
            >
              <div className="text-xs space-y-0.5 min-w-[160px] p-1">
                <p className="font-semibold text-sm">{popupInfo.department}</p>
                <p>Status: <span className="font-medium">{popupInfo.status}</span></p>
                {popupInfo.priority && (
                  <p>Priority: <span className="font-medium">{popupInfo.priority}</span></p>
                )}
                <p className="text-slate-400">
                  {new Date(popupInfo.created_at).toLocaleDateString()}
                </p>
              </div>
            </Popup>
          )}
        </Map>
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
