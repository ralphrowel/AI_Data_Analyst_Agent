import { useState } from "react";
import ChartZoomModal from "./ChartZoomModal";
import InteractiveChart from "./InteractiveChart";

export default function ChartPanel({ charts, currentIndex, onIndexChange }) {
  const [showZoom, setShowZoom] = useState(false);
  const currentItem = charts[currentIndex];
  const chartBase64 = typeof currentItem === "string" ? currentItem : currentItem?.chart_base64 || currentItem?.base64;
  const chartSvg = typeof currentItem === "object" ? currentItem?.chart_svg : null;
  const hasChart = Boolean(chartBase64 || chartSvg);

  const handleDownload = () => {
    if (!chartBase64) return;
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${chartBase64}`;
    link.download = `chart_${currentIndex + 1}.png`;
    link.click();
  };

  const chartCount = charts.filter(Boolean).length;

  return (
    <aside className="w-96 shrink-0 border-l border-surface-200 dark:border-gray-700 bg-surface-50 dark:bg-gray-900 flex flex-col">
      <div className="p-4 border-b border-surface-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="text-sm font-medium text-surface-600 dark:text-gray-300">
          Charts <span className="text-surface-400 dark:text-gray-500 font-normal">({chartCount})</span>
        </h3>
        {hasChart && (
          <button
            onClick={() => setShowZoom(true)}
            className="flex items-center gap-1 text-xs text-accent hover:underline cursor-pointer"
            title="Enlarge chart"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
            </svg>
            <span>Zoom</span>
          </button>
        )}
      </div>
      <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-y-auto">
        {hasChart ? (
          <div className="w-full flex flex-col items-center">
            <InteractiveChart
              chartSvg={chartSvg}
              chartBase64={chartBase64}
              onZoom={() => setShowZoom(true)}
              compact={true}
            />
            <div className="flex items-center gap-2 mt-3">
              <button
                onClick={() => setShowZoom(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-surface-600 dark:text-gray-300 bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-lg hover:bg-surface-50 dark:hover:bg-gray-700 hover:text-surface-800 dark:hover:text-gray-100 transition-colors cursor-pointer shadow-sm"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
                </svg>
                <span>Zoom</span>
              </button>
              {chartBase64 && (
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-surface-600 dark:text-gray-300 bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-lg hover:bg-surface-50 dark:hover:bg-gray-700 hover:text-surface-800 dark:hover:text-gray-100 transition-colors cursor-pointer shadow-sm"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  <span>Download PNG</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-surface-400 dark:text-gray-500">
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859M12 3v8.25m0 0l-3-3m3 3l3-3" />
            </svg>
            <p className="text-xs">No chart for this response</p>
          </div>
        )}
      </div>
      {charts.length > 1 && (
        <div className="flex justify-center gap-2 p-4 border-t border-surface-200 dark:border-gray-700">
          {charts.map((_, i) => (
            <button
              key={i}
              onClick={() => onIndexChange(i)}
              className={`rounded-full transition-all duration-200 cursor-pointer ${
                i === currentIndex
                  ? "bg-accent w-5 h-2"
                  : "bg-surface-300 dark:bg-gray-600 hover:bg-surface-400 dark:hover:bg-gray-500 w-2 h-2"
              }`}
              aria-label={`Go to chart ${i + 1}`}
            />
          ))}
        </div>
      )}
      {showZoom && hasChart && (
        <ChartZoomModal
          chartBase64={chartBase64}
          chartSvg={chartSvg}
          onClose={() => setShowZoom(false)}
          title={`Chart ${currentIndex + 1} Preview`}
        />
      )}
    </aside>
  );
}
