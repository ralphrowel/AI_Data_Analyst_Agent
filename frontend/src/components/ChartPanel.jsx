export default function ChartPanel({ charts, currentIndex, onIndexChange }) {
  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${charts[currentIndex]}`;
    link.download = `chart_${currentIndex + 1}.png`;
    link.click();
  };

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
        <button
          onClick={handleDownload}
          className="mt-3 flex items-center gap-1.5 px-3 py-1.5 text-xs text-surface-600 bg-white border border-surface-200 rounded-lg hover:bg-surface-50 hover:text-surface-800 transition-colors cursor-pointer shadow-sm"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Download PNG
        </button>
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
