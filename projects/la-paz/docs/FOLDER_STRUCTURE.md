# Folder Structure — Next.js 15 App Router

> Version: 1.0.0
> Date: 2026-03-05
> Author: Architect
> 기준: MVP_SPEC_v1.md

---

## 프로젝트 루트

```
frontend/
├── app/
│   ├── (main)/                     ← 메인 레이아웃 그룹
│   │   ├── layout.tsx              ← Header + Sidebar + Footer
│   │   ├── page.tsx                ← / 홈 (리그 오버뷰, 최신 루머, 인기 경기)
│   │   ├── transfers/
│   │   │   ├── page.tsx            ← /transfers — 이적 루머 피드 (ISR 1h)
│   │   │   └── [id]/
│   │   │       └── page.tsx        ← /transfers/[id] — 루머 상세 (ISR 1h)
│   │   ├── matches/
│   │   │   ├── page.tsx            ← /matches — 경기 목록 (ISR 5m)
│   │   │   └── [id]/
│   │   │       └── page.tsx        ← /matches/[id] — 경기 상세 (ISR 5m)
│   │   ├── teams/
│   │   │   ├── page.tsx            ← /teams — 팀 목록 (ISR 1h)
│   │   │   └── [id]/
│   │   │       └── page.tsx        ← /teams/[id] — 팀 프로필 (ISR 30m)
│   │   ├── players/
│   │   │   └── [id]/
│   │   │       ├── page.tsx        ← /players/[id] — 선수 프로필 (ISR 30m)
│   │   │       └── transfers/
│   │   │           └── page.tsx    ← /players/[id]/transfers — 선수 이적 히스토리 (SSR)
│   │   ├── standings/
│   │   │   ├── page.tsx            ← /standings — 전체 리그 순위 (ISR 1h)
│   │   │   └── [competitionId]/
│   │   │       └── page.tsx        ← /standings/[competitionId] — 리그 상세 순위 (ISR 1h)
│   │   ├── chat/
│   │   │   ├── page.tsx            ← /chat — AI Q&A 새 대화 (CSR)
│   │   │   └── [sessionId]/
│   │   │       └── page.tsx        ← /chat/[sessionId] — 대화 이어가기 (CSR)
│   │   └── simulate/
│   │       ├── transfer/
│   │       │   └── page.tsx        ← /simulate/transfer — 이적 시뮬레이션 (CSR)
│   │       ├── match/
│   │       │   └── page.tsx        ← /simulate/match — 경기 예측 (CSR)
│   │       └── results/
│   │           └── [id]/
│   │               └── page.tsx    ← /simulate/results/[id] — 결과 공유 (SSR)
│   ├── (auth)/                     ← 인증 레이아웃 그룹
│   │   ├── layout.tsx              ← 인증 전용 레이아웃 (미니멀)
│   │   ├── login/
│   │   │   └── page.tsx            ← /login — 소셜 로그인 (Google, GitHub)
│   │   └── callback/
│   │       └── page.tsx            ← /callback — OAuth 콜백 처리
│   ├── api/                        ← Route Handlers (필요 시)
│   │   └── revalidate/
│   │       └── route.ts            ← ISR On-Demand Revalidation 웹훅
│   ├── sitemap.ts                  ← 동적 사이트맵 생성
│   ├── robots.ts                   ← robots.txt 생성
│   ├── layout.tsx                  ← Root Layout (html, body, Providers)
│   ├── globals.css                 ← Tailwind 글로벌 스타일
│   ├── not-found.tsx               ← 404 페이지
│   └── error.tsx                   ← 글로벌 에러 바운더리
├── components/
│   ├── ui/                         ← shadcn/ui 컴포넌트 (Button, Card, Dialog 등)
│   ├── transfers/                  ← 이적 루머 관련
│   │   ├── RumorCard.tsx           ← 루머 카드 (신뢰도 게이지 포함)
│   │   ├── RumorList.tsx           ← 루머 피드 리스트
│   │   ├── RumorDetail.tsx         ← 루머 상세 뷰
│   │   ├── RumorFilter.tsx         ← 선수/팀/리그 필터
│   │   └── ConfidenceGauge.tsx     ← 신뢰도 시각적 게이지
│   ├── matches/                    ← 경기 관련
│   │   ├── MatchCard.tsx           ← 경기 카드 (스코어, 팀 로고)
│   │   ├── MatchList.tsx           ← 날짜/리그별 그룹핑 리스트
│   │   ├── MatchDetail.tsx         ← 경기 상세 (타임라인, 통계)
│   │   ├── EventTimeline.tsx       ← 골/카드 타임라인
│   │   └── MatchStats.tsx          ← 팀 통계 비교 바
│   ├── teams/                      ← 팀 관련
│   │   ├── TeamCard.tsx
│   │   ├── TeamProfile.tsx
│   │   ├── SquadList.tsx
│   │   └── SeasonStatsTable.tsx
│   ├── players/                    ← 선수 관련
│   │   ├── PlayerCard.tsx
│   │   ├── PlayerProfile.tsx
│   │   └── StatsChart.tsx          ← 시즌별 골/어시스트/xG 차트
│   ├── standings/                  ← 순위 관련
│   │   ├── StandingsTable.tsx      ← 리그 순위 테이블
│   │   └── LeagueSelector.tsx      ← 리그 선택 탭
│   ├── chat/                       ← AI Q&A 관련
│   │   ├── ChatInput.tsx           ← 질문 입력 폼
│   │   ├── ChatBubble.tsx          ← 메시지 버블 (user/assistant)
│   │   ├── ChatStream.tsx          ← SSE 스트리밍 렌더러
│   │   ├── SourceCard.tsx          ← 인용 소스 카드
│   │   └── SessionList.tsx         ← 이전 대화 목록
│   ├── simulate/                   ← 시뮬레이션 관련
│   │   ├── TransferSimForm.tsx     ← 이적 시뮬레이션 입력 폼
│   │   ├── TransferSimResult.tsx   ← 이적 시뮬레이션 결과 뷰
│   │   ├── MatchSimForm.tsx        ← 경기 예측 입력 폼
│   │   ├── MatchSimResult.tsx      ← 경기 예측 결과 뷰
│   │   └── SimulationStream.tsx    ← SSE 스트리밍 공통 렌더러
│   └── shared/                     ← 공통 컴포넌트
│       ├── Header.tsx              ← 글로벌 헤더 (네비, 검색, 테마/언어 토글)
│       ├── Footer.tsx              ← 글로벌 푸터
│       ├── Sidebar.tsx             ← 모바일 사이드바 네비게이션
│       ├── ThemeToggle.tsx         ← 다크/라이트 테마 토글
│       ├── LocaleSwitch.tsx        ← 언어 전환 (ko/en)
│       ├── SearchBar.tsx           ← 글로벌 검색 (search Edge Function 연동)
│       ├── AiDisclaimer.tsx        ← AI 사용 고지 라벨 (인공지능기본법)
│       ├── LoadingSkeleton.tsx     ← 공통 로딩 스켈레톤
│       └── ErrorFallback.tsx       ← 공통 에러 UI
├── lib/
│   ├── supabase/
│   │   ├── client.ts               ← 브라우저 Supabase 클라이언트
│   │   ├── server.ts               ← 서버 컴포넌트용 Supabase 클라이언트
│   │   └── middleware.ts            ← Supabase Auth 미들웨어 헬퍼
│   ├── hooks/
│   │   ├── useChat.ts              ← AI Q&A SSE 훅
│   │   ├── useSimulation.ts        ← 시뮬레이션 SSE 훅
│   │   ├── useSearch.ts            ← 검색 훅
│   │   └── useAuth.ts              ← 인증 상태 훅
│   ├── utils/
│   │   ├── formatters.ts           ← 날짜, 숫자, 점수 포매터
│   │   ├── sse.ts                  ← SSE 파싱 유틸
│   │   └── seo.ts                  ← 메타 태그/구조화 데이터 생성
│   └── types/
│       ├── api.ts                  ← Edge Function Request/Response 타입 (API_CONTRACT.md 동기화)
│       ├── database.ts             ← Supabase 생성 타입 (supabase gen types)
│       └── common.ts               ← 공유 유틸 타입
├── messages/                        ← next-intl 번역 파일
│   ├── ko.json                     ← 한국어 (기본)
│   └── en.json                     ← English
├── styles/
│   └── theme.css                   ← CSS 변수 (다크/라이트 테마)
├── public/
│   ├── icons/                      ← 팀 로고, 리그 아이콘
│   └── og/                         ← OG 이미지 템플릿
├── middleware.ts                    ← Next.js 미들웨어 (i18n, auth)
├── next.config.ts                  ← Next.js 설정
├── tailwind.config.ts              ← Tailwind 설정 (디자인 토큰 반영)
├── tsconfig.json
├── package.json
└── .env.local                      ← 환경변수 (NEXT_PUBLIC_SUPABASE_URL, ANON_KEY 등)
```

