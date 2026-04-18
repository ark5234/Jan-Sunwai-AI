import { useState, useEffect, useMemo, useRef } from "react";
import { MessageSquare, Send } from "lucide-react";
import api from "../context/api";

const ROLE_LABEL = {
  citizen: "Citizen",
  dept_head: "Dept. Officer",
  admin: "Admin",
  worker: "Worker",
};
const ROLE_COLOR = {
  citizen: "bg-blue-100 text-blue-700",
  dept_head: "bg-purple-100 text-purple-700",
  admin: "bg-red-100 text-red-700",
  worker: "bg-emerald-100 text-emerald-700",
};

function formatTime(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * ComplaintComments — collapsible comment thread for a complaint.
 * Props:
 *   complaintId {string}
 *   currentRole {string}  — "citizen" | "dept_head" | "admin"
 */
export default function ComplaintComments({ complaintId, currentRole }) {
  const storageKey = useMemo(
    () => `complaint_comments_open_${complaintId || "unknown"}`,
    [complaintId]
  );
  const [open, setOpen] = useState(() => {
    try {
      return localStorage.getItem(storageKey) === "1";
    } catch {
      return false;
    }
  });
  const [comments, setComments] = useState([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);

  const sortComments = (items) =>
    [...items].sort((a, b) => {
      const aTs = new Date(a?.created_at || 0).getTime();
      const bTs = new Date(b?.created_at || 0).getTime();
      return aTs - bTs;
    });

  const labelForComment = (authorRole) => {
    if (authorRole && authorRole === currentRole) return "You";
    return ROLE_LABEL[authorRole] || authorRole || "?";
  };

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, open ? "1" : "0");
    } catch {
      // ignore storage errors
    }
  }, [open, storageKey]);

  useEffect(() => {
    if (!open || !listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [comments, open]);

  useEffect(() => {
    if (!open || !complaintId) return;
    setLoading(true);
    setError("");
    api
      .get(`/complaints/${complaintId}/comments`)
      .then((r) => {
        const items = Array.isArray(r.data) ? r.data : [];
        setComments(sortComments(items));
      })
      .catch(() => setError("Failed to load comments."))
      .finally(() => setLoading(false));
  }, [open, complaintId]);

  const handlePost = async () => {
    if (!text.trim()) return;
    setPosting(true);
    setError("");
    try {
      const r = await api.post(`/complaints/${complaintId}/comments`, { text: text.trim() });
      setComments((prev) => sortComments([...prev, r.data.comment]));
      setText("");
    } catch {
      setError("Failed to post comment.");
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-blue-600 transition-colors"
      >
        <MessageSquare size={13} />
        {open ? `Hide comments (${comments.length})` : `Comments (${comments.length})`}
      </button>

      {open && (
        <div className="mt-2 border border-slate-200 rounded-lg p-3 bg-slate-50 space-y-3">
          {loading && <p className="text-xs text-slate-400">Loading…</p>}
          {error && <p className="text-xs text-red-500">{error}</p>}

          {!loading && comments.length === 0 && (
            <p className="text-xs text-slate-400">No comments yet.</p>
          )}

          <div ref={listRef} className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {comments.map((c, i) => (
              <div key={`${c.author_id || "anon"}-${c.created_at || i}`} className="flex gap-2">
                <div className="shrink-0 mt-0.5">
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                      ROLE_COLOR[c.author_role] || "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {labelForComment(c.author_role)}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="text-xs text-slate-700">{c.text}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">{formatTime(c.created_at)}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2 pt-1 border-t border-slate-200">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handlePost()}
              placeholder="Add a comment…"
              maxLength={1000}
              className="flex-1 text-xs border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400 bg-white"
            />
            <button
              onClick={handlePost}
              disabled={posting || !text.trim()}
              className="px-2.5 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              <Send size={11} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
