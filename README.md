# AI Dev Team

Claude 에이전트 팀 기반의 AI 개발 워크스페이스입니다.

## 구조

- `projects/` - 모든 개발 프로젝트가 하위 폴더로 생성됩니다
- `integrations/` - Slack, Monday.com 연동 모듈
- `tasks/` - 글로벌 태스크 관리 (prd.json, progress.md)
- `scripts/` - 공용 스크립트
- `.claude/` - Claude 에이전트 설정, 커맨드, 템플릿

## QA 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/qa` | 전체 QA 실행 (린트 + 타입체크 + 테스트 + 빌드) |
| `/qa-fix` | QA 실행 + 실패 항목 자동 수정 |
| `/qa-report` | QA 결과를 Slack/Monday.com에 공유 |

## 프로젝트 생성

새 프로젝트는 `projects/` 하위에 자동 생성됩니다.
폴더명 형식: `{project-name}-{YYYYMMDDHHMMSS}`

## 연동

- **Slack**: 프로젝트 생성, 태스크 변경, QA 결과 자동 알림
- **Monday.com**: 태스크 상태 동기화, 프로젝트 그룹 관리
