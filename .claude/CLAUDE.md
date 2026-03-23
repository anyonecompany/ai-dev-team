# 프로젝트 중앙 제어 헌장 (Master Charter)

> 버전: 3.2.0
> 최종 갱신: 2026-03-14
> 관리자: CTO 당현송

---

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 이름 | AI Development Team Platform |
| 시작일 | 2026-02-02 |
| 현재 단계 | Claude 에이전트 팀 구조 전환 완료 |
| 버전 | v1.0.0 |
| GitHub | https://github.com/anyonecompany/ai-dev-team |

---

## 기술 스택

### 핵심 (Claude 에이전트 팀)
- 에이전트 오케스트레이션: Claude 에이전트 팀 (Opus 4.6 기반)
- 프로젝트 관리: **Notion** (Dev Home 워크스페이스)
- 알림: Slack 웹훅 (Notion 보고 시 자동 발송)
- 코드 저장소: GitHub (anyonecompany/ai-dev-team)
- Agent Teams: Claude Code 내장 팀 기능 (실험적, tmux 분할 화면)

### 프로젝트별 기술 스택 (필요에 따라 선택)
- Backend: Python 3.11+ / FastAPI / Supabase (PostgreSQL)
- Frontend: React 18+ / TypeScript / Vite / Zustand / Tailwind CSS
- 인프라: Docker / Vercel / Railway / GitHub Actions

### 외부 연동
- **Notion: 태스크/의사결정/기술레퍼런스/프로젝트 관리** (`integrations/notion/reporter.py`)
- **Slack: 웹훅 기반 알림** — Notion 보고 시 자동 발송 (`integrations/slack/slack_notifier.py`)
- GitHub: gh CLI + API

---

## 코딩 규칙

### Python
- PEP 8 준수 (ruff로 검증)
- Type hints 필수
- docstring 필수 (Google 스타일)
- 함수는 단일 책임 원칙 (SRP)
- 비동기 우선 설계

### TypeScript/JavaScript
- ESLint + Prettier 적용
- 명시적 타입 정의
- 함수형 컴포넌트 사용
- Hooks 패턴 준수

### 공통
- 한글 주석 허용
- 에러 메시지는 사용자 친화적으로 (한글 지원)
- 환경변수는 .env 사용 (절대 하드코딩 금지)
- 민감 정보 커밋 금지
- 의미 있는 커밋 메시지 작성

---

## 작업 프로토콜

### 보고 시스템 (필수)

모든 프로젝트 작업은 **Notion + Slack**에 자동 보고한다.

```python
# 사용법 (프로젝트 루트에서)
from integrations.notion.reporter import (
    report_task_done, report_decision, report_techref,
    report_completion, add_project, add_task,
)

# 또는 CLI
python scripts/report.py --task "태스크명" --status "✅ 완료" --summary "요약"
python scripts/report.py --file /path/to/report.json
python scripts/report.py --new-project "프로젝트명"
```

### 새 프로젝트 시작
1. `projects/` 하위에 `{project-name}-{YYYYMMDDHHMMSS}` 폴더 생성
2. README.md, .gitignore, 기본 구조 생성
3. **Notion에 프로젝트 등록** → `add_project("프로젝트명", "🔵 탐색", "한줄 요약", icon="⚽")`
4. **Notion에 태스크 등록** → `add_task("태스크명", priority="🔴 P0", project_name="프로젝트명", done_criteria="완료 조건")`
5. Slack 알림은 자동 발송됨

### ⚠️ project_name 필수 규칙

**모든 Notion 보고 시 반드시 `project_name`을 지정해야 한다. 예외 없음.**

- `report_decision(... project_name="프로젝트명")` ← 필수
- `report_techref(... project_name="프로젝트명")` ← 필수
- `add_task(... project_name="프로젝트명")` ← 필수
- `report_completion(... project_name="프로젝트명")` ← 필수 (하위 항목 자동 전파)

