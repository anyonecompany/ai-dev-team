# Portfiq(포트픽) — Phase 1 개발 (기반 인프라 + 앱 핵심)

> 서학 ETF 개미를 위한 AI 브리핑 앱
> "내가 보유한 ETF 기준으로, 오늘 밤 뭘 봐야 하는지 3줄로 알려주는 앱"

## 프로젝트 경로
- 모노레포: `projects/portfiq/`
- Flutter 앱: `projects/portfiq/apps/mobile/`
- FastAPI 백엔드: `projects/portfiq/backend/`
- Admin 대시보드: `projects/portfiq/apps/admin/` (Phase 3)
- 문서: `projects/portfiq/docs/`

## 기술 스택
- **앱**: Flutter 3.41 + Dart, GoRouter, Riverpod, Dio, Hive, freezed
- **백엔드**: Python 3.11+ / FastAPI / Supabase (PostgreSQL) / APScheduler
- **AI**: Claude API (브리핑 생성, 뉴스 영향도 분류)
- **푸시**: Firebase Cloud Messaging (FCM)
- **데이터**: Yahoo Finance API, Investing.com RSS, ETF 구성종목 CSV

## 디자인 시스템
- **Key Accent**: Electric Indigo `#6366F1`
- **Primary BG**: `#0D0E14` (다크, 미세 블루 틴트)
- **Secondary BG**: `#16181F` (카드 레이어)
- **Surface**: `#1E2028` (인터랙티브 컴포넌트)
- **Impact High**: `#EF4444` (Red)
- **Impact Medium**: `#F59E0B` (Amber)
- **Impact Low**: `#6B7280` (Gray)
- **Positive**: `#10B981` (Emerald, 수익 +)
- **Negative**: `#EF4444` (Red, 수익 -)
- **Text Primary**: `#F9FAFB`
- **Text Secondary**: `#9CA3AF`
- **Divider**: `#2D2F3A`
- **폰트**: Pretendard (한국어) + Inter (영어/숫자)
- **아이콘**: Lucide Icons (2px 선)
- **라운딩**: 12px (카드), 8px (버튼), 24px (칩)
- **다크 모드 전용** — 라이트 모드 없음

## 탭 구조 (4탭)
1. 홈 (피드 + 브리핑) — 하우스 아이콘
2. 내 ETF (해부 리포트) — 차트 아이콘
3. 캘린더 (경제 이벤트) — 캘린더 아이콘
4. 설정 (ETF 관리/알림) — 슬라이더 아이콘

---

## 에이전트 팀 구성 (5인)

### 1. Infra-Architect
**담당**: 모노레포 구조 + 프로젝트 초기화 + 공통 설정

**작업 내용**:
1. `projects/portfiq/` 모노레포 생성
   ```
   portfiq/
   ├── apps/
   │   ├── mobile/          ← flutter create
   │   └── admin/           ← (Phase 3, 빈 폴더만)
   ├── backend/             ← FastAPI
   ├── docs/
   │   ├── event_schema.md  ← 이벤트 스펙 단일 소스
   │   └── api_spec.md      ← API 엔드포인트 명세
   ├── .github/workflows/
   ├── docker-compose.yml
   ├── Makefile
   └── README.md
   ```

