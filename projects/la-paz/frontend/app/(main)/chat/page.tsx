"use client";

import { useRef, useEffect } from "react";
import { Circle } from "lucide-react";
import { useChat } from "@/lib/hooks/useChat";
import ChatBubble from "@/components/chat/ChatBubble";
import ChatInput from "@/components/chat/ChatInput";
import { Button } from "@/components/ui/Button";

const quickQuestions = [
  "맨유 vs 아스톤빌라 프리뷰",
  "캐릭 감독 전술 분석",
  "에메리 감독 전술 스타일",
  "맨유 최근 폼 분석",
  "빌라 핵심 선수는?",
  "이번 경기 핵심 매치업",
  "UCL 진출 경쟁 현황",
  "브루노 페르난데스 시즌 분석",
];

export default function ChatPage() {
  const { messages, isLoading, sendMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="flex-1 overflow-y-auto space-y-4 p-4" role="log" aria-live="polite">
        {isEmpty && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Circle className="mb-4 h-12 w-12 fill-primary text-primary" aria-hidden="true" />
            <h2 className="text-xl font-semibold">La Paz AI</h2>
            <p className="mt-1 text-sm text-muted-foreground">축구에 대해 무엇이든 물어보세요!</p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {quickQuestions.map((q) => (
                <Button
                  key={q}
                  variant="outline"
                  size="sm"
                  className="cursor-pointer"
                  onClick={() => sendMessage(q)}
                >
                  {q}
                </Button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatBubble
            key={i}
            role={msg.role}
            content={msg.content}
            sources={msg.sources}
            isStreaming={msg.isStreaming}
            timestamp={msg.timestamp}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border p-4">
        <ChatInput onSend={sendMessage} disabled={isLoading} />
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Powered by RAG + Claude API
        </p>
      </div>
    </div>
  );
}
