import InputBar from "./InputBar";

export default function ChatHome({
  activeDatasetName,
  datasetInfo,
  suggestions = [],
  onSubmit,
  onNewChat,
  input,
  setInput,
  isStreaming,
}) {
  const columns = datasetInfo?.columns || [];
  const rows = datasetInfo?.rows;

  return (
    <div className="flex-1 flex flex-col justify-between h-full overflow-y-auto px-4 py-6 md:px-8">
      {/* Centered Content Container */}
      <div className="max-w-3xl mx-auto w-full flex-1 flex flex-col justify-center py-4">
        {/* Hero Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent border border-accent/20 mb-3 shadow-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            AI Data Analyst Agent
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-surface-900 dark:text-gray-100">
            What insights are you looking for?
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-surface-500 dark:text-gray-400 max-w-lg mx-auto">
            Explore your data through conversational AI. Ask questions, compute statistical metrics, and generate real-time visual charts.
          </p>
        </div>

        {/* Active Dataset Status Card */}
        {activeDatasetName ? (
          <div className="mb-6 p-4 rounded-xl bg-surface-50 dark:bg-gray-800/80 border border-surface-200 dark:border-gray-700 shadow-xs backdrop-blur-xs transition-all">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-200 dark:border-gray-700/60">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-accent/15 dark:bg-accent/20 flex items-center justify-center text-accent shrink-0">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-surface-800 dark:text-gray-100 truncate">
                      {activeDatasetName}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      Locked Void
                    </span>
                  </div>
                  <p className="text-[11px] text-surface-400 dark:text-gray-400 mt-0.5">
                    {rows ? `${rows.toLocaleString()} rows • ` : ""}
                    {columns.length > 0 ? `${columns.length} columns • ` : ""}
                    Session memory isolated
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={onNewChat}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-surface-600 dark:text-gray-300 hover:text-accent dark:hover:text-accent bg-surface-100 dark:bg-gray-700/60 hover:bg-surface-200 dark:hover:bg-gray-700 transition-colors cursor-pointer shrink-0"
                title="Start a new chat with another dataset or local file"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <span>New File / Chat</span>
              </button>
            </div>

            {/* Columns Preview */}
            {columns.length > 0 && (
              <div className="pt-2.5">
                <div className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500 tracking-wider mb-1.5">
                  Available Columns
                </div>
                <div className="flex flex-wrap gap-1.5 max-h-16 overflow-y-auto">
                  {columns.slice(0, 10).map((col) => (
                    <span
                      key={col}
                      className="px-2 py-0.5 text-[11px] font-mono rounded-md bg-surface-200/70 dark:bg-gray-700/60 text-surface-700 dark:text-gray-300 border border-surface-300/40 dark:border-gray-600/40"
                    >
                      {col}
                    </span>
                  ))}
                  {columns.length > 10 && (
                    <span className="px-2 py-0.5 text-[11px] font-mono rounded-md text-surface-400 dark:text-gray-500">
                      +{columns.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="mb-6 p-6 rounded-xl bg-surface-50 dark:bg-gray-800 border border-dashed border-surface-300 dark:border-gray-700 text-center">
            <svg className="w-8 h-8 mx-auto mb-2 text-surface-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-semibold text-surface-800 dark:text-gray-100">No active chat workspace</p>
            <p className="text-xs text-surface-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
              Create a new chat workspace to pick a dataset from storage or open a CSV from your computer.
            </p>
            <button
              onClick={onNewChat}
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <span>Create New Workspace</span>
            </button>
          </div>
        )}

        {/* Suggested Starter Prompts */}
        {suggestions && suggestions.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-surface-600 dark:text-gray-300 mb-2.5">
              <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              <span>Suggested Explorations</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {suggestions.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSubmit(prompt)}
                  className="group flex items-start justify-between gap-2 p-3 text-left rounded-lg bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 hover:border-accent/40 dark:hover:border-accent/40 hover:bg-surface-100 dark:hover:bg-gray-700/60 transition-all cursor-pointer shadow-2xs"
                >
                  <span className="text-xs text-surface-700 dark:text-gray-200 group-hover:text-accent dark:group-hover:text-accent font-medium leading-relaxed">
                    {prompt}
                  </span>
                  <svg className="w-3.5 h-3.5 mt-0.5 text-surface-400 dark:text-gray-500 group-hover:text-accent group-hover:translate-x-0.5 transition-all shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
                  </svg>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-2">
          <div className="p-3 rounded-lg bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-6 h-6 rounded-md bg-blue-500/10 text-blue-500 flex items-center justify-center mb-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">Instant Charts</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-0.5 leading-snug">
              Automatic bar, line, pie, and distribution graphs with theme styling.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-6 h-6 rounded-md bg-amber-500/10 text-amber-500 flex items-center justify-center mb-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">Dual-Engine Speed</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-0.5 leading-snug">
              Powered by Groq 120B with automatic fallback to Gemini 2.5 Flash.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-6 h-6 rounded-md bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">Isolated Voids</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-0.5 leading-snug">
              Each chat maintains a locked, private dataset DataFrame and context.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Input Section */}
      <div className="max-w-3xl mx-auto w-full pt-3">
        <InputBar
          value={input}
          onChange={setInput}
          onSubmit={onSubmit}
          isStreaming={isStreaming}
        />
        <p className="text-center text-[10px] text-surface-400 dark:text-gray-500 mt-2">
          Responses are generated with real Python data execution on your locked dataset.
        </p>
      </div>
    </div>
  );
}