프로젝트가 지정되지 않은 DB 행은 고아 데이터다. 찾을 수 없으면 없는 것과 같다.

### 작업 중 (실시간 보고 — 커밋이 아니라 작업 시점마다!)

**중요: 커밋/푸시 시점이 아니라, 각 작업이 발생하는 시점에 즉시 보고해야 한다.**

1. 태스크 시작 시 → `report_task_done("태스크명", "🔨 진행중")`
2. 기술 결정 시 → `report_decision(title, category, decision, rationale, alternatives="대안", project_name="프로젝트명")`
3. 태스크 완료 시 → `report_task_done("태스크명", "✅ 완료", "결과 요약")`
4. 새 태스크 발생 시 → `add_task("구체적 행동 태스크명", priority="🟡 P1", project_name="프로젝트명", done_criteria="완료 조건")`
5. 코드 변경 시 커밋 + push

**보고 타이밍 예시:**
```
[태스크 시작] report_task_done("API 설계", "🔨 진행중")
[결정 발생]  report_decision("SQLite 선택", "기술선택", "SQLite", "MVP 단순성", alternatives="PostgreSQL, MySQL", project_name="La Paz")
[태스크 완료] report_task_done("API 설계", "✅ 완료", "4개 엔드포인트 확정")
[후속 발견]  add_task("CORS 설정 추가", priority="🟡 P1", project_name="La Paz", done_criteria="CORS 미들웨어 적용 + 허용 도메인 설정")
```

### 태스크 작성 규칙
- 태스크명은 **구체적 행동**으로 ("설계하기" X → "Supabase 테이블 3개 생성" O)
- **완료 조건(done_criteria) 필수** — 없으면 끝났는지 알 수 없다
- **대안(alternatives) 필수** — 3개월 뒤 같은 고민을 하지 않기 위해
- 3일 이상 "🔨 진행중"이면 쪼개라 (태스크가 너무 큰 것이다)

### 작업 완료 후
1. QA 실행 → `/qa` 커맨드
2. QA 통과 시 **통합 보고** (한번에 태스크+의사결정+기술레퍼런스):
   ```python
   report_completion(
       task_name="태스크명",
       status="✅ 완료",
       summary="QA PASS, 결과 요약",
       project_name="프로젝트명",  # ← 필수! 하위 항목에 자동 전파
       decisions=[{"title": "...", "category": "기술선택", "decision": "...", "rationale": "...", "alternatives": "..."}],
       tech_refs=[{"title": "...", "category": "코드패턴", "tags": ["Python"], "content": "..."}],
       new_tasks=[{"task_name": "후속 태스크", "priority": "🟡 P1", "done_criteria": "완료 조건"}],
   )
   ```
3. Slack 알림은 모든 보고에 자동 포함
4. 커밋 + push
5. QA 실패 시: `/qa-fix`로 자동 수정 시도 (최대 3회)

### 노션 상태값 규칙
- 태스크: `⏳ 진행 전` → `🔨 진행중` → `👀 리뷰` → `✅ 완료` / `⏸ 중단됨`
- 프로젝트: `🔵 탐색` → `🟡 진행중` → `🟢 완료`
- 우선순위: `🔴 P0` (긴급) / `🟡 P1` (일반) / `🟢 P2` (낮음)
- 의사결정 카테고리: `기술선택` / `아키텍처` / `데이터` / `비즈니스` / `프로세스` / `인프라`
- 기술 레퍼런스 카테고리: `기술스택` / `아키텍처패턴` / `코드패턴` / `데이터소스` / `프롬프트` / `인프라` / `컨벤션` / `도메인지식`

---

## 에이전트 체계

### 역할 및 모델 매핑

