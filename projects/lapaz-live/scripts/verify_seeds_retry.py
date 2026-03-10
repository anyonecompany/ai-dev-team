"""team_mun, team_avl 재시도 - 타임아웃 증가"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
import time
import json

opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--disable-javascript")  # JS 비활성화로 빠른 로딩
opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=opts)
driver.set_page_load_timeout(60)  # 60초로 증가

urls = [
    ("https://namu.wiki/w/" + quote("맨체스터 유나이티드 FC"), "team_mun"),
    ("https://namu.wiki/w/" + quote("아스톤 빌라 FC"), "team_avl"),
]

for url, cat in urls:
    try:
        print(f"\n--- [{cat}] 시도 (JS 비활성화): {url}")
        driver.get(url)
        time.sleep(5)

        final_url = driver.current_url
        print(f"  최종 URL: {final_url}")

        page_source = driver.page_source
        if "해당 문서를 찾을 수 없습니다" in page_source:
            print(f"  X 문서 없음")
        else:
            # JS 비활성화 상태이므로 page_source에서 h2 텍스트 추출
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
            h3s = [h.get_text(strip=True) for h in soup.find_all("h3")]
            title_el = soup.find("h1")
            title = title_el.get_text(strip=True) if title_el else ""
            print(f"  OK - 제목: {title}")
            print(f"  h2 ({len(h2s)}개): {h2s[:15]}")
            print(f"  h3 ({len(h3s)}개): {h3s[:15]}")

    except Exception as e:
        print(f"  오류: {e}")

    time.sleep(3)

driver.quit()
