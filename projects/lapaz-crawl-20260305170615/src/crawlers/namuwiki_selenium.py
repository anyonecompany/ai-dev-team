"""나무위키 Selenium 크롤러 - #app + h2 기반.

JS 렌더링이 필요한 나무위키 페이지를 Selenium으로 크롤링하여
플레이 스타일 정보를 추출한다.

한국어 약칭 → 나무위키 문서명 매핑 + 검색 fallback 포함.
"""

import logging
import re
import time
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

# 한국어 약칭 → 나무위키 문서 제목 매핑
NAMU_NAME_MAP: dict[str, list[str]] = {
    "데 리흐트": ["마테이스 더 리흐트", "마타이스 데 리흐트"],
    "달로": ["디오구 달로트", "디오고 달로트"],
    "에반스": ["조니 에반스"],
    "유로": ["레니 요로"],
    "마운트": ["메이슨 마운트"],
    "콜리어": ["토비 콜리어"],
    "안토니": ["안토니(축구 선수)", "안토니 산투스"],
    "캐시": ["매티 캐시"],
    "토레스": ["파우 토레스"],
    "딘뉴": ["뤼카 디뉴", "루카스 디뉴"],
    "카를로스": ["디에고 카를로스", "디에고 카를루스"],
    "밍스": ["타이론 밍스"],
    "카마라": ["부바카르 카마라"],
    "티엘레만스": ["유리 틸레만스", "유리 틸레만"],
    "로저스": ["모건 로저스"],
    "램지": ["제이컵 램지", "제이콥 램지"],
    "바클리": ["로스 바클리"],
    "왓킨스": ["올리 왓킨스"],
    "베일리": ["레온 베일리"],
    "듀란": ["혼 두란", "존 두란"],
    "필로제": ["제이든 필로전", "제이든 필로제"],
    "타운센드": ["안드로스 타운센드"],
}


