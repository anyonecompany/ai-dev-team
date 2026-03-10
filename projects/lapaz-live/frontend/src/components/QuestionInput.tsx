"use client";

import { useState, useCallback, type KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";

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
    <div className="card-surface p-4">
      <div className="relative">
        <textarea
          className="input-dark w-full resize-none rounded-[2px] p-4 pr-14 text-[16px] leading-relaxed"
          rows={3}
          placeholder="경기에 대해 질문해보세요..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
          aria-label="질문 입력"
        />

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || loading || disabled}
          className="btn-primary absolute bottom-3 right-3 flex h-10 w-10 items-center justify-center !p-0 rounded-[2px]"
          title="Send"
          aria-label="질문 보내기"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.5} aria-hidden="true" />
          ) : (
            <Send className="h-4 w-4" strokeWidth={1.5} aria-hidden="true" />
          )}
        </button>
      </div>

      <div className="mt-2 flex items-center justify-between px-1">
        <span className="text-[12px] text-[#6B6B6B] font-body">
          {typeof navigator !== "undefined" && navigator?.platform?.includes("Mac")
            ? "Cmd"
            : "Ctrl"}
          +Enter
        </span>
        {loading && (
          <span className="text-[12px] text-[#00E5A0] font-body animate-toast-in">
            AI가 답변을 생성하고 있습니다...
          </span>
        )}
      </div>
    </div>
  );
}
