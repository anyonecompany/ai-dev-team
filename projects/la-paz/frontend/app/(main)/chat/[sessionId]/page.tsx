"use client";

import { useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import { useChat } from "@/lib/hooks/useChat";
import ChatBubble from "@/components/chat/ChatBubble";
import ChatInput from "@/components/chat/ChatInput";

export default function ChatSessionPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const { messages, isLoading, sendMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <p className="py-12 text-center text-muted-foreground">
            세션 {sessionId}의 대화를 이어갑니다.
          </p>
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
        <ChatInput
          onSend={(msg) => sendMessage(msg, "ko", sessionId)}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}
