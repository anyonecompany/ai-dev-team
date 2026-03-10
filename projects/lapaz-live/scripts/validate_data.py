"""크롤링 데이터 검증 스크립트.

Supabase documents 테이블에 저장된 선수 데이터를 검증한다:
1. 40명 선수 데이터 존재 여부
2. content(bio)가 비어있지 않은지
3. metadata 필드 완전성 (name_kr, name_en, position, team)
"""

from __future__ import annotations

import json
import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.config import (
    AVL_PLAYERS,
    COLLECTION_NAME,
    MUN_PLAYERS,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REQUIRED_METADATA = {"name_kr", "name_en", "position", "team"}
EXPECTED_TOTAL = len(MUN_PLAYERS) + len(AVL_PLAYERS)


def _load_from_supabase() -> list[dict]:
    """Supabase documents 테이블에서 선수 데이터 로드."""
    try:
        from supabase import create_client
    except ImportError:
        logger.error("supabase 패키지 미설치. pip install supabase")
        return []

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    resp = (
        client.table("documents")
        .select("*")
        .eq("collection", COLLECTION_NAME)
        .execute()
    )
    return resp.data or []


def _load_from_json(path: str) -> list[dict]:
    """로컬 JSON 파일에서 선수 데이터 로드."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    players: list[dict] = []
    for team_key in ("mun", "avl"):
        players.extend(data.get(team_key, []))
    return players


def validate(records: list[dict]) -> dict:
    """데이터 검증 실행.

    Returns:
        {"passed": bool, "total": int, "issues": list[str], "stats": dict}
    """
    issues: list[str] = []
    stats = {"total": len(records), "empty_bio": 0, "missing_metadata": 0}

    # 1. 총 선수 수 확인
    if len(records) < EXPECTED_TOTAL:
        issues.append(
            f"선수 수 부족: {len(records)}/{EXPECTED_TOTAL}"
        )

    # 2. 개별 레코드 검증
    seen_names: set[str] = set()
    for i, rec in enumerate(records):
        # content / bio 비어있는지
        content = rec.get("content") or rec.get("bio") or ""
        if not content.strip():
            stats["empty_bio"] += 1
            name = rec.get("name_en") or rec.get("metadata", {}).get("name_en", f"record#{i}")
            issues.append(f"빈 content: {name}")

        # metadata 완전성
        meta = rec.get("metadata", rec)  # Supabase는 metadata 컬럼, 로컬 JSON은 flat
        missing = REQUIRED_METADATA - set(meta.keys())
        if missing:
            stats["missing_metadata"] += 1
            name = meta.get("name_en", f"record#{i}")
            issues.append(f"메타데이터 누락 ({', '.join(missing)}): {name}")

        # 중복 체크
        name_en = meta.get("name_en", "")
        if name_en:
            if name_en in seen_names:
                issues.append(f"중복 선수: {name_en}")
            seen_names.add(name_en)

    passed = len(issues) == 0
    return {"passed": passed, "total": len(records), "issues": issues, "stats": stats}


def main() -> None:
    """검증 실행. --json <path> 옵션으로 로컬 JSON 검증 가능."""
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        if idx + 1 >= len(sys.argv):
            logger.error("--json 뒤에 파일 경로를 지정하세요.")
            sys.exit(1)
        json_path = sys.argv[idx + 1]
        logger.info("로컬 JSON 검증: %s", json_path)
        records = _load_from_json(json_path)
    else:
        logger.info("Supabase documents 테이블 검증 (collection=%s)", COLLECTION_NAME)
        records = _load_from_supabase()

    result = validate(records)

    logger.info("=== 검증 결과 ===")
    logger.info("총 레코드: %d / 기대: %d", result["total"], EXPECTED_TOTAL)
    logger.info("빈 content: %d건", result["stats"]["empty_bio"])
    logger.info("메타데이터 누락: %d건", result["stats"]["missing_metadata"])

    if result["passed"]:
        logger.info("PASS — 모든 검증 통과")
    else:
        logger.warning("FAIL — %d건의 이슈 발견:", len(result["issues"]))
        for issue in result["issues"]:
            logger.warning("  - %s", issue)
        sys.exit(1)


if __name__ == "__main__":
    main()
