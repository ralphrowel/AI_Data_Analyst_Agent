export default function SuggestedPrompts({ prompts, onClick }) {
  if (!prompts || prompts.length === 0) return null;

  return (
    <div className="mb-3">
      <p className="text-xs text-surface-400 dark:text-gray-500 mb-2">Try asking</p>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onClick(prompt)}
            className="px-3 py-1.5 rounded-full border border-surface-200 dark:border-gray-700 bg-surface-50 dark:bg-gray-800 text-xs text-surface-600 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-700 hover:border-surface-300 dark:hover:border-gray-600 transition-colors duration-150 cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
