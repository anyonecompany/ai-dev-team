"""La Paz Agent 2 — football-data.org 기본 수집기.

2순위 소스: 최근 경기, 리그 순위, 득점 순위, 스쿼드.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_config import (  # noqa: E402
    get_agent_logger,
    get_supabase,
    sb_upsert,
    sb_insert,
    FOOTBALL_DATA_TOKEN,
)

from ._common import (
    _resolve_team_id,
    _resolve_comp_id,
    _resolve_season_id,
    _resolve_player_id,
    FD_LEAGUES,
    _fd_get,
)

log = get_agent_logger("agent_2")


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 최근 경기
# ══════════════════════════════════════════════════

def collect_matches_footballdata() -> int:
    """football-data.org에서 최근 완료 경기 수집."""
    log.info("[football-data.org] 경기 수집 시작...")

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    total = 0
    team_cache: dict = {}
    comp_cache: dict = {}
    season_cache: dict = {}

    for code, name in FD_LEAGUES.items():
        try:
            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/matches?status=FINISHED&limit=100")
            if not data or "matches" not in data:
                continue

            source_id = f"fd_{code}"
            comp_id = _resolve_comp_id(source_id, "football-data", comp_cache)

            rows = []
            for m in data["matches"]:
                fd_id = m.get("id")
                home_info = m.get("homeTeam") or {}
                away_info = m.get("awayTeam") or {}
                home_name = home_info.get("shortName") or home_info.get("name", "")
                away_name = away_info.get("shortName") or away_info.get("name", "")
                score = (m.get("score") or {}).get("fullTime") or {}
                utc_date = m.get("utcDate", "")
                match_date = utc_date[:10] if utc_date else None

                season_data = m.get("season") or {}
                start_date = season_data.get("startDate", "")
                season_year = ""
                if start_date:
                    sy = start_date[:4]
                    season_year = f"{sy}-{int(sy) + 1}"

                season_id = (
                    _resolve_season_id(comp_id, season_year, season_cache)
                    if comp_id and season_year else None
                )

                referees = m.get("referees") or []
                referee_name = referees[0].get("name") if referees else None

                rows.append({
                    "source_id": f"fd_{fd_id}",
                    "competition_id": comp_id,
                    "season_id": season_id,
                    "match_date": match_date,
                    "matchday": m.get("matchday"),
                    "home_team_id": _resolve_team_id(home_name, team_cache),
                    "away_team_id": _resolve_team_id(away_name, team_cache),
                    "home_score": score.get("home"),
                    "away_score": score.get("away"),
                    "referee": referee_name,
                    "source": "football-data",
                    "meta": {
                        "fd_id": fd_id,
                        "competition": code,
                        "season": season_year,
                    },
                })

            if rows:
                count = sb_upsert("matches", rows, on_conflict="source,source_id")
                total += count
                log.info(f"  {name}: {count} matches")

        except Exception as e:
            log.warning(f"  [football-data.org] {name}: {e}")

    log.info(f"[football-data.org] 경기 총 {total}건 수집")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 리그 순위표
# ══════════════════════════════════════════════════

def collect_standings_footballdata() -> int:
    """football-data.org에서 리그 순위표 수집 -> team_season_stats."""
    log.info("[football-data.org] 순위표 수집 시작...")

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    total = 0
    team_cache: dict = {}
    comp_cache: dict = {}
    season_cache: dict = {}

    for code, name in FD_LEAGUES.items():
        try:
            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/standings")
            if not data or "standings" not in data:
                continue

            source_id = f"fd_{code}"
            comp_id = _resolve_comp_id(source_id, "football-data", comp_cache)

            season_data = data.get("season") or {}
            start_date = season_data.get("startDate", "")
            season_year = ""
            if start_date:
                sy = start_date[:4]
                season_year = f"{sy}-{int(sy) + 1}"
            season_id = (
                _resolve_season_id(comp_id, season_year, season_cache)
                if comp_id and season_year else None
            )

            for standing in data["standings"]:
                if standing.get("type") != "TOTAL":
                    continue

                rows = []
                for entry in standing.get("table", []):
                    team_info = entry.get("team") or {}
                    team_name = team_info.get("shortName") or team_info.get("name", "")
                    team_id = _resolve_team_id(team_name, team_cache)

                    rows.append({
                        "team_id": team_id,
                        "season_id": season_id,
                        "competition_id": comp_id,
                        "position": entry.get("position"),
                        "played": entry.get("playedGames", 0),
                        "won": entry.get("won", 0),
                        "draw": entry.get("draw", 0),
                        "lost": entry.get("lost", 0),
                        "goals_for": entry.get("goalsFor", 0),
                        "goals_against": entry.get("goalsAgainst", 0),
                        "goal_diff": entry.get("goalDifference", 0),
                        "points": entry.get("points", 0),
                        "source": "football-data",
                        "meta": {"competition": code, "season": season_year},
                    })

                if rows:
                    count = sb_insert("team_season_stats", rows)
                    total += count
                    log.info(f"  {name}: {count} team standings")

        except Exception as e:
            log.warning(f"  [football-data.org] {name} 순위표: {e}")

    log.info(f"[football-data.org] 순위표 총 {total}건 수집")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 득점 순위 (선수 시즌 스탯)
# ══════════════════════════════════════════════════

def collect_scorers_footballdata() -> int:
    """football-data.org scorers 엔드포인트에서 선수 시즌 스탯 수집."""
    log.info("[football-data.org] 득점 순위(scorers) 수집 시작...")

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    # 기존 football-data 소스 데이터 삭제 후 재삽입
    try:
        sb = get_supabase()
        sb.table("player_season_stats").delete().eq("source", "football-data").execute()
        log.info("  기존 football-data scorers 삭제 완료")
    except Exception as e:
        log.warning(f"  기존 데이터 삭제 실패 (계속 진행): {e}")

    total = 0
    team_cache: dict = {}
    comp_cache: dict = {}
    season_cache: dict = {}
    player_cache: dict = {}

    for code, name in FD_LEAGUES.items():
        try:
            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/scorers?limit=100")
            if not data or "scorers" not in data:
                log.warning(f"  {name}: scorers 데이터 없음")
                continue

            source_id = f"fd_{code}"
            comp_id = _resolve_comp_id(source_id, "football-data", comp_cache)

            season_data = data.get("season") or {}
            start_date = season_data.get("startDate", "")
            season_year = ""
            if start_date:
                sy = start_date[:4]
                season_year = f"{sy}-{int(sy) + 1}"
            season_id = (
                _resolve_season_id(comp_id, season_year, season_cache)
                if comp_id and season_year else None
            )

            rows = []
            for scorer in data["scorers"]:
                player_info = scorer.get("player") or {}
                team_info = scorer.get("team") or {}

                player_name = player_info.get("name", "")
                if not player_name:
                    continue

                team_name = (
                    team_info.get("shortName")
                    or team_info.get("name", "")
                )

                player_id = _resolve_player_id(player_name, player_cache)
                team_id = _resolve_team_id(team_name, team_cache)

                rows.append({
                    "player_id": player_id,
                    "season_id": season_id,
                    "team_id": team_id,
                    "competition_id": comp_id,
                    "appearances": scorer.get("playedMatches"),
                    "minutes": None,
                    "goals": scorer.get("goals"),
                    "assists": scorer.get("assists"),
                    "xg": None,
                    "xa": None,
                    "source": "football-data",
                    "meta": {
                        "fd_player_id": player_info.get("id"),
                        "player_name": player_name,
                        "team_name": team_name,
                        "competition": code,
                        "season": season_year,
                        "penalties": scorer.get("penalties"),
                    },
                })

            if rows:
                count = sb_insert("player_season_stats", rows)
                total += count
                log.info(f"  {name}: {count} player season stats")

        except Exception as e:
            log.warning(f"  [football-data.org] {name} scorers: {e}")

    log.info(f"[football-data.org] 득점 순위 총 {total}건 수집")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 스쿼드 (선수 확대 수집)
# ══════════════════════════════════════════════════

def collect_squads_footballdata() -> int:
    """football-data.org /v4/competitions/{code}/teams 에서 전체 스쿼드 수집."""
    log.info("[football-data.org] 스쿼드 수집 시작...")

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    # 기존 football-data 소스 선수 삭제 후 재삽입
    try:
        sb = get_supabase()
        sb.table("players").delete().eq("source", "football-data").execute()
        log.info("  기존 football-data players 삭제 완료")
    except Exception as e:
        log.warning(f"  기존 데이터 삭제 실패 (계속 진행): {e}")

    total = 0

    for code, name in FD_LEAGUES.items():
        try:
            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/teams")
            if not data or "teams" not in data:
                log.warning(f"  {name}: teams 데이터 없음")
                continue

            rows: list[dict] = []
            for team in data["teams"]:
                team_name = (
                    team.get("shortName")
                    or team.get("name", "")
                )
                squad = team.get("squad") or []
                for player in squad:
                    p_name = player.get("name")
                    if not p_name:
                        continue

                    # position 매핑
                    fd_pos = player.get("position", "")
                    pos_map = {
                        "Goalkeeper": "Goalkeeper",
                        "Defence": "Defender",
                        "Midfield": "Midfielder",
                        "Offence": "Forward",
                    }
                    position = pos_map.get(fd_pos, fd_pos) or None

                    rows.append({
                        "name": p_name,
                        "full_name": p_name,
                        "nationality": player.get("nationality"),
                        "birth_date": player.get("dateOfBirth"),
                        "position": position,
                        "source": "football-data",
                        "meta": {
                            "fd_player_id": player.get("id"),
                            "team": team_name,
                            "competition": code,
                        },
                    })

            if rows:
                count = sb_insert("players", rows)
                total += count
                log.info(f"  {name}: {count} players ({len(rows)} in squad)")

        except Exception as e:
            log.warning(f"  [football-data.org] {name} squads: {e}")

    log.info(f"[football-data.org] 스쿼드 총 {total}명 수집")
    return total
