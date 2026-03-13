"""태스크 보드 보고 모듈."""

from ..config import TASK_DB_ID
from ..notion_client import get_client


def find_task(task_name: str) -> str | None:
    """태스크명으로 검색하여 page_id 반환."""
    client = get_client()
    results = client.query_db(
        TASK_DB_ID,
        filter={
            "property": "\ud0dc\uc2a4\ud06c\uba85",
            "title": {"equals": task_name},
        },
    )
    if results:
        return results[0]["id"]
    return None


def update_status(task_name: str, new_status: str, note: str | None = None) -> dict | None:
    """태스크 상태 변경.

    Args:
        task_name: 태스크명
        new_status: "\u23f3 \uc9c4\ud589 \uc804", "\ud83d\udd28 \uc9c4\ud589\uc911", "\ud83d\udc40 \ub9ac\ubdf0", "\u2705 \uc644\ub8cc", "\u23f8 \uc911\ub2e8\ub428"
        note: 비고 (선택)
    """
    page_id = find_task(task_name)
    if not page_id:
        print(f"[WARN] \ud0dc\uc2a4\ud06c\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4: {task_name}")
        return None

    props: dict = {
        "\uc0c1\ud0dc": {"select": {"name": new_status}},
    }
    if note:
        props["\ube44\uace0"] = {"rich_text": [{"text": {"content": note}}]}

    client = get_client()
    return client.update_page(page_id, props)


def add_task(
    task_name: str,
    priority: str = "\ud83d\udfe1 P1",
    deadline: str | None = None,
    done_criteria: str | None = None,
    project_name: str | None = None,
) -> dict:
    """새 태스크 추가.

    Args:
        task_name: 태스크명
        priority: "\ud83d\udd34 P0", "\ud83d\udfe1 P1", "\ud83d\udfe2 P2"
        deadline: ISO 날짜 문자열 (예: "2026-03-10")
        done_criteria: 완료 조건
        project_name: 프로젝트명 (relation 연결용)
    """
    client = get_client()

    props: dict = {
        "\ud0dc\uc2a4\ud06c\uba85": {"title": [{"text": {"content": task_name}}]},
        "\uc0c1\ud0dc": {"select": {"name": "\u23f3 \uc9c4\ud589 \uc804"}},
        "\uc6b0\uc120\uc21c\uc704": {"select": {"name": priority}},
    }

    if deadline:
        props["\ub370\ub4dc\ub77c\uc778"] = {"date": {"start": deadline}}

    if done_criteria:
        props["\uc644\ub8cc \uc870\uac74"] = {"rich_text": [{"text": {"content": done_criteria}}]}

    if project_name:
        project_id = client.find_project_by_name(project_name)
        if project_id:
            props["\ud504\ub85c\uc81d\ud2b8"] = {"relation": [{"id": project_id}]}
        else:
            print(f"[WARN] \ud504\ub85c\uc81d\ud2b8\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4: {project_name}")

    return client.create_page(TASK_DB_ID, props)
