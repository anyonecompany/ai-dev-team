# Portfiq Codemap
> 최종 갱신: 2026-03-23

## 아키텍처 개요

Portfiq는 AI 기반 ETF 브리핑 서비스다. Flutter 모바일 앱(Riverpod + GoRouter, Dark mode only)이 FastAPI 백엔드(Fly.io)를 호출하고, 백엔드는 Supabase(PostgreSQL)를 주 데이터 저장소로 사용한다. 뉴스 수집/번역/브리핑 생성은 APScheduler 백그라운드 잡으로 실행되며 Gemini API(gemini-2.5-flash-lite)로 요약/번역한다. 가격 데이터는 yfinance에서 가져오고 장중/장외 적응형 TTL로 캐싱한다. Next.js 어드민 대시보드(Vercel)는 Supabase Auth(Google OAuth)로 인증하며 DAU/퍼널/리텐션/푸시/배포를 관리한다. Supabase Edge Function(Deno)으로 뉴스 시그널 파이프라인도 운영한다.

---

## 디렉토리 맵

```
projects/portfiq/
├── apps/
│   ├── mobile/                          # Flutter 모바일 앱 (iOS/Android)
│   │   └── lib/
│   │       ├── main.dart                # 진입점 (production flavor)
│   │       ├── main_local.dart          # 진입점 (local flavor, localhost:8000)
│   │       ├── main_qa.dart             # 진입점 (qa flavor)
│   │       ├── main_production.dart     # 진입점 (production flavor, 중복)
│   │       ├── app.dart                 # PortfiqApp — MaterialApp.router + ProviderScope
│   │       ├── config/
│   │       │   ├── app_config.dart      # Flavor enum + API base URL 매핑
│   │       │   ├── constants.dart       # 앱 전역 상수
│   │       │   ├── router.dart          # GoRouter 라우트 정의 (splash→onboarding→home→etf detail→settings)
│   │       │   └── theme.dart           # PortfiqTheme — dark mode, Electric Indigo 액센트, Pretendard 폰트
│   │       ├── core/
│   │       │   ├── constants.dart       # 코어 상수
│   │       │   └── extensions.dart      # Dart 확장 메서드
│   │       ├── features/
│   │       │   ├── briefing/            # 브리핑 상세 + 공유카드 생성
│   │       │   │   ├── briefing_detail_screen.dart
│   │       │   │   ├── share_service.dart
│   │       │   │   └── widgets/share_card.dart
│   │       │   ├── calendar/            # 경제 이벤트 캘린더 (Finnhub)
│   │       │   │   ├── calendar_provider.dart
│   │       │   │   └── calendar_screen.dart
│   │       │   ├── etf_detail/          # ETF 상세 정보 + 리포트 + 운용사별 ETF 목록
│   │       │   │   ├── etf_detail_screen.dart
│   │       │   │   ├── etf_report_screen.dart      # AI 분석 리포트
│   │       │   │   ├── etf_report_provider.dart
│   │       │   │   ├── etf_holdings_changes_widget.dart  # 주간 보유종목 변동
│   │       │   │   └── company_etfs_screen.dart
│   │       │   ├── feed/                # 뉴스 피드 (메인 탭)
│   │       │   │   ├── feed_screen.dart
│   │       │   │   ├── feed_provider.dart
│   │       │   │   ├── feed_models.dart
│   │       │   │   └── tab_shell.dart   # 하단 탭 바 쉘 (피드/내ETF/캘린더)
│   │       │   ├── my_etf/              # 내 ETF 포트폴리오 관리
│   │       │   │   ├── my_etf_screen.dart
│   │       │   │   ├── my_etf_provider.dart
│   │       │   │   ├── etf_models.dart
│   │       │   │   ├── add_etf_sheet.dart          # ETF 추가 바텀시트
│   │       │   │   └── widgets/weekly_share_card.dart
│   │       │   ├── onboarding/          # 온보딩 4단계 (ETF 선택→로딩→첫 피드→푸시 권한)
│   │       │   │   ├── onboarding_screen.dart
│   │       │   │   ├── onboarding_provider.dart
│   │       │   │   ├── step1_etf_select.dart
│   │       │   │   ├── step2_loading.dart
│   │       │   │   ├── step3_first_feed.dart
│   │       │   │   └── step4_push_permission.dart
│   │       │   ├── settings/            # 설정 (푸시 시간 설정 포함)
│   │       │   │   ├── settings_screen.dart
│   │       │   │   └── settings_provider.dart
│   │       │   └── splash/
│   │       │       └── splash_screen.dart
│   │       └── shared/
│   │           ├── services/
│   │           │   ├── api_client.dart   # Dio 싱글톤 — X-Device-ID 헤더 자동 추가, 15s/30s 타임아웃
│   │           │   └── push_service.dart # FCM 푸시 토큰 등록
│   │           ├── tracking/            # AARRR 이벤트 트래킹 시스템
│   │           │   ├── event_tracker.dart   # 싱글톤 트래커 (Hive 큐 + 30초 배치 전송)
│   │           │   ├── event_models.dart
│   │           │   ├── event_queue.dart
│   │           │   ├── event_sender.dart
│   │           │   └── screen_observer.dart # GoRouter 화면 전환 자동 추적
│   │           └── widgets/             # 공유 UI 컴포넌트
│   │               ├── animated_list_item.dart
│   │               ├── bottom_tab_bar.dart
│   │               ├── briefing_card.dart
│   │               ├── empty_state.dart
│   │               ├── etf_chip.dart
│   │               ├── glass_card.dart
│   │               ├── impact_badge.dart
│   │               ├── loading_shimmer.dart
│   │               ├── news_card.dart
│   │               ├── pressable_card.dart
│   │               ├── price_count_up.dart
│   │               ├── share_channel_sheet.dart
│   │               └── shimmer_variants.dart
│   │
│   └── admin/                           # Next.js 어드민 대시보드 (Vercel)
│       ├── app/
│       │   ├── layout.tsx               # 루트 레이아웃 (AuthGuard 래핑)
│       │   ├── page.tsx                 # 메인 대시보드 (DAU 차트)
│       │   ├── auth/callback/page.tsx   # Supabase OAuth 콜백
│       │   ├── login/page.tsx           # 로그인 페이지
│       │   ├── deploy/page.tsx          # GitHub Actions 배포 트리거
│       │   ├── events/page.tsx          # 이벤트 로그 뷰어
│       │   ├── funnel/page.tsx          # AARRR 퍼널 분석
│       │   ├── push/page.tsx            # 푸시 알림 관리
│       │   ├── retention/page.tsx       # 리텐션 히트맵
│       │   └── users/page.tsx           # 사용자 통계
│       ├── components/
│       │   ├── auth-guard.tsx           # Supabase 세션 기반 인증 가드
│       │   ├── ui/
│       │   │   ├── admin-shell.tsx      # 사이드바 + 콘텐츠 레이아웃
│       │   │   ├── card.tsx
│       │   │   ├── data-table.tsx
│       │   │   ├── sidebar.tsx
│       │   │   ├── skeleton.tsx
│       │   │   └── stat-card.tsx
│       │   └── charts/
│       │       ├── DauChart.tsx          # DAU 라인 차트
│       │       ├── FunnelChart.tsx       # AARRR 퍼널 차트
│       │       ├── PushChart.tsx         # 푸시 전송 통계
│       │       ├── RetentionHeatmap.tsx  # 리텐션 히트맵
│       │       └── RetentionLineChart.tsx
│       ├── hooks/
│       │   └── use-fetch.ts             # SWR 스타일 데이터 패칭 훅
│       ├── lib/
│       │   ├── api.ts                   # API 클라이언트 (Next.js rewrite proxy 경유, CORS 우회)
│       │   ├── auth.ts                  # Supabase Auth 유틸
│       │   ├── supabase.ts              # Supabase 클라이언트 초기화
│       │   └── utils.ts                 # 공용 유틸
│       └── types/
│           └── admin.ts                 # 어드민 API 응답 타입 정의
│
├── backend/                             # FastAPI 백엔드 (Fly.io)
│   ├── main.py                          # FastAPI 앱 생성, 라우터 등록, lifespan(스케줄러+Firebase)
│   ├── config.py                        # Settings — 환경변수 로드 (Supabase/Gemini/Finnhub/FCM 등)
│   ├── Dockerfile                       # 컨테이너 빌드
│   ├── Procfile                         # uvicorn 실행 명령
│   ├── requirements.txt                 # Python 의존성
│   ├── routers/
│   │   ├── feed.py                      # GET /api/v1/feed — 시그널 피드 우선, news_service fallback
│   │   ├── briefing.py                  # GET /api/v1/briefing — 아침/밤 브리핑 조회
│   │   ├── etf.py                       # GET /api/v1/etf — ETF 검색/상세/등록/해제
│   │   ├── etf_analysis.py              # GET /api/v1/etf/compare — ETF 비교 분석 (Gemini)
│   │   ├── holdings.py                  # GET /api/v1/holdings — 보유종목 + 주간 변동
│   │   ├── calendar.py                  # GET /api/v1/calendar — Finnhub 경제 이벤트 캘린더
│   │   ├── analytics.py                 # POST /api/v1/analytics — 이벤트 수집/조회
│   │   ├── admin.py                     # /api/v1/admin — 대시보드/캐시/배포/푸시 (인증 필수)
│   │   └── devices.py                   # /api/v1/devices — FCM 토큰 등록/해제
│   ├── services/
│   │   ├── briefing_service.py          # Gemini 브리핑 생성 — 백그라운드 전용, 캐시에서 반환
│   │   ├── news_service.py              # RSS 수집 + Gemini 번역 — 백그라운드 번역, 즉시 반환
│   │   ├── etf_service.py               # ETF 메타데이터 — Supabase 우선, yfinance fallback
│   │   ├── price_service.py             # yfinance 가격 — 적응형 TTL (장중 15분/장외 6시간)
│   │   ├── holdings_service.py          # ETF 보유종목 조회 + 주간 변동 비교
│   │   ├── impact_service.py            # 뉴스→ETF 영향도 분석
│   │   ├── calendar_service.py          # Finnhub 경제 이벤트 조회
│   │   ├── signal_feed_service.py       # Supabase 시그널 파이프라인 피드 변환
│   │   ├── exchange_rate_service.py     # USD/KRW 환율 조회
│   │   ├── cache.py                     # in-memory TTLCache (cachetools, thread-safe, 100엔트리/15분)
│   │   ├── cache_ttl.py                 # 데이터 유형별 TTL 상수 + 장중/장외 적응형 가격 TTL
│   │   ├── analytics_service.py         # AARRR 이벤트 저장/집계
│   │   ├── admin_service.py             # 어드민 대시보드 서비스
│   │   ├── push_service.py              # Firebase Admin SDK — FCM 푸시 전송
│   │   └── supabase_client.py           # Supabase 클라이언트 싱글톤 (anon/service key)
│   ├── jobs/
│   │   ├── briefing_scheduler.py        # APScheduler — 9개 잡 등록 (뉴스/브리핑/집계/스냅샷)
│   │   ├── news_collector.py            # RSS 뉴스 수집 잡
│   │   ├── aggregation.py               # 일간 메트릭 집계 (01:00 KST)
│   │   └── funnel_aggregation.py        # AARRR 퍼널 코호트 집계 (01:30 KST)
│   ├── middleware/
│   │   ├── admin_auth.py                # Supabase Auth 토큰 검증 + 이메일 화이트리스트 + 역할 매핑
│   │   └── rate_limit.py                # slowapi 기반 — X-Device-ID 또는 IP 키, 엔드포인트별 제한
│   ├── models/
│   │   └── schemas.py                   # Pydantic 스키마 (BriefingResponse, FeedItem, ETFInfo 등)
│   ├── prompts/
│   │   ├── briefing.py                  # 아침/밤 브리핑 프롬프트 (Gemini용)
│   │   ├── impact.py                    # 뉴스→ETF 영향도 분석 프롬프트
│   │   └── translate.py                 # 뉴스 한국어 번역 프롬프트
│   ├── seeds/
│   │   ├── etf_master.json              # ETF 마스터 데이터 (ticker, name_kr, top_holdings)
│   │   ├── etf_comparison_groups.json   # ETF 비교 그룹 정의
│   │   ├── macro_sensitivity.json       # 거시경제 민감도 데이터
│   │   └── seed_etf_master.py           # Supabase에 마스터 데이터 시딩
│   ├── migrations/                      # Supabase SQL 마이그레이션 (6개)
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_analytics_tables.sql
│   │   ├── 003_admin_deploy_tables.sql
│   │   ├── 004_news_feed_fixes.sql
│   │   ├── 005_device_preferences_and_deploy_steps.sql
│   │   └── 006_event_id_unique_and_api_cache.sql
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_briefing.py
│   │   ├── test_briefing_personalization.py
│   │   ├── test_etf_search.py
│   │   ├── test_feed.py
│   │   ├── test_health.py
│   │   └── test_release_readiness.py
│   ├── data/
│   │   └── macro_sensitivity.json       # 거시경제 민감도 (런타임 참조)
│   └── logs/                            # 런타임 로그 디렉토리
│
├── supabase/
│   ├── config.toml                      # Supabase 로컬 설정
│   ├── pg_cron_setup.sql                # pg_cron 스케줄 설정
│   ├── migrations/                      # Supabase 마이그레이션 (backend/migrations과 동일)
│   └── functions/
│       └── news-pipeline/               # Edge Function (Deno) — 뉴스 시그널 파이프라인
│           ├── index.ts                 # 진입점
│           ├── collector.ts             # 뉴스 수집
│           ├── classifier.ts            # 뉴스 분류
│           ├── matcher.ts               # ETF 매칭
│           ├── translator.ts            # 번역
│           ├── glossary.ts              # 금융 용어 사전
│           └── deno.json                # Deno 설정
│
├── docs/                                # 프로젝트 문서
│   ├── api_spec.md                      # API 명세
│   ├── admin_api_spec.md                # 어드민 API 명세
│   ├── event_schema.md                  # AARRR 이벤트 스키마
│   ├── deployment_env_vars.md           # 배포 환경변수 목록
│   ├── ai_risk_assessment.md            # AI 위험 평가
│   ├── privacy_policy.md               # 개인정보처리방침 (한국어)
│   ├── privacy_policy_en.md             # Privacy Policy (영문)
│   ├── terms_of_service.md              # 이용약관
│   ├── store_metadata.md               # 앱스토어 메타데이터
│   ├── store_screenshots_guide.md       # 스토어 스크린샷 가이드
│   ├── final_qa_report.md
│   └── release_qa_report.md
│
├── docker-compose.yml                   # 로컬 개발 환경 (백엔드+Supabase)
├── Makefile                             # 빌드/실행 명령 단축
├── .env.example                         # 환경변수 템플릿
└── README.md
```

