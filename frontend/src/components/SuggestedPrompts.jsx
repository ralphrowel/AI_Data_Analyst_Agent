export default function SuggestedPrompts({ prompts, onClick }) {
  if (!prompts || prompts.length === 0) return null;

  return (
    <div className="mb-3">
      <p className="text-xs text-surface-400 mb-2">Try asking</p>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onClick(prompt)}
            className="px-3 py-1.5 rounded-full border border-surface-200 bg-surface-50 text-xs text-surface-600 hover:bg-surface-100 hover:border-surface-300 transition-colors duration-150 cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
