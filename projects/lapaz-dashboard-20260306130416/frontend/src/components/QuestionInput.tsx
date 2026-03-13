"use client";

import { useState, useCallback, type KeyboardEvent } from "react";

interface QuestionInputProps {
  onSubmit: (question: string) => Promise<void>;
  disabled?: boolean;
}

export default function QuestionInput({
  onSubmit,
  disabled,
}: QuestionInputProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    try {
      await onSubmit(trimmed);
      setText("");
    } finally {
      setLoading(false);
    }
  }, [text, loading, onSubmit]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="glass-card p-4">
      <div className="relative">
        <textarea
          className="w-full resize-none rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 pr-14 text-[15px] text-white placeholder-gray-500 focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
          rows={3}
          placeholder="경기에 대해 질문해보세요..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
        />

        {/* Send button - floating */}
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || loading || disabled}
          className="btn-glow absolute bottom-3 right-3 flex h-10 w-10 items-center justify-center rounded-xl text-white"
          title="Send"
        >
          {loading ? (
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
            </svg>
          )}
        </button>
      </div>

      <div className="mt-2 flex items-center justify-between px-1">
        <span className="text-[11px] text-gray-600">
          {typeof navigator !== "undefined" && navigator?.platform?.includes("Mac") ? "Cmd" : "Ctrl"}+Enter
        </span>
        {loading && (
          <span className="text-[11px] text-indigo-400 toast-enter">
            AI가 답변을 생성하고 있습니다...
          </span>
        )}
      </div>
    </div>
  );
}