---

## 핵심 진입점 테이블

| 작업 유형 | 시작 파일 | 비고 |
|---|---|---|
| Flutter 앱 수정 | `apps/mobile/lib/main.dart` | Flavor: local/qa/production. `app_config.dart`에서 API URL 결정 |
| Flutter 새 화면 추가 | `apps/mobile/lib/config/router.dart` | GoRouter에 라우트 추가 + features/ 하위에 폴더 생성 |
| Flutter 테마/색상 변경 | `apps/mobile/lib/config/theme.dart` | PortfiqTheme 클래스. Dark mode only, Pretendard 폰트 |
| Flutter 공유 위젯 추가 | `apps/mobile/lib/shared/widgets/` | 재사용 위젯. glass_card, briefing_card 등 |
| Flutter 이벤트 트래킹 | `apps/mobile/lib/shared/tracking/event_tracker.dart` | `EventTracker.instance.track('event_name')` |
| 백엔드 API 추가 | `backend/routers/` | 라우터 파일 생성 후 `main.py`에 `include_router()` 등록 |
| 브리핑 로직 수정 | `backend/services/briefing_service.py` | 백그라운드 전용 생성. 프롬프트는 `prompts/briefing.py` |
| 브리핑 프롬프트 수정 | `backend/prompts/briefing.py` | MORNING_PROMPT, NIGHT_PROMPT 상수 |
| 뉴스 수집/번역 수정 | `backend/services/news_service.py` | RSS 수집 → Gemini 번역. 프롬프트는 `prompts/translate.py` |
| 스케줄러 잡 추가/수정 | `backend/jobs/briefing_scheduler.py` | APScheduler. `_run_in_thread()` 패턴으로 별도 스레드 실행 |
| 캐시 TTL 조정 | `backend/services/cache_ttl.py` | CacheTTL 클래스 + `get_market_aware_price_ttl()` |
| ETF 마스터 데이터 수정 | `backend/seeds/etf_master.json` | ticker, name_kr, top_holdings. 시딩: `seed_etf_master.py` |
| DB 스키마 변경 | `backend/migrations/` | 순번 SQL 파일. Supabase 대시보드에서 직접 실행 |
| 어드민 대시보드 수정 | `apps/admin/app/page.tsx` | Next.js App Router. Vercel 배포 |
| 어드민 새 페이지 추가 | `apps/admin/app/{page-name}/page.tsx` | `components/ui/admin-shell.tsx` 사이드바에 링크 추가 |
| 어드민 인증 수정 | `backend/middleware/admin_auth.py` | Supabase Auth + 이메일 화이트리스트 (`config.py` ADMIN_ALLOWED_EMAILS) |
| 환경변수 추가 | `backend/config.py` | Settings 클래스에 추가. 배포 시 `docs/deployment_env_vars.md` 갱신 |
| Supabase Edge Function | `supabase/functions/news-pipeline/index.ts` | Deno 런타임. 뉴스 시그널 파이프라인 |

