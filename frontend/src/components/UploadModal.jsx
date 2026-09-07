import { useState, useRef } from "react";
import { uploadDataset, fetchDatasets } from "../api";

export default function UploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
  onStartNewChatWithDataset,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const resetState = () => {
    setSelectedFile(null);
    setFileContent("");
    setIsDragging(false);
    setUploading(false);
    setUploadResult(null);
    setErrorMessage("");
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const processFile = (file) => {
    setErrorMessage("");
    setUploadResult(null);
    const name = file.name.toLowerCase();
    const isCsv = name.endsWith(".csv");
    const isDoc = name.endsWith(".md") || name.endsWith(".txt");

    if (!isCsv && !isDoc) {
      setErrorMessage("Please select a .csv dataset or a .md/.txt knowledge document.");
      return;
    }

    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setFileContent(e.target.result);
    };
    reader.onerror = () => {
      setErrorMessage("Failed to read local file.");
    };
    reader.readAsText(file);
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

  const handleUpload = async () => {
    if (!selectedFile || !fileContent) return;
    setUploading(true);
    setErrorMessage("");
    try {
      const res = await uploadDataset(selectedFile.name, fileContent);
      setUploadResult(res);
      if (onUploadSuccess) onUploadSuccess(res);
    } catch (err) {
      setErrorMessage(err.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleStartChat = () => {
    if (uploadResult && uploadResult.type === "dataset" && onStartNewChatWithDataset) {
      onStartNewChatWithDataset(uploadResult.name);
      handleClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none animate-in fade-in duration-150">
      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-surface-200 dark:border-gray-700 w-full max-w-lg p-5 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-surface-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent/15 dark:bg-accent/20 flex items-center justify-center text-accent">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-surface-800 dark:text-gray-100">
                Upload File or Knowledge
              </h3>
              <p className="text-[11px] text-surface-400 dark:text-gray-500 leading-tight">
                Upload CSV datasets or Markdown/Text knowledge notes.
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-md text-surface-400 hover:text-surface-700 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Drag & Drop Zone */}
        <div className="mt-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.md,.txt"
            onChange={handleFileChange}
            className="hidden"
          />
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
              isDragging
                ? "border-accent bg-accent/10 dark:bg-accent/15 scale-[1.01]"
                : "border-surface-300 dark:border-gray-700 hover:border-accent dark:hover:border-accent bg-surface-50 dark:bg-gray-950/50"
            }`}
          >
            <div className="w-10 h-10 mx-auto mb-2 rounded-full bg-surface-100 dark:bg-gray-800 flex items-center justify-center text-surface-500 dark:text-gray-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            {selectedFile ? (
              <div>
                <p className="text-xs font-semibold text-accent font-mono">
                  {selectedFile.name}
                </p>
                <p className="text-[10px] text-surface-400 dark:text-gray-500 mt-1">
                  {(selectedFile.size / 1024).toFixed(1)} KB •{" "}
                  {selectedFile.name.toLowerCase().endsWith(".csv") ? "CSV Dataset" : "Knowledge Document"}
                </p>
                <p className="text-[10px] text-surface-500 dark:text-gray-400 mt-0.5 underline">
                  Click or drop to replace
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-medium text-surface-700 dark:text-gray-200">
                  Drag and drop your file here, or browse
                </p>
                <p className="text-[10px] text-surface-400 dark:text-gray-500 mt-1">
                  Supports <strong className="text-surface-600 dark:text-gray-300">.csv</strong> (Structured Datasets) and <strong className="text-surface-600 dark:text-gray-300">.md, .txt</strong> (RAG Knowledge)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div className="mt-3 p-2.5 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Success Result Card */}
        {uploadResult && (
          <div className="mt-3 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-700 dark:text-emerald-300 mb-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Upload Successful!</span>
            </div>
            <p className="text-[11px] opacity-90">{uploadResult.message}</p>
            {uploadResult.type === "dataset" && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/50 font-mono">
                  {uploadResult.rows.toLocaleString()} rows • {uploadResult.columns} columns
                </span>
                <button
                  type="button"
                  onClick={handleStartChat}
                  className="ml-auto text-xs px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-colors cursor-pointer shadow-xs"
                >
                  Start Chat with this Dataset →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-surface-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleClose}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-accent text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity shadow-sm cursor-pointer flex items-center gap-1.5"
          >
            {uploading ? (
              <>
                <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                <span>Uploading...</span>
              </>
            ) : (
              <span>Upload to System</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
