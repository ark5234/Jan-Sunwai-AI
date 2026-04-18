import { useState, useEffect } from "react";
import {
  BarChart2,
  TrendingUp,
  CheckCircle,
  Clock,
  AlertTriangle,
  Download,
} from "lucide-react";
import api from "../context/api";

const STATUS_COLORS = {
  Open: "bg-blue-500",
  "In Progress": "bg-yellow-500",
  Resolved: "bg-green-500",
  Rejected: "bg-red-400",
};

const PRIORITY_COLORS = {
  Critical: "bg-red-600",
  High: "bg-orange-500",
  Medium: "bg-yellow-400",
  Low: "bg-green-400",
};

const MONTH_NAMES = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function StatCard({ icon: Icon, label, value, sub, colour }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-start gap-4">
      <div className={`p-2.5 rounded-lg ${colour}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
        <p className="text-sm font-medium text-slate-600">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function HBar({ label, value, max, colour }) {
  const pct = max ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-600 w-44 truncate" title={label}>
        {label}
      </span>
      <div className="flex-1 bg-slate-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colour}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-700 w-8 text-right">
        {value}
      </span>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/analytics/overview")
      .then((r) => setData(r.data))
      .catch(() => setError("Failed to load analytics. Make sure you are logged in as Admin."))
      .finally(() => setLoading(false));
  }, []);

  const handleExport = () => {
    // Export uses the shared axios instance, which sends auth cookies automatically.
    api
      .get("/complaints/export/csv", { responseType: "blob" })
      .then((r) => {
        const url = URL.createObjectURL(new Blob([r.data], { type: "text/csv" }));
        const a = document.createElement("a");
        a.href = url;
        a.download = "complaints_export.csv";
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => alert("Export failed."));
  };

  if (loading)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    );

  if (error)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    );

  const total = data?.total_complaints ?? 0;
  const resolved = data?.by_status?.Resolved ?? 0;
  const open = data?.by_status?.Open ?? 0;
  const inProgress = data?.by_status?.["In Progress"] ?? 0;
  const maxDept = Math.max(...(data?.by_department ?? []).map((d) => d.count), 1);
  const maxMonth = Math.max(...(data?.monthly_trend ?? []).map((m) => m.count), 1);
  const totalPriority = Object.values(data?.by_priority ?? {}).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart2 size={24} className="text-blue-600" />
            Analytics Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Real-time grievance statistics</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Download size={15} />
          Export CSV
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={BarChart2} label="Total Complaints" value={total} colour="bg-blue-600" />
        <StatCard
          icon={CheckCircle}
          label="Resolved"
          value={resolved}
          sub={`${data?.resolution_rate ?? 0}% rate`}
          colour="bg-green-600"
        />
        <StatCard icon={Clock} label="Open" value={open} colour="bg-yellow-500" />
        <StatCard icon={TrendingUp} label="In Progress" value={inProgress} colour="bg-purple-600" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Status breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Status Breakdown</h2>
          <div className="space-y-2.5">
            {Object.entries(data?.by_status ?? {}).map(([s, c]) => (
              <HBar
                key={s}
                label={s}
                value={c}
                max={total}
                colour={STATUS_COLORS[s] || "bg-slate-400"}
              />
            ))}
          </div>
        </div>

        {/* Priority breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Priority Breakdown</h2>
          <div className="space-y-2.5">
            {["Critical", "High", "Medium", "Low"].map((p) => {
              const c = data?.by_priority?.[p] ?? 0;
              return (
                <HBar
                  key={p}
                  label={p}
                  value={c}
                  max={total || 1}
                  colour={PRIORITY_COLORS[p]}
                />
              );
            })}
          </div>
        </div>

        {/* By department */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Complaints by Department</h2>
          <div className="space-y-2.5">
            {(data?.by_department ?? []).map((d) => (
              <HBar
                key={d.department}
                label={d.department}
                value={d.count}
                max={maxDept}
                colour="bg-blue-400"
              />
            ))}
          </div>
        </div>

        {/* Avg resolution time */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">
            Avg Resolution Time (days)
          </h2>
          {(data?.resolution_time_by_dept ?? []).length === 0 ? (
            <p className="text-xs text-slate-400">No resolved complaints yet.</p>
          ) : (
            <div className="space-y-2.5">
              {(data?.resolution_time_by_dept ?? []).map((d) => (
                <HBar
                  key={d.department}
                  label={d.department}
                  value={d.avg_days}
                  max={Math.max(
                    ...(data?.resolution_time_by_dept ?? []).map((x) => x.avg_days),
                    1
                  )}
                  colour="bg-green-400"
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Monthly trend */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
          <TrendingUp size={15} className="text-blue-500" />
          Monthly Trend (last 6 months)
        </h2>
        {(data?.monthly_trend ?? []).length === 0 ? (
          <p className="text-xs text-slate-400">No data yet.</p>
        ) : (
          <div className="flex items-end gap-3 h-32">
            {(data?.monthly_trend ?? []).map((m) => {
              const pct = (m.count / maxMonth) * 100;
              return (
                <div key={`${m.year}-${m.month}`} className="flex flex-col items-center gap-1 flex-1">
                  <span className="text-xs font-semibold text-slate-600">{m.count}</span>
                  <div
                    className="w-full bg-blue-500 rounded-t"
                    style={{ height: `${Math.max(pct, 4)}%` }}
                  />
                  <span className="text-[10px] text-slate-400">
                    {MONTH_NAMES[m.month]}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
