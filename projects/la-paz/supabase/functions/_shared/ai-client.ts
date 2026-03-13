// ================================================================
// La Paz — AI Client with Claude → Gemini Fallback
// Pattern: AI_FALLBACK.md §3
// ================================================================

import Anthropic from "npm:@anthropic-ai/sdk@0";
import type { AICallOptions, SSEEventType } from "./types.ts";

// --- SSE Event generator type ---

export interface AIEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

// --- Error classification ---

function isRetryable(error: unknown): boolean {
  if (error instanceof Anthropic.APIError) {
    return error.status === 429 || error.status >= 500;
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return true;
  }
  if (error instanceof TypeError) {
    return true;
  }
  return false;
}

function getErrorCode(error: unknown): string {
  if (error instanceof Anthropic.APIError) {
    if (error.status === 429) return "rate_limit";
    if (error.status >= 500) return "model_error";
    if (error.status === 401) return "auth_required";
    return "model_error";
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return "timeout";
  }
  return "internal_error";
}

// --- Error messages (i18n) ---

const ERROR_MESSAGES: Record<string, Record<string, string>> = {
  rate_limit: {
    ko: "잠시 후 다시 시도해 주세요",
    en: "Please try again in a moment",
  },
  timeout: {
    ko: "응답 시간이 초과되었습니다. 다시 시도해 주세요",
    en: "Response timed out. Please try again",
  },
  model_error: {
    ko: "AI 서비스에 일시적 문제가 발생했습니다",
    en: "AI service is temporarily unavailable",
  },
  invalid_input: {
    ko: "입력 정보를 확인해 주세요",
    en: "Please check your input",
  },
  no_data: {
    ko: "해당 데이터가 없습니다",
    en: "No data available for this query",
  },
  auth_required: {
    ko: "로그인이 필요합니다",
    en: "Authentication required",
  },
  quota_exceeded: {
    ko: "일일 사용 한도를 초과했습니다. 로그인하면 더 많이 사용할 수 있습니다",
    en: "Daily limit exceeded. Sign in for more usage",
  },
  internal_error: {
    ko: "알 수 없는 오류가 발생했습니다",
    en: "An unexpected error occurred",
  },
};

export function getErrorMessage(code: string, language: "ko" | "en" = "ko"): string {
  return ERROR_MESSAGES[code]?.[language] ?? ERROR_MESSAGES.internal_error[language];
}

// --- Main AI call with fallback ---

export async function* callAI(
  systemPrompt: string,
  userMessage: string,
  options: AICallOptions = {},
): AsyncGenerator<AIEvent> {
  // 1. Try Claude (Primary)
  try {
    yield* callClaude(systemPrompt, userMessage, options);
    return;
  } catch (claudeError) {
    if (!isRetryable(claudeError)) {
      const code = getErrorCode(claudeError);
      yield {
        event: "error",
        data: {
          code,
          message: getErrorMessage(code),
          fallback: false,
        },
      };
      return;
    }

    // Signal fallback to client
    yield {
      event: "error",
      data: {
        code: getErrorCode(claudeError),
        message: "Switching to fallback model...",
        fallback: true,
      },
    };
  }

  // 2. Try Gemini Flash (Fallback)
  try {
    yield* callGemini(systemPrompt, userMessage, options);
  } catch (geminiError) {
    const code = getErrorCode(geminiError);
    yield {
      event: "error",
      data: {
        code,
        message: getErrorMessage(code),
        fallback: false,
      },
    };
  }
}

// --- Claude streaming/non-streaming ---