2. Flutter 프로젝트 초기화 (`flutter create`)
   - 패키지명: `com.portfiq.app`
   - Flavor 3개: local / qa / production
   - 기본 의존성 설치: `go_router`, `flutter_riverpod`, `riverpod_annotation`, `dio`, `hive_flutter`, `freezed`, `freezed_annotation`, `build_runner`, `json_annotation`, `json_serializable`, `firebase_messaging`, `firebase_core`, `lucide_icons`
   - 폴더 구조:
     ```
     lib/
     ├── app.dart                    ← MaterialApp + GoRouter
     ├── main_local.dart             ← Flavor: local
     ├── main_qa.dart                ← Flavor: qa
     ├── main_production.dart        ← Flavor: production
     ├── config/
     │   ├── app_config.dart         ← Flavor별 설정 (API URL 등)
     │   ├── theme.dart              ← 디자인 시스템 ThemeData
     │   └── router.dart             ← GoRouter 라우트 정의
     ├── features/
     │   ├── onboarding/             ← 온보딩 플로우
     │   ├── feed/                   ← 뉴스 피드
     │   ├── briefing/               ← 브리핑 카드
     │   ├── etf_detail/             ← ETF 해부 리포트
     │   ├── calendar/               ← 경제 캘린더
     │   └── settings/               ← 설정
     ├── shared/
     │   ├── tracking/               ← EventTracker SDK
     │   ├── models/                 ← 공용 모델
     │   ├── widgets/                ← 공용 위젯
     │   └── services/               ← API 클라이언트 등
     └── core/
         ├── constants.dart
         └── extensions.dart
     ```

3. FastAPI 백엔드 초기화
   ```
   backend/
   ├── main.py
   ├── config.py                    ← 환경변수, Supabase 설정
   ├── routers/
   │   ├── feed.py                  ← 뉴스 피드 API
   │   ├── briefing.py              ← 브리핑 생성 API
   │   ├── etf.py                   ← ETF 등록/조회 API
   │   ├── analytics.py             ← 이벤트 수신 API
   │   └── admin.py                 ← Admin API (Phase 3)
   ├── services/
   │   ├── news_service.py          ← 뉴스 수집
   │   ├── briefing_service.py      ← Claude 브리핑 생성
   │   ├── etf_service.py           ← ETF 데이터
   │   ├── impact_service.py        ← 영향도 분류
   │   └── analytics_service.py     ← 이벤트 저장/집계
   ├── models/
   │   └── schemas.py               ← Pydantic 모델
   ├── jobs/
   │   ├── briefing_scheduler.py    ← 08:35/22:00 배치
   │   └── aggregation.py           ← daily_metrics 집계
   └── requirements.txt
   ```

4. `docs/event_schema.md` 작성 — 전체 트래킹 이벤트 스펙
5. `docs/api_spec.md` 작성 — API 엔드포인트 명세
6. `.gitignore`, `.env.example` 생성

**파일 소유권**: 루트 설정, `docs/`, `.github/`

---

### 2. Flutter-Onboarding (앱 영역 1)
**담당**: 온보딩 플로우 + EventTracker SDK + 테마

**작업 내용**:

1. `lib/config/theme.dart` — 디자인 시스템 ThemeData 구현
   - ColorScheme: 위 디자인 시스템 컬러 전부
   - TextTheme: Pretendard + Inter, Display/Heading/Body/Caption/Label 스케일
   - 카드/버튼/칩/바텀시트 테마 커스터마이징

2. `lib/shared/tracking/` — EventTracker SDK
   - `event_tracker.dart`: 싱글톤, `track(name, properties)` 메서드
   - `event_queue.dart`: Hive 기반 로컬 큐 (10개 or 30초마다 배치 전송)
   - `event_sender.dart`: Dio로 `POST /api/v1/analytics/events` 배치 전송
   - `event_models.dart`: freezed 이벤트 모델
   - `screen_observer.dart`: GoRouter 화면 전환 자동 트래킹
   - Flavor별 분리: local=콘솔 출력, qa/prod=API 전송

