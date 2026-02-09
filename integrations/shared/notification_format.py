"""공용 알림 포맷팅"""

from __future__ import annotations

from datetime import datetime


def format_qa_report(project_name: str, results: dict) -> str:
    """QA 결과를 읽기 좋은 형태로 포맷."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 QA Report - {project_name} ({timestamp})", ""]

    checks = [
        ("Lint", results.get("lint", None)),
        ("Type Check", results.get("typecheck", None)),
        ("Unit Tests", results.get("tests", None)),
        ("Build", results.get("build", None)),
    ]

    for name, passed in checks:
        if passed is None:
            lines.append(f"  ⏭️ {name}: skipped")
        elif passed:
            lines.append(f"  ✅ {name}: passed")
        else:
            lines.append(f"  ❌ {name}: FAILED")

    all_passed = all(v is True for v in results.values() if v is not None)
    lines.append("")
    lines.append(f"Result: {'✅ ALL PASSED' if all_passed else '❌ FAILURES DETECTED'}")

    return "\n".join(lines)


def format_project_summary(project_name: str, description: str, tech_stack: list[str]) -> str:
    """프로젝트 생성 알림 포맷."""
    return (
        "🚀 *새 프로젝트 생성*\n"
        f"*이름:* {project_name}\n"
        f"*설명:* {description}\n"
        f"*기술 스택:* {', '.join(tech_stack)}"
    )
