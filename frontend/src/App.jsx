import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import "./index.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ===== Icons =====
const Icons = {
  Database: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
    </svg>
  ),
  Sparkles: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
    </svg>
  ),
  Code: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  ),
  ArrowPath: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
  ),
  Table: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5" />
    </svg>
  ),
  Link: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
    </svg>
  ),
  Shield: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  ),
  Play: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
    </svg>
  ),
  Lightning: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    </svg>
  ),
  X: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Info: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  ),
  Chat: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
    </svg>
  ),
  Trash: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  ),
  Copy: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
    </svg>
  ),
  Download: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  ),
  Expand: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
    </svg>
  ),
};

// Pipeline steps configuration
const PIPELINE_STEPS = [
  { id: "question_validation", label: "Validate", icon: <Icons.Check /> },
  { id: "intent_detection", label: "Intent", icon: <Icons.Lightning /> },
  { id: "schema_load", label: "Schema", icon: <Icons.Database /> },
  { id: "plan_generation", label: "Planner", icon: <Icons.Sparkles /> },
  { id: "plan_validation", label: "Validator", icon: <Icons.Shield /> },
  { id: "sql_compilation", label: "SQL Build", icon: <Icons.Code /> },
  { id: "safety_validation", label: "Safety", icon: <Icons.Shield /> },
  { id: "query_execution", label: "Execute", icon: <Icons.Play /> },
  { id: "narration", label: "Narrate", icon: <Icons.Chat /> },
];

// ===== Components =====
const Card = ({ icon, title, subtitle, children, className = "", actions }) => (
  <div className={`card p-6 ${className}`}>
    {(icon || title) && (
      <div className="flex items-start justify-between gap-3 mb-5">
        <div className="flex items-start gap-3">
          {icon && (
            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-accent-500/20 to-accent-600/10 border border-accent-500/20 flex items-center justify-center text-accent-400">
              {icon}
      </div>
          )}
          <div className="flex-1 min-w-0">
            <h3 className="font-display font-semibold text-white text-lg">{title}</h3>
            {subtitle && <p className="text-sm text-surface-400 mt-0.5">{subtitle}</p>}
    </div>
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    )}
    {children}
  </div>
);

const Badge = ({ children, variant = "neutral", className = "" }) => {
  const variants = {
    primary: "badge-primary",
    secondary: "badge-secondary",
    success: "badge-success",
    warning: "badge-warning",
    error: "badge-error",
    info: "badge-info",
    neutral: "badge-neutral",
  };
  return <span className={`badge ${variants[variant]} ${className}`}>{children}</span>;
};

const Button = ({ children, variant = "secondary", size = "md", disabled, loading, onClick, className = "", title }) => {
  const variants = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "btn-ghost",
    danger: "btn-danger",
  };
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
    icon: "p-2",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      title={title}
      className={`btn ${variants[variant]} ${sizes[size]} ${disabled || loading ? "opacity-50 cursor-not-allowed" : ""} ${className}`}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {children}
    </button>
  );
};

const IconButton = ({ icon, onClick, title, variant = "ghost", disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    title={title}
    className={`p-2 rounded-lg transition-all duration-200 ${
      variant === "ghost"
        ? "text-surface-400 hover:text-white hover:bg-surface-700/50"
        : variant === "danger"
        ? "text-red-400 hover:text-red-300 hover:bg-red-500/10"
        : "text-surface-400 hover:text-accent-400 hover:bg-accent-500/10"
    } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
  >
    {icon}
  </button>
);

const Toast = ({ message, tone, onClose }) => {
  if (!message) return null;
  const tones = { success: "toast-success", error: "toast-error", info: "toast-info", warning: "toast-warning" };
  const icons = { success: <Icons.Check />, error: <Icons.X />, info: <Icons.Info />, warning: <Icons.Info /> };
  return (
    <div className={`toast ${tones[tone]}`}>
      <span className="flex-shrink-0">{icons[tone]}</span>
      <span className="font-medium">{message}</span>
      <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100 transition-opacity"><Icons.X /></button>
    </div>
  );
};

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-900 border border-surface-700 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden animate-slide-up">
        <div className="flex items-center justify-between p-5 border-b border-surface-800">
          <h2 className="font-display font-semibold text-xl text-white">{title}</h2>
          <IconButton icon={<Icons.X />} onClick={onClose} title="Close" />
        </div>
        <div className="p-5 overflow-auto max-h-[calc(85vh-80px)]">{children}</div>
      </div>
    </div>
  );
};

const PipelineStep = ({ step, status, isLast }) => {
  const statusStyles = {
    pending: "bg-surface-800 border-surface-700 text-surface-500",
    running: "bg-accent-500/20 border-accent-500/40 text-accent-400 animate-pulse",
    success: "bg-success/20 border-success/40 text-emerald-400",
    error: "bg-error/20 border-error/40 text-red-400",
  };
  return (
    <div className="flex items-center">
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${statusStyles[status] || statusStyles.pending}`}>
        {step.icon}
        <span className="text-xs font-medium whitespace-nowrap">{step.label}</span>
        {status === "success" && <Icons.Check />}
        {status === "error" && <Icons.X />}
      </div>
      {!isLast && <div className={`w-6 h-0.5 ${status === "success" ? "bg-success/40" : "bg-surface-700"}`} />}
    </div>
  );
};

