export default function ChartPanel({ charts, currentIndex, onIndexChange }) {
  return (
    <aside className="w-96 shrink-0 border-l border-surface-800 bg-surface-900 flex flex-col">
      <div className="p-4 border-b border-surface-800">
        <h3 className="text-sm font-medium text-surface-300">
          Charts ({charts.length})
        </h3>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-hidden">
        <img
          src={`data:image/png;base64,${charts[currentIndex]}`}
          alt={`Chart ${currentIndex + 1}`}
          className="max-w-full max-h-full object-contain rounded-lg"
        />
      </div>
      {charts.length > 1 && (
        <div className="flex justify-center gap-2 p-4 border-t border-surface-800">
          {charts.map((_, i) => (
            <button
              key={i}
              onClick={() => onIndexChange(i)}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-200 cursor-pointer ${
                i === currentIndex
                  ? "bg-accent w-6"
                  : "bg-surface-600 hover:bg-surface-500"
              }`}
              aria-label={`Go to chart ${i + 1}`}
            />
          ))}
        </div>
      )}
    </aside>
  );
}
