export default function Toolbar({ chartType, chartEnabled, onChartTypeChange, onChartEnabledChange }) {
  const options = [
    { label: "Auto", value: null },
    { label: "Bar", value: "bar" },
    { label: "Line", value: "line" },
    { label: "Pie", value: "pie" },
  ];

  return (
    <div className="flex items-center gap-3 px-1 py-2 mb-2">
      <div className="flex items-center gap-1">
        {options.map((o) => (
          <button
            key={o.label}
            onClick={() => onChartTypeChange(o.value)}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors cursor-pointer ${
              chartType === o.value
                ? "bg-accent text-white"
                : "text-surface-500 hover:text-surface-700 hover:bg-surface-100"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>

      <div className="w-px h-4 bg-surface-200" />

      <label className="flex items-center gap-1.5 text-xs text-surface-500 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={chartEnabled}
          onChange={(e) => onChartEnabledChange(e.target.checked)}
          className="w-3.5 h-3.5 rounded border-surface-300 text-accent focus:ring-accent/30 cursor-pointer"
        />
        Charts
      </label>

      <div className="w-px h-4 bg-surface-200" />

      <span className="text-xs text-surface-400 italic">More tools coming soon</span>
    </div>
  );
}
