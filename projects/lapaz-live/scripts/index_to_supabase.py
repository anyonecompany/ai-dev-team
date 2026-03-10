"""선수 프로필을 Supabase documents 테이블에 인덱싱하는 스크립트."""

import json
import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.config import (
    COLLECTION_NAME,
    OPENAI_API_KEY,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL,
)
from src.embeddings.indexer import SupabaseIndexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _find_latest_output() -> str | None:
    """output/ 디렉토리에서 가장 최신 players JSON 파일 경로 반환."""
    output_dir = os.path.join(PROJECT_ROOT, "output")
    if not os.path.isdir(output_dir):
        return None
    files = sorted(
        [f for f in os.listdir(output_dir) if f.startswith("players_") and f.endswith(".json")],
        reverse=True,
    )
    return os.path.join(output_dir, files[0]) if files else None


def main() -> None:
    """크롤링 결과를 Supabase에 인덱싱."""
    data_path = _find_latest_output()
    if not data_path or not os.path.exists(data_path):
        logger.error("크롤링 결과 파일 없음. 먼저 scripts/crawl_all.py를 실행하세요.")
        sys.exit(1)

    logger.info(f"데이터 파일: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # crawl_all.py 출력 형식: {"mun": [...], "avl": [...]}
    if isinstance(data, dict):
        profiles = []
        for team_profiles in data.values():
            profiles.extend(team_profiles)
    else:
        profiles = data

    logger.info(f"총 {len(profiles)}명 프로필 로드")

    indexer = SupabaseIndexer(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_SERVICE_KEY,
        openai_api_key=OPENAI_API_KEY,
        collection=COLLECTION_NAME,
    )

    success = 0
    fail = 0
    for profile in profiles:
        if indexer.index_player(profile):
            success += 1
        else:
            fail += 1

    logger.info(f"=== 인덱싱 완료 ===")
    logger.info(f"성공: {success}, 실패: {fail}, 총: {len(profiles)}")


if __name__ == "__main__":
    main()
