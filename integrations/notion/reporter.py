"""통합 보고 모듈 — Notion + Slack 동시 발송.

사용법:
    from integrations.notion.reporter import (
        report_task_done, report_decision, report_techref,
        report_completion, add_project
    )

    # 태스크 완료
    report_task_done("RAG 파이프라인 구현", "✅ 완료", "E2E 5/5 PASS")

    # 의사결정 기록
    report_decision(
        title="Voyage AI 임베딩 선택",
        category="기술선택",
        decision="voyage-3 (1024차원)",
        rationale="OpenAI 크레딧 부족",
    )

    # 통합 보고 (한번에 전부 — project_name 한 번만 넣으면 하위 항목에 자동 전파)
    report_completion(
        task_name="크롤링 완료",
        status="✅ 완료",
        summary="40명 완료",
        decisions=[...],
        tech_refs=[...],
        new_tasks=[...],
        project_name="La Paz",  # decisions/tech_refs/new_tasks에 자동 전파
    )
"""

import logging
from datetime import date

import httpx

from .client import get_client
from .config import (
    TASK_DB_ID, PROJECT_DB_ID, DECISION_DB_ID, TECHREF_DB_ID,
    SLACK_WEBHOOK_URL,
)

logger = logging.getLogger(__name__)


# ── Slack ──

def _slack(text: str) -> None:
    """Slack 웹훅 동기 전송."""
    if not SLACK_WEBHOOK_URL:
        return
    try:
        httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=5.0)
    except Exception as e:
        logger.warning("Slack 알림 실패: %s", e)


# ── 태스크 ──

def find_task(task_name: str) -> str | None:
    """태스크명으로 page_id 반환."""
    results = get_client().query_db(TASK_DB_ID, filter={
        "property": "태스크명",
        "title": {"equals": task_name},
    })
    return results[0]["id"] if results else None


def report_task_done(task_name: str, status: str = "✅ 완료", note: str = "") -> bool:
    """태스크 상태 변경 + Slack 알림."""
    page_id = find_task(task_name)
    if not page_id:
        print(f"[WARN] 태스크를 찾을 수 없습니다: {task_name}")
        return False

    props: dict = {"상태": {"select": {"name": status}}}
    if note:
        props["비고"] = {"rich_text": [{"text": {"content": note}}]}

    get_client().update_page(page_id, props)
    _slack(f"*태스크 업데이트* — *{task_name}* → {status}")
    print(f"[OK] 태스크 '{task_name}' → {status}")
    return True


def add_task(
    task_name: str,
    priority: str = "🟡 P1",
    deadline: str | None = None,
    done_criteria: str | None = None,
    project_name: str | None = None,
) -> dict:
    """새 태스크 추가 + Slack 알림.

    운영 규칙:
    - 태스크명은 구체적 행동으로 ("Supabase 테이블 3개 생성" O, "설계하기" X)
    - 완료 조건(done_criteria) 필수 — 없으면 끝났는지 알 수 없다
    """
    if not done_criteria:
        logger.warning("[규칙 위반] 완료 조건 없이 태스크 생성: %s", task_name)
        print(f"[WARN] 완료 조건(done_criteria)을 반드시 적어주세요: {task_name}")

    client = get_client()
    props: dict = {
        "태스크명": {"title": [{"text": {"content": task_name}}]},
        "상태": {"select": {"name": "⏳ 진행 전"}},
        "우선순위": {"select": {"name": priority}},
    }
    if deadline:
        props["데드라인"] = {"date": {"start": deadline}}
    if done_criteria:
        props["완료 조건"] = {"rich_text": [{"text": {"content": done_criteria}}]}
    if project_name:
        project_id = client.find_project_by_name(project_name)
        if project_id:
            props["프로젝트"] = {"relation": [{"id": project_id}]}

    result = client.create_page(TASK_DB_ID, props)
    _slack(f"*새 태스크* — *{task_name}* ({priority})")
    print(f"[OK] 새 태스크: {task_name}")
    return result


