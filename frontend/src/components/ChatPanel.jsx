import SuggestedPrompts from "./SuggestedPrompts";
import MessageList from "./MessageList";
import InputBar from "./InputBar";

export default function ChatPanel({
  messages,
  suggestions,
  isStreaming,
  onSubmit,
}) {
  return (
    <div className="flex-1 flex flex-col min-w-0">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col">
          <div className="flex-1 flex items-center justify-center px-6">
            <div className="text-center max-w-md">
              <h2 className="text-xl font-semibold text-surface-50 mb-2">
                What would you like to know?
              </h2>
              <p className="text-sm text-surface-400 mb-8">
                Ask a question about your dataset and get instant analysis with charts.
              </p>
              <SuggestedPrompts prompts={suggestions} onClick={onSubmit} />
            </div>
          </div>
          <div className="border-t border-surface-800 px-4 py-4">
            <InputBar onSubmit={onSubmit} isStreaming={isStreaming} />
          </div>
        </div>
      ) : (
        <>
          <MessageList messages={messages} />
          <div className="border-t border-surface-800 px-4 py-4">
            <InputBar onSubmit={onSubmit} isStreaming={isStreaming} />
          </div>
        </>
      )}
    </div>
  );
}
