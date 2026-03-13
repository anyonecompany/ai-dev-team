"""나무위키 CSS 셀렉터 검증 스크립트"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def validate_selectors():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    try:
        url = "https://namu.wiki/w/%EB%B8%8C%EB%A3%A8%EB%85%B8%20%ED%8E%98%EB%A5%B4%EB%82%9C%EB%8D%B0%EC%8A%A4"
        print(f"접속 URL: {url}")
        driver.get(url)
        time.sleep(7)  # JS 렌더링 대기

        page_source = driver.page_source
        print(f"page_source 길이: {len(page_source)}")

        # 1. M8xPxt04 클래스 확인
        if "M8xPxt04" in page_source:
            print("\n[결과] M8xPxt04 클래스 발견!")
            elements = driver.find_elements(By.CLASS_NAME, "M8xPxt04")
            print(f"  요소 수: {len(elements)}")
            if elements:
                text = elements[0].text[:300]
                print(f"  텍스트 샘플: {text[:200]}")
        else:
            print("\n[결과] M8xPxt04 클래스 없음")

        # 2. 대안 셀렉터들 탐색
        selectors = [
            ("CSS: div.wiki-paragraph", By.CSS_SELECTOR, "div.wiki-paragraph"),
            ("CSS: article", By.CSS_SELECTOR, "article"),
            ("CSS: div.wiki-content", By.CSS_SELECTOR, "div.wiki-content"),
            ("CSS: div[class*='wiki']", By.CSS_SELECTOR, "div[class*='wiki']"),
            ("CSS: div[class*='content']", By.CSS_SELECTOR, "div[class*='content']"),
            ("CSS: div[class*='article']", By.CSS_SELECTOR, "div[class*='article']"),
            ("CSS: div[class*='body']", By.CSS_SELECTOR, "div[class*='body']"),
            ("CSS: div[class*='paragraph']", By.CSS_SELECTOR, "div[class*='paragraph']"),
            ("CSS: div[class*='text']", By.CSS_SELECTOR, "div[class*='text']"),
            ("CSS: .wiki-heading-content", By.CSS_SELECTOR, ".wiki-heading-content"),
            ("CSS: div[class*='Document']", By.CSS_SELECTOR, "div[class*='Document']"),
        ]

        print("\n--- 대안 셀렉터 탐색 ---")
        for name, by, selector in selectors:
            try:
                elements = driver.find_elements(by, selector)
                if elements:
                    total_text = sum(len(e.text) for e in elements)
                    print(f"\n[{name}] 요소 수: {len(elements)}, 총 텍스트: {total_text}자")
                    if total_text > 100:
                        sample = elements[0].text[:200] if elements[0].text else "(빈 텍스트)"
                        print(f"  샘플: {sample}")
            except Exception as e:
                print(f"\n[{name}] 에러: {e}")

        # 3. page_source에서 클래스 패턴 분석
        print("\n--- page_source 클래스 패턴 분석 ---")
        import re
        # 해시 기반 클래스명 찾기 (나무위키 CSS Modules 패턴)
        hash_classes = re.findall(r'class="([A-Za-z0-9_-]{6,20})"', page_source)
        from collections import Counter
        common = Counter(hash_classes).most_common(20)
        print("상위 20개 클래스:")
        for cls, count in common:
            print(f"  {cls}: {count}회")

        # 4. 본문 영역 구조 파악 - 큰 텍스트 블록 div
        print("\n--- 큰 텍스트 블록 div 탐색 ---")
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        big_divs = []
        for div in all_divs:
            text = div.text
            if len(text) > 1000:
                cls = div.get_attribute("class") or "(no class)"
                big_divs.append((cls, len(text)))
        big_divs.sort(key=lambda x: x[1], reverse=True)
        print(f"1000자 이상 div: {len(big_divs)}개")
        for cls, length in big_divs[:10]:
            print(f"  class='{cls}' → {length}자")

    finally:
        driver.quit()

if __name__ == "__main__":
    validate_selectors()
