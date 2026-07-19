import { useState, useEffect, useCallback } from "react";
import { fetchSuggestions, askQuestion } from "../api";
import Sidebar from "./Sidebar";
import ChatPanel from "./ChatPanel";
import ChartPanel from "./ChartPanel";
import Header from "./Header";

let messageId = 0;

export default function App() {
  const [messages, setMessages] = useState([]);
  const [charts, setCharts] = useState([]);
  const [currentChartIndex, setCurrentChartIndex] = useState(0);
  const [suggestions, setSuggestions] = useState([]);
  const [tokenUsage, setTokenUsage] = useState({
    prompt_tokens: 0,
    response_tokens: 0,
    total_tokens: 0,
  });
  const [chartType, setChartType] = useState(null);
  const [chartEnabled, setChartEnabled] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem("darkMode") === "true"
  );
  const [activeModel, setActiveModel] = useState("gemini");
  const [chartTheme, setChartTheme] = useState(
    () => localStorage.getItem("darkMode") === "true" ? "dark" : "light"
  );

  useEffect(() => {
    localStorage.setItem("darkMode", darkMode);
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  const handleClearChat = useCallback(() => {
    setMessages([]);
    setCharts([]);
    setCurrentChartIndex(0);
    setTokenUsage({ prompt_tokens: 0, response_tokens: 0, total_tokens: 0 });
    setActiveModel("gemini");
  }, []);

  useEffect(() => {
    fetchSuggestions()
      .then((data) => setSuggestions(data))
      .catch(() => {});
  }, []);

  const handleSubmit = useCallback(
    async (question) => {
      if (!question.trim() || isStreaming) return;

      const userMsg = { id: ++messageId, role: "user", text: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);

      try {
        const data = await askQuestion(question, chartType, chartTheme);

        const modelUsed = data.model_used || "gemini";
        if (modelUsed === "groq" && activeModel === "gemini") {
          setMessages((prev) => [
            ...prev,
            {
              id: ++messageId,
              role: "system",
              systemType: "model_switch",
              text: "Gemini quota reached — switched to Groq for this response. Subsequent responses will continue using Groq unless the quota resets.",
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
        };
        setMessages((prev) => [...prev, assistantMsg]);

        setCharts((prev) => [...prev, data.chart_base64 || null]);
        setCurrentChartIndex(charts.length);

        if (data.usage) {
          setTokenUsage((prev) => ({
            prompt_tokens: prev.prompt_tokens + (data.usage.prompt_tokens || 0),
            response_tokens: prev.response_tokens + (data.usage.response_tokens || 0),
            total_tokens: prev.total_tokens + (data.usage.total_tokens || 0),
          }));
        }
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
    [chartType, isStreaming, charts.length, activeModel, chartTheme]
  );

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-surface-800 dark:text-gray-100">
      <div className="relative z-[3] h-full">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
        tokenUsage={tokenUsage}
      />
      </div>
      <div className="flex flex-col flex-1 min-w-0">
      <div className="relative z-[2]">
      <Header
        chartType={chartType}
        chartEnabled={chartEnabled}
        onChartTypeChange={setChartType}
        onChartEnabledChange={setChartEnabled}
        onClearChat={handleClearChat}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        activeModel={activeModel}
        chartTheme={chartTheme}
        onChartThemeChange={setChartTheme}
      />
      </div>
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
      />
      {charts.length > 0 && (
        <ChartPanel
          charts={charts}
          currentIndex={currentChartIndex}
          onIndexChange={setCurrentChartIndex}
        />
      )}
    </div>
    </div>
    </div>
  );
}
