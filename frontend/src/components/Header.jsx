import { useState } from "react";
import ConfirmModal from "./ConfirmModal";

export default function Header({
  activeTab = "chat",
  onTabChange,
  chartType,
  chartEnabled,
  onChartTypeChange,
  onChartEnabledChange,
  onClearChat,
  darkMode,
  setDarkMode,
  activeModel,
  selectedModel,
  onSelectedModelChange,
  chartTheme,
  onChartThemeChange,
  activeDatasetName,
  currentUser,
  userQuota,
  onOpenAuthModal,
  onStartTour,
  guestQueriesRemaining = 5,
}) {
  const [showClearModal, setShowClearModal] = useState(false);
  const options = [
    { label: "Auto", value: null },
    { label: "Bar", value: "bar" },
    { label: "Line", value: "line" },
    { label: "Pie", value: "pie" },
  ];

  const handleClearClick = () => setShowClearModal(true);

  const handleConfirmClear = () => {
    onClearChat();
    setShowClearModal(false);
  };

  const handleCancelClear = () => setShowClearModal(false);

  return (
    <header className="flex flex-col border-b border-surface-200 dark:border-gray-800 bg-white dark:bg-gray-900 shrink-0">
      {/* Row 1: Workspace Identity, Tab Navigation & User Status */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 px-4 py-2 border-b border-surface-100 dark:border-gray-800/80">
        {/* Left: Active Dataset Badge */}
        <div className="flex items-center gap-2 shrink-0">
          <div
            data-tour="active-dataset"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-200 text-xs font-medium select-none shadow-2xs"
            title="Active dataset locked to this workspace"
          >
            <svg className="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
            </svg>
            <span className="font-mono text-[11px] font-semibold max-w-[130px] sm:max-w-[180px] truncate">{activeDatasetName || "No dataset"}</span>
          </div>
        </div>

        {/* Center: Segmented Tab Switcher with Uniform Heights & Full Active Backgrounds */}
        <div className="flex justify-center items-center">
          <div
            data-tour="tab-switcher"
            className="inline-flex items-stretch p-0.5 rounded-lg bg-surface-100 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 select-none shadow-2xs"
          >
            <button
              type="button"
              onClick={() => onTabChange && onTabChange("chat")}
              className={`h-7 sm:h-8 flex items-center justify-center gap-1.5 px-3 sm:px-3.5 text-xs rounded-md transition-all cursor-pointer whitespace-nowrap leading-none ${
                activeTab === "chat"
                  ? "bg-white dark:bg-gray-700 text-surface-900 dark:text-white shadow-xs font-semibold"
                  : "text-surface-500 dark:text-gray-400 hover:text-surface-800 dark:hover:text-gray-200 font-medium"
              }`}
            >
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v5.518z" />
              </svg>
              <span>Chat & Insights</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange && onTabChange("spreadsheet")}
              className={`h-7 sm:h-8 flex items-center justify-center gap-1.5 px-3 sm:px-3.5 text-xs rounded-md transition-all cursor-pointer whitespace-nowrap leading-none ${
                activeTab === "spreadsheet"
                  ? "bg-white dark:bg-gray-700 text-surface-900 dark:text-white shadow-xs font-semibold"
                  : "text-surface-500 dark:text-gray-400 hover:text-surface-800 dark:hover:text-gray-200 font-medium"
              }`}
            >
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h17.25" />
              </svg>
              <span>Spreadsheet</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange && onTabChange("dashboard")}
              className={`h-7 sm:h-8 flex items-center justify-center gap-1.5 px-3 sm:px-3.5 text-xs rounded-md transition-all cursor-pointer whitespace-nowrap leading-none ${
                activeTab === "dashboard"
                  ? "bg-white dark:bg-gray-700 text-surface-900 dark:text-white shadow-xs font-semibold"
                  : "text-surface-500 dark:text-gray-400 hover:text-surface-800 dark:hover:text-gray-200 font-medium"
              }`}
            >
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
              </svg>
              <span>Dashboard</span>
            </button>
          </div>
        </div>

        {/* Right: Global Status, Theme, Profile */}
        <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
          {/* Daily Query Quota Meter */}
          {userQuota && (
            <div
              className={`hidden md:flex items-center gap-2 px-2.5 py-1 rounded-lg border select-none shadow-2xs ${
                (userQuota.queries_remaining ?? 10) === 0
                  ? "bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/60"
                  : "bg-surface-100 dark:bg-gray-800 border-surface-200 dark:border-gray-700"
              }`}
              title={`Company Allowance: ${userQuota.queries_used || 0} / ${userQuota.query_limit || 10} queries used today. ${userQuota.company_notice || "This is for a company, not for public use."}`}
            >
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center justify-between gap-2 text-[10px] font-mono leading-none">
                  <span className="text-surface-500 dark:text-gray-400">Queries</span>
                  <span
                    className={`font-semibold ${
                      (userQuota.queries_remaining ?? 10) === 0
                        ? "text-red-600 dark:text-red-400 font-bold"
                        : "text-surface-800 dark:text-gray-200"
                    }`}
                  >
                    {(userQuota.queries_remaining ?? 10)} / {(userQuota.query_limit || 10)} left
                  </span>
                </div>
                <div className="w-16 h-1.5 bg-surface-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      (userQuota.queries_remaining ?? 10) <= 2
                        ? "bg-red-500"
                        : (userQuota.queries_remaining ?? 10) <= 5
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{
                      width: `${Math.max(
                        4,
                        Math.min(100, ((userQuota.queries_remaining ?? 10) / (userQuota.query_limit || 10)) * 100)
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tour trigger button */}
          <button
            type="button"
            onClick={onStartTour}
            className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:text-surface-900 dark:hover:text-white hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors cursor-pointer border border-surface-200 dark:border-gray-700 shadow-2xs"
            title="Start interactive guided tour"
          >
            <span className="w-3.5 h-3.5 rounded-full bg-accent/20 text-accent font-bold text-[10px] flex items-center justify-center">?</span>
            <span className="hidden sm:inline">Tour</span>
          </button>

          {/* Dark / Light Mode Toggle */}
          <button
            type="button"
            onClick={() => setDarkMode((prev) => !prev)}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors cursor-pointer select-none border border-surface-200 dark:border-gray-700 shadow-2xs"
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            <div
              className={`w-7 h-3.5 rounded-full transition-colors relative ${
                darkMode ? "bg-accent" : "bg-surface-300"
              }`}
            >
              <div
                className={`absolute top-0.5 left-0.5 bg-white rounded-full h-2.5 w-2.5 shadow-xs transition-transform duration-200 ${
                  darkMode ? "translate-x-3.5" : "translate-x-0"
                }`}
              />
            </div>
            <span className="hidden sm:inline text-xs text-surface-500 dark:text-gray-400 select-none">
              {darkMode ? "Dark" : "Light"}
            </span>
          </button>

          {/* Guest Demo Mode Pill */}
          {currentUser?.isGuest && (
            <button
              type="button"
              onClick={onOpenAuthModal}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 hover:bg-amber-500/25 transition-all cursor-pointer shadow-2xs"
              title="Guest Demo: Click to sign in for full 50,000 tokens & dataset uploads"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse shrink-0" />
              <span>Demo ({guestQueriesRemaining})</span>
            </button>
          )}

          {/* User Identity Profile Pill */}
          <button
            type="button"
            onClick={onOpenAuthModal}
            className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors cursor-pointer border border-surface-200 dark:border-gray-700 shadow-2xs select-none"
            title="Switch User Identity / Supabase Login"
          >
            <div className="w-5 h-5 rounded-full bg-accent text-white font-bold text-[10px] flex items-center justify-center shrink-0">
              {currentUser?.avatar || currentUser?.name?.[0] || currentUser?.email?.[0]?.toUpperCase() || "U"}
            </div>
            <span className="text-xs font-medium text-surface-700 dark:text-gray-200 max-w-[80px] sm:max-w-[100px] truncate">
              {currentUser?.name?.split(" ")[0] || currentUser?.email?.split("@")[0] || "Sign In"}
            </span>
            <svg className="w-3 h-3 text-surface-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Row 2: Conversation Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 px-4 py-1.5 bg-surface-50/70 dark:bg-gray-950/40 text-xs">
        {/* Left: Model Selector & Fallback */}
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-surface-600 dark:text-gray-300 select-none">
            <span className="font-semibold text-surface-500 dark:text-gray-400">Model:</span>
            <select
              value={selectedModel}
              onChange={(e) => onSelectedModelChange(e.target.value)}
              className="text-xs font-medium bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-md px-2 py-1 text-surface-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent cursor-pointer shadow-2xs"
            >
              <option value="groq">Groq GPT-OSS 120B</option>
              <option value="gemini">Gemini 2.5 Flash</option>
            </select>
          </label>
          {activeModel && activeModel !== selectedModel && (
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
              title="Fell back to alternative model"
            >
              fallback: {activeModel === "groq" ? "Groq" : "Gemini"}
            </span>
          )}
        </div>

        {/* Center: Chart Type Segmented Pills, Toggle, and Graph Theme */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-0.5 bg-surface-100 dark:bg-gray-800/80 p-0.5 rounded-lg border border-surface-200 dark:border-gray-700 shadow-2xs">
            {options.map((o) => (
              <button
                key={o.label}
                onClick={() => onChartTypeChange(o.value)}
                className={`flex items-center gap-1 px-2 py-1 rounded-md transition-colors cursor-pointer text-[11px] font-medium leading-none ${
                  chartType === o.value
                    ? "bg-white dark:bg-gray-700 text-accent font-semibold shadow-xs"
                    : "text-surface-500 dark:text-gray-400 hover:text-surface-800 dark:hover:text-gray-200"
                }`}
                title={`Chart type: ${o.label}`}
              >
                {o.label === "Auto" && (
                  <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                  </svg>
                )}
                {o.label === "Bar" && (
                  <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                    <rect x="2" y="10" width="3" height="4" rx="0.5" />
                    <rect x="6.5" y="6" width="3" height="8" rx="0.5" />
                    <rect x="11" y="2" width="3" height="12" rx="0.5" />
                  </svg>
                )}
                {o.label === "Line" && (
                  <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="1,13 5,9 8,12 12,4 15,6" />
                  </svg>
                )}
                {o.label === "Pie" && (
                  <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                    <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.2" />
                    <path d="M8 8 L8 1 A7 7 0 0 1 14.06 10.56 Z" />
                  </svg>
                )}
                <span>{o.label}</span>
              </button>
            ))}
          </div>

          <div className="w-px h-3.5 bg-surface-200 dark:bg-gray-700 hidden sm:block" />

          <label className="flex items-center gap-1 text-xs text-surface-600 dark:text-gray-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={chartEnabled}
              onChange={(e) => onChartEnabledChange(e.target.checked)}
              className="w-3.5 h-3.5 rounded border-surface-300 dark:border-gray-600 text-accent focus:ring-accent/30 cursor-pointer"
            />
            <span>Charts</span>
          </label>

          <div className="w-px h-3.5 bg-surface-200 dark:bg-gray-700 hidden sm:block" />

          <label className="flex items-center gap-1.5 text-xs text-surface-600 dark:text-gray-300 select-none">
            <span className="text-surface-500 dark:text-gray-400">Theme:</span>
            <select
              value={chartTheme}
              onChange={(e) => onChartThemeChange(e.target.value)}
              className="text-xs font-medium bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-md px-1.5 py-0.5 text-surface-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent cursor-pointer shadow-2xs"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>
        </div>

        {/* Right: Clear Chat Action */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleClearClick}
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-surface-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 border border-transparent hover:border-red-200 dark:hover:border-red-800 rounded-md transition-colors cursor-pointer shadow-2xs"
            title="Clear chat messages"
          >
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
            <span>Clear</span>
          </button>
        </div>
      </div>

      <ConfirmModal isOpen={showClearModal} onConfirm={handleConfirmClear} onCancel={handleCancelClear} />
    </header>
  );
}
