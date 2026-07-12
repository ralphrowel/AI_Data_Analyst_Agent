export default function SuggestedPrompts({ prompts, onClick }) {
  if (!prompts || prompts.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs text-surface-500 uppercase tracking-wider mb-3">
        Try asking
      </p>
      <div className="flex flex-col gap-2">
        {prompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onClick(prompt)}
            className="text-left px-4 py-3 rounded-lg border border-surface-700 bg-surface-900 hover:bg-surface-800 hover:border-accent/50 text-sm text-surface-300 transition-colors duration-150 cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