const ResultsTable = ({ columns, rows }) => {
  if (!rows?.length) return <p className="text-surface-500 text-sm">No results</p>;
  return (
    <div className="overflow-auto max-h-[400px] rounded-xl border border-surface-700/50">
      <table className="w-full text-sm">
        <thead className="bg-surface-800/80 sticky top-0">
          <tr>
            {columns.map((col) => (
              <th key={col} className="px-4 py-3 text-left font-semibold text-surface-300 border-b border-surface-700/50">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-surface-800/50 hover:bg-surface-800/30 transition-colors">
              {columns.map((col) => (
                <td key={col} className="px-4 py-3 text-surface-300">{row[col]?.toString() ?? "-"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ===== Validation Error Display =====
const ValidationErrors = ({ errors, warnings }) => {
  if (!errors?.length && !warnings?.length) return null;
  return (
    <div className="space-y-3">
      {errors?.length > 0 && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
          <div className="flex items-center gap-2 text-red-400 font-semibold text-sm mb-2">
            <Icons.X /> Validation Errors ({errors.length})
          </div>
          <ul className="space-y-1.5">
            {errors.map((e, i) => (
              <li key={i} className="text-sm text-red-300">
                <span className="font-mono text-red-400">[{e.code || "ERROR"}]</span>{" "}
                {e.message || e}
                {e.suggestion && <p className="text-xs text-surface-400 mt-0.5">💡 {e.suggestion}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {warnings?.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm mb-2">
            <Icons.Info /> Warnings ({warnings.length})
          </div>
          <ul className="space-y-1">
            {warnings.map((w, i) => (
              <li key={i} className="text-sm text-amber-300">
                {w.message || w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// ===== Database Status =====
const DatabaseStatus = ({ info }) => {
  if (!info) return null;
  return (
    <div className="flex items-center gap-3 text-xs text-surface-400">
      <div className="flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
        <span className="font-medium">{info.dialect?.toUpperCase()}</span>
      </div>
      <span>{info.host}:{info.port}</span>
      <span className="text-surface-500">•</span>
      <span>{info.database}</span>
    </div>
  );
};

// ===== Execution Stats =====
const ExecutionStats = ({ result }) => {
  if (!result) return null;
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs">
      {result.execution_time_ms && (
        <Badge variant="info">⏱️ {result.execution_time_ms}ms total</Badge>
      )}
      {result.results?.row_count !== undefined && (
        <Badge variant="success">📊 {result.results.row_count} rows</Badge>
      )}
      {result.results?.truncated && (
        <Badge variant="warning">⚠️ Results truncated</Badge>
      )}
      {result.steps?.filter(s => s.status === "success").length && (
        <Badge variant="neutral">
          ✓ {result.steps.filter(s => s.status === "success").length}/{result.steps.length} steps
        </Badge>
      )}
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
  if (!res.ok) {
    const detail = data.detail || res.statusText;
    // Handle structured error response
    if (typeof detail === "object" && detail.errors) {
      const err = new Error(detail.message || "Validation failed");
      err.errors = detail.errors;
      throw err;
    }
    throw new Error(Array.isArray(detail) ? detail.join("; ") : typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

// ===== Main App =====
function App() {
  const [question, setQuestion] = useState("");
  const [schema, setSchema] = useState([]);
  const [enums, setEnums] = useState([]);
  const [mappings, setMappings] = useState({ tables: [], columns: [] });
  const [tableMapping, setTableMapping] = useState({ table: "", role: "fact", priority: "silver", tenant_column: "", business_name: "" });
  const [columnMapping, setColumnMapping] = useState({ table: "", column: "", business_meaning: "" });
  const [toast, setToast] = useState({ message: "", tone: "info" });
  const [busy, setBusy] = useState(false);
  const [activeTab, setActiveTab] = useState("tables");
  
  // Pipeline state
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [pipelineSteps, setPipelineSteps] = useState({});
  const [executeQuery, setExecuteQuery] = useState(true);
  const [includeNarration, setIncludeNarration] = useState(true);
  
  // Modal state
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showSqlModal, setShowSqlModal] = useState(false);
  const [showDocModal, setShowDocModal] = useState(false);
  const [copied, setCopied] = useState("");
  
  // Documentation state
  const [tableDocumentation, setTableDocumentation] = useState(null);
  const [docLoading, setDocLoading] = useState(false);
  const [selectedDocTable, setSelectedDocTable] = useState(null);
  
  // Sample Questions state
  const [sampleQuestions, setSampleQuestions] = useState(null);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [showQuestionsPanel, setShowQuestionsPanel] = useState(false);
  
  // Database Configuration state
  const [showDbConfig, setShowDbConfig] = useState(false);
  const [dbConfig, setDbConfig] = useState({
    dialect: "mysql",
    host: "127.0.0.1",
    port: 3306,
    user: "root",
    password: "",
    database: "",
  });
  const [dbConnected, setDbConnected] = useState(false);
  
  // Query History state
  const [queryHistory, setQueryHistory] = useState([]);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  
  // Auto-analysis state
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const tables = useMemo(() => schema.map((t) => t.name), [schema]);
  const selectedTableColumns = useMemo(() => {
    const t = schema.find((s) => s.name === columnMapping.table);
    return t ? t.columns : [];
  }, [schema, columnMapping.table]);

  useEffect(() => {
    loadMappings();
    loadDbConfig();
    loadHistory();
  }, []);

  const notify = (message, tone = "info") => {
    setToast({ message, tone });
    setTimeout(() => setToast({ message: "", tone: "info" }), 4000);
  };

  const copyToClipboard = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(label);
      notify(`${label} copied to clipboard`, "success");
      setTimeout(() => setCopied(""), 2000);
    } catch (err) {
      notify("Failed to copy", "error");
    }
  };

  const downloadJson = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    notify(`${filename} downloaded`, "success");
  };

  const downloadSql = (sql, filename) => {
    const blob = new Blob([sql], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    notify(`${filename} downloaded`, "success");
  };

  const clearAllData = () => {
    setQuestion("");
    setPipelineResult(null);
    setPipelineSteps({});
    notify("All data cleared", "info");
  };

  const loadSchema = async () => {
    setBusy(true);
    try {
      const data = await api("/schema");
      setSchema(data.tables || []);
      setEnums(data.enums || []);
      notify("Schema introspected successfully", "success");
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  const loadMappings = async () => {
    try { setMappings(await api("/mappings")); } catch {}
  };

  const loadDbConfig = async () => {
    try {
      const config = await api("/database/config");
      setDbConfig(prev => ({
        ...prev,
        dialect: config.dialect,
        host: config.host,
        port: config.port,
        user: config.user,
        database: config.database,
      }));
      setDbConnected(config.database && config.host);
    } catch {}
  };

  const loadHistory = async () => {
    try {
      const data = await api("/history");
      setQueryHistory(data.items || []);
    } catch {}
  };

  const saveDbConfig = async () => {
    setBusy(true);
    try {
      const result = await api("/database/config", {
        method: "POST",
        body: JSON.stringify(dbConfig),
      });
      if (result.success) {
        setDbConnected(true);
        notify("Database connected successfully", "success");
        setShowDbConfig(false);
        // Auto-refresh schema after connection
        loadSchema();
      } else {
        notify(result.message || "Connection failed", "error");
      }
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  const autoAnalyzeTables = async () => {
    setAnalyzing(true);
    try {
      const result = await api("/database/analyze", { method: "POST" });
      setAnalysisResult(result);
      loadMappings();
      notify(`Analyzed ${result.analyzed_tables?.length || 0} tables: ${result.fact_tables?.length || 0} fact, ${result.dimension_tables?.length || 0} dimension`, "success");
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setAnalyzing(false);
    }
  };

  const refreshAndAnalyze = async () => {
    setAnalyzing(true);
    setBusy(true);
    try {
      const result = await api("/database/refresh", { method: "POST" });
      setSchema([]); // Will be reloaded
      setAnalysisResult(result);
      loadMappings();
      loadSchema();
      notify(`Refreshed and analyzed ${result.tables_count || 0} tables`, "success");
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setAnalyzing(false);
      setBusy(false);
    }
  };

  const exportHistory = async (format) => {
    try {
      if (format === "json") {
        const result = await api("/history/export/json");
        downloadJson(JSON.parse(result.content), `query-history-${Date.now()}.json`);
      } else if (format === "csv") {
        const result = await fetch(`${API_BASE}/history/export/csv`);
        const text = await result.text();
        downloadText(text, `query-history-${Date.now()}.csv`);
      } else {
        const result = await fetch(`${API_BASE}/history/export/text`);
        const text = await result.text();
        downloadText(text, `query-history-${Date.now()}.txt`);
      }
    } catch (err) {
      notify(err.message, "error");
    }
  };

  const clearHistory = async () => {
    if (!window.confirm("Clear all query history?")) return;
    try {
      await api("/history/clear", { method: "DELETE" });
      setQueryHistory([]);
      notify("History cleared", "success");
    } catch (err) {
      notify(err.message, "error");
    }
  };

  const loadDocumentation = async () => {
    setDocLoading(true);
    try {
      const doc = await api("/schema/documentation");
      setTableDocumentation(doc);
      notify("Documentation generated", "success");
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setDocLoading(false);
    }
  };

  const exportDocumentation = async () => {
    try {
      const result = await api("/schema/export");
      downloadText(result.content, `database-documentation-${new Date().toISOString().split('T')[0]}.txt`);
    } catch (err) { notify(err.message, "error"); }
  };

  const downloadText = (text, filename) => {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    notify(`${filename} downloaded`, "success");
  };

  const generateAiDocumentation = async (tableName) => {
    setSelectedDocTable(tableName);
    try {
      const result = await api("/schema/documentation/generate-ai", {
        method: "POST",
        body: JSON.stringify({ table_name: tableName }),
      });
      // Update the table documentation with AI-generated content
      if (tableDocumentation) {
        const updatedTables = tableDocumentation.tables.map(t => 
          t.table_name === tableName 
            ? { ...t, ai_documentation: result.documentation }
            : t
        );
        setTableDocumentation({ ...tableDocumentation, tables: updatedTables });
      }
      notify(`AI documentation generated for ${tableName}`, "success");
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setSelectedDocTable(null);
    }
  };

  // Sample Questions Functions
  const loadSampleQuestions = async (includeAi = false, includeDataAnalysis = true) => {
    setQuestionsLoading(true);
    try {
      const data = await api(`/questions?include_ai=${includeAi}&include_data_analysis=${includeDataAnalysis}&ai_count=15`);
      setSampleQuestions(data);
      setShowQuestionsPanel(true);
      notify(`Loaded ${data.total} sample questions based on your database`, "success");
    } catch (err) {
      notify(err.message, "error");
    } finally {
      setQuestionsLoading(false);
    }
  };

  const exportQuestionsToText = () => {
    if (!sampleQuestions) return;
    let text = "# Sample Questions for AP Query Engine\n\n";
    text += "Note: All queries require tenant_id for security.\n";
    text += "Questions marked with [USER] also require user_id.\n\n";
    
    Object.entries(sampleQuestions.by_category || {}).forEach(([category, questions]) => {
      text += `## ${category}\n\n`;
      questions.forEach((q, i) => {
        const userTag = q.requires_user ? " [USER]" : "";
        text += `${i + 1}. ${q.question}${userTag}\n`;
      });
      text += "\n";
    });
    
    downloadText(text, `sample-questions-${new Date().toISOString().split('T')[0]}.txt`);
  };

  const exportFullSession = () => {
    if (!pipelineResult) {
      notify("No pipeline result to export", "warning");
      return;
    }
    const session = {
      timestamp: new Date().toISOString(),
      question: question,
      plan: pipelineResult.plan,
      sql: pipelineResult.sql,
      params: pipelineResult.params,
      results: pipelineResult.results,
      narration: pipelineResult.narration,
      validation_errors: pipelineResult.validation_errors,
      validation_warnings: pipelineResult.validation_warnings,
      execution_time_ms: pipelineResult.execution_time_ms,
      database_info: pipelineResult.database_info,
    };
    downloadJson(session, `query-session-${Date.now()}.json`);
  };

  const useQuestionTemplate = (q) => {
    setQuestion(q.question);
    setShowQuestionsPanel(false);
    notify("Question loaded. Add your tenant_id and run the pipeline!", "info");
  };

  const filteredQuestions = useMemo(() => {
    if (!sampleQuestions?.questions) return [];
    if (selectedCategory === "All") return sampleQuestions.questions;
    return sampleQuestions.questions.filter(q => q.category === selectedCategory);
  }, [sampleQuestions, selectedCategory]);

  const saveTable = async () => {
    try {
      await api("/mappings/table", { method: "POST", body: JSON.stringify(tableMapping) });
      notify("Table mapping saved", "success");
      loadMappings();
    } catch (err) { notify(err.message, "error"); }
  };

  const saveColumn = async () => {
    try {
      await api("/mappings/column", { method: "POST", body: JSON.stringify(columnMapping) });
      notify("Column mapping saved", "success");
      loadMappings();
    } catch (err) { notify(err.message, "error"); }
  };

  // Run the full pipeline
  const runPipeline = async () => {
    if (!question.trim()) {
      notify("Please enter a question", "warning");
      return;
    }
    
    setPipelineRunning(true);
    setPipelineResult(null);
    setPipelineSteps({});
    
    PIPELINE_STEPS.forEach((s) => setPipelineSteps((prev) => ({ ...prev, [s.id]: "pending" })));
    
    try {
      const result = await api("/pipeline/run", {
        method: "POST",
        body: JSON.stringify({ question, execute: executeQuery, narrate: includeNarration }),
      });
      
      // Update step statuses
      result.steps?.forEach((s) => {
        setPipelineSteps((prev) => ({ ...prev, [s.step]: s.status }));
      });
      
      setPipelineResult(result);
      
      if (result.success) {
        notify(`Pipeline completed in ${result.execution_time_ms}ms`, "success");
      } else {
        notify("Pipeline completed with errors", "warning");
      }
    } catch (err) {
      // Handle validation errors with detailed info
      if (err.errors) {
        setPipelineResult({
          success: false,
          question,
          validation_errors: err.errors,
          steps: [],
        });
      }
      notify(err.message, "error");
    } finally {
      setPipelineRunning(false);
    }
  };

  const planJson = pipelineResult?.plan ? JSON.stringify(pipelineResult.plan, null, 2) : "";
  const sqlText = pipelineResult?.sql || "";

  return (
    <div className="min-h-screen bg-surface-950 bg-grid">
      <div className="fixed inset-0 bg-gradient-radial from-accent-500/5 via-transparent to-transparent pointer-events-none" />
      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: "", tone: "info" })} />

      {/* Plan Modal */}
      <Modal isOpen={showPlanModal} onClose={() => setShowPlanModal(false)} title="Generated Query Plan">
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <Button size="sm" variant="secondary" onClick={() => copyToClipboard(planJson, "Plan")}>
              <Icons.Copy /> {copied === "Plan" ? "Copied!" : "Copy"}
            </Button>
            <Button size="sm" variant="secondary" onClick={() => downloadJson(pipelineResult?.plan, `query-plan-${Date.now()}.json`)}>
              <Icons.Download /> Download JSON
            </Button>
          </div>
          <div className="code-block">
            <pre className="text-sm">{planJson}</pre>
          </div>
        </div>
      </Modal>

      {/* SQL Modal */}
      <Modal isOpen={showSqlModal} onClose={() => setShowSqlModal(false)} title="Compiled SQL">
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <Button size="sm" variant="secondary" onClick={() => copyToClipboard(sqlText, "SQL")}>
              <Icons.Copy /> {copied === "SQL" ? "Copied!" : "Copy"}
            </Button>
            <Button size="sm" variant="secondary" onClick={() => downloadSql(sqlText, `query-${Date.now()}.sql`)}>
              <Icons.Download /> Download SQL
            </Button>
          </div>
          <div className="code-block">
            <pre className="text-secondary-300">{sqlText}</pre>
          </div>
          {pipelineResult?.params?.length > 0 && (
            <div className="p-4 rounded-xl bg-surface-800/50 border border-surface-700/50">
              <p className="section-title mb-3">Parameters</p>
              <div className="flex flex-wrap gap-2">
                {pipelineResult.params.map((p, i) => (
                  <Badge key={i} variant="secondary">{p[0]}: {p[1]}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Database Configuration Modal */}
      <Modal isOpen={showDbConfig} onClose={() => setShowDbConfig(false)} title="Database Configuration">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
          <div>
              <label className="label">Dialect</label>
              <select 
                className="select"
                value={dbConfig.dialect}
                onChange={(e) => setDbConfig({...dbConfig, dialect: e.target.value})}
              >
                <option value="mysql">MySQL</option>
                <option value="postgres">PostgreSQL</option>
                <option value="mssql">SQL Server</option>
                <option value="oracle">Oracle</option>
                <option value="sqlite">SQLite</option>
              </select>
            </div>
            <div>
              <label className="label">Port</label>
              <input 
                type="number"
                className="input"
                value={dbConfig.port}
                onChange={(e) => setDbConfig({...dbConfig, port: parseInt(e.target.value) || 3306})}
              />
            </div>
          </div>
          <div>
            <label className="label">Host</label>
            <input 
              className="input"
              value={dbConfig.host}
              onChange={(e) => setDbConfig({...dbConfig, host: e.target.value})}
              placeholder="127.0.0.1"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Username</label>
              <input 
                className="input"
                value={dbConfig.user}
                onChange={(e) => setDbConfig({...dbConfig, user: e.target.value})}
                placeholder="root"
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input 
                type="password"
                className="input"
                value={dbConfig.password}
                onChange={(e) => setDbConfig({...dbConfig, password: e.target.value})}
                placeholder="••••••••"
              />
            </div>
          </div>
          <div>
            <label className="label">Database Name</label>
            <input 
              className="input"
              value={dbConfig.database}
              onChange={(e) => setDbConfig({...dbConfig, database: e.target.value})}
              placeholder="my_database"
            />
          </div>
          <div className="flex items-center justify-between pt-4 border-t border-surface-800">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${dbConnected ? "bg-success" : "bg-surface-600"}`} />
              <span className="text-sm text-surface-400">
                {dbConnected ? "Connected" : "Not connected"}
              </span>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setShowDbConfig(false)}>Cancel</Button>
              <Button variant="primary" onClick={saveDbConfig} loading={busy}>
                <Icons.Database /> Connect & Analyze
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      <div className="relative max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <header className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-400 to-accent-600 flex items-center justify-center shadow-glow-md">
                  <Icons.Database />
                </div>
                <Badge variant="primary">AP Semantic Engine</Badge>
              </div>
              <h1 className="font-display text-4xl lg:text-5xl font-bold text-white tracking-tight">
                Natural Language to <span className="text-gradient">Safe SQL</span>
            </h1>
              <p className="text-surface-400 mt-3 max-w-2xl text-lg">
                Transform questions into validated, deterministic SQL with full audit trails.
            </p>
          </div>
            <div className="flex items-center gap-3">
              <Button variant="danger" onClick={clearAllData} title="Clear all data">
                <Icons.Trash /> Clear All
              </Button>
              <Button variant="secondary" onClick={() => setShowDbConfig(true)} title="Configure database">
                <Icons.Database /> {dbConfig.database || "Configure DB"}
              </Button>
              <Link to="/history" className="inline-flex items-center gap-2 px-4 py-2.5 text-sm rounded-xl font-medium bg-surface-800 hover:bg-surface-700 text-surface-200 border border-surface-700 transition-all duration-200">
                <Icons.Table /> History ({queryHistory.length})
              </Link>
              <Button variant="secondary" onClick={() => loadSampleQuestions(false)} loading={questionsLoading}><Icons.Chat /> Questions</Button>
              <Button variant="primary" onClick={refreshAndAnalyze} loading={busy || analyzing}><Icons.Sparkles /> Auto-Analyze</Button>
            </div>
          </div>
        </header>

        {/* Pipeline Flow Diagram */}
        <Card className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-semibold text-white text-lg flex items-center gap-2">
              <Icons.Lightning /> Query Pipeline
            </h3>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-surface-400 cursor-pointer">
                <input type="checkbox" checked={executeQuery} onChange={(e) => setExecuteQuery(e.target.checked)} className="rounded bg-surface-800 border-surface-600" />
                Execute Query
              </label>
              <label className="flex items-center gap-2 text-sm text-surface-400 cursor-pointer">
                <input type="checkbox" checked={includeNarration} onChange={(e) => setIncludeNarration(e.target.checked)} className="rounded bg-surface-800 border-surface-600" />
                Include Narration
              </label>
          </div>
          </div>
          <div className="flex items-center gap-1 overflow-x-auto pb-2">
            {PIPELINE_STEPS.map((step, i) => (
              <PipelineStep key={step.id} step={step} status={pipelineSteps[step.id]} isLast={i === PIPELINE_STEPS.length - 1} />
            ))}
          </div>
        </Card>

        {/* Query Input */}
        <Card icon={<Icons.Sparkles />} title="Ask Your Question" subtitle="Enter a natural language query about your data" className="mb-8">
          <div className="space-y-4">
            <textarea
              className="textarea text-lg"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Show me all invoices over $10,000 from last quarter for tenant 42"
            />
            <div className="flex flex-wrap items-center gap-4">
              <Button variant="primary" size="lg" onClick={runPipeline} loading={pipelineRunning} disabled={!question.trim()}>
                <Icons.Play /> Run Full Pipeline
              </Button>
              {pipelineResult?.intent && (
                <Badge variant={pipelineResult.intent === "unknown" ? "warning" : "success"}>
                  Intent: {pipelineResult.intent}
                </Badge>
              )}
              {pipelineResult && <ExecutionStats result={pipelineResult} />}
            </div>
{pipelineResult?.database_info && (
              <DatabaseStatus info={pipelineResult.database_info} />
            )}
          </div>
        </Card>

        {/* Sample Questions Panel */}
        {showQuestionsPanel && sampleQuestions && (
          <Card 
            icon={<Icons.Chat />} 
            title="Sample Questions" 
            subtitle={`${sampleQuestions.total} questions across ${sampleQuestions.categories?.length || 0} categories`}
            className="mb-8"
            actions={
              <div className="flex items-center gap-2">
                <Button size="sm" variant="secondary" onClick={() => loadSampleQuestions(true)} loading={questionsLoading}>
                  <Icons.Sparkles /> Generate AI Questions
                </Button>
                <Button size="sm" variant="secondary" onClick={exportQuestionsToText}>
                  <Icons.Download /> Export
                </Button>
                <IconButton icon={<Icons.X />} onClick={() => setShowQuestionsPanel(false)} title="Close" />
              </div>
            }
          >
            <div className="space-y-4">
              {/* Category Filter */}
              <div className="flex flex-wrap gap-2">
            <button
                  onClick={() => setSelectedCategory("All")}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    selectedCategory === "All" 
                      ? "bg-accent-500 text-white" 
                      : "bg-surface-800 text-surface-400 hover:text-white"
                  }`}
                >
                  All ({sampleQuestions.total})
            </button>
                {sampleQuestions.categories?.map((cat) => (
            <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      selectedCategory === cat 
                        ? "bg-accent-500 text-white" 
                        : "bg-surface-800 text-surface-400 hover:text-white"
                    }`}
                  >
                    {cat} ({sampleQuestions.by_category?.[cat]?.length || 0})
            </button>
                ))}
          </div>
              
              {/* Questions List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[400px] overflow-auto pr-2">
                {filteredQuestions.map((q, i) => (
                  <div 
                    key={i} 
                    className="p-4 rounded-xl bg-surface-800/40 border border-surface-700/40 hover:border-accent-500/40 transition-all cursor-pointer group"
                    onClick={() => useQuestionTemplate(q)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm text-surface-200 leading-relaxed group-hover:text-white transition-colors">
                        {q.question}
                      </p>
                      <Icons.Play />
          </div>
                    {q.data_hint && (
                        <p className="text-xs text-surface-500 mt-1 italic">{q.data_hint}</p>
                      )}
                      <div className="flex items-center gap-2 mt-3">
                        <Badge variant="neutral" className="text-[10px]">{q.category}</Badge>
                        {q.requires_tenant && <Badge variant="warning" className="text-[10px]">tenant_id</Badge>}
                        {q.requires_user && <Badge variant="info" className="text-[10px]">user_id</Badge>}
                      </div>
                    </div>
                  ))}
              </div>
              
              <div className="flex items-center justify-between pt-3 border-t border-surface-800">
                <p className="text-xs text-surface-500">
                  💡 Click any question to use it as a template. Remember: <span className="text-warning">tenant_id</span> is mandatory in all queries.
                </p>
                <Button size="sm" variant="ghost" onClick={exportFullSession} disabled={!pipelineResult}>
                  <Icons.Download /> Export Full Session
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Validation Errors */}
        {pipelineResult?.validation_errors && (
          <Card className="mb-8">
            <ValidationErrors 
              errors={pipelineResult.validation_errors} 
              warnings={pipelineResult.validation_warnings} 
            />
          </Card>
        )}

        {/* Pipeline Results */}
        {pipelineResult && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Query Plan */}
            <Card
              icon={<Icons.Code />}
              title="Generated Plan"
              subtitle="Structured JSON query plan"
              actions={
                pipelineResult.plan && (
                  <>
                    <IconButton icon={<Icons.Expand />} onClick={() => setShowPlanModal(true)} title="View Full Plan" variant="accent" />
                    <IconButton icon={<Icons.Copy />} onClick={() => copyToClipboard(planJson, "Plan")} title="Copy Plan" />
                    <IconButton icon={<Icons.Download />} onClick={() => downloadJson(pipelineResult.plan, `query-plan-${Date.now()}.json`)} title="Download JSON" />
                  </>
                )
              }
            >
              {pipelineResult.plan ? (
                <div className="code-block max-h-[300px] overflow-hidden relative">
                  <pre className="text-sm">{planJson}</pre>
                  <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-surface-950 to-transparent pointer-events-none" />
            </div>
              ) : (
                <p className="text-surface-500">No plan generated</p>
              )}
              {pipelineResult.plan && (
                <Button size="sm" variant="ghost" onClick={() => setShowPlanModal(true)} className="mt-3">
                  <Icons.Expand /> View Full Plan
                </Button>
              )}
          </Card>

            {/* Compiled SQL */}
            <Card
              icon={<Icons.Shield />}
              title="Compiled SQL"
              subtitle="Safe, parameterized SQL"
              actions={
                pipelineResult.sql && (
                  <>
                    <IconButton icon={<Icons.Expand />} onClick={() => setShowSqlModal(true)} title="View Full SQL" variant="accent" />
                    <IconButton icon={<Icons.Copy />} onClick={() => copyToClipboard(sqlText, "SQL")} title="Copy SQL" />
                    <IconButton icon={<Icons.Download />} onClick={() => downloadSql(sqlText, `query-${Date.now()}.sql`)} title="Download SQL" />
                  </>
                )
              }
            >
              {pipelineResult.sql ? (
                <div className="space-y-4">
                  <div className="code-block max-h-[200px] overflow-hidden relative">
                    <pre className="text-secondary-300">{sqlText}</pre>
                    <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-surface-950 to-transparent pointer-events-none" />
              </div>
                  {pipelineResult.params?.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {pipelineResult.params.map((p, i) => (
                        <Badge key={i} variant="secondary">{p[0]}: {p[1]}</Badge>
                      ))}
                    </div>
                  )}
                  {pipelineResult.audit_id && (
                    <p className="text-xs text-surface-500 flex items-center gap-2">
                      <Icons.Shield /> Audit ID: {pipelineResult.audit_id}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-surface-500">No SQL generated</p>
              )}
              {pipelineResult.sql && (
                <Button size="sm" variant="ghost" onClick={() => setShowSqlModal(true)} className="mt-3">
                  <Icons.Expand /> View Full SQL
                </Button>
              )}
            </Card>
          </div>
        )}

        {/* Query Results */}
        {pipelineResult?.results && (
          <Card
            icon={<Icons.Table />}
            title="Query Results"
            subtitle={`${pipelineResult.results?.row_count ?? 0} rows returned${pipelineResult.results?.truncated ? " (truncated)" : ""}`}
            className="mb-8"
            actions={
              <Button size="sm" variant="secondary" onClick={() => downloadJson(pipelineResult.results.rows, `results-${Date.now()}.json`)}>
                <Icons.Download /> Export Results
              </Button>
            }
          >
            <ResultsTable columns={pipelineResult.results.columns} rows={pipelineResult.results.rows} />
          </Card>
        )}

        {/* Narration */}
        {pipelineResult?.narration && (
          <Card
            icon={<Icons.Chat />}
            title="AI Explanation"
            subtitle="Natural language summary of results"
            className="mb-8"
            actions={
              <IconButton icon={<Icons.Copy />} onClick={() => copyToClipboard(pipelineResult.narration, "Narration")} title="Copy Narration" />
            }
          >
            <div className="bg-surface-800/50 rounded-xl p-5 border border-surface-700/50">
              <p className="text-surface-200 leading-relaxed">{pipelineResult.narration}</p>
            </div>
          </Card>
        )}

        {/* Schema & Configuration */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Schema & Mappings */}
          <Card icon={<Icons.Database />} title="Schema & Mappings" className="lg:col-span-2">
            <div className="flex gap-1 p-1 bg-surface-800/50 rounded-xl mb-5">
              {["tables", "columns", "enums"].map((tab) => (
                <button key={tab} onClick={() => setActiveTab(tab)} className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab ? "bg-surface-700 text-white" : "text-surface-400 hover:text-surface-200"}`}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {activeTab === "tables" && (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-3 max-h-[200px] overflow-auto pr-2">
                {schema.map((t) => (
                    <div key={t.name} className="p-3 rounded-xl bg-surface-800/40 border border-surface-700/40 hover:border-surface-600/60 transition-all">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white text-sm">{t.name}</span>
                        <Badge variant={mappings.tables.find((m) => m.table === t.name) ? "success" : "neutral"} className="text-[10px]">
                        {mappings.tables.find((m) => m.table === t.name)?.role || "unmapped"}
                        </Badge>
                    </div>
                  </div>
                ))}
                  {schema.length === 0 && <div className="col-span-2 text-center py-8 text-surface-500">Click "Introspect Schema" to load tables</div>}
              </div>
                <div className="divider" />
                <p className="section-title">Map Table</p>
                <div className="grid grid-cols-2 gap-3">
                  <select className="select" value={tableMapping.table} onChange={(e) => setTableMapping({ ...tableMapping, table: e.target.value })}>
                    <option value="">Select table</option>
                    {tables.map((t) => <option key={t}>{t}</option>)}
                  </select>
                  <select className="select" value={tableMapping.role} onChange={(e) => setTableMapping({ ...tableMapping, role: e.target.value })}>
                    <option value="fact">Fact Table</option>
                    <option value="dimension">Dimension</option>
                  </select>
                  <input className="input" placeholder="Tenant column" value={tableMapping.tenant_column} onChange={(e) => setTableMapping({ ...tableMapping, tenant_column: e.target.value })} />
                  <input className="input" placeholder="Business meaning" value={tableMapping.business_name} onChange={(e) => setTableMapping({ ...tableMapping, business_name: e.target.value })} />
                </div>
                <Button variant="primary" onClick={saveTable} disabled={!tableMapping.table}><Icons.Check /> Save Mapping</Button>
              </div>
            )}

            {activeTab === "columns" && (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-3">
                  <select className="select" value={columnMapping.table} onChange={(e) => setColumnMapping({ ...columnMapping, table: e.target.value, column: "" })}>
                    <option value="">Select table</option>
                    {tables.map((t) => <option key={t}>{t}</option>)}
                  </select>
                  <select className="select" value={columnMapping.column} onChange={(e) => setColumnMapping({ ...columnMapping, column: e.target.value })}>
                    <option value="">Select column</option>
                    {selectedTableColumns.map((c) => <option key={c.name}>{c.name}</option>)}
                  </select>
                  <input className="input col-span-2" placeholder="Business meaning" value={columnMapping.business_meaning} onChange={(e) => setColumnMapping({ ...columnMapping, business_meaning: e.target.value })} />
                </div>
                <Button variant="primary" onClick={saveColumn} disabled={!columnMapping.table || !columnMapping.column}><Icons.Check /> Save Column</Button>
              </div>
            )}

            {activeTab === "enums" && (
              <div className="space-y-3 max-h-[250px] overflow-auto">
                {enums.length > 0 ? enums.map((e, i) => (
                  <div key={i} className="p-3 rounded-xl bg-surface-800/40 border border-surface-700/40">
                    <div className="font-medium text-white text-sm">{e.table}.{e.column}</div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {e.values.map((v) => <Badge key={v} variant="neutral" className="text-[10px]">{v}</Badge>)}
                    </div>
                  </div>
                )) : <div className="text-center py-8 text-surface-500">No enum columns detected</div>}
                </div>
              )}
          </Card>

          {/* Query History */}
          <Card 
            icon={<Icons.Table />} 
            title="Query History" 
            subtitle={`${queryHistory.length} queries stored`}
            actions={
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => exportHistory("json")}>
                  <Icons.Download /> JSON
                </Button>
                <Button size="sm" variant="secondary" onClick={() => exportHistory("csv")}>
                  <Icons.Download /> CSV
                </Button>
                {queryHistory.length > 0 && (
                  <Button size="sm" variant="danger" onClick={clearHistory}>
                    <Icons.Trash />
                  </Button>
                )}
              </div>
            }
          >
            <div className="space-y-3 max-h-[300px] overflow-auto">
              {queryHistory.length > 0 ? queryHistory.slice(0, 10).map((item, i) => (
                <div key={item.id || i} className="p-3 rounded-xl bg-surface-800/40 border border-surface-700/40">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="text-sm text-white font-medium truncate">{item.question}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant={item.success ? "success" : "error"} className="text-[10px]">
                          {item.success ? "Success" : "Failed"}
                        </Badge>
                        <span className="text-[10px] text-surface-500">{item.database}</span>
                        <span className="text-[10px] text-surface-500">{item.row_count || 0} rows</span>
                        <span className="text-[10px] text-surface-500">{item.execution_time_ms}ms</span>
                      </div>
                </div>
                <button
                      onClick={() => { setQuestion(item.question); notify("Question loaded", "info"); }}
                      className="text-surface-400 hover:text-accent-400 transition-colors"
                      title="Use this question"
                    >
                      <Icons.Play />
                </button>
              </div>
                    </div>
              )) : (
                <p className="text-center py-8 text-surface-500">No query history yet. Run some queries to see them here.</p>
              )}
              {queryHistory.length > 10 && (
                <p className="text-center text-surface-500 text-xs">Showing 10 of {queryHistory.length} queries</p>
              )}
            </div>
          </Card>
        </div>

        {/* Table Documentation Section */}
        <Card 
          icon={<Icons.Table />} 
          title="Table Documentation" 
          subtitle="Generate comprehensive documentation for your tables"
          className="mb-8"
          actions={
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={loadDocumentation} loading={docLoading}>
                <Icons.ArrowPath /> Generate
              </Button>
              {tableDocumentation && (
                <Button size="sm" variant="ghost" onClick={exportDocumentation}>
                  <Icons.Download /> Export
                </Button>
              )}
              </div>
          }
        >
          {!tableDocumentation ? (
            <div className="text-center py-8 text-surface-500">
              <p>Click "Generate" to create table documentation</p>
              <p className="text-xs mt-2 text-surface-600">Includes: Purpose, Columns, Possible Values, Frequent Queries, Join Columns</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-xs text-surface-400">
                <Badge variant="info">{tableDocumentation.tables?.length || 0} tables</Badge>
                <span>Database: {tableDocumentation.database}</span>
                <span>Dialect: {tableDocumentation.dialect}</span>
              </div>
              
              <div className="space-y-3 max-h-[400px] overflow-auto pr-2">
                {tableDocumentation.tables?.map((table, i) => (
                  <div key={i} className="p-4 rounded-xl bg-surface-800/40 border border-surface-700/40 space-y-3">
                    {/* Table Header */}
                    <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-white">{table.table_name}</h4>
                          {table.role && <Badge variant={table.role === "fact" ? "primary" : "secondary"}>{table.role}</Badge>}
                      </div>
                        <p className="text-xs text-surface-400 mt-1">{table.purpose}</p>
                    </div>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => generateAiDocumentation(table.table_name)}
                        loading={selectedDocTable === table.table_name}
                        title="Generate AI documentation"
                      >
                        <Icons.Sparkles />
                      </Button>
                  </div>
                    
                    {/* AI Documentation if available */}
                    {table.ai_documentation && (
                      <div className="p-3 rounded-lg bg-accent-500/10 border border-accent-500/20">
                        <div className="text-xs font-semibold text-accent-400 mb-1">AI Analysis</div>
                        <p className="text-xs text-surface-300">{table.ai_documentation.purpose}</p>
              </div>
                    )}
                    
                    {/* Columns */}
                    <div>
                      <div className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Columns ({table.columns?.length || 0})</div>
                      <div className="flex flex-wrap gap-1.5">
                        {table.columns?.slice(0, 8).map((col, ci) => (
                          <span 
                            key={ci} 
                            className={`text-xs px-2 py-1 rounded-md ${
                              col.is_primary ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                              col.is_foreign ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                              'bg-surface-700/50 text-surface-300'
                            }`}
                            title={`${col.data_type}${col.possible_values ? ` - Values: ${col.possible_values}` : ''}${col.description ? ` - ${col.description}` : ''}`}
                          >
                            {col.name}
                            {col.is_primary && <span className="ml-1 text-amber-500">🔑</span>}
                            {col.is_foreign && <span className="ml-1 text-blue-500">🔗</span>}
                    </span>
                ))}
                        {table.columns?.length > 8 && (
                          <span className="text-xs px-2 py-1 text-surface-500">+{table.columns.length - 8} more</span>
                        )}
              </div>
            </div>
                    
                    {/* Frequent Queries */}
                    {table.frequent_queries?.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Frequent Queries</div>
                        <ul className="space-y-1">
                          {table.frequent_queries.slice(0, 3).map((q, qi) => (
                            <li key={qi} className="text-xs text-surface-300 flex items-start gap-2">
                              <span className="text-accent-400">•</span>
                              {q}
                            </li>
                          ))}
                        </ul>
        </div>
                    )}
                    
                    {/* Join Columns */}
                    {table.join_columns?.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Join Columns</div>
                        <div className="flex flex-wrap gap-2">
                          {table.join_columns.map((j, ji) => (
                            <span key={ji} className="text-xs px-2 py-1 rounded-md bg-info/10 text-info border border-info/20">
                              {j.column} → {j.joins_to}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
            </div>
                ))}
                </div>
              </div>
            )}
          </Card>

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-surface-800/50 text-center text-surface-500 text-sm">
          <p>AP Semantic Query Engine • Secure, Auditable, Deterministic</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
