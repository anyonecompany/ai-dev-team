"""나무위키 딥 크롤러 - 팀/감독/전술/시즌/규칙 데이터 수집.

시드 URL에서 시작하여 2depth까지 관련 내부 링크를 따라가며
카테고리별 컨텍스트 데이터를 수집한다.

대형 문서는 JS 비활성화 + BeautifulSoup 파싱,
소형 문서는 JS 활성화 + Selenium 텍스트 추출.
"""

import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

# 이미 확보된 선수 이름 (개인 페이지 제외용)
KNOWN_PLAYERS = [
    "오나나", "마즈라위", "데 리흐트", "리산드로 마르티네스", "달로", "에반스",
    "유로", "카세미루", "메이누", "브루노 페르난데스", "마운트", "에릭센",
    "우가르테", "콜리어", "호일룬", "가르나초", "아마드 디알로", "안토니",
    "지르크제", "래시포드", "에밀리아노 마르티네스", "올센", "캐시", "콘사",
    "토레스", "딘뉴", "카를로스", "밍스", "카마라", "티엘레만스", "맥긴",
    "로저스", "오나나", "램지", "바클리", "왓킨스", "베일리", "듀란",
    "필로제", "타운센드",
    # 영문명 변형
    "André Onana", "Noussair Mazraoui", "Matthijs de Ligt",
    "Lisandro Martínez", "Diogo Dalot", "Jonny Evans", "Leny Yoro",
    "Casemiro", "Kobbie Mainoo", "Bruno Fernandes", "Mason Mount",
    "Christian Eriksen", "Manuel Ugarte", "Toby Collyer",
    "Rasmus Højlund", "Alejandro Garnacho", "Amad Diallo", "Antony",
    "Joshua Zirkzee", "Marcus Rashford", "Emiliano Martínez",
    "Robin Olsen", "Matty Cash", "Ezri Konsa", "Pau Torres",
    "Lucas Digne", "Diego Carlos", "Tyrone Mings", "Boubacar Kamara",
    "Youri Tielemans", "John McGinn", "Morgan Rogers", "Amadou Onana",
    "Jacob Ramsey", "Ross Barkley", "Ollie Watkins", "Leon Bailey",
    "Jhon Durán", "Jaden Philogene", "Andros Townsend",
]

# 크롤링 제외 키워드 (URL or 제목에 포함되면 건너뜀)
EXCLUDE_KEYWORDS = [
    "유니폼", "마스코트", "응원가", "역대 로고", "파일:", "분류:", "틀:",
    "나무위키:", "사용자:", "토론:", "위키프로젝트:",
]

# 크롤링 포함 키워드 (내부 링크가 이 키워드 중 하나를 포함해야 2depth 대상)
INCLUDE_KEYWORDS = [
    "시즌", "전술", "감독", "이적", "스쿼드", "프리미어 리그",
    "챔피언스 리그", "성적", "역사", "라이벌", "맨체스터 유나이티드",
    "아스톤 빌라", "더비", "포메이션", "축구", "EPL",
]

# 대형 문서 카테고리 (JS 비활성화 모드)
LARGE_DOC_CATEGORIES = {"team_mun", "team_avl", "season"}


