"""La Paz Live — Dry-run test suite (20 scenarios).

Sends sequential requests to POST /api/ask and validates responses.
Generates a Markdown report at tests/DRYRUN_REPORT.md.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

API_URL = "http://localhost:8000/api/ask"

MATCH_CONTEXT = {
    "home_team": "Manchester United",
    "away_team": "Aston Villa",
    "match_date": "2026-03-15",
}

# ── Test scenarios ──────────────────────────────────────────────

SCENARIOS: list[dict[str, Any]] = [
    # 1-10: Manchester United questions (Korean)
    {"id": 1,  "question": "맨유의 현재 시즌 성적은 어떤가요?", "scope": "in"},
    {"id": 2,  "question": "루번 아모림 감독의 전술 스타일은?", "scope": "in"},
    {"id": 3,  "question": "맨유에서 가장 활약하고 있는 선수는 누구인가요?", "scope": "in"},
    {"id": 4,  "question": "맨유의 이번 시즌 이적 현황은?", "scope": "in"},
    {"id": 5,  "question": "맨유의 최근 5경기 결과는?", "scope": "in"},
    {"id": 6,  "question": "라시포드의 현재 상태는 어떤가요?", "scope": "in"},
    {"id": 7,  "question": "맨유의 수비 문제점은 뭔가요?", "scope": "in"},
    {"id": 8,  "question": "맨유와 빌라의 최근 상대전적은?", "scope": "in"},
    {"id": 9,  "question": "맨유의 UCL 진출 가능성은?", "scope": "in"},
    {"id": 10, "question": "맨유의 부상자 현황은?", "scope": "in"},
    # 11-15: Aston Villa questions
    {"id": 11, "question": "아스톤 빌라의 이번 시즌 성적은?", "scope": "in"},
    {"id": 12, "question": "에메리 감독의 전술 특징은?", "scope": "in"},
    {"id": 13, "question": "빌라의 핵심 선수는 누구인가요?", "scope": "in"},
    {"id": 14, "question": "아스톤 빌라의 이적 시장 움직임은?", "scope": "in"},
    {"id": 15, "question": "빌라의 홈/원정 성적 차이는?", "scope": "in"},
    # 16-18: Match-specific
    {"id": 16, "question": "이번 맨유 vs 빌라 경기 예상 라인업은?", "scope": "in"},
    {"id": 17, "question": "맨유와 빌라 경기 승부 예측해줘", "scope": "in"},
    {"id": 18, "question": "이 경기에서 주목해야 할 포인트는?", "scope": "in"},
    # 19-20: Out-of-scope
    {"id": 19, "question": "오늘 날씨 어때?", "scope": "out"},
    {"id": 20, "question": "비트코인 가격이 어떻게 되나요?", "scope": "out"},
]


# ── Helpers ──────────────────────────────────────────────────────

def run_single(scenario: dict) -> dict:
    """Send one request and return result dict."""
    payload = {
        "question": scenario["question"],
        "match_context": MATCH_CONTEXT,
    }
    result: dict[str, Any] = {
        "id": scenario["id"],
        "question": scenario["question"],
        "scope": scenario["scope"],
        "status_code": None,
        "answer": "",
        "category": "",
        "confidence": None,
        "source_count": None,
        "response_time_ms": None,
        "pass": False,
        "failures": [],
    }

    start = time.time()
    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        elapsed_ms = int((time.time() - start) * 1000)
    except requests.RequestException as exc:
        elapsed_ms = int((time.time() - start) * 1000)
        result["response_time_ms"] = elapsed_ms
        result["failures"].append(f"HTTP error: {exc}")
        return result

    result["status_code"] = resp.status_code
    result["response_time_ms"] = elapsed_ms

    # ── Assertions ──
    if resp.status_code != 201:
        result["failures"].append(f"Expected 201, got {resp.status_code}")
        try:
            result["answer"] = resp.text[:200]
        except Exception:
            pass
        return result

    body = resp.json()
    result["answer"] = (body.get("answer") or "")[:120]
    result["category"] = body.get("category", "")
    result["confidence"] = body.get("confidence")
    result["source_count"] = body.get("source_count")

    if elapsed_ms > 15000:
        result["failures"].append(f"Slow: {elapsed_ms}ms > 15000ms")

    if not body.get("answer"):
        result["failures"].append("Empty answer")

    if not body.get("category"):
        result["failures"].append("Empty category")

    if scenario["scope"] == "in" and (body.get("source_count") or 0) < 1:
        result["failures"].append(f"source_count={body.get('source_count')} < 1")

    result["pass"] = len(result["failures"]) == 0
    return result


def print_table(results: list[dict]) -> str:
    """Print a compact results table and return it as a string."""
    header = (
        f"{'#':>2} | {'Pass':4} | {'HTTP':4} | {'Time':>7} | {'Conf':>5} | "
        f"{'Src':>3} | {'Category':<14} | Question"
    )
    sep = "-" * len(header)
    lines = [sep, header, sep]
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        http = r["status_code"] or "ERR"
        t = f"{r['response_time_ms']}ms" if r["response_time_ms"] is not None else "N/A"
        conf = f"{r['confidence']:.2f}" if r['confidence'] is not None else "N/A"
        src = r["source_count"] if r["source_count"] is not None else "N/A"
        cat = (r["category"] or "-")[:14]
        q = r["question"][:40]
        lines.append(
            f"{r['id']:>2} | {mark:4} | {str(http):>4} | {t:>7} | {conf:>5} | "
            f"{str(src):>3} | {cat:<14} | {q}"
        )
        if not r["pass"]:
            for f in r["failures"]:
                lines.append(f"   ↳ {f}")
    lines.append(sep)
    table = "\n".join(lines)
    print(table)
    return table


def generate_report(results: list[dict], table_str: str) -> None:
    """Write DRYRUN_REPORT.md alongside this script."""
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    failed = total - passed
    times = [r["response_time_ms"] for r in results if r["response_time_ms"] is not None]
    confs = [r["confidence"] for r in results if r["confidence"] is not None]

    avg_time = int(sum(times) / len(times)) if times else 0
    max_time = max(times) if times else 0
    min_time = min(times) if times else 0
    avg_conf = sum(confs) / len(confs) if confs else 0.0

    issues: list[str] = []
    for r in results:
        if not r["pass"]:
            issues.append(f"- **Q{r['id']}**: {'; '.join(r['failures'])}")

    recs: list[str] = []
    if avg_time > 10000:
        recs.append("- Average response time exceeds 10s — consider caching or optimizing RAG retrieval.")
    if max_time > 15000:
        recs.append("- Some responses exceed 15s timeout — investigate slow queries.")
    if failed > 0:
        recs.append(f"- {failed} scenario(s) failed — review failures above and fix before production.")
    if avg_conf < 0.5:
        recs.append("- Average confidence is below 0.5 — review RAG source quality and retrieval relevance.")
    out_of_scope = [r for r in results if r["scope"] == "out"]
    for r in out_of_scope:
        if r["confidence"] is not None and r["confidence"] > 0.8:
            recs.append(f"- Q{r['id']} (out-of-scope) has high confidence ({r['confidence']:.2f}) — consider adding scope filtering.")
    if not recs:
        recs.append("- All checks passed. System is healthy.")

    report_path = Path(__file__).parent / "DRYRUN_REPORT.md"
    report = f"""# La Paz Live — Dry-Run Test Report

