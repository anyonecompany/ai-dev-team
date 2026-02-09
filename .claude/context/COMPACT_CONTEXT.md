# ⚡ 컴팩트 컨텍스트 (자동 생성)
> 최종 갱신: 2026-02-03 17:55
> 원본: CLAUDE.md 2.1.0 + OPERATING_PRINCIPLES 1.1.0

## 프로젝트 정체성
**2026-02-02** — 가상 AI 에이전트 팀이 협업하여 소프트웨어를 개발하는 플랫폼.
현재 단계: v0.2.0 (------)

## 기술 스택
- **Backend**: Python 3.11+ / FastAPI / aiofiles / structlog / tenacity
- **Frontend**: React 18+ / TypeScript / Vite / Zustand / Tailwind CSS
- **DB**: Supabase (PostgreSQL)
- **AI**: Claude (Opus 4.5, Sonnet 4.5, Haiku 4.5) + Gemini 2.0

## 에이전트 테이블
| 에이전트 | 역할 | 모델 | 핵심 권한 |
|---------|------|------|----------|
| PM-Planner | 요구사항 분석, 태스크 생성 | Opus 4.5 | 요구사항 정의, 태스크 생성 |
| Architect | 시스템 설계, API/DB 스키마 | Opus 4.5 | 아키텍처 결정, 스키마 승인 |
| Designer | UI/UX 설계 | Gemini 2.0 + Sonnet | 디자인 시안, 컴포넌트 설계 |
| BE-Developer | 백엔드 구현 | Sonnet 4.5 | API/서비스 코드 작성 |
| FE-Developer | 프론트엔드 구현 | Sonnet 4.5 | UI 컴포넌트 코드 작성 |
| AI-Engineer | ML/AI 기능 구현 | Sonnet 4.5 | AI 모델 연동, 프롬프트 설계 |
| QA-DevOps | 테스트, 배포, CI/CD | Haiku 4.5 | 테스트 실행, 배포 승인 |
| Orchestrator | 작업 분배, 상태 관리 | Sonnet 4.5 | 태스크 할당, 충돌 해결 |
| Security-Developer | 보안 감사, 취약점 분석 | Sonnet 4.5 | 보안 태스크 생성, 코드 리뷰 |

## 핵심 규칙 (Top 10)
1. **COMPACT_CONTEXT.md 먼저 읽기** — 상세 필요 시만 원본 참조
2. **다른 에이전트 담당 영역 임의 수정 금지**
3. **테스트 없이 "완료" 선언 금지**
4. **TODO.md 외 작업 임의 진행 금지**
5. **Security-Developer 승인 없이 인증/인가 로직 변경 금지**
6. **보안 스캔 미실행 상태로 릴리즈 금지**
7. **.env 파일 커밋 금지, 민감 정보 하드코딩 금지**
8. **코드 변경 후 보안 검증 요청 필수**
9. **복잡도 M 이상은 팀 설계 회의 필수**
10. **Self-QA 5단계 (정적분석→테스트→보안→성능→종합) 통과 후 납품**

## 현재 스프린트 상태
- **TODO**: 3건
- **진행중**: 0건
- **블로커**: 0건
- **Git 변경**: 0개 파일
- **다음 우선**:
  - TASK-SEC-001: 현재 코드베이스 보안 감사 [P1/L]
  - TASK-SEC-002: 시큐어 코딩 가이드라인 작성 [P1/M]

## 최근 핸드오프


## 상세 참조
- 전체 헌장: `.claude/CLAUDE.md`
- 운영 원칙: `.claude/docs/OPERATING_PRINCIPLES.md`
- 에이전트 프로필: `.claude/agents/[에이전트명].md`
- 태스크: `.claude/tasks/TODO.md`
- 결정 로그: `.claude/context/decisions-log.md`
