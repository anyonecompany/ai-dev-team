"""football-data.org API 연동 서비스.

EPL 순위, 팀 스쿼드, 경기 스코어, 일정 데이터를 제공한다.
무료 티어 제한: 10 requests/분 (요청 간 최소 6초 간격).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)

# --- Constants ---
TIMEOUT_SECONDS = 10
MAX_RETRIES = 1

# TTL (초)
STANDINGS_TTL = 600   # 10분
SQUAD_TTL = 1800      # 30분
SCORE_TTL_LIVE = 30   # 라이브 시 30초
SCORE_TTL_DEFAULT = 600  # 비라이브 10분


# --- In-memory TTL Cache ---
class _TTLCache:
    """간단한 인메모리 TTL 캐시."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """캐시에서 값을 가져온다. 만료 시 None을 반환한다."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """TTL(초)과 함께 값을 캐시에 저장한다."""
        self._store[key] = (time.monotonic() + ttl, value)


_cache = _TTLCache()

# --- Rate Limiter (슬라이딩 윈도우: 60초 내 최대 10 요청) ---
_request_timestamps: list[float] = []
_rate_lock = asyncio.Lock()
_MAX_REQUESTS = 10
_WINDOW_SECONDS = 60.0


# --- HTTP Client Singleton ---
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """httpx.AsyncClient 싱글톤을 반환한다."""
    global _client
    if _client is None or _client.is_closed:
        headers: dict[str, str] = {}
        if config.FOOTBALL_DATA_TOKEN:
            headers["X-Auth-Token"] = config.FOOTBALL_DATA_TOKEN
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(TIMEOUT_SECONDS),
            headers=headers,
            base_url=config.FOOTBALL_DATA_BASE,
        )
    return _client


async def _rate_limited_get(path: str, params: dict[str, Any] | None = None) -> dict | None:
    """Rate limit을 준수하며 GET 요청을 실행한다.

    Args:
        path: API 엔드포인트 경로 (예: /competitions/PL/standings).
        params: 쿼리 파라미터.

    Returns:
        JSON 응답 딕셔너리. 실패 시 None.
    """
    client = _get_client()

    async with _rate_lock:
        now = time.monotonic()
        # 윈도우 밖 타임스탬프 제거
        _request_timestamps[:] = [t for t in _request_timestamps if now - t < _WINDOW_SECONDS]
        # 윈도우 가득 차면 가장 오래된 요청이 윈도우 밖으로 나갈 때까지 대기
        if len(_request_timestamps) >= _MAX_REQUESTS:
            wait = _WINDOW_SECONDS - (now - _request_timestamps[0]) + 0.1
            if wait > 0:
                logger.info("Rate limit 대기: %.1f초", wait)
                await asyncio.sleep(wait)

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await client.get(path, params=params)
                _request_timestamps.append(time.monotonic())
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "football-data.org HTTP %s: %s (attempt %d)",
                    e.response.status_code, path, attempt + 1,
                )
                if e.response.status_code == 429:
                    # Rate limited — 60초 대기 후 재시도
                    await asyncio.sleep(60)
                    continue
                if attempt < MAX_RETRIES:
                    continue
                return None
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning("football-data.org 요청 실패: %s (attempt %d)", e, attempt + 1)
                if attempt < MAX_RETRIES:
                    continue
                return None

    return None


# --- Public API ---

async def get_epl_standings() -> list[dict]:
    """EPL 리그 순위표를 반환한다.

    Returns:
        StandingEntry 호환 딕셔너리 리스트. 에러 시 빈 리스트.
    """
    cache_key = "fd_epl_standings"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _rate_limited_get("/competitions/PL/standings")
    if not data:
        return []

    try:
        # standings[0] = TOTAL, standings[1] = HOME, standings[2] = AWAY
        table = data["standings"][0]["table"]
    except (KeyError, IndexError, TypeError):
        logger.warning("football-data.org 순위표 파싱 실패")
        return []

    standings: list[dict] = []
    for row in table:
        team = row.get("team", {})

        # form 파싱: "W,W,D,L,W" → ["W","W","D","L","W"]
        form_str = row.get("form", "")
        form = [f.strip() for f in form_str.split(",") if f.strip()] if form_str else []

        entry = {
            "rank": row.get("position", 0),
            "team_name": team.get("name", ""),
            "team_id": team.get("id", 0),
            "played": row.get("playedGames", 0),
            "wins": row.get("won", 0),
            "draws": row.get("draw", 0),
            "losses": row.get("lost", 0),
            "goals_for": row.get("goalsFor", 0),
            "goals_against": row.get("goalsAgainst", 0),
            "goal_diff": row.get("goalDifference", 0),
            "points": row.get("points", 0),
            "form": form,
        }
        standings.append(entry)

    _cache.set(cache_key, standings, STANDINGS_TTL)
    return standings


async def get_team_squad(team_id: int) -> dict:
    """팀 스쿼드를 반환한다.

    Args:
        team_id: football-data.org 팀 ID (맨유=66, 빌라=58).

    Returns:
        TeamStats 호환 딕셔너리. 에러 시 기본 구조.
    """
    cache_key = f"fd_squad_{team_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _rate_limited_get(f"/teams/{team_id}")
    if not data:
        return {"team_name": "", "team_id": team_id, "standings": None, "squad": [], "recent_form": [], "top_scorers": []}

    team_name = data.get("name", "")

    # 감독 정보
    coach_data = data.get("coach", {})
    coach: dict | None = None
    if coach_data:
        coach = {
            "name": coach_data.get("name", ""),
            "nationality": coach_data.get("nationality", ""),
        }

    # 포지션 매핑
    pos_map = {
        "Goalkeeper": "Keeper",
        "Defence": "Defender",
        "Midfield": "Midfielder",
        "Offence": "Attacker",
    }

    squad: list[dict] = []
    for player in data.get("squad", []):
        raw_pos = player.get("position", "Unknown")
        squad.append({
            "name": player.get("name", ""),
            "position": pos_map.get(raw_pos, raw_pos),
            "country": player.get("nationality", ""),
            "number": player.get("shirtNumber"),
        })

    result = {
        "team_name": team_name,
        "team_id": team_id,
        "standings": None,  # standings는 별도 API에서 채움
        "squad": squad,
        "recent_form": [],
        "top_scorers": [],
        "coach": coach,
    }

    _cache.set(cache_key, result, SQUAD_TTL)
    return result


async def get_match_score(match_id: int) -> dict:
    """경기 스코어 및 상태를 반환한다.

    Args:
        match_id: football-data.org 매치 ID (3/15 경기=538082).

    Returns:
        스코어 딕셔너리: {status, minute, home_score, away_score, home_team, away_team}.
        에러 시 빈 딕셔너리.
    """
    cache_key = f"fd_score_{match_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _rate_limited_get(f"/matches/{match_id}")
    if not data:
        return {}

    status_map = {
        "SCHEDULED": "upcoming",
        "TIMED": "upcoming",
        "IN_PLAY": "live",
        "PAUSED": "halftime",
        "FINISHED": "finished",
        "SUSPENDED": "suspended",
        "POSTPONED": "postponed",
        "CANCELLED": "cancelled",
    }

    fd_status = data.get("status", "SCHEDULED")
    score = data.get("score", {})
    full_time = score.get("fullTime", {})
    home_team = data.get("homeTeam", {})
    away_team = data.get("awayTeam", {})

    result = {
        "status": status_map.get(fd_status, fd_status.lower()),
        "minute": data.get("minute"),
        "home_score": full_time.get("home"),
        "away_score": full_time.get("away"),
        "home_team": home_team.get("name", ""),
        "away_team": away_team.get("name", ""),
        "match_date": data.get("utcDate", ""),
    }

    # 라이브 중이면 30초, 아니면 10분 캐시
    ttl = SCORE_TTL_LIVE if fd_status == "IN_PLAY" else SCORE_TTL_DEFAULT
    _cache.set(cache_key, result, ttl)
    return result


async def get_scheduled_matches(date_from: str, date_to: str) -> list[dict]:
    """기간 내 EPL 예정 경기를 반환한다.

    Args:
        date_from: 시작일 (YYYY-MM-DD).
        date_to: 종료일 (YYYY-MM-DD).

    Returns:
        경기 리스트. 에러 시 빈 리스트.
    """
    cache_key = f"fd_schedule_{date_from}_{date_to}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _rate_limited_get(
        "/competitions/PL/matches",
        params={"dateFrom": date_from, "dateTo": date_to},
    )
    if not data:
        return []

    matches: list[dict] = []
    for m in data.get("matches", []):
        home = m.get("homeTeam", {})
        away = m.get("awayTeam", {})
        matches.append({
            "match_id": m.get("id"),
            "home_team": home.get("name", ""),
            "away_team": away.get("name", ""),
            "date": m.get("utcDate", ""),
            "status": m.get("status", ""),
        })

    _cache.set(cache_key, matches, STANDINGS_TTL)
    return matches


async def get_match_preview(home_id: int, away_id: int) -> dict:
    """홈/어웨이 팀의 매치 프리뷰 데이터를 결합하여 반환한다.

    순위표 + 양팀 스쿼드를 병렬 로드하고, 순위표에서 각 팀의 순위를 매칭한다.

    Args:
        home_id: 홈 팀 football-data.org ID (맨유=66).
        away_id: 어웨이 팀 football-data.org ID (빌라=58).

    Returns:
        MatchPreview 호환 딕셔너리.
    """
    standings, home_data, away_data = await asyncio.gather(
        get_epl_standings(),
        get_team_squad(home_id),
        get_team_squad(away_id),
    )

    # 순위표에서 각 팀 정보 매칭
    for entry in standings:
        if entry["team_id"] == home_id:
            home_data["standings"] = entry
            form = entry.get("form", [])
            if form:
                home_data["recent_form"] = form
        elif entry["team_id"] == away_id:
            away_data["standings"] = entry
            form = entry.get("form", [])
            if form:
                away_data["recent_form"] = form

    # 경기 스코어/날짜 가져오기
    match_score = await get_match_score(config.MATCH_ID_FD)
    match_date = match_score.get("match_date", "")

    return {
        "home": home_data,
        "away": away_data,
        "standings": standings,
        "match_date": match_date,
        "match_id": config.MATCH_ID_FD,
    }
