"""La Paz Agent 2 — Match & Performance 수집 함수 모음.

8개 수집 함수를 agent_2_match.py에서 분리.

소스 우선순위:
  1순위: StatsBomb Open Data (statsbombpy)
  2순위: football-data.org API (10req/min)
  3순위: Understat (understatapi) — xG 보강
"""

from __future__ import annotations

import time
from typing import Any

from shared_config import (
    get_agent_logger,
    sb_upsert,
    sb_insert,
    sb_select,
    FOOTBALL_DATA_TOKEN,
)

log = get_agent_logger("agent_2_collectors")


# ── 공통 유틸 ─────────────────────────────────────

FD_BASE = "https://api.football-data.org/v4"
FD_LEAGUES = {
    "PL":  {"name": "Premier League", "country": "England"},
    "PD":  {"name": "La Liga",        "country": "Spain"},
    "SA":  {"name": "Serie A",        "country": "Italy"},
    "BL1": {"name": "Bundesliga",     "country": "Germany"},
    "FL1": {"name": "Ligue 1",        "country": "France"},
}

# football-data.org 추가 대회 (CL, ELC 등)
FD_EXTRA_COMPS = {
    "CL":  {"name": "Champions League", "country": "Europe"},
    "EC":  {"name": "European Championship", "country": "Europe"},
}


def _safe_str(val: Any) -> str | None:
    """NaN-safe 문자열 변환."""
    if val is None:
        return None
    try:
        import pandas as pd
        if isinstance(val, float) and pd.isna(val):
            return None
    except ImportError:
        if isinstance(val, float) and val != val:
            return None
    s = str(val).strip()
    return s if s else None


def _fd_get(endpoint: str) -> dict | None:
    """football-data.org GET (레이트 리밋 10req/min 대응)."""
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


def _resolve_team_id(team_name: str, country: str = "") -> str | None:
    """팀 이름으로 DB에서 team_id 조회."""
    if not team_name:
        return None
    teams = sb_select("teams", columns="id,canonical", limit=5000)
    for t in teams:
        if t["canonical"] == team_name or t.get("name") == team_name:
            return t["id"]
    return None


def _resolve_comp_and_season(league_code: str) -> tuple[str | None, str | None]:
    """football-data 리그 코드로 competition_id, season_id 조회."""
    info = FD_LEAGUES.get(league_code) or FD_EXTRA_COMPS.get(league_code)
    if not info:
        return None, None

    comps = sb_select("competitions", filters={"source": "football-data"}, limit=1000)
    comp_id = None
    for c in comps:
        if c.get("source_id") == f"fd_{league_code}":
            comp_id = c["id"]
            break
    if not comp_id:
        # statsbomb 소스에서도 탐색
        all_comps = sb_select("competitions", limit=1000)
        for c in all_comps:
            if info["name"].lower() in (c.get("name") or "").lower():
                comp_id = c["id"]
                break

    if not comp_id:
        return None, None

    seasons = sb_select("seasons", filters={"competition_id": comp_id}, limit=100)
    current = [s for s in seasons if s.get("is_current")]
    season_id = current[0]["id"] if current else (seasons[0]["id"] if seasons else None)

    return comp_id, season_id


# ══════════════════════════════════════════════════
# 1순위: StatsBomb Open Data — 경기 결과
# ══════════════════════════════════════════════════

