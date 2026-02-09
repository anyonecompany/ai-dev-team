#!/usr/bin/env python3
"""
Slack/Monday 연동 테스트 스크립트.

실행: cd ~/ai-dev-team && python3 integrations/test_integration.py
필요: pip3 install python-dotenv httpx
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    print("⚠️  python-dotenv 없음. pip3 install python-dotenv httpx")


async def test_slack():
    """Slack 알림 테스트."""
    print("\n═══ Slack 테스트 ═══")
    from integrations.slack.slack_notifier import send_notification, notify_project_created, notify_qa_result

    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    channel = os.getenv("SLACK_CHANNEL", "")
    print(f"  WEBHOOK: {'✅ 설정됨' if webhook else '❌ 미설정'}")
    print(f"  CHANNEL: {channel or '❌ 미설정'}")

    if not webhook:
        print("  ⏭️  건너뜀")
        return False

    try:
        await send_notification(channel, "🧪 [테스트] Slack 연동 테스트 메시지")
        print("  ✅ 기본 알림 전송 완료")

        await notify_project_created("연동-테스트-프로젝트")
        print("  ✅ 프로젝트 생성 알림 완료")

        await notify_qa_result("연동-테스트-프로젝트", True, "lint: PASS, typecheck: PASS")
        print("  ✅ QA 결과 알림 완료")

        print("  📱 Slack 채널을 확인하세요!")
        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


async def test_monday():
    """Monday.com 연동 테스트."""
    print("\n═══ Monday.com 테스트 ═══")
    from integrations.monday.monday_sync import (
        is_monday_enabled, initialize, create_project,
        log_qa_result, log_agent_activity, get_board_url,
    )

    print(f"  API_TOKEN: {'✅ 설정됨' if is_monday_enabled() else '❌ 미설정'}")

    if not is_monday_enabled():
        print("  ⏭️  건너뜀")
        return False

    try:
        print("  → 초기화 (보드/그룹/컬럼 확인)...")
        await initialize()
        url = get_board_url()
        print(f"  ✅ 보드 URL: {url}")

        print("  → 테스트 프로젝트 생성...")
        proj_id = await create_project(
            "연동 테스트 프로젝트",
            description="Slack/Monday 연동 테스트용",
            tech_stack=["Python", "FastAPI"],
            github_link="https://github.com/anyonecompany/ai-dev-team",
        )
        print(f"  ✅ 프로젝트 ID: {proj_id}")

        print("  → QA 결과 기록...")
        qa_id = await log_qa_result(
            "연동 테스트 프로젝트",
            lint=True, typecheck=True, tests=True, build=None,
            details="테스트용 QA 결과",
        )
        print(f"  ✅ QA ID: {qa_id}")

        print("  → 에이전트 활동 로그...")
        log_id = await log_agent_activity(
            agent="QA-DevOps",
            action="연동 테스트 실행",
            description="Slack/Monday 연동 테스트 완료",
        )
        print(f"  ✅ 활동 로그 ID: {log_id}")

        print(f"\n  📊 Monday.com 보드 확인: {url}")
        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


async def main():
    print("╔══════════════════════════════════════╗")
    print("║   AI Dev Team 연동 테스트            ║")
    print("╚══════════════════════════════════════╝")

    slack_ok = await test_slack()
    monday_ok = await test_monday()

    print("\n═══ 결과 요약 ═══")
    print(f"  Slack:     {'✅ 성공' if slack_ok else '❌ 실패/건너뜀'}")
    print(f"  Monday:    {'✅ 성공' if monday_ok else '❌ 실패/건너뜀'}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
