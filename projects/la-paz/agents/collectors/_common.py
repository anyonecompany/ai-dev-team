"""La Paz Agent 2 — 공통 유틸리티.

팀/대회/시즌/선수 ID 해석, NaN-safe 변환, football-data.org 헬퍼.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# agents/ 디렉토리를 sys.path에 추가하여 shared_config 접근
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_config import (  # noqa: E402
    get_agent_logger,
    sb_select,
    FOOTBALL_DATA_TOKEN,
)

log = get_agent_logger("agent_2")


# ── NaN-safe 변환 ────────────────────────────────

def _safe(val, default=None):
    """NaN-safe 값 변환."""
    if val is None:
        return default
    try:
        import pandas as pd
        if isinstance(val, float) and pd.isna(val):
            return default
    except ImportError:
        if isinstance(val, float) and val != val:
            return default
    return val


# ── ID 해석 함수들 ───────────────────────────────

def _resolve_team_id(team_name: str, cache: dict) -> str | None:
    """팀 canonical 이름으로 ID 조회."""
    if not team_name:
        return None
    if team_name in cache:
        return cache[team_name]
    teams = sb_select("teams", filters={"canonical": team_name.strip()})
    if teams:
        cache[team_name] = teams[0]["id"]
        return teams[0]["id"]
    # aliases 검색
    all_teams = sb_select("teams", limit=5000)
    for t in all_teams:
        aliases = t.get("aliases") or []
        if team_name in aliases or team_name.strip() == t["canonical"]:
            cache[team_name] = t["id"]
            return t["id"]
    return None


def _resolve_comp_id(source_id: str, source: str, cache: dict) -> str | None:
    """대회 source_id로 ID 조회."""
    key = f"{source}_{source_id}"
    if key in cache:
        return cache[key]
    comps = sb_select("competitions", filters={"source_id": source_id, "source": source})
    if comps:
        cache[key] = comps[0]["id"]
        return comps[0]["id"]
    return None


def _resolve_season_id(comp_id: str | None, year: str, cache: dict) -> str | None:
    """시즌 ID 조회."""
    if not comp_id:
        return None
    key = f"{comp_id}_{year}"
    if key in cache:
        return cache[key]
    seasons = sb_select("seasons", filters={"competition_id": comp_id, "year": year})
    if seasons:
        cache[key] = seasons[0]["id"]
        return seasons[0]["id"]
    return None


def _resolve_player_id(player_name: str, cache: dict) -> str | None:
    """선수 이름으로 ID 조회."""
    if not player_name:
        return None
    if player_name in cache:
        return cache[player_name]
    players = sb_select("players", filters={"name": player_name.strip()})
    if players:
        cache[player_name] = players[0]["id"]
        return players[0]["id"]
    return None


# ── football-data.org 헬퍼 ────────────────────────

FD_BASE = "https://api.football-data.org/v4"
FD_LEAGUES = {
    "PL":  "Premier League",
    "PD":  "La Liga",
    "SA":  "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
}


def _fd_get(endpoint: str) -> dict | None:
    """football-data.org GET (레이트 리밋 대응)."""
    if not FOOTBALL_DATA_TOKEN:
        return None
    import requests
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    try:
        resp = requests.get(f"{FD_BASE}{endpoint}", headers=headers, timeout=15)
        if resp.status_code == 429:
            log.info("  football-data.org 레이트 리밋 — 7초 대기")
            time.sleep(7)
            resp = requests.get(f"{FD_BASE}{endpoint}", headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        log.warning(f"  football-data.org {endpoint}: HTTP {resp.status_code}")
        return None
    except Exception as e:
        log.warning(f"  football-data.org {endpoint}: {e}")
        return None
