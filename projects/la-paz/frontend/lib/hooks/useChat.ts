"use client";

import { useState, useCallback } from "react";
import { parseSSE } from "@/lib/utils/sse";
import type { ChatSource } from "@/lib/types/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
  timestamp: string;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string, locale?: "ko" | "en", sessionId?: string) => Promise<void>;
  sessionId: string | null;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (message: string, locale: "ko" | "en" = "ko", existingSessionId?: string) => {
      setError(null);
      setIsLoading(true);

      const userMessage: ChatMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: "",
        sources: [],
        isStreaming: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/chat`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
            },
            body: JSON.stringify({
              message,
              locale,
              session_id: existingSessionId || sessionId,
            }),
          }
        );

        if (!response.ok) throw new Error("Chat request failed");

        for await (const event of parseSSE(response)) {
          switch (event.event) {
            case "sources":
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = {
                  ...last,
                  sources: (event.data as { sources: ChatSource[] }).sources,
                };
                return updated;
              });
              break;
            case "token":
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = {
                  ...last,
                  content: last.content + (event.data as { content: string }).content,
                };
                return updated;
              });
              break;
            case "done": {
              const doneData = event.data as { session_id?: string };
              if (doneData.session_id) setSessionId(doneData.session_id);
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  isStreaming: false,
                };
                return updated;
              });
              break;
            }
            case "error":
              setError((event.data as { message: string }).message);
              break;
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "알 수 없는 오류");
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: "응답 생성에 실패했습니다. 다시 시도해 주세요.",
            isStreaming: false,
          };
          return updated;
        });
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  return { messages, isLoading, error, sendMessage, sessionId };
}
