import { useState, useEffect, useCallback } from "react";
import {
  fetchQualityReport,
  previewCleaning,
  applyCleaning,
  fetchDatasetLineage,
  switchSessionDataset,
} from "../api";

export default function QualityPanel({
  datasetName,
  activeSessionId,
  onDatasetSwitched,
  darkMode,
}) {
  const [report, setReport] = useState(null);
  const [lineage, setLineage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Issues filtering
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Cleaning plan configuration
  const [stripWhitespace, setStripWhitespace] = useState(true);
  const [dropDuplicates, setDropDuplicates] = useState(true);
  const [casingCol, setCasingCol] = useState("");
  const [casingType, setCasingType] = useState("title");
  const [normalizeDates, setNormalizeDates] = useState(true);
  const [imputeNumeric, setImputeNumeric] = useState("median");
  const [imputeCategorical, setImputeCategorical] = useState("mode");

  // Preview & Apply state
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewResult, setPreviewResult] = useState(null);
  const [isApplying, setIsApplying] = useState(false);
  const [appliedJob, setAppliedJob] = useState(null);
  const [isSwitching, setIsSwitching] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(false);

  const loadReport = useCallback(
    async (refresh = false) => {
      if (!datasetName) return;
      setIsLoading(true);
      setError(null);
      try {
        const [qualityData, lineageData] = await Promise.all([
          fetchQualityReport(datasetName, refresh),
          fetchDatasetLineage(datasetName).catch(() => null),
        ]);
        setReport(qualityData);
        setLineage(lineageData);

        // Pre-fill plan from suggested_plan if present
        if (qualityData.suggested_plan) {
          const sp = qualityData.suggested_plan;
          setStripWhitespace(sp.strip_whitespace !== false);
          setDropDuplicates(Boolean(sp.drop_duplicates_subset));
          setNormalizeDates(Boolean(sp.date_columns && sp.date_columns.length > 0));
        }
      } catch (err) {
        setError(err.message || "Failed to load quality report");
      } finally {
        setIsLoading(false);
      }
    },
    [datasetName]
  );

  useEffect(() => {
    loadReport();
    setPreviewResult(null);
    setAppliedJob(null);
  }, [loadReport]);

  const buildPlanPayload = () => {
    const plan = {
      strip_whitespace: stripWhitespace,
      normalize_column_names: false,
    };

    if (dropDuplicates) {
      plan.drop_duplicates_subset = true;
    }

    if (normalizeDates && report?.suggested_plan?.date_columns) {
      plan.date_columns = report.suggested_plan.date_columns;
    }

    if (casingCol) {
      plan.casing_rules = { [casingCol]: casingType };
    }

    // Build imputation from issues
    const missingCols = report?.issues
      ?.filter((i) => i.category === "MISSING" && i.column)
      ?.map((i) => i.column);

    if (missingCols && missingCols.length > 0) {
      const strategies = {};
      missingCols.forEach((col) => {
        strategies[col] = { strategy: imputeCategorical };
      });
      plan.missing_strategies = strategies;
    }

    return plan;
  };

  const handlePreview = async () => {
    setIsPreviewing(true);
    setError(null);
    try {
      const plan = buildPlanPayload();
      const res = await previewCleaning(datasetName, plan);
      setPreviewResult(res);
    } catch (err) {
      setError(err.message || "Failed to preview cleaning");
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleApplyClean = async () => {
    setShowApplyModal(false);
    setIsApplying(true);
    setError(null);
    try {
      const plan = buildPlanPayload();
      const job = await applyCleaning(datasetName, plan);
      setAppliedJob(job);
      // Reload report and lineage
      loadReport(true);
    } catch (err) {
      setError(err.message || "Failed to apply cleaning");
    } finally {
      setIsApplying(false);
    }
  };

  const handleSwitchDataset = async (targetName) => {
    if (!activeSessionId) return;
    setIsSwitching(true);
    try {
      await switchSessionDataset(activeSessionId, targetName);
      if (onDatasetSwitched) {
        onDatasetSwitched(targetName);
      }
    } catch (err) {
      setError(err.message || "Failed to switch active dataset");
    } finally {
      setIsSwitching(false);
    }
  };

  // Grade badge styling
  const getGradeColor = (grade) => {
    switch (grade) {
      case "A":
        return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30";
      case "B":
        return "bg-teal-500/10 text-teal-600 dark:text-teal-400 border-teal-500/30";
      case "C":
        return "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30";
      case "D":
      case "F":
      default:
        return "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30";
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30";
      case "WARNING":
        return "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30";
      case "INFO":
      default:
        return "bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30";
    }
  };

  if (!datasetName) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 p-8 text-center text-surface-500 dark:text-gray-400">
        <div className="w-16 h-16 mb-4 rounded-2xl bg-surface-100 dark:bg-gray-800 flex items-center justify-center text-surface-400">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1.5 1.5 0 011.06.44l5.414 5.414a1.5 1.5 0 01.44 1.06V19a2.25 2.25 0 01-2.25 2.25z" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-surface-800 dark:text-gray-200">No Active Dataset</h3>
        <p className="max-w-md mt-1 text-xs">Upload or select a dataset from the sidebar to inspect quality and run cleaning.</p>
      </div>
    );
  }

  // Filter issues
  const filteredIssues = (report?.issues || []).filter((issue) => {
    if (severityFilter !== "ALL" && issue.severity !== severityFilter) return false;
    if (categoryFilter !== "ALL" && issue.category !== categoryFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const colMatch = issue.column && issue.column.toLowerCase().includes(q);
      const descMatch = issue.description.toLowerCase().includes(q);
      if (!colMatch && !descMatch) return false;
    }
    return true;
  });

  return (
    <div className="flex flex-col flex-1 h-full overflow-y-auto bg-surface-50/50 dark:bg-gray-950/50">
      {/* Top Banner Alert / Switcher if cleaned version exists */}
      {appliedJob && (
        <div className="flex items-center justify-between px-6 py-3 bg-emerald-500/10 border-b border-emerald-500/20 text-emerald-800 dark:text-emerald-200 text-xs animate-fadeIn">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-emerald-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>
              Clean dataset <strong className="font-mono">{appliedJob.target_dataset}</strong> created successfully! Score improved from {appliedJob.score_before.overall_score}% to {appliedJob.score_after.overall_score}% (+{appliedJob.score_delta} pts).
            </span>
          </div>
          <button
            type="button"
            disabled={isSwitching}
            onClick={() => handleSwitchDataset(appliedJob.target_dataset)}
            className="px-3 py-1.5 font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 transition-colors shadow-xs cursor-pointer disabled:opacity-50"
          >
            {isSwitching ? "Switching..." : "Switch Active Workspace to Clean Dataset"}
          </button>
        </div>
      )}

      {error && (
        <div className="px-6 py-3 bg-rose-500/10 border-b border-rose-500/20 text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-semibold underline cursor-pointer">Dismiss</button>
        </div>
      )}

      <div className="p-6 max-w-7xl w-full mx-auto space-y-6">
        {/* Row 1: Executive Quality Header Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-surface-200/80 dark:border-gray-800/80 shadow-xs relative overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-6">
            {/* Left: Overall Health Score & Grade */}
            <div className="flex items-center gap-5">
              <div className="flex flex-col items-center justify-center w-24 h-24 rounded-2xl bg-surface-100 dark:bg-gray-800/80 border border-surface-200 dark:border-gray-700/80 shadow-inner">
                <span className="text-3xl font-extrabold tracking-tight text-surface-900 dark:text-white">
                  {report ? `${Math.round(report.summary.overall_score)}%` : "—"}
                </span>
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-400 tracking-wider">Health Score</span>
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="text-xl font-bold text-surface-900 dark:text-white">
                    {datasetName}
                  </h2>
                  {report && (
                    <span className={`px-2.5 py-0.5 text-xs font-bold rounded-md border ${getGradeColor(report.summary.grade)}`}>
                      Grade {report.summary.grade}
                    </span>
                  )}
                </div>
                <p className="text-xs text-surface-500 dark:text-gray-400 mt-1 max-w-xl">
                  {report ? report.summary.grade_label : "Analyzing dataset quality and integrity..."}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-[11px] font-semibold rounded-full ${
                      report?.summary.is_trustworthy
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${report?.summary.is_trustworthy ? "bg-emerald-500" : "bg-amber-500"}`} />
                    {report?.summary.is_trustworthy ? "Trustworthy for Analytics" : "Remediation Recommended"}
                  </span>
                  {lineage && lineage.role === "cleaned" && (
                    <span className="px-2 py-0.5 text-[10px] font-mono font-medium rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                      Derived Clean v{lineage.version}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Quick Actions */}
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={() => loadReport(true)}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium rounded-xl bg-surface-100 hover:bg-surface-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-surface-700 dark:text-gray-200 transition-colors cursor-pointer disabled:opacity-50"
                title="Force fresh scan"
              >
                <svg className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Re-scan</span>
              </button>
            </div>
          </div>

          {/* Quick Metrics Strip */}
          {report && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-5 mt-5 border-t border-surface-100 dark:border-gray-800/80">
              <div className="px-3 py-2 rounded-xl bg-surface-50 dark:bg-gray-800/40">
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500">Rows</span>
                <p className="text-sm font-bold text-surface-800 dark:text-gray-200">{report.summary.total_rows.toLocaleString()}</p>
              </div>
              <div className="px-3 py-2 rounded-xl bg-surface-50 dark:bg-gray-800/40">
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500">Columns</span>
                <p className="text-sm font-bold text-surface-800 dark:text-gray-200">{report.summary.total_columns}</p>
              </div>
              <div className="px-3 py-2 rounded-xl bg-surface-50 dark:bg-gray-800/40">
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500">Missing Cells</span>
                <p className="text-sm font-bold text-surface-800 dark:text-gray-200">{report.summary.missing_cells?.toLocaleString() || 0} ({report.summary.missing_percentage}%)</p>
              </div>
              <div className="px-3 py-2 rounded-xl bg-surface-50 dark:bg-gray-800/40">
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500">Duplicate Rows</span>
                <p className="text-sm font-bold text-surface-800 dark:text-gray-200">{report.summary.duplicate_rows?.toLocaleString() || 0}</p>
              </div>
              <div className="px-3 py-2 rounded-xl bg-surface-50 dark:bg-gray-800/40">
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500">Invalid Dates/Types</span>
                <p className="text-sm font-bold text-surface-800 dark:text-gray-200">{(report.summary.invalid_dates || 0) + (report.summary.invalid_types || 0)}</p>
              </div>
              <div className="px-3 py-2 rounded-xl bg-surface-50 dark:bg-gray-800/40">
                <span className="text-[10px] uppercase font-semibold text-surface-400 dark:text-gray-500">Total Defects</span>
                <p className="text-sm font-bold text-surface-800 dark:text-gray-200">{report.issues?.length || 0}</p>
              </div>
            </div>
          )}
        </div>

        {/* Row 2: Four Quality Dimensions Breakdown */}
        {report?.dimensions && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(report.dimensions).map(([key, dim]) => (
              <div
                key={key}
                className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-surface-200/80 dark:border-gray-800/80 shadow-xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-surface-500 dark:text-gray-400">
                      {dim.name}
                    </span>
                    <span className="text-sm font-extrabold text-surface-900 dark:text-white">
                      {dim.score}%
                    </span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full h-2 rounded-full bg-surface-100 dark:bg-gray-800 overflow-hidden mb-3">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        dim.score >= 90
                          ? "bg-emerald-500"
                          : dim.score >= 80
                          ? "bg-teal-500"
                          : dim.score >= 70
                          ? "bg-amber-500"
                          : "bg-rose-500"
                      }`}
                      style={{ width: `${dim.score}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-surface-500 dark:text-gray-400 leading-relaxed">
                    {dim.details}
                  </p>
                </div>
                <div className="pt-3 mt-3 border-t border-surface-100 dark:border-gray-800 flex items-center justify-between text-[10px] text-surface-400 dark:text-gray-500">
                  <span>Weight: {Math.round(dim.weight * 100)}%</span>
                  <span>{dim.defects_count} defect(s)</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Row 3: Cleaning Plan Builder & Preview */}
        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-surface-200/80 dark:border-gray-800/80 shadow-xs space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-surface-100 dark:border-gray-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-surface-900 dark:text-white flex items-center gap-2">
                <span>Suggested Remediation Plan</span>
                <span className="px-2 py-0.5 text-[10px] font-semibold rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  Deterministic
                </span>
              </h3>
              <p className="text-xs text-surface-500 dark:text-gray-400 mt-0.5">
                Configure transformation rules to fix detected defects. Original file is never overwritten.
              </p>
            </div>
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={handlePreview}
                disabled={isPreviewing}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-surface-100 hover:bg-surface-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-surface-800 dark:text-gray-200 transition-colors cursor-pointer disabled:opacity-50"
              >
                {isPreviewing ? "Calculating Dry-Run..." : "Preview Cleaning (Dry-Run)"}
              </button>
              <button
                type="button"
                onClick={() => setShowApplyModal(true)}
                disabled={isApplying}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-accent hover:bg-accent/90 text-white transition-colors shadow-xs cursor-pointer disabled:opacity-50"
              >
                {isApplying ? "Applying..." : "Apply & Create Clean Dataset"}
              </button>
            </div>
          </div>

          {/* Plan Options Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-4 rounded-xl bg-surface-50/70 dark:bg-gray-800/30 border border-surface-200/50 dark:border-gray-800/50 space-y-3">
              <span className="text-xs font-bold text-surface-800 dark:text-gray-200">1. Hygiene & Duplication</span>
              <label className="flex items-center gap-2.5 text-xs text-surface-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={stripWhitespace}
                  onChange={(e) => setStripWhitespace(e.target.checked)}
                  className="rounded border-surface-300 text-accent focus:ring-accent"
                />
                <span>Trim cell whitespaces</span>
              </label>
              <label className="flex items-center gap-2.5 text-xs text-surface-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={dropDuplicates}
                  onChange={(e) => setDropDuplicates(e.target.checked)}
                  className="rounded border-surface-300 text-accent focus:ring-accent"
                />
                <span>Remove duplicate records</span>
              </label>
            </div>

            <div className="p-4 rounded-xl bg-surface-50/70 dark:bg-gray-800/30 border border-surface-200/50 dark:border-gray-800/50 space-y-3">
              <span className="text-xs font-bold text-surface-800 dark:text-gray-200">2. Missing Values Imputation</span>
              <div className="space-y-1.5">
                <label className="text-[11px] text-surface-500 dark:text-gray-400">Numeric Strategy</label>
                <select
                  value={imputeNumeric}
                  onChange={(e) => setImputeNumeric(e.target.value)}
                  className="w-full text-xs p-1.5 rounded-lg bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200"
                >
                  <option value="median">Fill with Median</option>
                  <option value="mean">Fill with Mean</option>
                  <option value="constant">Fill with Zero (0)</option>
                  <option value="drop">Drop Rows with Missing</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] text-surface-500 dark:text-gray-400">Categorical Strategy</label>
                <select
                  value={imputeCategorical}
                  onChange={(e) => setImputeCategorical(e.target.value)}
                  className="w-full text-xs p-1.5 rounded-lg bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200"
                >
                  <option value="mode">Fill with Mode (Most Frequent)</option>
                  <option value="constant">Fill with 'Unknown'</option>
                  <option value="drop">Drop Rows with Missing</option>
                </select>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface-50/70 dark:bg-gray-800/30 border border-surface-200/50 dark:border-gray-800/50 space-y-3">
              <span className="text-xs font-bold text-surface-800 dark:text-gray-200">3. Formatting & Types</span>
              <label className="flex items-center gap-2.5 text-xs text-surface-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={normalizeDates}
                  onChange={(e) => setNormalizeDates(e.target.checked)}
                  className="rounded border-surface-300 text-accent focus:ring-accent"
                />
                <span>Normalize dates to ISO-8601</span>
              </label>
              <div className="pt-1 flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Column to standardize case"
                  value={casingCol}
                  onChange={(e) => setCasingCol(e.target.value)}
                  className="flex-1 text-xs px-2.5 py-1.5 rounded-lg bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200"
                />
                <select
                  value={casingType}
                  onChange={(e) => setCasingType(e.target.value)}
                  className="text-xs p-1.5 rounded-lg bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200"
                >
                  <option value="title">Title</option>
                  <option value="lower">Lower</option>
                  <option value="upper">Upper</option>
                </select>
              </div>
            </div>
          </div>

          {/* Dry Run Preview Diff Card */}
          {previewResult && (
            <div className="p-5 rounded-xl bg-surface-50 dark:bg-gray-800/60 border border-blue-500/20 space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Dry-Run Preview Result (No Changes Saved)
                </span>
                <span className="text-xs font-semibold text-surface-700 dark:text-gray-300">
                  Expected Score: {previewResult.score_comparison.before_score}% →{" "}
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                    {previewResult.score_comparison.after_score}% (+{previewResult.score_comparison.score_delta} pts)
                  </span>
                </span>
              </div>

              <p className="text-xs font-medium text-surface-700 dark:text-gray-200 bg-white dark:bg-gray-900 p-3 rounded-lg border border-surface-200 dark:border-gray-700">
                {previewResult.audit.explanation}
              </p>

              {/* Step list */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-surface-200 dark:border-gray-700 text-surface-400 dark:text-gray-500 text-[10px] uppercase">
                      <th className="py-2 px-3">Step</th>
                      <th className="py-2 px-3">Operation</th>
                      <th className="py-2 px-3">Column</th>
                      <th className="py-2 px-3">Rows Affected</th>
                      <th className="py-2 px-3">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewResult.steps.map((st) => (
                      <tr key={st.step_number} className="border-b border-surface-100 dark:border-gray-800 text-surface-700 dark:text-gray-300">
                        <td className="py-2 px-3 font-mono text-[11px]">{st.step_number}</td>
                        <td className="py-2 px-3 font-semibold">{st.operation}</td>
                        <td className="py-2 px-3 font-mono">{st.target_column || "—"}</td>
                        <td className="py-2 px-3 font-semibold">{st.rows_affected}</td>
                        <td className="py-2 px-3 text-surface-500 dark:text-gray-400">{st.details}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Row 4: Quality Issue Inventory */}
        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-surface-200/80 dark:border-gray-800/80 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-surface-100 dark:border-gray-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-surface-900 dark:text-white">
                Detected Quality Defects ({filteredIssues.length})
              </h3>
              <p className="text-xs text-surface-500 dark:text-gray-400">
                Detailed inventory of missing data, duplicates, outliers, and formatting issues.
              </p>
            </div>
            {/* Filter buttons */}
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="text"
                placeholder="Search issues..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="text-xs px-3 py-1.5 rounded-lg bg-surface-100 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200 w-36 sm:w-48"
              />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-surface-100 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
              </select>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-surface-100 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200"
              >
                <option value="ALL">All Categories</option>
                <option value="MISSING">Missing</option>
                <option value="DUPLICATE">Duplicates</option>
                <option value="INVALID_FORMAT">Format</option>
                <option value="INVALID_TYPE">Type</option>
                <option value="INVALID_RANGE">Range</option>
                <option value="INCONSISTENT_CATEGORY">Categorical</option>
                <option value="OUTLIER">Outliers</option>
              </select>
            </div>
          </div>

          {filteredIssues.length === 0 ? (
            <div className="py-12 text-center text-xs text-surface-400 dark:text-gray-500">
              No quality defects match the selected filter criteria.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {filteredIssues.map((issue) => (
                <div
                  key={issue.id}
                  className="p-4 rounded-xl bg-surface-50/60 dark:bg-gray-800/40 border border-surface-200/60 dark:border-gray-800/60 space-y-2 hover:border-surface-300 dark:hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded-md border ${getSeverityBadge(issue.severity)}`}>
                        {issue.severity}
                      </span>
                      <span className="text-[11px] font-bold uppercase tracking-wide text-surface-500 dark:text-gray-400">
                        {issue.category}
                      </span>
                    </div>
                    {issue.column && (
                      <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-white dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-800 dark:text-gray-200">
                        {issue.column}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-surface-800 dark:text-gray-200 font-medium">
                    {issue.description}
                  </p>

                  {issue.sample_values && issue.sample_values.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[10px] text-surface-400 dark:text-gray-500">Samples:</span>
                      {issue.sample_values.slice(0, 5).map((val, idx) => (
                        <span
                          key={idx}
                          className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-surface-200/60 dark:bg-gray-700/60 text-surface-700 dark:text-gray-300 truncate max-w-[140px]"
                        >
                          {String(val)}
                        </span>
                      ))}
                    </div>
                  )}

                  {issue.suggested_action && (
                    <p className="text-[11px] text-blue-600 dark:text-blue-400 pt-1 flex items-center gap-1">
                      <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>{issue.suggested_action}</span>
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Row 5: Lineage & Version History */}
        {lineage && lineage.versions && lineage.versions.length > 0 && (
          <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-surface-200/80 dark:border-gray-800/80 shadow-xs space-y-4">
            <h3 className="text-base font-bold text-surface-900 dark:text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Lineage & Derivation History
            </h3>
            <div className="divide-y divide-surface-100 dark:divide-gray-800">
              {lineage.versions.map((ver, idx) => (
                <div key={idx} className="py-3 flex items-center justify-between gap-4 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 font-bold flex items-center justify-center text-[11px]">
                      v{ver.version}
                    </span>
                    <div>
                      <p className="font-semibold text-surface-900 dark:text-white font-mono">{ver.dataset_name}</p>
                      <p className="text-[11px] text-surface-400 dark:text-gray-500">Created: {new Date(ver.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                      Score: {ver.score_after}%
                    </span>
                    <button
                      type="button"
                      disabled={isSwitching || ver.dataset_name === datasetName}
                      onClick={() => handleSwitchDataset(ver.dataset_name)}
                      className="px-3 py-1 rounded-lg text-xs font-medium border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-40 cursor-pointer"
                    >
                      {ver.dataset_name === datasetName ? "Active" : "Use in Session"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal for Applying Cleaning */}
      {showApplyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-md p-6 bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-surface-200 dark:border-gray-800 space-y-4">
            <h3 className="text-base font-bold text-surface-900 dark:text-white">
              Apply Data Cleaning?
            </h3>
            <p className="text-xs text-surface-600 dark:text-gray-300 leading-relaxed">
              This will execute the configured cleaning pipeline and save a new derived version{" "}
              <strong className="font-mono text-accent">
                {datasetName.replace(/\.csv$/i, "")}__clean_v1.csv
              </strong>.
            </p>
            <div className="p-3 bg-surface-50 dark:bg-gray-800/50 rounded-xl border border-surface-200/60 dark:border-gray-700/60 text-[11px] text-surface-500 dark:text-gray-400">
              🛡️ <strong>Safety Guarantee:</strong> Your original dataset remains 100% untouched and byte-identical.
            </div>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowApplyModal(false)}
                className="px-4 py-2 text-xs font-semibold rounded-xl text-surface-600 dark:text-gray-400 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleApplyClean}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-accent text-white hover:bg-accent/90 transition-colors shadow-xs cursor-pointer"
              >
                Confirm & Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