---

## Supabase Edge Functions

```
supabase/
├── functions/
│   ├── _shared/                    ← 공유 모듈
│   │   ├── types.ts                ← 공유 타입 (API_CONTRACT.md 동기화)
│   │   ├── supabase.ts             ← Supabase 클라이언트 초기화
│   │   ├── cors.ts                 ← CORS 헤더 유틸
│   │   ├── validate.ts             ← Zod 스키마 검증 유틸
│   │   ├── sse.ts                  ← SSE 응답 유틸
│   │   ├── rate-limit.ts           ← Rate Limiting 유틸
│   │   └── ai-client.ts            ← Claude + Gemini 클라이언트 (fallback 포함)
│   ├── chat/
│   │   └── index.ts                ← POST /functions/v1/chat
│   ├── search/
│   │   └── index.ts                ← POST /functions/v1/search
│   ├── parse-rumors/
│   │   └── index.ts                ← POST /functions/v1/parse-rumors
│   ├── simulate-transfer/
│   │   └── index.ts                ← POST /functions/v1/simulate-transfer
│   └── simulate-match/
│       └── index.ts                ← POST /functions/v1/simulate-match
├── migrations/
│   ├── 001_enable_rls_all_tables.sql
│   ├── 002_enable_rls_remaining_tables.sql
│   ├── 003_fix_search_path_warnings.sql
│   ├── 004_query_logs_and_rls.sql
│   ├── 005_demand_signals_and_rpc.sql
│   ├── 010_mvp_tables.sql          ← 신규: MVP 테이블
│   └── 011_mvp_rls.sql             ← 신규: MVP RLS 정책
├── schema.sql                       ← 기존 31 테이블 원본
└── config.toml                      ← Supabase 프로젝트 설정
```

