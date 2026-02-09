# 결정 로그

## DEC-2026-0203-SEC — Security-Developer 도입 + 운영 체계 고도화

- **일시**: 2026-02-03
- **결정자**: Human Lead
- **상태**: ✅ 승인

**결정 내용:**
1. Security-Developer (Sonnet 4.5, Level 3) 신설
2. 팀 설계 회의 (Design Discussion) 프로토콜 도입
3. 자율 QA 사이클 (Self-QA Loop) 도입
4. KPT 회고 체계화
5. 보안 품질 게이트 추가

**영향 범위:**
- CLAUDE.md v2.0.0 → v2.1.0
- OPERATING_PRINCIPLES.md v1.0.0 → v1.1.0
- 신규 에이전트 프로필: `.claude/agents/Security-Developer.md`
- 초기 보안 태스크 3건 등록 (TASK-SEC-001, 002, 003)

---

## 2026-02-02

### 프로젝트별 태스크 분리

**결정**: 태스크 API에 `project_id` 쿼리 파라미터 추가

**이유**:
- 기존에는 전역 태스크 레지스트리만 사용
- 프로젝트별로 태스크를 분리해야 독립적인 관리 가능

**구현**:
- `api/tasks.py`: 모든 엔드포인트에 `project_id` 파라미터 추가
- `services/file_sync.py`: 프로젝트별 경로로 레지스트리 관리
- 프론트엔드: `currentProject.id`를 API 호출 시 전달

### 기술 스택 개별 선택

**결정**: 백엔드/프론트엔드 스택을 개별적으로 선택 가능하게 변경

**이유**:
- 이전에는 `fastapi-react`, `express-vue` 같은 조합만 가능
- 사용자가 원하는 조합을 자유롭게 선택하고 싶어함

**구현**:
- `CreateProjectModal.jsx`: 백엔드/프론트엔드 선택 UI 분리
- `project_manager.py`: 각 스택별 구조 생성 메서드 추가

### UI 관측성 강화

**결정**: 에러 바운더리 및 API 로깅 추가

**이유**:
- 디버깅 시 사용자에게 스크린샷 요청 없이 문제 파악 필요
- API 실패 시 명확한 에러 메시지 표시 필요

**구현**:
- `ErrorBoundary.jsx`: React 에러 캐치 및 표시
- `api.js`: 구조화된 로깅 + 타임아웃 + 에러 처리
- `ApiStatus.jsx`: API 에러 상태 컴포넌트

### .env 로드 방식 변경

**결정**: `dotenv_values()` 사용하여 명시적 로드

**이유**:
- `pydantic-settings`가 `.env` 파일을 제대로 로드하지 못함
- `load_dotenv()`도 일부 환경에서 작동 안 함

**구현**:
```python
from dotenv import dotenv_values
env_values = dotenv_values(env_path)
os.environ.update(env_values)
```

---

## 2026-02-03

### IN_PROGRESS 태스크 상태 불일치 해결

**문제**: 일부 태스크가 대시보드에서 "진행중"으로 표시되지만 실제로 작업이 진행되지 않음

**원인**:
- 서버 재시작 시 메모리 상태는 초기화되지만 registry.json은 업데이트되지 않음
- 태스크 결과물(REVIEW 폴더)은 저장되었으나 상태가 IN_PROGRESS에서 멈춤

**해결**:
- TASK-003: 결과물 존재 확인 후 REVIEW 상태로 동기화
- TASK-007: 결과물 없음 확인 후 TODO로 변경 (재실행 필요)

**교훈**:
1. 서버 시작 시 REVIEW 폴더와 registry.json 자동 동기화 로직 필요
2. 태스크 실행 타임아웃 설정 및 자동 BLOCKED 전환 권장
3. 상태 변경 시 파일 시스템 검증 추가 고려

### Gemini API SDK 호환성

**결정**: `google-genai` 대신 `google-generativeai` 유지

**이유**:
- 사용자 환경에 `google-generativeai` 패키지가 설치되어 있음
- `google-genai`는 별도 패키지로 추가 설치 필요
- 기존 작동 코드 호환성 유지

**구현**:
```python
import google.generativeai as genai
genai.configure(api_key=settings.GEMINI_API_KEY)
self.model = genai.GenerativeModel(model_name)
```

### 시스템 아키텍처 개선 (v0.2.0)

**결정**: 비동기 I/O, DI, 구조화 로깅, 재시도 메커니즘 도입

**이유**:
1. 동기 파일 I/O가 이벤트 루프를 블로킹하여 성능 저하
2. 서비스 인스턴스 관리가 분산되어 있어 테스트 어려움
3. 로그 파싱 및 모니터링 어려움
4. API 실패 시 전체 파이프라인 중단

**구현**:

1. **비동기 파일 I/O (aiofiles)**
```python
async with aiofiles.open(path, "w") as f:
    await f.write(content)
```

2. **의존성 주입**
```python
FileSyncDep = Annotated[FileSyncService, Depends(get_file_sync_service)]
```

3. **구조화 로깅 (structlog)**
```python
logger = structlog.get_logger("module")
logger.info("이벤트", key="value")
```

4. **재시도 메커니즘 (tenacity)**
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def api_call():
    ...
