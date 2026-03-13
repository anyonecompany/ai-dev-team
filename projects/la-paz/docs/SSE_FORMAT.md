# La Paz — SSE (Server-Sent Events) Format Standard

> Version: 1.0.0
> Date: 2026-03-05
> Author: AI-Engineer
> Scope: 모든 스트리밍 Edge Function이 준수할 SSE 포맷 표준

---

## 1. 공통 규칙

- Content-Type: `text/event-stream; charset=utf-8`
- Cache-Control: `no-cache`
- Connection: `keep-alive`
- 모든 `data` 필드는 유효한 JSON 문자열이어야 한다
- 각 이벤트는 빈 줄(`\n\n`)로 구분한다
- 클라이언트는 `event` 타입으로 분기 처리한다

---

## 2. Event Types

### 2.1 `token` — 텍스트 스트리밍 토큰

LLM 응답의 개별 토큰을 전달한다.

```
event: token
data: {"content": "손흥민은 "}

event: token
data: {"content": "이번 시즌 "}

event: token
data: {"content": "12골을 기록했습니다 [1]."}
```

| Field | Type | Description |
|-------|------|-------------|
| `content` | `string` | 응답 텍스트 청크 |

### 2.2 `sources` — 참조 소스 목록

RAG 검색 결과에서 사용된 소스 문서 정보를 전달한다. 토큰 스트리밍 전에 전송한다.

```
event: sources
data: {"sources": [{"title": "Son Heung-min 2025-26 Season Stats", "doc_type": "player_profile", "ref_id": "abc-123", "similarity": 0.92}, {"title": "Tottenham vs Arsenal Match Report", "doc_type": "match_report", "ref_id": "def-456", "similarity": 0.85}]}
```

| Field | Type | Description |
|-------|------|-------------|
| `sources` | `Source[]` | 소스 배열 |
| `sources[].title` | `string` | 문서 제목 |
| `sources[].doc_type` | `string` | 문서 유형 (match_report, player_profile, team_profile, transfer_news, league_standing, article) |
| `sources[].ref_id` | `string` | 원본 레코드 ID |
| `sources[].similarity` | `number` | 코사인 유사도 (0.0-1.0) |

### 2.3 `metadata` — 요청 메타데이터

인텐트 분류 결과, AI 생성 라벨 등의 메타정보를 전달한다. 토큰 스트리밍 전에 전송한다.

```
event: metadata
data: {"intent": "stat_lookup", "entities": [{"name": "Son Heung-min", "type": "player"}], "language": "ko", "ai_generated": true}
```

| Field | Type | Description |
|-------|------|-------------|
| `intent` | `string` | 분류된 의도 |
| `entities` | `Entity[]` | 추출된 엔티티 |
| `language` | `string` | 감지된 언어 (ko/en) |
| `ai_generated` | `boolean` | 항상 `true` (인공지능기본법 준수) |

### 2.4 `result` — 구조화 결과 (비스트리밍 AI 기능)

시뮬레이션/파싱 등 구조화된 결과를 한 번에 전달한다.

```
event: result
data: {"team_strength_change": {"before": 78, "after": 83, "delta": 5}, "formation_impact": {...}, "position_fit": {"score": 85, "reasoning": "..."}, "salary_feasibility": {"assessment": "feasible", "reasoning": "..."}, "overall_rating": 82, "summary": "...", "caveats": ["..."]}
```

| Field | Type | Description |
|-------|------|-------------|
| (전체) | `TransferSimulationResult \| MatchSimulationResult \| ParsedRumor` | AI_PROMPTS.md에 정의된 스키마 |

### 2.5 `done` — 스트리밍 완료

응답이 정상적으로 완료되었음을 알린다. 항상 마지막에 전송한다.

```
event: done
data: {"model": "claude-sonnet-4-20250514", "latency_ms": 2340, "tokens_used": 450}
```

| Field | Type | Description |
|-------|------|-------------|
| `model` | `string` | 사용된 모델 ID |
| `latency_ms` | `number` | 총 처리 시간 (ms) |
| `tokens_used` | `number` | 사용된 토큰 수 |

### 2.6 `error` — 에러

처리 중 발생한 에러를 전달한다.

```
event: error
data: {"code": "rate_limit", "message": "잠시 후 다시 시도해 주세요", "fallback": true}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | `string` | 에러 코드 (아래 표 참조) |
| `message` | `string` | 사용자 친화적 에러 메시지 |
| `fallback` | `boolean` | `true`: fallback 모델로 전환 중, `false`: 최종 실패 |

**에러 코드 목록**:

| Code | 원인 | Fallback 가능 |
|------|------|-------------|
| `rate_limit` | API rate limit 초과 | Yes |
| `timeout` | 요청 타임아웃 | Yes |
| `model_error` | LLM API 5xx 에러 | Yes |
| `invalid_input` | 잘못된 입력 파라미터 | No |
| `no_data` | 검색 결과 없음 (데이터 부재) | No |
| `auth_required` | 인증 필요 | No |
| `quota_exceeded` | 비로그인 일일 한도 초과 | No |
| `internal_error` | 서버 내부 에러 | No |

---

## 3. Edge Function별 Event 시퀀스

### 3.1 `chat` (RAG Q&A)

```
┌─ Client Request ─────────────────────────┐
│ POST /functions/v1/chat                  │
│ Body: { query, session_id?, locale }     │
└──────────────────────────────────────────┘
           │
           ▼