---

## 라우트 → 파일 매핑 요약

| 라우트 | 파일 | 렌더링 |
|--------|------|--------|
| `/` | `app/(main)/page.tsx` | ISR 30m |
| `/transfers` | `app/(main)/transfers/page.tsx` | ISR 1h |
| `/transfers/[id]` | `app/(main)/transfers/[id]/page.tsx` | ISR 1h |
| `/matches` | `app/(main)/matches/page.tsx` | ISR 5m |
| `/matches/[id]` | `app/(main)/matches/[id]/page.tsx` | ISR 5m |
| `/teams` | `app/(main)/teams/page.tsx` | ISR 1h |
| `/teams/[id]` | `app/(main)/teams/[id]/page.tsx` | ISR 30m |
| `/players/[id]` | `app/(main)/players/[id]/page.tsx` | ISR 30m |
| `/players/[id]/transfers` | `app/(main)/players/[id]/transfers/page.tsx` | SSR |
| `/standings` | `app/(main)/standings/page.tsx` | ISR 1h |
| `/standings/[competitionId]` | `app/(main)/standings/[competitionId]/page.tsx` | ISR 1h |
| `/chat` | `app/(main)/chat/page.tsx` | CSR |
| `/chat/[sessionId]` | `app/(main)/chat/[sessionId]/page.tsx` | CSR |
| `/simulate/transfer` | `app/(main)/simulate/transfer/page.tsx` | CSR |
| `/simulate/match` | `app/(main)/simulate/match/page.tsx` | CSR |
| `/simulate/results/[id]` | `app/(main)/simulate/results/[id]/page.tsx` | SSR |
| `/login` | `app/(auth)/login/page.tsx` | CSR |
| `/callback` | `app/(auth)/callback/page.tsx` | CSR |
