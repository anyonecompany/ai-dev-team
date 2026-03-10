#!/usr/bin/env python3
"""통합 보고 CLI — Notion + Slack 동시 발송.

사용법:
    # 태스크 완료 보고
    python scripts/report.py --task "태스크명" --status "✅ 완료" --summary "요약"

    # JSON 파일로 상세 보고
    python scripts/report.py --file /path/to/report.json

    # 새 프로젝트 등록
    python scripts/report.py --new-project "프로젝트명" --project-status "🟡 진행중"
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.notion.reporter import report_completion, add_project


def main():
    parser = argparse.ArgumentParser(description="Notion + Slack 통합 보고")
    parser.add_argument("--task", help="태스크명")
    parser.add_argument("--status", default="✅ 완료", help="상태")
    parser.add_argument("--summary", default="", help="요약")
    parser.add_argument("--file", help="JSON 보고서 파일 경로")
    parser.add_argument("--new-project", help="새 프로젝트명")
    parser.add_argument("--project-status", default="🟡 진행중", help="프로젝트 상태")
    parser.add_argument("--project-summary", default="", help="프로젝트 한줄 요약")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("status", "✅ 완료")
        data.setdefault("summary", "")
        result = report_completion(**data)
    elif args.task:
        result = report_completion(
            task_name=args.task, status=args.status, summary=args.summary,
        )
    elif args.new_project:
        result = add_project(
            name=args.new_project,
            status=args.project_status,
            summary=args.project_summary,
        )
        print(f"\n프로젝트 등록 완료: {args.new_project}")
        return
    else:
        parser.error("--task, --file, 또는 --new-project 중 하나를 지정하세요.")
        return

    print(f"\n=== 보고 완료 (Notion + Slack) ===")
    print(f"Task: {result.get('task', 'N/A')}")
    print(f"Decisions: {len(result.get('decisions', []))}")
    print(f"TechRefs: {len(result.get('tech_refs', []))}")
    print(f"NewTasks: {len(result.get('new_tasks', []))}")


if __name__ == "__main__":
    main()
