# Supabase Connection Pattern

> 카테고리: Backend / Database
> 출처: dashboard/backend/core/database.py
> 최종 갱신: 2026-02-03

## 개요

FastAPI 애플리케이션에서 Supabase 클라이언트를 싱글톤으로 관리하는 패턴.
비동기 초기화와 전역 접근을 지원합니다.

## 구현

```python
# core/database.py
"""Supabase 데이터베이스 연결."""

from typing import Optional
from supabase import create_client, Client
from core.config import settings

supabase: Optional[Client] = None


async def init_db() -> None:
    """데이터베이스 클라이언트 초기화."""
    global supabase
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_db() -> Optional[Client]:
    """데이터베이스 클라이언트 반환."""
    return supabase
```

## 사용법

### FastAPI lifespan에서 초기화

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

### 서비스에서 사용

```python
# services/some_service.py
from core.database import get_db

async def get_items():
    db = get_db()
    if not db:
        raise Exception("Database not initialized")

    response = db.table("items").select("*").execute()
    return response.data
```

## 필요 환경변수

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

## 장점

1. **싱글톤**: 애플리케이션 전체에서 하나의 클라이언트만 사용
2. **지연 초기화**: 환경변수가 없으면 초기화 건너뜀 (개발 편의)
3. **타입 안전**: Optional 타입으로 None 체크 강제
4. **테스트 용이**: 모듈 레벨 변수로 쉽게 모킹 가능

## 주의사항

- `supabase-py`는 내부적으로 connection pooling을 관리함
- 실제 쿼리 시 `get_db()` 반환값 None 체크 필수
- 환경변수 누락 시 조용히 실패 (의도적 설계)

## 관련 패턴

- [config.py - 설정 관리](#)
- [dependencies.py - FastAPI 의존성 주입](#)
