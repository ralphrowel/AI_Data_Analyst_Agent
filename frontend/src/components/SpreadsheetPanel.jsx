import { useState, useEffect, useCallback, useRef } from "react";
import {
  fetchDatasetRows,
  updateDatasetCells,
  addDatasetRow,
  deleteDatasetRow,
} from "../api";

export default function SpreadsheetPanel({ datasetName, onDatasetUpdated }) {
  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [totalRows, setTotalRows] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [totalPages, setTotalPages] = useState(1);

  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [statusNotification, setStatusNotification] = useState(null);

  // Pending edits: { [cellKey]: { rowIndex, column, originalValue, newValue } }
  const [pendingEdits, setPendingEdits] = useState({});

  // Active inline cell edit: { rowIndex, column }
  const [editingCell, setEditingCell] = useState(null);
  const [cellDraftValue, setCellDraftValue] = useState("");
  const editInputRef = useRef(null);

  // Add row modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRowData, setNewRowData] = useState({});
  const [isAddingRow, setIsAddingRow] = useState(false);

  // Delete row confirmation
  const [rowToDelete, setRowToDelete] = useState(null);
  const [isDeletingRow, setIsDeletingRow] = useState(false);

  // Fetch paginated data from backend
  const loadData = useCallback(async () => {
    if (!datasetName) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchDatasetRows(
        datasetName,
        page,
        pageSize,
        activeSearch,
        sortBy,
        sortOrder
      );
      setRows(data.rows || []);
      setColumns(data.columns || []);
      setTotalRows(data.total_rows || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setErrorMessage(err.message || "Failed to load spreadsheet records");
    } finally {
      setIsLoading(false);
    }
  }, [datasetName, page, pageSize, activeSearch, sortBy, sortOrder]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Focus inline edit input when active
  useEffect(() => {
    if (editingCell && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingCell]);

  // Auto-dismiss status notifications
  useEffect(() => {
    if (statusNotification) {
      const timer = setTimeout(() => setStatusNotification(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [statusNotification]);

  const handleSearchSubmit = (e) => {
    if (e) e.preventDefault();
    setActiveSearch(searchInput.trim());
    setPage(1);
  };

  const handleClearSearch = () => {
    setSearchInput("");
    setActiveSearch("");
    setPage(1);
  };

  const handleSort = (colName) => {
    if (sortBy === colName) {
      if (sortOrder === "asc") {
        setSortOrder("desc");
      } else {
        setSortBy("");
        setSortOrder("asc");
      }
    } else {
      setSortBy(colName);
      setSortOrder("asc");
    }
    setPage(1);
  };

  // Cell editing triggers
  const handleCellDoubleClick = (row, col) => {
    const rowIdx = row._row_index;
    const key = `${rowIdx}_${col.name}`;
    const currentValue =
      pendingEdits[key] !== undefined
        ? pendingEdits[key].newValue
        : (row[col.name] ?? "");
    setEditingCell({ rowIndex: rowIdx, column: col.name });
    setCellDraftValue(currentValue === null ? "" : String(currentValue));
  };

  const handleCellSave = (rowIdx, colName) => {
    if (!editingCell) return;
    const targetRow = rows.find((r) => r._row_index === rowIdx);
    if (!targetRow) {
      setEditingCell(null);
      return;
    }

    const originalVal = targetRow[colName];
    const originalStr = originalVal === null || originalVal === undefined ? "" : String(originalVal);
    const key = `${rowIdx}_${colName}`;

    if (cellDraftValue !== originalStr) {
      setPendingEdits((prev) => ({
        ...prev,
        [key]: {
          row_index: rowIdx,
          column: colName,
          originalValue: originalVal,
          value: cellDraftValue,
        },
      }));
    } else {
      // Reverted to original, remove from pending
      setPendingEdits((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
    setEditingCell(null);
  };

  const handleCellKeyDown = (e, rowIdx, colName) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleCellSave(rowIdx, colName);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setEditingCell(null);
    }
  };

  // Commit pending edits to server
  const handleSaveChanges = async () => {
    const editList = Object.values(pendingEdits);
    if (editList.length === 0) return;

    setIsSaving(true);
    setErrorMessage(null);
    try {
      const payload = editList.map((item) => ({
        row_index: item.row_index,
        column: item.column,
        value: item.value,
      }));
      await updateDatasetCells(datasetName, payload);
      setStatusNotification(`Successfully saved ${payload.length} modification${payload.length > 1 ? "s" : ""}.`);
      setPendingEdits({});
      if (onDatasetUpdated) onDatasetUpdated();
      await loadData();
    } catch (err) {
      setErrorMessage(err.message || "Failed to commit changes to dataset");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiscardChanges = () => {
    setPendingEdits({});
    setStatusNotification("Unsaved changes discarded.");
  };

  // Export current view or full rows to CSV
  const handleExportCSV = () => {
    if (rows.length === 0) return;
    const colKeys = columns.map((c) => c.name);
    const headerRow = colKeys.map((c) => `"${c.replace(/"/g, '""')}"`).join(",");
    const dataRows = rows.map((row) => {
      return colKeys
        .map((colName) => {
          const key = `${row._row_index}_${colName}`;
          const val = pendingEdits[key] !== undefined ? pendingEdits[key].value : row[colName];
          const str = val === null || val === undefined ? "" : String(val);
          return `"${str.replace(/"/g, '""')}"`;
        })
        .join(",");
    });
    const csvContent = [headerRow, ...dataRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${datasetName || "dataset"}_export.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Add row submission
  const handleConfirmAddRow = async (e) => {
    e.preventDefault();
    setIsAddingRow(true);
    try {
      await addDatasetRow(datasetName, newRowData);
      setShowAddModal(false);
      setNewRowData({});
      setStatusNotification("New row successfully added.");
      if (onDatasetUpdated) onDatasetUpdated();
      await loadData();
    } catch (err) {
      setErrorMessage(err.message || "Failed to add row");
    } finally {
      setIsAddingRow(false);
    }
  };

  // Delete row execution
  const handleConfirmDeleteRow = async () => {
    if (rowToDelete === null) return;
    setIsDeletingRow(true);
    try {
      await deleteDatasetRow(datasetName, rowToDelete);
      setRowToDelete(null);
      setStatusNotification("Row removed.");
      if (onDatasetUpdated) onDatasetUpdated();
      await loadData();
    } catch (err) {
      setErrorMessage(err.message || "Failed to delete row");
    } finally {
      setIsDeletingRow(false);
    }
  };

  const pendingCount = Object.keys(pendingEdits).length;
  const startRowIndex = totalRows > 0 ? (page - 1) * pageSize + 1 : 0;
  const endRowIndex = Math.min(page * pageSize, totalRows);

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-surface-50 dark:bg-gray-950">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-2.5 bg-white dark:bg-gray-900 border-b border-surface-200 dark:border-gray-700 shrink-0 select-none">
        {/* Left: Search & Filter */}
        <div className="flex items-center gap-3">
          <form onSubmit={handleSearchSubmit} className="relative w-64 md:w-80">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-surface-400 dark:text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search table values..."
              className="w-full pl-9 pr-8 py-1.5 text-xs bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-lg text-surface-800 dark:text-gray-200 placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600 dark:text-gray-500 dark:hover:text-gray-300"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </form>

          {activeSearch && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent/10 text-accent font-medium flex items-center gap-1">
              <span>Filtered:</span>
              <span className="font-semibold truncate max-w-[120px]">"{activeSearch}"</span>
              <button
                type="button"
                onClick={handleClearSearch}
                className="ml-0.5 hover:opacity-75 cursor-pointer"
              >
                ✕
              </button>
            </span>
          )}

          <div className="hidden lg:flex items-center text-xs text-surface-500 dark:text-gray-400">
            {totalRows > 0 ? (
              <span>
                Showing <span className="font-medium text-surface-800 dark:text-gray-200">{startRowIndex}–{endRowIndex}</span> of{" "}
                <span className="font-semibold text-surface-800 dark:text-gray-200">{totalRows.toLocaleString()}</span> rows
              </span>
            ) : (
              <span>0 rows</span>
            )}
          </div>
        </div>

        {/* Right: Actions & Edit Controls */}
        <div className="flex items-center gap-2">
          {pendingCount > 0 && (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800/80 rounded-lg animate-fade-in">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-xs font-medium text-amber-800 dark:text-amber-300">
                {pendingCount} unsaved {pendingCount === 1 ? "change" : "changes"}
              </span>
              <button
                type="button"
                onClick={handleDiscardChanges}
                disabled={isSaving}
                className="text-[11px] text-surface-500 hover:text-surface-700 dark:text-gray-400 dark:hover:text-gray-200 underline cursor-pointer ml-1"
              >
                Discard
              </button>
              <button
                type="button"
                onClick={handleSaveChanges}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md bg-amber-600 hover:bg-amber-700 text-white shadow-xs transition-colors cursor-pointer disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-surface-100 dark:bg-gray-800 hover:bg-surface-200 dark:hover:bg-gray-700 border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-200 transition-colors cursor-pointer shadow-xs"
            title="Append a new record to this dataset"
          >
            <svg className="w-3.5 h-3.5 text-surface-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span>Add Row</span>
          </button>

          <button
            type="button"
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-surface-100 dark:bg-gray-800 hover:bg-surface-200 dark:hover:bg-gray-700 border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-200 transition-colors cursor-pointer shadow-xs"
            title="Export visible records to CSV file"
          >
            <svg className="w-3.5 h-3.5 text-surface-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            <span>Export CSV</span>
          </button>

          <button
            type="button"
            onClick={loadData}
            className="p-1.5 text-surface-500 hover:text-surface-800 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-800 rounded-lg border border-surface-200 dark:border-gray-700 transition-colors cursor-pointer shadow-xs"
            title="Refresh table"
          >
            <svg className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          </button>
        </div>
      </div>

      {/* Notification and Error Banners */}
      {statusNotification && (
        <div className="px-5 py-2 bg-emerald-50 dark:bg-emerald-950/40 border-b border-emerald-200 dark:border-emerald-800/80 text-emerald-800 dark:text-emerald-200 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <span>{statusNotification}</span>
          </div>
          <button onClick={() => setStatusNotification(null)} className="text-emerald-600 hover:opacity-75">✕</button>
        </div>
      )}

      {errorMessage && (
        <div className="px-5 py-2 bg-rose-50 dark:bg-rose-950/40 border-b border-rose-200 dark:border-rose-800/80 text-rose-800 dark:text-rose-200 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-rose-600 dark:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-600 hover:opacity-75">✕</button>
        </div>
      )}

      {/* Table Container */}
      <div className="flex-1 overflow-auto relative">
        {isLoading && (
          <div className="absolute inset-0 bg-white/60 dark:bg-gray-950/60 backdrop-blur-[1px] flex items-center justify-center z-20">
            <div className="flex items-center gap-2.5 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg border border-surface-200 dark:border-gray-700 shadow-md">
              <svg className="w-4 h-4 animate-spin text-accent" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span className="text-xs font-medium text-surface-700 dark:text-gray-200">Loading records...</span>
            </div>
          </div>
        )}

        <table className="w-full border-collapse text-left text-xs">
          {/* Table Header */}
          <thead className="bg-surface-100 dark:bg-gray-900 sticky top-0 z-10 select-none shadow-[0_1px_0_0_rgba(0,0,0,0.08)] dark:shadow-[0_1px_0_0_rgba(255,255,255,0.06)]">
            <tr>
              <th className="w-12 px-3 py-2.5 font-mono text-[11px] font-semibold text-surface-400 dark:text-gray-500 border-b border-r border-surface-200 dark:border-gray-800 text-center sticky left-0 bg-surface-100 dark:bg-gray-900 z-11">
                #
              </th>
              {columns.map((col) => {
                const isSorted = sortBy === col.name;
                return (
                  <th
                    key={col.name}
                    onClick={() => handleSort(col.name)}
                    className="px-3 py-2.5 font-medium text-surface-700 dark:text-gray-300 border-b border-r border-surface-200 dark:border-gray-800 cursor-pointer hover:bg-surface-200/70 dark:hover:bg-gray-800/80 transition-colors whitespace-nowrap"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-surface-900 dark:text-gray-100">{col.name}</span>
                        <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-surface-200 dark:bg-gray-800 text-surface-500 dark:text-gray-400 font-mono">
                          {col.type}
                        </span>
                      </div>
                      <div className="text-surface-400 dark:text-gray-500 w-3">
                        {isSorted ? (
                          sortOrder === "asc" ? "▲" : "▼"
                        ) : (
                          <span className="opacity-0 group-hover:opacity-100">↕</span>
                        )}
                      </div>
                    </div>
                  </th>
                );
              })}
              <th className="w-10 px-2 py-2.5 border-b border-surface-200 dark:border-gray-800 text-center text-surface-400 dark:text-gray-500 font-normal">
                Actions
              </th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-surface-200 dark:divide-gray-800 bg-white dark:bg-gray-950 font-sans">
            {rows.length === 0 && !isLoading ? (
              <tr>
                <td
                  colSpan={columns.length + 2}
                  className="px-4 py-16 text-center text-surface-400 dark:text-gray-500"
                >
                  <div className="flex flex-col items-center justify-center gap-2">
                    <svg className="w-8 h-8 text-surface-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    <span>No records found</span>
                  </div>
                </td>
              </tr>
            ) : (
              rows.map((row) => {
                const rowIdx = row._row_index;
                return (
                  <tr
                    key={rowIdx}
                    className="hover:bg-surface-50 dark:hover:bg-gray-900/60 transition-colors group"
                  >
                    {/* Sticky Row Index Column */}
                    <td className="px-2 py-1.5 font-mono text-[11px] text-surface-400 dark:text-gray-500 border-r border-surface-200 dark:border-gray-800 text-center sticky left-0 bg-white dark:bg-gray-950 group-hover:bg-surface-50 dark:group-hover:bg-gray-900/60 z-1 select-none">
                      {rowIdx + 1}
                    </td>

                    {/* Data Cells */}
                    {columns.map((col) => {
                      const cellKey = `${rowIdx}_${col.name}`;
                      const isPending = pendingEdits[cellKey] !== undefined;
                      const displayValue = isPending
                        ? pendingEdits[cellKey].value
                        : row[col.name];

                      const isEditing =
                        editingCell?.rowIndex === rowIdx &&
                        editingCell?.column === col.name;

                      return (
                        <td
                          key={col.name}
                          onDoubleClick={() => handleCellDoubleClick(row, col)}
                          title="Double-click to edit cell"
                          className={`px-3 py-1.5 border-r border-surface-200 dark:border-gray-800 whitespace-nowrap max-w-[280px] overflow-hidden text-ellipsis cursor-cell relative ${
                            isPending
                              ? "bg-amber-50/90 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 font-medium ring-1 ring-inset ring-amber-400/50"
                              : "text-surface-700 dark:text-gray-200"
                          }`}
                        >
                          {isPending && (
                            <span
                              className="absolute top-0 right-0 w-2 h-2 border-t-4 border-r-4 border-t-amber-500 border-r-amber-500"
                              title="Modified (unsaved)"
                            />
                          )}

                          {isEditing ? (
                            <input
                              ref={editInputRef}
                              type="text"
                              value={cellDraftValue}
                              onChange={(e) => setCellDraftValue(e.target.value)}
                              onBlur={() => handleCellSave(rowIdx, col.name)}
                              onKeyDown={(e) => handleCellKeyDown(e, rowIdx, col.name)}
                              className="w-full px-1.5 py-0.5 text-xs bg-white dark:bg-gray-900 border-2 border-accent rounded text-surface-900 dark:text-white focus:outline-none shadow-sm"
                            />
                          ) : (
                            <span>
                              {displayValue === null || displayValue === undefined ? (
                                <span className="text-surface-300 dark:text-gray-600 italic">null</span>
                              ) : (
                                String(displayValue)
                              )}
                            </span>
                          )}
                        </td>
                      );
                    })}

                    {/* Actions Column */}
                    <td className="px-2 py-1.5 border-surface-200 dark:border-gray-800 text-center">
                      <button
                        type="button"
                        onClick={() => setRowToDelete(rowIdx)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-surface-400 hover:text-rose-600 dark:text-gray-500 dark:hover:text-rose-400 rounded transition-opacity cursor-pointer"
                        title="Delete this row"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Bottom Pagination Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-2 bg-white dark:bg-gray-900 border-t border-surface-200 dark:border-gray-700 shrink-0 select-none text-xs">
        <div className="flex items-center gap-2 text-surface-500 dark:text-gray-400">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded px-2 py-0.5 text-surface-700 dark:text-gray-200 focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span className="hidden sm:inline">
            (Total {totalRows.toLocaleString()} rows)
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-surface-500 dark:text-gray-400 mr-2">
            Page <span className="font-semibold text-surface-800 dark:text-gray-200">{page}</span> of{" "}
            <span className="font-semibold text-surface-800 dark:text-gray-200">{totalPages}</span>
          </span>

          <button
            type="button"
            onClick={() => setPage(1)}
            disabled={page <= 1 || isLoading}
            className="px-2 py-1 rounded border border-surface-200 dark:border-gray-700 hover:bg-surface-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="First Page"
          >
            «
          </button>
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1 || isLoading}
            className="px-2.5 py-1 rounded border border-surface-200 dark:border-gray-700 hover:bg-surface-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Previous Page"
          >
            ‹
          </button>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages || isLoading}
            className="px-2.5 py-1 rounded border border-surface-200 dark:border-gray-700 hover:bg-surface-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Next Page"
          >
            ›
          </button>
          <button
            type="button"
            onClick={() => setPage(totalPages)}
            disabled={page >= totalPages || isLoading}
            className="px-2 py-1 rounded border border-surface-200 dark:border-gray-700 hover:bg-surface-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Last Page"
          >
            »
          </button>
        </div>
      </div>

      {/* Add Row Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-700 rounded-xl shadow-2xl max-w-lg w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="px-5 py-3.5 border-b border-surface-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-surface-900 dark:text-white">
                Add New Row to {datasetName}
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-surface-400 hover:text-surface-600 dark:text-gray-400 dark:hover:text-gray-200 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleConfirmAddRow} className="flex flex-col flex-1 overflow-hidden">
              <div className="p-5 overflow-y-auto space-y-3">
                {columns.map((col) => (
                  <div key={col.name}>
                    <label className="block text-xs font-medium text-surface-700 dark:text-gray-300 mb-1">
                      {col.name} <span className="font-mono text-[10px] text-surface-400">({col.type})</span>
                    </label>
                    <input
                      type="text"
                      value={newRowData[col.name] || ""}
                      onChange={(e) =>
                        setNewRowData({ ...newRowData, [col.name]: e.target.value })
                      }
                      placeholder={`Enter ${col.name}...`}
                      className="w-full px-3 py-1.5 text-xs bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 rounded-lg text-surface-900 dark:text-white placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
                    />
                  </div>
                ))}
              </div>

              <div className="px-5 py-3 bg-surface-50 dark:bg-gray-800/50 border-t border-surface-200 dark:border-gray-700 flex items-center justify-end gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-200 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAddingRow}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-accent text-white hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {isAddingRow ? "Adding..." : "Add Row"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Row Confirmation Modal */}
      {rowToDelete !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-700 rounded-xl shadow-2xl max-w-sm w-full p-5">
            <h3 className="text-sm font-semibold text-surface-900 dark:text-white mb-2">
              Delete Row #{rowToDelete + 1}?
            </h3>
            <p className="text-xs text-surface-500 dark:text-gray-400 mb-4 leading-relaxed">
              Are you sure you want to remove this record from the active dataset? This will update the dataset file.
            </p>
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setRowToDelete(null)}
                disabled={isDeletingRow}
                className="px-3 py-1.5 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-200 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDeleteRow}
                disabled={isDeletingRow}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-700 text-white transition-colors disabled:opacity-50"
              >
                {isDeletingRow ? "Deleting..." : "Delete Row"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
