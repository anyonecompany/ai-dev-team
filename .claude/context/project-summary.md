# AI 개발팀 대시보드 - 프로젝트 요약

**버전**: 0.3.0 (운영 체계 고도화)
**최종 업데이트**: 2026-02-03

## 프로젝트 개요

AI 개발팀 대시보드는 멀티 에이전트 시스템을 관리하기 위한 웹 기반 대시보드입니다.
8개의 전문화된 AI 에이전트가 협력하여 소프트웨어 개발 프로젝트를 수행합니다.

---

## 기술 스택

### 백엔드
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL)
- **AI**: Anthropic Claude API, Google Gemini API
- **Server**: Uvicorn
- **Async I/O**: aiofiles
- **Logging**: structlog (JSON format)
- **Retry**: tenacity (exponential backoff)
- **Testing**: pytest, pytest-asyncio

### 프론트엔드
- **Framework**: React 18 + Vite
- **Language**: TypeScript (점진적 마이그레이션)
- **State**: Zustand (TypeScript 지원)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Markdown**: react-markdown, remark-gfm
- **Syntax Highlight**: react-syntax-highlighter
- **WebSocket**: 지수 백오프 재연결 지원

---

## 폴더 구조

```
ai-dev-team/
├── dashboard/
│   ├── backend/
│   │   ├── api/              # API 엔드포인트 (DI 적용)
│   │   ├── core/             # 설정, DB 연결, 보안, 로깅
│   │   ├── models/           # Pydantic 모델
│   │   ├── services/         # 비즈니스 로직
│   │   └── tests/            # 단위 테스트
│   └── frontend/
│       └── src/
│           ├── components/   # React 컴포넌트
│           ├── pages/        # 페이지 컴포넌트
│           ├── stores/       # Zustand 스토어
│           ├── services/     # API 클라이언트
│           ├── hooks/        # 커스텀 훅
│           └── types/        # TypeScript 타입 정의
├── scripts/
│   └── qa.sh                 # QA 자동화 스크립트
├── projects/                 # 생성된 프로젝트들
└── .claude/
    ├── CLAUDE.md             # 마스터 헌장 (v2.0.0)
    ├── docs/                 # 운영 문서
    │   └── OPERATING_PRINCIPLES.md  # 운영 원칙 (신규)
    ├── agents/               # 에이전트 프로필 (v2.0.0)
    ├── templates/            # 템플릿
    │   ├── ORDER_TEMPLATE.md # 오더 템플릿 (신규)
    │   ├── TASK-TEMPLATE.md
    │   └── HANDOFF-TEMPLATE.md
    ├── handoff/              # 핸드오프 문서
    ├── context/              # 컨텍스트 문서
    ├── tasks/                # 태스크 레지스트리
    └── scripts/              # 유틸리티 스크립트
```

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

---

## API 엔드포인트

### 프로젝트
- `GET /api/projects/` - 프로젝트 목록
- `POST /api/projects/` - 프로젝트 생성
- `GET /api/projects/{id}` - 프로젝트 상세
- `DELETE /api/projects/{id}` - 프로젝트 삭제

### 태스크
- `GET /api/tasks/?project_id=xxx` - 태스크 목록
- `POST /api/tasks/{id}/resume?project_id=xxx` - 태스크 재개
- `PATCH /api/tasks/{id}?project_id=xxx` - 태스크 수정
- `POST /api/tasks/sync` - 파일 시스템 동기화

### 채팅
- `POST /api/chat/send` - 메시지 전송
- `GET /api/projects/{id}/chat/history` - 채팅 기록

---

## 주요 결정사항

### 아키텍처 결정

1. **프로젝트별 격리**: 각 프로젝트는 독립적인 태스크와 채팅 기록을 가짐
2. **파일 기반 저장**: 태스크는 `.claude/tasks/registry.json`에 저장
3. **실시간 연결**: WebSocket으로 에이전트 상태 실시간 업데이트
4. **에러 처리**: ErrorBoundary + API 타임아웃으로 안정성 확보

### v0.2.0 시스템 개선

5. **비동기 파일 I/O**: `aiofiles`로 이벤트 루프 블로킹 방지
6. **의존성 주입**: FastAPI `Depends`로 서비스 인스턴스 관리
7. **구조화 로깅**: `structlog`로 JSON 형식 로그 (요청 ID 추적)
8. **재시도 메커니즘**: `tenacity`로 API 호출 자동 재시도
9. **상태 자동 복구**: 서버 시작 시 IN_PROGRESS 태스크 검사 및 복구
10. **WebSocket 개선**: 지수 백오프 재연결, 1012/1006 에러 코드 처리
11. **TypeScript 마이그레이션**: 프론트엔드 핵심 파일 TypeScript 전환

### v0.3.0 운영 체계 고도화

12. **운영 원칙 수립**: Multi-agent 베스트 프랙티스 문서화
13. **오더 템플릿 정식화**: 프로젝트 오더 표준 템플릿 생성
14. **에이전트 프로필 표준화**: 8개 에이전트 모두 일관된 구조로 정비
15. **참조 체계 정립**: 문서 간 상호 참조 구조 확립

---

## QA 결과

### 최신 QA 결과 (2026-02-03)

| 항목 | 결과 |
|------|------|
| Frontend TypeScript Check | PASS |
| Frontend Build | PASS (2.00s) |
| Backend Import Check | PASS |
| Backend Tests | PASS (11/11 통과, 0.59s) |
| WebSocket 재연결 | PASS (지수 백오프 구현됨) |

### QA 스크립트 실행

```bash
./scripts/qa.sh
```

검사 항목:
- Backend Lint (ruff/flake8)
- Backend Tests (pytest)
- Backend Import Check
- TypeScript Type Check
- Frontend Build
- Backend Health Check

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| 0.3.0 | 2026-02-03 | 운영 체계 고도화, 문서 정비 |
| 0.2.0 | 2026-02-03 | 비동기 I/O, DI, 로깅, 재시도 |
| 0.1.0 | 2026-02-02 | 초기 MVP |

---

## 참조 문서

| 문서 | 경로 | 목적 |
|------|------|------|
| 마스터 헌장 | `.claude/CLAUDE.md` | 기본 규칙 |
| 운영 원칙 | `.claude/docs/OPERATING_PRINCIPLES.md` | 상세 프로토콜 |
| 오더 템플릿 | `.claude/templates/ORDER_TEMPLATE.md` | 프로젝트 지시서 |
| 현재 상태 | `.claude/handoff/current.md` | 최신 상황 |
| 결정 로그 | `.claude/context/decisions-log.md` | 결정 이력 |
