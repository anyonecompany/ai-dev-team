# La Paz Web MVP - 기획서 v1.0

> Version: 1.0.0
> Date: 2026-03-05
> Status: Confirmed
> Author: PM-Planner (Opus)
> Scope: Web MVP 4대 기능 정의 + Acceptance Criteria

---

## 1. 서비스 비전 & 포지셔닝

### 비전
**La Paz는 글로벌 축구 팬 인텔리전스 플랫폼이다.**
팬의 질의 데이터를 구조화하여 축적하고, 이를 기반으로 팬이 원하는 정보를 정확하게 전달한다.

### 포지셔닝
| 축 | La Paz | 경쟁자 (FotMob, SofaScore 등) |
|---|---|---|
| 핵심 가치 | AI 기반 자연어 Q&A + 구조화된 데이터 | 데이터 대시보드 |
| 차별점 | RAG 기반 소스 인용, 이적 시뮬레이션, 팬 수요 인텔리전스 | 통계 열람 |
| 수익 모델 | Phase 1 무료 → Phase 2 구독 → Phase 3 B2B 집계 | 프리미엄 구독/광고 |
| 타겟 | 축구에 대해 "궁금한 것을 물어보고 싶은" 팬 | 경기 실시간 추적 팬 |

### Phase 로드맵
- **Phase 1 (MVP)**: 무료 팬 서비스 — 사용자 확보 + 질의 데이터 축적
- Phase 2: 구독 확장 — 고급 분석, 알림, 개인화
- Phase 3: B2B 집계 상품화 — 익명화된 팬 수요 지표

---

## 2. MVP 범위

### 2.1 In-Scope (MVP에 포함)

| # | 기능 | 설명 |
|---|------|------|
| F1 | **이적 루머 허브** | 이적 루머 피드, 신뢰도 점수, 엔티티 파싱, 소스 추적 |
| F2 | **경기 분석** | 경기 결과/통계 뷰, 팀/선수 프로필, 리그 순위 |
| F3 | **AI Q&A** | RAG 기반 축구 챗봇, SSE 스트리밍, 소스 인용 |
| F4 | **시뮬레이션** | 이적 시뮬레이션, 경기 결과 예측 |
| NF | **비기능** | 인증, 다국어(ko/en), SEO, 모바일 반응형, 다크 테마 |

### 2.2 Out-of-Scope (MVP 이후)

| 항목 | 이유 | 예정 Phase |
|------|------|-----------|
| B2B API 엔드포인트 | 팬 데이터 축적 선행 필요 | Phase 3 |
| 푸시 알림 / 실시간 경기 알림 | Realtime 인프라 추가 필요 | Phase 2 |
| 소셜 기능 (댓글, 공유, 팔로우) | 커뮤니티 기능은 후순위 | Phase 2 |
| 커스텀 ML 모델 학습 | RAG + LLM API로 충분 | N/A |
| 네이티브 앱 (iOS/Android) | 웹 PWA로 대체 | Phase 3 |
| K리그 외 아시아 리그 확장 | Tier 1 데이터 완성 우선 | Phase 2 |
| 팬 수요 리포트 대시보드 | 내부 분석용만 우선 | Phase 2 |
| 결제 / 구독 시스템 | 무료 Phase | Phase 2 |

---

## 3. 기능별 상세 스펙

### 3.1 F1: 이적 루머 허브

#### 사용자 스토리

| ID | 스토리 | 우선순위 |
|----|--------|---------|
| F1-US1 | 팬으로서, 최신 이적 루머 목록을 시간순으로 볼 수 있다 | P0 |
| F1-US2 | 팬으로서, 각 루머의 신뢰도 점수(0~100)를 확인할 수 있다 | P0 |
| F1-US3 | 팬으로서, 루머를 선수/팀/리그별로 필터링할 수 있다 | P1 |
| F1-US4 | 팬으로서, 루머 상세에서 원본 소스 링크를 확인할 수 있다 | P0 |
| F1-US5 | 팬으로서, 특정 선수의 이적 히스토리와 현재 루머를 함께 볼 수 있다 | P1 |

#### 페이지 / 라우트

| 라우트 | 렌더링 | 설명 |
|--------|--------|------|
| `/transfers` | ISR (1h) | 이적 루머 피드 (리스트) |
| `/transfers/[id]` | ISR (1h) | 루머 상세 (소스, 타임라인, 신뢰도) |
| `/players/[id]/transfers` | SSR | 선수별 이적 히스토리 + 현재 루머 |

