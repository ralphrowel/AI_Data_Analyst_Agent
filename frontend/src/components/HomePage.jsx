export default function HomePage({
  availableDatasets = [],
  sessions = [],
  onSelectSession,
  onPickDataset,
  onNewChat,
  onOpenUpload,
  darkMode,
  setDarkMode,
}) {
  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-white dark:bg-gray-900 text-surface-800 dark:text-gray-100">
      {/* Top Navbar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-surface-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-white shadow-sm font-bold text-sm">
            AI
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-tight text-surface-900 dark:text-gray-100">
              Data Analyst Agent
            </h2>
            <p className="text-[10px] text-surface-400 dark:text-gray-400 font-medium">
              Autonomous Conversational BI
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-gray-800 hover:bg-surface-200 dark:hover:bg-gray-700 border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-200 text-xs font-medium transition-colors cursor-pointer shadow-xs"
            title="Upload CSV dataset or Markdown knowledge base"
          >
            <svg className="w-3.5 h-3.5 text-surface-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <span>Upload File</span>
          </button>

          <button
            type="button"
            onClick={() => setDarkMode((prev) => !prev)}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-gray-800 border border-surface-200 dark:border-gray-700 transition-colors cursor-pointer select-none"
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            <div
              className={`w-8 h-4 rounded-full transition-colors relative ${
                darkMode ? "bg-accent" : "bg-surface-300"
              }`}
            >
              <div
                className={`absolute top-0.5 left-0.5 bg-white rounded-full h-3 w-3 shadow-xs transition-transform duration-200 ${
                  darkMode ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </div>
            <span className="text-xs text-surface-500 dark:text-gray-400">
              {darkMode ? (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              )}
            </span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-8 md:py-12 space-y-10">
        {/* Visual Hero Section */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-accent/10 text-accent border border-accent/20 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            Autonomous Dual-Engine Intelligence
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-surface-900 dark:text-gray-100">
            Analyze Data at the Speed of Thought
          </h1>
          <p className="text-sm md:text-base text-surface-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Pick a dataset or open an existing conversation to run deterministic Python analysis, generate real-time charts, and search company knowledge bases.
          </p>
        </div>

        {/* Quick Launch Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={onNewChat}
            className="group p-5 rounded-2xl bg-surface-50 dark:bg-gray-800/80 border border-surface-200 dark:border-gray-700 hover:border-accent/40 dark:hover:border-accent/40 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
          >
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-accent/15 dark:bg-accent/20 text-accent flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-surface-900 dark:text-gray-100 group-hover:text-accent transition-colors">
                Start New Chat Workspace
              </h3>
              <p className="text-xs text-surface-500 dark:text-gray-400 leading-relaxed">
                Create a fresh isolated conversation void. Choose from stored datasets or pick a local CSV file directly from your computer.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-surface-200 dark:border-gray-700/60 flex items-center justify-between text-xs font-semibold text-accent">
              <span>Configure Workspace</span>
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </div>
          </div>

          <div
            onClick={onOpenUpload}
            className="group p-5 rounded-2xl bg-surface-50 dark:bg-gray-800/80 border border-surface-200 dark:border-gray-700 hover:border-accent/40 dark:hover:border-accent/40 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
          >
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <h3 className="text-base font-bold text-surface-900 dark:text-gray-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                Upload New Data / Document
              </h3>
              <p className="text-xs text-surface-500 dark:text-gray-400 leading-relaxed">
                Add new CSV tables for data analysis, or upload Markdown / text documents to automatically index into the TF-IDF RAG vector retriever.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-surface-200 dark:border-gray-700/60 flex items-center justify-between text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <span>Upload Dataset or Docs</span>
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </div>
          </div>
        </div>

        {/* Available Datasets Section */}
        {availableDatasets && availableDatasets.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-surface-900 dark:text-gray-100">
                  Pick a Dataset to Explore
                </h2>
                <p className="text-xs text-surface-500 dark:text-gray-400">
                  Click any dataset below to open or launch an instant conversation.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableDatasets.map((ds) => (
                <div
                  key={ds.name}
                  onClick={() => onPickDataset && onPickDataset(ds.name)}
                  className="group p-4 rounded-xl bg-surface-50 dark:bg-gray-800/70 border border-surface-200 dark:border-gray-700 hover:border-accent dark:hover:border-accent transition-all cursor-pointer shadow-2xs hover:shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="w-7 h-7 rounded-lg bg-accent/10 text-accent flex items-center justify-center shrink-0">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                        </svg>
                      </span>
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-surface-200/80 dark:bg-gray-700 text-surface-600 dark:text-gray-300">
                        CSV Void
                      </span>
                    </div>
                    <h4 className="font-mono text-xs font-bold text-surface-900 dark:text-gray-100 truncate group-hover:text-accent transition-colors" title={ds.name}>
                      {ds.name}
                    </h4>
                    <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-1">
                      {ds.rows ? `${ds.rows.toLocaleString()} rows • ` : ""}
                      {ds.columns ? `${ds.columns.length} columns` : "Ready to analyze"}
                    </p>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-surface-200 dark:border-gray-700/60 flex items-center justify-between text-[11px] font-semibold text-accent">
                    <span>Analyze dataset</span>
                    <svg className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Conversations */}
        {sessions && sessions.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-surface-900 dark:text-gray-100">
                  Recent Conversations
                </h2>
                <p className="text-xs text-surface-500 dark:text-gray-400">
                  Pick up right where you left off.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {sessions.slice(0, 6).map((s) => (
                <div
                  key={s.session_id}
                  onClick={() => onSelectSession && onSelectSession(s.session_id)}
                  className="group p-3.5 rounded-xl bg-surface-50 dark:bg-gray-800/70 border border-surface-200 dark:border-gray-700 hover:border-accent dark:hover:border-accent transition-all cursor-pointer shadow-2xs hover:shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <svg className="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.502 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                      </svg>
                      <h4 className="text-xs font-bold text-surface-900 dark:text-gray-100 truncate group-hover:text-accent transition-colors">
                        {s.title || "Chat Workspace"}
                      </h4>
                    </div>
                    <p className="text-[11px] font-mono text-surface-500 dark:text-gray-400 truncate">
                      {s.dataset_name}
                    </p>
                  </div>

                  <div className="mt-3 pt-2 border-t border-surface-200 dark:border-gray-700/60 flex items-center justify-between text-[11px] font-medium text-surface-500 dark:text-gray-400 group-hover:text-accent">
                    <span>Open chat</span>
                    <svg className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feature Highlights Showcase */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
          <div className="p-3.5 rounded-xl bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center mb-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">Dynamic Charts</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-1 leading-relaxed">
              Auto-generated responsive Bar, Line, Pie, and Distribution plots.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center mb-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">Dual-Engine Speed</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-1 leading-relaxed">
              Lightning-fast Groq Llama 3.3 70B with Gemini 2.5 Flash fallback.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">Isolated Voids</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-1 leading-relaxed">
              Every chat session locks its own private dataset frame and history.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-50/70 dark:bg-gray-800/50 border border-surface-200/80 dark:border-gray-700/50">
            <div className="w-7 h-7 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center mb-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
              </svg>
            </div>
            <h4 className="text-xs font-semibold text-surface-800 dark:text-gray-200">RAG Knowledge</h4>
            <p className="text-[11px] text-surface-500 dark:text-gray-400 mt-1 leading-relaxed">
              Search unstructured documentation, policy guides, and notes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
