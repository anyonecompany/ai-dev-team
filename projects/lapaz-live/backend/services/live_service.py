"""API-Football 라이브 이벤트 전용 서비스.

실시간 이벤트(골, 카드, 교체), 라인업, 경기 통계를 제공한다.
스코어/상태는 football-data.org에서 가져오므로 여기서는 제외.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Any

import httpx

import config

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
MAX_RETRIES = 1

# TTL (초)
EVENTS_TTL = 30       # 30초 (라이브 시)
LINEUPS_TTL = 300     # 5분
STATISTICS_TTL = 30   # 30초 (라이브 시)


# --- In-memory TTL Cache ---
class _TTLCache:
    """간단한 인메모리 TTL 캐시."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """캐시에서 값을 가져온다."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """TTL과 함께 값을 캐시에 저장한다."""
        self._store[key] = (time.monotonic() + ttl, value)


_cache = _TTLCache()

# --- HTTP Client Singleton ---
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """httpx.AsyncClient 싱글톤을 반환한다."""
    global _client
    if _client is None or _client.is_closed:
        headers: dict[str, str] = {
            "x-apisports-key": config.API_FOOTBALL_KEY,
        }
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(TIMEOUT_SECONDS),
            headers=headers,
            base_url=config.API_FOOTBALL_BASE,
        )
    return _client


async def _fetch(path: str, params: dict[str, Any] | None = None) -> list[dict]:
    """API-Football에서 데이터를 가져온다.

    Args:
        path: 엔드포인트 경로.
        params: 쿼리 파라미터.

    Returns:
        응답 데이터 리스트. 실패 시 빈 리스트.
    """
    client = _get_client()
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.get(path, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", [])
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("API-Football 요청 실패: %s (attempt %d)", e, attempt + 1)
            if attempt < MAX_RETRIES:
                continue
            return []

    return []


async def find_fixture_id(home_team: str = "Manchester United", away_team: str = "Aston Villa") -> int | None:
    """라이브 또는 당일 예정 경기에서 fixture_id를 찾는다.

    라이브 경기를 먼저 검색하고, 없으면 당일 PL 경기에서 찾는다.

    Args:
        home_team: 홈 팀명.
        away_team: 어웨이 팀명.

    Returns:
        fixture ID. 해당 경기 없으면 None.
    """
    cache_key = f"af_fixture_{home_team}_{away_team}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    def _match_teams(fixtures: list[dict]) -> int | None:
        for fix in fixtures:
            teams = fix.get("teams", {})
            h = teams.get("home", {}).get("name", "")
            a = teams.get("away", {}).get("name", "")
            if home_team.lower() in h.lower() and away_team.lower() in a.lower():
                return fix.get("fixture", {}).get("id")
        return None

    # 1) 라이브 경기 검색
    live_fixtures = await _fetch("/fixtures", params={"live": "all"})
    fid = _match_teams(live_fixtures)
    if fid:
        _cache.set(cache_key, fid, 300)
        return fid

    # 2) 당일 PL 경기 검색 (라인업 발표 후 ~ 경기 시작 전)
    today = date.today().isoformat()
    daily_fixtures = await _fetch("/fixtures", params={
        "date": today,
        "league": 39,
        "season": 2025,
    })
    fid = _match_teams(daily_fixtures)
    if fid:
        _cache.set(cache_key, fid, 300)
        return fid

    return None


async def get_match_events(fixture_id: int) -> list[dict]:
    """경기 이벤트(골, 카드, 교체 등)를 반환한다.

    Args:
        fixture_id: API-Football fixture ID.

    Returns:
        이벤트 리스트. 각 이벤트: {time, team, player, type, detail}.
    """
    cache_key = f"af_events_{fixture_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _fetch("/fixtures/events", params={"fixture": fixture_id})

    events: list[dict] = []
    for evt in data:
        events.append({
            "time": evt.get("time", {}).get("elapsed"),
            "extra_time": evt.get("time", {}).get("extra"),
            "team": evt.get("team", {}).get("name", ""),
            "player": evt.get("player", {}).get("name", ""),
            "assist": evt.get("assist", {}).get("name"),
            "type": evt.get("type", ""),
            "detail": evt.get("detail", ""),
        })

    _cache.set(cache_key, events, EVENTS_TTL)
    return events


async def get_match_lineups(fixture_id: int) -> dict:
    """경기 라인업을 반환한다.

    Args:
        fixture_id: API-Football fixture ID.

    Returns:
        {home: {team, formation, players}, away: {team, formation, players}}.
    """
    cache_key = f"af_lineups_{fixture_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _fetch("/fixtures/lineups", params={"fixture": fixture_id})
    if len(data) < 2:
        return {}

    def _parse_lineup(lineup: dict) -> dict:
        team = lineup.get("team", {}).get("name", "")
        formation = lineup.get("formation", "")
        start_xi = []
        for p in lineup.get("startXI", []):
            player = p.get("player", {})
            start_xi.append({
                "name": player.get("name", ""),
                "number": player.get("number"),
                "pos": player.get("pos", ""),
            })
        subs = []
        for p in lineup.get("substitutes", []):
            player = p.get("player", {})
            subs.append({
                "name": player.get("name", ""),
                "number": player.get("number"),
                "pos": player.get("pos", ""),
            })
        return {"team": team, "formation": formation, "start_xi": start_xi, "substitutes": subs}

    result = {
        "home": _parse_lineup(data[0]),
        "away": _parse_lineup(data[1]),
    }

    _cache.set(cache_key, result, LINEUPS_TTL)
    return result


async def get_match_statistics(fixture_id: int) -> dict:
    """경기 통계를 반환한다.

    Args:
        fixture_id: API-Football fixture ID.

    Returns:
        {home: {team, stats}, away: {team, stats}}.
    """
    cache_key = f"af_stats_{fixture_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _fetch("/fixtures/statistics", params={"fixture": fixture_id})
    if len(data) < 2:
        return {}

    def _parse_stats(team_data: dict) -> dict:
        team = team_data.get("team", {}).get("name", "")
        stats: dict[str, Any] = {}
        for s in team_data.get("statistics", []):
            stats[s.get("type", "")] = s.get("value")
        return {"team": team, "stats": stats}

    result = {
        "home": _parse_stats(data[0]),
        "away": _parse_stats(data[1]),
    }

    _cache.set(cache_key, result, STATISTICS_TTL)
    return result


async def get_fixture_referee(fixture_id: int) -> str | None:
    """경기의 주심 정보를 반환한다.

    API-Football /fixtures 엔드포인트의 response[].fixture.referee 필드를 추출한다.

    Args:
        fixture_id: API-Football fixture ID.

    Returns:
        주심 이름 문자열. 정보가 없으면 None.
    """
    cache_key = f"af_referee_{fixture_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = await _fetch("/fixtures", params={"id": fixture_id})
    if not data:
        return None

    referee = data[0].get("fixture", {}).get("referee")
    if referee:
        _cache.set(cache_key, referee, LINEUPS_TTL)  # 주심은 자주 바뀌지 않으므로 5분 TTL
    return referee


async def get_live_state(fixture_id: int) -> dict:
    """라이브 경기의 이벤트+라인업+통계+주심을 한번에 가져온다.

    Args:
        fixture_id: API-Football fixture ID.

    Returns:
        {events, lineups, statistics, referee} 통합 딕셔너리.
    """
    events, lineups, statistics, referee = await asyncio.gather(
        get_match_events(fixture_id),
        get_match_lineups(fixture_id),
        get_match_statistics(fixture_id),
        get_fixture_referee(fixture_id),
    )

    return {
        "events": events,
        "lineups": lineups,
        "statistics": statistics,
        "referee": referee,
    }
