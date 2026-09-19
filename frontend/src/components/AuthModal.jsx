import { useState } from "react";
import { supabase, isSupabaseConfigured, DEMO_ACCOUNTS, demoAuthEnabled } from "../supabase";
import { setAuthToken } from "../api";

export default function AuthModal({
  isOpen,
  onClose,
  currentUser,
  onUserChanged,
  bannerMessage = "",
  canClose = true,
}) {
  const [activeTab, setActiveTab] = useState(
    demoAuthEnabled && !isSupabaseConfigured ? "demo" : "supabase"
  ); // "demo" | "supabase"
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleGuestExplore = () => {
    const guestAccount = {
      id: "user_default",
      email: "guest@visiq.ai",
      name: "Guest Explorer",
      role: "Guest Demo",
      avatar: "G",
      color: "bg-gradient-to-tr from-cyan-600 to-blue-600",
      token: "demo_default",
      isGuest: true,
    };
    setAuthToken("demo_default");
    onUserChanged(guestAccount);
    onClose();
  };

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
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
              Welcome to Visiq AI
            </h3>
            <p className="text-xs text-surface-500 dark:text-gray-400 mt-0.5">
              Autonomous AI Data Analyst with real-time Python analytics
            </p>
          </div>
          {canClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-gray-200 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        <div className="p-6">
          {/* Custom Banner message (e.g. quota limit reached) */}
          {bannerMessage && (
            <div className="mb-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs leading-relaxed flex items-start gap-2.5">
              <span className="text-base leading-none">⚠️</span>
              <div>
                <span className="font-semibold block mb-0.5">Demo Limit Notice</span>
                <span>{bannerMessage}</span>
              </div>
            </div>
          )}

          {/* Primary Explore as Guest Card */}
          <div className="mb-5 p-4 rounded-2xl bg-gradient-to-br from-accent/15 via-accent/5 to-transparent border border-accent/30 shadow-xs">
            <div className="flex items-start justify-between gap-3 mb-1.5">
              <div>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-accent/20 text-accent mb-1">
                  Instant Access
                </span>
                <h4 className="text-sm font-bold text-surface-900 dark:text-white">
                  Explore as Guest (Instant Demo)
                </h4>
              </div>
              <span className="text-2xl select-none">🚀</span>
            </div>
            <p className="text-xs text-surface-600 dark:text-gray-300 leading-relaxed mb-3">
              Explore the preloaded <strong>Netflix Catalog dataset (8,800+ titles)</strong>, test automated queries, and generate charts immediately. No account needed.
            </p>
            <button
              type="button"
              onClick={handleGuestExplore}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-accent hover:bg-accent/90 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all cursor-pointer"
            >
              <span>Explore as Guest (Instant Demo)</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          </div>

          <div className="relative flex py-2 items-center mb-4">
            <div className="flex-grow border-t border-surface-200 dark:border-gray-800" />
            <span className="flex-shrink mx-3 text-[11px] font-semibold text-surface-400 dark:text-gray-500 uppercase tracking-wider font-mono">
              or sign in for full access
            </span>
            <div className="flex-grow border-t border-surface-200 dark:border-gray-800" />
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-600 dark:text-red-400 text-xs leading-relaxed flex items-start gap-2">
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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

          <div className="space-y-4">
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
                or email magic link
              </span>
              <div className="flex-1 border-t border-surface-200 dark:border-gray-800" />
            </div>

            <form onSubmit={handleMagicLink} className="space-y-3">
              <div>
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
                className="w-full py-2.5 px-4 rounded-xl bg-surface-100 hover:bg-surface-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-surface-800 dark:text-gray-100 text-sm font-medium border border-surface-200 dark:border-gray-700 shadow-xs transition-colors cursor-pointer disabled:opacity-50"
              >
                {loading ? "Sending..." : "Send Magic Link"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
