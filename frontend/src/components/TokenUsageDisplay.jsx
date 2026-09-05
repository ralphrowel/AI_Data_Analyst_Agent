export default function TokenUsageDisplay({ usage, activeModel }) {
  const geminiTokens = usage.gemini_tokens || 0;
  const groqTokens = usage.groq_tokens || 0;

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-surface-400 dark:text-gray-500 uppercase tracking-wider">Session Tokens</p>
      <div className="flex justify-between text-xs text-surface-500 dark:text-gray-400">
        <span>Prompt</span>
        <span className="text-surface-600 dark:text-gray-300 font-mono">{usage.prompt_tokens.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-xs text-surface-500 dark:text-gray-400">
        <span>Response</span>
        <span className="text-surface-600 dark:text-gray-300 font-mono">{usage.response_tokens.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-xs text-surface-400 dark:text-gray-500 border-t border-surface-200 dark:border-gray-700 pt-1.5 mt-1.5">
        <span className="font-medium">Total</span>
        <span className="text-surface-700 dark:text-gray-200 font-mono font-medium">{usage.total_tokens.toLocaleString()}</span>
      </div>
      {/* Per-provider breakdown — only shows providers that have been used */}
      {(geminiTokens > 0 || groqTokens > 0) && (
        <div className="border-t border-surface-200 dark:border-gray-700 pt-1.5 mt-1.5 space-y-1">
          <p className="text-[10px] font-medium text-surface-400 dark:text-gray-500 uppercase tracking-wider">By Provider</p>
          {geminiTokens > 0 && (
            <div className="flex justify-between text-xs text-surface-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                Gemini
              </span>
              <span className="text-surface-600 dark:text-gray-300 font-mono">{geminiTokens.toLocaleString()}</span>
            </div>
          )}
          {groqTokens > 0 && (
            <div className="flex justify-between text-xs text-surface-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-orange-500"></span>
                Groq
              </span>
              <span className="text-surface-600 dark:text-gray-300 font-mono">{groqTokens.toLocaleString()}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
