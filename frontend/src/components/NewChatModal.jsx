import { useState, useRef, useEffect } from "react";

export default function NewChatModal({
  isOpen,
  onClose,
  onCreate,
  availableDatasets = [],
}) {
  const [activeTab, setActiveTab] = useState("catalog"); // "catalog" | "upload"
  const [selectedDatasetName, setSelectedDatasetName] = useState("");
  const [localFile, setLocalFile] = useState(null);
  const [customTitle, setCustomTitle] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  // Auto-select first available dataset if catalog tab is opened
  useEffect(() => {
    if (availableDatasets && availableDatasets.length > 0 && !selectedDatasetName) {
      setSelectedDatasetName(availableDatasets[0].name);
      const cleanName = availableDatasets[0].name
        .replace(/\.[^/.]+$/, "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      setCustomTitle(`${cleanName} Workspace`);
    }
  }, [availableDatasets, selectedDatasetName]);

  if (!isOpen) return null;

  const handleSelectCatalogDataset = (dName) => {
    setSelectedDatasetName(dName);
    const cleanName = dName
      .replace(/\.[^/.]+$/, "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    setCustomTitle(`${cleanName} Workspace`);
  };

  const processFile = (file) => {
    if (!file) return;
    if (file.name.toLowerCase().endsWith(".csv")) {
      setLocalFile(file);
      const cleanName = file.name
        .replace(/\.[^/.]+$/, "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      setCustomTitle(`${cleanName} Workspace`);
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
      setActiveTab("upload");
    }
  };

  const handleResetFile = (e) => {
    e.stopPropagation();
    setLocalFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (activeTab === "catalog") {
      if (!selectedDatasetName) {
        alert("Please select a dataset from the list.");
        return;
      }
      try {
        setIsSubmitting(true);
        await onCreate({
          datasetName: selectedDatasetName,
          title: customTitle.trim() || undefined,
        });
      } finally {
        setIsSubmitting(false);
      }
    } else {
      if (!localFile) {
        alert("Please select or drop a .csv file from your computer.");
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
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return "0 KB";
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const isMatchedPreloaded = localFile && availableDatasets.some(
    (d) => d.name.toLowerCase() === localFile.name.toLowerCase()
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none animate-in fade-in duration-150">
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-surface-200 dark:border-gray-700 w-full max-w-lg p-6 overflow-hidden">
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
                Select an existing dataset or upload a CSV to start an analysis session.
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

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-surface-100 dark:bg-gray-900/60 rounded-xl mt-4 border border-surface-200/80 dark:border-gray-700/60">
          <button
            type="button"
            onClick={() => setActiveTab("catalog")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === "catalog"
                ? "bg-white dark:bg-gray-800 text-surface-900 dark:text-gray-100 shadow-xs"
                : "text-surface-500 dark:text-gray-400 hover:text-surface-800 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            </svg>
            Existing Datasets ({availableDatasets.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("upload")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === "upload"
                ? "bg-white dark:bg-gray-800 text-surface-900 dark:text-gray-100 shadow-xs"
                : "text-surface-500 dark:text-gray-400 hover:text-surface-800 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            Upload New CSV
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {activeTab === "catalog" ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-surface-700 dark:text-gray-200">
                Choose a Dataset:
              </label>
              <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                {availableDatasets.length === 0 ? (
                  <p className="text-xs text-surface-400 dark:text-gray-500 py-3 text-center">
                    No catalog datasets found. Please upload a CSV.
                  </p>
                ) : (
                  availableDatasets.map((d) => {
                    const isSelected = selectedDatasetName === d.name;
                    return (
                      <div
                        key={d.name}
                        onClick={() => handleSelectCatalogDataset(d.name)}
                        className={`flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer ${
                          isSelected
                            ? "border-accent bg-accent/10 dark:bg-accent/15 ring-1 ring-accent/30"
                            : "border-surface-200 dark:border-gray-700 hover:border-surface-300 dark:hover:border-gray-600 bg-surface-50/50 dark:bg-gray-900/40"
                        }`}
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                            isSelected ? "bg-accent text-white" : "bg-surface-200 dark:bg-gray-700 text-surface-600 dark:text-gray-300"
                          }`}>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M1.5 5.625v1.5c0 .621.504 1.125 1.125 1.125" />
                            </svg>
                          </div>
                          <div className="truncate">
                            <p className="text-xs font-bold text-surface-900 dark:text-gray-100 font-mono truncate">
                              {d.name}
                            </p>
                            <p className="text-[10px] text-surface-500 dark:text-gray-400">
                              {(d.rows || 0).toLocaleString()} rows • {d.columns || 0} cols
                              {d.size_bytes ? ` • ${formatSize(d.size_bytes)}` : ""}
                            </p>
                          </div>
                        </div>
                        <div className="shrink-0 ml-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                            isSelected
                              ? "bg-accent text-white"
                              : "bg-surface-200 dark:bg-gray-700 text-surface-600 dark:text-gray-300"
                          }`}>
                            {isSelected ? "Selected" : "Select"}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          ) : (
            /* File Picker & Drag-and-Drop Area */
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-surface-700 dark:text-gray-200">
                Select CSV File:
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
                className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
                  isDragging
                    ? "border-accent bg-accent/10 dark:bg-accent/15"
                    : localFile
                    ? "border-accent/50 bg-accent/5 dark:bg-accent/10"
                    : "border-surface-300 dark:border-gray-700 hover:border-accent dark:hover:border-accent bg-surface-50 dark:bg-gray-950/50"
                }`}
              >
                {localFile ? (
                  <div className="space-y-2">
                    <div className="w-9 h-9 mx-auto rounded-xl bg-accent/15 dark:bg-accent/25 text-accent flex items-center justify-center">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs font-bold text-surface-900 dark:text-gray-100 font-mono break-all">
                        {localFile.name}
                      </p>
                      <p className="text-[10px] text-surface-500 dark:text-gray-400 mt-0.5">
                        {formatSize(localFile.size)} • Ready to analyze
                      </p>
                      {isMatchedPreloaded && (
                        <p className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 mt-1">
                          ✓ Matches system dataset (instant creation)
                        </p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={handleResetFile}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 text-[11px] font-medium rounded-md text-surface-600 dark:text-gray-300 hover:bg-surface-200 dark:hover:bg-gray-700 transition-colors"
                    >
                      Change file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="w-9 h-9 mx-auto rounded-xl bg-surface-200/70 dark:bg-gray-800 text-surface-500 dark:text-gray-400 flex items-center justify-center">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
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
          )}

          {/* Workspace Title */}
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
              disabled={(activeTab === "upload" && !localFile) || (activeTab === "catalog" && !selectedDatasetName) || isSubmitting}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg text-white shadow-xs transition-all ${
                (activeTab === "upload" && !localFile) || (activeTab === "catalog" && !selectedDatasetName) || isSubmitting
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
