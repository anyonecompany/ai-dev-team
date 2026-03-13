# La Paz — AI Fallback Strategy

> Version: 1.0.0
> Date: 2026-03-05
> Author: AI-Engineer
> Scope: T-AI5 — Claude → Gemini Flash 자동 전환 전략

---

## 1. Fallback 아키텍처

```
User Request
    │
    ▼
┌─────────────────────────┐
│  Claude API (Primary)   │
│  claude-sonnet-4-20250514│
└────────┬────────────────┘
         │
    ┌────┴────┐
    │ Success │──→ SSE Response (token/result → done)
    └────┬────┘
         │ Failure (retryable)
         ▼
    ┌─────────────────────┐
    │  SSE: error event   │
    │  { fallback: true } │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │  Gemini Flash (Fallback)│
    │  gemini-2.0-flash       │
    └────────┬────────────────┘
             │
        ┌────┴────┐
        │ Success │──→ SSE Response (token/result → done, model: "gemini-2.0-flash")
        └────┬────┘
             │ Failure
             ▼
        ┌─────────────────────┐
        │  SSE: error event   │
        │  { fallback: false }│
        │  → 최종 에러 응답    │
        └─────────────────────┘
```

---

## 2. Retryable vs Non-Retryable 에러

### 2.1 Retryable (Fallback 전환 대상)

| 에러 유형 | Claude 응답 | 판별 방법 |
|-----------|-------------|----------|
| Rate Limit | HTTP 429 | `status === 429` |
| Server Error | HTTP 500, 502, 503 | `status >= 500` |
| Timeout | 요청 시간 초과 | `AbortController` timeout |
| Overloaded | HTTP 529 | `status === 529` |
| Connection Error | 네트워크 실패 | `TypeError: fetch failed` |

### 2.2 Non-Retryable (즉시 에러 응답)

| 에러 유형 | 응답 | 이유 |
|-----------|------|------|
| Invalid API Key | HTTP 401 | 설정 오류 — 재시도 무의미 |
| Bad Request | HTTP 400 | 입력 문제 — 동일 입력으로 재시도 무의미 |
| Content Filter | HTTP 400 (content_filter) | 콘텐츠 정책 위반 |
| Invalid Input | 입력 검증 실패 | Zod 스키마 검증 실패 |
| No Data | 검색 결과 0건 | 데이터 부재 — LLM 호출 불필요 |

---

## 3. 구현 패턴

### 3.1 핵심 Fallback 함수

```typescript
// supabase/functions/_shared/ai_client.ts

import Anthropic from "@anthropic-ai/sdk";

interface AICallOptions {
  model?: string;
  maxTokens?: number;
  temperature?: number;
  stream?: boolean;
  timeoutMs?: number;
}

interface SSEEvent {
  event: "token" | "sources" | "metadata" | "result" | "done" | "error";
  data: Record<string, unknown>;
}

function isRetryable(error: unknown): boolean {
  if (error instanceof Anthropic.APIError) {
    return error.status === 429 || error.status >= 500;
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return true; // timeout
  }
  if (error instanceof TypeError) {
    return true; // network error
  }
  return false;
}

async function* callAI(
  systemPrompt: string,
  userMessage: string,
  options: AICallOptions = {}
): AsyncGenerator<SSEEvent> {
  const startTime = Date.now();

  // 1. Try Claude (Primary)
  try {
    yield* callClaude(systemPrompt, userMessage, options);
    return;
  } catch (claudeError) {
    if (!isRetryable(claudeError)) {
      yield {
        event: "error",
        data: {
          code: getErrorCode(claudeError),
          message: getErrorMessage(claudeError),
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
    yield {
      event: "error",
      data: {
        code: getErrorCode(geminiError),
        message: getErrorMessage(geminiError),
        fallback: false,
      },
    };
  }
}
```

### 3.2 Claude 호출 (스트리밍)

```typescript
async function* callClaude(
  systemPrompt: string,
  userMessage: string,
  options: AICallOptions
): AsyncGenerator<SSEEvent> {
  const startTime = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? 30_000
  );

  try {
    const anthropic = new Anthropic();
    let tokensUsed = 0;

    if (options.stream) {
      // Streaming mode (chat)
      const stream = await anthropic.messages.stream({
        model: options.model ?? "claude-sonnet-4-20250514",
        max_tokens: options.maxTokens ?? 4096,
        temperature: options.temperature ?? 0.3,
        system: systemPrompt,
        messages: [{ role: "user", content: userMessage }],
      });

      for await (const event of stream) {
        if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
          yield { event: "token", data: { content: event.delta.text } };
        }
      }

      const finalMessage = await stream.finalMessage();
      tokensUsed = finalMessage.usage.output_tokens;

      yield {
        event: "done",
        data: {
          model: options.model ?? "claude-sonnet-4-20250514",
          latency_ms: Date.now() - startTime,
          tokens_used: tokensUsed,
        },
      };
    } else {
      // Non-streaming mode (simulate, parse)
      const response = await anthropic.messages.create({
        model: options.model ?? "claude-sonnet-4-20250514",
        max_tokens: options.maxTokens ?? 2048,
        temperature: options.temperature ?? 0.3,
        system: systemPrompt,
        messages: [{ role: "user", content: userMessage }],
        tools: options.tools,
        tool_choice: options.toolChoice,
      });

      const toolResult = response.content.find((c) => c.type === "tool_use");
      if (toolResult) {
        yield { event: "result", data: toolResult.input };
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
```