class NamuWikiSeleniumCrawler:
    """나무위키 Selenium 기반 크롤러."""

    BASE_URL = "https://namu.wiki/w/"
    SEARCH_URL = "https://namu.wiki/search/"
    SLEEP_BETWEEN = 3
    PAGE_LOAD_WAIT = 7
    MAX_RETRIES = 2

    def __init__(self) -> None:
        self.driver: webdriver.Chrome | None = None

    def _init_driver(self) -> None:
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

    def crawl_player(self, name_kr: str) -> dict | None:
        """나무위키에서 선수 페이지를 크롤링하여 플레이스타일 추출."""
        # 시도할 이름 목록: 매핑된 이름들 + 원래 이름
        names_to_try = NAMU_NAME_MAP.get(name_kr, []) + [name_kr]

        for try_name in names_to_try:
            result = self._try_crawl(try_name)
            if result:
                logger.info(f"성공: {name_kr} (문서명: {try_name})")
                return result
            logger.info(f"시도 실패: {name_kr} -> {try_name}")

        # 검색 fallback
        search_result = self._search_and_crawl(name_kr)
        if search_result:
            return search_result

        return None

    def _try_crawl(self, name: str) -> dict | None:
        """단일 이름으로 크롤링 시도."""
        url = self.BASE_URL + quote(name, safe="")

        for attempt in range(self.MAX_RETRIES):
            try:
                if not self.driver:
                    self._init_driver()
                self.driver.get(url)
                time.sleep(self.PAGE_LOAD_WAIT)

                full_text = self.driver.find_element(By.CSS_SELECTOR, "#app").text

                # 문서 없음 체크
                if "해당 문서를 찾을 수 없습니다" in full_text:
                    return None

                if not full_text or len(full_text) < 200:
                    logger.warning(f"본문 짧음: {name} (len={len(full_text) if full_text else 0})")
                    time.sleep(self.SLEEP_BETWEEN)
                    continue

                play_style = self._extract_play_style(full_text)
                fun_facts = self._extract_fun_facts(full_text)
                one_line = play_style[:150].split(".")[0] + "." if play_style else ""

                time.sleep(self.SLEEP_BETWEEN)

                return {
                    "full_text": full_text[:5000],
                    "play_style": play_style,
                    "fun_facts": fun_facts,
                    "one_line_summary": one_line[:200],
                    "source_url": url,
                    "success": True,
                }
            except Exception as e:
                logger.warning(f"크롤링 오류: {name} (attempt {attempt + 1}): {e}")
                self._close_driver()
                time.sleep(self.SLEEP_BETWEEN)

        return None

    def _search_and_crawl(self, name_kr: str) -> dict | None:
        """나무위키 검색으로 선수 문서를 찾아 크롤링."""
        search_query = f"{name_kr} 축구"
        search_url = self.SEARCH_URL + quote(search_query, safe="")

        try:
            if not self.driver:
                self._init_driver()
            self.driver.get(search_url)
            time.sleep(self.PAGE_LOAD_WAIT)

            # 검색 결과에서 첫 번째 링크 찾기
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='/w/']")
            for link in links[:5]:
                href = link.get_attribute("href") or ""
                link_text = link.text.strip()
                if not link_text or len(link_text) < 2:
                    continue
                # 축구 선수 관련 문서인지 확인
                if any(kw in link_text for kw in ["축구", name_kr]):
                    logger.info(f"검색 결과에서 발견: {link_text} -> {href}")
                    self.driver.get(href)
                    time.sleep(self.PAGE_LOAD_WAIT)

                    full_text = self.driver.find_element(By.CSS_SELECTOR, "#app").text
                    if "해당 문서를 찾을 수 없습니다" in full_text:
                        continue
                    if len(full_text) < 200:
                        continue

                    play_style = self._extract_play_style(full_text)
                    fun_facts = self._extract_fun_facts(full_text)
                    one_line = play_style[:150].split(".")[0] + "." if play_style else ""

                    time.sleep(self.SLEEP_BETWEEN)
                    return {
                        "full_text": full_text[:5000],
                        "play_style": play_style,
                        "fun_facts": fun_facts,
                        "one_line_summary": one_line[:200],
                        "source_url": href,
                        "success": True,
                    }
        except Exception as e:
            logger.warning(f"검색 크롤링 실패: {name_kr}: {e}")
            self._close_driver()

        return None

    def _extract_play_style(self, full_text: str) -> str:
        """나무위키 페이지에서 '플레이 스타일' 섹션 본문을 추출.

        구조: TOC에 "3. 플레이 스타일" 나오고, 본문에서 같은 제목 + "[편집]" 패턴으로 시작됨.
        "[편집]" 마커가 있는 실제 섹션만 캡처한다.
        """
        style_keywords = [
            "플레이 스타일", "플레이스타일", "선수 특성", "선수 특징", "경기 스타일",
        ]
        end_keywords = [
            "기록", "수상", "여담", "사건", "논란", "이적", "통계",
            "둘러보기", "역대", "경력", "같이 보기",
        ]
        skip_patterns = [
            "[편집]", "자세한 내용은", "문서를 참고하십시오",
        ]

        lines = full_text.split("\n")
        capturing = False
        found_edit_marker = False
        captured: list[str] = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 섹션 시작 감지: 키워드 포함 + 바로 다음에 "[편집]" 있어야 실제 섹션
            if not capturing and any(kw in stripped for kw in style_keywords) and len(stripped) < 30:
                # 다음 비공백 줄이 "[편집]"인지 확인
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line == "[편집]":
                        capturing = True
                        found_edit_marker = True
                        break
                    if next_line:
                        break
                continue

            if not capturing:
                continue

            # "[편집]" 마커 건너뛰기
            if stripped == "[편집]":
                continue

            # 하위 섹션 제목 (3.1. 첼시 시절 등) 건너뛰기
            if re.match(r"^\d+\.\d+\.?\s", stripped) and len(stripped) < 40:
                continue

            # 상위 섹션 변경 감지 (4. 기록 등) → 중단
            if re.match(r"^\d+\.?\s", stripped) and len(stripped) < 30:
                if any(ek in stripped for ek in end_keywords):
                    break

            # 스킵 패턴
            if any(sp in stripped for sp in skip_patterns):
                continue

            # 각주 번호만 있는 줄 스킵
            if re.match(r"^\[\d+\]$", stripped):
                continue

            # 실제 콘텐츠 캡처 (20자 이상인 줄만)
            if len(stripped) > 20:
                captured.append(stripped)

        if captured:
            return " ".join(captured[:25])

        # fallback: 개요 섹션에서 추출
        capturing = False
        result: list[str] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "개요" in stripped and len(stripped) < 20:
                # 다음 줄이 "[편집]"인지 확인
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip() == "[편집]":
                        capturing = True
                        break
                    if lines[j].strip():
                        break
                continue
            if capturing and re.match(r"^\d+\.?\s", stripped) and len(stripped) < 20:
                break
            if capturing and stripped and stripped != "[편집]" and len(stripped) > 10:
                result.append(stripped)
                if len(result) >= 5:
                    break

        return " ".join(result) if result else ""

    def _extract_fun_facts(self, full_text: str) -> list[str]:
        """여담/기타 섹션에서 재미있는 사실 추출."""
        facts: list[str] = []

        # 별명 패턴
        nickname_patterns = [
            r"별명[은는이가]?\s*[\"']?([^\"'\.]{2,30})[\"']?",
            r"별칭[은는이가]?\s*[\"']?([^\"'\.]{2,30})[\"']?",
            r"애칭[은는이가]?\s*[\"']?([^\"'\.]{2,30})[\"']?",
        ]
        for pat in nickname_patterns:
            for m in re.findall(pat, full_text)[:2]:
                facts.append(f"별명: {m.strip()}")

        # 여담 섹션
        lines = full_text.split("\n")
        capturing = False
        for line in lines:
            s = line.strip()
            if ("여담" in s or "기타" in s) and len(s) < 15:
                capturing = True
                continue
            if capturing and re.match(r"^\d+\.?\s", s) and len(s) < 20:
                break
            if capturing and s and 10 < len(s) < 100 and s != "[편집]":
                facts.append(s)
                if len(facts) >= 5:
                    break

        return facts[:5]
