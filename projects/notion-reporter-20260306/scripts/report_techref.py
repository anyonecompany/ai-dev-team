#!/usr/bin/env python3
"""기술 레퍼런스 추가 CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporters.techref_reporter import add_reference


def main() -> None:
    parser = argparse.ArgumentParser(description="기술 레퍼런스 추가")
    parser.add_argument("--title", required=True, help="제목")
    parser.add_argument("--category", required=True, help="카테고리")
    parser.add_argument("--tags", nargs="*", default=None, help="태그 목록")
    parser.add_argument("--status", default="\u2705 \uac80\uc99d\ub428", help="상태")
    parser.add_argument("--content", default="", help="본문 (마크다운)")
    parser.add_argument("--project", default=None, help="프로젝트명")
    args = parser.parse_args()

    result = add_reference(
        title=args.title,
        category=args.category,
        tags=args.tags,
        status=args.status,
        content=args.content,
        project_name=args.project,
    )
    print(f"[OK] TechRef created: {result['id']}")


if __name__ == "__main__":
    main()
