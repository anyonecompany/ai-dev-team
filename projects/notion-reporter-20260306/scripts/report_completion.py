#!/usr/bin/env python3
"""통합 완료 보고 CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporters.completion_reporter import report
from src.parsers.agent_output_parser import parse_completion_json


def main() -> None:
    parser = argparse.ArgumentParser(description="통합 완료 보고")
    parser.add_argument("--task", help="태스크명")
    parser.add_argument("--status", default="\u2705 \uc644\ub8cc", help="상태")
    parser.add_argument("--summary", default="", help="요약")
    parser.add_argument("--file", help="JSON 파일 경로 (전체 보고 데이터)")
    args = parser.parse_args()

    if args.file:
        data = parse_completion_json(args.file)
        result = report(**data)
    elif args.task:
        result = report(task_name=args.task, status=args.status, summary=args.summary)
    else:
        parser.error("--task 또는 --file 중 하나를 지정하세요.")
        return

    print(f"\n=== 보고 완료 ===")
    print(f"Task: {result['task']}")
    print(f"Decisions: {len(result['decisions'])}")
    print(f"TechRefs: {len(result['tech_refs'])}")
    print(f"NewTasks: {len(result['new_tasks'])}")


if __name__ == "__main__":
    main()
