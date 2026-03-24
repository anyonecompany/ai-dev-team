"""
Notion 버전 관리 DB 자동 기록.
속성 7개 (간결) + 본문 상세 (문제→가설→해결→결과).

사용법:
    python integrations/notion/version_recorder.py \
        --title "v4.1.0 — 기능 추가" \
        --type "✨ Minor" \
        --summary "한줄 요약" \
        --scope "커맨드,스킬" \
        --problem "이전 문제" \
        --hypothesis "가설" \
        --solution "해결 방식" \
        --result "결과"
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import NOTION_API_KEY

logger = logging.getLogger(__name__)

DB_ID = os.getenv("NOTION_VERSION_DB_ID", "32d37b6f-6bf8-8001-8e4a-df30f98cfbfc")

try:
    import requests
except ImportError:
    requests = None


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def _get_changed_files() -> int:
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
        )
        return len(r.stdout.strip().split("\n")) if r.stdout.strip() else 0
    except Exception:
        return 0


def _h3(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _p(text: str) -> dict:
    chunks = [text[i : i + 2000] for i in range(0, len(text), 2000)]
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": c}} for c in chunks]
        },
    }


def _callout(text: str, emoji: str = "💡") -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": emoji},
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
        },
    }


def record_version(
    title: str,
    vtype: str = "✨ Minor",
    summary: str = "",
    scope: list[str] | None = None,
    problem: str = "",
    hypothesis: str = "",
    solution: str = "",
    result: str = "",
) -> bool:
    """버전 기록: 속성 7개 + 본문 상세."""
    if not NOTION_API_KEY or not requests:
        print("Notion 설정 미완료 — 버전 기록 스킵")
        return False

    scope = scope or []
    files = _get_changed_files()

    body: list[dict] = []
    if problem:
        body += [_h3("🔍 이전 문제점"), _p(problem)]
    if hypothesis:
        body += [_h3("💡 가설"), _callout(hypothesis)]
    if solution:
        body += [_h3("🛠️ 해결 방식"), _p(solution)]
    if result:
        body += [_h3("📊 결과"), _p(result)]
    if not body:
        body = [
            _h3("🔍 이전 문제점"),
            _p("(작성)"),
            _h3("💡 가설"),
            _p("(작성)"),
            _h3("🛠️ 해결 방식"),
            _p("(작성)"),
            _h3("📊 결과"),
            _p("(작성)"),
        ]

    page = {
        "parent": {"database_id": DB_ID},
        "properties": {
            "이름": {"title": [{"text": {"content": title}}]},
            "유형": {"select": {"name": vtype}},
            "상태": {"select": {"name": "✅ 완료"}},
            "날짜": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "변경 요약": {"rich_text": [{"text": {"content": summary[:2000]}}]},
            "영향 범위": {"multi_select": [{"name": s} for s in scope]},
            "변경 파일": {"number": files},
        },
        "children": body,
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages", headers=_headers(), json=page
    )
    if resp.status_code == 200:
        print(f"Notion 버전 기록: {title}")
        return True

    print(f"Notion 버전 기록 실패: {resp.status_code} — {resp.text[:200]}")
    return False


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--type", default="✨ Minor")
    p.add_argument("--summary", default="")
    p.add_argument("--scope", default="")
    p.add_argument("--problem", default="")
    p.add_argument("--hypothesis", default="")
    p.add_argument("--solution", default="")
    p.add_argument("--result", default="")
    a = p.parse_args()

    scope = [s.strip() for s in a.scope.split(",") if s.strip()]
    record_version(
        a.title, a.type, a.summary, scope, a.problem, a.hypothesis, a.solution, a.result
    )
