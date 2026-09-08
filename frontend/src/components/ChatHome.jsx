import InputBar from "./InputBar";

export default function ChatHome({
  suggestions = [],
  onSubmit,
  input,
  setInput,
  isStreaming,
}) {
  const defaultSuggestions = [
    "How many Movies vs TV Shows are there?",
    "What are the top 5 countries by number of titles?",
    "How many titles were released each year from 2015 to 2020?",
    "Which genres are the most common in the dataset?",
  ];

  const displaySuggestions =
    suggestions && suggestions.length > 0 ? suggestions : defaultSuggestions;

  return (
    <div className="flex-1 flex flex-col justify-between h-full overflow-y-auto px-4 py-6 md:px-8">
      {/* Centered Minimalist Content Container */}
      <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center py-6">
        {/* Minimalist Hero Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent border border-accent/20 mb-3 shadow-xs select-none">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            Visiq AI Analyst
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-surface-900 dark:text-gray-100">
            What insights are you looking for?
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-surface-500 dark:text-gray-400 max-w-lg mx-auto leading-relaxed">
            Explore your data through conversational AI. Ask questions, compute statistical metrics, and generate real-time visual charts.
          </p>
        </div>

        {/* Suggested Starter Prompts (Minimalist Grid) */}
        {displaySuggestions.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full mx-auto">
            {displaySuggestions.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => onSubmit(prompt)}
                className="group flex items-center justify-between gap-3 p-3.5 text-left rounded-xl bg-surface-50 dark:bg-gray-800/60 border border-surface-200 dark:border-gray-700/70 hover:border-accent/40 dark:hover:border-accent/40 hover:bg-surface-100/70 dark:hover:bg-gray-700/50 transition-all cursor-pointer shadow-2xs"
              >
                <span className="text-xs text-surface-700 dark:text-gray-200 group-hover:text-accent dark:group-hover:text-accent font-medium leading-snug">
                  {prompt}
                </span>
                <svg
                  className="w-3.5 h-3.5 text-surface-400 dark:text-gray-500 group-hover:text-accent group-hover:translate-x-0.5 transition-all shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
                </svg>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Input Section */}
      <div className="max-w-2xl mx-auto w-full pt-3 pb-2">
        <InputBar
          value={input}
          onChange={setInput}
          onSubmit={onSubmit}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
