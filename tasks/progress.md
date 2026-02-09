# Progress Log

반복 과정에서 얻은 교훈을 기록합니다.

---

## Iteration 1: S1 - CI green baseline

**날짜:** 2026-02-05

### 검증 결과
- pytest: 25 passed (수정 후)
- tsc + vite build: PASS
- eslint: 설정 파일 필요 (ESLint 9.x 마이그레이션 필요)

### 수정 사항
1. **`tests/test_monday_sync.py`** - `test_is_monday_enabled_without_token` 테스트 수정
   - 문제: 실제 `.env` 파일에서 토큰이 로드되어 테스트 실패
   - 해결: `monkeypatch.setattr()`로 모듈 레벨 변수 직접 패치

### 교훈
- 환경 변수 테스트 시 `monkeypatch.delenv()`만으로는 부족할 수 있음
- `load_dotenv()`가 모듈 로드 시점에 실행되면 모듈 레벨 변수를 직접 패치해야 함
- ESLint 9.x는 `eslint.config.js` 형식의 새 설정 파일이 필요함

---

## Iteration 2: S2 - 스토리 생성 UI 구현

**날짜:** 2026-02-05

### 검증 결과
- pytest: 36 passed (11개 새 테스트 추가)
- tsc + vite build: PASS
- Frontend test: N/A (테스트 스크립트 미설정)

### 구현 사항
1. **`backend/api/prd.py`** - PRD CRUD API 엔드포인트
   - `POST /api/queue/prd` - 새 스토리 생성
   - `PUT /api/queue/prd/{story_id}` - 스토리 업데이트
   - `DELETE /api/queue/prd/{story_id}` - 스토리 삭제
   - Pydantic 모델로 요청 검증 (`StoryCreate`, `StoryUpdate`)

2. **`frontend/src/components/queue/StoryCreationForm.jsx`** - 스토리 생성 폼
   - ID, Priority, Title, Acceptance, Verify 필드 입력
   - 동적 배열 필드 (추가/삭제 버튼)
   - 중복 ID 에러 핸들링
   - 다크 테마 스타일 적용

3. **`frontend/src/components/queue/WorkQueuePanel.jsx`** - 폼 통합
   - StoryCreationForm 컴포넌트 포함
   - 스토리 생성 후 자동 새로고침

4. **`backend/tests/test_prd_api.py`** - API 테스트
   - 11개 테스트 케이스 (CRUD + 에러 케이스)

### 교훈
- FastAPI의 Pydantic 모델로 요청 검증을 하면 타입 안전성과 자동 문서화가 보장됨
- React 폼에서 동적 배열 필드는 인덱스 기반 상태 관리가 깔끔함
- `unittest.mock.patch`로 모듈 레벨 상수를 패치하면 테스트 격리가 쉬움
- WorkQueuePanel에서 콜백 패턴으로 자식 컴포넌트 이벤트를 처리하면 상태 관리가 단순해짐

---

## Iteration 3: S3 - 스토리 편집/삭제 UI 구현

**날짜:** 2026-02-05

### 검증 결과
- pytest: 36 passed
- tsc + vite build: PASS

### 구현 사항
1. **`frontend/src/components/queue/StoryEditModal.jsx`** - 스토리 편집 모달
   - Priority, Title, Acceptance, Verify, Passes 필드 수정
   - ID는 읽기 전용으로 표시
   - 동적 배열 필드 지원
   - Passes 토글 스위치 추가
   - PUT `/api/queue/prd/{story_id}` 호출

2. **`frontend/src/components/queue/StoryDeleteButton.jsx`** - 스토리 삭제 버튼
   - 확인 모달로 실수 방지
   - DELETE `/api/queue/prd/{story_id}` 호출
   - 삭제 후 자동 새로고침

3. **`frontend/src/components/queue/WorkQueuePanel.jsx`** - 편집/삭제 UI 통합
   - StoryCard에 편집/삭제 버튼 추가
   - editingStory 상태로 모달 제어
   - 콜백 패턴으로 CRUD 후 자동 갱신

