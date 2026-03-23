"""ai-dev-team 자동 보고 디스패처.

모든 보고 이벤트의 단일 진입점.
기존 integrations/notion/reporter.py와 integrations/slack/ 를 래핑하여 호출.

사용법:
    from integrations.shared.report_dispatcher import dispatch_report

    dispatch_report("qa_report", {"project": "portfiq", "verdict": "GO", ...})

CLI:
    ./scripts/report-to-external.sh qa_report '{"project":"portfiq",...}'
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# integrations 루트를 path에 추가 (CLI 실행 시 필요)
_INTEGRATIONS_DIR = Path(__file__).resolve().parent.parent
if str(_INTEGRATIONS_DIR) not in sys.path:
    sys.path.insert(0, str(_INTEGRATIONS_DIR))

logger = logging.getLogger(__name__)

# 환경변수 기반 on/off
NOTION_ENABLED = bool(os.getenv("NOTION_API_KEY"))
SLACK_ENABLED = bool(os.getenv("SLACK_WEBHOOK_URL"))


def _slack(text: str) -> bool:
    """Slack 웹훅 동기 전송 (reporter.py와 동일 방식)."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return False
    try:
        import httpx

        httpx.post(webhook_url, json={"text": text}, timeout=5.0)
        return True
    except Exception as e:
        logger.warning("Slack 알림 실패: %s", e)
        return False


def _notion_techref(
    title: str,
    category: str,
    content: str,
    tags: list[str] | None = None,
    project_name: str | None = None,
) -> bool:
    """기존 reporter.report_techref()를 사용하여 Notion 기술레퍼런스 DB에 기록."""
    try:
        from notion.reporter import report_techref

        report_techref(
            title=title,
            category=category,
            tags=tags or [],
            content=content,
            project_name=project_name,
        )
        return True
    except Exception as e:
        logger.warning("Notion 보고 실패: %s", e)
        return False


# ── 이벤트별 포맷터 ──


def _format_qa_report(
    data: dict[str, Any], timestamp: str
) -> tuple[dict[str, Any] | None, str | None]:
    """QA 리포트 포맷팅."""
    project = data.get("project", "unknown")
    verdict = data.get("verdict", "UNKNOWN")
    p0 = data.get("p0", 0)
    p1 = data.get("p1", 0)
    p2 = data.get("p2", 0)
    fixed = data.get("fixed", 0)
    manual = data.get("manual", 0)
    summary = data.get("summary", "")

    emoji = {
        "GO": "\U0001f7e2",
        "CONDITIONAL GO": "\U0001f7e1",
        "NO GO": "\U0001f534",
    }.get(verdict, "\u26aa")

    notion_data = {
        "title": f"[QA] {project} \u2014 {verdict}",
        "category": "\ucf54\ub4dc\ud328\ud134",
        "content": f"\ud310\uc815: {emoji} {verdict}\nP0: {p0} | P1: {p1} | P2: {p2}\n\uc790\ub3d9\uc218\uc815: {fixed}\uac74 | \uc218\ub3d9\ud544\uc694: {manual}\uac74\n\n{summary}",
        "tags": ["qa", project],
        "project_name": project,
    }

    slack_text = f"{emoji} *{project} QA \uc644\ub8cc*: {verdict}\nP0:{p0} P1:{p1} P2:{p2} | \uc790\ub3d9\uc218\uc815 {fixed}\uac74 | \uc218\ub3d9 {manual}\uac74"

    return notion_data, slack_text


def _format_retrospective(
    data: dict[str, Any], timestamp: str
) -> tuple[dict[str, Any] | None, str | None]:
    """회고 포맷팅."""
    project = data.get("project", "unknown")
    decisions = data.get("decisions", [])
    mistakes = data.get("mistakes", [])
    patterns = data.get("patterns", [])

    content_parts = []
    if decisions:
        content_parts.append(
            f"\uc758\uc0ac\uacb0\uc815 {len(decisions)}\uac74: " + ", ".join(decisions)
        )
    if mistakes:
        content_parts.append(
            f"\uc2e4\uc218 \ud328\ud134 {len(mistakes)}\uac74: " + ", ".join(mistakes)
        )
    if patterns:
        content_parts.append(
            f"\ucf54\ub4dc \ud328\ud134 {len(patterns)}\uac74: " + ", ".join(patterns)
        )

    content = (
        "\n".join(content_parts)
        or "\uc0c8\ub85c\uc6b4 \ud559\uc2b5 \ud56d\ubaa9 \uc5c6\uc74c"
    )

    notion_data = {
        "title": f"[\ud68c\uace0] {project} \u2014 {timestamp[:10]}",
        "category": "\ucf54\ub4dc\ud328\ud134",
        "content": content,
        "tags": ["retrospective", project],
        "project_name": project,
    }

    slack_text = f"\U0001f4dd *{project} \ud68c\uace0*\n{content}"

    return notion_data, slack_text


