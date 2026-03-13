# La Paz Web MVP - TODO

> 기준 문서: `docs/MVP_SPEC_v1.md`
> 생성일: 2026-03-05
> 범위: Web MVP 4대 기능 (이적 루머 허브, 경기 분석, AI Q&A, 시뮬레이션)

---

## 의존성 그래프

```
[Architect] T-A1~A5 ──┬──→ [BE-Dev] T-B1~B8
                       ├──→ [FE-Dev] T-F1~F10
                       └──→ [AI-Eng] T-AI1~AI5

[Designer] T-D1~D3 ──────→ [FE-Dev] T-F1~F10

[BE-Dev] T-B1~B8 ────┬──→ [FE-Dev] T-F3~F10 (API 연동)
                      └──→ [QA-DevOps] T-Q1~Q5

[AI-Eng] T-AI1~AI5 ──────→ [FE-Dev] T-F7~F10 (AI 연동)

[QA-DevOps] T-Q1~Q5 ─────→ 릴리즈 게이트

[Security] T-S1~S4 ──────→ 릴리즈 게이트 (병렬)
```

---

## Architect 태스크

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-A1 | DB 스키마 확정: transfer_rumors, rumor_sources, simulations 신규 테이블 + fan_predictions 확장 DDL 작성 | P0 | - | `supabase/migrations/010_mvp_tables.sql` |
| T-A2 | Edge Functions API 인터페이스 계약서: 5개 함수의 Request/Response 스키마 (TypeScript types) | P0 | - | `docs/API_CONTRACT.md` + `types/api.ts` |
| T-A3 | Next.js 프로젝트 구조 확정: App Router 라우트 맵, 폴더 구조, 공유 타입 | P0 | - | `docs/FOLDER_STRUCTURE.md` |
| T-A4 | ISR/SSR/CSR 렌더링 전략 확정: 페이지별 렌더링 방식 + 캐시 TTL 매트릭스 | P0 | T-A3 | `docs/RENDERING_STRATEGY.md` |
| T-A5 | Supabase RLS 신규 테이블 정책 설계 | P1 | T-A1 | `supabase/migrations/011_mvp_rls.sql` |

---

## Designer 태스크

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-D1 | Design Token 확정: 색상 팔레트 (다크 테마 기본), 타이포그래피, spacing, border-radius | P0 | - | `design/tokens.json` + Tailwind config |
| T-D2 | 핵심 컴포넌트 스펙: 루머 카드, 경기 카드, 순위 테이블, 챗 버블, 시뮬레이션 폼 | P0 | T-D1 | `design/COMPONENT_SPEC.md` |
| T-D3 | 페이지 와이어프레임: 주요 10페이지 레이아웃 (모바일 + 데스크톱) | P0 | T-D1 | `design/wireframes/` |

---

## BE-Developer 태스크 (Supabase + Edge Functions)

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-B1 | Supabase 마이그레이션 실행: 신규 3테이블 + 확장 1테이블 | P0 | T-A1 | DB 적용 완료 |
| T-B2 | team_season_stats 데이터 채움: Agent 2 수집 파이프라인 수정/실행 | P0 | - | team_season_stats 행 > 0 |
| T-B3 | Edge Function: `search` — 시맨틱 검색 (pgvector + ILIKE 하이브리드) | P0 | T-A2 | `supabase/functions/search/` |
| T-B4 | Edge Function: `chat` — RAG 파이프라인 + SSE 스트리밍 | P0 | T-A2, T-AI1 | `supabase/functions/chat/` |
| T-B5 | Edge Function: `parse-rumors` — articles → transfer_rumors 엔티티 추출 | P0 | T-A2, T-B1 | `supabase/functions/parse-rumors/` |
| T-B6 | Edge Function: `simulate-transfer` — 이적 시뮬레이션 | P1 | T-A2, T-AI2 | `supabase/functions/simulate-transfer/` |
| T-B7 | Edge Function: `simulate-match` — 경기 예측 | P1 | T-A2, T-AI3 | `supabase/functions/simulate-match/` |
| T-B8 | RLS 정책 적용: 신규 테이블 + 기존 테이블 보강 | P1 | T-A5, T-B1 | RLS 적용 완료 |

---

## FE-Developer 태스크 (Next.js 15)

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-F1 | Next.js 15 프로젝트 초기화: App Router, shadcn/ui, Tailwind, next-intl, Supabase 클라이언트 | P0 | T-A3, T-D1 | `frontend/` 프로젝트 |
| T-F2 | 공통 레이아웃: Header, Sidebar, Footer, 다크 테마 토글, 언어 전환 | P0 | T-D2 | 레이아웃 컴포넌트 |
| T-F3 | 경기 분석 페이지: `/matches`, `/matches/[id]` (ISR) | P0 | T-A4, T-D2, T-B2 | 경기 페이지 |
| T-F4 | 팀/선수 프로필: `/teams/[id]`, `/players/[id]` (ISR) | P0 | T-D2 | 프로필 페이지 |
| T-F5 | 리그 순위: `/standings`, `/standings/[competitionId]` (ISR) | P0 | T-D2, T-B2 | 순위 페이지 |
| T-F6 | 이적 루머 허브: `/transfers`, `/transfers/[id]` (ISR) | P0 | T-D2, T-B5 | 이적 페이지 |
| T-F7 | AI Q&A 챗: `/chat`, `/chat/[sessionId]` (CSR + SSE) | P0 | T-D2, T-B4, T-AI1 | 챗 페이지 |
| T-F8 | 이적 시뮬레이션: `/simulate/transfer` (CSR) | P1 | T-D2, T-B6, T-AI2 | 시뮬레이션 페이지 |
| T-F9 | 경기 예측: `/simulate/match` (CSR) | P1 | T-D2, T-B7, T-AI3 | 예측 페이지 |
| T-F10 | 인증 플로우: Supabase Auth 연동 (Google/GitHub 소셜 로그인) | P0 | T-A2 | 인증 컴포넌트 |

