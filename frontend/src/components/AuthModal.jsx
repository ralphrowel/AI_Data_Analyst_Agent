import { useState } from "react";
import { setAuthToken, loginWithPassword } from "../api";

export default function AuthModal({
  isOpen,
  onClose,
  currentUser,
  onUserChanged,
  bannerMessage = "",
  canClose = true,
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
      isAdmin: false,
    };
    setAuthToken("demo_default");
    onUserChanged(guestAccount);
    onClose();
  };

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) return;

    setLoading(true);
    setError("");
    setMessage("");

    try {
      // Local instant check for primary admin account
      if (username.trim() === "ralph123" && password === "ralph123") {
        const adminAccount = {
          id: "user_admin_ralph",
          email: "ralph@visiq.ai",
          name: "Ralph (Admin)",
          role: "Main Admin",
          avatar: "R",
          color: "bg-gradient-to-tr from-amber-500 to-red-600",
          token: "admin_ralph_token",
          isAdmin: true,
        };
        setAuthToken(adminAccount.token);
        onUserChanged(adminAccount);
        onClose();
        return;
      }

      // Backend fallback check for password authentication
      const result = await loginWithPassword(username.trim(), password);
      if (result?.user) {
        setAuthToken(result.token);
        onUserChanged({
          ...result.user,
          token: result.token,
          isAdmin: Boolean(result.user.is_admin || result.user.role === "admin"),
        });
        onClose();
      }
    } catch (err) {
      setError(err.message || "Invalid username or password. Please check your credentials.");
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
              Autonomous AI Data Analyst • Internal Company System
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
          {/* Custom Banner message (e.g. query limit reached) */}
          {bannerMessage && (
            <div className="mb-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs leading-relaxed flex items-start gap-2.5">
              <svg className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <div>
                <span className="font-semibold block mb-0.5">System Notice</span>
                <span>{bannerMessage}</span>
              </div>
            </div>
          )}

          {/* Primary Explore as Guest Card */}
          <div className="mb-5 p-4 rounded-2xl bg-gradient-to-br from-accent/15 via-accent/5 to-transparent border border-accent/30 shadow-xs">
            <div className="mb-1.5">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-accent/20 text-accent mb-1">
                Instant Access
              </span>
              <h4 className="text-sm font-bold text-surface-900 dark:text-white">
                Explore as Guest (10 Query Demo)
              </h4>
            </div>
            <p className="text-xs text-surface-600 dark:text-gray-300 leading-relaxed mb-3">
              Explore the preloaded <strong>Netflix Catalog dataset (8,800+ titles)</strong>, test automated queries, and generate charts immediately. Up to 10 queries allowed.
            </p>
            <button
              type="button"
              onClick={handleGuestExplore}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-accent hover:bg-accent/90 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all cursor-pointer"
            >
              <span>Explore as Guest</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          </div>

          <div className="relative flex py-2 items-center mb-4">
            <div className="flex-grow border-t border-surface-200 dark:border-gray-800" />
            <span className="flex-shrink mx-3 text-[11px] font-semibold text-surface-400 dark:text-gray-500 uppercase tracking-wider font-mono">
              or administrator login
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
            {/* Darkened & Unsupported Google Button */}
            <div
              className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl border border-surface-200 dark:border-gray-800 bg-surface-100/50 dark:bg-gray-800/40 text-surface-400 dark:text-gray-500 text-sm select-none opacity-50 cursor-not-allowed"
              title="Google Sign-in is temporarily disabled. Please use Username & Password below."
            >
              <div className="flex items-center gap-3">
                <svg className="w-4 h-4 grayscale opacity-60" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.665-5.17 3.665-9.12z" />
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.28 21.43 7.33 24 12 24z" />
                  <path fill="#FBBC05" d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.13z" />
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.28 2.57 1.25 6.58l4.03 3.13c.95-2.83 3.6-4.96 6.72-4.96z" />
                </svg>
                <span className="line-through decoration-surface-400">Continue with Google / Gmail</span>
              </div>
              <span className="text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-surface-200 dark:bg-gray-700/60 text-surface-500 dark:text-gray-400">
                Disabled
              </span>
            </div>

            {/* Username & Password Form */}
            <form onSubmit={handlePasswordLogin} className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-semibold text-surface-700 dark:text-gray-300 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. ralph123"
                  required
                  autoCapitalize="none"
                  className="w-full px-3 py-2 text-sm rounded-xl bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-900 dark:text-white placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-surface-700 dark:text-gray-300 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-3 py-2 text-sm rounded-xl bg-surface-50 dark:bg-gray-800 border border-surface-200 dark:border-gray-700 text-surface-900 dark:text-white placeholder-surface-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-colors"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700 hover:from-amber-600 hover:to-amber-800 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                </svg>
                <span>{loading ? "Authenticating..." : "Sign In"}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
