#!/usr/bin/env python3
"""태스크 상태 변경 CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporters.task_reporter import update_status


def main() -> None:
    parser = argparse.ArgumentParser(description="태스크 상태 변경")
    parser.add_argument("--task", required=True, help="태스크명")
    parser.add_argument(
        "--status",
        default="\u2705 \uc644\ub8cc",
        help='상태 (기본: "\u2705 \uc644\ub8cc")',
    )
    parser.add_argument("--note", default=None, help="비고")
    args = parser.parse_args()

    result = update_status(args.task, args.status, note=args.note)
    if result:
        print(f"[OK] '{args.task}' \u2192 {args.status}")
    else:
        print(f"[FAIL] Task not found: {args.task}")
        sys.exit(1)


if __name__ == "__main__":
    main()
