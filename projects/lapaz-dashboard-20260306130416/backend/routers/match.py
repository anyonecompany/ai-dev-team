"""GET /api/match/live — 경기 정보 라우터."""

from fastapi import APIRouter

from models.schemas import MatchInfoResponse
from services import match_service

router = APIRouter()


@router.get("/match/live", response_model=MatchInfoResponse)
async def get_live_match() -> MatchInfoResponse:
    """현재 라이브 경기 정보를 반환한다."""
    info = await match_service.get_match_info()
    return MatchInfoResponse(**info)
