"""전역 에러 핸들러 미들웨어.

예외 처리 및 에러 응답 표준화.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger

logger = get_logger("middleware.error")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """전역 에러 핸들러 미들웨어.

    처리되지 않은 예외를 잡아서 표준화된 JSON 응답을 반환합니다.
    """

    async def dispatch(self, request: Request, call_next):
        """요청 처리 및 에러 핸들링."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(
                "미들웨어에서 예외 포착",
                path=request.url.path,
                method=request.method,
                error=str(e),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "서버 내부 오류가 발생했습니다.",
                    "detail": str(e) if logger.isEnabledFor(10) else None,  # DEBUG일 때만
                },
            )


class NotFoundError(Exception):
    """리소스를 찾을 수 없음."""

    def __init__(self, resource: str, id: str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource}을(를) 찾을 수 없습니다: {id}")


class ValidationError(Exception):
    """유효성 검증 실패."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"유효성 검증 실패 - {field}: {message}")


class UnauthorizedError(Exception):
    """인증 실패."""

    def __init__(self, message: str = "인증이 필요합니다."):
        super().__init__(message)
