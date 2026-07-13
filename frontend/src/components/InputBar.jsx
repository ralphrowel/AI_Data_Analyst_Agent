export default function InputBar({ value, onChange, onSubmit, isStreaming }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim() || isStreaming) return;
    onSubmit(value.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Ask a question about your data..."
        disabled={isStreaming}
        className="flex-1 bg-white dark:bg-gray-800 border border-surface-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm text-surface-800 dark:text-gray-100 placeholder-surface-400 dark:placeholder-gray-500 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={!value.trim() || isStreaming}
        className="px-4 py-3 rounded-xl bg-accent text-white text-sm font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer shadow-sm"
      >
        {isStreaming ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        )}
      </button>
    </form>
  );
}