| 역할 | 모델 | 주요 책임 |
|------|------|----------|
| PM-Planner | Opus 4.5 | 요구사항 분석, 태스크 생성 |
| Architect | Opus 4.5 | 시스템 설계, API/DB 스키마 |
| Designer | Gemini 2.0 + Sonnet | UI/UX 설계 |
| BE-Developer | Sonnet 4.5 | 백엔드 구현 |
| FE-Developer | Sonnet 4.5 | 프론트엔드 구현 |
| AI-Engineer | Sonnet 4.5 | ML/AI 기능 구현 |
| QA-DevOps | Haiku 4.5 | 테스트, 배포, CI/CD |
| Orchestrator | Sonnet 4.5 | 작업 분배, 상태 관리 |
| Security-Developer | Sonnet 4.5 | 보안 감사, 시큐어 코딩, 취약점 분석 |

### 에이전트 호출 규칙
- **기획/설계 작업** → Opus 모델
- **구현 작업** → Sonnet 모델
- **테스트/자동화** → Haiku 모델
- **비주얼/UI 작업** → Gemini 모델
- **보안 감사/리뷰** → Security-Developer (Sonnet)

---

## Agent Teams 운영 가이드

> Claude Code 내장 Agent Teams 기능으로 여러 에이전트가 동시에 협업합니다.
> 상세 가이드: `.claude/docs/AGENT_TEAMS_GUIDE.md`

### 사전 요구사항
- tmux 설치: `brew install tmux`
- tmux 세션 안에서 Claude Code 실행: `tmux new -s dev` → `claude`
- Agent Teams 활성화: `settings.local.json`에 설정됨

### 팀 구성 프롬프트 패턴

#### 풀스택 프로젝트 (5인 팀)
```
에이전트 팀을 구성해서 이 프로젝트를 진행해줘.

팀 구성:
1. PM-Planner: 요구사항 분석 후 태스크 분해
2. Architect: 시스템 설계, API/DB 스키마
3. BE-Developer: FastAPI 백엔드 구현
4. FE-Developer: React/TypeScript 프론트엔드 구현
5. QA-DevOps: 린트, 타입체크, 테스트, 빌드 검증

프로젝트: {프로젝트 설명}

규칙:
- projects/{project-name}-{timestamp}/ 에 생성
- 각 팀원은 plan approval 후 구현 시작
- BE와 FE는 Architect 설계 완료 후 병렬 진행
- QA는 구현 완료 후 실행
```

#### 백엔드 전용 (3인 팀)
```
에이전트 팀을 구성해서 백엔드를 개발해줘.

팀 구성:
1. Architect: API 설계, DB 스키마
2. BE-Developer: FastAPI 구현
3. QA-DevOps: 테스트 및 검증

프로젝트: {프로젝트 설명}
```

#### 코드 리뷰 (3인 팀)
```
에이전트 팀으로 코드 리뷰를 진행해줘.

팀 구성:
1. 보안 리뷰어: 인증/인가, 입력 검증, OWASP Top 10
2. 품질 리뷰어: 코드 품질, 테스트 커버리지, 타입 안전성
3. 성능 리뷰어: N+1 쿼리, 메모리 누수, 비동기 패턴

대상: {리뷰 대상 경로}
```

### 파이프라인 순서

| 단계 | 담당 에이전트 | 실행 방식 | 산출물 |
|------|------------|----------|--------|
| 1. 기획 | PM-Planner | 단독 | 태스크 목록, 요구사항 명세 |
| 2. 설계 | Architect | 단독 | API 스키마, DB 스키마, 폴더 구조 |
| 3. 구현 | BE/FE/AI-Engineer | **병렬** | 소스 코드 |
| 4. 검증 | QA-DevOps + Security | **병렬** | QA 리포트, 보안 감사 |
| 5. 통합 | 리드 (Orchestrator) | 단독 | 최종 보고, Monday/Slack 알림 |

### 파일 소유권 (충돌 방지)

| 에이전트 | 담당 디렉토리 |
|---------|-------------|
| BE-Developer | `backend/`, `api/`, `models/`, `services/` |
| FE-Developer | `frontend/`, `src/`, `components/`, `pages/` |
| AI-Engineer | `ai/`, `ml/`, `prompts/` |
| QA-DevOps | `tests/`, `__tests__/` |
| Architect | `docs/`, 루트 설정 파일 |