def collect_matches_statsbomb() -> int:
    """StatsBomb Open Data에서 경기 결과 수집 → matches 테이블.

    Returns:
        저장된 경기 수.
    """
    log.info("[StatsBomb] 경기 결과 수집 시작...")
    try:
        from statsbombpy import sb
    except ImportError:
        log.warning("[StatsBomb] statsbombpy 미설치 — 건너뜀")
        return 0

    total = 0
    try:
        competitions = sb.competitions()
        if competitions is None or competitions.empty:
            return 0

        men_comps = competitions[competitions["competition_gender"] == "male"]
        teams_cache = {t["canonical"]: t["id"] for t in sb_select("teams", limit=5000)}

        for _, comp_row in men_comps.iterrows():
            sb_comp_id = comp_row.get("competition_id")
            sb_season_id = comp_row.get("season_id")
            comp_name = str(comp_row.get("competition_name", ""))
            country = str(comp_row.get("country_name", ""))

            # DB에서 competition_id/season_id 조회
            comps = sb_select("competitions", filters={"source_id": f"statsbomb_{sb_comp_id}", "source": "statsbomb"})
            if not comps:
                continue
            comp_uuid = comps[0]["id"]

            season_name = str(comp_row.get("season_name", ""))
            seasons = sb_select("seasons", filters={"competition_id": comp_uuid, "year": season_name})
            season_uuid = seasons[0]["id"] if seasons else None

            try:
                matches = sb.matches(competition_id=sb_comp_id, season_id=sb_season_id)
                if matches is None or matches.empty:
                    continue
            except Exception as e:
                log.warning(f"  [StatsBomb] {comp_name} {season_name} 매치 로드 실패: {e}")
                continue

            rows = []
            for _, m in matches.iterrows():
                home_name = _safe_str(m.get("home_team"))
                away_name = _safe_str(m.get("away_team"))
                home_id = teams_cache.get(home_name)
                away_id = teams_cache.get(away_name)

                match_date = _safe_str(m.get("match_date"))
                h_score = m.get("home_score")
                a_score = m.get("away_score")
                match_id = m.get("match_id")

                if not match_id:
                    continue

                rows.append({
                    "source_id": f"sb_{match_id}",
                    "competition_id": comp_uuid,
                    "season_id": season_uuid,
                    "match_date": match_date,
                    "matchday": int(m["match_week"]) if "match_week" in m and m.get("match_week") else None,
                    "home_team_id": home_id,
                    "away_team_id": away_id,
                    "home_score": int(h_score) if h_score is not None else None,
                    "away_score": int(a_score) if a_score is not None else None,
                    "stadium": _safe_str(m.get("stadium", {}).get("name")) if isinstance(m.get("stadium"), dict) else _safe_str(m.get("stadium")),
                    "referee": _safe_str(m.get("referee")),
                    "source": "statsbomb",
                })

            if rows:
                count = sb_upsert("matches", rows, on_conflict="source,source_id")
                total += count
                log.info(f"  [StatsBomb] {comp_name} {season_name}: {count} matches")

    except Exception as e:
        log.warning(f"[StatsBomb] 경기 수집 오류: {e}")

    log.info(f"[StatsBomb] 총 {total} matches 저장")
    return total


# ══════════════════════════════════════════════════
# 1순위: StatsBomb Open Data — 이벤트 + 라인업
# ══════════════════════════════════════════════════

