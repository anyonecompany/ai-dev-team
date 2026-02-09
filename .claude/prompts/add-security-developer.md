# Claude에게 보안 개발자 에이전트 추가 요청 프롬프트

아래 내용을 Claude 채팅에 복사해서 붙여넣으세요.

---

## 프롬프트 시작

```
# AI 개발팀 대시보드 - 보안 개발자 에이전트 추가 요청

## 현재 프로젝트 상황

### 프로젝트 개요
- **프로젝트명**: AI Development Team Dashboard
- **버전**: v0.3.0 (운영 체계 고도화 완료)
- **목적**: 8개의 AI 에이전트가 협력하여 소프트웨어 개발을 수행하는 멀티 에이전트 시스템

### 기술 스택

**백엔드**
- Python 3.11+ / FastAPI
- Supabase (PostgreSQL)
- Claude API (Opus 4.5, Sonnet 4.5, Haiku 4.5)
- Gemini API (2.0 Flash)
- aiofiles (비동기 I/O)
- structlog (구조화 로깅)
- tenacity (재시도 메커니즘)

**프론트엔드**
- React 18 + Vite
- TypeScript (점진적 마이그레이션 중)
- Zustand (상태 관리)
- Tailwind CSS

### 현재 에이전트 체계 (8개)

| 역할 | 모델 | 권한 레벨 | 주요 책임 |
|------|------|----------|----------|
| Orchestrator | Sonnet 4.5 | Level 2 | 워크플로우 조율, 에이전트 할당, 충돌 해결 |
| PM-Planner | Opus 4.5 | Level 3 | 요구사항 분석, 태스크 생성, 우선순위 |
| Architect | Opus 4.5 | Level 3 | 시스템 설계, API/DB 스키마, 기술 결정 |
| Designer | Gemini 2.0 | Level 4 | UI/UX 시안, 디자인 토큰, 컴포넌트 스펙 |
| BE-Developer | Sonnet 4.5 | Level 4 | API/DB 구현, 비즈니스 로직 |
| FE-Developer | Sonnet 4.5 | Level 4 | UI 구현, 상태 관리, 백엔드 연동 |
| AI-Engineer | Sonnet 4.5 | Level 4 | LLM 프롬프트, ML 기능, 외부 API |
| QA-DevOps | Haiku 4.5 | Level 3 | 테스트, CI/CD, 배포, 보안 스캔 |

### 에이전트 프로필 표준 구조 (v2.0.0)

모든 에이전트는 다음 구조를 따름:
1. 기본 정보 (모델, 역할, 권한 레벨)
2. 핵심 임무
3. 작업 시작 전 필수 확인 사항
4. 완료 기준 (Definition of Done)
5. 산출물/코딩 표준
6. 의사결정 권한 매트릭스
7. 협업 규칙
8. 참조 문서
9. 금지 사항

### 주요 문서 체계

| 문서 | 경로 | 목적 |
|------|------|------|
| 마스터 헌장 | `.claude/CLAUDE.md` | 기본 규칙, 에이전트 체계 정의 |
| 운영 원칙 | `.claude/docs/OPERATING_PRINCIPLES.md` | 상세 프로토콜, 워크플로우 |
| 에이전트 프로필 | `.claude/agents/*.md` | 개별 에이전트 역할/책임 정의 |
| 결정 로그 | `.claude/context/decisions-log.md` | 아키텍처 결정 기록 |
| 현재 상태 | `.claude/handoff/current.md` | 최신 진행 상황 |

### 현재 보안 관련 구현 상태

**구현된 것:**
- `core/security.py`: JWT 검증, API 키 인증
- CORS 설정
- pydantic 입력 검증
- 환경 변수를 통한 시크릿 관리

**미구현/부족한 것:**
- ❌ 전담 보안 에이전트 없음 (QA-DevOps가 일부 담당)
- ❌ OWASP Top 10 체크리스트 미적용
- ❌ 의존성 취약점 스캔 자동화 없음
- ❌ 시큐어 코딩 가이드라인 미수립
- ❌ 인증/인가 아키텍처 검토 미실시
- ❌ API 보안 테스트 (펜테스트) 없음
- ❌ 보안 사고 대응 프로토콜 미정의

---

## 요청 사항

### 1. Security-Developer 에이전트 프로필 생성

`.claude/agents/Security-Developer.md` 파일을 v2.0.0 표준에 맞게 생성해주세요.

**권장 모델**: Sonnet 4.5 (코드 분석 및 보안 로직 구현에 적합)
**권한 레벨**: Level 3 (Architect/QA-DevOps와 동급)

**핵심 책임 영역:**
1. 시큐어 코딩 가이드라인 수립 및 검토
2. OWASP Top 10 기반 취약점 점검
3. 의존성 보안 스캔 (dependabot, snyk 등)
4. 인증/인가 아키텍처 설계 협업
5. API 보안 테스트 설계
6. 보안 사고 대응 프로토콜 수립
7. 코드 리뷰 시 보안 관점 체크

**협업 대상:**
- Architect: 보안 아키텍처 결정
- BE-Developer: 백엔드 보안 구현 검토
- FE-Developer: 프론트엔드 보안 (XSS, CSRF 등)
- QA-DevOps: 보안 테스트 자동화 연동

### 2. 관련 문서 업데이트

프로필 생성 후 아래 문서들도 업데이트 필요:
- `.claude/CLAUDE.md`: 에이전트 목록에 Security-Developer 추가
- `.claude/docs/OPERATING_PRINCIPLES.md`: 보안 관련 섹션 추가 또는 강화
- `.claude/context/decisions-log.md`: 보안 에이전트 추가 결정 기록

### 3. 초기 태스크 제안

Security-Developer가 시작할 첫 번째 태스크들:
- TASK-SEC-001: 현재 코드베이스 보안 감사
- TASK-SEC-002: 시큐어 코딩 가이드라인 문서 작성
- TASK-SEC-003: 의존성 취약점 스캔 자동화 설정

---

## 기대 산출물

1. `.claude/agents/Security-Developer.md` (v2.0.0 표준)
2. 업데이트된 `.claude/CLAUDE.md`
3. `decisions-log.md`에 결정 기록
4. (선택) 초기 보안 체크리스트 문서
```

## 프롬프트 끝

---

## 사용 방법

1. 위의 "프롬프트 시작"과 "프롬프트 끝" 사이의 내용을 복사
2. Claude 채팅(claude.ai)에 붙여넣기
3. Claude가 Security-Developer.md 및 관련 문서 업데이트를 생성
4. 생성된 내용을 실제 파일로 저장

## 추가 컨텍스트 (필요시 첨부)

Claude에게 더 정확한 결과를 얻으려면 아래 파일들도 첨부하면 좋습니다:
- `.claude/CLAUDE.md` (마스터 헌장)
- `.claude/agents/QA-DevOps.md` (비슷한 역할 참고용)
- `.claude/docs/OPERATING_PRINCIPLES.md` (운영 원칙)
