"""기술 레퍼런스 보고 모듈."""

from datetime import date

from ..config import TECHREF_DB_ID
from ..notion_client import get_client


def _text_to_blocks(content: str) -> list[dict]:
    """마크다운 텍스트를 Notion 블록으로 변환.

    간단한 변환: # heading, - bullet, 나머지 paragraph.
    """
    blocks: list[dict] = []
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]
                },
            })
        elif stripped.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]
                },
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": stripped}}]
                },
            })
    return blocks


def add_reference(
    title: str,
    category: str,
    tags: list[str] | None = None,
    status: str = "\u2705 \uac80\uc99d\ub428",
    content: str = "",
    project_name: str | None = None,
) -> dict:
    """기술 레퍼런스 추가.

    Args:
        title: 제목
        category: "기술스택", "아키텍처패턴", "코드패턴", "데이터소스", "프롬프트", "인프라", "컨벤션", "도메인지식"
        tags: ["Python", "FastAPI", ...] (multi_select)
        status: "\u2705 \uac80\uc99d\ub428", "\ud83e\uddea \uc2e4\ud5d8\uc911", "\u274c \ud3d0\uae30"
        content: 본문 (마크다운 형식)
        project_name: 프로젝트명 (relation 연결용)
    """
    client = get_client()

    props: dict = {
        "\uc81c\ubaa9": {"title": [{"text": {"content": title}}]},
        "\uce74\ud14c\uace0\ub9ac": {"select": {"name": category}},
        "\uc0c1\ud0dc": {"select": {"name": status}},
        "\ub9c8\uc9c0\ub9c9 \uc5c5\ub370\uc774\ud2b8": {"date": {"start": date.today().isoformat()}},
    }

    if tags:
        props["\ud0dc\uadf8"] = {"multi_select": [{"name": t} for t in tags]}

    if project_name:
        project_id = client.find_project_by_name(project_name)
        if project_id:
            props["\ud504\ub85c\uc81d\ud2b8"] = {"relation": [{"id": project_id}]}
        else:
            print(f"[WARN] \ud504\ub85c\uc81d\ud2b8\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4: {project_name}")

    children = _text_to_blocks(content) if content else None
    return client.create_page(TECHREF_DB_ID, props, children=children)
