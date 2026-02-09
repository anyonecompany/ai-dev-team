# Knowledge Library

> 버전: 1.0.0
> 최종 갱신: 2026-02-03

## 개요

프로젝트에서 학습한 패턴, 실수, 기술 결정을 축적하는 지식 라이브러리입니다.
새로운 에이전트가 빠르게 컨텍스트를 파악하고, 같은 실수를 반복하지 않도록 합니다.

## 디렉토리 구조

```
.claude/knowledge/
├── README.md              # 이 파일
├── patterns/              # 재사용 가능한 코드 패턴
│   ├── supabase-connection.md
│   ├── fastapi-error-handling.md
│   ├── react-api-client.md
│   ├── crud-service.md
│   └── auth-supabase.md
├── mistakes/              # 자주 발생하는 실수와 해결책
│   └── common-pitfalls.md
└── decisions/             # 기술 선택 및 이유
    └── tech-choices.md
```

## 사용 방법

### 패턴 참조하기

작업 전 관련 패턴이 있는지 확인:

```bash
# 패턴 목록 확인
ls .claude/knowledge/patterns/

# 특정 패턴 읽기
cat .claude/knowledge/patterns/supabase-connection.md
```

### 새 패턴 추가하기

스크립트를 사용하여 템플릿 생성:

```bash
# 백엔드 패턴 추가
bash .claude/scripts/save-pattern.sh rate-limiting backend

# 프론트엔드 패턴 추가
bash .claude/scripts/save-pattern.sh form-validation frontend

# DevOps 패턴 추가
bash .claude/scripts/save-pattern.sh docker-multistage devops
```

### 실수 기록하기

`mistakes/common-pitfalls.md`에 새로운 섹션 추가:

```markdown
### N. 문제 제목

**문제**
[잘못된 코드 또는 상황]

**해결**
[올바른 코드 또는 해결 방법]

**원인**: [근본 원인 설명]
```

### 기술 결정 기록하기

`decisions/tech-choices.md`에 새로운 섹션 추가:

```markdown
### [기술명] 선택

**결정**: [어떤 기술을 어디에 사용]

**이유**:
- 이유 1
- 이유 2

**대안 고려**:
- 대안 1: 선택하지 않은 이유
```

## 패턴 목록

### Backend Patterns

| 패턴 | 설명 | 파일 |
|------|------|------|
| Supabase Connection | 싱글톤 DB 클라이언트 | `supabase-connection.md` |
| FastAPI Error Handling | structlog 기반 에러/로깅 | `fastapi-error-handling.md` |
| CRUD Service | 서비스 레이어 추상화 | `crud-service.md` |
| Auth Supabase | Supabase Auth 통합 | `auth-supabase.md` |

### Frontend Patterns

| 패턴 | 설명 | 파일 |
|------|------|------|
| React API Client | 타입 안전 API 클라이언트 | `react-api-client.md` |

## 기여 가이드

### 좋은 패턴의 조건

1. **재사용 가능**: 여러 프로젝트에서 사용 가능
2. **완전한 예시**: 복사-붙여넣기로 즉시 사용 가능
3. **명확한 설명**: 왜 이 방식인지 이유 포함
4. **실제 출처**: 프로젝트 내 실제 코드 참조

### 패턴 작성 팁

- 문제 상황부터 시작 (왜 필요한가?)
- 핵심 코드는 최소화 (필수 부분만)
- 주의사항/엣지 케이스 명시
- 관련 패턴 링크

### 실수 기록 팁

- 같은 실수를 반복하지 않도록
- 문제 코드와 해결 코드 모두 포함
- 근본 원인 분석

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-02-03 | 초기 라이브러리 생성 (5개 패턴) |

---

*이 라이브러리는 프로젝트의 집단 지성입니다. 적극적으로 기여해주세요!*
