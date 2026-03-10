#!/usr/bin/env python3
"""La Paz 데이터 보강 크롤링.

빌라 데이터 부족 + 전술 데이터 부족 해결을 위한 집중 크롤링.
기존 auto_update.py와 같은 파이프라인(크롤링→삭제→업로드→임베딩)을 따르되,
보강 대상 시드를 확장한다.

사용법:
    cd /Users/danghyeonsong/ai-dev-team/projects/lapaz-live
    python3 scripts/crawl_reinforce.py
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

import voyageai
from supabase import create_client

from src.crawlers.namuwiki_deep_crawler import NamuWikiDeepCrawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("crawl_reinforce")

# ── 보강 대상 시드 (빌라 + 전술 + 감독 + 상대전적 집중) ──

REINFORCE_SEEDS = [
    # === 아스톤 빌라 보강 (현재 54건 → 목표 200건+) ===
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC/2025-26%20시즌", "category": "season_avl"},
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC", "category": "team_avl"},
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC/스쿼드", "category": "team_avl"},
    {"url": "https://namu.wiki/w/빌라%20파크", "category": "team_avl"},

    # === 감독 전술 심층 ===
    {"url": "https://namu.wiki/w/우나이%20에메리", "category": "manager_avl"},
    {"url": "https://namu.wiki/w/루번%20아모림", "category": "manager_mun"},

    # === 맨유 최신 시즌 (재크롤링으로 최신화) ===
    {"url": "https://namu.wiki/w/맨체스터%20유나이티드%20FC/2025-26%20시즌", "category": "season_mun"},
    {"url": "https://namu.wiki/w/맨체스터%20유나이티드%20FC/2025-26%20시즌/리그", "category": "season_mun"},

    # === 리그 현황 ===
    {"url": "https://namu.wiki/w/프리미어%20리그/2025-26%20시즌", "category": "season"},
    {"url": "https://namu.wiki/w/2025-26%20프리미어%20리그", "category": "season"},

    # === 주요 선수 (빌라) ===
    {"url": "https://namu.wiki/w/올리%20왓킨스", "category": "player_avl"},
    {"url": "https://namu.wiki/w/에밀리아노%20마르티네스", "category": "player_avl"},
    {"url": "https://namu.wiki/w/유리%20틸레만스", "category": "player_avl"},
    {"url": "https://namu.wiki/w/존%20맥긴", "category": "player_avl"},
    {"url": "https://namu.wiki/w/모건%20로저스", "category": "player_avl"},
    {"url": "https://namu.wiki/w/레온%20베일리", "category": "player_avl"},
    {"url": "https://namu.wiki/w/파우%20토레스", "category": "player_avl"},

    # === 주요 선수 (맨유) ===
    {"url": "https://namu.wiki/w/브루노%20페르난데스", "category": "player_mun"},
    {"url": "https://namu.wiki/w/아마드%20디알로", "category": "player_mun"},
    {"url": "https://namu.wiki/w/라스무스%20회일룬", "category": "player_mun"},
    {"url": "https://namu.wiki/w/마르쿠스%20래시포드", "category": "player_mun"},
    {"url": "https://namu.wiki/w/코비%20메이누", "category": "player_mun"},
    {"url": "https://namu.wiki/w/마누엘%20우가르테", "category": "player_mun"},
]

MAX_PAGES = 30  # 더 많은 페이지 허용
BATCH_SIZE = 50


def get_supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def crawl_pages() -> list[dict]:
    """보강 대상 페이지 크롤링."""
    logger.info("=== 보강 크롤링 시작: 시드 %d개 ===", len(REINFORCE_SEEDS))

    crawler = NamuWikiDeepCrawler(max_pages=MAX_PAGES)
    try:
        results = crawler.crawl_seeds(REINFORCE_SEEDS)
    finally:
        crawler.close()

    logger.info("크롤링 완료: %d 페이지", len(results))

    # 백업
    backup_dir = os.path.join(PROJECT_ROOT, "data", "reinforcement")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"reinforce_{ts}.json")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("백업: %s", backup_path)

    return results


def delete_stale(supabase, page_titles: list[str]) -> int:
    """기존 데이터 삭제 (같은 페이지 타이틀 기준)."""
    deleted = 0
    for title in page_titles:
        for collection in ["match_context", "player_profiles"]:
            try:
                result = (
                    supabase.table("documents")
                    .delete()
                    .eq("collection", collection)
                    .eq("metadata->>page_title", title)
                    .execute()
                )
                count = len(result.data) if result.data else 0
                if count > 0:
                    logger.info("삭제: '%s' [%s] (%d docs)", title, collection, count)
                    deleted += count
            except Exception as e:
                logger.error("삭제 실패 '%s': %s", title, e)
    return deleted


def upload_pages(supabase, results: list[dict]) -> tuple[int, int]:
    """크롤링 결과 업로드. 선수 카테고리는 player_profiles 컬렉션으로."""
    success = 0
    fail = 0

    player_categories = {"player_avl", "player_mun"}

    for page in results:
        cat = page.get("category", "")
        collection = "player_profiles" if cat in player_categories else "match_context"

        for section in page["sections"]:
            content = f"# {page['title']} - {section['heading']}\n\n{section['content']}"
            row = {
                "content": content,
                "metadata": {
                    "category": cat,
                    "page_title": page["title"],
                    "section": section["heading"],
                    "source_url": page["url"],
                    "crawled_at": page["crawled_at"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "type": "context",
                },
                "collection": collection,
            }
            try:
                supabase.table("documents").insert(row).execute()
                success += 1
            except Exception as e:
                logger.error("업로드 실패: %s - %s: %s", page["title"], section["heading"], e)
                fail += 1

    return success, fail


def generate_embeddings(supabase) -> tuple[int, int]:
    """임베딩 NULL인 문서에 Voyage 임베딩 생성."""
    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if not voyage_key:
        logger.warning("VOYAGE_API_KEY 미설정")
        return 0, 0

    vo = voyageai.Client(api_key=voyage_key)

    result = (
        supabase.table("documents")
        .select("id, content")
        .is_("embedding", "null")
        .order("id")
        .execute()
    )
    docs = result.data or []
    total = len(docs)

    if total == 0:
        logger.info("임베딩 생성 필요 없음")
        return 0, 0

    logger.info("임베딩 생성 대상: %d건", total)
    success = 0
    errors = 0

    for i in range(0, total, BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        texts = [doc["content"][:8000] for doc in batch]

        try:
            response = vo.embed(texts, model="voyage-3", input_type="document")
            embeddings = response.embeddings
        except Exception as e:
            logger.error("임베딩 배치 실패: %s", e)
            errors += len(batch)
            continue

        for j, embedding in enumerate(embeddings):
            doc_id = batch[j]["id"]
            try:
                supabase.table("documents").update(
                    {"embedding": embedding}
                ).eq("id", doc_id).execute()
                success += 1
            except Exception as e:
                logger.error("임베딩 실패 (id=%s): %s", doc_id, e)
                errors += 1

        processed = min(i + BATCH_SIZE, total)
        logger.info("임베딩 진행: %d/%d", processed, total)

        if i + BATCH_SIZE < total:
            time.sleep(1)

    return success, errors


def main():
    start = time.monotonic()
    supabase = get_supabase()

    # 1. 크롤링
    results = crawl_pages()
    if not results:
        logger.error("크롤링 결과 없음")
        return

    # 2. 기존 데이터 삭제
    titles = list({p["title"] for p in results})
    logger.info("=== 기존 데이터 교체: %d개 페이지 ===", len(titles))
    deleted = delete_stale(supabase, titles)

    # 3. 업로드
    uploaded, upload_fail = upload_pages(supabase, results)
    logger.info("업로드: 성공 %d, 실패 %d", uploaded, upload_fail)

    # 4. 임베딩
    embed_ok, embed_fail = generate_embeddings(supabase)

    elapsed = time.monotonic() - start
    logger.info(
        "=== 보강 완료 (%.1f초) ===\n"
        "  크롤링: %d 페이지\n"
        "  삭제: %d docs\n"
        "  업로드: %d / 실패 %d\n"
        "  임베딩: %d / 실패 %d",
        elapsed, len(results), deleted, uploaded, upload_fail, embed_ok, embed_fail,
    )


if __name__ == "__main__":
    main()