# ── 의사결정 ──

def report_decision(
    title: str,
    category: str,
    decision: str,
    rationale: str,
    alternatives: str = "",
    decided_by: str = "CTO",
    decision_date: str | None = None,
    project_name: str | None = None,
    icon: str | None = None,
) -> dict:
    """의사결정 기록 + Slack 알림.

    운영 규칙:
    - 기술 선택, 아키텍처 변경, 데이터 소스 결정은 반드시 기록
    - alternatives(대안)를 적는 이유: 3개월 뒤에 다시 같은 고민을 하지 않기 위해
    - 사소해 보여도 기록하라. 안 쓴 것보다 쓸모없는 기록이 낫다

    Args:
        icon: 페이지 이모지 아이콘 (미지정 시 카테고리별 자동 매핑)
    """
    if not alternatives:
        logger.warning("[규칙 위반] 대안(alternatives) 없이 의사결정 기록: %s", title)
        print(f"[WARN] 대안(alternatives)을 적어주세요 — 3개월 뒤 같은 고민 방지: {title}")

    client = get_client()
    dt = decision_date or date.today().isoformat()

    props: dict = {
        "결정 사항": {"title": [{"text": {"content": title}}]},
        "날짜": {"date": {"start": dt}},
        "카테고리": {"select": {"name": category}},
        "결정": {"rich_text": [{"text": {"content": decision}}]},
        "근거": {"rich_text": [{"text": {"content": rationale}}]},
        "결정자": {"select": {"name": decided_by}},
    }
    if alternatives:
        props["대안"] = {"rich_text": [{"text": {"content": alternatives}}]}
    if project_name:
        project_id = client.find_project_by_name(project_name)
        if project_id:
            props["프로젝트"] = {"relation": [{"id": project_id}]}

    page_icon = icon or _DECISION_CATEGORY_ICONS.get(category, "📝")
    result = client.create_page(DECISION_DB_ID, props, icon=page_icon)
    _slack(f"*의사결정* — {page_icon} *{title}* [{category}]")
    print(f"[OK] 의사결정: {page_icon} {title}")
    return result


# ── 기술 레퍼런스 ──

def _text_to_blocks(content: str) -> list[dict]:
    """마크다운 텍스트를 Notion 블록으로 변환."""
    blocks: list[dict] = []
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]},
            })
        elif stripped.startswith("- "):
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]},
            })
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": stripped}}]},
            })
    return blocks


_DECISION_CATEGORY_ICONS: dict[str, str] = {
    "기술선택": "⚙️",
    "아키텍처": "🏛️",
    "데이터": "🗃️",
    "비즈니스": "💼",
    "프로세스": "🔄",
    "인프라": "🌐",
}

_TECHREF_CATEGORY_ICONS: dict[str, str] = {
    "기술스택": "🛠️",
    "아키텍처패턴": "🏗️",
    "코드패턴": "💻",
    "데이터소스": "🗄️",
    "프롬프트": "💬",
    "인프라": "☁️",
    "컨벤션": "📐",
    "도메인지식": "📚",
}


def report_techref(
    title: str,
    category: str,
    tags: list[str] | None = None,
    status: str = "✅ 검증됨",
    content: str = "",
    project_name: str | None = None,
    icon: str | None = None,
) -> dict:
    """기술 레퍼런스 추가 + Slack 알림.

    Args:
        icon: 페이지 이모지 아이콘 (미지정 시 카테고리별 자동 매핑)
    """
    client = get_client()
    props: dict = {
        "제목": {"title": [{"text": {"content": title}}]},
        "카테고리": {"select": {"name": category}},
        "상태": {"select": {"name": status}},
        "마지막 업데이트": {"date": {"start": date.today().isoformat()}},
    }
    if tags:
        props["태그"] = {"multi_select": [{"name": t} for t in tags]}
    if project_name:
        project_id = client.find_project_by_name(project_name)
        if project_id:
            props["프로젝트"] = {"relation": [{"id": project_id}]}

    page_icon = icon or _TECHREF_CATEGORY_ICONS.get(category, "📄")
    children = _text_to_blocks(content) if content else None
    result = client.create_page(TECHREF_DB_ID, props, children=children, icon=page_icon)
    _slack(f"*기술 레퍼런스* — {page_icon} *{title}* [{category}]")
    print(f"[OK] 기술 레퍼런스: {page_icon} {title}")
    return result