#### 핵심 데이터 모델

| 테이블 | 용도 | 상태 |
|--------|------|------|
| `transfers` | 확정 이적 기록 | 기존 (재사용) |
| `articles` | 루머 소스 기사 | 기존 (재사용) |
| `transfer_rumors` | **신규** — 루머 엔티티 (선수, 출발팀, 도착팀, 신뢰도, 소스, 상태) | 신규 생성 |
| `rumor_sources` | **신규** — 루머별 소스 추적 (기사 링크, 기자, 매체 신뢰 등급) | 신규 생성 |
| `players` | 선수 프로필 | 기존 (재사용) |
| `teams` | 팀 프로필 | 기존 (재사용) |

#### Acceptance Criteria

| ID | 조건 | 검증 방법 |
|----|------|----------|
| F1-AC1 | `/transfers` 페이지가 최소 10개 루머를 시간순으로 표시한다 | E2E: 페이지 로드 → 10개 이상 카드 렌더링 확인 |
| F1-AC2 | 각 루머 카드에 신뢰도 점수(0~100)가 시각적 게이지로 표시된다 | Visual: 게이지 컴포넌트 렌더링 확인 |
| F1-AC3 | 선수명/팀명 필터 적용 시 1초 이내 결과 갱신 | Performance: 필터 변경 후 응답 시간 < 1s |
| F1-AC4 | 루머 상세 페이지에서 원본 소스 URL이 외부 링크로 제공된다 | E2E: 링크 클릭 → 외부 사이트 이동 확인 |
| F1-AC5 | Edge Function이 articles 테이블에서 이적 관련 기사를 파싱하여 transfer_rumors에 엔티티를 추출/저장한다 | Integration: Edge Function 호출 → transfer_rumors 행 생성 확인 |

---

### 3.2 F2: 경기 분석

#### 사용자 스토리

| ID | 스토리 | 우선순위 |
|----|--------|---------|
| F2-US1 | 팬으로서, 리그별 최근 경기 결과를 볼 수 있다 | P0 |
| F2-US2 | 팬으로서, 경기 상세에서 스코어, 골 기록, 주요 이벤트를 확인할 수 있다 | P0 |
| F2-US3 | 팬으로서, 팀 프로필에서 시즌 통계와 최근 폼을 확인할 수 있다 | P0 |
| F2-US4 | 팬으로서, 선수 프로필에서 시즌별 골/어시스트/xG를 확인할 수 있다 | P0 |
| F2-US5 | 팬으로서, 리그 순위표를 실시간으로 확인할 수 있다 | P0 |

#### 페이지 / 라우트

| 라우트 | 렌더링 | 설명 |
|--------|--------|------|
| `/matches` | ISR (5m) | 경기 목록 (날짜/리그 필터) |
| `/matches/[id]` | ISR (5m) | 경기 상세 (스코어, 이벤트, 통계) |
| `/teams` | ISR (1h) | 팀 목록 |
| `/teams/[id]` | ISR (30m) | 팀 프로필 (시즌 통계, 최근 경기, 스쿼드) |
| `/players/[id]` | ISR (30m) | 선수 프로필 (시즌 통계, 최근 경기) |
| `/standings` | ISR (1h) | 리그 순위표 |
| `/standings/[competitionId]` | ISR (1h) | 특정 리그 순위 상세 |

#### 핵심 데이터 모델

| 테이블 | 용도 | 상태 |
|--------|------|------|
| `competitions` | 리그/대회 정보 | 기존 (재사용) |
| `seasons` | 시즌 정보 | 기존 (재사용) |
| `teams` | 팀 프로필 | 기존 (재사용) |
| `players` | 선수 프로필 | 기존 (재사용) |
| `matches` | 경기 일정/결과 | 기존 (재사용) |
| `match_events` | 경기 이벤트 (골, 카드 등) | 기존 (재사용) |
| `lineups` | 라인업 | 기존 (재사용) |
| `player_season_stats` | 선수 시즌 통계 | 기존 (재사용) |
| `team_season_stats` | 팀 시즌 통계 (순위) | 기존 (재사용, 데이터 채움 필요) |
| `player_match_stats` | 선수 경기별 통계 | 기존 (재사용) |
| `team_match_stats` | 팀 경기별 통계 | 기존 (재사용) |
| `formations` | 포메이션 | 기존 (재사용) |