def collect_events_statsbomb() -> int:
    """StatsBomb 이벤트(골, 카드 등) + 라인업 수집.

    Returns:
        저장된 이벤트 수.
    """
    log.info("[StatsBomb] 이벤트 수집 시작...")
    try:
        from statsbombpy import sb
    except ImportError:
        log.warning("[StatsBomb] statsbombpy 미설치 — 건너뜀")
        return 0

    total = 0
    try:
        # DB에서 statsbomb 소스 매치 조회
        matches = sb_select("matches", filters={"source": "statsbomb"}, limit=0)
        log.info(f"  StatsBomb 매치 {len(matches)}건에서 이벤트 수집")

        for m in matches:
            source_id = m.get("source_id", "")
            if not source_id.startswith("sb_"):
                continue
            sb_match_id = int(source_id.replace("sb_", ""))
            match_uuid = m["id"]

            # 이벤트
            try:
                events = sb.events(match_id=sb_match_id)
                if events is not None and not events.empty:
                    event_rows = []
                    for _, e in events.iterrows():
                        etype = _safe_str(e.get("type"))
                        if not etype:
                            continue
                        # 주요 이벤트만 저장 (Shot, Goal, Card 등)
                        if etype not in ("Shot", "Goal", "Own Goal", "Bad Behaviour",
                                         "Foul Committed", "Pass", "Dribble", "Interception",
                                         "Tackle", "Clearance", "Block"):
                            continue

                        loc = e.get("location")
                        x_start = loc[0] if isinstance(loc, (list, tuple)) and len(loc) >= 2 else None
                        y_start = loc[1] if isinstance(loc, (list, tuple)) and len(loc) >= 2 else None

                        # outcome 처리
                        outcome_val = e.get("shot_outcome") or e.get("pass_outcome") or e.get("dribble_outcome")
                        if isinstance(outcome_val, dict):
                            outcome_val = outcome_val.get("name")

                        event_rows.append({
                            "match_id": match_uuid,
                            "source_id": _safe_str(e.get("id")),
                            "minute": int(e["minute"]) if e.get("minute") is not None else None,
                            "second": int(e["second"]) if e.get("second") is not None else None,
                            "type": etype,
                            "player_name": _safe_str(e.get("player")),
                            "team_name": _safe_str(e.get("team")),
                            "outcome": _safe_str(outcome_val),
                            "x_start": x_start,
                            "y_start": y_start,
                        })

                    if event_rows:
                        count = sb_insert("match_events", event_rows)
                        total += count

            except Exception as e_err:
                log.debug(f"  이벤트 수집 실패 (match {sb_match_id}): {e_err}")

            # 라인업
            try:
                lineups = sb.lineups(match_id=sb_match_id)
                if lineups:
                    for team_name, lineup_df in lineups.items():
                        if lineup_df is None or lineup_df.empty:
                            continue
                        lineup_rows = []
                        for _, p in lineup_df.iterrows():
                            player_name = _safe_str(p.get("player_name"))
                            if not player_name:
                                continue
                            lineup_rows.append({
                                "match_id": match_uuid,
                                "player_id": None,  # 이후 매핑
                                "position": _safe_str(p.get("position")),
                                "is_starter": True,
                                "jersey_number": int(p["jersey_number"]) if p.get("jersey_number") else None,
                                "meta": {"player_name": player_name, "team": str(team_name)},
                            })
                        if lineup_rows:
                            sb_insert("lineups", lineup_rows)
            except Exception:
                pass

    except Exception as e:
        log.warning(f"[StatsBomb] 이벤트 수집 오류: {e}")

    log.info(f"[StatsBomb] 총 {total} events 저장")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 최근 경기
# ══════════════════════════════════════════════════

def collect_matches_footballdata() -> int:
    """football-data.org에서 5대 리그 최근 경기 수집 → matches 테이블.

    Returns:
        저장된 경기 수.
    """
    log.info("[football-data.org] 경기 수집 시작...")
    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return 0

    total = 0
    teams_cache = {t["canonical"]: t["id"] for t in sb_select("teams", limit=5000)}
    # name → id 도 추가
    for t in sb_select("teams", limit=5000):
        teams_cache[t["name"]] = t["id"]

    for code, info in FD_LEAGUES.items():
        try:
            comp_id, season_id = _resolve_comp_and_season(code)
            if not comp_id:
                continue

            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/matches?status=FINISHED&limit=100")
            if not data or "matches" not in data:
                continue

            rows = []
            for m in data["matches"]:
                fd_id = m.get("id")
                if not fd_id:
                    continue

                home_name = (m.get("homeTeam") or {}).get("shortName") or (m.get("homeTeam") or {}).get("name", "")
                away_name = (m.get("awayTeam") or {}).get("shortName") or (m.get("awayTeam") or {}).get("name", "")
                score = m.get("score", {}).get("fullTime", {})

                rows.append({
                    "source_id": f"fd_{fd_id}",
                    "competition_id": comp_id,
                    "season_id": season_id,
                    "match_date": (m.get("utcDate") or "")[:10] or None,
                    "matchday": m.get("matchday"),
                    "home_team_id": teams_cache.get(home_name),
                    "away_team_id": teams_cache.get(away_name),
                    "home_score": score.get("home"),
                    "away_score": score.get("away"),
                    "stadium": (m.get("venue") or ""),
                    "referee": (m.get("referees") or [{}])[0].get("name") if m.get("referees") else None,
                    "source": "football-data",
                    "meta": {
                        "status": m.get("status"),
                        "stage": m.get("stage"),
                        "home_team_name": home_name,
                        "away_team_name": away_name,
                    },
                })

            if rows:
                count = sb_upsert("matches", rows, on_conflict="source,source_id")
                total += count
                log.info(f"  {info['name']}: {count} matches")

        except Exception as e:
            log.warning(f"  [football-data.org] {info['name']} 매치: {e}")

    log.info(f"[football-data.org] 총 {total} matches 저장")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 리그 순위표
