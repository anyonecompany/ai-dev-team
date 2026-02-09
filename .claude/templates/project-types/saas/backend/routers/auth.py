"""인증 라우터.

Supabase Auth를 활용한 인증 API.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from core.logging import get_logger
from core.database import get_db
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth")


class LoginRequest(BaseModel):
    """로그인 요청."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """회원가입 요청."""
    email: EmailStr
    password: str
    name: str | None = None


class AuthResponse(BaseModel):
    """인증 응답."""
    access_token: str
    refresh_token: str
    user: dict


class RefreshRequest(BaseModel):
    """토큰 갱신 요청."""
    refresh_token: str


def get_auth_service() -> AuthService:
    """AuthService 의존성."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="데이터베이스 연결 실패")
    return AuthService(db)


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """회원가입.

    이메일/비밀번호로 새 계정을 생성합니다.
    """
    logger.info("회원가입 요청", email=request.email)

    try:
        result = await auth_service.register(
            email=request.email,
            password=request.password,
            name=request.name,
        )
        logger.info("회원가입 성공", email=request.email)
        return result
    except Exception as e:
        logger.warning("회원가입 실패", email=request.email, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """로그인.

    이메일/비밀번호로 인증하고 토큰을 발급합니다.
    """
    logger.info("로그인 요청", email=request.email)

    try:
        result = await auth_service.login(
            email=request.email,
            password=request.password,
        )
        logger.info("로그인 성공", email=request.email)
        return result
    except Exception as e:
        logger.warning("로그인 실패", email=request.email, error=str(e))
        raise HTTPException(status_code=401, detail="인증에 실패했습니다.")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """토큰 갱신.

    refresh_token으로 새 access_token을 발급합니다.
    """
    try:
        result = await auth_service.refresh(request.refresh_token)
        return result
    except Exception as e:
        logger.warning("토큰 갱신 실패", error=str(e))
        raise HTTPException(status_code=401, detail="토큰 갱신에 실패했습니다.")


@router.post("/logout")
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
):
    """로그아웃.

    현재 세션을 종료합니다.
    """
    # Supabase는 클라이언트에서 로그아웃 처리
    return {"message": "로그아웃 되었습니다."}


@router.get("/me")
async def get_current_user(
    # 실제 구현 시 auth 미들웨어에서 user 주입
    auth_service: AuthService = Depends(get_auth_service),
):
    """현재 사용자 정보.

    인증된 사용자의 정보를 반환합니다.
    TODO: JWT에서 user_id 추출 후 사용자 정보 조회
    """
    # 임시 응답
    return {
        "id": "user_placeholder",
        "email": "user@example.com",
        "name": "Test User",
    }
