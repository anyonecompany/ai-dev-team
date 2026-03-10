"""전체 크롤링 실행 스크립트.

1. config에서 선수 목록 로드
2. 나무위키 크롤링 시도
3. 실패 시 위키피디아 fallback
4. 둘 다 실패 시 최소 프로필 생성
5. 결과 저장 (JSON + 로그)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.config import AVL_PLAYERS, CRAWL_DELAY, MUN_PLAYERS, USER_AGENT
from src.crawlers.wikipedia_fallback import WikipediaFallbackCrawler

# 나무위키 크롤러 / 프로필 빌더는 ai-engineer가 아직 구현 중일 수 있음
try:
    from src.crawlers.namuwiki import NamuWikiCrawler

    HAS_NAMUWIKI = True
except ImportError:
    HAS_NAMUWIKI = False

try:
    from src.processors.profile_builder import ProfileBuilder

    HAS_PROFILE_BUILDER = True
except ImportError:
    HAS_PROFILE_BUILDER = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def _build_minimal_profile(player: dict, team: str, team_kr: str) -> dict:
    """크롤링 전부 실패 시 최소 프로필 생성."""
    return {
        "name_kr": player["name_kr"],
        "name_en": player["name_en"],
        "position": player.get("position", ""),
        "team": team,
        "team_kr": team_kr,
        "bio": "",
        "source": "none",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_wikipedia_profile(raw: dict, player: dict, team: str, team_kr: str) -> dict:
    """위키피디아 데이터로 프로필 생성."""
    return {
        "name_kr": player["name_kr"],
        "name_en": player["name_en"],
        "position": player.get("position", ""),
        "team": team,
        "team_kr": team_kr,
        "bio": raw.get("extract", ""),
        "description": raw.get("description", ""),
        "thumbnail_url": raw.get("thumbnail_url"),
        "page_url": raw.get("page_url"),
        "source": "wikipedia",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


def crawl_all() -> dict:
    """전체 선수 크롤링 실행."""
    namuwiki = NamuWikiCrawler(delay=CRAWL_DELAY) if HAS_NAMUWIKI else None
    wikipedia = WikipediaFallbackCrawler(delay=1.0, user_agent=USER_AGENT)
    builder = ProfileBuilder() if HAS_PROFILE_BUILDER else None

    results: dict[str, list[dict]] = {"mun": [], "avl": []}
    log_entries: list[str] = []
    stats = {"namuwiki": 0, "wikipedia": 0, "minimal": 0}

    teams = [
        ("mun", MUN_PLAYERS, "Manchester United", "맨체스터 유나이티드"),
        ("avl", AVL_PLAYERS, "Aston Villa", "아스톤 빌라"),
    ]

    for team_key, players, team_name, team_kr in teams:
        logger.info("=== %s (%d players) ===", team_name, len(players))

        for player in players:
            name_kr = player["name_kr"]
            name_en = player["name_en"]
            profile: dict | None = None

            # 1. 나무위키 시도
            if namuwiki is not None:
                try:
                    raw = namuwiki.crawl_player(name_kr, name_en)
                except Exception:
                    logger.exception("NamuWiki error for %s", name_kr)
                    raw = None

                if raw:
                    if builder:
                        profile = builder.build_from_namuwiki(
                            raw, {**player, "team": team_name, "team_kr": team_kr}
                        )
                    else:
                        profile = {
                            **raw,
                            "name_kr": name_kr,
                            "name_en": name_en,
                            "team": team_name,
                            "team_kr": team_kr,
                            "source": "namuwiki",
                            "crawled_at": datetime.now(timezone.utc).isoformat(),
                        }

                    # 빌드된 프로필의 주요 필드가 비어있으면 fallback
                    cs = profile.get("career_summary", "") or profile.get("career_text", "")
                    ps = profile.get("play_style", "") or profile.get("play_style_text", "")
                    if not cs.strip() and not ps.strip():
                        logger.warning("EMPTY    [namuwiki]   %s — fallback", name_kr)
                        profile = None
                    else:
                        stats["namuwiki"] += 1
                        log_entries.append(f"SUCCESS  [namuwiki]   {name_kr} ({name_en})")
                        logger.info("SUCCESS  [namuwiki]   %s", name_kr)

            # 2. 위키피디아 fallback
            if profile is None:
                raw_wiki = wikipedia.crawl_player(name_en)
                if raw_wiki:
                    if builder:
                        profile = builder.build_from_wikipedia(
                            raw_wiki, {**player, "team": team_name, "team_kr": team_kr}
                        )
                    else:
                        profile = _build_wikipedia_profile(raw_wiki, player, team_name, team_kr)
                    stats["wikipedia"] += 1
                    log_entries.append(f"FALLBACK [wikipedia]  {name_kr} ({name_en})")
                    logger.info("FALLBACK [wikipedia]  %s", name_kr)

            # 3. 최소 프로필
            if profile is None:
                if builder:
                    profile = builder.build_minimal(
                        {**player, "team": team_name, "team_kr": team_kr}
                    )
                else:
                    profile = _build_minimal_profile(player, team_name, team_kr)
                stats["minimal"] += 1
                log_entries.append(f"MINIMAL  [none]       {name_kr} ({name_en})")
                logger.warning("MINIMAL  [none]       %s", name_kr)

            results[team_key].append(profile)

    # ── 결과 저장 ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # JSON — output/ (timestamped)
    json_path = os.path.join(OUTPUT_DIR, f"players_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("JSON saved: %s", json_path)

    # JSON — data/ (stable paths for indexing)
    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    for key in ("mun", "avl"):
        with open(os.path.join(data_dir, f"players_{key}.json"), "w", encoding="utf-8") as f:
            json.dump(results[key], f, ensure_ascii=False, indent=2)
    all_profiles = results["mun"] + results["avl"]
    with open(os.path.join(data_dir, "players_all.json"), "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, ensure_ascii=False, indent=2)
    logger.info("Data cached: data/players_mun.json, data/players_avl.json, data/players_all.json")

    # 로그
    log_path = os.path.join(OUTPUT_DIR, f"crawl_log_{timestamp}.txt")
    summary_lines = [
        f"Crawl completed: {datetime.now(timezone.utc).isoformat()}",
        f"Total: {sum(stats.values())} players",
        f"  namuwiki:   {stats['namuwiki']}",
        f"  wikipedia:  {stats['wikipedia']}",
        f"  minimal:    {stats['minimal']}",
        "",
        "--- Detail ---",
    ]
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines + log_entries) + "\n")
    logger.info("Log saved: %s", log_path)

    logger.info(
        "Done — namuwiki: %d, wikipedia: %d, minimal: %d",
        stats["namuwiki"],
        stats["wikipedia"],
        stats["minimal"],
    )
    return results


if __name__ == "__main__":
    crawl_all()
