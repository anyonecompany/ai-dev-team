"""GET /api/errors/summary — 에러 로그 요약 라우터."""

from fastapi import APIRouter

from services.error_log_service import get_error_summary

router = APIRouter(tags=["errors"])


@router.get("/errors/summary")
async def error_summary(hours: int = 24) -> dict:
    """최근 N시간의 에러 유형별 카운트를 반환한다.

    Args:
        hours: 조회 범위 (시간, 기본 24).

    Returns:
        에러 유형별/파이프라인 단계별 카운트 요약.
    """
    return await get_error_summary(hours=hours)