3. `lib/features/onboarding/` — 온보딩 4스텝
   - **Step 1**: ETF 등록 화면
     - 검색바 (자동완성) + 인기 ETF 칩 6개 (QQQ/VOO/SCHD/TQQQ/SOXL/JEPI)
     - 칩 탭 시 Indigo 테두리 + 체크 애니메이션 (0.15초)
     - CTA "완료" 버튼 (ETF 1개 이상 시 활성)
   - **Step 2**: 로딩 화면
     - "내 ETF 기준으로 뉴스를 분석하는 중..." + Indigo 프로그레스
     - 1.5초 로딩 후 자동 전환
   - **Step 3**: 아하 모먼트 — 첫 피드 노출
     - 영향도 High 뉴스 카드가 최상단 (mock 데이터)
     - 카드에 사용자가 등록한 ETF 티커 배지 표시
     - 카드 순차 등장 애니메이션 (Staggered, 0.2초 간격)
   - **Step 4**: 푸시 권한 바텀시트
     - 피드 1~2개 스크롤 후 자동 등장
     - "매일 아침 8:35, 간밤 미장 결과를 알려드릴게요"
     - CTA "알림 받기" (Indigo) + "나중에 설정할게요" 텍스트 링크
   - 각 단계마다 EventTracker 이벤트 삽입

4. `lib/config/router.dart` — GoRouter 설정
   - `/onboarding` → `/home` → `/etf/:ticker` → `/settings`
   - ScreenObserver 연동

