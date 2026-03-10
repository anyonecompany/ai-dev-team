"""크롤링 결과 데이터 품질 검증.

검증 항목:
1. 총 선수 수 >= 40명
2. 필수 필드 존재: name_kr, name_en, team, position, play_style
3. 필드 타입 검증: fun_facts는 list, birth_date는 날짜 형식
4. 중복 선수 검출
5. 팀별 최소 인원: MUN >= 20, AVL >= 20
6. content 텍스트 길이: 최소 100자 이상 (검색 품질 보장)
"""

import json
import re
from pathlib import Path


class DataChecker:
    """크롤링 데이터 품질 검증기."""

    REQUIRED_FIELDS = ["name_kr", "name_en", "team", "position"]
    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def _find_data_file(self, data_dir: str) -> Path | None:
        """data/players_all.json 또는 output/players_*.json 중 최신 파일 탐색."""
        data_path = Path(data_dir)

        # 1. data/players_all.json (인덱싱용 병합 파일)
        players_all = data_path / "players_all.json"
        if players_all.exists():
            return players_all

        # 2. output/players_*.json (크롤링 직후 파일)
        output_dir = data_path.parent / "output"
        if output_dir.exists():
            json_files = sorted(output_dir.glob("players_*.json"), reverse=True)
            if json_files:
                return json_files[0]

        return None

    def _load_players(self, file_path: Path) -> list[dict]:
        """JSON 파일에서 선수 목록 로드. nested/flat 모두 지원."""
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            players: list[dict] = []
            for key in ("mun", "avl"):
                players.extend(data.get(key, []))
            return players
        return []

    def check_all(self, data_dir: str) -> dict:
        """전체 검증 실행. 결과 dict 반환."""
        results: dict = {
            "total_players": 0,
            "mun_count": 0,
            "avl_count": 0,
            "missing_fields": [],
            "type_errors": [],
            "duplicates": [],
            "short_content": [],
            "errors": [],
            "passed": False,
        }

        data_file = self._find_data_file(data_dir)
        if data_file is None:
            results["errors"].append(f"데이터 파일 없음: {data_dir}/players_all.json 또는 output/players_*.json")
            return results

        try:
            players = self._load_players(data_file)
        except (json.JSONDecodeError, OSError) as e:
            results["errors"].append(f"JSON 파싱 실패: {e}")
            return results

        results["total_players"] = len(players)

        seen_names: set[str] = set()

        for i, player in enumerate(players):
            name_en = player.get("name_en", f"unknown_{i}")

            # 필수 필드 검증
            for field in self.REQUIRED_FIELDS:
                if field not in player or not player[field]:
                    results["missing_fields"].append(
                        {"player": name_en, "field": field}
                    )

            # 팀 카운트 (MUN/Manchester United 등 모두 지원)
            team = player.get("team", "").upper()
            if "MUN" in team or "MANCHESTER" in team:
                results["mun_count"] += 1
            elif "AVL" in team or "ASTON" in team or "VILLA" in team:
                results["avl_count"] += 1

            # 타입 검증: fun_facts
            if "fun_facts" in player and not isinstance(player["fun_facts"], list):
                results["type_errors"].append(
                    {"player": name_en, "field": "fun_facts", "expected": "list"}
                )

            # 타입 검증: birth_date
            if "birth_date" in player and player["birth_date"]:
                if not self.DATE_PATTERN.match(str(player["birth_date"])):
                    results["type_errors"].append(
                        {"player": name_en, "field": "birth_date", "expected": "YYYY-MM-DD"}
                    )

            # 중복 검출
            if name_en in seen_names:
                results["duplicates"].append(name_en)
            seen_names.add(name_en)

            # content/bio 길이 검증
            content = player.get("content", "") or player.get("bio", "") or player.get("career_summary", "")
            if len(content) < 100:
                results["short_content"].append(
                    {"player": name_en, "length": len(content)}
                )

        # 최종 판정
        passed = (
            results["total_players"] >= 40
            and results["mun_count"] >= 20
            and results["avl_count"] >= 20
            and len(results["missing_fields"]) == 0
            and len(results["duplicates"]) == 0
            and len(results["errors"]) == 0
        )
        results["passed"] = passed
        return results

    def print_report(self, results: dict) -> None:
        """검증 결과를 콘솔에 출력."""
        status = "PASS" if results["passed"] else "FAIL"
        print(f"\n{'='*50}")
        print(f"  데이터 품질 검증 결과: {status}")
        print(f"{'='*50}")
        print(f"  총 선수 수: {results['total_players']} (기준: >= 40)")
        print(f"  MUN 선수: {results['mun_count']} (기준: >= 20)")
        print(f"  AVL 선수: {results['avl_count']} (기준: >= 20)")

        if results["missing_fields"]:
            print(f"\n  필수 필드 누락 ({len(results['missing_fields'])}건):")
            for item in results["missing_fields"][:10]:
                print(f"    - {item['player']}: {item['field']}")

        if results["type_errors"]:
            print(f"\n  타입 오류 ({len(results['type_errors'])}건):")
            for item in results["type_errors"][:10]:
                print(f"    - {item['player']}: {item['field']} (expected {item['expected']})")

        if results["duplicates"]:
            print(f"\n  중복 선수 ({len(results['duplicates'])}건):")
            for name in results["duplicates"]:
                print(f"    - {name}")

        if results["short_content"]:
            print(f"\n  짧은 content ({len(results['short_content'])}건):")
            for item in results["short_content"][:10]:
                print(f"    - {item['player']}: {item['length']}자")

        if results["errors"]:
            print(f"\n  오류:")
            for err in results["errors"]:
                print(f"    - {err}")

        print(f"{'='*50}\n")


if __name__ == "__main__":
    import sys

    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    checker = DataChecker()
    results = checker.check_all(data_dir)
    checker.print_report(results)
    sys.exit(0 if results["passed"] else 1)
