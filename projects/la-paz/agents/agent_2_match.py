#!/usr/bin/env python3
"""La Paz Agent 2: Match & Performance Collector

소스 우선순위:
  1순위: StatsBomb Open Data — 이벤트, 라인업, 경기 결과
  2순위: football-data.org — 리그 순위표, 최근 경기
  3순위: Understat (understatapi) — xG 보완

저장: matches, lineups, match_events,
      player_match_stats, player_season_stats,
      team_match_stats, team_season_stats
의존성: Agent 1 완료 대기
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_config import (
    get_agent_logger,
    publish_status,
    wait_for_agent,
)

from collectors import (
    collect_matches_statsbomb,
    collect_events_statsbomb,
    collect_matches_footballdata,
    collect_standings_footballdata,
    collect_squads_footballdata,
    collect_matches_detail_footballdata,
    collect_top_scorers_all_leagues,
    collect_understat_xg,
)

log = get_agent_logger("agent_2")


# ── Main ─────────────────────────────────────────

def main() -> None:
    """메인 오케스트레이션: 모든 수집기를 순서대로 실행."""
    log.info("=" * 60)
    log.info("La Paz Agent 2 — Match & Performance Collector 시작")
    log.info("=" * 60)
    publish_status("agent_2", "waiting", "Agent 1 대기")

    if not wait_for_agent("agent_1", "completed", timeout=900):
        log.warning("Agent 1 타임아웃 — 기존 Structure 데이터로 진행")

    publish_status("agent_2", "running", "Match & Performance 수집 시작")

    try:
        # 1순위: StatsBomb 경기 결과
        match_count = collect_matches_statsbomb()

        # 1순위: StatsBomb 이벤트 + 라인업
        event_count = collect_events_statsbomb()

        # 2순위: football-data.org 스쿼드 (선수 확대)
        squads_count = collect_squads_footballdata()

        # 2순위: football-data.org 최근 경기
        fd_match_count = collect_matches_footballdata()

        # 2순위: football-data.org 현시즌 경기 상세 (골/카드 이벤트)
        fd_detail_count = collect_matches_detail_footballdata()

        # 2순위: football-data.org 리그 순위표
        standings_count = collect_standings_footballdata()

        # 2순위: football-data.org 전체 대회 득점 순위 (CL+ELC 포함)
        scorers_count = collect_top_scorers_all_leagues()

        # 3순위: Understat xG 보강
        xg_count = collect_understat_xg()

        # K리그 경기/순위/득점 수집 (API-Football)
        kl_matches = 0
        kl_standings = 0
        kl_scorers = 0
        try:
            from kleague_collectors import (
                collect_kleague_matches_af,
                collect_kleague_standings_af,
                collect_kleague_scorers_af,
            )
            kl_matches = collect_kleague_matches_af()
            kl_standings = collect_kleague_standings_af()
            kl_scorers = collect_kleague_scorers_af()
        except Exception as e:
            log.warning(f"K리그 수집 실패: {e}")

        summary = (
            f"sb_matches={match_count}, sb_events={event_count}, "
            f"fd_squads={squads_count}, fd_matches={fd_match_count}, "
            f"fd_detail={fd_detail_count}, fd_standings={standings_count}, "
            f"fd_scorers={scorers_count}, understat_xg={xg_count}, "
            f"kl_matches={kl_matches}, kl_standings={kl_standings}, "
            f"kl_scorers={kl_scorers}"
        )
        publish_status("agent_2", "completed", summary)
        log.info(f"Agent 2 완료! {summary}")

    except Exception as e:
        log.error(f"Agent 2 오류: {e}\n{traceback.format_exc()}")
        publish_status("agent_2", "error", str(e)[:500])
        raise


if __name__ == "__main__":
    main()