---

## AI-Engineer 태스크

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-AI1 | RAG 파이프라인 설계: Intent 분류 + Hybrid Search + Claude 생성 프롬프트 | P0 | T-A2 | `prompts/chat_system.md` + 타입 정의 |
| T-AI2 | 이적 시뮬레이션 프롬프트: Claude 구조화 출력 (team_strength_change, position_fit 등) | P0 | T-A2 | `prompts/simulate_transfer.md` + 타입 정의 |
| T-AI3 | 경기 예측 프롬프트: Claude 구조화 출력 (predicted_score, win_probability 등) | P1 | T-A2 | `prompts/simulate_match.md` + 타입 정의 |
| T-AI4 | 루머 파싱 프롬프트: articles → 엔티티 추출 (선수, 팀, 신뢰도, 상태) | P0 | T-A2 | `prompts/parse_rumors.md` + 타입 정의 |
| T-AI5 | Fallback 전략 구현: Claude → Gemini Flash 자동 전환 로직 | P0 | T-AI1 | fallback 유틸 모듈 |

---

## QA-DevOps 태스크

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-Q1 | CI 파이프라인: GitHub Actions (lint, typecheck, build, test) | P0 | T-F1 | `.github/workflows/ci.yml` |
| T-Q2 | E2E 테스트: Playwright 기반 주요 페이지 스모크 테스트 (10페이지) | P0 | T-F3~F9 | `tests/e2e/` |
| T-Q3 | Integration 테스트: Edge Function 5개 통합 테스트 | P0 | T-B3~B7 | `tests/integration/` |
| T-Q4 | 성능 테스트: Lighthouse CI (LCP < 2.5s, CLS < 0.1) | P1 | T-F1~F10 | 성능 리포트 |
| T-Q5 | 배포 파이프라인: Vercel 프리뷰/프로덕션 + Supabase Edge Function 배포 | P1 | T-Q1 | 배포 자동화 |

---

## Security-Developer 태스크

| ID | 태스크 | 우선순위 | 의존성 | 산출물 |
|----|--------|---------|--------|--------|
| T-S1 | RLS 정책 감사: 신규 3테이블 + 기존 31테이블 RLS 검증 | P0 | T-B1, T-B8 | 보안 감사 리포트 |
| T-S2 | Edge Function 보안 리뷰: 입력 검증, Rate Limiting, API 키 관리 | P0 | T-B3~B7 | 보안 리뷰 리포트 |
| T-S3 | 환경변수/시크릿 관리 검증: Supabase secrets, Vercel env, 키 로테이션 | P0 | - | 키 관리 체크리스트 |
| T-S4 | 데이터 스크래핑 법적 리스크 체크: 6개 데이터 소스 TOS 검토 | P1 | - | 법적 리스크 리포트 |

---

## 실행 순서 (권장)

### Wave 1: 설계 (병렬)
```
[Architect] T-A1, T-A2, T-A3, T-A4    ← 병렬
[Designer]  T-D1, T-D2, T-D3           ← 병렬
[AI-Eng]    T-AI1, T-AI2, T-AI4        ← 병렬
[Security]  T-S3, T-S4                 ← 병렬
```

### Wave 2: 기반 구축 (Architect 완료 후)
```
[BE-Dev]    T-B1, T-B2                  ← 순차
[FE-Dev]    T-F1, T-F2                  ← 순차
[QA-DevOps] T-Q1                        ← 단독
[Architect] T-A5                        ← T-A1 이후
```

### Wave 3: 핵심 구현 (병렬)
```
[BE-Dev]    T-B3, T-B4, T-B5           ← 병렬
[FE-Dev]    T-F3, T-F4, T-F5, T-F6    ← 병렬
[AI-Eng]    T-AI5                       ← T-AI1 이후
```

### Wave 4: AI 기능 구현
```
[FE-Dev]    T-F7 (챗), T-F10 (인증)    ← T-B4 이후
[BE-Dev]    T-B6, T-B7                  ← T-AI2, T-AI3 이후
[AI-Eng]    T-AI3                       ← 순차
```

### Wave 5: 시뮬레이션 + 마무리
```
[FE-Dev]    T-F8, T-F9                  ← T-B6, T-B7 이후
[BE-Dev]    T-B8                        ← T-A5 이후
[Security]  T-S1, T-S2                  ← T-B3~B7 이후
```

### Wave 6: 검증 + 릴리즈
```
[QA-DevOps] T-Q2, T-Q3, T-Q4, T-Q5    ← 구현 완료 후
[Security]  최종 감사                    ← 병렬
```

---

## 완료 기준 (전체 MVP)

- [ ] 4대 기능 모든 AC 통과
- [ ] E2E 테스트 10페이지 PASS
- [ ] Integration 테스트 5 Edge Functions PASS
- [ ] Lighthouse 성능 점수 > 90
- [ ] RLS 보안 감사 PASS
- [ ] 린트/타입체크 에러 0건
- [ ] 인공지능기본법 AI 고지 UI 포함
- [ ] ko/en 다국어 전환 정상 동작
- [ ] 다크 테마 전체 페이지 적용
