export default function SystemMessage({ message }) {
  const isModelSwitch = message.systemType === "model_switch";
  if (isModelSwitch) {
    return (
      <div className="flex items-center gap-2 py-1.5 select-none">
        <div className="flex-1 h-px bg-surface-200 dark:bg-gray-700" />
        <span className="text-xs text-surface-400 dark:text-gray-500 whitespace-nowrap">{message.text}</span>
        <div className="flex-1 h-px bg-surface-200 dark:bg-gray-700" />
      </div>
    );
  }
  return (
    <div className="flex justify-start">
      <div className="max-w-[75%] rounded-2xl px-4 py-3 border rounded-bl-md bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200">
        <div className="flex items-start gap-2.5">
          <svg className="w-5 h-5 mt-0.5 shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z" />
          </svg>
          <div>
            <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1 uppercase tracking-wider">Not answerable</p>
            <p className="text-sm leading-relaxed">{message.text}</p>
            {message.quality_badge && (
              <div className="mt-2 pt-1.5 border-t border-amber-200/60 dark:border-amber-800/60 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                <span className="font-medium">Dataset Quality:</span>
                <span>{message.quality_badge.score}/100 (Grade {message.quality_badge.grade})</span>
                {message.quality_badge.version_role === "cleaned" && <span className="text-[11px] px-1.5 py-0.2 rounded bg-amber-200/50 dark:bg-amber-800/40 font-semibold">Cleaned</span>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
