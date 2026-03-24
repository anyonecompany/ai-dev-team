"""
Notion 태스크 큐 매니저.
태스크 등록/조회/상태 갱신.

사용법:
    python task_manager.py add "태스크 제목" --project portfiq --size M
    python task_manager.py next
    python task_manager.py update <page_id> --status "✅ 완료" --result "결과"
    python task_manager.py status
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import NOTION_API_KEY

try:
    import requests
except ImportError:
    requests = None

TASK_DB_ID = os.getenv("NOTION_TASKQUEUE_DB_ID", "32d37b6f-6bf8-8160-bf01-c203ce7ef790")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def add_task(
    title: str,
    project: str = "",
    size: str = "M",
    priority: str = "🟡 보통",
    order: int = 0,
    parent_task: str = "",
    description: str = "",
) -> str | None:
    """태스크를 Notion DB에 추가. 페이지 ID 반환."""
    if not NOTION_API_KEY or not requests:
        print("Notion 설정 미완료 — 스킵")
        return None

    props: dict = {
        "태스크": {"title": [{"text": {"content": title}}]},
        "상태": {"select": {"name": "📋 대기"}},
        "크기": {"select": {"name": size}},
        "우선순위": {"select": {"name": priority}},
        "순서": {"number": order},
        "생성일": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
    }
    if project:
        props["프로젝트"] = {"select": {"name": project}}
    if parent_task:
        props["상위 태스크"] = {"rich_text": [{"text": {"content": parent_task}}]}

    page: dict = {"parent": {"database_id": TASK_DB_ID}, "properties": props}
    if description:
        page["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": description[:2000]}}]},
            }
        ]

    resp = requests.post(
        "https://api.notion.com/v1/pages", headers=_headers(), json=page
    )
    if resp.status_code == 200:
        page_id = resp.json()["id"]
        print(f"  📋 등록: {title} ({page_id[:8]})")
        return page_id

    print(f"  등록 실패: {title} — {resp.status_code}")
    return None


def get_next_task() -> dict | None:
    """다음 실행할 대기 태스크."""
    if not NOTION_API_KEY or not requests:
        return None

    query = {
        "filter": {"property": "상태", "select": {"equals": "📋 대기"}},
        "sorts": [
            {"property": "우선순위", "direction": "ascending"},
            {"property": "순서", "direction": "ascending"},
        ],
        "page_size": 1,
    }

    resp = requests.post(
        f"https://api.notion.com/v1/databases/{TASK_DB_ID}/query",
        headers=_headers(),
        json=query,
    )

    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            task = results[0]
            title = task["properties"]["태스크"]["title"]
            project = task["properties"].get("프로젝트", {}).get("select", {})
            size = task["properties"].get("크기", {}).get("select", {})
            return {
                "id": task["id"],
                "title": title[0]["text"]["content"] if title else "무제",
                "project": project.get("name", "") if project else "",
                "size": size.get("name", "M") if size else "M",
            }
    return None


def get_all_tasks() -> list[dict]:
    """전체 태스크 현황."""
    if not NOTION_API_KEY or not requests:
        return []

    resp = requests.post(
        f"https://api.notion.com/v1/databases/{TASK_DB_ID}/query",
        headers=_headers(),
        json={"sorts": [{"property": "순서", "direction": "ascending"}]},
    )
    if resp.status_code != 200:
        return []

    tasks = []
    for r in resp.json().get("results", []):
        title = r["properties"]["태스크"]["title"]
        status = r["properties"].get("상태", {}).get("select", {})
        project = r["properties"].get("프로젝트", {}).get("select", {})
        tasks.append(
            {
                "id": r["id"],
                "title": title[0]["text"]["content"] if title else "무제",
                "status": status.get("name", "?") if status else "?",
                "project": project.get("name", "") if project else "",
            }
        )
    return tasks


def update_task(
    page_id: str,
    status: str | None = None,
    result: str | None = None,
    commit: str | None = None,
) -> bool:
    """태스크 상태 갱신."""
    if not NOTION_API_KEY or not requests:
        return False

    props: dict = {}
    if status:
        props["상태"] = {"select": {"name": status}}
    if result:
        props["결과"] = {"rich_text": [{"text": {"content": result[:2000]}}]}
    if commit:
        props["커밋"] = {"rich_text": [{"text": {"content": commit}}]}

    resp = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_headers(),
        json={"properties": props},
    )
    if resp.status_code == 200:
        print(f"  갱신: {page_id[:8]} → {status or ''}")
        return True

    print(f"  갱신 실패: {resp.status_code}")
    return False


def print_status() -> None:
    """전체 태스크 현황 출력."""
    tasks = get_all_tasks()
    if not tasks:
        print("태스크 없음")
        return

    counts: dict[str, int] = {}
    for t in tasks:
        s = t["status"]
        counts[s] = counts.get(s, 0) + 1

    print("━━━ 태스크 현황 ━━━")
    for s, c in sorted(counts.items()):
        print(f"  {s}: {c}건")
    print(f"  총: {len(tasks)}건")
    print()
    for t in tasks:
        print(f"  {t['status']} [{t['project']}] {t['title']}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    parser = argparse.ArgumentParser(description="Notion 태스크 매니저")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add")
    p_add.add_argument("title")
    p_add.add_argument("--project", default="")
    p_add.add_argument("--size", default="M")
    p_add.add_argument("--priority", default="🟡 보통")
    p_add.add_argument("--order", type=int, default=0)
    p_add.add_argument("--parent", default="")
    p_add.add_argument("--desc", default="")

    sub.add_parser("next")

    p_upd = sub.add_parser("update")
    p_upd.add_argument("page_id")
    p_upd.add_argument("--status", default=None)
    p_upd.add_argument("--result", default=None)
    p_upd.add_argument("--commit", default=None)

    sub.add_parser("status")

    args = parser.parse_args()

    if args.command == "add":
        add_task(
            args.title,
            args.project,
            args.size,
            args.priority,
            args.order,
            args.parent,
            args.desc,
        )
    elif args.command == "next":
        task = get_next_task()
        if task:
            print(json.dumps(task, ensure_ascii=False, indent=2))
        else:
            print("대기 태스크 없음")
    elif args.command == "update":
        update_task(args.page_id, args.status, args.result, args.commit)
    elif args.command == "status":
        print_status()
    else:
        parser.print_help()
