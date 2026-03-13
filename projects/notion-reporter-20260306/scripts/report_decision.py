#!/usr/bin/env python3
"""의사결정 기록 CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporters.decision_reporter import add_decision


def main() -> None:
    parser = argparse.ArgumentParser(description="의사결정 기록 추가")
    parser.add_argument("--title", required=True, help="결정 사항")
    parser.add_argument("--category", required=True, help="카테고리")
    parser.add_argument("--decision", required=True, help="결정 내용")
    parser.add_argument("--rationale", required=True, help="근거")
    parser.add_argument("--alternatives", default="", help="대안")
    parser.add_argument("--decided-by", default="CTO", help="결정자")
    parser.add_argument("--date", default=None, help="날짜 (ISO)")
    parser.add_argument("--project", default=None, help="프로젝트명")
    args = parser.parse_args()

    result = add_decision(
        title=args.title,
        category=args.category,
        decision=args.decision,
        rationale=args.rationale,
        alternatives=args.alternatives,
        decided_by=args.decided_by,
        decision_date=args.date,
        project_name=args.project,
    )
    print(f"[OK] Decision created: {result['id']}")


if __name__ == "__main__":
    main()
