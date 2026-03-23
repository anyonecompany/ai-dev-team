# 코드 패턴

> 최종 갱신: 2026-03-23
> 출처: 코드베이스 분석 기반

기존 개별 패턴 파일(supabase-connection, fastapi-error-handling 등)은 `patterns/` 디렉토리 참조.
이 문서는 프로젝트 전반에서 반복 사용되는 상위 패턴을 인덱싱한다.

---

## P-001: 환경변수 계층 탐색 (.env cascade)
- **구조**: 프로젝트 config.py에서 `.env` 파일을 여러 디렉토리 레벨에서 탐색. `backend/.env` → `project/.env` → `projects/.env` → `ai-dev-team/.env` 순서로 찾아 첫 번째 발견 파일을 로드
- **적용처**: `projects/portfiq/backend/config.py`, `projects/lapaz-live/backend/config.py`
- **주의사항**: 여러 레벨에 `.env`가 존재하면 가장 가까운 파일만 로드됨. `override=True` 옵션으로 기존 환경변수를 덮어쓰므로 시스템 환경변수와 충돌 가능

## P-002: Notion + Slack 통합 보고 패턴
- **구조**: `report_completion()` 한 번 호출로 태스크 상태 변경 + 의사결정 기록 + 기술 레퍼런스 등록 + 후속 태스크 생성 + Slack 알림을 일괄 처리. `project_name`을 한 번만 지정하면 하위 항목에 자동 전파
- **적용처**: `integrations/notion/reporter.py` (모든 프로젝트 공통)
- **주의사항**: `project_name` 누락 시 고아 데이터 발생. `done_criteria`와 `alternatives` 없으면 경고 로그 출력. Slack 웹훅 실패는 silent fail (보고 자체는 계속 진행)

## P-003: Settings 클래스 기반 설정 관리
- **구조**: `os.getenv()`로 환경변수를 읽되, `Settings` 클래스에 모든 설정을 중앙 집중. 기본값은 개발 환경용으로 설정. 여러 환경변수 키를 OR로 연결하여 fallback 제공 (`PORTFIQ_GEMINI_API_KEY` or `GEMINI_API_KEY`)
- **적용처**: 모든 프로젝트의 `backend/config.py`
- **주의사항**: pydantic-settings가 아닌 plain class를 사용하므로 타입 검증은 수동. `int()` 변환 시 환경변수 미설정이면 `ValueError` 발생 가능

## P-004: Slack 웹훅 동기/비동기 이중 구현
- **구조**: `integrations/notion/reporter.py`에서는 `httpx.post()` 동기 호출 (Notion 보고는 동기 컨텍스트). `integrations/slack/slack_notifier.py`에서는 `httpx.AsyncClient` 비동기 호출 (FastAPI 라우터에서 사용)
- **적용처**: Notion 보고 모듈 (동기), 서비스 레이어 알림 (비동기)
- **주의사항**: 동기 버전에서 timeout 5초 하드코딩. 웹훅 URL 미설정 시 early return으로 silent skip. 에러 시 warning 로그만 남기고 예외 전파 안 함

## P-005: 연쇄 fix 패턴 (점진적 안정화)
- **구조**: 복잡한 기능(OAuth, 배포, 비동기 작업)은 한 번에 완성되지 않고 3~5건의 연쇄 fix 커밋으로 안정화. 첫 구현 → 엣지케이스 발견 → 근본 원인 수정 → 최종 안정화
- **적용처**: OAuth 콜백(4건), event loop 블로킹(3건), CORS/타임아웃(5건+)
- **주의사항**: 첫 fix에서 "해결" 선언하지 말 것. 복잡한 기능은 최소 3일 모니터링 후 안정화 판단. git log에서 같은 영역 fix가 3건 이상이면 근본 원인 재검토 필요

## P-006: 갭 분석 기반 개선 사이클
- **구조**: 현재 상태를 체계적으로 진단(갭 분석) → Critical/Major/Minor 분류 → 우선순위순 일괄 수정 → QA 리포트 발행
- **적용처**: Portfiq 출시 준비 (`1099686` → `05eb5e9` → `87ee399`), QA 감사 기반 버그 수정 (`036bbfc`)
- **주의사항**: 갭 분석 결과를 문서화하지 않으면 같은 이슈 재발. QA는 정적 검증뿐 아니라 실사용자 플로우 검증 필수

---

## 기존 개별 패턴 파일 인덱스

| 파일 | 설명 |
|------|------|
| `supabase-connection.md` | 싱글톤 DB 클라이언트 패턴 |
| `fastapi-error-handling.md` | structlog 기반 에러/로깅 패턴 |
| `crud-service.md` | 서비스 레이어 CRUD 추상화 |
| `auth-supabase.md` | Supabase Auth 통합 패턴 |
| `react-api-client.md` | 타입 안전 API 클라이언트 패턴 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-23 | 코드베이스 분석 기반 상위 패턴 6건 신규 작성 + 기존 파일 인덱스 추가 |
