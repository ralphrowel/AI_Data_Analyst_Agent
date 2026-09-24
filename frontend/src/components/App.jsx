import { useState, useEffect, useCallback } from "react";
import {
  fetchSuggestions,
  askQuestion,
  fetchDatasets,
  fetchSessions,
  createSession,
  fetchSessionDetails,
  deleteSession,
  uploadDataset,
  pinWidgetToSession,
  fetchUserQuota,
  setAuthToken,
  registerClientDataset,
} from "../api";
import { supabase, isSupabaseConfigured } from "../supabase";
import Sidebar from "./Sidebar";
import ChatPanel from "./ChatPanel";
import ChartPanel from "./ChartPanel";
import Header from "./Header";
import SpreadsheetPanel from "./SpreadsheetPanel";
import DashboardPanel from "./DashboardPanel";
import NewChatModal from "./NewChatModal";
import HomePage from "./HomePage";
import AuthModal from "./AuthModal";
import ProductTour from "./ProductTour";

let messageId = 0;

// Safe localStorage wrapper to prevent crashes in privacy browsers (Brave Shields, strict cookies)
const safeStorage = {
  getItem: (key, fallback = null) => {
    try {
      const val = localStorage.getItem(key);
      return val !== null ? val : fallback;
    } catch {
      return fallback;
    }
  },
  setItem: (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch {}
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key);
    } catch {}
  },
};

const DEFAULT_TOKEN_USAGE = {
  prompt_tokens: 0,
  response_tokens: 0,
  total_tokens: 0,
  gemini_tokens: 0,
  groq_tokens: 0,
};

const MAX_QUERIES_LIMIT = 10;
const MAX_GUEST_QUERIES = 10;

const DEFAULT_GUEST_SESSION = {
  session_id: "demo_guest_netflix",
  dataset_name: "netflix_titles.csv",
  title: "Netflix Catalog Analysis",
  created_at: new Date().toISOString(),
  message_count: 0,
  widget_count: 0,
  token_usage: { ...DEFAULT_TOKEN_USAGE },
  last_message: "",
};

const DEFAULT_NETFLIX_DATASET = {
  name: "netflix_titles.csv",
  filename: "netflix_titles.csv",
  rows: 8807,
  columns: 14,
  size_bytes: 3443996,
  is_private: false,
};

const DEFAULT_TECH_SALARIES_DATASET = {
  name: "tech_salaries.csv",
  filename: "tech_salaries.csv",
  rows: 15,
  columns: 7,
  size_bytes: 758,
  is_private: false,
};

