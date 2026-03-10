"""딥 크롤링 실행 스크립트.

시드 URL 9개로 1depth 크롤링 → 발견 링크로 2depth 크롤링 (최대 30페이지).
결과를 data/context/ 에 카테고리별 JSON + 통합 JSON + RAG용 마크다운 생성.
크롤링 완료 후 Supabase documents 테이블에 업로드.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.config import SUPABASE_SERVICE_KEY, SUPABASE_URL
from src.crawlers.namuwiki_deep_crawler import NamuWikiDeepCrawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SEED_URLS = [
    {"url": "https://namu.wiki/w/맨체스터%20유나이티드%20FC", "category": "team_mun"},
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC", "category": "team_avl"},
    {"url": "https://namu.wiki/w/마이클%20캐릭", "category": "manager_mun"},
    {"url": "https://namu.wiki/w/우나이%20에메리", "category": "manager_avl"},
    {"url": "https://namu.wiki/w/프리미어%20리그/2025-26%20시즌", "category": "season"},
    {"url": "https://namu.wiki/w/맨체스터%20유나이티드%20FC/2025-26%20시즌", "category": "season_mun"},
    {"url": "https://namu.wiki/w/아스톤%20빌라%20FC/2025-26%20시즌", "category": "season_avl"},
    {"url": "https://namu.wiki/w/비디오%20판독", "category": "rules"},
    {"url": "https://namu.wiki/w/오프사이드", "category": "rules"},
]

CONTEXT_DIR = os.path.join(PROJECT_ROOT, "data", "context")
MARKDOWN_DIR = os.path.join(CONTEXT_DIR, "markdown")


def save_results(results: list[dict]) -> dict[str, list[dict]]:
    """카테고리별 JSON + 통합 JSON + 마크다운 저장."""
    os.makedirs(CONTEXT_DIR, exist_ok=True)
    os.makedirs(MARKDOWN_DIR, exist_ok=True)

    # 카테고리별 분류
    by_category: dict[str, list[dict]] = {}
    for page in results:
        cat = page["category"]
        by_category.setdefault(cat, []).append(page)

    # 카테고리별 JSON
    for cat, pages in by_category.items():
        path = os.path.join(CONTEXT_DIR, f"{cat}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        logger.info("저장: %s (%d 페이지)", path, len(pages))

    # 통합 JSON
    all_path = os.path.join(CONTEXT_DIR, "all_context.json")
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("통합 저장: %s (%d 페이지)", all_path, len(results))

    # RAG용 마크다운
    for page in results:
        safe_title = page["title"].replace("/", "_").replace(" ", "_")[:80]
        md_path = os.path.join(MARKDOWN_DIR, f"{safe_title}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {page['title']}\n\n")
            f.write(f"- URL: {page['url']}\n")
            f.write(f"- Category: {page['category']}\n")
            f.write(f"- Crawled: {page['crawled_at']}\n\n")
            for section in page["sections"]:
                f.write(f"## {section['heading']}\n\n")
                f.write(section["content"] + "\n\n")

    logger.info("마크다운 %d개 저장: %s", len(results), MARKDOWN_DIR)
    return by_category


def upload_to_supabase(results: list[dict]) -> tuple[int, int]:
    """크롤링 결과를 Supabase documents 테이블에 업로드."""
    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
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
                    "type": "context",
                },
                "collection": "match_context",
            }
            try:
                client.table("documents").insert(row).execute()
                success += 1
            except Exception as e:
                logger.error("Supabase 업로드 실패: %s - %s: %s", page["title"], section["heading"], e)
                fail += 1

    return success, fail


def print_report(
    results: list[dict],
    by_category: dict[str, list[dict]],
    upload_result: tuple[int, int],
) -> str:
    """크롤링 요약 리포트."""
    total_chars = sum(
        sum(len(s["content"]) for s in page["sections"])
        for page in results
    )
    total_sections = sum(len(page["sections"]) for page in results)

    lines = [
        "=" * 60,
        "딥 크롤링 리포트",
        "=" * 60,
        f"총 페이지: {len(results)}",
        f"총 섹션: {total_sections}",
        f"총 글자 수: {total_chars:,}",
        "",
        "카테고리별:",
    ]
    for cat, pages in sorted(by_category.items()):
        cat_chars = sum(
            sum(len(s["content"]) for s in p["sections"]) for p in pages
        )
        lines.append(f"  {cat}: {len(pages)} 페이지, {cat_chars:,}자")

    lines.extend([
        "",
        f"Supabase 업로드: 성공 {upload_result[0]}, 실패 {upload_result[1]}",
        "",
        "생성 파일:",
        f"  - data/context/all_context.json",
        f"  - data/context/markdown/ ({len(results)}개 .md)",
    ])
    for cat in sorted(by_category.keys()):
        lines.append(f"  - data/context/{cat}.json")

    lines.append("=" * 60)
    report = "\n".join(lines)
    print(report)
    return report


def main() -> None:
    """딥 크롤링 실행."""
    logger.info("딥 크롤링 시작: 시드 %d개, 최대 %d 페이지", len(SEED_URLS), 30)

    crawler = NamuWikiDeepCrawler(max_pages=30)
    try:
        results = crawler.crawl_seeds(SEED_URLS)
    finally:
        crawler.close()

    if not results:
        logger.error("크롤링 결과 없음")
        sys.exit(1)

    # 결과 저장
    by_category = save_results(results)

    # Supabase 업로드
    logger.info("Supabase 업로드 시작...")
    upload_result = upload_to_supabase(results)

    # 리포트
    report = print_report(results, by_category, upload_result)

    # 리포트 파일 저장
    report_path = os.path.join(CONTEXT_DIR, "crawl_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info("완료!")


if __name__ == "__main__":
    main()
