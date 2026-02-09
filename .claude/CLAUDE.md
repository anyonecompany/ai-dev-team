# 프로젝트 중앙 제어 헌장 (Master Charter)

> 버전: 3.1.0
> 최종 갱신: 2026-02-09
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
- 프로젝트 관리: Monday.com (올인원 보드 "AI Dev Team Hub")
- 알림: Slack 웹훅
- 코드 저장소: GitHub (anyonecompany/ai-dev-team)
- Agent Teams: Claude Code 내장 팀 기능 (실험적, tmux 분할 화면)

### 프로젝트별 기술 스택 (필요에 따라 선택)
- Backend: Python 3.11+ / FastAPI / Supabase (PostgreSQL)
- Frontend: React 18+ / TypeScript / Vite / Zustand / Tailwind CSS
- 인프라: Docker / Vercel / Railway / GitHub Actions

### 외부 연동
- Slack: 웹훅 기반 알림 (`integrations/slack/slack_notifier.py`)
- Monday.com: GraphQL API 올인원 보드 (`integrations/monday/monday_sync.py`)
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

### 새 프로젝트 시작
1. `projects/` 하위에 `{project-name}-{YYYYMMDDHHMMSS}` 폴더 생성
2. README.md, .gitignore, 기본 구조 생성
3. Monday.com에 프로젝트 등록 → `create_project()`
4. Slack에 프로젝트 생성 알림 → `notify_project_created()`
5. 에이전트 활동 로그 기록 → `log_agent_activity()`

### 작업 중
1. Monday.com 프로젝트 상태를 "진행중"으로 → `update_project_status()`
2. 주요 작업마다 에이전트 활동 로그 기록
3. 마일스톤 달성 시 기록 → `log_project_milestone()`
4. 코드 변경 시 커밋 + push

### 작업 완료 후
1. QA 실행 → `/qa` 커맨드
2. QA 통과 시:
   - Monday.com에 QA 결과 기록 → `log_qa_result()`
   - 프로젝트 상태 "완료"로 업데이트
   - 산출물 기록 → `log_project_deliverables()`
   - Slack에 결과 알림
   - 커밋 + push
3. QA 실패 시:
   - `/qa-fix`로 자동 수정 시도 (최대 3회)
   - Monday.com에 실패 결과 기록, 상태 "차단됨"

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
│   ├── slack/            ← Slack 웹훅 알림
│   ├── monday/           ← Monday.com 올인원 보드
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
├── commands/              ← 커맨드 (/qa, /qa-fix, /qa-report)
├── docs/                  ← 운영 문서, 법규 가이드
├── tasks/                 ← 태스크 관리
├── templates/             ← 프로젝트/태스크 템플릿
├── handoff/               ← 인수인계 문서
├── context/               ← 프로젝트 컨텍스트
├── scripts/               ← 자동화 스크립트
├── knowledge/             ← 지식 베이스
├── reports/               ← QA/활동 리포트
└── settings.local.json    ← 로컬 설정
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

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 3.1.0 | 2026-02-09 | Agent Teams 설정 및 운영 가이드 추가, 팀 협업 규칙 신설 |
| 3.0.0 | 2026-02-09 | Claude 에이전트 팀 구조 전환, Monday.com 올인원 보드, QA 커맨드 신설 |
| 2.2.0 | 2026-02-06 | 인공지능기본법 준수 가이드라인 추가, AI 컴플라이언스 품질 기준 신설 |
| 2.1.0 | 2026-02-03 | Security-Developer 추가, 보안 게이트 도입 |
| 2.0.0 | 2026-02-03 | 구조 개편, 운영 원칙 연동, 참조 체계 정립 |
| 1.0.0 | 2026-02-02 | 초기 버전 |

---

*이 문서는 모든 에이전트의 작업 시작점입니다. 반드시 숙지 후 작업을 진행하세요.*