const DEFAULT_GLOBAL_DATASETS = [
  DEFAULT_NETFLIX_DATASET,
  DEFAULT_TECH_SALARIES_DATASET,
];

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = safeStorage.getItem("visiq_current_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [userQuota, setUserQuota] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(() => {
    return !safeStorage.getItem("visiq_current_user");
  });
  const [authModalBanner, setAuthModalBanner] = useState("");
  const [showProductTour, setShowProductTour] = useState(false);
  const [guestQueriesCount, setGuestQueriesCount] = useState(() => {
    return Number(safeStorage.getItem("visiq_guest_queries", "0"));
  });

  const [sessions, setSessions] = useState(() => {
    try {
      const savedUser = JSON.parse(safeStorage.getItem("visiq_current_user") || "null");
      if (savedUser?.isGuest) {
        return [DEFAULT_GUEST_SESSION];
      }
    } catch {}
    return [];
  });
  const [activeSessionId, setActiveSessionId] = useState(() => {
    try {
      const savedUser = JSON.parse(safeStorage.getItem("visiq_current_user") || "null");
      if (savedUser?.isGuest) {
        return safeStorage.getItem("activeSessionId", "demo_guest_netflix");
      }
    } catch {}
    return safeStorage.getItem("activeSessionId", null);
  });
  const [activeTab, setActiveTab] = useState("chat");
  const [availableDatasets, setAvailableDatasets] = useState(() => {
    return [...DEFAULT_GLOBAL_DATASETS];
  });
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [messages, setMessages] = useState([]);

  const [charts, setCharts] = useState([]);
  const [currentChartIndex, setCurrentChartIndex] = useState(0);
  const [suggestions, setSuggestions] = useState([]);
  const [tokenUsage, setTokenUsage] = useState({ ...DEFAULT_TOKEN_USAGE });
  const [chartType, setChartType] = useState(null);
  const [chartEnabled, setChartEnabled] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    return safeStorage.getItem("darkMode") !== "false";
  });
  const [selectedModel, setSelectedModel] = useState(() => {
    return safeStorage.getItem("selectedModel", "groq");
  });
  const [activeModel, setActiveModel] = useState(() => {
    return safeStorage.getItem("selectedModel", "groq");
  });
  const [chartTheme, setChartTheme] = useState(() => {
    return safeStorage.getItem("darkMode") === "false" ? "light" : "dark";
  });

  const activeSession = sessions.find((s) => s.session_id === activeSessionId) || null;
  const activeDatasetName = activeSession?.dataset_name || (currentUser?.isGuest ? "netflix_titles.csv" : null);
  const guestQueriesRemaining = Math.max(0, MAX_GUEST_QUERIES - guestQueriesCount);

  // Dark mode effect
  useEffect(() => {
    localStorage.setItem("darkMode", darkMode);
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    setChartTheme(darkMode ? "dark" : "light");
  }, [darkMode]);

  const loadQuota = useCallback(() => {
    fetchUserQuota()
      .then((q) => {
        if (q) setUserQuota(q);
      })
      .catch(() => {});
  }, []);

  const loadDatasets = useCallback(() => {
    fetchDatasets()
      .then((data) => {
        let list = data || [];
        for (const def of DEFAULT_GLOBAL_DATASETS) {
          if (!list.some((d) => d.name.toLowerCase() === def.name.toLowerCase())) {
            list.unshift(def);
          }
        }
        setAvailableDatasets(list);
      })
      .catch(() => {
        setAvailableDatasets([...DEFAULT_GLOBAL_DATASETS]);
      });
  }, []);

  // When currentUser changes: synchronize auth token, reload datasets, sessions & quota
  useEffect(() => {
    if (!currentUser) {
      setAuthToken(null);
      setSessions([]);
      setMessages([]);
      setCharts([]);
      setAvailableDatasets([]);
      setUserQuota(null);
      setActiveSessionId(null);
      setShowAuthModal(true);
      return;
    }
    setShowAuthModal(false);
    setAuthModalBanner("");
    if (currentUser?.token) {
      setAuthToken(currentUser.token);
    }
    localStorage.setItem("visiq_current_user", JSON.stringify(currentUser));

    // If guest user, immediately activate Netflix session and chat view so the user never sees a blank screen
    if (currentUser?.isGuest) {
      setSessions((prev) =>
        prev.some((s) => s.dataset_name === "netflix_titles.csv")
          ? prev
          : [DEFAULT_GUEST_SESSION, ...prev]
      );
      setActiveSessionId((prev) => prev || "demo_guest_netflix");
      setActiveTab("chat");
      setAvailableDatasets((prev) =>
        prev.some((d) => d.name === "netflix_titles.csv")
          ? prev
          : [DEFAULT_NETFLIX_DATASET, ...prev]
      );
    }

    loadDatasets();

    fetchSessions()
      .then(async (sessionList) => {
        let list = sessionList || [];
        // If guest user, ensure Netflix session exists and is active immediately
        if (currentUser?.isGuest) {
          let netflixSession = list.find((s) => s.dataset_name === "netflix_titles.csv");
          if (!netflixSession) {
            try {
              netflixSession = await createSession("netflix_titles.csv", "Netflix Catalog Analysis");
              list = [netflixSession, ...list];
            } catch (err) {
              console.warn("Backend session creation deferred; using local demo session:", err);
            }
          }
          if (netflixSession) {
            setSessions(list);
            setActiveSessionId(netflixSession.session_id);
            localStorage.setItem("activeSessionId", netflixSession.session_id);
            setActiveTab("chat");
          } else {
            setSessions((prev) => (prev.length > 0 ? prev : [DEFAULT_GUEST_SESSION]));
            setActiveSessionId((prev) => prev || "demo_guest_netflix");
            setActiveTab("chat");
          }

          // Trigger guided tour for first-time visitors
          if (!localStorage.getItem("hasSeenTour")) {
            setTimeout(() => setShowProductTour(true), 700);
          }
          return;
        }

        setSessions(list);
        if (list.length > 0) {
          const savedId = localStorage.getItem("activeSessionId");
          const found = list.find((s) => s.session_id === savedId);
          setActiveSessionId(found ? found.session_id : list[0].session_id);
        } else {
          setActiveSessionId(null);
          localStorage.removeItem("activeSessionId");
        }
        setMessages([]);
        setCharts([]);
      })
      .catch((err) => {
        console.warn("Failed to fetch sessions:", err);
        if (currentUser?.isGuest) {
          setSessions((prev) => (prev.length > 0 ? prev : [DEFAULT_GUEST_SESSION]));
          setActiveSessionId((prev) => prev || "demo_guest_netflix");
          setActiveTab("chat");
          if (!localStorage.getItem("hasSeenTour")) {
            setTimeout(() => setShowProductTour(true), 600);
          }
        }
      });

    loadQuota();
  }, [currentUser, loadDatasets, loadQuota]);

  // Live Supabase Auth Subscription (safely guarded against Brave Shields and adblockers)
  useEffect(() => {
    if (isSupabaseConfigured && supabase) {
      try {
        supabase.auth
          .getSession()
          .then((res) => {
            const session = res?.data?.session;
            if (session?.user) {
              setAuthToken(session.access_token);
              const u = {
                id: session.user.id,
                token: session.access_token,
                email: session.user.email,
                name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0],
                avatar: (session.user.user_metadata?.full_name?.[0] || session.user.email?.[0] || "U").toUpperCase(),
                role: "Supabase User",
                isGuest: false,
              };
              setCurrentUser(u);
            }
          })
          .catch((err) => {
            console.warn("Supabase session check bypassed (e.g. Brave Shields blocked):", err);
          });

        const authChangeResult = supabase.auth.onAuthStateChange((event, session) => {
          if (session?.user) {
            setAuthToken(session.access_token);
            const u = {
              id: session.user.id,
              token: session.access_token,
              email: session.user.email,
              name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0],
              avatar: (session.user.user_metadata?.full_name?.[0] || session.user.email?.[0] || "U").toUpperCase(),
              role: "Supabase User",
              isGuest: false,
            };
            setCurrentUser(u);
          } else if (event === "SIGNED_OUT") {
            setCurrentUser(null);
          }
        });

        return () => {
          try {
            authChangeResult?.data?.subscription?.unsubscribe();
          } catch {}
        };
      } catch (err) {
        console.warn("Supabase auth subscription failed:", err);
      }
    }
  }, []);

  // Fetch dataset suggestions when active dataset changes
  useEffect(() => {
    if (activeDatasetName) {
      fetchSuggestions(activeDatasetName)
        .then((sug) => setSuggestions(sug))
        .catch(() => setSuggestions([]));
    } else {
      setSuggestions([]);
    }
  }, [activeDatasetName]);

  // Load session messages when activeSessionId changes
  useEffect(() => {
    if (activeSessionId) {
      fetchSessionDetails(activeSessionId)
        .then((details) => {
          if (details) {
            const rawMessages = details.messages || details.history || [];
            const formatted = rawMessages.map((m) => ({
              id: ++messageId,
              role: m.role,
              text: m.text || m.content || "",
              operation: m.operation || m.metadata?.operation,
              unsupported_reason: m.unsupported_reason || m.metadata?.unsupported_reason,
              chart_base64: m.chart_base64 || m.metadata?.chart_base64,
              chart_svg: m.chart_svg || m.metadata?.chart_svg,
              chart_spec: m.chart_spec || m.metadata?.chart_spec,
            }));
            setMessages(formatted);

            const sessionCharts = formatted.filter((m) => m.chart_base64 || m.chart_svg);
            setCharts(sessionCharts);
            setCurrentChartIndex(Math.max(0, sessionCharts.length - 1));
          }
        })
        .catch(() => {});
    }
  }, [activeSessionId]);

  const handleSelectSession = useCallback((sessionId) => {
    setActiveSessionId(sessionId);
    if (sessionId) {
      localStorage.setItem("activeSessionId", sessionId);
    } else {
      localStorage.removeItem("activeSessionId");
      setMessages([]);
      setSuggestions([]);
    }
    setCharts([]);
    setCurrentChartIndex(0);
  }, []);

  const handleNewChatClick = useCallback(() => {
    if (currentUser?.isGuest) {
      setAuthModalBanner(
        "Sign in with Google or Email to create multiple custom workspaces and upload private CSV files."
      );
      setShowAuthModal(true);
      return;
    }
    setShowNewChatModal(true);
  }, [currentUser]);

  const handleConfirmNewChat = useCallback(
    async ({ file, title }) => {
      try {
        if (!file) {
          alert("Please select or drop a valid CSV file.");
          return;
        }

        const fileContent = await file.text();
        const lines = fileContent.trim().split(/\r?\n/).filter(Boolean);
        const headers = lines[0] ? lines[0].split(",").map((h) => h.trim().replace(/^["']|["']$/g, "")) : [];
        const rowCount = Math.max(0, lines.length - 1);

        // Register client-side dataset immediately for instant preview / Vercel offline support
        registerClientDataset(file.name, fileContent);

        let targetDataset = file.name;
        let isUploaded = false;

        try {
          const uploadRes = await uploadDataset(file.name, fileContent);
          targetDataset = uploadRes.name || uploadRes.filename || file.name;
          isUploaded = true;
          const updatedDatasets = await fetchDatasets().catch(() => null);
          if (updatedDatasets) {
            setAvailableDatasets(updatedDatasets);
          }
        } catch (uploadErr) {
          console.warn("Backend upload unreachable or failed; using client dataset mode:", uploadErr);
        }

        // Add to availableDatasets state
        const datasetMetadata = {
          name: targetDataset,
          filename: targetDataset,
          rows: rowCount,
          columns: headers.length,
          size_bytes: file.size,
          is_private: true,
        };
        setAvailableDatasets((prev) => [
          datasetMetadata,
          ...prev.filter((d) => d.name.toLowerCase() !== targetDataset.toLowerCase()),
        ]);

        const fallbackTitle = `${targetDataset
          .replace(/\.[^/.]+$/, "")
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase())} Workspace`;

        let newSession = null;
        if (isUploaded) {
          try {
            newSession = await createSession(targetDataset, title || fallbackTitle);
          } catch (sessErr) {
            console.warn("Backend session creation failed:", sessErr);
          }
        }

        if (!newSession) {
          newSession = {
            session_id: `session_${Date.now()}`,
            dataset_name: targetDataset,
            title: title || fallbackTitle,
            created_at: new Date().toISOString(),
            message_count: 0,
            widget_count: 0,
            token_usage: { ...DEFAULT_TOKEN_USAGE },
            last_message: "",
          };
        }

        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.session_id);
        setActiveTab("chat");
        localStorage.setItem("activeSessionId", newSession.session_id);
        setMessages([]);
        setCharts([]);
        setCurrentChartIndex(0);
        setTokenUsage({ ...DEFAULT_TOKEN_USAGE });
        setShowNewChatModal(false);
      } catch (err) {
        console.error("Failed to create workspace:", err);
        const detail = err?.message || "Please check your file and try again.";
        alert(`Failed to create workspace: ${detail}`);
      }
    },
    [currentUser]
  );

  const handleDeleteSession = useCallback(async (sessionId) => {
    try {
      await deleteSession(sessionId);
      setSessions((prev) => {
        const remaining = prev.filter((s) => s.session_id !== sessionId);
        if (activeSessionId === sessionId && remaining.length > 0) {
          setActiveSessionId(remaining[0].session_id);
          localStorage.setItem("activeSessionId", remaining[0].session_id);
        }
        return remaining;
      });
    } catch {
      // ignore
    }
  }, [activeSessionId]);

  const handleModelChange = (model) => {
    setSelectedModel(model);
    setActiveModel(model);
    localStorage.setItem("selectedModel", model);
  };

  const handleClearChat = useCallback(() => {
    setMessages([]);
    setCharts([]);
    setCurrentChartIndex(0);
    const cleared = { ...DEFAULT_TOKEN_USAGE };
    setTokenUsage(cleared);
    setActiveModel(selectedModel);
  }, [selectedModel]);

  const handlePinToDashboard = useCallback(
    async (msg) => {
      if (!activeSessionId) return;
      try {
        await pinWidgetToSession(activeSessionId, {
          title: msg.text ? msg.text.slice(0, 48) + "..." : "Pinned Chart",
          prompt: msg.text ? msg.text.slice(0, 100) : "Pinned from chat",
          chart_base64: msg.chart_base64,
          chart_svg: msg.chart_svg,
          chart_spec: msg.chart_spec,
          operation: msg.operation,
        });
      } catch (err) {
        console.error("Failed to pin widget:", err);
      }
    },
    [activeSessionId]
  );

  const handleSubmit = useCallback(
    async (question) => {
      if (!question.trim() || isStreaming) return;

      // Query limit enforcement (10 queries max for regular users, admin has no restriction)
      if (!currentUser?.isAdmin && !userQuota?.is_admin) {
        const currentQueriesUsed = userQuota?.queries_used ?? (currentUser?.isGuest ? guestQueriesCount : 0);
        const currentQueryLimit = userQuota?.query_limit ?? MAX_QUERIES_LIMIT;
        if (currentQueriesUsed >= currentQueryLimit) {
          const companyNotice = "You have reached the maximum limit of 10 queries. This AI data analyst is built for internal company use and is not intended for public access.";
          const userMsg = { id: ++messageId, role: "user", text: question };
          const assistantMsg = {
            id: ++messageId,
            role: "assistant",
            text: companyNotice,
            operation: "error",
          };
          setMessages((prev) => [...prev, userMsg, assistantMsg]);
          return;
        }
      }

      const userMsg = { id: ++messageId, role: "user", text: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);

      try {
        const data = await askQuestion(
          question,
          chartType,
          chartTheme,
          selectedModel,
          activeSessionId
        );

        const modelUsed = data.model_used || selectedModel;
        if (modelUsed !== selectedModel) {
          setMessages((prev) => [
            ...prev,
            {
              id: ++messageId,
              role: "system",
              systemType: "model_switch",
              text: `${selectedModel === "gemini" ? "Gemini quota reached" : "Groq rate limit reached"} — switched to ${modelUsed === "groq" ? "Groq" : "Gemini"} for this response.`,
            },
          ]);
        }
        setActiveModel(modelUsed);

        const assistantMsg = {
          id: ++messageId,
          role: "assistant",
          text: data.summary,
          operation: data.operation,
          unsupported_reason: data.unsupported_reason,
          chart_base64: data.chart_base64,
          chart_svg: data.chart_svg,
          chart_spec: data.chart_spec,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (data.chart_base64 || data.chart_svg) {
          setCharts((prev) => {
            const next = [...prev, assistantMsg];
            setCurrentChartIndex(next.length - 1);
            return next;
          });
        }

        if (data.token_usage) {
          setTokenUsage((prev) => ({
            prompt_tokens: prev.prompt_tokens + (data.token_usage.prompt_tokens || 0),
            response_tokens: prev.response_tokens + (data.token_usage.response_tokens || 0),
            total_tokens: prev.total_tokens + (data.token_usage.total_tokens || 0),
            gemini_tokens: prev.gemini_tokens + (data.token_usage.gemini_tokens || 0),
            groq_tokens: prev.groq_tokens + (data.token_usage.groq_tokens || 0),
          }));
        }

        loadQuota();

        // Track guest query count
        if (currentUser?.isGuest) {
          const nextCount = guestQueriesCount + 1;
          setGuestQueriesCount(nextCount);
          localStorage.setItem("visiq_guest_queries", nextCount);
          if (nextCount >= MAX_GUEST_QUERIES) {
            setTimeout(() => {
              setAuthModalBanner(
                "You have reached the limit of 10 queries. This platform is configured for internal company use and is not available for public access."
              );
            }, 1000);
          }
        }
      } catch (err) {
        const errorText = err.message || "An error occurred while analyzing the dataset.";
        if (err.status === 429 || errorText.toLowerCase().includes("budget") || errorText.toLowerCase().includes("company")) {
          setAuthModalBanner(
            "Query limit reached (10/10). This AI data analyst is built for internal company use and is not intended for public access."
          );
        }
        const errorMsg = {
          id: ++messageId,
          role: "assistant",
          text: errorText,
          operation: "error",
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsStreaming(false);
      }
    },
    [
      isStreaming,
      chartType,
      chartTheme,
      selectedModel,
      activeSessionId,
      loadQuota,
      currentUser,
      guestQueriesCount,
    ]
  );

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-surface-800 dark:text-gray-100">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        tokenUsage={tokenUsage}
        activeModel={activeModel}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChatClick}
        onDeleteSession={handleDeleteSession}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {activeSessionId === null ? (
          <HomePage
            sessions={sessions}
            availableDatasets={availableDatasets}
            onSelectSession={handleSelectSession}
            onNewChat={handleNewChatClick}
            onDeleteSession={handleDeleteSession}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            selectedModel={selectedModel}
            onRefreshData={loadDatasets}
            currentUser={currentUser}
            userQuota={userQuota}
            onOpenAuthModal={() => {
              setAuthModalBanner("");
              setShowAuthModal(true);
            }}
          />
        ) : (
          <>
            <div className="relative z-[2]">
              <Header
                activeTab={activeTab}
                onTabChange={setActiveTab}
                chartType={chartType}
                chartEnabled={chartEnabled}
                onChartTypeChange={setChartType}
                onChartEnabledChange={setChartEnabled}
                onClearChat={handleClearChat}
                darkMode={darkMode}
                setDarkMode={setDarkMode}
                activeModel={activeModel}
                selectedModel={selectedModel}
                onSelectedModelChange={handleModelChange}
                chartTheme={chartTheme}
                onChartThemeChange={setChartTheme}
                activeDatasetName={activeDatasetName}
                currentUser={currentUser}
                userQuota={userQuota}
                onOpenAuthModal={() => {
                  setAuthModalBanner("");
                  setShowAuthModal(true);
                }}
                onStartTour={() => setShowProductTour(true)}
                guestQueriesRemaining={guestQueriesRemaining}
              />
            </div>
            {activeTab === "chat" ? (
              <div className="flex flex-1 min-h-0 relative z-[1]">
                <ChatPanel
                  messages={messages}
                  suggestions={suggestions}
                  isStreaming={isStreaming}
                  chartType={chartType}
                  chartEnabled={chartEnabled}
                  onChartTypeChange={setChartType}
                  onChartEnabledChange={setChartEnabled}
                  onSubmit={handleSubmit}
                  activeDatasetName={activeDatasetName}
                  datasetInfo={availableDatasets.find((d) => d.name === activeDatasetName)}
                  onPinToDashboard={handlePinToDashboard}
                />
                <ChartPanel
                  charts={charts}
                  currentIndex={currentChartIndex}
                  onIndexChange={setCurrentChartIndex}
                  theme={chartTheme}
                  activeDatasetName={activeDatasetName}
                  isStreaming={isStreaming}
                />
              </div>
            ) : activeTab === "spreadsheet" ? (
              <SpreadsheetPanel
                datasetName={activeDatasetName || "netflix_titles.csv"}
                activeDatasetName={activeDatasetName || "netflix_titles.csv"}
                datasetInfo={availableDatasets.find((d) => d.name === activeDatasetName) || availableDatasets[0]}
                onDatasetUpdated={loadDatasets}
              />
            ) : (
              <DashboardPanel
                activeSessionId={activeSessionId}
                activeDatasetName={activeDatasetName}
                theme={chartTheme}
              />
            )}
          </>
        )}
      </div>

      <NewChatModal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        onCreate={handleConfirmNewChat}
      />

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        currentUser={currentUser}
        bannerMessage={authModalBanner}
        canClose={Boolean(currentUser)}
        onUserChanged={(user) => {
          setCurrentUser(user);
          if (user?.isGuest) {
            setSessions([DEFAULT_GUEST_SESSION]);
            setActiveSessionId(DEFAULT_GUEST_SESSION.session_id);
            localStorage.setItem("activeSessionId", DEFAULT_GUEST_SESSION.session_id);
            setActiveTab("chat");
            setAvailableDatasets((prev) =>
              prev.some((d) => d.name === "netflix_titles.csv")
                ? prev
                : [DEFAULT_NETFLIX_DATASET, ...prev]
            );
            setMessages([]);
            setCharts([]);
            if (!localStorage.getItem("hasSeenTour")) {
              setTimeout(() => setShowProductTour(true), 600);
            }
          }
        }}
      />

      <ProductTour
        isOpen={showProductTour}
        onClose={() => setShowProductTour(false)}
        onSelectTab={setActiveTab}
      />
    </div>
  );
}
