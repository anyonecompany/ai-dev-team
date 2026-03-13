#!/usr/bin/env python3
"""Daily crawl runner for GitHub Actions.

football-data.org 3개 수집 함수만 실행 후 agent_4 문서 재생성.
wait_for_agent 대기 로직을 우회하여 CI 환경에서 바로 실행.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# agents/ 디렉토리를 import path에 추가
agents_dir = Path(__file__).resolve().parent.parent / "agents"
sys.path.insert(0, str(agents_dir))

from shared_config import get_agent_logger, publish_status

log = get_agent_logger("daily_crawl")


def run_collectors() -> None:
    """football-data.org 3개 수집 함수 실행."""
    from collectors import (
        collect_squads_footballdata,
        collect_matches_detail_footballdata,
        collect_top_scorers_all_leagues,
    )

    log.info("=== 1/3 squads 수집 ===")
    squads = collect_squads_footballdata()
    log.info(f"squads 완료: {squads}건")

    log.info("=== 2/3 matches detail 수집 ===")
    matches = collect_matches_detail_footballdata()
    log.info(f"matches detail 완료: {matches}건")

    log.info("=== 3/3 top scorers 수집 ===")
    scorers = collect_top_scorers_all_leagues()
    log.info(f"top scorers 완료: {scorers}건")

    publish_status("agent_2", "completed", "daily crawl 수집 완료")
    publish_status("agent_3", "completed", "daily crawl skip")


def run_document_generator() -> None:
    """agent_4 문서 생성 & 임베딩 (wait 로직 우회)."""
    from agent_4_document import (
        _load_model,
        _build_team_lookup,
        _embed_and_store,
        generate_match_reports,
        generate_team_profiles,
        generate_player_profiles,
        generate_transfer_news,
        generate_league_standings,
        generate_scorer_rankings,
        generate_article_docs,
        get_supabase,
    )

    log.info("=== agent_4 문서 생성 시작 ===")
    model = _load_model()
    team_lookup = _build_team_lookup()

    # 기존 documents 삭제
    try:
        sb = get_supabase()
        sb.table("documents").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()
        log.info("기존 documents 클리어")
    except Exception as e:
        log.warning(f"documents 클리어 실패 (계속 진행): {e}")

    generators = [
        ("match_report", generate_match_reports, True),
        ("team_profile", generate_team_profiles, True),
        ("player_profile", generate_player_profiles, True),
        ("transfer_news", generate_transfer_news, True),
        ("league_standing", generate_league_standings, True),
        ("scorer_ranking", generate_scorer_rankings, True),
        ("article", generate_article_docs, False),
    ]

    total = 0
    for name, gen_fn, needs_lookup in generators:
        docs = gen_fn(team_lookup) if needs_lookup else gen_fn()
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  {name}: {count}/{len(docs)}건 임베딩")

    publish_status("agent_4", "completed", f"총 {total}건 문서 생성 완료")
    log.info(f"=== agent_4 완료: 총 {total}건 ===")


def main() -> None:
    log.info("=" * 60)
    log.info("La Paz Daily Crawl 시작")
    log.info("=" * 60)

    try:
        run_collectors()
        run_document_generator()
        log.info("Daily Crawl 전체 완료!")
    except Exception as e:
        log.error(f"Daily Crawl 실패: {e}\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
