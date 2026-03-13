"""La Paz Agent 2 — StatsBomb Open Data 수집기.

1순위 소스: 경기 결과, 이벤트, 라인업 수집.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_config import (  # noqa: E402
    get_agent_logger,
    sb_upsert,
    sb_insert,
    sb_select,
)

from ._common import (
    _safe,
    _resolve_team_id,
    _resolve_comp_id,
    _resolve_season_id,
    _resolve_player_id,
)

log = get_agent_logger("agent_2")


# ══════════════════════════════════════════════════
# 1순위: StatsBomb Open Data — 경기 결과
# ══════════════════════════════════════════════════

def collect_matches_statsbomb() -> int:
    """StatsBomb Open Data에서 경기 결과 수집."""
    log.info("[StatsBomb] 경기 수집 시작...")
    total = 0
    team_cache: dict = {}
    comp_cache: dict = {}
    season_cache: dict = {}

    try:
        from statsbombpy import sb
    except ImportError:
        log.warning("[StatsBomb] statsbombpy 미설치 — 건너뜀")
        return 0

    try:
        competitions = sb.competitions()
        if competitions is None or competitions.empty:
            return 0

        men_comps = competitions[competitions["competition_gender"] == "male"]

        for _, comp_row in men_comps.iterrows():
            sb_comp_id = comp_row["competition_id"]
            sb_season_id = comp_row["season_id"]
            comp_name = str(comp_row.get("competition_name", ""))
            season_name = str(comp_row.get("season_name", ""))

            source_id = f"statsbomb_{sb_comp_id}"
            comp_id = _resolve_comp_id(source_id, "statsbomb", comp_cache)
            season_id = (
                _resolve_season_id(comp_id, season_name, season_cache)
                if comp_id else None
            )

            try:
                matches = sb.matches(
                    competition_id=sb_comp_id, season_id=sb_season_id,
                )
                if matches is None or matches.empty:
                    continue

                rows = []
                for _, m in matches.iterrows():
                    match_id_sb = m.get("match_id")
                    home = str(_safe(m.get("home_team"), ""))
                    away = str(_safe(m.get("away_team"), ""))
                    match_date = _safe(m.get("match_date"))

                    # stadium: dict 또는 str 대응
                    stadium_raw = m.get("stadium")
                    stadium = (
                        stadium_raw.get("name")
                        if isinstance(stadium_raw, dict)
                        else _safe(stadium_raw)
                    )

                    # referee: dict 또는 str 대응
                    referee_raw = m.get("referee")
                    referee = (
                        referee_raw.get("name")
                        if isinstance(referee_raw, dict)
                        else _safe(referee_raw)
                    )

                    rows.append({
                        "source_id": f"statsbomb_{match_id_sb}",
                        "competition_id": comp_id,
                        "season_id": season_id,
                        "match_date": str(match_date)[:10] if match_date else None,
                        "matchday": _safe(m.get("match_week")),
                        "home_team_id": _resolve_team_id(home, team_cache),
                        "away_team_id": _resolve_team_id(away, team_cache),
                        "home_score": _safe(m.get("home_score")),
                        "away_score": _safe(m.get("away_score")),
                        "stadium": stadium,
                        "referee": referee,
                        "source": "statsbomb",
                        "meta": {
                            "sb_match_id": int(match_id_sb) if match_id_sb else None,
                            "competition": comp_name,
                            "season": season_name,
                        },
                    })

                count = sb_upsert("matches", rows, on_conflict="source,source_id")
                total += count
                log.info(f"  {comp_name} {season_name}: {count} matches")

            except Exception as e:
                log.warning(f"  {comp_name} {season_name} 경기 수집 실패: {e}")

    except Exception as e:
        log.warning(f"[StatsBomb] 경기 수집 오류: {e}")

    log.info(f"[StatsBomb] 경기 총 {total}건 수집")
    return total


# ══════════════════════════════════════════════════
# 1순위: StatsBomb Open Data — 이벤트 + 라인업
# ══════════════════════════════════════════════════

def collect_events_statsbomb() -> int:
    """StatsBomb Open Data에서 이벤트 + 라인업 수집."""
    log.info("[StatsBomb] 이벤트/라인업 수집 시작...")
    total_events = 0
    total_lineups = 0

    try:
        from statsbombpy import sb
    except ImportError:
        log.warning("[StatsBomb] statsbombpy 미설치 — 건너뜀")
        return 0

    team_cache: dict = {}
    player_cache: dict = {}

    try:
        competitions = sb.competitions()
        if competitions is None or competitions.empty:
            return 0

        men_comps = competitions[competitions["competition_gender"] == "male"]

        # 주요 대회만 이벤트 수집
        target = men_comps[
            men_comps["competition_name"].isin([
                "Premier League", "La Liga", "Serie A",
                "Bundesliga", "Ligue 1",
                "Champions League", "FIFA World Cup", "UEFA Euro",
            ])
        ]

        for _, comp_row in target.iterrows():
            sb_comp_id = comp_row["competition_id"]
            sb_season_id = comp_row["season_id"]
            comp_name = comp_row.get("competition_name", "")
            season_name = comp_row.get("season_name", "")

            try:
                matches_sb = sb.matches(
                    competition_id=sb_comp_id, season_id=sb_season_id,
                )
                if matches_sb is None or matches_sb.empty:
                    continue

                # 시즌당 최대 20경기
                for _, m in matches_sb.head(20).iterrows():
                    match_id_sb = m["match_id"]

                    # DB의 match UUID 조회
                    db_matches = sb_select("matches", filters={
                        "source_id": f"statsbomb_{match_id_sb}",
                        "source": "statsbomb",
                    })
                    match_uuid = db_matches[0]["id"] if db_matches else None

                    # ── 이벤트 ──
                    try:
                        events = sb.events(match_id=match_id_sb)
                        if events is not None and not events.empty:
                            event_rows = []
                            for _, ev in events.iterrows():
                                loc = ev.get("location")
                                x_s = loc[0] if isinstance(loc, list) and len(loc) >= 2 else None
                                y_s = loc[1] if isinstance(loc, list) and len(loc) >= 2 else None

                                ev_type = ev.get("type")
                                type_str = (
                                    ev_type.get("name")
                                    if isinstance(ev_type, dict)
                                    else str(_safe(ev_type, "unknown"))
                                )

                                event_rows.append({
                                    "match_id": match_uuid,
                                    "source_id": str(_safe(ev.get("id"), "")),
                                    "minute": _safe(ev.get("minute")),
                                    "second": _safe(ev.get("second")),
                                    "type": type_str,
                                    "player_name": _safe(ev.get("player")),
                                    "team_name": _safe(ev.get("team")),
                                    "outcome": None,
                                    "x_start": x_s,
                                    "y_start": y_s,
                                    "meta": {
                                        "sb_match_id": int(match_id_sb),
                                        "possession_team": _safe(ev.get("possession_team")),
                                        "play_pattern": _safe(ev.get("play_pattern")),
                                    },
                                })

                            count = sb_insert("match_events", event_rows)
                            total_events += count
                    except Exception:
                        pass

                    # ── 라인업 ──
                    try:
                        lineups = sb.lineups(match_id=match_id_sb)
                        if lineups and match_uuid:
                            for team_name, lineup_df in lineups.items():
                                if lineup_df is None or lineup_df.empty:
                                    continue
                                team_id = _resolve_team_id(str(team_name), team_cache)

                                lineup_rows = []
                                for _, p in lineup_df.iterrows():
                                    player_name = _safe(p.get("player_name"), "")
                                    player_id = _resolve_player_id(player_name, player_cache)

                                    positions = p.get("positions")
                                    position = None
                                    if isinstance(positions, list) and positions:
                                        first = positions[0]
                                        position = (
                                            first.get("position")
                                            if isinstance(first, dict)
                                            else str(first)
                                        )

                                    lineup_rows.append({
                                        "match_id": match_uuid,
                                        "team_id": team_id,
                                        "player_id": player_id,
                                        "position": position,
                                        "jersey_number": _safe(p.get("jersey_number")),
                                        "meta": {"player_name": player_name},
                                    })

                                if lineup_rows:
                                    count = sb_insert("lineups", lineup_rows)
                                    total_lineups += count
                    except Exception:
                        pass

                log.info(f"  {comp_name} {season_name}: events/lineups collected")

            except Exception as e:
                log.warning(f"  StatsBomb {comp_name} {season_name}: {e}")

    except Exception as e:
        log.warning(f"[StatsBomb] 이벤트 수집 오류: {e}")

    log.info(f"[StatsBomb] 이벤트 {total_events}건, 라인업 {total_lineups}건 수집")
    return total_events + total_lineups
