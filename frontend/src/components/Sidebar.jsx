import TokenUsageDisplay from "./TokenUsageDisplay";

export default function Sidebar({
  collapsed,
  onToggle,
  tokenUsage,
  activeModel,
  sessions = [],
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
}) {
  return (
    <aside
      className={`${
        collapsed ? "w-14" : "w-64"
      } shrink-0 border-r border-surface-200 dark:border-gray-700 bg-surface-100 dark:bg-gray-950 flex flex-col transition-all duration-200 h-full select-none`}
    >
      {/* Header */}
      <div className={`flex items-center ${collapsed ? "justify-center" : "justify-between"} p-3 border-b border-surface-200 dark:border-gray-700`}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-surface-800 dark:text-gray-100 tracking-tight">Workspaces</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-md text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200 hover:bg-surface-200 dark:hover:bg-gray-700 transition-colors cursor-pointer"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-2">
        <button
          onClick={onNewChat}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-accent text-white hover:opacity-90 shadow-sm transition-all cursor-pointer ${
            collapsed ? "justify-center px-0" : ""
          }`}
          title="Start a new chat workspace"
        >
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          {!collapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* Chat Sessions List */}
      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1">
        {!collapsed && sessions.length > 0 && (
          <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-surface-400 dark:text-gray-500">
            Recent Chats
          </p>
        )}
        {sessions.map((s) => {
          const isActive = s.session_id === activeSessionId;
          return (
            <div
              key={s.session_id}
              onClick={() => onSelectSession && onSelectSession(s.session_id)}
              className={`group relative flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs transition-all cursor-pointer ${
                isActive
                  ? "bg-accent/15 dark:bg-accent/20 text-accent font-medium ring-1 ring-accent/30"
                  : "text-surface-600 dark:text-gray-300 hover:bg-surface-200 dark:hover:bg-gray-800"
              } ${collapsed ? "justify-center px-0" : ""}`}
              title={collapsed ? `${s.title} (${s.dataset_name})` : undefined}
            >
              <svg className="w-4 h-4 shrink-0 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.502 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
              </svg>

              {!collapsed && (
                <div className="flex-1 min-w-0 pr-6">
                  <p className="truncate text-xs leading-tight font-medium">
                    {s.title || "New Chat"}
                  </p>
                  <p className="truncate text-[10px] text-surface-400 dark:text-gray-500 font-mono mt-0.5">
                    {s.dataset_name}
                  </p>
                </div>
              )}

              {/* Delete Session Button (visible on hover) */}
              {!collapsed && sessions.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onDeleteSession) onDeleteSession(s.session_id);
                  }}
                  className="absolute right-2 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/40 text-surface-400 hover:text-red-600 dark:hover:text-red-400 transition-opacity cursor-pointer"
                  title="Delete chat"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Token Usage footer */}
      {!collapsed && tokenUsage && (
        <div className="p-3 border-t border-surface-200 dark:border-gray-700">
          <TokenUsageDisplay usage={tokenUsage} activeModel={activeModel} />
        </div>
      )}
    </aside>
  );
}
