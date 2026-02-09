# TASK-034 결과

생성 시간: 2026-02-02T17:50:16.324352

---

# 시스템 설계 문서

## 아키텍처 개요

### 시스템 구성도
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│  Supabase   │
│   (Vercel)  │◀────│  (Railway)  │◀────│(PostgreSQL) │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │                    │
        └───────────────────┴────────────────────┘
                    환경변수 (.env)
```

### 기술 스택 검증
- **Backend**: Python 3.11+ / FastAPI ✓
- **Database**: Supabase (PostgreSQL) ✓
- **Frontend**: 미정 (PM-Planner 결정 대기)
- **배포**: Vercel(Frontend) / Railway(Backend) ✓

## 기술적 차단 요소 분석

### 1. Supabase 연동 이슈
**문제**: 인증/권한 관리 복잡도
**해결방안**:
- Supabase Auth 대신 FastAPI 자체 JWT 구현
- Row Level Security(RLS) 비활성화 후 백엔드에서 권한 관리
- Supabase는 순수 PostgreSQL DB로만 활용

### 2. Railway 배포 제약
**문제**: 빌드 시간 제한, 메모리 제약
**해결방안**:
- Docker 이미지 최적화 (multi-stage build)
- 불필요한 의존성 제거
- 대안: Render.com 또는 Fly.io 고려

### 3. Frontend 미정
**문제**: 기술 스택 미확정으로 API 설계 지연
**해결방안**:
- RESTful API 표준 준수로 프레임워크 독립적 설계
- CORS 설정으로 모든 프론트엔드 지원
- OpenAPI 문서 자동 생성으로 연동 용이성 확보

## API 명세 (기본 구조)

| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| /api/health | GET | 서버 상태 확인 | - | {"status": "healthy"} |
| /api/v1/auth/login | POST | 로그인 | {"username", "password"} | {"access_token", "token_type"} |
| /api/v1/users | GET | 사용자 목록 | - | [{"id", "username", "created_at"}] |
| /api/v1/users/{id} | GET | 사용자 상세 | - | {"id", "username", "email", ...} |

## DB 스키마 (기본 구조)

```sql
-- users 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 추가 테이블은 프로젝트 요구사항에 따라 정의
```

## 폴더 구조
```
project/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── users.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   └── schemas/
│       ├── __init__.py
│       └── user.py
├── tests/
│   ├── __init__.py
│   └── test_api/
└── .claude/
    ├── CLAUDE.md
    └── ...
```

## 기술적 위험 및 대응방안

1. **Supabase 벤더 종속성**
   - 대응: 순수 PostgreSQL 호환 코드 작성
   - 마이그레이션 스크립트 준비

2. **Railway 무료 티어 제한**
   - 대응: 리소스 모니터링 설정
   - 스케일링 계획 수립

3. **프론트엔드 미확정**
   - 대응: API-First 개발
   - Postman Collection 제공

## CLAUDE.md 업데이트 필요 사항
- [ ] Frontend 기술 스택 확정 시 업데이트
- [ ] 프로젝트명 및 시작일 기입
- [ ] 현재 단계 명시 (MVP/고도화)

---

**다음 단계**: PM-Planner의 프로젝트 상세 요구사항 확인 후 API 및 DB 스키마 구체화 필요