| Item | Value |
|------|-------|
| Date | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| API URL | `{API_URL}` |
| Match Context | {json.dumps(MATCH_CONTEXT)} |
| Total Scenarios | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Pass Rate | {passed/total*100:.1f}% |

---

## Results Table

```
{table_str}
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Avg Response Time | {avg_time} ms |
| Min Response Time | {min_time} ms |
| Max Response Time | {max_time} ms |
| Avg Confidence | {avg_conf:.3f} |
| In-scope Pass Rate | {sum(1 for r in results if r['scope']=='in' and r['pass'])}/{sum(1 for r in results if r['scope']=='in')} |
| Out-of-scope Pass Rate | {sum(1 for r in results if r['scope']=='out' and r['pass'])}/{sum(1 for r in results if r['scope']=='out')} |

---

## Issues Found

{"(none)" if not issues else chr(10).join(issues)}

---

## Recommendations

{chr(10).join(recs)}

---

*Generated by `tests/dryrun_test.py` — La Paz Live QA-DevOps*
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {report_path}")


# ── Main ─────────────────────────────────────────────────────────

def main() -> None:
    print(f"La Paz Live — Dry-Run Test Suite ({len(SCENARIOS)} scenarios)")
    print(f"API: {API_URL}")
    print(f"Match: {MATCH_CONTEXT['home_team']} vs {MATCH_CONTEXT['away_team']}")
    print()

    # Health check
    try:
        r = requests.get("http://localhost:8000/docs", timeout=5)
        print(f"Health check: {r.status_code}")
    except requests.RequestException as exc:
        print(f"WARNING: Backend may not be running — {exc}")

    print()
    results: list[dict] = []
    for sc in SCENARIOS:
        print(f"  [{sc['id']:>2}/{len(SCENARIOS)}] {sc['question'][:50]}...", end=" ", flush=True)
        res = run_single(sc)
        mark = "PASS" if res["pass"] else "FAIL"
        t = f"{res['response_time_ms']}ms" if res["response_time_ms"] else "ERR"
        print(f"→ {mark} ({t})")
        results.append(res)

    print()
    table_str = print_table(results)
    generate_report(results, table_str)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    print(f"\nFinal: {passed}/{total} passed ({passed/total*100:.1f}%)")


if __name__ == "__main__":
    main()