# ── 프로젝트 ──

def add_project(
    name: str,
    status: str = "🔵 탐색",
    summary: str = "",
    tech_stack: list[str] | None = None,
    icon: str | None = None,
) -> dict:
    """프로젝트 추가 + Slack 알림.

    Args:
        name: 프로젝트명
        status: 상태
        summary: 한줄 요약
        tech_stack: 기술 스택 태그 리스트
        icon: 페이지 이모지 아이콘 (미지정 시 기본 🚀)
    """
    props: dict = {
        "프로젝트명": {"title": [{"text": {"content": name}}]},
        "상태": {"select": {"name": status}},
    }
    if summary:
        props["한줄 요약"] = {"rich_text": [{"text": {"content": summary}}]}
    if tech_stack:
        props["기술 스택"] = {"multi_select": [{"name": t} for t in tech_stack]}

    page_icon = icon or "🚀"
    result = get_client().create_page(PROJECT_DB_ID, props, icon=page_icon)
    _slack(f"*새 프로젝트* — {page_icon} *{name}* ({status})")
    print(f"[OK] 프로젝트: {page_icon} {name}")
    return result


# ── 통합 보고 ──

def report_completion(
    task_name: str,
    status: str = "✅ 완료",
    summary: str = "",
    decisions: list[dict] | None = None,
    tech_refs: list[dict] | None = None,
    new_tasks: list[dict] | None = None,
    project_name: str | None = None,
) -> dict:
    """통합 완료 보고 — Notion 업데이트 + Slack 알림.

    Args:
        task_name: 태스크명
        status: 상태
        summary: 요약
        decisions: [{"title", "category", "decision", "rationale", ...}]
        tech_refs: [{"title", "category", "tags", "content", ...}]
        new_tasks: [{"task_name", "priority", ...}]
        project_name: 프로젝트명 — 지정 시 하위 decisions/tech_refs/new_tasks에 자동 전파
    """
    results: dict = {"task": None, "decisions": [], "tech_refs": [], "new_tasks": []}

    # 1. 태스크
    ok = report_task_done(task_name, status, summary)
    results["task"] = "updated" if ok else "not_found"

    # 2. 의사결정 (project_name 자동 전파)
    for d in (decisions or []):
        if project_name and "project_name" not in d:
            d = {**d, "project_name": project_name}
        resp = report_decision(**d)
        results["decisions"].append(resp["id"])

    # 3. 기술 레퍼런스 (project_name 자동 전파)
    for t in (tech_refs or []):
        if project_name and "project_name" not in t:
            t = {**t, "project_name": project_name}
        resp = report_techref(**t)
        results["tech_refs"].append(resp["id"])

    # 4. 신규 태스크 (project_name 자동 전파)
    for nt in (new_tasks or []):
        if project_name and "project_name" not in nt:
            nt = {**nt, "project_name": project_name}
        resp = add_task(**nt)
        results["new_tasks"].append(resp["id"])

    # 5. 통합 Slack 요약
    n_d = len(results["decisions"])
    n_t = len(results["tech_refs"])
    n_n = len(results["new_tasks"])
    extras = []
    if n_d:
        extras.append(f"의사결정 {n_d}건")
    if n_t:
        extras.append(f"기술레퍼런스 {n_t}건")
    if n_n:
        extras.append(f"신규태스크 {n_n}건")
    if extras:
        _slack(f"*통합 보고 완료* — {', '.join(extras)}")

    return results