### 교훈
- 모달 컴포넌트는 `isOpen` prop과 `onClose` 콜백 패턴이 재사용성에 좋음
- 삭제 기능은 확인 모달을 통해 사용자 실수를 방지하는 것이 필수
- 부모 컴포넌트에서 상태를 관리하고 자식에게 콜백을 전달하면 데이터 흐름이 명확함
- 기존 API 엔드포인트(PUT/DELETE)를 재사용하여 프론트엔드만 구현하면 개발 속도가 빨라짐

---

## Iteration 4: S4 - 인스타그램 메트릭스 패널 구현

**날짜:** 2026-02-05

### 검증 결과
- pytest: 40 passed (4개 새 테스트 추가)
- tsc + vite build: PASS

### 구현 사항
1. **`backend/api/instagram.py`** - Instagram 메트릭스 API
   - `GET /api/instagram/metrics` - 메트릭스 조회
   - `GET /api/instagram/health` - 헬스 체크
   - Pydantic 모델 `InstagramMetrics` 정의
   - Mock 데이터: followerCount=1234, engagementRate=0.045 등

2. **`frontend/src/components/instagram/InstagramMetricsPanel.jsx`** - 메트릭스 패널
   - 6개 메트릭 카드: Followers, Engagement Rate, Avg. Likes, Avg. Comments, Reach Rate, Impressions
   - Instagram 브랜드 그라디언트 헤더
   - 숫자 포맷팅 (K, M 단위)
   - 퍼센트 포맷팅
   - 1분 간격 자동 갱신
   - Mock Data 표시

3. **`frontend/src/pages/DashboardPage.jsx`** - 대시보드 통합
   - InstagramMetricsPanel을 WorkQueuePanel 위에 배치
   - 스크롤 가능한 사이드 패널

4. **`backend/tests/test_instagram_api.py`** - API 테스트
   - 4개 테스트 케이스 (메트릭스 조회, 값 검증, 타입 검증, 헬스 체크)

### 교훈
- Mock 데이터 패턴으로 API 설계를 먼저 하면 프론트엔드 개발이 병렬로 가능함
- Pydantic `response_model`을 사용하면 자동 문서화 + 응답 검증이 됨
- 메트릭 카드 컴포넌트는 icon, label, value, color props로 재사용성 높임
- `formatNumber`, `formatPercent` 유틸리티 함수로 숫자 표시 일관성 유지
- 외부 API 연동 전에 Mock 모드를 명시적으로 표시하면 개발 중 혼란 방지

---

## Iteration 5: S5 - 에이전트 할당 UI 구현

**날짜:** 2026-02-05

### 검증 결과
- pytest: 47 passed (7개 새 테스트 추가)
- tsc + vite build: PASS

