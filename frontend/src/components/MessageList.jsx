import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import SystemMessage from "./SystemMessage";

export default function MessageList({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.map((msg) =>
        msg.operation === "unsupported" ? (
          <SystemMessage key={msg.id} message={msg} />
        ) : (
          <MessageBubble key={msg.id} message={msg} />
        )
      )}
      <div ref={bottomRef} />
    </div>
  );
}
