"""인증 미들웨어.

JWT 토큰 검증 및 사용자 정보 주입.
"""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger
from core.database import get_db

logger = get_logger("middleware.auth")

# HTTP Bearer 스키마
security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """인증 미들웨어.

    Authorization 헤더에서 JWT를 추출하고 검증합니다.
    """

    # 인증 제외 경로
    EXCLUDE_PATHS = [
        "/",
        "/health",
        "/health/detailed",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/refresh",
        "/api/payment/webhook",
        "/api/payment/plans",
    ]

    async def dispatch(self, request: Request, call_next):
        """요청 처리."""
        # 제외 경로 체크
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)

        # OPTIONS 요청은 통과
        if request.method == "OPTIONS":
            return await call_next(request)

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            # 인증 필요 경로에서 토큰 없음
            # 현재는 경고만 로깅하고 통과 (개발 모드)
            logger.warning("인증 토큰 없음", path=request.url.path)
            # 프로덕션에서는 아래 주석 해제
            # raise HTTPException(status_code=401, detail="인증이 필요합니다.")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            try:
                # TODO: Supabase JWT 검증
                # db = get_db()
                # user = db.auth.get_user(token)
                # request.state.user = user

                logger.debug("인증 토큰 확인됨", path=request.url.path)

            except Exception as e:
                logger.warning("인증 토큰 검증 실패", error=str(e))
                # 프로덕션에서는 아래 주석 해제
                # raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

        return await call_next(request)


async def get_current_user(request: Request):
    """현재 사용자 가져오기.

    AuthMiddleware에서 주입한 사용자 정보를 반환합니다.
    라우터에서 Depends(get_current_user)로 사용.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return user


async def get_optional_user(request: Request):
    """현재 사용자 가져오기 (선택적).

    인증되지 않아도 에러를 발생시키지 않습니다.
    """
    return getattr(request.state, "user", None)
