import { useState, useEffect } from "react";
import { fetchRecentGraphs, fetchDatasetChanges } from "../api";

function formatRelativeTime(dateString) {
  if (!dateString) return "Recently";
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffSec = Math.floor((now - date) / 1000);
    if (diffSec < 60) return "Just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "Recently";
  }
}

function formatBytes(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function HomePage({
  sessions = [],
  availableDatasets = [],
  onSelectSession,
  onNewChat,
  onDeleteSession,
  darkMode,
  setDarkMode,
  selectedModel = "groq",
}) {
  const [recentGraphs, setRecentGraphs] = useState([]);
  const [datasetChanges, setDatasetChanges] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      fetchRecentGraphs(6).catch(() => []),
      fetchDatasetChanges().catch(() => []),
    ]).then(([graphs, changes]) => {
      if (isMounted) {
        setRecentGraphs(graphs || []);
        setDatasetChanges(changes || []);
        setIsLoading(false);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [sessions, availableDatasets]);

  // Aggregate Metrics
  const totalRows = availableDatasets.reduce((acc, d) => acc + (d.rows || 0), 0);
  const totalDatasets = availableDatasets.length;
  const totalWorkspaces = sessions.length;
  const totalVisualizations = recentGraphs.length;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-surface-50/50 dark:bg-gray-950 text-surface-800 dark:text-gray-100 select-none">
      {/* Compact Top Navigation Bar */}
      <header className="flex items-center justify-between px-5 py-2.5 border-b border-surface-200 dark:border-gray-800 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md sticky top-0 z-20 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center text-white shadow-xs font-bold text-xs tracking-wider">
            V
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-bold text-surface-900 dark:text-gray-100">
                Visiq Analytics
              </h2>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            </div>
            <p className="text-[10px] text-surface-400 dark:text-gray-500 leading-none">
              {totalWorkspaces} chats • {totalDatasets} datasets ({totalRows.toLocaleString()} rows)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Active Model Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-md bg-surface-100 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-[10px] font-mono text-surface-600 dark:text-gray-300">
            <span className="font-semibold text-accent">Model:</span>
            <span>{selectedModel === "groq" ? "Groq 70B" : "Gemini 2.5"}</span>
          </div>

          {/* New Chat Button */}
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent text-white hover:opacity-90 shadow-xs text-xs font-semibold transition-all cursor-pointer"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span>New Chat</span>
          </button>

          {/* Dark / Light Toggle */}
          <button
            type="button"
            onClick={() => setDarkMode((prev) => !prev)}
            className="p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-500 dark:text-gray-400 transition-colors cursor-pointer"
            title={darkMode ? "Light Mode" : "Dark Mode"}
          >
            {darkMode ? (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      {/* Main Compact Content Container */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-5 py-4 space-y-4">
        {/* Compact Quick Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <div className="px-3.5 py-2 rounded-xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-2xs flex items-center justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-surface-400 dark:text-gray-500">
                Workspaces
              </p>
              <p className="text-base font-bold text-surface-900 dark:text-gray-100">
                {totalWorkspaces}
              </p>
            </div>
            <span className="w-7 h-7 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.502 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
              </svg>
            </span>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-2xs flex items-center justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-surface-400 dark:text-gray-500">
                Datasets
              </p>
              <p className="text-base font-bold text-surface-900 dark:text-gray-100">
                {totalDatasets} <span className="text-[11px] font-normal text-surface-400 dark:text-gray-500">({totalRows.toLocaleString()} rows)</span>
              </p>
            </div>
            <span className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h17.25" />
              </svg>
            </span>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-2xs flex items-center justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-surface-400 dark:text-gray-500">
                Visual Graphs
              </p>
              <p className="text-base font-bold text-surface-900 dark:text-gray-100">
                {totalVisualizations}
              </p>
            </div>
            <span className="w-7 h-7 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </span>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-2xs flex items-center justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-surface-400 dark:text-gray-500">
                Memory State
              </p>
              <p className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                Synchronized
              </p>
            </div>
            <span className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </span>
          </div>
        </div>

        {/* Section 1: Recent Graphs (Visual Insights Showcase) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
              </svg>
              <h3 className="text-xs font-bold text-surface-900 dark:text-gray-100 uppercase tracking-wide">
                Recent Graphs
              </h3>
            </div>
            {recentGraphs.length > 0 && (
              <span className="text-[10px] text-surface-400 dark:text-gray-500">
                Click graph to jump into conversation
              </span>
            )}
          </div>

          {isLoading ? (
            <div className="h-28 flex items-center justify-center rounded-xl border border-surface-200 dark:border-gray-800 bg-white/40 dark:bg-gray-900/40">
              <span className="text-xs text-surface-400">Loading graphs...</span>
            </div>
          ) : recentGraphs.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
              {recentGraphs.map((graph, idx) => (
                <div
                  key={`${graph.session_id}-${idx}`}
                  onClick={() => onSelectSession && onSelectSession(graph.session_id)}
                  className="group rounded-xl border border-surface-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-accent/50 dark:hover:border-accent/50 hover:shadow-sm transition-all cursor-pointer overflow-hidden flex flex-col justify-between"
                >
                  {/* Compact Preview Thumbnail */}
                  <div className="h-28 w-full bg-surface-50 dark:bg-gray-950/70 flex items-center justify-center p-2 overflow-hidden border-b border-surface-100 dark:border-gray-800/60">
                    {graph.chart_svg ? (
                      <div
                        className="w-full h-full flex items-center justify-center pointer-events-none [&>svg]:w-full [&>svg]:h-full [&>svg]:max-h-24 object-contain"
                        dangerouslySetInnerHTML={{ __html: graph.chart_svg }}
                      />
                    ) : graph.chart_base64 ? (
                      <img
                        src={
                          graph.chart_base64.startsWith("data:")
                            ? graph.chart_base64
                            : `data:image/png;base64,${graph.chart_base64}`
                        }
                        alt={graph.prompt}
                        className="w-full h-full object-contain pointer-events-none group-hover:scale-102 transition-transform duration-150"
                      />
                    ) : (
                      <div className="text-[10px] text-surface-400">Chart Insight</div>
                    )}
                  </div>

                  {/* Compact Caption */}
                  <div className="p-2.5 space-y-1">
                    <p className="text-[11px] font-semibold text-surface-800 dark:text-gray-100 truncate group-hover:text-accent transition-colors">
                      {graph.prompt || "Visual Insight"}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-surface-400 dark:text-gray-500 font-mono">
                      <span className="truncate max-w-[120px]">{graph.dataset_name}</span>
                      <span className="text-accent font-medium text-[9px] uppercase tracking-wider group-hover:underline">
                        Open &rarr;
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-dashed border-surface-200 dark:border-gray-800 bg-white/40 dark:bg-gray-900/40 text-center flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-left">
                <span className="w-8 h-8 rounded-lg bg-surface-100 dark:bg-gray-800 text-surface-400 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
                  </svg>
                </span>
                <div>
                  <p className="text-xs font-semibold text-surface-800 dark:text-gray-200">
                    No visual graphs generated yet
                  </p>
                  <p className="text-[10px] text-surface-400 dark:text-gray-500">
                    Ask a question in any chat workspace to automatically generate distribution, bar, and trend charts.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onNewChat}
                className="px-3 py-1 text-[11px] font-semibold text-accent hover:underline cursor-pointer shrink-0"
              >
                + Start Analysis
              </button>
            </div>
          )}
        </div>

        {/* Section 2: Two-Column Bento (Recent Chats & Recent Changes) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: Recent Chats */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.502 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                </svg>
                <h3 className="text-xs font-bold text-surface-900 dark:text-gray-100 uppercase tracking-wide">
                  Recent Chats
                </h3>
              </div>
              <span className="text-[10px] text-surface-400 dark:text-gray-500">
                {sessions.length} workspaces
              </span>
            </div>

            {sessions.length > 0 ? (
              <div className="space-y-1.5 max-h-80 overflow-y-auto pr-0.5">
                {sessions.slice(0, 5).map((s) => (
                  <div
                    key={s.session_id}
                    onClick={() => onSelectSession && onSelectSession(s.session_id)}
                    className="group relative p-2.5 rounded-xl border border-surface-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-accent/40 dark:hover:border-accent/40 hover:shadow-xs transition-all cursor-pointer flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                        <h4 className="text-xs font-semibold text-surface-900 dark:text-gray-100 truncate group-hover:text-accent transition-colors">
                          {s.title || "Workspace"}
                        </h4>
                      </div>
                      {s.last_message ? (
                        <p className="text-[11px] text-surface-500 dark:text-gray-400 truncate mt-0.5 pl-3">
                          "{s.last_message}"
                        </p>
                      ) : (
                        <p className="text-[10px] text-surface-400 dark:text-gray-500 font-mono mt-0.5 pl-3">
                          {s.dataset_name}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-surface-100 dark:bg-gray-800 text-surface-600 dark:text-gray-300">
                        {s.message_count ? `${s.message_count} msgs` : "new"}
                      </span>
                      {onDeleteSession && sessions.length > 1 && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSession(s.session_id);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-surface-400 hover:text-red-600 transition-opacity"
                          title="Delete chat"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-dashed border-surface-200 dark:border-gray-800 bg-white/40 dark:bg-gray-900/40 text-center">
                <p className="text-xs text-surface-500">No active chats. Start one now!</p>
              </div>
            )}
          </div>

          {/* Right: Recent Dataset Changes & Transformations */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
                <h3 className="text-xs font-bold text-surface-900 dark:text-gray-100 uppercase tracking-wide">
                  Recent Changes
                </h3>
              </div>
              <span className="text-[10px] text-surface-400 dark:text-gray-500">
                Activity audit log
              </span>
            </div>

            {datasetChanges.length > 0 ? (
              <div className="space-y-1.5 max-h-80 overflow-y-auto pr-0.5">
                {datasetChanges.slice(0, 5).map((change, idx) => (
                  <div
                    key={change.id || idx}
                    className="p-2.5 rounded-xl border border-surface-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center justify-between gap-3 text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span
                        className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 text-[10px] font-bold ${
                          change.action === "upload"
                            ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                            : change.action === "cell_update"
                            ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                            : change.action === "add_row"
                            ? "bg-blue-500/15 text-blue-600 dark:text-blue-400"
                            : "bg-surface-200 dark:bg-gray-800 text-surface-600 dark:text-gray-300"
                        }`}
                      >
                        {change.action === "upload" ? "↑" : change.action === "cell_update" ? "✎" : change.action === "add_row" ? "+" : "✓"}
                      </span>
                      <div className="min-w-0">
                        <p className="font-medium text-surface-800 dark:text-gray-200 truncate">
                          {change.description}
                        </p>
                        <p className="text-[10px] text-surface-400 dark:text-gray-500 font-mono">
                          {change.dataset_name}
                        </p>
                      </div>
                    </div>

                    <span className="text-[10px] text-surface-400 dark:text-gray-500 whitespace-nowrap font-mono">
                      {formatRelativeTime(change.timestamp)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-dashed border-surface-200 dark:border-gray-800 bg-white/40 dark:bg-gray-900/40 text-center">
                <p className="text-xs text-surface-500">No modifications logged yet.</p>
              </div>
            )}
          </div>
        </div>

        {/* Section 3: Datasets Quick Status & Quick Query Inspiration */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Active Datasets Table (2 cols on desktop) */}
          <div className="lg:col-span-2 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h17.25" />
                </svg>
                <h3 className="text-xs font-bold text-surface-900 dark:text-gray-100 uppercase tracking-wide">
                  Active Tables
                </h3>
              </div>
              <span className="text-[10px] text-surface-400 dark:text-gray-500">
                Disk storage
              </span>
            </div>

            <div className="rounded-xl border border-surface-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden shadow-2xs">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-50 dark:bg-gray-800/60 text-surface-500 dark:text-gray-400 font-semibold border-b border-surface-200 dark:border-gray-800 text-[10px] uppercase">
                  <tr>
                    <th className="py-2 px-3">Dataset</th>
                    <th className="py-2 px-3">Rows</th>
                    <th className="py-2 px-3">Cols</th>
                    <th className="py-2 px-3">Size</th>
                    <th className="py-2 px-3 text-right">Modified</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100 dark:divide-gray-800/80">
                  {availableDatasets.map((ds) => (
                    <tr key={ds.name} className="hover:bg-surface-50/70 dark:hover:bg-gray-800/40 transition-colors">
                      <td className="py-2 px-3 font-mono font-medium text-surface-900 dark:text-gray-100 truncate max-w-[160px]">
                        {ds.name}
                      </td>
                      <td className="py-2 px-3 text-surface-600 dark:text-gray-300 font-mono">
                        {ds.rows ? ds.rows.toLocaleString() : "0"}
                      </td>
                      <td className="py-2 px-3 text-surface-600 dark:text-gray-300 font-mono">
                        {ds.columns || "0"}
                      </td>
                      <td className="py-2 px-3 text-surface-500 dark:text-gray-400 font-mono text-[11px]">
                        {formatBytes(ds.size_bytes)}
                      </td>
                      <td className="py-2 px-3 text-right text-surface-400 dark:text-gray-500 text-[11px]">
                        {formatRelativeTime(ds.modified_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Quick Query Ideas / Crucial Info for User */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.516 0c.85.493 1.509 1.333 1.509 2.316V18" />
                </svg>
                <h3 className="text-xs font-bold text-surface-900 dark:text-gray-100 uppercase tracking-wide">
                  Quick Query Ideas
                </h3>
              </div>
            </div>

            <div className="space-y-1.5">
              {[
                "Distribution of values by category",
                "Top 5 highest records with bar chart",
                "Compare year-over-year trends",
                "Find outlier rows in the dataset",
              ].map((idea, idx) => (
                <div
                  key={idx}
                  onClick={onNewChat}
                  className="p-2 rounded-xl border border-surface-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-accent/40 dark:hover:border-accent/40 text-[11px] font-medium text-surface-700 dark:text-gray-300 hover:text-accent dark:hover:text-accent transition-colors cursor-pointer flex items-center justify-between group shadow-2xs"
                >
                  <span className="truncate">{idea}</span>
                  <span className="text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                    &rarr;
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
