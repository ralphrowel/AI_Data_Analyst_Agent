import { useState } from "react";

export default function PrivacyPolicyModal({ isOpen, onClose, onAccept }) {
  const [activeSection, setActiveSection] = useState("all");

  if (!isOpen) return null;

  const sections = [
    {
      id: "ownership",
      title: "1. Data Ownership & Sovereignty",
      icon: (
        <svg className="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      ),
      content: (
        <>
          <p className="mb-2">
            All CSV datasets, raw spreadsheets, custom queries, and generated visualizations processed by Visiq AI remain the exclusive intellectual and proprietary property of you and your organization.
          </p>
          <p>
            Visiq AI asserts zero ownership, licensing, or commercial claims over the contents of your datasets. Your data is isolated strictly to your tenant workspace.
          </p>
        </>
      ),
    },
    {
      id: "deterministic",
      title: "2. Deterministic Execution & Zero Hallucinations",
      icon: (
        <svg className="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
        </svg>
      ),
      content: (
        <>
          <p className="mb-2">
            To prevent statistical and arithmetic hallucinations common in generative models, all mathematical calculations, filtering, aggregations, and correlations are performed deterministically in isolated Python Pandas execution environments.
          </p>
          <p>
            Large Language Models are utilized solely for intent translation, structured code generation, and qualitative executive commentary—never for raw mental arithmetic.
          </p>
        </>
      ),
    },
    {
      id: "ai_privacy",
      title: "3. AI Inference & Zero-Retention Enterprise APIs",
      icon: (
        <svg className="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
        </svg>
      ),
      content: (
        <>
          <p className="mb-2">
            Inference requests routed to third-party model providers (including Google Gemini and Groq LPUs) operate strictly under enterprise Zero Data Retention agreements over encrypted TLS 1.3 tunnels.
          </p>
          <p className="font-semibold text-accent">
            Under no circumstances is your uploaded data, query text, or schema information used to train, retrain, or fine-tune public foundation AI models.
          </p>
        </>
      ),
    },
    {
      id: "retention",
      title: "4. Data Erasure & Right to be Forgotten",
      icon: (
        <svg className="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
        </svg>
      ),
      content: (
        <>
          <p className="mb-2">
            You maintain full sovereignty to delete individual chats or purge workspaces at any time. When a session is deleted, associated tabular datasets, conversation logs, and generated Plotly chart artifacts are irreversibly purged from backend storage.
          </p>
        </>
      ),
    },
    {
      id: "cookies",
      title: "5. Storage, Cookies & Telemetry",
      icon: (
        <svg className="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918" />
        </svg>
      ),
      content: (
        <>
          <p className="mb-2">
            Visiq AI does not utilize commercial advertising cookies, cross-site trackers, or behavioral profiling scripts.
          </p>
          <p>
            Client-side browser storage (<code className="px-1.5 py-0.5 rounded text-[11px] bg-surface-200 dark:bg-gray-800 font-mono">localStorage</code>) is used strictly for technical operation: dark/light theme preferences and session authentication tokens.
          </p>
        </>
      ),
    },
    {
      id: "access",
      title: "6. Guest Sandbox & Role Governance",
      icon: (
        <svg className="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
      ),
      content: (
        <>
          <p>
            Guest explorer mode operates within an isolated sandbox with query limits (10 queries per guest session) and ephemeral token generation. Administrator accounts manage authorized tenant configurations and access control policies.
          </p>
        </>
      ),
    },
  ];

  const handleAgreeAndClose = () => {
    if (onAccept) {
      onAccept();
    }
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-100 dark:border-gray-800 bg-surface-50/70 dark:bg-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center text-accent shrink-0 border border-accent/25">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-bold text-surface-900 dark:text-white flex items-center gap-2">
                Privacy Policy & Data Protection Terms
              </h3>
              <p className="text-xs text-surface-500 dark:text-gray-400">
                Visiq AI • Autonomous Data Analysis • Internal Enterprise System
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
            title="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Security / Compliance Badges Banner */}
        <div className="px-6 py-2.5 bg-accent/5 border-b border-surface-100 dark:border-gray-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Zero AI Training on User Data
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              Deterministic Pandas
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/20">
              TLS 1.3 Encrypted
            </span>
          </div>
          <span className="text-[11px] text-surface-400 dark:text-gray-500 font-mono">
            v2.4 • Effective Oct 2026
          </span>
        </div>

        {/* Scrollable Policy Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1 text-xs text-surface-700 dark:text-gray-300 leading-relaxed">
          <div className="p-3.5 rounded-xl bg-surface-50 dark:bg-gray-800/60 border border-surface-200/80 dark:border-gray-700/60">
            <p className="font-semibold text-surface-900 dark:text-white mb-1">
              Commitment to Internal Enterprise Privacy
            </p>
            <p className="text-surface-600 dark:text-gray-300">
              Visiq AI is engineered for mission-critical enterprise financial and business intelligence. Before authenticating as an Administrator or exploring as a Guest, please review our core data governance protocols below.
            </p>
          </div>

          <div className="space-y-3">
            {sections.map((section) => (
              <div
                key={section.id}
                className="p-4 rounded-xl border border-surface-200/70 dark:border-gray-800 bg-surface-50/40 dark:bg-gray-800/30 hover:border-accent/40 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2 font-semibold text-surface-900 dark:text-white text-xs">
                  {section.icon}
                  <span>{section.title}</span>
                </div>
                <div className="pl-6 text-[12px] text-surface-600 dark:text-gray-300 space-y-1.5">
                  {section.content}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-surface-100 dark:border-gray-800 text-[11px] text-surface-500 dark:text-gray-400">
            For inquiries regarding enterprise compliance, self-hosted deployments, or custom data retention periods, contact your internal Visiq administrator.
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-surface-100 dark:border-gray-800 bg-surface-50/50 dark:bg-gray-800/50 flex items-center justify-between gap-3">
          <p className="text-[11px] text-surface-500 dark:text-gray-400 hidden sm:block">
            By proceeding, you acknowledge agreement with these terms.
          </p>
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-surface-200 dark:border-gray-700 text-surface-700 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-800 text-xs font-semibold transition-colors cursor-pointer"
            >
              Close
            </button>
            <button
              type="button"
              onClick={handleAgreeAndClose}
              className="px-5 py-2 rounded-xl bg-accent hover:bg-accent/90 text-white text-xs font-semibold shadow-md hover:shadow-lg transition-all cursor-pointer flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <span>I Understand & Agree</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