#### Acceptance Criteria

| ID | 조건 | 검증 방법 |
|----|------|----------|
| F2-AC1 | `/matches` 페이지가 5대 리그 경기를 날짜별로 그룹핑하여 표시한다 | E2E: 리그 필터 5개 전환 + 날짜 그룹 확인 |
| F2-AC2 | `/matches/[id]` 상세에서 스코어, 골 이벤트, 카드가 타임라인으로 표시된다 | E2E: 이벤트 타임라인 렌더링 확인 |
| F2-AC3 | `/teams/[id]` 에서 시즌 순위, 승/무/패, 득실차가 표시된다 | E2E: team_season_stats 데이터 표시 확인 |
| F2-AC4 | `/players/[id]` 에서 시즌별 골/어시스트/xG 차트가 렌더링된다 | E2E: 차트 컴포넌트 렌더링 확인 |
| F2-AC5 | `/standings` 에서 5대 리그 순위표가 정확한 순위로 표시된다 | E2E: 순위 1위~하위 순서 정렬 확인 |
| F2-AC6 | 모든 경기 분석 페이지의 ISR 캐시가 정상 동작한다 (stale 시 백그라운드 재생성) | Integration: 캐시 TTL 확인 |

---

### 3.3 F3: AI Q&A

#### 사용자 스토리

| ID | 스토리 | 우선순위 |
|----|--------|---------|
| F3-US1 | 팬으로서, 자연어로 축구 관련 질문을 하고 AI 답변을 받을 수 있다 | P0 |
| F3-US2 | 팬으로서, AI 답변이 실시간 스트리밍(SSE)으로 표시된다 | P0 |
| F3-US3 | 팬으로서, AI 답변에 인용된 소스(기사, 통계 등)를 확인할 수 있다 | P0 |
| F3-US4 | 팬으로서, 이전 대화 기록을 세션 단위로 다시 볼 수 있다 | P1 |
| F3-US5 | 팬으로서, 한국어와 영어 모두로 질문할 수 있다 | P0 |

#### 페이지 / 라우트

| 라우트 | 렌더링 | 설명 |
|--------|--------|------|
| `/chat` | CSR | AI 챗봇 메인 (새 대화) |
| `/chat/[sessionId]` | CSR | 기존 대화 이어가기 |

#### 핵심 데이터 모델

| 테이블 | 용도 | 상태 |
|--------|------|------|
| `chat_sessions` | 대화 세션 | 기존 (재사용) |
| `chat_messages` | 대화 메시지 | 기존 (재사용) |
| `documents` | RAG 벡터 문서 (384-dim pgvector) | 기존 (재사용) |
| `query_logs` | 질의 로깅 (intent, entities) | 기존 phase1 스키마 (재사용) |
| `fan_events` | 팬 행동 로깅 | 기존 (재사용) |

#### RAG 파이프라인 (Edge Function)

```
User Query (ko/en)
→ 언어 감지 + 한→영 번역 (엔티티 매핑)
→ Intent 분류 (Claude API structured output)
→ Hybrid Search:
    1. 엔티티 직접 조회 (SQL)
    2. pgvector 코사인 유사도
    3. 키워드 폴백 (ILIKE)
→ Context 랭킹
→ Claude API 생성 (SSE 스트리밍)
→ 소스 인용 첨부
→ query_logs 비동기 저장
```

#### Acceptance Criteria

| ID | 조건 | 검증 방법 |
|----|------|----------|
| F3-AC1 | `/chat` 에서 질문 입력 후 3초 이내에 첫 토큰이 스트리밍된다 | Performance: TTFT < 3s |
| F3-AC2 | AI 응답에 최소 1개 소스가 인용된다 (소스 없는 경우 "소스 없음" 명시) | E2E: 소스 카드/링크 렌더링 확인 |
| F3-AC3 | 한국어 질문 "손흥민 이번 시즌 골 수"에 대해 통계 기반 답변이 반환된다 | Integration: 응답에 숫자 통계 포함 확인 |
| F3-AC4 | SSE 스트리밍이 중단 없이 완료된다 (네트워크 에러 시 재시도 UI 표시) | E2E: 전체 응답 수신 완료 확인 |
| F3-AC5 | 대화 기록이 chat_sessions/chat_messages에 저장되고, `/chat/[sessionId]`에서 복원된다 | Integration: 세션 생성 → 재방문 → 메시지 표시 확인 |
| F3-AC6 | 환각 방지: 데이터 없는 질문에 "해당 데이터가 없습니다" 응답이 반환된다 | Integration: 존재하지 않는 선수 질문 → 데이터 없음 응답 확인 |
| F3-AC7 | Gemini Flash fallback: Claude API 실패 시 Gemini로 자동 전환된다 | Integration: Claude mock 실패 → Gemini 응답 확인 |

