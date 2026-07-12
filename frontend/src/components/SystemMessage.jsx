export default function SystemMessage({ message }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[75%] rounded-2xl px-4 py-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-bl-md">
        <div className="flex items-start gap-2.5">
          <svg
            className="w-5 h-5 mt-0.5 shrink-0 text-amber-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z"
            />
          </svg>
          <div>
            <p className="text-xs font-medium text-amber-600 mb-1 uppercase tracking-wider">Not answerable</p>
            <p className="text-sm leading-relaxed">{message.text}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
