import { useState } from "react";
import ReactMarkdown from "react-markdown";
import ChartZoomModal from "./ChartZoomModal";
import InteractiveChart from "./InteractiveChart";

function QualityBadge({ badge }) {
  if (!badge) return null;
  const isTrustworthy = badge.is_trustworthy;
  const isCleaned = badge.version_role === "cleaned";

  return (
    <div className="mb-2.5">
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border shadow-2xs transition-colors ${
          isTrustworthy
            ? "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/60"
            : "bg-amber-50 text-amber-900 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800/70"
        }`}
        title={badge.badge_text}
      >
        {isTrustworthy ? (
          <svg className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
          </svg>
        ) : (
          <svg className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        )}
        <span>
          {isCleaned ? "Cleaned Version" : isTrustworthy ? "Verified Clean" : "Raw Data Notice"}
          {" • "}
          <strong className="font-semibold">Score: {badge.score}/100 ({badge.grade})</strong>
        </span>
      </div>

      {!isTrustworthy && badge.warning && (
        <div className="mt-1.5 p-2.5 rounded-lg bg-amber-100/70 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-[11.5px] leading-relaxed text-amber-900 dark:text-amber-200">
          <div className="flex items-center gap-1 font-semibold mb-0.5 text-amber-950 dark:text-amber-100">
            <svg className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span>Data Quality Warning</span>
          </div>
          <p>{badge.warning}</p>
        </div>
      )}
    </div>
  );
}

export default function MessageBubble({ message, onPinToDashboard }) {
  const [copied, setCopied] = useState(false);
  const [showZoom, setShowZoom] = useState(false);
  const isUser = message.role === "user";
  const hasChart = Boolean(message.chart_svg || message.chart_base64 || message.chart_spec);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const handleDownloadCsv = () => {
    const headers = ["Field", "Value"];
    const rows = [
      ["Operation", message.operation || "N/A"],
      ["Summary", message.text],
      ["Has Chart", hasChart ? "Yes" : "No"],
    ];
    const csvContent = [
      headers.join(","),
      ...rows.map((r) => r.map((v) => `"${v.replace(/"/g, '""')}"`).join(",")),
    ].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `result_${message.id}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-accent text-white rounded-br-md"
            : "bg-surface-100 dark:bg-gray-800 text-surface-800 dark:text-gray-100 rounded-bl-md border border-surface-200 dark:border-gray-700"
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
        ) : (
          <div className="text-sm leading-relaxed space-y-2">
            {message.quality_badge && <QualityBadge badge={message.quality_badge} />}
            <ReactMarkdown
              components={{
                h1: ({ node, ...props }) => (
                  <h1 className="text-base font-bold text-surface-900 dark:text-white mt-1 mb-1.5" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-sm font-bold text-surface-900 dark:text-white mt-2 mb-1" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-sm font-bold text-surface-900 dark:text-white mt-2 mb-1" {...props} />
                ),
                p: ({ node, ...props }) => (
                  <p className="mb-2 leading-relaxed text-surface-800 dark:text-gray-100 last:mb-0" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc pl-5 mb-2 space-y-1 text-surface-800 dark:text-gray-100" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal pl-5 mb-2 space-y-1 text-surface-800 dark:text-gray-100" {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li className="leading-snug" {...props} />
                ),
                strong: ({ node, ...props }) => (
                  <strong className="font-semibold text-surface-950 dark:text-white" {...props} />
                ),
                hr: ({ node, ...props }) => (
                  <hr className="my-2.5 border-surface-200 dark:border-gray-700" {...props} />
                ),
                code: ({ node, inline, ...props }) =>
                  inline ? (
                    <code className="px-1 py-0.5 rounded bg-surface-200 dark:bg-gray-700 text-accent font-mono text-xs" {...props} />
                  ) : (
                    <code className="block p-2 rounded-lg bg-surface-200/70 dark:bg-gray-900 text-surface-900 dark:text-gray-200 font-mono text-xs overflow-x-auto my-1.5" {...props} />
                  ),
              }}
            >
              {message.text}
            </ReactMarkdown>
          </div>
        )}
        {!isUser && (
          <div className="flex items-center gap-1 mt-2 pt-2 border-t border-surface-200/50 dark:border-gray-700/50">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-colors cursor-pointer text-surface-500 hover:text-surface-700 hover:bg-surface-200/50"
              title="Copy summary"
            >
              {copied ? (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
                </svg>
              )}
            </button>
            <button
              onClick={handleDownloadCsv}
              className="flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-colors cursor-pointer text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200 hover:bg-surface-200/50 dark:hover:bg-gray-700/50"
              title="Download result as CSV"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </button>
            {hasChart && (
              <>
                <button
                  onClick={() => setShowZoom(true)}
                  className="flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-colors cursor-pointer text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200 hover:bg-surface-200/50 dark:hover:bg-gray-700/50"
                  title="Enlarge and zoom chart"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
                  </svg>
                  <span className="text-[11px]">Zoom</span>
                </button>
                {onPinToDashboard && (
                  <button
                    onClick={() => {
                      onPinToDashboard(message);
                    }}
                    className="flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-colors cursor-pointer text-surface-500 dark:text-gray-400 hover:text-accent dark:hover:text-accent hover:bg-surface-200/50 dark:hover:bg-gray-700/50"
                    title="Pin this chart to live Dashboard"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
                    </svg>
                    <span className="text-[11px]">Pin</span>
                  </button>
                )}
              </>
            )}
          </div>
        )}


        {/* Real Matplotlib Chart with interactive hover tooltips */}
        {hasChart && (
          <InteractiveChart
            chartSvg={message.chart_svg}
            chartBase64={message.chart_base64}
            onZoom={() => setShowZoom(true)}
            compact={true}
          />
        )}
      </div>

      {showZoom && (
        <ChartZoomModal
          chartBase64={message.chart_base64}
          chartSvg={message.chart_svg}
          onClose={() => setShowZoom(false)}
          title={message.chart_spec?.title || "Analysis Chart"}
        />
      )}
    </div>
  );
}
