import { useState, useEffect, useCallback } from "react";
import {
  fetchSessionWidgets,
  createSessionWidget,
  deleteSessionWidget,
  recomputeSessionWidgets,
} from "../api";
import InteractiveChart from "./InteractiveChart";
import ChartZoomModal from "./ChartZoomModal";

export default function DashboardPanel({
  sessionId,
  datasetName,
  chartTheme = "light",
  selectedModel = "groq",
}) {
  const [widgets, setWidgets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [promptInput, setPromptInput] = useState("");
  const [selectedChartType, setSelectedChartType] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [zoomedChart, setZoomedChart] = useState(null);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  // Load session widgets
  const loadWidgets = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchSessionWidgets(sessionId);
      setWidgets(data || []);
      setLastSyncTime(new Date());
    } catch (err) {
      setErrorMessage(err.message || "Failed to load dashboard widgets");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Initial load
  useEffect(() => {
    loadWidgets();
  }, [loadWidgets]);

  // Real-time recompute against active dataset with ZERO AI calls
  const handleSyncNow = async () => {
    if (!sessionId) return;
    setIsSyncing(true);
    setErrorMessage(null);
    try {
      const updated = await recomputeSessionWidgets(sessionId, chartTheme);
      setWidgets(updated || []);
      setLastSyncTime(new Date());
    } catch (err) {
      setErrorMessage(err.message || "Failed to sync widgets");
    } finally {
      setIsSyncing(false);
    }
  };

  // Create new widget
  const handleCreateWidget = async (e) => {
    if (e) e.preventDefault();
    if (!promptInput.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const newWidget = await createSessionWidget(
        sessionId,
        promptInput.trim(),
        selectedChartType,
        chartTheme,
        selectedModel
      );
      setWidgets((prev) => [...prev, newWidget]);
      setPromptInput("");
      setSelectedChartType(null);
      setShowAddModal(false);
      setLastSyncTime(new Date());
    } catch (err) {
      setErrorMessage(err.message || "Failed to compile widget");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick preset adder
  const handleQuickAdd = async (presetPrompt, presetChartType) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const newWidget = await createSessionWidget(
        sessionId,
        presetPrompt,
        presetChartType,
        chartTheme,
        selectedModel
      );
      setWidgets((prev) => [...prev, newWidget]);
      setLastSyncTime(new Date());
    } catch (err) {
      setErrorMessage(err.message || "Failed to compile quick widget");
    } finally {
      setIsLoading(false);
    }
  };

  // Delete widget
  const handleDeleteWidget = async (widgetId) => {
    try {
      await deleteSessionWidget(sessionId, widgetId);
      setWidgets((prev) => prev.filter((w) => w.id !== widgetId));
    } catch (err) {
      setErrorMessage(err.message || "Failed to remove widget");
    }
  };

  // Split widgets into KPI metrics and Charts
  const kpiWidgets = widgets.filter((w) => w.widget_type === "kpi" || (!w.chart_svg && !w.chart_base64 && w.metric_value));
  const chartWidgets = widgets.filter((w) => w.chart_svg || w.chart_base64);

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-surface-50 dark:bg-gray-950 overflow-y-auto">
      {/* Top Dashboard Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 bg-white dark:bg-gray-900 border-b border-surface-200 dark:border-gray-700 shrink-0 select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-accent/10 text-accent">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-surface-900 dark:text-gray-100">
                  Live Analytics Dashboard
                </h2>
                <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Real-Time Aligned
                </span>
              </div>
              <p className="text-[11px] text-surface-500 dark:text-gray-400">
                {datasetName} • {widgets.length} {widgets.length === 1 ? "widget" : "widgets"}
                {lastSyncTime && ` • Synced ${lastSyncTime.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleSyncNow}
            disabled={isSyncing || isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-surface-100 dark:bg-gray-800 hover:bg-surface-200 dark:hover:bg-gray-700 border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-200 transition-colors cursor-pointer shadow-xs disabled:opacity-50"
            title="Recompute all visual widgets against updated spreadsheet data (0 LLM tokens)"
          >
            <svg
              className={`w-3.5 h-3.5 text-accent ${isSyncing ? "animate-spin" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            <span>{isSyncing ? "Syncing..." : "Sync with Data"}</span>
          </button>

          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-accent text-white hover:opacity-90 transition-opacity cursor-pointer shadow-xs"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span>Add Visual Widget</span>
          </button>
        </div>
      </div>

      {/* Error banner */}
      {errorMessage && (
        <div className="px-6 py-2 bg-rose-50 dark:bg-rose-950/40 border-b border-rose-200 dark:border-rose-800/80 text-rose-800 dark:text-rose-200 text-xs flex items-center justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-rose-600 hover:opacity-75">✕</button>
        </div>
      )}

      {/* Dashboard Body */}
      <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Empty State */}
        {widgets.length === 0 && !isLoading && (
          <div className="text-center py-16 px-4 rounded-2xl border-2 border-dashed border-surface-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/60 backdrop-blur-xs">
            <div className="w-12 h-12 mx-auto rounded-xl bg-accent/10 text-accent flex items-center justify-center mb-3">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-surface-900 dark:text-gray-100">
              Your Dashboard is Ready
            </h3>
            <p className="mt-1 text-xs text-surface-500 dark:text-gray-400 max-w-md mx-auto leading-relaxed">
              Create live visual widgets or pin graphs from your chats. Whenever you edit cells in the Spreadsheet, all dashboard widgets update in real-time.
            </p>

            {/* Quick Starter Suggestions */}
            <div className="mt-6 max-w-lg mx-auto">
              <div className="text-[11px] font-semibold text-surface-400 dark:text-gray-500 uppercase tracking-wider mb-2.5">
                Quick Suggested Widgets
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickAdd("Content breakdown by type", "pie")}
                  className="p-2.5 text-left rounded-lg bg-surface-100/70 dark:bg-gray-800/60 hover:bg-surface-200 dark:hover:bg-gray-700/60 border border-surface-200 dark:border-gray-700 transition-colors text-xs font-medium text-surface-700 dark:text-gray-200 flex items-center justify-between group cursor-pointer"
                >
                  <span>Content by Type</span>
                  <span className="text-accent group-hover:translate-x-0.5 transition-transform">+</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickAdd("Top 10 release years by number of titles", "bar")}
                  className="p-2.5 text-left rounded-lg bg-surface-100/70 dark:bg-gray-800/60 hover:bg-surface-200 dark:hover:bg-gray-700/60 border border-surface-200 dark:border-gray-700 transition-colors text-xs font-medium text-surface-700 dark:text-gray-200 flex items-center justify-between group cursor-pointer"
                >
                  <span>Top Release Years</span>
                  <span className="text-accent group-hover:translate-x-0.5 transition-transform">+</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickAdd("Top 5 countries by content count", "bar")}
                  className="p-2.5 text-left rounded-lg bg-surface-100/70 dark:bg-gray-800/60 hover:bg-surface-200 dark:hover:bg-gray-700/60 border border-surface-200 dark:border-gray-700 transition-colors text-xs font-medium text-surface-700 dark:text-gray-200 flex items-center justify-between group cursor-pointer"
                >
                  <span>Top Countries</span>
                  <span className="text-accent group-hover:translate-x-0.5 transition-transform">+</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickAdd("Total titles in dataset", null)}
                  className="p-2.5 text-left rounded-lg bg-surface-100/70 dark:bg-gray-800/60 hover:bg-surface-200 dark:hover:bg-gray-700/60 border border-surface-200 dark:border-gray-700 transition-colors text-xs font-medium text-surface-700 dark:text-gray-200 flex items-center justify-between group cursor-pointer"
                >
                  <span>Total Record Count</span>
                  <span className="text-accent group-hover:translate-x-0.5 transition-transform">+</span>
                </button>
              </div>
            </div>

            <div className="mt-6">
              <button
                type="button"
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-accent text-white hover:opacity-90 transition-opacity shadow-xs cursor-pointer"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <span>Create Custom Widget</span>
              </button>
            </div>
          </div>
        )}

        {/* KPI Metrics Row */}
        {kpiWidgets.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {kpiWidgets.map((w) => (
              <div
                key={w.id}
                className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-xs relative group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-medium text-surface-500 dark:text-gray-400 truncate max-w-[80%]">
                    {w.metric_label || w.title}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDeleteWidget(w.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-surface-400 hover:text-rose-500 rounded transition-opacity"
                    title="Remove metric card"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="text-2xl font-extrabold text-surface-900 dark:text-gray-100 tracking-tight font-mono">
                  {w.metric_value || "—"}
                </div>
                <div className="mt-1 text-[10px] text-surface-400 dark:text-gray-500 truncate">
                  {w.prompt}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Visual Charts Grid */}
        {chartWidgets.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {chartWidgets.map((w) => (
              <div
                key={w.id}
                className="flex flex-col rounded-xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-xs overflow-hidden group hover:border-surface-300 dark:hover:border-gray-700 transition-all"
              >
                {/* Widget Card Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-surface-150 dark:border-gray-800/80 bg-surface-50/50 dark:bg-gray-800/40">
                  <div className="min-w-0 pr-2">
                    <h4 className="text-xs font-bold text-surface-900 dark:text-gray-100 truncate">
                      {w.title}
                    </h4>
                    <p className="text-[10px] text-surface-400 dark:text-gray-500 truncate mt-0.5">
                      {w.prompt}
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-surface-200/80 dark:bg-gray-800 text-surface-500 dark:text-gray-400 font-mono font-semibold">
                      {w.chart_type || "chart"}
                    </span>
                    <button
                      type="button"
                      onClick={() => setZoomedChart({ chart_svg: w.chart_svg, chart_base64: w.chart_base64 })}
                      className="p-1 text-surface-400 hover:text-surface-700 dark:text-gray-500 dark:hover:text-gray-200 rounded transition-colors"
                      title="Enlarge chart"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteWidget(w.id)}
                      className="p-1 text-surface-400 hover:text-rose-500 dark:text-gray-500 dark:hover:text-rose-400 rounded transition-colors"
                      title="Remove widget"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Widget Chart Body */}
                <div className="p-3 flex-1 flex items-center justify-center bg-white dark:bg-gray-900 min-h-[220px]">
                  <InteractiveChart
                    chartSvg={w.chart_svg}
                    chartBase64={w.chart_base64}
                    onZoom={() => setZoomedChart({ chart_svg: w.chart_svg, chart_base64: w.chart_base64 })}
                    compact={true}
                  />
                </div>

                {/* Card Footer */}
                <div className="px-4 py-2 border-t border-surface-150 dark:border-gray-800/80 bg-surface-50/30 dark:bg-gray-900/40 flex items-center justify-between text-[10px] text-surface-400 dark:text-gray-500 select-none">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span>Reactive Tool Recipe</span>
                  </span>
                  <span>
                    {w.last_updated ? new Date(w.last_updated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Live"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Widget Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-700 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="px-5 py-4 border-b border-surface-200 dark:border-gray-700 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-surface-900 dark:text-white">
                  Add Visual Widget
                </h3>
                <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-0.5">
                  AI generates the recipe once; the data tool keeps it live.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-surface-400 hover:text-surface-600 dark:text-gray-400 dark:hover:text-gray-200 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateWidget} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-surface-700 dark:text-gray-300 mb-1.5">
                  What do you want to visualize?
                </label>
                <textarea
                  rows={3}
                  value={promptInput}
                  onChange={(e) => setPromptInput(e.target.value)}
                  placeholder="e.g. Distribution of TV shows vs movies, Top 5 genres, Content added per year..."
                  className="w-full px-3 py-2 text-xs bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-xl text-surface-900 dark:text-white placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent resize-none"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-surface-700 dark:text-gray-300 mb-1.5">
                  Chart Format
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { label: "Auto", value: null },
                    { label: "Bar", value: "bar" },
                    { label: "Line", value: "line" },
                    { label: "Pie", value: "pie" },
                  ].map((opt) => (
                    <button
                      key={opt.label}
                      type="button"
                      onClick={() => setSelectedChartType(opt.value)}
                      className={`py-2 px-2 text-xs font-medium rounded-lg border transition-all cursor-pointer text-center ${
                        selectedChartType === opt.value
                          ? "bg-accent text-white border-accent shadow-xs font-semibold"
                          : "bg-surface-50 dark:bg-gray-800 border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-700"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!promptInput.trim() || isSubmitting}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-accent text-white hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {isSubmitting ? (
                    <>
                      <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                      </svg>
                      <span>Generating Widget...</span>
                    </>
                  ) : (
                    <span>Add to Dashboard</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Enlarge / Zoom Modal */}
      {zoomedChart && (
        <ChartZoomModal
          chartBase64={zoomedChart.chart_base64}
          chartSvg={zoomedChart.chart_svg}
          onClose={() => setZoomedChart(null)}
        />
      )}
    </div>
  );
}
