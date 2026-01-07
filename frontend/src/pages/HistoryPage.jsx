import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ===== Icons =====
const Icons = {
  ArrowLeft: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
    </svg>
  ),
  Download: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  ),
  Trash: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  ),
  ArrowPath: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
  ),
  ChevronLeft: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
    </svg>
  ),
  ChevronRight: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  ),
  Eye: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Table: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5" />
    </svg>
  ),
  X: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  ),
};

// ===== Components =====
const Badge = ({ children, variant = "neutral", className = "" }) => {
  const variants = {
    success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    error: "bg-red-500/20 text-red-400 border-red-500/30",
    warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    info: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    neutral: "bg-surface-700/50 text-surface-300 border-surface-600/50",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

const Button = ({ children, variant = "secondary", size = "md", disabled, loading, onClick, className = "" }) => {
  const variants = {
    primary: "bg-gradient-to-r from-violet-500 to-indigo-500 hover:from-violet-400 hover:to-indigo-400 text-white shadow-lg shadow-violet-500/20",
    secondary: "bg-surface-800 hover:bg-surface-700 text-surface-200 border border-surface-700",
    ghost: "text-surface-400 hover:text-white hover:bg-surface-800",
    danger: "bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30",
  };
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`inline-flex items-center gap-2 rounded-xl font-medium transition-all duration-200 ${variants[variant]} ${sizes[size]} ${disabled || loading ? "opacity-50 cursor-not-allowed" : ""} ${className}`}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {children}
    </button>
  );
};

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-900 border border-surface-700 rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden animate-scale-in">
        <div className="flex items-center justify-between p-5 border-b border-surface-800">
          <h2 className="font-semibold text-xl text-white">{title}</h2>
          <button onClick={onClose} className="p-2 text-surface-400 hover:text-white hover:bg-surface-800 rounded-lg transition-colors">
            <Icons.X />
          </button>
        </div>
        <div className="p-5 overflow-auto max-h-[calc(90vh-80px)]">{children}</div>
      </div>
    </div>
  );
};

// ===== API Helper =====
async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

