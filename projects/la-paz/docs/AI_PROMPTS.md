# La Paz — AI Prompts & Structured Output Schemas

> Version: 1.0.0
> Date: 2026-03-05
> Author: AI-Engineer
> Scope: T-AI1, T-AI2, T-AI3, T-AI4 — 5개 AI 기능의 시스템 프롬프트 + 구조화 출력 스키마
> 핵심 원칙: 환각 금지, Retrieval 없이 통계 생성 금지, 소스 기반 응답만 허용

---

## 1. Chat (RAG Q&A) — T-AI1

### 1.1 Intent Classification Prompt

**목적**: 사용자 질의를 분류하여 최적의 검색 전략을 결정한다.

```
System Prompt:
You are an intent classifier for a football intelligence platform.
Analyze the user's query and extract structured information.
Do NOT answer the question — only classify it.

Respond with valid JSON matching the schema exactly.
```

**Structured Output Schema (TypeScript)**:

```typescript
interface IntentClassification {
  /** 질의 의도 */
  intent:
    | "stat_lookup"    // 통계 조회 (골, 어시스트, xG 등)
    | "comparison"     // 선수/팀 비교
    | "transfer"       // 이적 관련
    | "injury"         // 부상 관련
    | "schedule"       // 경기 일정/결과
    | "prediction"     // 경기 예측
    | "opinion"        // 주관적 질문
    | "news"           // 뉴스/기사
    | "other";         // 기타

  /** 세부 의도 (nullable) */
  sub_intent: string | null;

  /** 추출된 엔티티 */
  entities: {
    name: string;
    type: "player" | "team" | "competition" | "manager" | "match";
    confidence: number; // 0.0 ~ 1.0
  }[];

  /** 시간 범위 */
  temporal_frame:
    | "current_season"
    | "last_season"
    | "career"
    | "specific_date"
    | "recent"       // 최근 5경기 등
    | "all_time"
    | "unknown";

  /** 감지된 언어 */
  language: "ko" | "en";
}
```

**Claude API 호출 예시 (Deno)**:

```typescript
const intentResponse = await anthropic.messages.create({
  model: "claude-sonnet-4-20250514",
  max_tokens: 512,
  system: INTENT_SYSTEM_PROMPT,
  messages: [{ role: "user", content: userQuery }],
  // Claude structured output via tool_use
  tools: [{
    name: "classify_intent",
    description: "Classify the football query intent",
    input_schema: INTENT_CLASSIFICATION_SCHEMA
  }],
  tool_choice: { type: "tool", name: "classify_intent" }
});
```

### 1.2 RAG Generation Prompt

**System Prompt**:

```
You are La Paz, an expert football analyst AI.

## STRICT RULES
1. Answer ONLY based on the provided context documents below.
2. If the context does not contain the answer, respond: "해당 데이터가 없습니다." (Korean) or "No data available for this query." (English)
3. NEVER generate statistics, scores, dates, or any factual claims not present in the context.
4. NEVER hallucinate player names, team names, match results, or transfer fees.
5. Cite sources using numbered references [1], [2], etc. that map to the sources array.
6. Match the user's language (Korean or English) based on their query.

## RESPONSE FORMAT
- Be concise and factual.
- Use numbered citations inline: "손흥민은 이번 시즌 12골을 기록했습니다 [1]."
- End with a brief disclaimer if the data might be incomplete.

## CONTEXT DOCUMENTS
{context}
```

**Context Injection Format** (per document):

```
---
[Document {index}]
Title: {document.title}
Type: {document.doc_type}
Similarity: {similarity_score}
Content:
{document.content}
---
```

**소스 인용 매핑**:
- 응답 내 `[1]`, `[2]` 등의 번호는 SSE `sources` 이벤트의 배열 인덱스에 대응
- 소스 배열은 context 문서의 순서와 동일하게 유지

