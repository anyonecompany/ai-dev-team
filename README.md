# AI Dev Team

Claude 에이전트 12명으로 구성된 AI 가상 개발팀 워크스페이스입니다. 레포를 클론하고 Claude Code를 실행하면 기획-설계-구현-검증-배포 전 과정을 에이전트 팀이 수행합니다. Notion + Slack 자동 보고, 보안 훅, GSD 워크플로우가 내장되어 있습니다.

---

## 워크플로우 선택

| 작업 크기 | 커맨드 | 흐름 |
|-----------|--------|------|
| Small (1-2 파일) | `/quick` | 실행 → lint → test → commit |
| Small (빠른 수정) | `/auto` | 계획 → 실행 → commit |
| Medium (3-5 파일) | `/plan` → `/orchestrate` → `/verify-loop` | 설계 → 병렬 구현 → 검증 |
| Large (5 파일+) | `/phase-loop` | discuss → plan → execute → verify → qa |
| CI 실패 | `/ci-fix` | 자동 진단 → 수정 → 검증 → 회고 |

---

## 인프라 현황

| 카테고리 | 수량 | 비고 |
|----------|------|------|
| 커맨드 | 31 | 7개 카테고리 |
| 스킬 | 10 | 프로젝트/공통/시스템 |
| 훅 | 12 | 7개 이벤트 트리거 |
| 에이전트 | 12 | Opus 4, Sonnet 7, Haiku 1 |
| 스크립트 | 17 | 자동화/모니터링 |
| 워크플로우 | 8 | GitHub Actions |
| Knowledge ADR | 7 | 아키텍처 의사결정 기록 |
| Knowledge 실수 | 7 | 시스템 레벨 반복 실수 |
| Knowledge 패턴 | 6 | 재사용 코드 패턴 |

---

## 커맨드 목록

### 탐색/설계

| 커맨드 | 설명 |
|--------|------|
| `/explore` | 코드베이스 탐색 |
| `/discuss` | 요구사항 토론, 결정사항 `.planning/CONTEXT.md` 저장 |
| `/plan` | 구현 계획 수립, `.planning/PLAN.md` 저장 |
| `/codemap-update` | 코드맵 갱신 |
| `/cross-ref` | 프로젝트 간 공통 패턴 조회 |

### 실행

| 커맨드 | 설명 |
|--------|------|
| `/auto` | 계획부터 커밋까지 원버튼 실행 |
| `/quick` | 1-2 파일 빠른 수정 + commit |
| `/quick-commit` | 간단한 수정용 빠른 커밋+push |
| `/orchestrate` | Agent Teams 병렬 오케스트레이션 |
| `/phase-loop` | discuss → plan → execute → verify → qa 전체 루프 |
| `/build-fix` | 빌드/타입 에러 점진적 수정 |
| `/ci-fix` | CI 실패 자동 진단 + 수정 |

### 검증

| 커맨드 | 설명 |
|--------|------|
| `/qa` | 전체 QA (린트 + 타입체크 + 테스트 + 빌드) |
| `/qa-fix` | QA 실행 + 실패 항목 자동 수정 |
| `/qa-report` | QA 결과 Notion + Slack 보고 |
| `/code-review` | 보안 + 품질 코드 리뷰 |
| `/verify-loop` | 자동 재검증 루프 (최대 3회) |
| `/handoff-verify` | 빌드/테스트/린트 한번에 검증 |

### 세션

| 커맨드 | 설명 |
|--------|------|
| `/session-save` | 작업 상태 핸드오프 문서로 저장 |
| `/session-restore` | 이전 세션 상태 복원 |
| `/checkpoint` | 작업 상태 저장/복원 (git patch) |
| `/retrospective` | 세션 회고 + knowledge 축적 |

### 모니터링

| 커맨드 | 설명 |
|--------|------|
| `/mcp-status` | MCP 연결 상태 확인 |
| `/usage-report` | 도구 사용량 리포트 |
| `/benchmark` | 에이전트 성능 벤치마크 |

### 프로젝트 전용

| 커맨드 | 설명 |
|--------|------|
| `/portfiq-design` | Portfiq 디자인 시스템 |
| `/portfiq-phase1` ~ `/portfiq-phase3` | Portfiq 단계별 실행 |
| `/portfiq-release` | Portfiq 릴리즈 |
| `/lapaz-structured-data` | La Paz 구조화 데이터 |

---

## 에이전트 팀

### Opus (기획/설계/감독) - 4명

| 에이전트 | 역할 |
|----------|------|
| PM-Planner | 요구사항 분석, 태스크 분해, MVP 정의 |
| Architect | 시스템 설계, API/DB 스키마, 기술 의사결정 |
| Tech-Lead | 기획+설계+오케스트레이션+게이트 승인 (통합 리더) |
| CTO-Agent | 엔지니어링 메트릭 분석, 아키텍처 건강성 리뷰 |

### Sonnet (구현/검증) - 7명

| 에이전트 | 역할 |
|----------|------|
| BE-Developer | FastAPI/Python 백엔드 구현 |
| FE-Developer | React/TypeScript 프론트엔드 구현 |
| AI-Engineer | LLM 프롬프트 설계, AI API 연동 |
| Security-Developer | 보안 감사, OWASP Top 10, 시큐어 코딩 |
| QA-Engineer | 테스트+보안 점검+배포 승인 (통합 게이트 키퍼) |
| Orchestrator | 전체 워크플로우 지휘, 에이전트 조율 |
| Designer | UI/UX 디자인 시스템 생성, 컴포넌트 스펙 |

