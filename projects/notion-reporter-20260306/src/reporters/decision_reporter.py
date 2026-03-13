"""의사결정 로그 보고 모듈."""

from datetime import date

from ..config import DECISION_DB_ID
from ..notion_client import get_client


def add_decision(
    title: str,
    category: str,
    decision: str,
    rationale: str,
    alternatives: str = "",
    decided_by: str = "CTO",
    decision_date: str | None = None,
    project_name: str | None = None,
) -> dict:
    """의사결정 기록 추가.

    Args:
        title: 결정 사항 (제목)
        category: "기술선택", "아키텍처", "데이터", "비즈니스", "프로세스", "인프라"
        decision: 결정 내용
        rationale: 근거
        alternatives: 대안
        decided_by: "CEO", "CTO", "합의"
        decision_date: ISO 날짜 (기본: 오늘)
        project_name: 프로젝트명 (relation 연결용)
    """
    client = get_client()
    dt = decision_date or date.today().isoformat()

    props: dict = {
        "\uacb0\uc815 \uc0ac\ud56d": {"title": [{"text": {"content": title}}]},
        "\ub0a0\uc9dc": {"date": {"start": dt}},
        "\uce74\ud14c\uace0\ub9ac": {"select": {"name": category}},
        "\uacb0\uc815": {"rich_text": [{"text": {"content": decision}}]},
        "\uadfc\uac70": {"rich_text": [{"text": {"content": rationale}}]},
        "\uacb0\uc815\uc790": {"select": {"name": decided_by}},
    }

    if alternatives:
        props["\ub300\uc548"] = {"rich_text": [{"text": {"content": alternatives}}]}

    if project_name:
        project_id = client.find_project_by_name(project_name)
        if project_id:
            props["\ud504\ub85c\uc81d\ud2b8"] = {"relation": [{"id": project_id}]}
        else:
            print(f"[WARN] \ud504\ub85c\uc81d\ud2b8\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4: {project_name}")

    return client.create_page(DECISION_DB_ID, props)