### 3.3 Gemini Flash 호출 (Fallback)

```typescript
async function* callGemini(
  systemPrompt: string,
  userMessage: string,
  options: AICallOptions
): AsyncGenerator<SSEEvent> {
  const startTime = Date.now();
  const apiKey = Deno.env.get("GOOGLE_API_KEY");
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? 30_000
  );

  try {
    if (options.stream) {
      // Streaming mode
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?key=${apiKey}&alt=sse`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            contents: [{
              role: "user",
              parts: [{ text: `${systemPrompt}\n\n---\n\n${userMessage}` }],
            }],
            generationConfig: {
              maxOutputTokens: options.maxTokens ?? 4096,
              temperature: options.temperature ?? 0.3,
            },
          }),
        }
      );

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let totalTokens = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        for (const line of buffer.split("\n")) {
          if (line.startsWith("data: ")) {
            const json = JSON.parse(line.slice(6));
            const text = json.candidates?.[0]?.content?.parts?.[0]?.text;
            if (text) {
              yield { event: "token", data: { content: text } };
              totalTokens += text.split(/\s+/).length; // 근사치
            }
          }
        }
        buffer = "";
      }

      yield {
        event: "done",
        data: {
          model: "gemini-2.0-flash",
          latency_ms: Date.now() - startTime,
          tokens_used: totalTokens,
        },
      };
    } else {
      // Non-streaming mode (structured output)
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            contents: [{
              role: "user",
              parts: [{ text: `${systemPrompt}\n\n---\n\n${userMessage}` }],
            }],
            generationConfig: {
              responseMimeType: "application/json",
              responseSchema: options.responseSchema,
              maxOutputTokens: options.maxTokens ?? 2048,
              temperature: options.temperature ?? 0.3,
            },
          }),
        }
      );

      const json = await response.json();
      const resultText = json.candidates?.[0]?.content?.parts?.[0]?.text;

      if (resultText) {
        yield { event: "result", data: JSON.parse(resultText) };
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
```

---

## 4. Rate Limiting & Timeout 설정

### 4.1 기능별 Timeout

| Edge Function | Claude Timeout | Gemini Timeout | 총 최대 대기 |
|---------------|---------------|----------------|-------------|
| `chat` | 30s | 30s | 60s |
| `simulate-transfer` | 60s | 60s | 120s |
| `simulate-match` | 60s | 60s | 120s |
| `parse-rumors` | 30s (per article) | 30s (per article) | 60s per article |

### 4.2 Rate Limiting (Edge Function 레벨)

| 사용자 유형 | 제한 | 적용 방법 |
|------------|------|----------|
| 비로그인 | 분당 10회 (AI 엔드포인트) | IP 기반, Supabase Edge Function header 검사 |
| 로그인 | 분당 30회 (AI 엔드포인트) | user_id 기반, fan_events 카운트 |
| 비로그인 시뮬레이션 | 일 5회 | IP + localStorage fingerprint |

### 4.3 Rate Limit 구현 패턴

```typescript
async function checkRateLimit(
  supabase: SupabaseClient,
  userId: string | null,
  clientIp: string
): Promise<{ allowed: boolean; remaining: number }> {
  const windowMs = 60_000; // 1분
  const limit = userId ? 30 : 10;
  const key = userId ?? clientIp;

  const { count } = await supabase
    .from("fan_events")
    .select("id", { count: "exact", head: true })
    .eq(userId ? "user_id" : "payload->>client_ip", key)
    .gte("created_at", new Date(Date.now() - windowMs).toISOString());

  return {
    allowed: (count ?? 0) < limit,
    remaining: Math.max(0, limit - (count ?? 0)),
  };
}
```

---

## 5. 모델별 프롬프트 차이점

### 5.1 구조화 출력

| 기능 | Claude 방식 | Gemini 방식 |
|------|------------|------------|
| Intent 분류 | `tool_use` + `tool_choice: { type: "tool" }` | `responseMimeType: "application/json"` + `responseSchema` |
| 시뮬레이션 | `tool_use` + `tool_choice: { type: "tool" }` | `responseMimeType: "application/json"` + `responseSchema` |
| 루머 파싱 | `tool_use` + `tool_choice: { type: "tool" }` | `responseMimeType: "application/json"` + `responseSchema` |
| Chat (스트리밍) | `messages.stream()` | `streamGenerateContent?alt=sse` |

### 5.2 System Prompt 전달

| | Claude | Gemini |
|-|--------|--------|
| System prompt | 별도 `system` 파라미터 | 첫 `user` 메시지에 합쳐서 전달 |
| 형식 | `system: "..."` | `parts: [{ text: "{systemPrompt}\n\n---\n\n{userMessage}" }]` |

### 5.3 응답 파싱

| | Claude | Gemini |
|-|--------|--------|
| 스트리밍 토큰 | `content_block_delta.delta.text` | `candidates[0].content.parts[0].text` |
| 구조화 결과 | `content[].type === "tool_use"` → `.input` | `candidates[0].content.parts[0].text` → `JSON.parse()` |
| 토큰 카운트 | `usage.output_tokens` | `usageMetadata.candidatesTokenCount` |

### 5.4 프롬프트 일관성 보장

Gemini fallback 시에도 동일한 system prompt를 사용한다. 차이점:

1. **Temperature 동일 유지**: 두 모델 모두 같은 temperature 사용
2. **Max tokens 동일 유지**: 출력 길이 제한 동일
3. **가드레일 동일 적용**: 환각 방지 규칙은 system prompt에 포함되므로 모델 무관
4. **구조화 출력 스키마 변환**: Claude `tool_use` 스키마를 Gemini `responseSchema`로 자동 변환

```typescript
function convertToolSchemaToGeminiSchema(
  claudeToolSchema: Record<string, unknown>
): Record<string, unknown> {
  // Claude tool input_schema → Gemini responseSchema
  // 구조는 동일한 JSON Schema이므로 직접 전달 가능
  return claudeToolSchema;
}
```

---

## 6. 에러 메시지 (다국어)

| Code | 한국어 | English |
|------|--------|---------|
| `rate_limit` | 잠시 후 다시 시도해 주세요 | Please try again in a moment |
| `timeout` | 응답 시간이 초과되었습니다. 다시 시도해 주세요 | Response timed out. Please try again |
| `model_error` | AI 서비스에 일시적 문제가 발생했습니다 | AI service is temporarily unavailable |
| `invalid_input` | 입력 정보를 확인해 주세요 | Please check your input |
| `no_data` | 해당 데이터가 없습니다 | No data available for this query |
| `auth_required` | 로그인이 필요합니다 | Authentication required |
| `quota_exceeded` | 일일 사용 한도를 초과했습니다. 로그인하면 더 많이 사용할 수 있습니다 | Daily limit exceeded. Sign in for more usage |
| `internal_error` | 알 수 없는 오류가 발생했습니다 | An unexpected error occurred |

```typescript
function getErrorMessage(code: string, language: "ko" | "en"): string {
  const messages: Record<string, Record<string, string>> = {
    rate_limit: { ko: "잠시 후 다시 시도해 주세요", en: "Please try again in a moment" },
    timeout: { ko: "응답 시간이 초과되었습니다. 다시 시도해 주세요", en: "Response timed out. Please try again" },
    model_error: { ko: "AI 서비스에 일시적 문제가 발생했습니다", en: "AI service is temporarily unavailable" },
    invalid_input: { ko: "입력 정보를 확인해 주세요", en: "Please check your input" },
    no_data: { ko: "해당 데이터가 없습니다", en: "No data available for this query" },
    auth_required: { ko: "로그인이 필요합니다", en: "Authentication required" },
    quota_exceeded: { ko: "일일 사용 한도를 초과했습니다. 로그인하면 더 많이 사용할 수 있습니다", en: "Daily limit exceeded. Sign in for more usage" },
    internal_error: { ko: "알 수 없는 오류가 발생했습니다", en: "An unexpected error occurred" },
  };
  return messages[code]?.[language] ?? messages.internal_error[language];
}
```

---

## 7. 모니터링 & 로깅

Fallback 발생 시 fan_events에 기록하여 모니터링한다.

```typescript
// Fallback 발생 시 로깅
await supabase.from("fan_events").insert({
  event_type: "ai_fallback",
  payload: {
    primary_model: "claude-sonnet-4-20250514",
    fallback_model: "gemini-2.0-flash",
    error_code: claudeErrorCode,
    function_name: edgeFunctionName,
    latency_ms: totalLatency,
  },
});
```

Fallback 비율이 10%를 초과하면 RAG 품질 위험 신호로 간주한다 (CLAUDE.md §7).

---

*이 문서는 BE-Developer가 Edge Function의 AI 호출 로직을 구현할 때 참조하는 단일 소스이다.*