---

## 최근 변경 이력

```
8ea630b fix: portfiq 백엔드 QA HIGH/MEDIUM 이슈 5건 수정 + openapi.json 500 해결
86eadbd fix: stabilize portfiq release candidate
931d78d fix: 뉴스 카드에서 summary_3line 우선 표시 (impact_reason 대신)
3453170 fix: 캐시 클리어 API + 야간 브리핑 정확성 개선
8145c87 feat: Portfiq 갭 분석 기반 5대 개선 — AARRR 트래킹 + 푸시 시간 설정 + 관련 뉴스
40c41cc fix: 뉴스 번역 후 피드 캐시 무효화 누락 수정
c2c5805 feat: 뉴스 한국어 번역 강화 + 원화 가격 표시
1099686 feat: Portfiq 출시 Critical+Major 전면 수정 — 하드코딩 제거, 실데이터 연동, UI 안정화
05eb5e9 docs: Portfiq 출시 QA 리포트 — 전항목 PASS
87ee399 feat: Portfiq 출시 준비 — UI/UX 디자인 고도화 + 백엔드 버그 수정 + Admin 개선
036bbfc fix: QA 감사 기반 12건 버그 수정 — 브리핑 자동생성/온보딩 ETF 등록/Admin 엔드포인트
e33baee fix: Flutter lint 17건 전부 수정 — flutter analyze 0 issues 달성
e5dd6ca fix: Flutter 앱 출시 준비 — API URL Fly.io 전환 + share card 오버플로우 수정
1e1709e fix: ruff lint 에러 수정 (unused variable, unused import)
5799613 refactor: 브리핑 생성도 Claude→Gemini 전환 (Anthropic SDK 완전 제거)
```

