# API Contract — Edge Functions

> Version: 1.0.0
> Date: 2026-03-05
> Author: Architect
> Base URL: `https://<project-ref>.supabase.co/functions/v1`

---

## 공통 규칙

### 인증
- 모든 요청에 `Authorization: Bearer <anon_key>` 헤더 필수
- 로그인 사용자는 `Authorization: Bearer <access_token>` (Supabase Auth JWT)
- Edge Function 내부에서 `service_role` 키로 DB 접근

### Rate Limiting
- 비로그인: 분당 10회 (AI 엔드포인트)
- 로그인: 분당 30회 (AI 엔드포인트)

### 에러 형식
```typescript
interface ErrorResponse {
  error: {
    code: string;       // "RATE_LIMITED" | "INVALID_INPUT" | "INTERNAL_ERROR" | "MODEL_ERROR"
    message: string;
    details?: unknown;
  };
}
```

### SSE 스트리밍 규약
- Content-Type: `text/event-stream`
- 각 이벤트: `event: <type>\ndata: <json>\n\n`
- 마지막 이벤트: `event: done`
- 에러 발생 시: `event: error` 후 스트림 종료

---

## 1. chat

AI Q&A — RAG 파이프라인 + SSE 스트리밍

### Endpoint
```
POST /functions/v1/chat
```

### Request
```typescript
interface ChatRequest {
  message: string;          // 사용자 질문 (최대 2000자)
  session_id?: string;      // 기존 대화 이어가기 (uuid)
  locale: "ko" | "en";     // 응답 언어
}
```

### Response (SSE Stream)
```typescript
// event: token
interface ChatTokenEvent {
  text: string;             // 생성된 텍스트 청크
}

// event: sources
interface ChatSourcesEvent {
  sources: Array<{
    doc_id: string;
    title: string;
    snippet: string;
    doc_type: string;       // match_report | team_profile | player_profile | transfer_news | ...
    similarity: number;     // 0.0 ~ 1.0
  }>;
}

// event: done
interface ChatDoneEvent {
  session_id: string;       // 생성/사용된 세션 ID
  message_id: string;       // 저장된 메시지 ID
  model_used: string;       // "claude" | "gemini-flash"
  latency_ms: number;
}

// event: error
interface ChatErrorEvent {
  code: string;
  message: string;
}
```

### 내부 파이프라인
```
1. 입력 검증 (Zod)
2. 언어 감지 + 한→영 엔티티 매핑
3. Intent 분류 (Claude structured output)
4. Hybrid Search:
   a. 엔티티 직접 SQL 조회
   b. pgvector 코사인 유사도 (match_documents RPC)
   c. 키워드 폴백 (ILIKE)
5. Context 랭킹 + 토큰 제한
6. Claude API 생성 (SSE)
   - 실패 시 Gemini Flash fallback
7. 소스 인용 첨부
8. chat_sessions/chat_messages 저장
9. query_logs 비동기 저장
```

---

## 2. search

시맨틱 + 키워드 하이브리드 검색

### Endpoint
```
POST /functions/v1/search
```

### Request
```typescript
interface SearchRequest {
  query: string;            // 검색어 (최대 500자)
  limit?: number;           // 결과 수 (기본 10, 최대 50)
  locale?: "ko" | "en";    // 검색 언어 (엔티티 별칭 매핑용)
}
```

### Response
```typescript
interface SearchResponse {
  results: Array<{
    doc_id: string;
    title: string;
    snippet: string;        // 최대 300자
    similarity: number;     // 0.0 ~ 1.0
    doc_type: string;       // match_report | team_profile | player_profile | ...
  }>;
  query_time_ms: number;
}
```

---

## 3. parse-rumors

articles 테이블에서 이적 관련 기사를 파싱하여 transfer_rumors/rumor_sources에 엔티티 추출/저장

### Endpoint
```
POST /functions/v1/parse-rumors
```

### Request
```typescript
interface ParseRumorsRequest {
  article_ids?: string[];   // 특정 기사만 파싱 (uuid[])
  max_articles?: number;    // 최대 처리 건수 (기본 20, 최대 100)
}
```

### Response
```typescript
interface ParseRumorsResponse {
  parsed_count: number;     // 처리된 기사 수
  rumors_created: number;   // 생성된 루머 수
  rumors_updated: number;   // 업데이트된 루머 수
  sources_created: number;  // 생성된 소스 수
  errors: Array<{
    article_id: string;
    error: string;
  }>;
}
```

### 내부 파이프라인
```
1. 입력 검증
2. articles 테이블에서 미파싱 기사 조회
   - article_ids 지정 시 해당 기사만
   - 미지정 시 tags에 'transfer' 포함 + 최근 순 max_articles개
3. Claude API 엔티티 추출 (structured output):
   - player_name → players 테이블 매칭
   - from_team, to_team → teams 테이블 매칭
   - confidence_score (0-100)
   - status (rumor/confirmed/denied)
   - journalist, source_name
4. transfer_rumors UPSERT (player_id + to_team_id 기준)
5. rumor_sources INSERT
6. 결과 반환
```