def _format_session_save(
    data: dict[str, Any], timestamp: str
) -> tuple[dict[str, Any] | None, str | None]:
    """세션 저장/핸드오프 포맷팅 (Slack만)."""
    summary = data.get("summary", "")
    next_actions = data.get("next_actions", "")
    branch = data.get("branch", "")
    changed_files = data.get("changed_files", 0)

    slack_text = f"\U0001f4be *\uc138\uc158 \uc800\uc7a5* ({branch})\n{summary}\n\n\ub2e4\uc74c \ud560 \uc77c: {next_actions}\n\ubcc0\uacbd \ud30c\uc77c: {changed_files}\uac1c"

    return None, slack_text


def _format_ci_fix(
    data: dict[str, Any], timestamp: str
) -> tuple[dict[str, Any] | None, str | None]:
    """CI 수정 포맷팅."""
    project = data.get("project", "unknown")
    workflow = data.get("workflow", "")
    error_type = data.get("error_type", "")
    fixed = data.get("fixed", False)

    emoji = "\u2705" if fixed else "\u274c"
    status = (
        "\uc790\ub3d9 \uc218\uc815 \uc644\ub8cc"
        if fixed
        else "\uc218\ub3d9 \uc218\uc815 \ud544\uc694"
    )

    notion_data = {
        "title": f"[CI] {project} \u2014 {status}",
        "category": "\uc778\ud504\ub77c",
        "content": f"\uc6cc\ud06c\ud50c\ub85c\uc6b0: {workflow}\n\uc5d0\ub7ec: {error_type}\n\uacb0\uacfc: {status}",
        "tags": ["ci", project],
        "project_name": project,
    }

    slack_text = f"{emoji} *CI \uc218\uc815* ({project}/{workflow})\n\uc5d0\ub7ec: {error_type}\n\uacb0\uacfc: {status}"

    return notion_data, slack_text


def _format_benchmark(
    data: dict[str, Any], timestamp: str
) -> tuple[dict[str, Any] | None, str | None]:
    """벤치마크 포맷팅 (Notion만)."""
    total_calls = data.get("total_calls", 0)
    read_write_ratio = data.get("read_write_ratio", "N/A")
    top_agents = data.get("top_agents", "")
    top_tools = data.get("top_tools", "")

    notion_data = {
        "title": f"[\ubca4\uce58\ub9c8\ud06c] {timestamp[:10]}",
        "category": "\ucf54\ub4dc\ud328\ud134",
        "content": f"\ucd1d \ud638\ucd9c: {total_calls}\ud68c\nR/W \ube44\uc728: {read_write_ratio}\n\uc0c1\uc704 \uc5d0\uc774\uc804\ud2b8: {top_agents}\n\uc0c1\uc704 \ub3c4\uad6c: {top_tools}",
        "tags": ["benchmark"],
    }

    return notion_data, None


# 포맷터 매핑
FORMATTERS: dict[str, Any] = {
    "qa_report": _format_qa_report,
    "retrospective": _format_retrospective,
    "session_save": _format_session_save,
    "ci_fix": _format_ci_fix,
    "benchmark": _format_benchmark,
}


def dispatch_report(event_type: str, data: dict[str, Any]) -> dict[str, bool]:
    """보고 이벤트 디스패치.

    Args:
        event_type: qa_report | retrospective | session_save | ci_fix | benchmark
        data: 이벤트별 데이터 딕셔너리

    Returns:
        {"notion": bool, "slack": bool} 성공 여부
    """
    results = {"notion": False, "slack": False}
    timestamp = datetime.now().isoformat()

    formatter = FORMATTERS.get(event_type)
    if not formatter:
        logger.error("알 수 없는 이벤트 타입: %s", event_type)
        return results

    notion_data, slack_text = formatter(data, timestamp)

    # Notion 보고 (기존 report_techref 활용)
    if NOTION_ENABLED and notion_data:
        try:
            ok = _notion_techref(
                title=notion_data["title"],
                category=notion_data.get("category", "코드패턴"),
                content=notion_data.get("content", ""),
                tags=notion_data.get("tags"),
                project_name=notion_data.get("project_name"),
            )
            results["notion"] = ok
            if ok:
                logger.info("Notion 보고 성공: %s", event_type)
        except Exception as e:
            logger.error("Notion 보고 실패: %s", e)

    # Slack 보고
    if SLACK_ENABLED and slack_text:
        try:
            results["slack"] = _slack(slack_text)
            if results["slack"]:
                logger.info("Slack 보고 성공: %s", event_type)
        except Exception as e:
            logger.error("Slack 보고 실패: %s", e)

    if not NOTION_ENABLED and not SLACK_ENABLED:
        logger.info("Notion/Slack 미설정 — 보고 스킵 (%s)", event_type)

    return results


# ── CLI 진입점 ──

if __name__ == "__main__":
    import sys as _sys

    if len(_sys.argv) < 2:
        print("사용법: python report_dispatcher.py <event_type> '<json_data>'")
        print(f"이벤트: {', '.join(FORMATTERS.keys())}")
        _sys.exit(1)

    _event = _sys.argv[1]
    _json_str = _sys.argv[2] if len(_sys.argv) > 2 else "{}"

    try:
        _data = json.loads(_json_str)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
        _sys.exit(1)

    _result = dispatch_report(_event, _data)
    print(json.dumps(_result))