# ══════════════════════════════════════════════════

def collect_standings_footballdata() -> int:
    """football-data.org 리그 순위 → team_season_stats 테이블.

    Returns:
        저장된 행 수.
    """
    log.info("[football-data.org] 순위표 수집 시작...")
    if not FOOTBALL_DATA_TOKEN:
        return 0

    total = 0
    teams_cache = {}
    for t in sb_select("teams", limit=5000):
        teams_cache[t["canonical"]] = t["id"]
        teams_cache[t["name"]] = t["id"]

    for code, info in FD_LEAGUES.items():
        try:
            comp_id, season_id = _resolve_comp_and_season(code)
            if not comp_id or not season_id:
                continue

            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/standings")
            if not data or "standings" not in data:
                continue

            standings = data["standings"]
            total_standing = [s for s in standings if s.get("type") == "TOTAL"]
            if not total_standing:
                continue

            rows = []
            for entry in total_standing[0].get("table", []):
                team_info = entry.get("team", {})
                team_name = team_info.get("shortName") or team_info.get("name", "")
                team_id = teams_cache.get(team_name)

                if not team_id:
                    # 이름으로 재검색
                    for t in sb_select("teams", limit=5000):
                        if team_name in (t.get("aliases") or []) or team_name == t.get("name"):
                            team_id = t["id"]
                            break

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
                    "meta": {
                        "league": info["name"],
                        "season": data.get("season", {}).get("startDate", "")[:4] + "-" if data.get("season") else "",
                        "team_name": team_name,
                    },
                })

            if rows:
                # meta.season 보정
                for r in rows:
                    if r["meta"]["season"].endswith("-"):
                        sy = r["meta"]["season"][:-1]
                        r["meta"]["season"] = f"{sy}-{int(sy)+1}" if sy.isdigit() else ""

                count = sb_upsert("team_season_stats", rows, on_conflict="team_id,season_id,competition_id")
                total += count
                log.info(f"  {info['name']}: {count} standings")

        except Exception as e:
            log.warning(f"  [football-data.org] {info['name']} 순위표: {e}")

    log.info(f"[football-data.org] 총 {total} standings 저장")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 스쿼드 (선수 확대)
# ══════════════════════════════════════════════════

def collect_squads_footballdata() -> int:
    """football-data.org 팀별 스쿼드 → players, player_season_stats 테이블.

    Returns:
        저장된 선수 수.
    """
    log.info("[football-data.org] 스쿼드 수집 시작...")
    if not FOOTBALL_DATA_TOKEN:
        return 0

    total = 0
    for code, info in FD_LEAGUES.items():
        try:
            comp_id, season_id = _resolve_comp_and_season(code)

            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/teams")
            if not data or "teams" not in data:
                continue

            for team in data["teams"]:
                team_name = (team.get("shortName") or team.get("name", "")).strip()
                squad = team.get("squad") or []
                if not squad:
                    continue

                player_rows = []
                for p in squad:
                    pname = (p.get("name") or "").strip()
                    if not pname:
                        continue
                    player_rows.append({
                        "name": pname,
                        "full_name": pname,
                        "nationality": p.get("nationality"),
                        "birth_date": p.get("dateOfBirth"),
                        "position": p.get("position"),
                        "source": "football-data",
                        "meta": {"team": team_name, "fd_id": p.get("id")},
                    })

                if player_rows:
                    count = sb_insert("players", player_rows)
                    total += count

        except Exception as e:
            log.warning(f"  [football-data.org] {info['name']} 스쿼드: {e}")

    log.info(f"[football-data.org] 총 {total} players 저장")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 경기 상세 (골/카드 이벤트)
