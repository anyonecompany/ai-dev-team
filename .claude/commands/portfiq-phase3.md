# Portfiq(포트픽) — Phase 3 전체 완성

> Phase 1(UI 스켈레톤) + Phase 2(데이터 연동) 완료 상태.
> Phase 3: 나머지 탭 전체 구현 + UI 폴리싱 + FCM 푸시 + ETF 시드 업로드 + 전체 통합.

## 프로젝트 경로
- Flutter 앱: `projects/portfiq/apps/mobile/`
- FastAPI 백엔드: `projects/portfiq/backend/`
- 환경변수: `projects/portfiq/.env` (Supabase, Claude API 설정 완료)

## 현재 문제점 (반드시 수정)
1. **뒤로가기 버튼 없음** — placeholder 화면들에 AppBar/뒤로가기 미구현
2. **내 ETF 탭** — placeholder만 있음 ("My ETF" 텍스트만 표시)
3. **캘린더 탭** — placeholder만 있음
4. **설정 탭** — placeholder만 있음
5. **ETF 상세 화면** — placeholder만 있음 (router에 `_PlaceholderScreen`)
6. **ETF 시드 데이터** — Supabase에 아직 업로드 안 됨
7. **FCM 푸시** — 미구현
8. **실시간 ETF 가격** — 미구현

## 디자인 시스템 (기존 유지)
- **Primary BG**: `#0D0E14` / **Card**: `#16181F` / **Surface**: `#1E2028`
- **Accent**: `#6366F1` (Electric Indigo)
- **Positive**: `#10B981` / **Negative**: `#EF4444`
- **Text Primary**: `#F9FAFB` / **Secondary**: `#9CA3AF`
- **Divider**: `#2D2F3A`
- **다크 모드 전용**, 라운딩 12px(카드) 8px(버튼), 최소 터치 44x44

---

## 에이전트 팀 구성 (5인)

### 1. Flutter-MyETF
**담당**: 내 ETF 탭 + ETF 상세 화면 전체 구현

**작업 내용**:

1. `lib/features/my_etf/my_etf_screen.dart` — 내 ETF 탭 메인
   - 상단: "내 포트폴리오" 타이틀 + ETF 추가 버튼 (+ 아이콘)
   - 등록된 ETF 카드 리스트 (세로 스크롤)
   - 각 카드: 티커 + 이름(한국어) + 현재가 + 일간 등락률 + 카테고리 칩
   - 카드 탭 → ETF 상세 화면 이동
   - ETF 미등록 시: 빈 상태 일러스트 + "ETF를 추가해보세요" CTA
   - Pull-to-refresh로 가격 갱신

2. `lib/features/etf_detail/etf_detail_screen.dart` — ETF 상세 (router의 placeholder 교체)
   - AppBar: ← 뒤로가기 + 티커명 + 즐겨찾기 토글
   - 섹션 1: 가격 헤더 (현재가 + 등락률 + 등락 금액)
   - 섹션 2: 기본 정보 카드 (카테고리, 운용보수, 한줄 설명)
   - 섹션 3: 구성종목 Top 10 리스트 (종목명 + 비중%)
   - 섹션 4: 관련 뉴스 (해당 ETF 영향도 High/Medium 뉴스만 필터)
   - 하단: "포트폴리오에서 제거" 버튼 (빨간색)

3. `lib/features/my_etf/add_etf_sheet.dart` — ETF 추가 바텀시트
   - 검색바 (디바운스 300ms)
   - 검색 결과 리스트 (티커 + 이름 + 카테고리)
   - 탭하면 즉시 추가 + 스낵바 확인

4. ETF 관련 Provider
   - `lib/features/my_etf/my_etf_provider.dart` — 등록 ETF 목록 + CRUD
   - API 연동: `GET /api/v1/etf/search`, `POST /api/v1/etf/register`, `GET /api/v1/etf/{ticker}/detail`

**파일 소유권**: `lib/features/my_etf/`, `lib/features/etf_detail/`

---

### 2. Flutter-CalendarSettings
**담당**: 캘린더 탭 + 설정 탭 구현

**작업 내용**:

1. `lib/features/calendar/calendar_screen.dart` — 경제 캘린더 탭
   - 상단: 현재 월 표시 + 좌우 화살표 네비게이션
   - 달력 그리드: 이벤트 있는 날짜에 Indigo 도트 표시
   - 하단: 선택 날짜의 이벤트 리스트
   - 이벤트 카드: 시간 + 이벤트명 + 영향 ETF 배지
   - Mock 데이터로 구현 (FOMC, CPI, 고용보고서 등 주요 경제 이벤트)

2. `lib/features/settings/settings_screen.dart` — 설정 탭
   - 섹션 1: ETF 관리
     - 등록된 ETF 리스트 (스와이프 삭제)
     - ETF 추가 버튼
   - 섹션 2: 알림 설정
     - 아침 브리핑 알림 토글 (08:35)
     - 밤 체크포인트 알림 토글 (22:00)
     - 긴급 뉴스 알림 토글
   - 섹션 3: 앱 정보
     - 버전 정보
     - 이용약관, 개인정보처리방침 링크
     - AI 기반 서비스 고지 (인공지능기본법 준수)
   - 각 설정은 Hive로 로컬 저장

3. `lib/features/settings/notification_settings_screen.dart` — 알림 상세 설정