---

## 주의사항 / Gotchas

### yfinance Rate Limit
- `price_service.py`에서 yfinance 호출은 `asyncio.to_thread()`로 스레드 풀 실행, 10초 타임아웃 적용
- 실패 시 stale cache(`_stale_cache`)에서 마지막 성공 데이터를 반환하는 fallback 존재
- 과도한 호출 시 yfinance가 IP 차단할 수 있음 — 적응형 TTL(장중 15분/장외 6시간)로 호출 최소화

### 캐시 TTL 전략 (장중/장외 다름)
- `cache_ttl.py`의 `get_market_aware_price_ttl()`: US/Eastern 기준 장중(9:30~16:00 평일) 15분, 장외/주말 6시간
- 범용 in-memory 캐시(`cache.py`): cachetools TTLCache, 100엔트리, 기본 15분
- 브리핑 캐시는 12시간, 뉴스 번역은 30일, ETF 메타/보유종목은 7일
- 뉴스 번역 후 피드 캐시 무효화 누락이 과거 버그였음 (40c41cc에서 수정)

### Gemini 모델만 사용 (openai/anthropic 금지)
- 모든 AI 호출은 `google-genai` 패키지의 `genai.Client` 사용
- 모델: `gemini-2.5-flash-lite` (config.py의 GEMINI_MODEL)
- Gemini rate limit 백오프: `news_service.py`에서 모노토닉 타임스탬프로 60초 백오프 관리
- anthropic/openai 패키지 의존성 추가 절대 금지