# ══════════════════════════════════════════════════

def collect_matches_detail_footballdata() -> int:
    """football-data.org 경기 상세 → match_events 테이블 (골, 카드).

    Returns:
        저장된 이벤트 수.
    """
    log.info("[football-data.org] 경기 상세 수집 시작...")
    if not FOOTBALL_DATA_TOKEN:
        return 0

    total = 0
    for code, info in FD_LEAGUES.items():
        try:
            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/matches?status=FINISHED&limit=50")
            if not data or "matches" not in data:
                continue

            # DB에서 해당 매치의 uuid 매핑
            db_matches = sb_select("matches", filters={"source": "football-data"}, limit=0)
            match_id_map = {m["source_id"]: m["id"] for m in db_matches}

            for m in data["matches"]:
                fd_id = m.get("id")
                source_key = f"fd_{fd_id}"
                match_uuid = match_id_map.get(source_key)
                if not match_uuid:
                    continue

                # 골 이벤트
                goals = m.get("goals") or []
                for g in goals:
                    scorer = g.get("scorer", {})
                    assist = g.get("assist", {})
                    sb_insert("match_events", [{
                        "match_id": match_uuid,
                        "source_id": f"fd_goal_{fd_id}_{g.get('minute', 0)}",
                        "minute": g.get("minute"),
                        "type": "Goal",
                        "player_name": scorer.get("name") if scorer else None,
                        "team_name": (g.get("team") or {}).get("name"),
                        "outcome": "Goal",
                        "meta": {
                            "assist": assist.get("name") if assist else None,
                            "type": g.get("type"),  # REGULAR, OWN_GOAL, PENALTY
                        },
                    }])
                    total += 1

                # 카드 이벤트 (bookings)
                bookings = m.get("bookings") or []
                for b in bookings:
                    player = b.get("player", {})
                    card_type = "Yellow Card" if b.get("card") == "YELLOW" else "Red Card"
                    sb_insert("match_events", [{
                        "match_id": match_uuid,
                        "source_id": f"fd_card_{fd_id}_{b.get('minute', 0)}",
                        "minute": b.get("minute"),
                        "type": card_type,
                        "player_name": player.get("name") if player else None,
                        "team_name": (b.get("team") or {}).get("name"),
                        "outcome": card_type,
                    }])
                    total += 1

        except Exception as e:
            log.warning(f"  [football-data.org] {info['name']} 상세: {e}")

    log.info(f"[football-data.org] 총 {total} events 저장")
    return total


# ══════════════════════════════════════════════════
# 2순위: football-data.org — 전체 대회 득점 순위
# ══════════════════════════════════════════════════

