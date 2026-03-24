"""Notion 현황 페이지 재구성 — 토글 기반 구조."""

import json
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__) + "/..")
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import requests

TOKEN = os.getenv("NOTION_API_KEY")
PAGE_ID = "32d37b6f6bf880b49a17edcaebcf98ed"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def callout(text, emoji, color="default"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
            "rich_text": [{"text": {"content": text}}],
        },
    }


def paragraph(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"text": {"content": text}}]},
    }


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def bullet(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"text": {"content": text}}]},
    }


def toggle_h2(text, children):
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"text": {"content": text}}],
            "is_toggleable": True,
            "children": children[:100],
        },
    }


def toggle_h3(text, children):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"text": {"content": text}}],
            "is_toggleable": True,
            "children": children[:100],
        },
    }


def table_row(cells):
    return {
        "type": "table_row",
        "table_row": {"cells": [[{"text": {"content": str(c)}}] for c in cells]},
    }


def table_4col(header, rows):
    trs = [table_row(header)] + [table_row(r) for r in rows]
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 4,
            "has_column_header": True,
            "has_row_header": False,
            "children": trs,
        },
    }


# Collect infra
try:
    r = subprocess.run(
        ["bash", "scripts/collect-infra-status.sh"], capture_output=True, text=True
    )
    status = json.loads(r.stdout)
except Exception:
    status = {
        "infra": {},
        "branch": "main",
        "last_commit": "unknown",
        "current_work": "없음",
        "next_step": "없음",
    }

infra = status.get("infra", {})
ts = datetime.now().strftime("%Y-%m-%d %H:%M")