---

### 3.4 F4: 시뮬레이션

#### 사용자 스토리

| ID | 스토리 | 우선순위 |
|----|--------|---------|
| F4-US1 | 팬으로서, "선수 A가 팀 B로 이적하면?" 시뮬레이션을 실행할 수 있다 | P0 |
| F4-US2 | 팬으로서, 시뮬레이션 결과로 팀 전력 변화, 포메이션 영향 등을 확인할 수 있다 | P0 |
| F4-US3 | 팬으로서, 두 팀 간 경기 결과를 예측할 수 있다 | P1 |
| F4-US4 | 팬으로서, 다른 팬들의 예측과 내 예측을 비교할 수 있다 | P1 |
| F4-US5 | 팬으로서, 시뮬레이션 결과를 공유할 수 있다 (URL 복사) | P2 |

#### 페이지 / 라우트

| 라우트 | 렌더링 | 설명 |
|--------|--------|------|
| `/simulate/transfer` | CSR | 이적 시뮬레이션 (선수+팀 선택 → AI 분석) |
| `/simulate/match` | CSR | 경기 예측 (홈팀+어웨이팀 선택 → AI 분석) |
| `/simulate/results/[id]` | SSR | 시뮬레이션 결과 공유 페이지 |

#### 핵심 데이터 모델

| 테이블 | 용도 | 상태 |
|--------|------|------|
| `simulations` | **신규** — 시뮬레이션 요청/결과 저장 (type, params, result, user_id) | 신규 생성 |
| `fan_predictions` | 팬 경기 예측 | 기존 (재사용, 스키마 확장) |
| `players` | 선수 데이터 (시뮬레이션 입력) | 기존 (재사용) |
| `teams` | 팀 데이터 (시뮬레이션 입력) | 기존 (재사용) |
| `player_season_stats` | 선수 성과 데이터 (시뮬레이션 입력) | 기존 (재사용) |
| `team_season_stats` | 팀 성과 데이터 (시뮬레이션 입력) | 기존 (재사용) |

#### 시뮬레이션 파이프라인 (Edge Function)

```
이적 시뮬레이션:
  Input: player_id + target_team_id
  → 선수 현재 통계 조회 (player_season_stats)
  → 타겟 팀 현재 스쿼드/통계 조회
  → Claude API 구조화 출력: {
      team_strength_change, formation_impact,
      position_fit, salary_feasibility, overall_rating
    }
  → 결과 저장 (simulations 테이블)
  → SSE 스트리밍 응답

경기 예측:
  Input: home_team_id + away_team_id
  → 양팀 시즌 통계, 최근 5경기 폼, 상대 전적 조회
  → Claude API 구조화 출력: {
      predicted_score, win_probability,
      key_factors, head_to_head_analysis
    }
  → 결과 저장 + 팬 예측 집계 표시
```

#### Acceptance Criteria

| ID | 조건 | 검증 방법 |
|----|------|----------|
| F4-AC1 | 이적 시뮬레이션: 선수/팀 선택 후 10초 이내에 분석 결과가 표시된다 | Performance: 응답 시간 < 10s |
| F4-AC2 | 시뮬레이션 결과에 팀 전력 변화 점수, 포지션 적합도, 포메이션 영향이 포함된다 | E2E: 3개 섹션 렌더링 확인 |
| F4-AC3 | 경기 예측: 양팀 선택 후 승률(%)과 예상 스코어가 표시된다 | E2E: 승률 + 스코어 표시 확인 |
| F4-AC4 | 시뮬레이션 결과가 simulations 테이블에 저장되고, `/simulate/results/[id]`에서 조회 가능하다 | Integration: DB 저장 + URL 접근 확인 |
| F4-AC5 | 로그인 없이도 시뮬레이션을 실행할 수 있다 (비로그인 사용자는 일 5회 제한) | E2E: 비로그인 실행 + 6회째 제한 메시지 확인 |

---

## 4. 비기능 요구사항

