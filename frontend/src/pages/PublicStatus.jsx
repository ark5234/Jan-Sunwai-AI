import { useState, useEffect } from "react";
import { Search, Filter, Globe } from "lucide-react";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STATUS_BADGE = {
  Open: "bg-blue-100 text-blue-700",
  "In Progress": "bg-yellow-100 text-yellow-700",
  Resolved: "bg-green-100 text-green-700",
  Rejected: "bg-red-100 text-red-600",
};

const PRIORITY_BADGE = {
  Critical: "bg-red-100 text-red-700",
  High: "bg-orange-100 text-orange-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Low: "bg-green-100 text-green-700",
};

function formatDate(ts) {
  if (!ts) return "—";
  return new Date(ts).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function PublicStatus() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [deptFilter, setDeptFilter] = useState("All");

  useEffect(() => {
    axios
      .get(`${API_BASE_URL}/public/complaints`)
      .then((r) => setComplaints(r.data))
      .catch(() => setError("Failed to load public complaints."))
      .finally(() => setLoading(false));
  }, []);

  const departments = [
    "All",
    ...Array.from(new Set(complaints.map((c) => c.department).filter(Boolean))).sort(),
  ];

  const filtered = complaints.filter((c) => {
    if (statusFilter !== "All" && c.status !== statusFilter) return false;
    if (deptFilter !== "All" && c.department !== deptFilter) return false;
    if (
      search &&
      !c.department?.toLowerCase().includes(search.toLowerCase()) &&
      !c._id?.includes(search)
    )
      return false;
    return true;
  });

  const statsScoped = complaints.filter((c) => {
    if (deptFilter !== "All" && c.department !== deptFilter) return false;
    if (
      search &&
      !c.department?.toLowerCase().includes(search.toLowerCase()) &&
      !c._id?.includes(search)
    )
      return false;
    return true;
  });

  const statsTotal = statsScoped.length;
  const openCount = statsScoped.filter((c) => c.status === "Open").length;
  const inProgressCount = statsScoped.filter((c) => c.status === "In Progress").length;

  const percentage = (count, total) => (total ? Math.round((count / total) * 1000) / 10 : 0);
  const openPct = percentage(openCount, statsTotal);
  const inProgressPct = percentage(inProgressCount, statsTotal);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 text-blue-600 bg-blue-50 px-3 py-1 rounded-full text-xs font-medium">
          <Globe size={13} />
          Public Transparency Board
        </div>
        <h1 className="text-3xl font-bold text-slate-800">Grievance Status Tracker</h1>
        <p className="text-slate-500 text-sm max-w-lg mx-auto">
          Live anonymised view of civic complaints across all departments. No personal
          information is shown.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-stretch sm:items-center">
        <div className="relative flex-1 min-w-40">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search department or ID…"
            className="w-full pl-8 pr-3 py-3 sm:py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>

        <div className="flex items-center gap-1.5 text-sm w-full sm:w-auto">
          <Filter size={13} className="text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-3 sm:py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 flex-1 sm:flex-none"
          >
            {["All", "Open", "In Progress", "Resolved", "Rejected"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>

          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-3 sm:py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 flex-1 sm:flex-none sm:max-w-50"
          >
            {departments.map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>
        </div>

        <span className="text-xs text-slate-400 sm:ml-auto">
          {filtered.length} grievance{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Error */}
      {error && (
        <p className="text-center text-red-500 text-sm">{error}</p>
      )}

      {/* Status Percentage Snapshot */}
      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Open</p>
              <p className="text-sm font-semibold text-blue-700">{openPct}%</p>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full bg-blue-500" style={{ width: `${openPct}%` }} />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {openCount} of {statsTotal} grievance{statsTotal !== 1 ? "s" : ""}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress</p>
              <p className="text-sm font-semibold text-yellow-700">{inProgressPct}%</p>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full bg-yellow-500" style={{ width: `${inProgressPct}%` }} />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {inProgressCount} of {statsTotal} grievance{statsTotal !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16">
          <div className="animate-spin h-8 w-8 rounded-full border-b-2 border-blue-600" />
        </div>
      )}

      {/* Table */}
      {!loading && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {filtered.length === 0 ? (
            <div className="py-16 text-center">
              <Globe size={36} className="mx-auto text-slate-300 mb-3" />
              <p className="text-slate-500 text-sm">No grievances match your filters.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Department
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Filed
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Updated
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((c) => (
                    <tr key={c._id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-xs text-slate-400 font-mono">
                        #{c._id?.slice(-6).toUpperCase()}
                      </td>
                      <td className="px-4 py-3 text-slate-700 font-medium">
                        {c.department || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                            STATUS_BADGE[c.status] || "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {c.priority ? (
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                              PRIORITY_BADGE[c.priority] || "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {c.priority}
                          </span>
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{formatDate(c.created_at)}</td>
                      <td className="px-4 py-3 text-slate-500">{formatDate(c.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <p className="text-center text-xs text-slate-400">
        Data refreshes on page load · Personal information is never displayed
      </p>
    </div>
  );
}
