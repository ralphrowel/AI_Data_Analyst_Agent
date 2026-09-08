import { useState, useRef } from "react";

export default function NewChatModal({
  isOpen,
  onClose,
  onCreate,
}) {
  const [localFile, setLocalFile] = useState(null);
  const [customTitle, setCustomTitle] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const processFile = (file) => {
    if (!file) return;
    if (file.name.toLowerCase().endsWith(".csv")) {
      setLocalFile(file);
      if (!customTitle) {
        const cleanName = file.name
          .replace(/\.[^/.]+$/, "")
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
        setCustomTitle(`${cleanName} Workspace`);
      }
    } else {
      alert("Please select a valid CSV (.csv) file.");
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleResetFile = (e) => {
    e.stopPropagation();
    setLocalFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!localFile) {
      alert("Please select a .csv file from your computer.");
      return;
    }
    try {
      setIsSubmitting(true);
      await onCreate({
        file: localFile,
        title: customTitle.trim() || undefined,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return "0 KB";
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none animate-in fade-in duration-150">
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-surface-200 dark:border-gray-700 w-full max-w-md p-6 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-surface-200 dark:border-gray-700">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-accent/15 dark:bg-accent/20 flex items-center justify-center text-accent shadow-xs">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-bold text-surface-900 dark:text-gray-100">
                New Chat Workspace
              </h3>
              <p className="text-[11px] text-surface-500 dark:text-gray-400 leading-tight">
                Upload a CSV file to create an isolated conversational void.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="p-1 rounded-md text-surface-400 hover:text-surface-700 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-50"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* File Picker & Drag-and-Drop Area */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-surface-700 dark:text-gray-200">
              Select Dataset File:
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-accent bg-accent/10 dark:bg-accent/15"
                  : localFile
                  ? "border-accent/50 bg-accent/5 dark:bg-accent/10"
                  : "border-surface-300 dark:border-gray-700 hover:border-accent dark:hover:border-accent bg-surface-50 dark:bg-gray-950/50"
              }`}
            >
              {localFile ? (
                <div className="space-y-2">
                  <div className="w-10 h-10 mx-auto rounded-xl bg-accent/15 dark:bg-accent/25 text-accent flex items-center justify-center">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-surface-900 dark:text-gray-100 font-mono break-all">
                      {localFile.name}
                    </p>
                    <p className="text-[10px] text-surface-500 dark:text-gray-400 mt-0.5">
                      {formatSize(localFile.size)} • Ready to upload & analyze
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleResetFile}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-md text-surface-600 dark:text-gray-300 hover:bg-surface-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    Change file
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-10 h-10 mx-auto rounded-xl bg-surface-200/70 dark:bg-gray-800 text-surface-500 dark:text-gray-400 flex items-center justify-center">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-surface-800 dark:text-gray-200">
                      Click to browse or drag & drop CSV file here
                    </p>
                    <p className="text-[10px] text-surface-400 dark:text-gray-500 mt-0.5">
                      Accepts standard tabular .csv files
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Optional Chat Title */}
          <div>
            <label className="text-xs font-semibold text-surface-700 dark:text-gray-200 block mb-1">
              Workspace Title <span className="text-surface-400 dark:text-gray-500 text-[10px] font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={customTitle}
              onChange={(e) => setCustomTitle(e.target.value)}
              placeholder="e.g., Tech Salaries Analysis"
              className="w-full text-xs px-3 py-2 rounded-lg bg-surface-50 dark:bg-gray-950 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-100 placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-3 border-t border-surface-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!localFile || isSubmitting}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg text-white shadow-xs transition-all ${
                !localFile || isSubmitting
                  ? "bg-accent/40 cursor-not-allowed"
                  : "bg-accent hover:opacity-90 cursor-pointer"
              }`}
            >
              {isSubmitting ? "Creating..." : "Create Workspace"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
