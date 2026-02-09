"""
Monday.com 동기화 모듈
- create_project_group(project_name)
- create_task_item(group_id, task_name, status, assignee)
- update_task_status(item_id, status)
- sync_qa_result(project_name, result)
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any

import httpx

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY") or os.getenv("MONDAY_API_TOKEN", "")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID", "")
MONDAY_API_URL = "https://api.monday.com/v2"

logger = logging.getLogger(__name__)

PROJECT_GROUP_MAP = ".monday_project_group_map.json"
TASK_MAP = ".monday_id_map.json"


def _mapping_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), filename)


def load_mapping(filename: str) -> dict[str, Any]:
    path = _mapping_path(filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_mapping(filename: str, mapping: dict[str, Any]) -> None:
    path = _mapping_path(filename)
    with open(path, "w") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def _board_id_value() -> str | int:
    if MONDAY_BOARD_ID.isdigit():
        return int(MONDAY_BOARD_ID)
    return MONDAY_BOARD_ID


async def monday_query(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monday.com GraphQL API 호출."""
    if not MONDAY_API_KEY:
        return {}

    headers = {"Authorization": MONDAY_API_KEY, "Content-Type": "application/json"}
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(MONDAY_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                logger.warning("monday_graphql_error", extra={"errors": data["errors"]})
                return {}
            return data.get("data", {})
    except httpx.HTTPError as exc:
        logger.warning("monday_request_failed", exc_info=exc)
        return {}


async def create_project_group(project_name: str) -> str:
    """Monday.com 보드에 프로젝트 그룹 생성."""
    if not MONDAY_BOARD_ID:
        return ""

    existing = load_mapping(PROJECT_GROUP_MAP).get(project_name)
    if existing:
        return existing

    query = """mutation ($board_id: ID!, $group_name: String!) {
        create_group(board_id: $board_id, group_name: $group_name) { id }
    }"""
    result = await monday_query(query, {"board_id": _board_id_value(), "group_name": project_name})
    group_id = result.get("create_group", {}).get("id", "")

    if group_id:
        mapping = load_mapping(PROJECT_GROUP_MAP)
        mapping[project_name] = group_id
        _save_mapping(PROJECT_GROUP_MAP, mapping)

    return group_id


async def create_task_item(group_id: str, task_name: str, status: str, assignee: str | None = None) -> str:
    """프로젝트 그룹에 태스크 아이템 생성."""
    if not MONDAY_BOARD_ID:
        return ""

    column_values: dict[str, Any] = {}
    if status:
        column_values["status"] = {"label": status}
    if assignee:
        column_values["assignee"] = assignee

    query = """mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON!) {
        create_item(board_id: $board_id, group_id: $group_id, item_name: $item_name, column_values: $column_values) { id }
    }"""

    result = await monday_query(
        query,
        {
            "board_id": _board_id_value(),
            "group_id": group_id,
            "item_name": task_name,
            "column_values": json.dumps(column_values),
        },
    )
    item_id = result.get("create_item", {}).get("id", "")

    if item_id:
        mapping = load_mapping(TASK_MAP)
        mapping[task_name] = item_id
        _save_mapping(TASK_MAP, mapping)

    return item_id


async def update_task_status(item_id: str, status: str) -> None:
    """태스크 상태 업데이트."""
    if not MONDAY_BOARD_ID:
        return

    query = """mutation ($board_id: ID!, $item_id: ID!, $value: JSON!) {
        change_column_value(board_id: $board_id, item_id: $item_id, column_id: "status", value: $value) { id }
    }"""

    await monday_query(
        query,
        {
            "board_id": _board_id_value(),
            "item_id": item_id,
            "value": json.dumps({"label": status}),
        },
    )


async def sync_qa_result(project_name: str, result: str) -> str:
    """QA 결과를 Monday.com에 기록."""
    group_id = await create_project_group(project_name)
    if not group_id:
        return ""

    status = "PASS" if result.upper() == "PASS" else "FAIL"
    return await create_task_item(group_id, f"QA Result - {project_name}", status)
