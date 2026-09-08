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
} from "../api";
import Sidebar from "./Sidebar";
import ChatPanel from "./ChatPanel";
import ChartPanel from "./ChartPanel";
import Header from "./Header";
import SpreadsheetPanel from "./SpreadsheetPanel";
import DashboardPanel from "./DashboardPanel";
import NewChatModal from "./NewChatModal";
import HomePage from "./HomePage";



let messageId = 0;

const DEFAULT_TOKEN_USAGE = {
  prompt_tokens: 0,
  response_tokens: 0,
  total_tokens: 0,
  gemini_tokens: 0,
  groq_tokens: 0,
};

export default function App() {
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
    () => localStorage.getItem("darkMode") === "true"
  );
  const [selectedModel, setSelectedModel] = useState(
    () => localStorage.getItem("selectedModel") || "groq"
  );
  const [activeModel, setActiveModel] = useState(
    () => localStorage.getItem("selectedModel") || "groq"
  );
  const [chartTheme, setChartTheme] = useState(
    () => localStorage.getItem("darkMode") === "true" ? "dark" : "light"
  );

  const activeSession = sessions.find((s) => s.session_id === activeSessionId) || null;
  const activeDatasetName = activeSession?.dataset_name || null;

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

  const loadDatasets = useCallback(() => {
    fetchDatasets()
      .then((data) => setAvailableDatasets(data))
      .catch(() => {});
  }, []);

  // Initial load: fetch datasets and sessions (always default to Home panel)
  useEffect(() => {
    loadDatasets();

    fetchSessions()
      .then((sessionList) => {
        setSessions(sessionList || []);
        setActiveSessionId(null);
        localStorage.removeItem("activeSessionId");
      })
      .catch(() => {});
  }, [loadDatasets]);

  // When activeSessionId changes, load its details, history, and suggestions
  useEffect(() => {
    if (!activeSessionId) return;

    fetchSessionDetails(activeSessionId)
      .then((detail) => {
        if (detail.history && detail.history.length > 0) {
          const restoredMessages = detail.history.map((turn) => ({
            id: ++messageId,
            role: turn.role,
            text: turn.content,
            operation: turn.metadata?.operation,
            chart_base64: turn.metadata?.chart_base64,
            chart_svg: turn.metadata?.chart_svg,
            chart_spec: turn.metadata?.chart_spec,
          }));
          setMessages(restoredMessages);
          const restoredCharts = restoredMessages
            .filter((m) => m.chart_base64 || m.chart_svg)
            .map((m) => ({ chart_base64: m.chart_base64, chart_svg: m.chart_svg }));
          setCharts(restoredCharts);
          setCurrentChartIndex(restoredCharts.length > 0 ? restoredCharts.length - 1 : 0);
        } else {
          setMessages([]);
          setCharts([]);
          setCurrentChartIndex(0);
        }

        if (detail.token_usage) {
          setTokenUsage({
            prompt_tokens: detail.token_usage.prompt_tokens || 0,
            response_tokens: detail.token_usage.response_tokens || 0,
            total_tokens: detail.token_usage.total_tokens || 0,
            gemini_tokens: detail.token_usage.gemini_tokens || 0,
            groq_tokens: detail.token_usage.groq_tokens || 0,
          });
        }
      })
      .catch(() => { });

    fetchSuggestions(activeSessionId)
      .then((suggs) => setSuggestions(suggs))
      .catch(() => { });
  }, [activeSessionId]);

  const handleSelectSession = useCallback((sessionId) => {
    setActiveSessionId(sessionId);
    setActiveTab("chat");
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

  const handleConfirmNewChat = useCallback(
    async ({ file, datasetName, title }) => {
      try {
        let targetDataset = datasetName;
        if (file) {
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
    []
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
            const next = [...prev, { chart_base64: data.chart_base64, chart_svg: data.chart_svg }];
            setCurrentChartIndex(next.length - 1);
            return next;
          });
        }

        if (data.usage) {
          setTokenUsage((prev) => {
            const callTokens = data.usage.total_tokens || 0;
            return {
              prompt_tokens: prev.prompt_tokens + (data.usage.prompt_tokens || 0),
              response_tokens: prev.response_tokens + (data.usage.response_tokens || 0),
              total_tokens: prev.total_tokens + callTokens,
              gemini_tokens: (prev.gemini_tokens || 0) + (modelUsed === "gemini" ? callTokens : 0),
              groq_tokens: (prev.groq_tokens || 0) + (modelUsed === "groq" ? callTokens : 0),
            };
          });
        }

        // Refresh sessions list to display updated message count and title
        fetchSessions().then((list) => setSessions(list)).catch(() => { });
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: ++messageId,
            role: "assistant",
            text: "Sorry, something went wrong. Please try again.",
            operation: "error",
          },
        ]);
      }
      setIsStreaming(false);
    },
    [chartType, isStreaming, charts.length, activeModel, chartTheme, selectedModel, activeSessionId]
  );

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-surface-800 dark:text-gray-100">
      <div className="relative z-[3] h-full">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed((prev) => !prev)}
          tokenUsage={tokenUsage}
          activeModel={activeModel}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onNewChat={() => setShowNewChatModal(true)}
          onDeleteSession={handleDeleteSession}
        />
      </div>
      <div className="flex flex-col flex-1 min-w-0">
        {activeSessionId ? (
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
                  onNewChat={() => setShowNewChatModal(true)}
                  onPinToDashboard={handlePinToDashboard}
                />
                {charts.length > 0 && (
                  <ChartPanel
                    charts={charts}
                    currentIndex={currentChartIndex}
                    onIndexChange={setCurrentChartIndex}
                  />
                )}
              </div>
            ) : activeTab === "spreadsheet" ? (
              <SpreadsheetPanel
                datasetName={activeDatasetName}
                onDatasetUpdated={() => {
                  loadDatasets();
                }}
              />
            ) : (
              <DashboardPanel
                sessionId={activeSessionId}
                datasetName={activeDatasetName}
                chartTheme={chartTheme}
                selectedModel={selectedModel}
              />
            )}

          </>
        ) : (
          <HomePage
            sessions={sessions}
            availableDatasets={availableDatasets}
            onSelectSession={handleSelectSession}
            onNewChat={() => setShowNewChatModal(true)}
            onDeleteSession={handleDeleteSession}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            selectedModel={selectedModel}
            onRefreshData={loadDatasets}
          />
        )}
      </div>

      <NewChatModal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        onCreate={handleConfirmNewChat}
      />
    </div>
  );
}

