"""play_style 보강 실행 스크립트 (Selenium 기반).

실행: cd ~/ai-dev-team/projects/lapaz-crawl-20260305170615 && python3 scripts/enrich_play_style.py

1. data/players_all.json 백업
2. 각 선수에 대해 나무위키 Selenium 크롤링 -> play_style 추출
3. 실패 시 Claude LLM fallback
4. 결과 저장: data/players_all.json (업데이트)
5. 로그: data/crawl_log_v2.txt
"""

import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.processors.play_style_enricher import PlayStyleEnricher

# .env 로드 (프로젝트 로컬 + 루트)
for env_candidate in [
    project_root / ".env",
    project_root.parent.parent / ".env",
]:
    if env_candidate.exists():
        load_dotenv(env_candidate)

# 로깅 설정
log_path = project_root / "data" / "crawl_log_v2.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(log_path), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    data_path = project_root / "data" / "players_all.json"
    backup_path = project_root / "data" / "players_all_backup.json"

    # 백업 생성
    logger.info(f"백업 생성: {backup_path}")
    shutil.copy2(data_path, backup_path)

    # 데이터 로드
    logger.info(f"데이터 로드: {data_path}")
    with open(data_path, encoding="utf-8") as f:
        players = json.load(f)
    logger.info(f"선수 수: {len(players)}")

    # 보강 전 상태
    missing_before = sum(
        1 for p in players
        if not p.get("play_style") or len(p.get("play_style", "")) < 10
    )
    logger.info(f"보강 필요 선수: {missing_before}명")

    # 보강 실행
    enricher = PlayStyleEnricher()
    players, stats = enricher.enrich(players)

    # 타임스탬프 추가
    now = datetime.now(timezone.utc).isoformat()
    for p in players:
        if p.get("play_style_source") in ("namuwiki", "llm_generated"):
            p.setdefault("enriched_at", now)

    # 저장
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)
    logger.info(f"저장 완료: {data_path}")

    # 최종 결과 요약
    sources: dict[str, int] = {}
    total_has_ps = 0
    for p in players:
        src = p.get("play_style_source", "none")
        sources[src] = sources.get(src, 0) + 1
        if p.get("play_style") and len(p.get("play_style", "")) >= 10:
            total_has_ps += 1

    logger.info(f"=== 최종 결과 ===")
    logger.info(f"play_style 보유: {total_has_ps}/{len(players)}")
    logger.info(f"소스별: {sources}")
    logger.info(f"이번 실행: namuwiki={stats['namuwiki']}, llm={stats['llm']}, failed={stats['failed']}")


if __name__ == "__main__":
    main()