### Haiku (자동화) - 1명

| 에이전트 | 역할 |
|----------|------|
| QA-DevOps | 테스트, CI/CD, 배포 관리 |

---

## 스킬 시스템

### 프로젝트 전용

| 스킬 | 설명 |
|------|------|
| `portfiq-dev` | Portfiq 프로젝트 개발 컨텍스트 |
| `lapaz-dev` | La Paz 프로젝트 개발 컨텍스트 |

### 공통

| 스킬 | 설명 |
|------|------|
| `code-quality` | 코드 품질 검증 |
| `security-review` | 보안 리뷰 |
| `deployment` | 배포 관리 |
| `codemap-update` | 코드맵 갱신 |

### 시스템

| 스킬 | 설명 |
|------|------|
| `session-wrap` | 세션 저장/복원 |
| `verification-engine` | 증거 기반 검증 엔진 |
| `build-system` | 빌드 시스템 관리 |
| `context-compact` | 컨텍스트 압축 |

---

## 규율 시스템 (자동 강제)

12개 훅이 7개 이벤트에서 자동 실행되어 규율을 강제합니다.

| 이벤트 | 훅 | 역할 |
|--------|-----|------|
| PreToolUse | `remote-command-guard` | 파괴적 삭제, 시크릿 유출, 명령 주입 차단 |
| PreToolUse | `db-guard` | DROP/TRUNCATE/DELETE without WHERE 차단 |
| PostToolUse | `output-secret-filter` | API 키/토큰 자동 마스킹 |
| PostToolUse | `security-auto-trigger` | 보안 민감 파일 수정 시 리뷰 권고 |
| PostToolUse | `auto-format` | 파일 저장 시 자동 포맷팅 |
| PostToolUse | `tool-usage-logger` | 모든 도구 호출 기록 |
| Stop | `verify-on-stop` | lint/테스트/회고 넛지 |
| UserPromptSubmit | `skill-suggest` | 관련 스킬 자동 추천 |
| SessionStart | `session-start-check` | codemap 신선도 + 비용 체크 |
| SubagentStart/Stop | `agent-activity-logger` | 에이전트 활동 기록 |
| PostToolUse | `context-monitor` | 컨텍스트 사용량 모니터링 |
| PreToolUse | `workflow-gate` | 워크플로우 게이트 검증 |

deny 패턴: `git push --force`, `git reset --hard`, `rm -rf /`, `rm -rf ~`, `chmod 777`, `mkfs`, `dd if=` 자동 차단

---

## 프로젝트

| 프로젝트 | 설명 | 상태 | 배포 |
|----------|------|------|------|
| Portfiq | AI 투자 뉴스 브리핑 앱 (Flutter + FastAPI) | 진행중 | portfiq.fly.dev |
| La Paz Live | 실시간 축구 팬 Q&A (React + FastAPI + Gemini) | 진행중 | Vercel + Fly.io |
| La Paz Crawl | 축구 데이터 자동 크롤링 파이프라인 | 운영중 | GitHub Actions |
| Tactical GNN | 축구 전술 GNN 분석 | 탐색 | - |
| AdaptFit AI | 적응형 운동 추천 | 탐색 | - |

---

## 시작하기

```bash
# 1. 레포 클론
git clone https://github.com/anyonecompany/ai-dev-team.git
cd ai-dev-team

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력

# 3. tmux 세션에서 Claude Code 실행
brew install tmux  # 최초 1회
tmux new -s dev
claude
```

### 환경변수 (.env)

| 변수명 | 설명 | 발급처 |
|--------|------|--------|
| `GEMINI_API_KEY` | Google Gemini API 키 | [Google AI Studio](https://aistudio.google.com/) |
| `NOTION_API_KEY` | Notion 통합 토큰 | [Notion Developers](https://developers.notion.com/) |
| `NOTION_TASK_DB_ID` | Notion 태스크 DB ID | Notion 워크스페이스 |
| `NOTION_PROJECT_DB_ID` | Notion 프로젝트 DB ID | Notion 워크스페이스 |
| `NOTION_DECISION_DB_ID` | Notion 의사결정 DB ID | Notion 워크스페이스 |
| `NOTION_TECHREF_DB_ID` | Notion 기술레퍼런스 DB ID | Notion 워크스페이스 |
| `SLACK_WEBHOOK_URL` | Slack 웹훅 URL | [Slack API](https://api.slack.com/messaging/webhooks) |

---

## 모니터링

```bash
# 코드맵 신선도 체크
./scripts/codemap-freshness.sh

# 비용 알림
./scripts/cost-alert.sh

# 에이전트 벤치마크
./scripts/agent-benchmark.sh

# 토큰 사용량 리포트
./scripts/token-report.sh

# QA 게이트 실행
./scripts/qa-gate.sh <project-path>

# 런타임 검증
./scripts/runtime-check.sh <project-path>
```

---

## 보고 시스템

모든 작업은 Notion + Slack에 자동 보고됩니다.

```python
from integrations.notion.reporter import (
    report_task_done, report_decision, report_techref,
    report_completion, add_project, add_task,
)
```

---

## 라이선스

Private -- AnyOne Company 내부 사용