### 리드 역할 (Orchestrator)
- delegate 모드 사용 권장 (Shift+Tab)
- 직접 코드 작성 금지, 조율만 담당
- Monday.com/Slack 연동 처리
- 팀원 간 의존성 관리

### 비용 관리
- 단순 작업: 팀 없이 단독 실행
- 중간 복잡도: 3인 팀
- 높은 복잡도: 5인 팀
- 최대 7인 팀 (비용 급증 주의)

---

## 금지 사항

### 절대 금지
- 다른 에이전트 담당 영역 임의 수정
- 테스트 없이 "완료" 선언
- TODO.md 외 작업 임의 진행
- `.env` 파일 커밋
- 민감 정보 하드코딩
- 승인 없이 파괴적 작업 (삭제, 덮어쓰기)
- Security-Developer 승인 없이 인증/인가 로직 변경
- 보안 스캔 미실행 상태로 릴리즈

### 확인 후 진행
- 아키텍처 변경
- 의존성 추가/제거
- 스키마 마이그레이션
- 외부 API 연동

### 인공지능기본법 준수 (필수)
- **모든 AI 서비스 개발 시** `.claude/docs/AI_BASIC_LAW_COMPLIANCE.md` 참조 필수
- AI 사용 고지 없이 AI 서비스 출시 금지
- 생성형 AI 결과물에 워터마크/라벨 없이 배포 금지
- 고영향 AI 해당 여부 판단 없이 프로젝트 진행 금지
- 편향성 테스트 없이 고영향 AI 출시 금지

---

## 디렉토리 구조

### 루트
```
ai-dev-team/
├── .claude/              ← 에이전트 설정, 커맨드, 템플릿
├── projects/             ← 모든 개발 프로젝트 (하위 폴더로 자동 생성)
├── integrations/         ← 외부 서비스 연동
│   ├── notion/           ← **Notion 자동 보고 (reporter.py)**
│   ├── slack/            ← Slack 웹훅 알림
│   └── shared/           ← 공용 포맷팅 유틸
├── tasks/                ← 글로벌 태스크 관리
├── scripts/              ← 공용 스크립트
└── _archive/             ← 아카이브 (참조만, 수정 금지)
```

### .claude/ 내부
```
.claude/
├── CLAUDE.md              ← 마스터 헌장
├── agents/                ← 에이전트 프로필
├── commands/              ← 커맨드 (17개: qa, auto, plan, verify-loop 등)
├── rules/                 ← 6개 규칙 파일 (claude-forge 기반)
├── hooks/                 ← 4개 자동화 훅 (보안 필터, 명령 가드, DB 가드)
├── skills/                ← 3개 스킬 (session-wrap, verification-engine, build-system)
├── docs/                  ← 운영 문서, 법규 가이드
├── tasks/                 ← 태스크 관리
├── templates/             ← 프로젝트/태스크 템플릿
├── handoff/               ← 인수인계 문서
├── context/               ← 프로젝트 컨텍스트
├── scripts/               ← 자동화 스크립트
├── knowledge/             ← 지식 베이스
├── reports/               ← QA/활동 리포트
└── settings.local.json    ← 로컬 설정 (hooks + deny 패턴 포함)
```

---

## 품질 기준

### 코드 품질
- 린트 에러: 0건
- 타입 체크 에러: 0건
- 테스트 커버리지: 80% 이상

### 문서 품질
- 모든 공개 함수에 docstring
- API 엔드포인트 문서화
- 변경 사항 로깅

### 프로세스 품질
- 핸드오프 문서 필수
- 결정 로그 기록
- 코드 리뷰 (복잡도 M 이상)

### 보안 품질
- OWASP Top 10: 전 항목 PASS
- Critical/High 취약점: 0건 (릴리즈 차단)
- 의존성: 알려진 Critical 없음
- 인증/인가 테스트: PASS
- 입력 검증: 모든 외부 입력 pydantic/zod 적용