```

### 상태 자동 복구

**결정**: 서버 시작 시 IN_PROGRESS 태스크 자동 검사 및 복구

**이유**:
- 서버 재시작 시 IN_PROGRESS 상태가 영구적으로 남는 문제
- 결과 파일이 있는데도 상태가 업데이트되지 않는 경우 존재

**구현**:
- `FileSyncService.initialize()`: 서버 시작 시 호출
- 결과 파일 존재 시 REVIEW로 전환
- 30분 이상 경과 시 BLOCKED로 전환
- `/api/tasks/sync` 엔드포인트로 수동 동기화 가능

### WebSocket 재연결 전략

**결정**: 지수 백오프(Exponential Backoff)와 Close Code 기반 재연결

**이유**:
- 단순 3초 고정 재연결은 서버 과부하 유발 가능
- 서버 재시작(1012)과 비정상 종료(1006)를 구분해야 함
- 정상 종료(1000)는 재연결하면 안 됨

**구현**:
```typescript
// useWebSocket.ts
const MAX_RECONNECT_ATTEMPTS = 10;
const BASE_RECONNECT_DELAY = 1000; // 1초
const MAX_RECONNECT_DELAY = 30000; // 30초

const getReconnectDelay = () => {
  const delay = Math.min(
    BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current),
    MAX_RECONNECT_DELAY
  );
  return delay * (0.5 + Math.random()); // 지터 추가
};
```

**Close Code별 처리**:
- `1000`: 정상 종료 - 재연결 안 함
- `1006`: 비정상 종료 - 지수 백오프로 재연결
- `1012`: 서버 재시작 - 카운트 리셋 후 2초 뒤 재연결

### TypeScript 마이그레이션

**결정**: 프론트엔드 핵심 파일을 TypeScript로 점진적 전환

**이유**:
- 타입 안전성으로 런타임 에러 방지
- IDE 자동완성 및 리팩토링 지원 개선
- 코드베이스 이해도 향상

**전환 파일**:
1. `src/types/index.ts`: 전체 타입 정의
2. `src/services/api.ts`: API 클라이언트
3. `src/stores/useStore.ts`: Zustand 스토어
4. `src/hooks/useWebSocket.ts`: WebSocket 훅

**TypeScript 설정**:
- `strict: true` 엄격 모드 활성화
- `noUncheckedIndexedAccess: true` 배열 접근 안전성
- 경로 별칭 (`@/*` → `src/*`)

### QA 자동화 스크립트

**결정**: `scripts/qa.sh`로 전체 품질 검사 자동화

**이유**:
- 수동 검사 누락 방지
- CI/CD 파이프라인 통합 준비
- 개발자 생산성 향상

**검사 항목**:
- Backend Lint (ruff/flake8)
- Backend Tests (pytest)
- Backend Import Check
- TypeScript Type Check
- Frontend Build
- Backend Health Check

---

## 2026-02-03 (운영 체계 고도화)

### 운영 원칙 문서 작성

**결정**: `.claude/docs/OPERATING_PRINCIPLES.md` 작성

**이유**:
- Multi-agent 시스템의 베스트 프랙티스 필요
- 일관된 작업 프로토콜 부재
- 에이전트 간 책임 분리 명확화 필요
- 로깅/모니터링 표준 부재

**구현 내용**:
1. **핵심 철학**: 점진적 확장, 투명성, 책임 분리
2. **역할 체계**: 계층 구조 및 권한 매트릭스
3. **작업 흐름**: 태스크 생명주기 및 체크리스트
4. **통신 프로토콜**: 메시지 형식, 에스컬레이션 규칙
5. **로깅**: 필수 항목, 레벨, 보존 기간
6. **오류 처리**: 분류 및 복구 전략

### 오더 템플릿 정식화

**결정**: `.claude/templates/ORDER_TEMPLATE.md` 작성

**이유**:
- 프로젝트 시작 시 명확한 지시 형식 필요
- DoD(Definition of Done) 표준화 필요
- 제약 조건/컨텍스트 명시 필요

**포함 항목**:
- 메타 정보 (ID, 우선순위, 복잡도)
- 목표 및 완료 기준
- 범위 (포함/제외 사항)
- 제약 조건 (기술적, 환경적, 시간적)
- 컨텍스트 참조
- 산출물 명세
- 리스크 및 대응
- 에이전트별 지시

### 에이전트 프로필 표준화

**결정**: 8개 에이전트 프로필을 v2.0.0으로 표준화

**이유**:
- 프로필 형식 불일치로 인한 혼란
- 권한/책임 경계 모호
- 핸드오프 형식 비표준
- 참조 문서 연결 부재

**표준화 구조**:
1. 기본 정보 (모델, 역할, 권한 레벨)
2. 핵심 임무
3. 작업 시작 전 필수 확인
4. 완료 기준 (DoD)
5. 산출물/코딩 표준
6. 의사결정 권한
7. 협업 규칙
8. 참조 문서
9. 금지 사항

**대상 에이전트**:
- Orchestrator
- PM-Planner
- Architect
- BE-Developer
- FE-Developer
- QA-DevOps
- AI-Engineer
- Designer

### CLAUDE.md 구조 개편

**결정**: CLAUDE.md를 v2.0.0으로 개편

**이유**:
- 새 운영 원칙 문서와의 연동 필요
- 참조 문서 체계 정립 필요
- 에이전트 체계 정보 갱신

**변경 내용**:
- 프로젝트 정보 테이블화
- 기술 스택 상세화 (Backend/Frontend/인프라)
- 작업 프로토콜에 운영 원칙 참조 추가
- 에이전트 체계 섹션 강화
- 참조 문서 섹션 신설
- 변경 이력 추가

### 자율 실행 모드 정의

**결정**: Human Lead 부재 시 자율 실행 프로토콜 명시

**이유**:
- 사용자 부재 시 작업 연속성 보장 필요
- 결정 로그 기록 의무화
- 에스컬레이션 기준 명확화

**프로토콜**:
1. 명확한 지시 범위 내에서 자율 진행
2. 모든 결정 사항 decisions-log.md에 기록
3. 에스컬레이션 필요 사항은 보류 후 목록화
4. 완료 시 상세 보고서 작성
