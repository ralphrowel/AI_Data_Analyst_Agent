import { useState, useEffect, useRef, useMemo } from "react";
import { createPortal } from "react-dom";

function formatValue(v) {
  if (v === null || v === undefined) return "";
  const num = Number(v);
  if (isNaN(num)) return v;
  if (Number.isInteger(num)) return num.toLocaleString();
  return num.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 });
}

export default function ChartZoomModal({
  chartBase64,
  chartSvg,
  onClose,
  title = "Analysis Chart",
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef(null);
  const tooltipRef = useRef(null);
  const labelRef = useRef(null);
  const valueRef = useRef(null);
  const activeElementRef = useRef(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const clearHighlight = () => {
    if (activeElementRef.current) {
      activeElementRef.current.style.filter = "";
      activeElementRef.current = null;
    }
    if (tooltipRef.current) {
      tooltipRef.current.style.opacity = "0";
      tooltipRef.current.style.visibility = "hidden";
    }
  };

  const handleZoomIn = () => {
    clearHighlight();
    setZoom((z) => Math.min(z + 0.25, 3));
  };

  const handleZoomOut = () => {
    clearHighlight();
    setZoom((z) => Math.max(z - 0.25, 0.5));
  };

  const handleReset = () => {
    clearHighlight();
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleWheel = (e) => {
    clearHighlight();
    e.preventDefault();
    if (e.deltaY < 0) {
      setZoom((z) => Math.min(z + 0.15, 3));
    } else {
      setZoom((z) => Math.max(z - 0.15, 0.5));
    }
  };

  const handleMouseDown = (e) => {
    if (zoom > 1) {
      clearHighlight();
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging && zoom > 1) {
      clearHighlight();
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
      return;
    }

    if (!containerRef.current || !tooltipRef.current || isDragging) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const datumEl = e.target.closest('[id^="datum__"]');
    if (datumEl) {
      const parts = datumEl.id.split("__");
      if (parts.length >= 3) {
        const label = parts[1];
        const val = parts[2];

        if (labelRef.current) labelRef.current.textContent = label;
        if (valueRef.current) valueRef.current.textContent = formatValue(val);

        if (activeElementRef.current !== datumEl) {
          if (activeElementRef.current) activeElementRef.current.style.filter = "";
          datumEl.style.filter = "drop-shadow(0 0 6px rgba(59, 130, 246, 0.8)) brightness(1.2)";
          datumEl.style.transition = "filter 0.1s ease-out, brightness 0.1s ease-out";
          activeElementRef.current = datumEl;
        }

        const isRight = x > rect.width * 0.65;
        const isBottom = y > rect.height * 0.65;
        const posX = isRight ? x - 15 : x + 15;
        const posY = isBottom ? y - 15 : y + 15;
        const translateX = isRight ? "-100%" : "0%";
        const translateY = isBottom ? "-100%" : "0%";

        tooltipRef.current.style.left = `${posX}px`;
        tooltipRef.current.style.top = `${posY}px`;
        tooltipRef.current.style.transform = `translate(${translateX}, ${translateY})`;
        tooltipRef.current.style.opacity = "1";
        tooltipRef.current.style.visibility = "visible";
        return;
      }
    }

    clearHighlight();
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleMouseLeave = () => {
    setIsDragging(false);
    clearHighlight();
  };

  const handleDownload = () => {
    if (!chartBase64) return;
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${chartBase64}`;
    link.download = `chart_${Date.now()}.png`;
    link.click();
  };

  const processedSvg = useMemo(() => {
    if (!chartSvg) return null;
    let s = chartSvg;
    s = s.replace(/<\?xml[\s\S]*?\?>/i, "");
    s = s.replace(/<!DOCTYPE[\s\S]*?>/i, "");
    s = s.replace(/<svg\b([^>]*)>/i, (match, attrs) => {
      let cleanAttrs = attrs
        .replace(/\bwidth="[^"]*"/gi, "")
        .replace(/\bheight="[^"]*"/gi, "");
      return `<svg ${cleanAttrs} style="width: 100%; height: auto; max-height: 100%; display: block;">`;
    });
    return s;
  }, [chartSvg]);

  const modalContent = (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 pt-16 pb-6 select-none animate-in fade-in duration-150"
      onClick={onClose}
    >
      {/* Minimalist Lowered Modal Container */}
      <div
        className="relative flex flex-col w-full max-w-4xl max-h-[74vh] h-[72vh] bg-surface-900 border border-gray-700/80 rounded-2xl overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Minimalist Top Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-950/80 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent" />
            <span className="text-xs font-semibold text-gray-200 truncate max-w-xs">{title}</span>
            <span className="text-[11px] text-gray-400 font-mono">({Math.round(zoom * 100)}%)</span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 0.5}
              className="p-1 rounded-md bg-gray-800/80 hover:bg-gray-700 text-gray-300 disabled:opacity-40 transition-colors cursor-pointer"
              title="Zoom Out"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12h-15" />
              </svg>
            </button>

            <button
              onClick={handleReset}
              className="px-2 py-0.5 text-xs rounded-md bg-gray-800/80 hover:bg-gray-700 text-gray-300 transition-colors cursor-pointer font-mono"
              title="Reset Zoom (100%)"
            >
              100%
            </button>

            <button
              onClick={handleZoomIn}
              disabled={zoom >= 3}
              className="p-1 rounded-md bg-gray-800/80 hover:bg-gray-700 text-gray-300 disabled:opacity-40 transition-colors cursor-pointer"
              title="Zoom In"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </button>

            <div className="w-px h-3.5 bg-gray-700 mx-1" />

            {chartBase64 && (
              <button
                onClick={handleDownload}
                className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-gray-800/80 hover:bg-gray-700 text-gray-200 transition-colors cursor-pointer"
                title="Download PNG"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <span>PNG</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1 rounded-md bg-gray-800/80 hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors cursor-pointer ml-1"
              title="Close (Esc)"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Zoomable & Interactive Canvas Container */}
        <div
          ref={containerRef}
          className={`relative flex-1 flex items-center justify-center p-4 overflow-hidden bg-gray-950/40 ${
            zoom > 1 ? (isDragging ? "cursor-grabbing" : "cursor-grab") : "cursor-default"
          }`}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
        >
          <div
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transition: isDragging ? "none" : "transform 0.12s ease-out",
            }}
            className="w-full h-full flex items-center justify-center max-w-full max-h-full"
          >
            {processedSvg ? (
              <div
                dangerouslySetInnerHTML={{ __html: processedSvg }}
                className="w-full h-full flex items-center justify-center [&>svg]:max-h-[60vh] [&>svg]:w-auto [&>svg]:object-contain pointer-events-auto"
              />
            ) : chartBase64 ? (
              <img
                src={`data:image/png;base64,${chartBase64}`}
                alt="Enlarged Chart"
                className="max-w-full max-h-[60vh] object-contain rounded-xl shadow-lg pointer-events-none"
              />
            ) : (
              <span className="text-xs text-gray-400">No chart available</span>
            )}
          </div>

          {/* Zero-Lag Tooltip in Zoom Modal */}
          <div
            ref={tooltipRef}
            className="pointer-events-none absolute z-40 transition-opacity duration-150 ease-out opacity-0 invisible"
            style={{ left: 0, top: 0 }}
          >
            <div className="bg-gray-950/95 text-white border border-gray-700/80 shadow-2xl rounded-xl px-3 py-1.5 text-xs backdrop-blur-md min-w-[120px]">
              <div ref={labelRef} className="font-semibold text-gray-200 truncate max-w-[180px]">
                Label
              </div>
              <div className="flex items-baseline justify-between gap-3 pt-0.5 border-t border-gray-800 mt-1">
                <span className="text-gray-400 text-[10px]">Value:</span>
                <span ref={valueRef} className="font-bold font-mono text-emerald-400 text-xs">
                  0
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Minimalist 1-Line Footer */}
        <div className="px-4 py-1.5 border-t border-gray-800 bg-gray-950/60 flex items-center justify-between text-[10px] text-gray-500">
          <span>Scroll to zoom. Drag to pan. Hover bars or points for metrics.</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
