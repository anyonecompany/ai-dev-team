#!/usr/bin/env python3
"""Notion workspace audit — find items not linked to any project."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Load env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
TASK_DB_ID = os.environ["NOTION_TASK_DB_ID"]
PROJECT_DB_ID = os.environ["NOTION_PROJECT_DB_ID"]
DECISION_DB_ID = os.environ["NOTION_DECISION_DB_ID"]
TECHREF_DB_ID = os.environ["NOTION_TECHREF_DB_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

client = httpx.Client(
    base_url="https://api.notion.com/v1/",
    headers=HEADERS,
    timeout=30.0,
)


def query_all(database_id: str) -> list[dict]:
    """Query all pages from a Notion database with pagination."""
    results = []
    has_more = True
    start_cursor = None
    while has_more:
        body = {}
        if start_cursor:
            body["start_cursor"] = start_cursor
        resp = client.post(f"databases/{database_id}/query", json=body)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data["results"])
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    return results


def get_title(page: dict, prop_name: str) -> str:
    """Extract title text from a page property."""
    prop = page.get("properties", {}).get(prop_name, {})
    title_arr = prop.get("title", [])
    if title_arr:
        return title_arr[0].get("text", {}).get("content", "(no text)")
    return "(untitled)"


def get_relation(page: dict, prop_name: str = "프로젝트") -> list[str]:
    """Extract relation IDs from a page property."""
    prop = page.get("properties", {}).get(prop_name, {})
    relation = prop.get("relation", [])
    return [r["id"] for r in relation]


def get_select(page: dict, prop_name: str) -> str:
    """Extract select value."""
    prop = page.get("properties", {}).get(prop_name, {})
    sel = prop.get("select")
    if sel:
        return sel.get("name", "")
    return ""


def main():
    print("=" * 70)
    print("  NOTION WORKSPACE AUDIT — Unlinked Items Report")
    print("=" * 70)
    print()

    # 1. Projects
    print("[1/4] Querying Projects database...")
    projects = query_all(PROJECT_DB_ID)
    project_map = {}  # id -> name
    print(f"\n{'='*70}")
    print(f"  PROJECTS ({len(projects)} total)")
    print(f"{'='*70}")
    for p in projects:
        name = get_title(p, "프로젝트명")
        status = get_select(p, "상태")
        pid = p["id"]
        project_map[pid] = name
        print(f"  - {name}  [{status}]  (ID: {pid})")
    print()

    # 2. Tasks
    print("[2/4] Querying Tasks database...")
    tasks = query_all(TASK_DB_ID)
    tasks_linked = []
    tasks_unlinked = []
    for t in tasks:
        name = get_title(t, "태스크명")
        status = get_select(t, "상태")
        rels = get_relation(t, "프로젝트")
        entry = {"name": name, "status": status, "project_ids": rels, "id": t["id"]}
        if rels:
            tasks_linked.append(entry)
        else:
            tasks_unlinked.append(entry)

    print(f"\n{'='*70}")
    print(f"  TASKS — Total: {len(tasks)}, Linked: {len(tasks_linked)}, Unlinked: {len(tasks_unlinked)}")
    print(f"{'='*70}")
    if tasks_unlinked:
        print("\n  ** UNLINKED TASKS (no project relation): **")
        for t in tasks_unlinked:
            print(f"    - [{t['status']}] {t['name']}")
    else:
        print("\n  All tasks are linked to a project.")

    if tasks_linked:
        print(f"\n  Linked tasks:")
        for t in tasks_linked:
            proj_names = [project_map.get(pid, pid) for pid in t["project_ids"]]
            print(f"    - [{t['status']}] {t['name']}  -> {', '.join(proj_names)}")
    print()

    # 3. Decisions
    print("[3/4] Querying Decisions database...")
    decisions = query_all(DECISION_DB_ID)
    dec_linked = []
    dec_unlinked = []
    for d in decisions:
        name = get_title(d, "결정 사항")
        category = get_select(d, "카테고리")
        rels = get_relation(d, "프로젝트")
        entry = {"name": name, "category": category, "project_ids": rels, "id": d["id"]}
        if rels:
            dec_linked.append(entry)
        else:
            dec_unlinked.append(entry)

    print(f"\n{'='*70}")
    print(f"  DECISIONS — Total: {len(decisions)}, Linked: {len(dec_linked)}, Unlinked: {len(dec_unlinked)}")
    print(f"{'='*70}")
    if dec_unlinked:
        print("\n  ** UNLINKED DECISIONS (no project relation): **")
        for d in dec_unlinked:
            print(f"    - [{d['category']}] {d['name']}")
    else:
        print("\n  All decisions are linked to a project.")

    if dec_linked:
        print(f"\n  Linked decisions:")
        for d in dec_linked:
            proj_names = [project_map.get(pid, pid) for pid in d["project_ids"]]
            print(f"    - [{d['category']}] {d['name']}  -> {', '.join(proj_names)}")
    print()

    # 4. Tech References
    print("[4/4] Querying Tech References database...")
    techrefs = query_all(TECHREF_DB_ID)
    tr_linked = []
    tr_unlinked = []
    for t in techrefs:
        name = get_title(t, "제목")
        category = get_select(t, "카테고리")
        rels = get_relation(t, "프로젝트")
        entry = {"name": name, "category": category, "project_ids": rels, "id": t["id"]}
        if rels:
            tr_linked.append(entry)
        else:
            tr_unlinked.append(entry)

    print(f"\n{'='*70}")
    print(f"  TECH REFERENCES — Total: {len(techrefs)}, Linked: {len(tr_linked)}, Unlinked: {len(tr_unlinked)}")
    print(f"{'='*70}")
    if tr_unlinked:
        print("\n  ** UNLINKED TECH REFERENCES (no project relation): **")
        for t in tr_unlinked:
            print(f"    - [{t['category']}] {t['name']}")
    else:
        print("\n  All tech references are linked to a project.")

    if tr_linked:
        print(f"\n  Linked tech references:")
        for t in tr_linked:
            proj_names = [project_map.get(pid, pid) for pid in t["project_ids"]]
            print(f"    - [{t['category']}] {t['name']}  -> {', '.join(proj_names)}")
    print()

    # Summary
    total_unlinked = len(tasks_unlinked) + len(dec_unlinked) + len(tr_unlinked)
    total_items = len(tasks) + len(decisions) + len(techrefs)
    print(f"{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Projects:        {len(projects)}")
    print(f"  Tasks:           {len(tasks)} ({len(tasks_unlinked)} unlinked)")
    print(f"  Decisions:       {len(decisions)} ({len(dec_unlinked)} unlinked)")
    print(f"  Tech References: {len(techrefs)} ({len(tr_unlinked)} unlinked)")
    print(f"  ---")
    print(f"  Total items:     {total_items}")
    print(f"  Total unlinked:  {total_unlinked}")
    print()


if __name__ == "__main__":
    main()
