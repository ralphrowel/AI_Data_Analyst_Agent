export default function ChartTypeSelector({ value, onChange }) {
  const options = [
    { label: "Auto", value: null },
    { label: "Bar", value: "bar" },
    { label: "Line", value: "line" },
    { label: "Pie", value: "pie" },
  ];

  return (
    <div>
      <label className="block text-xs font-medium text-surface-400 mb-2 uppercase tracking-wider">
        Chart Type
      </label>
      <select
        value={value === null ? "null" : value}
        onChange={(e) => onChange(e.target.value === "null" ? null : e.target.value)}
        className="w-full bg-surface-800 text-surface-200 border border-surface-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent cursor-pointer"
      >
        {options.map((o) => (
          <option key={o.label} value={o.value === null ? "null" : o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