**파일 소유권**: `lib/features/calendar/`, `lib/features/settings/`

---

### 3. Flutter-UIPolish
**담당**: 네비게이션 수정 + UI 폴리싱 + 공통 개선

**작업 내용**:

1. **라우터 수정** (`lib/config/router.dart`)
   - `/etf/:ticker` → `etf_detail_screen.dart` 연결 (placeholder 제거)
   - 모든 하위 화면에 뒤로가기 전환 애니메이션 추가 (slide from right)

2. **TabShell 수정** (`lib/features/feed/tab_shell.dart`)
   - placeholder를 실제 화면으로 교체:
     - index 1 → `MyEtfScreen()`
     - index 2 → `CalendarScreen()`
     - index 3 → `SettingsScreen()`

3. **온보딩 개선**
   - 온보딩 완료 여부 Hive에 저장
   - 재실행 시 온보딩 스킵 → 바로 `/home`
   - `lib/config/router.dart`의 `initialLocation`을 조건부로 변경

4. **공통 UI 개선**
   - 모든 Scaffold에 SafeArea 적용
   - 스크롤 시 AppBar 그림자/블러 효과
   - 로딩 상태: Shimmer 효과 (간단한 커스텀 위젯)
   - 에러 상태: 재시도 버튼 포함 에러 화면
   - 빈 상태: 아이콘 + 안내 텍스트

5. **Splash Screen**
   - `lib/features/splash/splash_screen.dart`
   - Portfiq 로고 (텍스트) + Indigo 그라데이션
   - 1초 후 온보딩 or 홈으로 자동 이동

**파일 소유권**: `lib/config/router.dart`, `lib/features/feed/tab_shell.dart`, `lib/features/splash/`

---

### 4. BE-DataSeed
**담당**: ETF 시드 데이터 업로드 + 실시간 가격 API + FCM 기반 구조

**작업 내용**:

1. ETF 시드 데이터 Supabase 업로드
   - `backend/seeds/seed_etf_master.py` 실행 → `etf_master` 테이블에 30종 ETF 삽입
   - 업로드 후 검증: `SELECT count(*) FROM etf_master` → 30

2. `backend/services/price_service.py` — 실시간 ETF 가격 (신규)
   - Yahoo Finance API (yfinance 패키지) 또는 무료 API
   - `GET /api/v1/etf/{ticker}/price` — 현재가 + 일간 등락률
   - 15분 캐시 (메모리 or Supabase)
   - `requirements.txt`에 `yfinance` 추가

3. `backend/routers/etf.py` — 가격 엔드포인트 추가
   - `GET /api/v1/etf/{ticker}/price` → `{"price": 485.23, "change_pct": 1.2, "change_amt": 5.73}`

4. FCM 기반 구조 (서버 사이드만, 실제 전송은 Firebase 프로젝트 설정 후)
   - `backend/services/push_service.py` — FCM 토큰 저장/전송 로직
   - `POST /api/v1/devices/register` — device_id + push_token 저장
   - `backend/jobs/briefing_scheduler.py` 수정 — 브리핑 생성 후 FCM 발송 호출

**파일 소유권**: `backend/seeds/`, `backend/services/price_service.py`, `backend/services/push_service.py`

---

### 5. QA-DevOps
**담당**: 전체 통합 검증

**작업 내용**:
1. `flutter analyze` → 에러 0
2. `flutter build web` → 빌드 성공
3. Backend import 검증 → 모든 모듈 정상
4. Python syntax 검증 → 에러 0
5. Supabase ETF 시드 데이터 확인 (30건)
6. API 스모크 테스트: `/api/v1/etf/popular`, `/api/v1/feed/latest`, `/api/v1/etf/QQQ/price`
7. 라우터 전체 경로 검증 (placeholder 없는지 확인)
8. iOS 시뮬레이터 빌드 테스트

**파일 소유권**: `tests/`

---

## 실행 순서

```
Phase 1 (병렬): Flutter-MyETF + Flutter-CalendarSettings + Flutter-UIPolish + BE-DataSeed
  ↓
Phase 2: QA-DevOps (전체 통합 검증)
```

## Notion 보고 규칙 (필수 — 반드시 지킬 것)

각 에이전트는 작업 **시작 시점**과 **완료 시점** 모두 Notion에 보고해야 한다.

```python
from integrations.notion.reporter import report_task_done, report_completion, add_task

# 작업 시작 시 — 반드시 진행중으로 변경
report_task_done("태스크명", "🔨 진행중")

# 작업 완료 시
report_task_done("태스크명", "✅ 완료", "결과 요약")
```

**상태 전이 필수**: `⏳ 진행 전` → `🔨 진행중` → `✅ 완료`
- `🔨 진행중` 없이 바로 `✅ 완료`로 가는 것은 금지

## 규칙
- 기존 Phase 1/2 코드 구조 최대한 유지
- 뒤로가기/네비게이션은 GoRouter + Navigator.pop() 활용
- 다크 모드 전용 — 라이트 모드 코드 금지
- 최소 터치 영역 44x44px
- 애니메이션: 화면 전환 250ms / 마이크로인터랙션 150ms
- 모든 인터랙션에 EventTracker 이벤트 삽입
- 환경변수 하드코딩 금지
- 모든 함수에 type hints + docstring (Python)
- 작업 완료 후 Notion 보고 (project_name="Portfiq (포트픽)")
