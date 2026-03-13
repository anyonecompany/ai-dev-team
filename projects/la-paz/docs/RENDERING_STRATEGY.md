# Rendering Strategy — 페이지별 렌더링 방식 + 캐시 TTL

> Version: 1.0.0
> Date: 2026-03-05
> Author: Architect
> 기준: MVP_SPEC_v1.md §4.1 (성능), §4.2 (SEO)
> 프레임워크: Next.js 15 App Router

---

## 렌더링 방식 정의

| 방식 | Next.js 구현 | 설명 |
|------|-------------|------|
| **ISR** | `export const revalidate = N` | 정적 생성 + 백그라운드 재검증. 첫 요청은 빌드 시 생성, 이후 TTL 만료 시 백그라운드 재생성 |
| **SSR** | `export const dynamic = 'force-dynamic'` | 매 요청마다 서버에서 렌더링. 항상 최신 데이터 |
| **CSR** | `'use client'` + `useEffect` | 클라이언트에서 렌더링. 서버 컴포넌트 셸 + 클라이언트 데이터 페칭 |

---

## 페이지별 렌더링 매트릭스

### F1: 이적 루머 허브

| 라우트 | 방식 | TTL | 이유 | SEO |
|--------|------|-----|------|-----|
| `/transfers` | ISR | 1h (3600s) | 루머 업데이트 빈도가 낮음 (시간 단위). 높은 트래픽 예상 페이지이므로 정적 캐시 유리 | O — 메타 태그, OG |
| `/transfers/[id]` | ISR | 1h (3600s) | 개별 루머의 status/confidence 변경도 시간 단위. On-demand revalidation으로 즉시 갱신 가능 | O — 구조화 데이터 (NewsArticle) |
| `/players/[id]/transfers` | SSR | N/A | 선수 이적 히스토리 + 현재 루머 결합. 데이터 신선도 중요. 트래픽 낮음 | O — 동적 메타 |

### F2: 경기 분석

| 라우트 | 방식 | TTL | 이유 | SEO |
|--------|------|-----|------|-----|
| `/matches` | ISR | 5m (300s) | 경기 결과가 자주 업데이트됨. 경기 당일에는 실시간에 가까운 갱신 필요 | O — SportsEvent schema |
| `/matches/[id]` | ISR | 5m (300s) | 경기 상세 (스코어, 이벤트). 경기 중/직후 빈번한 업데이트 | O — SportsEvent schema |
| `/teams` | ISR | 1h (3600s) | 팀 목록은 시즌 중 거의 변하지 않음 | O — 메타 태그 |
| `/teams/[id]` | ISR | 30m (1800s) | 팀 통계는 경기 후 변동. 일 평균 2~3회 갱신 충분 | O — SportsTeam schema |
| `/players/[id]` | ISR | 30m (1800s) | 선수 통계도 경기 후 변동 | O — Person schema |
| `/standings` | ISR | 1h (3600s) | 순위는 경기 종료 후에만 변동. 일 1~2회 갱신 충분 | O — 메타 태그 |
| `/standings/[competitionId]` | ISR | 1h (3600s) | 특정 리그 순위도 동일 패턴 | O — 메타 태그 |

### F3: AI Q&A

| 라우트 | 방식 | TTL | 이유 | SEO |
|--------|------|-----|------|-----|
| `/chat` | CSR | N/A | 실시간 인터랙션 (SSE 스트리밍). 사용자별 동적 콘텐츠. 검색 엔진에 노출 불필요 | X — robots.txt 제외 |
| `/chat/[sessionId]` | CSR | N/A | 개인 대화 기록. 인증 필요 | X — robots.txt 제외 |

### F4: 시뮬레이션

| 라우트 | 방식 | TTL | 이유 | SEO |
|--------|------|-----|------|-----|
| `/simulate/transfer` | CSR | N/A | 사용자 입력 기반 동적 콘텐츠. SSE 스트리밍 | X — robots.txt 제외 |
| `/simulate/match` | CSR | N/A | 사용자 입력 기반 동적 콘텐츠. SSE 스트리밍 | X — robots.txt 제외 |
| `/simulate/results/[id]` | SSR | N/A | 공유용 URL. 매 요청 시 DB에서 최신 결과 조회. SEO 가치 있음 | O — 동적 메타, OG |

### 기타

| 라우트 | 방식 | TTL | 이유 | SEO |
|--------|------|-----|------|-----|
| `/` (홈) | ISR | 30m (1800s) | 최신 루머 + 인기 경기 집합. 적당한 신선도 | O — 메타 태그 |
| `/login` | CSR | N/A | 인증 UI | X |
| `/callback` | CSR | N/A | OAuth 콜백 처리 | X |

---

## On-Demand Revalidation

ISR 페이지는 TTL 외에 즉시 갱신이 필요한 경우 On-Demand Revalidation 사용:

### 트리거 엔드포인트
```
POST /api/revalidate
Authorization: Bearer <REVALIDATE_SECRET>
Content-Type: application/json

{
  "paths": ["/transfers", "/transfers/<id>"],
  "tags": ["transfers"]        // 또는 tag 기반 revalidation
}
```

### 트리거 시나리오

| 이벤트 | 갱신 대상 | 트리거 |
|--------|----------|--------|
| parse-rumors 실행 완료 | `/transfers`, 관련 `/transfers/[id]` | Edge Function에서 revalidate 호출 |
| 경기 결과 업데이트 | `/matches`, `/matches/[id]`, `/standings` | Agent 2 수집 완료 시 웹훅 |
| 선수 통계 업데이트 | `/players/[id]`, `/teams/[id]` | Agent 2 수집 완료 시 웹훅 |

---

## 캐시 계층

```
사용자 브라우저
  └── Vercel Edge Network (CDN)
        └── ISR 캐시 (TTL 기반)
              └── Next.js 서버 (SSR/ISR 재생성)
                    └── Supabase (PostgreSQL)
```

### Vercel 캐시 헤더

| 페이지 유형 | Cache-Control |
|-------------|---------------|
| ISR | `s-maxage=<TTL>, stale-while-revalidate=<TTL*2>` |
| SSR | `no-cache, no-store` |
| CSR (셸) | `s-maxage=31536000` (정적 셸은 영구 캐시) |
| 정적 에셋 | `public, max-age=31536000, immutable` |

---

## 성능 목표 달성 전략

| 지표 | 목표 | 전략 |
|------|------|------|
| LCP < 2.5s | ISR 페이지: Vercel Edge에서 즉시 서빙. CSR 페이지: 셸 즉시 렌더 + 데이터 로딩 스켈레톤 |
| FID < 100ms | JS 번들 최소화. shadcn/ui 트리 셰이킹. 동적 import로 코드 스플리팅 |
| CLS < 0.1 | 이미지/카드에 고정 크기. 스켈레톤 레이아웃과 실제 레이아웃 일치 |
| TTFB < 500ms | Vercel Edge Runtime. Supabase 리전 일치 (ap-northeast-2 / 서울) |
| AI TTFT < 3s | Edge Function에서 SSE 즉시 시작. Claude 스트리밍 모드 사용 |
