# La Paz Live Q&A Dashboard - API Specification

> Version: 1.0.0
> Date: 2026-03-06
> Author: Architect Agent

---

## Base URL

```
http://localhost:8000/api
```

---

## Endpoints

### 1. POST /api/ask

RAG 파이프라인을 통해 팬 질문에 대한 답변을 생성한다.

**Request Body**

```json
{
  "question": "string (required)",
  "match_context": {
    "home_team": "string",
    "away_team": "string",
    "match_date": "string (YYYY-MM-DD)",
    "current_minute": "number | null"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | 팬 질문 텍스트 |
| match_context | object | No | 경기 컨텍스트 (없으면 현재 라이브 경기 기본값 사용) |
| match_context.home_team | string | No | 홈팀 이름 |
| match_context.away_team | string | No | 원정팀 이름 |
| match_context.match_date | string | No | 경기 날짜 (YYYY-MM-DD) |
| match_context.current_minute | number | No | 현재 경기 진행 시간(분) |

**Response** `201 Created`

```json
{
  "id": "uuid",
  "question": "string",
  "answer": "string",
  "category": "string",
  "confidence": 0.95,
  "source_count": 3,
  "generation_time_ms": 1200,
  "status": "draft"
}
```

| Field | Type | Description |
|-------|------|-------------|
| id | string (uuid) | 질문 고유 ID |
| question | string | 원본 질문 |
| answer | string | RAG 파이프라인 생성 답변 |
| category | string | 질문 카테고리 (7종: 선수정보, 전술, 역사, 규칙, 이적, 부상, 기타) |
| confidence | number (0-1) | 답변 신뢰도 |
| source_count | number | 참조한 소스 문서 수 |
| generation_time_ms | number | 답변 생성 소요 시간(ms) |
| status | string | 초기 상태는 항상 "draft" |

**Error Responses**

| Status | Description |
|--------|-------------|
| 400 | question 필드 누락 또는 빈 문자열 |
| 500 | RAG 파이프라인 내부 오류 |

---

### 2. GET /api/questions

질문 목록을 조회한다. 페이지네이션 및 상태 필터 지원.

**Query Parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| status | string | (all) | 필터: `draft`, `published`, `archived` |
| limit | number | 20 | 한 페이지당 항목 수 (max: 100) |
| offset | number | 0 | 시작 위치 |

**Response** `200 OK`

```json
{
  "questions": [
    {
      "id": "uuid",
      "question": "string",
      "answer": "string",
      "category": "string",
      "confidence": 0.95,
      "source_count": 3,
      "generation_time_ms": 1200,
      "status": "draft",
      "match_context": { "home_team": "...", "away_team": "...", "match_date": "..." },
      "created_at": "2026-03-06T12:00:00Z",
      "updated_at": "2026-03-06T12:00:00Z"
    }
  ],
  "total": 42
}
```

---

### 3. PATCH /api/questions/{id}/status

질문의 상태를 변경한다. 운영자가 draft → published (방송 노출) 또는 archived (숨김) 처리.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| id | string (uuid) | 질문 ID |

**Request Body**

```json
{
  "status": "draft" | "published" | "archived"
}
```

**Response** `200 OK`

```json
{
  "id": "uuid",
  "status": "published",
  "updated_at": "2026-03-06T12:05:00Z"
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 400 | 유효하지 않은 status 값 |
| 404 | 해당 ID의 질문이 존재하지 않음 |

**상태 전이 규칙**

```
draft → published    (방송 노출 승인)
draft → archived     (폐기)
published → archived (방송 후 보관)
archived → draft     (재검토)
```

---

### 4. GET /api/match/live

현재 설정된 라이브 경기 정보를 조회한다.

**Response** `200 OK`

```json
{
  "home_team": "LA Paz FC",
  "away_team": "Opponent FC",
  "match_date": "2026-03-06",
  "kickoff_time": "19:00",
  "status": "live",
  "current_minute": 45
}
```

| Field | Type | Description |
|-------|------|-------------|
| home_team | string | 홈팀 이름 |
| away_team | string | 원정팀 이름 |
| match_date | string | 경기 날짜 (YYYY-MM-DD) |
| kickoff_time | string | 킥오프 시간 (HH:MM) |
| status | string | `upcoming`, `live`, `finished` |
| current_minute | number \| null | 현재 경기 시간(분), live일 때만 존재 |

---

## 공통 사항

### 인증
- MVP 단계에서는 인증 없음 (내부 운영 도구)

### Content-Type
- 모든 요청/응답: `application/json`

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

### CORS
- 프론트엔드 개발 서버 허용: `http://localhost:3000`