**디자인 필수 준수사항**:
- 다크 모드 전용 (#0D0E14 배경)
- 폰트 14px 미만 본문 금지
- 한 화면 CTA 3개 이하
- 모달 위 모달 금지
- 최소 터치 영역 44x44px
- 애니메이션: 화면 전환 250ms / 마이크로인터랙션 150ms

**파일 소유권**: `lib/config/`, `lib/shared/`, `lib/features/onboarding/`, `lib/core/`

---

### 3. Flutter-Feed (앱 영역 2)
**담당**: 뉴스 피드 + 브리핑 카드 + 탭 네비게이션

**작업 내용**:

1. `lib/shared/widgets/` — 공용 위젯
   - `news_card.dart`: 뉴스 카드 컴포넌트
     - Row 1: [ETF 영향도 배지들] [시간 우측정렬]
     - Row 2: 헤드라인 (Bold, 최대 2줄)
     - Row 3: 영향 이유 3줄 (Regular, Text Secondary)
     - Row 4: [출처명] [원문 보기 링크]
     - High 카드: 좌측 Indigo/Red 세로 액센트 바
     - 배지: High=#EF4444, Medium=#F59E0B, Low=#2D2F3A
   - `briefing_card.dart`: 브리핑 카드
     - 아침: "🌅 간밤 미장 브리핑" + ETF 등락률 칩 + 핵심 한줄
     - 밤: "🌙 오늘 밤 체크포인트" + 체크포인트 3개 리스트
     - Indigo(아침)/Amber(밤) 1px 테두리
   - `impact_badge.dart`: 영향도 배지 컴포넌트
   - `etf_chip.dart`: ETF 등락률 칩 (Positive/Negative 컬러)
   - `bottom_tab_bar.dart`: 4탭 네비게이션 바

2. `lib/features/feed/` — 홈 피드 화면
   - 상단: 브리핑 배너 (시간대별 아침/밤 자동 전환)
   - 메인: 뉴스 카드 무한 스크롤 (영향도 순 정렬)
   - Pull-to-refresh
   - 카드 탭 → 바텀시트 상세
   - 모든 인터랙션에 EventTracker 이벤트

3. `lib/features/briefing/` — 브리핑 상세 화면
   - 아침 브리핑: ETF별 등락률 + 원인 1줄 + 간밤 핵심 이벤트
   - 밤 체크포인트: 이벤트 3개 + ETF 영향도 매핑
   - 공유 버튼 (카카오톡/X)

4. 탭 네비게이션 (4탭) 쉘 구현
   - 홈(피드), 내 ETF(플레이스홀더), 캘린더(플레이스홀더), 설정(플레이스홀더)

5. `lib/shared/services/api_client.dart` — Dio 기반 API 클라이언트
   - Base URL: Flavor별 분기
   - X-Device-ID 헤더 자동 삽입

**파일 소유권**: `lib/features/feed/`, `lib/features/briefing/`, `lib/shared/widgets/`, `lib/shared/services/`

---

### 4. BE-Developer
**담당**: FastAPI 백엔드 전체

**작업 내용**:

1. `backend/config.py` — 환경변수 관리
   - SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY, YAHOO_FINANCE_API
   - FCM 관련 설정

2. `backend/routers/etf.py` — ETF API
   - `POST /api/v1/etf/register` — ETF 등록 (device_id + tickers)
   - `GET /api/v1/etf/search?q=QQQ` — ETF 검색 (자동완성)
   - `GET /api/v1/etf/popular` — 인기 ETF Top 10
   - `GET /api/v1/etf/{ticker}/detail` — ETF 상세 (구성종목, 섹터, 민감도)

3. `backend/routers/feed.py` — 뉴스 피드 API
   - `GET /api/v1/feed?device_id={id}` — 개인화 피드 (등록 ETF 기준 영향도 순)
   - `GET /api/v1/feed/latest` — 최신 뉴스 (영향도 분류 포함)

4. `backend/routers/briefing.py` — 브리핑 API
   - `GET /api/v1/briefing/morning?device_id={id}` — 아침 브리핑
   - `GET /api/v1/briefing/night?device_id={id}` — 밤 체크포인트
   - `POST /api/v1/briefing/generate` — 수동 브리핑 생성 (관리용)

5. `backend/routers/analytics.py` — 이벤트 수신 API
   - `POST /api/v1/analytics/events` — 배치 이벤트 수신 (202 Accepted)
   - 인증: X-Device-ID 헤더
   - Supabase `events` 테이블 Bulk Insert

6. `backend/services/briefing_service.py` — Claude API 브리핑 생성
   - ETF 등락률 + 당일 이벤트 인풋 → 3줄 브리핑 아웃풋
   - 모델: claude-sonnet-4-5-20250929 (비용 효율)
   - ETF 그룹별 배치 처리 (비용 최적화)

7. `backend/services/impact_service.py` — 뉴스 영향도 분류
   - Claude API: "이 뉴스가 {ETF 구성종목 Top 10}에 해당하는가?" → High/Medium/Low

8. `backend/services/news_service.py` — 뉴스 수집
   - Yahoo Finance RSS + Investing.com RSS
   - 15분 간격 갱신
   - 한국어 번역 헤드라인 (Claude API)

9. `backend/models/schemas.py` — Pydantic 모델 전체

10. Supabase 테이블 마이그레이션 SQL
    - `devices`, `device_etfs`, `etf_master`, `news`, `briefings`
    - `events`, `daily_metrics`, `funnel_cohorts`, `session_metrics`, `push_metrics`

**파일 소유권**: `backend/` 전체

---

### 5. QA-DevOps
**담당**: 전체 빌드 검증 + 환경 체크

**작업 내용**:
1. Flutter 빌드: `flutter build web` (또는 `flutter run -d chrome`) → 에러 0
2. `flutter analyze` → 에러 0
3. FastAPI 서버 기동: `uvicorn main:app` → 정상
4. API 스모크 테스트: `/api/v1/etf/popular`, `/api/v1/feed/latest` → 200
5. EventTracker → Analytics API 연동 확인
6. Supabase 테이블 생성 확인

**파일 소유권**: `tests/`

---

## 실행 순서

```
Phase 0: Infra-Architect (모노레포 + 프로젝트 초기화)
  ↓
Phase 1 (병렬): Flutter-Onboarding + Flutter-Feed + BE-Developer
  ↓
Phase 2: QA-DevOps (전체 통합 검증)
```

## 규칙
- 각 에이전트는 자기 파일 소유권 내에서만 작업
- 이벤트 추가 시 `docs/event_schema.md` 먼저 업데이트
- 환경변수 하드코딩 절대 금지
- 다크 모드 전용 — 라이트 모드 코드 작성 금지
- 모든 함수에 type hints + docstring
- Flutter: Riverpod 상태관리, GoRouter 라우팅, freezed 모델
- 작업 완료 후 Notion 보고 (project_name="Portfiq (포트픽)")
