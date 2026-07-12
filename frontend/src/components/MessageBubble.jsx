export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-accent text-white rounded-br-md"
            : "bg-surface-800 text-surface-200 rounded-bl-md"
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.text}
        </p>
        {message.chart_base64 && (
          <img
            src={`data:image/png;base64,${message.chart_base64}`}
            alt="Chart"
            className="mt-3 rounded-lg w-full max-h-80 object-contain bg-surface-900"
          />
        )}
      </div>
    </div>
  );
}
