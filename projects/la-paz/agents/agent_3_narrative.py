#!/usr/bin/env python3
"""La Paz Agent 3: Narrative Collector

소스:
  - soccerdata (Transfermarkt) — 이적/부상 (403 가능, graceful fallback)
  - feedparser (RSS) — BBC Sport, Guardian, ESPN, Reddit r/soccer
저장: transfers, injuries, articles
의존성: Agent 1 완료 대기 (Agent 2와 병렬 가능)
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_config import (
    get_agent_logger,
    publish_status,
    wait_for_agent,
    sb_upsert,
    sb_insert,
    sb_select,
)

log = get_agent_logger("agent_3")

# ── RSS 피드 목록 ────────────────────────────────
RSS_FEEDS = {
    "bbc": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "guardian": "https://www.theguardian.com/football/rss",
    "espn": "https://www.espn.com/espn/rss/soccer/news",
    "reddit": "https://www.reddit.com/r/soccer/.rss",
}


def _safe_str(val) -> str | None:
    import pandas as pd
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val).strip()


def _resolve_team_id(team_name: str, cache: dict) -> str | None:
    """팀 이름 → ID 조회 (캐시 사용)."""
    if not team_name:
        return None
    if team_name in cache:
        return cache[team_name]
    teams = sb_select("teams", filters={"canonical": team_name.strip()})
    if teams:
        cache[team_name] = teams[0]["id"]
        return teams[0]["id"]
    return None


def _resolve_player_id(player_name: str, cache: dict) -> str | None:
    """선수 이름 → ID 조회 (캐시 사용)."""
    if not player_name:
        return None
    if player_name in cache:
        return cache[player_name]
    players = sb_select("players", filters={"name": player_name.strip()})
    if players:
        cache[player_name] = players[0]["id"]
        return players[0]["id"]
    return None


# ── Transfers (Transfermarkt via soccerdata) ─────
def collect_transfers() -> int:
    """Transfermarkt에서 이적 정보 수집 (403 시 graceful skip)."""
    log.info("이적 정보 수집 시작 (Transfermarkt)...")

    total = 0
    team_cache: dict = {}
    player_cache: dict = {}
    blocked = False

    try:
        import soccerdata as sd
    except ImportError:
        log.warning("[Transfermarkt] soccerdata 미설치 — 이적 수집 건너뜀")
        return 0

    leagues = [
        "ENG-Premier League",
        "ESP-La Liga",
        "ITA-Serie A",
        "GER-Bundesliga",
        "FRA-Ligue 1",
    ]

    for league in leagues:
        if blocked:
            break
        try:
            tm = sd.Transfermarkt(leagues=league, seasons="2024-2025")
            transfers = tm.read_transfers()
            if transfers is None or transfers.empty:
                continue

            transfers = transfers.reset_index()
            rows = []
            for _, row in transfers.iterrows():
                player_name = _safe_str(row.get("player"))
                from_team = _safe_str(row.get("from_team"))
                to_team = _safe_str(row.get("to_team"))

                fee_raw = _safe_str(row.get("fee"))
                fee = None
                if fee_raw and fee_raw not in ["?", "-", "free transfer"]:
                    try:
                        fee = float(fee_raw.replace("€", "").replace("m", "e6")
                                   .replace("k", "e3").strip())
                    except (ValueError, AttributeError):
                        pass

                transfer_type = "permanent"
                if fee_raw and "loan" in str(fee_raw).lower():
                    transfer_type = "loan"
                elif fee_raw and "free" in str(fee_raw).lower():
                    transfer_type = "free"

                rows.append({
                    "player_id": _resolve_player_id(player_name, player_cache),
                    "from_team_id": _resolve_team_id(from_team, team_cache),
                    "to_team_id": _resolve_team_id(to_team, team_cache),
                    "fee": fee,
                    "transfer_type": transfer_type,
                    "season": "2024-2025",
                    "source": "transfermarkt",
                    "meta": {
                        "player_name": player_name,
                        "from_team": from_team,
                        "to_team": to_team,
                        "fee_raw": fee_raw,
                        "league": league,
                    },
                })

            count = sb_insert("transfers", rows)
            total += count
            log.info(f"  {league}: {count} transfers")
        except Exception as e:
            err_str = str(e).lower()
            if "403" in err_str or "forbidden" in err_str:
                log.warning(f"  [Transfermarkt] 403 Forbidden — 이적 수집 중단 (나머지 리그 건너뜀)")
                blocked = True
            else:
                log.warning(f"  {league} 이적 수집 실패: {e}")

    if blocked:
        log.info("[Transfermarkt] 차단됨 — 이적 데이터는 다음 소스 추가 시 보완 가능")

    log.info(f"이적 정보 총 {total}건 수집")
    return total


# ── Injuries (Transfermarkt via soccerdata) ──────
def collect_injuries() -> int:
    """Transfermarkt에서 부상 정보 수집 (403 시 graceful skip)."""
    log.info("부상 정보 수집 시작 (Transfermarkt)...")

    total = 0
    team_cache: dict = {}
    player_cache: dict = {}
    blocked = False

    try:
        import soccerdata as sd
    except ImportError:
        log.warning("[Transfermarkt] soccerdata 미설치 — 부상 수집 건너뜀")
        return 0

    leagues = [
        "ENG-Premier League",
        "ESP-La Liga",
        "ITA-Serie A",
        "GER-Bundesliga",
        "FRA-Ligue 1",
    ]

    for league in leagues:
        if blocked:
            break
        try:
            tm = sd.Transfermarkt(leagues=league, seasons="2024-2025")
            injuries = tm.read_injuries()
            if injuries is None or injuries.empty:
                continue

            injuries = injuries.reset_index()
            rows = []
            for _, row in injuries.iterrows():
                player_name = _safe_str(row.get("player"))
                team_name = _safe_str(row.get("team"))

                start_date = None
                if hasattr(row.get("from"), "isoformat"):
                    start_date = row["from"].isoformat()[:10]

                end_date = None
                if hasattr(row.get("until"), "isoformat"):
                    end_date = row["until"].isoformat()[:10]

                rows.append({
                    "player_id": _resolve_player_id(player_name, player_cache),
                    "team_id": _resolve_team_id(team_name, team_cache),
                    "injury_type": _safe_str(row.get("injury")),
                    "start_date": start_date,
                    "end_date": end_date,
                    "games_missed": row.get("games_missed") if row.get("games_missed") else 0,
                    "source": "transfermarkt",
                    "meta": {
                        "player_name": player_name,
                        "team": team_name,
                        "league": league,
                    },
                })

            count = sb_insert("injuries", rows)
            total += count
            log.info(f"  {league}: {count} injuries")
        except Exception as e:
            err_str = str(e).lower()
            if "403" in err_str or "forbidden" in err_str:
                log.warning(f"  [Transfermarkt] 403 Forbidden — 부상 수집 중단 (나머지 리그 건너뜀)")
                blocked = True
            else:
                log.warning(f"  {league} 부상 수집 실패: {e}")

    if blocked:
        log.info("[Transfermarkt] 차단됨 — 부상 데이터는 다음 소스 추가 시 보완 가능")

    log.info(f"부상 정보 총 {total}건 수집")
    return total


# ── RSS Articles ─────────────────────────────────
def collect_articles() -> int:
    """RSS 피드에서 축구 뉴스 기사 수집."""
    log.info("RSS 뉴스 수집 시작...")

    total = 0
    try:
        import feedparser
    except ImportError:
        log.warning("feedparser 미설치 — RSS 수집 건너뜀")
        return 0

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                log.info(f"  {source_name}: 엔트리 없음")
                continue

            rows = []
            for entry in feed.entries[:50]:  # 피드당 최대 50건
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()

                published_at = None
                if entry.get("published_parsed"):
                    try:
                        from time import mktime
                        published_at = datetime.fromtimestamp(
                            mktime(entry.published_parsed), tz=timezone.utc
                        ).isoformat()
                    except Exception:
                        pass

                if not title or not link:
                    continue

                # 태그 추출
                tags = []
                if entry.get("tags"):
                    tags = [t.get("term", "") for t in entry.tags if t.get("term")]

                rows.append({
                    "source_name": source_name,
                    "title": title[:500],
                    "url": link[:2000],
                    "summary": summary[:2000] if summary else None,
                    "published_at": published_at,
                    "language": "en",
                    "tags": tags,
                    "meta": {"feed_url": feed_url},
                })

            count = sb_upsert("articles", rows, on_conflict="url")
            total += count
            log.info(f"  {source_name}: {count} articles")

        except Exception as e:
            log.warning(f"  {source_name} RSS 수집 실패: {e}")

    log.info(f"RSS 기사 총 {total}건 수집")
    return total


# ── Main ─────────────────────────────────────────
def main() -> None:
    log.info("=" * 60)
    log.info("La Paz Agent 3 — Narrative Collector 시작")
    log.info("=" * 60)
    publish_status("agent_3", "waiting", "Agent 1 대기")

    if not wait_for_agent("agent_1", "completed", timeout=900):
        log.warning("Agent 1 타임아웃 — 기존 Structure 데이터로 진행")

    publish_status("agent_3", "running", "Narrative 수집 시작")

    try:
        # 1. 이적 정보
        transfer_count = collect_transfers()

        # 2. 부상 정보
        injury_count = collect_injuries()

        # 3. RSS 뉴스
        article_count = collect_articles()

        # 4. K리그 뉴스 (RSS)
        kl_news_count = 0
        try:
            from kleague_collectors import collect_kleague_news
            kl_news_count = collect_kleague_news()
        except Exception as e:
            log.warning(f"K리그 뉴스 수집 실패: {e}")

        summary = (
            f"transfers={transfer_count}, injuries={injury_count}, "
            f"articles={article_count}, kl_news={kl_news_count}"
        )
        publish_status("agent_3", "completed", summary)
        log.info(f"Agent 3 완료! {summary}")

    except Exception as e:
        log.error(f"Agent 3 오류: {e}\n{traceback.format_exc()}")
        publish_status("agent_3", "error", str(e)[:500])
        raise


if __name__ == "__main__":
    main()
