#!/usr/bin/env python3
"""La Paz 데이터 자동 업데이트 파이프라인.

최신 시즌/팀/감독 페이지를 재크롤링하고,
Supabase에서 기존 데이터를 교체한 뒤 임베딩을 생성한다.

사용법:
    # 전체 업데이트 (크롤링 + DB 교체 + 임베딩)
    python3 scripts/auto_update.py

    # 크롤링만 (DB 업데이트 없이)
    python3 scripts/auto_update.py --crawl-only

    # 임베딩만 재생성 (이미 업로드된 데이터에 대해)
    python3 scripts/auto_update.py --embed-only

cron 예시 (매일 06:00 실행):
    0 6 * * * cd /Users/danghyeonsong/ai-dev-team/projects/lapaz-crawl-20260305170615 && /usr/local/bin/python3 scripts/auto_update.py >> logs/auto_update.log 2>&1
"""

import argparse
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
logger = logging.getLogger("auto_update")

# --- 최신 정보가 필요한 페이지들 (시즌/팀/감독 위주) ---
FRESH_SEEDS = [
    # 25-26 시즌 (매일 업데이트될 수 있는 페이지들)
    {"url": "https://namu.wiki/w/맨체스터%20유나이티드%20FC/2025-26%20시즌", "category": "season_mun"},
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC/2025-26%20시즌", "category": "season_avl"},
    {"url": "https://namu.wiki/w/프리미어%20리그/2025-26%20시즌", "category": "season"},
    # 팀 메인 페이지 (스쿼드, 최근 동향)
    {"url": "https://namu.wiki/w/맨체스터%20유나이티드%20FC", "category": "team_mun"},
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC", "category": "team_avl"},
    # 감독
    {"url": "https://namu.wiki/w/루번%20아모림", "category": "manager_mun"},
    {"url": "https://namu.wiki/w/우나이%20에메리", "category": "manager_avl"},
]

# 시드 페이지만 크롤링 (2depth 과거 시즌 유입 방지)
MAX_PAGES = 10

BATCH_SIZE = 50  # Voyage AI 임베딩 배치


def get_supabase():
    """Supabase 클라이언트 생성."""
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def crawl_fresh_pages() -> list[dict]:
    """최신 시즌/팀/감독 페이지 크롤링."""
    logger.info("=== 크롤링 시작: 시드 %d개, 최대 %d 페이지 ===", len(FRESH_SEEDS), MAX_PAGES)

    crawler = NamuWikiDeepCrawler(max_pages=MAX_PAGES)
    try:
        results = crawler.crawl_seeds(FRESH_SEEDS)
    finally:
        crawler.close()

    logger.info("크롤링 완료: %d 페이지", len(results))

    # 결과 로컬 백업
    backup_dir = os.path.join(PROJECT_ROOT, "data", "updates")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"update_{timestamp}.json")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("백업 저장: %s", backup_path)

    return results


def delete_stale_pages(supabase, page_titles: list[str]) -> int:
    """Supabase에서 재크롤링 대상 페이지의 기존 데이터를 삭제한다."""
    deleted = 0
    for title in page_titles:
        try:
            result = (
                supabase.table("documents")
                .delete()
                .eq("collection", "match_context")
                .eq("metadata->>page_title", title)
                .execute()
            )
            count = len(result.data) if result.data else 0
            if count > 0:
                logger.info("삭제: '%s' (%d docs)", title, count)
                deleted += count
        except Exception as e:
            logger.error("삭제 실패 '%s': %s", title, e)
    return deleted


def upload_fresh_pages(supabase, results: list[dict]) -> tuple[int, int]:
    """크롤링 결과를 Supabase documents에 업로드한다."""
    success = 0
    fail = 0

    for page in results:
        for section in page["sections"]:
            content = f"# {page['title']} - {section['heading']}\n\n{section['content']}"
            row = {
                "content": content,
                "metadata": {
                    "category": page["category"],
                    "page_title": page["title"],
                    "section": section["heading"],
                    "source_url": page["url"],
                    "crawled_at": page["crawled_at"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "type": "context",
                },
                "collection": "match_context",
            }
            try:
                supabase.table("documents").insert(row).execute()
                success += 1
            except Exception as e:
                logger.error("업로드 실패: %s - %s: %s", page["title"], section["heading"], e)
                fail += 1

    return success, fail


def generate_embeddings(supabase) -> tuple[int, int]:
    """임베딩이 없는 새 문서에 Voyage AI 임베딩 생성."""
    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if not voyage_key:
        logger.warning("VOYAGE_API_KEY 미설정 - 임베딩 스킵")
        return 0, 0

    vo = voyageai.Client(api_key=voyage_key)

    # 임베딩 NULL인 문서 조회
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
        logger.info("임베딩 생성 필요 없음 (모든 문서에 이미 임베딩 존재)")
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
                logger.error("임베딩 업데이트 실패 (id=%s): %s", doc_id, e)
                errors += 1

        processed = min(i + BATCH_SIZE, total)
        logger.info("임베딩 진행: %d/%d (성공: %d, 실패: %d)", processed, total, success, errors)

        if i + BATCH_SIZE < total:
            time.sleep(1)

    return success, errors


def run_full_update():
    """전체 업데이트 파이프라인 실행."""
    start_time = time.monotonic()
    supabase = get_supabase()

    # 1. 크롤링
    results = crawl_fresh_pages()
    if not results:
        logger.error("크롤링 결과 없음, 중단")
        return

    # 2. 기존 데이터 삭제 (재크롤링 대상만)
    page_titles = list({page["title"] for page in results})
    logger.info("=== 기존 데이터 교체: %d개 페이지 ===", len(page_titles))
    deleted = delete_stale_pages(supabase, page_titles)
    logger.info("삭제 완료: %d docs", deleted)

    # 3. 새 데이터 업로드
    logger.info("=== 새 데이터 업로드 ===")
    uploaded, upload_fail = upload_fresh_pages(supabase, results)
    logger.info("업로드 완료: 성공 %d, 실패 %d", uploaded, upload_fail)

    # 4. 임베딩 생성
    logger.info("=== 임베딩 생성 ===")
    embed_ok, embed_fail = generate_embeddings(supabase)
    logger.info("임베딩 완료: 성공 %d, 실패 %d", embed_ok, embed_fail)

    elapsed = time.monotonic() - start_time
    logger.info(
        "=== 전체 업데이트 완료 (%.1f초) ===\n"
        "  크롤링: %d 페이지\n"
        "  삭제: %d docs\n"
        "  업로드: %d 성공 / %d 실패\n"
        "  임베딩: %d 성공 / %d 실패",
        elapsed, len(results), deleted, uploaded, upload_fail, embed_ok, embed_fail,
    )


def main():
    parser = argparse.ArgumentParser(description="La Paz 데이터 자동 업데이트")
    parser.add_argument("--crawl-only", action="store_true", help="크롤링만 (DB 업데이트 없이)")
    parser.add_argument("--embed-only", action="store_true", help="임베딩만 재생성")
    args = parser.parse_args()

    if args.embed_only:
        logger.info("=== 임베딩만 재생성 모드 ===")
        supabase = get_supabase()
        ok, fail = generate_embeddings(supabase)
        logger.info("임베딩 완료: 성공 %d, 실패 %d", ok, fail)
    elif args.crawl_only:
        logger.info("=== 크롤링만 모드 ===")
        crawl_fresh_pages()
    else:
        run_full_update()


if __name__ == "__main__":
    main()
