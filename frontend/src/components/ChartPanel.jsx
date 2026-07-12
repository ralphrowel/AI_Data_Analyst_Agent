export default function ChartPanel({ charts, currentIndex, onIndexChange }) {
  return (
    <aside className="w-96 shrink-0 border-l border-surface-200 bg-surface-50 flex flex-col">
      <div className="p-4 border-b border-surface-200">
        <h3 className="text-sm font-medium text-surface-600">
          Charts <span className="text-surface-400 font-normal">({charts.length})</span>
        </h3>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-hidden">
        <img
          src={`data:image/png;base64,${charts[currentIndex]}`}
          alt={`Chart ${currentIndex + 1}`}
          className="max-w-full max-h-full object-contain rounded-lg bg-white shadow-sm border border-surface-200"
        />
      </div>
      {charts.length > 1 && (
        <div className="flex justify-center gap-2 p-4 border-t border-surface-200">
          {charts.map((_, i) => (
            <button
              key={i}
              onClick={() => onIndexChange(i)}
              className={`rounded-full transition-all duration-200 cursor-pointer ${
                i === currentIndex
                  ? "bg-accent w-5 h-2"
                  : "bg-surface-300 hover:bg-surface-400 w-2 h-2"
              }`}
              aria-label={`Go to chart ${i + 1}`}
            />
          ))}
        </div>
      )}
    </aside>
  );
}
