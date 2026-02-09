"""헬스 체크 라우터.

서버 상태 및 데이터베이스 연결 확인 엔드포인트.
"""

from fastapi import APIRouter

from core.database import is_db_connected
from core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트.

    Returns:
        서버 상태, 버전, DB 연결 상태
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "project": settings.PROJECT_NAME,
        "database": {
            "connected": is_db_connected(),
        },
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """상세 헬스 체크 엔드포인트.

    Returns:
        상세 서버 상태 정보
    """
    import platform
    import sys

    return {
        "status": "healthy",
        "version": "0.1.0",
        "project": settings.PROJECT_NAME,
        "environment": {
            "debug": settings.DEBUG,
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "database": {
            "connected": is_db_connected(),
            "url_configured": bool(settings.SUPABASE_URL),
        },
    }
