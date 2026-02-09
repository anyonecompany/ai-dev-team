"""
Slack 알림 모듈
- send_notification(channel, message, blocks=None)
- notify_project_created(project_name)
- notify_task_updated(task_name, status)
- notify_qa_result(project_name, passed, details)
- notify_error(project_name, error_message)
"""

from __future__ import annotations

import os
import logging
from typing import Any

import httpx

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#dev-team")

logger = logging.getLogger(__name__)


async def send_notification(channel: str, message: str, blocks: list[dict[str, Any]] | None = None) -> None:
    """Slack 웹훅으로 알림 전송."""
    if not SLACK_WEBHOOK_URL:
        return

    payload: dict[str, Any] = {"channel": channel or SLACK_CHANNEL, "text": message}
    if blocks:
        payload["blocks"] = blocks

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("slack_notification_failed", exc_info=exc)


async def notify_project_created(project_name: str) -> None:
    await send_notification(SLACK_CHANNEL, f"🚀 새 프로젝트 생성: *{project_name}*")


async def notify_task_updated(task_name: str, status: str) -> None:
    emoji = {"TODO": "📋", "IN_PROGRESS": "🔨", "DONE": "✅", "BLOCKED": "🚫"}.get(status, "📌")
    await send_notification(SLACK_CHANNEL, f"{emoji} 태스크 업데이트: *{task_name}* → {status}")


async def notify_qa_result(project_name: str, passed: bool, details: str = "") -> None:
    emoji = "✅" if passed else "❌"
    status = "PASS" if passed else "FAIL"
    details_text = f"\n{details}" if details else ""
    await send_notification(SLACK_CHANNEL, f"{emoji} QA 결과 [{project_name}]: {status}{details_text}")


async def notify_error(project_name: str, error_message: str) -> None:
    await send_notification(SLACK_CHANNEL, f"🔥 에러 발생 [{project_name}]: {error_message}")