### 4.1 성능

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| LCP (Largest Contentful Paint) | < 2.5s | Lighthouse |
| FID (First Input Delay) | < 100ms | Lighthouse |
| CLS (Cumulative Layout Shift) | < 0.1 | Lighthouse |
| TTFB (Time to First Byte) | < 500ms | Edge 배포 기준 |
| AI 응답 TTFT | < 3s | SSE 첫 토큰 측정 |
| API 응답 (비 AI) | < 500ms (p95) | Supabase 쿼리 기준 |

### 4.2 SEO

| 항목 | 적용 |
|------|------|
| 메타 태그 | 모든 페이지에 title, description, og:image 동적 생성 |
| 구조화 데이터 | 경기 결과: SportsEvent schema, 팀: SportsTeam schema |
| 사이트맵 | `/sitemap.xml` 자동 생성 (ISR 페이지 기준) |
| robots.txt | `/chat`, `/simulate` 제외 (CSR, 동적 콘텐츠) |
| SSR/ISR | 콘텐츠 페이지 전부 서버 렌더링 (크롤러 접근 가능) |

### 4.3 다국어 (i18n)

| 항목 | 적용 |
|------|------|
| 지원 언어 | 한국어 (ko, 기본), English (en) |
| 라우트 | `/ko/...`, `/en/...` (Next.js i18n routing) |
| 엔티티 별칭 | teams.aliases, players.name (canonical + 다국어 별칭 jsonb) |
| UI 텍스트 | next-intl 또는 유사 라이브러리 |
| AI 응답 | 사용자 locale에 맞춰 응답 언어 자동 설정 |

### 4.4 접근성 (a11y)

| 항목 | 기준 |
|------|------|
| WCAG | 2.1 Level AA |
| 키보드 네비게이션 | 모든 인터랙티브 요소 접근 가능 |
| 스크린 리더 | 시맨틱 HTML + aria-label |
| 색상 대비 | 4.5:1 이상 (다크 테마 포함) |

### 4.5 보안

| 항목 | 적용 |
|------|------|
| 인증 | Supabase Auth (Google/GitHub 소셜 로그인) |
| RLS | 모든 테이블에 Row Level Security 적용 (기존 정책 유지) |
| API 키 | 환경변수로만 관리 (Edge Function secrets) |
| Rate Limiting | 비로그인: 분당 10회, 로그인: 분당 30회 (AI 엔드포인트) |
| CORS | 허용 도메인만 설정 |
| 입력 검증 | Zod 스키마 검증 (프론트), Edge Function 입력 검증 |

### 4.6 인공지능기본법 준수

| 항목 | 적용 |
|------|------|
| AI 사용 고지 | 모든 AI 응답 영역에 "AI가 생성한 답변입니다" 라벨 표시 |
| 소스 인용 | AI 응답에 근거 출처 명시 |
| 한계 명시 | "AI 응답은 부정확할 수 있습니다" 면책 조항 |
| 데이터 처리 고지 | 개인정보 처리 방침에 AI 질의 데이터 활용 명시 |

---

## 5. 기술 제약 사항

### 5.1 기술 스택 (확정)

| 레이어 | 기술 | 비고 |
|--------|------|------|
| Frontend | Next.js 15 (App Router) | SSR/ISR/CSR 혼합 |
| UI | shadcn/ui + Tailwind CSS | 다크 테마 기본 |
| Backend | Supabase (Postgres + pgvector + RLS + Realtime) | 기존 31테이블 기반 |
| Serverless | Supabase Edge Functions (Deno) | API 로직 + AI 호출 |
| AI (Primary) | Claude API | RAG 생성, 시뮬레이션 |
| AI (Fallback) | Gemini Flash | Claude 실패 시 자동 전환 |
| 인증 | Supabase Auth | 소셜 로그인 (Google, GitHub) |
| 배포 | Vercel | Edge Runtime, ISR |
| 모니터링 | Vercel Analytics + Supabase Dashboard | |

### 5.2 기존 Python 에이전트와의 관계

| 에이전트 | MVP에서의 역할 | 비고 |
|---------|-------------|------|
| Agent 1 (Structure) | **유지** — 데이터 수집 파이프라인으로 계속 사용 | cron/수동 실행 |
| Agent 2 (Match) | **유지** — 경기/통계 데이터 수집 | cron/수동 실행 |
| Agent 3 (Narrative) | **유지** — 이적/부상/뉴스 수집 | cron/수동 실행 |
| Agent 4 (Document) | **유지** — RAG 문서 생성 + 임베딩 | cron/수동 실행 |
| Agent 5 (API) | **대체** — Edge Functions로 이관 | FastAPI → Edge Function |