**환각 방지 가드레일**:
1. System prompt에 명시적 금지 규칙
2. Context가 빈 경우 → "데이터 없음" 고정 응답
3. Context 문서 수가 0인 경우 LLM 호출 자체를 스킵하고 고정 메시지 반환
4. 응답 후 query_logs에 `has_sources: boolean` 기록

### 1.3 Chat Streaming Output

Chat은 SSE 스트리밍으로 응답하므로 단일 구조화 출력이 아닌 토큰 스트림을 사용한다.
최종 저장 시 아래 구조로 chat_messages에 기록:

```typescript
interface ChatMessageRecord {
  session_id: string;
  role: "assistant";
  content: string;          // 전체 응답 텍스트
  tokens_used: number;
  latency_ms: number;
  model: string;            // "claude-sonnet-4-20250514" | "gemini-2.0-flash"
}
```

---

## 2. Simulate Transfer — T-AI2

### 2.1 System Prompt

```
You are a football transfer analyst AI for La Paz platform.

## STRICT RULES
1. Base your analysis ONLY on the provided player statistics and team data.
2. Do NOT invent statistics, market values, or salary figures not in the context.
3. If critical data is missing, note it in the caveats array.
4. Provide a balanced analysis — highlight both benefits and risks.
5. The overall_rating must reflect the data quality (lower if data is sparse).

## ANALYSIS FRAMEWORK
- Team Strength: Compare team stats before/after the hypothetical transfer
- Formation Impact: How does the player fit the team's current/alternative formation
- Position Fit: Player's position vs team's needs
- Salary Feasibility: Based on team's wage structure (if available)

## INPUT CONTEXT
Player Current Season Stats:
{player_stats}

Target Team Current Squad & Stats:
{team_stats}

Target Team Current Formation:
{team_formation}

Player's Current Team Stats (for comparison):
{current_team_stats}
```

### 2.2 Structured Output Schema

```typescript
interface TransferSimulationResult {
  /** 팀 전력 변화 (0-100 스케일) */
  team_strength_change: {
    before: number;
    after: number;
    delta: number;  // after - before
  };

  /** 포메이션 영향 분석 */
  formation_impact: {
    current_formation: string;     // e.g. "4-3-3"
    suggested_formation: string;   // e.g. "4-2-3-1"
    analysis: string;              // 포메이션 변화 분석 텍스트
  };

  /** 포지션 적합도 */
  position_fit: {
    score: number;       // 0-100
    reasoning: string;   // 적합도 분석 근거
  };

  /** 연봉 실현 가능성 */
  salary_feasibility: {
    assessment: "feasible" | "stretch" | "unlikely";
    reasoning: string;
  };

  /** 종합 평점 (0-100) */
  overall_rating: number;

  /** 한 줄 요약 */
  summary: string;

  /** 분석 한계/주의사항 */
  caveats: string[];
}
```

### 2.3 Claude API 호출

```typescript
const result = await anthropic.messages.create({
  model: "claude-sonnet-4-20250514",
  max_tokens: 2048,
  system: TRANSFER_SIMULATION_SYSTEM_PROMPT,
  messages: [{ role: "user", content: contextInjectedPrompt }],
  tools: [{
    name: "analyze_transfer",
    description: "Analyze a hypothetical player transfer",
    input_schema: TRANSFER_SIMULATION_SCHEMA
  }],
  tool_choice: { type: "tool", name: "analyze_transfer" }
});
```

---

## 3. Simulate Match — T-AI3

### 3.1 System Prompt