class NamuWikiDeepCrawler:
    """나무위키 딥 크롤러 - 2depth 관련 문서 수집."""

    BASE_URL = "https://namu.wiki/w/"
    SLEEP_BETWEEN = 5
    PAGE_LOAD_WAIT = 7
    MAX_RETRIES = 2
    MAX_SECTION_CHARS = 3000

    def __init__(self, max_pages: int = 30) -> None:
        self.max_pages = max_pages
        self.driver: webdriver.Chrome | None = None
        self.crawled_urls: set[str] = set()
        self.results: list[dict] = []
        self.total_chars = 0

    def _init_driver(self, disable_js: bool = False) -> None:
        """Selenium WebDriver 초기화."""
        self._close_driver()
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        if disable_js:
            opts.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.javascript": 2,
            })
        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_page_load_timeout(60)

    def _close_driver(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def close(self) -> None:
        """외부에서 드라이버를 정리할 때 호출."""
        self._close_driver()

    def crawl_seeds(self, seeds: list[dict]) -> list[dict]:
        """시드 URL에서 1depth 크롤링 후, 발견 링크로 2depth 크롤링.

        Args:
            seeds: [{"url": str, "category": str}, ...]

        Returns:
            크롤링 결과 리스트.
        """
        discovered_links: list[dict] = []

        # 1depth: 시드 크롤링
        logger.info("=== 1depth: 시드 URL %d개 크롤링 시작 ===", len(seeds))
        for seed in seeds:
            if len(self.results) >= self.max_pages:
                logger.info("최대 페이지 수 도달 (%d), 중단", self.max_pages)
                break

            url = seed["url"]
            category = seed["category"]
            use_js_disabled = any(
                category.startswith(prefix) for prefix in LARGE_DOC_CATEGORIES
            )

            result = self._crawl_page(url, category, disable_js=use_js_disabled)
            if result:
                self.results.append(result)
                self.total_chars += sum(
                    len(s["content"]) for s in result["sections"]
                )
                # 내부 링크 수집
                links = result.get("internal_links", [])
                for link in links:
                    if self._is_relevant_link(link):
                        discovered_links.append({
                            "url": link,
                            "category": self._infer_category(link, category),
                        })
                logger.info(
                    "1depth 완료: %s (%d 섹션, %d 관련 링크)",
                    result["title"],
                    len(result["sections"]),
                    len([l for l in links if self._is_relevant_link(l)]),
                )

        # 2depth: 발견 링크 크롤링
        logger.info(
            "=== 2depth: 발견 링크 %d개 중 크롤링 ===",
            len(discovered_links),
        )
        for link_info in discovered_links:
            if len(self.results) >= self.max_pages:
                logger.info("최대 페이지 수 도달 (%d), 중단", self.max_pages)
                break

            url = link_info["url"]
            if url in self.crawled_urls:
                continue

            category = link_info["category"]
            result = self._crawl_page(url, category, disable_js=False)
            if result:
                self.results.append(result)
                self.total_chars += sum(
                    len(s["content"]) for s in result["sections"]
                )
                logger.info(
                    "2depth 완료: %s (%d 섹션)", result["title"], len(result["sections"])
                )

        self._close_driver()
        logger.info(
            "크롤링 완료: %d 페이지, 총 %d자",
            len(self.results), self.total_chars,
        )
        return self.results

    def _crawl_page(
        self, url: str, category: str, disable_js: bool = False
    ) -> dict | None:
        """단일 페이지 크롤링."""
        if url in self.crawled_urls:
            return None
        self.crawled_urls.add(url)

        for attempt in range(self.MAX_RETRIES):
            try:
                # 드라이버 모드 전환 필요 여부 확인
                if self.driver is None:
                    self._init_driver(disable_js=disable_js)

                self.driver.get(url)
                time.sleep(self.PAGE_LOAD_WAIT)

                # 페이지 소스 가져오기
                page_source = self.driver.page_source
                title = self.driver.title.replace(" - 나무위키", "").strip()

                if not page_source or len(page_source) < 500:
                    logger.warning("페이지 소스 짧음: %s (attempt %d)", url, attempt + 1)
                    time.sleep(self.SLEEP_BETWEEN)
                    continue

                # BeautifulSoup 파싱
                soup = BeautifulSoup(page_source, "html.parser")
                app_div = soup.select_one("#app")
                if not app_div:
                    logger.warning("'#app' 컨테이너 없음: %s", url)
                    time.sleep(self.SLEEP_BETWEEN)
                    continue

                full_text = app_div.get_text("\n", strip=False)
                if "해당 문서를 찾을 수 없습니다" in full_text:
                    logger.warning("문서 없음: %s", url)
                    return None

                if len(full_text) < 200:
                    logger.warning("본문 짧음: %s (len=%d)", url, len(full_text))
                    time.sleep(self.SLEEP_BETWEEN)
                    continue

                # 섹션 분할
                sections = self._extract_sections(full_text)

                # 내부 링크 수집
                internal_links = self._collect_internal_links(app_div)

                time.sleep(self.SLEEP_BETWEEN)

                return {
                    "url": url,
                    "title": title or unquote(url.split("/w/")[-1]),
                    "category": category,
                    "sections": sections,
                    "internal_links": internal_links,
                    "full_text_length": len(full_text),
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.warning(
                    "크롤링 오류: %s (attempt %d): %s", url, attempt + 1, e
                )
                self._close_driver()
                time.sleep(self.SLEEP_BETWEEN)

        logger.error("크롤링 실패 (최대 재시도 초과): %s", url)
        return None

    def _extract_sections(self, full_text: str) -> list[dict]:
        """[편집] 마커 기반으로 섹션 분할.

        나무위키 구조:
        - TOC 영역에 "1. 개요" 등이 나옴 (짧은 줄)
        - 본문에서 같은 제목 + "[편집]" 패턴이 나옴 → 실제 섹션 시작
        """
        lines = full_text.split("\n")
        sections: list[dict] = []
        current_heading = "서론"
        current_lines: list[str] = []
        in_toc = True  # 초반 TOC 영역 스킵

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # [편집] 마커 발견 → 이전 줄이 섹션 제목
            if stripped == "[편집]":
                in_toc = False
                # 이전에 모은 내용 저장
                if current_lines:
                    content = "\n".join(current_lines).strip()
                    if len(content) > 30:
                        sections.append({
                            "heading": current_heading,
                            "content": content[:self.MAX_SECTION_CHARS],
                        })
                    current_lines = []

                # 바로 이전 비공백 줄이 제목
                for j in range(i - 1, max(i - 4, -1), -1):
                    prev = lines[j].strip()
                    if prev and prev != "[편집]":
                        # "1. 개요" → "개요" 로 정리
                        heading = re.sub(r"^\d+(\.\d+)*\.?\s*", "", prev).strip()
                        current_heading = heading if heading else prev
                        break
                continue

            # TOC 영역 스킵 (첫 [편집] 이전)
            if in_toc:
                continue

            # 각주/편집 마커 스킵
            if re.match(r"^\[\d+\]$", stripped):
                continue
            if stripped in ("[편집]", "[펼치기·접기]"):
                continue

            current_lines.append(stripped)

        # 마지막 섹션
        if current_lines:
            content = "\n".join(current_lines).strip()
            if len(content) > 30:
                sections.append({
                    "heading": current_heading,
                    "content": content[:self.MAX_SECTION_CHARS],
                })

        return sections

    def _collect_internal_links(self, app_div) -> list[str]:
        """BeautifulSoup에서 내부 링크 수집."""
        links = set()
        for a_tag in app_div.select("a[href^='/w/']"):
            href = a_tag.get("href", "")
            if not href or href == "/w/":
                continue
            full_url = "https://namu.wiki" + href
            # 앵커 제거
            full_url = full_url.split("#")[0]
            links.add(full_url)
        return list(links)

    def _is_relevant_link(self, url: str) -> bool:
        """2depth 크롤링 대상인지 판단."""
        decoded = unquote(url)

        # 제외 키워드 체크
        for kw in EXCLUDE_KEYWORDS:
            if kw in decoded:
                return False

        # 이미 확보된 선수 페이지 제외
        page_name = decoded.split("/w/")[-1] if "/w/" in decoded else ""
        for player in KNOWN_PLAYERS:
            if player in page_name:
                return False

        # 포함 키워드 체크
        return any(kw in decoded for kw in INCLUDE_KEYWORDS)

    def _infer_category(self, url: str, parent_category: str) -> str:
        """링크 URL에서 카테고리 추론."""
        decoded = unquote(url)
        if "맨체스터 유나이티드" in decoded:
            if "시즌" in decoded:
                return "season_mun"
            return "team_mun_related"
        if "아스톤 빌라" in decoded:
            if "시즌" in decoded:
                return "season_avl"
            return "team_avl_related"
        if "프리미어 리그" in decoded:
            return "epl"
        if "챔피언스 리그" in decoded:
            return "ucl"
        if any(kw in decoded for kw in ["전술", "포메이션"]):
            return "tactics"
        if any(kw in decoded for kw in ["감독", "코치"]):
            return "manager"
        if any(kw in decoded for kw in ["이적", "스쿼드"]):
            return "transfer"
        if "라이벌" in decoded or "더비" in decoded:
            return "rivalry"
        return f"{parent_category}_related"
