import { useState, useEffect, useCallback } from "react";
import { fetchSuggestions, askQuestion } from "../api";
import Sidebar from "./Sidebar";
import ChatPanel from "./ChatPanel";
import ChartPanel from "./ChartPanel";

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
  const [isStreaming, setIsStreaming] = useState(false);

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
        const data = await askQuestion(question, chartType);
        const assistantMsg = {
          id: ++messageId,
          role: "assistant",
          text: data.summary,
          operation: data.operation,
          unsupported_reason: data.unsupported_reason,
          chart_base64: data.chart_base64,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (data.chart_base64) {
          setCharts((prev) => [...prev, data.chart_base64]);
          setCurrentChartIndex(charts.length);
        }

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
    [chartType, isStreaming, charts.length]
  );

  return (
    <div className="flex h-screen bg-surface-950">
      <Sidebar
        tokenUsage={tokenUsage}
        chartType={chartType}
        onChartTypeChange={setChartType}
      />
      <ChatPanel
        messages={messages}
        suggestions={suggestions}
        isStreaming={isStreaming}
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
  );
}
