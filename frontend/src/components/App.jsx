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

const DEFAULT_TOKEN_USAGE = {
  prompt_tokens: 0,
  response_tokens: 0,
  total_tokens: 0,
  gemini_tokens: 0,
  groq_tokens: 0,
};

const MAX_GUEST_QUERIES = 5;

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem("visiq_current_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [userQuota, setUserQuota] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(() => {
    return !localStorage.getItem("visiq_current_user");
  });
  const [authModalBanner, setAuthModalBanner] = useState("");
  const [showProductTour, setShowProductTour] = useState(false);
  const [guestQueriesCount, setGuestQueriesCount] = useState(() => {
    return Number(localStorage.getItem("visiq_guest_queries") || 0);
  });

  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");
  const [availableDatasets, setAvailableDatasets] = useState([]);
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
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem("darkMode") !== "false"
  );
  const [selectedModel, setSelectedModel] = useState(
    () => localStorage.getItem("selectedModel") || "groq"
  );
  const [activeModel, setActiveModel] = useState(
    () => localStorage.getItem("selectedModel") || "groq"
  );
  const [chartTheme, setChartTheme] = useState(
    () => localStorage.getItem("darkMode") === "false" ? "light" : "dark"
  );

  const activeSession = sessions.find((s) => s.session_id === activeSessionId) || null;
  const activeDatasetName = activeSession?.dataset_name || null;
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
      .then((data) => setAvailableDatasets(data))
      .catch(() => {});
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
              console.error("Failed to auto-create guest session:", err);
            }
          }
          if (netflixSession) {
            setSessions(list);
            setActiveSessionId(netflixSession.session_id);
            localStorage.setItem("activeSessionId", netflixSession.session_id);
            setActiveTab("chat");

            // Trigger guided tour for first-time visitors
            if (!localStorage.getItem("hasSeenTour")) {
              setTimeout(() => setShowProductTour(true), 700);
            }
            return;
          }
        }

        setSessions(list);
        setActiveSessionId(null);
        localStorage.removeItem("activeSessionId");
        setMessages([]);
        setCharts([]);
      })
      .catch(() => {});

    loadQuota();
  }, [currentUser, loadDatasets, loadQuota]);

  // Live Supabase Auth Subscription
  useEffect(() => {
    if (isSupabaseConfigured && supabase) {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session) {
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
      });

      const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        if (session) {
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

      return () => subscription?.unsubscribe();
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
          if (details && details.messages) {
            const formatted = details.messages.map((m) => ({
              id: ++messageId,
              role: m.role,
              text: m.text,
              operation: m.operation,
              unsupported_reason: m.unsupported_reason,
              chart_base64: m.chart_base64,
              chart_svg: m.chart_svg,
              chart_spec: m.chart_spec,
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
    async ({ file, datasetName, title }) => {
      try {
        let targetDataset = datasetName;
        if (file) {
          if (currentUser?.isGuest) {
            setAuthModalBanner("Guest accounts cannot upload private datasets. Please sign in with Google or Email.");
            setShowAuthModal(true);
            return;
          }
          const fileContent = await file.text();
          const uploadRes = await uploadDataset(file.name, fileContent);
          targetDataset = uploadRes.name || uploadRes.filename || file.name;
          const updatedDatasets = await fetchDatasets();
          setAvailableDatasets(updatedDatasets);
        }

        if (!targetDataset) {
          alert("Please select a valid CSV file.");
          return;
        }

        const fallbackTitle = `${targetDataset
          .replace(/\.[^/.]+$/, "")
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase())} Workspace`;

        const newSession = await createSession(targetDataset, title || fallbackTitle);
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
        alert("Failed to create workspace. Please check the file and try again.");
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

      // Guest query limit enforcement
      if (currentUser?.isGuest && guestQueriesCount >= MAX_GUEST_QUERIES) {
        setAuthModalBanner(
          "You've reached your 5 free demo queries! Sign in with Google or Email for 50,000 daily tokens, unlimited chats, and private dataset uploads."
        );
        setShowAuthModal(true);
        return;
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
                "You've completed your 5 free demo queries! Sign in with Google or Email to continue chatting and unlock 50,000 daily tokens."
              );
              setShowAuthModal(true);
            }, 1500);
          }
        }
      } catch (err) {
        if (err.status === 429 || (err.message && err.message.toLowerCase().includes("budget"))) {
          setAuthModalBanner(
            "You've reached your free guest demo limit. Sign in with Google or Email to unlock 50,000 daily tokens and custom uploads."
          );
          setShowAuthModal(true);
        }
        const errorMsg = {
          id: ++messageId,
          role: "assistant",
          text: err.message || "An error occurred while analyzing the dataset.",
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
                activeDatasetName={activeDatasetName}
                datasetInfo={availableDatasets.find((d) => d.name === activeDatasetName)}
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
        }}
      />

      <ProductTour
        isOpen={showProductTour}
        onClose={() => setShowProductTour(false)}
      />
    </div>
  );
}