def collect_top_scorers_all_leagues() -> int:
    """football-data.org 5대 리그 + CL 득점 순위 → player_season_stats.

    Returns:
        저장된 행 수.
    """
    log.info("[football-data.org] 득점 순위 수집 시작...")
    if not FOOTBALL_DATA_TOKEN:
        return 0

    total = 0
    all_leagues = {**FD_LEAGUES, **FD_EXTRA_COMPS}

    # 선수 이름 → id 캐시
    players_cache: dict[str, str] = {}
    for p in sb_select("players", columns="id,name", limit=0):
        players_cache[p["name"]] = p["id"]

    teams_cache: dict[str, str] = {}
    for t in sb_select("teams", limit=5000):
        teams_cache[t["canonical"]] = t["id"]
        teams_cache[t["name"]] = t["id"]

    for code, info in all_leagues.items():
        try:
            comp_id, season_id = _resolve_comp_and_season(code)

            time.sleep(7)
            data = _fd_get(f"/competitions/{code}/scorers?limit=30")
            if not data or "scorers" not in data:
                continue

            rows = []
            for s in data["scorers"]:
                player_info = s.get("player", {})
                team_info = s.get("team", {})
                player_name = player_info.get("name", "")
                team_name = team_info.get("shortName") or team_info.get("name", "")

                player_id = players_cache.get(player_name)
                team_id = teams_cache.get(team_name)

                rows.append({
                    "player_id": player_id,
                    "season_id": season_id,
                    "team_id": team_id,
                    "competition_id": comp_id,
                    "appearances": s.get("playedMatches", 0),
                    "goals": s.get("goals", 0),
                    "assists": s.get("assists", 0),
                    "source": "football-data",
                    "meta": {
                        "player_name": player_name,
                        "team_name": team_name,
                        "season": data.get("season", {}).get("startDate", "")[:4] + "-" if data.get("season") else "",
                        "league": info["name"],
                        "penalties": s.get("penalties"),
                    },
                })

            if rows:
                # meta.season 보정
                for r in rows:
                    if r["meta"]["season"].endswith("-"):
                        sy = r["meta"]["season"][:-1]
                        r["meta"]["season"] = f"{sy}-{int(sy)+1}" if sy.isdigit() else ""

                count = sb_insert("player_season_stats", rows)
                total += count
                log.info(f"  {info['name']}: {count} scorers")

        except Exception as e:
            log.warning(f"  [football-data.org] {info['name']} 득점 순위: {e}")

    log.info(f"[football-data.org] 총 {total} scorer stats 저장")
    return total


# ══════════════════════════════════════════════════
# 3순위: Understat — xG 보강
# ══════════════════════════════════════════════════

def collect_understat_xg() -> int:
    """Understat에서 팀/선수 xG 데이터 보강 → team_season_stats, player_season_stats.

    Returns:
        업데이트된 행 수.
    """
    log.info("[Understat] xG 수집 시작...")
    try:
        from understatapi import UnderstatClient
    except ImportError:
        log.warning("[Understat] understatapi 미설치 — 건너뜀")
        return 0

    total = 0
    UNDERSTAT_LEAGUES = {
        "EPL": "Premier League",
        "La_liga": "La Liga",
        "Serie_A": "Serie A",
        "Bundesliga": "Bundesliga",
        "Ligue_1": "Ligue 1",
    }

    teams_cache: dict[str, str] = {}
    for t in sb_select("teams", limit=5000):
        teams_cache[t["canonical"]] = t["id"]
        teams_cache[t["name"]] = t["id"]

    try:
        understat = UnderstatClient()

        for u_league, league_name in UNDERSTAT_LEAGUES.items():
            try:
                # 팀 xG 데이터
                teams_data = understat.league(league=u_league).get_team_data(season="2024")
                if not teams_data:
                    continue

                for team_key, team_data in teams_data.items():
                    team_title = team_data.get("title", "")
                    team_id = teams_cache.get(team_title)
                    if not team_id:
                        continue

                    history = team_data.get("history", [])
                    if not history:
                        continue

                    # 시즌 집계
                    xg_for = sum(float(g.get("xG", 0)) for g in history)
                    xg_against = sum(float(g.get("xGA", 0)) for g in history)

                    # team_season_stats에 xg 업데이트 (기존 행에 보강)
                    existing = sb_select("team_season_stats", filters={"team_id": team_id}, limit=10)
                    for row in existing:
                        if row.get("xg_for") is None:
                            try:
                                from shared_config import get_supabase
                                sb = get_supabase()
                                sb.table("team_season_stats").update({
                                    "xg_for": round(xg_for, 2),
                                    "xg_against": round(xg_against, 2),
                                }).eq("id", row["id"]).execute()
                                total += 1
                            except Exception:
                                pass

                log.info(f"  [Understat] {league_name}: xG 보강")

            except Exception as e:
                log.warning(f"  [Understat] {league_name}: {e}")

    except Exception as e:
        log.warning(f"[Understat] xG 수집 오류: {e}")

    log.info(f"[Understat] 총 {total} rows xG 보강")
    return total
