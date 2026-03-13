#!/usr/bin/env python3
"""La Paz Agent 1: Structure Collector

소스 우선순위:
  1순위: StatsBomb Open Data (statsbombpy) — GitHub 오픈데이터, 차단 없음
  2순위: football-data.org API (무료, 10req/min)
  3순위: FBref (soccerdata) — fallback only, 403 가능성 높음

저장: competitions, seasons, teams, players,
      team_seasons
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_config import (
    get_agent_logger,
    publish_status,
    sb_upsert,
    sb_insert,
    sb_select,
    FOOTBALL_DATA_TOKEN,
)

log = get_agent_logger("agent_1")


# ── 공통 유틸 ─────────────────────────────────────

def _safe_str(val) -> str | None:
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


# ── football-data.org 헬퍼 ────────────────────────

FD_BASE = "https://api.football-data.org/v4"
FD_LEAGUES = {
    "PL":  {"name": "Premier League", "country": "England"},
    "PD":  {"name": "La Liga",        "country": "Spain"},
    "SA":  {"name": "Serie A",        "country": "Italy"},
    "BL1": {"name": "Bundesliga",     "country": "Germany"},
    "FL1": {"name": "Ligue 1",        "country": "France"},
}


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


# ══════════════════════════════════════════════════
# 1순위: StatsBomb Open Data
# ══════════════════════════════════════════════════

def collect_statsbomb() -> dict[str, dict]:
    """StatsBomb Open Data에서 대회/시즌/팀/선수 수집.

    Returns:
        {league_key: {"comp_id": uuid, "season_ids": {year: uuid}}}
    """
    log.info("[StatsBomb] 수집 시작...")
    comp_map: dict[str, dict] = {}

    try:
        from statsbombpy import sb
    except ImportError:
        log.warning("[StatsBomb] statsbombpy 미설치 — 건너뜀")
        return comp_map

    try:
        competitions = sb.competitions()
        if competitions is None or competitions.empty:
            log.warning("[StatsBomb] 대회 데이터 없음")
            return comp_map

        men_comps = competitions[competitions["competition_gender"] == "male"]
        seen_comps: dict[str, str] = {}  # competition_name → comp_uuid

        for _, comp_row in men_comps.iterrows():
            comp_name = str(comp_row.get("competition_name", ""))
            country = str(comp_row.get("country_name", ""))
            sb_comp_id = comp_row.get("competition_id")
            sb_season_id = comp_row.get("season_id")
            season_name = str(comp_row.get("season_name", ""))

            if not comp_name:
                continue

            source_id = f"statsbomb_{sb_comp_id}"
            league_key = f"{country}-{comp_name}"

            # ── 대회 등록 ──
            if comp_name not in seen_comps:
                sb_upsert("competitions", [{
                    "source_id": source_id,
                    "name": comp_name,
                    "country": country,
                    "source": "statsbomb",
                }], on_conflict="source,source_id")

                comps = sb_select("competitions", filters={
                    "source_id": source_id, "source": "statsbomb",
                })
                if comps:
                    seen_comps[comp_name] = comps[0]["id"]

            comp_uuid = seen_comps.get(comp_name)
            if not comp_uuid:
                continue

            # ── 시즌 등록 ──
            sb_upsert("seasons", [{
                "competition_id": comp_uuid,
                "year": season_name,
                "name": f"{comp_name} {season_name}",
                "is_current": False,
            }], on_conflict="competition_id,year")

            seasons = sb_select("seasons", filters={
                "competition_id": comp_uuid, "year": season_name,
            })
            season_uuid = seasons[0]["id"] if seasons else None

            if league_key not in comp_map:
                comp_map[league_key] = {"comp_id": comp_uuid, "season_ids": {}}
            if season_uuid:
                comp_map[league_key]["season_ids"][season_name] = season_uuid

            # ── 매치에서 팀/선수 추출 ──
            try:
                matches = sb.matches(
                    competition_id=sb_comp_id, season_id=sb_season_id,
                )
                if matches is not None and not matches.empty:
                    _extract_teams_from_sb(matches, country)
                    _extract_players_from_sb(matches.head(10))
            except Exception as e:
                log.warning(f"  [StatsBomb] {comp_name} {season_name} 매치 추출 실패: {e}")

        log.info(
            f"[StatsBomb] {len(seen_comps)} 대회, "
            f"{sum(len(v['season_ids']) for v in comp_map.values())} 시즌 수집"
        )

    except Exception as e:
        log.warning(f"[StatsBomb] 수집 오류: {e}")

    return comp_map


def _extract_teams_from_sb(matches_df, country: str) -> None:
    """StatsBomb 매치 DataFrame에서 팀명 추출 → teams 테이블."""
    team_names: set[str] = set()
    for col in ["home_team", "away_team"]:
        if col in matches_df.columns:
            team_names.update(
                str(n).strip() for n in matches_df[col].dropna().unique()
            )

    rows = []
    for name in team_names:
        if not name:
            continue
        rows.append({
            "name": name,
            "canonical": name,
            "aliases": [name],
            "country": country,
            "source": "statsbomb",
        })

    if rows:
        sb_upsert("teams", rows, on_conflict="canonical")
        log.info(f"    팀 {len(rows)}개 등록/갱신")


def _extract_players_from_sb(matches_df) -> None:
    """StatsBomb 라인업에서 선수 정보 추출 → players 테이블."""
    try:
        from statsbombpy import sb
    except ImportError:
        return

    players_seen: set[str] = set()
    rows = []

    for _, match_row in matches_df.iterrows():
        match_id = match_row.get("match_id")
        if not match_id:
            continue
        try:
            lineups = sb.lineups(match_id=match_id)
            if not lineups:
                continue
            for team_name, lineup_df in lineups.items():
                if lineup_df is None or lineup_df.empty:
                    continue
                for _, p in lineup_df.iterrows():
                    pname = _safe_str(p.get("player_name"))
                    if not pname or pname in players_seen:
                        continue
                    players_seen.add(pname)
                    # country: dict {"id":..,"name":"Portugal"} 또는 str
                    country_val = p.get("country")
                    if isinstance(country_val, dict):
                        nationality = country_val.get("name")
                    else:
                        nationality = _safe_str(country_val)
                    rows.append({
                        "name": pname,
                        "full_name": pname,
                        "nationality": nationality,
                        "source": "statsbomb",
                        "meta": {
                            "team": str(team_name),
                            "nickname": _safe_str(p.get("player_nickname")),
                        },
                    })
        except Exception:
            pass

    if rows:
        sb_insert("players", rows)
        log.info(f"    선수 {len(rows)}명 등록")


# ══════════════════════════════════════════════════
# 2순위: football-data.org
# ══════════════════════════════════════════════════

def collect_footballdata() -> dict[str, dict]:
    """football-data.org에서 5대 리그 대회/시즌/팀/선수 수집."""
    log.info("[football-data.org] 수집 시작...")
    comp_map: dict[str, dict] = {}

    if not FOOTBALL_DATA_TOKEN:
        log.warning("[football-data.org] FOOTBALL_DATA_TOKEN 미설정 — 건너뜀")
        return comp_map

    for code, info in FD_LEAGUES.items():
        try:
            source_id = f"fd_{code}"

            # ── 대회 등록 ──
            sb_upsert("competitions", [{
                "source_id": source_id,
                "name": info["name"],
                "country": info["country"],
                "source": "football-data",
            }], on_conflict="source,source_id")

            comps = sb_select("competitions", filters={
                "source_id": source_id, "source": "football-data",
            })
            if not comps:
                continue
            comp_uuid = comps[0]["id"]

            # ── 현재 시즌 ──
            comp_data = _fd_get(f"/competitions/{code}")
            season_info = comp_data.get("currentSeason", {}) if comp_data else {}
            season_name = ""
            if season_info.get("startDate"):
                sy = season_info["startDate"][:4]
                season_name = f"{sy}-{int(sy) + 1}"

            if season_name:
                sb_upsert("seasons", [{
                    "competition_id": comp_uuid,
                    "year": season_name,
                    "name": f"{info['name']} {season_name}",
                    "is_current": True,
                    "start_date": season_info.get("startDate"),
                    "end_date": season_info.get("endDate"),
                }], on_conflict="competition_id,year")

                seasons = sb_select("seasons", filters={
                    "competition_id": comp_uuid, "year": season_name,
                })
                league_key = f"{info['country']}-{info['name']}"
                comp_map[league_key] = {
                    "comp_id": comp_uuid,
                    "season_ids": {season_name: seasons[0]["id"]} if seasons else {},
                }

            # ── 팀 + 선수 ──
            time.sleep(7)  # 레이트 리밋 대응
            teams_data = _fd_get(f"/competitions/{code}/teams")
            if teams_data and "teams" in teams_data:
                _store_fd_teams(teams_data["teams"], info["country"])
                log.info(f"  {info['name']}: {len(teams_data['teams'])} teams")

        except Exception as e:
            log.warning(f"  [football-data.org] {info['name']}: {e}")

    log.info(f"[football-data.org] {len(comp_map)} 리그 수집")
    return comp_map


def _store_fd_teams(teams: list[dict], country: str) -> None:
    """football-data.org 팀+스쿼드 → teams + players 테이블."""
    team_rows = []
    player_rows = []

    for t in teams:
        name = (t.get("name") or "").strip()
        short = (t.get("shortName") or name).strip()
        if not name:
            continue

        team_rows.append({
            "name": name,
            "canonical": short or name,
            "aliases": list({name, short}) if short != name else [name],
            "country": country,
            "founded_year": t.get("founded"),
            "stadium": t.get("venue"),
            "crest_url": t.get("crest"),
            "source": "football-data",
        })

        for p in t.get("squad") or []:
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
                "meta": {"team": short or name, "fd_id": p.get("id")},
            })

    if team_rows:
        sb_upsert("teams", team_rows, on_conflict="canonical")
    if player_rows:
        sb_insert("players", player_rows)
        log.info(f"    선수 {len(player_rows)}명 등록")


# ══════════════════════════════════════════════════
# 3순위: FBref fallback (403 가능성 높음)
# ══════════════════════════════════════════════════

def collect_fbref_fallback() -> dict[str, dict]:
    """FBref (soccerdata) fallback. 403 실패 시 빈 결과 반환."""
    log.info("[FBref] fallback 시도...")
    comp_map: dict[str, dict] = {}

    try:
        import soccerdata as sd
    except ImportError:
        log.info("[FBref] soccerdata 미설치 — 건너뜀")
        return comp_map

    LEAGUES = {
        "ENG-Premier League": {"country": "England", "fbref": "ENG-Premier League"},
        "ESP-La Liga":        {"country": "Spain",   "fbref": "ESP-La Liga"},
        "ITA-Serie A":        {"country": "Italy",   "fbref": "ITA-Serie A"},
        "GER-Bundesliga":     {"country": "Germany", "fbref": "GER-Bundesliga"},
        "FRA-Ligue 1":        {"country": "France",  "fbref": "FRA-Ligue 1"},
    }

    for league_key, info in LEAGUES.items():
        try:
            fbref = sd.FBref(leagues=info["fbref"], seasons="2024-2025")
            schedule = fbref.read_schedule()
            if schedule is None or schedule.empty:
                continue

            sb_upsert("competitions", [{
                "source_id": league_key,
                "name": league_key.split("-", 1)[1],
                "country": info["country"],
                "source": "fbref",
            }], on_conflict="source,source_id")

            comps = sb_select("competitions", filters={
                "source_id": league_key, "source": "fbref",
            })
            if not comps:
                continue
            comp_id = comps[0]["id"]
            comp_map[league_key] = {"comp_id": comp_id, "season_ids": {}}

            schedule = schedule.reset_index()
            team_names: set[str] = set()
            for col in ["home_team", "away_team"]:
                if col in schedule.columns:
                    team_names.update(schedule[col].dropna().unique())

            rows = [{
                "name": n, "canonical": str(n).strip(),
                "aliases": [n], "country": info["country"],
                "source": "fbref",
            } for n in team_names if n]

            if rows:
                sb_upsert("teams", rows, on_conflict="canonical")
            log.info(f"  [FBref] {league_key}: {len(team_names)} teams")

        except Exception as e:
            log.warning(f"  [FBref] {league_key} 실패 (403?): {e}")
            continue

    return comp_map


# ── Team-Season 매핑 ─────────────────────────────

def link_team_seasons(comp_map: dict[str, dict]) -> None:
    """team_seasons 테이블에 팀-시즌 매핑 저장."""
    log.info("팀-시즌 매핑 시작...")
    teams = sb_select("teams", limit=5000)

    for league_key, info in comp_map.items():
        comp_id = info["comp_id"]
        # league_key 형식: "Country-CompName"
        country = league_key.split("-")[0] if "-" in league_key else ""

        league_teams = [t for t in teams if t.get("country") == country]

        for season_key, season_id in info["season_ids"].items():
            rows = [{
                "team_id": t["id"],
                "season_id": season_id,
                "competition_id": comp_id,
            } for t in league_teams]

            if rows:
                sb_upsert(
                    "team_seasons", rows,
                    on_conflict="team_id,season_id,competition_id",
                )
                log.info(f"  {league_key} {season_key}: {len(rows)} team-season links")


# ── Main ─────────────────────────────────────────

def main() -> None:
    log.info("=" * 60)
    log.info("La Paz Agent 1 — Structure Collector 시작")
    log.info("=" * 60)
    publish_status("agent_1", "running", "Structure 수집 시작")

    try:
        # 1순위: StatsBomb Open Data
        comp_map = collect_statsbomb()
        publish_status("agent_1", "running", f"StatsBomb: {len(comp_map)} leagues")

        # 2순위: football-data.org (5대 리그 보완)
        fd_map = collect_footballdata()
        for k, v in fd_map.items():
            if k not in comp_map:
                comp_map[k] = v
        publish_status("agent_1", "running", f"총 {len(comp_map)} leagues")

        # 3순위: FBref fallback (1·2순위로 부족할 때만)
        if len(comp_map) < 3:
            log.info("데이터 부족 — FBref fallback 시도")
            fbref_map = collect_fbref_fallback()
            for k, v in fbref_map.items():
                if k not in comp_map:
                    comp_map[k] = v

        # K리그 수집 (API-Football > FBref fallback)
        try:
            from kleague_collectors import collect_kleague_structure_af, collect_kleague_fbref
            import os
            if os.environ.get("API_FOOTBALL_KEY"):
                log.info("K리그 구조 수집 (API-Football)...")
                kleague_map = collect_kleague_structure_af()
            else:
                log.info("K리그 구조 수집 (FBref fallback)...")
                kleague_map = collect_kleague_fbref()
            for k, v in kleague_map.items():
                if k not in comp_map:
                    comp_map[k] = v
            log.info(f"K리그 {len(kleague_map)} 리그 구조 추가")
        except Exception as e:
            log.warning(f"K리그 구조 수집 실패: {e}")

        # 팀-시즌 매핑
        link_team_seasons(comp_map)

        publish_status(
            "agent_1", "completed",
            f"Structure 수집 완료: {len(comp_map)} leagues",
        )
        log.info(f"Agent 1 완료! {len(comp_map)} leagues")

    except Exception as e:
        log.error(f"Agent 1 오류: {e}\n{traceback.format_exc()}")
        publish_status("agent_1", "error", str(e)[:500])
        raise


if __name__ == "__main__":
    main()
