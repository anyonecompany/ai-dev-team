"""play_style 보강 결과 검증.

검증 항목:
1. players_all_backup.json 존재 확인
2. players_all.json의 모든 40명에 play_style 채워짐
3. play_style 길이 >= 30자 (의미 있는 내용)
4. play_style에 JS 코드 오염 없음
5. 기존 데이터 손상 없음:
   - career_summary가 backup과 동일
   - name_kr, name_en, team, position이 backup과 동일
6. fun_facts 보강 여부 (필수는 아님, 통계만)
7. namu_crawled / play_style_source 필드 존재
8. 나무위키 크롤링 성공률 통계
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# JS 오염 패턴
JS_CONTAMINATION_PATTERNS: list[str] = [
    r"localStorage",
    r"sessionStorage",
    r"document\.",
    r"window\.",
    r"function\s*\(",
    r"var\s+\w+\s*=",
    r"let\s+\w+\s*=",
    r"const\s+\w+\s*=",
    r"console\.\w+",
    r"<script",
    r"addEventListener",
    r"innerHTML",
    r"getElementById",
]

# 보존해야 할 필드 (backup과 동일해야 함)
PRESERVED_FIELDS: list[str] = [
    "name_kr",
    "name_en",
    "team",
    "team_kr",
    "position",
    "career_summary",
]

MIN_PLAY_STYLE_LENGTH = 30


class EnrichmentChecker:
    """보강 데이터 품질 검증기."""

    def check_all(self, data_path: str, backup_path: str) -> dict[str, Any]:
        """전체 검증 실행."""
        results: dict[str, Any] = {
            "backup_exists": False,
            "total_players": 0,
            "play_style_filled": 0,
            "play_style_empty": [],
            "play_style_too_short": [],
            "js_contaminated": [],
            "data_corrupted": [],
            "fun_facts_stats": {"enriched": 0, "empty": 0},
            "namu_crawled_stats": {"crawled": 0, "not_crawled": 0},
            "play_style_source_stats": {},
            "all_passed": False,
        }

        # 1. backup 존재 확인
        results["backup_exists"] = os.path.exists(backup_path)

        # 데이터 로드
        with open(data_path, encoding="utf-8") as f:
            current = json.load(f)
        results["total_players"] = len(current)

        backup = None
        if results["backup_exists"]:
            with open(backup_path, encoding="utf-8") as f:
                backup = json.load(f)

        # 2-4. play_style 검증
        for i, player in enumerate(current):
            name = player.get("name_kr", f"player_{i}")
            ps = player.get("play_style", "")

            if not ps or not ps.strip():
                results["play_style_empty"].append(name)
            else:
                results["play_style_filled"] += 1
                if len(ps.strip()) < MIN_PLAY_STYLE_LENGTH:
                    results["play_style_too_short"].append(
                        {"name": name, "length": len(ps.strip())}
                    )

            # JS 오염 검사
            for pattern in JS_CONTAMINATION_PATTERNS:
                if re.search(pattern, ps, re.IGNORECASE):
                    results["js_contaminated"].append(
                        {"name": name, "pattern": pattern}
                    )
                    break

            # 6. fun_facts 통계
            ff = player.get("fun_facts", [])
            if ff and len(ff) > 0:
                results["fun_facts_stats"]["enriched"] += 1
            else:
                results["fun_facts_stats"]["empty"] += 1

            # 7. namu_crawled / play_style_source
            if player.get("namu_crawled"):
                results["namu_crawled_stats"]["crawled"] += 1
            else:
                results["namu_crawled_stats"]["not_crawled"] += 1

            source = player.get("play_style_source", "unknown")
            results["play_style_source_stats"][source] = (
                results["play_style_source_stats"].get(source, 0) + 1
            )

        # 5. 기존 데이터 손상 검사
        if backup:
            results["data_corrupted"] = self.check_no_data_corruption(
                current, backup
            )

        # 종합 판정
        results["all_passed"] = (
            results["backup_exists"]
            and results["play_style_filled"] == results["total_players"]
            and len(results["play_style_too_short"]) == 0
            and len(results["js_contaminated"]) == 0
            and len(results["data_corrupted"]) == 0
        )

        return results

    def check_no_data_corruption(
        self, current: list[dict], backup: list[dict]
    ) -> list[dict[str, Any]]:
        """기존 데이터 손상 여부 확인."""
        corrupted: list[dict[str, Any]] = []

        # backup을 name_en 기준으로 인덱싱
        backup_map = {p["name_en"]: p for p in backup}

        for player in current:
            name_en = player.get("name_en", "")
            bp = backup_map.get(name_en)
            if not bp:
                corrupted.append(
                    {"name": player.get("name_kr", name_en), "issue": "backup에 없는 선수"}
                )
                continue

            for field in PRESERVED_FIELDS:
                cur_val = player.get(field, "")
                bak_val = bp.get(field, "")
                if cur_val != bak_val:
                    corrupted.append(
                        {
                            "name": player.get("name_kr", name_en),
                            "field": field,
                            "backup_value": bak_val[:50] if isinstance(bak_val, str) else bak_val,
                            "current_value": cur_val[:50] if isinstance(cur_val, str) else cur_val,
                        }
                    )

        return corrupted

    def print_report(self, results: dict[str, Any]) -> None:
        """검증 결과 출력."""
        print("=" * 60)
        print("  ENRICHMENT QA REPORT")
        print("=" * 60)

        total = results["total_players"]

        # 1. Backup
        status = "PASS" if results["backup_exists"] else "FAIL"
        print(f"\n[{status}] Backup 존재: {results['backup_exists']}")

        # 2. play_style 채워짐
        filled = results["play_style_filled"]
        status = "PASS" if filled == total else "FAIL"
        print(f"[{status}] play_style 채워짐: {filled}/{total}")
        if results["play_style_empty"]:
            for name in results["play_style_empty"]:
                print(f"       - 비어있음: {name}")

        # 3. play_style 길이
        status = "PASS" if not results["play_style_too_short"] else "FAIL"
        print(f"[{status}] play_style 길이 >= {MIN_PLAY_STYLE_LENGTH}자")
        for item in results["play_style_too_short"]:
            print(f"       - {item['name']}: {item['length']}자")

        # 4. JS 오염
        status = "PASS" if not results["js_contaminated"] else "FAIL"
        print(f"[{status}] JS 코드 오염 없음")
        for item in results["js_contaminated"]:
            print(f"       - {item['name']}: '{item['pattern']}' 발견")

        # 5. 기존 데이터 손상
        status = "PASS" if not results["data_corrupted"] else "FAIL"
        print(f"[{status}] 기존 데이터 손상 없음")
        for item in results["data_corrupted"]:
            issue = item.get("issue", f"{item.get('field')} 변경됨")
            print(f"       - {item['name']}: {issue}")

        # 6. fun_facts (정보)
        fs = results["fun_facts_stats"]
        print(f"\n[INFO] fun_facts 보강: {fs['enriched']}/{total}")

        # 7-8. 나무위키 크롤링
        ns = results["namu_crawled_stats"]
        print(f"[INFO] 나무위키 크롤링 성공: {ns['crawled']}/{total}")

        # play_style_source 분포
        print("[INFO] play_style_source 분포:")
        for src, cnt in results["play_style_source_stats"].items():
            print(f"       - {src}: {cnt}명")

        # 종합
        print("\n" + "=" * 60)
        final = "ALL PASSED" if results["all_passed"] else "FAILED"
        print(f"  최종 결과: {final}")
        print("=" * 60)


def main() -> None:
    """CLI 진입점."""
    base = Path(__file__).resolve().parent.parent.parent / "data"
    data_path = str(base / "players_all.json")
    backup_path = str(base / "players_all_backup.json")

    if not os.path.exists(data_path):
        print(f"ERROR: {data_path} 없음")
        sys.exit(1)

    checker = EnrichmentChecker()
    results = checker.check_all(data_path, backup_path)
    checker.print_report(results)

    sys.exit(0 if results["all_passed"] else 1)


if __name__ == "__main__":
    main()
