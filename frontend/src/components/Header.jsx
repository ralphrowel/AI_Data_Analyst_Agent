import { useState } from "react";
import ConfirmModal from "./ConfirmModal";

export default function Header({ chartType, chartEnabled, onChartTypeChange, onChartEnabledChange, onClearChat }) {
  const [darkMode, setDarkMode] = useState(false);
  const [showUploadTooltip, setShowUploadTooltip] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [aiModel, setAiModel] = useState("gemini-2.5-flash");
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
    <header className="flex items-center gap-4 px-4 py-2 border-b border-surface-200 bg-white shrink-0">
      <div className="flex items-center shrink-0">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-l-lg bg-surface-100 border border-surface-200 border-r-0 text-surface-600 text-xs font-medium">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
          </svg>
          <span>netflix_titles.csv</span>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowUploadTooltip((prev) => !prev)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-r-lg bg-surface-100 border border-surface-200 text-surface-500 hover:text-surface-700 hover:bg-surface-150 text-xs transition-colors cursor-pointer"
            title="Upload Dataset"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            Upload
          </button>
          {showUploadTooltip && (
            <div className="absolute top-full left-0 mt-1.5 px-3 py-1.5 bg-surface-800 text-white text-xs rounded-lg shadow-lg whitespace-nowrap z-50 pointer-events-none">
              Coming soon — currently using netflix_titles.csv
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 flex justify-center">
        <div className="relative w-full max-w-md">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Search chats..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-surface-50 border border-surface-200 rounded-full text-surface-700 placeholder-surface-400 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
          />
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <label className="relative inline-flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" className="sr-only peer" checked={darkMode} onChange={(e) => setDarkMode(e.target.checked)} />
          <div className="w-8 h-4 bg-surface-300 rounded-full peer-checked:bg-accent after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4" />
          {darkMode ? (
            <span className="flex items-center gap-1 text-xs text-surface-500 select-none">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
              </svg>
              Dark
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-surface-500 select-none">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
              </svg>
              Light
            </span>
          )}
        </label>

        <div className="w-px h-4 bg-surface-200" />

        <div className="flex items-center gap-1">
          {options.map((o) => (
            <button
              key={o.label}
              onClick={() => onChartTypeChange(o.value)}
              className={`flex flex-col items-center justify-center w-11 h-11 rounded-lg transition-colors cursor-pointer text-[10px] leading-tight ${
                chartType === o.value
                  ? "bg-accent/10 text-accent ring-1 ring-accent/30"
                  : "text-surface-500 hover:text-surface-700 hover:bg-surface-100"
              }`}
            >
              {o.label === "Auto" && (
  <svg className="w-4 h-4 mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
  </svg>
)}
              {o.label === "Bar" && (
                <svg className="w-4 h-4 mb-0.5" viewBox="0 0 16 16" fill="currentColor">
                  <rect x="2" y="10" width="3" height="4" rx="0.5" />
                  <rect x="6.5" y="6" width="3" height="8" rx="0.5" />
                  <rect x="11" y="2" width="3" height="12" rx="0.5" />
                </svg>
              )}
              {o.label === "Line" && (
                <svg className="w-4 h-4 mb-0.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="1,13 5,9 8,12 12,4 15,6" />
                </svg>
              )}
              {o.label === "Pie" && (
                <svg className="w-4 h-4 mb-0.5" viewBox="0 0 16 16" fill="currentColor">
                  <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M8 8 L8 1 A7 7 0 0 1 14.06 10.56 Z" />
                </svg>
              )}
              <span>{o.label}</span>
            </button>
          ))}
        </div>

        <div className="w-px h-4 bg-surface-200" />

        <label className="flex items-center gap-1 text-xs text-surface-500 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={chartEnabled}
            onChange={(e) => onChartEnabledChange(e.target.checked)}
            className="w-3 h-3 rounded border-surface-300 text-accent focus:ring-accent/30 cursor-pointer"
          />
          Charts
        </label>

        <div className="w-px h-4 bg-surface-200" />

        <select
          value={aiModel}
          onChange={(e) => {
            setAiModel(e.target.value);
            setTimeout(() => setAiModel("gemini-2.5-flash"), 200);
          }}
          className="text-xs bg-surface-50 border border-surface-200 rounded-md px-2 py-1 text-surface-600 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent cursor-pointer"
        >
          <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
          <option value="gpt-4" disabled>GPT-4 (coming soon)</option>
          <option value="claude-3" disabled>Claude 3 (coming soon)</option>
        </select>

        <button
          onClick={handleClearClick}
          className="flex items-center gap-1 px-2 py-1 text-xs text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-md transition-colors cursor-pointer"
          title="Clear chat"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
        </button>
      </div>
      <ConfirmModal isOpen={showClearModal} onConfirm={handleConfirmClear} onCancel={handleCancelClear} />
    </header>
  );
}
