#!/usr/bin/env python3
"""La Paz Agent 4: Document Generator & Embedder

입력: 전체 테이블 데이터 쿼리
처리: 자연어 문서 변환 + 팀명 해소(canonical+aliases)
임베딩: SentenceTransformer(paraphrase-multilingual-MiniLM-L12-v2) → 384차원
문서 유형: match_report, team_profile, player_profile,
          transfer_news, league_standing, scorer_ranking, article
저장: documents 테이블 (pgvector)
의존성: Agent 2 + Agent 3 완료 대기

v2 개선:
- 문서 생성 로직을 doc_generators.py로 분리
- player_profile: meta.player_name 역매칭으로 통계 커버리지 향상
- team_profile: competition_id 기반 리그 풀네임 해소
- league_standing: competition_id별 분리 (1건 → 리그별 독립 문서)
- scorer_ranking: 리그 약칭→풀네임 + 어시스트 순위 추가
- 배치 임베딩으로 저장 속도 개선
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
    sb_select,
    get_supabase,
)
from doc_generators import (
    generate_match_reports,
    generate_team_profiles,
    generate_player_profiles,
    generate_transfer_news,
    generate_league_standings,
    generate_scorer_rankings,
    generate_article_docs,
    _load_shared_data,
)

log = get_agent_logger("agent_4")

EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 100  # 배치 임베딩 크기


def _load_model():
    """SentenceTransformer 모델 로드."""
    from sentence_transformers import SentenceTransformer
    log.info(f"임베딩 모델 로드: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL)


def _embed_and_store(model, docs: list[dict]) -> int:
    """문서 목록을 배치 임베딩 + 배치 insert로 Supabase에 저장.

    개선: 건별 insert → 배치 insert로 속도 10~50배 향상.
    """
    if not docs:
        return 0

    sb = get_supabase()
    stored = 0
    INSERT_CHUNK = 50  # Supabase 배치 insert 단위

    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        texts = [d["content"] for d in batch]
        embeddings = model.encode(texts, show_progress_bar=False)

        # 배치 행 생성
        rows = []
        for doc, emb in zip(batch, embeddings):
            vec_str = "[" + ",".join(str(x) for x in emb.tolist()) + "]"
            rows.append({
                "doc_type": doc["doc_type"],
                "ref_id": doc.get("ref_id"),
                "title": doc["title"],
                "content": doc["content"],
                "embedding": vec_str,
                "metadata": doc.get("metadata", {}),
            })

        # 배치 insert (INSERT_CHUNK 단위)
        for j in range(0, len(rows), INSERT_CHUNK):
            chunk = rows[j:j + INSERT_CHUNK]
            try:
                sb.table("documents").insert(chunk).execute()
                stored += len(chunk)
            except Exception as e:
                # 배치 실패 시 건별 insert로 폴백
                for row in chunk:
                    try:
                        sb.table("documents").insert(row).execute()
                        stored += 1
                    except Exception:
                        pass

        log.info(
            f"    임베딩 저장: {min(i + BATCH_SIZE, len(docs))}/{len(docs)} "
            f"(누적 {stored}건)"
        )

    return stored


def _build_team_lookup() -> dict[str, str]:
    """팀 aliases → canonical 매핑 생성."""
    teams = sb_select("teams", limit=0)
    lookup: dict[str, str] = {}
    for t in teams:
        canonical = t["canonical"]
        lookup[canonical] = canonical
        lookup[t["name"]] = canonical
        for alias in (t.get("aliases") or []):
            lookup[alias] = canonical
    return lookup


def main() -> None:
    """Agent 4 메인: 문서 생성 + 임베딩 + 저장."""
    log.info("=" * 60)
    log.info("La Paz Agent 4 — Document Generator & Embedder v2 시작")
    log.info("=" * 60)
    publish_status("agent_4", "waiting", "Agent 2 + Agent 3 대기")

    a2_ok = wait_for_agent("agent_2", "completed", timeout=1200)
    a3_ok = wait_for_agent("agent_3", "completed", timeout=1200)
    if not a2_ok:
        log.warning("Agent 2 타임아웃 — 기존 데이터로 진행")
    if not a3_ok:
        log.warning("Agent 3 타임아웃 — 기존 데이터로 진행")

    publish_status("agent_4", "running", "문서 생성 & 임베딩 시작")

    try:
        model = _load_model()
        team_lookup = _build_team_lookup()

        # 공유 데이터 1회 로드 (teams, comps)
        shared = _load_shared_data()
        log.info(
            f"공유 데이터: teams={len(shared['teams'])}건, "
            f"comps={len(shared['comps'])}건"
        )

        # 기존 documents 삭제 (전체 재생성)
        try:
            sb = get_supabase()
            sb.table("documents").delete().neq(
                "id", "00000000-0000-0000-0000-000000000000"
            ).execute()
            log.info("기존 documents 테이블 클리어")
        except Exception as e:
            log.warning(f"documents 클리어 실패 (계속 진행): {e}")

        total = 0

        # 1. match_report
        publish_status("agent_4", "running", "match_report 생성 중")
        docs = generate_match_reports(team_lookup, shared)
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  match_report 저장: {count}/{len(docs)}")
        publish_status("agent_4", "running", f"match_report {count}건 완료")

        # 2. team_profile
        publish_status("agent_4", "running", "team_profile 생성 중")
        docs = generate_team_profiles(team_lookup, shared)
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  team_profile 저장: {count}/{len(docs)}")

        # 3. player_profile
        publish_status("agent_4", "running", "player_profile 생성 중")
        docs = generate_player_profiles(team_lookup, shared)
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  player_profile 저장: {count}/{len(docs)}")

        # 4. transfer_news
        publish_status("agent_4", "running", "transfer_news 생성 중")
        docs = generate_transfer_news(team_lookup)
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  transfer_news 저장: {count}/{len(docs)}")

        # 5. league_standing
        publish_status("agent_4", "running", "league_standing 생성 중")
        docs = generate_league_standings(team_lookup, shared)
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  league_standing 저장: {count}/{len(docs)}")

        # 6. scorer_ranking
        publish_status("agent_4", "running", "scorer_ranking 생성 중")
        docs = generate_scorer_rankings(team_lookup, shared)
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  scorer_ranking 저장: {count}/{len(docs)}")

        # 7. articles
        publish_status("agent_4", "running", "article 생성 중")
        docs = generate_article_docs()
        count = _embed_and_store(model, docs)
        total += count
        log.info(f"  article 저장: {count}/{len(docs)}")

        publish_status(
            "agent_4", "completed",
            f"총 {total}건 문서 생성 & 임베딩 완료",
        )
        log.info(f"Agent 4 완료! 총 {total}건 문서")

    except Exception as e:
        log.error(f"Agent 4 오류: {e}\n{traceback.format_exc()}")
        publish_status("agent_4", "error", str(e)[:500])
        raise


if __name__ == "__main__":
    main()
