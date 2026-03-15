# AI Dev Team

Claude 에이전트 팀 기반의 AI 가상 개발팀 워크스페이스입니다.
레포를 클론하면 Claude Code에서 즉시 에이전트 팀을 운영할 수 있습니다.

## 빠른 시작

```bash
# 1. 레포 클론
git clone https://github.com/anyonecompany/ai-dev-team.git
cd ai-dev-team

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력 (아래 환경변수 설정 참고)

# 3. tmux 세션에서 Claude Code 실행
brew install tmux  # 최초 1회
tmux new -s dev
claude
```

## 환경변수 설정 (.env)

`.env` 파일에 아래 키들을 설정해야 합니다.

### 필수

| 변수명 | 설명 | 발급처 |
|--------|------|--------|
| `GEMINI_API_KEY` | Google Gemini API 키 (AI 호출용) | [Google AI Studio](https://aistudio.google.com/) |
| `NOTION_API_KEY` | Notion 통합 토큰 | [Notion Developers](https://developers.notion.com/) |
| `NOTION_TASK_DB_ID` | Notion 태스크 DB ID | Notion 워크스페이스 |
| `NOTION_PROJECT_DB_ID` | Notion 프로젝트 DB ID | Notion 워크스페이스 |
| `NOTION_DECISION_DB_ID` | Notion 의사결정 DB ID | Notion 워크스페이스 |
| `NOTION_TECHREF_DB_ID` | Notion 기술레퍼런스 DB ID | Notion 워크스페이스 |
| `SLACK_WEBHOOK_URL` | Slack 웹훅 URL (알림용) | [Slack API](https://api.slack.com/messaging/webhooks) |

### 선택 (프로젝트별)

| 변수명 | 설명 |
|--------|------|
| `PORTFIQ_GEMINI_API_KEY` | Portfiq 전용 Gemini 키 (분리 추적용) |
| `PORTFIQ_SUPABASE_URL` | Portfiq Supabase URL |
| `PORTFIQ_SUPABASE_ANON_KEY` | Portfiq Supabase Anon 키 |
| `PORTFIQ_SUPABASE_SERVICE_KEY` | Portfiq Supabase Service 키 |

## 구조

```
ai-dev-team/
├── .claude/              ← 에이전트 설정 (핵심)
│   ├── CLAUDE.md         ← 마스터 헌장 (모든 규칙의 시작점)
│   ├── agents/           ← 에이전트 프로필 (PM, Architect, BE/FE 등)
│   ├── commands/         ← 슬래시 커맨드 (19개)
│   ├── rules/            ← 코딩/검증/Git 규칙 (6개)
│   ├── hooks/            ← 보안 자동화 훅 (4개)
│   ├── skills/           ← 스킬 (3개)
│   ├── docs/             ← 운영 문서, 법규 가이드
│   ├── templates/        ← 프로젝트/태스크 템플릿
│   ├── knowledge/        ← 지식 베이스 (패턴, 실수 기록)
│   └── handoff/          ← 인수인계 문서
├── integrations/         ← 외부 서비스 연동
│   ├── notion/           ← Notion 자동 보고 (reporter.py)
│   ├── slack/            ← Slack 웹훅 알림
│   └── shared/           ← 공용 포맷팅 유틸
├── projects/             ← 개발 프로젝트 (각 프로젝트는 자체 레포 관리)
├── scripts/              ← 공용 스크립트
├── design-system/        ← UI/UX 디자인 시스템
└── tasks/                ← 글로벌 태스크 관리
```

## 에이전트 팀

| 역할 | 모델 | 주요 책임 |
|------|------|----------|
| PM-Planner | Opus | 요구사항 분석, 태스크 분해 |
| Architect | Opus | 시스템 설계, API/DB 스키마 |
| BE-Developer | Sonnet | 백엔드 구현 (FastAPI/Python) |
| FE-Developer | Sonnet | 프론트엔드 구현 (React/TypeScript) |
| AI-Engineer | Sonnet | ML/AI 기능 구현 |
| QA-DevOps | Haiku | 테스트, 배포, CI/CD |
| Security-Developer | Sonnet | 보안 감사, 시큐어 코딩 |
| Orchestrator | Sonnet | 팀 조율, 상태 관리 |

## 주요 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/plan` | AI가 구현 계획을 세움 |
| `/auto` | 계획부터 커밋까지 원버튼 실행 |
| `/qa` | 전체 QA 실행 (린트 + 타입체크 + 테스트 + 빌드) |
| `/qa-fix` | QA 실행 + 실패 항목 자동 수정 |
| `/code-review` | 보안 + 품질 코드 리뷰 |
| `/verify-loop` | 자동 재검증 루프 (최대 3회 재시도) |
| `/build-fix` | 빌드/타입 에러 점진적 수정 |
| `/orchestrate` | Agent Teams 병렬 오케스트레이션 |
| `/handoff-verify` | 빌드/테스트/린트 한번에 검증 |
| `/checkpoint` | 작업 상태 저장/복원 (git patch) |
| `/quick-commit` | 간단한 수정용 빠른 커밋+push |
| `/explore` | 코드베이스 탐색 |

## 보안 훅 (자동 적용)

| 훅 | 역할 |
|---|------|
| `remote-command-guard.sh` | 파괴적 삭제, 시크릿 유출, 명령 주입 차단 |
| `db-guard.sh` | DROP/TRUNCATE/DELETE without WHERE 차단 |
| `output-secret-filter.sh` | 도구 출력에서 API 키/토큰 자동 마스킹 |
| `security-auto-trigger.sh` | 보안 민감 파일 수정 시 리뷰 권고 |

## 보고 시스템

모든 작업은 **Notion + Slack**에 자동 보고됩니다.

```python
from integrations.notion.reporter import (
    report_task_done, report_decision, report_techref,
    report_completion, add_project, add_task,
)
```

## 프로젝트 관리

- `projects/` 하위에 프로젝트 폴더가 생성되지만, **각 프로젝트는 자체 Git 레포**에서 관리됩니다
- ai-dev-team 레포에는 가상 개발팀 인프라만 커밋합니다
- 새 프로젝트 시작 시 Notion에 자동 등록됩니다

## 기술 스택

- **에이전트**: Claude Code (Opus 4.6 기반)
- **AI API**: Google Gemini (gemini-2.5-flash / flash-lite)
- **보고**: Notion API + Slack Webhook
- **프로젝트별**: Python/FastAPI, React/TypeScript, Flutter 등 자유 선택

## 라이선스

Private — AnyOne Company 내부 사용