### Pretendard 폰트 통일 (Inter 사용 금지)
- Flutter 앱: `theme.dart`에서 Pretendard 적용
- 어드민 대시보드: `layout.tsx`에서 현재 Inter 폰트 사용 중 (Pretendard로 전환 필요 — 미해결)

### Supabase RLS
- `supabase_client.py`에 anon key(`get_supabase()`)와 service key(`get_service_supabase()`) 두 클라이언트 존재
- 어드민/백그라운드 잡은 service key 사용 (RLS 우회)
- 프론트엔드/일반 API는 anon key 사용 (RLS 적용)
- 마이그레이션 6개 파일 — Supabase 대시보드 SQL 에디터에서 직접 실행

### APScheduler 스레드 분리 패턴
- `briefing_scheduler.py`의 `_run_in_thread()`: 코루틴을 별도 스레드 + 별도 event loop에서 실행
- 이유: 메인 event loop 블로킹 방지 — Gemini/yfinance 동기 I/O가 `/health` 등 API 응답을 막지 않도록
- 새 잡 추가 시 반드시 `_run_in_thread()` 래퍼 사용

### 어드민 인증
- Supabase Auth(Google OAuth) + 이메일 화이트리스트 (`config.py`의 ADMIN_ALLOWED_EMAILS)
- 역할 매핑: `ADMIN_ROLE_MAP` (cto/ceo)
- 기존 JWT 방식도 폴백으로 유지

### API 라우터 등록
- 새 라우터 추가 시 `main.py`의 import + `app.include_router()` 두 곳 모두 수정 필수
- 모든 API는 `/api/v1/` prefix

### Flutter Flavor
- `main.dart`(production), `main_local.dart`(local), `main_qa.dart`(qa) — 각각 `AppConfig.initialize(Flavor.xxx)` 호출
- production API: `https://portfiq.fly.dev`
- Hive box 'settings'에 device_id 영구 저장 — 첫 실행 시 생성
