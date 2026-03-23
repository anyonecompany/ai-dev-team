"""play_style 보강기.

나무위키 크롤링 → 실패 시 Gemini LLM fallback으로 play_style/fun_facts 보강.
"""

import logging
import os

from src.crawlers.namuwiki_selenium import NamuWikiSeleniumCrawler

logger = logging.getLogger(__name__)


class PlayStyleEnricher:
    """선수 프로필의 play_style/fun_facts를 보강 (Selenium 기반)."""

    def __init__(self, delay: float = 2.5):
        self.crawler = NamuWikiSeleniumCrawler()
        self._gemini_client = None

    def enrich(self, players: list[dict]) -> list[dict]:
        """전체 선수 목록의 play_style/fun_facts 보강."""
        stats = {"namuwiki": 0, "llm": 0, "failed": 0, "skipped": 0}

        try:
            for i, player in enumerate(players):
                name_kr = player.get("name_kr", "")
                name_en = player.get("name_en", "")

                # 이미 보강된 경우 스킵 (play_style이 10자 이상이면 보강됨으로 간주)
                existing_ps = player.get("play_style", "")
                if existing_ps and len(existing_ps) >= 10:
                    stats["skipped"] += 1
                    logger.info(f"[{i+1}/{len(players)}] 스킵: {name_kr} (이미 보강됨)")
                    continue

                logger.info(f"[{i+1}/{len(players)}] 보강 시작: {name_kr} ({name_en})")

                # 1. 나무위키 Selenium 크롤링 시도
                result = self.crawler.crawl_player(name_kr)
                if result and result.get("play_style") and len(result["play_style"]) >= 10:
                    player["play_style"] = result["play_style"]
                    player["fun_facts"] = result.get("fun_facts", [])
                    player["one_line_summary"] = result.get(
                        "one_line_summary", player.get("one_line_summary", "")
                    )
                    player["namu_source_url"] = result.get("source_url", "")
                    player["namu_crawled"] = True
                    player["play_style_source"] = "namuwiki"
                    stats["namuwiki"] += 1
                    logger.info(f"나무위키 성공: {name_kr}")
                    continue

                # 2. LLM fallback
                logger.info(f"나무위키 실패, LLM fallback: {name_kr}")
                llm_text = self._generate_play_style_llm(player)
                if llm_text:
                    player["play_style"] = llm_text
                    player["namu_crawled"] = False
                    player["play_style_source"] = "llm_generated"
                    stats["llm"] += 1
                    logger.info(f"LLM 생성 성공: {name_kr}")
                else:
                    player["namu_crawled"] = False
                    player["play_style_source"] = "failed"
                    stats["failed"] += 1
                    logger.warning(f"보강 실패: {name_kr}")
        finally:
            self.crawler.close()

        logger.info(
            f"보강 완료: namuwiki={stats['namuwiki']}, "
            f"llm={stats['llm']}, failed={stats['failed']}, "
            f"skipped={stats['skipped']}"
        )
        return players, stats

    def _generate_play_style_llm(self, player: dict) -> str:
        """Gemini gemini-2.5-flash로 play_style 생성."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY 없음 - LLM fallback 불가")
            return ""

        try:
            if self._gemini_client is None:
                from google import genai
                self._gemini_client = genai.Client(api_key=api_key)

            prompt = (
                f"아래 축구 선수의 플레이스타일을 한국 축구 팬이 30초 안에 이해할 수 있도록 "
                f"2~3문장으로 설명해줘.\n"
                f"전문 용어 사용 시 쉬운 설명을 괄호로 병기해줘.\n\n"
                f"선수: {player['name_kr']} ({player['name_en']})\n"
                f"포지션: {player['position']}\n"
                f"팀: {player.get('team_kr', player.get('team', ''))}\n"
                f"커리어 요약: {player.get('career_summary', '')}\n"
            )

            response = self._gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text

        except Exception as e:
            logger.error(f"LLM 생성 실패: {player['name_kr']} - {e}")
            return ""
