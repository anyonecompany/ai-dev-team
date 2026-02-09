"""Supabase 데이터베이스 연결.

Supabase 클라이언트 싱글톤 패턴 구현.
"""

from typing import Optional
from supabase import create_client, Client
from core.config import settings
from core.logging import get_logger

logger = get_logger("database")

# Supabase 클라이언트 싱글톤
_supabase: Optional[Client] = None


async def init_db() -> None:
    """데이터베이스 클라이언트 초기화.

    Supabase URL과 KEY가 설정된 경우에만 연결을 시도합니다.
    """
    global _supabase

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning(
            "Supabase 설정 누락",
            message="SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.",
        )
        return

    try:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(
            "Supabase 연결 실패",
            error=str(e),
            url=settings.SUPABASE_URL[:30] + "..." if len(settings.SUPABASE_URL) > 30 else settings.SUPABASE_URL,
        )
        raise


def get_db() -> Optional[Client]:
    """데이터베이스 클라이언트 반환.

    Returns:
        Supabase Client 또는 None (미연결 시)
    """
    return _supabase


def is_db_connected() -> bool:
    """데이터베이스 연결 상태 확인.

    Returns:
        연결 여부 (True/False)
    """
    return _supabase is not None