### 구현 사항
1. **`backend/api/prd.py`** - 에이전트 관련 기능 추가
   - `GET /api/queue/agents` - .claude/agents/*.md 파일 목록 반환
   - `StoryCreate`, `StoryUpdate` 모델에 `agent: Optional[str]` 필드 추가
   - 스토리 생성/수정 시 agent 필드 저장

2. **`frontend/src/components/queue/WorkQueuePanel.jsx`** - 에이전트 UI 통합
   - agents 상태 추가 및 fetchData에서 에이전트 목록 로드
   - StoryCard에 에이전트 드롭다운 추가
   - handleAgentChange로 선택 시 PUT 요청 자동 전송
   - 선택된 에이전트 뱃지 표시

3. **`frontend/src/components/queue/StoryCreationForm.jsx`** - 에이전트 선택 추가
   - agents prop 수신
   - 에이전트 선택 드롭다운 필드 추가
   - 기본값 "미할당"

4. **`frontend/src/components/queue/StoryEditModal.jsx`** - 편집 시 에이전트 지원
   - agents prop 수신
   - 에이전트 선택 드롭다운 필드 추가

5. **`backend/tests/test_prd_api.py`** - 테스트 추가
   - 에이전트 지정 스토리 생성 테스트
   - 에이전트 업데이트 테스트
   - 에이전트 목록 조회 테스트 (빈 목록, 파일 있음, 정렬, 디렉토리 없음)

### 교훈
- 파일 시스템 기반 에이전트 목록은 설정 파일 없이 구조만으로 확장 가능
- Pydantic `exclude_none=True`는 명시적 null 설정을 무시하므로 주의 필요
- 드롭다운 onchange에서 직접 PUT 요청을 보내면 UX가 즉각적임
- 부모 컴포넌트에서 agents를 한 번 fetch하고 자식에게 전달하면 중복 요청 방지
- 테스트에서 임시 디렉토리 fixture를 사용하면 파일 시스템 테스트가 격리됨

---

## Iteration 6: S6 - 스토리 리스트 필터링 및 정렬 기능

**날짜:** 2026-02-05

### 검증 결과
- pytest: 47 passed
- tsc + vite build: PASS

### 구현 사항
1. **`frontend/src/components/queue/WorkQueuePanel.jsx`** - 필터/정렬 기능 추가
   - 상태(statusFilter): all, pending, passed 필터
   - 에이전트(agentFilter): all, unassigned, 특정 에이전트 필터
   - 정렬 기준(sortBy): priority, id
   - 정렬 순서(sortOrder): asc, desc
   - `useMemo`로 필터링/정렬 로직 최적화
   - 접이식 필터 컨트롤 패널
   - 빠른 정렬 토글 버튼
   - 활성 필터 뱃지 및 초기화 버튼
   - 필터 결과가 없을 때 빈 상태 UI

### 교훈
- `useMemo`로 파생 데이터를 캐싱하면 렌더링 성능이 향상됨
- 접이식 컨트롤 패널로 UI 복잡도를 관리하면서도 기능 접근성 유지
- 활성 필터 상태를 시각적으로 표시(뱃지, 인디케이터)하면 사용자 경험 개선
- 필터 결과가 없을 때 빈 상태 UI와 초기화 버튼을 제공하면 사용자 혼란 방지
- 클라이언트 사이드 필터/정렬은 데이터가 적을 때(수십 개 이하) 서버 부담 없이 즉각 반응

---

## Iteration 7: S7 - 반복 기록(Iteration History) 패널 구현

**날짜:** 2026-02-05

### 검증 결과
- pytest: 52 passed (5개 새 테스트 추가)
- tsc + vite build: PASS

### 구현 사항
1. **`backend/api/prd.py`** - 반복 기록 파서 및 API 추가
   - `_parse_progress_md()` 함수로 progress.md 파싱
   - 정규식으로 `## Iteration N: SX - Title` 패턴 분리
   - 날짜, 검증 결과, 수정/구현 사항, 교훈 섹션 추출
   - `GET /api/queue/history` 엔드포인트 추가

2. **`frontend/src/components/queue/IterationHistoryPanel.jsx`** - 반복 기록 패널
   - 아코디언 형식의 반복 카드 컴포넌트
   - 클릭하여 상세 교훈/검증 결과 펼치기
   - 최신순 정렬 (내림차순)
   - 30초 간격 자동 새로고침
   - 검증 결과에 따른 색상 분류 (pass=green, fail=red)

3. **`frontend/src/pages/DashboardPage.jsx`** - 대시보드 통합
   - IterationHistoryPanel을 사이드 패널에 추가

4. **`backend/tests/test_prd_api.py`** - 테스트 추가
   - 빈 기록 조회, 데이터 있는 기록 조회, 정렬 확인
   - 파서 단위 테스트 (빈 파일, 반복 없는 파일)

### 교훈
- Markdown 파싱은 정규식으로 섹션을 분리한 후 각 섹션을 개별 파싱하면 복잡도가 줄어듦
- `re.DOTALL` 플래그로 여러 줄에 걸친 패턴 매칭 가능
- 아코디언 UI는 상태 ID로 펼침 여부를 관리하면 단일 열림 동작 구현이 쉬움
- 테스트에서 실제 progress.md 형식을 그대로 사용하면 파서 로직 검증이 정확함
- 30초 자동 새로고침으로 새 반복이 기록될 때 사용자가 수동 새로고침 없이 확인 가능

---

## Iteration 8: S8 - n8n QA 트리거 통합

**날짜:** 2026-02-05

### 검증 결과
- pytest: 56 passed (4개 새 테스트 추가)
- tsc + vite build: PASS

### 구현 사항
1. **`backend/core/config.py`** - N8N 웹훅 설정 추가
   - `N8N_QA_WEBHOOK_URL` 환경 변수 설정

2. **`backend/api/prd.py`** - QA 실행 API 추가
   - `POST /api/queue/qa/run` 엔드포인트
   - httpx.AsyncClient로 비동기 웹훅 호출
   - 환경 변수 미설정 시 400 에러
   - 타임아웃(504), 요청 실패(502) 처리
   - PRD 요약 정보를 페이로드로 전송

3. **`frontend/src/components/queue/WorkQueuePanel.jsx`** - QA 버튼 추가
   - 헤더에 Play 아이콘 QA 실행 버튼
   - qaRunning, qaResult 상태로 실행 중/결과 표시
   - 성공/실패에 따른 색상 구분 알림
   - 5초 후 자동 숨김, X 버튼으로 수동 닫기

4. **`backend/tests/test_prd_api.py`** - 테스트 추가
   - 웹훅 URL 미설정 테스트
   - 웹훅 호출 성공 테스트
   - 웹훅 에러 응답 테스트
   - 타임아웃 테스트

### 교훈
- httpx.AsyncClient는 FastAPI와 함께 쓰기 좋은 비동기 HTTP 클라이언트
- 테스트에서 AsyncMock과 MagicMock을 혼용할 때 response.json()은 MagicMock 사용 (동기 메서드)
- 환경 변수 기반 기능은 미설정 시 명확한 에러 메시지 반환 필요
- 웹훅 호출 시 타임아웃, 연결 실패 등 다양한 예외 처리 필수
- Toast 스타일 알림은 자동 숨김 + 수동 닫기 둘 다 지원하면 UX 개선

---

## Iteration 9: S9 - Instagram API 실데이터 연동

**날짜:** 2026-02-05

### 검증 결과
- pytest: 60 passed (8개 새 테스트 추가, 기존 4개 교체)
- tsc + vite build: PASS

### 구현 사항
1. **`backend/core/config.py`** - Instagram 환경 변수 추가
   - `INSTAGRAM_USER_ID`: Instagram Business Account ID
   - `INSTAGRAM_ACCESS_TOKEN`: Graph API Access Token

2. **`backend/api/instagram.py`** - 실데이터 연동
   - `fetch_instagram_live_data()` 비동기 함수 추가
   - Instagram Graph API v18.0 호출:
     - 계정 정보 (followers_count, follows_count, media_count)
     - 인사이트 (reach, impressions)
     - 미디어 (like_count, comments_count)
   - 인게이지먼트율, reach_rate, impressions_rate 계산
   - 환경 변수 미설정/API 실패 시 `get_mock_metrics()` fallback
   - `InstagramMetrics` 모델에 `source: Literal["live", "mock"]` 필드 추가
   - 헬스 체크 엔드포인트에서 실제 연결 테스트

3. **`frontend/src/components/instagram/InstagramMetricsPanel.jsx`** - 출처 표시
   - 헤더에 source 배지: "실데이터" (green) / "모킹" (amber)
   - 푸터에 "Instagram Graph API" / "Mock Data" 텍스트

4. **`backend/tests/test_instagram_api.py`** - 테스트 리팩토링
   - 환경 변수 미설정 시 fallback 테스트
   - 실데이터 조회 성공 테스트 (API 모킹)
   - API 에러 시 fallback 테스트
   - 타임아웃 시 fallback 테스트
   - 헬스 체크 테스트 (credentials 유무)

### 교훈
- Instagram Graph API는 여러 엔드포인트(계정, 인사이트, 미디어)를 조합해야 완전한 메트릭 구성 가능
- 외부 API 연동 시 fallback 패턴은 서비스 안정성에 필수
- Pydantic의 `Literal` 타입으로 열거형 필드를 정의하면 타입 안전성 확보
- 테스트에서 httpx.AsyncClient 모킹 시 `side_effect`로 여러 순차 응답 시뮬레이션
- 프론트엔드에서 데이터 출처를 명시하면 사용자 신뢰도 향상

---

