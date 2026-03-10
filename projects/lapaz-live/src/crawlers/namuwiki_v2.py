"""나무위키 선수 프로필 크롤러 v2.

/w/ HTML SSR 페이지를 파싱하여 플레이 스타일 정보를 추출.
패턴 A: 메인 문서 내 인라인 섹션
패턴 B: 별도 하위 문서 (/선수명/플레이 스타일)
"""

import logging
import re
import time
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PLAY_STYLE_KEYWORDS = ["플레이 스타일", "플레이스타일", "선수 특성"]
FUN_FACT_KEYWORDS = ["별명", "여담", "사건사고", "평가", "이야기거리"]


class NamuWikiCrawlerV2:
    """나무위키 /w/ HTML SSR 기반 크롤러."""

    BASE_URL = "https://namu.wiki/w/"

    def __init__(self, delay: float = 2.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._last_request_time: float = 0.0

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def _fetch(self, url: str) -> requests.Response | None:
        self._wait()
        try:
            resp = self.session.get(url, timeout=15)
            self._last_request_time = time.time()
            if resp.status_code == 200:
                return resp
            logger.warning(f"HTTP {resp.status_code}: {url}")
        except requests.RequestException as e:
            self._last_request_time = time.time()
            logger.warning(f"요청 실패: {url} - {e}")
        return None

    def crawl_player(self, name_kr: str) -> dict | None:
        """나무위키에서 선수 플레이스타일 정보 크롤링."""
        encoded = quote(name_kr, safe="")
        url = self.BASE_URL + encoded
        logger.info(f"크롤링 시도: {name_kr} -> {url}")

        resp = self._fetch(url)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        source_url = url

        # 플레이 스타일 추출
        play_style_text = ""
        sub_doc_href = self._find_sub_doc_link(soup, name_kr)

        if sub_doc_href:
            # 패턴 B: 별도 하위 문서
            sub_url = "https://namu.wiki" + sub_doc_href
            logger.info(f"하위 문서 크롤링: {sub_url}")
            sub_resp = self._fetch(sub_url)
            if sub_resp:
                play_style_text = self._extract_full_page_text(sub_resp.text)
                source_url = sub_url

        if not play_style_text:
            # 패턴 A: 메인 문서 내 인라인 섹션
            play_style_text = self._extract_section_text(resp.text, PLAY_STYLE_KEYWORDS)

        if not play_style_text or len(play_style_text) < 30:
            logger.warning(f"플레이스타일 콘텐츠 부족: {name_kr}")
            return None

        # fun_facts 추출 (여담/별명 섹션)
        fun_facts_text = self._extract_section_text(resp.text, FUN_FACT_KEYWORDS)
        fun_facts = self._split_fun_facts(fun_facts_text) if fun_facts_text else []

        # 한줄 요약 생성
        one_line = play_style_text[:150].split(".")[0] + "." if play_style_text else ""

        result = {
            "play_style": play_style_text[:3000],
            "fun_facts": fun_facts[:10],
            "one_line_summary": one_line[:200],
            "source_url": source_url,
        }
        logger.info(f"크롤링 성공: {name_kr} (play_style: {len(play_style_text)}자)")
        return result

    def _find_sub_doc_link(self, soup: BeautifulSoup, name_kr: str) -> str | None:
        """h2 헤딩에서 플레이 스타일 하위 문서 링크 탐색."""
        for h2 in soup.find_all("h2"):
            text = h2.get_text(strip=True)
            if any(kw.replace(" ", "") in text.replace(" ", "") for kw in PLAY_STYLE_KEYWORDS):
                # 헤딩 내 링크에서 하위 문서 참조 확인
                for a in h2.find_all("a"):
                    href = a.get("href", "")
                    decoded = unquote(href)
                    if "플레이" in decoded and "/w/" in decoded:
                        return href
        return None

    def _extract_section_text(self, html: str, keywords: list[str]) -> str:
        """HTML에서 특정 키워드를 가진 h2 섹션의 텍스트를 추출."""
        # h2 heading의 span id로 섹션 시작점 찾기
        for kw in keywords:
            pattern = f"<span id='{kw}'"
            idx = html.find(pattern)
            if idx < 0:
                pattern = f'<span id="{kw}"'
                idx = html.find(pattern)
            if idx >= 0:
                # h2 끝 찾기
                h2_end = html.find("</h2>", idx)
                if h2_end < 0:
                    continue
                # 다음 h2 찾기
                next_h2 = html.find("<h2", h2_end + 5)
                if next_h2 < 0:
                    next_h2 = len(html)

                section_html = html[h2_end + 5 : next_h2]
                soup = BeautifulSoup(section_html, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                lines = [
                    l.strip()
                    for l in text.split("\n")
                    if len(l.strip()) > 10
                ]
                return "\n".join(lines)
        return ""

    def _extract_full_page_text(self, html: str) -> str:
        """하위 문서 전체 텍스트 추출 (헤딩 제외, 본문만)."""
        soup = BeautifulSoup(html, "html.parser")
        # 나무위키 본문 텍스트 추출
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 15]

        # 네비게이션/메타 라인 제거
        skip_prefixes = [
            "나무위키", "최근 변경", "편집 요청", "이용중인 IP",
            "사유:", "편집 권한", "문서 역사", "토론",
            "(이 메세지는", "로그인이 필요합니다", "로그인 허용",
        ]
        filtered = []
        started = False
        for line in lines:
            if any(line.startswith(p) for p in skip_prefixes):
                continue
            # 목차/편집 링크 제거
            if re.match(r"^\d+\.\s", line) and len(line) < 50:
                continue
            if "[편집]" in line:
                started = True
                continue
            # 문서 메타 정보 제거
            if "문서를 참고하십시오" in line or "서술하는 문서" in line:
                continue
            if "#" in line and len(line) < 40:
                continue
            if started or len(line) > 30:
                started = True
                filtered.append(line)

        return "\n".join(filtered)

    def _split_fun_facts(self, text: str) -> list[str]:
        """여담 텍스트를 개별 항목으로 분리."""
        if not text:
            return []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        facts = []
        for s in sentences:
            s = s.strip()
            if len(s) > 15 and len(s) < 300:
                facts.append(s)
        return facts[:10]
