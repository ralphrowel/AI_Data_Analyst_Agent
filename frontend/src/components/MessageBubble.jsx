import { useState } from "react";

export default function MessageBubble({ message }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

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
      ["Has Chart", message.chart_base64 ? "Yes" : "No"],
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
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
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
          </div>
        )}
        {message.chart_base64 && (
          <img
            src={`data:image/png;base64,${message.chart_base64}`}
            alt="Chart"
            className="mt-3 rounded-lg w-full max-h-80 object-contain bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700"
          />
        )}
      </div>
    </div>
  );
}
