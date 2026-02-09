"""__PROJECT_NAME_TITLE__ - FastAPI 메인 애플리케이션.

SaaS 풀스택 (인증 + 결제 + 대시보드) API 서버.
자동 생성됨 - __DATE__
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import init_db, get_db
from core.logging import setup_logging, get_logger
from routers import health, auth, payment, dashboard
from middleware.auth import AuthMiddleware


# 로깅 설정 (앱 생성 전에 호출)
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리."""
    logger.info("서버 시작 중...", debug=settings.DEBUG)

    # 데이터베이스 초기화
    await init_db()
    logger.info("데이터베이스 초기화 완료")

    logger.info(
        "서버 준비 완료",
        host=settings.HOST,
        port=settings.PORT,
    )

    yield

    logger.info("서버 종료 중...")


app = FastAPI(
    title="__PROJECT_NAME_TITLE__ API",
    description="__PROJECT_NAME__ SaaS API 서버 (인증 + 결제 + 대시보드)",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# 미들웨어
# ============================================================================

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 미들웨어
app.add_middleware(AuthMiddleware)


# 전역 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리."""
    logger.exception(
        "처리되지 않은 예외 발생",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "서버 내부 오류가 발생했습니다.",
        },
    )


# ============================================================================
# 라우터 등록
# ============================================================================

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(payment.router, prefix="/api", tags=["payment"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])


# ============================================================================
# 기본 엔드포인트
# ============================================================================

@app.get("/")
async def root():
    """루트 엔드포인트."""
    return {
        "name": "__PROJECT_NAME_TITLE__ API",
        "version": "0.1.0",
        "docs": "/docs",
        "type": "saas",
    }


# ============================================================================
# 진입점
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
