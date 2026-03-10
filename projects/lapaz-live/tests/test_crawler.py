"""크롤러 모듈 테스트."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_namuwiki_crawler_import():
    """NamuWikiCrawler 임포트 및 인스턴스 생성 테스트."""
    from src.crawlers.namuwiki import NamuWikiCrawler

    crawler = NamuWikiCrawler()
    assert crawler is not None
    assert hasattr(crawler, "crawl_player")


def test_wikipedia_fallback_crawler_import():
    """WikipediaFallbackCrawler 임포트 및 인스턴스 생성 테스트."""
    from src.crawlers.wikipedia_fallback import WikipediaFallbackCrawler

    crawler = WikipediaFallbackCrawler()
    assert crawler is not None
    assert hasattr(crawler, "crawl_player")


@pytest.mark.slow
def test_wikipedia_crawl_bruno():
    """WikipediaFallbackCrawler로 Bruno Fernandes 검색 테스트 (네트워크 필요)."""
    from src.crawlers.wikipedia_fallback import WikipediaFallbackCrawler

    crawler = WikipediaFallbackCrawler()
    result = crawler.crawl_player("Bruno Fernandes")
    assert result is not None
    assert len(result) > 0
