"""나무위키 선수 프로필 크롤러.

나무위키 raw 마크업 API를 사용하여 선수 프로필을 크롤링.
차단 시 None 반환 (위키피디아 fallback에 의존).
"""

import logging
import re
import time
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class NamuWikiCrawler:
    """나무위키 선수 프로필 크롤러."""

    RAW_URL = "https://namu.wiki/raw/"

    def __init__(self, delay: float = 2.5, user_agent: str = "AnyOneCompany-Research/1.0"):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last_request_time: float = 0.0

    def _wait(self) -> None:
        """요청 간 딜레이 적용."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def crawl_player(self, name_kr: str, name_en: str, max_retries: int = 3) -> dict | None:
        """선수 한글명으로 나무위키 크롤링. 실패 시 None 반환."""
        url = self.RAW_URL + quote(name_kr, safe="")
        logger.info(f"크롤링 시도: {name_kr} ({name_en}) -> {url}")

        for attempt in range(1, max_retries + 1):
            self._wait()
            try:
                resp = self.session.get(url, timeout=15)
                self._last_request_time = time.time()

                if resp.status_code == 200:
                    raw_text = resp.text
                    parsed = self._parse_raw(raw_text, name_kr)
                    if parsed:
                        logger.info(f"크롤링 성공: {name_kr}")
                        return parsed
                    logger.warning(f"파싱 결과 없음: {name_kr}")
                    return None

                if resp.status_code == 404:
                    logger.warning(f"문서 없음 (404): {name_kr}")
                    return None

                logger.warning(
                    f"HTTP {resp.status_code} (시도 {attempt}/{max_retries}): {name_kr}"
                )
            except requests.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt}/{max_retries}): {name_kr} - {e}")

        logger.error(f"최대 재시도 초과: {name_kr}")
        return None

    def _is_js_antibot(self, text: str) -> bool:
        """JS anti-scraping 응답인지 판별."""
        js_indicators = [
            "localStorage.getItem",
            "document.onreadystatechange",
            "theseed_settings",
            "function(){",
            "JSON.parse(",
            "window.__NUXT__",
            "<script>",
        ]
        return any(indicator in text for indicator in js_indicators)

    def _has_valid_content(self, parsed: dict) -> bool:
        """파싱 결과에 실제 유의미한 콘텐츠가 있는지 검증."""
        overview = parsed.get("overview", "")
        career = parsed.get("career_text", "")
        play_style = parsed.get("play_style_text", "")
        first_para = parsed.get("first_paragraph", "")

        # 주요 필드 중 하나라도 100자 이상이면 유효
        meaningful_text = overview + career + play_style + first_para
        if len(meaningful_text) < 100:
            return False

        # JS 코드가 섞여 있으면 무효
        if self._is_js_antibot(meaningful_text):
            return False

        return True

    def _parse_raw(self, raw_text: str, name_kr: str) -> dict | None:
        """나무위키 raw 마크업에서 선수 정보 추출."""
        if not raw_text or len(raw_text) < 50:
            return None

        # JS anti-scraping 응답 감지
        if self._is_js_antibot(raw_text):
            logger.warning(f"JS anti-scraping 감지: {name_kr}")
            return None

        # 나무위키 마크업 정리
        cleaned = self._clean_markup(raw_text)

        # 섹션 분리
        sections = self._extract_sections(raw_text)

        # 경력/플레이스타일 추출
        career = sections.get("선수 경력", sections.get("경력", ""))
        play_style = sections.get("플레이 스타일", sections.get("플레이스타일", ""))
        overview = sections.get("개요", "")

        # 첫 문단을 요약으로 사용
        first_paragraph = ""
        for line in cleaned.split("\n"):
            line = line.strip()
            if len(line) > 30:
                first_paragraph = line
                break

        result = {
            "source": "namuwiki",
            "name_kr": name_kr,
            "raw_text": cleaned[:5000],
            "overview": overview[:1000],
            "career_text": career[:2000],
            "play_style_text": play_style[:2000],
            "first_paragraph": first_paragraph[:500],
            "sections": list(sections.keys()),
        }

        if not self._has_valid_content(result):
            logger.warning(f"유효 콘텐츠 부족 (100자 미만 또는 JS 포함): {name_kr}")
            return None

        return result

    def _clean_markup(self, text: str) -> str:
        """나무위키 마크업을 텍스트로 정리."""
        # 매크로/틀 제거
        text = re.sub(r"\[include\([^\)]*\)\]", "", text)
        text = re.sub(r"\[ruby\(([^,]*),.*?\)\]", r"\1", text)
        # 링크 처리: [[문서|표시]] -> 표시, [[문서]] -> 문서
        text = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", text)
        text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
        # 볼드/이탤릭
        text = re.sub(r"'''(.*?)'''", r"\1", text)
        text = re.sub(r"''(.*?)''", r"\1", text)
        # 각주
        text = re.sub(r"\[\*[^\]]*\]", "", text)
        # 이미지/파일
        text = re.sub(r"\[\[파일:[^\]]*\]\]", "", text)
        text = re.sub(r"\[\[file:[^\]]*\]\]", "", text, flags=re.IGNORECASE)
        # 테이블 마크업
        text = re.sub(r"\|\|[^\n]*\|\|", "", text)
        # HTML 태그
        text = re.sub(r"<[^>]+>", "", text)
        # 매크로
        text = re.sub(r"\[(?:date|datetime|age|dday|br|clearfix)\]", "", text)
        # 연속 공백/빈줄 정리
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_sections(self, raw_text: str) -> dict[str, str]:
        """나무위키 마크업에서 섹션별 텍스트 추출."""
        sections: dict[str, str] = {}
        # 나무위키 제목: == 제목 ==, === 소제목 === 등
        pattern = re.compile(r"^(={2,})\s*(.+?)\s*\1\s*$", re.MULTILINE)
        matches = list(pattern.finditer(raw_text))

        for i, match in enumerate(matches):
            title = match.group(2).strip()
            # 링크 마크업 제거
            title = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", title)
            title = re.sub(r"\[\[([^\]]*)\]\]", r"\1", title)
            title = re.sub(r"#s-[\d.]+\s*", "", title).strip()

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            content = self._clean_markup(raw_text[start:end]).strip()

            if title and content:
                sections[title] = content

        return sections
