#!/usr/bin/env python3
"""Notion API 연동 확인 스크립트."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import NOTION_API_KEY, TASK_DB_ID, PROJECT_DB_ID, DECISION_DB_ID, TECHREF_DB_ID
from src.notion_client import get_client


def main() -> None:
    print("=== Notion Reporter Setup Check ===\n")

    # 1. API 키 확인
    masked = NOTION_API_KEY[:8] + "..." + NOTION_API_KEY[-4:]
    print(f"API Key: {masked}")

    # 2. DB 접근 테스트
    client = get_client()

    dbs = {
        "Tasks": TASK_DB_ID,
        "Projects": PROJECT_DB_ID,
        "Decisions": DECISION_DB_ID,
        "TechRef": TECHREF_DB_ID,
    }

    all_ok = True
    for name, db_id in dbs.items():
        try:
            results = client.query_db(db_id)
            print(f"[OK] {name}: {len(results)} rows (DB: {db_id[:8]}...)")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            all_ok = False

    print()
    if all_ok:
        print("All checks passed!")
    else:
        print("Some checks failed. Please verify your .env configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