// ===== Main History Page =====
export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await api("/history/table");
      setHistory(data.rows || []);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all query history? This cannot be undone.")) return;
    try {
      await api("/history/clear", { method: "DELETE" });
      setHistory([]);
    } catch (err) {
      console.error("Failed to clear history:", err);
    }
  };

  const exportHistory = async (format) => {
    try {
      if (format === "excel") {
        const response = await fetch(`${API_BASE}/history/export/excel`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `query-history-${new Date().toISOString().split("T")[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else if (format === "csv") {
        const response = await fetch(`${API_BASE}/history/export/csv`);
        const text = await response.text();
        const blob = new Blob([text], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `query-history-${new Date().toISOString().split("T")[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        const data = await api("/history/export/json");
        const blob = new Blob([data.content], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `query-history-${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error("Failed to export:", err);
    }
  };

  const filteredHistory = useMemo(() => {
    let items = history;
    
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      items = items.filter(
        (item) =>
          item.question?.toLowerCase().includes(term) ||
          item.intent?.toLowerCase().includes(term) ||
          item.sql?.toLowerCase().includes(term)
      );
    }
    
    if (statusFilter !== "all") {
      items = items.filter((item) => item.status === statusFilter);
    }
    
    return items;
  }, [history, searchTerm, statusFilter]);

  const paginatedHistory = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredHistory.slice(start, start + pageSize);
  }, [filteredHistory, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredHistory.length / pageSize);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "-";
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const truncateText = (text, maxLength = 50) => {
    if (!text) return "-";
    return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
  };

  const viewDetails = (item) => {
    setSelectedItem(item);
    setShowDetailModal(true);
  };

  return (
    <div className="min-h-screen bg-surface-950">
      {/* Background */}
      <div className="fixed inset-0 bg-gradient-radial from-violet-500/5 via-transparent to-transparent pointer-events-none" />
      <div className="fixed inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDIwMjAiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiLz48L2c+PC9nPjwvc3ZnPg==')] pointer-events-none opacity-50" />

      {/* Detail Modal */}
      <Modal isOpen={showDetailModal} onClose={() => setShowDetailModal(false)} title="Query Details">
        {selectedItem && (
          <div className="space-y-6">
            {/* Question */}
            <div>
              <label className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Question</label>
              <p className="mt-1 text-white text-lg">{selectedItem.question}</p>
            </div>

            {/* Status & Timing */}
            <div className="flex items-center gap-4">
              <Badge variant={selectedItem.status === "success" ? "success" : "error"}>
                {selectedItem.status === "success" ? <Icons.Check /> : <Icons.X />}
                {selectedItem.status?.toUpperCase()}
              </Badge>
              <span className="text-sm text-surface-400">
                {formatTimestamp(selectedItem.timestamp)}
              </span>
              <span className="text-sm text-surface-400">
                ⏱️ {selectedItem.execution_time_ms}ms
              </span>
              {selectedItem.row_count > 0 && (
                <span className="text-sm text-surface-400">
                  📊 {selectedItem.row_count} rows
                </span>
              )}
            </div>

            {/* Intent */}
            <div>
              <label className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Intent</label>
              <p className="mt-1 text-surface-200">{selectedItem.intent || "-"}</p>
            </div>

            {/* Query Plan */}
            {selectedItem.query_plan && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Query Plan</label>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(selectedItem.query_plan, null, 2));
                    }}
                    className="text-xs px-2 py-1 text-surface-400 hover:text-violet-400 hover:bg-violet-500/10 rounded transition-colors"
                  >
                    Copy JSON
                  </button>
                </div>
                <div className="mt-2 p-4 bg-surface-950 rounded-xl border border-surface-700/50 overflow-x-auto">
                  <pre className="text-sm text-cyan-400 font-mono whitespace-pre-wrap">{JSON.stringify(selectedItem.query_plan, null, 2)}</pre>
                </div>
              </div>
            )}

            {/* SQL */}
            {selectedItem.sql && (
              <div>
                <label className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Generated SQL</label>
                <div className="mt-2 p-4 bg-surface-950 rounded-xl border border-surface-700/50 overflow-x-auto">
                  <pre className="text-sm text-emerald-400 font-mono whitespace-pre-wrap">{selectedItem.sql}</pre>
                </div>
              </div>
            )}

            {/* Error */}
            {selectedItem.error && (
              <div>
                <label className="text-xs font-semibold text-red-400 uppercase tracking-wider">Error</label>
                <div className="mt-2 p-4 bg-red-500/10 rounded-xl border border-red-500/30">
                  <p className="text-sm text-red-300">{selectedItem.error}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <div className="relative max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-4 mb-6">
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-300 hover:text-white transition-all"
            >
              <Icons.ArrowLeft />
              Back to Dashboard
            </Link>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
                <Icons.Table />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">Query History</h1>
                <p className="text-surface-400 mt-1">
                  {filteredHistory.length} {filteredHistory.length === 1 ? "query" : "queries"} recorded
                </p>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="flex items-center gap-3">
              <Button variant="secondary" onClick={loadHistory} loading={loading}>
                <Icons.ArrowPath /> Refresh
              </Button>
              <div className="flex items-center gap-1 p-1 bg-surface-800 rounded-xl">
                <Button size="sm" variant="ghost" onClick={() => exportHistory("csv")}>
                  <Icons.Download /> CSV
                </Button>
                <Button size="sm" variant="ghost" onClick={() => exportHistory("excel")}>
                  <Icons.Download /> Excel
                </Button>
                <Button size="sm" variant="ghost" onClick={() => exportHistory("json")}>
                  <Icons.Download /> JSON
                </Button>
              </div>
              {history.length > 0 && (
                <Button variant="danger" onClick={clearHistory}>
                  <Icons.Trash /> Clear All
                </Button>
              )}
            </div>
          </div>
        </header>

        {/* Filters */}
        <div className="bg-surface-900/80 backdrop-blur-sm border border-surface-800 rounded-2xl p-5 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search questions, intents, or SQL..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-3 bg-surface-800 border border-surface-700 rounded-xl text-white placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-surface-400">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-4 py-3 bg-surface-800 border border-surface-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              >
                <option value="all">All</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Page Size */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-surface-400">Show:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="px-4 py-3 bg-surface-800 border border-surface-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-surface-900/80 backdrop-blur-sm border border-surface-800 rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-800/80 border-b border-surface-700">
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">#</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Timestamp</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider min-w-[250px]">Question</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Intent</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Time</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Rows</th>
                  <th className="px-4 py-4 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-800/50">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center">
                      <div className="flex items-center justify-center gap-3 text-surface-400">
                        <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Loading history...
                      </div>
                    </td>
                  </tr>
                ) : paginatedHistory.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-surface-500">
                      {searchTerm || statusFilter !== "all"
                        ? "No queries match your filters"
                        : "No query history yet. Run some queries to see them here."}
                    </td>
                  </tr>
                ) : (
                  paginatedHistory.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-surface-800/30 transition-colors cursor-pointer"
                      onClick={() => viewDetails(item)}
                    >
                      <td className="px-4 py-4 text-sm text-surface-500">{item.row_num}</td>
                      <td className="px-4 py-4 text-sm text-surface-400">{formatTimestamp(item.timestamp)}</td>
                      <td className="px-4 py-4">
                        <p className="text-sm text-white font-medium">{truncateText(item.question, 60)}</p>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm text-surface-300">{truncateText(item.intent, 25)}</span>
                      </td>
                      <td className="px-4 py-4">
                        <Badge variant={item.status === "success" ? "success" : "error"}>
                          {item.status === "success" ? <Icons.Check /> : <Icons.X />}
                          {item.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-4 text-sm text-surface-400">{item.execution_time_ms}ms</td>
                      <td className="px-4 py-4 text-sm text-surface-400">{item.row_count || 0}</td>
                      <td className="px-4 py-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            viewDetails(item);
                          }}
                          className="p-2 text-surface-400 hover:text-violet-400 hover:bg-violet-500/10 rounded-lg transition-colors"
                          title="View details"
                        >
                          <Icons.Eye />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-4 border-t border-surface-800">
              <div className="text-sm text-surface-400">
                Showing {(currentPage - 1) * pageSize + 1} to{" "}
                {Math.min(currentPage * pageSize, filteredHistory.length)} of {filteredHistory.length} queries
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <Icons.ChevronLeft />
                </Button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let page;
                    if (totalPages <= 5) {
                      page = i + 1;
                    } else if (currentPage <= 3) {
                      page = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      page = totalPages - 4 + i;
                    } else {
                      page = currentPage - 2 + i;
                    }
                    return (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                          currentPage === page
                            ? "bg-violet-500 text-white"
                            : "text-surface-400 hover:text-white hover:bg-surface-800"
                        }`}
                      >
                        {page}
                      </button>
                    );
                  })}
                </div>

                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <Icons.ChevronRight />
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-surface-800/50 text-center text-surface-500 text-sm">
          <p>AP Semantic Query Engine • Query History</p>
        </footer>
      </div>
    </div>
  );
}