event: metadata    ← Intent 분류 결과 + ai_generated 라벨
event: sources     ← RAG 검색 결과 (소스 목록)
event: token       ← (반복) LLM 응답 토큰 스트리밍
event: token
...
event: done        ← 완료 (모델, 지연시간, 토큰 수)
```

에러 시:
```
event: metadata
event: error       ← { fallback: true } → Gemini로 전환
event: sources
event: token       ← Gemini 응답 스트리밍
...
event: done        ← { model: "gemini-2.0-flash" }
```

### 3.2 `simulate-transfer` (이적 시뮬레이션)

```
┌─ Client Request ─────────────────────────┐
│ POST /functions/v1/simulate-transfer     │
│ Body: { player_id, target_team_id }      │
└──────────────────────────────────────────┘
           │
           ▼
event: metadata    ← { ai_generated: true, simulation_type: "transfer" }
event: result      ← TransferSimulationResult (한 번에 전달)
event: done        ← 완료
```

### 3.3 `simulate-match` (경기 예측)

```
┌─ Client Request ─────────────────────────┐
│ POST /functions/v1/simulate-match        │
│ Body: { home_team_id, away_team_id }     │
└──────────────────────────────────────────┘
           │
           ▼
event: metadata    ← { ai_generated: true, simulation_type: "match" }
event: result      ← MatchSimulationResult (한 번에 전달)
event: done        ← 완료
```

### 3.4 `parse-rumors` (루머 파싱)

```
┌─ Client Request ─────────────────────────┐
│ POST /functions/v1/parse-rumors          │
│ Body: { article_ids: string[] }          │
└──────────────────────────────────────────┘
           │
           ▼
event: result      ← ParsedRumor (기사당 1회)
event: result      ← ParsedRumor (다음 기사)
...
event: done        ← 완료 { processed: number, rumors_found: number }
```

### 3.5 `search` (시맨틱 검색)

검색은 SSE가 아닌 일반 JSON 응답을 사용한다.

```
┌─ Client Request ─────────────────────────┐
│ POST /functions/v1/search                │
│ Body: { query, limit?, filter_type? }    │
└──────────────────────────────────────────┘
           │
           ▼
Response (JSON):
{
  "results": [
    { "id": "...", "title": "...", "doc_type": "...", "content": "...", "similarity": 0.92 }
  ],
  "query_time_ms": 120,
  "total": 5
}
```

---

## 4. TypeScript 타입 정의

```typescript
// SSE Event 기본 타입
interface SSEEvent {
  event: "token" | "sources" | "metadata" | "result" | "done" | "error";
  data: Record<string, unknown>;
}

// Token Event
interface TokenEvent extends SSEEvent {
  event: "token";
  data: { content: string };
}

// Sources Event
interface SourcesEvent extends SSEEvent {
  event: "sources";
  data: {
    sources: {
      title: string;
      doc_type: string;
      ref_id: string;
      similarity: number;
    }[];
  };
}

// Metadata Event
interface MetadataEvent extends SSEEvent {
  event: "metadata";
  data: {
    intent?: string;
    entities?: { name: string; type: string }[];
    language?: string;
    ai_generated: true;
    simulation_type?: "transfer" | "match";
  };
}

// Result Event
interface ResultEvent extends SSEEvent {
  event: "result";
  data: TransferSimulationResult | MatchSimulationResult | ParsedRumor;
}

// Done Event
interface DoneEvent extends SSEEvent {
  event: "done";
  data: {
    model: string;
    latency_ms: number;
    tokens_used?: number;
    processed?: number;
    rumors_found?: number;
  };
}

// Error Event
interface ErrorEvent extends SSEEvent {
  event: "error";
  data: {
    code: string;
    message: string;
    fallback: boolean;
  };
}
```

---

## 5. 클라이언트 파싱 예시 (FE 참조)

```typescript
const eventSource = new EventSource(url);
// 또는 fetch + ReadableStream 사용

async function* parseSSE(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop()!;

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7);
      } else if (line.startsWith("data: ")) {
        const data = JSON.parse(line.slice(6));
        yield { event: currentEvent, data } as SSEEvent;
      }
    }
  }
}
```

---

*이 문서는 BE-Developer (Edge Function 구현)와 FE-Developer (클라이언트 SSE 파싱)의 공통 계약서이다.*
