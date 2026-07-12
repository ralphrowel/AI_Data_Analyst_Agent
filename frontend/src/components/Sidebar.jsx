import TokenUsageDisplay from "./TokenUsageDisplay";
import ChartTypeSelector from "./ChartTypeSelector";

export default function Sidebar({ tokenUsage, chartType, onChartTypeChange }) {
  return (
    <aside className="w-64 shrink-0 border-r border-surface-800 bg-surface-900 flex flex-col">
      <div className="p-5 border-b border-surface-800">
        <h1 className="text-lg font-semibold text-surface-50 tracking-tight">
          AI Data Analyst
        </h1>
        <p className="text-xs text-surface-400 mt-1">
          Ask questions about your dataset
        </p>
      </div>
      <div className="flex-1 p-4 space-y-6">
        <ChartTypeSelector value={chartType} onChange={onChartTypeChange} />
      </div>
      <div className="p-4 border-t border-surface-800">
        <TokenUsageDisplay usage={tokenUsage} />
      </div>
    </aside>
  );
}
