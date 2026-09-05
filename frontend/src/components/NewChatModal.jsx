import { useState, useRef } from "react";

export default function NewChatModal({
  isOpen,
  availableDatasets = [],
  onClose,
  onCreate,
}) {
  const [activeTab, setActiveTab] = useState("storage"); // 'storage' | 'device'
  const [selectedDataset, setSelectedDataset] = useState(
    availableDatasets[0]?.name || "netflix_titles.csv"
  );
  const [localFile, setLocalFile] = useState(null);
  const [customTitle, setCustomTitle] = useState("");
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.toLowerCase().endsWith(".csv")) {
        setLocalFile(file);
      } else {
        alert("Please select a valid .csv file.");
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (activeTab === "device") {
      if (!localFile) {
        alert("Please select a .csv file from your computer.");
        return;
      }
      onCreate({
        source: "device",
        file: localFile,
        title: customTitle.trim() || undefined,
      });
    } else {
      onCreate({
        source: "storage",
        datasetName: selectedDataset,
        title: customTitle.trim() || undefined,
      });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none animate-in fade-in duration-150">
      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-surface-200 dark:border-gray-700 w-full max-w-md p-5 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-surface-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent/15 dark:bg-accent/20 flex items-center justify-center text-accent">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-surface-800 dark:text-gray-100">
                New Chat Workspace
              </h3>
              <p className="text-[11px] text-surface-400 dark:text-gray-500 leading-tight">
                Data will be locked to this isolated chat void.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-surface-400 hover:text-surface-700 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Source Selector Tabs */}
        <div className="grid grid-cols-2 gap-1 bg-surface-100 dark:bg-gray-950 p-1 rounded-lg mt-4 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab("storage")}
            className={`py-1.5 rounded-md transition-all cursor-pointer ${
              activeTab === "storage"
                ? "bg-white dark:bg-gray-800 text-surface-800 dark:text-gray-100 shadow-xs"
                : "text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200"
            }`}
          >
            Available Storage
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("device")}
            className={`py-1.5 rounded-md transition-all cursor-pointer ${
              activeTab === "device"
                ? "bg-white dark:bg-gray-800 text-surface-800 dark:text-gray-100 shadow-xs"
                : "text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200"
            }`}
          >
            Open Local File
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Tab 1: Storage Dataset Selection */}
          {activeTab === "storage" && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-surface-600 dark:text-gray-300">
                Select Dataset:
              </label>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                {availableDatasets.map((d) => (
                  <label
                    key={d.name}
                    className={`flex items-center justify-between p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                      selectedDataset === d.name
                        ? "border-accent bg-accent/10 dark:bg-accent/15 text-accent font-medium"
                        : "border-surface-200 dark:border-gray-700 bg-surface-50 dark:bg-gray-950/50 hover:bg-surface-100 dark:hover:bg-gray-700/50 text-surface-700 dark:text-gray-300"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="dataset"
                        value={d.name}
                        checked={selectedDataset === d.name}
                        onChange={() => setSelectedDataset(d.name)}
                        className="text-accent focus:ring-accent/30 cursor-pointer"
                      />
                      <span className="font-mono">{d.name}</span>
                    </div>
                    <span className="text-[10px] opacity-70">
                      {d.rows.toLocaleString()} rows
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Tab 2: Open Local File from Computer */}
          {activeTab === "device" && (
            <div className="space-y-2">
              <label className="text-xs font-medium text-surface-600 dark:text-gray-300">
                Choose CSV from Computer:
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
                className="border-2 border-dashed border-surface-300 dark:border-gray-700 hover:border-accent dark:hover:border-accent rounded-xl p-5 text-center cursor-pointer transition-colors bg-surface-50 dark:bg-gray-950/50"
              >
                <svg className="w-8 h-8 mx-auto mb-2 text-surface-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                {localFile ? (
                  <div>
                    <p className="text-xs font-semibold text-accent font-mono">
                      {localFile.name}
                    </p>
                    <p className="text-[10px] text-surface-400 dark:text-gray-500 mt-0.5">
                      {(localFile.size / 1024).toFixed(1)} KB • Click to choose another
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-xs font-medium text-surface-700 dark:text-gray-200">
                      Click to browse your file explorer
                    </p>
                    <p className="text-[10px] text-surface-400 dark:text-gray-500 mt-0.5">
                      Accepts standard .csv files
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Optional Chat Title */}
          <div>
            <label className="text-xs font-medium text-surface-600 dark:text-gray-300 block mb-1">
              Workspace Title <span className="text-surface-400 dark:text-gray-500 text-[10px] font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={customTitle}
              onChange={(e) => setCustomTitle(e.target.value)}
              placeholder="e.g., Q3 Financial Review"
              className="w-full text-xs px-3 py-2 rounded-lg bg-surface-50 dark:bg-gray-950 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-100 placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-2 border-t border-surface-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-accent text-white hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
            >
              Create Workspace
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
