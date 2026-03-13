"""통합 완료 보고 모듈. 한 번 호출로 태스크+의사결정+기술레퍼런스 전부 보고 + Slack 알림."""

import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .task_reporter import update_status, add_task
from .decision_reporter import add_decision
from .techref_reporter import add_reference

logger = logging.getLogger(__name__)

# .env 로드 (루트 .env에 SLACK_WEBHOOK_URL 있음)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
# 프로젝트 루트 .env에 없으면 ai-dev-team 루트 .env에서
load_dotenv(Path(__file__).resolve().parent.parent.parent.parent.parent / ".env")

_SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def _notify_slack(text: str) -> None:
    """Slack 웹훅으로 동기 알림 전송."""
    if not _SLACK_WEBHOOK_URL:
        return
    try:
        httpx.post(_SLACK_WEBHOOK_URL, json={"text": text}, timeout=5.0)
    except Exception as e:
        logger.warning("Slack 알림 실패: %s", e)


def report(
    task_name: str,
    status: str = "\u2705 \uc644\ub8cc",
    summary: str = "",
    decisions: list[dict] | None = None,
    tech_refs: list[dict] | None = None,
    new_tasks: list[dict] | None = None,
) -> dict:
    """통합 완료 보고.

    Args:
        task_name: 완료할 태스크명
        status: 태스크 상태 ("\u2705 \uc644\ub8cc" 등)
        summary: 완료 요약 (비고에 기록)
        decisions: 의사결정 목록 [{"title", "category", "decision", "rationale", ...}]
        tech_refs: 기술 레퍼런스 목록 [{"title", "category", "tags", "content", ...}]
        new_tasks: 신규 태스크 목록 [{"task_name", "priority", "deadline", ...}]

    Returns:
        보고 결과 요약
    """
    results: dict = {"task": None, "decisions": [], "tech_refs": [], "new_tasks": []}

    # 1. 태스크 상태 업데이트
    task_result = update_status(task_name, status, note=summary)
    results["task"] = "updated" if task_result else "not_found"
    print(f"[OK] \ud0dc\uc2a4\ud06c '{task_name}' \u2192 {status}")

    # 2. 의사결정 기록
    for d in (decisions or []):
        resp = add_decision(**d)
        results["decisions"].append(resp["id"])
        print(f"[OK] \uc758\uc0ac\uacb0\uc815: {d.get('title', '?')}")

    # 3. 기술 레퍼런스 기록
    for t in (tech_refs or []):
        resp = add_reference(**t)
        results["tech_refs"].append(resp["id"])
        print(f"[OK] \uae30\uc220\ub808\ud37c\ub7f0\uc2a4: {t.get('title', '?')}")

    # 4. 신규 태스크 생성
    for nt in (new_tasks or []):
        resp = add_task(**nt)
        results["new_tasks"].append(resp["id"])
        print(f"[OK] \uc2e0\uaddc \ud0dc\uc2a4\ud06c: {nt.get('task_name', '?')}")

    # 5. Slack 알림
    n_decisions = len(results["decisions"])
    n_techrefs = len(results["tech_refs"])
    n_newtasks = len(results["new_tasks"])
    extras = []
    if n_decisions:
        extras.append(f"의사결정 {n_decisions}건")
    if n_techrefs:
        extras.append(f"기술레퍼런스 {n_techrefs}건")
    if n_newtasks:
        extras.append(f"신규태스크 {n_newtasks}건")
    extras_text = f" | {', '.join(extras)}" if extras else ""
    summary_text = f"\n> {summary}" if summary else ""
    slack_msg = f"*노션 보고* — *{task_name}* → {status}{extras_text}{summary_text}"
    _notify_slack(slack_msg)

    return results