### AI 컴플라이언스 품질 (인공지능기본법)
- AI 사용 고지: 모든 AI 서비스에 고지 UI 포함
- 투명성: 생성형 AI 결과물 워터마크/라벨 적용
- 안전성: 위험 식별/완화 문서화 완료
- 편향성: 고영향 AI 편향성 테스트 PASS
- 영향평가: 고영향 AI 프로젝트 영향평가 완료
- 설명가능성: 고영향 AI 의사결정 근거 설명 기능 구현

---

## 참조 문서

| 문서 | 경로 | 목적 |
|------|------|------|
| 운영 원칙 | `.claude/docs/OPERATING_PRINCIPLES.md` | 상세 프로토콜 |
| 오더 템플릿 | `.claude/templates/ORDER_TEMPLATE.md` | 프로젝트 지시서 |
| 태스크 템플릿 | `.claude/templates/TASK-TEMPLATE.md` | 작업 정의 |
| 핸드오프 템플릿 | `.claude/templates/HANDOFF-TEMPLATE.md` | 인수인계 |
| 현재 상태 | `.claude/handoff/current.md` | 최신 상황 |
| 결정 로그 | `.claude/context/decisions-log.md` | 결정 이력 |
| 보안 에이전트 | `.claude/agents/Security-Developer.md` | 보안 역할 정의 |
| **인공지능기본법 가이드라인** | **`.claude/docs/AI_BASIC_LAW_COMPLIANCE.md`** | **AI 법규 준수 (필수)** |
| Agent Teams 가이드 | `.claude/docs/AGENT_TEAMS_GUIDE.md` | 팀 실행 실용 가이드 |
| 골든 원칙 | `.claude/rules/golden-principles.md` | 12가지 코딩 핵심 원칙 (claude-forge 기반) |
| 검증 규칙 | `.claude/rules/verification.md` | 증거 기반 완료 선언 규칙 |
| 상호작용 규칙 | `.claude/rules/interaction.md` | 가정 확인, 결론 먼저, 비유 설명 |
| 코딩 스타일 | `.claude/rules/coding-style.md` | 불변성, 파일 크기, 에러 핸들링 |
| Git 워크플로우 | `.claude/rules/git-workflow.md` | 커밋 형식, PR, 브랜치 전략 |
| 에이전트 규칙 | `.claude/rules/agents.md` | 병렬 실행, 서브에이전트 vs Teams |

---

## 자동화 훅 (claude-forge 기반)