async function* callClaude(
  systemPrompt: string,
  userMessage: string,
  options: AICallOptions,
): AsyncGenerator<AIEvent> {
  const startTime = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? 30_000,
  );

  try {
    const anthropic = new Anthropic();

    if (options.stream) {
      // Streaming mode (chat)
      const stream = await anthropic.messages.stream({
        model: options.model ?? "claude-sonnet-4-20250514",
        max_tokens: options.maxTokens ?? 4096,
        temperature: options.temperature ?? 0.3,
        system: systemPrompt,
        messages: [{ role: "user", content: userMessage }],
      }, { signal: controller.signal });

      let fullText = "";
      for await (const event of stream) {
        if (
          event.type === "content_block_delta" &&
          event.delta.type === "text_delta"
        ) {
          fullText += event.delta.text;
          yield { event: "token", data: { content: event.delta.text } };
        }
      }

      const finalMessage = await stream.finalMessage();

      yield {
        event: "done",
        data: {
          model: options.model ?? "claude-sonnet-4-20250514",
          latency_ms: Date.now() - startTime,
          tokens_used: finalMessage.usage.output_tokens,
          _fullText: fullText,
        },
      };
    } else {
      // Non-streaming mode (structured output via tool_use)
      const createParams: Record<string, unknown> = {
        model: options.model ?? "claude-sonnet-4-20250514",
        max_tokens: options.maxTokens ?? 2048,
        temperature: options.temperature ?? 0.3,
        system: systemPrompt,
        messages: [{ role: "user", content: userMessage }],
      };
      if (options.tools) createParams.tools = options.tools;
      if (options.toolChoice) createParams.tool_choice = options.toolChoice;

      const response = await anthropic.messages.create(
        createParams as Parameters<typeof anthropic.messages.create>[0],
        { signal: controller.signal },
      );

      const toolResult = response.content.find(
        (c: { type: string }) => c.type === "tool_use",
      );
      if (toolResult && "input" in toolResult) {
        yield {
          event: "result",
          data: toolResult.input as Record<string, unknown>,
        };
      }

      yield {
        event: "done",
        data: {
          model: options.model ?? "claude-sonnet-4-20250514",
          latency_ms: Date.now() - startTime,
          tokens_used: response.usage.output_tokens,
        },
      };
    }
  } finally {
    clearTimeout(timeoutId);
  }
}

// --- Gemini Flash fallback ---

async function* callGemini(
  systemPrompt: string,
  userMessage: string,
  options: AICallOptions,
): AsyncGenerator<AIEvent> {
  const startTime = Date.now();
  const apiKey = Deno.env.get("GOOGLE_API_KEY");
  if (!apiKey) throw new Error("Missing GOOGLE_API_KEY");

  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? 30_000,
  );

  try {
    const combinedPrompt = `${systemPrompt}\n\n---\n\n${userMessage}`;

    if (options.stream) {
      // Streaming mode
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?key=${apiKey}&alt=sse`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            contents: [
              { role: "user", parts: [{ text: combinedPrompt }] },
            ],
            generationConfig: {
              maxOutputTokens: options.maxTokens ?? 4096,
              temperature: options.temperature ?? 0.3,
            },
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Gemini API error: ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop()!;

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const json = JSON.parse(line.slice(6));
              const text =
                json.candidates?.[0]?.content?.parts?.[0]?.text;
              if (text) {
                fullText += text;
                yield { event: "token", data: { content: text } };
              }
            } catch {
              // skip malformed JSON chunks
            }
          }
        }
      }

      yield {
        event: "done",
        data: {
          model: "gemini-2.0-flash",
          latency_ms: Date.now() - startTime,
          tokens_used: fullText.split(/\s+/).length,
          _fullText: fullText,
        },
      };
    } else {
      // Non-streaming mode (structured output)
      const bodyPayload: Record<string, unknown> = {
        contents: [
          { role: "user", parts: [{ text: combinedPrompt }] },
        ],
        generationConfig: {
          maxOutputTokens: options.maxTokens ?? 2048,
          temperature: options.temperature ?? 0.3,
        },
      };

      if (options.responseSchema) {
        (bodyPayload.generationConfig as Record<string, unknown>).responseMimeType =
          "application/json";
        (bodyPayload.generationConfig as Record<string, unknown>).responseSchema =
          options.responseSchema;
      }

      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify(bodyPayload),
        },
      );

      if (!response.ok) {
        throw new Error(`Gemini API error: ${response.status}`);
      }

      const json = await response.json();
      const resultText =
        json.candidates?.[0]?.content?.parts?.[0]?.text;

      if (resultText) {
        yield {
          event: "result",
          data: JSON.parse(resultText),
        };
      }

      yield {
        event: "done",
        data: {
          model: "gemini-2.0-flash",
          latency_ms: Date.now() - startTime,
          tokens_used: json.usageMetadata?.candidatesTokenCount ?? 0,
        },
      };
    }
  } finally {
    clearTimeout(timeoutId);
  }
}
