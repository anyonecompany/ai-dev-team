"""La Paz Agent 2 — football-data.org 상세 수집기.

현시즌 전체 경기 상세 + 전체 대회 득점 순위 수집.
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
# 2순위: football-data.org — 현시즌 전체 경기 상세
# ══════════════════════════════════════════════════

def collect_matches_detail_footballdata() -> int:
    """football-data.org 현시즌 전체 완료 경기 상세 수집."""
    log.info("[football-data.org] 현시즌 경기 상세 수집 시작...")

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    total_matches = 0
    total_events = 0
    team_cache: dict = {}
    comp_cache: dict = {}
    season_cache: dict = {}

    for code, name in FD_LEAGUES.items():
        try:
            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/matches?status=FINISHED")
            if not data or "matches" not in data:
                log.warning(f"  {name}: 경기 데이터 없음")
                continue

            source_id = f"fd_{code}"
            comp_id = _resolve_comp_id(source_id, "football-data", comp_cache)

            match_rows: list[dict] = []
            event_rows: list[dict] = []

            for m in data["matches"]:
                fd_id = m.get("id")
                home_info = m.get("homeTeam") or {}
                away_info = m.get("awayTeam") or {}
                home_name = home_info.get("shortName") or home_info.get("name", "")
                away_name = away_info.get("shortName") or away_info.get("name", "")

                score_obj = m.get("score") or {}
                full_time = score_obj.get("fullTime") or {}
                half_time = score_obj.get("halfTime") or {}

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
                referee_meta = [
                    {"name": r.get("name"), "type": r.get("type")}
                    for r in referees
                ] if referees else []

                home_tid = _resolve_team_id(home_name, team_cache)
                away_tid = _resolve_team_id(away_name, team_cache)
                match_source_id = f"fd_{fd_id}"

                match_rows.append({
                    "source_id": match_source_id,
                    "competition_id": comp_id,
                    "season_id": season_id,
                    "match_date": match_date,
                    "matchday": m.get("matchday"),
                    "home_team_id": home_tid,
                    "away_team_id": away_tid,
                    "home_score": full_time.get("home"),
                    "away_score": full_time.get("away"),
                    "referee": referee_name,
                    "source": "football-data",
                    "meta": {
                        "fd_id": fd_id,
                        "competition": code,
                        "season": season_year,
                        "half_time": {
                            "home": half_time.get("home"),
                            "away": half_time.get("away"),
                        },
                        "referees": referee_meta,
                        "stage": m.get("stage"),
                    },
                })

                # 골/카드 이벤트
                goals = m.get("goals") or []
                bookings = m.get("bookings") or []
                for g in goals:
                    scorer = g.get("scorer") or {}
                    assist = g.get("assist") or {}
                    event_rows.append({
                        "source_id": f"fd_goal_{fd_id}_{g.get('minute', 0)}_{scorer.get('name', '')}",
                        "minute": g.get("minute"),
                        "type": "Goal",
                        "player_name": scorer.get("name"),
                        "team_name": g.get("team", {}).get("name", ""),
                        "outcome": "Goal",
                        "meta": {
                            "scorer_id": scorer.get("id"),
                            "assist_name": assist.get("name"),
                            "assist_id": assist.get("id"),
                            "source_match_id": match_source_id,
                        },
                    })
                for b in bookings:
                    b_player = b.get("player") or {}
                    card_type = b.get("card", "YELLOW_CARD")
                    card_label = {
                        "YELLOW_CARD": "Yellow Card",
                        "YELLOW_RED": "Second Yellow",
                        "RED_CARD": "Red Card",
                    }.get(card_type, card_type)
                    event_rows.append({
                        "source_id": f"fd_card_{fd_id}_{b.get('minute', 0)}_{b_player.get('name', '')}",
                        "minute": b.get("minute"),
                        "type": card_label,
                        "player_name": b_player.get("name"),
                        "team_name": b.get("team", {}).get("name", ""),
                        "outcome": card_label,
                        "meta": {
                            "player_id": b_player.get("id"),
                            "source_match_id": match_source_id,
                        },
                    })

            # 경기 upsert
            if match_rows:
                count = sb_upsert("matches", match_rows, on_conflict="source,source_id")
                total_matches += count
                log.info(f"  {name}: {count} matches (상세)")

            if not event_rows:
                log.info(f"  {name}: 이벤트 0건 (무료 티어 — goals/bookings 미제공, StatsBomb 이벤트 활용)")
            else:
                log.info(f"  {name}: event_rows={len(event_rows)}건")

            # 이벤트 — match_id FK 연결 후 삽입
            if event_rows:
                sb = get_supabase()
                inserted = 0
                for ev in event_rows:
                    src_mid = ev.get("meta", {}).get("source_match_id")
                    if src_mid:
                        matches = sb.table("matches").select("id")\
                                    .eq("source_id", src_mid).limit(1).execute()
                        if matches.data:
                            ev["match_id"] = matches.data[0]["id"]
                    ev.pop("source_id", None)
                    try:
                        sb.table("match_events").insert(ev).execute()
                        inserted += 1
                    except Exception:
                        pass  # 중복 무시
                total_events += inserted
                log.info(f"  {name}: {inserted} events (골+카드)")

        except Exception as e:
            log.warning(f"  [football-data.org] {name} matches detail: {e}")

    log.info(f"[football-data.org] 경기 상세 총 {total_matches}건, 이벤트 {total_events}건")
    return total_matches


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 전체 대회 득점 순위
# ══════════════════════════════════════════════════

def collect_top_scorers_all_leagues() -> int:
    """5대 리그 + Champions League + EFL Championship 득점 순위 수집."""
    log.info("[football-data.org] 전체 대회 득점 순위 수집 시작...")

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    # 기존 football-data 소스 데이터 삭제 후 재삽입
    try:
        sb = get_supabase()
        sb.table("player_season_stats").delete().eq("source", "football-data").execute()
        log.info("  기존 football-data player_season_stats 삭제 완료")
    except Exception as e:
        log.warning(f"  기존 데이터 삭제 실패 (계속 진행): {e}")

    ALL_LEAGUES = {
        **FD_LEAGUES,
        "CL":  "Champions League",
        "ELC": "EFL Championship",
    }

    total = 0
    team_cache: dict = {}
    comp_cache: dict = {}
    season_cache: dict = {}
    player_cache: dict = {}

    for code, name in ALL_LEAGUES.items():
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

            rows: list[dict] = []
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

    log.info(f"[football-data.org] 전체 대회 득점 순위 총 {total}건 수집")
    return total
