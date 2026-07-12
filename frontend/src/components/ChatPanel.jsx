import { useState } from "react";
import SuggestedPrompts from "./SuggestedPrompts";
import MessageList from "./MessageList";
import InputBar from "./InputBar";
import Toolbar from "./Toolbar";

export default function ChatPanel({
  messages,
  suggestions,
  isStreaming,
  chartType,
  chartEnabled,
  onChartTypeChange,
  onChartEnabledChange,
  onSubmit,
}) {
  const [input, setInput] = useState("");

  const handleSubmit = (question) => {
    if (!question.trim() || isStreaming) return;
    onSubmit(question);
    setInput("");
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-white">
      {isEmpty ? (
        <div className="flex-1 flex flex-col">
          <div className="flex-1" />
          <div className="px-6 pb-4 max-w-2xl mx-auto w-full">
            <SuggestedPrompts prompts={suggestions} onClick={handleSubmit} />
            <Toolbar
              chartType={chartType}
              chartEnabled={chartEnabled}
              onChartTypeChange={onChartTypeChange}
              onChartEnabledChange={onChartEnabledChange}
            />
            <InputBar
              value={input}
              onChange={setInput}
              onSubmit={handleSubmit}
              isStreaming={isStreaming}
            />
          </div>
          <div className="h-12" />
        </div>
      ) : (
        <>
          <MessageList messages={messages} />
          <div className="px-6 py-4 max-w-2xl mx-auto w-full">
            <Toolbar
              chartType={chartType}
              chartEnabled={chartEnabled}
              onChartTypeChange={onChartTypeChange}
              onChartEnabledChange={onChartEnabledChange}
            />
            <InputBar
              value={input}
              onChange={setInput}
              onSubmit={handleSubmit}
              isStreaming={isStreaming}
            />
          </div>
        </>
      )}
    </div>
  );
}
