# TASK-043 결과

생성 시간: 2026-02-02T17:55:48.958292

---

# 시스템 설계 문서

## 아키텍처 개요

### 시스템 구조
```
┌─────────────────────────────────────────────┐
│            Frontend (Vercel)                │
│         - React/Next.js                     │
│         - Tailwind CSS                      │
│         - Axios for API calls              │
└─────────────────┬───────────────────────────┘
                  │ HTTPS
┌─────────────────▼───────────────────────────┐
│         Backend API (Railway)               │
│         - FastAPI                           │
│         - Uvicorn ASGI Server              │
│         - Pydantic for validation          │
└─────────────────┬───────────────────────────┘
                  │ PostgreSQL Protocol
┌─────────────────▼───────────────────────────┐
│         Database (Supabase)                 │
│         - PostgreSQL                        │
│         - Row Level Security                │
│         - Realtime subscriptions           │
└─────────────────────────────────────────────┘
```

### 차단 해제를 위한 핵심 설계 원칙
1. **의존성 최소화**: 외부 라이브러리 의존성을 최소화하고 Python 표준 라이브러리 우선 사용
2. **단순화된 인증**: Supabase의 내장 인증 대신 간단한 JWT 토큰 기반 인증 구현
3. **캐싱 전략**: Redis 대신 인메모리 캐싱으로 시작
4. **비동기 처리**: Celery 대신 FastAPI의 백그라운드 태스크 활용

## API 명세

### 인증 관련
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/api/auth/register` | POST | 사용자 등록 | `{email, password, name}` | `{user_id, token}` |
| `/api/auth/login` | POST | 로그인 | `{email, password}` | `{token, user}` |
| `/api/auth/refresh` | POST | 토큰 갱신 | `{refresh_token}` | `{token}` |

### 핵심 비즈니스 로직
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/api/resources` | GET | 리소스 목록 조회 | `?page=1&limit=10` | `{items[], total, page}` |
| `/api/resources` | POST | 리소스 생성 | `{name, data}` | `{id, created_at}` |
| `/api/resources/{id}` | GET | 리소스 상세 조회 | - | `{resource_detail}` |
| `/api/resources/{id}` | PUT | 리소스 수정 | `{updated_data}` | `{updated_resource}` |
| `/api/resources/{id}` | DELETE | 리소스 삭제 | - | `{success: true}` |

## DB 스키마

### users 테이블
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

### resources 테이블 (예시)
```sql
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    data JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_resources_user_id ON resources(user_id);
CREATE INDEX idx_resources_status ON resources(status);
```

## 기술적 위험 및 해결책

### 1. Supabase 연결 문제
- **위험**: Supabase 클라이언트 라이브러리 의존성 충돌
- **해결**: 
  - psycopg2 또는 asyncpg로 직접 PostgreSQL 연결
  - 환경변수로 DATABASE_URL 관리
  ```python
  # .env
  DATABASE_URL=postgresql://user:pass@host:5432/db
  ```

### 2. 인증 시스템 복잡도
- **위험**: 복잡한 인증 라이브러리 설정 문제
- **해결**: 
  - python-jose를 이용한 간단한 JWT 구현
  - 세션 관리는 메모리 캐시로 시작
  ```python
  from jose import jwt
  from datetime import datetime, timedelta
  
  def create_token(user_id: str) -> str:
      expire = datetime.utcnow() + timedelta(hours=24)
      return jwt.encode(
          {"sub": user_id, "exp": expire},
          SECRET_KEY,
          algorithm="HS256"
      )
  ```

### 3. 비동기 작업 처리
- **위험**: Celery/Redis 설정의 복잡도
- **해결**: 
  - FastAPI BackgroundTasks 활용
  - 긴 작업은 별도 엔드포인트로 상태 폴링
  ```python
  from fastapi import BackgroundTasks
  
  @app.post("/api/tasks")
  async def create_task(background_tasks: BackgroundTasks):
      task_id = str(uuid.uuid4())
      background_tasks.add_task(long_running_task, task_id)
      return {"task_id": task_id}
  ```

### 4. CORS 설정
- **위험**: 프론트엔드-백엔드 통신 차단
- **해결**: 
  - FastAPI CORS 미들웨어 설정
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # 프로덕션에서는 특정 도메인만
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

## 폴더 구조
```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 앱 진입점
│   │   ├── config.py         # 환경 설정
│   │   ├── database.py       # DB 연결 설정
│   │   ├── models/           # SQLAlchemy 모델
│   │   ├── schemas/          # Pydantic 스키마
│   │   ├── routers/          # API 라우터
│   │   ├── services/         # 비즈니스 로직
│   │   └── utils/            # 유틸리티 함수
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── docs/
```

## 다음 단계를 위한 준비
1. Backend Developer는 위 스키마를 바탕으로 FastAPI 앱 초기 구조 생성
2. Frontend Developer는 API 명세를 참고하여 API 클라이언트 설정
3. 각 개발자는 .env.example 파일 참고하여 로컬 환경 설정

---

**업데이트 필요 사항**:
- CLAUDE.md의 기술 스택 섹션에 구체적인 라이브러리 버전 추가
- 프로젝트별 구체적인 비즈니스 로직에 맞춰 API 명세 수정