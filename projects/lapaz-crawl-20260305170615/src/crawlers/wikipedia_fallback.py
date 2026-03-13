"""영문 위키피디아 API를 사용한 선수 프로필 수집 (fallback).

나무위키 크롤링 실패 시 영문 위키피디아에서 선수 정보를 수집한다.
API 엔드포인트:
- 요약: https://en.wikipedia.org/api/rest_v1/page/summary/{title}
- 검색: https://en.wikipedia.org/w/api.php?action=opensearch&search={name}
"""

from __future__ import annotations

import logging
import time

import requests

from src.config import USER_AGENT as DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
SEARCH_URL = "https://en.wikipedia.org/w/api.php"


class WikipediaFallbackCrawler:
    """위키피디아 REST / opensearch API를 사용한 선수 프로필 수집."""

    def __init__(self, delay: float = 1.0, user_agent: str = DEFAULT_USER_AGENT):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    # ── public ────────────────────────────────────────────

    def crawl_player(self, name_en: str) -> dict | None:
        """영문 이름으로 위키피디아 요약 크롤링.

        Args:
            name_en: 선수 영문 이름 (예: "Bruno Fernandes")

        Returns:
            요약 dict (extract, description, thumbnail 등) 또는 None.
        """
        title = self.search_player(name_en)
        if title is None:
            # 검색 실패 시 이름 그대로 시도
            title = name_en.replace(" ", "_")

        url = SUMMARY_URL + requests.utils.quote(title, safe="")
        try:
            time.sleep(self.delay)
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning("Wikipedia summary %s → HTTP %s", title, resp.status_code)
                return None

            data = resp.json()
            result: dict = {
                "title": data.get("title", ""),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
                "thumbnail_url": (data.get("thumbnail") or {}).get("source"),
                "page_url": (data.get("content_urls") or {}).get("desktop", {}).get("page"),
                "source": "wikipedia",
            }
            if not result["extract"]:
                logger.warning("Wikipedia: empty extract for %s", title)
                return None
            return result
        except requests.RequestException as exc:
            logger.error("Wikipedia request failed for %s: %s", title, exc)
            return None

    def search_player(self, name_en: str) -> str | None:
        """위키피디아 opensearch API로 정확한 페이지 제목을 찾는다.

        "(footballer)" 가 포함된 결과를 우선 선택한다.

        Args:
            name_en: 선수 영문 이름.

        Returns:
            위키피디아 페이지 제목 또는 None.
        """
        params = {
            "action": "opensearch",
            "search": name_en,
            "limit": "10",
            "namespace": "0",
            "format": "json",
        }
        try:
            time.sleep(self.delay)
            resp = self.session.get(SEARCH_URL, params=params, timeout=15)
            if resp.status_code != 200:
                return None
            data = resp.json()
            # opensearch returns [query, [titles], [descriptions], [urls]]
            if len(data) < 2 or not data[1]:
                return None

            titles: list[str] = data[1]

            # 축구선수 관련 결과 우선
            for t in titles:
                lower = t.lower()
                if "footballer" in lower or "soccer" in lower:
                    logger.info("Wikipedia search '%s' → '%s' (footballer match)", name_en, t)
                    return t

            # 첫 번째 결과 반환
            logger.info("Wikipedia search '%s' → '%s' (first result)", name_en, titles[0])
            return titles[0]
        except requests.RequestException as exc:
            logger.error("Wikipedia search failed for %s: %s", name_en, exc)
            return None
