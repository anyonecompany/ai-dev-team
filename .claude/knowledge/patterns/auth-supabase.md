# Supabase Auth Pattern

> 카테고리: Backend / Authentication
> 출처: 템플릿 (saas 프로젝트 기준)
> 최종 갱신: 2026-02-03

## 개요

Supabase Auth를 FastAPI와 통합하는 패턴.
JWT 검증, 사용자 세션 관리, 보호된 라우트를 지원합니다.

## 구현

### 1. 인증 의존성 (core/auth.py)

```python
"""Supabase Auth 의존성."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.database import get_db
from models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """현재 사용자 반환 (선택적 인증)."""
    if not credentials:
        return None

    db = get_db()
    if not db:
        return None

    try:
        # Supabase JWT 검증
        user_response = db.auth.get_user(credentials.credentials)
        if user_response and user_response.user:
            return User(
                id=user_response.user.id,
                email=user_response.user.email,
                created_at=user_response.user.created_at,
            )
    except Exception:
        return None

    return None


async def require_user(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """인증 필수 의존성."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# 타입 별칭
CurrentUser = Depends(get_current_user)
RequiredUser = Depends(require_user)
```

### 2. 인증 라우터 (routers/auth.py)

```python
"""인증 API 엔드포인트."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from core.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """회원가입."""
    db = get_db()
    if not db:
        raise HTTPException(500, "Database not available")

    try:
        response = db.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })

        if response.user is None:
            raise HTTPException(400, "회원가입에 실패했습니다.")

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
            }
        )
    except Exception as e:
        raise HTTPException(400, f"회원가입 실패: {str(e)}")


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """로그인."""
    db = get_db()
    if not db:
        raise HTTPException(500, "Database not available")

    try:
        response = db.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if response.user is None:
            raise HTTPException(401, "이메일 또는 비밀번호가 올바르지 않습니다.")

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
            }
        )
    except Exception:
        raise HTTPException(401, "이메일 또는 비밀번호가 올바르지 않습니다.")


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """토큰 갱신."""
    db = get_db()
    if not db:
        raise HTTPException(500, "Database not available")

    try:
        response = db.auth.refresh_session(refresh_token)
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except Exception:
        raise HTTPException(401, "토큰 갱신에 실패했습니다.")


@router.post("/logout")
async def logout():
    """로그아웃."""
    db = get_db()
    if db:
        db.auth.sign_out()
    return {"message": "로그아웃되었습니다."}
```

### 3. 보호된 라우트에서 사용

```python
# routers/protected.py
from fastapi import APIRouter, Depends
from core.auth import require_user
from models.user import User

router = APIRouter(prefix="/api/protected", tags=["protected"])


@router.get("/profile")
async def get_profile(user: User = Depends(require_user)):
    """현재 사용자 프로필."""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


@router.get("/dashboard")
async def get_dashboard(user: User = Depends(require_user)):
    """대시보드 데이터."""
    return {
        "user_id": user.id,
        "stats": {
            "projects": 5,
            "tasks": 23,
        }
    }
```

## 프론트엔드 연동

```typescript
// stores/useAuthStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken: string | null;
  user: { id: string; email: string } | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,

      login: async (email, password) => {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        set({ accessToken: data.access_token, user: data.user });
      },

      logout: () => {
        set({ accessToken: null, user: null });
      },
    }),
    { name: 'auth-storage' }
  )
);
```

## 장점

1. **Supabase 통합**: 별도 JWT 라이브러리 불필요
2. **의존성 주입**: FastAPI Depends로 깔끔한 인증 처리
3. **유연한 인증**: 필수/선택 인증 모두 지원
4. **토큰 갱신**: refresh_token으로 세션 유지

## 관련 패턴

- [supabase-connection.md - DB 연결](#)
- [react-api-client.md - API 클라이언트](#)
