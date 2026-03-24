"""
AI-dev-team 현황 Notion 페이지 자동 갱신 + 버전 기록.

사용법:
    python integrations/notion/status_updater.py update
    python integrations/notion/status_updater.py version "v4.0.0" "규율 시스템 추가"
    python integrations/notion/status_updater.py both "v4.0.0" "규율 시스템 추가"
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 경로 설정
_THIS_DIR = Path(__file__).parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
sys.path.insert(0, str(_THIS_DIR))

from config import NOTION_API_KEY

logger = logging.getLogger(__name__)

STATUS_PAGE_ID = os.getenv("NOTION_STATUS_PAGE_ID", "")

try:
    import httpx
except ImportError:
    httpx = None


def _headers() -> dict:
    """Notion API 헤더."""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def _collect_status() -> dict:
    """인프라 현황 수집 (bash 스크립트 실행)."""
    script = _PROJECT_ROOT / "scripts" / "collect-infra-status.sh"
    if script.exists():
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        if result.returncode == 0:
            return json.loads(result.stdout)

    return {"timestamp": datetime.now().isoformat(), "infra": {}, "version": "unknown"}


def _table_row(cells: list[str]) -> dict:
    """Notion 테이블 행."""
    return {
        "type": "table_row",
        "table_row": {
            "cells": [[{"type": "text", "text": {"content": c}}] for c in cells]
        },
    }


def _callout(text: str, icon: str = "📊", color: str = "blue_background") -> dict:
    """Notion 콜아웃 블록."""
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": icon},
            "color": color,
        },
    }


def _toggle_heading(text: str, level: int = 2, children: list = None) -> dict:
    """Notion 토글 가능 헤딩 블록."""
    key = f"heading_{level}"
    block = {
        "object": "block",
        "type": key,
        key: {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "is_toggleable": True,
        },
    }
    if children:
        block[key]["children"] = children
    return block


def _bullet(text: str) -> dict:
    """Notion 불릿 블록."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def _build_status_blocks(status: dict) -> list[dict]:
    """현황 데이터를 Notion 블록으로 변환. 토글/콜아웃 활용."""
    infra = status.get("infra", {})
    ts = status.get("timestamp", "")[:19]

    cmds = infra.get("commands", "?")
    agents = infra.get("agents", "?")
    skills = infra.get("skills", "?")
    hooks = infra.get("hooks", "?")
    hook_ev = infra.get("hook_events", "?")
    scripts = infra.get("scripts", "?")
    wf = infra.get("workflows", "?")

    # 1. 핵심 수치 콜아웃 (항상 보임)
    summary_text = (
        f"커맨드 {cmds} | 에이전트 {agents} "
        f"(Opus {infra.get('agents_opus', '?')}, "
        f"Sonnet {infra.get('agents_sonnet', '?')}, "
        f"Haiku {infra.get('agents_haiku', '?')}) | "
        f"스킬 {skills} | 훅 {hooks} ({hook_ev} events) | "
        f"스크립트 {scripts} | CI/CD {wf}"
    )

    # 2. 현재 상태 콜아웃
    current = status.get("current_work", "없음")
    next_step = status.get("next_step", "없음")
    branch = status.get("branch", "?")
    commit = status.get("last_commit", "?")

    state_text = (
        f"브랜치: {branch}\n"
        f"마지막 커밋: {commit}\n"
        f"현재 작업: {current}\n"
        f"다음 단계: {next_step}"
    )

    # 3. 상세 수치 테이블 (토글 안에)
    detail_table = {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 2,
            "has_column_header": True,
            "has_row_header": False,
            "children": [
                _table_row(["항목", "수량"]),
                _table_row(["커맨드", str(cmds)]),
                _table_row(
                    [
                        "에이전트",
                        f"{agents} (Opus {infra.get('agents_opus', '?')}, Sonnet {infra.get('agents_sonnet', '?')}, Haiku {infra.get('agents_haiku', '?')})",
                    ]
                ),
                _table_row(["스킬", str(skills)]),
                _table_row(["훅", f"{hooks} ({hook_ev} events)"]),
                _table_row(["스크립트", str(scripts)]),
                _table_row(["CI/CD 워크플로우", str(wf)]),
                _table_row(["규칙 파일", str(infra.get("rules", "?"))]),
                _table_row(["Codemap", str(infra.get("codemaps", "?"))]),
                _table_row(
                    ["프로젝트 CLAUDE.md", str(infra.get("project_claudemd", "?"))]
                ),
                _table_row(
                    [
                        "Knowledge",
                        f"ADR {infra.get('knowledge_adr', '?')} + 실수 {infra.get('knowledge_mistakes', '?')} + 패턴 {infra.get('knowledge_patterns', '?')}",
                    ]
                ),
            ],
        },
    }

    return [
        # 갱신 시각
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"자동 갱신: {ts}"},
                        "annotations": {"color": "gray"},
                    }
                ]
            },
        },
        # 핵심 수치 콜아웃
        _callout(summary_text, "📊", "blue_background"),
        # 현재 상태 콜아웃
        _callout(state_text, "🔄", "yellow_background"),
        # 상세 수치 (토글)
        _toggle_heading("상세 인프라 수치", 3, [detail_table]),
    ]


