# Knowledge Library

> 버전: 2.0.0
> 최종 갱신: 2026-03-23

## 개요

프로젝트에서 학습한 패턴, 실수, 기술 결정을 축적하는 지식 라이브러리입니다.
새로운 에이전트가 빠르게 컨텍스트를 파악하고, 같은 실수를 반복하지 않도록 합니다.

## 디렉토리 구조

```
.claude/knowledge/
├── README.md                    # 이 파일 (인덱스)
├── codemap-index.md             # 코드맵 인덱스 (전체 구조 개요)
├── codemap-lapaz.md             # La Paz 프로젝트 코드맵
├── codemap-portfiq.md           # Portfiq 프로젝트 코드맵
├── codemap-others.md            # 기타 프로젝트 코드맵
├── decisions/                   # 기술 선택 및 아키텍처 의사결정
│   ├── README.md                # ADR 7건 (인프라 마이그레이션, LLM 전환 등)
│   └── tech-choices.md          # 초기 기술 스택 선택 (Python/FastAPI/React 등)
├── mistakes/                    # 반복 실수 패턴 및 예방법
│   ├── README.md                # 시스템 레벨 실수 7건 (OAuth, event loop, CORS 등)
│   └── common-pitfalls.md       # 코딩 레벨 pitfall (None 체크, 비동기 I/O 등)
└── patterns/                    # 재사용 가능한 코드 패턴
    ├── README.md                # 상위 패턴 6건 (.env cascade, 통합 보고 등)
    ├── supabase-connection.md   # 싱글톤 DB 클라이언트
    ├── fastapi-error-handling.md # structlog 기반 에러/로깅
    ├── crud-service.md          # 서비스 레이어 추상화
    ├── auth-supabase.md         # Supabase Auth 통합
    └── react-api-client.md      # 타입 안전 API 클라이언트
```

## 파일별 용도

### Codemap (탐색 비용 최소화)

| 파일 | 용도 |
|------|------|
| `codemap-index.md` | 전체 프로젝트 구조 개요. 세션 시작 시 먼저 로드 |
| `codemap-lapaz.md` | La Paz Live 프로젝트 파일/모듈 맵 |
| `codemap-portfiq.md` | Portfiq 프로젝트 파일/모듈 맵 |
| `codemap-others.md` | 기타 프로젝트 및 인프라 파일 맵 |

### Decisions (왜 이렇게 결정했는가)

| 파일 | 내용 | 건수 |
|------|------|------|
| `decisions/README.md` | 운영 중 발생한 아키텍처 의사결정 (ADR) | 7건 |
| `decisions/tech-choices.md` | 초기 기술 스택 선택 및 이유 | 12건 |

주요 ADR: Railway→Fly.io 마이그레이션, Anthropic→Gemini LLM 전환, OAuth 인증 전환, claude-forge 도입

### Mistakes (같은 실수를 반복하지 마라)

| 파일 | 내용 | 건수 |
|------|------|------|
| `mistakes/README.md` | 시스템/아키텍처 레벨 반복 실수 패턴 | 7건 |
| `mistakes/common-pitfalls.md` | 코딩 레벨 흔한 실수와 해결법 | 11건 |

핵심 교훈: OAuth는 전용 콜백 페이지 분리, 무거운 백그라운드 작업은 별도 스레드, 캐시 무효화 잊지 말 것

### Patterns (이렇게 하면 된다)

| 파일 | 내용 | 건수 |
|------|------|------|
| `patterns/README.md` | 프로젝트 전반 반복 사용 상위 패턴 | 6건 |
| `patterns/supabase-connection.md` | 싱글톤 DB 클라이언트 패턴 | - |
| `patterns/fastapi-error-handling.md` | structlog 기반 에러/로깅 패턴 | - |
| `patterns/crud-service.md` | 서비스 레이어 CRUD 추상화 | - |
| `patterns/auth-supabase.md` | Supabase Auth 통합 패턴 | - |
| `patterns/react-api-client.md` | 타입 안전 API 클라이언트 패턴 | - |

## 사용 방법

### 세션 시작 시
```bash
# 1. 코드맵 로드 (탐색 컨텍스트 절약)
cat .claude/knowledge/codemap-index.md

# 2. 관련 프로젝트 코드맵 로드
cat .claude/knowledge/codemap-portfiq.md
```

### 작업 전 실수 패턴 확인
```bash
# 시스템 레벨 실수 패턴
cat .claude/knowledge/mistakes/README.md

# 코딩 레벨 pitfall
cat .claude/knowledge/mistakes/common-pitfalls.md
```

### 새 패턴 추가
```bash
bash .claude/scripts/save-pattern.sh <패턴명> <카테고리>
```

## 기여 가이드

### 좋은 패턴의 조건
1. **재사용 가능**: 여러 프로젝트에서 사용 가능
2. **완전한 예시**: 복사-붙여넣기로 즉시 사용 가능
3. **명확한 설명**: 왜 이 방식인지 이유 포함
4. **실제 출처**: 프로젝트 내 실제 코드 참조

### 실수 기록 기준
- git log에서 같은 영역 fix 커밋 3건 이상 → 반드시 패턴화
- 2시간 이상 디버깅한 이슈 → 원인+예방 기록

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-23 | v2.0.0 — git log 분석 기반 decisions/mistakes/patterns README 신규 작성, 인덱스 전면 개편 |
| 2026-02-03 | v1.0.0 — 초기 라이브러리 생성 (5개 패턴) |
