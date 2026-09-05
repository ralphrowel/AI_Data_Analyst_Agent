import { useState } from "react";
import MessageList from "./MessageList";
import InputBar from "./InputBar";
import Toolbar from "./Toolbar";
import ChatHome from "./ChatHome";

export default function ChatPanel({
  messages,
  suggestions,
  isStreaming,
  chartType,
  chartEnabled,
  onChartTypeChange,
  onChartEnabledChange,
  onSubmit,
  activeDatasetName,
  datasetInfo,
  onNewChat,
}) {
  const [input, setInput] = useState("");

  const handleSubmit = (question) => {
    if (!question.trim() || isStreaming) return;
    onSubmit(question);
    setInput("");
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-gray-900">
      {isEmpty ? (
        <ChatHome
          activeDatasetName={activeDatasetName}
          datasetInfo={datasetInfo}
          suggestions={suggestions}
          onSubmit={handleSubmit}
          onNewChat={onNewChat}
          input={input}
          setInput={setInput}
          isStreaming={isStreaming}
        />
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