def _build_version_block(version: str, description: str) -> list[dict]:
    """버전 기록 블록."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return [
        {"object": "block", "type": "divider", "divider": {}},
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"{version} — {ts}"}}
                ]
            },
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": description}}]
            },
        },
    ]


def update_status_page(page_id: str = "") -> bool:
    """현황 페이지 갱신."""
    page_id = page_id or STATUS_PAGE_ID

    if not page_id:
        print("NOTION_STATUS_PAGE_ID 미설정 — Notion 현황 갱신 스킵")
        return False

    if not NOTION_API_KEY:
        print("NOTION_API_KEY 미설정")
        return False

    if not httpx:
        print("httpx 모듈 없음")
        return False

    status = _collect_status()
    blocks = _build_status_blocks(status)

    with httpx.Client(timeout=30.0) as client:
        # 기존 블록 중 인프라 현황 관련만 삭제
        resp = client.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100",
            headers=_headers(),
        )

        if resp.status_code == 200:
            # 자동 갱신 블록만 삭제 (버전 기록 보존)
            auto_keywords = (
                "인프라 현황",
                "현재 상태",
                "상세 인프라 수치",
                "자동 갱신:",
                "커맨드 ",
                "브랜치:",
                "마지막 커밋:",
                "현재 작업:",
                "다음 단계:",
            )
            for block in resp.json().get("results", []):
                bt = block.get("type", "")
                text = ""
                if bt in block and "rich_text" in block[bt]:
                    texts = block[bt]["rich_text"]
                    if texts:
                        text = texts[0].get("text", {}).get("content", "")

                should_delete = (
                    any(text.startswith(kw) for kw in auto_keywords)
                    or bt == "table"
                    or (
                        bt == "callout"
                        and any(
                            kw in text for kw in ("커맨드", "브랜치:", "현재 작업:")
                        )
                    )
                )

                if should_delete:
                    client.delete(
                        f"https://api.notion.com/v1/blocks/{block['id']}",
                        headers=_headers(),
                    )

        # 새 블록 추가
        resp = client.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=_headers(),
            json={"children": blocks},
        )

    if resp.status_code == 200:
        print(f"Notion 현황 갱신 완료 ({status.get('timestamp', '')[:19]})")
        return True

    print(f"Notion 갱신 실패: {resp.status_code} — {resp.text[:200]}")
    return False


def add_version_record(version: str, description: str, page_id: str = "") -> bool:
    """버전 기록 추가."""
    page_id = page_id or STATUS_PAGE_ID

    if not page_id or not NOTION_API_KEY or not httpx:
        print("Notion 설정 미완료 — 버전 기록 스킵")
        return False

    blocks = _build_version_block(version, description)

    with httpx.Client(timeout=30.0) as client:
        resp = client.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=_headers(),
            json={"children": blocks},
        )

    if resp.status_code == 200:
        print(f"Notion 버전 기록 추가: {version}")
        return True

    print(f"Notion 버전 기록 실패: {resp.status_code} — {resp.text[:200]}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python status_updater.py update")
        print("  python status_updater.py version v4.0.0 '설명'")
        print("  python status_updater.py both v4.0.0 '설명'")
        sys.exit(1)

    action = sys.argv[1]

    if action == "update":
        update_status_page()
    elif action == "version" and len(sys.argv) >= 4:
        add_version_record(sys.argv[2], sys.argv[3])
    elif action == "both" and len(sys.argv) >= 4:
        update_status_page()
        add_version_record(sys.argv[2], sys.argv[3])
    else:
        print(f"알 수 없는 명령: {action}")
