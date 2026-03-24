"""
Notion 태스크 보드 매니저.
기존 "태스크 보드" DB (31a37b6f...80f3)에 연결.

사용법:
    python task_manager.py add "태스크 제목" --project portfiq --size M
    python task_manager.py next
    python task_manager.py update <page_id> --status "✅ 완료" --result "결과"
    python task_manager.py status
"""

import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import NOTION_API_KEY

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None

# 기존 태스크 보드 DB (primary) → 태스크 큐 DB (fallback)
TASK_DB_ID = os.getenv(
    "NOTION_TASKBOARD_DB_ID",
    os.getenv("NOTION_TASKQUEUE_DB_ID", "31a37b6f-6bf8-80f3-9017-d5df9ed5559a"),
)

PROJECT_DB_ID = os.getenv(
    "NOTION_PROJECT_DB_ID", "31a37b6f-6bf8-8036-90e9-e2720d2c10b5"
)

# 프로젝트명 → Notion 페이지 ID 캐시
_PROJECT_CACHE: dict[str, str] = {
    "portfiq": "31f37b6f-6bf8-81dd-a6b1-e59895438f80",
    "la-paz": "31a37b6f-6bf8-8009-a65c-e101b96857cc",
    "lapaz-live": "31a37b6f-6bf8-8009-a65c-e101b96857cc",
    "adaptfitai": "31a37b6f-6bf8-809f-a969-fb1baa842f7c",
    "서로연": "31b37b6f-6bf8-81dc-8f6d-f52cfab34ec3",
    "foundloop": "32037b6f-6bf8-8170-889e-d6968aa0014b",
    "ai-dev-team": "32037b6f-6bf8-8161-a940-c0e2cc103c8d",
    "tactical-gnn": "32437b6f-6bf8-81da-accf-feb252ff7e14",
}

# 기존 태스크 보드 상태 매핑
STATUS_MAP = {
    "📋 대기": "⏳ 진행 전",
    "🔄 진행중": "🔨 진행중",
    "✅ 완료": "✅ 완료",
    "❌ 실패": "⏸ 중단됨",
    "⏸️ 보류": "⏸ 중단됨",
}

PRIORITY_MAP = {
    "🔴 긴급": "🔴 P0",
    "🟠 높음": "🔴 P0",
    "🟡 보통": "🟡 P1",
    "🟢 낮음": "🟢 P2",
}


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def _get_project_id(project_name: str) -> str | None:
    """프로젝트명 → Notion 프로젝트 페이지 ID."""
    if not project_name:
        return None

    # 캐시 확인
    lower = project_name.lower().replace(" ", "-")
    for key, pid in _PROJECT_CACHE.items():
        if lower in key.lower() or key.lower() in lower:
            return pid

    # Notion에서 검색
    if not requests:
        return None
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{PROJECT_DB_ID}/query",
        headers=_headers(),
        json={
            "filter": {
                "property": "프로젝트명",
                "title": {"contains": project_name},
            },
            "page_size": 1,
        },
    )
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            pid = results[0]["id"]
            _PROJECT_CACHE[lower] = pid
            return pid
    return None


def add_task(
    title: str,
    project: str = "",
    size: str = "M",
    priority: str = "🟡 보통",
    order: int = 0,
    parent_task: str = "",
    description: str = "",
) -> str | None:
    """태스크를 기존 태스크 보드 DB에 추가."""
    if not NOTION_API_KEY or not requests:
        print("Notion 설정 미완료 — 스킵")
        return None

    mapped_status = STATUS_MAP.get("📋 대기", "⏳ 진행 전")
    mapped_priority = PRIORITY_MAP.get(priority, "🟡 P1")

    props: dict = {
        "태스크명": {"title": [{"text": {"content": title}}]},
        "상태": {"select": {"name": mapped_status}},
        "우선순위": {"select": {"name": mapped_priority}},
        "크기": {"select": {"name": size}},
        "순서": {"number": order},
    }

    if description:
        props["완료 조건"] = {"rich_text": [{"text": {"content": description[:2000]}}]}
    if parent_task:
        props["상위 태스크"] = {"rich_text": [{"text": {"content": parent_task}}]}

    # 프로젝트 relation
    project_id = _get_project_id(project)
    if project_id:
        props["프로젝트"] = {"relation": [{"id": project_id}]}

    page: dict = {"parent": {"database_id": TASK_DB_ID}, "properties": props}

    resp = requests.post(
        "https://api.notion.com/v1/pages", headers=_headers(), json=page
    )
    if resp.status_code == 200:
        page_id = resp.json()["id"]
        print(f"  📋 등록: {title} ({page_id[:8]})")
        return page_id

    print(f"  등록 실패: {title} — {resp.status_code} {resp.text[:150]}")
    return None


def get_next_task() -> dict | None:
    """다음 실행할 대기 태스크."""
    if not NOTION_API_KEY or not requests:
        return None

    query = {
        "filter": {"property": "상태", "select": {"equals": "⏳ 진행 전"}},
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
            title = task["properties"]["태스크명"]["title"]
            size = task["properties"].get("크기", {}).get("select", {})
            return {
                "id": task["id"],
                "title": title[0]["text"]["content"] if title else "무제",
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
        json={
            "sorts": [{"property": "순서", "direction": "ascending"}],
            "page_size": 100,
        },
    )
    if resp.status_code != 200:
        return []

    tasks = []
    for r in resp.json().get("results", []):
        title = r["properties"]["태스크명"]["title"]
        status = r["properties"].get("상태", {}).get("select", {})
        tasks.append(
            {
                "id": r["id"],
                "title": title[0]["text"]["content"] if title else "무제",
                "status": status.get("name", "?") if status else "?",
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
        mapped = STATUS_MAP.get(status, status)
        props["상태"] = {"select": {"name": mapped}}
    if result:
        props["비고"] = {"rich_text": [{"text": {"content": result[:2000]}}]}
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
        print(f"  {t['status']} {t['title']}")


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
