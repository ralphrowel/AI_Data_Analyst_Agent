import { useState } from "react";
import { supabase, isSupabaseConfigured, DEMO_ACCOUNTS, demoAuthEnabled } from "../supabase";
import { setAuthToken } from "../api";

export default function AuthModal({ isOpen, onClose, currentUser, onUserChanged }) {
  const [activeTab, setActiveTab] = useState(
    demoAuthEnabled && !isSupabaseConfigured ? "demo" : "supabase"
  ); // "demo" | "supabase"
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSelectDemo = (account) => {
    setAuthToken(account.token);
    onUserChanged(account);
    onClose();
  };

  const handleGoogleSignIn = async () => {
    if (!isSupabaseConfigured || !supabase) {
      setError("Supabase URL and Anon Key are not yet configured in .env. Configure authentication to sign in.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { error: err } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: window.location.origin,
        },
      });
      if (err) throw err;
    } catch (err) {
      setError(err.message || "Failed to sign in with Google");
      setLoading(false);
    }
  };

  const handleMagicLink = async (e) => {
    e.preventDefault();
    if (!email || !email.trim()) return;

    if (!isSupabaseConfigured || !supabase) {
      setError("Supabase URL and Anon Key are not yet configured in .env. Configure authentication to sign in.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const { error: err } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: {
          emailRedirectTo: window.location.origin,
        },
      });
      if (err) throw err;
      setMessage("Check your inbox! We've sent an instant login link.");
    } catch (err) {
      setError(err.message || "Failed to send magic link");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-100 dark:border-gray-800 bg-surface-50/50 dark:bg-gray-800/50">
          <div>
            <h3 className="text-base font-semibold text-surface-900 dark:text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
              Account & Workspace Identity
            </h3>
            <p className="text-xs text-surface-500 dark:text-gray-400 mt-0.5">
              Workspaces, uploaded datasets, and token quotas are isolated per user
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-surface-100 dark:border-gray-800 px-6 pt-3 bg-surface-50/30 dark:bg-gray-800/30">
          {demoAuthEnabled && <button
            type="button"
            onClick={() => setActiveTab("demo")}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === "demo"
                ? "border-accent text-accent font-semibold"
                : "border-transparent text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200"
            }`}
          >
            Quick Switch Profiles
          </button>}
          <button
            type="button"
            onClick={() => setActiveTab("supabase")}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === "supabase"
                ? "border-accent text-accent font-semibold"
                : "border-transparent text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-200"
            }`}
          >
            Supabase Auth (Google / OTP)
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-600 dark:text-red-400 text-xs leading-relaxed flex items-start gap-2">
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-emerald-600 dark:text-emerald-400 text-xs leading-relaxed flex items-start gap-2">
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>{message}</span>
            </div>
          )}

          {activeTab === "demo" ? (
            <div className="space-y-3">
              <p className="text-xs text-surface-600 dark:text-gray-300 mb-3">
                Switch instantly between test users to verify workspace isolation, private dataset access, and separate token quotas:
              </p>
              {DEMO_ACCOUNTS.map((acc) => {
                const isActive = currentUser?.email === acc.email || currentUser?.id === acc.id;
                return (
                  <button
                    key={acc.id}
                    type="button"
                    onClick={() => handleSelectDemo(acc)}
                    className={`w-full flex items-center justify-between p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                      isActive
                        ? "border-accent/80 bg-accent/5 dark:bg-accent/10 ring-2 ring-accent/20"
                        : "border-surface-200 dark:border-gray-800 hover:border-surface-300 dark:hover:border-gray-700 bg-white dark:bg-gray-800/50 hover:bg-surface-50 dark:hover:bg-gray-800"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full ${acc.color} text-white font-bold flex items-center justify-center text-sm shadow-xs`}>
                        {acc.avatar}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-surface-900 dark:text-white">
                            {acc.name}
                          </span>
                          {isActive && (
                            <span className="px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-accent/20 text-accent">
                              Active
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-surface-500 dark:text-gray-400">
                          {acc.email} • {acc.role}
                        </span>
                      </div>
                    </div>
                    <svg className={`w-4 h-4 ${isActive ? "text-accent" : "text-surface-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              {!isSupabaseConfigured && (
                <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-700 dark:text-amber-300 text-xs">
                  <p className="font-semibold mb-1">Live Supabase Keys Missing</p>
                  <p>Add <code className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900 rounded font-mono">VITE_SUPABASE_URL</code> and <code className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900 rounded font-mono">VITE_SUPABASE_ANON_KEY</code> to your <code className="font-mono">.env</code> file for production Google 1-Click and Magic Link authentication.</p>
                </div>
              )}

              {/* Google 1-Click Button */}
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl border border-surface-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-surface-50 dark:hover:bg-gray-700 text-surface-800 dark:text-gray-100 text-sm font-medium shadow-xs transition-colors cursor-pointer"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.665-5.17 3.665-9.12z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.28 21.43 7.33 24 12 24z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.13z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.28 2.57 1.25 6.58l4.03 3.13c.95-2.83 3.6-4.96 6.72-4.96z"
                  />
                </svg>
                Continue with Google
              </button>

              <div className="flex items-center my-3">
                <div className="flex-1 border-t border-surface-200 dark:border-gray-800" />
                <span className="px-3 text-xs text-surface-400 dark:text-gray-500 uppercase tracking-wider font-mono">
                  or email OTP
                </span>
                <div className="flex-1 border-t border-surface-200 dark:border-gray-800" />
              </div>

              <form onSubmit={handleMagicLink} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-surface-700 dark:text-gray-300 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    required
                    className="w-full px-3 py-2 text-sm rounded-xl bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-900 dark:text-white placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-xl bg-accent hover:bg-accent/90 text-white text-sm font-medium shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Sending..." : "Send Magic Link"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