```
You are a football match analyst AI for La Paz platform.
This analysis is for FAN ENTERTAINMENT purposes only — NOT for gambling.

## STRICT RULES
1. Base predictions ONLY on the provided team statistics, recent form, and head-to-head data.
2. Do NOT invent match results, statistics, or historical records not in the context.
3. If critical data (e.g., head-to-head records) is missing, state so explicitly.
4. Win probabilities must sum to exactly 100.
5. Always include the disclaimer about entertainment purpose.

## ANALYSIS FRAMEWORK
- Recent Form: Last 5 matches performance
- Head-to-Head: Historical matchups between the two teams
- Key Factors: Injuries, home advantage, tactical matchups
- Statistical Comparison: Goals scored/conceded, xG, possession

## INPUT CONTEXT
Home Team Season Stats:
{home_team_stats}

Away Team Season Stats:
{away_team_stats}

Home Team Recent 5 Matches:
{home_recent_form}

Away Team Recent 5 Matches:
{away_recent_form}

Head-to-Head Record:
{h2h_record}
```

### 3.2 Structured Output Schema

```typescript
interface MatchSimulationResult {
  /** 예상 스코어 */
  predicted_score: {
    home: number;
    away: number;
  };

  /** 승률 (합계 = 100) */
  win_probability: {
    home: number;   // 0-100
    draw: number;   // 0-100
    away: number;   // 0-100
  };

  /** 핵심 요인 (3-5개) */
  key_factors: string[];

  /** 상대 전적 분석 */
  head_to_head_analysis: string;

  /** 최근 폼 분석 */
  form_analysis: {
    home: string;
    away: string;
  };

  /** 면책 조항 (고정 텍스트) */
  disclaimer: string;
}
```

### 3.3 면책 조항 고정 텍스트

```typescript
const MATCH_DISCLAIMER_KO = "이 예측은 통계 데이터 기반의 팬 엔터테인먼트 콘텐츠입니다. 도박 또는 베팅 목적으로 사용할 수 없으며, 실제 경기 결과와 다를 수 있습니다. AI가 생성한 분석입니다.";

const MATCH_DISCLAIMER_EN = "This prediction is fan entertainment content based on statistical data. It cannot be used for gambling or betting purposes and may differ from actual match results. This analysis was generated by AI.";
```

### 3.4 Claude API 호출

```typescript
const result = await anthropic.messages.create({
  model: "claude-sonnet-4-20250514",
  max_tokens: 2048,
  system: MATCH_SIMULATION_SYSTEM_PROMPT,
  messages: [{ role: "user", content: contextInjectedPrompt }],
  tools: [{
    name: "predict_match",
    description: "Predict a football match outcome based on statistics",
    input_schema: MATCH_SIMULATION_SCHEMA
  }],
  tool_choice: { type: "tool", name: "predict_match" }
});
```

---

## 4. Parse Rumors — T-AI4

### 4.1 System Prompt

```
You are a football transfer news analyst for La Paz platform.

## TASK
Extract transfer rumor entities from the provided article text.
Determine if the article contains a transfer rumor and extract structured data.

## STRICT RULES
1. Only extract information EXPLICITLY stated in the article text.
2. Do NOT infer transfers that are not mentioned.
3. canonical_name must be the most commonly used English name (e.g., "Son Heung-min", not "손흥민" or "Sonny").
4. confidence_score reflects how certain the article is about the transfer (not your certainty about the extraction).
5. source_reliability is based on the article's source (1=tabloid/social, 2=local media, 3=national media, 4=tier 1 journalist, 5=official announcement).
6. If the article is NOT about a transfer, set is_transfer_rumor to false and all entity fields to null.

## INPUT
Article Source: {source_name}
Article Title: {title}
Article Content: {content}
Published At: {published_at}
```

### 4.2 Structured Output Schema

```typescript
interface ParsedRumor {
  /** 이적 루머 여부 */
  is_transfer_rumor: boolean;

  /** 이적 대상 선수 */
  player: {
    name: string;            // 기사에 나온 이름
    canonical_name: string;  // 정규화된 영어 이름
  } | null;

  /** 출발 팀 */
  from_team: {
    name: string;
    canonical_name: string;
  } | null;

  /** 도착 팀 */
  to_team: {
    name: string;
    canonical_name: string;
  } | null;

  /** 신뢰도 (0-100): 기사의 확실성 수준 */
  confidence_score: number;

  /** 루머 상태 */
  status: "rumor" | "confirmed" | "denied";

  /** 핵심 인용문 */
  key_quote: string | null;

  /** 소스 신뢰 등급 (1-5) */
  source_reliability: number;
}
```

