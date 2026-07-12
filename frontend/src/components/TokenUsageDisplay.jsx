export default function TokenUsageDisplay({ usage }) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">
        Session Tokens
      </p>
      <div className="flex justify-between text-xs text-surface-500">
        <span>Prompt</span>
        <span className="text-surface-300 font-mono">{usage.prompt_tokens.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-xs text-surface-500">
        <span>Response</span>
        <span className="text-surface-300 font-mono">{usage.response_tokens.toLocaleString()}</span>
      </div>
      <div className="flex justify-between text-xs text-surface-400 border-t border-surface-800 pt-1.5 mt-1.5">
        <span className="font-medium">Total</span>
        <span className="text-surface-200 font-mono font-medium">{usage.total_tokens.toLocaleString()}</span>
      </div>
    </div>
  );
}
