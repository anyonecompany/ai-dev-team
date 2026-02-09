# 프로젝트 중앙 제어 헌장 (Master Charter)

> 버전: 2.2.0
> 최종 갱신: 2026-02-06
> 관리자: Human Lead

---

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 이름 | AI Development Team Platform |
| 시작일 | 2026-02-02 |
| 현재 단계 | MVP 완료 / 고도화 진행 중 |
| 버전 | v0.2.0 |

---

## 기술 스택

### Backend
- Runtime: Python 3.11+
- Framework: FastAPI
- Database: Supabase (PostgreSQL)
- 비동기: aiofiles, asyncio
- 로깅: structlog
- 재시도: tenacity

### Frontend
- Framework: React 18+
- Language: TypeScript
- Build: Vite
- State: Zustand
- Style: Tailwind CSS

### 인프라
- 배포: Vercel (Frontend) / Railway (Backend)
- 컨테이너: Docker
- CI/CD: GitHub Actions

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

### 작업 시작 전 (필수)
1. **`.claude/context/COMPACT_CONTEXT.md` 읽기** (필수, 최우선)
   - 상세 내용이 필요할 때만 원본 문서(CLAUDE.md, OPERATING_PRINCIPLES.md) 참조
2. **현재 상태 파악** - `.claude/handoff/current.md`
3. **할당 작업 확인** - `.claude/tasks/TODO.md`
4. **결정 로그 참조** - `.claude/context/decisions-log.md` (필요 시)

### 작업 중
1. 태스크 상태를 `IN_PROGRESS`로 변경
2. 주요 결정 사항은 `decisions-log.md`에 기록
3. 다른 에이전트 영역 수정 필요 시 협의

### 작업 완료 후 (필수)
1. 품질 검증 실행 (`scripts/qa-check.sh`)
2. **보안 검증 요청** (Security-Developer — 코드 변경 시 필수)
3. `.claude/handoff/current.md`를 `HANDOFF_TEMPLATE.md` 형식으로 갱신
4. `bash .claude/scripts/sync-context.sh` 실행하여 컴팩트 컨텍스트 갱신
5. 태스크 파일을 `DONE/`으로 이동
6. 핸드오프 문서 작성 (`handoff/HANDOFF_TEMPLATE.md` 참조)

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

```
.claude/
├── CLAUDE.md              # 이 파일 (마스터 헌장)
├── agents/                # 에이전트 프로필
│   ├── PM-Planner.md
│   ├── Architect.md
│   ├── BE-Developer.md
│   ├── FE-Developer.md
│   ├── QA-DevOps.md
│   ├── Orchestrator.md
│   └── Security-Developer.md
├── docs/                  # 운영 문서
│   ├── OPERATING_PRINCIPLES.md
│   └── AI_BASIC_LAW_COMPLIANCE.md
├── tasks/                 # 태스크 관리
│   ├── TODO.md
│   ├── registry.json
│   ├── IN_PROGRESS/
│   ├── BLOCKED/
│   ├── REVIEW/
│   └── DONE/
├── templates/             # 템플릿
│   ├── ORDER_TEMPLATE.md
│   ├── TASK-TEMPLATE.md
│   └── HANDOFF-TEMPLATE.md
├── handoff/              # 인수인계
│   └── current.md
├── context/              # 컨텍스트
│   ├── project-summary.md
│   ├── decisions-log.md
│   └── tech-debt.md
├── scripts/              # 자동화 스크립트
│   └── qa-check.sh
└── settings.local.json   # 로컬 설정
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

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 2.2.0 | 2026-02-06 | 인공지능기본법 준수 가이드라인 추가, AI 컴플라이언스 품질 기준 신설 |
| 2.1.0 | 2026-02-03 | Security-Developer 추가, 보안 게이트 도입 |
| 2.0.0 | 2026-02-03 | 구조 개편, 운영 원칙 연동, 참조 체계 정립 |
| 1.0.0 | 2026-02-02 | 초기 버전 |

---

*이 문서는 모든 에이전트의 작업 시작점입니다. 반드시 숙지 후 작업을 진행하세요.*

---

## 프로젝트 구조

```
ai-dev-team/
├── .claude/              ← 에이전트 설정, 커맨드, 템플릿
├── projects/             ← 모든 개발 프로젝트 (하위 폴더로 생성)
├── integrations/         ← 외부 서비스 연동
│   ├── slack/            ← Slack 알림
│   ├── monday/           ← Monday.com 동기화
│   └── shared/           ← 공용 유틸
├── tasks/                ← 글로벌 태스크 관리
├── scripts/              ← 공용 스크립트
└── _archive/             ← 아카이브 (참조만, 수정 금지)
```

## 프로젝트 생성 규칙

1. 모든 새 프로젝트는 반드시 `projects/` 하위에 생성
2. 폴더명 형식: `{project-name}-{YYYYMMDDHHMMSS}`
3. 프로젝트 생성 시 반드시 포함:
   - README.md (프로젝트 설명, 기술 스택, 실행 방법)
   - .gitignore (프로젝트 유형에 맞게)
   - 적절한 디렉토리 구조
4. 프로젝트 생성 후 Slack/Monday에 알림 전송

## QA 규칙

1. 코드 변경 후 반드시 QA 실행 (`/qa` 커맨드)
2. QA 실패 시 `/qa-fix` 로 자동 수정 시도
3. QA 결과는 `/qa-report` 로 Slack/Monday에 공유
4. 커밋 전 QA 통과 필수

## 연동 규칙

1. 프로젝트 생성/완료/주요 변경 시 `integrations/` 모듈 사용
2. Slack 알림: `integrations/slack/slack_notifier.py`
3. Monday.com 동기화: `integrations/monday/monday_sync.py`
4. 알림 포맷: `integrations/shared/notification_format.py`

## 금지 사항 (구조 개편 이후 추가)

1. `_archive/` 내 파일 수정 금지
2. `projects/` 외부에 프로젝트 코드 생성 금지
3. QA 미통과 상태로 커밋 금지