### 5.3 데이터베이스 변경 사항

| 구분 | 테이블 | 변경 |
|------|--------|------|
| **재사용** | 31개 기존 테이블 전부 | 스키마 변경 없음 |
| **데이터 채움** | `team_season_stats` | 현재 0행 → Agent 2에서 수집 필요 |
| **신규** | `transfer_rumors` | 이적 루머 엔티티 (F1) |
| **신규** | `rumor_sources` | 루머 소스 추적 (F1) |
| **신규** | `simulations` | 시뮬레이션 결과 저장 (F4) |
| **확장** | `fan_predictions` | `ai_prediction` jsonb 컬럼 추가 (F4) |

### 5.4 Edge Functions 목록 (예정)

| Function | 용도 | 기능 |
|----------|------|------|
| `chat` | AI Q&A | RAG 파이프라인 + SSE 스트리밍 |
| `simulate-transfer` | 이적 시뮬레이션 | 선수/팀 데이터 → Claude 분석 |
| `simulate-match` | 경기 예측 | 양팀 통계 → Claude 분석 |
| `parse-rumors` | 루머 파싱 | articles → transfer_rumors 엔티티 추출 |
| `search` | 시맨틱 검색 | pgvector + 키워드 하이브리드 |

---

## 6. MVP 이후 로드맵

### Phase 2 (구독 확장)

| 기능 | 설명 |
|------|------|
| 알림 시스템 | 관심 선수/팀 이적 루머 실시간 알림 (Supabase Realtime) |
| 개인화 피드 | 팬 행동 기반 맞춤 콘텐츠 |
| 고급 분석 | xG 타임라인, 패스 네트워크, 히트맵 시각화 |
| 구독 결제 | Stripe 연동 프리미엄 플랜 |
| K리그 확장 | API-Football 기반 K리그 전체 데이터 |
| 소셜 기능 | 댓글, 공유, 팔로우 |

### Phase 3 (B2B)

| 기능 | 설명 |
|------|------|
| B2B 대시보드 | 팬 수요 인텔리전스 대시보드 |
| API 상품화 | 트렌드, 세그먼트, 엔티티 버즈 API |
| demand_signals 집계 | query_logs 기반 수요 신호 자동 집계 |
| 데이터 내보내기 | CSV/JSON 리포트 다운로드 |

---

## 7. 기존 31 테이블 관계 정리

### 재사용 (변경 없음) — 31개

| 도메인 | 테이블 | MVP 기능에서 사용 |
|--------|--------|------------------|
| Structure | competitions, seasons, teams, players, managers, team_seasons, player_contracts, manager_tenures | F2, F3, F4 |
| Match | matches, lineups, match_events | F2, F3 |
| Performance | player_match_stats, player_season_stats, team_match_stats, team_season_stats | F2, F3, F4 |
| Narrative | transfers, injuries, articles | F1, F2, F3 |
| Tactics | formations | F2 |
| RAG | documents | F3 |
| Fan Engagement | users, chat_sessions, chat_messages, fan_events, fan_predictions | F3, F4 |
| B2B | trend_snapshots, fan_segments, b2b_clients, b2b_api_logs | (Phase 3) |
| Pipeline | agent_status, pipeline_runs | 백그라운드 |

### 신규 생성 — 3개

| 테이블 | 기능 | 주요 컬럼 |
|--------|------|----------|
| `transfer_rumors` | F1 | id, player_id, from_team_id, to_team_id, confidence_score (0-100), status (rumor/confirmed/denied), first_reported_at, last_updated_at, meta |
| `rumor_sources` | F1 | id, rumor_id (FK), source_name, source_url, journalist, reliability_tier (1-5), published_at |
| `simulations` | F4 | id, user_id, sim_type (transfer/match), params (jsonb), result (jsonb), model_used, latency_ms, created_at |

### 스키마 확장 — 1개

| 테이블 | 변경 | 이유 |
|--------|------|------|
| `fan_predictions` | `ai_prediction jsonb` 컬럼 추가 | AI 예측 결과와 팬 예측 비교를 위해 |

---

*이 문서는 이후 모든 에이전트(Architect, Designer, BE, FE, AI, QA, Security)의 단일 소스입니다.*
*MVP 범위 변경 시 이 문서를 먼저 업데이트하고, TODO.md에 반영합니다.*