> 출처: [claude-forge](https://github.com/sangrokjung/claude-forge) 선별 도입

### 활성 훅

| 훅 | 트리거 | 역할 |
|---|--------|------|
| `remote-command-guard.sh` | PreToolUse (Bash) | 파괴적 삭제, 시크릿 유출, 경로 순회, 명령 주입 차단 |
| `db-guard.sh` | PreToolUse (Bash) | DROP/TRUNCATE/DELETE without WHERE 차단 |
| `output-secret-filter.sh` | PostToolUse (전체) | 도구 출력에서 API 키/토큰 자동 마스킹 |
| `security-auto-trigger.sh` | PostToolUse (Edit/Write) | 보안 민감 파일 수정 시 리뷰 권고 |

### deny 패턴 (settings.local.json)

`git push --force`, `git reset --hard`, `rm -rf /`, `rm -rf ~`, `chmod 777`, `mkfs`, `dd if=` 자동 차단

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 3.2.0 | 2026-03-14 | claude-forge 3-Phase 선별 도입: rules(6), hooks(4), commands(8), skills(3), deny 패턴 |
| 3.1.0 | 2026-02-09 | Agent Teams 설정 및 운영 가이드 추가, 팀 협업 규칙 신설 |
| 3.0.0 | 2026-02-09 | Claude 에이전트 팀 구조 전환, Monday.com 올인원 보드, QA 커맨드 신설 |
| 2.2.0 | 2026-02-06 | 인공지능기본법 준수 가이드라인 추가, AI 컴플라이언스 품질 기준 신설 |
| 2.1.0 | 2026-02-03 | Security-Developer 추가, 보안 게이트 도입 |
| 2.0.0 | 2026-02-03 | 구조 개편, 운영 원칙 연동, 참조 체계 정립 |
| 1.0.0 | 2026-02-02 | 초기 버전 |

---

*이 문서는 모든 에이전트의 작업 시작점입니다. 반드시 숙지 후 작업을 진행하세요.*

---

## 컨텍스트 경제학 (필수 숙지)

### 세션 관리 원칙
- 모든 세션은 codemap 로드로 시작 → 탐색 컨텍스트 절약
- 컨텍스트 50% 소진 시 `/session-save` 자동 실행
- 세션 파일은 `.claude/handoff/session-{timestamp}.md` 에 저장
- 다음 날 작업 시작: `/session-restore` 로 전날 상태 로드

### MCP 관리 원칙
- 활성 MCP ≤ 10개, 활성 도구 ≤ 80개
- 세션 시작 전 `/mcp-status` 로 확인
- Supabase MCP 항상 활성화 (전 프로젝트 공통 DB)

### 서브에이전트 위임 시 필수 포함사항
1. 목적/이유 (PURPOSE)
2. 현재 컨텍스트 요약
3. 기대 결과물 형식
4. 사용 가능한 스킬 목록
→ 서브에이전트는 summary만 반환, 전체 덤프 금지

---

## 인프라 가이드 (Phase 1-3)

### 새 세션 시작 시
1. **자동** → SessionStart 훅이 codemap 신선도 + 비용 체크
2. **수동** → `/session-restore`로 이전 세션 이어받기
3. **수동** → `/mcp-status`로 MCP 상태 확인

### 작업 중
- `skill-suggest` 훅이 관련 스킬 자동 추천
- `auto-format` 훅이 파일 저장 시 자동 포맷팅
- `tool-usage-logger`가 모든 도구 호출 기록
- `agent-activity-logger`가 서브에이전트 활동 기록

### 작업 완료 시
1. `verify-on-stop` 훅이 검증 넛지
2. `/retrospective`로 knowledge 자동 축적
3. `/session-save`로 핸드오프 문서 갱신

### 모니터링 커맨드
| 커맨드 | 용도 |
|--------|------|
| `/usage-report` | 도구 사용량 리포트 |
| `/benchmark` | 에이전트 성능 벤치마크 |
| `/cross-ref` | 프로젝트간 공통 패턴 조회 |
| `/ci-fix` | CI 실패 자동 진단 + 수정 |

### 모니터링 스크립트
| 스크립트 | 용도 |
|---------|------|
| `./scripts/codemap-freshness.sh` | codemap 신선도 체크 |
| `./scripts/cost-alert.sh` | 비용 알림 |
| `./scripts/agent-benchmark.sh` | 에이전트 벤치마크 |
| `./scripts/token-report.sh` | 토큰 사용량 리포트 |
| `./scripts/load-project-context.sh` | 프로젝트 컨텍스트 로더 |

### 훅 이벤트 (8개)
| 이벤트 | 훅 | 역할 |
|--------|-----|------|
| PreToolUse | remote-command-guard, db-guard | 파괴적 명령/DB 조작 차단 |
| PostToolUse | output-secret-filter, security-auto-trigger, auto-format, tool-usage-logger | 시크릿 마스킹, 보안 리뷰, 자동 포맷, 사용 로깅 |
| Stop | verify-on-stop | lint/테스트/회고 넛지 |
| UserPromptSubmit | skill-suggest | 관련 스킬 자동 추천 |
| SessionStart | session-start-check | codemap 신선도 + 비용 체크 |
| SubagentStart/Stop | agent-activity-logger | 에이전트 활동 기록 |

