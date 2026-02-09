# Technical Decisions Log

> 최종 갱신: 2026-02-03

## 개요

프로젝트의 주요 기술 선택과 그 이유를 기록합니다.
새로운 에이전트가 "왜 이 기술을 선택했는지" 빠르게 이해할 수 있도록 합니다.

---

## Backend

### Python 3.11+ 선택

**결정**: Python 3.11 이상 사용

**이유**:
- 성능 향상 (CPython 10-60% 속도 개선)
- 향상된 에러 메시지 (traceback 개선)
- `typing` 모듈 개선 (`Self`, `TypeVarTuple` 등)
- 장기 지원 버전 (LTS)

**대안 고려**: Python 3.9/3.10
- 라이브러리 호환성은 좋으나 성능 이점 포기

---

### FastAPI 선택

**결정**: FastAPI를 메인 웹 프레임워크로 사용

**이유**:
- 비동기 지원 (async/await 네이티브)
- 자동 API 문서화 (Swagger/ReDoc)
- Pydantic 통합으로 타입 검증
- 높은 성능 (Starlette 기반)
- 활발한 커뮤니티

**대안 고려**:
- Flask: 동기 기반, 타입 힌트 지원 미흡
- Django: 풀스택이라 오버헤드, 비동기 지원 제한적

---

### Supabase 선택

**결정**: Supabase를 BaaS로 사용

**이유**:
- PostgreSQL 기반 (확장성, 신뢰성)
- 내장 Auth 시스템
- 실시간 구독 지원
- 무료 티어 넉넉함 (500MB DB, 1GB 스토리지)
- 오픈소스 (self-host 가능)

**대안 고려**:
- Firebase: NoSQL 기반, 복잡한 쿼리 어려움
- 직접 구축: 초기 설정 비용 높음

---

### structlog 선택

**결정**: structlog를 로깅 라이브러리로 사용

**이유**:
- 구조화된 로그 (JSON 출력)
- 컨텍스트 바인딩 (request_id 추적)
- 환경별 포맷 전환 (개발: 컬러, 프로덕션: JSON)
- 표준 logging과 통합

**대안 고려**:
- logging: 구조화 로그 어려움
- loguru: 좋지만 contextvars 지원 복잡

---

### pydantic-settings 선택

**결정**: pydantic-settings로 환경 설정 관리

**이유**:
- 환경변수 자동 로드
- 타입 검증
- .env 파일 지원
- 기본값 설정 용이

---

## Frontend

### React 18+ 선택

**결정**: React 18 이상 사용

**이유**:
- Concurrent Features (Suspense, Transitions)
- 가장 큰 생태계
- 팀 친숙도

**대안 고려**:
- Vue 3: 좋지만 TypeScript 지원이 React보다 약함
- Svelte: 생태계 작음

---

### TypeScript 선택

**결정**: TypeScript 필수 사용

**이유**:
- 컴파일 타임 타입 체크
- IDE 지원 (자동완성, 리팩토링)
- 문서화 효과
- 런타임 에러 감소

**규칙**:
- `any` 사용 금지 (필요 시 `unknown`)
- 외부 API 응답은 타입 정의 필수

---

### Vite 선택

**결정**: Vite를 빌드 도구로 사용

**이유**:
- 빠른 개발 서버 (ESM 기반)
- 빠른 HMR
- 간단한 설정
- Rollup 기반 최적화된 프로덕션 빌드

**대안 고려**:
- CRA: 느림, eject 필요
- webpack 직접 설정: 복잡함

---

### Zustand 선택

**결정**: Zustand를 상태 관리 라이브러리로 사용

**이유**:
- 미니멀한 API
- 보일러플레이트 적음
- TypeScript 친화적
- persist 미들웨어 내장
- Redux보다 학습 곡선 낮음

**대안 고려**:
- Redux Toolkit: 좋지만 보일러플레이트 많음
- Jotai/Recoil: atomic 패턴은 이 규모에서 오버

---

### Tailwind CSS 선택

**결정**: Tailwind CSS를 스타일링에 사용

**이유**:
- 유틸리티 우선 (빠른 개발)
- 번들 크기 최적화 (PurgeCSS)
- 일관된 디자인 시스템
- 컴포넌트 추출 쉬움

**대안 고려**:
- styled-components: CSS-in-JS 오버헤드
- CSS Modules: 클래스명 관리 필요

---

## Infrastructure

### Vercel (Frontend) 선택

**결정**: Vercel에 프론트엔드 배포

**이유**:
- 무료 티어
- GitHub 연동
- Preview 배포 자동화
- Edge Functions
- 빠른 글로벌 CDN

---

### Railway (Backend) 선택

**결정**: Railway에 백엔드 배포

**이유**:
- 무료 티어 ($5 크레딧/월)
- Docker 지원
- 환경변수 관리 용이
- GitHub 연동

**대안 고려**:
- Fly.io: 좋지만 설정 복잡
- Render: 무료 티어 sleep 문제

---

### GitHub Actions 선택

**결정**: GitHub Actions를 CI/CD에 사용

**이유**:
- GitHub 네이티브 통합
- 무료 (공개 레포)
- 풍부한 액션 마켓플레이스
- 매트릭스 빌드 지원

---

## 결정 원칙

### 기술 선택 기준

1. **팀 친숙도**: 학습 곡선 최소화
2. **생태계 크기**: 문제 해결 자료 풍부
3. **유지보수성**: 장기 지원, 활발한 개발
4. **비용**: 무료 티어 또는 저비용
5. **확장성**: 트래픽 증가 대응 가능

### 새 기술 도입 시

1. 기존 기술로 해결 불가한지 검토
2. PoC 구현 및 테스트
3. decisions-log.md에 이유 기록
4. 팀 공유 및 합의

---

## 변경 이력

| 날짜 | 결정 | 이유 |
|------|------|------|
| 2026-02-02 | Python 3.11 채택 | 성능/타입 개선 |
| 2026-02-02 | FastAPI 채택 | 비동기/문서화 |
| 2026-02-02 | Supabase 채택 | BaaS 편의성 |
| 2026-02-02 | structlog 채택 | 구조화 로깅 |
| 2026-02-02 | React 18 채택 | 생태계/팀 친숙도 |
| 2026-02-02 | Zustand 채택 | 미니멀 상태관리 |
| 2026-02-02 | Tailwind 채택 | 빠른 스타일링 |
| 2026-02-02 | Vite 채택 | 빠른 빌드 |
| 2026-02-03 | Railway 채택 | 무료 티어/Docker |
| 2026-02-03 | Vercel 채택 | Preview/CDN |
