"""나무위키 본문 구조 심층 분석"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def analyze():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    try:
        url = "https://namu.wiki/w/%EB%B8%8C%EB%A3%A8%EB%85%B8%20%ED%8E%98%EB%A5%B4%EB%82%9C%EB%8D%B0%EC%8A%A4"
        driver.get(url)
        time.sleep(7)

        # 1. 본문 컨테이너 후보 - 클래스 구조 탐색
        # 최상위 큰 div의 자식 구조 파악
        print("=== 최상위 본문 컨테이너 구조 분석 ===")

        # data-* 속성으로 찾기
        data_attrs = driver.find_elements(By.CSS_SELECTOR, "[data-content]")
        print(f"[data-content] 요소: {len(data_attrs)}")

        # role 속성으로 찾기
        for role in ["main", "article", "content"]:
            els = driver.find_elements(By.CSS_SELECTOR, f"[role='{role}']")
            if els:
                print(f"[role='{role}'] 요소: {len(els)}, text len: {len(els[0].text)}")

        # 2. 태그 기반 접근
        for tag in ["article", "main", "section", "p"]:
            els = driver.find_elements(By.TAG_NAME, tag)
            if els:
                total = sum(len(e.text) for e in els)
                print(f"<{tag}> 요소: {len(els)}개, 총 텍스트: {total}자")
                if els[0].text:
                    print(f"  첫번째 샘플: {els[0].text[:150]}")

        # 3. h2/h3 heading으로 섹션 구조 파악
        print("\n=== 헤딩 구조 ===")
        for tag in ["h1", "h2", "h3", "h4"]:
            headings = driver.find_elements(By.TAG_NAME, tag)
            if headings:
                texts = [h.text.strip() for h in headings[:10] if h.text.strip()]
                print(f"<{tag}> {len(headings)}개: {texts}")

        # 4. 본문 텍스트 추출 시도 - body > div 구조
        print("\n=== XPath 기반 본문 추출 시도 ===")

        # namu wiki는 보통 #app 아래에 렌더링
        app = driver.find_elements(By.CSS_SELECTOR, "#app")
        if app:
            print(f"#app 발견, text len: {len(app[0].text)}")

        root = driver.find_elements(By.CSS_SELECTOR, "#root")
        if root:
            print(f"#root 발견, text len: {len(root[0].text)}")

        # 5. 특정 클래스 직접 테스트 (1차 분석에서 발견된 큰 텍스트 블록)
        print("\n=== 1차 발견 클래스 직접 테스트 ===")
        test_classes = [
            "jvLk9gOU", "FWrkUxcB", "YWBPIqb2", "_0giB6pmk",
            "LE4bGlEn", "Wnk0u5KY", "johmgJAc", "_3Dg5oyw8",
            "TkCBXDUv", "IwcK+ZaJ"
        ]
        for cls in test_classes:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, f".{cls}" if not cls.startswith("_") else f"[class*='{cls}']")
                if els:
                    print(f"  .{cls}: {len(els)}개, text={len(els[0].text)}자")
            except:
                pass

        # 6. 안정적인 셀렉터 - 구조적 접근
        print("\n=== 구조적 셀렉터 테스트 ===")

        # namu.wiki 특유 구조: 본문은 보통 특정 div 안에 p 태그 또는 인라인 텍스트
        # body의 직접적 텍스트가 아니라 깊은 중첩 구조

        # XPath: 텍스트가 긴 말단 div 찾기
        all_p = driver.find_elements(By.TAG_NAME, "p")
        print(f"<p> 태그: {len(all_p)}개")
        if all_p:
            for i, p in enumerate(all_p[:5]):
                if p.text:
                    print(f"  p[{i}]: {p.text[:100]}")

        # dl/dd 태그 (나무위키 프로필 영역)
        dls = driver.find_elements(By.TAG_NAME, "dl")
        print(f"\n<dl> 태그: {len(dls)}개")

        # span 태그 중 텍스트가 있는 것들
        spans = driver.find_elements(By.TAG_NAME, "span")
        text_spans = [s for s in spans if len(s.text) > 50]
        print(f"<span> (50자+): {len(text_spans)}개")

        # 7. 핵심: page_source에서 본문 마커 찾기
        print("\n=== page_source 본문 마커 분석 ===")
        ps = driver.page_source
        # "플레이 스타일" 텍스트 주변 HTML 구조 확인
        idx = ps.find("플레이 스타일")
        if idx >= 0:
            snippet = ps[max(0,idx-300):idx+200]
            print(f"'플레이 스타일' 주변 HTML:\n{snippet}")
        else:
            # 다른 한글 키워드 시도
            for kw in ["개요", "선수 경력", "소속"]:
                idx = ps.find(kw)
                if idx >= 0:
                    snippet = ps[max(0,idx-300):idx+200]
                    print(f"'{kw}' 주변 HTML:\n{snippet[:400]}")
                    break

    finally:
        driver.quit()

if __name__ == "__main__":
    analyze()
