"""football-data.org에서 PL 전체 팀 선수명을 가져와 player_names.json으로 저장."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# 프로젝트 루트 .env 로드
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

FOOTBALL_DATA_TOKEN: str = os.getenv("FOOTBALL_DATA_TOKEN", "")
FOOTBALL_DATA_BASE: str = "https://api.football-data.org/v4"
OUTPUT_PATH = PROJECT_DIR / "src" / "rag" / "data" / "player_names.json"


def fetch_pl_players() -> list[str]:
    """PL 전체 팀 squad에서 선수명 추출.

    Returns:
        중복 제거된 선수명 리스트 (정렬).
    """
    if not FOOTBALL_DATA_TOKEN:
        print("[ERROR] FOOTBALL_DATA_TOKEN이 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}

    # 1) PL 팀 목록 + squad 조회
    url = f"{FOOTBALL_DATA_BASE}/competitions/PL/teams"
    print(f"[INFO] 요청: {url}")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    players: set[str] = set()
    for team in data.get("teams", []):
        team_name = team.get("name", "Unknown")
        squad = team.get("squad", [])
        for member in squad:
            name = member.get("name", "").strip()
            if name:
                players.add(name)
        print(f"  - {team_name}: {len(squad)}명")

    sorted_players = sorted(players)
    print(f"[INFO] 총 {len(sorted_players)}명 선수 수집 완료")
    return sorted_players


def main() -> None:
    """메인 엔트리포인트."""
    players = fetch_pl_players()

    output = {
        "players": players,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "football-data.org /competitions/PL/teams",
        "count": len(players),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[INFO] 저장 완료: {OUTPUT_PATH} ({len(players)}명)")


if __name__ == "__main__":
    main()
