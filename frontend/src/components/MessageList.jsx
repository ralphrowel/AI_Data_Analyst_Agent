import { useState, useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import SystemMessage from "./SystemMessage";

const AGENT_STEPS = [
  {
    type: "thinking",
    text: "Thinking...",
    icon: (
      <svg className="w-3.5 h-3.5 text-accent animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
  },
  {
    type: "querying",
    text: "Querying dataset...",
    icon: (
      <svg className="w-3.5 h-3.5 text-accent animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    ),
  },
  {
    type: "analyzing",
    text: "Looking for patterns & metrics...",
    icon: (
      <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
  {
    type: "formulating",
    text: "Formulating response...",
    icon: (
      <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" />
      </svg>
    ),
  },
];

function AgentStatusIndicator() {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % AGENT_STEPS.length);
    }, 1600);
    return () => clearInterval(interval);
  }, []);

  const current = AGENT_STEPS[stepIndex];

  return (
    <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="max-w-[80%] rounded-2xl rounded-bl-md px-4 py-2.5 bg-surface-100 dark:bg-gray-800 text-surface-800 dark:text-gray-100 border border-surface-200 dark:border-gray-700 shadow-xs flex items-center gap-3">
        <span className="shrink-0 p-1 rounded-md bg-accent/10">{current.icon}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-surface-800 dark:text-gray-100">
            {current.text}
          </span>
          <span className="flex items-center gap-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" />
          </span>
        </div>
      </div>
    </div>
  );
}

export default function MessageList({ messages, isStreaming }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto w-full">
      <div className="max-w-3xl mx-auto px-6 py-6 space-y-4">
        {messages.map((msg) =>
          msg.operation === "unsupported" || msg.role === "system" ? (
            <SystemMessage key={msg.id} message={msg} />
          ) : (
            <MessageBubble key={msg.id} message={msg} />
          )
        )}
        {isStreaming && <AgentStatusIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