### 호출 방식
- **cron**: Supabase pg_cron 또는 외부 cron에서 주기 호출 (1시간 간격 권장)
- **수동**: 관리자가 특정 기사 파싱 트리거

---

## 4. simulate-transfer

이적 시뮬레이션 — 선수/팀 데이터 기반 AI 분석

### Endpoint
```
POST /functions/v1/simulate-transfer
```

### Request
```typescript
interface SimulateTransferRequest {
  player_id: string;        // uuid
  target_team_id: string;   // uuid
}
```

### Response (SSE Stream)
```typescript
// event: analysis
interface TransferAnalysisEvent {
  section: "team_strength" | "formation_impact" | "position_fit" | "salary_feasibility" | "overall";
  data: {
    // section === "team_strength"
    team_strength_change?: {
      before: number;       // 0-100
      after: number;        // 0-100
      delta: number;
      reasoning: string;
    };
    // section === "formation_impact"
    formation_impact?: {
      best_formation: string;   // e.g. "4-3-3"
      position_in_formation: string;
      squad_depth_change: string;
      reasoning: string;
    };
    // section === "position_fit"
    position_fit?: {
      score: number;        // 0-100
      player_strengths: string[];
      team_needs: string[];
      reasoning: string;
    };
    // section === "salary_feasibility"
    salary_feasibility?: {
      estimated_salary: string;
      team_wage_budget: string;
      feasibility: "high" | "medium" | "low";
      reasoning: string;
    };
    // section === "overall"
    overall_rating?: {
      score: number;        // 0-100
      recommendation: "strongly_recommend" | "recommend" | "neutral" | "not_recommend";
      summary: string;
    };
  };
}

// event: done
interface TransferDoneEvent {
  simulation_id: string;    // 저장된 시뮬레이션 ID
  model_used: string;
  latency_ms: number;
}

// event: error
interface TransferErrorEvent {
  code: string;
  message: string;
}
```

### 내부 파이프라인
```
1. 입력 검증 + player/team 존재 확인
2. 데이터 수집:
   a. player_season_stats (현재 시즌)
   b. 타겟팀 team_season_stats
   c. 타겟팀 현재 스쿼드 (player_contracts WHERE is_active)
   d. 타겟팀 최근 formations
3. Claude API 구조화 출력 (SSE)
   - 5개 섹션 순차 스트리밍
4. simulations 테이블 저장
```

---

## 5. simulate-match

경기 결과 예측 — 양팀 통계 기반 AI 분석

### Endpoint
```
POST /functions/v1/simulate-match
```

### Request
```typescript
interface SimulateMatchRequest {
  home_team_id: string;     // uuid
  away_team_id: string;     // uuid
}
```

### Response (SSE Stream)
```typescript
// event: prediction
interface MatchPredictionEvent {
  section: "predicted_score" | "win_probability" | "key_factors" | "head_to_head" | "overall";
  data: {
    // section === "predicted_score"
    predicted_score?: {
      home: number;
      away: number;
      confidence: number;   // 0.0 ~ 1.0
    };
    // section === "win_probability"
    win_probability?: {
      home_win: number;     // 0.0 ~ 1.0
      draw: number;
      away_win: number;
    };
    // section === "key_factors"
    key_factors?: Array<{
      factor: string;
      impact: "positive_home" | "positive_away" | "neutral";
      description: string;
    }>;
    // section === "head_to_head"
    head_to_head_analysis?: {
      total_matches: number;
      home_wins: number;
      draws: number;
      away_wins: number;
      recent_form: string;
    };
    // section === "overall"
    overall?: {
      summary: string;
      prediction: string;   // e.g. "홈팀 2:1 승리 예상"
    };
  };
}

// event: done
interface MatchDoneEvent {
  simulation_id: string;
  model_used: string;
  latency_ms: number;
}

// event: error
interface MatchErrorEvent {
  code: string;
  message: string;
}
```

### 내부 파이프라인
```
1. 입력 검증 + team 존재 확인
2. 데이터 수집:
   a. 양팀 team_season_stats (현재 시즌)
   b. 양팀 최근 5경기 결과 (matches)
   c. 양팀 상대 전적 (matches WHERE home/away 조합)
   d. 양팀 주요 선수 부상 현황 (injuries WHERE end_date IS NULL)
3. Claude API 구조화 출력 (SSE)
   - 5개 섹션 순차 스트리밍
4. simulations 테이블 저장
5. fan_predictions.ai_prediction 업데이트 (해당 매치가 있을 경우)
```

---

## 타입 정의 파일 경로

Edge Function 구현 시 아래 공유 타입 파일을 참조:

```
frontend/lib/types/api.ts          ← 프론트엔드 공유 타입
supabase/functions/_shared/types.ts ← Edge Function 공유 타입
```

두 파일은 동일한 인터페이스를 정의하며, 변경 시 양쪽 동기화 필수.
