"""경기 정보 라우터 — football-data.org + API-Football 통합 엔드포인트."""

import logging

from fastapi import APIRouter

import config
from models.schemas import (
    MatchInfoResponse,
    MatchPreview,
    StandingEntry,
    TeamStats,
)
from services import match_service
from services.football_data_service import (
    get_epl_standings,
    get_match_preview,
    get_match_score,
    get_team_squad,
)
from services.live_service import find_fixture_id, get_live_state

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/match/live", response_model=MatchInfoResponse)
async def get_live_match() -> MatchInfoResponse:
    """현재 라이브 경기 정보를 반환한다.

    환경변수 기반 정보를 football-data.org 스코어 및 API-Football
    fixture 조회로 보정한다. football-data.org가 느릴 경우
    API-Football에서 라이브 fixture가 발견되면 status를 "live"로 덮어쓴다.
    """
    info = await match_service.get_match_info()

    # football-data.org 스코어로 상태/분 보정
    score = await get_match_score(config.MATCH_ID_FD)
    if score:
        if score.get("status") in ("live", "halftime"):
            info["status"] = score["status"]
            info["current_minute"] = score.get("minute")
        elif score.get("status") == "finished":
            info["status"] = "finished"
            info["current_minute"] = 90

    # football-data.org가 아직 upcoming인데 API-Football에 라이브 fixture가 있으면 덮어쓴다
    if info["status"] == "upcoming":
        fixture_id = await find_fixture_id()
        if fixture_id:
            live_data = await get_live_state(fixture_id)
            # live_state에 이벤트가 있으면 경기가 진행 중인 것
            if live_data.get("events"):
                info["status"] = "live"
                logger.info(
                    "football-data.org 지연 감지 — API-Football 기준 live로 보정 (fixture=%s)",
                    fixture_id,
                )

    return MatchInfoResponse(**info)


@router.get("/match/preview", response_model=MatchPreview)
async def get_preview() -> MatchPreview:
    """Man Utd vs Aston Villa 매치 프리뷰를 반환한다.

    football-data.org에서 순위 + 스쿼드를 조합한다.
    """
    data = await get_match_preview(
        home_id=config.MANUTD_FD_ID,
        away_id=config.VILLA_FD_ID,
    )
    return MatchPreview(**data)


@router.get("/standings", response_model=list[StandingEntry])
async def get_standings() -> list[StandingEntry]:
    """EPL 리그 순위표를 반환한다."""
    standings = await get_epl_standings()
    return [StandingEntry(**entry) for entry in standings]


@router.get("/teams/{team_id}/stats", response_model=TeamStats)
async def get_team_stats(team_id: int) -> TeamStats:
    """특정 팀의 상세 통계를 반환한다.

    Args:
        team_id: football-data.org 팀 ID (예: 66=Man Utd, 58=Aston Villa).
    """
    data = await get_team_squad(team_id)
    if not data:
        return TeamStats(team_name="", team_id=team_id)

    # 순위표에서 해당 팀 정보 매칭
    standings = await get_epl_standings()
    for entry in standings:
        if entry["team_id"] == team_id:
            data["standings"] = entry
            form = entry.get("form", [])
            if form:
                data["recent_form"] = form
            break

    return TeamStats(**data)


@router.get("/match/live-state")
async def get_match_live_state() -> dict:
    """라이브 경기 상태를 반환한다.

    football-data.org에서 스코어/상태, API-Football에서 이벤트/라인업/통계를 병합한다.
    """
    # 1. football-data.org에서 스코어
    score = await get_match_score(config.MATCH_ID_FD)

    # 2. 라이브/예정 경기 모두 API-Football 데이터 조회 (라인업은 경기 ~1시간 전 발표)
    live_data: dict = {}
    fixture_id = await find_fixture_id()
    if fixture_id:
        live_data = await get_live_state(fixture_id)

    return {
        "score": score,
        "events": live_data.get("events", []),
        "lineups": live_data.get("lineups", {}),
        "statistics": live_data.get("statistics", {}),
        "referee": live_data.get("referee"),
    }


@router.get("/health/data-sources")
async def check_data_sources() -> dict:
    """데이터 소스 연결 상태를 확인한다."""
    # football-data.org 체크
    fd_status = "error"
    try:
        standings = await get_epl_standings()
        if standings:
            fd_status = "ok"
    except Exception as e:
        logger.warning("football-data.org 헬스체크 실패: %s", e)

    # API-Football 체크
    af_status = "ok" if config.API_FOOTBALL_KEY else "no_key"

    return {
        "football_data": fd_status,
        "api_football": af_status,
    }