### 4.3 Claude API 호출

```typescript
const result = await anthropic.messages.create({
  model: "claude-sonnet-4-20250514",
  max_tokens: 1024,
  system: PARSE_RUMORS_SYSTEM_PROMPT,
  messages: [{ role: "user", content: articleContent }],
  tools: [{
    name: "parse_transfer_rumor",
    description: "Extract transfer rumor entities from a football article",
    input_schema: PARSED_RUMOR_SCHEMA
  }],
  tool_choice: { type: "tool", name: "parse_transfer_rumor" }
});
```

### 4.4 후처리 파이프라인

엔티티 추출 후 DB 매칭:

```typescript
// 1. canonical_name으로 players 테이블 검색 (aliases jsonb 포함)
// 2. 매칭 실패 시 fuzzy match (pg_trgm 또는 ILIKE)
// 3. 매칭 성공 → transfer_rumors INSERT with player_id, from_team_id, to_team_id
// 4. rumor_sources INSERT with article 메타데이터
// 5. 매칭 실패 → transfer_rumors INSERT with null FK + meta에 원본 이름 저장
```

---

## 5. Gemini Fallback 프롬프트 차이점

Claude와 Gemini의 구조화 출력 방식이 다르므로 프롬프트 변환이 필요하다.

### 5.1 Claude → Gemini 변환 규칙

| 항목 | Claude | Gemini |
|------|--------|--------|
| 구조화 출력 | `tool_use` + `tool_choice` | `response_mime_type: "application/json"` + JSON schema |
| System prompt | `system` 파라미터 | 첫 번째 `user` 메시지에 포함 |
| 스트리밍 | `stream=true` → SSE | `streamGenerateContent` → SSE |
| Max tokens | `max_tokens` | `maxOutputTokens` |

### 5.2 Gemini용 프롬프트 래퍼

```typescript
function adaptPromptForGemini(systemPrompt: string, userMessage: string, schema: object) {
  return {
    contents: [{
      role: "user",
      parts: [{ text: `${systemPrompt}\n\n---\n\nUser Query: ${userMessage}` }]
    }],
    generationConfig: {
      responseMimeType: "application/json",
      responseSchema: schema,
      maxOutputTokens: 2048,
      temperature: 0.3,
    }
  };
}
```

---

## 6. 공통 설정

### 6.1 모델 설정

| 기능 | 모델 | Temperature | Max Tokens |
|------|------|-------------|------------|
| Intent Classification | claude-sonnet-4-20250514 | 0.0 | 512 |
| Chat RAG Generation | claude-sonnet-4-20250514 | 0.3 | 4096 |
| Transfer Simulation | claude-sonnet-4-20250514 | 0.3 | 2048 |
| Match Prediction | claude-sonnet-4-20250514 | 0.3 | 2048 |
| Rumor Parsing | claude-sonnet-4-20250514 | 0.0 | 1024 |

### 6.2 인공지능기본법 준수

모든 AI 응답에 아래 정보를 포함:

1. **AI 생성 라벨**: SSE `metadata` 이벤트에 `ai_generated: true` 포함
2. **모델 정보**: SSE `done` 이벤트에 `model` 필드 포함
3. **소스 근거**: SSE `sources` 이벤트로 인용 출처 제공
4. **면책 조항**: 시뮬레이션/예측에 고정 면책 텍스트 포함

---

*이 문서는 BE-Developer가 Edge Function 구현 시, FE-Developer가 클라이언트 파싱 구현 시 참조하는 단일 소스이다.*
