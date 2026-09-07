import { useRef, useMemo } from "react";

function formatValue(v) {
  if (v === null || v === undefined) return "";
  const num = Number(v);
  if (isNaN(num)) return v;
  if (Number.isInteger(num)) return num.toLocaleString();
  return num.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 });
}

export default function InteractiveChart({
  chartSvg,
  chartBase64,
  onZoom,
  compact = false,
  className = "",
}) {
  const containerRef = useRef(null);
  const tooltipRef = useRef(null);
  const labelRef = useRef(null);
  const valueRef = useRef(null);
  const activeElementRef = useRef(null);

  // Clean and prepare Matplotlib SVG for inline responsive rendering
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

  const handleMouseMove = (e) => {
    if (!containerRef.current || !tooltipRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if mouse is directly over a chart datum (bar, slice, or point)
    const datumEl = e.target.closest('[id^="datum__"]');
    if (datumEl) {
      const parts = datumEl.id.split("__");
      if (parts.length >= 3) {
        const label = parts[1];
        const val = parts[2];

        // Update tooltip content directly via DOM for zero-lag 60fps response
        if (labelRef.current) labelRef.current.textContent = label;
        if (valueRef.current) valueRef.current.textContent = formatValue(val);

        // Highlight element
        if (activeElementRef.current !== datumEl) {
          if (activeElementRef.current) activeElementRef.current.style.filter = "";
          datumEl.style.filter = "drop-shadow(0 0 6px rgba(59, 130, 246, 0.8)) brightness(1.2)";
          datumEl.style.transition = "filter 0.1s ease-out, brightness 0.1s ease-out";
          activeElementRef.current = datumEl;
        }

        // Position tooltip with offset
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

    // Not over any datum element -> immediately hide tooltip and clear highlight
    clearHighlight();
  };

  const handleMouseLeave = () => {
    clearHighlight();
  };

  const handleClick = () => {
    clearHighlight();
    if (onZoom) onZoom();
  };

  // Fallback to PNG if no SVG is available
  if (!processedSvg) {
    if (chartBase64) {
      return (
        <div
          className={`relative group/chart rounded-lg overflow-hidden cursor-pointer ${className}`}
          onClick={handleClick}
        >
          <img
            src={`data:image/png;base64,${chartBase64}`}
            alt="Chart"
            className="w-full max-h-80 object-contain bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-lg group-hover/chart:opacity-95 transition-opacity"
          />
          {onZoom && (
            <div className="absolute inset-0 bg-black/30 opacity-0 group-hover/chart:opacity-100 flex items-center justify-center gap-1.5 text-white text-xs font-semibold backdrop-blur-2xs transition-opacity rounded-lg">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
              </svg>
              <span>Click anywhere to zoom</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={`relative group/chart rounded-xl overflow-hidden bg-white dark:bg-gray-800/90 border border-surface-200 dark:border-gray-700 select-none cursor-pointer transition-shadow hover:shadow-md ${
        compact ? "mt-3" : ""
      } ${className}`}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Real Matplotlib SVG Render */}
      <div
        dangerouslySetInnerHTML={{ __html: processedSvg }}
        className="w-full flex items-center justify-center overflow-hidden [&>svg]:max-h-80 [&>svg]:w-full [&>svg]:object-contain pointer-events-auto"
      />

      {/* Floating Hardware-Accelerated Zero-Lag Tooltip */}
      <div
        ref={tooltipRef}
        className="pointer-events-none absolute z-30 transition-opacity duration-150 ease-out opacity-0 invisible"
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

      {/* Click-to-Zoom Hint Badge on Top Right */}
      {onZoom && (
        <div className="absolute top-2.5 right-2.5 opacity-0 group-hover/chart:opacity-100 transition-opacity duration-150 pointer-events-none">
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-gray-900/85 text-white text-[11px] font-medium shadow-md backdrop-blur-sm border border-gray-700/60">
            <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
            </svg>
            <span>Click to zoom</span>
          </div>
        </div>
      )}
    </div>
  );
}