blocks = [
    # 1. Key metrics callout
    callout(
        f"커맨드 {infra.get('commands', '?')} | 에이전트 {infra.get('agents', '?')} "
        f"(Opus {infra.get('agents_opus', '?')}, Sonnet {infra.get('agents_sonnet', '?')}, "
        f"Haiku {infra.get('agents_haiku', '?')}) | 스킬 {infra.get('skills', '?')} | "
        f"훅 {infra.get('hooks', '?')} ({infra.get('hook_events', '?')} events) | "
        f"스크립트 {infra.get('scripts', '?')} | CI/CD {infra.get('workflows', '?')}",
        "📊",
        "blue_background",
    ),
    # 2. Current state callout
    callout(
        f"브랜치: {status.get('branch', '?')} | 마지막 커밋: {status.get('last_commit', '?')}\n"
        f"현재 작업: {status.get('current_work', '없음')}\n"
        f"다음 단계: {status.get('next_step', '없음')}",
        "🔄",
        "yellow_background",
    ),
    # 3. Timestamp
    paragraph(f"자동 갱신: {ts}"),
    divider(),
    # (DB is preserved here)
    divider(),
    # 4. Workflow guide
    toggle_h2(
        "🗺️ 워크플로우 선택 가이드",
        [
            table_4col(
                ["작업 크기", "기준", "커맨드", "흐름"],
                [
                    ["Small", "1-2파일", "/quick", "실행→lint→test→commit"],
                    ["Small", "빠른 수정", "/auto", "계획→실행→commit"],
                    ["Medium", "3-5파일", "/plan→/orchestrate", "선택적 /discuss"],
                    [
                        "Large",
                        "5파일+",
                        "/phase-loop",
                        "discuss→plan→execute→verify→qa",
                    ],
                    ["CI 실패", "-", "/ci-fix", "자동 진단→수정→검증→회고"],
                ],
            ),
            paragraph(
                "규율: Large에서 PLAN 없이 /orchestrate 불가. "
                "컨텍스트 50% 경고, 70% 강제 넛지."
            ),
        ],
    ),
    # 5. Commands
    toggle_h2(
        f"📋 커맨드 ({infra.get('commands', '?')}개)",
        [
            toggle_h3(
                "워크플로우 (GSD)",
                [
                    bullet("/phase-loop — 게이트 루프: discuss→plan→execute→verify→qa"),
                    bullet("/discuss — 결정 잠금 → CONTEXT.md"),
                    bullet("/quick — 경량 실행 (Small)"),
                    bullet("/auto — 원버튼 자동"),
                ],
            ),
            toggle_h3(
                "탐색/설계/실행",
                [
                    bullet(
                        "/explore, /plan (Nyquist 검증), /codemap-update, /cross-ref"
                    ),
                    bullet("/orchestrate — Agent Teams 병렬 (컨텍스트 자동 주입)"),
                    bullet("/build-fix, /quick-commit"),
                ],
            ),
            toggle_h3(
                "검증/리뷰",
                [
                    bullet("/verify-loop, /handoff-verify, /code-review"),
                    bullet("/qa, /qa-fix, /qa-report, /ci-fix"),
                ],
            ),
            toggle_h3(
                "세션/모니터링",
                [
                    bullet(
                        "/session-save, /session-restore, /checkpoint, /version-tag"
                    ),
                    bullet("/retrospective, /usage-report, /benchmark, /mcp-status"),
                ],
            ),
        ],
    ),
    # 6. Agents
    toggle_h2(
        "🤖 에이전트 (12명)",
        [
            paragraph("전원 memory: project + workflow-discipline.md 규율."),
            toggle_h3(
                "Opus 4명",
                [
                    bullet(
                        "PM-Planner (기획), Architect (설계), Tech-Lead (총괄), CTO-Agent (진화)"
                    )
                ],
            ),
            toggle_h3(
                "Sonnet 7명",
                [
                    bullet("BE-Developer, FE-Developer, AI-Engineer — portfiq-dev"),
                    bullet("Designer, Orchestrator — code-quality"),
                    bullet("Security-Developer — security-review"),
                    bullet("QA-Engineer — code-quality, deployment"),
                ],
            ),
            toggle_h3("Haiku 1명", [bullet("QA-DevOps — code-quality, deployment")]),
        ],
    ),
    # 7. Skills + Hooks
    toggle_h2(
        f"🧩 스킬 ({infra.get('skills', '?')}) + 🪝 훅 ({infra.get('hooks', '?')})",
        [
            toggle_h3(
                "프로젝트 스킬",
                [
                    bullet("portfiq-dev (refs/ 3개), lapaz-dev (refs/ 1개)"),
                ],
            ),
            toggle_h3(
                "공통/시스템 스킬",
                [
                    bullet("code-quality, deployment, security-review"),
                    bullet(
                        "verification-engine, session-wrap, context-compact, codemap-update, build-system"
                    ),
                ],
            ),
            toggle_h3(
                "훅 (7 events)",
                [
                    bullet("PreToolUse: remote-command-guard, db-guard"),
                    bullet(
                        "PostToolUse: secret-filter, security-trigger, auto-format, tool-logger, context-monitor"
                    ),
                    bullet("UserPromptSubmit: skill-suggest, workflow-gate"),
                    bullet("Stop: verify-on-stop | SessionStart: session-start-check"),
                    bullet("SubagentStart/Stop: agent-activity-logger"),
                ],
            ),
        ],
    ),
    # 8. CI/CD + External
    toggle_h2(
        f"🚀 CI/CD ({infra.get('workflows', '?')}) + 외부 연동",
        [
            toggle_h3(
                "Portfiq 6개",
                [
                    bullet("backend, deploy(Railway+Slack), flutter(Fastlane)"),
                    bullet("env-check, db-check, release(수동)"),
                ],
            ),
            toggle_h3(
                "La Paz 2개 + 외부",
                [
                    bullet("la-paz-ci, daily_crawl(매일)"),
                    bullet("Notion(현황+버전DB), Slack, GitHub PR 리뷰, Vercel"),
                ],
            ),
        ],
    ),
    # 9. Knowledge + Projects
    toggle_h2(
        "📚 Knowledge + 📁 프로젝트",
        [
            bullet(
                f"Codemap {infra.get('codemaps', '?')}개 | ADR {infra.get('knowledge_adr', '?')} | 실수 {infra.get('knowledge_mistakes', '?')} | 패턴 {infra.get('knowledge_patterns', '?')} | Cross-Ref | .planning/"
            ),
            bullet(
                "Portfiq (GO) | La Paz (활성) | La Paz Live (배포) | AdaptFit (개발) | 서로연 (MVP) | Foundloop (랜딩)"
            ),
        ],
    ),
]

print(f"총 {len(blocks)}개 블록 추가 중...")
for i in range(0, len(blocks), 100):
    chunk = blocks[i : i + 100]
    resp = requests.patch(
        f"https://api.notion.com/v1/blocks/{PAGE_ID}/children",
        headers=HEADERS,
        json={"children": chunk},
    )
    if resp.status_code != 200:
        print(f"실패: {resp.status_code} — {resp.text[:200]}")
        break
else:
    print("페이지 재구성 완료")
