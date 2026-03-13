"""La Paz — K리그 데이터 수집 모듈.

K리그 1/2 데이터를 FBref, API-Football, 웹 스크래핑 등으로 수집.

소스 우선순위:
  1순위: API-Football (K리그 공식 지원, REST API)
  2순위: FBref via soccerdata (커스텀 리그 설정)
  3순위: K리그 공식 포털 스크래핑 (data.kleague.com)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from shared_config import (
    get_agent_logger,
    sb_upsert,
    sb_insert,
    sb_select,
)

log = get_agent_logger("kleague_collectors")

# ── K리그 설정 ────────────────────────────────────
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")
AF_BASE = "https://v3.football.api-sports.io"

# API-Football 리그 ID
KLEAGUE_LEAGUES = {
    "KOR-K League 1": {
        "af_id": 292,
        "name": "K League 1",
        "country": "South Korea",
        "season_start": "Feb",
        "season_end": "Nov",
    },
    "KOR-K League 2": {
        "af_id": 293,
        "name": "K League 2",
        "country": "South Korea",
        "season_start": "Feb",
        "season_end": "Nov",
    },
}

# Free 플랜 최대 시즌 (2022~2024만 접근 가능)
AF_FREE_MAX_SEASON = 2024

# FBref 리그 설정 (soccerdata 커스텀)
KLEAGUE_FBREF = {
    "KOR-K League 1": {
        "fbref": "K League 1",
        "fbref_id": 55,
    },
}

# K리그 관련 RSS 피드
KLEAGUE_RSS_FEEDS = {
    "kleague_official": "https://www.kleague.com/rss",
    "goal_kr": "https://www.goal.com/feeds/kr/news",
    "football_korea": "https://sports.news.naver.com/rss/kfootball.xml",
}


# ── API-Football 헬퍼 ─────────────────────────────

def _af_get(endpoint: str, params: dict | None = None) -> dict | None:
    """API-Football GET 요청 (100req/day 대응).

    Args:
        endpoint: API 엔드포인트 (e.g., "/leagues").
        params: 쿼리 파라미터.

    Returns:
        JSON 응답 또는 None.
    """
    if not API_FOOTBALL_KEY:
        return None

    import requests

    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    url = f"{AF_BASE}{endpoint}"

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code == 429:
            log.info("  API-Football 레이트 리밋 — 60초 대기")
            time.sleep(60)
            resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("errors"):
                log.warning(f"  API-Football {endpoint}: {data['errors']}")
                return None
            return data
        log.warning(f"  API-Football {endpoint}: HTTP {resp.status_code}")
        return None
    except Exception as e:
        log.warning(f"  API-Football {endpoint}: {e}")
        return None


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


# ══════════════════════════════════════════════════
# 1순위: API-Football — K리그 구조 (대회/시즌/팀/선수)
# ══════════════════════════════════════════════════

def collect_kleague_structure_af() -> dict[str, dict]:
    """API-Football에서 K리그 대회/시즌/팀/선수 구조 수집.

    Returns:
        {league_key: {"comp_id": uuid, "season_ids": {year: uuid}}}
    """
    log.info("[API-Football] K리그 구조 수집 시작...")
    comp_map: dict[str, dict] = {}

    if not API_FOOTBALL_KEY:
        log.warning("[API-Football] API_FOOTBALL_KEY 미설정 — 건너뜀")
        return comp_map

    for league_key, info in KLEAGUE_LEAGUES.items():
        try:
            af_league_id = info["af_id"]

            # ── 대회 등록 ──
            source_id = f"af_{af_league_id}"
            sb_upsert("competitions", [{
                "source_id": source_id,
                "name": info["name"],
                "country": info["country"],
                "source": "api-football",
            }], on_conflict="source,source_id")

            comps = sb_select("competitions", filters={
                "source_id": source_id, "source": "api-football",
            })
            if not comps:
                continue
            comp_uuid = comps[0]["id"]

            # ── 현재 시즌 조회 ──
            league_data = _af_get("/leagues", {"id": af_league_id})
            if not league_data or not league_data.get("response"):
                continue

            league_info = league_data["response"][0]
            # Free 플랜: 2022~2024만 접근 가능 → 접근 가능한 최신 시즌 선택
            all_seasons = league_info.get("seasons", [])
            available_seasons = [
                s for s in all_seasons
                if s.get("year") and int(s["year"]) <= AF_FREE_MAX_SEASON
            ]
            # 가장 최신 접근 가능 시즌
            current_seasons = []
            if available_seasons:
                current_seasons = [max(available_seasons, key=lambda s: s["year"])]
                log.info(f"  Free 플랜: {info['name']} 시즌 {current_seasons[0]['year']} 사용")

            for season in current_seasons:
                year = str(season.get("year", ""))
                if not year:
                    continue

                sb_upsert("seasons", [{
                    "competition_id": comp_uuid,
                    "year": year,
                    "name": f"{info['name']} {year}",
                    "is_current": season.get("current", False),
                    "start_date": season.get("start"),
                    "end_date": season.get("end"),
                }], on_conflict="competition_id,year")

                seasons = sb_select("seasons", filters={
                    "competition_id": comp_uuid, "year": year,
                })
                season_uuid = seasons[0]["id"] if seasons else None

                if league_key not in comp_map:
                    comp_map[league_key] = {
                        "comp_id": comp_uuid,
                        "season_ids": {},
                    }
                if season_uuid:
                    comp_map[league_key]["season_ids"][year] = season_uuid

                # ── 팀 수집 ──
                time.sleep(1)
                _collect_teams_af(af_league_id, int(year), comp_uuid, season_uuid)

            log.info(f"  [API-Football] {info['name']}: 구조 수집 완료")

        except Exception as e:
            log.warning(f"  [API-Football] {league_key}: {e}")

    log.info(f"[API-Football] K리그 {len(comp_map)} 리그 구조 수집 완료")
    return comp_map


def _collect_teams_af(
    league_id: int, season: int,
    comp_uuid: str, season_uuid: str | None,
) -> None:
    """API-Football에서 팀 + 스쿼드 수집."""
    data = _af_get("/teams", {"league": league_id, "season": season})
    if not data or not data.get("response"):
        return

    team_rows = []
    player_rows = []

    for item in data["response"]:
        team = item.get("team", {})
        venue = item.get("venue", {})
        name = team.get("name", "").strip()
        if not name:
            continue

        team_rows.append({
            "name": name,
            "canonical": name,
            "aliases": [name],
            "country": "South Korea",
            "founded_year": team.get("founded"),
            "stadium": venue.get("name"),
            "crest_url": team.get("logo"),
            "source": "api-football",
            "meta": {"af_id": team.get("id")},
        })

        # 스쿼드 수집 (레이트 리밋 주의)
        time.sleep(1)
        squad_data = _af_get("/players/squads", {"team": team.get("id")})
        if squad_data and squad_data.get("response"):
            for squad_item in squad_data["response"]:
                for p in squad_item.get("players", []):
                    pname = (p.get("name") or "").strip()
                    if not pname:
                        continue
                    player_rows.append({
                        "name": pname,
                        "full_name": pname,
                        "position": p.get("position"),
                        "source": "api-football",
                        "meta": {
                            "team": name,
                            "af_id": p.get("id"),
                            "number": p.get("number"),
                            "photo": p.get("photo"),
                        },
                    })

    if team_rows:
        sb_upsert("teams", team_rows, on_conflict="canonical")
        log.info(f"    팀 {len(team_rows)}개 등록/갱신")

    if player_rows:
        sb_insert("players", player_rows)
        log.info(f"    선수 {len(player_rows)}명 등록")

    # 팀-시즌 매핑
    if season_uuid:
        teams = sb_select("teams", filters={"country": "South Korea"}, limit=100)
        ts_rows = [{
            "team_id": t["id"],
            "season_id": season_uuid,
            "competition_id": comp_uuid,
        } for t in teams]
        if ts_rows:
            sb_upsert("team_seasons", ts_rows,
                       on_conflict="team_id,season_id,competition_id")


# ══════════════════════════════════════════════════
# 1순위: API-Football — K리그 경기 결과
# ══════════════════════════════════════════════════

def collect_kleague_matches_af() -> int:
    """API-Football에서 K리그 경기 결과 수집 → matches 테이블.

    Returns:
        저장된 경기 수.
    """
    log.info("[API-Football] K리그 경기 수집 시작...")
    if not API_FOOTBALL_KEY:
        log.warning("[API-Football] API_FOOTBALL_KEY 미설정 — 건너뜀")
        return 0

    total = 0
    teams_cache: dict[str, str] = {}
    for t in sb_select("teams", filters={"country": "South Korea"}, limit=200):
        teams_cache[t["canonical"]] = t["id"]
        teams_cache[t["name"]] = t["id"]

    for league_key, info in KLEAGUE_LEAGUES.items():
        try:
            af_league_id = info["af_id"]

            # comp_id, season_id 조회
            comps = sb_select("competitions", filters={
                "source_id": f"af_{af_league_id}", "source": "api-football",
            })
            if not comps:
                continue
            comp_uuid = comps[0]["id"]

            # Free 플랜 범위 내 최신 시즌 조회
            all_db_seasons = sb_select("seasons", filters={
                "competition_id": comp_uuid,
            }, limit=100)
            valid_seasons = [
                s for s in all_db_seasons
                if s.get("year") and int(s["year"]) <= AF_FREE_MAX_SEASON
            ]
            if valid_seasons:
                best = max(valid_seasons, key=lambda s: int(s["year"]))
                season_uuid = best["id"]
                season_year = best["year"]
            else:
                season_uuid = None
                season_year = str(AF_FREE_MAX_SEASON)

            # 경기 조회
            time.sleep(1)
            data = _af_get("/fixtures", {
                "league": af_league_id,
                "season": int(season_year),
                "status": "FT",  # Finished
            })
            if not data or not data.get("response"):
                continue

            rows = []
            for fixture in data["response"]:
                fix = fixture.get("fixture", {})
                teams_info = fixture.get("teams", {})
                goals = fixture.get("goals", {})
                league = fixture.get("league", {})

                fix_id = fix.get("id")
                if not fix_id:
                    continue

                home_name = teams_info.get("home", {}).get("name", "")
                away_name = teams_info.get("away", {}).get("name", "")

                match_date = (fix.get("date") or "")[:10]

                rows.append({
                    "source_id": f"af_{fix_id}",
                    "competition_id": comp_uuid,
                    "season_id": season_uuid,
                    "match_date": match_date or None,
                    "matchday": league.get("round"),
                    "home_team_id": teams_cache.get(home_name),
                    "away_team_id": teams_cache.get(away_name),
                    "home_score": goals.get("home"),
                    "away_score": goals.get("away"),
                    "stadium": fix.get("venue", {}).get("name"),
                    "referee": fix.get("referee"),
                    "source": "api-football",
                    "meta": {
                        "status": fix.get("status", {}).get("long"),
                        "home_team_name": home_name,
                        "away_team_name": away_name,
                        "af_league_id": af_league_id,
                    },
                })

            if rows:
                count = sb_upsert("matches", rows, on_conflict="source,source_id")
                total += count
                log.info(f"  {info['name']}: {count} matches")

        except Exception as e:
            log.warning(f"  [API-Football] {league_key} 경기: {e}")

    log.info(f"[API-Football] K리그 총 {total} matches 저장")
    return total


# ══════════════════════════════════════════════════
# 1순위: API-Football — K리그 순위표
# ══════════════════════════════════════════════════

def collect_kleague_standings_af() -> int:
    """API-Football에서 K리그 순위표 수집 → team_season_stats.

    Returns:
        저장된 행 수.
    """
    log.info("[API-Football] K리그 순위표 수집 시작...")
    if not API_FOOTBALL_KEY:
        return 0

    total = 0
    teams_cache: dict[str, str] = {}
    for t in sb_select("teams", filters={"country": "South Korea"}, limit=200):
        teams_cache[t["canonical"]] = t["id"]
        teams_cache[t["name"]] = t["id"]

    for league_key, info in KLEAGUE_LEAGUES.items():
        try:
            af_league_id = info["af_id"]
            comps = sb_select("competitions", filters={
                "source_id": f"af_{af_league_id}", "source": "api-football",
            })
            if not comps:
                continue
            comp_uuid = comps[0]["id"]

            # Free 플랜 범위 내 최신 시즌 조회
            all_db_seasons = sb_select("seasons", filters={
                "competition_id": comp_uuid,
            }, limit=100)
            valid_seasons = [
                s for s in all_db_seasons
                if s.get("year") and int(s["year"]) <= AF_FREE_MAX_SEASON
            ]
            if valid_seasons:
                best = max(valid_seasons, key=lambda s: int(s["year"]))
                season_uuid = best["id"]
                season_year = best["year"]
            else:
                season_uuid = None
                season_year = str(AF_FREE_MAX_SEASON)

            time.sleep(1)
            data = _af_get("/standings", {
                "league": af_league_id,
                "season": int(season_year),
            })
            if not data or not data.get("response"):
                continue

            for item in data["response"]:
                league_info = item.get("league", {})
                for standings_group in league_info.get("standings", []):
                    rows = []
                    for entry in standings_group:
                        team_name = entry.get("team", {}).get("name", "")
                        team_id = teams_cache.get(team_name)
                        all_stats = entry.get("all", {})

                        rows.append({
                            "team_id": team_id,
                            "season_id": season_uuid,
                            "competition_id": comp_uuid,
                            "position": entry.get("rank"),
                            "played": all_stats.get("played", 0),
                            "won": all_stats.get("win", 0),
                            "draw": all_stats.get("draw", 0),
                            "lost": all_stats.get("lose", 0),
                            "goals_for": all_stats.get("goals", {}).get("for", 0),
                            "goals_against": all_stats.get("goals", {}).get("against", 0),
                            "goal_diff": entry.get("goalsDiff", 0),
                            "points": entry.get("points", 0),
                            "source": "api-football",
                            "meta": {
                                "team_name": team_name,
                                "league": info["name"],
                                "form": entry.get("form"),
                            },
                        })

                    if rows:
                        count = sb_upsert(
                            "team_season_stats", rows,
                            on_conflict="team_id,season_id,competition_id",
                        )
                        total += count

            log.info(f"  {info['name']}: 순위표 수집 완료")

        except Exception as e:
            log.warning(f"  [API-Football] {league_key} 순위표: {e}")

    log.info(f"[API-Football] K리그 총 {total} standings 저장")
    return total


# ══════════════════════════════════════════════════
# 1순위: API-Football — K리그 득점 순위
# ══════════════════════════════════════════════════

def collect_kleague_scorers_af() -> int:
    """API-Football에서 K리그 득점 순위 수집.

    Returns:
        저장된 행 수.
    """
    log.info("[API-Football] K리그 득점 순위 수집 시작...")
    if not API_FOOTBALL_KEY:
        return 0

    total = 0
    players_cache: dict[str, str] = {}
    for p in sb_select("players", columns="id,name", limit=0):
        players_cache[p["name"]] = p["id"]

    teams_cache: dict[str, str] = {}
    for t in sb_select("teams", filters={"country": "South Korea"}, limit=200):
        teams_cache[t["canonical"]] = t["id"]
        teams_cache[t["name"]] = t["id"]

    for league_key, info in KLEAGUE_LEAGUES.items():
        try:
            af_league_id = info["af_id"]
            comps = sb_select("competitions", filters={
                "source_id": f"af_{af_league_id}", "source": "api-football",
            })
            if not comps:
                continue
            comp_uuid = comps[0]["id"]

            # Free 플랜 범위 내 최신 시즌 조회
            all_db_seasons = sb_select("seasons", filters={
                "competition_id": comp_uuid,
            }, limit=100)
            valid_seasons = [
                s for s in all_db_seasons
                if s.get("year") and int(s["year"]) <= AF_FREE_MAX_SEASON
            ]
            if valid_seasons:
                best = max(valid_seasons, key=lambda s: int(s["year"]))
                season_uuid = best["id"]
                season_year = best["year"]
            else:
                season_uuid = None
                season_year = str(AF_FREE_MAX_SEASON)

            time.sleep(1)
            data = _af_get("/players/topscorers", {
                "league": af_league_id,
                "season": int(season_year),
            })
            if not data or not data.get("response"):
                continue

            rows = []
            for item in data["response"]:
                player_info = item.get("player", {})
                stats_list = item.get("statistics", [])
                if not stats_list:
                    continue

                stats = stats_list[0]
                team_info = stats.get("team", {})
                goals_info = stats.get("goals", {})
                games_info = stats.get("games", {})

                player_name = player_info.get("name", "")
                team_name = team_info.get("name", "")

                rows.append({
                    "player_id": players_cache.get(player_name),
                    "season_id": season_uuid,
                    "team_id": teams_cache.get(team_name),
                    "competition_id": comp_uuid,
                    "appearances": games_info.get("appearences", 0),
                    "goals": goals_info.get("total", 0),
                    "assists": goals_info.get("assists", 0),
                    "source": "api-football",
                    "meta": {
                        "player_name": player_name,
                        "team_name": team_name,
                        "league": info["name"],
                        "rating": games_info.get("rating"),
                        "minutes": games_info.get("minutes"),
                    },
                })

            if rows:
                count = sb_insert("player_season_stats", rows)
                total += count
                log.info(f"  {info['name']}: {count} scorers")

        except Exception as e:
            log.warning(f"  [API-Football] {league_key} 득점 순위: {e}")

    log.info(f"[API-Football] K리그 총 {total} scorers 저장")
    return total


# ══════════════════════════════════════════════════
# 2순위: FBref — K리그 통계 (soccerdata)
# ══════════════════════════════════════════════════

def collect_kleague_fbref() -> dict[str, dict]:
    """FBref에서 K리그 1 데이터 수집 (soccerdata 커스텀 리그).

    Returns:
        {league_key: {"comp_id": uuid, "season_ids": {year: uuid}}}
    """
    log.info("[FBref] K리그 수집 시도...")
    comp_map: dict[str, dict] = {}

    try:
        import soccerdata as sd
    except ImportError:
        log.warning("[FBref] soccerdata 미설치 — 건너뜀")
        return comp_map

    # soccerdata 커스텀 리그 설정 확인
    soccerdata_dir = Path.home() / "soccerdata" / "config"
    league_dict_path = soccerdata_dir / "league_dict.json"

    # 커스텀 리그 설정이 없으면 생성
    if not league_dict_path.exists() or "KOR-K League 1" not in league_dict_path.read_text():
        log.info("  soccerdata 커스텀 리그 설정 추가 중...")
        soccerdata_dir.mkdir(parents=True, exist_ok=True)

        existing = {}
        if league_dict_path.exists():
            try:
                existing = json.loads(league_dict_path.read_text())
            except Exception:
                pass

        existing["KOR-K League 1"] = {
            "FBref": "K League 1",
            "season_start": "Feb",
            "season_end": "Nov",
        }

        league_dict_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False)
        )
        log.info("  KOR-K League 1 설정 추가 완료")

    try:
        fbref = sd.FBref(leagues="KOR-K League 1", seasons="2025")
        schedule = fbref.read_schedule()
        if schedule is None or schedule.empty:
            log.info("  [FBref] K League 1 스케줄 없음")
            return comp_map

        league_key = "KOR-K League 1"

        # 대회 등록
        sb_upsert("competitions", [{
            "source_id": league_key,
            "name": "K League 1",
            "country": "South Korea",
            "source": "fbref",
        }], on_conflict="source,source_id")

        comps = sb_select("competitions", filters={
            "source_id": league_key, "source": "fbref",
        })
        if not comps:
            return comp_map

        comp_uuid = comps[0]["id"]
        comp_map[league_key] = {"comp_id": comp_uuid, "season_ids": {}}

        # 시즌 등록
        sb_upsert("seasons", [{
            "competition_id": comp_uuid,
            "year": "2025",
            "name": "K League 1 2025",
            "is_current": True,
        }], on_conflict="competition_id,year")

        seasons = sb_select("seasons", filters={
            "competition_id": comp_uuid, "year": "2025",
        })
        if seasons:
            comp_map[league_key]["season_ids"]["2025"] = seasons[0]["id"]

        # 팀 추출
        schedule = schedule.reset_index()
        team_names: set[str] = set()
        for col in ["home_team", "away_team"]:
            if col in schedule.columns:
                team_names.update(
                    str(n).strip() for n in schedule[col].dropna().unique()
                )

        team_rows = [{
            "name": n,
            "canonical": n,
            "aliases": [n],
            "country": "South Korea",
            "source": "fbref",
        } for n in team_names if n]

        if team_rows:
            sb_upsert("teams", team_rows, on_conflict="canonical")
            log.info(f"  [FBref] K League 1: {len(team_rows)} teams")

    except Exception as e:
        log.warning(f"  [FBref] K League 1 실패: {e}")

    return comp_map


# ══════════════════════════════════════════════════
# K리그 뉴스 RSS 수집
# ══════════════════════════════════════════════════

def collect_kleague_news() -> int:
    """K리그 관련 RSS 뉴스 기사 수집 → articles 테이블.

    Returns:
        저장된 기사 수.
    """
    log.info("[K리그 뉴스] RSS 수집 시작...")
    total = 0

    try:
        import feedparser
    except ImportError:
        log.warning("[K리그 뉴스] feedparser 미설치 — 건너뜀")
        return 0

    for source_name, feed_url in KLEAGUE_RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                log.info(f"  {source_name}: 기사 없음")
                continue

            rows = []
            for entry in feed.entries[:50]:
                title = (entry.get("title") or "").strip()
                url = (entry.get("link") or "").strip()
                if not title or not url:
                    continue

                summary = (entry.get("summary") or entry.get("description") or "").strip()
                published = entry.get("published") or entry.get("updated")

                # 날짜 파싱
                pub_date = None
                if published:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(published).isoformat()
                    except Exception:
                        pub_date = published

                # K리그 관련 태그
                tags = ["k-league", "korean-football"]
                if entry.get("tags"):
                    for tag in entry["tags"]:
                        tag_term = tag.get("term", "")
                        if tag_term:
                            tags.append(tag_term)

                rows.append({
                    "source_name": source_name,
                    "title": title[:500],
                    "url": url,
                    "summary": summary[:2000] if summary else None,
                    "published_at": pub_date,
                    "language": "ko",
                    "tags": tags,
                    "meta": {"feed_url": feed_url},
                })

            if rows:
                count = sb_upsert("articles", rows, on_conflict="url")
                total += count
                log.info(f"  {source_name}: {count} articles")

        except Exception as e:
            log.warning(f"  {source_name} RSS 수집 실패: {e}")

    log.info(f"[K리그 뉴스] 총 {total} articles 저장")
    return total


# ══════════════════════════════════════════════════
# 통합 실행 함수
# ══════════════════════════════════════════════════

def collect_all_kleague() -> dict[str, Any]:
    """K리그 전체 데이터 수집 실행.

    Returns:
        수집 결과 요약 dict.
    """
    log.info("=" * 60)
    log.info("K리그 데이터 수집 시작")
    log.info("=" * 60)

    result: dict[str, Any] = {
        "structure": {},
        "matches": 0,
        "standings": 0,
        "scorers": 0,
        "news": 0,
    }

    # 1순위: API-Football (구조 + 경기 + 순위 + 득점)
    if API_FOOTBALL_KEY:
        result["structure"] = collect_kleague_structure_af()
        result["matches"] = collect_kleague_matches_af()
        result["standings"] = collect_kleague_standings_af()
        result["scorers"] = collect_kleague_scorers_af()
    else:
        log.info("API_FOOTBALL_KEY 미설정 — FBref fallback으로 전환")
        # 2순위: FBref (구조만)
        result["structure"] = collect_kleague_fbref()

    # K리그 뉴스 (RSS)
    result["news"] = collect_kleague_news()

    log.info("=" * 60)
    log.info(
        f"K리그 수집 완료: "
        f"leagues={len(result['structure'])}, "
        f"matches={result['matches']}, "
        f"standings={result['standings']}, "
        f"scorers={result['scorers']}, "
        f"news={result['news']}"
    )
    log.info("=" * 60)

    return result


if __name__ == "__main__":
    collect_all_kleague()
