"""시드 URL 검증 스크립트 - 나무위키 9개 페이지 접속 및 섹션 구조 파악"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
import time
import json

# headless Chrome 설정
opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=opts)
driver.set_page_load_timeout(30)

# 검증할 URL 목록 (대안 URL 포함)
urls_to_check = [
    {
        "id": "team_mun",
        "urls": ["https://namu.wiki/w/" + quote("맨체스터 유나이티드 FC")],
        "desc": "맨체스터 유나이티드 FC"
    },
    {
        "id": "team_avl",
        "urls": ["https://namu.wiki/w/" + quote("아스톤 빌라 FC")],
        "desc": "아스톤 빌라 FC"
    },
    {
        "id": "manager_mun",
        "urls": [
            "https://namu.wiki/w/" + quote("마이클 캐릭"),
            "https://namu.wiki/w/" + quote("마이클 카릭"),
            "https://namu.wiki/w/" + quote("루벤 아모림"),
        ],
        "desc": "맨유 감독"
    },
    {
        "id": "manager_avl",
        "urls": ["https://namu.wiki/w/" + quote("우나이 에메리")],
        "desc": "우나이 에메리"
    },
    {
        "id": "season",
        "urls": [
            "https://namu.wiki/w/" + quote("프리미어 리그/2025-26 시즌"),
            "https://namu.wiki/w/" + quote("프리미어리그/2025-26 시즌"),
        ],
        "desc": "프리미어 리그 2025-26 시즌"
    },
    {
        "id": "season_mun",
        "urls": [
            "https://namu.wiki/w/" + quote("맨체스터 유나이티드 FC/2025-26 시즌"),
        ],
        "desc": "맨유 2025-26 시즌"
    },
    {
        "id": "season_avl",
        "urls": [
            "https://namu.wiki/w/" + quote("아스톤 빌라 FC/2025-26 시즌"),
        ],
        "desc": "아스톤 빌라 2025-26 시즌"
    },
    {
        "id": "rules_var",
        "urls": [
            "https://namu.wiki/w/" + quote("비디오 판독"),
            "https://namu.wiki/w/VAR",
            "https://namu.wiki/w/" + quote("비디오 보조 심판"),
        ],
        "desc": "VAR/비디오 판독"
    },
    {
        "id": "rules_offside",
        "urls": ["https://namu.wiki/w/" + quote("오프사이드")],
        "desc": "오프사이드"
    },
]

results = {}

for item in urls_to_check:
    cat_id = item["id"]
    found = False

    for url in item["urls"]:
        try:
            print(f"\n--- [{cat_id}] 시도: {url}")
            driver.get(url)
            time.sleep(7)

            # 페이지 존재 여부 확인
            body_text = driver.find_element(By.CSS_SELECTOR, "#app").text
            if "해당 문서를 찾을 수 없습니다" in body_text or "찾을 수 없습니다" in body_text:
                print(f"  X 문서 없음")
                continue

            # 리다이렉트 확인
            final_url = driver.current_url
            print(f"  최종 URL: {final_url}")

            # h2 섹션 추출
            h2_elements = driver.find_elements(By.TAG_NAME, "h2")
            h2_texts = [h.text.strip() for h in h2_elements if h.text.strip()]

            # h3 섹션도 추출 (구조 파악용)
            h3_elements = driver.find_elements(By.TAG_NAME, "h3")
            h3_texts = [h.text.strip() for h in h3_elements if h.text.strip()]

            # 페이지 제목 추출
            title = ""
            try:
                title_el = driver.find_element(By.CSS_SELECTOR, "h1")
                title = title_el.text.strip()
            except Exception:
                pass

            results[cat_id] = {
                "status": "OK",
                "url": final_url,
                "title": title,
                "h2_sections": h2_texts[:15],
                "h3_sections": h3_texts[:20],
                "desc": item["desc"]
            }

            print(f"  OK - 제목: {title}")
            print(f"  h2 섹션 ({len(h2_texts)}개): {h2_texts[:10]}")
            print(f"  h3 섹션 ({len(h3_texts)}개): {h3_texts[:10]}")
            found = True
            break

        except Exception as e:
            print(f"  오류: {e}")
            continue

    if not found:
        results[cat_id] = {
            "status": "NOT_FOUND",
            "url": None,
            "title": None,
            "h2_sections": [],
            "h3_sections": [],
            "desc": item["desc"],
            "tried_urls": item["urls"]
        }
        print(f"  >>> {cat_id}: 모든 URL 실패!")

    time.sleep(3)

driver.quit()

# 결과 저장
output_path = "/Users/danghyeonsong/ai-dev-team/projects/lapaz-live/data/seed_url_verification.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("검증 결과 요약")
print("=" * 60)
for cat_id, info in results.items():
    status = info["status"]
    if status == "OK":
        print(f"  OK  {cat_id}: {info['title']} ({len(info['h2_sections'])} h2)")
    else:
        print(f"  FAIL {cat_id}: {info['desc']} - 문서 없음")

print(f"\n결과 저장: {output_path}")
