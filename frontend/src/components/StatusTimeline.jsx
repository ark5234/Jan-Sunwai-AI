import React from 'react';

function formatTimelineDate(value) {
  if (!value) return 'Unknown time';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return 'Unknown time';
  return d.toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function StatusTimeline({ items = [] }) {
  if (!Array.isArray(items) || items.length === 0) {
    return null;
  }

  const sorted = [...items].sort(
    (a, b) => new Date(a.timestamp || 0).getTime() - new Date(b.timestamp || 0).getTime()
  );

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Status Timeline</p>
      <ul className="mt-2 space-y-2">
        {sorted.map((entry, idx) => (
          <li key={`${entry.status}-${entry.timestamp || 'no-time'}-${idx}`} className="flex gap-2.5">
            <span className="mt-1 inline-block h-2 w-2 rounded-full bg-blue-500" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-800">{entry.status || 'Unknown status'}</p>
              <p className="text-[11px] text-slate-500">{formatTimelineDate(entry.timestamp)}</p>
              {entry.note ? <p className="text-[11px] text-slate-600">{entry.note}</p> : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
