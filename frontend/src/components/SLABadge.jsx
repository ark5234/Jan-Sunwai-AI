import { Clock, AlertTriangle, CheckCircle } from "lucide-react";

// SLA deadlines in days, keyed by canonical department name
const SLA_DAYS = {
  "Health Department": 7,
  "Civil Department": 21,
  "Horticulture": 14,
  "Electrical Department": 5,
  "IT Department": 7,
  "Commercial": 14,
  "Enforcement": 3,
  "VBD Department": 3,
  "EBR Department": 30,
  "Fire Department": 1,
  "Uncategorized": 30,
};

const DEFAULT_SLA = 14;

/**
 * SLABadge — shows "X days left", "Due today", or "Overdue N days"
 * Props:
 *   createdAt  {string|Date}  — complaint creation timestamp
 *   department {string}       — canonical department name
 *   status     {string}       — current complaint status
 *   updatedAt  {string|Date}  — last updated timestamp (used for resolved date)
 */
export default function SLABadge({ createdAt, department, status, updatedAt }) {
  if (!createdAt) return null;

  // Resolved / Rejected: show resolution date instead of duplicating the status badge
  if (status === "Resolved" || status === "Rejected") {
    const resolvedDate = updatedAt ? new Date(updatedAt).toLocaleDateString() : null;
    return resolvedDate ? (
      <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700">
        <CheckCircle size={11} />
        {resolvedDate}
      </span>
    ) : null;
  }

  const sladays = SLA_DAYS[department] ?? DEFAULT_SLA;
  const created = new Date(createdAt);
  const deadline = new Date(created.getTime() + sladays * 86400000);
  const now = new Date();
  const diffMs = deadline.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / 86400000);

  if (diffDays < 0) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-700">
        <AlertTriangle size={11} />
        Overdue by {Math.abs(diffDays)}d
      </span>
    );
  }

  if (diffDays === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">
        <Clock size={11} />
        Due today
      </span>
    );
  }

  const colour =
    diffDays <= 2
      ? "bg-orange-100 text-orange-700"
      : diffDays <= 5
      ? "bg-yellow-100 text-yellow-700"
      : "bg-blue-100 text-blue-600";

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${colour}`}
    >
      <Clock size={11} />
      {diffDays}d left
    </span>
  );
}
